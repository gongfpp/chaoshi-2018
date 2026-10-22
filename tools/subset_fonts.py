#!/usr/bin/env python3
"""把随游戏打包的 CJK 字库裁成「只含游戏实际用到字符」的子集。

背景：网页版初始下载慢，主要不是资源本身，而是三份 Noto CJK 全字库
（12 + 11.6 + 8.3 = 32 MB）被塞进了 game.zip —— 占整个包体积的 94%。
游戏文本是固定的，没有玩家输入，因此按字符集裁剪是无损的。

    python3 tools/subset_fonts.py            # 就地替换 game/game/*.otf
    python3 tools/subset_fonts.py --dry-run  # 只统计字符数与预估
    python3 tools/subset_fonts.py --check    # 只检查「现用字库缺哪些字」

**裁剪是不可逆的**：子集里没有的字形补不回来。所以原字库（约 8.3 / 11.6 MB）
留在 `assets-src/fonts/`（已 gitignore），脚本优先从那里取源；只有在
`assets-src/fonts/` 缺文件时才退回 `game/game/` —— 这时会在包头打印警告，
意味着这一次只能在已有子集上再裁，不能新增字形。

重新获取原文（SIL OFL 1.1）：

    https://raw.githubusercontent.com/notofonts/noto-cjk/main/Sans/SubsetOTF/SC/NotoSansSC-Regular.otf
    https://raw.githubusercontent.com/notofonts/noto-cjk/main/Serif/SubsetOTF/SC/NotoSerifSC-Regular.otf
"""

import glob
import os
import sys

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "game", "game")
SRC_DIR = os.path.join(ROOT, "assets-src", "fonts")

# 未被任何 .rpy 引用的字重，直接删除，不占体积
DROP = ["NotoSerifSC-Bold.otf"]
KEEP = ["NotoSerifSC-Regular.otf", "NotoSansSC-Regular.otf"]

TEXT_GLOBS = [
    "novel/chapters/*.md",
    "novel/endings/*.md",
    "game/branches/*.md",
    "game/game/*.rpy",
    "game/game/gen/*.rpy",
]

# 数字、拉丁、中文标点、全角符号——界面里的「第 3 章」「60%」「——」等都要用
SAFETY = (
    "0123456789"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
    " !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~"
    "，。、；：？！“”‘’「」『』（）《》〈〉【】〔〕—…·％＃＠＆＊＋－／＜＞＝～　"
    "０１２３４５６７８９"
    "×÷±°℃№→←↑↓■□●○◆◇★☆"
    # 快进指示符（原为 ▸，Noto CJK 无此码位，已改用 ›）
    "›»▶"
    "年月日时分秒第章节结束存档读档设置历史自动快进返回标题退出开始继续"
    # 章节卡片、存读档、设置页会用到的词（生成式 UI 的固定文案）
    "章节目录重新开始放弃进度继续游戏"
)


def collect_chars():
    chars = set(SAFETY)
    files = []
    for g in TEXT_GLOBS:
        files.extend(glob.glob(os.path.join(ROOT, g)))
    for path in files:
        with open(path, encoding="utf-8") as f:
            chars.update(f.read())
    # 去掉控制字符与 BOM
    return {c for c in chars if ord(c) >= 0x20 and c != "\ufeff"}


def source_for(name):
    """返回 (源文件路径, 是否已裁剪过)。"""
    full = os.path.join(SRC_DIR, name)
    if os.path.exists(full):
        return full, False
    live = os.path.join(FONT_DIR, name)
    if os.path.exists(live):
        return live, True
    return None, False


def missing_in(path, chars):
    cmap = TTFont(path).getBestCmap()
    return sorted(c for c in chars if ord(c) not in cmap)


def check(chars):
    bad = 0
    for name in KEEP:
        p = os.path.join(FONT_DIR, name)
        if not os.path.exists(p):
            print("缺少 %s" % name)
            bad += 1
            continue
        miss = missing_in(p, chars)
        if miss:
            bad += 1
            print("%-28s 缺 %d 字：%s" % (name, len(miss), "".join(miss[:60])))
        else:
            print("%-28s 覆盖完整（%.0f KB）" % (name, os.path.getsize(p) / 1024))
    return bad


def main():
    dry = "--dry-run" in sys.argv
    if "--check" in sys.argv:
        chars = collect_chars()
        print("字符集：%d 个" % len(chars))
        sys.exit(1 if check(chars) else 0)

    chars = collect_chars()
    text = "".join(sorted(chars))
    hanzi = sum(1 for c in chars if "\u4e00" <= c <= "\u9fff")
    print("字符集：%d 个（汉字 %d，其余 %d）" % (len(chars), hanzi, len(chars) - hanzi))

    for name in DROP:
        p = os.path.join(FONT_DIR, name)
        if os.path.exists(p):
            print("删除未引用字重：%s（%.1f MB）" % (name, os.path.getsize(p) / 1e6))
            if not dry:
                os.remove(p)

    for name in KEEP:
        src, already = source_for(name)
        if not src:
            print("跳过（源与产物都不存在）：%s" % name)
            continue
        if already:
            print("!! 警告：%s 只有已裁剪版可用，本次无法新增字形（见文件头说明）" % name)

        before = os.path.getsize(src)
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.name_legacy = True
        opts.notdef_outline = True
        opts.recalc_bounds = True
        opts.drop_tables += ["DSIG"]
        font = subset.load_font(src, opts)
        sub = subset.Subsetter(options=opts)
        sub.populate(text=text)
        sub.subset(font)
        out = os.path.join(FONT_DIR, name + ".subset")
        subset.save_font(font, out, opts)
        after = os.path.getsize(out)
        print("%-28s %6.2f MB → %5.2f MB（%.1f%%）%s" % (
            name, before / 1e6, after / 1e6, 100.0 * after / before,
            "" if already else "  源：assets-src/fonts"))
        if dry:
            os.remove(out)
        else:
            os.replace(out, os.path.join(FONT_DIR, name))
            miss = missing_in(os.path.join(FONT_DIR, name), chars)
            if miss:
                raise SystemExit("裁剪后仍缺 %d 字：%s" % (len(miss), "".join(miss[:60])))


if __name__ == "__main__":
    main()
