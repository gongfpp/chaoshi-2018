// 验证「无 game.zip」的目录模式能否启动；同时记录关键资源请求数与失败原因。
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8082/';

(async () => {
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader', '--proxy-bypass-list=127.0.0.1;localhost'],
  });
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  const errors = [];
  const req = { total: 0, game: 0, zip: 0 };
  page.on('console', m => { if (m.type() === 'error') errors.push(m.text()); });
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('request', r => {
    req.total++;
    const u = r.url();
    if (u.includes('/game/')) req.game++;
    if (u.includes('game.zip')) req.zip++;
  });

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 60000 });
  let ok = false;
  for (let i = 0; i < 30; i++) {
    await page.waitForTimeout(2000);
    const st = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return c ? { width: c.width, height: c.height } : null;
    });
    if (st && st.width > 640) { ok = true; console.log('canvas ready after', Date.now() - t0, 'ms:', st.width + 'x' + st.height); break; }
  }
  await page.screenshot({ path: 'build/shots/nozip_check.png' });
  console.log('canvas:', ok, '| requests:', JSON.stringify(req));
  console.log('errors:', errors.length, errors.slice(0, 4).join(' | '));
  await browser.close();
})();
