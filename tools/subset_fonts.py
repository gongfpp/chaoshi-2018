#!/usr/bin/env python3
"""把随游戏打包的 CJK 字库裁成「只含游戏实际用到字符」的子集。

背景：网页版初始下载慢，主要不是资源本身，而是三份 Noto CJK 全字库
（12 + 11.6 + 8.3 = 32 MB）被塞进了 game.zip —— 占整个包体积的 94%。
游戏文本是固定的，没有玩家输入，因此按字符集裁剪是无损的。

    python3 tools/subset_fonts.py            # 就地替换 game/game/*.otf
    python3 tools/subset_fonts.py --dry-run  # 只统计字符数与预估

裁剪后若新增正文用字，必须重跑一次，否则缺字会显示成方框。
原文可在 https://github.com/notofonts/noto-cjk 重新获取（SIL OFL 1.1）。
"""

import glob
import os
import sys

from fontTools import subset

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "game", "game")
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
    "年月日时分秒第章节结束存档读档设置历史自动快进返回标题退出开始继续"
)


def collect_chars():
    chars = set(SAFETY)
    files = []
    for g in TEXT_GLOBS:
        files.extend(glob.glob(os.path.join(ROOT, g)))
    for path in files:
        with open(path, encoding="utf-8") as f:
            chars.update(f.read())
    # 去掉控制字符
    return {c for c in chars if ord(c) >= 0x20}


def main():
    dry = "--dry-run" in sys.argv
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
        p = os.path.join(FONT_DIR, name)
        if not os.path.exists(p):
            print("跳过（不存在）：%s" % name)
            continue
        before = os.path.getsize(p)
        opts = subset.Options()
        opts.layout_features = ["*"]
        opts.name_IDs = ["*"]
        opts.name_legacy = True
        opts.notdef_outline = True
        opts.recalc_bounds = True
        opts.drop_tables += ["DSIG"]
        font = subset.load_font(p, opts)
        sub = subset.Subsetter(options=opts)
        sub.populate(text=text)
        sub.subset(font)
        out = p + ".subset"
        subset.save_font(font, out, opts)
        after = os.path.getsize(out)
        print("%-28s %6.2f MB → %5.2f MB（%.1f%%）" % (
            name, before / 1e6, after / 1e6, 100.0 * after / before))
        if dry:
            os.remove(out)
        else:
            os.replace(out, p)


if __name__ == "__main__":
    main()
