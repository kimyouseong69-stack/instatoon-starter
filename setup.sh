#!/bin/bash
# 처음 한 번만 실행:  bash setup.sh
# 필요한 프로그램을 설치하고 .env 를 만든다. 이미 있는 건 건너뛴다.
set -e
cd "$(dirname "$0")"
ok(){ printf "  \033[32m✓\033[0m %s\n" "$1"; }
step(){ printf "\n\033[1m▶ %s\033[0m\n" "$1"; }

step "1. Homebrew(맥 프로그램 설치 도구)"
# 설치는 돼 있는데 이 계정 PATH 에만 없는 경우(새 사용자 계정 등) → 연결만 해 준다
if ! command -v brew >/dev/null 2>&1 && [ -x /opt/homebrew/bin/brew ]; then
  eval "$(/opt/homebrew/bin/brew shellenv)"
  grep -q "brew shellenv" ~/.zprofile 2>/dev/null || echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
fi
if ! command -v brew >/dev/null 2>&1; then
  echo "  Homebrew 가 없습니다. 아래 한 줄을 터미널에 붙여 넣고(맥 비밀번호 입력), 끝나면 bash setup.sh 를 다시 실행하세요:"
  echo '  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
  exit 1
fi
ok "brew $(brew --version | head -1 | awk '{print $2}')"

step "2. 프로그램 (node · python · ffmpeg · cloudflared)"
for p in node python3 ffmpeg cloudflared; do
  if command -v "$p" >/dev/null 2>&1; then ok "$p (이미 있음)"; else
    f="$p"; [ "$p" = python3 ] && f=python@3.12
    brew install "$f" && ok "$p" || { echo "  ✗ $p 설치 실패 — 위 메시지를 Claude에게 보여 주세요"; exit 1; }
  fi
done
step "3. 카드 렌더러 (puppeteer — 전용 크롬을 같이 받아서 몇 분 걸릴 수 있음)"
npm install --silent
ok "node_modules"

step "4. 파이썬 패키지 (.venv 안에만 설치 — 맥 전체는 건드리지 않음)"
# 파이썬 버전에 따라 가상환경 만들기가 실패할 때가 있어(일부 Homebrew 3.14) 되는 것을 차례로 시도
if [ ! -x .venv/bin/python ]; then
  for c in python3.12 python3.13 python3.11 /usr/bin/python3 python3; do
    command -v "$c" >/dev/null 2>&1 || continue
    rm -rf .venv
    if "$c" -m venv .venv >/dev/null 2>&1 && .venv/bin/python -m pip --version >/dev/null 2>&1; then break; fi
  done
  [ -x .venv/bin/python ] || { echo "  ✗ 파이썬 가상환경을 못 만들었습니다 — brew install python@3.12 후 다시"; exit 1; }
fi
.venv/bin/pip install -q --upgrade pip
.venv/bin/pip install -q -r requirements.txt
ok ".venv ($(.venv/bin/python --version))"

step "5. 기본 효과음·샘플 그림"
.venv/bin/python samples/엔진/scripts/make_sfx.py >/dev/null && ok "효과음 → samples/에셋/sfx/"
.venv/bin/python samples/엔진/scripts/draw_sample.py --sheet >/dev/null && ok "샘플 캐릭터 → samples/에셋/character/character.png"

step "6. 비밀 설정 파일(.env)"
if [ -f .env ]; then ok ".env (이미 있음 — 건드리지 않음)"; else cp .env.example .env; chmod 600 .env; ok ".env 만들었음 (키는 필요할 때 직접 채우기)"; fi

step "7. 샘플 편으로 시험"
node samples/예시편/EP00_샘플/build.js >/dev/null && node samples/엔진/render.js samples/예시편/EP00_샘플 >/dev/null && ok "예시편 카드 7장 → samples/예시편/EP00_샘플/card*.png"

printf "\n\033[1m완료!\033[0m 이제 이 폴더에서 claude 를 실행하고 「인스타툰 하네스 구성해 줘」라고 해 보세요.\n"
