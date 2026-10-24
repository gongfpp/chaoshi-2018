## 网页版「退出」按钮的安全替代（00 前缀保证先于 zh_ui.rpy 加载）。
##
## 问题（第五轮对抗测试实测复现）：
##   标题页「退出」绑的是 Quit(confirm=False)。Quit 动作最终调用
##   renpy.quit() → 抛 QuitException → 网页版直接终结 wasm 运行时：
##   画面冻结在最后一帧——没有错误页、没有提示、URL 都不变，
##   玩家不手动刷新永远回不来。这是「卡死且无法回退」的典型形态，
##   正是本轮要消灭的目标。Ren'Py 自己在 screens.rpy:342 的注释也说了
##   "The quit button is banned on iOS and unnecessary on Android and Web"，
##   但本作在 zh_ui.rpy 里显式加回了这一项，且没有任何平台判断。
##
## 方案：网页版退出 = toast 告知 → full_restart 活着回到标题页。
##   full_restart 就是本作游戏内「返回标题」按钮（MainMenu 动作）用的
##   同一套机制，网页版一直在用；它只重置 store 跳回主菜单，不杀运行时、
##   不重新下载资源（虚拟文件系统里的已下载文件原样保留）。
##   桌面版没有这个问题，仍走标准 renpy.quit()。
##
## 注意：本文件**不能**写 `import renpy`。Ren'Py 的 defaultstore 最后一行是
##   globals()["renpy"] = renpy.exports
## 即 store 里的 `renpy` 这个名字指向 renpy.exports（导出面）。
## 裸 `import renpy` 会把这个别名影子成真实 renpy 包，而真实包并没有
## emscripten / quit / confirm / full_restart 这些导出，按钮会直接失效。
## 这里不 import，让 `renpy` 保持 exports 别名（同 web_boot.rpy 的做法）。

init python:

    class WebQuit(Action):
        """网页版安全退出。confirm=True 时先弹一次确认（复用已有翻译
        「确定退出游戏？」）；确认后（或 confirm=False）toast + 回标题。"""

        def __init__(self, confirm=False):
            self.confirm = confirm

        def __call__(self):

            # 桌面版：标准退出行为不变。
            if not renpy.emscripten:
                renpy.quit(save=True)
                return

            if self.confirm:
                try:
                    if not renpy.confirm(_("确定退出游戏？")):
                        return
                except Exception:
                    pass          # 确认框本身出问题也别卡死，直接继续退

            # toast 走 robust.rpy 的 cs_toast（网页版=window.ChaoshiToast）。
            # 拿不到也无所谓，full_restart 本身已经是可见的反馈。
            try:
                cs_toast("已退出，回到标题画面…", "info", 2500)
            except Exception:
                pass

            renpy.full_restart()
