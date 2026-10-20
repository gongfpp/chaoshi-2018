// 验证裁字后的中文渲染：进游戏 → 对白 → 游戏菜单（密集界面文字）。
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8085/';
const OUT = process.env.OUT || 'build/shots';

(async () => {
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader', '--proxy-bypass-list=127.0.0.1;localhost'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });

  let ready = false;
  for (let i = 0; i < 60; i++) {
    const w = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return c ? c.width : 0;
    });
    if (w > 640) { ready = true; break; }
    await page.waitForTimeout(1000);
  }
  console.log('启动:', ready, '| 用时', Date.now() - t0, 'ms');

  await page.waitForTimeout(3000);
  await page.screenshot({ path: `${OUT}/font_01_title.png` });

  await page.mouse.click(130, 360);
  await page.waitForTimeout(4000);
  await page.screenshot({ path: `${OUT}/font_02_card.png` });

  for (let i = 0; i < 6; i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1200);
  }
  await page.screenshot({ path: `${OUT}/font_03_dialogue.png` });

  // 游戏菜单：文字最密集的地方
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${OUT}/font_04_menu.png` });

  console.log('errors:', errors.length, errors.slice(0, 3).join(' | '));
  await browser.close();
})();
