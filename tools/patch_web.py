#!/usr/bin/env python3
"""对 Ren'Py web 构建做「可部署化」后处理。

做四件事：

1. **开屏与装载层**（tools/web/chaoshi-loader.js）
   Ren'Py 原生的 #statusDiv 只吐英文，报错后还会把游戏永久挂住。我们把
   整个开屏/进度/报错 UI 换成自绘的一层（中文、电影感片头、可点重试），
   原生 div 留在 DOM 里但隐藏，继续当「技术细节」的数据源。

2. **分片下载器加固**
   Ren'Py 原本用一次 fetch 拉整个 game.zip（本项目 6.7 MB，切 7 片）。
   原实现给每片 60 秒墙钟硬超时 —— 2 MB/60 s 要求链路持续 ≥34 KB/s，
   而实测 Cloudflare Pages 对 Range 请求返回 200 全量（不支持续传），
   超时后只能从 0 重来，弱网下必然耗尽重试。现改为「空闲 15 秒才中断」。

3. **后台预取清单**（chaoshi_prefetch.json）
   渐进式下载把 81 个资源留在 zip 外按需拉，一次网络抖动就报
   `Download error: network error`。进游戏后用空闲带宽把它们灌进 HTTP 缓存。

4. **缓存响应头与 build 指纹**
   game.zip.* 曾用 7 天强缓存且 URL 无版本，新构建可能命中旧分片。

可重复执行（幂等）。用法：

    python3 tools/patch_web.py build/web
"""

import json
import os
import re
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 1 MB/片：Cloudflare 不支持 Range 时，单片失败的代价比 2 MB 减半
PART_SIZE = 1_000_000

LOADER_MARK_START = "    async function loadGameZip() {"
LOADER_MARK_END = "    function runLoadGameZip() {"
SENTINEL = "/* CHAOSHI_LOADER_V2 */"

MIRRORS = {
    "gh": "https://gongfpp.github.io/chaoshi-2018/",
    "cf": "https://chaoshi-2018.pages.dev/",
}

# 生产埋点端点（Cloudflare Worker + D1）。本地调试时 tracker 自动回落到同源
# /api/collect，由 tools/collector.py 接收，所以这里只填线上地址。
COLLECT_URL = os.environ.get(
    "CHAOSHI_COLLECT", "https://chaoshi-analytics.gong7968.workers.dev/api/collect")


# ---------------------------------------------------------------------------
# 注入的分片下载器
# ---------------------------------------------------------------------------

NEW_LOADER = r'''    /* CHAOSHI_LOADER_V2 */
    // ---- 并行分片 + 空闲超时 + 后台预取（由 tools/patch_web.py 注入）------
    // 与 Windows 无关的三条约束：
    //   1) 不能用墙钟超时判失败 —— 弱网是「慢」不是「死」，只有连续 IDLE_MS
    //      收不到字节才算断流（Cloudflare 不支持 Range，断了就得从头再来）。
    //   2) 进度只认 Σ st.got 一个账本，重下不能让进度条倒退或溢出。
    //   3) 落盘后必须核对字节数，截断的 zip 会让 Ren'Py 报 BadZipFile，
    //      不如在这里就说清楚。
    var CS = window.ChaoshiLoader || null;
    var GAME_FILE = null;
    var GAME_PARTS = [];
    var PREFETCH = null;

    var PART_CONC = 3;          // 弱网下 3 条流比 4 条更容易各自跑满
    var IDLE_MS = 15000;        // 连续 15 秒零字节才判定断流
    var ATTEMPT_MS = 180000;    // 单次尝试的墙钟兜底（不是主判据）
    var MAX_TRIES = 6;

    function csLog(s) { if (CS && CS.log) { CS.log(s); } }

    function csSleep(ms) {
        return new Promise(function (r) { setTimeout(r, ms); });
    }

    function zipBytes() {
        var n = 0;
        for (var i = 0; i < GAME_PARTS.length; i++) { n += GAME_PARTS[i].got; }
        return gameZipSize ? Math.min(n, gameZipSize) : n;
    }

    function reportZip() {
        if (CS && CS.zipProgress) { CS.zipProgress(zipBytes(), gameZipSize); }
    }

    function bootFail(kind, detail) {
        // 有自绘 UI 就走自绘；没有（理论上不会）退回原生报错，至少别白屏
        if (CS && CS.fatal) {
            CS.fatal(kind, detail);
        } else {
            reportError('Could not download game data', { message: String(detail || '') });
        }
    }

    function partsMeta() {
        var names = window.gameZipParts || [];
        var sizes = window.gameZipPartSizes || [];
        var total = 0;
        for (var i = 0; i < sizes.length; i++) { total += sizes[i] || 0; }
        return { names: names, sizes: sizes, total: window.gameZipTotal || total };
    }

    // 单次尝试：一次 fetch + 读完整个 body。返回的 Promise 只有在
    // 「本片已经收满」或「确定失败」时才会落定。
    function pullPart(st) {
        return new Promise(function (resolve, reject) {
            var ctrl = new AbortController();
            var lastByte = Date.now();
            var done = false;

            var idle = setInterval(function () {
                if (Date.now() - lastByte > IDLE_MS) {
                    try { ctrl.abort(); } catch (e) {}
                }
            }, 2000);
            var wall = setTimeout(function () {
                try { ctrl.abort(); } catch (e) {}
            }, ATTEMPT_MS);

            function finish(err) {
                if (done) { return; }
                done = true;
                clearInterval(idle);
                clearTimeout(wall);
                if (err) { reject(err); } else { resolve(); }
            }

            var wantFrom = st.got;
            var opt = { cache: 'default', signal: ctrl.signal };
            if (wantFrom > 0) { opt.headers = { 'Range': 'bytes=' + wantFrom + '-' }; }

            // 服务端忽略 Range（Cloudflare 返回 200 全量）时，body 是从 0 开始的，
            // 要把前面已经收到过的字节读掉再接着算，否则 zip 会整体错位。
            var skip = 0;

            fetch(st.url, opt).then(function (r) {
                if (!r.ok && r.status !== 206) {
                    throw new Error('HTTP ' + r.status + ' ' + r.statusText);
                }
                st.status = r.status;
                skip = (r.status === 206) ? 0 : wantFrom;
                if (!r.body || !r.body.getReader) {
                    return r.arrayBuffer().then(function (buf) {
                        var u8 = new Uint8Array(buf);
                        if (skip > 0) { u8 = u8.subarray(skip); skip = 0; }
                        lastByte = Date.now();
                        st.chunks.push(u8);
                        st.got += u8.length;
                        reportZip();
                    });
                }
                var reader = r.body.getReader();
                function pump() {
                    return reader.read().then(function (c) {
                        if (c.done) { return; }
                        lastByte = Date.now();
                        var v = c.value;
                        if (skip > 0) {
                            if (v.length <= skip) { skip -= v.length; return pump(); }
                            v = v.subarray(skip);
                            skip = 0;
                        }
                        st.chunks.push(v);
                        st.got += v.length;
                        reportZip();
                        return pump();
                    });
                }
                return pump();
            }).then(function () {
                if (st.size && st.got < st.size) {
                    throw new Error('分片不完整 ' + st.got + '/' + st.size);
                }
                finish(null);
            }).catch(function (e) {
                finish(e);
            });
        });
    }

    async function pullWithRetry(st) {
        var tries = 0;
        while (!st.size || st.got < st.size) {
            tries += 1;
            try {
                await pullPart(st);
            } catch (e) {
                st.lastErr = e;
                if (tries >= MAX_TRIES) {
                    throw new Error('分片 ' + st.url + ' 连续 ' + tries + ' 次失败：'
                                    + (e && e.message ? e.message : e));
                }
                csLog('retry ' + st.url + ' #' + tries + '：' + (e && e.message));
                await csSleep(700 * tries);
                continue;
            }
            if (!st.size || st.got >= st.size) { break; }
        }
        st.done = true;
        reportZip();
    }

    function startPrefetch() {
        if (PREFETCH) { return PREFETCH; }
        var m = partsMeta();
        GAME_PARTS = m.names.map(function (n, i) {
            return {
                url: n, size: m.sizes[i] || 0,
                chunks: [], got: 0, done: false, status: 0
            };
        });
        gameZipSize = m.total;
        if (CS && CS.zipProgress) { CS.zipProgress(0, gameZipSize); }

        PREFETCH = (async function () {
            var cursor = 0;
            var workers = [];
            for (var w = 0; w < PART_CONC; w++) {
                workers.push((async function () {
                    while (cursor < GAME_PARTS.length) {
                        var st = GAME_PARTS[cursor];
                        cursor += 1;
                        try {
                            await pullWithRetry(st);
                        } catch (e) {
                            st.error = e;
                            csLog('part gave up: ' + st.url);
                        }
                    }
                })());
            }
            await Promise.all(workers);
        })();
        return PREFETCH;
    }

    async function loadGameZip() {
        try {
            var m = partsMeta();
            gameZipSize = m.total;

            await startPrefetch();

            // 预取阶段放弃的分片：这里串行再兜一次（单独跑，不抢带宽）
            for (var i = 0; i < GAME_PARTS.length; i++) {
                var bad = GAME_PARTS[i];
                if (!bad.done) {
                    bad.chunks = bad.chunks || [];
                    await pullWithRetry(bad);
                }
            }

            GAME_FILE = FS.open('/game.zip', 'w');
            var offset = 0;
            for (var k = 0; k < GAME_PARTS.length; k++) {
                var p = GAME_PARTS[k];
                for (var j = 0; j < p.chunks.length; j++) {
                    var b = p.chunks[j];
                    FS.write(GAME_FILE, b, 0, b.length, offset);
                    offset += b.length;
                }
                p.chunks = [];
            }
            FS.close(GAME_FILE);
            GAME_FILE = null;

            var size = FS.stat('/game.zip').size;
            if (size !== gameZipSize) {
                throw new Error('落盘 ' + size + ' 字节，应为 ' + gameZipSize + ' 字节');
            }
            if (CS && CS.zipProgress) { CS.zipProgress(gameZipSize, gameZipSize); }

        } catch (e) {
            if (GAME_FILE) { try { FS.close(GAME_FILE); } catch (x) {} GAME_FILE = null; }
            var msg = (e && e.message) ? e.message : String(e);
            var kind = 'idle';
            if (/HTTP 4\d\d|HTTP 5\d\d/.test(msg)) { kind = 'http'; }
            else if (/不完整|落盘|offset/.test(msg)) { kind = 'incomplete'; }
            csLog('loadGameZip failed: ' + msg);
            bootFail(kind, msg);
        }
    }

    // 立即开始下载，与 wasm 的下载/编译并行
    startPrefetch();
'''


# ---------------------------------------------------------------------------
# 工具函数
# ---------------------------------------------------------------------------

def build_id():
    env = os.environ.get("CHAOSHI_BUILD", "").strip()
    if env:
        return env
    try:
        h = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                           cwd=ROOT, capture_output=True, text=True).stdout.strip()
        dirty = subprocess.run(["git", "diff", "--quiet"], cwd=ROOT).returncode != 0
        return (h or "nogit") + ("-dirty" if dirty else "")
    except Exception:
        return "nogit"


def split_zip(root):
    """把 game.zip 切成固定大小的分片，并返回清单。"""
    zip_path = os.path.join(root, "game.zip")
    if not os.path.exists(zip_path):
        meta_path = os.path.join(root, "game.zip.parts.json")
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                return json.load(f)
        raise SystemExit("game.zip 不存在，先跑 web_build")

    data = open(zip_path, "rb").read()
    for name in os.listdir(root):
        if re.fullmatch(r"game\.zip\.\d{3}", name):
            os.remove(os.path.join(root, name))

    parts = []
    for i in range(0, len(data), PART_SIZE):
        chunk = data[i:i + PART_SIZE]
        name = "game.zip.%03d" % (i // PART_SIZE)
        with open(os.path.join(root, name), "wb") as f:
            f.write(chunk)
        parts.append({"name": name, "size": len(chunk)})

    meta = {"total": len(data), "parts": parts}
    with open(os.path.join(root, "game.zip.parts.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f)
    os.remove(zip_path)
    return meta


def copy_loader(root):
    """把开屏层脚本放进站点根目录。"""
    src = os.path.join(ROOT, "tools", "web", "chaoshi-loader.js")
    if not os.path.exists(src):
        raise SystemExit("缺少 tools/web/chaoshi-loader.js")
    shutil.copy2(src, os.path.join(root, "chaoshi-loader.js"))
    return True


def patch_index(root, meta, build):
    path = os.path.join(root, "index.html")
    s = open(path, encoding="utf-8").read()

    # --- 中文界面 ---
    s = s.replace('<html lang="en-us">', '<html lang="zh-CN">', 1)

    # --- 分片清单（带 build 指纹，避免命中上一版的强缓存） ---
    s = re.sub(r"\n\s*// 分片信息（tools/patch_web\.py 注入）[\s\S]*?window\.gameZipTotal = \d+;\n",
               "\n", s)
    q = "?b=" + build
    parts_js = "\n      // 分片信息（tools/patch_web.py 注入）\n"
    parts_js += "      window.gameZipParts = %s;\n" % json.dumps(
        [p["name"] + q for p in meta["parts"]])
    parts_js += "      window.gameZipPartSizes = %s;\n" % json.dumps(
        [p["size"] for p in meta["parts"]])
    parts_js += "      window.gameZipTotal = %d;\n" % meta["total"]
    anchor = "      window.gameZipURL = 'game.zip';"
    if anchor not in s:
        raise SystemExit("index.html 中找不到 gameZipURL")
    s = s.replace(anchor, anchor + parts_js, 1)

    # --- 旧的 90 秒看门狗（已被自绘开屏取代） ---
    s = re.sub(r'\s*<script id="wb-timeout-watchdog">[\s\S]*?</script>\n?', "\n", s)

    # --- service worker：主动注销 + 清缓存 ---
    # 旧 SW 会把上一版的 index.html / renpy-pre.js / game.zip 分片钉在 Cache
    # Storage 里，表现是「代码改了、线上没变」或「分片校验失败」。宁可不离线。
    i = s.find("// Register the service worker.")
    if i != -1:
        j = s.find("</script>", i)
        if j == -1:
            raise SystemExit("index.html 的 SW 段落没有收尾")
        s = s[:i] + SW_OFF + "\n    " + s[j:]

    # --- 埋点桥：必须比开屏层更早，否则 boot_ready / error 事件全丢 ---
    s = re.sub(r"\s*<script>\s*\(function \(\) \{\s*var BUILD =[\s\S]*?</script>\n", "\n", s)

    # --- 开屏层：插在 renpy-pre.js 之前（此时 gameZipTotal / BUILD 已就绪） ---
    s = re.sub(r'\s*<script>window\.CHAOSHI_BUILD[\s\S]*?<script src="chaoshi-loader\.js"></script>\n?',
               "\n", s)
    boot_anchor = '  <script src="renpy-pre.js"></script>'
    if boot_anchor not in s:
        raise SystemExit("index.html 中找不到 renpy-pre.js")
    sizes = {"zip": meta["total"]}
    for k, fn in (("wasm", "renpy.wasm"), ("data", "renpy.data")):
        p = os.path.join(root, fn)
        sizes[k] = os.path.getsize(p) if os.path.exists(p) else 0
    boot_js = (
        "  <script>window.CHAOSHI_BUILD=%s;window.CHAOSHI_MIRRORS=%s;"
        "window.CHAOSHI_SIZES=%s;</script>\n"
        "%s\n"
        "  <script src=\"chaoshi-loader.js\"></script>\n"
    ) % (json.dumps(build), json.dumps(MIRRORS, ensure_ascii=False),
         json.dumps(sizes), tracker_script(build))
    s = s.replace(boot_anchor, boot_js + boot_anchor, 1)

    if s.count("chaoshiTrack") < 2:
        raise SystemExit("埋点脚本没有注入成功")

    open(path, "w", encoding="utf-8").write(s)


SW_OFF = """      // 旧的 service worker 会把上一版 game.zip 分片与 index.html 钉在缓存里，
      // 表现是「改了代码线上没变」。这里主动注销，并清掉它留下的 caches。
      (function () {
          if (!navigator.serviceWorker) { return; }
          navigator.serviceWorker.getRegistrations().then(function (rs) {
              rs.forEach(function (r) { r.unregister(); });
          }).catch(function () {});
          if (window.caches && caches.keys) {
              caches.keys().then(function (ks) {
                  ks.forEach(function (k) { caches.delete(k); });
              }).catch(function () {});
          }
      })();"""


def tracker_script(build):
    """页面级埋点：page_view / game_ready / error，并承接游戏侧事件。"""
    return """  <script>
  (function () {
    if (window.chaoshiTrack) { return; }
    var BUILD = %(build)s;
    // 线上发到 Cloudflare Worker + D1；本地（localhost/127.0.0.1）仍走同源
    // /api/collect，由 tools/collector.py 接收，避免调试时污染生产数据。
    var host = location.hostname;
    var ENDPOINT = window.CHAOSHI_COLLECT ||
      ((host === "localhost" || host === "127.0.0.1" || !host) ? "/api/collect" : %(collect)s);
    function rid(p) { return p + Math.random().toString(36).slice(2, 10) + Date.now().toString(36); }

    var vid = localStorage.getItem("chaoshi_vid");
    if (!vid) { vid = rid("v_"); localStorage.setItem("chaoshi_vid", vid); }
    var sKey = "chaoshi_sid_" + Math.floor(Date.now() / 1800000);
    var sid = sessionStorage.getItem(sKey);
    if (!sid) { sid = rid("s_"); sessionStorage.setItem(sKey, sid); }

    var queue = [], seq = 0, readySent = false, t0 = performance.now();

    // 关键节点立刻发，不等攒够 8 条：否则玩家关页/切走时这些事件会丢在队列里
    var IMMEDIATE = {
      page_view: 1, game_ready: 1, run_start: 1, chapter_enter: 1,
      chapter_complete: 1, choice_pick: 1, ending_enter: 1,
      ending_complete: 1, error: 1, voice_fail: 1
    };

    function flush() {
      if (!queue.length) { return; }
      var body = JSON.stringify({ events: queue.splice(0, 50) });
      var ok = false;
      try {
        if (navigator.sendBeacon) {
          // text/plain 不触发 CORS 预检，sendBeacon 才能可靠送达
          ok = navigator.sendBeacon(ENDPOINT, new Blob([body], { type: "text/plain;charset=UTF-8" }));
        }
      } catch (e) { ok = false; }
      if (!ok) {
        try {
          fetch(ENDPOINT, {
            method: "POST", body: body, keepalive: true,
            headers: { "Content-Type": "text/plain;charset=UTF-8" }
          });
        } catch (e) {}
      }
    }

    window.chaoshiTrack = function (raw) {
      try {
        var e = (typeof raw === "string") ? JSON.parse(raw) : raw;
        e.vid = vid; e.sid = sid; e.seq = ++seq; e.build = BUILD;
        e.site = location.host; e.t_client = e.t || Date.now();
        e.ref = document.referrer ? document.referrer.replace(/[?#].*$/, "") : "";
        queue.push(e);
        if (queue.length >= 8 || IMMEDIATE[e.event]) { flush(); }
      } catch (err) {}
    };

    window.addEventListener("message", function (ev) {
      if (ev.data && typeof ev.data.__chaoshi_event === "string") {
        window.chaoshiTrack(ev.data.__chaoshi_event);
      }
    });

    setInterval(flush, 4000);
    window.addEventListener("pagehide", flush);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden") { flush(); }
    });

    window.chaoshiTrack({ event: "page_view" });

    var iv = setInterval(function () {
      var c = document.querySelector("canvas");
      if (c && c.width > 640 && !readySent) {
        readySent = true;
        clearInterval(iv);
        window.chaoshiTrack({ event: "game_ready", ms: Math.round(performance.now() - t0) });
      }
    }, 500);

    window.addEventListener("error", function (ev) {
      window.chaoshiTrack({
        event: "error", reason: String(ev.message || "script").slice(0, 120)
      });
    });
  })();
  </script>""" % {"build": json.dumps(build), "collect": json.dumps(COLLECT_URL)}


def patch_loader(root):
    path = os.path.join(root, "renpy-pre.js")
    s = open(path, encoding="utf-8").read()

    # 幂等：先把上一次注入的块整段剥掉（块本身也包含 loadGameZip 这个函数名，
    # 直接按锚点找会把旧块当成新位置，越注越多）
    while SENTINEL in s:
        i = s.index(SENTINEL)
        j = s.find(LOADER_MARK_END, i)
        if j == -1:
            raise SystemExit("上一次注入的块没有收尾锚点，请重新 web_build")
        s = s[:i] + "@@CHAOSHI_INSERT@@" + s[j:]

    if s.count("@@CHAOSHI_INSERT@@") > 1:
        s = s.replace("@@CHAOSHI_INSERT@@", "")

    if "@@CHAOSHI_INSERT@@" not in s:
        start = s.find(LOADER_MARK_START)
        end = s.find(LOADER_MARK_END)
        if start == -1 or end == -1 or end <= start:
            head = "\n".join(s.splitlines()[:40])
            raise SystemExit(
                "renpy-pre.js 结构变了（SDK 升级？），找不到注入锚点。\n"
                "期望：%r / %r\n文件头：\n%s" % (LOADER_MARK_START, LOADER_MARK_END, head))
        s = s[:start] + "@@CHAOSHI_INSERT@@" + s[end:]

    s = s.replace("@@CHAOSHI_INSERT@@", NEW_LOADER.rstrip("\n") + "\n", 1)

    if s.count(SENTINEL) != 1:
        raise SystemExit("注入哨兵数量异常：%d（应为 1）" % s.count(SENTINEL))

    open(path, "w", encoding="utf-8").write(s)


PRIORITY = [
    ("images/cg/title", 0),   # 主菜单底图
    ("images/bg/", 1),        # 每章立刻要用
    ("images/char/", 2),      # 立绘
    ("images/cg/", 3),
    ("audio/sfx/", 4),        # 小文件，快
    ("audio/bgm/", 5),        # 最大，最后
]


def make_prefetch_manifest(root, build):
    """扫 build/web/game 下的渐进式资源，生成预取清单。

    这份清单与 Ren'Py 的 progressive_download.txt 天然一致（后者把
    image/** 与 audio/** 全部移出 zip），所以资源增删不需要改代码。
    """
    game_dir = os.path.join(root, "game")
    if not os.path.isdir(game_dir):
        raise SystemExit("build/web/game 不存在，先跑 web_build")

    files = []
    total = 0
    for dirpath, _dirs, names in os.walk(game_dir):
        for n in names:
            full = os.path.join(dirpath, n)
            rel = os.path.relpath(full, game_dir).replace(os.sep, "/")
            if not (rel.startswith("images/") or rel.startswith("audio/")):
                continue
            size = os.path.getsize(full)
            prio = 9
            for pref, p in PRIORITY:
                if rel.startswith(pref):
                    prio = p
                    break
            files.append({"p": rel, "b": size, "prio": prio})
            total += size

    files.sort(key=lambda f: (f["prio"], f["b"]))
    man = {"build": build, "total": total, "files": files}
    with open(os.path.join(root, "chaoshi_prefetch.json"), "w", encoding="utf-8") as f:
        json.dump(man, f, separators=(",", ":"))
    return man


def write_build_json(root, build):
    meta = {
        "build": build,
        "time": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                               capture_output=True, text=True).stdout.strip(),
    }
    with open(os.path.join(root, "build.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False)
    return meta


def patch_catalog(root, meta):
    path = os.path.join(root, "pwa_catalog.json")
    if not os.path.exists(path):
        return
    d = json.load(open(path, encoding="utf-8"))
    files = [f for f in d.get("files", []) if f != "game.zip"]
    files += [p["name"] for p in meta["parts"]]
    d["files"] = files
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False)


def copy_dashboard(root):
    src = os.path.join(ROOT, "tools", "dash.html")
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(root, "dash.html"))
        return True
    return False


def write_headers(root):
    """仅 Cloudflare Pages / Netlify 会读；GitHub Pages 忽略。

    注意：Cloudflare 按「先匹配先生效」，所以具体路径要写在 /* 之前。
    """
    s = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer

/chaoshi-loader.js
  Cache-Control: no-cache

/build.json
  Cache-Control: no-cache

/chaoshi_prefetch.json
  Cache-Control: no-cache

/index.html
  Cache-Control: public, max-age=300

/renpy.wasm
  Cache-Control: public, max-age=604800
  Content-Type: application/wasm

/renpy.data
  Cache-Control: public, max-age=604800

/game.zip.*
  Cache-Control: public, max-age=86400

/game/*
  Cache-Control: public, max-age=86400

/*.js
  Cache-Control: public, max-age=300
"""
    open(os.path.join(root, "_headers"), "w", encoding="utf-8").write(s)


def make_presplash(root):
    """把默认启动图换成标题 CG。

    **图上不烧任何文字** —— 以前用子集化字库渲染，缺字直接显示成方框
    （「首」「若」「此」）。现在所有文案由 chaoshi-loader.js 用系统字体
    在 HTML 层渲染，这张图只负责画面。
    """
    title = os.path.normpath(os.path.join(ROOT, "game", "game", "images", "cg", "title.jpg"))
    if not os.path.exists(title):
        return False
    try:
        from PIL import Image
    except ImportError:
        raise SystemExit("需要 Pillow：请用 "
                         "$HOME/.workbuddy/binaries/python/envs/default/bin/python")

    W, H = 1280, 720
    im = Image.open(title).convert("RGB")
    if im.size != (W, H):
        im = im.resize((W, H), Image.LANCZOS)
    # 压暗一点，让上层的中文和进度条压得住；不要压太狠，CSS 还有一层 scrim
    im = Image.eval(im, lambda v: int(v * 0.78))
    # 渐进式 JPEG：首屏先出模糊轮廓。80 质量约 110 KB，q84 会翻到 1 MB 以上
    im.save(os.path.join(root, "web-presplash.jpg"), quality=80,
            optimize=True, progressive=True)
    return True


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "build/web"
    root = os.path.abspath(root)
    build = build_id()

    meta = split_zip(root)
    copy_loader(root)
    patch_index(root, meta, build)
    patch_loader(root)
    manifest = make_prefetch_manifest(root, build)
    write_build_json(root, build)
    patch_catalog(root, meta)
    write_headers(root)
    copy_dashboard(root)
    made = make_presplash(root)

    biggest = max(p["size"] for p in meta["parts"])
    print("build id: %s" % build)
    print("分片: %d 片，最大 %.2f MB，zip 合计 %.2f MB" % (
        len(meta["parts"]), biggest / 1e6, meta["total"] / 1e6))
    print("预取清单: %d 个资源，%.1f MB" % (len(manifest["files"]), manifest["total"] / 1e6))
    print("启动图: %s（无文字）" % ("已替换" if made else "跳过"))


if __name__ == "__main__":
    main()
