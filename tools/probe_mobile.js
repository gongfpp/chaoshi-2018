// 收尾验证（临时，不提交）：竖屏提示 / 手机竖屏 / 手机横屏读档 / 手机全文阅读 / 对局内快捷栏
const { chromium } = require('playwright');
const URL = process.env.CS_URL || 'http://127.0.0.1:8080/';
const OUT = process.env.CS_OUT || 'build/shots';
const BOOT = Number(process.env.CS_BOOT || 36000);

function mapper(w, h) {
  const k = Math.min(w / 1280, h / 720);
  return (vx, vy) => [Math.round((w - 1280 * k) / 2 + vx * k), Math.round((h - 720 * k) / 2 + vy * k)];
}

async function open(browser, w, h, mob) {
  const ctx = await browser.newContext({
    viewport: { width: w, height: h },
    deviceScaleFactor: mob ? 3 : 1,
    isMobile: mob,
    hasTouch: mob,
  });
  const page = await ctx.newPage();
  await page.goto(URL + '?nointro', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(BOOT);
  return { ctx, page, tap: mapper(w, h) };
}

(async () => {
  const browser = await chromium.launch({ args: ['--enable-unsafe-swiftshader', '--use-gl=swiftshader'] });

  // 1) 竖屏：应看到「请把手机横过来」
  {
    const { ctx, page } = await open(browser, 390, 844, true);
    await page.waitForTimeout(1500);
    await page.screenshot({ path: `${OUT}/V_portrait.png` });
    console.log('V portrait ok');
    await ctx.close();
  }

  // 2) 手机横屏：进游戏看底部快捷栏 + 用快捷键开全文
  {
    const { ctx, page, tap } = await open(browser, 812, 375, true);
    let [x, y] = tap(120, 346);           // 开始
    await page.mouse.click(x, y);
    await page.waitForTimeout(3200);
    for (let i = 0; i < 6; i++) { await page.keyboard.press('Enter'); await page.waitForTimeout(700); }
    await page.screenshot({ path: `${OUT}/V_ingame.png` });
    console.log('V ingame ok');
    await ctx.close();
  }

  // 3) 手机横屏：全文目录 + 正文
  {
    const { ctx, page, tap } = await open(browser, 812, 375, true);
    let [x, y] = tap(120, 463);           // 全文
    await page.mouse.click(x, y);
    await page.waitForTimeout(2600);
    await page.screenshot({ path: `${OUT}/V_novel_index.png` });
    [x, y] = tap(420, 200);               // 目录里第一项附近
    await page.mouse.click(x, y);
    await page.waitForTimeout(2600);
    await page.screenshot({ path: `${OUT}/V_novel_read.png` });
    console.log('V novel ok');
    await ctx.close();
  }

  await browser.close();
})();
