#!/usr/bin/env python3
"""Cloudflare OAuth（PKCE）授权，替代 `wrangler login`。

原因：`wrangler login` 的本地回调只等 2—3 分钟，人在别处时必然超时；
这里自己起一个长驻回调服务，点授权页的时机不受限制。

    python3 tools/cf_oauth.py

成功后把 access token 写到 build/.cftoken（600 权限），可直接：
    CLOUDFLARE_API_TOKEN=$(cat build/.cftoken) wrangler pages deploy ...
"""

import base64
import hashlib
import json
import os
import secrets
import socket
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

CLIENT_ID = "54d11594-84e4-41aa-b438-e81b8fa78ee7"  # wrangler 的公开 client id
REDIRECT = "http://localhost:8976/oauth/callback"
SCOPES = (
    "k2.read k2.write account:read user:read workers:write workers_kv:write "
    "workers_routes:write workers_scripts:write workers_tail:read d1:write "
    "pages:write zone:read ssl_certs:write ai:write ai-search:write ai-search:run "
    "agent-memory:write queues:write pipelines:write secrets_store:write "
    "artifacts:write flagship:write containers:write cloudchamber:write "
    "connectivity:admin email_routing:write email_sending:write browser:write "
    "challenge-widgets.write offline_access"
)
TOKEN_URL = "https://dash.cloudflare.com/oauth2/token"
OUT = os.path.join("build", ".cftoken")

result = {}


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        qs = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(qs)
        if "code" in params:
            result["code"] = params["code"][0]
            body = "<h2>授权完成</h2><p>可以关闭这个页签，回到对话。</p>"
            code = 200
        else:
            result["error"] = params.get("error_description", params.get("error", ["unknown"]))[0]
            body = "<h2>授权失败</h2><pre>%s</pre>" % result["error"]
            code = 400
        self.send_response(code)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body.encode())

    def log_message(self, *a):
        pass


def serve(host):
    try:
        srv = HTTPServer((host, 8976), Handler)
    except OSError:
        return None
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def main():
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(48)).decode().rstrip("=")
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(16)

    both = [s for s in (serve("127.0.0.1"), serve("::1")) if s]
    if not both:
        sys.exit("8976 端口被占用，先关掉占用进程（可能是上一次的 wrangler login）")

    url = "https://dash.cloudflare.com/oauth2/auth?" + urllib.parse.urlencode({
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT,
        "scope": SCOPES,
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
    })
    print("授权地址：\n%s\n" % url, flush=True)
    try:
        subprocess.run(["open", url], check=False)
    except Exception:
        pass

    print("等待你在浏览器里点 Allow（最长 30 分钟）……", flush=True)
    deadline = time.time() + 1800
    while time.time() < deadline and "code" not in result and "error" not in result:
        time.sleep(0.5)

    if "code" not in result:
        sys.exit("没有拿到授权码：%s" % result.get("error", "超时"))

    data = urllib.parse.urlencode({
        "grant_type": "authorization_code",
        "code": result["code"],
        "redirect_uri": REDIRECT,
        "client_id": CLIENT_ID,
        "code_verifier": verifier,
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    with urllib.request.urlopen(req, timeout=30) as r:
        tok = json.loads(r.read())

    token = tok.get("access_token")
    if not token:
        sys.exit("换 token 失败：%s" % json.dumps(tok)[:300])

    os.makedirs("build", exist_ok=True)
    with open(OUT, "w") as f:
        f.write(token)
    os.chmod(OUT, 0o600)
    scope = tok.get("scope", "")
    print("\n成功。token 已写入 %s" % OUT)
    print("pages:write 在授权范围内：%s" % ("pages:write" in scope))


if __name__ == "__main__":
    main()
