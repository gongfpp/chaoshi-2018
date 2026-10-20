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
import re
import shutil
import sys

PART_SIZE = 8_000_000  # 8 MB/片，远低于 Cloudflare Pages 的 25 MiB 上限

LOADER_MARK_START = "    async function loadGameZip() {"
LOADER_MARK_END = "    function runLoadGameZip() {"

NEW_LOADER = r'''    // ---- 分片下载（由 tools/patch_web.py 注入）--------------------------------
    // 单个 33 MB 的 game.zip 在弱网下极易中途断流，且无法续传；
    // 这里改为按 game.zip.parts.json 逐片下载，单片失败可带 Range 续传重试。
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
                if (!r.ok && r.status !== 206) {
                    throw new Error('HTTP ' + r.status + ' ' + r.statusText);
                }
                clearTimeout(timer);
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

    async function loadGameZip() {
        try {
            var parts = window.gameZipParts;
            var sizes = window.gameZipPartSizes || [];
            var f = FS.open('/game.zip', 'w');
            var pos = 0;

            gameZipSize = window.gameZipTotal || 0;

            for (var p = 0; p < parts.length; p++) {
                var url = parts[p];
                var need = sizes[p] || 0;
                var partStart = pos;
                var got = 0;
                var attempt = 0;

                while (need === 0 || got < need) {
                    var r = await fetchPart(url, got, 6);
                    if (got > 0 && r.status !== 206) {
                        // 服务端忽略了 Range（返回 200 全量），必须从分片起点重写
                        pos = partStart;
                        got = 0;
                        gameZipDownloaded = pos;
                    }
                    var reader = r.body.getReader();
                    var finished = false;
                    try {
                        while (true) {
                            var chunk = await reader.read();
                            if (chunk.done) { finished = true; break; }
                            FS.write(f, chunk.value, 0, chunk.value.length, pos);
                            pos += chunk.value.length;
                            got += chunk.value.length;
                            gameZipDownloaded = pos;
                            updateDownloadProgress();
                        }
                    } catch (e) {
                        // 分片中途断流：下一轮用 Range 从 got 处续传
                        attempt += 1;
                        if (attempt >= 6) { throw e; }
                        await new Promise(function (res) { setTimeout(res, 800 * attempt); });
                        continue;
                    }
                    // 流正常结束但长度不足（连接被截断）也要继续续传，不能当作完成
                    if (finished && (need === 0 || got >= need)) { break; }
                    attempt += 1;
                    if (attempt >= 8) {
                        throw new Error('分片下载不完整：' + url + '（' + got + '/' + need + '）');
                    }
                    await new Promise(function (res) { setTimeout(res, 800 * attempt); });
                }
            }

            FS.close(f);

        } catch (e) {
            reportError('Could not download game data', e);
        }
    }

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
