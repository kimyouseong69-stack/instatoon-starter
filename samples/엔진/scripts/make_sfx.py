#!/usr/bin/env python3
"""효과음 직접 만들기 — 파이썬으로 합성해서 저작권 걱정 없는 기본 효과음 세트를 만든다.

    python3 samples/엔진/scripts/make_sfx.py        → samples/에셋/sfx/*.mp3

더 좋은 소리가 필요하면 무료 효과음 사이트에서 받아 같은 폴더에 넣고,
samples/엔진/reel/profiles/sfxmap.json 에 「그림 속 효과음 글자 → 소리 이름」을 한 줄 추가하면 된다.
(받은 소리는 사이트 약관상 재배포 금지인 경우가 많으니 깃허브에는 올리지 말 것 — .gitignore 참고)
"""
import os, subprocess, wave
import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "에셋", "sfx")
rng = np.random.default_rng(7)

def t(sec): return np.arange(int(SR * sec)) / SR
def env(n, a=0.005, r=0.1):
    x = np.ones(n); ai = int(SR * a); ri = min(n, int(SR * r))
    if ai: x[:ai] = np.linspace(0, 1, ai)
    x[-ri:] *= np.linspace(1, 0, ri) ** 2
    return x
def tone(f, sec, a=0.003, r=None, kind="sin"):
    tt = t(sec); ph = 2 * np.pi * np.cumsum(np.broadcast_to(f, tt.shape)) / SR
    w = np.sin(ph) if kind == "sin" else np.sign(np.sin(ph)) * 0.5
    return w * env(len(tt), a, r or sec)
def noise(sec): return rng.standard_normal(int(SR * sec))
def lowpass(x, k):                       # 아주 단순한 이동평균 저역통과
    return np.convolve(x, np.ones(k) / k, mode="same")
def cat(*xs, gap=0.0):
    g = np.zeros(int(SR * gap)); out = []
    for x in xs: out += [x, g]
    return np.concatenate(out[:-1])

S = {}
S["pop"] = tone(np.linspace(900, 300, int(SR * .09)), .09, r=.07)                       # 톡·뿅
S["whoosh"] = lowpass(noise(.35), 30) * env(int(SR * .35), .15, .2) * 3                # 휙·후다닥
S["ding"] = tone(1320, .9, r=.85) * .6 + tone(2640, .9, r=.5) * .2                     # 띵·반짝
S["dingdong"] = cat(tone(988, .45, r=.4), tone(784, .7, r=.65))                        # 띵동
S["thud"] = (tone(np.linspace(120, 45, int(SR * .3)), .3, r=.28) + lowpass(noise(.3), 60) * env(int(SR * .3), .001, .12)) * .9   # 쿵·털썩
S["tap"] = np.concatenate([np.concatenate([lowpass(noise(.03), 4) * env(int(SR * .03), .001, .025), np.zeros(int(SR * .07))]) for _ in range(4)]) * .8  # 타닥·탁탁
def sparkle():                                                                          # 반짝반짝
    out = np.zeros(int(SR * .6))
    for i, f in enumerate([1568, 1976, 2349, 3136]):
        x = tone(f, .25, r=.24) * .35; st = int(SR * i * .07); out[st:st + len(x)] += x
    return out
S["sparkle"] = sparkle()
S["drop"] = tone(np.linspace(700, 180, int(SR * .5)), .5, r=.45) * .7                  # 축… 철렁(가라앉는 컷)
S["boing"] = tone(220 + 90 * np.sin(2 * np.pi * 9 * t(.5)), .5, r=.45) * .8           # 띠용·화들짝
def babble(n, base, speed, seed):
    r = np.random.default_rng(seed); parts = []
    for _ in range(n):
        f = base * r.uniform(.85, 1.25); d = speed * r.uniform(.7, 1.2)
        parts.append(tone(f, d, a=.01, r=d * .6, kind="sq") * .5); parts.append(np.zeros(int(SR * speed * .25)))
    return lowpass(np.concatenate(parts), 6)
S["babble"] = babble(9, 520, .075, 1)          # 말풍선 중얼중얼(게임 대사처럼)
S["babble_fast"] = babble(12, 600, .05, 2)     # 당황한 말
S["babble_low"] = babble(8, 300, .09, 3)       # 어른·선배 말

os.makedirs(OUT, exist_ok=True)
for name, x in S.items():
    x = np.asarray(x, dtype=float); x = x / (np.abs(x).max() + 1e-9) * 0.8
    wav = os.path.join(OUT, name + ".wav")
    with wave.open(wav, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x * 32767).astype("<i2").tobytes())
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", wav, "-ar", "44100", "-b:a", "128k", os.path.join(OUT, name + ".mp3")], check=True)
    os.remove(wav)
    print("✓", name)
print("완료 →", os.path.abspath(OUT))
