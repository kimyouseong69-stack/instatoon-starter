// 카드 렌더러: <편 폴더>/instagram_cards.html 의 .slide 하나하나 → card1.png, card2.png …
// 사용: node samples/엔진/render.js <편 폴더> [폭=1080] [높이=1350]
const path = require('path');
const fs = require('fs');
const puppeteer = require('puppeteer');      // npm install 때 전용 크롬이 같이 받아짐

const DIR = path.resolve(process.argv[2] || '.');
const W = parseInt(process.argv[3] || '1080', 10);
const H = parseInt(process.argv[4] || '1350', 10);
if (!fs.existsSync(path.join(DIR, 'instagram_cards.html'))) {
  console.error('❌ instagram_cards.html 이 없습니다. 먼저 node build.js 를 실행하세요:', DIR); process.exit(1);
}
(async () => {
  const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox', '--allow-file-access-from-files'] });
  const page = await browser.newPage();
  await page.setViewport({ width: W, height: 16000, deviceScaleFactor: 2 });
  await page.goto('file://' + path.join(DIR, 'instagram_cards.html'), { waitUntil: 'load' });
  await page.evaluate(() => document.fonts.ready);
  await new Promise(r => setTimeout(r, 500));
  const count = await page.$$eval('.slide', s => s.length);
  console.log(`슬라이드 ${count}장 (${W}x${H})`);
  for (let i = 0; i < count; i++) {
    const box = await page.$$eval('.slide', (slides, idx) => {
      const r = slides[idx].getBoundingClientRect(); return { x: r.x, y: r.y };
    }, i);
    await page.screenshot({ path: path.join(DIR, `card${i + 1}.png`), clip: { x: box.x, y: box.y, width: W, height: H } });
    console.log(`  ✓ card${i + 1}.png`);
  }
  await browser.close();
  console.log('✅ 완료');
})().catch(e => { console.error(e); process.exit(1); });
