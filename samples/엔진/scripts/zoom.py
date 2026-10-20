#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""검토용 확대 보기 — 전체는 배경으로 두고 특정 카드/영역만 크게 띄운다.

    python3 <저장소>/samples/엔진/scripts/zoom.py 14                 # 14번 카드 전체를 크게
    python3 <저장소>/samples/엔진/scripts/zoom.py 14 --at 0.5,0.7    # 14번 카드의 (가로50%,세로70%) 지점을 확대
    python3 <저장소>/samples/엔진/scripts/zoom.py 14 --at 0.5,0.7 --box 0.35   # 확대 범위를 넓게(기본 0.28)
    python3 <저장소>/samples/엔진/scripts/zoom.py 14 --cols 5        # 컨택트시트 열 수(기본 5)

컨택트시트 위에 빨간 테두리로 「지금 보고 있는 자리」를 표시하므로,
확대된 그림이 전체 어디인지 헷갈리지 않는다.
"""
import argparse, glob, math, os, sys
from PIL import Image, ImageDraw, ImageEnhance

ap = argparse.ArgumentParser()
ap.add_argument("card", type=int, help="카드 번호 (card{N}.png)")
ap.add_argument("--at", default=None, help="확대할 지점 '가로비율,세로비율' (기본: 카드 전체)")
ap.add_argument("--box", type=float, default=0.28, help="확대 범위(카드 대비 비율)")
ap.add_argument("--cols", type=int, default=5, help="컨택트시트 열 수")
ap.add_argument("--out", default="_zoom.png")
a = ap.parse_args()

cards = sorted(glob.glob("card*.png"), key=lambda f: int("".join(c for c in os.path.basename(f) if c.isdigit())))
if not cards: sys.exit("card*.png 가 없습니다. 편 폴더 안에서 실행하세요.")
target = f"card{a.card}.png"
if not os.path.exists(target): sys.exit(f"{target} 없음")

card = Image.open(target).convert("RGB")
CW, CH = card.size

# ── 확대할 영역 ──
if a.at:
    fx, fy = (float(v) for v in a.at.split(","))
    bw, bh = int(CW * a.box), int(CH * a.box)
    cx, cy = int(CW * fx), int(CH * fy)
    left, top = max(0, min(CW - bw, cx - bw // 2)), max(0, min(CH - bh, cy - bh // 2))
    region = (left, top, left + bw, top + bh)
else:
    region = (0, 0, CW, CH)
crop = card.crop(region)

# ── 왼쪽: 확대본 ──
BIG_W = 1200
big = crop.resize((BIG_W, int(BIG_W * crop.height / crop.width)), Image.LANCZOS)

# ── 오른쪽: 컨택트시트(배경) + 현재 위치 표시 ──
tw = 210; th = int(tw * CH / CW)
rows = math.ceil(len(cards) / a.cols)
sheet = Image.new("RGB", (a.cols * tw, rows * th), "white")
for i, f in enumerate(cards):
    sheet.paste(Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS), ((i % a.cols) * tw, (i // a.cols) * th))
sheet = ImageEnhance.Brightness(sheet).enhance(0.55)          # 배경은 눌러 둔다
d = ImageDraw.Draw(sheet)
i = a.card - 1
ox, oy = (i % a.cols) * tw, (i // a.cols) * th
# 해당 카드는 원래 밝기로 되살리고 테두리
sheet.paste(Image.open(target).convert("RGB").resize((tw, th), Image.LANCZOS), (ox, oy))
d.rectangle([ox, oy, ox + tw - 1, oy + th - 1], outline=(230, 40, 70), width=5)
if a.at:   # 카드 안에서 확대한 자리
    rx = ox + tw * region[0] / CW; ry = oy + th * region[1] / CH
    d.rectangle([rx, ry, rx + tw * (region[2]-region[0]) / CW, ry + th * (region[3]-region[1]) / CH],
                outline=(255, 215, 0), width=4)

# ── 합치기 ──
PAD = 24
H = max(big.height, sheet.height) + PAD * 2
out = Image.new("RGB", (big.width + sheet.width + PAD * 3, H), (28, 26, 30))
out.paste(big, (PAD, PAD))
out.paste(sheet, (big.width + PAD * 2, PAD))
out.save(a.out)
print(f"✅ {a.out}  ({target}{' 부분 확대' if a.at else ' 전체'})  {out.size[0]}x{out.size[1]}")
