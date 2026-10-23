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
```

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

## 边界

- 不把不同用工模式（专送/众包）的规则混用在同一个人物身上。
- 金额、单量、时长必须与 `docs/story/04-经济账本.md` 对得上；改一处必须同步另一处。
- 真实事件只作为背景，不虚构为本地事件；真实地名与虚构站点名混用时，空间关系必须自洽。
- 生成物（`gen/`、`images/`、`audio/`）不手工修改，改源文件后重新生成。
