#!/usr/bin/env python3
"""Latent Taxonomies 属性归纳发展精研核验引擎（§87-§88）。

确定性核验：analysis-before-prereg 锁存的 P0-P6 命题一手锚点命中 + 两门禁 live_regression。
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
    "P0_emergence": [
        "taxonomically aligned induction emerges from next-token prediction alone",
        "a property learned for one entity transfers more strongly within its taxonomic category than across categories",
    ],
    "P1_recoverable": [
        "clustering recovers the full taxonomic tree from entity representations",
        "entities that share a deeper category become more similar in activation space",
        "Can the entire tree, including its branching structure, be fully reconstructed from the representations? Using a standard clustering technique, we find that it can",
    ],
    "P2_scale_hurts": [
        "induction weakens with model size when the data budget is fixed",
        "larger models memorize individual facts rather than compress them into shared structure",
        "At a fixed data budget, scale hurts",
        "the induction advantage decreases with model size",
    ],
    "P3_maturity": [
        "Induction also strengthens with more pre-training before the taxonomy injection",
        "a model that has learned more general language before the taxonomy is introduced learns to generalize over it more strongly",
    ],
    "P4_incontext": [
        "transfers to novel in-context properties",
        "acquiring taxonomic structure in the weights enables models to apply it to novel in-context properties",
    ],
    "P5_override": [
        "can be overridden by a latent taxonomy implied by the prompt",
        "Context overrides weights under conflicting taxonomies",
        "the model generalizes according to the context taxonomy",
    ],
    "P6_implication": [
        "inductive generalization reflects the latent organization of its training data",
        "predicting how far a learned fact will spread",
    ],
}


def check_anchors():
    details = {}
    for prop, arr in ANCHORS.items():
        hits = {s: (s in paper) for s in arr}
        details[prop] = {"all": all(hits.values()), "hits": hits}
    return details


def check_gates():
    from svagent.induction_structure_honesty import live_regression as reg_a
    from svagent.context_override_boundary import live_regression as reg_b
    return {
        "gate_A_induction_structure": reg_a(),
        "gate_B_context_override": reg_b(),
    }


def main():
    anchors = check_anchors()
    gates = check_gates()
    result = {
        "section": "§87-§88",
        "paper": "arXiv:2610.15836v1 Latent Taxonomies: How Property Induction Develops in Language Model Pre-training",
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
