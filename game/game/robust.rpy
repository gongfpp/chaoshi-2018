## 兜底层：资源失败、异常、玩家乱点，都不许把玩家推到白屏或错误页。
##
## 三条防线，从源头到末端。顺序很重要——越靠前，玩家感知越弱：
##
##   1) 资源下载失败（网页版按需下载）
##      原版 renpy/webloader.process_downloaded_resources 在「XHR 结束了但文件
##      没落地」时直接 raise IOError，源码注释写明目的就是
##        # trigger Ren'Py's error handler
##      这是网页版一切错误页的总源头：弱网下一张立绘下不动，整局游戏当场停住。
##      本文件把它换成「退避重试 → 放弃 → toast」，立绘/背景留在 Ren'Py 自带的
##      占位图上（im.py 的 `_placeholders/` 机制），文字剧情照常推进。
##
##   2) DynamicImage 找不到目标
##      原来是 raise Exception("... could not find image")，2026-10 的手机端崩溃
##      就是它。换成 Null()：界面上少一张图，游戏继续。
##
##   3) 其它任何未预期异常
##      经 config.exception_handler 收口（execution.py 的官方创作者钩子），
##      toast 告知并继续，不再弹 Ren'Py 的 _exception 全屏错误页。
##      同类错误连续出现时，toast 会升级成「建议刷新」，不会无限刷屏。
##
## 桌面版同样生效：所有 patch 都带平台判断，只有 webloader 那一处仅限网页版。

init -45 python:

    import os as _cs_os
    import time as _cs_time
    import json as _cs_json

    ## ---------------------------------------------------------------- toast

    CS_TOAST_MIN_GAP = 3.0        # 两条 toast 之间的最短间隔，防止刷屏
    CS_TOAST_MAX = 24             # 单局最多提示几条，再多就闭嘴
    _cs_toast_at = [0.0]
    _cs_toast_n = [0]

    def cs_toast(msg, kind="info", ms=5200):
        """轻量提示：不抢焦点、自动消失、可点掉，绝不打断当前操作。

        网页版走 window.ChaoshiToast（chaoshi-loader.js 里的页面级 toast）；
        桌面版退回 Ren'Py 的 notify。两条路都不会阻断交互。
        """
        now = _cs_time.time()

        if _cs_toast_n[0] >= CS_TOAST_MAX:
            return
        if now - _cs_toast_at[0] < CS_TOAST_MIN_GAP:
            return

        _cs_toast_at[0] = now
        _cs_toast_n[0] += 1

        if renpy.emscripten:
            try:
                import emscripten
                emscripten.run_script(
                    "try{window.ChaoshiToast&&window.ChaoshiToast(%s,%s,%s)}catch(e){}"
                    % (_cs_json.dumps(str(msg)),
                       _cs_json.dumps(kind),
                       _cs_json.dumps(int(ms))))
                return
            except Exception:
                pass

        try:
            renpy.exports.notify(str(msg))
        except Exception:
            pass

    ## ------------------------------------------- 防线 1：资源下载失败不 raise

    if renpy.emscripten:
        import renpy.webloader as _cs_wl

        CS_RES_MAX_TRY = 4              # 同一文件最多试几次
        CS_RES_DEAD_TTL = 60.0          # 放弃后 60 秒内不再重试，避免每帧发请求
        CS_RES_BACKOFF = (0.0, 1.0, 2.5, 5.0)

        _cs_res_try = {}                # relpath -> 已试次数
        _cs_res_at = {}                 # relpath -> 上次发起下载的时间
        _cs_res_dead = {}               # relpath -> 放弃时刻
        _cs_res_told = set()            # 已经提示过玩家的文件
        _cs_res_pending = []            # 还没到重试时间的请求

        def _cs_res_fail(rr):
            """下载结束但文件没落地。退避重试，超限就放弃并只提示一次。"""
            rel = rr.relpath
            now = _cs_time.time()

            dead_at = _cs_res_dead.get(rel)
            if dead_at is not None:
                if now - dead_at < CS_RES_DEAD_TTL:
                    return                      # 冷静期内，直接丢掉这个请求
                del _cs_res_dead[rel]           # 冷静期过了，再给一次机会
                _cs_res_try[rel] = 0
                _cs_res_told.discard(rel)

            n = _cs_res_try.get(rel, 0) + 1
            _cs_res_try[rel] = n

            if n > CS_RES_MAX_TRY:
                _cs_res_dead[rel] = now
                if rel not in _cs_res_told:
                    _cs_res_told.add(rel)
                    track("res_fail", target=rel)
                    cs_toast("「%s」还没下载成功，先用占位图顶着，剧情不受影响。"
                             % rel.split("/")[-1], "warn")
                return

            gap = CS_RES_BACKOFF[min(n - 1, len(CS_RES_BACKOFF) - 1)]
            last = _cs_res_at.get(rel, 0.0)
            if now - last < gap:
                _cs_res_pending.append(rr)      # 没到下次尝试的时间，先挂着
                return

            _cs_res_at[rel] = now
            # enqueue() 会按 rtype+data 去重，这里直接建新请求绕过它
            _cs_wl.queue.append(_cs_wl.ReloadRequest(rr.relpath, rr.rtype, rr.data))

        def _cs_process_downloaded_resources():
            """process_downloaded_resources 的健壮版：逻辑与原版一致，
            唯一区别是「文件没落地」不再 raise，而是走重试/放弃。"""
            queue = _cs_wl.queue
            if not queue:
                return

            global _cs_res_pending
            hold = _cs_res_pending
            _cs_res_pending = []

            with _cs_wl.queue_lock:
                todo = queue[:]
                n0 = len(queue)     # 循环前长度：之后追加的都是 _cs_res_fail 的重试请求
                postponed = []

                try:
                    while todo:
                        rr = todo.pop()

                        if not rr.download_completed():
                            postponed.append(rr)
                            continue

                        if rr.rtype == "image":
                            fullpath = _cs_os.path.join(renpy.config.gamedir, rr.relpath)
                            if not _cs_os.path.exists(fullpath):
                                _cs_res_fail(rr)
                                continue

                            renpy.exports.flush_cache_file(rr.data)
                            _cs_res_try.pop(rr.relpath, None)
                            _cs_res_at.pop(rr.relpath, None)
                            _cs_res_dead.pop(rr.relpath, None)
                            _cs_res_told.discard(rr.relpath)
                            _cs_wl.to_unlink[fullpath] = _cs_time.time() + 10

                        elif rr.rtype == "music":
                            if renpy.config.web_unload_music:
                                fullpath = _cs_os.path.join(renpy.config.gamedir, rr.relpath)
                                _cs_wl.to_unlink[fullpath] = _cs_time.time() + renpy.config.web_unload_music

                        elif rr.rtype == "voice":
                            fullpath = _cs_os.path.join(renpy.config.gamedir, rr.relpath)
                            _cs_wl.to_unlink[fullpath] = _cs_time.time() + 120

                finally:
                    # 原版在这里把队列收干净，保证错误处理阶段不会二次抛异常。
                    # 但**不能把循环内追加的重试请求一起丢掉**：_cs_res_fail 会往
                    # 队列里追加新的 ReloadRequest（Python 层退避重试的实体），
                    # 整体 rebind / 清空都会让它们消失 → 重试链断掉，
                    # 放弃线（n>4）永远摸不到，「还没下载成功」的 toast 也永不触发。
                    # 队列在锁内只被本函数改动，所以 n0 之后的部分就是本次新增的。
                    extra = queue[n0:]
                    _cs_wl.queue = postponed + todo + hold + extra

            current_time = _cs_time.time()
            for fullpath, value in tuple(_cs_wl.to_unlink.items()):
                if current_time - value > 60:
                    try:
                        _cs_os.unlink(fullpath)
                    except Exception:
                        pass
                    del _cs_wl.to_unlink[fullpath]

        _cs_wl.process_downloaded_resources = _cs_process_downloaded_resources

    ## -------------------------------------- 防线 2：DynamicImage 找不到目标

    try:
        import renpy.display.image as _cs_img
        import renpy.display.layout as _cs_layout
        import renpy.display.render as _cs_render

        if not getattr(_cs_img.DynamicImage, "_cs_guarded", False):
            _cs_orig_find_target = _cs_img.DynamicImage.find_target

            def _cs_find_target(self, scope=None, update=True):
                try:
                    return _cs_orig_find_target(self, scope, update)
                except Exception:
                    # 少一张图而已，界面继续渲染。raw_target 置空，下次还会再试。
                    try:
                        self.raw_target = None
                        self.target = _cs_layout.Null()
                        _cs_render.redraw(self, 0)
                    except Exception:
                        pass
                    return True

            _cs_find_target._cs_guarded = True
            _cs_img.DynamicImage.find_target = _cs_find_target
    except Exception:
        pass

    ## ------------------------------------------ 防线 3：未预期异常不再弹错误页

    _cs_err_reason = {}
    _cs_err_count = {}

    def _cs_exception_handler(te):
        """config.exception_handler：返回 True 表示「已经处理，别再弹错误页」。

        这是 execution.py 里留给创作者的官方钩子。图片/资源类错误直接吞掉；
        其它错误 toast 告知，同类错误连续出现时升级成「建议刷新」。
        """
        try:
            reason = ""
            try:
                reason = str(getattr(te, "simple", "") or "").strip()[:100]
            except Exception:
                pass

            key = reason or "unknown"
            _cs_err_count[key] = _cs_err_count.get(key, 0) + 1
            track("error", reason="py:" + key)

            # 图片类：引擎本来就能忽略，这里顺手把开关关掉，避免连环抛
            if "image" in key.lower() or "could not find" in key.lower():
                renpy.config.raise_image_exceptions = False
                renpy.config.raise_image_load_exceptions = False
                return True

            if _cs_err_count[key] >= 3:
                if _cs_err_count[key] == 3:
                    cs_toast("同一个问题反复出现（%s），建议刷新页面。" % key, "warn", 9000)
                return True

            cs_toast("出了点问题，已自动跳过。若画面不正常，刷新即可。", "warn")
        except Exception:
            pass

        return True

    config.exception_handler = _cs_exception_handler
