#!/usr/bin/env bash
# 重新生成网页版并部署：Cloudflare Pages / EdgeOne Pages / GitHub Pages。
# 用法：tools/deploy_pages.sh [cf|eo|gh|both]
#   cf   Cloudflare Pages（需 CLOUDFLARE_API_TOKEN 或已 wrangler 登录）
#   eo   EdgeOne Pages（需 EDGEONE_PAGES_API_TOKEN）
#   gh   GitHub Pages（推 gh-pages 分支）
#   both = cf + gh
#
# 环境变量：
#   SKIP_BUILD=1   复用现有 build/web（已经构建并打过补丁时用）
#   PROXY=...      gh-pages 推送用的代理，默认 http://127.0.0.1:7897
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RENPY="${RENPY:-$HOME/Developer/Tools/renpy-8.5.3/renpy.sh}"
WRANGLER="${WRANGLER:-$HOME/.workbuddy/binaries/node/workspace/node_modules/.bin/wrangler}"
PROJECT="${CF_PAGES_PROJECT:-chaoshi-2018}"
EDGEONE="${EDGEONE:-$HOME/.workbuddy/binaries/node/workspace/node_modules/.bin/edgeone}"
PY="${PY:-$HOME/.workbuddy/binaries/python/envs/default/bin/python}"
PROXY="${PROXY:-http://127.0.0.1:7897}"
TARGET="${1:-both}"

cd "$ROOT"

if [[ "${SKIP_BUILD:-0}" == "1" ]]; then
  echo "== 1-2/3 跳过构建与打补丁（SKIP_BUILD=1） =="
else
  echo "== 1/3 生成 web 构建 =="
  "$RENPY" launcher web_build "$ROOT/game" --destination "$ROOT/build/web" >/tmp/web_build.log 2>&1
  echo "   build/web 生成完成"

  echo "== 2/3 打补丁（分片 / 续传 / 停用 SW / 启动图） =="
  "$PY" tools/patch_web.py build/web
fi

if [[ "$TARGET" == "cf" || "$TARGET" == "both" ]]; then
  echo "== 3/3a 部署 Cloudflare Pages =="
  "$WRANGLER" pages deploy build/web --project-name "$PROJECT" --branch main --commit-dirty=true
fi

if [[ "$TARGET" == "eo" ]]; then
  echo "== 3/3c 部署 EdgeOne Pages =="
  : "${EDGEONE_PAGES_API_TOKEN:?需要先设置 EDGEONE_PAGES_API_TOKEN}"
  "$EDGEONE" makers deploy build/web -n "${EO_PROJECT:-chaoshi}" --json
fi

if [[ "$TARGET" == "gh" || "$TARGET" == "both" ]]; then
  echo "== 3/3b 部署 GitHub Pages =="
  TMP=$(mktemp -d)
  cp -R build/web/. "$TMP/"
  touch "$TMP/.nojekyll"
  # 本机沙盒对小写 http_proxy 指向的代理不通，必须显式指定；凭据用 gh token
  TOKEN="$(gh auth token)"
  ( cd "$TMP" && git init -q && git add -A \
      && git -c user.name=WorkBuddy -c user.email=workbuddy@local commit -qm "deploy: web build" \
      && git -c http.proxy="$PROXY" -c https.proxy="$PROXY" \
             -c "http.extraheader=AUTHORIZATION: basic $(printf 'x-access-token:%s' "$TOKEN" | base64)" \
             push --force https://github.com/gongfpp/chaoshi-2018.git HEAD:gh-pages )
  rm -rf "$TMP"
fi

echo "完成。"
