# 超时

> 2018—2023，杭州，一个外卖骑手的五年。

本项目包含：

1. **一部完整小说**《超时》（20 章，50,031 汉字）及两个替代结局。
2. **一部可通关的视觉小说**，由小说源文件自动生成 Ren'Py 脚本，含 6 个选择点、3 个结局。
3. **研究、设定、账本、改编对应表、验收记录**，可追溯每一个影响剧情因果的判断。

## 快速开始

### 网页版（无需安装）

```bash
cd build/dist && unzip -o chaoshi-1.0.0-web.zip -d ../web && cd ../web
python3 -m http.server 8080
# 浏览器打开 http://localhost:8080/
```

> Ren'Py 网页版需要 HTTP 服务，直接双击 `index.html` 无法加载 wasm。首次加载约 20—40 秒（≈57 MB）。

### macOS

解压 `build/dist/chaoshi-1.0.0-mac.zip`，得到 `超时.app`，双击打开。
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
build/dist/     发行包
```

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

## 素材与许可

- 字库：Noto Serif SC / Noto Sans SC，SIL Open Font License 1.1。
- 图像：由本机图像生成工具产出，逐张记录提示词与日期（见 `docs/资产清单.md`）；已裁切去除生成器水印。
- 音频：`tools/gen_audio.py` 用 NumPy 合成，无第三方采样。
- 引擎：Ren'Py 8.5.3，MIT 类许可（见 SDK `LICENSE.txt`）。

## 已知限制

- 网页版体积较大（57 MB），首次加载慢；移动端浏览器未做适配。
- 立绘为半身像羽化叠层，未做逐帧表情动画；同一角色 2—3 种状态。
- 无配音；音频为环境音与低频铺底，非旋律性配乐。
- macOS 包未签名/未公证。
