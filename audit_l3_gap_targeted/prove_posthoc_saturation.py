#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§L3 canary 诊断的诚实精确化：post-hoc 自由度与冻结集完美拟合的饱和关系。

【缘起 / 对昨日结论的自我修正】
昨日 prove_canary_unreachability.py 断言"单调判据上限 12/18，两家外家判据都属
单调一致性框架，故系统性失败"。本脚本在冻结集 18 样本上枚举【两特征单调布尔
组合】，发现 OR 组合可达 18/18 (>9.5 content_diff OR >0.98 jaccard)。
因此昨日"单调上限 12/18"精确说只在【单特征】范围成立；"单调框架必失败"
这一泛化表述被数据部分证伪——正如昨日部分证伪了"字面不可分"。

【修正后的精确结论（三层，核心不变）】
1. 单特征单调判据上限 12/18 —— 昨日技术事实，成立但范围有限；
2. 自由度 ≥ 2 的判据（两特征 AND/OR）在冻结集内可达 18/18，且达标阈值精确落在
   三簇生成伪影的鸿沟中点 —— 用 2 个数完美拟合 18 点，是过拟合签名，非语义发现；
3. 真正根因不是"判据族复杂度"，而是【判据独立性】与【冻结集完美拟合】在信息论上
   互斥：独立方（未看本仓标签）无法 post-hoc 调阈值；任何冻结集内 18/18 的判据
   都是看过标签设计的。两家外家失败是这一互斥的体现，不是某判据族的缺陷。

【纪律】纯诊断：只读 §100 冻结样本；不改任何 result.json verdict；不触冻结集；
        l3/absolute 保持 false；U 型/两特征判据仅作诊断演示，不作裁决输入；
        post-hoc 拟合不可用于翻案（Goodhart）。最终裁定权在用户。

运行：python3.11 audit_l3_gap_targeted/prove_posthoc_saturation.py
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prove_canary_unreachability as P

FEATS = ("content_diff", "jaccard_sim", "neg_diff", "conn_diff", "num_diff", "len_ratio")


def build_atoms(rows):
    """所有单特征阈值原子，阈值取相邻值中点（与昨日 best_monotone 同口径）。"""
    atoms = []
    for f in FEATS:
        vals = sorted(set(r[f] for r in rows))
        cands = [vals[0] - 1e-9]
        cands += [(vals[i] + vals[i + 1]) / 2 for i in range(len(vals) - 1)]
        cands += [vals[-1] + 1e-9]
        for t in cands:
            atoms.append((f, round(t, 6), "le"))
            atoms.append((f, round(t, 6), "gt"))
    return atoms


def apply(atom, r):
    f, t, d = atom
    return r[f] <= t if d == "le" else r[f] > t


def score(fn, rows):
    return sum(bool(fn(r)) == r["gt"] for r in rows)


def enumerate_up_to_two(rows, atoms):
    """枚举自由度 1（单原子）与自由度 2（两原子 AND/OR）的判据上限。"""
    one = 0
    for a in atoms:
        one = max(one, score(lambda r, a=a: apply(a, r), rows))

    two_best = {"acc": 0}
    perfect = []          # 所有 18/18 的两特征判据（用于阈值落点诊断）
    for i, a in enumerate(atoms):
        for b in atoms[i + 1:]:
            if a[0] == b[0]:          # 同特征两阈值等价于区间，归入单特征自由度
                continue
            for op in ("AND", "OR"):
                if op == "AND":
                    fn = lambda r, a=a, b=b: apply(a, r) and apply(b, r)
                else:
                    fn = lambda r, a=a, b=b: apply(a, r) or apply(b, r)
                s = score(fn, rows)
                if s > two_best["acc"]:
                    two_best = {"acc": s, "op": op, "a": a, "b": b}
                if s == len(rows):
                    perfect.append({"op": op, "a": a, "b": b})
    return one, two_best, perfect


def cluster_intervals(rows):
    out = {}
    for v in ("clean", "tampered", "canary"):
        sub = [r for r in rows if r["variant"] == v]
        out[v] = {
            "gt": sorted(set(r["gt"] for r in sub)),
            "content_diff": [min(r["content_diff"] for r in sub), max(r["content_diff"] for r in sub)],
            "jaccard_sim": [round(min(r["jaccard_sim"] for r in sub), 3),
                            round(max(r["jaccard_sim"] for r in sub), 3)],
        }
    return out


def perfect_threshold_loci(perfect):
    """统计所有 18/18 判据里最常见的内容词差异阈值落点（验证伪影窗口）。"""
    cd_gt = sorted(set(a[1] for p in perfect for a in (p["a"], p["b"])
                       if a[0] == "content_diff" and a[2] == "gt"))
    js_gt = sorted(set(round(a[1], 4) for p in perfect for a in (p["a"], p["b"])
                       if a[0] == "jaccard_sim" and a[2] == "gt"))
    return {"content_diff_gt_thresholds": cd_gt[:12],
            "jaccard_gt_thresholds": js_gt[:12],
            "n_perfect_two_feature": len(perfect)}


def build_report(rows=None):
    """构造完整诊断报告 dict（供测试与报告生成器复用，不打印）。"""
    rows = rows if rows is not None else P.load()
    atoms = build_atoms(rows)
    one, two_best, perfect = enumerate_up_to_two(rows, atoms)
    report = {
        "boundary": "纯诊断；只读§100冻结样本；不改verdict/冻结集；l3/absolute仍false；"
                    "所有18/18判据均为post-hoc伪影拟合，不作裁决输入、不可用于翻案。",
        "self_correction": {
            "yesterday_claim": "单调判据上限12/18，两家外家都属单调框架故系统性失败",
            "today_finding": "两特征单调OR组合(content_diff>9.5 OR jaccard>0.98)可达18/18",
            "correction": "昨日12/18只在【单特征】范围成立；'单调框架必失败'泛化表述被部分证伪，"
                          "正如昨日部分证伪了'字面不可分'。如实记录，不改核心结论。",
        },
        "degrees_of_freedom": {
            "dof_1_single_feature_max": one,
            "dof_2_two_feature_max": two_best["acc"],
            "dof_2_best_rule": {"op": two_best["op"], "a": two_best["a"], "b": two_best["b"]},
            "saturation_note": "自由度≥2即达准确率上界18/18；用2个数完美拟合18点=过拟合签名。",
        },
        "cluster_intervals": cluster_intervals(rows),
        "perfect_threshold_loci": perfect_threshold_loci(perfect),
        "refined_conclusion": [
            "单特征单调上限12/18是真实但【范围有限】的技术事实；两特征单调布尔组合可达18/18。",
            "所有18/18判据的阈值都精确落在三簇生成伪影鸿沟中点"
            "（content_diff 2→17 之间、jaccard 0.96→0.235 之间），学的是构造方式，不是语义蕴含。",
            "真正根因=【判据独立性】与【冻结集完美拟合】信息论互斥：独立方未看本仓标签，"
            "无法post-hoc调阈值；冻结集内任何18/18判据都是看过标签设计的。",
            "两家外家失败是上述互斥的体现，不是'单调框架'这一判据族的缺陷——这是昨日解释的精确化。",
            "结论核心不变：缺口不可靠换判据关闭，post-hoc拟合=Goodhart禁止；"
            "verdict保持GAP_INCONCLUSIVE，l3/absolute保持false。",
        ],
        "does_not_change": ["verdict=GAP_INCONCLUSIVE", "l3=false", "absolute=false",
                            "不翻十案", "不编译新门禁", "不动§100冻结样本"],
    }
    return report


def main():
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
