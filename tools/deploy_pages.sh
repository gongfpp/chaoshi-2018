#!/usr/bin/env bash
# 重新生成网页版并部署：Cloudflare Pages / EdgeOne Pages / GitHub Pages。
# 用法：tools/deploy_pages.sh [cf|eo|gh|both]
#   cf   Cloudflare Pages（需 CLOUDFLARE_API_TOKEN 或已 wrangler 登录）
#   eo   EdgeOne Pages（需 EDGEONE_PAGES_API_TOKEN）
#   gh   GitHub Pages（推 gh-pages 分支）
#   both = cf + gh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
RENPY="${RENPY:-$HOME/Developer/Tools/renpy-8.5.3/renpy.sh}"
WRANGLER="${WRANGLER:-$HOME/.workbuddy/binaries/node/workspace/node_modules/.bin/wrangler}"
PROJECT="${CF_PAGES_PROJECT:-chaoshi-2018}"
EDGEONE="${EDGEONE:-$HOME/.workbuddy/binaries/node/workspace/node_modules/.bin/edgeone}"
PY="${PY:-$HOME/.workbuddy/binaries/python/envs/default/bin/python}"
TARGET="${1:-both}"

cd "$ROOT"

echo "== 1/3 生成 web 构建 =="
"$RENPY" launcher web_build "$ROOT/game" --destination "$ROOT/build/web" >/tmp/web_build.log 2>&1
echo "   build/web 生成完成"

echo "== 2/3 打补丁（分片 / 续传 / 停用 SW / 启动图） =="
"$PY" tools/patch_web.py build/web

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
  ( cd "$TMP" && git init -q && git add -A \
      && git -c user.name=WorkBuddy -c user.email=workbuddy@local commit -qm "deploy: web build" \
      && git push --force https://github.com/gongfpp/chaoshi-2018.git HEAD:gh-pages )
  rm -rf "$TMP"
fi

echo "完成。"
