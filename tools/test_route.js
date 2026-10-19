// 快进通关测试：按住 Ctrl 跳过，周期性按 Enter 选择默认选项，直到结局。
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader'] });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));

  await page.goto('http://127.0.0.1:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(30000);

  // 开始游戏
  await page.mouse.click(130, 360);
  await page.waitForTimeout(3000);

  await page.keyboard.down('Control');
  for (let i = 0; i < 14; i++) {
    await page.waitForTimeout(9000);
    await page.keyboard.up('Control');
    await page.keyboard.press('Enter');   // 遇到选项时选第一项
    await page.waitForTimeout(500);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(400);
    await page.screenshot({ path: `build/shots/routeA_${String(i).padStart(2,'0')}.png` });
    await page.keyboard.down('Control');
  }
  await page.keyboard.up('Control');
  await page.waitForTimeout(1000);
  await page.screenshot({ path: 'build/shots/routeA_end.png' });
  console.log('ERRORS:', JSON.stringify(errors.slice(0, 5)));
  await browser.close();
})();
