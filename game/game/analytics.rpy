## 埋点桥：Ren'Py 事件 → 宿主网页 → 采集端
##
## 只在 Web 构建里生效（依赖 emscripten.run_script）；桌面版会静默跳过。
## 事件字段由 tools/gen_game.py 在生成脚本时注入，见 game/game/gen/*.rpy。
##
## 采集端是自部署在腾讯云的 chaoshi-analytics（见 server/chaoshi-analytics），
## 浏览器侧的上报地址由 tools/patch_web.py 注入。

## 标题页脚注的数据：JS 拉到 /api/live 后经 renpy_exec 回填这三个变量。
## -1 / "" 表示还没拿到，界面据此不显示。
default CHAOSHI_LIVE_ONLINE = -1
default CHAOSHI_LIVE_TOTAL = -1
default CHAOSHI_LIVE_TEXT = ""


init -20 python:
    import json as _ana_json
    import time as _ana_time

    ## 允许上报的事件白名单：新增事件必须在这里登记，避免误传正文内容
    ANA_EVENTS = {
        "run_start", "chapter_enter", "chapter_complete", "chapter_jump",
        "choice_shown", "choice_pick", "ending_enter", "ending_complete",
        "save_ok", "save_fail", "load_ok", "load_fail",
        "skip_on", "auto_on", "mute_on", "voice_fail",
        "res_fail",          # 资源下载重试耗尽后放弃（robust.rpy）
        "play_beat",         # 每 60 秒一次心跳：在线人数 + 单局时长 + 当前进度
    }

    ## 只允许这些键，防止把整段对白塞进埋点
    ANA_FIELDS = {
        "chapter", "choice", "option", "opt", "ending", "from", "to",
        "amount", "reason", "ms", "sec", "target",
    }

    ## 最近一次失败原因，便于在游戏内排查（不影响正常游玩）
    ANA_LAST_ERROR = []

    ## 心跳节流 / 标题页状态。用 list 包一层是因为 init python 里的
    ## 模块级名字不能在函数里靠 global 改（rollback 也会带来麻烦）。
    ANA_BEAT_AT = [0.0]
    ANA_TITLE_ON = [None]
    ANA_CHAPTER = [""]

    def _ana_js(js):
        try:
            import emscripten
            emscripten.run_script(js)
        except Exception:
            pass

    def track(event, **fields):
        if event not in ANA_EVENTS:
            return
        try:
            if event == "chapter_enter" and fields.get("chapter"):
                ANA_CHAPTER[0] = fields["chapter"]
            payload = {"event": event}
            for k, v in fields.items():
                if k in ANA_FIELDS:
                    payload[k] = v
            try:
                payload["run_id"] = getattr(renpy.store, "run_id", "") or ""
            except Exception:
                payload["run_id"] = ""
            payload["t"] = int(_ana_time.time() * 1000)

            raw = _ana_json.dumps(payload, ensure_ascii=False)
            quoted = _ana_json.dumps(raw, ensure_ascii=True)
            # 主线程直接用 window.chaoshiTrack；若运行在 worker 里则 postMessage 给宿主
            js = (
                "(function(){var s=(typeof window!=='undefined')?window"
                ":(typeof self!=='undefined'?self:null);"
                "if(s&&s.chaoshiTrack){s.chaoshiTrack(%s);}"
                "else if(typeof postMessage==='function'){"
                "postMessage({__chaoshi_event:%s});}})()"
            ) % (quoted, quoted)

            import emscripten
            emscripten.run_script(js)
        except Exception as e:
            if len(ANA_LAST_ERROR) < 20:
                ANA_LAST_ERROR.append("%s: %s" % (event, e))

    ## ---- 心跳 ------------------------------------------------------------
    ## 时长不在这里算：秒数由网页侧按「页面可见 + 最近 5 分钟内有过输入」累计，
    ## 挂在同一条事件上（见 tools/patch_web.py 的 activeSec）。这样玩家把
    ## 标签页挂在后台时不会把「游玩时长」灌成几十个小时。
    ##
    ## 这里只负责节奏与上下文：每 60 秒一拍，带上当前章节，顺便当在线信号。

    def ana_tick():
        try:
            now = _ana_time.time()

            on_title = bool(renpy.get_screen("main_menu"))
            if ANA_TITLE_ON[0] is not on_title:
                ANA_TITLE_ON[0] = on_title
                # 只在标题页轮询在线人数，进游戏就停，避免和剧情抢线程
                _ana_js("window.ChaoshiLive&&window.ChaoshiLive.setActive(%s)"
                        % ("true" if on_title else "false"))

            if now - ANA_BEAT_AT[0] < 60:
                return
            ANA_BEAT_AT[0] = now

            if on_title:
                return
            if not (getattr(renpy.store, "run_id", "") or ""):
                return
            track("play_beat", chapter=ANA_CHAPTER[0])
        except Exception:
            pass

    config.periodic_callbacks.append(ana_tick)

    ## ---- 标题页脚注 ------------------------------------------------------

    def ana_set_live(online, total):
        """由网页侧调用：renpy_exec('ana_set_live(3, 1284)')。"""
        try:
            online = int(online)
            total = int(total)
        except Exception:
            return
        store.CHAOSHI_LIVE_ONLINE = online
        store.CHAOSHI_LIVE_TOTAL = total
        if total <= 0:
            store.CHAOSHI_LIVE_TEXT = ""
        else:
            store.CHAOSHI_LIVE_TEXT = "此刻 %d 人在线 · 累计 %s 位读者" % (
                online, "{:,}".format(total))
        try:
            # 数字变了要让当前这屏重画一次，否则要等到下一次交互才更新
            if renpy.get_screen("main_menu"):
                renpy.restart_interaction()
        except Exception:
            pass
