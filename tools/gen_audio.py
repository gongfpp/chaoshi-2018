#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""程序化生成环境音与配乐（无第三方素材）。

全部素材由本脚本用 NumPy 合成：噪声整形、滤波、正弦簇、包络、卷积混响。
输出 44.1kHz 单声道 OGG（libvorbis q2），可无缝循环。
"""
import os
import sys
import math
import subprocess
import numpy as np

SR = 44100
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "game", "game", "audio")
TMP = os.path.join(ROOT, "build", "audio_tmp")

rng = np.random.default_rng(20180306)


def n_samples(dur):
    return int(dur * SR)


def white(n):
    return rng.standard_normal(n).astype(np.float32)


def pink(n):
    x = white(n)
    X = np.fft.rfft(x)
    f = np.arange(len(X)) + 1.0
    X = X / np.sqrt(f)
    y = np.fft.irfft(X, n)
    return (y / (np.max(np.abs(y)) + 1e-9)).astype(np.float32)


def brown(n):
    x = white(n)
    X = np.fft.rfft(x)
    f = np.arange(len(X)) + 1.0
    X = X / f
    y = np.fft.irfft(X, n)
    return (y / (np.max(np.abs(y)) + 1e-9)).astype(np.float32)


def bandpass(x, lo, hi, slope=1.0):
    n = len(x)
    X = np.fft.rfft(x)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    m = np.ones_like(freqs)
    if lo > 0:
        m *= 1 / (1 + (lo / np.maximum(freqs, 1e-6)) ** (4 * slope))
    if hi > 0:
        m *= 1 / (1 + (freqs / hi) ** (4 * slope))
    return np.fft.irfft(X * m, n).astype(np.float32)


def lowpass(x, hi):
    return bandpass(x, 0, hi)


def hi_pass(x, lo):
    return bandpass(x, lo, 0)


def env_ad(n, a, d, curve=2.0):
    a = max(1, int(a * SR))
    e = np.ones(n, dtype=np.float32)
    a = min(a, n)
    e[:a] = np.linspace(0, 1, a) ** (1 / curve)
    d = min(int(d * SR), n - a)
    if d > 0:
        e[n - d:] *= np.linspace(1, 0, d) ** curve
    return e


def tone(freq, dur, amp=0.2, harm=(1.0, 0.35, 0.12), detune=0.0, vibrato=0.0):
    n = n_samples(dur)
    t = np.arange(n) / SR
    sig = np.zeros(n, dtype=np.float32)
    ph = rng.uniform(0, 6.28, len(harm))
    for i, h in enumerate(harm):
        f = freq * (i + 1) * (1 + detune * (i - 0.5))
        v = 1 + vibrato * np.sin(2 * np.pi * 4.8 * t + ph[i])
        sig += (h * np.sin(2 * np.pi * f * t * v + ph[i])).astype(np.float32)
    sig *= amp / (sum(harm) + 1e-6)
    return sig


def reverb(x, decay=1.6, mix=0.35, pre=0.02):
    """FFT 卷积混响：用指数衰减噪声作脉冲响应。"""
    ir_n = n_samples(decay)
    ir = white(ir_n) * np.exp(-np.arange(ir_n) / (SR * decay / 4.5))
    ir = lowpass(ir, 6000)
    ir[: int(pre * SR)] = 0
    ir /= np.max(np.abs(ir)) + 1e-9
    n = len(x) + ir_n
    X = np.fft.rfft(x, n)
    I = np.fft.rfft(ir, n)
    y = np.fft.irfft(X * I, n)[: len(x)].astype(np.float32)
    y /= np.max(np.abs(y)) + 1e-9
    return ((1 - mix) * x + mix * y).astype(np.float32)


def place(buf, sig, at, gain=1.0):
    i = int(at * SR)
    if i >= len(buf):
        return
    j = min(len(buf), i + len(sig))
    buf[i:j] += sig[: j - i] * gain


def bed(dur, layers):
    n = n_samples(dur)
    out = np.zeros(n, dtype=np.float32)
    for sig, gain in layers:
        if len(sig) < n:
            sig = np.pad(sig, (0, n - len(sig)))
        out += sig[:n] * gain
    return out


def normalize(x, peak=0.72):
    m = np.max(np.abs(x)) + 1e-9
    return (x / m * peak).astype(np.float32)


def seamless(x, fade=1.2):
    """把尾部交叉淡入到头部，得到可循环片段。"""
    f = n_samples(fade)
    if len(x) < 3 * f:
        return x
    head = x[:f].copy()
    tail = x[-f:].copy()
    w = np.linspace(0, 1, f, dtype=np.float32)
    x = x[:-f].copy()
    x[:f] = head * w + tail * (1 - w)
    return x


# ---------- 声音族 ----------

def rain(dur, intensity=1.0, brightness=4200, thunder=False, seed=0):
    n = n_samples(dur)
    r = np.random.default_rng(seed or int(intensity * 1000) + 7)
    base = bandpass(r.standard_normal(n).astype(np.float32), 200, brightness)
    hiss = bandpass(r.standard_normal(n).astype(np.float32), brightness, 12000) * 0.35
    mod = 0.85 + 0.15 * np.sin(2 * np.pi * 0.07 * np.arange(n) / SR)
    sig = (base * mod + hiss) * intensity
    # 雨滴
    drops = np.zeros(n, dtype=np.float32)
    for _ in range(int(dur * 26 * intensity)):
        at = r.uniform(0, dur)
        f = r.uniform(900, 3600)
        d = tone(f, 0.035, amp=r.uniform(0.05, 0.16), harm=(1.0,), detune=r.uniform(-0.1, 0.1))
        place(drops, d * env_ad(len(d), 0.001, 0.03), at, 1.0)
    sig = sig * 0.5 + drops
    if thunder:
        t0 = r.uniform(dur * 0.2, dur * 0.7)
        td = 3.5
        th = lowpass(brown(n_samples(td)) * np.exp(-np.linspace(0, 6, n_samples(td))), 120) * 0.9
        place(sig, th, t0, 1.0)
    return reverb(sig, 1.4, 0.25)


def city(dur, traffic=1.0, night=False, river=False, crowd=0.0, seed=1):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    hum = lowpass(brown(n), 180) * (0.9 if night else 0.55)
    mid = bandpass(r.standard_normal(n).astype(np.float32), 120, 1200) * 0.22
    sig = hum + mid
    # 车流：周期性经过
    passes = int(dur / 6 * traffic) + 1
    for _ in range(passes):
        at = r.uniform(0, dur)
        pd = r.uniform(2.5, 6.0)
        pn = n_samples(pd)
        car = lowpass(brown(pn), r.uniform(300, 900))
        e = np.exp(-((np.linspace(-1, 1, pn)) ** 2) * 3)
        place(sig, (car * e * r.uniform(0.2, 0.55)).astype(np.float32), at)
    if river:
        water = bandpass(r.standard_normal(n).astype(np.float32), 300, 2400) * 0.12
        water *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.11 * np.arange(n) / SR)
        sig += water
    if crowd > 0:
        c = bandpass(r.standard_normal(n).astype(np.float32), 300, 2600)
        c *= 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 0.09 * np.arange(n) / SR + 1))
        sig += c * crowd * 0.35
    if night:
        sig = lowpass(sig, 3000)
    return reverb(sig, 1.8, 0.28)


def room(dur, warm=0.0, tv=False, clock=False, bird=False, seed=2):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = lowpass(brown(n), 220) * 0.35 + bandpass(white(n), 150, 900) * 0.05
    if warm > 0:
        # 温暖的和声垫
        chord = [130.81, 196.00, 261.63, 329.63]
        for i, f in enumerate(chord):
            sig += tone(f, dur, amp=0.06 * warm, harm=(1.0, 0.2, 0.05), detune=0.002,
                        vibrato=0.0015) * 0.6
            sig += tone(f * 1.005, dur, amp=0.05 * warm, harm=(1.0, 0.15), detune=0.003) * 0.4
    if tv:
        # 隔壁电视：带通噪声 + 语调起伏
        t = np.arange(n) / SR
        m = bandpass(white(n), 300, 2000)
        am = 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 0.37 * t) * np.sin(2 * np.pi * 0.11 * t))
        sig += m * am * 0.10
    if clock:
        for k in range(int(dur)):
            tick = tone(1800, 0.02, amp=0.10, harm=(1.0,))
            place(sig, tick * env_ad(len(tick), 0.001, 0.018), k, 1.0)
    if bird:
        for _ in range(int(dur * 1.5)):
            at = r.uniform(0, dur)
            f0 = r.uniform(1800, 3200)
            d = r.uniform(0.06, 0.14)
            b = tone(f0, d, amp=0.09, harm=(1.0, 0.3), vibrato=0.02)
            b *= env_ad(len(b), 0.005, d * 0.8)
            place(sig, b, at, 0.9)
    return reverb(sig, 1.2, 0.22)


def station(dur, busy=0.0, seed=3):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    hum = lowpass(brown(n), 160) * 0.4
    fan = bandpass(white(n), 200, 900) * 0.10
    sig = hum + fan
    # 充电器风扇与提示音
    for _ in range(int(dur * (2 + busy * 6))):
        at = r.uniform(0, dur)
        f = r.choice([1320, 1560, 1760, 1980])
        beep = tone(f, 0.09, amp=r.uniform(0.04, 0.11), harm=(1.0, 0.2))
        beep *= env_ad(len(beep), 0.004, 0.07)
        place(sig, beep, at)
    if busy > 0:
        c = bandpass(white(n), 250, 2400)
        am = 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.13 * np.arange(n) / SR))
        sig += c * am * 0.18 * busy
    return reverb(sig, 1.0, 0.2)


def hospital(dur, tense=0.0, night=True, seed=4):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = lowpass(brown(n), 180) * 0.32 + bandpass(white(n), 400, 2400) * 0.04
    # 荧光灯 100Hz 嗡鸣
    sig += tone(100, dur, amp=0.035, harm=(1.0, 0.5, 0.2)) * 0.6
    # 监护仪
    for _ in range(int(dur / 4)):
        at = r.uniform(0, dur)
        for k in range(r.integers(1, 3)):
            beep = tone(r.choice([880, 990, 1046]), 0.12, amp=0.07, harm=(1.0,))
            beep *= env_ad(len(beep), 0.004, 0.10)
            place(sig, beep, at + k * 0.22)
    if tense > 0:
        sig += tone(55, dur, amp=0.10 * tense, harm=(1.0, 0.6, 0.3), vibrato=0.004)
        pulse = (np.sin(2 * np.pi * 1.15 * np.arange(n) / SR) > 0.6).astype(np.float32)
        sig += lowpass(white(n), 90) * pulse * 0.12 * tense
    if night:
        sig = lowpass(sig, 5000)
    return reverb(sig, 2.2, 0.32)


def drone(dur, base=55, tense=0.5, beat=0.0, seed=5):
    n = n_samples(dur)
    sig = tone(base, dur, amp=0.18, harm=(1.0, 0.5, 0.25, 0.12), detune=0.001, vibrato=0.002)
    sig += tone(base * 1.5, dur, amp=0.07, harm=(1.0, 0.3), detune=0.004)
    sig += lowpass(brown(n), 120) * 0.12
    if beat > 0:
        t = np.arange(n) / SR
        env = (np.sin(2 * np.pi * 0.55 * t) * 0.5 + 0.5) ** 4
        sig += lowpass(white(n), 70) * env * 0.35 * beat
    if tense > 0:
        sig += bandpass(white(n), 1800, 5200) * 0.02 * tense
    return reverb(sig, 2.6, 0.4)


def funeral(dur, winter=False, seed=6):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = tone(73.42, dur, amp=0.16, harm=(1.0, 0.5, 0.25), detune=0.002, vibrato=0.002)
    sig += lowpass(brown(n), 150) * 0.2
    wind = bandpass(white(n), 200, 1400) * 0.06
    wind *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.06 * np.arange(n) / SR)
    sig += wind
    if winter:
        sig += bandpass(white(n), 3000, 8000) * 0.02
    return reverb(sig, 3.0, 0.45)


def wedding(dur, soft=False, seed=7):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = np.zeros(n, dtype=np.float32)
    # 五声音阶，缓慢拨弦
    scale = [261.63, 293.66, 329.63, 392.00, 440.00, 523.25]
    t = 0.0
    while t < dur - 1:
        f = r.choice(scale)
        d = r.uniform(0.5, 1.2)
        s = tone(f, d, amp=0.09 if not soft else 0.05, harm=(1.0, 0.25, 0.08), detune=0.001)
        s *= env_ad(len(s), 0.008, d * 0.9)
        place(sig, s, t, 0.8)
        t += r.uniform(0.45, 1.1)
    sig += lowpass(brown(n), 200) * 0.12
    if not soft:
        c = bandpass(white(n), 300, 2400) * 0.06
        sig += c * (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.08 * np.arange(n) / SR)))
        for _ in range(int(dur / 8)):
            at = r.uniform(0, dur)
            cl = bandpass(white(n_samples(0.25)), 2500, 9000) * np.exp(-np.linspace(0, 10, n_samples(0.25)))
            place(sig, cl.astype(np.float32), at, 0.12)
    return reverb(sig, 2.0, 0.35 if soft else 0.3)


def market(dur, seed=8):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = bandpass(white(n), 200, 3000) * 0.12
    sig *= 0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 0.07 * np.arange(n) / SR))
    for _ in range(int(dur * 2)):
        at = r.uniform(0, dur)
        cl = bandpass(white(n_samples(0.2)), 2000, 9000) * np.exp(-np.linspace(0, 9, n_samples(0.2)))
        place(sig, cl.astype(np.float32), at, 0.08)
    sig += lowpass(brown(n), 200) * 0.25
    return reverb(sig, 1.2, 0.22)


def ktv(dur, seed=9):
    n = n_samples(dur)
    sig = np.zeros(n, dtype=np.float32)
    # 隔墙的低频鼓点
    bpm = 96
    step = 60 / bpm
    t = 0.0
    while t < dur - 1:
        k = tone(52, 0.22, amp=0.32, harm=(1.0, 0.4))
        k *= env_ad(len(k), 0.002, 0.2, 2.5)
        place(sig, k, t, 1.0)
        place(sig, lowpass(brown(n_samples(0.06)), 200) * 0.2, t + step / 2, 1.0)
        t += step
    hum = lowpass(brown(n), 120) * 0.2
    sig = lowpass(sig + hum, 400)
    return reverb(sig, 2.4, 0.3)


def train(dur, night=False, seed=10):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = lowpass(brown(n), 260) * 0.5
    # 车轨节奏
    period = 0.93
    t = 0.0
    while t < dur - 1:
        th = lowpass(white(n_samples(0.09)), 300) * np.exp(-np.linspace(0, 8, n_samples(0.09)))
        place(sig, th.astype(np.float32), t, 0.35)
        place(sig, th.astype(np.float32), t + 0.16, 0.22)
        t += period
    sig += bandpass(white(n), 300, 1800) * 0.06
    if night:
        sig = lowpass(sig, 2500)
    return reverb(sig, 1.4, 0.25)


def shop(dur, radio=False, seed=11):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = lowpass(brown(n), 200) * 0.3 + bandpass(white(n), 200, 1200) * 0.05
    if radio:
        # 老式收音机：中频噪声 + 缓慢调制
        t = np.arange(n) / SR
        am = bandpass(white(n), 400, 2600) * 0.09
        am *= (0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.13 * t)))
        sig += am
        sig += tone(1200, dur, amp=0.006, harm=(1.0,))
    for _ in range(int(dur * 0.8)):
        at = r.uniform(0, dur)
        cl = bandpass(white(n_samples(0.18)), 1800, 7000) * np.exp(-np.linspace(0, 10, n_samples(0.18)))
        place(sig, cl.astype(np.float32), at, 0.06)
    return reverb(sig, 1.0, 0.2)


def rural(dur, seed=12):
    n = n_samples(dur)
    r = np.random.default_rng(seed)
    sig = bandpass(white(n), 150, 1600) * 0.10
    sig *= 0.5 + 0.5 * np.sin(2 * np.pi * 0.05 * np.arange(n) / SR)
    sig += lowpass(brown(n), 150) * 0.2
    for _ in range(3):
        at = r.uniform(0, dur * 0.8)
        f = r.uniform(320, 520)
        d = 0.5
        b = tone(f, d, amp=0.05, harm=(1.0, 0.4, 0.2), vibrato=0.01)
        b *= env_ad(len(b), 0.05, 0.4)
        place(sig, b, at, 0.7)
    return reverb(sig, 2.2, 0.35)


def siren(dur, seed=13):
    n = n_samples(dur)
    t = np.arange(n) / SR
    f = 700 + 220 * np.sin(2 * np.pi * 0.55 * t)
    phase = 2 * np.pi * np.cumsum(f) / SR
    sig = (np.sin(phase) * 0.06).astype(np.float32)
    sig += lowpass(brown(n), 200) * 0.25
    return reverb(sig, 2.6, 0.5)


def silence_room(dur, tense=0.0, seed=14):
    n = n_samples(dur)
    sig = lowpass(brown(n), 120) * 0.12
    if tense > 0:
        sig += tone(4200, dur, amp=0.0035 * tense, harm=(1.0,))
        sig += tone(58, dur, amp=0.05 * tense, harm=(1.0, 0.4), vibrato=0.003)
    return reverb(sig, 2.0, 0.3)


def office(dur, seed=15):
    n = n_samples(dur)
    sig = lowpass(brown(n), 180) * 0.28 + tone(100, dur, amp=0.02, harm=(1.0, 0.3))
    for _ in range(int(dur * 3)):
        at = rng.uniform(0, dur)
        key = bandpass(white(n_samples(0.03)), 1500, 6000) * np.exp(-np.linspace(0, 8, n_samples(0.03)))
        place(sig, key.astype(np.float32), at, 0.05)
    return reverb(sig, 0.9, 0.18)


BGMS = {
    "city_cold": lambda: city(42, 0.8, night=False, seed=21),
    "city_day": lambda: city(40, 1.3, night=False, seed=22),
    "city_night": lambda: city(44, 0.7, night=True, seed=23),
    "city_empty": lambda: city(38, 0.15, night=True, seed=24),
    "alley_dusk": lambda: city(40, 0.9, night=False, crowd=0.5, seed=25),
    "river_night": lambda: city(44, 0.5, night=True, river=True, seed=26),
    "rain_street": lambda: rain(42, 1.1, 4600, seed=31),
    "rain_night": lambda: rain(44, 1.0, 3600, thunder=True, seed=32),
    "rain_light": lambda: rain(38, 0.65, 5200, seed=33),
    "room_night": lambda: room(40, tv=True, seed=41),
    "room_warm": lambda: room(42, warm=1.0, seed=42),
    "room_dawn": lambda: room(38, bird=True, seed=43),
    "room_empty": lambda: room(40, clock=True, seed=44),
    "room_sad": lambda: room(42, warm=0.45, tv=False, seed=45),
    "station_room": lambda: station(40, 0.0, seed=51),
    "station_busy": lambda: station(40, 0.8, seed=52),
    "station_warm": lambda: station(36, 0.25, seed=53),
    "hospital_day": lambda: hospital(42, 0.0, night=False, seed=61),
    "hospital_night": lambda: hospital(44, 0.0, night=True, seed=62),
    "hospital_low": lambda: hospital(44, 0.35, night=True, seed=63),
    "hospital_tense": lambda: hospital(40, 1.0, night=True, seed=64),
    "funeral": lambda: funeral(44, seed=71),
    "funeral_low": lambda: funeral(44, winter=True, seed=72),
    "funeral_winter": lambda: funeral(46, winter=True, seed=73),
    "tense": lambda: drone(40, 55, 0.8, 0.5, seed=81),
    "tense_low": lambda: drone(42, 49, 0.6, 0.2, seed=82),
    "dark_low": lambda: drone(44, 43.65, 0.9, 0.0, seed=83),
    "silence": lambda: silence_room(36, 0.0, seed=91),
    "silence_tense": lambda: silence_room(38, 1.0, seed=92),
    "wedding": lambda: wedding(42, False, seed=101),
    "wedding_soft": lambda: wedding(40, True, seed=102),
    "market_noise": lambda: market(38, seed=111),
    "ktv_night": lambda: ktv(40, seed=112),
    "train": lambda: train(40, False, seed=121),
    "train_night": lambda: train(42, True, seed=122),
    "shop_morning": lambda: shop(38, False, seed=131),
    "shop_radio": lambda: shop(40, True, seed=132),
    "rural_winter": lambda: rural(42, seed=141),
    "siren_far": lambda: siren(20, seed=151),
    "office_hum": lambda: office(40, seed=161),
    "fade_out": lambda: silence_room(12, 0.0, seed=171),
}


def write_ogg(name, sig, folder):
    sig = normalize(seamless(sig, 1.2), 0.65)
    # 轻微立体声去相关
    d = int(0.008 * SR)
    left = sig
    right = np.concatenate([np.zeros(d, dtype=np.float32), sig[:-d]]) * 0.98
    stereo = np.stack([left, right], axis=1)
    wav = os.path.join(TMP, name + ".wav")
    import wave
    with wave.open(wav, "wb") as f:
        f.setnchannels(2)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes((stereo * 32767).astype("<i2").tobytes())
    out = os.path.join(OUT, folder, name + ".ogg")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav,
                    "-c:a", "vorbis", "-strict", "-2", "-q:a", "2", out], check=True)
    os.remove(wav)


def make_sfx():
    def phone():
        n = n_samples(1.6)
        sig = np.zeros(n, dtype=np.float32)
        for k, f in enumerate([880, 1174]):
            s = tone(f, 0.18, amp=0.25, harm=(1.0, 0.4, 0.2))
            s *= env_ad(len(s), 0.005, 0.16)
            place(sig, s, k * 0.22)
        place(sig, tone(660, 0.3, amp=0.12, harm=(1.0, 0.3)) * env_ad(n_samples(0.3), 0.01, 0.25), 0.55)
        return reverb(sig, 0.8, 0.2)

    def scooter():
        n = n_samples(2.4)
        t = np.arange(n) / SR
        f = 120 + 40 * np.sin(2 * np.pi * 0.4 * t)
        sig = np.sin(2 * np.pi * np.cumsum(f) / SR).astype(np.float32) * 0.12
        sig += bandpass(white(n), 400, 3000) * 0.06
        sig *= env_ad(n, 0.3, 1.2)
        return reverb(sig, 1.0, 0.2)

    def start():
        n = n_samples(1.2)
        sig = bandpass(white(n), 600, 4000) * 0.08
        sig *= np.exp(-np.linspace(0, 4, n))
        tt = tone(90, 0.5, amp=0.12, harm=(1.0, 0.5))
        place(sig, tt * env_ad(len(tt), 0.01, 0.4), 0.0)
        return reverb(sig, 0.8, 0.2)

    def crowd():
        n = n_samples(3.0)
        sig = bandpass(white(n), 250, 2800) * 0.14
        sig *= 0.4 + 0.6 * np.abs(np.sin(2 * np.pi * 0.7 * np.arange(n) / SR))
        return reverb(sig, 1.2, 0.25)

    for name, fn in (("phone_notify", phone), ("scooter", scooter),
                     ("scooter_start", start), ("crowd", crowd)):
        write_ogg(name, fn(), "sfx")


def main():
    os.makedirs(os.path.join(OUT, "bgm"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "sfx"), exist_ok=True)
    os.makedirs(TMP, exist_ok=True)
    if "--sfx-only" not in sys.argv:
        for name, fn in BGMS.items():
            write_ogg(name, fn(), "bgm")
            print("bgm", name, flush=True)
    make_sfx()
    print("sfx done, total bgm:", len(BGMS))


if __name__ == "__main__":
    main()
