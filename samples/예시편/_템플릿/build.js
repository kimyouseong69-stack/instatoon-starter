// EP.xx «제목» — 대본.md 를 보고 채우세요
// 실행:  node <편 폴더>/build.js  →  node samples/엔진/render.js <편 폴더>
// 그림 = scenes/s1.png … (AI 작화 또는 직접 그린 그림), 표지 = s0_cover.png
// 저장소 맨 위(package.json 있는 곳)를 찾아 엔진을 불러온다 — 이 폴더를 어디로 복사해도 동작
const ROOT = (function up(d) { return require('fs').existsSync(d + '/package.json') ? d : up(require('path').dirname(d)); })(__dirname);
const { narr, say, think, sfx, em, slide, cover, build, NIGHT } = require(ROOT + '/samples/엔진/lib/toon.js');

const S = [];
// ==================== 여기부터 편집 ====================
S.push(cover({ series: '시리즈 이름', ep: 'EP.01', hook: '한 줄 훅', title: '큰 제목', sub: '「부제」' }));

S.push(slide('s1.png', `
  ${narr('나레이션은 꼭 필요할 때만.', 'top:60px;left:120px;right:120px')}
`));
S.push(slide('s2.png', `
  ${say('말풍선 대사', 'top:200px;left:300px;width:420px', { tailX: '50%', tailRot: 0 })}
  ${sfx('쿵', 'top:900px;left:120px', { rot: -8, size: 60 })}
`));
// ==================== 편집 끝 ====================
build(__dirname, S);
