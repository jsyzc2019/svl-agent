#!/usr/bin/env python3
"""UltraBERT 编码器预训练配方精研核验引擎（§85-§86）。

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
    "P0_problem": [
        "the pretraining recipe itself remains inherited from small-scale conventions",
        "no single model performing competitively across both classification and retrieval tasks",
    ],
    "P1_saturation": [
        "downstream performance saturates around 1–2T tokens even as training and validation losses keep decreasing",
        "This indicates an upper bound that additional tokens cannot raise",
        "the BEIR scores saturate even earlier, showing no significant improvement beyond the first evaluation point of 275B tokens",
    ],
    "P2_mask_conflict": [
        "classification consistently favors lower masking ratios across model sizes, contradicting prior work suggesting larger ratios for larger models",
        "lower masking ratios benefit classification while higher ones benefit retrieval",
    ],
    "P3_distill_interaction": [
        "Distillation with pruning improves classification at low masking ratios but degrades retrieval at high ones",
    ],
    "P4_de_confounding": [
        "At saturation, where convergence speed no longer confounds the comparison",
    ],
    "P5_decoupling": [
        "reconciles the two masking regimes within a single encoder rather than settling for a single configuration",
        "mixes 5% and 50% masked sequences within each batch while assigning a separate LM head to each ratio",
        "restrict distillation to the low-ratio sequences, while training the high-ratio ones with standard MLM",
    ],
    "P6_sota": [
        "the first encoder to achieve state of the art on both classification and retrieval tasks",
        "reaching 91.0 on GLUE and 47.7 on BEIR",
    ],
}


def check_anchors():
    details = {}
    for prop, arr in ANCHORS.items():
        hits = {s: (s in paper) for s in arr}
        details[prop] = {"all": all(hits.values()), "hits": hits}
    return details


def check_gates():
    from svagent.config_conflict_isolation import live_regression as reg_a
    from svagent.compute_saturation_honesty import live_regression as reg_b
    return {
        "gate_A_config_conflict": reg_a(),
        "gate_B_compute_saturation": reg_b(),
    }


def main():
    anchors = check_anchors()
    gates = check_gates()
    result = {
        "section": "§85-§86",
        "paper": "arXiv:2610.15028v1 UltraBERT: Beyond the Limit of BERT Pre-Training",
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
