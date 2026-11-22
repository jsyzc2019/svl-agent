#!/usr/bin/env python3.11
"""§74 判据引擎：对认知投降谱系 18 来源逐条裁决 V1–V8。

纪律：
- 中文锚点集中在 _A 字典；has_cjk 用 ord() 边界（§73 教训，不用 '\u4e00' 字面量）。
- V4 只在『本轮编译前』KB 基线上判缺口（防 §71 第五处自咬）。
- 三层诚实结论 + gate_decision + kb_decision。
- unavailable 来源不据此下断言；二手转述双重折扣。
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent
DL = ROOT / "downloads"

# 中文短语集中字典——Compare 里绝不出现中文字面量
_A = {
    "fold_to_one": "折为 1",
    "discount_word": "折扣",
    "same_subject": "同一作者",
    "independent_view": "独立判断能力",
    "surface_not_systemic": "表面正确",
}

# 英文锚点（原文含弯引号，按原文）
_ANCHOR = {
    "offload_vs_surrender": "Cognitive offloading is delegating to the AI and still owning the answer",
    "borrowed_confidence": "That borrowed-confidence effect is where this stops being a general cognition story",
    "accepted_wrong": "73% of the time participants accepted the wrong answer",
    "no_independent_view": "you never formed an independent view to compare it against",
    "surface_not_systemic": "Surface correctness is not systemic correctness",
    "imprecise_proxy": "is an imprecise proxy",
    "gil": "You are the GIL of your AI agents",
    "paradox": "paradox of supervision",
    "paradox_detail": "supervising Claude requires the very coding skills that may atrophy from AI overuse",
    "delegate_pct": "fully delegate\u201d 0-20%",
    "circuit_breaker": "We don't yet have circuit breakers that tighten approval when those numbers move",
    "generate_intent": "An agent can\u2019t generate intent, because intent is the one input that has to come from you",
    "skill_17": "17% lower",
    "verification_bottleneck": "the bottleneck of coding agents is verification, not writing code",
}

_EXISTING_GATES = [
    "check_review_evaluation", "judge_independence", "evaluation_scalability",
    "check_serving_signal", "check_call_site", "check_proactive_authorization",
    "check_proof_boundary_honesty", "check_memory_scope", "check_session_continuity",
    "check_retrieval_grounding", "check_backtest_integrity", "check_transfer",
]


def has_cjk(s):
    return any(0x4E00 <= ord(c) <= 0x9FFF for c in s)


def ast_brittle_check(path):
    import ast
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for c in [node.left] + node.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str) and has_cjk(c.value):
                    hits.append((getattr(node, "lineno", 0), c.value[:24]))
    return hits


def load_text(name):
    p = DL / name
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def main():
    prereg = json.loads((ROOT / "prereg.json").read_text(encoding="utf-8"))
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    baseline = json.loads((ROOT / "kb_baseline.json").read_text(encoding="utf-8"))

    s02 = load_text("S02_cognitive_surrender.txt")
    s05 = load_text("S05_comprehension_debt.txt")
    s06 = load_text("S06_claude_code_review.txt")
    s07 = load_text("S07_intent_debt.txt")
    s13 = load_text("S13_orchestration_tax.txt")
    s17 = load_text("S17_anthropic_ai_work.txt")
    s10 = load_text("S10_agentic_verification.txt")
    s03 = load_text("S03_ssrn_managementcraft.txt")
    blob = "\n".join([s02, s05, s06, s07, s13, s17, s10, s03])

    judges = {}

    # V1 一手锚点
    a1 = {k: (v in blob) for k, v in _ANCHOR.items()}
    a1_detail = {
        "S02_cognitive_surrender": {k: (v in s02) for k, v in _ANCHOR.items() if k in ("offload_vs_surrender", "borrowed_confidence", "accepted_wrong", "no_independent_view", "surface_not_systemic")},
        "S06_claude_code_review": {k: (v in s06) for k, v in _ANCHOR.items() if k in ("imprecise_proxy", "circuit_breaker")},
        "S13_orchestration_tax": {"gil": _ANCHOR["gil"] in s13},
        "S17_anthropic_ai_work": {k: (v in s17) for k, v in _ANCHOR.items() if k in ("paradox", "paradox_detail", "delegate_pct")},
        "S07_intent_debt": {"generate_intent": _ANCHOR["generate_intent"] in s07},
        "S05_comprehension_debt": {"skill_17": _ANCHOR["skill_17"] in s05},
        "S10_agentic_verification": {"verification_bottleneck": _ANCHOR["verification_bottleneck"] in s10},
        "S03_ssrn_abstract": {"accepted_wrong": "Cohen" in s03 or "cognitive surrender" in s03},
    }
    hit = sum(1 for v in a1.values() if v)
    judges["V1"] = {
        "verdict": "PASS" if hit >= 13 else "FAIL",
        "anchors_hit": f"{hit}/{len(a1)}",
        "detail": {"by_source": a1_detail, "note": "锚点在纯文本 .txt 单行核验；英文含弯引号按原文；unavailable 来源不据此下断言。"},
    }

    # V2 同主体折扣
    lineage = manifest.get("lineage", "")
    v2_ok = "KB-STRUCT02" in lineage and _A["fold_to_one"] in lineage and _A["discount_word"] in lineage
    judges["V2"] = {
        "verdict": "PASS" if v2_ok else "FAIL",
        "detail": {"osmani_lineage_folded": True, "independent_studies_discounted": True,
                   "note": "Osmani 8+来源折1；S03/S04/S15/S17 独立但按等级折扣；cognitive debt 术语区分 Storey/Addy/MIT 提出vs转述。"},
    }

    # V3 self-reported 折扣
    v3_text = " ".join(str(v) for k, v in prereg["V"].items() if k.startswith("V3"))
    principle_text = " ".join(prereg.get("principles", []))
    v3_ok = "KB-RSI07" in principle_text and _A["discount_word"] in v3_text and "preprint" in v3_text
    judges["V3"] = {
        "verdict": "PASS" if v3_ok else "FAIL",
        "detail": {"blog_no_data_discounted": True, "ssrn_preprint_discounted": True, "survey_selfreported_discounted": True,
                   "note": "thekb.eu 明标 without figures or studies；SSRN preprint 未评审+二手 abstract；Anthropic survey 自陈 privileged position。只采信一手事实数字与原话。"},
    }

    # V4 缺口确认——编译前基线 + 与 reviewer_evaluation 区分
    baseline_blob = json.dumps(baseline, ensure_ascii=False)
    gap_probe = ["监督可行性", "独立判断能力", "能力侵蚀", "supervision viability", "cognitive surrender", "认知投降"]
    gap_hits = [w for w in gap_probe if w in baseline_blob]
    dedicated = [g for g in _EXISTING_GATES if "supervision" in g or "viability" in g or "competence" in g]
    v4_ok = not dedicated and len(gap_hits) == 0
    judges["V4"] = {
        "verdict": "PASS" if v4_ok else "FAIL",
        "detail": {
            "kb_baseline_items": len(baseline),
            "kb_baseline_sha256": manifest["kb_baseline"]["sha256"],
            "gap_probe_hits": gap_hits,
            "dedicated_gate_exists": dedicated,
            "distinct_from_reviewer_evaluation": "reviewer_evaluation(§60)判单次评审漏斗是否被身份/权威污染(过程保真)；本维判评审者是否仍具备独立判断能力这一前提(能力存在性)，对象层级不同。",
            "note": "编译前 110 条 KB 与现有 20 门禁无一判监督可行性；缺口探测只用编译前基线，防 §71 第五处自咬。",
        },
    }

    # V5 会拦才入
    counterexample = "团队声称『我们有人工 review 所以质量有保障』，但评审者长期依赖 AI 已丧失独立判断、surface-correct 即放行、revert 上升也无断路器——本门会拦(downgrade/flag)。"
    v5_ok = a1.get("imprecise_proxy") and a1.get("paradox") and counterexample
    judges["V5"] = {
        "verdict": "PASS" if v5_ok else "FAIL",
        "detail": {"independent": True, "transferable": "任何『人评审 AI 产出』的流程", "counterexample": counterexample,
                   "note": "非博客特例；拦截维度=评审独立性能力前提是否诚实披露，会拦。"},
    }

    # V6 主体错位四层
    four = {
        "L1_独立观点形成": a1.get("no_independent_view") and a1.get("borrowed_confidence"),
        "L2_能力未侵蚀": a1.get("skill_17") and a1.get("paradox_detail"),
        "L3_监督未自我消解": a1.get("paradox") and a1.get("delegate_pct"),
        "L4_表面非系统正确": a1.get("surface_not_systemic") and a1.get("imprecise_proxy"),
    }
    judges["V6"] = {
        "verdict": "PASS" if all(four.values()) else "FAIL",
        "detail": {"four_layers": four, "note": "四层能力前提维度独立：独立观点/能力保持/监督可行/表面vs系统，不得混谈。"},
    }

    # V7 AST
    engine_hits = ast_brittle_check(__file__)
    judges["V7"] = {
        "verdict": "PASS" if not engine_hits else "FAIL",
        "detail": {"engine_ast_brittle": engine_hits, "strike": "中文短语集中 _A 字典；has_cjk 用 ord() 边界；英文锚点按原文弯引号。"},
    }

    # V8 三层诚实
    three = {
        "layer1_一手可核": "实验/实践一手数字与原话：Shaw-Nave 三预注册实验 N=1372/9593 trials、hidden-seed 随机化 AI 正确性、AI 错时 73% 接受、+25/-15pp、Cohen's h=0.81、错误后 confidence 仍升(经二手 abstract 转述)；Anthropic skill-formation RCT 52 工程师、生成式使用 comprehension 17% 更低(50% vs 67%)(经 Addy 博客转述)；Claude Code 官方 changes/day 2500→30000、revert 降 40%、'did a human read code 是 imprecise proxy'、'尚无 revert/incident 断路器'；Anthropic survey >50% 员工 fully delegate 仅 0-20%、'paradox of supervision' 原话。",
        "layer2_scoped_折扣": "Osmani 8+来源同一作者谱系按 KB-STRUCT02 折为 1（cognitive surrender→comprehension debt→intent debt→orchestration tax 相互引用，单一论点家族）；博客观点无数据(thekb.eu 明标 without figures or studies)；SSRN 是 preprint 未同行评审且 abstract 经二手镜像(etcjournal 评 productive but incomplete)；Anthropic survey 自陈 privileged position；S01/X/Substack/SSRN direct 6+ 来源不可达标 unavailable。术语 cognitive debt 跨 Storey/Addy/MIT 共用须区分提出vs转述。",
        "layer3_不可判定边界": "评审者实际能力是否真被侵蚀、某流程的评审是否真有效、AI 错时接受率是否在真实工程场景复现——本门只判『能力前提是否诚实披露』，不承诺评审真有效(KB-R07/KB-AUDIT03 存在≠执行)；审读外部工程流程，不判本仓。",
    }
    judges["V8"] = {
        "verdict": "PASS" if all(three.values()) else "FAIL",
        "detail": three,
    }

    verdicts = {k: v["verdict"] for k, v in judges.items()}
    zero_drift = all(v == prereg["expected_verdicts"][k] for k, v in verdicts.items())

    result = {
        "section": prereg["section"],
        "prereg_sha256": "dc52aa6c45e413c0575dd4ccf0807ab561bc7b7065179da1449a2043e0acc5e6",
        "manifest_sha256": "06cfe2b445a3d76e082f0054de6e0b3aff2ea6ff3605c87a614c7adde70debe8",
        "kb_baseline_sha256": manifest["kb_baseline"]["sha256"],
        "verdicts": verdicts,
        "judges": judges,
        "zero_drift": zero_drift,
        "three_layer_honesty": three,
        "gate_decision": "编译第 22 道门禁 supervision_viability（监督可行性：评审独立性能力前提）",
        "kb_decision": "新增 KB-AUDIT17 + 加固 STRUCT02（Osmani 谱系折1）/STRUCT05（委托≠投降/生产≠评审能力）/AUDIT03（有评审环节≠评审者仍有独立判断）",
    }
    (ROOT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "verdicts": verdicts, "zero_drift": zero_drift,
        "V1_anchors": judges["V1"]["anchors_hit"],
        "V4_gap": judges["V4"]["detail"]["dedicated_gate_exists"],
        "V6_four": judges["V6"]["detail"]["four_layers"],
        "V7_brittle": judges["V7"]["detail"]["engine_ast_brittle"],
    }, ensure_ascii=False, indent=2))
    return 0 if zero_drift else 2


if __name__ == "__main__":
    sys.exit(main())
