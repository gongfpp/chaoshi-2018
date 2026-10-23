// 验证环境音分层：进入剧情后 amb/*.ogg 是否被实际拉取、有无缺文件报错。
// 依据：amb/pa 不在 progressive_download 的常驻清单里，只有真正播放时才会请求。
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8087/';

(async () => {
  const browser = await chromium.launch({
    args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader',
           '--autoplay-policy=no-user-gesture-required',
           '--proxy-bypass-list=127.0.0.1;localhost'],
  });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });

  const audioReq = [];
  const errors = [];
  page.on('request', r => {
    const u = r.url();
    const m = u.match(/audio\/(amb|pa)\/([a-z0-9_]+)\.ogg/);
    if (m) audioReq.push(m[1] + '/' + m[2]);
  });
  page.on('response', r => {
    const u = r.url();
    if (/audio\/(amb|pa)\//.test(u) && r.status() >= 400) {
      errors.push('HTTP ' + r.status() + ' ' + u.split('/').pop());
    }
  });
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));
  page.on('console', m => {
    const t = m.text();
    if (m.type() === 'error' && !/favicon/.test(t)) errors.push(t);
  });

  await page.goto(URL + '?nointro', { waitUntil: 'domcontentloaded', timeout: 90000 });
  for (let i = 0; i < 90; i++) {
    const w = await page.evaluate(() => {
      const c = document.querySelector('canvas');
      return c ? c.width : 0;
    });
    if (w > 640) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(4000);

  // 主菜单 → 开始（1280×720 下按钮文字在 x≈104–184、y≈330–372）
  await page.mouse.click(120, 352);
  await page.waitForTimeout(3200);
  await page.screenshot({ path: 'build/shots/audio-01-start.png' });

  // 章节卡后进入正文，推进若干句，让 scene 指令与环境音都过一遍
  for (let i = 0; i < 14; i++) {
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1100);
  }
  await page.waitForTimeout(1500);
  await page.screenshot({ path: 'build/shots/audio-02-text.png' });

  const seen = [...new Set(audioReq)];
  console.log('AUDIO_REQ:', seen.length, JSON.stringify(seen.slice(0, 20)));
  console.log('AMB_COUNT:', seen.filter(x => x.startsWith('amb/')).length);
  console.log('PA_COUNT:', seen.filter(x => x.startsWith('pa/')).length);
  console.log('ERRORS:', errors.length, JSON.stringify(errors.slice(0, 5)));

  await browser.close();
})();
