#!/usr/bin/env bash
# 部署埋点端点（Cloudflare Worker + D1）
#
#   export CLOUDFLARE_API_TOKEN=...      # 需要 Pages:Edit + Workers Scripts:Edit + D1:Edit
#   export CLOUDFLARE_ACCOUNT_ID=...
#   bash tools/deploy_worker.sh
#
# 首次部署：先 `wrangler d1 create chaoshi_events`，把 uuid 填进 worker/wrangler.toml，
# 再 `wrangler d1 execute chaoshi_events --remote --file=worker/schema.sql`。
# 令牌（ANALYTICS_TOKEN）只在首次生成，落在 build/analytics/token.txt（已被 git 忽略）。
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
WRANGLER="${WRANGLER:-$HOME/.workbuddy/binaries/node/workspace/node_modules/.bin/wrangler}"
PY="${PY:-$HOME/.workbuddy/binaries/python/envs/default/bin/python}"
TOKEN_FILE="$ROOT/build/analytics/token.txt"

: "${CLOUDFLARE_API_TOKEN:?需要 CLOUDFLARE_API_TOKEN}"
: "${CLOUDFLARE_ACCOUNT_ID:?需要 CLOUDFLARE_ACCOUNT_ID}"
export HTTPS_PROXY="${HTTPS_PROXY:-http://127.0.0.1:7897}"
export HTTP_PROXY="${HTTP_PROXY:-http://127.0.0.1:7897}"

cd "$ROOT"
echo "== 1/3 生成看板内联 =="
"$PY" tools/gen_worker_dash.py

echo "== 2/3 建表（幂等） =="
( cd worker && "$WRANGLER" d1 execute chaoshi_events --remote --config wrangler.toml --file=schema.sql >/dev/null )

echo "== 3/3 部署 Worker =="
( cd worker && "$WRANGLER" deploy --config wrangler.toml 2>&1 | tail -6 )

if [ -f "$TOKEN_FILE" ]; then
  echo
  echo "看板：https://chaoshi-analytics.gong7968.workers.dev/?token=$(cat "$TOKEN_FILE")"
else
  echo
  echo "未找到 $TOKEN_FILE；若要设置令牌："
  echo "  ( cd worker && $WRANGLER secret put ANALYTICS_TOKEN --config wrangler.toml )"
fi
