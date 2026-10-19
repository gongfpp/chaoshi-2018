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
| `game/game/ui_extra.rpy` | 界面扩展（章节卡、结局卡、账本） | 是 |
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

# 3. 构建（mac + web）
~/Developer/Tools/renpy-8.5.3/renpy.sh launcher distribute "$PWD/game" \
  --destination "$PWD/build/dist" --package mac --package web
```

`lint` 必须为 0 错误。构建后必须实际打开，不得只凭 lint 判断可玩性。

## 边界

- 不把不同用工模式（专送/众包）的规则混用在同一个人物身上。
- 金额、单量、时长必须与 `docs/story/04-经济账本.md` 对得上；改一处必须同步另一处。
- 真实事件只作为背景，不虚构为本地事件；真实地名与虚构站点名混用时，空间关系必须自洽。
- 生成物（`gen/`、`images/`、`audio/`）不手工修改，改源文件后重新生成。
