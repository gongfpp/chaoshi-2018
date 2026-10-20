// 模拟「分片只传了一半就断」：首次只返回前 1 MB，之后走真实请求。
// 同时覆盖服务端忽略 Range（返回 200 全量）时的回退路径。
const { chromium } = require('playwright');
const fs = require('fs');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8084/';
const PART = 'game.zip.002';
const FILE = process.env.PART_FILE || '/tmp/web_patched2/game.zip.002';

(async () => {
  const buf = fs.readFileSync(FILE);
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader', '--proxy-bypass-list=127.0.0.1;localhost'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

  let served = 0;
  let rangedRequests = 0;
  await page.route(new RegExp(PART), async route => {
    const req = route.request();
    if (req.headers()['range']) rangedRequests++;
    if (served === 0) {
      served++;
      const half = buf.subarray(0, 1_000_000);
      console.log('首次只返回 1 MB（模拟断流）');
      await route.fulfill({
        status: 200,
        headers: { 'Content-Type': 'application/octet-stream', 'Content-Length': String(half.length) },
        body: half,
      });
      return;
    }
    await route.continue();
  });

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
  let ready = false;
  for (let i = 0; i < 45; i++) {
    const w = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return c ? c.width : 0;
    });
    if (w > 640) { ready = true; break; }
    await page.waitForTimeout(2000);
  }
  console.log('断流后仍启动:', ready, '| 用时', Date.now() - t0, 'ms | Range 重试次数:', rangedRequests);
  await browser.close();
})();
