#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""무료 경로 — AI 없이 코드로 캐릭터·장면을 그린다(샘플 캐릭터 「말랑이」).

    python3 samples/엔진/scripts/draw_sample.py           → samples/예시편/EP00_샘플/scenes/*.png + s0_cover.png
    python3 samples/엔진/scripts/draw_sample.py --sheet   → samples/에셋/character/character.png (캐릭터 시트)

그림 실력이 없어도 「도형 + 표정 몇 개」로 툰 한 편이 된다는 걸 보여 주는 샘플이다.
내 캐릭터를 만들고 싶으면 Claude에게 「말랑이 대신 ○○ 캐릭터로 바꿔 줘」라고 하면 된다.
캐릭터 시트(character.png)는 AI 작화(gen_scenes.py)의 참고 그림으로도 쓴다.
"""
import argparse, math, os
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
K = 2                                   # 2배로 그려서 줄이면 선이 부드럽다
W, H = 1080 * K, 1350 * K
LINE = (74, 62, 54); BODY = (255, 226, 205); BLUSH = (247, 160, 160); LEAF = (126, 196, 140)


def P(*v): return [int(x * K) for x in v]


def char(d, cx, cy, s=1.0, eyes="dot", mouth="smile", sweat=False, arms="down", lean=0):
    """말랑이 — 둥근 몸 + 머리 위 잎 하나. eyes: dot/wide/closed/happy/dizzy, mouth: smile/o/flat/wave/open"""
    r = 150 * s; lw = max(4, int(7 * s)) * K
    x0, y0, x1, y1 = cx - r * 1.05 + lean, cy - r, cx + r * 1.05 + lean, cy + r * .92
    # 팔
    for side in (-1, 1):
        ax = cx + side * r * .95 + lean
        if arms == "up":   pts = (ax, cy - r * .1, ax + side * r * .35, cy - r * .75)
        elif arms == "run": pts = (ax, cy + r * .1, ax + side * r * .45, cy + r * (.35 if side < 0 else -.25))
        else:              pts = (ax, cy + r * .1, ax + side * r * .25, cy + r * .5)
        d.line(P(*pts), fill=LINE, width=lw * 2)
        d.ellipse(P(pts[2] - r * .12, pts[3] - r * .12, pts[2] + r * .12, pts[3] + r * .12), fill=BODY, outline=LINE, width=lw)
    # 발
    for side in (-1, 1):
        fx = cx + side * r * .45 + (side * r * .25 if arms == "run" else 0)
        d.ellipse(P(fx - r * .28, cy + r * .78, fx + r * .28, cy + r * 1.02), fill=BODY, outline=LINE, width=lw)
    d.ellipse(P(x0, y0, x1, y1), fill=BODY, outline=LINE, width=lw)
    # 잎
    lx, ly = cx + lean, y0 + r * .02
    d.line(P(lx, ly, lx, ly - r * .28), fill=LINE, width=lw)
    d.ellipse(P(lx, ly - r * .5, lx + r * .42, ly - r * .22), fill=LEAF, outline=LINE, width=lw)
    # 볼
    for side in (-1, 1):
        bx = cx + lean + side * r * .55
        d.ellipse(P(bx - r * .16, cy + r * .12, bx + r * .16, cy + r * .28), fill=BLUSH)
    # 눈
    ex, ey = r * .33, cy - r * .1
    for side in (-1, 1):
        x = cx + lean + side * ex
        if eyes == "dot":      d.ellipse(P(x - r * .07, ey - r * .09, x + r * .07, ey + r * .09), fill=LINE)
        elif eyes == "wide":
            d.ellipse(P(x - r * .14, ey - r * .17, x + r * .14, ey + r * .17), fill="white", outline=LINE, width=lw)
            d.ellipse(P(x - r * .05, ey - r * .05, x + r * .05, ey + r * .05), fill=LINE)
        elif eyes == "closed": d.line(P(x - r * .12, ey, x + r * .12, ey), fill=LINE, width=lw)
        elif eyes == "happy":  d.arc(P(x - r * .12, ey - r * .08, x + r * .12, ey + r * .14), 200, 340, fill=LINE, width=lw)
        elif eyes == "dizzy":
            d.line(P(x - r * .1, ey - r * .1, x + r * .1, ey + r * .1), fill=LINE, width=lw)
            d.line(P(x - r * .1, ey + r * .1, x + r * .1, ey - r * .1), fill=LINE, width=lw)
    # 입
    my = cy + r * .2; mx = cx + lean
    if mouth == "smile":  d.arc(P(mx - r * .14, my - r * .1, mx + r * .14, my + r * .1), 20, 160, fill=LINE, width=lw)
    elif mouth == "o":    d.ellipse(P(mx - r * .08, my - r * .02, mx + r * .08, my + r * .16), fill=LINE)
    elif mouth == "open": d.chord(P(mx - r * .17, my - r * .1, mx + r * .17, my + r * .22), 0, 180, fill=LINE)
    elif mouth == "flat": d.line(P(mx - r * .1, my + r * .04, mx + r * .1, my + r * .04), fill=LINE, width=lw)
    elif mouth == "wave":
        pts = [(mx - r * .15 + i * r * .05, my + r * .04 + (r * .03 if i % 2 else -r * .03)) for i in range(7)]
        d.line([tuple(int(v * K) for v in p) for p in pts], fill=LINE, width=lw)
    if sweat:
        sx, sy = cx + lean + r * .9, cy - r * .7
        d.polygon(P(sx, sy - r * .2, sx - r * .1, sy, sx + r * .1, sy), fill=(150, 205, 240))
        d.ellipse(P(sx - r * .1, sy - r * .08, sx + r * .1, sy + r * .12), fill=(150, 205, 240))


def canvas(bg):
    im = Image.new("RGB", (W, H), bg); return im, ImageDraw.Draw(im)


def bedroom(d, night=False):
    wall = (58, 64, 98) if night else (250, 238, 222)
    d.rectangle(P(0, 0, 1080, 1350), fill=wall)
    d.rectangle(P(0, 1040, 1080, 1350), fill=(214, 186, 160) if not night else (60, 52, 70))
    # 창문
    sky = (40, 46, 80) if night else (186, 222, 245)
    d.rounded_rectangle(P(640, 330, 960, 640), radius=18 * K, fill=sky, outline=LINE, width=8 * K)
    d.line(P(800, 330, 800, 640), fill=LINE, width=6 * K); d.line(P(640, 485, 960, 485), fill=LINE, width=6 * K)
    # 침대
    d.rounded_rectangle(P(60, 900, 760, 1120), radius=40 * K, fill=(240, 240, 250), outline=LINE, width=8 * K)
    d.rounded_rectangle(P(40, 820, 120, 1180), radius=24 * K, fill=(196, 160, 130), outline=LINE, width=8 * K)


def clock(d, cx, cy, s=1.0, ring=False):
    r = 80 * s
    d.ellipse(P(cx - r, cy - r, cx + r, cy + r), fill=(255, 120, 110), outline=LINE, width=8 * K)
    d.ellipse(P(cx - r * .75, cy - r * .75, cx + r * .75, cy + r * .75), fill="white", outline=LINE, width=5 * K)
    d.line(P(cx, cy, cx, cy - r * .55), fill=LINE, width=7 * K); d.line(P(cx, cy, cx + r * .4, cy), fill=LINE, width=7 * K)
    for side in (-1, 1):
        d.ellipse(P(cx + side * r * .7 - r * .25, cy - r * 1.15, cx + side * r * .7 + r * .25, cy - r * .7), fill=(255, 200, 80), outline=LINE, width=6 * K)
    if ring:
        for k in range(3):
            a = r * (1.3 + k * .3)
            d.arc(P(cx - a, cy - a, cx + a, cy + a), 200, 250, fill=LINE, width=6 * K)
            d.arc(P(cx - a, cy - a, cx + a, cy + a), 290, 340, fill=LINE, width=6 * K)


def speed_lines(d, y0, y1, n=7):
    for i in range(n):
        y = y0 + (y1 - y0) * i / max(1, n - 1)
        d.line(P(40, y, 300 + (i % 3) * 60, y), fill=(200, 190, 180), width=8 * K)


def save(im, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    im.resize((1080, 1350), Image.LANCZOS).save(path); print("✓", os.path.relpath(path, ROOT))


def episode():
    ep = os.path.join(ROOT, "samples", "예시편", "EP00_샘플")
    sc = os.path.join(ep, "scenes")
    # 표지 — 이불 속에서 알람을 노려봄
    im, d = canvas((255, 236, 220)); bedroom(d)
    char(d, 400, 900, 1.25, eyes="closed", mouth="wave")
    d.rounded_rectangle(P(80, 960, 760, 1160), radius=60 * K, fill=(160, 196, 236), outline=LINE, width=8 * K)   # 이불
    clock(d, 860, 1000, 1.0, ring=True); save(im, os.path.join(ep, "s0_cover.png"))
    # 1 — 알람이 울린다(밤처럼 어두운 새벽)
    im, d = canvas((0, 0, 0)); bedroom(d, night=True)
    char(d, 380, 930, 1.0, eyes="closed", mouth="flat")
    d.rounded_rectangle(P(80, 980, 760, 1160), radius=60 * K, fill=(110, 130, 170), outline=LINE, width=8 * K)
    clock(d, 820, 820, 1.4, ring=True); save(im, os.path.join(sc, "s1.png"))
    # 2 — 손만 뻗어 끈다
    im, d = canvas((0, 0, 0)); bedroom(d, night=True)
    clock(d, 760, 900, 1.6)
    d.line(P(200, 1150, 640, 880), fill=LINE, width=34 * K); d.line(P(200, 1150, 640, 880), fill=BODY, width=20 * K)
    d.ellipse(P(600, 830, 720, 950), fill=BODY, outline=LINE, width=8 * K)
    save(im, os.path.join(sc, "s2.png"))
    # 3 — 시계를 보고 화들짝(아침)
    im, d = canvas((0, 0, 0)); bedroom(d)
    char(d, 540, 880, 1.7, eyes="wide", mouth="open", sweat=True, arms="up")
    save(im, os.path.join(sc, "s3.png"))
    # 4 — 후다닥 뛰어나감
    im, d = canvas((210, 232, 250))
    d.rectangle(P(0, 1000, 1080, 1350), fill=(200, 200, 205))
    for x in (60, 360, 700):
        d.rounded_rectangle(P(x, 420, x + 260, 1000), radius=10 * K, fill=(236, 226, 214), outline=LINE, width=6 * K)
    speed_lines(d, 700, 1000)
    char(d, 620, 820, 1.25, eyes="wide", mouth="o", sweat=True, arms="run", lean=30)
    save(im, os.path.join(sc, "s4.png"))
    # 5 — 달력: 오늘은 쉬는 날(글자 대신 빨간 동그라미)
    im, d = canvas((255, 246, 232))
    d.rounded_rectangle(P(180, 300, 900, 1000), radius=30 * K, fill="white", outline=LINE, width=8 * K)
    d.rectangle(P(180, 300, 900, 420), fill=(255, 140, 130), outline=LINE, width=8 * K)
    for r_ in range(4):
        for c_ in range(5):
            x, y = 230 + c_ * 135, 460 + r_ * 130
            d.rounded_rectangle(P(x, y, x + 100, y + 90), radius=12 * K, fill=(245, 240, 234))
    x, y = 230 + 2 * 135, 460 + 1 * 130
    d.ellipse(P(x - 30, y - 30, x + 130, y + 120), outline=(230, 60, 70), width=12 * K)
    char(d, 660, 1130, .8, eyes="dizzy", mouth="wave")
    save(im, os.path.join(sc, "s5.png"))
    # 6 — 다시 이불 속으로(행복)
    im, d = canvas((0, 0, 0)); bedroom(d)
    char(d, 400, 900, 1.25, eyes="happy", mouth="smile")
    d.rounded_rectangle(P(80, 960, 760, 1160), radius=60 * K, fill=(160, 196, 236), outline=LINE, width=8 * K)
    save(im, os.path.join(sc, "s6.png"))


def sheet():
    im, d = canvas((255, 255, 255))
    poses = [("dot", "smile", False, "down"), ("wide", "open", True, "up"), ("happy", "smile", False, "down"),
             ("closed", "wave", False, "down"), ("dizzy", "wave", False, "down"), ("wide", "o", True, "run")]
    for i, (e, m, sw, a) in enumerate(poses):
        cx = 200 + (i % 3) * 340; cy = 330 + (i // 3) * 560
        char(d, cx, cy, .85, eyes=e, mouth=m, sweat=sw, arms=a)
    save(im, os.path.join(ROOT, "samples", "에셋", "character", "character.png"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("--sheet", action="store_true"); a = ap.parse_args()
    sheet() if a.sheet else episode()
