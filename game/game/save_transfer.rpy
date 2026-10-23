# 存档迁移（网页版）
#
# 网页版的存档全在浏览器的 IndexedDB 里（挂载点 /home/web_user/.renpy/<项目名>）。
# 换设备、清缓存、换浏览器都会丢，而且没有任何提示。这里补两个入口：
#   导出 —— 把 *.save 打成 zip，交给浏览器下载；
#   导入 —— 选一个 .chaoshisave，写回存档目录。
#
# 两端靠两条桥联系：
#   Python → JS: `import emscripten; emscripten.run_script(...)`（Ren'Py 官方做法）
#   JS → Python: `window.renpy_exec("...")`（renpy.js 暴露的全局函数）
# 文件本身走 /tmp/cs-import.zip 中转，避免把上百 KB 的 base64 拼进 Python 源码。

init python:

    import os as _cs_os
    import glob as _cs_glob
    import io as _cs_io
    import time as _cs_time
    import base64 as _cs_b64
    import zipfile as _cs_zip

    CS_IMPORT_TMP = "/tmp/cs-import.zip"

    def cs_is_web():
        return bool(getattr(renpy, "emscripten", False))

    def cs_run_js(code):
        """在浏览器里执行一段 JS。桌面版安静地忽略。"""
        if not cs_is_web():
            return False
        try:
            import emscripten
            emscripten.run_script(code)
            return True
        except Exception as e:
            renpy.notify("浏览器脚本执行失败：%s" % e)
            return False

    def cs_export_saves():
        if not cs_is_web():
            renpy.notify("桌面版：存档在 %s，直接复制即可" % renpy.config.savedir)
            return

        try:
            files = sorted(_cs_glob.glob(
                _cs_os.path.join(renpy.config.savedir, "*.save")))
            if not files:
                renpy.notify("还没有存档可以导出")
                return

            buf = _cs_io.BytesIO()
            with _cs_zip.ZipFile(buf, "w", _cs_zip.ZIP_DEFLATED) as z:
                for p in files:
                    z.write(p, _cs_os.path.basename(p))

            b64 = _cs_b64.b64encode(buf.getvalue()).decode("ascii")
            name = "chaoshi-saves-%s.chaoshisave" % _cs_time.strftime("%Y%m%d-%H%M")
            # base64 只含 A-Za-z0-9+/=，可以直接当 JS 字符串字面量
            cs_run_js("ChaoshiSaves.download('%s', '%s');" % (b64, name))
            renpy.notify("已导出 %d 个存档（%.1f KB）" % (
                len(files), len(buf.getvalue()) / 1024.0))
        except Exception as e:
            renpy.notify("导出失败：%s" % e)

    def cs_pick_import():
        if not cs_is_web():
            renpy.notify("桌面版：把 .save 文件放回存档目录即可")
            return
        cs_run_js("ChaoshiSaves.pick();")

    def cs_apply_import():
        """由 JS 在文件落进 /tmp 之后调用。"""
        try:
            if not _cs_os.path.exists(CS_IMPORT_TMP):
                renpy.notify("没有收到文件")
                return

            n_ok = 0
            with _cs_zip.ZipFile(CS_IMPORT_TMP) as z:
                for n in z.namelist():
                    # 只认平铺的 *.save，避免压缩包里的路径穿越
                    if not n.endswith(".save") or "/" in n or "\\" in n:
                        continue
                    dest = _cs_os.path.join(renpy.config.savedir,
                                            _cs_os.path.basename(n))
                    with open(dest, "wb") as f:
                        f.write(z.read(n))
                    n_ok += 1

            try:
                _cs_os.remove(CS_IMPORT_TMP)
            except OSError:
                pass

            if n_ok:
                renpy.notify("已导入 %d 个存档，关掉这页再打开「读档」就能看到" % n_ok)
            else:
                renpy.notify("这个文件里没有存档")
        except Exception as e:
            renpy.notify("导入失败：%s" % e)
        finally:
            renpy.restart_interaction()


screen save_transfer_bar():
    ## 存档 / 读档界面底部的一行，接在翻页按钮下面。只在网页版出现。
    if cs_is_web():
        hbox:
            xalign 0.5
            spacing 18

            textbutton "导出存档":
                action Function(cs_export_saves)
                style "cstrans_button"

            textbutton "导入存档":
                action Function(cs_pick_import)
                style "cstrans_button"


style cstrans_button is button:
    padding (14, 7)
    background "#00000055"
    hover_background "#ffffff22"

style cstrans_button_text is button_text:
    size 22
    color "#bdb6aa"
    hover_color "#f2ede6"
