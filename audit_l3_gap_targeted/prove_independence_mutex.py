#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§L3 canary 诊断收尾：用两家【真实外家判据源码】A级实证"独立性⇔冻结集完美拟合"互斥。

【本轮增量（继 §4al U型/单调12-18、§4am 两特征OR18-18 之后的收尾）】
前两轮用的是本仓【合成判据】。本轮直接 import 两家外家交付的真实 criterion.py：
  - Qoder（audit_l3_fullchain_external）：数值+限定词一致性，159 行；
  - 智谱（audit_l3_gap_targeted/received/l3_external_audit_v2）：三层词类多重集，86 行。
两家框架完全不同。冻结集回放基线均 11/18。给每家叠加【纯 post-hoc 的构造签名补丁】：
  - canary 端补丁：content_diff>9.5 OR jaccard<0.24 → True
  - tampered 端补丁：0.24<=jaccard<=0.96 → False
结果：单一 canary 补丁只到 Qoder 14/18、智谱 17/18（tampered 端仍独立错位）；
两端补丁后两家都 18/18。

【结论（A级实证，核心不变）】
1. 两家框架不同却都能被同一组 post-hoc 补丁拉满 → 失败与判据族复杂度无关；
2. 单一补丁不够、必须双端 → 两家在 clean/canary 端和 tampered 端各有残留错位，
   昨日"单调框架只抓一端"的说法过于简化（§4am 已部分修正，本轮进一步精确）；
3. 这些补丁阈值全部取自看过标签的三簇鸿沟 → 【判据独立性】与【冻结集完美拟合】
   信息论互斥的铁证：真正独立的设计方（没看本仓标签）不可能设计出这组阈值；
4. 两家回放 11/18 是上述互斥的必然结果，不是它们"不够聪明"或某框架缺陷；
   靠 post-hoc 补丁翻案=Goodhart，纪律禁止。

【纪律】纯诊断：import 判据源码但不改它；只读 §100 冻结样本；不改任何 verdict；
       不触冻结集；l3/absolute 保持 false；补丁仅诊断演示，不作裁决输入；最终裁定权在用户。

运行：python3.11 audit_l3_gap_targeted/prove_independence_mutex.py
"""
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import prove_canary_unreachability as P

QODER_C = os.path.join(ROOT, "audit_l3_fullchain_external", "received",
                       "l3_external_audit", "criterion.py")
ZHIPU_C = os.path.join(HERE, "received", "l3_external_audit_v2", "criterion.py")


def _load_criterion(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _verdicts(mod, rows):
    return {r["id"]: bool(mod.judge(r["claim"], r["evidence"])[0]) for r in rows}


def _score(pred, gt):
    return sum(pred[i] == gt[i] for i in gt)


def _canary_patch(feat):
    return feat["content_diff"] > 9.5 or feat["jaccard_sim"] < 0.24


def _tampered_patch(feat):
    return 0.24 <= feat["jaccard_sim"] <= 0.96


def build_report(rows=None):
    rows = rows if rows is not None else P.load()
    raw = json.load(open(os.path.join(ROOT, "audit_frozen_holdout", "downloads",
                                      "samples.json"), encoding="utf-8"))["samples"]
    feat = {r["id"]: P.features(r) for r in raw}
    gt = {r["id"]: r["gt"] for r in rows}

    criteria = {
        "Qoder(数值+限定词,159行)": _load_criterion(QODER_C, "_qoder_c"),
        "智谱(三层词类多重集,86行)": _load_criterion(ZHIPU_C, "_zhipu_c"),
    }
    results = {}
    for name, mod in criteria.items():
        base = _verdicts(mod, raw)
        p_canary = {i: (base[i] or _canary_patch(feat[i])) for i in gt}
        p_both = {i: ((base[i] or _canary_patch(feat[i])) and not _tampered_patch(feat[i]))
                  for i in gt}
        results[name] = {
            "framework_lines": len(open(QODER_C if "Qoder" in name else ZHIPU_C,
                                        encoding="utf-8").readlines()),
            "baseline": _score(base, gt),
            "plus_canary_patch": _score(p_canary, gt),
            "plus_both_patches": _score(p_both, gt),
            "baseline_errors": [i for i in gt if base[i] != gt[i]],
        }

    report = {
        "boundary": "纯诊断；import两家真实判据源码但不改；只读§100冻结样本；不改verdict/冻结集；"
                    "l3/absolute仍false；post-hoc补丁仅诊断演示，不作裁决输入、不可翻案。",
        "method": "把两家外家真实 criterion.py 回放到§100冻结18样本，"
                  "再叠加纯post-hoc构造签名补丁(canary端content_diff>9.5 OR jaccard<0.24→True; "
                  "tampered端0.24<=jaccard<=0.96→False)，量化局部补丁天花板。",
        "results": results,
        "key_finding": "两家框架完全不同、基线均11/18；叠加同一组post-hoc双端补丁后都达18/18；"
                       "单一canary补丁不足以满血(Qoder14/18、智谱17/18)，tampered端仍独立错位。",
        "refined_conclusion": [
            "两家框架不同却都能被同一组post-hoc补丁拉满 → 失败与判据族复杂度无关。",
            "单一补丁不够、必须双端 → 两家在canary端与tampered端各有残留错位，"
            "昨日'单调框架只抓一端'过于简化，本轮用真实判据进一步精确。",
            "补丁阈值全部取自看过标签的三簇鸿沟 → 【判据独立性】与【冻结集完美拟合】"
            "信息论互斥的铁证：真正独立方(未见本仓标签)不可能设计出这组阈值。",
            "两家回放11/18是上述互斥的必然结果，非判据不聪明或框架缺陷；"
            "post-hoc补丁翻案=Goodhart禁止；verdict保持GAP_INCONCLUSIVE，l3/absolute保持false。",
        ],
        "does_not_change": ["verdict=GAP_INCONCLUSIVE", "l3=false", "absolute=false",
                            "不翻十案", "不编译新门禁", "不动§100冻结样本", "不改两家判据源码"],
    }
    return report


def main():
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
