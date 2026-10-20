#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""AI 작화 — 편 폴더의 ai_prompts.md 를 읽어 컷 그림을 뽑는다 (OpenAI 이미지 API, 유료).

    python3 samples/엔진/scripts/gen_scenes.py --ep episodes/EP01_제목 --plan        # 비용만 계산(무료)
    python3 samples/엔진/scripts/gen_scenes.py --ep episodes/EP01_제목 s1 s2         # 시험 = low (기본)
    python3 samples/엔진/scripts/gen_scenes.py --ep episodes/EP01_제목 --all
    TOON_OK=1 python3 samples/엔진/scripts/gen_scenes.py --ep ... --final s3        # 확정 = high (비쌈)

비용 규칙
  1. 시험은 low. 이 그림체(굵은 선·평면 색)는 high 와 품질 차이가 거의 없다. 구도가 마음에 안 들면
     high 로 올리지 말고 low 로 여러 번 다시 뽑는다.
  2. 돌리기 전에 --plan 으로 「몇 장 × 얼마」를 먼저 본다.
  3. 호출은 전부 _작화비용.log 에 쌓인다 → python3 samples/엔진/scripts/cost.py 로 합계.
  ※ 단가는 대략값이다. 실제 청구는 OpenAI 대시보드(Usage)에서 확인.

캐릭터 참고 그림: 편 폴더 gen.json 의 "ref"(없으면 samples/에셋/character/character.png).
  같은 캐릭터가 매 컷 똑같이 나오게 하는 핵심이다. 내 캐릭터 그림 한 장을 거기에 두면 된다.
"""
import argparse, base64, json, os, re, sys, time
import platform, subprocess
from datetime import datetime

# 일부 Homebrew 파이썬에서 platform.mac_ver() 가 빈 값이라 openai 가 죽는 문제 우회
if sys.platform == "darwin" and not platform.mac_ver()[0]:
    _v = subprocess.run(["sw_vers", "-productVersion"], capture_output=True, text=True).stdout.strip()
    platform.mac_ver = lambda *a, **k: (_v, ("", "", ""), "")
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]                                      # 저장소 맨 위
REF  = ROOT / "samples" / "에셋" / "character" / "character.png"
ENV  = ROOT / ".env"
LOG  = ROOT / "_작화비용.log"

GEN_W, GEN_H, CROP_H = 1024, 1536, 1280      # 2:3으로 뽑아 위에서 잘라 4:5
PRICE = {"low": .005, "medium": .041, "high": .165}   # 1024x1536 기준(출력분).
REF_COST = .012                                        # 참고이미지 1장당 대략(입력 토큰)

FRAMING = ("\n[FRAMING] The canvas is a TALL vertical 2:3 image, but the TOP SIXTH of it will be CUT AWAY "
"and discarded. Treat the LOWER FIVE SIXTHS as the real picture and compose entirely inside it: "
"the main character must be LARGE and fill a good part of that area, with a comfortable empty caption "
"band above it worth about a quarter of the real picture — NOT a huge void. Nothing important "
"may touch the very bottom edge of the canvas.")
FRAMING_BOTTOM = ("\n[FRAMING] The canvas is a TALL vertical 2:3 image, but the TOP SIXTH will be CUT AWAY. "
"Compose inside the LOWER FIVE SIXTHS: the main character LARGE and in the UPPER part of that area, "
"leaving the empty caption band BELOW it, worth about a third. Nothing important at the bottom edge.")
ANCHOR_NOTE = ("\n[LOCATION LOCK] The SECOND reference image shows the exact same location this scene takes "
"place in. Reuse that room/place: same window, same curtain, same furniture, same wall colours, "
"same camera direction. Only the pose, the action and the lighting change.")


def parse_prompts(md: Path):
    """ai_prompts.md 의 「## 공통 헤더」 코드블록 + 「## 표지 장면 (s0_cover.png)」 + 「### 1. 제목」… 코드블록."""
    src = md.read_text(encoding="utf-8")
    hdr = re.search(r"## 공통 헤더 .*?\n```\n(.*?)\n```", src, re.S).group(1).strip()
    out = {}
    m = re.search(r"## 표지 장면 \(s0_cover\.png\)\n```\n(.*?)\n```", src, re.S)
    if m: out["s0_cover"] = m.group(1).strip()
    for m in re.finditer(r"### (\d+)\. [^\n]*\n```\n(.*?)\n```", src, re.S):
        out[f"s{int(m.group(1))}"] = m.group(2).strip()
    return {k: hdr + "\n" + v.replace("[공통 헤더]", "").strip() for k, v in out.items()}


def load_cfg(ep: Path):
    """gen.json — 캐릭터 참고 그림·컷별 앵커(같은 장소)·복장. 없으면 빈 설정."""
    f = ep / "gen.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}


def key():
    k = os.environ.get("OPENAI_API_KEY")
    if k: return k
    if not ENV.exists(): sys.exit("ERROR: .env 가 없습니다 — cp .env.example .env 후 OPENAI_API_KEY 를 채우세요")
    for ln in ENV.read_text(encoding="utf-8").splitlines():
        if ln.startswith("OPENAI_API_KEY="):
            return ln.split("=", 1)[1].strip().strip('"').strip("'")
    sys.exit("ERROR: .env 에 OPENAI_API_KEY 가 비어 있습니다")


def crop45(p: Path, mode: str = "4:5"):
    """기본은 4:5(위를 잘라냄). gen.json 에 "crop":"9:16" 이면 좌우를 잘라 9:16."""
    im = Image.open(p)
    if mode == "9:16":
        w = int(round(im.height * 9 / 16))
        left = (im.width - w) // 2
        im.crop((left, 0, left + w, im.height)).save(p)
    elif im.height > CROP_H:
        im.crop((0, im.height - CROP_H, im.width, im.height)).save(p)   # 항상 위에서 자른다
    return Image.open(p).size


def out_path(ep: Path, name: str) -> Path:
    return ep / "s0_cover.png" if name == "s0_cover" else ep / "scenes" / f"{name}.png"


def gen(ep, prompts, cfg, name, quality, model):
    from openai import OpenAI
    anchors = cfg.get("anchor", {}); bottom = set(cfg.get("bottom_caption", []))
    wardrobe = cfg.get("wardrobe", {})
    p = prompts[name] + wardrobe.get(name, cfg.get("wardrobe_default", "")) + (FRAMING_BOTTOM if name in bottom else FRAMING)
    ref = (ep / cfg["ref"]) if cfg.get("ref") else REF
    if not ref.exists(): sys.exit(f"ERROR: 캐릭터 참고 그림이 없습니다: {ref}")
    refs = [ref]
    anc = anchors.get(name)
    if anc:
        ap = out_path(ep, anc)
        if ap.exists(): refs.append(ap); p += ANCHOR_NOTE
        else: print(f"  ⚠️ {name}: 앵커 {anc} 아직 없음 — 단독 생성")
    dst = out_path(ep, name); dst.parent.mkdir(parents=True, exist_ok=True)
    files = [open(r, "rb") for r in refs]
    try:
        res = OpenAI(api_key=key()).images.edit(
            model=model, image=files, prompt=p, size=f"{GEN_W}x{GEN_H}", quality=quality, n=1)
    finally:
        for f in files: f.close()
    dst.write_bytes(base64.b64decode(res.data[0].b64_json))
    sz = crop45(dst, cfg.get("crop", "4:5"))
    cost = PRICE[quality] + REF_COST * len(refs)
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now():%Y-%m-%d %H:%M}\t{ep.name}\t{name}\t{quality}\t{cost:.3f}\n")
    print(f"  ✅ {name}  {sz[0]}x{sz[1]}  {quality}  ${cost:.3f}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cuts", nargs="*")
    ap.add_argument("--ep", default=".", help="화 폴더 (기본: 현재 폴더)")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--final", action="store_true", help="확정본 — high로 뽑는다")
    ap.add_argument("--plan", action="store_true", help="비용만 계산하고 끝(무료)")
    ap.add_argument("--model", default="gpt-image-2")
    a = ap.parse_args()

    ep = Path(a.ep).resolve()
    prompts = parse_prompts(ep / "ai_prompts.md")
    cfg = load_cfg(ep)
    order = ["s0_cover"] + [f"s{i}" for i in range(1, 40)]
    names = [n for n in order if n in prompts] if a.all else a.cuts
    if not names: sys.exit("뽑을 컷(s1 s2 …)을 적거나 --all 을 붙이세요.")
    q = "high" if a.final else "low"

    n_ref = sum(2 if cfg.get("anchor", {}).get(n) else 1 for n in names)
    total = len(names) * PRICE[q] + n_ref * REF_COST
    print(f"\n[비용 계획] {ep.name} · {len(names)}장 × {q}(${PRICE[q]}) + 참고이미지 {n_ref}장"
          f"\n           ≈ ${total:.2f}   {'← 확정본' if a.final else '← 시험(low). 확정은 --final'}\n")
    if a.plan: return
    if a.final and not os.environ.get("TOON_OK"):
        print("high 는 비쌉니다. 위 비용을 확인했으면 앞에 TOON_OK=1 을 붙여 다시 실행하세요.")
        sys.exit(2)
    for n in names:
        for k in (1, 2, 3):
            try: gen(ep, prompts, cfg, n, q, a.model); break
            except Exception as e:
                print(f"  ⚠️ {n} 시도{k}: {str(e)[:150]}")
                if k == 3: print(f"  ❌ {n} 포기")
                else: time.sleep(6)


if __name__ == "__main__":
    main()
