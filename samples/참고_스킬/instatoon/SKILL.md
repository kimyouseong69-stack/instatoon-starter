---
name: instatoon
description: 인스타툰 한 편을 대본부터 카드 이미지까지 만든다. 「인스타툰 만들자」「새 편」「EP 만들기」「이 이야기로 툰」「대본 써 줘」「컷 조립」「카드 다시 뽑아」 요청 시 사용. 릴스는 toon-reel, 업로드는 tools/ig_publish.py.
---

> **참고용 예시입니다.** harness 로 내 하네스를 만들 때 「완성된 스킬은 이런 모양」을 보여 주는 견본이에요. 이 폴더에 있으면 클로드가 자동으로 켜지 않습니다(.claude/skills/ 에 있어야 켜짐).


# 인스타툰 한 편 만들기

상세 규칙은 저장소 맨 위 `CLAUDE.md` 가 단일 출처다. 이 스킬은 순서를 이끈다.

1. **새 편 폴더**: `cp -r samples/예시편/_템플릿 "episodes/EP01_제목"` (번호는 기존 편 다음)
2. **이야기 → 대본**: 사용자에게 상황·꺾이는 지점·남은 마음을 묻고 `대본.md` 표를 채운다. → **확인받기**
3. **그림** — 어느 쪽인지 사용자에게 묻는다.
   - 무료: `samples/엔진/scripts/draw_sample.py` 를 본떠 이 편 장면을 코드로 그린다(도형+표정). 또는 사용자가 직접 그린 그림·사진을 `scenes/s1.png …` 로.
   - 유료(AI): `ai_prompts.md` 를 형식대로 쓰고 → `.venv/bin/python samples/엔진/scripts/gen_scenes.py --ep episodes/<편> --all --plan` 으로 **비용부터 보고** → 확인받고 low 로 실행.
     `.env` 의 OPENAI_API_KEY 가 비어 있으면 터미널 새 탭에서 `bash tools/set_key.sh OPENAI_API_KEY` 를 실행하게 안내(대화창에 붙이지 말라고).
4. **조립**: `build.js` 의 「여기부터 편집」만 채운다 → `node episodes/<편>/build.js`
5. **렌더**: `node samples/엔진/render.js episodes/<편>` → `card*.png`
6. **스스로 검수**: 카드를 직접 열어(Read) 겹침·잘림·글자 크기를 보고 고친다. 자세히 볼 땐 `cd episodes/<편> && ../../.venv/bin/python ../../samples/엔진/scripts/zoom.py 3`
7. **사용자 확인** → 확정되면 `캡션.md` 작성 → 확인
8. 다음: 릴스(toon-reel 스킬) 또는 업로드
