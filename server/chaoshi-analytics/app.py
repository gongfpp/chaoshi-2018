#!/usr/bin/env python3
"""《超时》自部署埋点服务 —— 只用标准库，单进程 + SQLite。

接口（对外经 Caddy 挂在 https://gongfpp.icu/chaoshi/ ，前缀被 handle_path 剥掉）：

    POST /api/collect   {events:[...]}      收事件，写 SQLite
    GET  /api/live                          标题页脚注：{online, total, today}
    GET  /api/stats?token=&days=            看板 JSON（需令牌）
    GET  /                                  看板页面
    GET  /healthz                           存活探针

设计取舍：
  * 不用框架 —— 服务器 3.7 GB 内存还跑着别的项目，标准库足够，零依赖升级。
  * 每次请求开一个连接（WAL 下读并发不阻塞），避免线程间共享连接。
  * (sid, seq) 唯一索引去重：sendBeacon 在 pagehide 会重投同一批事件。
  * 在线人数用「5 分钟内有过事件的 vid 去重」；单局时长用 play_beat 的
    累计秒数取 max，丢包只会少一次心跳，不会把时长算小或算重。
"""

import argparse
import json
import os
import sqlite3
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.environ.get("CHAOSHI_DB", "/var/lib/chaoshi-analytics/events.db")
TOKEN = os.environ.get("CHAOSHI_TOKEN", "")
BIND = os.environ.get("CHAOSHI_BIND", "127.0.0.1")
PORT = int(os.environ.get("CHAOSHI_PORT", "3155"))

MAX_BODY = 256 * 1024
ONLINE_WINDOW = 300          # 同时在线：5 分钟窗口
LIVE_TTL = 20                # /api/live 进程内缓存秒数
KEEP_DAYS = 400              # 事件保留天数

# 允许上报的键。服务端再白名单一次，避免客户端被改后往库里塞任意字段。
FIELDS = ("vid", "sid", "seq", "run_id", "build", "site", "chapter", "choice",
          "opt", "ending", "ms", "sec", "reason", "ref", "t_client", "test")

_live_lock = threading.Lock()
_live_cache = {"at": 0.0, "body": b""}


# --------------------------------------------------------------------------
# 数据库
# --------------------------------------------------------------------------

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=8000")
    return conn


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = connect()
    with open(os.path.join(HERE, "schema.sql"), encoding="utf-8") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()


def _int(v, limit=10 ** 12):
    try:
        n = int(v)
    except (TypeError, ValueError):
        return None
    if n < 0 or n > limit:
        return None
    return n


def _text(v, limit=120):
    if v is None:
        return None
    s = str(v)
    return s[:limit]


def ingest(events):
    """写事件，返回 (新增, 重复)。同一 (sid,seq) 只留第一条。"""
    now = int(time.time())
    rows = []
    for e in events:
        if not isinstance(e, dict):
            continue
        name = _text(e.get("event"), 40)
        if not name:
            continue
        r = {
            "event": name,
            "vid": _text(e.get("vid")),
            "sid": _text(e.get("sid")),
            "seq": _int(e.get("seq")),
            "run_id": _text(e.get("run_id"), 40),
            "build": _text(e.get("build"), 40),
            "site": _text(e.get("site"), 80),
            "chapter": _text(e.get("chapter"), 20),
            "choice": _text(e.get("choice"), 20),
            "opt": _text(e.get("opt"), 40),
            "ending": _text(e.get("ending"), 40),
            "ms": _int(e.get("ms")),
            "sec": _int(e.get("sec"), 10 ** 7),
            "reason": _text(e.get("reason"), 160),
            "ref": _text(e.get("ref"), 200),
            "test": 1 if e.get("test") else 0,
            "t_client": _int(e.get("t_client")),
            "t_server": now,
            "raw": "",
        }
        rows.append(r)
    if not rows:
        return 0, 0

    cols = ("event", "vid", "sid", "seq", "run_id", "build", "site", "chapter",
            "choice", "opt", "ending", "ms", "sec", "reason", "ref", "test",
            "t_client", "t_server", "raw")
    sql = ("INSERT OR IGNORE INTO events (%s) VALUES (%s)"
           % (",".join(cols), ",".join("?" * len(cols))))

    conn = connect()
    try:
        before = conn.total_changes
        conn.executemany(sql, [tuple(r[c] for c in cols) for r in rows])
        conn.commit()
        added = conn.total_changes - before
    finally:
        conn.close()
    return added, len(rows) - added


# --------------------------------------------------------------------------
# 查询
# --------------------------------------------------------------------------

def live_stats():
    now = int(time.time())
    conn = connect()
    try:
        online = conn.execute(
            "SELECT COUNT(DISTINCT vid) FROM events "
            "WHERE t_server >= ? AND test = 0 AND vid IS NOT NULL",
            (now - ONLINE_WINDOW,)).fetchone()[0]
        total = conn.execute(
            "SELECT COUNT(DISTINCT vid) FROM events "
            "WHERE event = 'page_view' AND test = 0 AND vid IS NOT NULL").fetchone()[0]
        today = conn.execute(
            "SELECT COUNT(DISTINCT vid) FROM events "
            "WHERE event = 'page_view' AND test = 0 AND vid IS NOT NULL "
            "AND t_server >= ?",
            (now - now % 86400 - 8 * 3600,)).fetchone()[0]
    finally:
        conn.close()
    return {"ok": True, "online": online, "total": total, "today": today,
            "ts": now, "window": ONLINE_WINDOW}


def _pct(sorted_vals, q):
    if not sorted_vals:
        return None
    k = max(0, min(len(sorted_vals) - 1, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[k]


def full_stats(days=30, include_test=False):
    days = max(1, min(365, int(days)))
    since = int(time.time()) - days * 86400
    tf = "1=1" if include_test else "test = 0"
    conn = connect()
    try:
        def q(sql, args=()):
            return conn.execute(sql.format(tf=tf), args).fetchall()

        def one(sql, args=()):
            row = conn.execute(sql.format(tf=tf), args).fetchone()
            return row[0] if row else 0

        base = "FROM events WHERE {tf} AND t_server >= ?"
        pv = one("SELECT COUNT(*) " + base + " AND event = 'page_view'", (since,))
        uv = one("SELECT COUNT(DISTINCT vid) " + base + " AND event = 'page_view'",
                 (since,))
        sessions = one("SELECT COUNT(DISTINCT sid) " + base, (since,))
        runs = one("SELECT COUNT(DISTINCT run_id) FROM events "
                   "WHERE {tf} AND t_server >= ? AND event = 'run_start' "
                   "AND run_id <> ''", (since,))
        ready = one("SELECT COUNT(*) FROM events WHERE {tf} AND t_server >= ? "
                    "AND event = 'game_ready'", (since,))
        errors = one("SELECT COUNT(*) FROM events WHERE {tf} AND t_server >= ? "
                     "AND event = 'error'", (since,))
        chapter_done = one("SELECT COUNT(*) FROM events WHERE {tf} AND t_server >= ? "
                           "AND event = 'chapter_complete'", (since,))
        endings_done = one("SELECT COUNT(*) FROM events WHERE {tf} AND t_server >= ? "
                           "AND event = 'ending_complete'", (since,))
        total_events = one("SELECT COUNT(*) " + base, (since,))

        ready_ms = sorted(r[0] for r in q(
            "SELECT ms FROM events WHERE {tf} AND t_server >= ? "
            "AND event = 'game_ready' AND ms IS NOT NULL", (since,)))

        # 进度漏斗：每一章有多少「局」到达
        chapters = [
            (r[0], r[1]) for r in q(
                "SELECT chapter, COUNT(DISTINCT run_id) FROM events "
                "WHERE {tf} AND t_server >= ? AND event = 'chapter_enter' "
                "AND chapter IS NOT NULL AND run_id <> '' "
                "GROUP BY chapter ORDER BY chapter", (since,))
        ]

        # 单局时长：play_beat 的累计秒取 max
        per_run = [r[0] for r in q(
            "SELECT MAX(sec) FROM events WHERE {tf} AND t_server >= ? "
            "AND event = 'play_beat' AND sec IS NOT NULL AND run_id <> '' "
            "GROUP BY run_id", (since,))]
        per_run = sorted(x for x in per_run if x is not None)

        choices = [
            {"choice": r[0], "opt": r[1], "n": r[2]} for r in q(
                "SELECT choice, COALESCE(opt, '-'), COUNT(*) FROM events "
                "WHERE {tf} AND t_server >= ? AND event = 'choice_pick' "
                "GROUP BY choice, opt ORDER BY choice, COUNT(*) DESC", (since,))
        ]

        endings = [
            {"ending": r[0], "n": r[1]} for r in q(
                "SELECT ending, COUNT(*) FROM events WHERE {tf} AND t_server >= ? "
                "AND event = 'ending_complete' GROUP BY ending ORDER BY COUNT(*) DESC",
                (since,))
        ]
        sites = [
            {"site": r[0], "n": r[1]} for r in q(
                "SELECT site, COUNT(*) FROM events WHERE {tf} AND t_server >= ? "
                "AND event = 'page_view' GROUP BY site ORDER BY COUNT(*) DESC",
                (since,))
        ]
        jumps = [
            {"chapter": r[0], "n": r[1]} for r in q(
                "SELECT chapter, COUNT(*) FROM events WHERE {tf} AND t_server >= ? "
                "AND event = 'chapter_jump' GROUP BY chapter ORDER BY COUNT(*) DESC",
                (since,))
        ]
        daily = [
            {"d": r[0], "pv": r[1], "uv": r[2]} for r in q(
                "SELECT date(t_server,'unixepoch','+8 hours') AS d, COUNT(*), "
                "COUNT(DISTINCT vid) FROM events WHERE {tf} AND t_server >= ? "
                "AND event = 'page_view' GROUP BY d ORDER BY d DESC LIMIT 60",
                (since,))
        ]
        builds = [r[0] for r in q(
            "SELECT DISTINCT build FROM events WHERE {tf} AND t_server >= ? "
            "AND build IS NOT NULL AND build <> ''", (since,))]

    finally:
        conn.close()

    buckets = [("<1 分钟", 0, 60), ("1–3 分钟", 60, 180), ("3–10 分钟", 180, 600),
               ("10–30 分钟", 600, 1800), ("30–60 分钟", 1800, 3600),
               ("≥1 小时", 3600, 10 ** 9)]
    dist = []
    for label, lo, hi in buckets:
        dist.append({"label": label, "n": sum(1 for s in per_run if lo <= s < hi)})

    return {
        "ok": True, "days": days, "events": total_events,
        "pv": pv, "uv": uv, "sessions": sessions, "runs": runs, "ready": ready,
        "ready_p50_ms": _pct(ready_ms, 0.5), "ready_p95_ms": _pct(ready_ms, 0.95),
        "errors": errors, "chapter_done": chapter_done, "endings_done": endings_done,
        "chapters": chapters, "choices": choices, "endings": endings,
        "sites": sites, "jumps": jumps, "daily": daily, "builds": builds,
        "play": {
            "runs": len(per_run),
            "avg": int(sum(per_run) / len(per_run)) if per_run else None,
            "p50": _pct(per_run, 0.5),
            "p90": _pct(per_run, 0.9),
            "max": per_run[-1] if per_run else None,
            "dist": dist,
        },
        "live": live_stats(),
    }


def purge_old(days=KEEP_DAYS):
    cutoff = int(time.time()) - days * 86400
    conn = connect()
    try:
        n = conn.execute("DELETE FROM events WHERE t_server < ?", (cutoff,)).rowcount
        conn.commit()
        conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    finally:
        conn.close()
    return n


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

_rl_lock = threading.Lock()
_rl = {}


def rate_ok(ip, limit=180, window=60):
    now = time.time()
    with _rl_lock:
        slot = _rl.get(ip)
        if not slot or now - slot[0] > window:
            _rl[ip] = [now, 1]
            return True
        if slot[1] >= limit:
            return False
        slot[1] += 1
        if len(_rl) > 4096:                 # 粗粒度的表大小保护
            for k in [k for k, v in _rl.items() if now - v[0] > window]:
                _rl.pop(k, None)
        return True


class Handler(BaseHTTPRequestHandler):
    server_version = "chaoshi-analytics"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        # 只记错误级别，正常请求不刷日志（每天几千条没必要留）
        pass

    # -- 工具 ---------------------------------------------------------------

    def _send(self, code, body, ctype="application/json; charset=utf-8",
              extra=None):
        if isinstance(body, str):
            body = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def _json(self, code, obj):
        self._send(code, json.dumps(obj, ensure_ascii=False,
                                    separators=(",", ":")))

    def _ip(self):
        return self.headers.get("CF-Connecting-IP") or self.client_address[0]

    # -- 路由 ---------------------------------------------------------------

    def do_OPTIONS(self):
        self._send(204, b"")

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"
        qs = parse_qs(u.query)

        if path == "/healthz":
            return self._json(200, {"ok": True})

        if path == "/api/live":
            if not rate_ok(self._ip()):
                return self._json(429, {"ok": False})
            with _live_lock:
                if time.time() - _live_cache["at"] < LIVE_TTL:
                    return self._send(200, _live_cache["body"])
            body = json.dumps(live_stats(), ensure_ascii=False,
                              separators=(",", ":")).encode("utf-8")
            with _live_lock:
                _live_cache["at"] = time.time()
                _live_cache["body"] = body
            return self._send(200, body)

        if path == "/api/stats":
            token = (qs.get("token") or [""])[0]
            if not TOKEN or token != TOKEN:
                return self._json(401, {"ok": False, "error": "token"})
            days = (qs.get("days") or ["30"])[0]
            try:
                days = int(days)
            except ValueError:
                days = 30
            inc = (qs.get("test") or ["0"])[0] in ("1", "true", "yes")
            return self._json(200, full_stats(days, include_test=inc))

        if path in ("/", "/index.html", "/dash"):
            p = os.path.join(HERE, "dash.html")
            with open(p, "rb") as f:
                return self._send(200, f.read(), "text/html; charset=utf-8")

        return self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        path = u.path.rstrip("/") or "/"

        if path == "/api/purge":
            # 只有持令牌的人能清库（部署时清理自己的验收数据）
            token = (parse_qs(u.query).get("token") or [""])[0]
            if not TOKEN or token != TOKEN:
                return self._json(401, {"ok": False})
            days = int((parse_qs(u.query).get("days") or [KEEP_DAYS])[0])
            return self._json(200, {"ok": True, "removed": purge_old(days)})

        if path != "/api/collect":
            return self._json(404, {"ok": False, "error": "not found"})

        if not rate_ok(self._ip()):
            return self._json(429, {"ok": False})

        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            length = 0
        if length <= 0 or length > MAX_BODY:
            return self._json(413, {"ok": False, "error": "size"})

        raw = self.rfile.read(length)
        try:
            payload = json.loads(raw.decode("utf-8", "replace"))
        except Exception:
            return self._json(400, {"ok": False, "error": "json"})

        events = payload.get("events") if isinstance(payload, dict) else payload
        if not isinstance(events, list):
            return self._json(400, {"ok": False, "error": "shape"})

        added, dup = ingest(events[:200])
        return self._json(200, {"ok": True, "added": added, "dup": dup})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--init", action="store_true", help="只建表后退出")
    ap.add_argument("--purge", type=int, metavar="DAYS", help="删掉 N 天前的事件")
    args = ap.parse_args()

    init_db()
    if args.init:
        print("schema ok:", DB_PATH)
        return 0
    if args.purge is not None:
        print("purged:", purge_old(args.purge))
        return 0

    if not TOKEN:
        print("warning: CHAOSHI_TOKEN 为空，看板接口将一律 401", file=sys.stderr)

    srv = ThreadingHTTPServer((BIND, PORT), Handler)
    srv.daemon_threads = True
    print("chaoshi-analytics on %s:%d, db=%s" % (BIND, PORT, DB_PATH))

    def janitor():
        while True:
            time.sleep(6 * 3600)
            try:
                purge_old()
            except Exception:
                pass

    threading.Thread(target=janitor, daemon=True).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
