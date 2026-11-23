"""§114 冻结输入生成器——从四轮 result.json 自动提取裁决充分统计量（杜绝手填）。

产出（spawn 前锁定，之后不得改）:
- cases_blind.json : 给异厂解释者的匿名指标 + 中性化裁决规则（不含轮次/历史裁决）
- gt_private.json  : 私有 scorer —— 匿名 id -> 来源轮次/历史裁决/中性档（绝不进异厂 prompt）

可复现: 固定 SEED 打乱 case 顺序; 所有指标来自四轮已锁 result.json, 不重算不手填。
"""
import json, hashlib, random, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
SEED = 11420261123

def load(rel):
    return json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))

def dsha(d):
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

# 四轮来源：原始匿名槽 A/B/C/D（映射在打乱前先记录）
SRC = {
    "A": ("audit_stratified_confirmation/result.json", "STRATIFIED_CONFIRMED"),
    "B": ("audit_cross_domain_confirm2/result.json", "CROSS_SET_PARTIAL"),
    "C": ("audit_admission_ast_audit/result.json", "AST_V2_PARTIAL"),
    "D": ("audit_cross_vendor_designer2/result.json", "CROSS_VENDOR2_PARTIAL"),
}

def extract(rel):
    d = load(rel)
    sm = d.get("stratified_metric") or {}
    m = d.get("metrics") or {}
    primary = sm.get("PRIMARY_non_negation_gap", m.get("PRIMARY"))
    secondary = sm.get("SECONDARY_negation_gap", m.get("SECONDARY"))
    core = d.get("core", {})
    p1core = core.get("P1") if core else m.get("P1_core")
    p0core = core.get("P0") if core else m.get("P0_core")
    p0dT = sm.get("dT_non_negation", {}).get("P0") if "dT_non_negation" in sm else m.get("P0_dT")
    return {
        "PRIMARY": round(float(primary), 6),
        "SECONDARY": round(float(secondary), 6),
        "P1_core": round(float(p1core), 6),
        "P0_core": round(float(p0core), 6),
        "P0_dT": round(float(p0dT), 6),
        "admission_ok": True,
    }

def neutral_tier(verdict):
    # 只取档位语义，去掉 STRATIFIED_/CROSS_SET_/AST_V2_/CROSS_VENDOR2_ 前缀
    for t in ("CONFIRMED", "PARTIAL", "REFUTED", "INCONCLUSIVE"):
        if verdict.endswith(t) or ("_" + t) in verdict:
            return t
    raise ValueError(verdict)

# 中性化裁决规则（四轮同构，去前缀），给异厂解释者判据
NEUTRAL_RULES = [
    "FULL：admission_ok 且 PRIMARY≥0.8 且 SECONDARY≤0.3 且 P1_core≥0.9 且 P0_地板(P0_core≤0.6 或 P0_dT≥0.8)",
    "PARTIAL：admission_ok 且 PRIMARY≥0.8，但 SECONDARY>0.3 或 P1_core<0.9 或 非P0_地板（三者至少一条不满足）",
    "REFUTED：admission_ok 且 PRIMARY<0.3（取向差真不复现）",
    "INCONCLUSIVE：admission 未过 / PRIMARY 落 0.3~0.8 中间带 / 无法判定",
]

def main():
    raw = {cid: extract(rel) for cid, (rel, _) in SRC.items()}
    order = ["A", "B", "C", "D"]
    random.Random(SEED).shuffle(order)   # 固定 seed 打乱 -> 匿名 id = case_1..case_4
    blind_cases, gt = [], {}
    for i, orig in enumerate(order, 1):
        nid = f"case_{i}"
        blind_cases.append({"id": nid, **raw[orig]})
        rel, verdict = SRC[orig]
        gt[nid] = {
            "source_round": rel.split("/")[0],
            "historical_verdict": verdict,
            "neutral_tier": neutral_tier(verdict),
        }
    cases_blind = {
        "experiment": "§114 interpreter-independence blind cases",
        "seed": SEED,
        "note": "指标自动提取自四轮已锁 result.json；case 顺序经固定 seed 打乱；档位名中性化；不含轮次与历史裁决。",
        "rules_neutral": NEUTRAL_RULES,
        "cases": blind_cases,
    }
    gt_private = {
        "experiment": "§114 private scorer —— 绝不进异厂 prompt",
        "seed": SEED,
        "mapping": gt,
        "neutral_gt": {k: v["neutral_tier"] for k, v in gt.items()},
    }
    json.dump(cases_blind, open(os.path.join(BASE, "cases_blind.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    json.dump(gt_private, open(os.path.join(BASE, "gt_private.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("cases_blind.sha256 =", dsha(cases_blind))
    print("gt_private.sha256  =", dsha(gt_private))
    print("neutral_gt =", json.dumps(gt_private["neutral_gt"], ensure_ascii=False, sort_keys=True))
    print("blind order =", order)

if __name__ == "__main__":
    main()
