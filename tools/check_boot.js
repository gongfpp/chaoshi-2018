// 检查站点能否真正启动：等到 canvas 尺寸变为 1280x720（默认 stub 是 300x150）。
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8083/';
const PROXY = process.env.PROXY || '';

(async () => {
  const args = ['--enable-unsafe-swiftshader', '--use-gl=swiftshader',
    '--proxy-bypass-list=127.0.0.1;localhost'];
  if (PROXY) args.push(`--proxy-server=${PROXY}`);
  if (process.env.DIRECT === '1') args.push('--no-proxy-server');   // 真·直连，绕过系统代理
  const browser = await chromium.launch({ args });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  const req = { total: 0, parts: 0 };
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('request', r => {
    req.total++;
    if (/game\.zip\.\d{3}/.test(r.url())) req.parts++;
  });

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });
  let ready = false;
  for (let i = 0; i < 45; i++) {
    const st = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return c ? { w: c.width, h: c.height } : null;
    });
    if (st && st.w > 640) {
      ready = true;
      console.log('启动成功：', Date.now() - t0, 'ms，canvas', st.w + 'x' + st.h);
      break;
    }
    await page.waitForTimeout(2000);
  }
  await page.screenshot({ path: 'build/shots/boot_check.png' });
  console.log('ready:', ready, '| requests:', JSON.stringify(req),
    '| errors:', errors.length, errors.slice(0, 3).join(' | '));
  await browser.close();
})();
