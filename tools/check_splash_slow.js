// 弱网下的开屏回归：把带宽压到 4 Mbps，确认真会出现「进度面板」，
// 而且百分比在动、阶段文案正确、没有英文残留。
//
// 用法：DIRECT=1 SITE_URL=http://127.0.0.1:8090/ node tools/check_splash_slow.js
const { chromium } = require('playwright');
const fs = require('fs');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8090/';
const OUT = process.env.SHOT_DIR || 'build/shots';
const KBPS = parseInt(process.env.KBPS || '500', 10);   // 500 KB/s ≈ 4 Mbps

const args = ['--enable-unsafe-swiftshader', '--use-gl=swiftshader',
  '--proxy-bypass-list=127.0.0.1;localhost'];
if (process.env.DIRECT === '1') args.push('--no-proxy-server');

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch({ args });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

  const cdp = await page.context().newCDPSession(page);
  await cdp.send('Network.enable');
  await cdp.send('Network.emulateNetworkConditions', {
    offline: false, latency: 60,
    downloadThroughput: KBPS * 1024, uploadThroughput: 128 * 1024
  });

  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });

  const snaps = [];
  for (const at of [3500, 7000, 12000]) {
    const wait = at - (Date.now() - t0);
    if (wait > 0) await page.waitForTimeout(wait);
    const st = await page.evaluate(() => {
      const r = document.getElementById('chaoshiBoot');
      const num = document.querySelector('#chaoshiBoot .cb-num');
      const name = document.querySelector('#chaoshiBoot .cb-stage-name');
      return {
        on: !!r,
        pct: num ? num.textContent.trim() : '',
        stage: name ? name.textContent.trim() : '',
        panel: r ? /cb-panel-on/.test(r.className) : false
      };
    });
    snaps.push({ at, ...st });
    await page.screenshot({ path: `${OUT}/slow_${at}.png` });
  }

  console.log(JSON.stringify({ kbps: KBPS, snaps, errors: errors.slice(0, 3) }, null, 2));
  await browser.close();
})();
