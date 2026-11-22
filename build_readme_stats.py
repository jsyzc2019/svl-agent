#!/usr/bin/env python3
"""README 统计段自动生成器（阶段5：消除 F6 手工漂移）。

从 KB / 测试 / audit 目录 / 包模块实时重算统计数字，输出可粘贴的 Markdown 统计卡，
并用 --write 直接替换 README.md 中 <!-- STATS:START --> / <!-- STATS:END --> 之间的内容。
数字全部来自文件系统实测，不再手工维护。
"""
import argparse
import ast
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
START = "<!-- STATS:START -->"
END = "<!-- STATS:END -->"


def collect() -> dict:
    # KB
    kb = json.loads((ROOT / "knowledge_base_store.json").read_text(encoding="utf-8"))
    items = kb.get("items", [])
    # audit 目录 / 五件套
    five = ("manifest.json", "prereg.json", "gate_prereg.json", "engine.py", "result.json")
    dirs = [d for d in ROOT.iterdir() if d.is_dir() and d.name.startswith("audit_")]
    full = sum(1 for d in dirs if all((d / f).exists() for f in five))
    # check_* 门禁函数
    gates = 0
    for p in (ROOT / "svagent").glob("*.py"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        gates += sum(1 for n in ast.walk(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                     and n.name.startswith("check_"))
    # 测试项数（从 pytest --collect-only 拿，回退到文件数）
    try:
        out = subprocess.run(
            ["python3", "-m", "pytest", "-p", "no:cacheprovider",
             "--override-ini=addopts=", "--collect-only", "-q"],
            cwd=ROOT, capture_output=True, text=True, timeout=120,
        ).stdout
        m = re.findall(r"(\d+) tests? collected", out)
        tests = int(m[-1]) if m else "?"
    except Exception:
        tests = "?"
    # 推导进度（commentary 最高 section）
    commentary = (ROOT / "commentary.md").read_text(encoding="utf-8")
    sections = re.findall(r"§(\d+)", commentary)
    max_sec = max((int(s) for s in sections), default=0)
    return {
        "kb_items": len(items),
        "audit_dirs": len(dirs),
        "five_piece": full,
        "gate_functions": gates,
        "tests": tests,
        "last_section": max_sec,
    }


def render(s: dict) -> str:
    return "\n".join([
        START,
        "## 仓库现状（自动生成 · 运行 `python3 build_readme_stats.py --write` 刷新）",
        "",
        "| 指标 | 数值 | 来源 |",
        "|---|---|---|",
        f"| 推导进度 | §1–§{s['last_section']} | `commentary.md` 实测最高节 |",
        f"| 知识库条目 | {s['kb_items']} | `knowledge_base_store.json` |",
        f"| 会拦门禁（`check_*`） | {s['gate_functions']} | `svagent/*.py` AST 扫描 |",
        f"| 测试项 | {s['tests']} | `pytest --collect-only` |",
        f"| 证据目录 | {s['audit_dirs']}（五件套齐全 {s['five_piece']}） | `audit_*/` 实测 |",
        "",
        "> 诚实边界：模拟线（autopoiesis/self_evolving/telos/axiology/mechanism/estimation）",
        "> 的输出均标注 `evidence_scope: synthetic`，是方法演示，不外推为真实世界自进化能力。",
        END,
    ])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true", help="回写 README.md 的 STATS 区块")
    args = ap.parse_args()
    s = collect()
    card = render(s)
    if args.write:
        p = ROOT / "README.md"
        text = p.read_text(encoding="utf-8")
        if START in text and END in text:
            new = re.sub(re.escape(START) + r".*?" + re.escape(END),
                         lambda _: card, text, flags=re.S)
        else:
            new = text.rstrip() + "\n\n" + card + "\n"
        p.write_text(new, encoding="utf-8")
        print("README.md 统计段已刷新")
    else:
        print(card)
    print(json.dumps(s, ensure_ascii=False))


if __name__ == "__main__":
    main()
