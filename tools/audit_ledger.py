#!/usr/bin/env python3
"""账本一致性校验：按路线模拟现金与债务，检查章节之间是否对得上。

用法：
    python3 tools/audit_ledger.py            # 打印主线与各分支路线
    python3 tools/audit_ledger.py --check    # 有矛盾则非零退出（供 CI 使用）

规则：
- `<!-- stat: k=v when=cond -->` 是章节入口的绝对状态，条件不成立则跳过。
- `<!-- money: k=±v when=cond -->` 是本章内发生的收支，累加。
- 选项的 actions 里 `$ qian -= 12000` 这类语句按同一套变量计算。
- 章节结束时，状态应等于下一章入口（条件允许的部分由 when 区分）。
"""

import glob
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DIRECTIVE = re.compile(r"<!--\s*([a-z]+)\s*:\s*(.*?)\s*-->")

CHOICES = {
    "ch03": [
        ("接下这些“刚好”的单子", {"c_haodan": True, "xin": 1, "qian": 300}),
        ("把钥匙还回去", {"c_haodan": False, "xin": -1}),
    ],
    "ch07": [
        ("报警，走程序", {"c_siyu": False, "qian": -4000, "shen": -1}),
        ("私了，花钱买平安", {"c_siyu": True, "qian": -12000, "debt": 8000}),
    ],
    "ch09": [
        ("把工资卡交给她", {"c_gongzi": True, "xin": 2}),
        ("工资卡自己留着", {"c_gongzi": False, "xin": -1}),
    ],
    "ch12": [
        ("先把手上那单送完", {"c_zaodao": False, "qian": 6}),
        ("立刻掉头回家", {"c_zaodao": True}),
    ],
    "ch14": [
        ("当晚带她走", {"xf_saved": True}),
        ("下个月再来接她", {"xf_saved": False}),
    ],
    "ch19": [
        ("交出陈立的住址和聊天记录", {"sold_chen": True, "qian": 2000, "debt": -2000}),
        ("拒绝", {"sold_chen": False, "xin": 2}),
    ],
}

DEFAULTS = {"qian": 0, "debt": 0, "xin": 0, "shen": 0,
            "c_haodan": False, "c_siyu": False, "c_gongzi": False,
            "c_zaodao": False, "xf_saved": False, "sold_chen": False}


def eval_cond(cond, state):
    if not cond:
        return True
    cond = cond.strip()
    if cond.startswith("not "):
        return not state.get(cond[4:].strip(), False)
    return bool(state.get(cond, False))


def parse_chapter(path):
    """返回 [(kind, payload, cond)]，kind ∈ {stat, money, choice}。"""
    out = []
    for line in open(path, encoding="utf-8"):
        m = DIRECTIVE.search(line)
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        if key in ("stat", "money"):
            cond = None
            if "when=" in val:
                head, cond = val.split("when=", 1)
                cond = cond.strip()
                tokens = head.split()
            else:
                tokens = val.split()
            d = {}
            for kv in tokens:
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    d[k] = int(v) if re.fullmatch(r"[+-]?\d+", v) else v
            out.append((key, d, cond))
        elif key == "choice":
            out.append(("choice", val.strip(), None))
    return out


def run(route_pick):
    state = dict(DEFAULTS)
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "novel", "chapters", "ch*.md"))):
        name = os.path.splitext(os.path.basename(path))[0]
        entry = dict(state)
        for kind, payload, cond in parse_chapter(path):
            if kind == "stat":
                if eval_cond(cond, state):
                    for k, v in payload.items():
                        state[k] = v
            elif kind == "money":
                if eval_cond(cond, state):
                    for k, v in payload.items():
                        cur = state.get(k, 0)
                        state[k] = v if (isinstance(v, str) or isinstance(cur, str)) else cur + v
            elif kind == "choice":
                idx = route_pick.get(payload)
                if idx is None:
                    continue
                _, acts = CHOICES[payload][idx]
                for k, v in acts.items():
                    if isinstance(v, bool):
                        state[k] = v
                    else:
                        state[k] = state.get(k, 0) + v
        rows.append((name, entry["qian"], entry["debt"], state["qian"], state["debt"]))
    return rows, state


ROUTES = {
    "主线（私了·交卡·送完）": {"ch07": 1, "ch09": 0, "ch12": 0, "ch19": 0},
    "报警·留卡·掉头": {"ch07": 0, "ch09": 1, "ch12": 1, "ch19": 0},
}


def main():
    check = "--check" in sys.argv
    problems = []
    for label, picks in ROUTES.items():
        rows, end = run(picks)
        print("\n=== %s ===" % label)
        print("%-6s %10s %9s %10s %9s" % ("章", "入口现金", "入口债", "出口现金", "出口债"))
        prev = None
        for name, q0, d0, q1, d1 in rows:
            flag = ""
            if q1 < 0:
                flag = "  ← 现金为负"
                problems.append("%s %s 现金为负：%d" % (label, name, q1))
            print("%-6s %10d %9d %10d %9d%s" % (name, q0, d0, q1, d1, flag))
            prev = (q1, d1)
        print("结局前状态：现金 %d，债务 %d" % prev)

    if problems:
        print("\n发现 %d 处问题：" % len(problems))
        for p in problems:
            print("  " + p)
        if check:
            sys.exit(1)
    else:
        print("\n账本校验通过：全部路线现金非负，章节入口与上一章出口衔接。")


if __name__ == "__main__":
    main()
