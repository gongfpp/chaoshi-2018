// 弱网/断流的错误路径回归。
//
// 场景一：某一片 game.zip 被彻底打断（模拟「链路一直给不了这一片」）
//   → 应当出现中文错误面板（.cb-dead），不能是英文 "Download error"，
//     也不能永远白屏。
// 场景二：所有资源都正常
//   → 不应出现错误面板（对照组，避免误报）。
//
// 用法：DIRECT=1 SITE_URL=http://127.0.0.1:8090/ node tools/check_boot_fail.js
const { chromium } = require('playwright');
const fs = require('fs');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8090/';
const OUT = process.env.SHOT_DIR || 'build/shots';

const args = ['--enable-unsafe-swiftshader', '--use-gl=swiftshader',
  '--proxy-bypass-list=127.0.0.1;localhost'];
if (process.env.DIRECT === '1') args.push('--no-proxy-server');

async function run(blockPart) {
  const browser = await chromium.launch({ args });
  const page = await browser.newPage({ viewport: { width: 1280, height: 720 } });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGEERROR ' + e.message));

  if (blockPart) {
    await page.route('**/game.zip.*', route => {
      if (route.request().url().indexOf(blockPart) !== -1) {
        return route.abort('connectionfailed');
      }
      return route.continue();
    });
  }

  const t0 = Date.now();
  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 90000 });

  let state = null;
  for (let i = 0; i < 80; i++) {
    state = await page.evaluate(() => ({
      dead: !!document.querySelector('#chaoshiBoot.cb-dead'),
      boot: !!document.getElementById('chaoshiBoot'),
      why: (document.querySelector('#chaoshiBoot .cb-why') || {}).textContent || '',
      canvas: (document.querySelector('canvas') || {}).width || 0
    }));
    if (state.dead || (state.canvas > 640 && !state.boot)) break;
    await page.waitForTimeout(1000);
  }

  const ms = Date.now() - t0;
  const bodyText = await page.evaluate(() => document.body.innerText || '');
  const english = ['Downloading engine', 'Downloading game data', 'Could not download', 'Download error']
    .filter(k => bodyText.indexOf(k) >= 0);

  await page.screenshot({ path: `${OUT}/boot_fail_${blockPart ? 'broken' : 'ok'}.png` });
  await browser.close();
  return { ms, dead: state.dead, why: state.why, english, errors: errors.slice(0, 3) };
}

(async () => {
  fs.mkdirSync(OUT, { recursive: true });

  const broken = await run('game.zip.003');
  console.log('断流：', JSON.stringify(broken));

  const ok = await run(null);
  console.log('正常：', JSON.stringify(ok));

  const pass =
    broken.dead &&
    broken.english.length === 0 &&
    broken.why.length > 0 &&
    !ok.dead &&
    ok.english.length === 0;

  console.log(pass ? 'PASS' : 'FAIL');
  process.exit(pass ? 0 : 1);
})();
