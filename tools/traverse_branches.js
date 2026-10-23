// 分支与结局的**真机**遍历（当前未跑通，留作记录，别重复踩）
//
// 目标：把 7 个选择点按不同组合走完，确认 3 个结局都走得到、且不报错。
//
// 现在卡在两条引擎限制上（详见 tools/check_branches.py 末尾的说明）：
//   1. renpy_exec 不在 context 执行循环里，renpy.run(Start()) / renpy.jump()
//      抛出的控制流异常会丢失，跳转不生效；
//   2. config.skipping 每次交互被重置，靠 interact_callbacks 能顶住，但
//      `call screen chapter_card` 这类阻塞屏幕不会被跳过自动点掉，
//      而点击又会取消跳过，推进极慢。
//
// → 覆盖核查请用 tools/check_branches.py（静态、确定、秒级）。
// 要跑真机遍历，得先给游戏加一个自动化测试模式（自动推进 + 章节卡自动消失）。
//
// 用法（若将来修通）：SITE_URL=http://127.0.0.1:8931/ node tools/traverse_branches.js
const { chromium } = require('playwright');

const URL = process.env.SITE_URL || 'http://127.0.0.1:8931/';
const PROXY = process.env.PROXY || 'http://127.0.0.1:7897';
const LOCAL = /^http:\/\/(127\.0\.0\.1|localhost)/.test(URL);

// 三条路线：全选第一项 / 全选第二项 / 前面选二、面对陈立时选一
const ROUTES = [
  { name: '一路第一项', seq: [0, 0, 0, 0, 0, 0], expect: 'ending_raolu' },
  { name: '一路第二项', seq: [1, 1, 1, 1, 1, 1], expect: 'ending_zhundian' },
  { name: '先保后卖', seq: [1, 1, 1, 1, 1, 0], expect: 'ch20_end' },
];

const INSTALL = (seq) => `
def _cs_probe_install(seq):
    import renpy
    st = {"seq": list(seq), "i": 0, "picks": [], "done": False}
    def _menu(items, *a, **kw):
        idx = st["seq"][st["i"]] if st["i"] < len(st["seq"]) else 0
        if idx >= len(items):
            idx = len(items) - 1
        st["i"] += 1
        st["picks"].append(items[idx][0])
        return items[idx][1]
    renpy.display_menu = _menu
    store._cs_probe = st

    # config.skipping is reset at the start of every interaction, so re-arm it each time
    def _keep_skip():
        renpy.config.skipping = "fast"
    if _keep_skip not in renpy.config.interact_callbacks:
        renpy.config.interact_callbacks.append(_keep_skip)

_cs_probe_install(${JSON.stringify(seq)})
renpy.game.preferences.skip_unseen = True
renpy.game.preferences.transitions = 0
`;

async function runRoute(browser, route) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));

  await page.goto(URL, { waitUntil: 'domcontentloaded', timeout: 120000 });
  for (let i = 0; i < 120; i++) {
    const w = await page.evaluate(() => (document.querySelector('canvas') || {}).width || 0);
    if (w > 640) break;
    await page.waitForTimeout(1000);
  }
  await page.waitForTimeout(2000);

  await page.evaluate(code => renpy_exec(code), INSTALL(route.seq).trim());
  // 用真点击进游戏。不能走 renpy.run(Start())：它靠 JumpOutException 跳出主菜单
  // 上下文，而 renpy_exec 这条路上没人接住这个异常，跳转就丢了。
  await page.mouse.click(148, 366);

  let reached = null;
  const t0 = Date.now();
  let lastLabel = '', lastLog = 0, clicks = 0;
  while (Date.now() - t0 < 200000) {
    const st = await page.evaluate(async () => {
      try {
        return {
          card: await renpy_get('renpy.get_screen("ending_card") is not None'),
          picks: await renpy_get('len(store._cs_probe["picks"])'),
          label: await renpy_get('(renpy.game.context().current or "")[0].split("/")[-1]'),
        };
      } catch (e) { return { err: String(e.message || e) }; }
    });
    if (st.card === true) { reached = st.label || 'ending_card'; break; }

    // 章节卡 / 任何阻塞界面靠点击推掉；跳过模式由交互回调维持，不会被打断
    await page.mouse.click(640, 360).catch(() => {});
    clicks++;

    const el = Date.now() - t0;
    if (st.label !== lastLabel || el - lastLog > 15000) {
      lastLabel = st.label; lastLog = el;
      console.log(`   [${route.name}] ${(el / 1000).toFixed(0)}s ` +
                  `file=${st.label} picks=${st.picks} clicks=${clicks}`);
    }
    await page.waitForTimeout(220);
  }

  const picks = await page.evaluate(async () => {
    try { return await renpy_get('store._cs_probe["picks"]'); } catch (e) { return null; }
  });
  await ctx.close();
  return { ...route, reached, picks, errors, sec: ((Date.now() - t0) / 1000).toFixed(0) };
}

(async () => {
  const browser = await chromium.launch({
    args: (LOCAL ? ['--proxy-bypass-list=<-loopback>'] : [`--proxy-server=${PROXY}`])
      .concat(['--enable-unsafe-swiftshader', '--use-gl=angle', '--ignore-gpu-blocklist']),
  });

  let bad = 0;
  for (const route of ROUTES) {
    const r = await runRoute(browser, route);
    const hit = r.reached && r.reached.indexOf(r.expect) !== -1;
    if (!hit) bad++;
    console.log(`${hit ? 'PASS' : 'FAIL'} ${r.name}  期望=${r.expect} 到达=${r.reached} ` +
                `选择=${JSON.stringify(r.picks)} 用时=${r.sec}s` +
                (r.errors.length ? ` 页面错误=${JSON.stringify(r.errors.slice(0, 2))}` : ''));
  }
  console.log(bad === 0 ? '全部路线通过' : `有 ${bad} 条路线未通过`);
  await browser.close();
  process.exit(bad === 0 ? 0 : 1);
})();
