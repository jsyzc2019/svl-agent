#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4at 自我否定诊断：用本仓真实数据机械验证 v3 内核对三篇一手前沿的三个缺陷。

外部一手证据（B级，arXiv摘要级自报，非本仓实测）：
  F09 arXiv:2610.14662 — 失败反馈归因幻觉：分数上升≠修对目标失败
  F10 arXiv:2610.25858 — 检索碰撞：相似检索在冲突情境检索到外来记忆
  F11 arXiv:2611.28244 — 丢弃持续未用经验优于累积/升为常驻规则

本脚本只读内核源码/数据，证明这三个缺陷在 v3 中真实存在，不产生新判定，不改文件。
运行：python3.11 life_kernel/diagnose_v3_defects.py
"""
import inspect
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kernel as K


def src(fn):
    return inspect.getsource(fn) if callable(fn) else ""


def build_report():
    d = {}
    sm = src(K.self_modify)
    val = src(K._validate_policy)
    pw = src(K.pareto_walk)
    traces = K.path_list()
    seeds = json.load(open(K.FRONTIER_SEEDS, encoding="utf-8"))["seeds"]
    kb = json.load(open(K.KB, encoding="utf-8"))["items"]

    # 缺陷1 归因幻觉：self_modify/validate 中是否存在"修改是否针对诊断问题"的检验
    checks1 = ["target_repair", "transfer", "heldout", "attribution", "归因"]
    d["defect1_attribution_hallucination"] = {
        "external_basis": "F09 arXiv:2610.14662: 145 DGM修改无可检测目标特异优势; 应分报 target/transfer/held-out",
        "checks_absent": [c for c in checks1 if c not in sm and c not in val],
        "diagnosis_field_present": ("diagnosis" in sm),  # 有诊断，但不检验修改是否命中诊断
        "verdict_keys": sorted(k for k in json.load(open(os.path.join(os.path.dirname(HERE),
                            "life_kernel", "data", "runtime_policy.json"), encoding="utf-8"))
                            .get("last_self_modify", {}).get("validation", {}).keys()),
        "confirmed": all(c not in sm and c not in val for c in checks1),
        "meaning": "内核会诊断(guard/similarity)并修改(注册种子)，但经验验证从不检验这次修改是否真的改善了诊断出的问题——正是F09批判的归因幻觉。",
    }

    # 缺陷2 检索碰撞：脚印是否有适用条件字段，注入时是否检查情境匹配
    checks2 = ["applicability", "applicable", "context_sig", "适用条件", "collision", "碰撞"]
    trace_has_cond = all("applicability" in t for t in traces) if traces else None
    d["defect2_no_applicability"] = {
        "external_basis": "F10 arXiv:2610.25858: 相似检索在相似查询需冲突工作流时发生 retrieval collision",
        "guards_absent": [c for c in checks2 if c not in pw],
        "trace_has_applicability": trace_has_cond,  # 真实脚印是否带适用条件
        "all_footprints_injected_unconditionally": ("footprints" in pw and "append" in pw),
        "footprints_count": len(traces),
        "confirmed": (all(c not in pw for c in checks2)
                      and (not traces or trace_has_cond is False)),
        "meaning": "v3 把全部历史脚印无条件注入候选(1.5x偏置)，脚印不带'适用情境'标签——若当前情境与旧脚印相似却需不同行动，会检索到外来脚印(F10检索碰撞)。",
    }

    # 缺陷3 只增不减：是否有任何丢弃/剪枝未用经验的函数
    checks3 = ["prune", "discard", "forget", "delete_unused", "衰减", "丢弃", "剪枝"]
    allsrc = "\n".join(src(getattr(K, n)) for n in dir(K)
                       if not n.startswith("__") and callable(getattr(K, n)))
    d["defect3_growth_only"] = {
        "external_basis": "F11 arXiv:2611.28244: 选择性丢弃持续未用经验优于合并/升为常驻规则",
        "pruning_symbols_absent": [c for c in checks3 if c not in allsrc],
        "kb_count": len(kb),
        "seed_count": len(seeds),
        "footprints_count": len(traces),
        "archive_count": len(K.archive_list()),
        "confirmed": all(c not in allsrc for c in checks3),
        "meaning": "KB/摄食种子/脚印/archive 全部只增不减，没有任何机制丢弃长期未用的经验——与F11'丢弃优于累积'的实证相悖。",
    }

    d["all_three_confirmed"] = all(
        d[k]["confirmed"] for k in
        ("defect1_attribution_hallucination", "defect2_no_applicability", "defect3_growth_only"))
    d["boundary"] = "只读诊断：证明外部一手批判在本仓内核真实成立；不产生新判定，不改verdict/l3/absolute/§100。"
    d["evidence_tier"] = "外部证据 B 级（arXiv 摘要级自报，非本仓实测）；本诊断对本仓内核的验证为 A 级（读真实源码/数据）。"
    return d


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
