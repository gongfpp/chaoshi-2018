// 性能探针：量线上网页版的渲染开销与交互延迟。
// 用法：SITE_URL=https://chaoshi-2018.pages.dev/ node tools/perf_probe.js
const { chromium, webkit } = require('playwright');

const URL = process.env.SITE_URL || 'https://chaoshi-2018.pages.dev/';
const PROXY = process.env.PROXY || 'http://127.0.0.1:7897';
const ENGINE = process.env.BROWSER || 'chromium';

(async () => {
  const browser = ENGINE === 'webkit'
    ? await webkit.launch({ proxy: { server: PROXY } })
    : await chromium.launch({
        args: [
          `--proxy-server=${PROXY}`,
          '--enable-unsafe-swiftshader',
          '--use-gl=angle',
          '--ignore-gpu-blocklist',
        ],
      });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 2 });

  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));

  // 主线程长任务
  await page.addInitScript(() => {
    window.__longtasks = [];
    try {
      new PerformanceObserver(list => {
        for (const e of list.getEntries()) {
          window.__longtasks.push([Math.round(e.startTime), Math.round(e.duration)]);
        }
      }).observe({ entryTypes: ['longtask'] });
    } catch (e) {}
  });

  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 120000 });
  for (let i = 0; i < 90; i++) {
    const w = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return c ? c.width : 0;
    });
    if (w > 640) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(4000);

  const info = await page.evaluate(() => {
    const c = document.querySelector('canvas');
    let renderer = 'n/a';
    try {
      const gl = c.getContext('webgl2') || c.getContext('webgl');
      const ext = gl.getExtension('WEBGL_debug_renderer_info');
      renderer = ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    } catch (e) { renderer = 'err:' + e.message; }
    return {
      dpr: window.devicePixelRatio,
      canvasW: c ? c.width : 0,
      canvasH: c ? c.height : 0,
      cssW: c ? c.clientWidth : 0,
      cssH: c ? c.clientHeight : 0,
      renderer,
      build: window.CHAOSHI_BUILD || null,
      longtasks: (window.__longtasks || []).length,
    };
  });

  // 帧率：连续 5 秒统计 rAF 回调次数
  const fps = await page.evaluate(() => new Promise(res => {
    let n = 0;
    const t0 = performance.now();
    (function loop() {
      n++;
      if (performance.now() - t0 < 5000) requestAnimationFrame(loop);
      else res(Math.round((n / (performance.now() - t0)) * 10000) / 10);
    })();
  }));

  // 交互延迟：主菜单按钮区域来回移动，记录每次 mouseover 到下一帧的时间
  const moves = [];
  for (let i = 0; i < 6; i++) {
    const t0 = Date.now();
    await page.mouse.move(112, i % 2 ? 366 : 416);
    await page.mouse.move(112, i % 2 ? 416 : 366, { steps: 4 });
    await page.waitForTimeout(60);
    moves.push(Date.now() - t0);
  }

  const after = await page.evaluate(() => ({
    longtasks: (window.__longtasks || []).slice(-20),
    heap: performance.memory ? Math.round(performance.memory.usedJSHeapSize / 1048576) : -1,
    prefetch: window.ChaoshiLoader && window.ChaoshiLoader._prefetch ? window.ChaoshiLoader._prefetch : null,
  }));

  console.log(JSON.stringify({ info, fps, moveMs: moves, after, errors: errors.slice(0, 5) }, null, 2));
  await browser.close();
})();
