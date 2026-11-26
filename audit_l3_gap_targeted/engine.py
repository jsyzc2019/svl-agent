#!/usr/bin/env python3
"""本仓侧：§L3-R2 缺口定向全链外置的机械比对与裁决。

只读：外家 v2 交付副本 + 本仓冻结样本 + prereg 预注册阈值。
不改外家任何文件/判据/参数。裁决树来自 prereg（早于外家执行），
不事后设阈值。l3_claimed 恒 false，由人裁定。

用法：python3 engine.py [外家交付目录，默认 audit_l3_gap_targeted/received/l3_external_audit_v2]
外家交付未到时落 PRE_REGISTERED_AWAITING_EXTERNAL_EXECUTION 待命态。
"""
import importlib.util
import json
import os
import sys

BASE = "audit_l3_gap_targeted"
EXT = sys.argv[1] if len(sys.argv) > 1 else f"{BASE}/received/l3_external_audit_v2"
OWN = "audit_frozen_holdout/downloads/samples.json"
PREREG = f"{BASE}/prereg.json"
# §4gm 判定态源职责分离（承 §4gl ENGINE_LOG 待改进点）：
# result.json 是内核判定态权威源（kernel.py / numeric_honesty.truth_snapshot 只读它），
# 子实验裁决只能写独立文件 result_experiment.json，绝不回写权威源。
# engine 运行前后以三态快照守卫，任何污染立即抛错，不静默放过。
KERNEL_VERDICT_SOURCE = f"{BASE}/result.json"
EXPERIMENT_RESULT = f"{BASE}/result_experiment.json"


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def kernel_state_snapshot():
    """只读内核判定态三元组（verdict/l3/absolute）；字段缺失抛错，不静默。"""
    r = load(KERNEL_VERDICT_SOURCE)
    return (r["verdict"], r["l3_claimed"], r["absolute_claimed"])


def awaiting():
    return {
        "experiment": "L3_GAP_TARGETED_EXTERNAL",
        "status": "PRE_REGISTERED_AWAITING_EXTERNAL_EXECUTION",
        "verdict": None,
        "metrics": None,
        "baseline": load(PREREG)["baseline_from_previous_round"],
        "does_not_overturn": load(PREREG)["does_not_overturn"],
        "l3_claimed": False,
        "absolute_claimed": False,
    }


def main():
    before = kernel_state_snapshot()  # 运行前锁定内核权威态，收尾处校验未被污染
    need = ["criterion.py", "judgments.json", "verdict.json", "samples_blind.json"]
    if not all(os.path.exists(f"{EXT}/{f}") for f in need):
        json.dump(awaiting(), open(EXPERIMENT_RESULT, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        assert kernel_state_snapshot() == before, "内核判定态源被子实验写入污染"
        print("status=PRE_REGISTERED_AWAITING_EXTERNAL_EXECUTION (外家交付未到)")
        return

    prereg = load(PREREG)
    fam = prereg["family_taxonomy"]
    assertion_ids = set(fam["assertion_family_list"])
    numeric_ids = set(fam["numeric_family_list"])

    # 1. 外家内部一致性（不信自报，独立重算）
    spec = importlib.util.spec_from_file_location("gap_crit", f"{EXT}/criterion.py")
    ec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ec)
    ext_samples = load(f"{EXT}/samples_blind.json")["pairs"]
    ext_j = load(f"{EXT}/judgments.json")
    internal, internal_total = 0, 0
    for r in ext_samples:
        got = ec.judge(r["text_a"], r["text_b"])
        gotb = bool(got[0]) if isinstance(got, tuple) else bool(got)
        internal += int(gotb == bool(ext_j[r["id"]]["verdict"]))
        internal_total += 1

    # 2. 回放外家判据到本仓冻结样本
    own = load(OWN)["samples"]
    by_variant, detail = {}, []
    agree = 0
    for r in own:
        got = ec.judge(r["claim"], r["evidence"])
        gotb = bool(got[0]) if isinstance(got, tuple) else bool(got)
        exp = bool(r["ground_truth_supported"])
        ok = gotb == exp
        agree += int(ok)
        v = r.get("variant", "?")
        a, b = by_variant.get(v, [0, 0])
        by_variant[v] = [a + int(ok), b + 1]
        detail.append({"id": r["id"], "variant": v,
                       "family": next((f for f, ids in (
                           ("ASSERTION_TAIL", fam["ASSERTION_TAIL"]),
                           ("NEGATION", fam["NEGATION"]),
                           ("CONNECTOR", fam["CONNECTOR"]),
                           ("NUMERIC_QUANT", fam["NUMERIC_QUANT"])) if r["id"] in ids), "?"),
                       "external_judge": gotb, "own_gt": exp, "match": ok})
    total = len(own)

    # 3. 按族统计检出（仅 tampered：gt=False，judge=False 才算检出）
    def detected(ids):
        hit = sum(1 for d in detail if d["id"] in ids and d["own_gt"] is False and d["external_judge"] is False)
        return hit, len(ids)

    a_hit, a_tot = detected(assertion_ids)
    n_hit, n_tot = detected(numeric_ids)
    clean = by_variant.get("clean", [0, 0])
    canary = by_variant.get("canary", [0, 0])

    # 4. 裁决（prereg §verdict_tree_pre_registered，逐字阈值，不放宽）
    ext_v = load(f"{EXT}/verdict.json")
    if not (clean[0] == clean[1] == 6):
        verdict = "GAP_DIVERGENT"
        why = f"clean {clean[0]}/{clean[1]} <6/6：判据过拟合到数值特征，牺牲普通情形"
    elif a_hit >= 3 and canary[0] >= 3:
        verdict = "GAP_CLOSED"
        why = (f"断言类检出 {a_hit}/{a_tot} 相对基线 0/4 实质突破，clean {clean[0]}/{clean[1]}，"
               f"canary {canary[0]}/{canary[1]}：第二家判据看到了断言层")
    elif a_hit in (1, 2):
        verdict = "GAP_PARTIAL"
        why = f"断言类检出 {a_hit}/{a_tot}：可见面从数值层向断言层部分扩展，但未闭合"
    elif a_hit == 0:
        verdict = "GAP_NOT_CLOSED"
        why = (f"断言类检出 0/{a_tot}，与上一轮数值型判据基线持平；"
               f"数值类 {n_hit}/{n_tot}——缺口未闭合")
    else:
        verdict = "GAP_INCONCLUSIVE"
        why = f"回放结果落入未预期分支：a_hit={a_hit}"

    # 交付验收结论必须是验收器实跑写入的摘要；缺失=未验收=封顶 INCONCLUSIVE（不放宽）
    acc_path = f"{EXT}/verification_summary.json"
    accepted = os.path.exists(acc_path) and json.load(open(acc_path, encoding="utf-8")).get("passed") is True
    acceptance = json.load(open(acc_path, encoding="utf-8")) if os.path.exists(acc_path) else "未提供验收摘要（未验收）"
    if not accepted:
        verdict = "GAP_INCONCLUSIVE"
        why = "交付未验收或验收未全过（verification_summary.passed!=true）：" + why

    result = {
        "experiment": "L3_GAP_TARGETED_EXTERNAL",
        "status": "EXECUTED",
        "verdict": verdict,
        "why": why,
        "external_delivery": {
            "evaluator": ext_v.get("evaluator", "第二家异种大模型（外家）"),
            "own_verdict": ext_v.get("verdict"),
            "internal_replay": f"{internal}/{internal_total}（本仓独立重算外家判据vs其gt，不信自报）",
            "acceptance": acceptance,
            "criterion_sha256": __import__("hashlib").sha256(
                open(f"{EXT}/criterion.py", "rb").read()).hexdigest(),
        },
        "mechanical_comparison": {
            "direction": "外家 criterion.py 回放到本仓 §100 冻结样本（claim→text_a, evidence→text_b）",
            "agreement": f"{agree}/{total}",
            "by_variant": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_variant.items())},
            "assertion_family_detected": f"{a_hit}/{a_tot}",
            "numeric_family_detected": f"{n_hit}/{n_tot}",
            "baseline_assertion": prereg["baseline_from_previous_round"]["assertion_family_total"],
            "baseline_numeric": prereg["baseline_from_previous_round"]["numeric_family_total"],
            "per_case": detail,
        },
        "hard_bound": prereg["hard_bound"]["reasons"],
        "l3_claimed": False,
        "absolute_claimed": False,
        "does_not_overturn": prereg["does_not_overturn"],
    }
    json.dump(result, open(EXPERIMENT_RESULT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    after = kernel_state_snapshot()
    assert after == before, f"内核判定态源被子实验裁决污染：{before} -> {after}"
    print(f"verdict={verdict}")
    print(f"external own={ext_v.get('verdict')} internal_replay={internal}/{internal_total}")
    print(f"repo={agree}/{total} assertion={a_hit}/{a_tot} numeric={n_hit}/{n_tot} "
          f"clean={clean[0]}/{clean[1]} canary={canary[0]}/{canary[1]}")
    print(f"l3={result['l3_claimed']} absolute={result['absolute_claimed']}")


if __name__ == "__main__":
    main()
