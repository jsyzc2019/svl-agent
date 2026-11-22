#!/usr/bin/env python3
"""EvoSteer 在线自演化图编排精研核验引擎（§81-§82）。

确定性核验：analysis-before-prereg 已锁存的 P0-P6 命题一手锚点命中（在 HTML 原文
逐字核对）+ 两门禁 live_regression。只读证据目录，输出 result.json，可重跑复现。
锚点提取工具已修正为 get_text(' ')+空白规整（跨行断字不放水、不改规则）。
"""
import json
import pathlib
import re
import sys
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).parent
DL = ROOT / "downloads"
sys.path.insert(0, str(ROOT.parent))

# 从 HTML 原文按空格连接重建 flat 文本（修正跨行断字的提取工具）
_soup = BeautifulSoup((DL / "paper.html").read_text(encoding="utf-8"), "html.parser")
for _t in _soup(["script", "style", "math", "svg"]):
    _t.decompose()
paper = re.sub(r"\s+", " ", _soup.get_text(" ")).strip()

# analysis-before-prereg 锁存的 19 个逐字锚点（anchors_locked.json 同源）
ANCHORS = {
    "P0_online_in_run": [
        "in which the orchestrator dynamically builds and repairs a running team from execution features and a learned value estimate",
        "The orchestrator issues one atomic edit per turn, rerun and drop included",
        "so a plausible but failing result can be redone mid-run.",
    ],
    "P1_posthoc_cost": [
        "orchestration still evolves only between trajectories, by revising skills, prompts, or topology after a batch of runs has ended",
        "impossible to repair while the workflow is still being executed.",
    ],
    "P2_credit_diffusion": [
        "give every action the same coefficient of a single terminal advantage",
        "learned state values confound how often a task is solved, execution noise, and structural choice",
        "whether a low score came from a task the reference rarely solves or from a badly organized team",
    ],
    "P3_reference_anchor": [
        "assigns each orchestration action a coefficient by balancing subtrajectories against a frozen reference",
        "combines a task-level reference anchor with prefix-dependent corrections",
        "The measured terms are held fixed",
    ],
    "P4_skill_trial": [
        "lets a candidate be tried before it is promoted, and promotes or retires it only when paired evidence passes a sequential test under a shared alpha-spending budget",
        "two extra trajectories are launched from the same record and the same forced first role, one binding and one not",
    ],
    "P5_calibration": [
        "such point estimates cannot separate insufficient evidence from a confirmed effect",
        "no test tracks whether an admitted skill still helps on later tasks, it stays in the library and is never retired",
        "which promotes, retires, or defers",
    ],
    "P6_fwer": [
        "the total nominal level is at most",
        "By a union bound, family-wise error is at most",
        "whenever each directional p-value is valid for the selection and sampling rules in use, even for dependent tests",
    ],
}


def check_anchors():
    details = {}
    for prop, arr in ANCHORS.items():
        hits = {s: (s in paper) for s in arr}
        details[prop] = {"all": all(hits.values()), "hits": hits}
    return details


def check_gates():
    from svagent.online_repair_honesty import live_regression as reg_a
    from svagent.skill_admission_calibration import live_regression as reg_b
    return {
        "gate_A_online_repair": reg_a(),
        "gate_B_skill_admission": reg_b(),
    }


def main():
    anchors = check_anchors()
    gates = check_gates()
    result = {
        "section": "§81-§82",
        "paper": "arXiv:2609.38661v2 EvoSteer: Online Self-Evolving Graph Orchestration via Reference-Anchored Credit Assignment",
        "evidence_grade": "primary（arXiv 官方 HTML 全文，self-reported 实验按 KB-RSI07 折1；只编译机制拦截面）",
        "anchors": anchors,
        "gates": gates,
        "anchor_all_passed": all(v["all"] for v in anchors.values()),
        "gate_all_passed": all(g["all_passed"] for g in gates.values()),
    }
    result["all_passed"] = result["anchor_all_passed"] and result["gate_all_passed"]
    (ROOT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("anchor_all_passed:", result["anchor_all_passed"])
    print("gate_all_passed:", result["gate_all_passed"])
    print("ALL:", result["all_passed"])
    for k, v in anchors.items():
        if not v["all"]:
            print("  MISS", k, [s for s, h in v["hits"].items() if not h])


if __name__ == "__main__":
    main()
