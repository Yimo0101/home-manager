# -*- coding: utf-8 -*-
"""居家管家 - 白噪音 / 助眠铃合成（纯标准库，无需 numpy）

生成 30 秒、22050Hz 单声道 16bit WAV，可循环：
雨声、海浪、粉噪（营火般温暖）、轻柔风铃提示音。
文件生成一次后重复使用，集市页与铃声选择器直接读取。
"""
import math
import os
import random
import struct
import wave

from config import AUDIO_DIR

SR = 22050
SECONDS = 30

FILES = {
    "ambient_rain": "白噪音-雨声.wav",
    "ambient_waves": "白噪音-海浪.wav",
    "ambient_pink": "白噪音-粉噪.wav",
    "ambient_chime": "铃声-轻柔风铃.wav",
}


def _save(name, samples):
    path = os.path.join(AUDIO_DIR, name)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        frames = bytearray()
        for s in samples:
            v = int(max(-1.0, min(1.0, s)) * 32767)
            frames += struct.pack("<h", v)
        wf.writeframes(bytes(frames))
    return path


def _white(n, rnd):
    return [rnd.uniform(-1, 1) for _ in range(n)]


def _rain(n, rnd):
    """高通白噪（沙沙雨幕）+ 少量低频隆隆"""
    src = _white(n, rnd)
    out = []
    lp = 0.0
    lp2 = 0.0
    for x in src:
        lp += 0.08 * (x - lp)       # 低频成分
        hp = x - lp                # 高频雨声
        lp2 += 0.02 * (x - lp2)    # 远处闷雷
        out.append(hp * 0.55 + lp2 * 0.35)
    return out


def _pink(n, rnd):
    """Voss-McCartney 近似 1/f 粉噪（温暖、不刺耳）"""
    rows = 8
    vals = [rnd.uniform(-1, 1) for _ in range(rows)]
    out = []
    for i in range(n):
        idx = (i & -(i + 1)).bit_length() if (i + 1) & i == 0 else 0
        if idx < rows:
            vals[idx] = rnd.uniform(-1, 1)
        out.append(sum(vals) / rows * 1.6)
    return out


def _waves(n, rnd):
    """棕噪 + 慢速振幅 LFO，模拟海浪一涨一落"""
    out = []
    brown = 0.0
    lfo = 0.0
    for i in range(n):
        white = rnd.uniform(-1, 1)
        brown += 0.02 * white
        brown *= 0.98
        lfo += 2 * math.pi / (SR * 7.0)   # 约 7 秒一浪
        env = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(lfo)) ** 1.5
        out.append(brown * 5.5 * env)
    return out


def _chime(n, rnd):
    """五声音阶风铃，随机轻碰，余韵衰减"""
    scale = [523.25, 587.33, 659.25, 783.99, 880.0]   # C5 D5 E5 G5 A5
    active = []   # [freq, 起始样本, 音量]
    out = []
    next_hit = 0
    for i in range(n):
        if i >= next_hit:
            active.append([rnd.choice(scale), i, rnd.uniform(0.25, 0.5)])
            next_hit = i + rnd.randint(int(SR * 1.2), int(SR * 3.5))
        v = 0.0
        for note in active:
            f, t0, amp = note
            age = (i - t0) / SR
            if age > 4.0:
                continue
            env = math.exp(-1.6 * age)
            v += amp * env * (
                math.sin(2 * math.pi * f * age)
                + 0.5 * math.sin(2 * math.pi * f * 2.01 * age)
                + 0.25 * math.sin(2 * math.pi * f * 2.99 * age))
        out.append(v * 0.5)
    return out


_BUILDERS = {
    "ambient_rain": _rain,
    "ambient_waves": _waves,
    "ambient_pink": _pink,
    "ambient_chime": _chime,
}


def ensure_all(force=False):
    """缺失才生成；返回 {key: 路径}"""
    result = {}
    for key, fname in FILES.items():
        path = os.path.join(AUDIO_DIR, fname)
        if force or not os.path.exists(path):
            rnd = random.Random(20261005 + hash(key) % 1000)
            samples = _BUILDERS[key](SR * SECONDS, rnd)
            _save(fname, samples)
        result[key] = path
    return result


if __name__ == "__main__":
    for k, p in ensure_all().items():
        print(k, os.path.getsize(p), p)
