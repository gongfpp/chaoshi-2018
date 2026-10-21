#!/usr/bin/env python3
"""本地埋点采集 + 看板（生产用 Cloudflare Pages Functions + D1，接口一致）。

    python3 tools/collector.py            # http://127.0.0.1:8090/
    python3 tools/collector.py --port 8090

路由：
    POST /api/collect     接收 {events:[...]}，落盘到 build/analytics/events.jsonl
    GET  /api/stats       聚合结果（需要 ?token=<ANALYTICS_TOKEN>）
    GET  /dash.html       看板页面
    其余                   静态服务 build/web

环境变量：ANALYTICS_TOKEN（默认 chaoshi-local）
"""

import json
import os
import sys
import time
import collections
from http.server import HTTPServer, SimpleHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WEB = os.path.join(ROOT, "build", "web")
DATA = os.path.join(ROOT, "build", "analytics")
TOKEN = os.environ.get("ANALYTICS_TOKEN", "chaoshi-local")
MAX_BYTES = 64 * 1024

ALLOWED = {
    "page_view", "game_ready", "run_start", "chapter_enter", "chapter_complete",
    "chapter_jump", "choice_shown", "choice_pick", "ending_enter",
    "ending_complete", "save_ok", "save_fail", "load_ok", "load_fail",
    "skip_on", "auto_on", "mute_on", "voice_fail", "error",
}


def day_path():
    return os.path.join(DATA, time.strftime("%Y-%m-%d") + ".jsonl")


def load_events(days=30):
    rows = []
    if not os.path.isdir(DATA):
        return rows
    for name in sorted(os.listdir(DATA))[-days:]:
        if not name.endswith(".jsonl"):
            continue
        with open(os.path.join(DATA, name), encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        rows.append(json.loads(line))
                    except ValueError:
                        pass
    return rows


def aggregate(events, exclude_test=True):
    """按文档口径聚合：UV 按匿名 id，测试流量默认排除。"""
    ev = [e for e in events if not (exclude_test and e.get("test"))]
    uvs = {e.get("vid") for e in ev if e.get("event") == "page_view"}
    sessions = {e.get("sid") for e in ev if e.get("sid")}
    pv = sum(1 for e in ev if e.get("event") == "page_view")
    ready = [e for e in ev if e.get("event") == "game_ready"]
    runs = {e.get("run_id") for e in ev if e.get("event") == "run_start"}
    chapters = collections.Counter(e.get("chapter") for e in ev if e.get("event") == "chapter_enter")
    choices = collections.Counter(
        "%s#%s" % (e.get("choice"), e.get("option")) for e in ev if e.get("event") == "choice_pick")
    endings = collections.Counter(e.get("ending") for e in ev if e.get("event") == "ending_complete")
    sites = collections.Counter(e.get("site") for e in ev if e.get("event") == "page_view")
    builds = collections.Counter(e.get("build") for e in ev)
    ready_ms = sorted(e.get("ms", 0) for e in ready if isinstance(e.get("ms"), int))

    def pct(vals, q):
        if not vals:
            return None
        i = min(len(vals) - 1, int(round((len(vals) - 1) * q)))
        return vals[i]

    return {
        "pv": pv,
        "uv": len(uvs),
        "sessions": len(sessions),
        "runs": len(runs),
        "ready": len(ready),
        "ready_p50_ms": pct(ready_ms, 0.5),
        "ready_p95_ms": pct(ready_ms, 0.95),
        "chapters": chapters.most_common(),
        "choices": choices.most_common(),
        "endings": endings.most_common(),
        "sites": sites.most_common(),
        "builds": builds.most_common(5),
        "errors": sum(1 for e in ev if e.get("event") == "error"),
        "events": len(ev),
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=WEB, **kw)

    def log_message(self, *a):
        pass

    def _json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if not self.path.startswith("/api/collect"):
            self._json({"ok": False}, 404)
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0 or length > MAX_BYTES:
            self._json({"ok": False, "error": "bad length"}, 413)
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except ValueError:
            self._json({"ok": False, "error": "bad json"}, 400)
            return

        os.makedirs(DATA, exist_ok=True)
        now = int(time.time() * 1000)
        kept = 0
        with open(day_path(), "a", encoding="utf-8") as f:
            for e in payload.get("events", [])[:100]:
                if not isinstance(e, dict) or e.get("event") not in ALLOWED:
                    continue
                e["t_server"] = now
                e.setdefault("site", self.headers.get("Host", ""))
                f.write(json.dumps(e, ensure_ascii=False) + "\n")
                kept += 1
        self._json({"ok": True, "kept": kept})

    def do_GET(self):
        if self.path.startswith("/api/stats"):
            from urllib.parse import urlparse, parse_qs
            q = parse_qs(urlparse(self.path).query)
            if q.get("token", [""])[0] != TOKEN:
                self._json({"error": "unauthorized"}, 401)
                return
            self._json(aggregate(load_events()), 200)
            return
        if self.path in ("/", ""):
            self.path = "/index.html"
        super().do_GET()


def main():
    port = 8090
    if "--port" in sys.argv:
        port = int(sys.argv[sys.argv.index("--port") + 1])
    print("采集端：http://127.0.0.1:%d/   看板：/dash.html?token=%s" % (port, TOKEN))
    HTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__":
    main()
