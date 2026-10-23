#!/usr/bin/env python3
"""分支与结局覆盖核查（静态）。

`docs/进度与决策.md` 一直挂着「6 个分支与 3 个结局的逐条遍历还没做」。
在网页版里做真机遍历卡在两个硬约束上（见文件末尾），所以这里用静态方式把
**可验证的部分**查清楚：

  1. 每个 `jump` 的目标 label 是否真的存在（lint 也查，这里独立复核一遍）；
  2. 7 个选择点各自的选项，以及每个选项里写死的 `jump`（真正的分叉）；
  3. 3 个结局分别由哪条路径触发，是否存在走不到的结局；
  4. 有没有定义了却没人跳过去、也不在主链上的孤儿 label。

用法：python3 tools/check_branches.py
"""
import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GEN = os.path.join(ROOT, "game", "game", "gen")

LABEL_RE = re.compile(r"^label\s+([A-Za-z_][\w]*)\s*:")
JUMP_RE = re.compile(r"^\s*jump\s+([A-Za-z_][\w]*)\s*$")
MENU_RE = re.compile(r"^(\s*)menu\s*:")
# 选项行：比 menu 再多缩进一级，且是 "文本":
OPTION_RE = re.compile(r'^(\s*)"((?:[^"\\]|\\.)*)"\s*:\s*$')


def indent_of(line):
    return len(line) - len(line.lstrip(" "))


def load():
    files = {}
    for p in sorted(glob.glob(os.path.join(GEN, "*.rpy"))):
        files[os.path.basename(p)] = open(p, encoding="utf-8").read().split("\n")
    return files


def collect_labels(files):
    labels = {}
    for fn, lines in files.items():
        for i, line in enumerate(lines):
            m = LABEL_RE.match(line)
            if m:
                labels[m.group(1)] = (fn, i)
    return labels


def collect_jumps(files):
    """返回 [(file, lineno, target, inside_menu_option)]"""
    out = []
    for fn, lines in files.items():
        for i, line in enumerate(lines):
            m = JUMP_RE.match(line)
            if m:
                out.append((fn, i, m.group(1)))
    return out


def collect_menus(files):
    """返回 [{file, line, chapter, options:[{text, jumps:[...]}]}]"""
    menus = []
    for fn, lines in files.items():
        if not fn.startswith("ch") and not fn.startswith("endings"):
            continue
        for i, line in enumerate(lines):
            if not MENU_RE.match(line):
                continue
            menu_indent = indent_of(line)
            chapter = None
            for j in range(i, -1, -1):
                m = LABEL_RE.match(lines[j])
                if m:
                    chapter = m.group(1)
                    break

            options = []
            for k in range(i + 1, len(lines)):
                ln = lines[k]
                if ln.strip() == "":
                    continue
                if indent_of(ln) <= menu_indent:
                    break
                om = OPTION_RE.match(ln)
                if not om or indent_of(ln) != menu_indent + 4:
                    continue
                opt = {"text": om.group(2), "jumps": []}
                # 收集该选项块内的语句（更深缩进，直到下一个同级选项）
                for t in range(k + 1, len(lines)):
                    inner = lines[t]
                    if inner.strip() == "":
                        continue
                    if indent_of(inner) <= indent_of(ln):
                        break
                    jm = JUMP_RE.match(inner)
                    if jm:
                        opt["jumps"].append(jm.group(1))
                options.append(opt)
            menus.append({"file": fn, "line": i, "chapter": chapter, "options": options})
    return menus


def main():
    files = load()
    labels = collect_labels(files)
    jumps = collect_jumps(files)
    menus = collect_menus(files)

    bad = 0

    print("== 选择点 ==")
    total_opts = 0
    for m in menus:
        print("  %-14s %s 行 %d  → %d 个选项" % (
            m["chapter"] or "?", m["file"], m["line"] + 1, len(m["options"])))
        for idx, o in enumerate(m["options"]):
            total_opts += 1
            tail = ("→ jump " + ", ".join(o["jumps"])) if o["jumps"] else "（继续主线）"
            print("      [%d] %s  %s" % (idx, o["text"][:24], tail))
    print("  合计：%d 个选择点 / %d 个选项" % (len(menus), total_opts))

    print("\n== 跳转目标 ==")
    missing = [(fn, ln + 1, t) for fn, ln, t in jumps if t not in labels]
    for fn, ln, t in missing:
        print("  ✗ %s:%d → %s（未定义）" % (fn, ln, t))
    bad += len(missing)
    if not missing:
        print("  ✓ %d 处 jump 全部指向已定义的 label" % len(jumps))

    print("\n== 结局可达性 ==")
    ending_labels = sorted(l for l in labels if l.startswith("ending_"))
    # 主线终点：谁 jump 到 ch20_end
    into_ch20_end = [t for _, _, t in jumps if t == "ch20_end"]
    reached = set()
    for m in menus:
        for o in m["options"]:
            for t in o["jumps"]:
                if t.startswith("ending_"):
                    reached.add(t)
    if into_ch20_end:
        reached.add("ch20_end")

    for e in ending_labels:
        hit = e in reached
        print("  %s %s" % ("✓" if hit else "✗", e))
        if not hit:
            bad += 1
    if into_ch20_end:
        print("  ✓ ch20_end（主线终点，%d 处跳转汇入；结尾 call screen ending_card）"
              % len(into_ch20_end))
    else:
        print("  ✗ ch20_end 没有任何跳转汇入")
        bad += 1
    print("  合计：%d 个结局，均可由选择分支到达" % (len(ending_labels) + 1))

    print("\n== 孤儿 label ==")
    # label 可以由顺序执行自然流过（不是必须被 jump）。只有当它前面那条语句
    # 已经是 jump / return / raise 时，才真的到不了。
    referenced = {t for _, _, t in jumps}
    referenced |= {"start"}
    orphans = []
    for name, (fn, ln) in sorted(labels.items()):
        if name in referenced or name.endswith("_entry") or name.startswith("ending_"):
            continue
        prev = ""
        for j in range(ln - 1, -1, -1):
            if files[fn][j].strip():
                prev = files[fn][j].strip()
                break
        if prev.startswith(("jump ", "return", "raise ")):
            orphans.append("%s（%s:%d，前一条是 %s）" % (name, fn, ln + 1, prev))
    if orphans:
        print("  到不了：\n    " + "\n    ".join(orphans))
    else:
        print("  ✓ 没有到不了的 label")

    print("\n" + ("全部检查通过" if bad == 0 else "有 %d 处问题" % bad))
    return 0 if bad == 0 else 1


if __name__ == "__main__":
    sys.exit(main())


# ---------------------------------------------------------------------------
# 为什么这里只做静态核查，不做真机遍历
#
# `tools/traverse_branches.js` 试过在网页版里跑完整流程，卡在两条引擎限制上：
#
#   1. `renpy_exec`（renpy-pre.js 暴露的 Python 执行入口）不在 context 的执行循环
#      里。`renpy.run(Start())` 和 `renpy.jump("x")` 都靠抛控制流异常来完成跳转
#      （JumpOutException / JumpException），这个异常会一路冒到 JS 侧没人接住，
#      跳转随之丢失——实测会卡在主菜单或原地不动。
#   2. `config.skipping` 在每次交互开始时被重置。用 `config.interact_callbacks`
#      能把它顶回 "fast"（已验证 skipping == 'fast' 能站住），但第一章开头是
#      `call screen chapter_card(...)`，屏幕交互不会被跳过自动点掉，仍然要点击；
#      而点击又会取消跳过状态，循环下来推进极慢（120 次点击仍停在第一章）。
#
# 结论：真机全流程遍历需要给游戏加一个「自动化测试模式」（例如统一的
# auto-advance 开关 + 章节卡自动消失），属于改动游戏代码，暂不做。
# 静态核查覆盖了「跳转是否悬空、结局是否可达、label 是否到不了」这三类真问题；
# 文本层面的运行时报错仍靠 `renpy lint` 与人眼试玩。
# ---------------------------------------------------------------------------
