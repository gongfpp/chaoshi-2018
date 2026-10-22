// 生产埋点端到端校验：两个互相隔离的浏览器会话分别访问两个部署点，
// 等游戏真正起来后查 /api/stats，用「前后差值」判定事件确实落到了 D1。
//
//   NODE_PATH=... node tools/check_analytics.js
// 环境变量：SITE_A / SITE_B / WORKER / ANALYTICS_TOKEN_FILE / DIRECT=1

const fs = require("fs");
const { chromium } = require("playwright");

const A = process.env.SITE_A || "https://chaoshi-2018.pages.dev/";
const B = process.env.SITE_B || "https://gongfpp.github.io/chaoshi-2018/";
const WORKER = process.env.WORKER || "https://chaoshi-analytics.gong7968.workers.dev";
const TOKEN = (fs.readFileSync(process.env.ANALYTICS_TOKEN_FILE || "build/analytics/token.txt", "utf8") || "").trim();
const DIRECT = process.env.DIRECT === "1";
const ARGS = ["--enable-unsafe-swiftshader", "--use-gl=swiftshader",
  DIRECT ? "--no-proxy-server" : "--proxy-server=http://127.0.0.1:7897"];

async function visit(browser, url, label) {
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 720 } });
  const page = await ctx.newPage();
  const errs = [];
  page.on("pageerror", (e) => errs.push(e.message));
  const t0 = Date.now();
  await page.goto(url, { waitUntil: "domcontentloaded", timeout: 120000 });

  let ready = false;
  for (let i = 0; i < 90; i++) {
    const w = await page.evaluate(() => {
      const c = document.querySelector("canvas");
      return c ? c.width : 0;
    });
    if (w > 640) { ready = true; break; }
    await page.waitForTimeout(1000);
  }
  const ms = Date.now() - t0;
  await page.waitForTimeout(2500); // 即时 flush 后仍给 sendBeacon 一点时间
  await page.screenshot({ path: "build/shots/ana_" + label + ".png" });
  const build = await page.evaluate(() => window.CHAOSHI_BUILD || null);
  console.log(`[${label}] ${url}\n        ready=${ready}  ${ms}ms  build=${build}  pageerror=${errs.length}`);
  if (errs.length) console.log("        " + errs.slice(0, 2).join(" | "));
  return { ctx, ready, ms, build };
}

(async () => {
  const browser = await chromium.launch({ args: ARGS });

  // 探针页：与 Worker 同源，用它查统计（免 CORS、且复用浏览器代理）
  const probeCtx = await browser.newContext();
  const probe = await probeCtx.newPage();
  await probe.goto(WORKER + "/", { waitUntil: "domcontentloaded", timeout: 60000 });
  const getStats = () => probe.evaluate(async ({ w, t }) => {
    const r = await fetch(w + "/api/stats?token=" + encodeURIComponent(t) + "&days=30");
    return { status: r.status, body: r.status === 200 ? await r.json() : null };
  }, { w: WORKER, t: TOKEN });

  const before = await getStats();
  if (before.status !== 200) {
    console.log("统计接口异常，HTTP " + before.status);
    process.exit(1);
  }

  const a = await visit(browser, A, "cf");
  const b = await visit(browser, B, "gh");

  const after = await getStats();
  await probeCtx.close();
  await a.ctx.close();
  await b.ctx.close();
  await browser.close();

  if (after.status !== 200) { console.log("统计接口异常，HTTP " + after.status); process.exit(1); }

  const d0 = before.body, d1 = after.body;
  const dv = (k) => (d1[k] || 0) - (d0[k] || 0);
  const hasA = (d1.sites || []).some((s) => s[0] && s[0].includes("pages.dev"));
  const hasB = (d1.sites || []).some((s) => s[0] && s[0].includes("github.io"));

  console.log("\n=== 增量（本轮两个会话） ===");
  console.log(`PV +${dv("pv")}  UV +${dv("uv")}  会话 +${dv("sessions")}  加载完成 +${dv("ready")}  事件 +${dv("events")}`);
  console.log("累计站点：" + JSON.stringify(d1.sites));
  console.log("累计版本：" + JSON.stringify(d1.builds) + "  首屏 P50 " + d1.ready_p50_ms + "ms");

  const ok = dv("pv") >= 2 && dv("uv") >= 2 && dv("ready") >= 2 && hasA && hasB;
  console.log("\n判定：" + (ok ? "通过（两站各一条会话，PV/UV/ready 均 +2）" : "未达标"));
  process.exit(ok ? 0 : 2);
})();
