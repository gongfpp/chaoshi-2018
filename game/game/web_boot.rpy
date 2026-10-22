## 网页版装载链路的运行时补丁（桌面版全部跳过）。
##
## 为什么需要：
##   Ren'Py 的渐进式下载把 80 个重资源留在 game.zip 之外，玩到哪下到哪。
##   原生实现（renpy/webloader.py 的 RenPyWeb.dl_new）**一次请求失败就放弃**：
##   文件没落地 → process_downloaded_resources() 抛
##   IOError("Download error: network error") → 直接进英文报错界面。
##   弱网上这就是「玩到一半突然黑了」。
##
## 做两件事：
##   1) 把 dl_new 换成带重试的版本（实现在 tools/web/chaoshi-loader.js 的
##      installAssetRetry）：20 秒无数据才中断、指数退避、后两次自动换镜像。
##      重试期间 readyState 保持 0，占位图继续显示，Python 侧不会抛错。
##   2) 彻底失败时，把英文原因换成中文，玩家才知道该刷新还是换网络。

init -50 python:

    if renpy.emscripten:
        import emscripten as _cs_em

        try:
            _cs_em.run_script(
                "try{"
                "  if(window.ChaoshiLoader&&window.ChaoshiLoader.installAssetRetry){"
                "    window.ChaoshiLoader.installAssetRetry();"
                "  }"
                "}catch(e){}")
        except Exception:
            pass

        import renpy.webloader as _cs_wl

        if not getattr(_cs_wl, "_cs_wrapped", False):
            _cs_orig_process = _cs_wl.process_downloaded_resources

            def _cs_process_downloaded():
                try:
                    _cs_orig_process()
                except IOError as e:
                    raise IOError(
                        u"剧本资源没有下载成功（%s）。"
                        u"多半是网络中断：刷新页面会接着下，已经下过的不再重来。" % (e,))

            _cs_wl.process_downloaded_resources = _cs_process_downloaded
            _cs_wl._cs_wrapped = True
