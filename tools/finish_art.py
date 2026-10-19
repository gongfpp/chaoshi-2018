#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 ImageGen 产出的原图裁切/羽化，输出游戏用资源。

用法：python tools/finish_art.py bg|char|cg|title <name>
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
RAW = os.path.join(ROOT, "build", "art_raw")
IMG = os.path.join(ROOT, "game", "game", "images")


def crop_169(im):
    w, h = im.size
    target = 16 / 9
    if w / h > target:
        nw = int(h * target)
        x = (w - nw) // 2
        im = im.crop((x, 0, x + nw, h))
    else:
        nh = int(w / target)
        y = (h - nh) // 2
        im = im.crop((0, y, w, y + nh))
    return im.resize((1280, 720), Image.LANCZOS)


def feather_portrait(im, target=(520, 900)):
    w, h = im.size
    # 去掉生成器右下角的水印区域
    im = im.crop((0, 0, w, int(h * 0.945)))
    w, h = im.size
    # 先居中裁成 2:3
    tw, th = 2, 3
    if w / h > tw / th:
        nw = int(h * tw / th)
        im = im.crop(((w - nw) // 2, 0, (w - nw) // 2 + nw, h))
    else:
        nh = int(w * th / tw)
        im = im.crop((0, max(0, int(h * 0.04)), w, max(0, int(h * 0.04)) + nh))
    im = im.convert("RGBA").resize(target, Image.LANCZOS)

    # 生成羽化遮罩：左右与底部柔和过渡，顶部略收
    W, H = target
    mask = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(mask)
    inset_x = int(W * 0.10)
    inset_top = int(H * 0.03)
    inset_bottom = int(H * 0.06)
    d.rectangle([inset_x, inset_top, W - inset_x, H - inset_bottom], fill=255)
    mask = mask.filter(ImageFilter.GaussianBlur(int(W * 0.075)))
    # 顶部渐隐，避免人像背景形成硬边
    top = Image.new("L", (W, H), 0)
    td = ImageDraw.Draw(top)
    for y in range(int(H * 0.22)):
        td.line([(0, y), (W, y)], fill=int(255 * (y / (H * 0.22)) ** 0.9))
    td.rectangle([0, int(H * 0.22), W, H], fill=255)
    from PIL import ImageChops
    mask = ImageChops.multiply(mask, top)
    im.putalpha(mask)
    return im


def latest_raw(name):
    d = os.path.join(RAW, name)
    files = [os.path.join(d, f) for f in os.listdir(d) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
    files.sort(key=os.path.getmtime)
    return files[-1]


def main():
    if len(sys.argv) < 3:
        print("usage: finish_art.py <kind> <name> [src]")
        return
    kind, name = sys.argv[1], sys.argv[2]
    src = sys.argv[3] if len(sys.argv) > 3 else latest_raw(name)
    im = Image.open(src)
    if kind == "bg":
        out = os.path.join(IMG, "bg", name + ".jpg")
        crop_169(im).save(out, quality=90, optimize=True)
    elif kind == "cg":
        out = os.path.join(IMG, "cg", name + ".jpg")
        crop_169(im).save(out, quality=92, optimize=True)
    elif kind == "title":
        out = os.path.join(IMG, "cg", name + ".jpg")
        crop_169(im).save(out, quality=92, optimize=True)
    elif kind == "char":
        out = os.path.join(IMG, "char", name + ".png")
        feather_portrait(im).save(out)
    else:
        raise SystemExit("unknown kind")
    print("wrote", out)


if __name__ == "__main__":
    main()
