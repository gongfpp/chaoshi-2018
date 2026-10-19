// 在快进测试版上跑出一条完整路线：定时按 Enter 选择默认项，直到出现结局卡。
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));

  await page.goto('http://127.0.0.1:8081/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(30000);
  await page.mouse.click(130, 360);   // 开始
  await page.waitForTimeout(2000);

  await page.keyboard.down('Control');
  for (let i = 0; i < 40; i++) {
    await page.waitForTimeout(2500);
    await page.keyboard.up('Control');
    await page.keyboard.press('Enter');
    await page.waitForTimeout(300);
    await page.keyboard.press('Enter');
    await page.keyboard.down('Control');
    if (i % 5 === 0) await page.screenshot({ path: `build/shots/route_${String(i).padStart(2,'0')}.png` });
  }
  await page.keyboard.up('Control');
  await page.screenshot({ path: 'build/shots/route_final.png' });
  console.log('ERRORS:', JSON.stringify(errors.slice(0, 5)));
  await browser.close();
})();
