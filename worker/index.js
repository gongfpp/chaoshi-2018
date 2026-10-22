// 《超时》埋点采集 + 聚合端点（Cloudflare Worker + D1）
//   POST /api/collect     接收 {events:[...]}
//   GET  /api/stats       聚合结果（?token=<ANALYTICS_TOKEN>）
//   GET  /healthz         存活与计数
//   GET  /                看板页
// 接口约定与 tools/collector.py 保持一致，本地/线上可互换。

import { DASH_HTML } from "./dash_html.js";

const ALLOWED = new Set([
  "page_view", "game_ready", "run_start", "chapter_enter", "chapter_complete",
  "chapter_jump", "choice_shown", "choice_pick", "ending_enter",
  "ending_complete", "save_ok", "save_fail", "load_ok", "load_fail",
  "skip_on", "auto_on", "mute_on", "voice_fail", "error",
]);

const MAX_BYTES = 64 * 1024;
const MAX_EVENTS = 100;

function cors(extra) {
  return Object.assign({
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
  }, extra || {});
}

function json(obj, status) {
  return new Response(JSON.stringify(obj), {
    status: status || 200,
    headers: cors({ "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" }),
  });
}

const str = (v, n) => (v === null || v === undefined ? null : String(v).slice(0, n || 120));
const num = (v) => (typeof v === "number" && isFinite(v) ? v : null);

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const path = url.pathname.replace(/\/+$/, "") || "/";

    if (request.method === "OPTIONS") {
      return new Response(null, { status: 204, headers: cors() });
    }

    try {
      if (path === "/api/collect") {
        if (request.method !== "POST") return json({ ok: false, error: "POST only" }, 405);
        return await collect(request, env);
      }
      if (path === "/api/stats") return await stats(url, env);
      if (path === "/healthz") {
        const r = await env.DB.prepare("SELECT COUNT(*) AS n FROM events").first();
        return json({ ok: true, events: r ? r.n : 0, build: env.BUILD || null });
      }
      if (path === "/" || path === "/dash" || path === "/dash.html") {
        return new Response(DASH_HTML, {
          headers: cors({ "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" }),
        });
      }
      return json({ error: "not found" }, 404);
    } catch (e) {
      return json({ error: String((e && e.message) || e) }, 500);
    }
  },
};

async function collect(request, env) {
  const txt = await request.text();
  if (!txt || txt.length > MAX_BYTES) return json({ ok: false, error: "bad length" }, 413);

  let payload;
  try {
    payload = JSON.parse(txt);
  } catch (e) {
    return json({ ok: false, error: "bad json" }, 400);
  }

  const list = Array.isArray(payload && payload.events) ? payload.events.slice(0, MAX_EVENTS) : [];
  const host = request.headers.get("host") || "";
  const now = Date.now();
  const stmts = [];

  for (const e of list) {
    if (!e || typeof e !== "object" || !ALLOWED.has(e.event)) continue;
    stmts.push(
      env.DB.prepare(
        "INSERT OR IGNORE INTO events " +
        "(event,vid,sid,seq,run_id,build,site,chapter,choice,opt,ending,ms,reason,ref,test,t_client,t_server,raw) " +
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)"
      ).bind(
        e.event,
        str(e.vid, 64), str(e.sid, 64), num(e.seq),
        str(e.run_id, 64), str(e.build, 40), str(e.site || host, 80),
        str(e.chapter, 16), str(e.choice, 32),
        e.option === null || e.option === undefined ? null : str(e.option, 8),
        str(e.ending, 32), num(e.ms) === null ? null : Math.round(e.ms),
        str(e.reason, 160), str(e.ref, 200), e.test ? 1 : 0,
        num(e.t_client), now, JSON.stringify(e).slice(0, 1000)
      )
    );
  }

  if (!stmts.length) return json({ ok: true, kept: 0 });
  const res = await env.DB.batch(stmts);
  // batch 不会告诉你有几行真的插进去了，(sid,seq) 去重时要看 meta.changes
  const kept = (res || []).reduce((n, r) => n + ((r && r.meta && r.meta.changes) || 0), 0);
  return json({ ok: true, kept, sent: stmts.length });
}

const pairs = (r) => ((r && r.results) || []).map((x) => [x.k == null ? "-" : String(x.k), x.c]);

async function stats(url, env) {
  const token = url.searchParams.get("token") || "";
  const expect = env.ANALYTICS_TOKEN || "";
  if (!expect || token !== expect) return json({ error: "unauthorized" }, 401);

  const days = Math.max(1, Math.min(365, parseInt(url.searchParams.get("days") || "30", 10) || 30));
  const since = Date.now() - days * 86400000;
  const W = "FROM events WHERE t_server >= ? AND test = 0";

  const r = await env.DB.batch([
    env.DB.prepare(
      "SELECT COUNT(*) AS events, " +
      "SUM(event='page_view') AS pv, " +
      "COUNT(DISTINCT CASE WHEN event='page_view' THEN vid END) AS uv, " +
      "COUNT(DISTINCT sid) AS sessions, " +
      "COUNT(DISTINCT CASE WHEN event='run_start' THEN run_id END) AS runs, " +
      "SUM(event='game_ready') AS ready, " +
      "SUM(event='error') AS errors, " +
      "SUM(event='chapter_complete') AS chapter_done, " +
      "SUM(event='ending_complete') AS endings_done, " +
      "MIN(t_server) AS first_t, MAX(t_server) AS last_t " + W
    ).bind(since),
    env.DB.prepare(
      "SELECT ms FROM events WHERE t_server >= ? AND test = 0 " +
      "AND event='game_ready' AND ms IS NOT NULL ORDER BY ms LIMIT 5000"
    ).bind(since),
    env.DB.prepare(
      "SELECT chapter AS k, COUNT(*) AS c " + W +
      " AND event='chapter_enter' AND chapter IS NOT NULL GROUP BY chapter ORDER BY chapter"
    ).bind(since),
    env.DB.prepare(
      "SELECT choice || '#' || COALESCE(opt,'?') AS k, COUNT(*) AS c " + W +
      " AND event='choice_pick' AND choice IS NOT NULL GROUP BY k ORDER BY c DESC, k LIMIT 50"
    ).bind(since),
    env.DB.prepare(
      "SELECT choice AS k, COUNT(*) AS c " + W +
      " AND event='choice_shown' AND choice IS NOT NULL GROUP BY choice ORDER BY c DESC, k LIMIT 50"
    ).bind(since),
    env.DB.prepare(
      "SELECT ending AS k, COUNT(*) AS c " + W +
      " AND event='ending_complete' AND ending IS NOT NULL GROUP BY ending ORDER BY c DESC LIMIT 30"
    ).bind(since),
    env.DB.prepare(
      "SELECT site AS k, COUNT(*) AS c " + W +
      " AND event='page_view' GROUP BY site ORDER BY c DESC LIMIT 20"
    ).bind(since),
    env.DB.prepare(
      "SELECT build AS k, COUNT(*) AS c " + W +
      " GROUP BY build ORDER BY c DESC LIMIT 5"
    ).bind(since),
    env.DB.prepare(
      "SELECT date(t_server/1000,'unixepoch','+8 hours') AS k, COUNT(*) AS c " + W +
      " AND event='page_view' GROUP BY k ORDER BY k"
    ).bind(since),
    env.DB.prepare(
      "SELECT chapter AS k, COUNT(*) AS c " + W +
      " AND event='chapter_jump' AND chapter IS NOT NULL GROUP BY chapter ORDER BY chapter"
    ).bind(since),
  ]);

  const t = (r[0] && r[0].results && r[0].results[0]) || {};
  const ms = ((r[1] && r[1].results) || []).map((x) => x.ms).filter((v) => typeof v === "number");
  const pick = (q) => (ms.length ? ms[Math.min(ms.length - 1, Math.round((ms.length - 1) * q))] : null);

  return json({
    pv: t.pv || 0,
    uv: t.uv || 0,
    sessions: t.sessions || 0,
    runs: t.runs || 0,
    ready: t.ready || 0,
    ready_p50_ms: pick(0.5),
    ready_p95_ms: pick(0.95),
    errors: t.errors || 0,
    events: t.events || 0,
    chapter_done: t.chapter_done || 0,
    endings_done: t.endings_done || 0,
    chapters: pairs(r[2]),
    choices: pairs(r[3]),
    choice_shown: pairs(r[4]),
    endings: pairs(r[5]),
    sites: pairs(r[6]),
    builds: pairs(r[7]),
    daily: pairs(r[8]),
    jumps: pairs(r[9]),
    days,
    first_t: t.first_t || null,
    last_t: t.last_t || null,
  });
}
