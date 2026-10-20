# EP.xx «제목» — 장면 프롬프트

> 이 파일 하나로 두 방법이 다 돼요.
> - **기본 — ChatGPT 복붙**(API 키 없음, ChatGPT 구독 웹): `.venv/bin/python samples/엔진/scripts/chatgpt_prompts.py <편 폴더>` → `ChatGPT_복붙.md` / 한 컷씩 `--copy s1`. 받은 그림은 `import_images.py <편 폴더> --apply`.
> - **유료 자동 — OpenAI API**: `.venv/bin/python samples/엔진/scripts/gen_scenes.py --ep <편 폴더> --plan` 으로 비용부터.
> ★형식을 지켜야 스크립트가 읽습니다: (`## 캐릭터 시트` 선택) → `## 공통 헤더` 코드블록 → `## 표지 장면 (s0_cover.png)` → `### 1. 컷 제목` …
> 프롬프트는 영어가 결과가 안정적입니다. Claude에게 「대본 보고 장면 프롬프트 써 줘」라고 하면 이 형식으로 씁니다.

## 캐릭터 시트 (character.png)
> 이 편 주인공을 새로 만들 때만. 먼저 이걸 뽑아 마음에 들면, 모든 컷에 이 그림을 첨부해요. 샘플 캐릭터 「말랑이」를 쓰면 지워도 돼요.
```
Front view, full body, of ONE original cute character: (생김새·색·옷·소품을 문장으로). Simple FLAT cartoon, clean thick outline, solid muted colors. Below it, three small head shots: happy, surprised, sad.
```

## 공통 헤더` 코드블록 1개 → `## 표지 장면 (s0_cover.png)` 코드블록 → `### 1. 컷 제목` 코드블록 …
> 프롬프트는 영어가 결과가 안정적입니다. Claude에게 「대본 보고 장면 프롬프트 써 줘」라고 하면 이 형식으로 씁니다.

## 공통 헤더 (모든 컷 앞에 자동으로 붙음)
```
[STYLE] simple FLAT cartoon, clean thick outline, solid muted color fills, cozy Korean daily-life webtoon look.
[STYLE-LOCK] Match the attached character reference exactly: same body shape, same colors, same face.
Simple SOLID dark dot eyes (NO glossy anime eyes). FLAT shading only — NO gradients, NO glow.
[EXPRESSION] Expressions BIG and readable but on-model: change EYE SHAPE, EYEBROWS, MOUTH, blush, sweat drops.
[CAMERA] Never repeat the same staging twice in a row. Vary shot size and angle (wide / medium / close; eye level / low / high).
[CAST] EXACTLY ONE main character in any picture. Other people are FACELESS: the TOP EDGE of the picture cuts them at chest
height so the head is outside the picture. Far-away people are seen from behind.
[NO-GO] NO written characters anywhere — no letters, no numbers, no signs, no clock numerals.
[COMPOSITION] Leave generous EMPTY SPACE at the top for captions. NO speech bubbles, NO text. Vertical 4:5.
```

## 표지 장면 (s0_cover.png)
```
Medium shot. The main character ... (표지 장면 설명)
```

### 1. 컷 제목
```
Wide shot from a high angle. ... (이 컷의 장소·동작·표정·카메라를 문장으로)
```

### 2. 컷 제목
```
Close-up at eye level. ...
```
