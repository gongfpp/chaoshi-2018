#!/usr/bin/env node
/**
 * 对抗性测试：白屏 / 错误页 / 乱点 / 断网 / 视口切换 / ≡ 菜单 / 资源 404。
 *
 * 目标：任何情况下都不该出现「白屏或 Ren'Py 错误页且无法回退」。
 * 判定手段：
 *   - renpy.get_screen("_exception")        —— Ren'Py 全屏错误页（必须为 false）
 *   - window.renpy_exec 能否解析            —— Python 主循环还活着
 *   - #csToast 文本                         —— 兜底 toast 是否弹出
 *   - #chaoshiBoot.cb-dead                  —— 启动期致命面板（启动中允许，进游戏后不允许）
 *   - pageerror / console error             —— 页面级异常
 *   - 截图 md5 序列                         —— 画面是否冻结/变白
 *
 * 用法：
 *   NODE_PATH=<renpy web node_modules> node tools/test_adversarial.js [T0,T2,...]
 *   默认跑全部。环境变量 SITE_URL 可换测试站点。
 */
const { chromium } = require("playwright");
const crypto = require("crypto");
const fs = require("fs");
const path = require("path");

const BASE = (process.env.SITE_URL || "http://127.0.0.1:8080/").replace(/\/$/, "") + "/";
const SHOTS = path.join("build", "shots", "adv");
fs.mkdirSync(SHOTS, { recursive: true });

const ANDROID_UA =
  "Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36";

const ONLY = process.argv[2] ? process.argv[2].split(",").map((s) => s.trim()) : null;
const results = [];
let browser = null;

function rec(id, name, ok, detail) {
  results.push({ id, name, ok, detail });
  console.log((ok ? "  ✅ " : "  ❌ ") + id + " " + name + " —— " + detail);
}

/* ---------------------------------------------------------------- helpers */

/**
 * 给 page.evaluate / $$eval / screenshot 加超时。
 * 背景：headless renderer 偶尔会 wedged（泄漏进程吃光 CPU、wasm 运行时进入
 * 怪状态），裸 evaluate 会永久挂住，把整个测试拖死（full_suite4 的 T5 就这么
 * 卡了 10 分钟：无输出、无请求、renderer 空转 5 分钟 CPU）。超时按失败处理，
 * 各调用方本来就有 catch。
 */
function ev(page, fn, arg, ms) {
  ms = ms || 8000;
  return Promise.race([
    page.evaluate(fn, arg),
    new Promise((_, rej) => setTimeout(() => rej(new Error("eval-timeout")), ms)),
  ]);
}

function evAll(page, fn, arg, ms) {
  ms = ms || 8000;
  return Promise.race([
    page.$$eval(fn, arg),
    new Promise((_, rej) => setTimeout(() => rej(new Error("eval-timeout")), ms)),
  ]);
}

function shot(page, opts) {
  return Promise.race([
    page.screenshot(opts),
    new Promise((_, rej) => setTimeout(() => rej(new Error("shot-timeout")), 15000)),
  ]);
}

async function newPage(opts) {
  opts = opts || {};
  const ctx = await browser.newContext({
    viewport: { width: opts.w || 1280, height: opts.h || 720 },
    userAgent: opts.ua || undefined,
    locale: "zh-CN",
  });
  const page = await ctx.newPage();
  page.__errs = [];
  page.__ces = [];
  page.__reqfail = [];
  page.__crashed = false;
  page.on("pageerror", (e) => page.__errs.push(String((e && e.message) || e)));
  page.on("console", (m) => {
    if (m.type() === "error") page.__ces.push(String(m.text()).slice(0, 200));
  });
  page.on("requestfailed", (r) => {
    const f = r.failure() || {};
    page.__reqfail.push(r.url().slice(0, 90) + " :: " + (f.errorText || ""));
  });
  page.on("crash", () => { page.__crashed = true; });
  page.__ctx = ctx;
  return page;
}

async function waitReady(page, timeout) {
  const t0 = Date.now();
  timeout = timeout || 120000;
  // 还没导航过就先导航（about:blank 是纯白页，什么都不测）
  if (!page.url() || page.url().startsWith("about:")) {
    await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  }
  while (Date.now() - t0 < timeout) {
    try {
      // 就绪 = 画布已被引擎放大（躲开 300x150 的 stub，且宽 >100 适配移动端）
      //       + renpy_exec 可用。开屏层消失作为附加信号，不强制要求。
      const st = await ev(page, () => {
        const c = document.querySelector("canvas");
        if (!c) { return null; }
        const stub = c.width === 300 && c.height === 150;
        if (stub || c.width < 100) { return null; }
        if (typeof window.renpy_exec !== "function") { return null; }
        return c.width + "x" + c.height;
      });
      if (st) return st;
    } catch (e) {
      /* 导航中，忽略 */
    }
    await page.waitForTimeout(1000);
  }
  return null;
}

async function py(page, script) {
  return ev(page, (s) => window.renpy_exec(s), script, 10000);
}

async function hasException(page) {
  try {
    return await py(page, 'result = renpy.get_screen("_exception") is not None');
  } catch (e) {
    return "eval-failed:" + String(e.message).slice(0, 80);
  }
}

async function alive(page) {
  try {
    return (await py(page, "result = 6 * 7")) === 42;
  } catch (e) {
    return false;
  }
}

async function shownScreens(page) {
  try {
    return await py(
      page,
      "result = sorted([n for n in (" +
        ' "main_menu","chapter_list","load","save","text_novel_index","preferences",' +
        ' "about","help","say","nvl","confirm","game_menu","quick_menu","history","_exception"' +
        ") if renpy.get_screen(n) is not None])"
    );
  } catch (e) {
    return [];
  }
}

async function toasts(page) {
  try {
    return await evAll(page, "#csToast .cs-tx", (els) => els.map((e) => (e.textContent || "").trim()));
  } catch (e) {
    return [];
  }
}

async function hashShot(page, tag) {
  const buf = await shot(page, { type: "jpeg", quality: 55 });
  fs.writeFileSync(path.join(SHOTS, tag + ".jpg"), buf);
  return crypto.createHash("md5").update(buf).digest("hex") + "@" + buf.length;
}

async function bootState(page) {
  return ev(page, () => {
    const b = document.getElementById("chaoshiBoot");
    return b ? b.className || "" : "(no-boot-el)";
  }, undefined, 8000);
}

/** 等某个屏幕真的显示出来（waitReady 只保证引擎起来，标题菜单可能还在路上） */
async function waitScreen(page, name, timeout) {
  const t0 = Date.now();
  timeout = timeout || 20000;
  while (Date.now() - t0 < timeout) {
    const s = await shownScreens(page);
    if (s.indexOf(name) >= 0) return true;
    await page.waitForTimeout(400);
  }
  return false;
}

/** 标题页按方向键聚焦第一个菜单项后回车开局（本作初始无焦点，第一次方向键=聚焦） */
async function startGameFromTitle(page) {
  if (!(await waitScreen(page, "main_menu"))) return false;
  await page.keyboard.press("ArrowDown"); // 初始无焦点：第一下只是把焦点放到 Start
  await page.waitForTimeout(300);
  await page.keyboard.press("Enter");
  await page.waitForTimeout(3500);
  return true;
}

async function advance(page, n, gap) {
  for (let i = 0; i < n; i++) {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(gap || 700);
  }
}

/** 关掉当前菜单回到游戏：先点左下角 Return 按钮（本作布局 xpos=90 底对齐），再试右键 */
async function backToGame(page) {
  const before = (await shownScreens(page)).join(",");
  await page.mouse.click(135, 670);   // game_menu 的 Return 按钮（1280x720）
  await page.waitForTimeout(1000);
  let now = (await shownScreens(page)).join(",");
  if (now !== before) return "return-btn";
  await page.mouse.click(640, 200, { button: "right" });
  await page.waitForTimeout(900);
  now = (await shownScreens(page)).join(",");
  if (now !== before) return "rightclick";
  await page.keyboard.press("Escape");
  await page.waitForTimeout(900);
  now = (await shownScreens(page)).join(",");
  if (now !== before) return "escape";
  return "stuck:" + before;
}

/** 启动失败时的现场信息：请求失败 / 渲染器崩溃 / DOM 摘要 */
async function diag(page) {
  const parts = [];
  parts.push("url=" + page.url());
  if (page.__crashed) parts.push("RENDERER-CRASHED");
  if (page.__reqfail.length) parts.push("reqfail=" + page.__reqfail.slice(0, 5).join(" | "));
  if (page.__errs.length) parts.push("pageerror=" + page.__errs.slice(0, 2).join(" | "));
  try {
    const dom = await ev(page, () => {
      const b = document.getElementById("chaoshiBoot");
      const c = document.querySelector("canvas");
      return "boot=" + (b ? (b.className || "(empty)") : "no-el") +
        " canvas=" + (c ? c.width : "none") +
        " bodyLen=" + document.body.innerHTML.length +
        " text=" + (document.body.innerText || "").replace(/\s+/g, " ").slice(0, 120);
    });
    parts.push(dom);
  } catch (e) {
    parts.push("dom-eval-failed:" + String(e.message).slice(0, 80));
  }
  return parts.join(" | ");
}

function summarize() {
  console.log("\n================ 汇总 ================");
  const pass = results.filter((r) => r.ok).length;
  for (const r of results) {
    console.log((r.ok ? "✅ " : "❌ ") + r.id + "  " + r.name + "  |  " + r.detail);
  }
  console.log("====================================\n" + pass + "/" + results.length + " 通过");
  return pass === results.length;
}

/* ------------------------------------------------------------------ tests */

async function T0() {
  console.log("\nT0 基线启动（桌面 1280x720）");
  const page = await newPage();
  const errs0 = page.__errs.length + page.__ces.length;
  const dim = await waitReady(page);
  const exc = await hasException(page);
  const al = await alive(page);
  const menu = await shownScreens(page);
  const h = await hashShot(page, "T0_title");
  const ok = !!dim && exc === false && al && menu.indexOf("main_menu") >= 0 && page.__errs.length === 0;
  rec("T0", "基线启动进标题页", ok, "canvas=" + dim + " exc=" + exc + " alive=" + al +
    " screens=" + menu.join(",") + " pageerror=" + page.__errs.length + " consoleErr=" + page.__ces.length +
    " shot=" + h);
  if (page.__errs.length) console.log("   pageerrors:", page.__errs.slice(0, 3).join(" | "));
  await page.__ctx.close();
}

async function T1() {
  console.log("\nT1 标题页菜单全遍历（点击导航：每项全新页面，进得去、回得来、无错误页）");
  // 坐标由 calib2.js 逐行标定（1280x720）：
  // 347=开始 403=章节目录 461=全文 513=读取 571=设置 627=关于 683=退出
  const items = [
    ["Start", null, 347],           // 开始：进游戏，验证 quick_menu 出现、main_menu 消失、游戏内菜单能开能关
    ["Chapters", "chapter_list", 403],
    ["Novel", "text_novel_index", 461],
    ["Load", "load", 513],
    ["Preferences", "preferences", 571],
    ["About", "about", 627],
    ["Quit", null, 683],            // 退出：行为不固定（确认框/停留），只验证不弹错误页
  ];
  const fails = [];
  for (const [label, screen, y] of items) {
    const page = await newPage();
    const ready = await waitReady(page);
    if (!ready) {
      fails.push(label + " 启动失败: " + (await diag(page)));
      await page.__ctx.close();
      continue;
    }
    if (!(await waitScreen(page, "main_menu"))) {
      fails.push(label + " 标题页没出来");
      await page.__ctx.close();
      continue;
    }
    await page.mouse.click(160, y);
    await page.waitForTimeout(label === "Quit" ? 300 : 1800);
    const s = await shownScreens(page);
    const exc = await hasException(page);
    let okOpen;
    if (label === "Start") {
      okOpen = s.indexOf("quick_menu") >= 0 && s.indexOf("main_menu") < 0 && exc === false;
    } else if (label === "Quit") {
      // 网页版退出 = toast + full_restart 回标题（不杀运行时、不刷新页面）。
      // 旧行为（Quit(confirm=False)）会终结 wasm 运行时 → 画面冻结且无法回退。
      let sawToast = false, backTitle = false, aliveOk = false;
      for (let i = 0; i < 15; i++) {
        await page.waitForTimeout(400);
        const toast = await toasts(page);
        const s2 = await shownScreens(page);
        const al = await ev(page, () => window.renpy_exec("result = 6 * 7"), undefined, 6000).catch(() => null);
        if (toast.some((t) => t.indexOf("退出") >= 0)) sawToast = true;
        if (s2.indexOf("main_menu") >= 0) backTitle = true;
        if (al === 42) aliveOk = true;
      }
      okOpen = exc === false && sawToast && backTitle && aliveOk;
      if (!okOpen) fails.push("Quit 行为异常(exc=" + exc + ",toast=" + sawToast +
        ",back=" + backTitle + ",alive=" + aliveOk + ")");
    } else {
      okOpen = s.indexOf(screen) >= 0 && exc === false;
    }
    if (!okOpen) fails.push(label + " 打开失败(screens=" + s.join(",") + ",exc=" + exc + ")");
    let okBack = true;
    if (label === "Start") {
      // 游戏中：Escape 应进存档页（本作设计行为），再 Return 回游戏
      await page.keyboard.press("Escape");
      let inMenu = false;
      for (let i = 0; i < 12; i++) {
        await page.waitForTimeout(400);
        const s2 = await shownScreens(page);
        if (s2.indexOf("save") >= 0 || s2.indexOf("load") >= 0) { inMenu = true; break; }
      }
      // 菜单展开有过渡动画：立刻点 Return 会点空（旧构建偶发同款 flake）。
      await page.waitForTimeout(700);
      await page.mouse.click(135, 670);
      let backToGame = false;
      for (let i = 0; i < 12; i++) {
        await page.waitForTimeout(400);
        const s2 = await shownScreens(page);
        if (s2.indexOf("quick_menu") >= 0 && s2.indexOf("save") < 0 && s2.indexOf("load") < 0) { backToGame = true; break; }
      }
      okBack = inMenu && backToGame;
      if (!okBack) fails.push("Start 游戏内菜单开关异常(inMenu=" + inMenu + ",backToGame=" + backToGame + ")");
    } else if (label !== "Quit") {
      await page.mouse.click(135, 670); // 左下角 Return
      okBack = false;
      for (let i = 0; i < 12; i++) {
        await page.waitForTimeout(500);
        const s2 = await shownScreens(page);
        if (s2.indexOf("main_menu") >= 0 && s2.indexOf(screen) < 0) { okBack = true; break; }
      }
      if (!okBack) {
        const s2 = await shownScreens(page);
        fails.push(label + " 返回失败(screens=" + s2.join(",") + ")");
      }
    }
    console.log("   " + (okOpen && okBack ? "✓ " : "✗ ") + label + (screen ? " → " + screen : "") +
      " | 打开=" + okOpen + " 返回=" + okBack + " pageerror=" + page.__errs.length);
    await page.__ctx.close();
  }
  rec("T1", "标题页 7 个菜单项点击遍历", fails.length === 0,
    fails.length ? fails.join(" ; ") : "7/7 正常开合（开始/章节目录/全文/读取/设置/关于/退出）");
}

async function T2() {
  console.log("\nT2 移动端游戏内 200 次随机点击（Android UA / 390x844 / 触屏变体）");
  const page = await newPage({ w: 390, h: 844, ua: ANDROID_UA });
  const ready = await waitReady(page);
  if (!ready) return rec("T2", "启动", false, "未能启动 | " + await diag(page));
  await startGameFromTitle(page);
  await advance(page, 8, 600);
  const hashes = [];
  for (let i = 0; i < 200; i++) {
    const x = 20 + Math.random() * 350;
    const y = 60 + Math.random() * 720;
    await page.mouse.click(Math.round(x), Math.round(y));
    if (i % 40 === 0) {
      await page.waitForTimeout(250);
      hashes.push(await hashShot(page, "T2_r" + i));
      const exc = await hasException(page);
      if (exc !== false) {
        return rec("T2", "随机点击 " + i, false, "第 " + i + "次点击后出现错误页 exc=" + exc +
          " pageerror=" + page.__errs.length);
      }
    }
    if (i % 40 === 0) await page.waitForTimeout(150);
  }
  // 点完后确认还能推进剧情
  const h1 = await hashShot(page, "T2_before_final");
  await advance(page, 6, 600);
  const h2 = await hashShot(page, "T2_after_final");
  const exc = await hasException(page);
  const al = await alive(page);
  const distinct = new Set(hashes).size;
  rec("T2", "200 次随机点击后仍可玩", exc === false && al && h1 !== h2 && page.__errs.length === 0,
    "exc=" + exc + " alive=" + al + " 画面变化=" + distinct + "/6 次不同" +
    " 点击后仍能推进=" + (h1 !== h2) + " pageerror=" + page.__errs.length +
    (page.__errs.length ? " | " + page.__errs[0].slice(0, 120) : ""));
  await page.__ctx.close();
}

async function T3() {
  console.log("\nT3 游戏菜单 50 次快速开关（Escape 开关 + 返回）");
  const page = await newPage();
  const ready = await waitReady(page);
  if (!ready) return rec("T3", "启动", false, "未能启动 | " + await diag(page));
  await startGameFromTitle(page);
  await advance(page, 5, 600);
  const seq = [];
  let worst = "";
  for (let i = 0; i < 50; i++) {
    await page.keyboard.press("Escape");
    await page.waitForTimeout(140);
    if (i % 10 === 0) seq.push((await shownScreens(page)).join("+"));
    const exc = await hasException(page);
    if (exc !== false) worst = "第 " + i + " 次 Escape 后 exc=" + exc;
    if (worst) break;
    await backToGame(page);
    const exc2 = await hasException(page);
    if (exc2 !== false) worst = "第 " + i + " 次返回后 exc=" + exc2;
    if (worst) break;
  }
  const al = await alive(page);
  const h1 = await hashShot(page, "T3_a");
  await advance(page, 4, 600);
  const h2 = await hashShot(page, "T3_b");
  rec("T3", "50 次菜单快速开关", !worst && al && h1 !== h2 && page.__errs.length === 0,
    (worst || "无异常") + " | alive=" + al + " 开关后仍能推进=" + (h1 !== h2) +
    " pageerror=" + page.__errs.length + " 序列=" + seq.join(" → "));
  await page.__ctx.close();
}

/**
 * 资源全失败场景的推进 + 观测（T4a/T4b 共用）：
 *  - toast 持续轮询（每次迭代都读，带时间戳收集去重）——cs_toast 默认 5.2s 就
 *    消失，事后一次性采样必然全漏（full_suite4 的 T4a「toast=0」就是这么误判的）
 *  - 统计被拦截的图片请求数（证明失败场景真的发生了，不是「根本没下图」）
 *  - 遇到选择支先点选项——Enter 在选择支上不推进，剧情会卡住，
 *    后面所有 Enter 都打在同一个画面上（旧版 T4a/T4b「画面变化=2/6」的另一个原因）
 */
async function advanceWithAssetFailure(page, tag, n, stats, seen) {
  const hashes = [];
  for (let i = 0; i < n; i++) {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(650);
    if (i % 10 === 0) hashes.push(await hashShot(page, tag + "_r" + i));
    const atChoice = await ev(
      page,
      () => window.renpy_exec('result = renpy.get_screen("choice") is not None'),
      undefined, 6000
    ).catch(() => false);
    if (atChoice === true) {
      stats.choices = (stats.choices || 0) + 1;
      await page.mouse.click(640, 315);
      await page.waitForTimeout(700);
    }
    const t = await toasts(page);
    for (const s of t) {
      if (!seen.has(s)) seen.set(s, { first: ((Date.now() - stats.t0) / 1000).toFixed(1), n: 0 });
      seen.get(s).n++;
    }
  }
  return hashes;
}

function toastReport(seen) {
  const lines = [];
  for (const [txt, v] of seen) lines.push("t+" + v.first + "s ×" + v.n + " " + txt.slice(0, 60));
  return lines.length ? lines.join(" ； ") : "（全程无 toast）";
}

async function T4a() {
  console.log("\nT4a 立绘/背景全部 404（服务器说不存在）——剧情必须继续");
  const page = await newPage();
  const stats = { t0: Date.now(), img: 0 };
  await page.route("**/game/images/**", (route) => {
    stats.img++;
    route.fulfill({ status: 404, body: "nope" });
  });
  const ready = await waitReady(page);
  if (!ready) return rec("T4a", "启动", false, "未能启动 | " + await diag(page));
  await startGameFromTitle(page);
  await advance(page, 5, 700);
  const seen = new Map();
  const hashes = await advanceWithAssetFailure(page, "T4a", 70, stats, seen);
  const exc = await hasException(page);
  const al = await alive(page);
  const distinct = new Set(hashes).size;
  const giveUp = [...seen.keys()].filter((s) => s.indexOf("还没下载成功") >= 0);
  const jsRetry = [...seen.keys()].filter((s) => s.indexOf("有张图没拿到") >= 0);
  rec("T4a", "图片全 404 不弹错误页", exc === false && al && page.__errs.length === 0 && distinct >= 2 &&
    (giveUp.length >= 1 || jsRetry.length >= 1),
    "exc=" + exc + " alive=" + al + " 画面变化=" + distinct + "/8" +
    " 图片404请求=" + stats.img + " 次 选择支=" + (stats.choices || 0) + " 个" +
    " 放弃toast=" + giveUp.length + " 条 JS重试toast=" + jsRetry.length + " 条" +
    " | " + toastReport(seen) +
    " pageerror=" + page.__errs.length + (page.__errs.length ? " | " + page.__errs[0].slice(0, 120) : ""));
  await page.__ctx.close();
}

async function T4b() {
  console.log("\nT4b 立绘/背景全部 abort（连接被掐断）——剧情必须继续");
  const page = await newPage();
  const stats = { t0: Date.now(), img: 0 };
  await page.route("**/game/images/**", (route) => {
    stats.img++;
    route.abort();
  });
  const ready = await waitReady(page);
  if (!ready) return rec("T4b", "启动", false, "未能启动 | " + await diag(page));
  await startGameFromTitle(page);
  await advance(page, 5, 700);
  const seen = new Map();
  const hashes = await advanceWithAssetFailure(page, "T4b", 70, stats, seen);
  const exc = await hasException(page);
  const al = await alive(page);
  const distinct = new Set(hashes).size;
  const giveUp = [...seen.keys()].filter((s) => s.indexOf("还没下载成功") >= 0);
  const jsRetry = [...seen.keys()].filter((s) => s.indexOf("有张图没拿到") >= 0);
  rec("T4b", "图片全 abort 不弹错误页", exc === false && al && page.__errs.length === 0 && distinct >= 2,
    "exc=" + exc + " alive=" + al + " 画面变化=" + distinct + "/8" +
    " 图片abort=" + stats.img + " 次 选择支=" + (stats.choices || 0) + " 个" +
    " 放弃toast=" + giveUp.length + " 条 JS重试toast=" + jsRetry.length + " 条" +
    " | " + toastReport(seen) +
    " pageerror=" + page.__errs.length + (page.__errs.length ? " | " + page.__errs[0].slice(0, 120) : ""));
  await page.__ctx.close();
}

async function T5() {
  console.log("\nT5 启动中被掐断 game.zip → 贴底错误面板（非白屏）→ 恢复后能进");
  const page = await newPage();
  let blocked = true;
  await page.route("**/game.zip*", (route) => {
    if (blocked) return route.abort();
    route.continue();
  });
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  // 下载类失败会自动重载一次（?csretry=1），判死要经过两轮：
  // 固定等 18 秒会正好落在重载后的片头窗口里（cb-t1/t3 而无 cb-dead）。
  // 且失败时序很长还抖：首次判死 ≈50s，重载后二次判死 ≈100s+，引擎重试
  // 节奏受机器负载影响。按墙钟等，不按迭代数——旧版 90 迭代在 evaluate
  // 快时约 135s 就耗尽，可能没等到二次判死（full_suite5 的 T5 就这么
  // 把「加载中」当成最终状态采样了）。
  const deadline = Date.now() + 210000;
  let cls = "";
  while (Date.now() < deadline) {
    cls = await bootState(page).catch(() => "");
    if (cls.indexOf("cb-dead") >= 0) {
      // 判死后 2.6 秒会自动重载一次（?csretry=1）。等它走完，
      // 确认第二次判死（稳定态），否则后面的 evaluate 会被导航竞态打掉。
      await page.waitForTimeout(4500);
      cls = await bootState(page).catch(() => "");
      if (cls.indexOf("cb-dead") >= 0) break;
      continue;   // 还在重载/片头里，继续等
    }
    await page.waitForTimeout(1000);
  }
  const exc0 = await hasException(page).catch(() => "nav");
  // 判死稳定后页面是空闲的，evaluate 不该超时；万一超时（负载抖动），
  // 隔 2s 重读一次再认。
  let exc = exc0;
  if (String(exc).indexOf("eval-timeout") >= 0) {
    await page.waitForTimeout(2000);
    exc = await hasException(page).catch(() => "nav");
  }
  const t = await toasts(page);
  const h = await hashShot(page, "T5_blocked");
  const deadOk = cls.indexOf("cb-dead") >= 0;
  const errVisible = await ev(page, () => {
    const e = document.querySelector("#chaoshiBoot .cb-err");
    if (!e) return false;
    return getComputedStyle(e).display !== "none";
  }).catch(() => false);
  // 恢复：解除拦截，点「重新加载」
  blocked = false;
  await ev(page, () => {
    const b = document.querySelector('#chaoshiBoot .cb-err [data-act="reload"]');
    if (b) b.click();
  }).catch(() => {});
  const dim = await waitReady(page, 90000);
  const menu = await shownScreens(page);
  const exc2 = await hasException(page);
  // 判死态下引擎已中止/主线程被未下载完的 zip 堵死，renpy_exec 本来就
  // 不可能响应——拿不到异常状态是正常的。「没有错误页」的真断言放在
  // 恢复后（exc2 === false）。
  const excDeadOk = exc === false || exc === "nav" || String(exc).indexOf("eval-failed") >= 0;
  rec("T5", "启动失败有面板可恢复", deadOk && errVisible && excDeadOk && !!dim &&
    menu.indexOf("main_menu") >= 0 && exc2 === false,
    "面板=" + cls + " 错误条可见=" + errVisible + " 恢复后 canvas=" + dim +
    " screens=" + menu.join(",") + " exc=" + exc + "/" + exc2 + " toast=" + t.length + " 条");
  await page.__ctx.close();
}

async function T5b() {
  console.log("\nT5b 游玩中断网 12 秒 → 不白屏不报错 → 恢复后继续");
  const page = await newPage();
  const ready = await waitReady(page);
  if (!ready) return rec("T5b", "启动", false, "未能启动 | " + await diag(page));
  await startGameFromTitle(page);
  await advance(page, 6, 600);
  await page.__ctx.setOffline(true);
  const hashes = [];
  for (let i = 0; i < 12; i++) {
    await page.keyboard.press("Enter");
    await page.waitForTimeout(600);
    if (i % 4 === 0) hashes.push(await hashShot(page, "T5b_off" + i));
  }
  const exc = await hasException(page);
  const al = await alive(page);
  const t = await toasts(page);
  await page.__ctx.setOffline(false);
  await page.waitForTimeout(1500);
  // 断网期间可能已经把剧情推到选择支：Enter 在选择支上不推进，
  // 先点一个选项，再验证「恢复后能继续玩」。
  const atChoice = await ev(
    page,
    () => window.renpy_exec('result = renpy.get_screen("choice") is not None'),
    undefined, 8000
  ).catch(() => false);
  if (atChoice === true) {
    await page.mouse.click(640, 315);
    await page.waitForTimeout(900);
    const still = await ev(
      page,
      () => window.renpy_exec('result = renpy.get_screen("choice") is not None'),
      undefined, 8000
    ).catch(() => false);
    if (still === true) { await page.mouse.click(640, 385); await page.waitForTimeout(900); }
  }
  const h1 = await hashShot(page, "T5b_back1");
  await advance(page, 5, 600);
  const h2 = await hashShot(page, "T5b_back2");
  const exc2 = await hasException(page);
  const distinct = new Set(hashes).size;
  rec("T5b", "中途断网不白屏", exc === false && al && exc2 === false && h1 !== h2 &&
    page.__errs.length === 0 && distinct >= 2,
    "断网中 exc=" + exc + " alive=" + al + " 画面变化=" + distinct + "/3" +
    " toast=" + t.length + " 恢复后能推进=" + (h1 !== h2) + " pageerror=" + page.__errs.length);
  await page.__ctx.close();
}

async function T6() {
  console.log("\nT6 游玩中 20 次横竖屏/视口来回切");
  const page = await newPage({ w: 390, h: 844, ua: ANDROID_UA });
  const ready = await waitReady(page);
  if (!ready) return rec("T6", "启动", false, "未能启动 | " + await diag(page));
  await startGameFromTitle(page);
  await advance(page, 4, 600);
  let worst = "";
  const sizes = [
    [390, 844], [844, 390], [412, 915], [915, 412], [360, 640],
  ];
  for (let i = 0; i < 20; i++) {
    const [w, h] = sizes[i % sizes.length];
    await page.setViewportSize({ width: w, height: h });
    await page.waitForTimeout(420);
    const exc = await hasException(page);
    if (exc !== false) { worst = "第 " + i + " 次切视口 exc=" + exc; break; }
    if (i % 5 === 0) await page.keyboard.press("Enter");
  }
  const al = await alive(page);
  const h1 = await hashShot(page, "T6_a");
  await advance(page, 4, 600);
  const h2 = await hashShot(page, "T6_b");
  rec("T6", "20 次视口切换后仍可玩", !worst && al && h1 !== h2 && page.__errs.length === 0,
    (worst || "无异常") + " | alive=" + al + " 切换后仍能推进=" + (h1 !== h2) +
    " pageerror=" + page.__errs.length);
  await page.__ctx.close();
}

async function T7() {
  console.log("\nT7 ≡ 菜单六项反复点（含 FS/静音/导入/导出/日志/关于）");
  const page = await newPage();
  const ready = await waitReady(page);
  if (!ready) return rec("T7", "启动", false, "未能启动 | " + await diag(page));
  await startGameFromTitle(page);
  await advance(page, 3, 600);
  const fails = [];
  // 文件选择器：直接取消，不让它挡住后续
  page.on("filechooser", async (fc) => {
    try { await fc.setFiles([]); } catch (e) { /* 取消即可 */ }
  });
  // 关于会开新标签页，接住并关掉
  page.__ctx.on("page", async (p) => { try { await p.close(); } catch (e) {} });
  // renpy.org 外链拦掉，保持测试自洽
  await page.route("**://www.renpy.org/**", (r) => r.fulfill({ status: 200, contentType: "text/html", body: "<html>ok</html>" }));

  const items = ["ID_Fullscreen", "ID_Mute"];
  for (let round = 0; round < 5; round++) {
    // 菜单按钮本身狂点
    for (let i = 0; i < 8; i++) {
      await page.click("#ContextButton");
      await page.waitForTimeout(60);
    }
    await page.waitForTimeout(400);
    const menuOpen = await ev(page, () => {
      const m = document.getElementById("ContextMenu");
      return m && m.style.display === "block";
    }).catch(() => "eval-failed");
    // 纯 toggle：狂点偶数次后恰好是关的。不苛求此刻开着，
    // 只要求按钮还活着——下面每项用前先确保开着。
    if (typeof menuOpen !== "boolean") fails.push("round" + round + " 菜单节点丢了");
    // 确保菜单开着：先读状态，关着才点（点一下是开、再点是关）
    async function ensureOpen(who) {
      let opened = await ev(page, () => document.getElementById("ContextMenu").style.display === "block")
        .catch(() => false);
      if (!opened) {
        await page.click("#ContextButton").catch(() => {});
        await page.waitForTimeout(200);
        opened = await ev(page, () => document.getElementById("ContextMenu").style.display === "block")
          .catch(() => false);
      }
      if (!opened) { fails.push(who + " 菜单未开"); return false; }
      return true;
    }
    // 全屏 / 静音
    for (const id of items) {
      if (!(await ensureOpen(id))) continue;
      await page.click("#" + id).catch((e) => fails.push(id + " 点击失败 " + e.message.slice(0, 60)));
      await page.waitForTimeout(500);
    }
    // 导入（取消文件选择器）
    if (await ensureOpen("import")) {
      await page.click('#ContextMenu a[data-cs="import"]').catch((e) => fails.push("import " + e.message.slice(0, 60)));
      await page.waitForTimeout(500);
    }
    // 导出
    if (await ensureOpen("export")) {
      await page.click('#ContextMenu a[data-cs="export"]').catch((e) => fails.push("export " + e.message.slice(0, 60)));
      await page.waitForTimeout(700);
    }
    // 日志
    if (await ensureOpen("log")) {
      await page.click('#ContextMenu a[data-cs="log"]').catch((e) => fails.push("log " + e.message.slice(0, 60)));
      await page.waitForTimeout(500);
    }
    // 关于（新标签页）
    if (await ensureOpen("about")) {
      await page.click('#ContextMenu a[data-cs="about"]').catch((e) => fails.push("about " + e.message.slice(0, 60)));
      await page.waitForTimeout(600);
    }
    const exc = await hasException(page);
    if (exc !== false) { fails.push("round" + round + " exc=" + exc); break; }
  }
  // 静音状态应该被真的切过
  const muted = await py(page, "result = chaoshi_is_muted()");
  const exc = await hasException(page);
  const al = await alive(page);
  const h1 = await hashShot(page, "T7_a");
  await advance(page, 3, 600);
  const h2 = await hashShot(page, "T7_b");
  rec("T7", "≡ 菜单 5 轮狂点不坏", fails.length === 0 && exc === false && al && h1 !== h2 && page.__errs.length === 0,
    (fails.length ? fails.join(" ; ") : "5 轮 × 6 项全部无异常") + " | 静音状态=" + muted +
    " alive=" + al + " 仍能推进=" + (h1 !== h2) + " pageerror=" + page.__errs.length +
    (page.__errs.length ? " | " + page.__errs[0].slice(0, 120) : ""));
  await page.__ctx.close();
}

async function T8() {
  console.log("\nT8 启动过程中频繁切视口 + 启动中途刷新");
  const page = await newPage({ w: 390, h: 844, ua: ANDROID_UA });
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  const sizes = [[390, 844], [844, 390], [412, 915], [768, 1024]];
  let i = 0;
  const t0 = Date.now();
  while (Date.now() - t0 < 25000) {
    const [w, h] = sizes[i++ % sizes.length];
    await page.setViewportSize({ width: w, height: h }).catch(() => {});
    await page.waitForTimeout(1200);
  }
  const dim = await waitReady(page, 90000);
  const exc = await hasException(page);
  const al = await alive(page);
  // 启动中途再刷新一次
  await page.reload({ waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(4000);
  await page.reload({ waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  const dim2 = await waitReady(page, 90000);
  const exc2 = await hasException(page);
  rec("T8", "启动中切视口+刷新都能起来", !!dim && !!dim2 && exc === false && exc2 === false && al &&
    page.__errs.length === 0,
    "切视口后 canvas=" + dim + " 刷新两次后 canvas=" + dim2 + " exc=" + exc + "/" + exc2 +
    " alive=" + al + " pageerror=" + page.__errs.length +
    (page.__errs.length ? " | " + page.__errs[0].slice(0, 120) : ""));
  await page.__ctx.close();
}

async function T9() {
  console.log("\nT9 chaoshi-loader.js 本身被拦 → 4 秒后静态兜底层亮出 → 恢复后可进");
  const page = await newPage();
  let blocked = true;
  await page.route("**/chaoshi-loader.js", (route) => {
    if (blocked) return route.abort();
    route.continue();
  });
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  await page.waitForTimeout(9000); // 兜底层 4 秒计时
  const fb = await ev(page, () => {
    const f = document.getElementById("csFallback");
    if (!f) return "no-el";
    const cs = getComputedStyle(f);
    return (f.className || "") + " display=" + cs.display +
      " text=" + (f.innerText || "").replace(/\s+/g, " ").slice(0, 60);
  }).catch(() => "eval-failed");
  const exc = await hasException(page);
  const h = await hashShot(page, "T9_fallback");
  // 恢复：解除拦截，点兜底层里的「重新加载」
  blocked = false;
  await ev(page, () => {
    const b = document.querySelector("#csFallback button");
    if (b) b.click();
  }).catch(() => {});
  const dim = await waitReady(page, 90000);
  const menu = await shownScreens(page);
  rec("T9", "loader 挂掉有静态兜底", fb.indexOf("on") >= 0 && fb.indexOf("display=flex") >= 0 &&
    exc === false && !!dim && menu.indexOf("main_menu") >= 0,
    "兜底层=" + fb + " | 恢复后 canvas=" + dim + " screens=" + menu.join(","));
  await page.__ctx.close();
}

async function T10() {
  console.log("\nT10 renpy-pre.js 被拦 → loader 走 fatal 面板（非白屏）→ 恢复后可进");
  const page = await newPage();
  let blocked = true;
  await page.route("**/renpy-pre.js", (route) => {
    if (blocked) return route.abort();
    route.continue();
  });
  await page.goto(BASE, { waitUntil: "domcontentloaded", timeout: 60000 }).catch(() => {});
  // pre.js 被拦 → 引擎起不来 → fatal('engine')。检测要走完超时，别固定等。
  let cls = "";
  for (let i = 0; i < 60; i++) {
    cls = await bootState(page).catch(() => "");
    if (cls.indexOf("cb-dead") >= 0) break;
    await page.waitForTimeout(1000);
  }
  const t = await toasts(page);
  blocked = false;
  await ev(page, () => {
    const b = document.querySelector('#chaoshiBoot .cb-err [data-act="reload"]');
    if (b) b.click();
  }).catch(() => {});
  const dim = await waitReady(page, 90000);
  const menu = await shownScreens(page);
  rec("T10", "pre.js 挂掉有面板可恢复", cls.indexOf("cb-dead") >= 0 && !!dim &&
    menu.indexOf("main_menu") >= 0,
    "面板=" + cls + " toast=" + t.length + " 条 | 恢复后 canvas=" + dim + " screens=" + menu.join(","));
  await page.__ctx.close();
}

/* ------------------------------------------------------------------- main */

(async () => {
  browser = await chromium.launch({
    args: ["--enable-unsafe-swiftshader", "--use-gl=swiftshader", "--proxy-bypass-list=127.0.0.1;localhost"],
  });
  const tests = [
    ["T0", T0], ["T1", T1], ["T2", T2], ["T3", T3],
    ["T4a", T4a], ["T4b", T4b], ["T5", T5], ["T5b", T5b],
    ["T6", T6], ["T7", T7], ["T8", T8], ["T9", T9], ["T10", T10],
  ];
  try {
    for (const [id, fn] of tests) {
      if (ONLY && ONLY.indexOf(id) < 0) continue;
      try {
        // 单测试看门狗：单项挂死不该拖垮全套（full_suite4 的 T5 挂过 10 分钟）。
        // T5 要等两轮判死（≈100s+）再加恢复，给 420s；其它 300s。
        const wd = id === "T5" ? 420000 : 300000;
        await Promise.race([
          fn(),
          new Promise((_, rej) => setTimeout(() => rej(new Error("test-timeout")), wd)),
        ]);
      } catch (e) {
        rec(id, "执行本身崩溃", false, String((e && e.message) || e).slice(0, 200));
      }
    }
  } finally {
    await browser.close();
  }
  const ok = summarize();
  process.exit(ok ? 0 : 1);
})();
