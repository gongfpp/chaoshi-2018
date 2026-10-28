# chaoshi-analytics —— 《超时》自部署埋点

一个进程、只用 Python 标准库 + SQLite。收游戏事件、算进度/时长/分支，并给标题页
提供「同时在线 / 累计访客」两个数字。

## 这台机器上的位置

| 项 | 值 |
| --- | --- |
| 代码 | `/opt/chaoshi-analytics/versions/<ver>-<sha>`，`current` 软链指向它 |
| 安装清单 | `/opt/chaoshi-analytics/INSTALL.json` |
| 服务 | `chaoshi-analytics.service`（用户 `chaoshi-analytics`，127.0.0.1:3155） |
| 配置 | `/etc/chaoshi-analytics/runtime.env`（640，root:chaoshi-analytics） |
| 数据 | `/var/lib/chaoshi-analytics/events.db`（WAL） |
| 对外 | `https://gongfpp.icu/chaoshi/`（Caddy `handle_path /chaoshi/*`） |

**与同机其他项目零共享**：不碰 `/opt/umami`、`/opt/journey-collector`、
postgres `umami` 库、`stats.gongfpp.icu`，也不占 3101/3300。

## 接口

| 方法 | 路径 | 说明 |
| --- | --- | --- |
| POST | `/api/collect` | `{events:[...]}`，最多 200 条/次 |
| GET | `/api/live` | `{online, total, today}`，进程内缓存 20 s |
| GET | `/api/stats?token=&days=&test=` | 看板数据 |
| GET | `/` | 看板页面 |
| POST | `/api/purge?token=&days=` | 删掉 N 天前的事件 |
| GET | `/healthz` | 探活 |

`test=1` 时把测试流量算进统计（客户端用 `?cs_test=1` 打开游戏即可打标）。

## 口径

- **同时在线**：5 分钟内出现过任何事件的 `vid` 去重。不是真实人数，不做设备指纹。
- **累计访客**：历史上出现过 `page_view` 的 `vid` 去重。
- **单局时长**：`play_beat` 心跳里的累计秒数取 `MAX()`。心跳每 60 秒一次，
  丢一两拍不影响结果，也不会重复累加。
- **进度**：`chapter_enter` 按 `run_id` 去重计数；跳章进入会新开一局，漏斗里含跳读。
- **去重**：`(sid, seq)` 唯一索引。`sendBeacon` 在 `pagehide` 会重投同一批。

## 运维

```bash
systemctl status chaoshi-analytics
journalctl -u chaoshi-analytics -n 50 --no-pager
sqlite3 /var/lib/chaoshi-analytics/events.db 'select count(*) from events'
```

保留 400 天，服务自己每 6 小时清一次。表结构改动走 `schema.sql`（`IF NOT EXISTS`），
部署即生效，不需要手工迁移。

本地起一份调试（不污染线上）：

```bash
CHAOSHI_DB=/tmp/csa/e.db CHAOSHI_TOKEN=dev CHAOSHI_PORT=3156 python3 app.py --init
CHAOSHI_DB=/tmp/csa/e.db CHAOSHI_TOKEN=dev CHAOSHI_PORT=3156 python3 app.py
```

部署：`tools/deploy_analytics.sh`；回滚：`tools/deploy_analytics.sh rollback <ver-sha>`。
