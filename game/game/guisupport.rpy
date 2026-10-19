# 仅保留 gui.scale：界面图像由 tools/gen_gui.py 预先生成，运行时不再自动重绘。
init -100 python in gui:

    def scale(n):
        return int(n)
