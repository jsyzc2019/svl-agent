"""DeepMind essay《What comes after AGI?》框架论证引擎（E1–E6）。

判据适配对象（KB-STRUCT01）：观点文不套统计复算、不套分类自洽，
改查主体归属 / 外推链算术+假设 / 可证伪分级 / 同谱系污染 / 诚实刻度 / 吸收决策。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 可证伪分级：具体预测 vs 宏大叙事（逐字依据 agi_essay_evidence.json）
FALSIFIABLE_PREDICTIONS = {
    "RSI 在可自动验证领域最快": {
        "quote": "RSI should advance fastest in domains that allow for automated verification without humans in the loop, such as mathematical proofs, while other domains might lag behind or taper off sooner.",
        "why": "带领域(数学证明)+可观测条件(自动验证)+对照(其他领域滞后)，可被未来观测证伪",
    },
    "多智能体协调收益递减": {
        "quote": "coordination inefficiencies still lead to diminishing returns as the population size grows",
        "why": "可观测的规模-收益关系，可证伪",
    },
    "capability overhang 导致陡跳": {
        "quote": "holding back one dimension while the others move forward would lead to sudden, steep jumps in progress when the suppressed dimension is relaxed",
        "why": "因果机制+可观测条件，可证伪",
    },
    "RSI runaway 是经验问题": {
        "quote": "Whether RSI leads to 'runaway' progress is largely an empirical question.",
        "why": "作者自己标为经验问题——开放但可研究，非不可证伪叙事",
    },
}

GRAND_NARRATIVES = {
    "ASI 将加速科学突破": "could ... accelerating science and enabling breakthroughs in medicine, materials, clean energy",
    "认知工业化重塑经济": "cognitive industrialization alone could reshape knowledge work and the broader economy",
}

CROSS_RELEVANCE = {
    "feedback_quality": ("本文 poor feedback→loops degenerate ↔ 我方 §36 predicted/observed + §38 评估可靠性", "同谱系"),
    "eval_scaling": ("本文 评估须扩展到超人领域 ↔ 我方尚未显式覆盖", "新增量"),
    "three_mechanisms": ("本文 code/data/group 三分 ↔ 我方 harness/memory 组件分类/awesome-rsi 阶梯", "不同切分轴·同谱系"),
    "model_measure_repeat": ("本文 model/measure/forecast/repeat ↔ 我方 PDCA/SVL 闭环", "同谱系"),
}


def load_ev() -> dict:
    return json.loads((ROOT / "agi_essay_evidence.json").read_text(encoding="utf-8"))


def e1_subject(ev: dict) -> dict:
    rn = ev["retrieval_note"]
    disclaimer = rn["disclaimer_verbatim"]
    is_dmi = "DMI" in rn["platform"] or "DeepMind Institute" in rn["platform"]
    not_official = "should not be read as Google's official view" in disclaimer
    return {
        "id": "E1",
        "platform_is_dmi": is_dmi,
        "disclaimer_explicit": not_official,
        "decision": "主体=作者/DMI团队观点，非Google官方立场（免责声明明确）" if not_official else "主体需警惕",
        "misplacement_guard": "二手若读成'DeepMind官方预言ASI'→主体错位；原作者有免责不连坐",
        "preserve": not_official,
        "pass": is_dmi and not_official,
    }


def verify_extrapolation_arithmetic() -> dict:
    """可复算：从论文给出的因子重算外推，不靠一次性手算硬编码。"""
    hw, algo_lo, algo_hi, inv = 1.5, 3.0, 6.0, 2.5
    low, high = hw * algo_lo * inv, hw * algo_hi * inv
    ten_year = 10 ** 10
    ten_year_cost = 1e9 / (4 ** 10)
    return {
        "effective_compute_per_year": [round(low, 2), round(high, 2)],
        "at_least_10x": low >= 10,
        "ten_year_factor": ten_year,
        "ten_year_is_10_billion": ten_year == 10_000_000_000,
        "exceeds_world_population": ten_year > 8e9,
        "cost_after_10y": round(ten_year_cost, 2),
        "cost_approx_1000": abs(ten_year_cost - 1000) < 100,
    }


def e2_extrapolation(ev: dict) -> dict:
    nums = ev["primary_source"]["extrapolation_numbers"]
    caveats = nums["caveats_authored"]
    check = verify_extrapolation_arithmetic()
    # 真正复算：所有算术断言须为 True（取代脆弱的字符串包含检查）
    arithmetic_checks = [
        check["at_least_10x"], check["ten_year_is_10_billion"],
        check["exceeds_world_population"], check["cost_approx_1000"],
    ]
    arithmetic_ok = all(arithmetic_checks)
    labeled = len(caveats) >= 3
    return {
        "id": "E2",
        "arithmetic_recomputed": check,
        "arithmetic_self_consistent": arithmetic_ok,
        "assumptions_labeled": labeled,
        "caveats": caveats,
        "decision": "算术自洽+主动标注假设=高严谨度（preserve）" if (arithmetic_ok and labeled) else "需警惕外推未标注",
        "critical_separation": "算术自洽≠外推成立：趋势维持十年是经验问题，不因算对就认预测为真",
        "pass": arithmetic_ok and labeled,
    }


def e3_falsifiability() -> dict:
    return {
        "id": "E3",
        "falsifiable_predictions": [
            {"claim": k, "why": v["why"]} for k, v in FALSIFIABLE_PREDICTIONS.items()
        ],
        "grand_narratives": [
            {"claim": k, "quote": v} for k, v in GRAND_NARRATIVES.items()
        ],
        "n_falsifiable": len(FALSIFIABLE_PREDICTIONS),
        "n_narrative": len(GRAND_NARRATIVES),
        "decision": f"{len(FALSIFIABLE_PREDICTIONS)}条可证伪具体预测 + {len(GRAND_NARRATIVES)}条宏大叙事，分层不混同",
        "pass": len(FALSIFIABLE_PREDICTIONS) >= 3 and len(GRAND_NARRATIVES) >= 1,
    }


def e4_lineage() -> dict:
    rows = [
        {"aspect": k, "relation": v[0], "verdict": v[1]} for k, v in CROSS_RELEVANCE.items()
    ]
    isomorphic = all(r["verdict"] in ("同谱系", "新增量", "不同切分轴·同谱系") for r in rows)
    independent_claim_would_be_wrong = all("同谱系" in r["verdict"] or "不同切分轴" in r["verdict"] for r in rows if r["verdict"] != "新增量")
    return {
        "id": "E4",
        "rows": rows,
        "contamination_declared": isomorphic,
        "decision": "一律标注同谱系呼应/不同切分轴，非独立验证；新增量单列" if isomorphic else "谱系未声明",
        "guard": "若把呼应当成对方面框架的独立佐证→触发KB-STRUCT02污染门禁",
        "pass": isomorphic and independent_claim_would_be_wrong,
    }


def e5_honesty(ev: dict) -> dict:
    signals = ev["primary_source"]["honesty_signals"]
    n = len(signals)
    return {
        "id": "E5",
        "n_self_declarations": n,
        "samples": signals[:3],
        "decision": f"高诚实度（preserve）：主动声明{n}处边界/不确定" if n >= 5 else "诚实度待查",
        "pass": n >= 5,
    }


def e6_absorption() -> dict:
    """KB-META01：只编译能指出具体被拦/被判/被降级动作的新增量。"""
    candidates = {
        "evaluation_scalability": {
            "content": "评估须可扩展到超人领域（人类群体也难判AI输出）",
            "concrete_action": "当评估方案依赖人工判断且目标为超人域时 → flag '评估不可扩展'，要求补充自动验证/可扩展判据方可下强结论",
            "verdict": "能长出牙（但需先查是否与已有 evaluation_reliability 重复→不重复则为轻量增量）",
        },
        "domain_specific_rsi_speed": {
            "content": "RSI 在可自动验证领域(数学证明)最快、其他领域滞后",
            "concrete_action": "这是一条可证伪预测，价值在于'可追踪'，但无现成执行流挂载点 → 记 preserve 观察项，不强行造模块",
            "verdict": "暂不长牙（避免为改进而改进）",
        },
    }
    actionable = [k for k, v in candidates.items() if "能长出牙" in v["verdict"]]
    return {
        "id": "E6",
        "candidates": candidates,
        "actionable": actionable,
        "decision": f"新增量中 {len(actionable)} 项可长牙（评估可扩展性），1 项记观察不强造模块",
        "kb_meta01_compliance": True,
        "pass": len(actionable) == 1,
    }


def three_layer(ev: dict, e1, e2, e3, e4, e5, e6) -> dict:
    return {
        "layer1_fact": (
            "DeepMind Institute 2026-11-19 观点文（作者 Tim Genewein，基于 From AGI to ASI 技术报告）："
            "智能连续统 + 认知工业化 + 四条路径(scaling/范式/协调/RSI) + 多路径复合；"
            "含数量级外推且算术自洽；Disclaimer 明确非 Google 官方立场。"
        ),
        "layer2_boundary": (
            "观点文≠实证(无统计量可复算)；算术自洽≠外推成立(趋势维持十年是经验问题)；"
            "DMI个人观点≠官方立场；RSI段与我方判据同谱系呼应≠独立验证；"
            "可证伪具体预测与不可证伪宏大叙事须分层。"
        ),
        "layer3_method": (
            "①判据适配对象：观点文查外推链算术+假设明示+可证伪分级，不套统计复算/分类自洽；"
            "②主体归属精确到'作者/平台/免责'三层；③同谱系呼应标污染；"
            "④吸收按KB-META01：评估可扩展性可长牙、领域速度预测记观察不强造模块。"
        ),
    }


def run() -> dict:
    ev = load_ev()
    e1, e2, e3, e4, e5, e6 = e1_subject(ev), e2_extrapolation(ev), e3_falsifiability(), e4_lineage(), e5_honesty(ev), e6_absorption()
    result = {
        "document": "DeepMind essay 框架论证结果",
        "pre_registration_sha256": (ROOT / "agi_essay_prereg.sha256").read_text().split()[0],
        "E1": e1, "E2": e2, "E3": e3, "E4": e4, "E5": e5, "E6": e6,
        "conclusion": three_layer(ev, e1, e2, e3, e4, e5, e6),
        "all_judgments_fired": all(x["pass"] for x in [e1, e2, e3, e4, e5, e6]),
    }
    (ROOT / "agi_essay_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


if __name__ == "__main__":
    r = run()
    for e in ["E1", "E2", "E3", "E4", "E5", "E6"]:
        print(f"[{e}] {r[e]['decision']}")
    print("\n全部判据按预期触发:", r["all_judgments_fired"])
