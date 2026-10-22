// 本地验证：进对白 → 开菜单 → 开历史，截图并统计各阶段长任务。
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8080/';

(async () => {
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=angle', '--proxy-bypass-list=127.0.0.1;localhost'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('console', m => { if (m.type() === 'error' && !/501|api\/collect/.test(m.text())) errors.push(m.text()); });

  await page.addInitScript(() => {
    window.__lt = [];
    try {
      new PerformanceObserver(l => {
        for (const e of l.getEntries()) window.__lt.push([Math.round(e.startTime), Math.round(e.duration)]);
      }).observe({ entryTypes: ['longtask'] });
    } catch (e) {}
  });

  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 120000 });
  for (let i = 0; i < 90; i++) {
    const w = await page.evaluate(() => (document.querySelector('canvas') || {}).width || 0);
    if (w > 640) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(3000);

  await page.mouse.click(112, 366);            // 主菜单「开始」
  await page.waitForTimeout(3000);             // 章节卡

  const marks = {};
  for (let i = 0; i < 10; i++) { await page.keyboard.press('Enter'); await page.waitForTimeout(700); }
  await page.screenshot({ path: 'build/shots/perf-01-dialogue.png' });

  marks.beforeMenu = await page.evaluate(() => window.__lt.length);
  await page.keyboard.press('Escape');
  await page.waitForTimeout(1500);
  marks.menuTasks = await page.evaluate(m => window.__lt.slice(m), marks.beforeMenu);
  await page.screenshot({ path: 'build/shots/perf-02-menu.png' });

  // 菜单左栏「历史」在第一项
  marks.beforeHistory = await page.evaluate(() => window.__lt.length);
  await page.mouse.click(100, 227);
  await page.waitForTimeout(2000);
  marks.historyTasks = await page.evaluate(m => window.__lt.slice(m), marks.beforeHistory);
  await page.screenshot({ path: 'build/shots/perf-03-history.png' });

  console.log(JSON.stringify({ marks, errors: errors.slice(0, 5) }, null, 2));
  await browser.close();
})();
