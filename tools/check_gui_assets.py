#!/usr/bin/env python3
"""静态核对：脚本里引用的 GUI 贴图必须真的存在。

为什么要有它

Ren'Py 的 `Frame("gui/xxx_[prefix]_bar.png")` 是**运行时**解析的：
`[prefix_]` 会按 idle / hover / insensitive 展开再去加载。文件不在，构建
不会报错、lint 也不报错，只有玩家真的点开那个界面时才抛

    Exception: DynamicImage 'gui/phone/scrollbar/vertical_[prefix]_bar.png':
    could not find image.

然后整个画面被异常界面盖住。2026-10 就踩过一次：`screens.rpy` 的
`variant "small"` 段落引用了 `gui/phone/{bar,scrollbar,slider}/`，而项目里
`gui/phone/` 只有 textbox、nvl、button/、overlay/ —— 桌面端一切正常，
手机上开读档/设置/全文就崩。

这条检查把「引用」和「文件」对齐，任何一边漏了都当场失败。

用法：

    python3 tools/check_gui_assets.py            # 检查，失败退出码 1
    python3 tools/check_gui_assets.py --list      # 顺带列出每条引用
"""

import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "game", "game")

# `[prefix_]` 在 Ren'Py 里可能展开成这些前缀
PREFIXES = ["", "idle_", "hover_", "insensitive_", "selected_"]

# 只认字面量路径（gui/… 或 images/… 开头的 png/jpg/webp）
PATH_RE = re.compile(r'["\']((?:gui|images)/[^"\']+?\.(?:png|jpg|jpeg|webp))["\']')

# 这些目录由生成器在构建前产出，缺失不算错（但本项目里 gui/ 是提交进仓库的）
SKIP_PREFIX = ()


def rpy_files():
    for dirpath, dirnames, names in os.walk(GAME):
        dirnames[:] = [d for d in dirnames if d not in ("cache", "saves", "gen", "libs")]
        for n in sorted(names):
            if n.endswith(".rpy"):
                yield os.path.join(dirpath, n)


def expand(path):
    """把 [prefix_] 展开成候选路径；没有占位符就原样返回。"""
    if "[prefix" not in path:
        return [path]
    out = []
    for p in PREFIXES:
        out.append(re.sub(r"\[prefix_?\]", p, path))
    return out


def main():
    show_all = "--list" in sys.argv
    missing = {}
    total = 0

    for f in rpy_files():
        rel = os.path.relpath(f, ROOT).replace(os.sep, "/")
        text = io.open(f, encoding="utf-8", errors="replace").read()
        for lineno, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            for ref in PATH_RE.findall(line):
                total += 1
                cands = expand(ref)
                hits = [c for c in cands
                        if os.path.exists(os.path.join(GAME, c.replace("/", os.sep)))]
                if show_all:
                    print("%-42s %s:%d  %s" % (ref, rel, lineno,
                                               "%d/%d 命中" % (len(hits), len(cands))))
                # 带占位符的至少要有一对（idle + hover）；不带的必须存在
                need = 2 if len(cands) > 1 else 1
                if len(hits) < need:
                    missing.setdefault(ref, []).append("%s:%d（命中 %d/%d）" % (
                        rel, lineno, len(hits), len(cands)))

    if missing:
        print("引用了不存在的 GUI 贴图：")
        for ref, where in sorted(missing.items()):
            print("  %s" % ref)
            for w in where:
                print("    ← %s" % w)
        print("\n共 %d 条引用有问题（总引用 %d 条）。" % (len(missing), total))
        print("修法二选一：把图补进 game/game/，或改掉引用它的 style/define。")
        return 1

    print("GUI 贴图引用检查通过：%d 条引用全部能在 game/game/ 里找到。" % total)
    return 0


if __name__ == "__main__":
    sys.exit(main())
