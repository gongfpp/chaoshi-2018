# worker/ —— 旧版埋点（已冻结）

这里的 Cloudflare Worker + D1 实现是 2026-10-22 的旧采集端，**自 2026-10-28 起不再
接收游戏流量**：网页版上报已切到自部署的 `server/chaoshi-analytics`
（腾讯云，`https://gongfpp.icu/chaoshi/api/collect`）。

保留原因：D1 里有 10-22 至 10-28 的历史事件，需要时还能查；接口字段与新服务一致
（新服务多 `sec` / `opt` / `test` 三个字段），所以两边统计口径可比。

- 不要在 `tools/patch_web.py` 里把 `COLLECT_URL` 指回这里。
- 不再部署：`tools/deploy_worker.sh` 只在需要复活它时用。
- 新看板在 `https://gongfpp.icu/chaoshi/`，令牌见 `.secrets/chaoshi-analytics.env`。
