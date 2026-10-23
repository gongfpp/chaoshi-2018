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

# 自动加载本地凭据（Cloudflare / EdgeOne），.secrets/ 已被 .gitignore 排除
for f in cloudflare.env edgeone.env; do
  if [[ -f "$ROOT/.secrets/$f" ]]; then
    set -a; . "$ROOT/.secrets/$f"; set +a
  fi
done
# wrangler 走系统代理；EdgeOne / GH 各自处理
CF_ENV=(HTTPS_PROXY="$PROXY" HTTP_PROXY="$PROXY" https_proxy="$PROXY" http_proxy="$PROXY")

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
  : "${CLOUDFLARE_API_TOKEN:?需要 CLOUDFLARE_API_TOKEN（写入 .secrets/cloudflare.env）}"
  # 只靠 wrangler 的 OAuth 登录会 10000 Authentication error，必须显式给 API Token
  env "${CF_ENV[@]}" "$WRANGLER" pages deploy build/web --project-name "$PROJECT" \
      --branch main --commit-dirty=true 2>&1 | grep -Ei "success|uploaded|deployment|error|✘|pages\.dev" | tail -6
fi

if [[ "$TARGET" == "eo" ]]; then
  echo "== 3/3c 部署 EdgeOne Pages =="
  : "${EDGEONE_PAGES_API_TOKEN:?需要 EDGEONE_PAGES_API_TOKEN（可写入 .secrets/edgeone.env）}"
  # 不设区域会报 Invalid region: undefined 并退化成「未登录」
  export EDGEONE_PAGES_API_REGION="${EDGEONE_PAGES_API_REGION:-china}"
  EO_JSON="$("$EDGEONE" makers deploy build/web -n "${EO_PROJECT:-chaoshi}" --json 2>&1)"
  echo "$EO_JSON" | tail -5
  if printf '%s' "$EO_JSON" | grep -q "Provider 'Github'"; then
    cat <<'MSG'

   EdgeOne 项目已改为 GitHub 仓库类型，不再接受本地直传。
   这条路要么到控制台把它改回「本地上传」，要么新建一个 Upload 类型项目
   （会换掉预览域名）。仓库里没有构建产物（build/ 被 gitignore），
   所以 Git 类型项目即使自动构建也产不出游戏。
MSG
  fi
  EO_URL="$(printf '%s' "$EO_JSON" | grep -o '"url":"[^"]*"' | tail -1 | cut -d'"' -f4)"
  if [[ -n "$EO_URL" ]]; then
    mkdir -p "$ROOT/build/analytics"
    printf '%s\n' "$EO_URL" > "$ROOT/build/analytics/edgeone-url.txt"
    echo
    echo "预览地址（token 有效期约 3 小时，过期需重新部署）："
    echo "  $EO_URL"
  fi
fi

if [[ "$TARGET" == "gh" || "$TARGET" == "both" ]]; then
  echo "== 3/3b 部署 GitHub Pages =="
  # 用一份常驻克隆做增量提交。以前每次都是 git init 一个全新仓库再 force push，
  # 服务端一个对象都没有，76 MB 全量重传；保留历史后只传改动过的 blob。
  CLONE="$ROOT/build/gh-pages"
  TOKEN="$(gh auth token)"
  GITNET=(-c "http.proxy=$PROXY" -c "https.proxy=$PROXY"
          -c "http.extraheader=AUTHORIZATION: basic $(printf 'x-access-token:%s' "$TOKEN" | base64)")
  REMOTE="https://github.com/gongfpp/chaoshi-2018.git"

  if [[ -d "$CLONE/.git" ]]; then
    git -C "$CLONE" "${GITNET[@]}" fetch -q --depth 1 origin gh-pages
    git -C "$CLONE" reset -q --hard FETCH_HEAD
  else
    git "${GITNET[@]}" clone -q --depth 1 -b gh-pages "$REMOTE" "$CLONE" \
      || { mkdir -p "$CLONE"; git -C "$CLONE" init -q; }
  fi

  rsync -a --delete --exclude '.git' "$ROOT/build/web/" "$CLONE/"
  touch "$CLONE/.nojekyll"

  if git -C "$CLONE" diff --quiet HEAD -- 2>/dev/null && \
     [[ -z "$(git -C "$CLONE" status --porcelain)" ]]; then
    echo "   内容无变化，跳过推送"
  else
    git -C "$CLONE" add -A
    git -C "$CLONE" -c user.name=WorkBuddy -c user.email=workbuddy@local \
        commit -qm "deploy: web build $(cat "$ROOT/build/web/build.json" 2>/dev/null || echo)"
    git -C "$CLONE" "${GITNET[@]}" push -q origin HEAD:gh-pages
    echo "   已推送 gh-pages"
  fi
fi

echo "完成。"
