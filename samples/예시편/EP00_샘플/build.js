// EP.00 샘플 «월요일 아침» — 표지 + 본편 6컷 = 7장
// 실행:  node samples/예시편/EP00_샘플/build.js  →  node samples/엔진/render.js samples/예시편/EP00_샘플
// 그림은 AI 없이 코드로 그렸다(samples/엔진/scripts/draw_sample.py). 글자는 전부 여기서 얹는다.
// 저장소 맨 위(package.json 있는 곳)를 찾아 엔진을 불러온다 — 이 폴더를 어디로 복사해도 동작
const ROOT = (function up(d) { return require('fs').existsSync(d + '/package.json') ? d : up(require('path').dirname(d)); })(__dirname);
const { narr, say, think, sfx, em, slide, cover, build, NIGHT } = require(ROOT + '/samples/엔진/lib/toon.js');

const S = [];
// ==================== 여기부터 편집 ====================
S.push(cover({ series: '말랑일기', ep: 'EP.00', hook: `알람 ${em('다섯 번')} 끄고`, title: '월요일 아침', sub: '「5분만 더…」' }));

S.push(slide('s1.png', `
  ${narr('새벽 여섯 시,<br>알람이 울렸어요.', 'top:60px;left:120px;right:120px', { dark: true })}
  ${sfx('띵띵띵', 'top:520px;right:90px', { col: '#fff', sh: NIGHT, rot: 8, size: 60 })}
`));
S.push(slide('s2.png', `
  ${think('딱 5분만 더…', 'top:80px;left:80px;width:440px', { size: 48, dot: 'left' })}
  ${sfx('탁', 'top:600px;left:560px', { col: '#fff', sh: NIGHT, rot: -10, size: 80 })}
`));
S.push(slide('s3.png', `
  ${narr(`눈을 떠 보니 ${em('여덟 시 반')}.`, 'top:60px;left:120px;right:120px')}
  ${sfx('헉!!', 'top:300px;left:90px', { rot: -12, size: 80 })}
`));
S.push(slide('s4.png', `
  ${say('늦었다 늦었다!', 'top:220px;left:300px;width:440px', { size: 46, tailX: '70%', tailRot: 10 })}
  ${sfx('후다닥', 'top:1080px;left:80px', { rot: -8, size: 58 })}
`));
S.push(slide('s5.png', `
  ${narr('그런데 달력을 보니…', 'top:90px;left:150px;right:150px')}
  ${sfx('띠용', 'top:1050px;left:420px', { rot: 6, size: 60 })}
`));
S.push(slide('s6.png', `
  ${narr(`오늘, ${em('쉬는 날')}이었어요.`, 'top:60px;left:120px;right:120px')}
  ${think('다시 잘래…', 'top:300px;left:560px;width:380px', { size: 44, dot: 'left' })}
  ${narr('여러분도 이런 날 있으셨나요?', 'bottom:50px;left:120px;right:120px', { size: 40, bg: '#fffaf2' })}
`));
// ==================== 편집 끝 ====================
build(__dirname, S);
