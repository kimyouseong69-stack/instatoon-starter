#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ChatGPT 복붙용 그림 프롬프트 — 기본 그림 방식 (API 키·추가 비용 없음, ChatGPT 구독 웹에서).

편 폴더의 ai_prompts.md(공통 헤더 + 컷별 장면)를 읽어, ChatGPT 에 **그대로 붙여 넣을 완성 프롬프트**를
컷마다 만든다. 같은 ai_prompts.md 를 유료 자동(gen_scenes.py)도 읽으므로 나중에 API 로 바꿔도 그대로 쓴다.

    .venv/bin/python samples/엔진/scripts/chatgpt_prompts.py episodes/EP01_제목            # ChatGPT_복붙.md 만들기
    .venv/bin/python samples/엔진/scripts/chatgpt_prompts.py episodes/EP01_제목 --copy s1  # s1 프롬프트를 클립보드로
    .venv/bin/python samples/엔진/scripts/chatgpt_prompts.py episodes/EP01_제목 --list     # 컷 목록만

ChatGPT 에서 하는 일 (컷마다)
  1. 새 채팅(또는 같은 채팅) → 캐릭터 그림(character.png)을 **첨부**
  2. 클립보드의 프롬프트 붙여 넣기 → 그림이 나오면 다운로드
  3. 다 받았으면 클로드에게 「받은 그림 가져와 줘」 → import_images.py 가 다운로드 폴더에서 컷 이름으로 가져옴
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gen_scenes import parse_prompts, FRAMING, FRAMING_BOTTOM, REF, load_cfg  # noqa: E402

CHATGPT_HEAD = ("Create ONE image. Use the ATTACHED character picture as the exact character reference. "
                "Portrait orientation, 2:3 (1024x1536). Do not write any text in the image.\n")

SHEET_RE = re.compile(r"## 캐릭터 시트 \(character\.png\)\n(?:[^`\n][^\n]*\n)*```\n(.*?)\n```", re.S)


def order_key(name: str):
    if name == "character":
        return -2
    if name == "s0_cover":
        return -1
    return int(name[1:])


def build(ep: Path):
    md = ep / "ai_prompts.md"
    if not md.exists():
        sys.exit(f"ai_prompts.md 가 없어요: {md}\n먼저 「대본 보고 장면 프롬프트 써 줘」로 만들어 주세요.")
    cfg = load_cfg(ep)
    bottom = set(cfg.get("bottom_caption", []))
    wardrobe = cfg.get("wardrobe", {})
    prompts = {}
    for name, p in parse_prompts(md).items():
        p = p + wardrobe.get(name, cfg.get("wardrobe_default", ""))
        p += FRAMING_BOTTOM if name in bottom else FRAMING
        prompts[name] = CHATGPT_HEAD + p
    m = SHEET_RE.search(md.read_text(encoding="utf-8"))
    if m:   # 캐릭터 시트는 참고 그림 없이 처음 만드는 그림이라 머리말·여백 규칙을 붙이지 않는다
        prompts["character"] = ("Create ONE image. Character design sheet on a plain white background. "
                                "Do not write any text in the image.\n" + m.group(1).strip())
    return dict(sorted(prompts.items(), key=lambda kv: order_key(kv[0])))


def save_name(name: str) -> str:
    if name == "character":
        return "character.png (편 폴더)"
    if name == "s0_cover":
        return "s0_cover.png (편 폴더)"
    return f"scenes/{name}.png"


def main():
    ap = argparse.ArgumentParser(description="ChatGPT 복붙용 그림 프롬프트")
    ap.add_argument("episode")
    ap.add_argument("--copy", metavar="컷", help="이 컷 프롬프트를 클립보드로 (예: s1, s0_cover, character)")
    ap.add_argument("--list", action="store_true")
    a = ap.parse_args()

    ep = Path(a.episode).resolve()
    prompts = build(ep)
    cfg = load_cfg(ep)
    ref = (ep / cfg["ref"]) if cfg.get("ref") else REF

    if a.list:
        for n in prompts:
            print(f"  {n:<10} → {save_name(n)}")
        return

    if a.copy:
        if a.copy not in prompts:
            sys.exit(f"{a.copy} 가 없어요. 있는 컷: {', '.join(prompts)}")
        subprocess.run(["pbcopy"], input=prompts[a.copy].encode("utf-8"), check=False)
        print(f"{a.copy} 프롬프트를 클립보드에 복사했어요 → ChatGPT 에 붙여 넣기"
              + ("" if a.copy == "character" else f" (캐릭터 그림 첨부: {ref})"))
        return

    lines = [f"# {ep.name} — ChatGPT 복붙 프롬프트", "",
             "> 컷마다: **캐릭터 그림 첨부** → 아래 상자 내용을 그대로 붙여 넣기 → 나온 그림 다운로드.",
             f"> 캐릭터 그림: `{ref}`",
             "> 다 받았으면 클로드에게 「받은 그림 가져와 줘」 (다운로드 폴더에서 받은 순서대로 컷 이름을 붙여요).",
             "> 마음에 안 드는 컷은 같은 채팅에서 「눈을 더 크게」처럼 고쳐 달라고 해도 돼요.", ""]
    for i, (n, p) in enumerate(prompts.items(), 1):
        lines += [f"## {i}. {n} → `{save_name(n)}`", "```", p, "```", ""]
    out = ep / "ChatGPT_복붙.md"
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"만들었어요: {out}")
    print(f"  컷 {len(prompts)}개: {', '.join(prompts)}")
    print(f"  한 컷씩 복사: --copy {next(iter(prompts))}")


if __name__ == "__main__":
    main()
