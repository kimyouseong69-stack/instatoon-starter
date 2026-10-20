#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatGPT 에서 받은 그림 가져오기 — 다운로드 폴더의 최근 그림을 컷 이름으로 옮긴다.

받은 순서(오래된 것 → 최신) = ai_prompts.md 의 컷 순서(표지 → 1 → 2 …)로 짝짓는다.
먼저 짝지은 표만 보여 주고, --apply 를 붙여야 실제로 옮긴다.

    .venv/bin/python samples/엔진/scripts/import_images.py episodes/EP01_제목                 # 짝 보기(아무것도 안 바꿈)
    .venv/bin/python samples/엔진/scripts/import_images.py episodes/EP01_제목 --apply
    .venv/bin/python samples/엔진/scripts/import_images.py episodes/EP01_제목 --names s3 --apply   # 다시 뽑은 한 컷만
    .venv/bin/python samples/엔진/scripts/import_images.py episodes/EP01_제목 --names character --apply

  --from 폴더      기본 ~/Downloads
  --minutes N      최근 N분 안에 받은 그림만 (기본 180)

컷 그림은 4:5 로 맞춘다(2:3 으로 받으면 위를 잘라냄 — 프롬프트가 위 1/6 을 비워 두게 시켜 둠).
원본은 다운로드 폴더에 그대로 남는다(복사).
"""
import argparse
import sys
import time
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chatgpt_prompts import build, order_key  # noqa: E402

EXT = {".png", ".jpg", ".jpeg", ".webp"}


def dest(ep: Path, name: str) -> Path:
    if name in ("character", "s0_cover"):
        return ep / f"{name}.png"
    return ep / "scenes" / f"{name}.png"


def fit45(im: Image.Image) -> Image.Image:
    """4:5 로 맞춘다. 더 길쭉하면 위를 잘라내고(gen_scenes 와 같은 규칙), 더 넓으면 좌우 가운데를 남긴다."""
    w, h = im.size
    target_h = round(w * 5 / 4)
    if h > target_h:
        return im.crop((0, h - target_h, w, h))
    target_w = round(h * 4 / 5)
    if w > target_w:
        left = (w - target_w) // 2
        return im.crop((left, 0, left + target_w, h))
    return im


def main():
    ap = argparse.ArgumentParser(description="받은 그림 가져오기")
    ap.add_argument("episode")
    ap.add_argument("--from", dest="src", default=str(Path.home() / "Downloads"))
    ap.add_argument("--minutes", type=int, default=180)
    ap.add_argument("--names", nargs="+", help="이 컷들만 (받은 순서대로 짝지음)")
    ap.add_argument("--apply", action="store_true", help="실제로 옮기기")
    a = ap.parse_args()

    ep = Path(a.episode).resolve()
    names = a.names or [n for n in build(ep) if n != "character"]
    names = sorted(names, key=order_key) if not a.names else names

    src = Path(a.src).expanduser()
    since = time.time() - a.minutes * 60
    files = sorted((p for p in src.iterdir() if p.suffix.lower() in EXT and p.stat().st_mtime >= since),
                   key=lambda p: p.stat().st_mtime)
    if not files:
        sys.exit(f"{src} 에 최근 {a.minutes}분 안에 받은 그림이 없어요.")
    files = files[-len(names):]          # 가장 최근 것들만
    if len(files) < len(names):
        print(f"⚠ 그림이 {len(files)}장뿐이에요(필요 {len(names)}장) → 앞 컷부터 {len(files)}개만 짝지어요.")
        names = names[:len(files)]

    print("받은 순서 → 컷")
    for f, n in zip(files, names):
        t = time.strftime("%H:%M:%S", time.localtime(f.stat().st_mtime))
        print(f"  {t}  {f.name}  →  {dest(ep, n).relative_to(ep)}")
    if not a.apply:
        print("\n짝이 맞으면 --apply 를 붙여 다시 실행하세요. (틀리면 --names 로 순서를 직접 적기)")
        return

    for f, n in zip(files, names):
        d = dest(ep, n)
        d.parent.mkdir(parents=True, exist_ok=True)
        im = Image.open(f).convert("RGB")
        if n != "character":
            im = fit45(im)
        im.save(d, "PNG")
        print(f"  ✓ {d.relative_to(ep)}  {im.size[0]}x{im.size[1]}")
    if "character" in names:
        print("  캐릭터 그림을 이 편 참고 그림으로 쓰려면 gen.json 의 \"ref\" 를 \"character.png\" 로.")


if __name__ == "__main__":
    main()
