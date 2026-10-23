## 网页版多出来的两个开关：全屏、静音（桌面版不会出现全屏按钮）。
##
## 为什么全屏必须走 JS
##   Ren'Py 的 Preference("display", "fullscreen") 改的是 SDL 窗口状态。网页版
##   跑在 wasm 里没有窗口可改，调了等于没调 —— Edge / Safari 顶上那条地址栏
##   照样占着，横屏之后画面还是被压掉一截。真正能让它消失的只有浏览器的
##   Fullscreen API，所以这里通过 emscripten 桥去调 tools/web/chaoshi-loader.js
##   里的 window.ChaoshiWebUI。同一条桥 web_boot.rpy 早就在用了
##   （import emscripten; emscripten.run_script）。
##
## 为什么静音用 Ren'Py 自己的
##   renpy/audio.py 的 periodic() 每次混音都读 preferences.mute，所以 set_mute()
##   是实时生效的，不用重启音频。下方菜单栏的按钮、设置页的「全部静音」、
##   左上角 ≡ 菜单里的「静音」共用同一份状态。

init -50 python:

    ## 与 Preference("all mute") 展开出来的混音器清单保持一致
    ## （00preferences.rpy: mixer_names["all"] = get_all_mixers() + ["main"]）。
    ## 四个全哑才算静音：只要还有一个没哑，游戏就还在出声。
    CS_MIXERS = ["music", "sfx", "voice", "main"]

    def chaoshi_is_muted():
        for m in CS_MIXERS:
            if not renpy.game.preferences.get_mute(m):
                return False
        return True

    def chaoshi_set_mute(value):
        for m in CS_MIXERS:
            renpy.game.preferences.set_mute(m, bool(value))
        renpy.restart_interaction()

    def chaoshi_toggle_mute():
        # 网页版 ≡ 菜单也会调这个函数（经 renpy_exec），返回值让 JS 侧
        # 直接把菜单文案改成「静音 / 取消静音」。
        chaoshi_set_mute(not chaoshi_is_muted())
        return chaoshi_is_muted()

    def _cs_js_int(script, default=0):
        """同步问一句 JS，只在网页版有效。

        run_script_int 是 Ren'Py 网页版现成的同步桥（renpy/main.py 的
        choose_variants 就拿它读 screen.width），用它问浏览器状态最省事：
        不需要 JS 往 Python 回写变量，也就不会多出一个会被存进存档的全局量。
        """
        if not renpy.emscripten:
            return default
        try:
            import emscripten
            return int(emscripten.run_script_int(script))
        except Exception:
            return default

    ## 浏览器允不允许进全屏。iOS Safari 的 document.fullscreenEnabled 是
    ## undefined（它只放行 <video> 全屏），这里会得到 False，于是按钮干脆不
    ## 出现 —— 比让玩家点一个没反应的东西强。
    chaoshi_can_fullscreen = bool(_cs_js_int(
        "((document.fullscreenEnabled||document.webkitFullscreenEnabled)?1:0)"))

    def chaoshi_is_fullscreen():
        return bool(_cs_js_int(
            "((document.fullscreenElement||document.webkitFullscreenElement)?1:0)"))

    def chaoshi_toggle_fullscreen():
        if not renpy.emscripten:
            return
        try:
            import emscripten
            emscripten.run_script(
                "try{window.ChaoshiWebUI&&window.ChaoshiWebUI.toggle()}catch(e){}")
        except Exception:
            pass
        # 浏览器要等 Promise 落地才真的进全屏，这里先重画一次让文案跟上；
        # 真正的窗口尺寸变化还会再触发一次重画。
        renpy.restart_interaction()
