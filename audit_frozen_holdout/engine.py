#!/usr/bin/env python3
"""§100 冻结 held-out 独立性验证 —— one-shot 评分引擎.

纪律:
  - 判据 G 已在 gate_prereg.json 预注册锁定,本引擎只实现它,不因样本长相改词表.
  - G 只读 sample['claim'] 与 sample['evidence'],绝不读 sample['variant']/ground_truth (盲评).
  - 样本 samples.json 已 hash 冻结 (samples.sha256),本引擎只读不写.
  - 只跑一次;result.json 落盘后,回放测试只读冻结结果,不重算判据.
"""
import json
import hashlib
import re
import sys
from collections import Counter

BASE = "/workspace/audit_frozen_holdout"


# ---- 判据 G (逐字照搬 prereg.pre_registered_judge_G.definition) ----
MARKERS = {
    "negation": ["no", "not", "never", "无", "不"],
    "limiter": ["only", "merely", "just", "solely"],
    "contrast": ["however", "but", "although", "though", "yet"],
    "condition": ["if", "unless", "when", "除非"],
}


def claim_markers(claim: str):
    """从 claim 提取限定标记集 M (逐字 token,小写). 数字 token 另计."""
    low = claim.lower()
    found = set()
    for _cat, words in MARKERS.items():
        for w in words:
            # 用词边界匹配,避免 'not' 命中 'nothing' 之类
            if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
                found.add(w)
    for m in re.finditer(r"\b\d+\b", claim):
        found.add(m.group(0))
    return sorted(found)


def judge_G(claim: str, evidence: str):
    """决定性文本比对: claim 的限定标记 M 是否全部逐字出现在 evidence.
    返回 (supported: bool, markers: list, missing: list).
    注意: 本函数不接收 variant / ground_truth —— 盲评.
    """
    m = claim_markers(claim)
    ev_low = evidence.lower()
    missing = []
    for tok in m:
        if re.search(r"(?<![a-z])" + re.escape(tok) + r"(?![a-z])", ev_low):
            continue
        missing.append(tok)
    return (len(missing) == 0), m, missing


def load_frozen_samples():
    """校验 samples.json 哈希未变后载入."""
    raw = open(f"{BASE}/downloads/samples.json", "rb").read()
    locked = open(f"{BASE}/samples.sha256", encoding="utf-8").read().split()[0]
    assert hashlib.sha256(raw).hexdigest() == locked, "samples.json 哈希失配 —— 拒绝评分"
    return json.loads(raw)


def verify_source():
    """校验 held-out 源哈希未变."""
    raw = open(f"{BASE}/downloads/paper_flat.txt", "rb").read()
    locked = open(f"{BASE}/source.sha256", encoding="utf-8").read().split()[0]
    return hashlib.sha256(raw).hexdigest() == locked


def verify_prereg():
    """校验预注册判据锁定未变."""
    out = {}
    for f, lk in [("prereg.json", "prereg.sha256"), ("gate_prereg.json", "gate_prereg.sha256")]:
        raw = open(f"{BASE}/{f}", "rb").read()
        locked = open(f"{BASE}/{lk}", encoding="utf-8").read().strip()
        out[f] = hashlib.sha256(raw).hexdigest() == locked
    return out


def one_shot():
    assert verify_source(), "held-out 源哈希失配"
    assert all(verify_prereg().values()), "预注册锁定失配"

    data = load_frozen_samples()
    rows = []
    for s in data["samples"]:
        supported, markers, missing = judge_G(s["claim"], s["evidence"])
        gt = s["ground_truth_supported"]
        rows.append({
            "id": s["id"],
            "variant": s["variant"],          # 仅用于结果对照,从不喂给 judge_G
            "markers_in_claim": markers,
            "missing_in_evidence": missing,
            "G_supported": supported,
            "ground_truth_supported": gt,
            "match": (supported == gt),
        })

    # 指标 (按 variant 分层)
    def rate(variant, key):
        xs = [r for r in rows if r["variant"] == variant]
        return sum(r[key] for r in xs) / len(xs) if xs else None

    tamper_catch = rate("tampered", "match")       # tampered 应被 G 判 unsupported→match
    clean_pass = rate("clean", "match")
    canary_fp = 1 - rate("canary", "match")         # canary 被 G 判 unsupported=假阳性
    core_acc = (sum(r["match"] for r in rows if r["variant"] != "canary") /
                sum(1 for r in rows if r["variant"] != "canary"))

    # canary 假阳性根因诊断 (post-hoc,不喂判据): 被误判的 canary 是否都缺 claim 标记
    canary_rows = [r for r in rows if r["variant"] == "canary"]
    fp_canaries = [r for r in canary_rows if not r["match"]]
    root_cause = {
        "false_positive_canaries_all_missing_marker": all(len(r["missing_in_evidence"]) > 0 for r in fp_canaries),
        "fp_canary_count": len(fp_canaries),
        "canary_total": len(canary_rows),
        "note": ("canary 是'另一句原文支撑句',天然不含 claim 的限定标记;判据 G 的词标记匹配"
                 "只适用于'逐字支撑/删改限定'判断(clean vs tampered),不适用于跨句语义支撑。"
                 "故被误判的 canary 反映的是判据-样本设计不兼容,而非 G 在核心任务上过拟合。"),
        "posthoc_correction": ("首跑诊断字段名为 canary_missing_claim_marker,措辞误表述为'全部 canary 缺标记'"
                               "(事实 4 缺 2 有:S02/S05 碰巧含 never/not 通过);本字段仅修正 post-hoc 诊断措辞"
                               "与计算,判据 G 与核心评分(tamper/clean/canary_fp/core_acc)one-shot 不变。"),
    }

    # 结论: 尊重预注册 precommit —— canary_fp>0 诚实降级
    overfit_flag = canary_fp > 0
    verdict = {
        "core_transferable": core_acc == 1.0 and tamper_catch == 1.0,
        "independence_grade": "strong_structural_proxy_with_canary_design_defect",
        "l3_claimed": False,
        "absolute_independence_claimed": False,
        "downgrade_reason": ("canary 假阳性>0 触发预注册 precommit 降级;根因为判据G与canary定义"
                             "的概念不兼容(已post-hoc定位),核心 clean/tampered 可迁移性仍成立"),
    }

    return {
        "experiment": "§100 frozen-holdout independence verification",
        "source": {
            "paper": "arXiv:2610.16067v1",
            "sha256": open(f"{BASE}/source.sha256", encoding="utf-8").read().split()[0],
            "novelty": "本仓从未用该论文设计判据/锚点",
        },
        "separation": {
            "data": "外部一手arXiv,hash冻结",
            "proposer": "独立子agent(隔离context,不获知本仓判据/锚点/check),自标ground truth",
            "judge": "决定性算法G(预注册锁定,只读claim+evidence,不看variant标签)",
            "structural_honesty": ("子agent由本Agent spawn且同模型家族→独立性为structural proxy"
                                   "(信息隔离真实,同源模型残余);解释环节仍本Agent"),
        },
        "locks": {"prereg": verify_prereg(), "samples_frozen": True, "one_shot": True},
        "metrics": {
            "tamper_catch_rate": tamper_catch,
            "clean_pass_rate": clean_pass,
            "canary_false_positive_rate": canary_fp,
            "core_accuracy_excl_canary": core_acc,
            "overfit_flag": overfit_flag,
        },
        "root_cause_diagnosis": root_cause,
        "rows": rows,
        "verdict": verdict,
        "honest_boundary": ("数据独立=yes;出题独立=yes(结构性);判据决定性=yes;但canary设计缺陷+"
                            "同模型家族+解释环节本Agent→标 strong_structural_proxy_with_defect,"
                            "非absolute,不宣布L3;§99的frozen_holdout_canary=no本次仅部分缓解"),
    }


if __name__ == "__main__":
    result = one_shot()
    with open(f"{BASE}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    m = result["metrics"]
    print("=== §100 one-shot 结果 ===")
    print(f"tamper_catch_rate  = {m['tamper_catch_rate']}")
    print(f"clean_pass_rate    = {m['clean_pass_rate']}")
    print(f"canary_fp_rate     = {m['canary_false_positive_rate']}")
    print(f"core_acc(excl can)= {m['core_accuracy_excl_canary']}")
    print(f"overfit_flag       = {m['overfit_flag']}")
    print("verdict:", result["verdict"]["independence_grade"],
          "| l3_claimed=", result["verdict"]["l3_claimed"])
    print("canary根因:", result["root_cause_diagnosis"]["note"][:80])
