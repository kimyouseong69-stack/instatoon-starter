---
name: toon-reel
description: 완성된 인스타툰 카드를 릴스(9:16 영상)로 바꾼다 — 줌·흔들림·전환·글자 등장 + 효과음. 「릴스로 만들어」「릴스툰」「영상으로」「효과음 바꿔」 요청 시 사용.
---

> **참고용 예시입니다.** harness 로 내 하네스를 만들 때 「완성된 스킬은 이런 모양」을 보여 주는 견본이에요. 이 폴더에 있으면 클로드가 자동으로 켜지 않습니다(.claude/skills/ 에 있어야 켜짐).


# 툰 → 릴스

전제: 그 편의 캐러셀(card*.png)을 사용자가 확정했다. 캐러셀이 바뀌면 릴스를 다시 만들어야 하니 먼저 만들지 않는다.

1. 계획: `.venv/bin/python samples/엔진/reel/toon_reel.py episodes/<편> --plan` → `reel.json`
   - 컷 길이 = 글자 수로 자동 계산, 효과음 = 카드에 그린 효과음 글자로 자동 선택(`samples/엔진/reel/profiles/sfxmap.json`)
   - 총 길이 15~60초인지 확인. 고치려면 reel.json 의 dur(초)·trans(fade/swipe/cut/zoom/dip/white)·sfx 를 고친다.
2. 렌더: `.venv/bin/python samples/엔진/reel/toon_reel.py episodes/<편>` → `episodes/<편>/reel/reel.mp4`
   - reel.json 이 이미 있으면 그걸 쓴다. 처음부터 다시 계획하려면 reel.json 을 지우고 1번부터.
3. 스스로 검수:
   - 프레임 시트: `ffmpeg -v error -y -i reel.mp4 -vf "fps=1/1.5,scale=216:384,tile=7x2" -frames:v 1 _sheet.png` → 열어서 잘림·겹침 확인
   - 음량: `ffmpeg -i reel.mp4 -af ebur128=peak=true -f null - 2>&1 | tail -12` → -14 LUFS 근처
4. 결과 경로·길이를 사용자에게. 사용자가 원하면 `open episodes/<편>/reel/reel.mp4`

음악: 기본은 BGM 없음 → 인스타 앱에서 올릴 때 인스타 음악을 붙이는 게 안전(인스타 음악은 파일에 넣으면 안 됨).
API로 올릴 땐 음악 없이 올라간다. 직접 고른 무료 BGM 은 `samples/에셋/bgm/` + 프로필 bgm.
