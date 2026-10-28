# 超时 · 项目规则（AGENTS.md）

本文件是该项目的有效约定。全局规则仍然适用；本文件在项目范围内补充具体做法。

## 一句话

小说《超时》是唯一事实来源；游戏从小说源文件自动生成，不得手改生成物。

## 目录职责

| 路径 | 职责 | 可否手改 |
| --- | --- | --- |
| `novel/chapters/*.md` | 小说正文，含 HTML 注释形式的演出指令 | 是（正文与指令的唯一来源） |
| `novel/endings/*.md` | 两个替代结局 | 是 |
| `novel/超时-全文.md` | 合并版，供连续阅读 | 否（脚本生成） |
| `game/branches/*.md` | 分支场景（选择后的替代段落） | 是 |
| `game/game/gen/*.rpy` | Ren'Py 脚本 | **否**（`tools/gen_game.py` 生成） |
| `game/game/ui_extra.rpy` | 界面扩展（章节卡、结局卡、章节目录） | 是 |
| `game/game/gui.rpy`、`screens.rpy`、`options.rpy` | Ren'Py 界面与工程配置 | 是 |
| `game/game/images/` | 背景、立绘、CG | 由 `tools/finish_art.py` 产出 |
| `game/game/audio/` | 程序化合成的音乐与音效 | 由 `tools/gen_audio.py` 产出 |
| `server/chaoshi-analytics/` | 自部署埋点服务与看板（腾讯云） | 是 |
| `worker/` | 旧的 Cloudflare Worker 版埋点 | 冻结（已被 `server/` 取代） |
| `tools/` | 生成器与构建工具 | 是 |
| `docs/` | 研究、设定、验收记录 | 是 |
| `build/` | 构建产物、中间文件 | 否（可重建） |
| `assets-src/fonts/` | 原始字库（OFL） | 只读 |

## 小说源文件格式

```markdown
<!-- stat: qian=8449 debt=14000 -->   ← 章节起始的账本数值
<!-- title: 喜酒 -->                  ← 章节标题（用于标题卡）
<!-- scene: bg_wedding -->            ← 切换背景
<!-- bgm: wedding -->                 ← 切换音乐
<!-- sfx: phone_notify -->            ← 播放音效
<!-- choice: ch09 -->                 ← 插入选项（选项表在 tools/gen_game.py）
<!-- anchor: ch09_join -->            ← 分支汇合点
<!-- s:ll -->「对白」                  ← 指定说话人；无标记的行按旁白处理
```

新增角色时，必须在 `tools/gen_game.py` 的 `SPEAKERS` 中登记 `id → (中文名, 颜色)`。
新增背景时，必须提供 `game/game/images/bg/<id>.jpg`，否则 lint 会报 “is not an image”。

## 验证方法

```bash
# 1. 生成脚本
python3 tools/gen_game.py

# 2. 静态检查（语法、图片、音频、跳转）
~/Developer/Tools/renpy-8.5.3/renpy.sh game lint

# 3. 构建（mac）
~/Developer/Tools/renpy-8.5.3/renpy.sh launcher distribute "$PWD/game" \
  --destination "$PWD/build/dist" --package mac

# 4. 网页版：先裁字库，再 web_build，最后**必须**跑 patch_web.py
python3 tools/subset_fonts.py
~/Developer/Tools/renpy-8.5.3/renpy.sh launcher web_build "$PWD/game" --destination "$PWD/build/web"
python3 tools/patch_web.py build/web

# 5. 发布（GitHub Pages + Cloudflare Pages）
tools/deploy_pages.sh both

# 6. 埋点端点（只在 worker/ 有改动、或首次建库时才需要）
export CLOUDFLARE_API_TOKEN=... CLOUDFLARE_ACCOUNT_ID=...
bash tools/deploy_worker.sh

# 7. 埋点服务（只在 server/chaoshi-analytics 有改动时才需要）
tools/deploy_analytics.sh          # 部署到腾讯云并挂 https://gongfpp.icu/chaoshi/
tools/deploy_analytics.sh token    # 打印看板令牌
```

## 埋点

线上事件发到自部署的 **chaoshi-analytics**（腾讯云 `212.64.11.71`，Caddy 挂在
`https://gongfpp.icu/chaoshi/api/collect`）。看板 `https://gongfpp.icu/chaoshi/`，
令牌存本机 `.secrets/chaoshi-analytics.env`（600，git 忽略），也可
`tools/deploy_analytics.sh token` 现取。

- **事件口径**：`run_start` / `chapter_enter` / `chapter_complete` / `choice_pick`
  （带 `opt` 短标签）/ `ending_enter` / `ending_complete` / `play_beat`（60 秒心跳）。
- **时长**：网页侧按「页面可见 + 最近 5 分钟有过输入」逐秒累计（`sec` 字段），
  `run_start` / `chapter_jump` 清零；服务端取单局 `MAX(sec)`。不要改成墙钟，
  也别用 `renpy.get_game_runtime()` —— 对白停在屏幕上等点击也会计入。
- **标题页脚注**的数字走 `GET /api/live`，只在主菜单轮询，进游戏即停。
- **验收时用 `?cs_test=1` 打开游戏**，事件打 `test=1`，看板默认排除；
  看板右上「含测试」可临时并入。
- 同机还跑着 Umami（`stats.gongfpp.icu`）与 journey-collector（3101），
  **不要动它们**：本服务独占 `127.0.0.1:3155` 与 `/var/lib/chaoshi-analytics`。

`lint` 必须为 0 错误。构建后必须实际打开，不得只凭 lint 判断可玩性。

## 交付与验收

- **每批改动都同步部署到三端**（GitHub Pages / EdgeOne / Cloudflare Pages），一条
  `tools/deploy_pages.sh both` 全覆盖。交付时给出线上地址；验收在线上做，
  不接受"本地 `build/web` 验完就算完成"。
- 三端不是同时生效：Cloudflare 每次 deploy 立即清自己的 CDN；EdgeOne 跟随
  `gh-pages` 约 60 秒；GitHub Pages 还要等一次 Pages 构建 + HTML 缓存（约 10 分钟）。
  另外 `?b=` 指纹只覆盖 `game.zip` 分片，`index.html` / `renpy-pre.js` /
  `chaoshi-loader.js` **没有指纹** —— 别用旧标签页验收，也别在推完 30 秒就断言"没变化"。
- 版本核对认 `build.json` 的 `"build"` 字段（产出该构建的提交号）：三端各拉一次
  `/build.json?nv=$(date +%s)`，三个都一样、且等于**最后一次改代码的提交**才算真上线。
  纯文档提交不触发重新构建，所以它允许比 `HEAD` 落后一两个。
- Mac 上的 `gh` 凭据会过期，报 `no oauth token found for github.com` 或
  `The token in default is invalid` 时，从 Windows 侧灌一次：
  `gh auth token | ssh mac "umask 077; cat > /tmp/.cs_ghtoken"`，再
  `ssh mac "gh auth login -h github.com --with-token < /tmp/.cs_ghtoken && rm -f /tmp/.cs_ghtoken"`。

## 健壮性与对抗测试

- **铁律：任何情况下都不许把玩家推到白屏或 Ren'Py `_exception` 全屏错误页。**
  资源失败弱化（占位图+toast）、异常吞掉（toast）、启动失败给可恢复面板。
- 三条防线在 `game/game/robust.rpy`（`init -45 python`）：
  1. `webloader.process_downloaded_resources` 的替换版——「XHR 结束但文件没落地」
     不再 raise，退避重试 4 次后放弃并只 toast 一次；原版那句
     `# trigger Ren'Py's error handler` 就是网页版错误页的总源头，别改回去。
  2. `DynamicImage.find_target` 包一层，失败置 `Null()` 继续渲染。
  3. `config.exception_handler` 收口所有未预期异常（官方钩子，返回 True 即不再弹错误页）。
- 启动期兜底在 `tools/web/chaoshi-loader.js`：`fatal()` 在已进游戏后只 toast 不盖画面；
  下载类失败自动重载一次（`?csretry=` 计数）；错误面板贴底可关闭。
  静态兜底层（`#csFallback`）由 `tools/patch_web.py` 注入 index.html：loader JS
  本身被拦时 4 秒后亮出，不再纯白。`window.__csLoaderOk` 是两边之间的信号。
- 跑对抗测试（本地 `http.server 8080` 起着）：
  `NODE_PATH=$HOME/.workbuddy/binaries/node/workspace/node_modules node tools/test_adversarial.js [T0,T4a,...]`
  13 项：标题菜单遍历 / 200 次随机点击 / 菜单狂开关 / 图片全 404 / 图片全 abort /
  启动断 game.zip / 中途断网 / 视口狂切 / ≡ 菜单六项狂点 / 启动中切视口+刷新 /
  loader 被拦 / renpy-pre.js 被拦。判定核心是 `renpy.get_screen("_exception")` 必须为 false。
  截图落在 `build/shots/adv/`。
- 已知行为（不是 bug）：游戏中按 Escape 直接进「存档」页（`_game_menu_screen` 指向
  `save_screen` 标签），返回游戏要点左下角「返回」按钮。

## 边界

- 不把不同用工模式（专送/众包）的规则混用在同一个人物身上。
- 金额、单量、时长必须与 `docs/story/04-经济账本.md` 对得上；改一处必须同步另一处。
- 真实事件只作为背景，不虚构为本地事件；真实地名与虚构站点名混用时，空间关系必须自洽。
- 生成物（`gen/`、`images/`、`audio/`）不手工修改，改源文件后重新生成。
