#!/usr/bin/env bash
# 把 server/chaoshi-analytics 部署到腾讯云，并挂到 https://gongfpp.icu/chaoshi/
#
# 目录规范沿用这台机器上已有项目（/opt/umami、/opt/journey-collector）的做法：
#   /opt/chaoshi-analytics/versions/<ver>-<sha>/   每次部署一个新的不可变目录
#   /opt/chaoshi-analytics/current -> 上面那个     回滚就是换软链
#   /opt/chaoshi-analytics/INSTALL.json            安装清单
#
# 刻意不碰的东西：/opt/umami、/opt/journey-collector、postgres、stats.gongfpp.icu、
# 3101/3300 端口。本服务独占 127.0.0.1:3155 与 /var/lib/chaoshi-analytics。
#
# 用法：
#   tools/deploy_analytics.sh            # 全量部署
#   tools/deploy_analytics.sh token      # 只打印看板令牌
#   tools/deploy_analytics.sh rollback <ver-sha>
set -euo pipefail

ROOT=$(cd "$(dirname "$0")/.." && pwd)
SRC="$ROOT/server/chaoshi-analytics"
HOST=${CHAOSHI_HOST:-root@212.64.11.71}
APP=/opt/chaoshi-analytics
UNIT=/etc/systemd/system/chaoshi-analytics.service
ENVF=/etc/chaoshi-analytics/runtime.env
PORT=${CHAOSHI_PORT:-3155}
SECRETS="$ROOT/.secrets/chaoshi-analytics.env"

SSH=(ssh -o BatchMode=yes -o ConnectTimeout=15 "$HOST")

read_token() {
  "${SSH[@]}" "grep -oP '(?<=^CHAOSHI_TOKEN=).*' $ENVF 2>/dev/null || true"
}

case "${1:-deploy}" in
  token)
    read_token
    exit 0
    ;;
  rollback)
    REL=${2:?"用法: $0 rollback <版本-sha>"}
    "${SSH[@]}" "test -d $APP/versions/$REL || { echo '没有这个版本: $REL'; exit 1; }
                 ln -sfn $APP/versions/$REL $APP/current
                 systemctl restart chaoshi-analytics"
    echo "已回滚到 $REL"
    exit 0
    ;;
esac

VER=$(cat "$SRC/VERSION" 2>/dev/null || echo "1.0.0")
SHA=$(git -C "$ROOT" rev-parse --short HEAD 2>/dev/null || echo nogit)
DIRTY=""
git -C "$ROOT" diff --quiet -- "$SRC" 2>/dev/null || DIRTY="-dirty"
REL="$VER-$SHA$DIRTY"
DEST="$APP/versions/$REL"

echo "==> 部署 $REL 到 $HOST"

# 1) 系统用户（已存在就跳过；--system 无登录 shell）
"${SSH[@]}" "id -u chaoshi-analytics >/dev/null 2>&1 || \
             useradd --system --no-create-home --home-dir /var/lib/chaoshi-analytics \
                     --shell /usr/sbin/nologin chaoshi-analytics"

# 2) 版本目录 + 代码
"${SSH[@]}" "mkdir -p '$DEST'"
rsync -az --delete -e "ssh -o BatchMode=yes" \
      "$SRC/app.py" "$SRC/schema.sql" "$SRC/dash.html" "$SRC/README.md" \
      "$HOST:$DEST/" 2>/dev/null || \
  rsync -az -e "ssh -o BatchMode=yes" \
      "$SRC/app.py" "$SRC/schema.sql" "$SRC/dash.html" "$HOST:$DEST/"

# 3) 配置文件与令牌（只在首次生成，重部署不换令牌）
"${SSH[@]}" "set -e
  mkdir -p /etc/chaoshi-analytics
  chmod 750 /etc/chaoshi-analytics
  if [ ! -f $ENVF ]; then
    TOKEN=\$(openssl rand -hex 24)
    cat > $ENVF <<EOF
CHAOSHI_DB=/var/lib/chaoshi-analytics/events.db
CHAOSHI_BIND=127.0.0.1
CHAOSHI_PORT=$PORT
CHAOSHI_TOKEN=\$TOKEN
EOF
    chmod 640 $ENVF
    chown root:chaoshi-analytics $ENVF
  fi"

# 4) 系统服务
scp -q -o BatchMode=yes "$SRC/chaoshi-analytics.service" "$HOST:$UNIT"
"${SSH[@]}" "set -e
  mkdir -p /var/lib/chaoshi-analytics
  chown chaoshi-analytics:chaoshi-analytics /var/lib/chaoshi-analytics
  chmod 750 /var/lib/chaoshi-analytics
  ln -sfn '$DEST' $APP/current
  systemctl daemon-reload
  systemctl enable chaoshi-analytics >/dev/null 2>&1
  systemctl restart chaoshi-analytics"

# 5) Caddy 路由（幂等；只往 gongfpp.icu 站点块里插自己的 handle_path）
"${SSH[@]}" 'bash -s' <<'REMOTE'
set -e
CF=/etc/caddy/Caddyfile
if grep -q "CHAOSHI_ANALYTICS" "$CF"; then
  echo "    caddy: 路由已存在，跳过"
else
  cp -a "$CF" "$CF.bak.$(date +%Y%m%d-%H%M%S)"
  python3 - "$CF" <<'PY'
import sys
p = sys.argv[1]
s = open(p, encoding="utf-8").read()
anchor = "\troot * /var/www/gongfpp.icu\n"
block = (
    "\t# ── 《超时》埋点（自部署，127.0.0.1:3155）──────────────────────────\n"
    "\t# 代码与安装清单见 /opt/chaoshi-analytics；与 Umami 完全独立，不共用库。\n"
    "\t# >>> CHAOSHI_ANALYTICS\n"
    "\thandle_path /chaoshi/* {\n"
    "\t\treverse_proxy 127.0.0.1:3155\n"
    "\t}\n"
    "\t# <<< CHAOSHI_ANALYTICS\n\n"
)
if anchor not in s:
    sys.exit("找不到插入锚点 root * /var/www/gongfpp.icu")
s = s.replace(anchor, block + anchor, 1)
open(p, "w", encoding="utf-8").write(s)
print("    caddy: 已插入 /chaoshi/* 路由")
PY
fi
caddy validate --config "$CF" --adapter caddyfile >/dev/null 2>&1 || {
  echo "!! caddy validate 失败，已回滚最近的备份"; ls -t "$CF".bak.* | head -1 | xargs -r cp -a --target-directory=/etc/caddy/ ; exit 1; }
systemctl reload caddy
REMOTE

# 6) 安装清单
"${SSH[@]}" "cat > $APP/INSTALL.json <<EOF
{
  \"name\": \"chaoshi-analytics\",
  \"version\": \"$REL\",
  \"python\": \"\$(python3 -V 2>&1 | awk '{print \$2}')\",
  \"entry\": \"$UNIT\",
  \"config\": \"$ENVF\",
  \"database\": \"/var/lib/chaoshi-analytics/events.db (SQLite, WAL)\",
  \"listener\": \"127.0.0.1:$PORT\",
  \"public_url\": \"https://gongfpp.icu/chaoshi/\",
  \"service_user\": \"chaoshi-analytics\",
  \"version_path\": \"$DEST\",
  \"co_tenants\": \"umami(/opt/umami), journey-collector(/opt/journey-collector) — 不共用库与端口\"
}
EOF"

# 7) 健康检查
sleep 1
if "${SSH[@]}" "curl -fsS --max-time 5 http://127.0.0.1:$PORT/healthz" >/dev/null; then
  echo "==> 服务健康 (127.0.0.1:$PORT)"
else
  echo "!! 服务没起来，看日志："; "${SSH[@]}" "journalctl -u chaoshi-analytics -n 30 --no-pager"; exit 1
fi

# 8) 令牌同步到本地（600，git 忽略）
TOKEN=$(read_token)
mkdir -p "$ROOT/.secrets"
umask 077
printf 'CHAOSHI_ANALYTICS_TOKEN=%s\nCHAOSHI_COLLECT=https://gongfpp.icu/chaoshi/api/collect\nCHAOSHI_LIVE=https://gongfpp.icu/chaoshi/api/live\nCHAOSHI_DASH=https://gongfpp.icu/chaoshi/?token=%s\n' \
  "$TOKEN" "$TOKEN" > "$SECRETS"
chmod 600 "$SECRETS"

echo "==> 完成：$REL"
echo "    看板 https://gongfpp.icu/chaoshi/"
echo "    令牌已存 .secrets/chaoshi-analytics.env（600, git 忽略）"
