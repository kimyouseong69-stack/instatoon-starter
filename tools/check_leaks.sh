#!/bin/bash
# 깃허브에 올리기 전 비밀 검사 — 올라갈 파일만(git 이 추적하는 것 + 새로 추가될 것) 훑는다.
#   bash tools/check_leaks.sh        → 문제 없으면 「통과」, 있으면 파일:줄 을 보여 주고 실패
cd "$(dirname "$0")/.."
LIST=$(mktemp); git -c core.quotepath=off ls-files -z --cached --others --exclude-standard > "$LIST"
FILES=$(tr '\0' '\n' < "$LIST")
fail=0
say(){ printf "  \033[31m✗\033[0m %s\n" "$1"; fail=1; }

# 1. 올라가면 안 되는 파일
while IFS= read -r f; do
  case "$f" in
    .env|.env.local|*.pem|*token*.json|*secret*.json|.claude/settings.local.json) say "비밀 파일이 올라가려 함: $f";;
  esac
done <<< "$FILES"

# 2. 내용 검사(값은 화면에 안 보여 주고 위치만)
PAT='(sk-[A-Za-z0-9_-]{20,}|sk-proj-[A-Za-z0-9_-]{20,}|IGAA[A-Za-z0-9]{30,}|EAA[A-Za-z0-9]{30,}|THAA[A-Za-z0-9]{30,}|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|AKIA[0-9A-Z]{16}|xox[baprs]-[A-Za-z0-9-]{10,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|[0-9]{8,10}:AA[A-Za-z0-9_-]{30,})'
xargs -0 grep -I -n -E -o "$PAT" < "$LIST" 2>/dev/null | cut -d: -f1,2 | sort -u | while read -r loc; do echo "  ✗ 키·토큰 모양 발견: $loc"; done | tee /tmp/.leak1 >/dev/null
[ -s /tmp/.leak1 ] && { cat /tmp/.leak1; fail=1; }

# 3. 개인 흔적: 내 컴퓨터 경로·사설 IP·이메일
ME="$(whoami)"
xargs -0 grep -I -n -E "/Users/$ME|100\.[0-9]+\.[0-9]+\.[0-9]+|192\.168\.[0-9]+\.[0-9]+|[A-Za-z0-9._%+-]+@(gmail|naver|daum|kakao|icloud)\.[a-z.]+" < "$LIST" 2>/dev/null | cut -d: -f1,2 | sort -u > /tmp/.leak2
if [ -s /tmp/.leak2 ]; then while read -r loc; do say "개인 흔적(경로·IP·이메일): $loc"; done < /tmp/.leak2; fi
rm -f /tmp/.leak1 /tmp/.leak2 "$LIST"

if [ $fail = 0 ]; then printf "\033[32m✓ 통과\033[0m — 올라갈 파일 %s개에서 비밀·개인 흔적 없음\n" "$(echo "$FILES" | wc -l | tr -d ' ')"; else echo "위 항목을 고치기 전에는 올리지 마세요."; exit 1; fi
