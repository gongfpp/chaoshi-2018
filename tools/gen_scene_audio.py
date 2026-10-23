#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""场景音效层：环境底噪、一次性音效、广播播报。

与 gen_audio.py 的分工：
  gen_audio.py  —— BGM 与少量旧音效（长循环、立体声、q2）
  本脚本        —— 环境层（amb/）、事件音效（sfx/）、播报（pa/）

全部素材自行合成，不引用任何第三方音频：
  环境层用「共振峰说话人」叠加 + 碰撞建模；播报用系统 TTS 生成后做
  喇叭频响（320–3600 Hz 带通）、轻度饱和、短混响，模拟店内广播。

体量与体积的权衡：
  环境层是底噪，上限只到 11 kHz，所以 22.05 kHz 单声道足够；
  24 秒无缝循环，q1，单文件约 60–90 KB。
"""
import os
import sys
import subprocess

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_audio import (  # noqa: E402
    SR, ROOT, OUT, TMP, white, pink, brown, bandpass, lowpass, hi_pass,
    env_ad, tone, reverb, place, normalize, seamless, n_samples,
)

AMB_SR = 22050
rng = np.random.default_rng(20180920)


# ---------------------------------------------------------------- 基础写法

def rms_norm(x, target, peak_limit=0.80):
    """按 RMS 归一，再做峰值限制。

    环境层必须用 RMS 而不是峰值：峰值归一会让"事件密度高"的场景（站点、
    客运站）听起来比"只有风"的场景响一倍，玩家会觉得音量在乱跳。
    实录混音里这一层叫「统一底噪电平」，吵不吵由密度和频谱决定。
    """
    r = np.sqrt((x ** 2).mean()) + 1e-9
    y = x * (target / r)
    m = float(np.abs(y).max())
    if m > peak_limit:
        y = y * (peak_limit / m)
    return y.astype(np.float32)


def write(name, sig, folder, sr=22050, q=None, bitrate=None, peak=0.5,
          rms=None, loop=False, fade=1.2, width=0.0):
    """统一落盘：OGG。

    两个坑：
    1. ffmpeg 自带的 vorbis 编码器只支持双声道，单声道信号在这里复制成两路。
       环境层给右声道 6 ms 延迟做去相关（听起来有宽度），事件音和播报保持
       两路一致（点声源不该被拉宽）。
    2. 不再写临时 wav 再删 —— 批量 os.remove 会触发沙盒的删除保护。PCM 直接
       通过 stdin 管道喂给 ffmpeg。
    """
    sig = np.asarray(sig, dtype=np.float32)
    if loop:
        sig = seamless(sig, fade)
    else:
        k = min(len(sig), int(0.003 * SR))
        if k > 4:
            sig[-k:] *= np.linspace(1, 0, k).astype(np.float32)
    if rms:
        sig = rms_norm(sig, rms)
    else:
        sig = normalize(sig, peak)
    d = int(width * SR)
    if d > 0:
        right = np.concatenate([np.zeros(d, dtype=np.float32), sig[:-d]]) * 0.94
        right[:d] = sig[:d]
    else:
        right = sig
    stereo = np.stack([sig, right], axis=1)
    pcm = (np.clip(stereo, -1, 1) * 32767).astype("<i2").tobytes()

    dst = os.path.join(OUT, folder, name + ".ogg")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    cmd = ["ffmpeg", "-y", "-loglevel", "error",
           "-f", "s16le", "-ar", str(SR), "-ac", "2", "-i", "-",
           "-ar", str(sr), "-c:a", "vorbis", "-strict", "-2"]
    if bitrate:
        cmd += ["-b:a", str(bitrate)]
    else:
        cmd += ["-q:a", str(2 if q is None else q)]
    cmd.append(dst)
    subprocess.run(cmd, input=pcm, check=True)
    return os.path.getsize(dst)


# ---------------------------------------------------------------- 人声嘈杂
#
# 真人说话无法合成，但「听不清内容的人声嘈杂」可以：
# 用锯齿波做声门源，过三组共振峰带通，再叠音节包络。
# 关键不是像某个人，而是「有音高起伏、有换气、彼此错开」。

def voice(dur, f0, seed, gain=1.0, syllable=(0.07, 0.22)):
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    if n < 64:
        return np.zeros(n, dtype=np.float32)
    src = tone(f0, dur, amp=1.0,
               harm=(1.0, 0.65, 0.45, 0.28, 0.18, 0.12, 0.08, 0.05),
               detune=0.004, vibrato=0.012)
    body = (bandpass(src, 280, 780) * 1.0
            + bandpass(src, 900, 2100) * 0.55
            + bandpass(src, 2300, 3600) * 0.20)
    env = np.zeros(n, dtype=np.float32)
    t = r.uniform(0, 0.3)
    while t < dur - 0.25:
        d = r.uniform(*syllable)
        m = n_samples(d)
        i = int(t * SR)
        if m < 16 or i >= n:
            break
        e = np.sin(np.linspace(0, np.pi, m)) ** 0.6
        j = min(n, i + m)
        env[i:j] += e[: j - i].astype(np.float32)
        t += d + r.uniform(0.015, 0.10)
        # 句读：句子之间停一下，这是「像说话」的关键
        if r.random() < 0.18:
            t += r.uniform(0.20, 0.75)
    return (body * env).astype(np.float32) * gain


def crowd(dur, count, seed, lo=100, hi=240, gain=(0.006, 0.018)):
    """count 个互不同步的说话人。"""
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    out = np.zeros(n, dtype=np.float32)
    for i in range(count):
        g = r.uniform(*gain)
        v = voice(dur, r.uniform(lo, hi), seed + i * 131, g)
        out[: len(v)] += v
    return out


# ---------------------------------------------------------------- 具体声源

def clink(dur=0.4, f=2400, seed=0, glass=False):
    """瓷碗/玻璃杯碰撞：瞬态 + 几个非谐分音余韵。"""
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    t = np.arange(n) / SR
    sig = bandpass(white(n), 1500, 9000) * np.exp(-t * (70 if glass else 95)) * 0.55
    ratios = [1.0, 1.51, 2.34, 3.11] if not glass else [1.0, 2.05, 3.17, 4.42]
    for k, ratio in enumerate(ratios):
        decay = (10 + k * 5) if glass else (20 + k * 7)
        sig += (np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * decay)
                * (0.34 / (k + 1))).astype(np.float32)
    return sig.astype(np.float32)


def plate_stack(seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(0.9)
    sig = np.zeros(n, dtype=np.float32)
    for k in range(r.integers(3, 6)):
        place(sig, clink(0.5, r.uniform(1600, 3000), int(r.integers(1e6))),
              r.uniform(0, 0.25) + k * 0.06, r.uniform(0.3, 0.7))
    return sig


def chair_scrape(dur=0.6, seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    t = np.arange(n) / SR
    fric = bandpass(white(n), 180, 1600) * np.exp(-t * 3.5)
    env = np.sin(np.linspace(0, np.pi, n)) ** 1.4
    thud = lowpass(brown(n), 120) * np.exp(-t * 24)
    return (fric * env * 0.5 + thud * 0.5).astype(np.float32)


def wok_toss(dur=1.4, seed=0):
    """翻勺：金属摩擦 + 油爆 + 落回锅底的闷响。"""
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    t = np.arange(n) / SR
    fric = bandpass(white(n), 2200, 9000) * np.exp(-((t - 0.18) ** 2) * 60)
    oil = np.zeros(n, dtype=np.float32)
    for _ in range(int(dur * 45)):
        at = r.uniform(0.05, dur * 0.8)
        place(oil, bandpass(white(n_samples(0.02)), 3000, 11000)
              * np.exp(-np.linspace(0, 9, n_samples(0.02))).astype(np.float32),
              at, r.uniform(0.05, 0.20))
    hit = lowpass(brown(n_samples(0.35)), 260) * np.exp(-np.linspace(0, 16, n_samples(0.35)))
    sig = fric * 0.45 + oil * 0.5
    place(sig, hit.astype(np.float32), 0.55, 0.6)
    place(sig, hit.astype(np.float32), 0.78, 0.35)
    return sig


def steamer(dur=24.0, seed=0):
    """蒸笼/开水：宽带嘶声 + 缓慢起伏。"""
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    hiss = bandpass(r.standard_normal(n).astype(np.float32), 900, 9000) * 0.30
    t = np.arange(n) / SR
    mod = 0.75 + 0.25 * np.sin(2 * np.pi * 0.09 * t + 1.2)
    return (hiss * mod).astype(np.float32)


def compressor(dur, seed=0, base=100.0):
    """冰箱/冰柜压缩机：基频 + 谐波 + 低噪。"""
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = tone(base, dur, amp=0.5, harm=(1.0, 0.55, 0.3, 0.15), detune=0.003)
    sig += lowpass(brown(n), 220) * 0.45
    sig += bandpass(white(n), 200, 900) * 0.05
    return sig.astype(np.float32)


def aircon(dur, seed=0):
    """空调外机：风叶斩波（120 Hz 附近）。"""
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    t = np.arange(n) / SR
    air = bandpass(r.standard_normal(n).astype(np.float32), 120, 1800)
    chop = 0.65 + 0.35 * np.sin(2 * np.pi * 47.0 * t)
    return (air * chop * 0.35 + lowpass(brown(n), 160) * 0.30).astype(np.float32)


def wheel_roll(dur=0.9, seed=0):
    """行李箱滚轮：摩擦 + 接缝磕碰。"""
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    t = np.arange(n) / SR
    sig = bandpass(white(n), 120, 900) * 0.35
    for k in range(int(dur / 0.28)):
        at = 0.1 + k * 0.28
        place(sig, (bandpass(white(n_samples(0.05)), 200, 2200)
                    * np.exp(-np.linspace(0, 8, n_samples(0.05)))).astype(np.float32),
              at, 0.5)
    return (sig * np.exp(-((t - dur / 2) ** 2) * 0.6)).astype(np.float32)


def footstep_wet(dur=0.5, seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    t = np.arange(n) / SR
    splash = bandpass(white(n), 700, 7000) * np.exp(-t * 30) * 0.5
    thud = lowpass(brown(n), 200) * np.exp(-t * 18)
    return (splash + thud * 0.8).astype(np.float32)


def cat_meow(seed=0):
    r = np.random.default_rng(seed)
    dur = 0.9
    n = n_samples(dur)
    t = np.arange(n) / SR
    f0 = 480 + 260 * np.sin(np.pi * np.minimum(t / dur, 1.0))
    phase = 2 * np.pi * np.cumsum(f0) / SR
    src = np.sin(phase).astype(np.float32)
    sig = (bandpass(src, 500, 1400) + bandpass(src, 1500, 3200) * 0.5).astype(np.float32)
    return (sig * np.sin(np.linspace(0, np.pi, n)) ** 0.8).astype(np.float32)


def glass_break(dur=1.6, seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(dur)
    t = np.arange(n) / SR
    sig = bandpass(white(n), 2500, 12000) * np.exp(-t * 26) * 0.7
    for _ in range(16):
        place(sig, clink(0.30, r.uniform(2400, 6200), int(r.integers(1e6)), glass=True),
              r.uniform(0, 0.45), r.uniform(0.1, 0.4))
    return sig.astype(np.float32)


def bell(f, dur=1.4, amp=0.4):
    n = n_samples(dur)
    t = np.arange(n) / SR
    sig = np.zeros(n, dtype=np.float32)
    for k, ratio in enumerate([1.0, 2.01, 2.98, 4.16]):
        sig += (np.sin(2 * np.pi * f * ratio * t) * np.exp(-t * (4 + k * 3.2))
                * (0.5 / (k + 1))).astype(np.float32)
    return sig * amp


def beep(f, dur=0.10, amp=0.3):
    s = tone(f, dur, amp=amp, harm=(1.0, 0.25))
    return (s * env_ad(len(s), 0.004, dur * 0.8)).astype(np.float32)


# ---------------------------------------------------------------- 环境层
#
# 每个函数返回 22.05k 单声道信号，由 write(..., loop=True) 做无缝处理。
# 24 秒是为了让「人声换气 + 碗碟随机」不形成可听出的周期。

DUR = 24.0


def amb_foodcourt(seed=201):
    """美食城 / 出餐口：多人低语、碗碟、抽油烟机、远处叫号。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    t = np.arange(n) / SR
    hood = (lowpass(brown(n), 190) * 0.40
            + bandpass(r.standard_normal(n).astype(np.float32), 220, 1500) * 0.075)
    sig = hood * (0.85 + 0.15 * np.sin(2 * np.pi * 0.05 * t))
    sig = sig + crowd(DUR, 11, seed + 1, 100, 245, (0.005, 0.016))
    for _ in range(int(DUR * 1.7)):
        place(sig, clink(r.uniform(0.25, 0.5), r.uniform(1700, 3400),
                         int(r.integers(1e6))),
              r.uniform(0, DUR - 0.6), r.uniform(0.05, 0.15))
    for _ in range(int(DUR * 0.4)):
        place(sig, chair_scrape(r.uniform(0.4, 0.7), int(r.integers(1e6))),
              r.uniform(0, DUR - 1.0), r.uniform(0.04, 0.10))
    for k in range(2):
        at = r.uniform(2.0, DUR - 4.0)
        place(sig, bell(1046, 1.2, 0.35), at, 0.09)
        place(sig, bell(1318, 1.2, 0.35), at + 0.30, 0.09)
    return reverb(sig, 1.8, 0.30)


def amb_restaurant(seed=202):
    """小饭馆堂食：更少的桌、更多炒锅、一台电视。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = (lowpass(brown(n), 200) * 0.35
           + bandpass(r.standard_normal(n).astype(np.float32), 250, 1800) * 0.05)
    sig = sig + crowd(DUR, 5, seed + 2, 105, 215, (0.006, 0.018))
    for _ in range(3):
        place(sig, wok_toss(1.4, int(r.integers(1e6))), r.uniform(0.5, DUR - 2.0),
              r.uniform(0.10, 0.20))
    for _ in range(int(DUR * 1.0)):
        place(sig, clink(r.uniform(0.2, 0.45), r.uniform(1800, 3200),
                         int(r.integers(1e6))), r.uniform(0, DUR - 0.5),
              r.uniform(0.04, 0.12))
    # 隔壁电视
    tv = bandpass(r.standard_normal(n).astype(np.float32), 300, 2000)
    tv *= 0.45 + 0.55 * np.abs(np.sin(2 * np.pi * 0.31 * t_of(n))
                               * np.sin(2 * np.pi * 0.13 * t_of(n)))
    sig = sig + tv * 0.055
    return reverb(sig, 1.5, 0.28)


def t_of(n):
    return np.arange(n) / SR


def amb_breakfast(seed=203):
    """早餐铺：蒸笼、豆浆机、早起的人。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = steamer(DUR, seed + 3) * 0.22
    sig = sig + crowd(DUR, 4, seed + 4, 110, 230, (0.005, 0.015))
    # 豆浆机：马达 3 秒一段
    for k in range(3):
        at = 2.0 + k * 7.5
        d = 2.6
        m = n_samples(d)
        tt = np.arange(m) / SR
        motor = (tone(118, d, amp=0.20, harm=(1.0, 0.6, 0.4, 0.2))
                 * (0.7 + 0.3 * np.sin(2 * np.pi * 26 * tt)))
        motor += bandpass(white(m), 400, 3000) * 0.05
        place(sig, motor.astype(np.float32) * env_ad(m, 0.2, 0.4), at, 0.8)
    for _ in range(int(DUR * 0.8)):
        place(sig, clink(r.uniform(0.2, 0.4), r.uniform(2000, 3600),
                         int(r.integers(1e6))), r.uniform(0, DUR - 0.5),
              r.uniform(0.04, 0.10))
    return reverb(sig, 1.1, 0.22)


def amb_banquet(seed=204):
    """聚餐 / 年会 / 婚宴：碰杯、哄笑、椅子响。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = crowd(DUR, 14, seed + 5, 100, 260, (0.006, 0.020))
    sig = sig + lowpass(brown(n), 180) * 0.22
    for _ in range(int(DUR * 0.9)):
        place(sig, clink(0.6, r.uniform(2600, 5200), int(r.integers(1e6)), glass=True),
              r.uniform(0, DUR - 1.0), r.uniform(0.04, 0.13))
    for _ in range(int(DUR * 0.5)):
        place(sig, chair_scrape(r.uniform(0.4, 0.8), int(r.integers(1e6))),
              r.uniform(0, DUR - 1.0), r.uniform(0.03, 0.09))
    # 哄笑：短促宽带人声爆发
    for _ in range(int(DUR * 0.30)):
        at = r.uniform(0, DUR - 1.5)
        d = r.uniform(0.5, 1.1)
        m = n_samples(d)
        burst = bandpass(white(m), 300, 2600) * 0.32
        burst *= (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * r.uniform(3.2, 5.5)
                                             * np.arange(m) / SR)))
        place(sig, burst.astype(np.float32) * np.sin(np.linspace(0, np.pi, m)) ** 0.7,
              at, r.uniform(0.10, 0.22))
    return reverb(sig, 2.0, 0.34)


def amb_wetmarket(seed=205):
    """菜市场：叫卖、剁肉、塑料袋、地面积水。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = crowd(DUR, 8, seed + 6, 105, 250, (0.006, 0.018))
    sig = sig + lowpass(brown(n), 200) * 0.20
    # 叫卖：一个人反复
    for k in range(6):
        at = 1.5 + k * 4.0 + r.uniform(-0.4, 0.4)
        place(sig, voice(1.6, r.uniform(180, 240), seed + 90 + k, 0.030,
                         (0.12, 0.26)), at, 0.6)
    # 剁肉
    for _ in range(int(DUR * 0.45)):
        at = r.uniform(0, DUR - 0.5)
        d = 0.18
        m = n_samples(d)
        thud = lowpass(brown(m), 260) * np.exp(-np.linspace(0, 22, m))
        place(sig, thud.astype(np.float32), at, r.uniform(0.10, 0.20))
    for _ in range(int(DUR * 1.4)):
        at = r.uniform(0, DUR - 0.4)
        bag = bandpass(white(n_samples(0.22)), 3000, 10000)
        bag *= np.exp(-np.linspace(0, 9, n_samples(0.22)))
        place(sig, bag.astype(np.float32), at, r.uniform(0.03, 0.08))
    return reverb(sig, 1.2, 0.24)


def amb_busstation(seed=206):
    """客运站：混响很长的广播、行李轮、人群。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = crowd(DUR, 9, seed + 7, 100, 240, (0.006, 0.017))
    sig = sig + lowpass(brown(n), 170) * 0.30
    for _ in range(int(DUR * 0.5)):
        place(sig, wheel_roll(r.uniform(0.7, 1.2), int(r.integers(1e6))),
              r.uniform(0, DUR - 1.5), r.uniform(0.04, 0.10))
    # 大空间广播残响：用带通噪声扫频模拟远处播报的「尾音」
    for _ in range(3):
        at = r.uniform(1.0, DUR - 5.0)
        d = 2.4
        m = n_samples(d)
        tail = bandpass(white(m), 400, 2400) * 0.10
        tail *= np.sin(np.linspace(0, np.pi, m)) ** 1.5
        place(sig, tail.astype(np.float32), at, 0.7)
    return reverb(sig, 3.2, 0.42)


def amb_hospital(seed=207):
    """医院走廊：推车、脚步、呼叫铃、荧光灯。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    t = t_of(n)
    sig = (lowpass(brown(n), 180) * 0.26
           + bandpass(r.standard_normal(n).astype(np.float32), 400, 2400) * 0.025)
    sig += tone(100, DUR, amp=0.020, harm=(1.0, 0.5, 0.2))
    # 推车：轮子吱 + 过门槛的咔哒
    for _ in range(3):
        at = r.uniform(0.5, DUR - 5.0)
        d = 3.2
        m = n_samples(d)
        w = bandpass(white(m), 900, 3200) * 0.06
        w *= 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * r.uniform(0.8, 1.6)
                                       * np.arange(m) / SR))
        place(sig, w.astype(np.float32), at, 0.8)
    # 护士站呼叫铃
    for _ in range(5):
        at = r.uniform(1.0, DUR - 3.0)
        for k in range(2):
            place(sig, beep(r.choice([880, 1046, 1318]), 0.14, 0.10), at + k * 0.26, 0.8)
    # 远处脚步
    for _ in range(int(DUR * 0.55)):
        at = r.uniform(0, DUR - 0.6)
        place(sig, footstep_wet(0.35, int(r.integers(1e6))), at, r.uniform(0.03, 0.08))
    return reverb(sig, 2.6, 0.36)


def amb_office(seed=208):
    """办公楼层：键盘、电话、空调、远端讨论。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = (lowpass(brown(n), 190) * 0.26
           + bandpass(r.standard_normal(n).astype(np.float32), 200, 1200) * 0.030)
    sig += tone(100, DUR, amp=0.012, harm=(1.0, 0.3))
    for _ in range(int(DUR * 6)):
        at = r.uniform(0, DUR - 0.1)
        key = bandpass(white(n_samples(0.025)), 1500, 7000)
        key *= np.exp(-np.linspace(0, 8, n_samples(0.025)))
        place(sig, key.astype(np.float32), at, r.uniform(0.02, 0.06))
    for _ in range(2):
        at = r.uniform(1.0, DUR - 4.0)
        ring = np.zeros(n_samples(1.8), dtype=np.float32)
        for k in range(3):
            place(ring, beep(660, 0.20, 0.16), k * 0.55, 1.0)
        place(sig, ring, at, 0.25)
    sig += crowd(DUR, 2, seed + 8, 110, 190, (0.003, 0.008))
    return reverb(sig, 1.2, 0.24)


def amb_street(seed=209, night=False):
    """街面：车流、电动车、远处人声。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = (lowpass(brown(n), 200 if night else 300) * (0.45 if night else 0.55)
           + bandpass(r.standard_normal(n).astype(np.float32), 120, 1200) * 0.10)
    for _ in range(int(DUR / 4.5)):
        at = r.uniform(0, DUR - 5.0)
        d = r.uniform(2.5, 5.0)
        m = n_samples(d)
        car = lowpass(brown(m), r.uniform(280, 800))
        car *= np.exp(-((np.linspace(-1, 1, m)) ** 2) * 2.5)
        place(sig, (car * r.uniform(0.2, 0.5)).astype(np.float32), at, 1.0)
    # 电动车驶过（高频电机啸叫）
    for _ in range(int(DUR / 6)):
        at = r.uniform(0, DUR - 3.0)
        d = 2.2
        m = n_samples(d)
        tt = np.arange(m) / SR
        f = 420 + 160 * np.sin(np.pi * tt / d)
        motor = np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32) * 0.10
        motor *= np.exp(-((np.linspace(-1, 1, m)) ** 2) * 1.6)
        place(sig, motor, at, 0.7)
    sig += crowd(DUR, 3, seed + 9, 110, 230, (0.003, 0.009))
    if not night:
        for _ in range(2):
            at = r.uniform(1.0, DUR - 2.0)
            place(sig, horn_short(int(r.integers(1e6))), at, 0.35)
    return reverb(sig, 1.6, 0.26)


def amb_alley(seed=210):
    """巷子：风、空调外机、水滴、猫。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    t = t_of(n)
    wind = bandpass(r.standard_normal(n).astype(np.float32), 180, 1400) * 0.10
    wind *= 0.55 + 0.45 * np.sin(2 * np.pi * 0.06 * t + 0.7)
    sig = wind + lowpass(brown(n), 150) * 0.18
    for k in range(3):
        at = r.uniform(0.5, DUR - 6.0)
        ac = aircon(4.0, seed + 40 + k)
        place(sig, ac * env_ad(len(ac), 0.6, 0.8), at, 0.40)
    # 空调冷凝水滴
    for _ in range(int(DUR * 0.6)):
        at = r.uniform(0, DUR - 0.3)
        drop = tone(r.uniform(1400, 2600), 0.035, amp=0.10, harm=(1.0,))
        place(sig, drop * env_ad(len(drop), 0.001, 0.03), at, r.uniform(0.3, 0.7))
    place(sig, cat_meow(seed + 61) * 0.16, r.uniform(6.0, DUR - 3.0), 1.0)
    return reverb(sig, 2.4, 0.38)


def amb_riverside(seed=211):
    """河边：水拍岸、船笛、风。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    t = t_of(n)
    water = bandpass(r.standard_normal(n).astype(np.float32), 300, 2600) * 0.12
    water *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.13 * t)
    sig = water + lowpass(brown(n), 140) * 0.22
    for k in range(2):
        at = r.uniform(2.0, DUR - 8.0)
        d = 3.5
        m = n_samples(d)
        tt = np.arange(m) / SR
        f = 180 + 20 * np.sin(2 * np.pi * 0.4 * tt)
        h = np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
        h = lowpass(h, 900) * env_ad(m, 0.8, 1.6) * 0.12
        place(sig, h, at, 1.0)
    return reverb(sig, 3.0, 0.40)


def amb_room(seed=212):
    """出租屋：邻居电视、水管、冰箱。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    t = t_of(n)
    sig = (lowpass(brown(n), 160) * 0.22
           + bandpass(r.standard_normal(n).astype(np.float32), 150, 900) * 0.020)
    tv = bandpass(r.standard_normal(n).astype(np.float32), 300, 2000) * 0.055
    tv *= 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.29 * t) * np.sin(2 * np.pi * 0.11 * t))
    sig += tv
    sig += compressor(DUR, seed + 12, 98) * 0.12
    # 水管：低频闷响 + 水锤
    for _ in range(3):
        at = r.uniform(1.0, DUR - 3.0)
        d = 1.2
        m = n_samples(d)
        pipe = lowpass(brown(m), 120) * 0.10
        pipe *= np.exp(-np.linspace(0, 5, m))
        place(sig, pipe.astype(np.float32), at, 0.8)
    return reverb(sig, 1.3, 0.24)


def amb_ktv(seed=213):
    """KTV 走廊：隔墙鼓点、跑调人声、门开合的漏音。"""
    n = n_samples(DUR)
    t = t_of(n)
    sig = np.zeros(n, dtype=np.float32)
    step = 60 / 96
    pos = 0.0
    while pos < DUR - 1:
        k = tone(52, 0.24, amp=0.30, harm=(1.0, 0.45))
        place(sig, k * env_ad(len(k), 0.002, 0.2, 2.5), pos, 1.0)
        place(sig, lowpass(brown(n_samples(0.06)), 200) * 0.18, pos + step / 2, 1.0)
        pos += step
    sig = lowpass(sig, 380)
    sig += bandpass(white(n), 250, 1600) * 0.035
    sig += crowd(DUR, 3, seed + 13, 180, 300, (0.004, 0.010))
    # 门开合：中频突然变亮
    for _ in range(2):
        at = rng.uniform(2.0, DUR - 4.0)
        d = 0.7
        m = n_samples(d)
        leak = bandpass(white(m), 500, 4000) * 0.10
        place(sig, leak.astype(np.float32) * np.sin(np.linspace(0, np.pi, m)), at, 0.8)
    return reverb(sig, 2.2, 0.32)


def amb_depot(seed=214):
    """骑手站点：充电器风扇、提示蜂鸣、门帘、对讲。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = (lowpass(brown(n), 200) * 0.32
           + bandpass(r.standard_normal(n).astype(np.float32), 200, 1000) * 0.045)
    for _ in range(int(DUR * 1.4)):
        at = r.uniform(0, DUR - 0.4)
        place(sig, beep(r.choice([1320, 1560, 1760, 1980]), 0.09, 0.10), at,
              r.uniform(0.3, 0.8))
    sig += crowd(DUR, 4, seed + 14, 105, 220, (0.004, 0.012))
    # 塑料门帘被掀开
    for _ in range(int(DUR * 0.25)):
        at = r.uniform(0, DUR - 0.8)
        d = 0.55
        m = n_samples(d)
        cl = bandpass(white(m), 2200, 9000) * 0.10
        cl *= (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 9 * np.arange(m) / SR)))
        place(sig, cl.astype(np.float32) * np.exp(-np.linspace(0, 5, m)), at, 0.7)
    return reverb(sig, 1.0, 0.20)


def amb_shop(seed=215):
    """小超市 / 便利店：冰柜、收银、门铃。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    sig = compressor(DUR, seed + 15, 100) * 0.16 + lowpass(brown(n), 200) * 0.18
    for _ in range(int(DUR * 0.30)):
        at = r.uniform(0, DUR - 1.5)
        place(sig, door_bell(int(r.integers(1e6))), at, r.uniform(0.12, 0.22))
    for _ in range(int(DUR * 0.25)):
        at = r.uniform(0, DUR - 1.2)
        place(sig, cash_drawer(int(r.integers(1e6))), at, r.uniform(0.10, 0.18))
    sig += crowd(DUR, 2, seed + 16, 110, 200, (0.003, 0.008))
    return reverb(sig, 0.9, 0.18)


def amb_funeral_out(seed=216):
    """殡仪馆外：风、远处唢呐、纸钱、低语。"""
    r = np.random.default_rng(seed)
    n = n_samples(DUR)
    t = t_of(n)
    sig = (bandpass(r.standard_normal(n).astype(np.float32), 200, 1500) * 0.10
           + lowpass(brown(n), 150) * 0.20)
    sig *= 0.7 + 0.3 * np.sin(2 * np.pi * 0.05 * t)
    # 唢呐：锯齿 + 强颤音，只给两句，远场
    for k in range(2):
        at = 2.0 + k * 9.0
        d = 4.0
        m = n_samples(d)
        tt = np.arange(m) / SR
        f = 520 + 40 * np.sin(2 * np.pi * 0.8 * tt) + 12 * np.sin(2 * np.pi * 5.5 * tt)
        src = np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32)
        src = bandpass(src, 400, 3000) * 0.09
        src *= env_ad(m, 0.5, 1.2)
        place(sig, src, at, 1.0)
    sig += crowd(DUR, 3, seed + 17, 100, 180, (0.003, 0.007))
    return reverb(sig, 3.4, 0.46)


AMBIENTS = {
    "foodcourt": lambda: amb_foodcourt(),
    "restaurant": lambda: amb_restaurant(),
    "breakfast": lambda: amb_breakfast(),
    "banquet": lambda: amb_banquet(),
    "wetmarket": lambda: amb_wetmarket(),
    "busstation": lambda: amb_busstation(),
    "hospital": lambda: amb_hospital(),
    "office": lambda: amb_office(),
    "street": lambda: amb_street(209, False),
    "street_night": lambda: amb_street(219, True),
    "alley": lambda: amb_alley(),
    "riverside": lambda: amb_riverside(),
    "room": lambda: amb_room(),
    "ktv": lambda: amb_ktv(),
    "depot": lambda: amb_depot(),
    "shop": lambda: amb_shop(),
    "funeral": lambda: amb_funeral_out(),
}


# ---------------------------------------------------------------- 事件音效

def door_bell(seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(1.2)
    sig = np.zeros(n, dtype=np.float32)
    place(sig, bell(1568, 1.0, 0.30), 0.0, 1.0)
    place(sig, bell(2093, 1.0, 0.22), 0.10, 1.0)
    return sig


def cash_drawer(seed=0):
    n = n_samples(0.9)
    t = np.arange(n) / SR
    sig = bandpass(white(n), 700, 6000) * np.exp(-t * 16) * 0.35
    place(sig, lowpass(brown(n_samples(0.25)), 300)
          * np.exp(-np.linspace(0, 14, n_samples(0.25))).astype(np.float32), 0.02, 0.9)
    place(sig, (bandpass(white(n_samples(0.08)), 1500, 8000)
                * np.exp(-np.linspace(0, 10, n_samples(0.08)))).astype(np.float32),
          0.42, 0.6)
    return sig


def coin_drop(seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(1.4)
    sig = np.zeros(n, dtype=np.float32)
    for k in range(3):
        place(sig, clink(0.5, r.uniform(3200, 5200), int(r.integers(1e6)), glass=False),
              k * 0.085 + r.uniform(0, 0.02), 0.5)
    return sig


def phone_ring(seed=0):
    n = n_samples(3.2)
    sig = np.zeros(n, dtype=np.float32)
    # 传统来电铃：两个音交替，0.4 s 一组，响 1.2 s 停 0.8 s
    for grp in range(2):
        base = grp * 2.0
        for k in range(3):
            place(sig, bell(1046, 0.35, 0.22), base + k * 0.28, 1.0)
            place(sig, bell(1318, 0.35, 0.18), base + k * 0.28 + 0.12, 1.0)
    return sig


def phone_vibrate(seed=0):
    n = n_samples(1.5)
    t = np.arange(n) / SR
    motor = tone(72, 1.5, amp=0.5, harm=(1.0, 0.6, 0.3))
    motor += bandpass(white(n), 80, 400) * 0.15
    gate = (np.sin(2 * np.pi * 6.5 * t) > 0).astype(np.float32)
    return (motor * gate).astype(np.float32)


def order_new(seed=0):
    """外卖 App 新单：三音上行，带一点电子味。"""
    n = n_samples(1.5)
    sig = np.zeros(n, dtype=np.float32)
    for k, f in enumerate([1046, 1318, 1568]):
        s = tone(f, 0.22, amp=0.28, harm=(1.0, 0.35, 0.12))
        place(sig, s * env_ad(len(s), 0.004, 0.20), k * 0.11, 1.0)
    place(sig, bell(2093, 1.0, 0.10), 0.34, 1.0)
    return sig


def order_timeout(seed=0):
    """超时预警：急促下行三连，刺耳但不长。"""
    n = n_samples(1.3)
    sig = np.zeros(n, dtype=np.float32)
    for k, f in enumerate([1568, 1318, 1046]):
        s = tone(f, 0.13, amp=0.32, harm=(1.0, 0.5, 0.25))
        place(sig, s * env_ad(len(s), 0.003, 0.11), k * 0.17, 1.0)
    return sig


def app_fail(seed=0):
    n = n_samples(0.9)
    sig = np.zeros(n, dtype=np.float32)
    for k, f in enumerate([740, 554]):
        s = tone(f, 0.26, amp=0.26, harm=(1.0, 0.3))
        place(sig, s * env_ad(len(s), 0.005, 0.24), k * 0.20, 1.0)
    return sig


def scan_ok(seed=0):
    n = n_samples(0.5)
    sig = np.zeros(n, dtype=np.float32)
    place(sig, beep(2093, 0.09, 0.28), 0.0, 1.0)
    place(sig, beep(2637, 0.10, 0.20), 0.11, 1.0)
    return sig


def nav_turn(seed=0):
    n = n_samples(0.7)
    sig = np.zeros(n, dtype=np.float32)
    place(sig, beep(1760, 0.10, 0.22), 0.0, 1.0)
    place(sig, beep(1760, 0.10, 0.16), 0.22, 1.0)
    return sig


def monitor_flat(seed=0):
    """监护仪长音。叙事上这是最安静的瞬间，所以不加混响尾巴。"""
    n = n_samples(4.0)
    t = np.arange(n) / SR
    sig = tone(1000, 4.0, amp=0.18, harm=(1.0, 0.12))
    sig *= env_ad(n, 0.05, 0.6)
    return sig.astype(np.float32)


def heartbeat(seed=0):
    n = n_samples(2.2)
    t = np.arange(n) / SR
    sig = np.zeros(n, dtype=np.float32)
    for k in range(2):
        at = k * 0.92
        th = lowpass(brown(n_samples(0.18)), 90) * np.exp(-np.linspace(0, 12, n_samples(0.18)))
        place(sig, th.astype(np.float32), at, 0.9)
        th2 = lowpass(brown(n_samples(0.16)), 110) * np.exp(-np.linspace(0, 14, n_samples(0.16)))
        place(sig, th2.astype(np.float32), at + 0.28, 0.55)
    return sig


def horn_short(seed=0):
    n = n_samples(0.6)
    t = np.arange(n) / SR
    sig = tone(392, 0.6, amp=0.22, harm=(1.0, 0.5, 0.3))
    sig += tone(494, 0.6, amp=0.16, harm=(1.0, 0.4))
    return (sig * env_ad(n, 0.02, 0.25)).astype(np.float32)


def brake_squeal(seed=0):
    n = n_samples(1.6)
    t = np.arange(n) / SR
    f = 2400 - 700 * np.minimum(t / 1.6, 1.0)
    phase = 2 * np.pi * np.cumsum(f) / SR
    sig = (np.sin(phase) * 0.10 + bandpass(white(n), 2000, 7000) * 0.05)
    return (sig * env_ad(n, 0.05, 1.0)).astype(np.float32)


def bus_door(seed=0):
    n = n_samples(2.2)
    t = np.arange(n) / SR
    hiss = bandpass(white(n), 600, 6000) * np.exp(-((t - 0.5) ** 2) * 4) * 0.22
    thud = lowpass(brown(n_samples(0.4)), 180) * np.exp(-np.linspace(0, 10, n_samples(0.4)))
    sig = hiss.astype(np.float32)
    place(sig, thud.astype(np.float32), 1.4, 0.8)
    return sig


def elevator_ding(seed=0):
    n = n_samples(1.6)
    sig = np.zeros(n, dtype=np.float32)
    place(sig, bell(1046, 1.4, 0.28), 0.0, 1.0)
    return sig


def stamp_thud(seed=0):
    n = n_samples(0.5)
    t = np.arange(n) / SR
    sig = lowpass(brown(n), 400) * np.exp(-t * 30) * 0.5
    sig += bandpass(white(n), 1200, 6000) * np.exp(-t * 60) * 0.2
    return sig.astype(np.float32)


def paper_rustle(seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(1.3)
    sig = np.zeros(n, dtype=np.float32)
    for _ in range(26):
        at = r.uniform(0, 1.1)
        d = r.uniform(0.03, 0.09)
        m = n_samples(d)
        s = bandpass(white(m), 1800, 9000) * np.exp(-np.linspace(0, 7, m)) * 0.18
        place(sig, s.astype(np.float32), at, r.uniform(0.3, 1.0))
    return sig


def pen_sign(seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(1.4)
    t = np.arange(n) / SR
    sig = bandpass(white(n), 2200, 9000) * 0.10
    sig *= (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 5.5 * t)))
    sig *= np.sin(np.linspace(0, np.pi, n)) ** 0.5
    return sig.astype(np.float32)


def keys_jingle(seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(1.1)
    sig = np.zeros(n, dtype=np.float32)
    for _ in range(9):
        place(sig, clink(0.4, r.uniform(3000, 6000), int(r.integers(1e6))),
              r.uniform(0, 0.5), r.uniform(0.10, 0.28))
    return sig


def lighter(seed=0):
    n = n_samples(0.9)
    t = np.arange(n) / SR
    flint = bandpass(white(n), 1500, 8000) * np.exp(-t * 60) * 0.35
    hiss = bandpass(white(n), 400, 3000) * np.exp(-((t - 0.25) ** 2) * 12) * 0.10
    return (flint + hiss).astype(np.float32)


def kettle(seed=0):
    n = n_samples(3.0)
    t = np.arange(n) / SR
    f = 1800 + 60 * np.sin(2 * np.pi * 3.1 * t)
    sig = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.10
    sig += bandpass(white(n), 1500, 8000) * 0.05
    return (sig * env_ad(n, 0.8, 0.6)).astype(np.float32)


def bowl_set(seed=0):
    n = n_samples(0.7)
    sig = np.zeros(n, dtype=np.float32)
    place(sig, clink(0.6, 1900, seed), 0.0, 0.9)
    place(sig, lowpass(brown(n_samples(0.12)), 400)
          * np.exp(-np.linspace(0, 12, n_samples(0.12))).astype(np.float32), 0.01, 0.5)
    return sig


def chopsticks(seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(0.5)
    sig = np.zeros(n, dtype=np.float32)
    for k in range(3):
        place(sig, clink(0.2, r.uniform(2600, 4200), int(r.integers(1e6))),
              k * 0.045, 0.6)
    return sig


def shutter(seed=0):
    """卷帘门：链条 + 金属板滑落的连续咔哒。"""
    r = np.random.default_rng(seed)
    n = n_samples(2.6)
    t = np.arange(n) / SR
    sig = (bandpass(white(n), 300, 4000) * 0.10
           * (0.6 + 0.4 * np.sin(2 * np.pi * 14 * t)))
    for k in range(int(2.4 / 0.12)):
        place(sig, clink(0.12, r.uniform(1200, 2600), int(r.integers(1e6))),
              k * 0.12, r.uniform(0.10, 0.22))
    sig *= np.sin(np.linspace(0, np.pi, n)) ** 0.4
    return sig.astype(np.float32)


def gate_iron(seed=0):
    n = n_samples(1.8)
    t = np.arange(n) / SR
    creak = bandpass(white(n), 300, 2200)
    creak *= (0.5 + 0.5 * np.sin(2 * np.pi * (7 + 4 * t) * t))
    sig = creak.astype(np.float32) * 0.10
    thud = lowpass(brown(n_samples(0.4)), 200) * np.exp(-np.linspace(0, 10, n_samples(0.4)))
    place(sig, thud.astype(np.float32), 1.3, 0.9)
    return sig


def footsteps_wet_run(seed=0):
    r = np.random.default_rng(seed)
    n = n_samples(2.2)
    sig = np.zeros(n, dtype=np.float32)
    at = 0.0
    while at < 1.9:
        place(sig, footstep_wet(0.4, int(r.integers(1e6))), at, r.uniform(0.5, 0.9))
        at += r.uniform(0.28, 0.36)
    return sig




def bag_rustle(seed=0):
    """塑料袋：送餐、菜市场都离不开。高频摩擦，无音高。"""
    r = np.random.default_rng(seed)
    n = n_samples(1.1)
    sig = np.zeros(n, dtype=np.float32)
    for _ in range(30):
        at = r.uniform(0, 0.95)
        d = r.uniform(0.03, 0.08)
        m = n_samples(d)
        s = bandpass(white(m), 2600, 11000) * np.exp(-np.linspace(0, 6, m))
        place(sig, s.astype(np.float32), at, r.uniform(0.2, 1.0))
    sig *= np.sin(np.linspace(0, np.pi, n)) ** 0.4
    return sig.astype(np.float32)


def cup_clink(seed=0):
    """碰杯：两三只玻璃杯撞在一起，余韵比单次 clink 更长。"""
    r = np.random.default_rng(seed)
    n = n_samples(1.4)
    sig = np.zeros(n, dtype=np.float32)
    for k in range(int(r.integers(2, 4))):
        place(sig, clink(0.9, r.uniform(2400, 4200), int(r.integers(1e6)), glass=True),
              k * r.uniform(0.04, 0.09), r.uniform(0.4, 0.8))
    return sig


def bicycle_bell(seed=0):
    """自行车/电动车铃：两声一组，快速重复。"""
    n = n_samples(1.3)
    sig = np.zeros(n, dtype=np.float32)
    for k in range(2):
        for j in range(2):
            at = k * 0.42 + j * 0.075
            place(sig, bell(2650, 0.5, 0.30), at, 1.0)
            place(sig, bell(3320, 0.4, 0.14), at + 0.012, 1.0)
    return sig


def door_knock(seed=0):
    """敲门：三下，间隔不均匀才像人敲的。"""
    n = n_samples(1.5)
    sig = np.zeros(n, dtype=np.float32)
    for k, at in enumerate((0.0, 0.34, 0.68)):
        m = n_samples(0.16)
        th = lowpass(brown(m), 380) * np.exp(-np.linspace(0, 14, m))
        th += bandpass(white(m), 800, 3000) * np.exp(-np.linspace(0, 30, m)) * 0.25
        place(sig, th.astype(np.float32), at, 0.8 - k * 0.12)
    return sig


def impact(seed=0):
    """撞击：低频冲击 + 金属板共振 + 碎屑。用在摔车、争执、门被撞开。"""
    n = n_samples(1.8)
    t = np.arange(n) / SR
    sig = lowpass(brown(n), 190) * np.exp(-t * 9) * 0.9
    for f, a in ((180, 0.25), (430, 0.18), (760, 0.12)):
        sig += (np.sin(2 * np.pi * f * t) * np.exp(-t * 6) * a).astype(np.float32)
    sig += bandpass(white(n), 1500, 8000) * np.exp(-t * 40) * 0.25
    return reverb(sig.astype(np.float32), 1.2, 0.25)


def door_break(seed=0):
    """门被撞开：闷撞 + 木框开裂。比 door_knock 重得多。"""
    n = n_samples(1.4)
    t = np.arange(n) / SR
    sig = lowpass(brown(n), 300) * np.exp(-t * 14) * 0.8
    sig += bandpass(white(n), 700, 5000) * np.exp(-t * 18) * 0.4
    for k in range(3):
        place(sig, clink(0.4, 780 + k * 260, k, glass=False), 0.02 + k * 0.05, 0.28)
    return reverb(sig.astype(np.float32), 1.0, 0.22)

EVENTS = {
    "bowl_set": bowl_set,
    "impact": impact,
    "door_break": door_break,
    "bag_rustle": bag_rustle,
    "cup_clink": cup_clink,
    "bicycle_bell": bicycle_bell,
    "door_knock": door_knock,
    "chopsticks": chopsticks,
    "kettle": kettle,
    "door_bell": door_bell,
    "shutter": shutter,
    "gate_iron": gate_iron,
    "keys": keys_jingle,
    "lighter": lighter,
    "paper": paper_rustle,
    "pen_sign": pen_sign,
    "stamp": stamp_thud,
    "phone_ring": phone_ring,
    "phone_vibrate": phone_vibrate,
    "order_new": order_new,
    "order_timeout": order_timeout,
    "app_fail": app_fail,
    "scan_ok": scan_ok,
    "nav_turn": nav_turn,
    "pay_cash": cash_drawer,
    "coin": coin_drop,
    "monitor_flat": monitor_flat,
    "heartbeat": heartbeat,
    "glass_break": glass_break,
    "horn": horn_short,
    "brake": brake_squeal,
    "bus_door": bus_door,
    "elevator_ding": elevator_ding,
    "footsteps_wet": footsteps_wet_run,
    "plate_stack": plate_stack,
    "wok_toss": wok_toss,
}


# ---------------------------------------------------------------- 广播播报
#
# 系统 TTS（macOS Tingting）→ 喇叭频响 → 饱和 → 店内短混响。
# 这不是原品牌音频的采样，是按「店内广播」的声学特征重新合成的近似音。

PA_VOICE = os.environ.get("PA_VOICE", "Tingting")
PA_RATE = os.environ.get("PA_RATE", "195")

PAS = {
    # 出餐播报（美团/外卖平台）
    "merchant_37": "美团外卖，三十七号订单，请取餐",
    "merchant_52": "美团外卖，五十二号订单，请取餐",
    "merchant_08": "美团外卖，八号订单已出餐",
    "order_new": "您有新的外卖订单，请及时处理",
    "order_late": "您有订单即将超时，请尽快送达",
    # 收款
    "alipay_25": "支付宝到账，二十五元",
    "alipay_6000": "支付宝到账，六千元",
    "wechat_18": "微信收款，十八元",
    "wechat_8": "微信收款，八元",
    # 车站 / 商场 / 医院
    "station_check": "开往宁波方向的旅客，请到三号检票口检票",
    "station_notice": "请旅客看管好随身物品，照顾好老人和小孩",
    "shop_sale": "全场商品第二件半价，欢迎选购",
    "hospital_call": "请家属到护士站",
}


def read_audio(path):
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1",
         "-ar", str(SR), "-"],
        capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype="<f4").astype(np.float32)


def trim(sig, thresh=0.008, pad=0.06):
    idx = np.flatnonzero(np.abs(sig) > thresh)
    if not len(idx):
        return sig
    a = max(0, idx[0] - int(pad * SR))
    b = min(len(sig), idx[-1] + int(pad * SR))
    return sig[a:b]


def broadcast(sig):
    sig = trim(sig)
    sig = normalize(sig, 0.9)
    # 小喇叭：低频砍掉、高频也砍掉，只留语音带
    y = bandpass(sig, 330, 3600)
    # 轻度过载，制造「喇叭被推到头」的毛边
    y = np.tanh(y * 2.4).astype(np.float32)
    y = y / (np.max(np.abs(y)) + 1e-9) * 0.8
    # 店内/站内的短混响
    y = reverb(y.astype(np.float32), 1.1, 0.30)
    # 底噪，避免「真空里的语音」
    y += lowpass(white(len(y)), 5000) * 0.004
    return y.astype(np.float32)


def make_pas():
    total = 0
    # 固定复用同一个临时文件：say 只能写文件，但反复新建再删除会触发
    # 沙盒的批量删除保护（单轮 50 个文件）。
    aiff = os.path.join(TMP, "pa_tts.aiff")
    os.makedirs(TMP, exist_ok=True)
    for name, text in PAS.items():
        subprocess.run(["say", "-v", PA_VOICE, "-r", PA_RATE, "-o", aiff, text],
                       check=True, capture_output=True)
        sig = read_audio(aiff)
        n = write("pa_" + name, broadcast(sig), "pa", sr=22050, q=2,
                  peak=0.60, loop=False)
        total += n
        print("pa   %-16s %6.1f KB" % (name, n / 1024), flush=True)
    return total


# ---------------------------------------------------------------- 入口

def main():
    only = None
    for a in sys.argv[1:]:
        if a.startswith("--only="):
            only = set(a.split("=", 1)[1].split(","))
    for d in ("amb", "sfx", "pa"):
        os.makedirs(os.path.join(OUT, d), exist_ok=True)
    os.makedirs(TMP, exist_ok=True)

    amb_total = 0
    if not only or "amb" in only:
        for name, fn in AMBIENTS.items():
            # q1 ≈ 26 kbps：环境层全是噪声，再高质量也听不出差别，
            # 但这一档是"能听/能省"的分界线（q0 只有 7 kbps，高频全糊）。
            n = write("amb_" + name, fn(), "amb", sr=AMB_SR, q=1,
                      rms=0.105, loop=True, fade=1.2, width=0.006)
            amb_total += n
            print("amb  %-14s %6.1f KB" % (name, n / 1024), flush=True)

    sfx_total = 0
    if not only or "sfx" in only:
        for name, fn in EVENTS.items():
            n = write(name, fn(), "sfx", sr=22050, q=2, peak=0.62, loop=False)
            sfx_total += n
            print("sfx  %-14s %6.1f KB" % (name, n / 1024), flush=True)

    pa_total = 0
    if not only or "pa" in only:
        pa_total = make_pas()

    print("\n合计: amb %.2f MB / sfx %.2f MB / pa %.2f MB" % (
        amb_total / 1048576, sfx_total / 1048576, pa_total / 1048576))


if __name__ == "__main__":
    main()
