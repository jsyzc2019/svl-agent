#!/usr/bin/env python3
"""MLLM 因果任务分解精研核验引擎（§83-§84）。

确定性核验：analysis-before-prereg 锁存的 P0-P7 命题一手锚点命中 + 两门禁 live_regression。
只读证据目录，输出 result.json，可重跑复现。
"""
import json
import pathlib
import re
import sys
from bs4 import BeautifulSoup

ROOT = pathlib.Path(__file__).parent
DL = ROOT / "downloads"
sys.path.insert(0, str(ROOT.parent))

_soup = BeautifulSoup((DL / "paper.html").read_text(encoding="utf-8"), "html.parser")
for _t in _soup(["script", "style", "math", "svg"]):
    _t.decompose()
paper = re.sub(r"\s+", " ", _soup.get_text(" ")).strip()

ANCHORS = {
    "P0_problem": [
        "records how often MLLMs fail, but cannot distinguish whether a failure reflects an intrinsic deficit in the targeted capability or a cascading error from an upstream prerequisite",
        "the same error but opposite capability diagnoses",
    ],
    "P1_why_trace_insufficient": [
        "observing untreated generation alone cannot disentangle the two failure modes",
        "stated chains-of-thought do not always reflect the computation behind the final answer",
        "linking sub-task and final correctness by co-occurrence",
    ],
    "P2_intervention": [
        "we instead set each prerequisite to a known correct or incorrect state",
        "injecting the correct answer for",
        "injecting an incorrect answer for",
        "the natural state where is not injected",
    ],
    "P3_exogeneity": [
        "the state of a unit task admits no faithful observational readout and is identified only through the intervention",
        "making conditioning on and intervening operationally identical",
        "absence of a faithful observational channel making intervention the reliable state-assignment mechanism",
    ],
    "P4_capability_metrics": [
        "a large gap indicates that the model can solve given correct prerequisites, pointing to upstream cascading errors as the primary bottleneck",
        "a small gap with low suggests an intrinsic deficit",
        "comparing with shows whether false prerequisites mislead the model below its natural baseline",
    ],
    "P5_no_monotonicity": [
        "We do not assume monotonicity: in LLM reasoning, injecting incorrect answer",
        "can help more than no injection",
        "N-Score and S-Score as observable lower bounds",
    ],
    "P6_bounds": [
        "N-Score and S-Score provide valid lower bounds on the Probability of Necessity",
        "A high N-Score pinpoints critical performance bottlenecks",
        "A high S-Score identifies high-leverage prerequisites",
    ],
    "P7_finding": [
        "supplying correct prerequisites eliminates",
        "of its natural errors",
        "the single most important one alone captures",
        "of the gain from supplying all prerequisites",
    ],
}


def check_anchors():
    details = {}
    for prop, arr in ANCHORS.items():
        hits = {s: (s in paper) for s in arr}
        details[prop] = {"all": all(hits.values()), "hits": hits}
    return details


def check_gates():
    from svagent.failure_causal_identifiability import live_regression as reg_a
    from svagent.causal_contribution_honesty import live_regression as reg_b
    return {
        "gate_A_failure_causal": reg_a(),
        "gate_B_causal_contribution": reg_b(),
    }


def main():
    anchors = check_anchors()
    gates = check_gates()
    result = {
        "section": "§83-§84",
        "paper": "arXiv:2609.38851v1 Where MLLMs Fail and Why: Causal Task Decomposition for Capability Failure Diagnosis",
        "evidence_grade": "primary（arXiv 官方 HTML 全文，self-reported 实验按 KB-RSI07 折1；只编译方法论拦截面）",
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
