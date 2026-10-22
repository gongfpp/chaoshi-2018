#!/usr/bin/env python3
"""把 tools/dash.html 内联成 worker/dash_html.js，让 Worker 自己托管看板。

    python3 tools/gen_worker_dash.py

看板与 /api/stats 同源，免 CORS、免额外部署。
"""

import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "tools", "dash.html")
OUT = os.path.join(ROOT, "worker", "dash_html.js")


def main():
    html = open(SRC, encoding="utf-8").read()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("// 由 tools/gen_worker_dash.py 从 tools/dash.html 生成，勿手改\n")
        f.write("export const DASH_HTML = ")
        f.write(json.dumps(html, ensure_ascii=False))
        f.write(";\n")
    print("写出 %s（%d 字节 HTML）" % (os.path.relpath(OUT, ROOT), len(html)))


if __name__ == "__main__":
    main()
