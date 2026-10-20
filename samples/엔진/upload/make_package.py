"""올릴 꾸러미 만들기 — 업로드는 사람이 직접(휴대폰 앱·인스타 웹).

한 편 폴더의 카드·릴스·캡션을 인스타에 바로 올릴 수 있는 모양으로 한 폴더에 모은다.
API 연결(토큰)이 필요 없다.

  .venv/bin/python samples/엔진/upload/make_package.py episodes/EP01_제목
  .venv/bin/python samples/엔진/upload/make_package.py episodes/EP01_제목 --copy --open

만들어지는 것 (<편>/올리기/):
  01.jpg 02.jpg …   카드(card1.png …)를 순서대로 JPEG 로 (인스타는 JPEG 가 안전)
  reel.mp4          릴스가 있으면 복사
  캡션.txt          캡션.md 내용 그대로 (해시태그 개수 검사)
  올리는_순서.txt    휴대폰·웹에서 올리는 순서

  --copy  캡션을 클립보드에 복사(맥 pbcopy) → 휴대폰에서 바로 붙여 넣기(같은 애플 계정이면)
  --open  Finder 로 폴더 열기 → 파일을 골라 에어드롭
"""
import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image

MAX_TAGS = 5      # 해시태그는 5개 이하 권장
MAX_CARDS = 10    # 한 게시물에 10장 이내로 묶는 것을 기본으로


def card_num(p: Path) -> int:
    m = re.search(r"(\d+)", p.stem)
    return int(m.group(1)) if m else 0


def main():
    ap = argparse.ArgumentParser(description="올릴 꾸러미 만들기")
    ap.add_argument("episode", help="편 폴더 (예: episodes/EP01_제목)")
    ap.add_argument("--copy", action="store_true", help="캡션을 클립보드에 복사")
    ap.add_argument("--open", action="store_true", help="Finder 로 폴더 열기")
    a = ap.parse_args()

    ep = Path(a.episode).resolve()
    if not ep.is_dir():
        sys.exit(f"편 폴더가 없어요: {ep}")

    cards = sorted(ep.glob("card*.png"), key=card_num)
    if not cards:
        sys.exit("card1.png … 가 없어요. 먼저 카드를 만들어 주세요(build.js → render.js).")

    out = ep / "올리기"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir()

    warn = []
    for i, c in enumerate(cards, 1):
        im = Image.open(c).convert("RGB")
        w, h = im.size
        ratio = w / h
        if not (0.8 - 0.01 <= ratio <= 1.91 + 0.01):
            warn.append(f"{c.name} 비율 {w}x{h} — 인스타 피드 비율(4:5 ~ 1.91:1) 밖이라 잘릴 수 있어요")
        im.save(out / f"{i:02d}.jpg", "JPEG", quality=92, optimize=True)
    if len(cards) > MAX_CARDS:
        warn.append(f"카드가 {len(cards)}장 — 10장 넘으면 두 게시물로 나누는 것을 권해요")

    reel = ep / "reel" / "reel.mp4"
    has_reel = reel.exists()
    if has_reel:
        shutil.copy2(reel, out / "reel.mp4")

    cap_src = ep / "캡션.md"
    caption = cap_src.read_text(encoding="utf-8").strip() if cap_src.exists() else ""
    if caption:
        (out / "캡션.txt").write_text(caption + "\n", encoding="utf-8")
        tags = re.findall(r"#[^\s#]+", caption)
        if len(tags) > MAX_TAGS:
            warn.append(f"해시태그 {len(tags)}개 — {MAX_TAGS}개 이하로 줄이는 것을 권해요")
    else:
        warn.append("캡션.md 가 없어요 — 캡션 없이 꾸러미를 만들었어요")

    steps = [
        "[휴대폰 인스타 앱]",
        f"1. 이 폴더의 01.jpg ~ {len(cards):02d}.jpg 를 휴대폰으로 보내기(에어드롭)",
        "2. 인스타 앱 → + → 게시물 → 오른쪽 위 「여러 장 선택」 → 01 부터 순서대로 누르기",
        "3. 다음 → (필터 없이) 다음 → 캡션 칸에 캡션.txt 내용 붙여 넣기 → 공유",
    ]
    if has_reel:
        steps += [
            "4. 릴스: reel.mp4 를 휴대폰으로 → + → 릴스 → 영상 고르기 → (음악은 여기서 붙이기) → 캡션 → 공유",
        ]
    steps += [
        "",
        "[컴퓨터 인스타 웹 (instagram.com)]",
        "왼쪽 「만들기」 → 컴퓨터에서 선택 → 01.jpg 부터 여러 장 선택 → 다음 → 캡션 붙여 넣기 → 공유",
        "",
        "※ 올리기 전에 라이선스 체크(samples/노하우/07)를 했는지 한 번 더 확인",
    ]
    (out / "올리는_순서.txt").write_text("\n".join(steps) + "\n", encoding="utf-8")

    print(f"꾸러미 완성: {out}")
    print(f"  카드 {len(cards)}장 → 01.jpg ~ {len(cards):02d}.jpg")
    print(f"  릴스: {'reel.mp4' if has_reel else '없음'}")
    print(f"  캡션: {'캡션.txt' if caption else '없음'}")
    for w in warn:
        print(f"  ⚠ {w}")

    if a.copy and caption:
        subprocess.run(["pbcopy"], input=caption.encode("utf-8"), check=False)
        print("  캡션을 클립보드에 복사했어요")
    if a.open:
        subprocess.run(["open", str(out)], check=False)


if __name__ == "__main__":
    main()
