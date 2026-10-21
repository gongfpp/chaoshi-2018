#!/usr/bin/env python3
"""对 Ren'Py web 构建做「可部署化」后处理。

背景：Ren'Py 的 web 加载器用**单个请求**拉 game.zip（本项目 33 MB），
中途断线就永远停在 presplash，而且 Cloudflare Pages 单文件上限 25 MiB。

本脚本把 game.zip 切成多个分片，并把加载器改成分片下载 + 断点续传 + 重试，
同时补上 Cloudflare Pages 的缓存响应头。可重复执行（幂等）。

    python3 tools/patch_web.py build/web
"""

import json
import os
import subprocess
import re
import shutil
import sys

PART_SIZE = 2_000_000  # 2 MB/片：足够并行，单片失败代价小

LOADER_MARK_START = "    async function loadGameZip() {"
LOADER_MARK_END = "    function runLoadGameZip() {"

NEW_LOADER = r'''    // ---- 并行分片 + 提前预取（由 tools/patch_web.py 注入）------------------
    // Ren'Py 原本用一次 fetch 拉整个 game.zip，要等 wasm 编译完才开始，弱网下还会断。
    // 这里做两件事：
    //   1) 页面一加载就开始分片下载（与 wasm/引擎数据并行），下载结果先存在内存里；
    //   2) 每片独立重试、支持 Range 续传，写入时按各自偏移量落到 /game.zip。
    var GAME_FILE = null;
    var GAME_PARTS = [];
    var PREFETCH = null;

    async function fetchPart(url, from, tries) {
        var lastErr = null;
        for (var i = 0; i < tries; i++) {
            var ctrl = new AbortController();
            var timer = setTimeout(function () { ctrl.abort(); }, 60000);
            try {
                var opt = { cache: 'default', signal: ctrl.signal };
                if (from > 0) {
                    opt.headers = { 'Range': 'bytes=' + from + '-' };
                }
                var r = await fetch(url, opt);
                clearTimeout(timer);
                if (!r.ok && r.status !== 206) {
                    throw new Error('HTTP ' + r.status + ' ' + r.statusText);
                }
                return r;
            } catch (e) {
                clearTimeout(timer);
                lastErr = e;
                if (i < tries - 1) {
                    await new Promise(function (res) { setTimeout(res, 800 * (i + 1)); });
                }
            }
        }
        throw lastErr || new Error('fetch failed');
    }

    function partsMeta() {
        var names = window.gameZipParts || [];
        var sizes = window.gameZipPartSizes || [];
        var offsets = [];
        var acc = 0;
        for (var i = 0; i < names.length; i++) {
            offsets.push(acc);
            acc += sizes[i] || 0;
        }
        return { names: names, sizes: sizes, offsets: offsets, total: window.gameZipTotal || acc };
    }

    async function fetchPartToMemory(st) {
        var got = 0;
        var attempt = 0;
        while (st.size === 0 || got < st.size) {
            var r = await fetchPart(st.url, got, 6);
            if (got > 0 && r.status !== 206) {
                // 服务端忽略 Range（返回 200 全量），从本片起点重来
                got = 0;
                st.chunks = [];
            }
            var reader = r.body.getReader();
            var finished = false;
            try {
                while (true) {
                    var chunk = await reader.read();
                    if (chunk.done) { finished = true; break; }
                    st.chunks.push(chunk.value);
                    got += chunk.value.length;
                    st.got = got;
                    gameZipDownloaded += chunk.value.length;
                    updateDownloadProgress();
                }
            } catch (e) {
                attempt += 1;
                if (attempt >= 6) { throw e; }
                await new Promise(function (res) { setTimeout(res, 800 * attempt); });
                continue;
            }
            if (finished && (st.size === 0 || got >= st.size)) { st.done = true; return; }
            attempt += 1;
            if (attempt >= 8) {
                throw new Error('分片下载不完整：' + st.url + '（' + got + '/' + st.size + '）');
            }
            await new Promise(function (res) { setTimeout(res, 800 * attempt); });
        }
        st.done = true;
    }

    function startPrefetch() {
        if (PREFETCH) { return PREFETCH; }
        var m = partsMeta();
        GAME_PARTS = m.names.map(function (n, i) {
            return {
                url: n, size: m.sizes[i] || 0, offset: m.offsets[i],
                chunks: [], got: 0, written: 0, done: false
            };
        });
        gameZipSize = m.total;
        PREFETCH = Promise.all(GAME_PARTS.map(function (st) {
            return fetchPartToMemory(st).catch(function (e) { st.error = e; });
        }));
        return PREFETCH;
    }

    async function loadGameZip() {
        try {
            var m = partsMeta();
            gameZipSize = m.total;
            GAME_FILE = FS.open('/game.zip', 'w');

            await startPrefetch();

            for (var i = 0; i < GAME_PARTS.length; i++) {
                var st = GAME_PARTS[i];
                if (!st.done) {
                    // 预取失败的分片：清空后重下（带 Range 续传）
                    st.chunks = [];
                    st.got = 0;
                    await fetchPartToMemory(st);
                }
                for (var j = 0; j < st.chunks.length; j++) {
                    var b = st.chunks[j];
                    FS.write(GAME_FILE, b, 0, b.length, st.offset + st.written);
                    st.written += b.length;
                }
                st.chunks = [];
            }

            FS.close(GAME_FILE);
            GAME_FILE = null;

        } catch (e) {
            reportError('Could not download game data', e);
        }
    }

    // 立即开始下载游戏数据，与 wasm 的下载/编译并行
    startPrefetch();
'''


def split_zip(root):
    zip_path = os.path.join(root, "game.zip")
    if not os.path.exists(zip_path):
        meta_path = os.path.join(root, "game.zip.parts.json")
        if os.path.exists(meta_path):
            with open(meta_path, encoding="utf-8") as f:
                return json.load(f)
        raise SystemExit("game.zip 不存在，先跑 web_build")
    data = open(zip_path, "rb").read()
    # 清掉上一次的分片
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


def patch_index(root, meta):
    path = os.path.join(root, "index.html")
    s = open(path, encoding="utf-8").read()
    # 先移除上一次注入的块
    s = re.sub(r"\n\s*// 分片信息（tools/patch_web\.py 注入）[\s\S]*?window\.gameZipTotal = \d+;\n",
               "\n", s)
    parts_js = "\n      // 分片信息（tools/patch_web.py 注入）\n"
    parts_js += "      window.gameZipParts = %s;\n" % json.dumps([p["name"] for p in meta["parts"]])
    parts_js += "      window.gameZipPartSizes = %s;\n" % json.dumps([p["size"] for p in meta["parts"]])
    parts_js += "      window.gameZipTotal = %d;\n" % meta["total"]
    anchor = "      window.gameZipURL = 'game.zip';"
    if anchor not in s:
        raise SystemExit("index.html 中找不到 gameZipURL")
    s = s.replace(anchor, anchor + parts_js, 1)

    # 关闭 Service Worker：它会把大文件塞进 Cache Storage，一旦某次下载中断，
    # 坏条目可能在客户端长期驻留（表现为「一直 loading」）。同时清理旧缓存。
    if "停用 Service Worker" not in s:
        sw_re = re.compile(r"      if \(navigator\.serviceWorker\) \{[\s\S]*?\n      \}\n")
        cleanup = (
            "      // 停用 Service Worker，并清理旧缓存（tools/patch_web.py 注入）\n"
            "      if (window.caches) {\n"
            "          caches.keys().then(function (ks) { ks.forEach(function (k) { caches.delete(k); }); });\n"
            "      }\n"
            "      if (navigator.serviceWorker) {\n"
            "          navigator.serviceWorker.getRegistrations().then(function (rs) {\n"
            "              rs.forEach(function (r) { r.unregister(); });\n"
            "          });\n"
            "      }\n"
        )
        new_s, n = sw_re.subn(cleanup, s, count=1)
        if n == 0:
            new_s = s.replace(parts_js.lstrip("\n"), parts_js.lstrip("\n") + "\n" + cleanup, 1)
        s = new_s

    # 加载看门狗：90 秒内 canvas 没有进入游戏尺寸，就明确提示并提供刷新入口，
    # 避免「一直 loading、什么也不说」。
    if "wb-timeout-watchdog" not in s:
        watchdog = """  <script id="wb-timeout-watchdog">
  (function () {
    var t0 = Date.now();
    var iv = setInterval(function () {
      var c = document.querySelector('canvas');
      if (c && c.width > 640) { clearInterval(iv); return; }
      if (Date.now() - t0 > 90000 && !document.getElementById('wbTimeout')) {
        clearInterval(iv);
        var d = document.createElement('div');
        d.id = 'wbTimeout';
        d.style.cssText = 'position:fixed;left:50%;top:64%;transform:translateX(-50%);z-index:99;'
          + 'color:#E8E4DC;font:16px/1.7 sans-serif;text-align:center;background:rgba(0,0,0,.8);'
          + 'padding:18px 26px;border-radius:10px;max-width:80%';
        d.innerHTML = '加载超时：网络似乎在传输中途断了。'
          + '<br><a href="javascript:location.reload()" style="color:#C79A4B">点此重新加载</a>（已下载的部分会重新请求，通常第二次会更快）';
        document.body.appendChild(d);
      }
    }, 2000);
  })();
  </script>
</body>"""
        s = s.replace("</body>", watchdog, 1)


    # 埋点桥：把游戏事件送到 /api/collect，并采集页面访问、加载与错误
    if "chaoshiTrack" not in s:
        try:
            build = subprocess.run(["git", "rev-parse", "--short", "HEAD"],
                                   cwd=os.path.dirname(os.path.abspath(__file__)),
                                   capture_output=True, text=True).stdout.strip() or "nogit"
        except Exception:
            build = "nogit"
        bridge = """  <script>
  (function () {
    var BUILD = "%(build)s";
    function rid(p) { return p + Math.random().toString(36).slice(2, 10) + Date.now().toString(36); }
    var vid = localStorage.getItem("chaoshi_vid");
    if (!vid) { vid = rid("v_"); localStorage.setItem("chaoshi_vid", vid); }
    var sKey = "chaoshi_sid_" + Math.floor(Date.now() / 1800000);
    var sid = sessionStorage.getItem(sKey);
    if (!sid) { sid = rid("s_"); sessionStorage.setItem(sKey, sid); }
    var queue = [], seq = 0, started = Date.now(), readySent = false, t0 = performance.now();

    function flush() {
      if (!queue.length) return;
      var body = JSON.stringify({ events: queue.splice(0, 50) });
      var ok = false;
      try {
        if (navigator.sendBeacon) {
          ok = navigator.sendBeacon("/api/collect", new Blob([body], { type: "application/json" }));
        }
      } catch (e) { ok = false; }
      if (!ok) {
        try {
          fetch("/api/collect", { method: "POST", body: body, keepalive: true,
                                  headers: { "Content-Type": "application/json" } });
        } catch (e) {}
      }
    }

    window.chaoshiTrack = function (raw) {
      try {
        var e = JSON.parse(raw);
        e.vid = vid; e.sid = sid; e.seq = ++seq; e.build = BUILD;
        e.site = location.host; e.t_client = e.t || Date.now();
        e.ref = document.referrer ? document.referrer.replace(/[?#].*$/, "") : "";
        queue.push(e);
        if (queue.length >= 8) flush();
      } catch (err) {}
    };
    // 若游戏跑在 worker 里，事件会通过 postMessage 转发过来
    window.addEventListener("message", function (ev) {
      if (ev.data && typeof ev.data.__chaoshi_event === "string") {
        window.chaoshiTrack(ev.data.__chaoshi_event);
      }
    });
    setInterval(flush, 8000);
    window.addEventListener("pagehide", flush);
    document.addEventListener("visibilitychange", function () {
      if (document.visibilityState === "hidden") flush();
    });

    window.chaoshiTrack(JSON.stringify({ event: "page_view" }));

    // 以 canvas 真正进入游戏尺寸作为「可交互」信号
    var iv = setInterval(function () {
      var c = document.querySelector("canvas");
      if (c && c.width > 640 && !readySent) {
        readySent = true;
        clearInterval(iv);
        window.chaoshiTrack(JSON.stringify({
          event: "game_ready", ms: Math.round(performance.now() - t0)
        }));
      }
    }, 500);

    window.addEventListener("error", function (ev) {
      window.chaoshiTrack(JSON.stringify({
        event: "error", reason: String(ev.message || "script").slice(0, 120)
      }));
    });
  })();
  </script>
</body>""" % {"build": build}
        s = s.replace("</body>", bridge, 1)

    open(path, "w", encoding="utf-8").write(s)


def patch_loader(root):
    path = os.path.join(root, "renpy-pre.js")
    s = open(path, encoding="utf-8").read()
    start = s.find(LOADER_MARK_START)
    end = s.find(LOADER_MARK_END)
    if start == -1 or end == -1 or end <= start:
        raise SystemExit("未找到 loadGameZip，构建版本可能变化")
    s = s[:start] + NEW_LOADER + s[end:]
    open(path, "w", encoding="utf-8").write(s)


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
    """把看板页面放进站点根目录（/dash.html）。"""
    src = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dash.html")
    if os.path.exists(src):
        shutil.copy2(src, os.path.join(root, "dash.html"))
        return True
    return False


def write_headers(root):
    # 仅 Cloudflare Pages / Netlify 会读取；GitHub Pages 忽略该文件。
    s = """/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: no-referrer

/renpy.wasm
  Cache-Control: public, max-age=604800
  Content-Type: application/wasm

/renpy.data
  Cache-Control: public, max-age=604800

/game.zip.*
  Cache-Control: public, max-age=604800

/index.html
  Cache-Control: public, max-age=300

/*.js
  Cache-Control: public, max-age=300
"""
    open(os.path.join(root, "_headers"), "w", encoding="utf-8").write(s)


def make_presplash(root):
    """把默认的 Ren'Py 启动图换成作品标题图，并提示加载耗时。"""
    title = os.path.join(os.path.dirname(root), "..", "game", "game", "images", "cg", "title.jpg")
    title = os.path.normpath(title)
    font_path = os.path.normpath(os.path.join(os.path.dirname(root), "..",
                                             "game", "game", "NotoSansSC-Regular.otf"))
    if not (os.path.exists(title) and os.path.exists(font_path)):
        return False
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return False

    W, H = 1920, 1080
    im = Image.open(title).convert("RGB").resize((W, H), Image.LANCZOS)
    im = Image.eval(im, lambda v: int(v * 0.62))
    d = ImageDraw.Draw(im, "RGBA")

    f_title = ImageFont.truetype(font_path, 150)
    f_sub = ImageFont.truetype(font_path, 40)
    f_hint = ImageFont.truetype(font_path, 30)

    def center(text, font, y, fill):
        box = d.textbbox((0, 0), text, font=font)
        d.text(((W - (box[2] - box[0])) / 2, y), text, font=font, fill=fill)

    # 文字区加深，避免压在亮部上不可读
    d.rounded_rectangle([W / 2 - 470, H / 2 - 210, W / 2 + 470, H / 2 + 160],
                        radius=24, fill=(0, 0, 0, 96))

    center("超时", f_title, H / 2 - 170, (232, 228, 220, 235))
    center("正在加载，首次约需 20—40 秒", f_sub, H / 2 + 30, (199, 154, 75, 235))
    center("若长时间停留在此页，请刷新重试", f_hint, H / 2 + 100, (150, 148, 140, 200))

    im.save(os.path.join(root, "web-presplash.jpg"), quality=82, optimize=True)
    return True


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "build/web"
    root = os.path.abspath(root)
    meta = split_zip(root)
    patch_index(root, meta)
    patch_loader(root)
    patch_catalog(root, meta)
    write_headers(root)
    copy_dashboard(root)
    made = make_presplash(root)
    biggest = max(p["size"] for p in meta["parts"])
    total = sum(os.path.getsize(os.path.join(root, f))
                for f in os.listdir(root) if os.path.isfile(os.path.join(root, f)))
    print("分片: %d 片，最大 %.1f MB，总量 %.1f MB" % (
        len(meta["parts"]), biggest / 1e6, meta["total"] / 1e6))
    print("目录体积: %.1f MB" % (total / 1e6))
    print("启动图: %s" % ("已替换" if made else "跳过"))


if __name__ == "__main__":
    main()
