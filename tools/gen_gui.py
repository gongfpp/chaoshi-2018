#!/usr/bin/env python3
"""生成《超时》的界面图形资源（无第三方素材，全部程序化绘制）。"""
import os
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1280, 720
GUI = os.path.join(os.path.dirname(__file__), "..", "game", "game", "gui")
FONT_SANS = os.path.join(os.path.dirname(__file__), "..", "game", "game", "NotoSansSC-Regular.otf")
FONT_SERIF = os.path.join(os.path.dirname(__file__), "..", "game", "game", "NotoSerifSC-Regular.otf")

INK = (10, 12, 15)
PANEL = (18, 22, 27)
TEXT = (232, 228, 220)
AMBER = (199, 154, 75)
GREY = (138, 143, 150)


def rgba(c, a):
    return (c[0], c[1], c[2], a)


def gradient_v(size, top, bottom):
    w, h = size
    img = Image.new("RGBA", size)
    d = ImageDraw.Draw(img)
    for y in range(h):
        t = y / max(1, h - 1)
        col = tuple(int(top[i] + (bottom[i] - top[i]) * t) for i in range(4))
        d.line([(0, y), (w, y)], fill=col)
    return img


def grain(img, amount=6):
    import random
    random.seed(7)
    px = img.load()
    w, h = img.size
    for _ in range(w * h // 14):
        x = random.randrange(w)
        y = random.randrange(h)
        r, g, b, a = px[x, y]
        k = random.randint(-amount, amount)
        px[x, y] = (max(0, min(255, r + k)), max(0, min(255, g + k)), max(0, min(255, b + k)), a)
    return img


def make_textbox():
    """底部对白区：先快速变暗，再渐变到底，保证中段文字有足够对比度。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    top = H - 300
    for y in range(top, H):
        t = (y - top) / 300.0
        if t < 0.30:
            a = int(185 * (t / 0.30) ** 0.6)
        else:
            a = int(185 + 60 * ((t - 0.30) / 0.70) ** 0.7)
        d.line([(0, y), (W, y)], fill=(9, 11, 14, min(252, a)))
    d.line([(90, top + 4), (W - 90, top + 4)], fill=rgba(AMBER, 55), width=1)
    d.line([(90, H - 56), (W - 90, H - 56)], fill=rgba(TEXT, 16), width=1)
    img.save(os.path.join(GUI, "textbox.png"))


def rounded(size, radius, fill, outline=None, width=1):
    img = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, size[0] - 1, size[1] - 1], radius=radius, fill=fill,
                        outline=outline, width=width)
    return img


def make_namebox():
    img = rounded((420, 62), 3, rgba(PANEL, 235), rgba(AMBER, 110), 1)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 4, 61], fill=rgba(AMBER, 220))
    img.save(os.path.join(GUI, "namebox.png"))


def make_frame():
    img = rounded((300, 200), 4, rgba(PANEL, 242), rgba(TEXT, 26), 1)
    img.save(os.path.join(GUI, "frame.png"))
    img2 = rounded((300, 200), 4, (8, 10, 12, 246), rgba(AMBER, 90), 1)
    img2.save(os.path.join(GUI, "confirm_frame.png"))


def make_choice():
    idle = Image.new("RGBA", (760, 74), (0, 0, 0, 0))
    d = ImageDraw.Draw(idle)
    d.rectangle([0, 0, 759, 73], fill=rgba(PANEL, 200))
    d.rectangle([0, 0, 3, 73], fill=rgba(AMBER, 90))
    idle.save(os.path.join(GUI, "button", "choice_idle_background.png"))
    hov = Image.new("RGBA", (760, 74), (0, 0, 0, 0))
    d = ImageDraw.Draw(hov)
    d.rectangle([0, 0, 759, 73], fill=rgba((32, 38, 44), 235))
    d.rectangle([0, 0, 3, 73], fill=rgba(AMBER, 255))
    d.rectangle([0, 0, 759, 73], outline=rgba(AMBER, 120), width=1)
    hov.save(os.path.join(GUI, "button", "choice_hover_background.png"))


def city_silhouette(d, w, h, base_y, color, seed=3):
    import random
    random.seed(seed)
    x = -20
    while x < w + 20:
        bw = random.randint(40, 110)
        bh = random.randint(60, 230)
        top = base_y - bh
        d.rectangle([x, top, x + bw, base_y], fill=color)
        # 窗户
        for wy in range(top + 14, base_y - 10, 18):
            for wx in range(x + 8, x + bw - 8, 14):
                if random.random() < 0.28:
                    d.rectangle([wx, wy, wx + 4, wy + 6], fill=rgba((214, 176, 108), random.randint(30, 110)))
        x += bw + random.randint(4, 16)


def make_main_menu():
    img = gradient_v((W, H), (12, 15, 19, 255), (28, 33, 38, 255))
    d = ImageDraw.Draw(img)
    d.ellipse([-200, -260, 620, 380], fill=(38, 46, 52, 90))
    city_silhouette(d, W, H, H - 120, (16, 20, 24, 255))
    city_silhouette(d, W, H, H - 60, (10, 13, 16, 255), seed=11)
    img = grain(img, 4)
    img.save(os.path.join(GUI, "main_menu.png"))


def make_game_menu():
    img = gradient_v((W, H), (13, 16, 20, 252), (22, 26, 31, 252))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 6, H], fill=rgba(AMBER, 40))
    img.save(os.path.join(GUI, "game_menu.png"))


def make_overlays():
    ov = Image.new("RGBA", (W, H), rgba((6, 8, 10), 120))
    ov.save(os.path.join(GUI, "overlay", "main_menu.png"))
    ov2 = Image.new("RGBA", (W, H), rgba((6, 8, 10), 96))
    ov2.save(os.path.join(GUI, "overlay", "game_menu.png"))
    ov3 = Image.new("RGBA", (W, H), rgba((4, 6, 8), 170))
    ov3.save(os.path.join(GUI, "overlay", "confirm.png"))


def make_bubbles():
    for name, tail in (("bubble.png", True), ("thoughtbubble.png", False)):
        img = rounded((420, 240), 18, (240, 237, 230, 245), (0, 0, 0, 0))
        if tail:
            d = ImageDraw.Draw(img)
            d.polygon([(60, 238), (96, 238), (70, 268)], fill=(240, 237, 230, 245))
        img.save(os.path.join(GUI, name))


def make_icon():
    img = Image.new("RGBA", (256, 256), rgba((14, 17, 21), 255))
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 255, 255], outline=rgba(AMBER, 180), width=3)
    try:
        f = ImageFont.truetype(FONT_SERIF, 150)
    except Exception:
        f = ImageFont.load_default()
    txt = "超"
    box = d.textbbox((0, 0), txt, font=f)
    tw, th = box[2] - box[0], box[3] - box[1]
    d.text(((256 - tw) / 2 - box[0], (256 - th) / 2 - box[1]), txt, font=f, fill=rgba(AMBER, 240))
    img.save(os.path.join(GUI, "window_icon.png"))


if __name__ == "__main__":
    os.makedirs(os.path.join(GUI, "button"), exist_ok=True)
    os.makedirs(os.path.join(GUI, "overlay"), exist_ok=True)
    make_textbox()
    make_namebox()
    make_frame()
    make_choice()
    make_main_menu()
    make_game_menu()
    make_overlays()
    make_bubbles()
    make_icon()
    print("GUI images generated in", GUI)
