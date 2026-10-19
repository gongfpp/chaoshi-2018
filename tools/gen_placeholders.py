#!/usr/bin/env python3
"""生成占位图（开发期使用）。正式美术由 ImageGen 产出后覆盖同名文件。"""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ASSETS = os.path.join(ROOT, "game", "game", "images")
FONT = os.path.join(ROOT, "game", "game", "NotoSerifSC-Regular.otf")

BGS = {
    "bg_station_arrival": ("杭州东站 · 出站口", (46, 52, 58), (24, 28, 33)),
    "bg_alley": ("五堡 · 城中村巷", (62, 58, 50), (28, 26, 23)),
    "bg_shop": ("广田车行", (58, 56, 48), (26, 25, 22)),
    "bg_station": ("新塘站 · 站点", (56, 54, 44), (24, 23, 20)),
    "bg_road": ("新塘路 · 白天", (72, 78, 84), (36, 40, 45)),
    "bg_rain": ("雨夜路口", (34, 40, 48), (12, 15, 19)),
    "bg_office": ("调度室", (44, 48, 52), (20, 23, 26)),
    "bg_room": ("出租屋 · 十平米", (58, 50, 42), (24, 21, 18)),
    "bg_cao": ("曹家客厅", (66, 60, 50), (30, 27, 23)),
    "bg_river": ("钱江新城 · 夜", (26, 34, 46), (8, 11, 16)),
    "bg_hospital": ("医院走廊", (66, 74, 76), (30, 34, 36)),
    "bg_funeral": ("殡仪馆 · 冬", (60, 62, 62), (26, 28, 28)),
    "bg_home": ("周口老家 · 院子", (70, 62, 48), (32, 28, 22)),
    "bg_wedding": ("金满楼 · 喜宴", (78, 50, 44), (34, 20, 18)),
    "bg_ktv": ("金座 KTV · 夜", (52, 28, 44), (18, 10, 16)),
    "bg_market": ("彭埠 · 二手电动车市场", (62, 58, 50), (28, 26, 23)),
}

CHARS = {
    "xz_normal": ("杨保祥", (86, 82, 74)),
    "xz_tired": ("杨保祥（疲惫）", (74, 72, 66)),
    "ll_normal": ("刘蕾", (92, 70, 62)),
    "ll_sick": ("刘蕾（病中）", (80, 66, 62)),
    "xf_normal": ("罗小福", (94, 76, 80)),
    "xf_sad": ("罗小福（低落）", (82, 68, 72)),
    "lt_normal": ("刘广田", (78, 72, 62)),
    "lm_normal": ("马长顺", (74, 76, 70)),
    "cy_normal": ("曹明远", (70, 76, 86)),
    "gj_normal": ("高秀兰", (82, 76, 66)),
    "sg_normal": ("孙德胜", (78, 70, 58)),
}

CGS = {
    "cg_bike": "提车那天，江边",
    "cg_hospital": "一月十八，走廊",
    "cg_funeral": "三月二十，火化间外",
    "cg_ending": "守夜之后",
}


def bg(path, cn, top, bottom):
    W, H = 1280, 720
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        c = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(3))
        d.line([(0, y), (W, y)], fill=c)
    try:
        f = ImageFont.truetype(FONT, 34)
        fs = ImageFont.truetype(FONT, 20)
    except Exception:
        f = fs = ImageFont.load_default()
    d.text((60, H - 120), cn, font=f, fill=(230, 226, 218))
    d.text((60, H - 76), "PLACEHOLDER", font=fs, fill=(150, 150, 150))
    img.save(path, quality=88)


def char(path, cn, color):
    W, H = 520, 900
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    cx = W // 2
    d.ellipse([cx - 78, 60, cx + 78, 216], fill=color + (235,))
    d.rounded_rectangle([cx - 150, 210, cx + 150, 640], radius=48, fill=color + (235,))
    d.rounded_rectangle([cx - 140, 600, cx + 140, 880], radius=40, fill=color + (225,))
    try:
        f = ImageFont.truetype(FONT, 26)
    except Exception:
        f = ImageFont.load_default()
    d.text((cx - 60, 300), cn, font=f, fill=(235, 232, 226, 230))
    img.save(path)


def main():
    for sub in ("bg", "char", "cg"):
        os.makedirs(os.path.join(ASSETS, sub), exist_ok=True)
    for name, (cn, top, bottom) in BGS.items():
        bg(os.path.join(ASSETS, "bg", name + ".jpg"), cn, top, bottom)
    for name, (cn, color) in CHARS.items():
        char(os.path.join(ASSETS, "char", name + ".png"), cn, color)
    for name, cn in CGS.items():
        bg(os.path.join(ASSETS, "cg", name + ".jpg"), cn, (40, 42, 46), (14, 16, 18))
    print("placeholders:", len(BGS), len(CHARS), len(CGS))


if __name__ == "__main__":
    main()
