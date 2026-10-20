#!/bin/bash
# 키·토큰을 화면에 안 보이게 .env 에 넣는다 (발표·녹화 중에도 안전).
#   bash tools/set_key.sh IG_ACCESS_TOKEN
#   bash tools/set_key.sh OPENAI_API_KEY
# ★클로드 창 말고 「터미널 새 탭(command+T)」에서 실행하세요. 붙여 넣어도 글자가 안 보이는 게 정상이에요.
cd "$(dirname "$0")/.."
NAME="$1"
case "$NAME" in
  IG_ACCESS_TOKEN|OPENAI_API_KEY|R2_ACCOUNT_ID|R2_ACCESS_KEY_ID|R2_SECRET_ACCESS_KEY|R2_BUCKET|R2_PUBLIC_BASE) ;;
  *) echo "사용법: bash tools/set_key.sh IG_ACCESS_TOKEN  (또는 OPENAI_API_KEY)"; exit 1;;
esac
[ -f .env ] || cp .env.example .env
printf "%s 붙여 넣고 엔터 (화면에 안 보여요): " "$NAME"
read -rs VAL; echo
VAL="$(printf '%s' "$VAL" | tr -d '[:space:]')"
[ -z "$VAL" ] && { echo "비어 있어서 저장 안 함"; exit 1; }
case "$NAME" in
  IG_ACCESS_TOKEN) [[ "$VAL" == IG* ]] || { echo "⚠️ 인스타 로그인 토큰은 보통 IG 로 시작해요. 다른 걸 복사하신 것 같아요 — 저장 안 함"; exit 1; };;
  OPENAI_API_KEY)  [[ "$VAL" == sk-* ]] || { echo "⚠️ OpenAI 키는 sk- 로 시작해요 — 저장 안 함"; exit 1; };;
esac
TMP=$(mktemp); grep -v "^$NAME=" .env > "$TMP"; printf '%s=%s\n' "$NAME" "$VAL" >> "$TMP"; mv "$TMP" .env; chmod 600 .env
echo "✓ $NAME 저장 (${#VAL}자, 끝 4자리 …${VAL: -4})"
