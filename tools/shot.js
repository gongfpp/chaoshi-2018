// 用无头 Chromium 打开网页版，截图并读取控制台错误。
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));

  await page.goto('http://127.0.0.1:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(30000);
  await page.screenshot({ path: 'build/shots/01_title.png' });

  await page.mouse.click(130, 360);
  await page.waitForTimeout(3500);
  await page.screenshot({ path: 'build/shots/02_chapter_card.png' });

  for (let i = 0; i < 8; i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1100);
  }
  await page.screenshot({ path: 'build/shots/03_dialogue.png' });

  for (let i = 0; i < 12; i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(700);
  }
  await page.screenshot({ path: 'build/shots/04_dialogue2.png' });

  await page.keyboard.press('Escape');
  await page.waitForTimeout(1800);
  await page.screenshot({ path: 'build/shots/05_menu.png' });

  console.log('ERRORS:', JSON.stringify(errors.slice(0, 10), null, 2));
  await browser.close();
})();
