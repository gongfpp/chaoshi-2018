// 打开章节目录并跳转一章，验证不崩、界面正常。
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8087/';

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

  // 主菜单：点击「章节目录」
  await page.mouse.click(112, 416);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'build/shots/jump_01_list.png' });

  // 点击第三章（列表第三行）
  await page.mouse.click(400, 302);
  await page.waitForTimeout(3500);
  await page.screenshot({ path: 'build/shots/jump_02_ch12.png' });
  await page.keyboard.press('Enter');
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'build/shots/jump_03_ch12_text.png' });

  console.log('errors:', errors.length, errors.slice(0, 3).join(' | '));
  await browser.close();
})();
