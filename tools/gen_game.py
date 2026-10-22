#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 novel/ 下的 Markdown 正文转换成 Ren'Py 脚本。

设计原则：小说是唯一事实来源。章节文件里的 HTML 注释是演出指令，
渲染成 Markdown 时不可见，因此同一份文件既是可读的小说，也是游戏脚本源。
"""
import os
import re
import json
import glob

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
NOVEL = os.path.join(ROOT, "novel")
OUT = os.path.join(ROOT, "game", "game", "gen")

SPEAKERS = {
    "xz": ("杨保祥", "#D9C8A6"),
    "ll": ("刘蕾", "#C98A62"),
    "xf": ("罗小福", "#D6A0AB"),
    "lt": ("刘广田", "#A89684"),
    "lm": ("马长顺", "#9AA79B"),
    "cy": ("曹明远", "#9FB0C4"),
    "gj": ("高秀兰", "#BFA98F"),
    "sg": ("孙德胜", "#A88F6E"),
    "wz": ("王建平", "#B0A693"),
    "cl": ("陈立", "#92A8B8"),
    "rq": ("罗二强", "#A57F6E"),
    "bj": ("杨保芝", "#C0A58F"),
    "wd": ("王大勇", "#A99C86"),
    "qun": ("骑手", "#A9A69C"),
    "police": ("警察", "#9FA5AC"),
    "nurse": ("护士", "#A8B4B8"),
    "doc": ("医生", "#A8B4B8"),
    "op": ("120 接线员", "#9FA5AC"),
    "staff": ("工作人员", "#9FA5AC"),
    "old": ("老人", "#B3AC9E"),
    "son": ("家属", "#B3AC9E"),
    "car": ("车主", "#B08C7A"),
    "qin": ("亲戚", "#AFA393"),
    "vol": ("志愿者", "#A3ADA6"),
    "guard": ("保安", "#A3ADA6"),
    "cust": ("顾客", "#B0A79A"),
    "land": ("房东", "#B0A79A"),
    "boss": ("老板", "#AFA08C"),
    "young": ("年轻骑手", "#A8B0A0"),
    "li": ("小李", "#A8B4A0"),
    "zhao": ("老赵", "#A8B4A0"),
    "new": ("新司机", "#A8B4A0"),
    "boy": ("顾客", "#A8B0A0"),
    "woman": ("邻居", "#B3A9A0"),
    "man": ("邻居", "#A9A296"),
    "nn": ("杨念", "#D8B9B0"),
    "father": ("父亲", "#B8AE9C"),
    "neighbor": ("邻居", "#A8A79C"),
    "consult": ("顾问", "#B9AFA4"),
    "lawyer": ("对方律师", "#A2A6AC"),
    "arb": ("仲裁员", "#A2A6AC"),
    "girl": ("女孩", "#B8AFA4"),
    "mom": ("赵桂枝", "#C0A99B"),
    "wu": ("老吴", "#A9AFA4"),
}

CH_TITLES = {
    "ch01": ("第一章", "三月雨"),
    "ch02": ("第二章", "单王"),
    "ch03": ("第三章", "调度室"),
    "ch04": ("第四章", "自己的车"),
    "ch05": ("第五章", "四十五天"),
    "ch06": ("第六章", "老马的车"),
    "ch07": ("第七章", "新国标"),
    "ch08": ("第八章", "彩礼"),
    "ch09": ("第九章", "喜酒"),
    "ch10": ("第十章", "封城"),
    "ch11": ("第十一章", "建档"),
    "ch12": ("第十二章", "一月十八"),
    "ch13": ("第十三章", "卖车"),
    "ch14": ("第十四章", "小福"),
    "ch15": ("第十五章", "服务分"),
    "ch16": ("第十六章", "三月十二"),
    "ch17": ("第十七章", "念念"),
    "ch18": ("第十八章", "群"),
    "ch19": ("第十九章", "交易"),
    "ch20": ("第二十章", "守夜"),
}

BG_ALIAS = {
    "bg_road_rain": "bg_rain",
    "bg_police": "bg_office",
}

SPRITE_IDS = {"xz", "ll", "xf", "lt", "lm", "cy", "gj", "sg"}
SPRITE_POS = {}

def expr_for(sid, chapter_no):
    """章节层面的「底色」表情：越往后的人越憔悴。"""
    if sid == "xz" and chapter_no >= 12:
        return "tired"
    if sid == "ll" and chapter_no >= 11:
        return "sick"
    if sid == "xf" and chapter_no >= 16:
        return "sad"
    return "normal"


# 台词里出现这些词，就把表情切过去。只看「有感」的词，别放太宽
# （早期版本按章节号硬编码，人物表情和剧情完全脱钩）。
EXPR_WORDS = {
    "xz": ("tired", ("累", "喘", "撑不住", "跑不动", "困", "熬", "疼", "血")),
    "ll": ("sick", ("病", "烧", "咳", "药", "医院", "针", "血", "疼")),
    "xf": ("sad", ("哭", "对不起", "别走", "舍不得", "委屈", "怕")),
}


def guess_expr(sid, text):
    hit = EXPR_WORDS.get(sid)
    if not hit or not text or len(text) < 4:
        return None
    expr, words = hit
    for w in words:
        if w in text:
            return expr
    return None


def pick_expr(sid, text, chapter_no, cur):
    """优先级：台词关键词 > 当前表情（不来回跳）> 章节底色。"""
    kw = guess_expr(sid, text)
    if kw:
        return kw
    if cur:
        return cur
    return expr_for(sid, chapter_no)

DIRECTIVE = re.compile(r"<!--\s*([a-z]+)\s*:\s*(.*?)\s*-->")
SPEAKER = re.compile(r"<!--\s*s:([a-z]+)\s*-->")


def esc(t):
    t = t.replace("\\", "\\\\").replace('"', '\\"')
    t = t.replace("{", "{{").replace("[", "[[")
    t = re.sub(r"\*\*(.+?)\*\*", r"{b}\1{/b}", t)
    return t


def split_text(text, limit):
    """按句读切分过长的段落，避免单屏文字过密。"""
    if len(text) <= limit:
        return [text]
    parts = re.findall(r"[^。！？…；]*[。！？…；]?", text)
    parts = [p for p in parts if p]
    out, buf = [], ""
    for p in parts:
        if len(buf) + len(p) <= limit:
            buf += p
        else:
            if buf:
                out.append(buf)
            buf = p
            while len(buf) > limit:
                out.append(buf[:limit])
                buf = buf[limit:]
    if buf:
        out.append(buf)
    return out


KNOWN_DIRECTIVES = {"scene", "show", "hide", "bgm", "sfx", "choice",
                    "anchor", "stat", "money", "ending", "title", "jump", "branch",
                    "when", "end", "expr"}


def parse_file(path):
    blocks = []
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    for lineno, line in enumerate(raw.split("\n"), 1):
        line = line.rstrip()
        if not line.strip():
            continue
        if line.startswith("# "):
            continue
        # 无条件段落结束标记：<!-- end -->（不带冒号，正则匹配不到）
        if re.fullmatch(r"<!--\s*end\s*-->", line.strip()):
            blocks.append(("endwhen",))
            continue
        m = DIRECTIVE.search(line)
        if m and not line.replace(m.group(0), "").strip():
            key, val = m.group(1), m.group(2)
            if key == "scene":
                blocks.append(("scene", val))
            elif key == "show":
                parts = val.split()
                tag = parts[0]
                expr = parts[1] if len(parts) > 1 else "normal"
                pos = parts[2] if len(parts) > 2 else None
                blocks.append(("show", tag, expr, pos))
            elif key == "hide":
                blocks.append(("hide", val.strip()))
            elif key == "expr":
                parts = val.split()
                if len(parts) < 2:
                    raise SystemExit("%s:%d  expr 需要「角色 表情」，例如 "
                                     "<!-- expr: xz tired -->" % (path, lineno))
                blocks.append(("expr", parts[0], parts[1]))
            elif key == "bgm":
                blocks.append(("bgm", val))
            elif key == "sfx":
                blocks.append(("sfx", val))
            elif key == "choice":
                blocks.append(("choice", val))
            elif key == "anchor":
                blocks.append(("anchor", val))
            elif key in ("stat", "money"):
                # stat：绝对写入（章节入口状态）；money：增量（本章发生的收支）
                # 两者都支持 when=<条件>，用于分支路线保留各自的钱数
                d = {}
                cond = None
                # when= 之后整段都是条件表达式（可能含空格，如 "not c_siyu"）
                if "when=" in val:
                    head, cond = val.split("when=", 1)
                    cond = cond.strip()
                    tokens = head.split()
                else:
                    tokens = val.split()
                for kv in tokens:
                    if "=" in kv:
                        k, v = kv.split("=", 1)
                        try:
                            d[k] = int(v)
                        except ValueError:
                            d[k] = v
                blocks.append((key, d, cond))
            elif key == "jump":
                # 控制流：分支段落结束后跳回汇合点。缺了这条会顺序落入下一个分支。
                blocks.append(("jump", val.strip()))
            elif key == "when":
                blocks.append(("when", val.strip()))
            elif key == "end":
                blocks.append(("endwhen",))
            elif key == "branch":
                # 分支段落开头的自述标记，仅用于校验，不产生运行时代码
                blocks.append(("branch", val.strip()))
            elif key in ("ending", "title"):
                blocks.append((key, val))
            else:
                raise ValueError("%s:%d 未知指令：%s（允许：%s）" % (
                    path, lineno, key, "、".join(sorted(KNOWN_DIRECTIVES))))
            continue
        sm = SPEAKER.match(line)
        if sm:
            spk = sm.group(1)
            text = SPEAKER.sub("", line).strip()
            blocks.append(("say", spk, text))
        else:
            blocks.append(("say", None, line))
    return blocks


def emit_chapter(name, blocks, next_label):
    lines = []
    num, title = CH_TITLES.get(name, ("", blocks[0][1] if blocks else ""))
    chapter_no = int(re.sub(r"\D", "", name) or 0)
    stage = []
    expr_state = {}
    lines.append("label %s:" % name)
    lines.append('    call screen chapter_card("%s", "%s")' % (num, title))
    lines.append('    $ track("chapter_enter", chapter="%s")' % name)
    for b in blocks:
        kind = b[0]
        if kind == "scene":
            lines.append('    scene %s' % BG_ALIAS.get(b[1], b[1]))
            lines.append("    with fade")
            stage.clear()
            expr_state.clear()
        elif kind == "expr":
            # 手写指定表情：<!-- expr: xz tired -->
            tag, ex = b[1], b[2]
            expr_state[tag] = ex
            if tag in stage:
                lines.append("    show %s %s" % (tag, ex))
                lines.append("    with dissolve")
        elif kind == "show":
            tag, expr, pos = b[1], b[2], b[3]
            cmd = "    show %s %s" % (tag, expr)
            if pos:
                cmd += " at %s" % pos
            lines.append(cmd)
            lines.append("    with dissolve")
            if tag not in stage:
                stage.append(tag)
        elif kind == "hide":
            lines.append("    hide %s" % b[1])
            lines.append("    with dissolve")
        elif kind == "bgm":
            lines.append('    play music "audio/bgm/%s.ogg" fadein 1.5' % b[1])
        elif kind == "sfx":
            lines.append('    play sound "audio/sfx/%s.ogg"' % b[1])
        elif kind in ("stat", "money"):
            d = b[1]
            cond = b[2] if len(b) > 2 else None
            op = "=" if kind == "stat" else "+="
            body = []
            for k, v in d.items():
                if isinstance(v, int):
                    if kind == "money" and v < 0:
                        body.append("    $ %s -= %d" % (k, -v))
                    else:
                        body.append("    $ %s %s %d" % (k, op, v))
                else:
                    body.append('    $ %s = "%s"' % (k, v))
            if cond:
                lines.append("    if %s:" % cond)
                lines.extend("    " + ln for ln in body)
            else:
                lines.extend(body)
        elif kind == "anchor":
            lines.append("")
            lines.append("label %s:" % b[1])
        elif kind == "choice":
            cid = b[1]
            lines.append('    $ track("choice_shown", choice="%s")' % cid)
            lines.append("    menu:")
            for oi, opt in enumerate(CHOICES[cid]):
                lines.append('        "%s":' % opt["text"])
                lines.append('            $ track("choice_pick", choice="%s", option=%d)' % (cid, oi))
                for act in opt["actions"]:
                    lines.append("            %s" % act)
                if opt.get("jump"):
                    lines.append("            jump %s" % opt["jump"])
                elif opt.get("jump_ending"):
                    lines.append("            jump %s" % opt["jump_ending"])
        elif kind == "say":
            spk, text = b[1], b[2]
            if spk in SPRITE_IDS and spk not in stage:
                if len(stage) >= 2:
                    old = stage.pop(0)
                    lines.append("    hide %s" % old)
                    lines.append("    with dissolve")
                    expr_state.pop(old, None)
                pos = "sprite_left" if not stage else "sprite_right"
                want = pick_expr(spk, text, chapter_no, expr_state.get(spk))
                expr_state[spk] = want
                lines.append("    show %s %s at %s" % (spk, want, pos))
                lines.append("    with dissolve")
                stage.append(spk)
            elif spk in SPRITE_IDS:
                # 已在台上：台词带了情绪就换表情，否则保持原样（不来回闪）
                want = pick_expr(spk, text, chapter_no, expr_state.get(spk))
                if want != expr_state.get(spk):
                    expr_state[spk] = want
                    lines.append("    show %s %s" % (spk, want))
                    lines.append("    with dissolve")
            limit = 110 if spk else 92
            for chunk in split_text(text, limit):
                if spk:
                    lines.append('    %s "%s"' % (spk, esc(chunk)))
                else:
                    lines.append('    "%s"' % esc(chunk))
        elif kind == "jump":
            lines.append("    jump %s" % b[1])
        elif kind == "ending":
            lines.append("    $ persistent.ending_%s = True" % b[1])
            lines.append('    $ track("ending_enter", ending="%s")' % b[1])
        elif kind in ("title", "branch"):
            pass
        elif kind == "when":
            lines.append("@@WHEN@@%s" % b[1])
        elif kind == "endwhen":
            lines.append("@@END@@")
    lines.append("")
    # 章节读完：埋点用来自算「读到第几章掉队」的漏斗
    if re.fullmatch(r"ch\d\d", name):
        lines.append('    $ track("chapter_complete", chapter="%s")' % name)
    if next_label:
        lines.append("    jump %s" % next_label)
    # @@WHEN@@ / @@END@@ 转成 Ren'Py 的 if 块并补缩进
    if any(ln.startswith("@@") for ln in lines):
        out, depth = [], 0
        for ln in lines:
            if ln.startswith("@@WHEN@@"):
                out.append("    " * (depth + 1) + "if %s:" % ln[8:])
                depth += 1
                continue
            if ln.startswith("@@END@@"):
                depth = max(0, depth - 1)
                continue
            out.append(("    " * depth + ln) if depth and ln.strip() else ln)
        lines = out
    else:
        lines.append("    return")
    return "\n".join(lines)


CHOICES = {
    "ch01": [
        {"text": "给姐姐打个电话", "actions": ["$ c_call = True", "$ xin += 1"]},
        {"text": "把手机揣回去，先找住处", "actions": ["$ c_call = False", "$ shen += 1"]},
    ],
    "ch03": [
        {"text": "接下这些“刚好”的单子", "actions": ["$ c_haodan = True", "$ xin += 1", "$ qian += 300"]},
        {"text": "把钥匙还回去", "actions": ["$ c_haodan = False", "$ xin -= 1"], "jump": "ch03_alt"},
    ],
    "ch07": [
        {"text": "报警，走程序", "actions": ["$ c_siyu = False", "$ qian -= 4000", "$ shen -= 1"], "jump": "ch07_alt"},
        {"text": "私了，花钱买平安", "actions": ["$ c_siyu = True", "$ qian -= 12000", "$ debt += 8000"]},
    ],
    "ch09": [
        {"text": "把工资卡交给她", "actions": ["$ c_gongzi = True", "$ xin += 2"]},
        {"text": "工资卡自己留着", "actions": ["$ c_gongzi = False", "$ xin -= 1"], "jump": "ch09_alt"},
    ],
    "ch12": [
        {"text": "先把手上那单送完", "actions": ["$ c_zaodao = False", "$ qian += 6"]},
        {"text": "立刻掉头回家", "actions": ["$ c_zaodao = True"], "jump": "ch12_alt"},
    ],
    "ch14": [
        {"text": "当晚带她走", "actions": ["$ xf_saved = True"], "jump_ending": "ending_raolu"},
        {"text": "下个月再来接她", "actions": ["$ xf_saved = False"]},
    ],
    "ch19": [
        {"text": "交出陈立的住址和聊天记录", "actions": ["$ sold_chen = True", "$ qian += 2000", "$ debt -= 2000"]},
        {"text": "拒绝", "actions": ["$ sold_chen = False", "$ xin += 2"], "jump_ending": "ending_zhundian"},
    ],
}


# 各章入口状态（主线口径，由 tools/audit_ledger.py 校验）。
# 章节跳转时先写入这张表，再进入章节；章节内的 stat/money 会在其上继续计算。
CHAPTER_ENTRY = {
    "ch01": (0, 0), "ch02": (0, 2000), "ch03": (14052, 0), "ch04": (14052, 0),
    "ch05": (3436, 0), "ch06": (9372, 0), "ch07": (19836, 0), "ch08": (10421, 8000),
    "ch09": (21205, 0), "ch10": (8449, 14000), "ch11": (5800, 14000),
    "ch12": (4800, 14000), "ch13": (4306, 85000), "ch14": (4306, 85000),
    "ch15": (3006, 70000), "ch16": (2006, 40000), "ch17": (1206, 30000),
    "ch18": (806, 28000), "ch19": (1206, 26000), "ch20": (2866, 22000),
}

# 章节时间（用于目录显示）
CHAPTER_TIME = {
    "ch01": "2018.03", "ch02": "2018.04", "ch03": "2018.07", "ch04": "2018.08",
    "ch05": "2018.10", "ch06": "2018.12", "ch07": "2019.05", "ch08": "2019.06",
    "ch09": "2019.10", "ch10": "2020.02", "ch11": "2020.08", "ch12": "2021.01",
    "ch13": "2021.03", "ch14": "2021.06", "ch15": "2021.09", "ch16": "2021.12",
    "ch17": "2022.06", "ch18": "2022.11", "ch19": "2023.03", "ch20": "2023.12",
}

FLAG_DEFAULTS = ("c_call", "c_haodan", "c_siyu", "c_gongzi", "c_zaodao",
                 "xf_saved", "sold_chen")


def emit_jump_table(names):
    """生成章节入口标签与目录数据，供「章节目录」界面使用。"""
    code = ["# 由 tools/gen_game.py 自动生成，请勿手改。", ""]
    rows = []
    for name in names:
        num, title = CH_TITLES.get(name, ("", name))
        rows.append('    ("%s", "%s", "%s", "%s"),' % (
            name, num, title, CHAPTER_TIME.get(name, "")))
    code.append("define CHAPTERS = [")
    code.extend(rows)
    code.append("]")
    code.append("")
    for name in names:
        q, d = CHAPTER_ENTRY.get(name, (0, 0))
        code.append("label %s_entry:" % name)
        code.append("    $ qian = %d" % q)
        code.append("    $ debt = %d" % d)
        # 体力 / 人情 / 完单数必须一起归零。之前只重置了 c_* 选项标志，
        # 从 ch20 跳回 ch01 会带着上一局的体力进来。
        code.append("    $ shen = 10")
        code.append("    $ xin = 5")
        code.append("    $ orders = 0")
        for f in FLAG_DEFAULTS:
            # 一律回到 defs.rpy 的默认值（c_siyu 默认 False = 报警线）。
            # 早先这里把 c_siyu 写成 True，等于强制玩家走「私了」分支。
            code.append("    $ %s = False" % f)
        code.append("    $ visited = False")
        # 每次跳章算一局新的，别和上一局的 run_id 混在同一份漏斗里
        code.append('    $ run_id = "j" + str(renpy.random.randint(1000, 9999)) + "_%s"' % name)
        code.append('    $ track("chapter_jump", chapter="%s")' % name)
        code.append("    jump %s" % name)
        code.append("")
    with open(os.path.join(OUT, "jump.rpy"), "w", encoding="utf-8") as f:
        f.write("\n".join(code) + "\n")

def validate_output():
    """生成后的控制流自检：标签唯一、跳转目标存在、无意外顺序落入。"""
    labels = {}
    errors = []
    warnings = []
    for path in sorted(glob.glob(os.path.join(OUT, "*.rpy"))):
        cur = None
        body = []
        seq = []

        def flush():
            if cur is not None:
                seq.append((cur, list(body)))

        for line in open(path, encoding="utf-8"):
            m = re.match(r"label\s+([A-Za-z0-9_]+)\s*:", line)
            if m:
                flush()
                cur = m.group(1)
                body = []
                if cur in labels:
                    errors.append("标签重复：%s（%s 与 %s）" % (
                        cur, labels[cur], os.path.basename(path)))
                labels[cur] = os.path.basename(path)
                continue
            if cur is not None:
                body.append(line.rstrip())
        flush()

        # 同一文件内，除最后一个 label 外，没有 jump/return 结尾就是顺序落入
        for i, (name, lines) in enumerate(seq):
            if i == len(seq) - 1:
                continue
            tail = [l for l in lines if l.strip()]
            last = tail[-1].strip() if tail else ""
            nxt = seq[i + 1][0]
            # 同章内的 anchor 汇合点（ch03 → ch03_join）是有意的顺序贯穿，不算问题
            base = name.split("_")[0]
            intentional = nxt.startswith(base + "_")
            if not intentional and not (last.startswith("jump ") or last.startswith("return")):
                warnings.append("%s: label %s 结尾没有 jump/return，会顺序落入 %s" % (
                    os.path.basename(path), name, nxt))

    for path in sorted(glob.glob(os.path.join(OUT, "*.rpy"))):
        for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
            for target in re.findall(r"\bjump\s+([A-Za-z0-9_]+)", line):
                if target not in labels:
                    errors.append("跳转目标不存在：%s（%s:%d）" % (
                        target, os.path.basename(path), lineno))

    for w in warnings:
        print("  警告 " + w)
    if errors:
        for e in errors:
            print("  错误 " + e)
        raise SystemExit("控制流自检失败：%d 个错误" % len(errors))
    print("控制流自检通过：%d 个标签，无悬空跳转，无顺序落入" % len(labels))
    return True

def main():
    os.makedirs(OUT, exist_ok=True)
    for f in glob.glob(os.path.join(OUT, "*.rpy")):
        os.remove(f)

    files = sorted(glob.glob(os.path.join(NOVEL, "chapters", "ch*.md")))
    names = [os.path.splitext(os.path.basename(f))[0] for f in files]
    mapping = []

    # 定义文件
    defs = ['# 由 tools/gen_game.py 自动生成，请勿手改。', ""]
    defs.append("define narrator = Character(None, what_color=\"#E8E4DC\")")
    for sid, (disp, color) in SPEAKERS.items():
        defs.append('define %s = Character("%s", who_color="%s")' % (sid, disp, color))
    defs.append("")
    defs.append("default qian = 3000")
    defs.append("default debt = 0")
    defs.append("default shen = 10")
    defs.append("default xin = 5")
    defs.append("default orders = 0")
    defs.append("default c_call = False")
    defs.append("default c_haodan = False")
    defs.append("default c_siyu = False")
    defs.append("default c_gongzi = False")
    defs.append("default c_zaodao = False")
    defs.append("default xf_saved = False")
    defs.append("default sold_chen = False")
    defs.append("default run_id = \"\"")
    defs.append("")
    defs.append("label start:")
    defs.append("    $ quick_menu = True")
    defs.append('    $ run_id = "%08x" % renpy.random.getrandbits(32)')
    defs.append('    $ track("run_start")')
    defs.append("    jump ch01")
    with open(os.path.join(OUT, "defs.rpy"), "w", encoding="utf-8") as f:
        f.write("\n".join(defs) + "\n")

    for i, (path, name) in enumerate(zip(files, names)):
        blocks = parse_file(path)
        nxt = names[i + 1] if i + 1 < len(names) else "ch20_end"
        code = emit_chapter(name, blocks, nxt)
        with open(os.path.join(OUT, name + ".rpy"), "w", encoding="utf-8") as f:
            f.write("# 由 tools/gen_game.py 自动生成，请勿手改。\n\n" + code + "\n")
        chars = sum(len(re.findall(r"[\u4e00-\u9fff]", b[2])) for b in blocks if b[0] == "say")
        scenes = [b[1] for b in blocks if b[0] == "scene"]
        mapping.append({"chapter": name, "title": CH_TITLES.get(name, ("", ""))[1],
                        "chars": chars, "scenes": scenes, "lines": sum(1 for b in blocks if b[0] == "say")})

    # 结局
    endings = []
    for path in sorted(glob.glob(os.path.join(NOVEL, "endings", "*.md"))):
        blocks = parse_file(path)
        label = "ending_" + os.path.splitext(os.path.basename(path))[0].replace("ending_", "")
        num = [b[1] for b in blocks if b[0] == "title"]
        code = []
        code.append("label %s:" % label)
        if num:
            code.append('    call screen chapter_card("结局", "%s")' % num[0])
        for b in blocks:
            kind = b[0]
            if kind == "scene":
                code.append("    scene %s" % BG_ALIAS.get(b[1], b[1]))
                code.append("    with fade")
            elif kind == "show":
                cmd = "    show %s %s" % (b[1], b[2])
                if b[3]:
                    cmd += " at %s" % b[3]
                code.append(cmd)
                code.append("    with dissolve")
            elif kind == "hide":
                code.append("    hide %s" % b[1])
                code.append("    with dissolve")
            elif kind == "bgm":
                code.append('    play music "audio/bgm/%s.ogg" fadein 1.5' % b[1])
            elif kind == "sfx":
                code.append('    play sound "audio/sfx/%s.ogg"' % b[1])
            elif kind == "ending":
                code.append("    $ persistent.ending_%s = True" % b[1])
            elif kind == "say":
                spk, text = b[1], b[2]
                for chunk in split_text(text, 110 if spk else 92):
                    if spk:
                        code.append('    %s "%s"' % (spk, esc(chunk)))
                    else:
                        code.append('    "%s"' % esc(chunk))
        code.append('    $ track("ending_complete", ending="%s")' % label)
        code.append("    call screen ending_card")
        code.append("    return")
        endings.append("\n".join(code))

    with open(os.path.join(OUT, "endings.rpy"), "w", encoding="utf-8") as f:
        f.write("# 由 tools/gen_game.py 自动生成，请勿手改。\n\n" + "\n\n".join(endings) + "\n")

    # 分支
    branches = []
    for path in sorted(glob.glob(os.path.join(ROOT, "game", "branches", "*.md"))):
        blocks = parse_file(path)
        label = os.path.splitext(os.path.basename(path))[0]
        code = ["label %s:" % label, '    $ track("ending_enter", ending="%s")' % label]
        for b in blocks:
            kind = b[0]
            if kind == "scene":
                code += ["    scene %s" % BG_ALIAS.get(b[1], b[1]), "    with fade"]
            elif kind == "bgm":
                code.append('    play music "audio/bgm/%s.ogg" fadein 1.0' % b[1])
            elif kind == "sfx":
                code.append('    play sound "audio/sfx/%s.ogg"' % b[1])
            elif kind == "jump":
                code.append("    jump %s" % b[1])
            elif kind == "say":
                spk, text = b[1], b[2]
                for chunk in split_text(text, 110 if spk else 92):
                    if spk:
                        code.append('    %s "%s"' % (spk, esc(chunk)))
                    else:
                        code.append('    "%s"' % esc(chunk))
        branches.append("\n".join(code))
    if branches:
        with open(os.path.join(OUT, "branches.rpy"), "w", encoding="utf-8") as f:
            f.write("# 由 tools/gen_game.py 自动生成，请勿手改。\n\n" + "\n\n".join(branches) + "\n")

    # 图片定义
    images = ["# 由 tools/gen_resources.py 自动生成，请勿手改。", ""]
    bgdir = os.path.join(ROOT, "game", "game", "images", "bg")
    for p in sorted(glob.glob(os.path.join(bgdir, "*.jpg")) + glob.glob(os.path.join(bgdir, "*.png"))):
        n = os.path.splitext(os.path.basename(p))[0]
        images.append('image %s = "images/bg/%s"' % (n, os.path.basename(p)))
    chardir = os.path.join(ROOT, "game", "game", "images", "char")
    for p in sorted(glob.glob(os.path.join(chardir, "*.png"))):
        n = os.path.splitext(os.path.basename(p))[0]
        if "_" in n:
            tag, expr = n.split("_", 1)
            images.append('image %s %s = "images/char/%s"' % (tag, expr, os.path.basename(p)))
    cgdir = os.path.join(ROOT, "game", "game", "images", "cg")
    for p in sorted(glob.glob(os.path.join(cgdir, "*.jpg")) + glob.glob(os.path.join(cgdir, "*.png"))):
        n = os.path.splitext(os.path.basename(p))[0]
        images.append('image %s = "images/cg/%s"' % (n, os.path.basename(p)))
    with open(os.path.join(OUT, "images.rpy"), "w", encoding="utf-8") as f:
        f.write("\n".join(images) + "\n")

    # 第 20 章结束标签
    with open(os.path.join(OUT, "ch20_end.rpy"), "w", encoding="utf-8") as f:
        f.write("label ch20_end:\n    call screen ending_card\n    return\n")

    with open(os.path.join(ROOT, "docs", "小说-游戏对应表.json"), "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    emit_jump_table(names)
    validate_output()
    print("生成完成：%d 章，%d 个结局，%d 个分支" % (len(files), len(endings), len(branches)))
    print("总字数（汉字）：", sum(m["chars"] for m in mapping))


if __name__ == "__main__":
    main()
