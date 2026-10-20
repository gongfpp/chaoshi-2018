# 超时

> 2018—2023，杭州，一个外卖骑手的五年。

**在线试玩：<https://chaoshi-2018.pages.dev/>**（Cloudflare Pages）
备用：<https://gongfpp.github.io/chaoshi-2018/>（GitHub Pages）
**下载发行包：[Releases](https://github.com/gongfpp/chaoshi-2018/releases/latest)**

本项目包含：

1. **一部完整小说**《超时》（20 章，50,031 汉字）及两个替代结局。
2. **一部可通关的视觉小说**，由小说源文件自动生成 Ren'Py 脚本，含 6 个选择点、3 个结局。
3. **研究、设定、账本、改编对应表、验收记录**，可追溯每一个影响剧情因果的判断。

## 快速开始

### 网页版（无需安装）

直接打开 <https://chaoshi-2018.pages.dev/>。首次下载约 18 MB（wasm 6 MB + 引擎数据 5.5 MB + 游戏数据 6.7 MB），实测冷启动 8—12 秒。

离线运行：

```bash
unzip -o chaoshi-1.0.0-web.zip -d web && cd web
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080/
```

> Ren'Py 网页版需要 HTTP 服务，直接双击 `index.html` 无法加载 wasm。

### macOS

从 [Releases](https://github.com/gongfpp/chaoshi-2018/releases/latest) 下载 `chaoshi-1.0.0-mac.zip`，解压得到 `超时.app`，双击打开。
未签名应用首次打开需在「系统设置 → 隐私与安全性」中允许。

### 操作

| 操作 | 按键 |
| --- | --- |
| 推进对白 | 空格 / 回车 / 鼠标左键 |
| 打开菜单 | 右键 / Esc |
| 快进（跳过已读） | Ctrl（按住） |
| 自动播放 | A |
| 历史记录 | 滚轮上 / 菜单「历史」 |
| 账本 | 右上角「账本」 |
| 存档/读档 | 菜单「保存」「读取」 |

## 小说

- 分章源文件：`novel/chapters/ch01.md` … `ch20.md`
- 替代结局：`novel/endings/`
- 合并版：`novel/超时-全文.md`
- 阅读顺序：正文 20 章 → 结局一（准点）/ 结局二（绕路）。两个结局是游戏的替代分支，不属于小说主线。

## 工程结构

```
docs/
  research/     原作研究、现实研究、引擎选型
  story/        总纲、人物与关系、时间线、经济账本、改编对应表、章节大纲
  验收记录.md、资产清单.md、小说-游戏对应表.md、evidence/
novel/          小说源文件（唯一事实来源）
game/           Ren'Py 工程
  branches/     分支段落（Markdown）
  game/gen/     生成的 .rpy（勿手改）
  game/images/  背景 17、立绘 11、CG 5
  game/audio/   41 段环境音乐 + 4 个音效（程序化合成）
tools/          生成与构建脚本
build/dist/     发行包（本地构建产物，不入库）
```

`build/`、`assets-src/fonts/` 均被 `.gitignore` 排除：前者是构建产物，后者是第三方字库的重复副本（运行所需副本已随 `game/game/*.otf` 入库）。

## 生成与构建

```bash
python3 tools/gen_game.py                      # 小说 → Ren'Py 脚本
python3 tools/gen_placeholders.py              # 仅开发期占位图
python3 tools/gen_audio.py                     # 合成音乐与音效
python3 tools/gen_gui.py                       # 生成界面图形
~/Developer/Tools/renpy-8.5.3/renpy.sh game lint
~/Developer/Tools/renpy-8.5.3/renpy.sh launcher distribute "$PWD/game" \
  --destination "$PWD/build/dist" --package mac --package web
```

依赖：Ren'Py 8.5.3、Python 3.13（Pillow、NumPy）、ffmpeg（vorbis 编码）。

## 部署

一条命令完成构建、补丁与发布（GitHub Pages 与 Cloudflare Pages 共用同一份构建）：

```bash
tools/deploy_pages.sh both     # 或 cf / gh
```

它做三件事：

1. `renpy.sh launcher web_build`（`distribute --package web` 不含 wasm 运行时，不能用）
2. `tools/patch_web.py`（见下）
3. 推 `gh-pages`（带 `.nojekyll`）/ `wrangler pages deploy`

### 为什么构建后必须跑 patch_web.py

Ren'Py 的网页加载器**用单个请求拉整个 game.zip**，没有超时也没有重试；原来 33 MB 的包在弱网下断一次，页面就永久停在启动图。`patch_web.py` 做以下几件事：

| 改动 | 原因 |
| --- | --- |
| `game.zip` 切成 2 MB 分片，4 路并行下载 | 单片失败代价小；并行能把延迟叠加上限压到接近最慢的一片 |
| 页面一加载就开始预取游戏数据 | 原来要等 wasm 编译完才发起，等于把两段下载串起来；现在与引擎下载并行 |
| 字库按实际用字裁剪（32 MB → 1.2 MB） | 三份 Noto CJK 全字库占了 `game.zip` 的 94%，而游戏文本是固定的 |
| 分片失败用 HTTP Range 续传，最多重试 6 次；服务端忽略 Range 时回退整片重下 | 断流后能自己接着下，而不是从头再来 |
| 停用 Service Worker 并清理旧 Cache Storage | 坏响应会被 SW 缓存住，之后每次打开都卡同一处 |
| 90 秒未进入游戏则弹出「加载超时 + 重新加载」 | 不再出现无提示的无限等待 |

另外会把启动图替换为作品标题图（`web-presplash.jpg`），并生成 Cloudflare Pages 用的 `_headers` 缓存规则。

字库裁剪由 `tools/subset_fonts.py` 完成（游戏文本固定、无玩家输入，因此按字符集裁剪是无损的）。**新增正文用字后必须重跑一次**，否则新字会显示成方框。

该构建为单线程 wasm，不依赖 `SharedArrayBuffer`，因此无需 COOP/COEP 响应头。

## 素材与许可

- 字库：Noto Serif SC / Noto Sans SC，SIL Open Font License 1.1。
- 图像：由本机图像生成工具产出，逐张记录提示词与日期（见 `docs/资产清单.md`）；已裁切去除生成器水印。
- 音频：`tools/gen_audio.py` 用 NumPy 合成，无第三方采样。
- 引擎：Ren'Py 8.5.3，MIT 类许可（见 SDK `LICENSE.txt`）。

## 已知限制

- 网页版首次下载约 18 MB（wasm 6 MB + 引擎数据 5.5 MB + 游戏数据 6.7 MB）；移动端浏览器未做适配。
- 立绘为半身像羽化叠层，未做逐帧表情动画；同一角色 2—3 种状态。
- 无配音；音频为环境音与低频铺底，非旋律性配乐。
- macOS 包未签名/未公证。
