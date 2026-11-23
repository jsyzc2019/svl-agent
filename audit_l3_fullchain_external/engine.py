#!/usr/bin/env python3
"""本仓侧：对外家全链外置交付的机械比对与裁决（§L3 计划 §4b/§7）。

只读：外家交付副本 + 本仓冻结样本 + 外家 verdict。不改外家任何文件/判据/参数。
裁决树为计划 §7 预注册的定性四档；本仓比对阈值按计划"逐 case 一致"定性语义，
不事后设数值阈值（避免 Goodhart）。l3_claimed 恒 false，由人裁定。
"""
import importlib.util
import json
import os

BASE = "audit_l3_fullchain_external"
EXT = f"{BASE}/received/l3_external_audit"
OWN = "audit_frozen_holdout/downloads/samples.json"


def load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def main():
    ext_v = load(f"{EXT}/verdict.json")
    ext_j = load(f"{EXT}/judgments.json")
    own = load(OWN)["samples"]

    # 1. 外家内部一致性（它自己的判据 vs 它自己的 gt）——采信验收器重跑结果，
    #    这里再独立重算一次作为交叉核验（不信自报）。
    spec = importlib.util.spec_from_file_location("ext_crit", f"{EXT}/criterion.py")
    ec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ec)
    internal = 0
    for r in load(f"{EXT}/samples_blind.json")["pairs"]:
        got = ec.judge(r["text_a"], r["text_b"])
        gotb = bool(got[0]) if isinstance(got, tuple) else bool(got)
        internal += int(gotb == bool(ext_j[r["id"]]["verdict"]))
    internal_total = len(load(f"{EXT}/samples_blind.json")["pairs"])

    # 2. 本仓机械比对：外家判据回放到本仓冻结样本（方向同构，跨判据目标迁移测试）
    by_variant, agree = {}, 0
    detail = []
    for r in own:
        got = ec.judge(r["claim"], r["evidence"])
        gotb = bool(got[0]) if isinstance(got, tuple) else bool(got)
        exp = bool(r["ground_truth_supported"])
        ok = gotb == exp
        agree += int(ok)
        v = r.get("variant", "?")
        a, b = by_variant.get(v, [0, 0])
        by_variant[v] = [a + int(ok), b + 1]
        detail.append({"id": r["id"], "variant": v, "external_judge": gotb,
                       "own_gt": exp, "match": ok})
    total = len(own)

    # 3. 裁决（计划 §7 定性四档）
    #    CONVERGED 须逐 case 一致；PARTIAL = 部分一致部分分歧；
    #    DIVERGENT = 系统性分歧（整体低且无结构）；INCONCLUSIVE = 交付无效。
    if agree == total:
        verdict = "FULLCHAIN_CONVERGED"
        why = "外家判据回放到本仓冻结样本逐 case 一致（含外部锚环境+8/8交付验收）"
    elif agree < total * 0.4 and not any(by_variant.get(v, [0, 1])[0] == by_variant.get(v, [0, 1])[1]
                                         for v in by_variant):
        verdict = "FULLCHAIN_DIVERGENT"
        why = "系统性分歧：整体一致率低且无任一子族全对"
    else:
        verdict = "FULLCHAIN_PARTIAL"
        why = (f"部分一致部分分歧：整体 {agree}/{total}；clean "
               f"{by_variant.get('clean',[0,0])[0]}/{by_variant.get('clean',[0,1])[1]} 全对，"
               f"tampered {by_variant.get('tampered',[0,0])[0]}/{by_variant.get('tampered',[0,1])[1]}，"
               f"canary {by_variant.get('canary',[0,0])[0]}/{by_variant.get('canary',[0,1])[1]}；"
               "外家判据（数值+固定限定词表）与本仓篡改语义（叙述性断言删改）可见面不同")

    result = {
        "experiment": "L3_FULLCHAIN_EXTERNAL",
        "verdict": verdict,
        "why": why,
        "external_delivery": {
            "evaluator": ext_v.get("evaluator") if "evaluator" in ext_v else "Qoder (异种大模型)",
            "own_verdict": ext_v["verdict"],
            "own_agreement": ext_v["metrics"]["agreement"],
            "own_tier_band": ext_v["metrics"]["pre_registered_thresholds"],
            "deliverable_verification": "8/8 PASS（verify_external.py，含承诺时序/零泄漏/gt隔离/判据纯函数/重跑一致/裁决自洽/论文避开/哈希锁）",
            "internal_replay": f"{internal}/{internal_total}（本仓独立重算外家判据vs其gt，不信自报）",
            "own_three_disagreements": "O_UNIT_REEXPRESS 3 组，外家拒绝事后加单位换算补洞（反Goodhart），如实落 PARTIAL",
        },
        "repo_mechanical_comparison": {
            "direction": "外家 criterion.py 回放到本仓 §100 冻结样本（claim→text_a, evidence→text_b）",
            "agreement": f"{agree}/{total}",
            "by_variant": {k: f"{v[0]}/{v[1]}" for k, v in sorted(by_variant.items())},
            "per_case": detail,
            "note": "跨判据目标迁移测试：外家判据在物理化学测量域归纳，本仓样本为 oracle-failures 域；不一致=诚实结果，不改外家判据（tuning 禁止）",
        },
        "hard_bound": ("即便 FULLCHAIN_CONVERGED 也只把五权力同置一次+逐case复现；"
                       "按 §101 无限回归不宣称绝对独立；self-reported 折1；"
                       "rubric R6 全yes只判声明自洽不承诺等级真实；"
                       "本轮实为 FULLCHAIN_PARTIAL，更不宣布 L3/absolute；"
                       "不翻 §107–§115 八案；外家 verdict 不改写。"),
        "l3_claimed": False,
        "absolute_claimed": False,
        "does_not_overturn": [
            "§107 STRATIFIED_CONFIRMED", "§108 CROSS_SET_PARTIAL",
            "§109 EXECUTOR_INDEPENDENCE_CONFIRMED", "§110 CROSS_VENDOR_INCONCLUSIVE",
            "§111 AST_V2_PARTIAL", "§112 CROSS_VENDOR2_PARTIAL",
            "§113 SET_VENDOR2_INCONCLUSIVE", "§114 INTERPRETER_CONFIRMED",
            "§115 INTERPRETER_CROSS_INCONCLUSIVE",
        ],
    }
    with open(f"{BASE}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"verdict={verdict}")
    print(f"external own verdict={ext_v['verdict']} agreement={ext_v['metrics']['agreement']}")
    print(f"internal replay={internal}/{internal_total}")
    print(f"repo comparison={agree}/{total} by_variant={result['repo_mechanical_comparison']['by_variant']}")
    print(f"l3={result['l3_claimed']} absolute={result['absolute_claimed']}")


if __name__ == "__main__":
    main()
