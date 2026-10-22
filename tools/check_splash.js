// 开屏/装载层的视觉与行为回归。
// 用法：DIRECT=1 SITE_URL=http://127.0.0.1:8090/ node tools/check_splash.js
//
// 抓四个时间点的截图（黑场/片名/台词+底图/进度），等游戏真正可交互后
// 再截一张，并断言：#chaoshiBoot 已移除、没有英文残留、没有错误态。
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8090/';
const OUT = process.env.SHOT_DIR || 'build/shots';

(async () => {
  fs.mkdirSync(OUT, { recursive: true });

  const args = ['--enable-unsafe-swiftshader', '--use-gl=swiftshader',
    '--proxy-bypass-list=127.0.0.1;localhost'];
  if (process.env.DIRECT === '1') args.push('--no-proxy-server');

  const browser = await chromium.launch({ args });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

  const errors = [];
  const failedReq = [];
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('requestfailed', r => failedReq.push(r.url() + ' ' + (r.failure() || {}).errorText));

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });

  const shots = [
    ['splash_1_black', 700],
    ['splash_2_title', 1500],
    ['splash_3_line', 2600],
    ['splash_4_progress', 4200],
  ];
  let elapsed = 0;
  for (const [name, at] of shots) {
    const wait = at - (Date.now() - t0);
    if (wait > 0) await page.waitForTimeout(wait);
    try {
      await page.screenshot({ path: path.join(OUT, name + '.png') });
      console.log('shot', name, '@', Date.now() - t0, 'ms');
    } catch (e) { console.log('shot failed', name, e.message); }
    elapsed = Date.now() - t0;
  }

  // 等游戏可交互
  let ready = false;
  for (let i = 0; i < 60; i++) {
    const st = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      const boot = document.getElementById('chaoshiBoot');
      return {
        w: c ? c.width : 0,
        boot: !!boot,
        loaderDone: !!(window.ChaoshiLoader && window.ChaoshiLoader.isDone())
      };
    });
    if (st.w > 640 && !st.boot) { ready = true; break; }
    await page.waitForTimeout(1000);
  }
  await page.screenshot({ path: path.join(OUT, 'splash_5_ingame.png') });

  // DOM 里不该再有英文装载文案
  const leftovers = await page.evaluate(() => {
    const bad = [];
    const t = (document.body.innerText || '');
    ['Downloading', 'Could not download', 'Download error', 'More information']
      .forEach(k => { if (t.indexOf(k) >= 0) bad.push(k); });
    return bad;
  });

  const hasErr = await page.evaluate(() => {
    const e = document.querySelector('#chaoshiBoot.cb-dead');
    return !!e;
  });

  console.log(JSON.stringify({
    ready,
    totalMs: Date.now() - t0,
    leftoverEnglish: leftovers,
    errorState: hasErr,
    consoleErrors: errors.slice(0, 5),
    failedRequests: failedReq.slice(0, 5)
  }, null, 2));

  await browser.close();
  process.exit(ready && !hasErr && leftovers.length === 0 ? 0 : 1);
})();
