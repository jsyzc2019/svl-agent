#!/usr/bin/env python3
"""HarnessPro 精研分析引擎（§77）。

确定性核验：预注册锁存的 C1-C8 命题的原文锚点命中 + 交叉证据 + 活体回归。
只读证据目录，输出 result.json。可重跑复现（analysis-before-prereg 已先锁存命题）。
"""
import json
import subprocess
import hashlib
import pathlib

ROOT = pathlib.Path(__file__).parent
DL = ROOT / "downloads"

paper = (DL / "S01_arxiv_pdf.txt").read_text(encoding="utf-8")
evalg = (DL / "S03_evaluation_raw.md").read_text(encoding="utf-8")

# C1-C8 原文锚点（按 pdftotext -layout 真实单行措辞；断字处取稳定子串）
anchors = {
    "C1_harness_def": [
        "An agent harness is the software infrastructure that manages interactions",
        "prompts, tools and skills, context and memory mechanisms, hooks",
        "Recursive self-improvement uses trajectories from previous tasks",
    ],
    "C2_dual_objective": [
        "min (−PR(h), C(h))",
        "Pareto frontier and select three representative operating",
        "cost-focused (lite), balanced (medium), and performance-focused (heavy)",
    ],
    "C3_label_free": [
        "label-free",
        "without access to ground-truth solutions or",
        "without access to ground-truth so-",
        "These generated tests remain fixed throughout the self-",
    ],
    "C4_recall_boundary": [
        "overly optimistic",
        "treating flawed implementations as suc-",
        "failure recall increasing from 41.7% to",
        "83.3% compared with direct LLM judgments (Figure 2)",
    ],
    "C5_criterion_boundary": [
        "No separate reviewer is part of this run.",
        "do not launch another reviewer.",
        "answer key. Public sample programs",  # 原文 "...never an" / "answer key." 跨行，取真实单行
        "what was not checked, and limitations",
    ],
    "C6_leakage_control": [
        "we partition tasks into training, validation, and test sets",
        "use only validation metrics, with no access to test-set results",
        "on the held-out test set Dtest only after all rounds",
    ],
    "C7_main_result": [
        "average pass-rate gain of 2.0 percentage points",
        "task cost reduction of 26.1%",  # 原文 "average per-" / "task cost reduction of 26.1%" 跨行
        "4.5 percent-",
        "33.9% lower mean cost",
    ],
    "C8_repro_boundary": [
        "does not reproduce",
        "not included in this release",
        "not part of this package",
    ],
}

claim_hits = {}
for k, arr in anchors.items():
    src = evalg if k == "C8_repro_boundary" else paper
    claim_hits[k] = {
        "hits": sum(1 for a in arr if a in src),
        "total": len(arr),
        "matched": [a for a in arr if a in src],
        "missed": [a for a in arr if a not in src],
    }

total = sum(v["total"] for v in claim_hits.values())
hits = sum(v["hits"] for v in claim_hits.values())

# 交叉证据：S03 明确复现边界（加分）；S01 AI use statement 自报人工复核
crosscheck = {
    "S03_release_scope_honest": "not included in this release" in evalg,
    "S03_glm_snapshot_missing": "GLM-5.2 evolved harness snapshots" in evalg,
    "S03_no_repro_with_mismatch": "does not reproduce" in evalg,
    "S01_ai_use_selfreported": "checked by the authors." in paper and "All AI-assisted code and text were manually reviewed" in paper,
    "S01_preprint_status": "Under review" in paper,
}

live = subprocess.run(
    ["python3", "-c",
     "import sys,json;sys.path.insert(0,'/workspace');"
     "from svagent.criterion_origin_honesty import live_regression;"
     "print(json.dumps(live_regression(),ensure_ascii=False))"],
    capture_output=True, text=True, cwd="/workspace",
).stdout.strip()

result = {
    "request_id": "harnesspro-20261122",
    "prereg_sha256": (ROOT / "prereg.sha256").read_text().strip(),
    "manifest_sha256": (ROOT / "manifest.sha256").read_text().strip(),
    "gate_prereg_sha256": (ROOT / "gate_prereg.sha256").read_text().strip(),
    "claim_anchors": {
        "per_claim": {k: f"{v['hits']}/{v['total']}" for k, v in claim_hits.items()},
        "detail": claim_hits,
        "total": f"{hits}/{total}",
        "all_hit": hits == total,
    },
    "crosscheck": crosscheck,
    "evidence_grade": {
        "S01": "preprint under review(未评审)折1；实验作者自报3次运行mean±std、无第三方复现；Table2数字为论文声称本机未重跑",
        "S03": "一手release文档，诚实披露不含benchmark数据/镜像/权重/凭据、GLM-5.2 snapshots缺失、错配不复现——复现边界诚实(加分)",
        "结论": "证据支持『作者实现框架并报告数字』，不支持『已独立复现/方法普遍有效』",
    },
    "novelty_check": {
        "covered_by_existing": [
            "proof_boundary_honesty(§71):形式化/密码学证明边界(承诺锚独立/证明范围)",
            "verification_boundary_honesty(§76):绿灯覆盖边界(经验性通过声明)",
            "finance_blind_test/retrospective:文本出现label-free/召回词但非判据",
        ],
        "gap": "无门禁判『自生成判据评估自生成改进』的判据来源/召回边界/外部锚定/独立评审缺口——对象评估判据本身的可信度前提",
        "decision": "编译第25门禁 criterion_origin_honesty(KB-META01会拦才入)",
    },
    "gate_live_regression": json.loads(live),
    "honesty_boundary": "本门禁只判声明自洽，不承诺评估判据真可靠(KB-STRUCT05框架≠有效、KB-R07自洽≠有效、KB-RSI07自述折扣、preprint折1)",
}

(ROOT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("锚点:", result["claim_anchors"]["total"], "all_hit", result["claim_anchors"]["all_hit"])
for k, v in claim_hits.items():
    miss = f" MISS={v['missed']}" if v["missed"] else ""
    print(f"  {k}: {v['hits']}/{v['total']}{miss}")
print("交叉:", sum(1 for v in crosscheck.values() if v), "/", len(crosscheck))
print("活体 all_passed:", result["gate_live_regression"]["all_passed"])
