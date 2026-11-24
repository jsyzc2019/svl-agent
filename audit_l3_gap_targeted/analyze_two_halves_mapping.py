#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§L3 外部前沿交叉印证：SLAN"两半拼图"与本仓两轮外家判据的能力映射。

纪律边界（务必先读）：
- 本脚本是【诊断性陈述归纳】，不产生任何新判定，不改任何 result.json 的 verdict。
- 只读本仓两份真实 received 判据源码 + 复现 §100 冻结样本的内容词差异诊断（analyze_canary_orthogonality.py）。
- "选择性/全局检索"的映射是【解释性类比】（证据等级 B/C），不是本仓实测因果；
  本仓硬证据仍是 A 级：断言 4/4、数值 1/2、canary 0/6、整体 11/18。
- 输出供 L3 方法论层交叉印证使用，禁止据此改阈值/翻案/触 §100 冻结集。

运行：python3.11 audit_l3_gap_targeted/analyze_two_halves_mapping.py
"""
import ast
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = os.path.dirname(os.path.abspath(__file__))

QODER = os.path.join(ROOT, "audit_l3_fullchain_external", "received",
                     "l3_external_audit", "criterion.py")
ZHIPU = os.path.join(ROOT, "audit_l3_gap_targeted", "received",
                     "l3_external_audit_v2", "criterion.py")


def static_features(path):
    """从判据源码静态提取可核验特征（不改源码、不执行判据逻辑）。"""
    src = open(path, encoding="utf-8").read()
    tree = ast.parse(src)
    funcs = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    # 顶层常量集合（frozenset/set/tuple Assign）
    consts = {}
    for n in tree.body:
        if isinstance(n, ast.Assign) and len(n.targets) == 1 and isinstance(n.targets[0], ast.Name):
            name = n.targets[0].id
            try:
                val = ast.literal_eval(n.value)
                if isinstance(val, (set, frozenset, tuple, list)):
                    consts[name] = len(val)
            except Exception:
                pass
    return {
        "path": os.path.relpath(path, ROOT),
        "lines": len(src.splitlines()),
        "functions": funcs,
        "literal_collections": consts,
        "has_numeric_parse": any(k in funcs for k in ("_numeric_literals", "_value_of", "_is_numeric_literal")),
        # 全局多重集：函数名按两家实际实现兼容（智谱=_multiset_diff/_tokens，Qoder 无）
        "has_global_multiset": any("multiset" in k or k in ("content", "mdiff", "toks", "_tokens", "_diff_list")
                                   for k in funcs),
        "has_neg_conn_sets": any(k.startswith("NEG") or k.startswith("CONN") or k.startswith("FUNC")
                                 for k in consts),
    }


def canary_separation():
    """复现 §100 冻结样本三簇内容词差异（直接调用已锚诊断脚本，不重写逻辑）。"""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "diag", os.path.join(BASE, "analyze_canary_orthogonality.py"))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    samples = json.load(open(os.path.join(ROOT, "audit_frozen_holdout", "downloads", "samples.json"),
                             encoding="utf-8"))["samples"]
    by = {}
    for r in samples:
        cd = m.mdiff(m.content(r["claim"]), m.content(r["evidence"]))
        by.setdefault(r["variant"], []).append(cd)
    return {
        "clean": by["clean"],
        "tampered": by["tampered"],
        "canary": by["canary"],
        "gap": min(by["canary"]) - max(by["tampered"]),
        "separated": min(by["canary"]) > max(by["tampered"]),
    }


def main():
    q = static_features(QODER)
    z = static_features(ZHIPU)
    sep = canary_separation()

    # 硬证据（A 级，来自本仓 result.json，不手抄）
    res = json.load(open(os.path.join(BASE, "result.json"), encoding="utf-8"))
    mc = res["mechanical_comparison"]

    report = {
        "boundary": "诊断性陈述归纳；不产生新判定、不改 verdict、不触 §100 冻结集；"
                    "选择性/全局检索映射为解释性类比(B/C级)，非本仓实测因果。",
        "evidence_grade": {
            "A_本仓实测": {"assertion": mc["assertion_family_detected"],
                          "numeric": mc["numeric_family_detected"],
                          "canary": mc["by_variant"]["canary"],
                          "overall": mc["agreement"]},
            "B_解释性类比": "SLAN 数学洞察(选择性遗忘×全局检索两半拼图)↔两家判据能力取向",
            "C_二级背景": "时序人公众号转述 ESWA 2026 论文；alphaXiv 作者自报与观察性结论",
        },
        "two_halves_mapping": {
            "Qoder_阿里": {
                "static_features": q,
                "orientation": "选择性过滤路径：数值字面量解析 + 封闭限定词表，"
                               "只盯特定标记(类比 SLAN 的 input-dependent selective forgetting)",
                "observed": {"numeric": "2/2", "assertion": "0/4", "canary": "3/6"},
                "missing_half": "无全局内容词检索——跨句/断言结构不在可见面",
            },
            "Zhipu_智谱": {
                "static_features": z,
                "orientation": "全局检索路径：否定/连接/内容词三层多重集比对，"
                               "对全部词类做集合匹配(类比 SLAN 的 global retrieval)",
                "observed": {"numeric": "1/2", "assertion": "4/4", "canary": "0/6"},
                "missing_half": "无选择性遗忘——无差别比对使跨句蕴含样本(内容词不重叠)全误判",
            },
            "slan_insight": "线性注意力=遗忘门恒为1的选择性SSM；两家各持一半，"
                            "SLAN 证明缺一不可(只检索不遗忘 ILI MSE 1.711→2.465)。"
                            "两家镜像互补却都在 canary 栽，与该架构结论形成能力层类比。",
        },
        "canary_separation": sep,
        "conclusion": [
            "A级硬证据不变：断言4/4(基线0/4突破)、数值1/2、canary0/6、整体11/18。",
            "解释性类比：两家各持'选择性过滤/全局检索'一半，与 SLAN 两半拼图同构；"
            "canary 是两家共同盲区，对应'缺另一半'+'任务说明书缺失'。",
            "元信息引导(三层模板把分布/平稳性/结构断点写成文本喂冻结LLM)↔ 第⑤类任务异质性："
            "解法方向是给判据'任务说明书'而非加词表；此诊断落方法论层，不触 verdict/§100。",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
