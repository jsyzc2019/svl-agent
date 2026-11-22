#!/usr/bin/env python3
"""多模态 Agent 记忆综述精研核验引擎（§79-§80）。

确定性核验：analysis-before-prereg 已锁存的 P0-P8 命题一手锚点命中 + 项目主页统计
交叉 + 两门禁 live_regression。只读证据目录，输出 result.json，可重跑复现。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
DL = ROOT / "downloads"
sys.path.insert(0, str(ROOT.parent))

paper = (DL / "paper.html").read_text(encoding="utf-8")
home = (DL / "S02_project_home.html").read_text(encoding="utf-8")

# 真实单行锚点（已按 paper_text.txt 断字校准；断行处取稳定单行子串）
ANCHORS = {
    "P0_two_axis": [
        "two-axis analytical framework for multimodal agent memory",
        "Axis I, Formation and Representation",
        "Axis II, Memory Management",
        "T3 Self-Evolving Memory updates memory through an evolving policy",
    ],
    "P1_t3_rare_explicit": [
        "T2 Dynamic Memory accounts for 204 architectures (68.7% of the corpus)",
        "T3 Self-Evolving Memory accounts for 17 architectures (5.7%)",
        "Of the 17 T3 Self-Evolving Memory architectures, 13 are cross-represented systems, while the other 4 are hybrid systems that include an explicit representation.",
        "neither the source-preserving category nor the latent or parametric category contains a T3 Self-Evolving Memory system under our definition",
    ],
    "P2_policy_addressability": [
        "policy addressability, policy-level feedback attribution, and persistent, validated policy revision",
        "behavior must provide an identifiable target for revision. It may be represented explicitly as a rule, instruction,",
        "Explicit policy representations allow more precise revisions, whereas distributed representations make the effects of individual changes harder to isolate.",
    ],
    "P3_feedback_attribution": [
        "such operations. Feedback must therefore be sufficiently informative to",
        "distinguish failures of writing, maintenance, retrieval, reasoning, and action.",
        "A task-level reward alone may reveal that the agent failed without identifying",
        "which part of memory management should change.",
    ],
    "P4_evidence_path_drift": [
        "revised policy can maintain or even improve short-term answers while relying less",
        "on the modality that originally grounded them. For example, a system may answer",
        "correctly from a cached textual summary while rarely reopening the visual",
        "policy-evolution methods rarely evaluate whether adaptation changes the balance",
        "of evidence used across representations.",
    ],
    "P5_revision_validated": [
        "A policy revision constitutes self-evolution only when it is retained as part",
        "of the reusable memory-management process and affects subsequent memory",
        "policy versions and their evaluation histories also supports comparison,",
        "auditing, and restoration when a revision proves harmful.",
        "Policy-level validation therefore requires subsequent, replayed, or held-out cases",
    ],
    "P6_provenance_designed": [
        "a substantial portion of the analyzed architectures do not retain a usable route",
        "back to the evidence from which their memories were formed.",
        "Provenance is therefore seldom a designed",
        "property of the representation.",
        "provenance should be treated as part of",
        "the representation itself rather than as optional metadata",
    ],
    "P7_temporal_validity": [
        "The central memory property is therefore not recall volume alone, but recoverable provenance and temporal validity, since persistence without these safeguards can retain stale or weakly grounded evidence.",
        "whether an apparent conflict reflects a genuine change, an unreliable observation, or information that is valid only under a different temporal or situational context",
    ],
    "P8_reversibility": [
        "verifiability requires provenance and version information connecting the update to supporting evidence; reversibility requires an earlier version, operation log, checkpoint, or reconstructible source;",
    ],
}

# 项目主页交叉统计锚点（P1 的另一口径）
HOME_ANCHORS = ["17 of 17", "68.2%", "46.8%", "7 of 82", "82 benchmarks"]


def check_anchors():
    details = {}
    for prop, arr in ANCHORS.items():
        hits = {s: (s in paper) for s in arr}
        details[prop] = {"all": all(hits.values()), "hits": hits}
    home_hits = {s: (s in home) for s in HOME_ANCHORS}
    details["HOME_stats"] = {"all": all(home_hits.values()), "hits": home_hits}
    return details


def check_gates():
    from svagent.policy_evolution_grounding import live_regression as reg_a
    from svagent.memory_provenance_honesty import live_regression as reg_b
    return {
        "gate_A_policy_evolution": reg_a(),
        "gate_B_memory_provenance": reg_b(),
    }


def main():
    anchors = check_anchors()
    gates = check_gates()
    result = {
        "section": "§79-§80",
        "paper": "arXiv:2610.19366v1 Seeing, Maintaining, and Learning: The Evolution of Multimodal Agent Memory",
        "evidence_grade": "survey（二手综合+作者自有corpus统计）按 KB-RSI07 折1；PDF 下载失败降级用官方HTML",
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
