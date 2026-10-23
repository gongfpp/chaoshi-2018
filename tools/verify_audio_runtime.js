// 运行时验证：进第一章，推进到出餐口场景（环境音 + 播报都在这一段），
// 确认无异常、画面正常。
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader',
           '--autoplay-policy=no-user-gesture-required',
           '--proxy-bypass-list=127.0.0.1;localhost'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !/favicon|501/.test(m.text())) errors.push(m.text()); });

  await page.goto('http://127.0.0.1:8087/?nointro', { waitUntil: 'domcontentloaded', timeout: 90000 });
  for (let i = 0; i < 90; i++) {
    const w = await page.evaluate(() => (document.querySelector('canvas') || {}).width || 0);
    if (w > 640) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(4000);

  await page.mouse.click(120, 352);          // 开始
  await page.waitForTimeout(3000);
  await page.keyboard.press('Enter');        // 跳过章节卡
  await page.waitForTimeout(2500);

  for (let i = 0; i < 8; i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(700);
  }
  // 第一章开场的二选一：选第一项「给姐姐打个电话」
  await page.mouse.click(640, 294);
  await page.waitForTimeout(1800);

  for (let i = 0; i < 85; i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(650);
  }
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'build/shots/audio-03-foodcourt.png' });
  console.log('ERRORS:', errors.length, JSON.stringify(errors.slice(0, 4)));
  await browser.close();
})();
