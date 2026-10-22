// 验证账本入口已移除：进入对白后截图，人工核对右上角与菜单里都没有「账本」。
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8080/';

(async () => {
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader', '--proxy-bypass-list=127.0.0.1;localhost'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });

  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
  for (let i = 0; i < 60; i++) {
    const w = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return c ? c.width : 0;
    });
    if (w > 640) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(3000);
  await page.screenshot({ path: 'build/shots/ledger-01-title.png' });

  // 主菜单点「开始」
  await page.mouse.click(112, 366);
  await page.waitForTimeout(3200);
  for (let i = 0; i < 8; i++) { await page.keyboard.press('Enter'); await page.waitForTimeout(900); }
  await page.waitForTimeout(1200);
  await page.screenshot({ path: 'build/shots/ledger-02-dialogue.png' });

  console.log('errors:', errors.length, errors.slice(0, 3).join(' | '));
  await browser.close();
})();
