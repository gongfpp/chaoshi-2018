// 存档 / 读档回归测试：保存到第 1 格，刷新页面，读取第 1 格，截图比对。
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader'] });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));

  await page.goto('http://127.0.0.1:8080/', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(30000);

  // 开始游戏
  await page.mouse.click(130, 360);
  await page.waitForTimeout(3500);
  for (let i = 0; i < 14; i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(650);
  }
  await page.screenshot({ path: 'build/shots/10_before_save.png' });

  // 打开菜单 → 保存 → 第一格
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
  await page.mouse.click(95, 271);   // 左栏「保存」
  await page.waitForTimeout(1200);
  await page.mouse.click(450, 260);  // 第一格
  await page.waitForTimeout(1200);
  await page.screenshot({ path: 'build/shots/11_saved.png' });

  // 刷新，模拟退出后重新启动
  await page.reload({ waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(30000);
  await page.screenshot({ path: 'build/shots/12_after_reload.png' });

  // 标题 → 读取 → 第一格
  await page.mouse.click(130, 507);  // 「读取」（标题页左栏第 4 项，1280x720 下的 CSS 坐标）
  await page.waitForTimeout(1800);
  await page.screenshot({ path: 'build/shots/13_load_menu.png' });
  await page.mouse.click(450, 260);
  await page.waitForTimeout(2500);
  await page.screenshot({ path: 'build/shots/14_after_load.png' });

  console.log('ERRORS:', JSON.stringify(errors.slice(0, 8), null, 2));
  await browser.close();
})();
