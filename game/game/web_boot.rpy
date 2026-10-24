## 网页版装载链路的运行时补丁（桌面版全部跳过）。
##
## 为什么需要：
##   Ren'Py 的渐进式下载把 80 个重资源留在 game.zip 之外，玩到哪下到哪。
##   原生实现（renpy/webloader.py 的 RenPyWeb.dl_new）**一次请求失败就放弃**：
##   文件没落地 → process_downloaded_resources() 抛
##   IOError("Download error: network error") → 直接进英文报错界面。
##   弱网上这就是「玩到一半突然黑了」。
##
## 做一件事：
##   把 dl_new 换成带重试的版本（实现在 tools/web/chaoshi-loader.js 的
##   installAssetRetry）：20 秒无数据才中断、指数退避、后两次自动换镜像。
##   重试期间 readyState 保持 0，占位图继续显示，Python 侧不会抛错。
##
## 重试也救不回来的情况（彻底失败）不在本文件处理，见 robust.rpy：
## 退避重试 4 次 → 放弃该文件 → toast 告知，立绘留在占位图上继续演。

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

        # 「下载失败该不该 raise」这件事挪到 robust.rpy 了（init -45，晚于本文件的
        # -50，所以它的替换会生效）：那里改成退避重试 + 放弃 + toast，不再把玩家
        # 推到错误页。本文件只管补下载重试。
