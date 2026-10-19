// 验证线上 GitHub Pages 版本能否真正启动（wasm 编译、资源加载、进入对白）。
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'https://gongfpp.github.io/chaoshi-2018/';
const PROXY = process.env.PROXY || 'http://127.0.0.1:7897';

(async () => {
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader', `--proxy-server=${PROXY}`],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 }, deviceScaleFactor: 1 });
  const errors = [];
  const failed = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('requestfailed', r => failed.push(r.url() + ' ' + (r.failure() && r.failure().errorText)));

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
  console.log('loaded html in', Date.now() - t0, 'ms');

  await page.waitForTimeout(45000);
  await page.screenshot({ path: 'build/shots/live_01_title.png' });

  // 点击「开始」
  await page.mouse.click(130, 360);
  await page.waitForTimeout(4000);
  await page.screenshot({ path: 'build/shots/live_02_card.png' });

  for (let i = 0; i < 6; i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1200);
  }
  await page.screenshot({ path: 'build/shots/live_03_dialogue.png' });

  const canvas = await page.evaluate(() => {
    const c = document.querySelector('canvas');
    return c ? { w: c.width, h: c.height } : null;
  });

  console.log('canvas:', JSON.stringify(canvas));
  console.log('console errors:', errors.length, errors.slice(0, 5).join(' | '));
  console.log('failed requests:', failed.length, failed.slice(0, 5).join(' | '));
  await browser.close();
})();
