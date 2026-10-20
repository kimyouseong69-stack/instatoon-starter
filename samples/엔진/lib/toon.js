// 인스타툰 컷 조립 공용 도구
// 편 폴더의 build.js 가 이 파일을 불러서 쓴다:
//   const T = require('<저장소>/samples/엔진/lib/toon.js');   (예시: samples/예시편/_템플릿/build.js)
//   T.slide('s1.png', T.narr('...', 'top:60px;left:80px;right:80px'))
//   T.build(__dirname, [ ...슬라이드 ])  → instagram_cards.html
//
// 글꼴(전부 상업 사용 가능한 OFL, samples/에셋/fonts/ 에 동봉)
//   나레이션 = 나눔스퀘어라운드 Bold / 대사·생각 = Gaegu / 표지·효과음 = Jua
const fs = require('fs'), path = require('path');

const W = 1080, H = 1350;
const INK = '#4a3e36';
const KEY = '#d83a5e';                         // 강조 키워드 색 — 내 브랜드 색으로 바꿔 쓰세요
const NIGHT = 'rgba(14,20,44,.95)';            // 어두운 컷 효과음 글로우

// 나레이션 — 반투명 받침
function narr(text, css, opt = {}) {
  const size = opt.size || 46, align = opt.align || 'center', dark = opt.dark;
  const bg = opt.bg || (dark ? 'rgba(38,35,46,.74)' : 'rgba(255,251,243,.90)');
  const fg = dark ? '#efe9f0' : (opt.col || '#33271f');
  return `<div style="position:absolute;${css};font-family:'NSR',sans-serif;font-weight:700;
    font-size:${size}px;line-height:1.4;color:${fg};text-align:${align};word-break:keep-all;
    background:${bg};border-radius:20px;padding:15px 24px;box-shadow:0 4px 14px rgba(0,0,0,.11)">${text}</div>`;
}

// 말풍선(대사) — 꼬리는 tailX(가로 위치 '50%') + tailRot(각도)로 말하는 캐릭터를 향하게
function say(text, css, opt = {}) {
  const size = opt.size || 40, bg = opt.bg || 'rgba(255,255,255,.92)', col = opt.col || '#2b2b2b';
  const tx = opt.tailX || '50%', rot = opt.tailRot || 0;
  const rad = opt.radius === undefined ? 30 : opt.radius;
  const line = opt.line || INK;
  const tf = `translateX(-50%) rotate(${rot}deg)`;
  return `<div style="position:absolute;${css};background:${bg};border:4px solid ${line};border-radius:${rad}px;
    padding:16px 24px;font-family:'Gaegu',sans-serif;font-weight:700;font-size:${size}px;line-height:1.3;
    color:${col};text-align:center;word-break:keep-all;box-shadow:0 6px 16px rgba(74,62,54,.15)">${text}
    <div style="position:absolute;bottom:-23px;left:${tx};transform-origin:top center;transform:${tf};
      width:0;height:0;border-left:15px solid transparent;border-right:15px solid transparent;border-top:26px solid ${line}"></div>
    <div style="position:absolute;bottom:-15px;left:${tx};transform-origin:top center;transform:${tf};
      width:0;height:0;border-left:11px solid transparent;border-right:11px solid transparent;border-top:19px solid ${bg}"></div></div>`;
}

// 생각풍선(구름) — dot 은 캐릭터 쪽('left' / 'right')
function think(text, css, opt = {}) {
  const size = opt.size || 38, col = opt.col || '#555', bg = opt.bg || 'rgba(255,255,255,.92)', dotside = opt.dot || 'left';
  const dx = dotside === 'left' ? 'left:34px' : 'right:34px';
  return `<div style="position:absolute;${css};background:${bg};border:4px solid ${INK};border-radius:50%/44%;
    padding:18px 26px;font-family:'Gaegu',sans-serif;font-weight:700;font-size:${size}px;line-height:1.3;
    color:${col};text-align:center;word-break:keep-all">${text}
    <div style="position:absolute;bottom:-14px;${dx};width:16px;height:16px;border-radius:50%;background:${bg};border:4px solid ${INK}"></div>
    <div style="position:absolute;bottom:-32px;${dx};margin-left:-6px;width:9px;height:9px;border-radius:50%;background:${bg};border:3px solid ${INK}"></div></div>`;
}

// 효과음 — 살짝 기울임. 어두운 컷은 밝은 글자 + 어두운 글로우: sfx('삐—', css, {col:'#fff', sh:NIGHT})
// ★릴스 변환기가 이 글자를 읽어 효과음을 고른다(samples/엔진/reel/profiles/sfxmap.json)
function sfx(text, css, opt = {}) {
  const size = opt.size || 44, rot = opt.rot || -6, col = opt.col || INK;
  const sh = opt.sh || '#fff';
  return `<div style="position:absolute;${css};font-family:'Jua',sans-serif;font-size:${size}px;color:${col};
    transform:rotate(${rot}deg);text-shadow:0 0 3px ${sh},0 0 7px ${sh},0 0 12px ${sh},0 2px 4px rgba(0,0,0,.22);letter-spacing:2px">${text}</div>`;
}

// 표지 큰 글씨 — 흰 테두리 글자
function outline(text, css, opt = {}) {
  const size = opt.size || 70, col = opt.col || '#4a3a30', sw = opt.sw || 8, stroke = opt.stroke || '#fff';
  return `<div style="position:absolute;${css};font-family:'Jua',sans-serif;font-size:${size}px;
    line-height:1.12;color:${col};text-align:center;word-break:keep-all;
    -webkit-text-stroke:${sw}px ${stroke};paint-order:stroke fill;">${text}</div>`;
}

// 강조 글자
const em = t => `<span style="color:${KEY}">${t}</span>`;

// 본편 한 장 = 그림(scenes/sN.png) + 글자들
// ★릴스 변환기는 slide('sN.png') 를 보고 「글자 없는 판」을 찾는다 — 첫 인자는 꼭 따옴표 문자열로
function slide(img, overlays = '') {
  return `<div class="slide" style="position:relative;width:${W}px;height:${H}px;overflow:hidden;background:#fff">
    <img src="scenes/${img}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">
    ${overlays}</div>`;
}

// 표지 = 그림(s0_cover.png) + 시리즈 이름·편 번호·훅·제목·부제
function cover({ img = 's0_cover.png', series = '', ep = '', hook = '', title = '', sub = '' } = {}) {
  return `<div class="slide" style="position:relative;width:${W}px;height:${H}px;overflow:hidden;background:#fff">
  <img src="${img}" style="position:absolute;inset:0;width:100%;height:100%;object-fit:cover">
  <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(58,42,34,.70) 0%,rgba(58,42,34,.30) 32%,rgba(58,42,34,0) 48%)"></div>
  ${series ? `<div style="position:absolute;top:48px;left:54px;background:#f6e9df;color:#3a2f2a;font-family:'Jua',sans-serif;font-size:32px;padding:9px 26px;border-radius:10px">${series}</div>` : ''}
  ${ep ? `<div style="position:absolute;top:56px;right:60px;font-family:'Jua',sans-serif;font-size:34px;color:#f2d3c4">${ep}</div>` : ''}
  ${hook ? `<div style="position:absolute;top:120px;left:0;right:0;text-align:center">
    <span style="display:inline-block;background:rgba(255,250,244,.96);border-radius:999px;padding:11px 34px;
      font-family:'Jua',sans-serif;font-size:46px;line-height:1.12;color:#3a2f2a;box-shadow:0 7px 20px rgba(45,25,15,.4)">${hook}</span></div>` : ''}
  ${title ? outline(title, 'top:212px;left:0;right:0', { size: 96, sw: 9, col: '#fff8f2', stroke: 'rgba(44,22,14,.9)' }) : ''}
  ${sub ? outline(sub, 'top:352px;left:0;right:0', { size: 40, col: '#ffe6d6', sw: 5, stroke: 'rgba(44,22,14,.9)' }) : ''}
</div>`;
}

// 슬라이드 목록 → <편 폴더>/instagram_cards.html
function build(epDir, slides) {
  const fonts = path.relative(epDir, path.join(__dirname, '..', '..', '에셋', 'fonts')).split(path.sep).join('/');
  const html = `<!doctype html><html><head><meta charset="utf-8">
<style>
  @font-face{font-family:'NSR';src:url('${fonts}/NanumSquareRoundB.ttf');}
  @font-face{font-family:'Gaegu';src:url('${fonts}/Gaegu-Bold.ttf');font-weight:700;}
  @font-face{font-family:'Jua';src:url('${fonts}/Jua-Regular.ttf');}
  *{margin:0;padding:0;box-sizing:border-box}b{color:inherit}
</style></head><body>
${slides.join('\n')}
</body></html>`;
  fs.writeFileSync(path.join(epDir, 'instagram_cards.html'), html);
  console.log(`✅ ${slides.length}장 조립 → instagram_cards.html`);
}

module.exports = { W, H, INK, KEY, NIGHT, narr, say, think, sfx, outline, em, slide, cover, build };
