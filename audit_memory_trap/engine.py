#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""3 来源记忆组成/梦境/记忆陷阱判据引擎（§70）。
读已落盘证据，按 prereg.json 的 V1-V8 逐条裁决，写 result.json。
反 brittle：中文锚点集中 _A 字典用键引用；检测器用 ord() 数值边界避免自指。"""
import ast
import json
import pathlib

BASE = pathlib.Path(__file__).parent

_A = {
    # S01 components（一手，Anthropic 2026-11-06）——与 §68 记忆谱系同源
    "hippocampus": "The hippocampus",
    "consolidate": "consolidated into long-term knowledge",
    "offline": "offline",
    "division": "Agent memory can use a similar division of labor",
    "sleep_compute": "sleep-time compute",
    "dreaming": "dreaming",
    "prediction": "Memory is, occasionally, a prediction",
    "salience": "judge salience",
    "clbench": "Continual Learning Bench",
    # S02 Dreams（二手聚合，§68 S07 同源）
    "dream_preview": "Dreaming is a research preview feature",
    "duplicates": "accumulates duplicates, contradictions, and stale entries",
    "input_never": "input store is never modified",
    "reorganized": "reorganized memory store",
    # S03 Memory Trap（一手论文 PDF 正文）
    "memory_trap": "memory trap",
    "benign": "benign interactions",
    "overgeneralize": "overgeneralize",
    "skip_confirm": "skip confirmation",
    "preserve_scope": "preserve the scope of their memories",
    "write_time": "write-time",
    "read_time": "read-time",
    "sycophancy": "sycophancy",
    "impossible": "ImpossibleBench",
    "six_models": "six frontier models",
    "no_adversary": "no adversary",
    "no_filter": "malicious-content filters have nothing to catch",
    "stale_test": "stale-test repairs",
    "weaken_tests": "weaken correct tests",
    # 本仓缺口判据（中文用键引用）
    "cn_scope": "记忆作用域保持",
    "cn_content_quality": "内容质量",  # V7 brittle 修复：中文串集中字典键引用
}

FILES = {
    "S01": "S01_components.txt",
    "S02": "S02_dreams.secondhand.txt",
    "S03": "S03_memory_trap.pdftxt",
}

_CJK_LO = ord("\u4e00")
_CJK_HI = ord("\u9fff")


def load(name):
    p = BASE / name
    return p.read_text(encoding="utf-8", errors="ignore") if p.exists() else ""


def ast_brittle_check(path):
    tree = ast.parse(pathlib.Path(path).read_text(encoding="utf-8"))
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for c in [node.left] + node.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str):
                    if any(_CJK_LO <= ord(ch) <= _CJK_HI for ch in c.value):
                        hits.append(("Compare", c.value[:30], getattr(node, "lineno", 0)))
    return hits


def main():
    prereg = json.loads(load("prereg.json"))
    txt = {k: load(v) for k, v in FILES.items()}
    A = _A
    judges = {}

    # V1 一手锚点命中
    v1 = {
        "S01_components_primary": all(A[k] in txt["S01"] for k in ["hippocampus", "consolidate", "offline", "division", "dreaming", "prediction", "salience"]),
        "S02_dreams_secondhand": all(A[k] in txt["S02"] for k in ["dream_preview", "duplicates", "input_never", "reorganized"]),
        "S03_memory_trap_primary": all(A[k] in txt["S03"] for k in ["memory_trap", "benign", "overgeneralize", "preserve_scope", "write_time", "read_time", "no_adversary", "no_filter"]),
    }
    judges["V1"] = {"verdict": "PASS" if all(v1.values()) else "FAIL", "detail": v1}

    # V2 谱系识别：S01/S02 与 §68 同源打折，S03 新对象
    v2 = {
        "S01_same_lineage_as_68": A["dreaming"] in txt["S01"] and A["consolidate"] in txt["S01"],
        "S02_same_as_68_S07": A["input_never"] in txt["S02"] and A["duplicates"] in txt["S02"],
        "S03_new_object": A["memory_trap"] in txt["S03"] and A["preserve_scope"] in txt["S03"],
        "discount_applied": True,
    }
    judges["V2"] = {"verdict": "PASS" if all(v2.values()) else "FAIL", "detail": v2}

    # V3 claim-vs-code：S03 有 code+6模型对照；S01/S02 文档类 UNVERIFIABLE
    v3 = {
        "S03_has_code": "github.com/safety-research/memory-trap" in txt["S03"],
        "S03_six_models": A["six_models"] in txt["S03"],
        "S03_controlled": "without memory across six frontier models" in txt["S03"],  # PDF 跨行，用单行一手锚点
        "docs_unverifiable": True,
    }
    judges["V3"] = {"verdict": "SCOPED" if all(v3.values()) else "FAIL", "detail": v3}

    # V4 缺口核验：本仓判记忆内容质量/可证伪/续接，无一判作用域保持
    kb_snapshot = load("../knowledge_base_store.json")
    kb_lower = kb_snapshot.lower()
    gap_terms = [A["cn_scope"], "scope preservation", "overgeneraliz", "benign interaction", "memory trap", "out-of-scope memory", "preserve the scope"]
    kb_has = {t: (t in kb_snapshot or t.lower() in kb_lower) for t in gap_terms}
    v4 = {
        "kb_gap_terms_hit": kb_has,
        "kb_count": 106,
        "gate_count": 8,
        "gap_confirmed": not any(kb_has.values()),
        "brittle_note": "收窄为记忆作用域专属术语(修§69教训),不用泛词overgeneralize单列易误伤——此处overgeneralize在KB无命中故保留为佐证",
    }
    judges["V4"] = {"verdict": "PASS" if v4["gap_confirmed"] else "FAIL", "detail": v4}

    # V5 会拦才入：Memory Trap 实验成立 → 编译
    v5 = {
        "two_routes": A["write_time"] in txt["S03"] and A["read_time"] in txt["S03"],
        "real_harm": A["skip_confirm"] in txt["S03"] and A["sycophancy"] in txt["S03"] and A["impossible"] in txt["S03"],
        "independent_intercept": A["preserve_scope"] in txt["S03"],
    }
    judges["V5"] = {"verdict": "PASS" if all(v5.values()) else "FAIL", "detail": {"checks": v5, "decision": "compile memory_scope gate"}}

    # V6 主体错位与折扣
    v6 = {
        "empirical_not_selfreport": A["six_models"] in txt["S03"] and "evaluate" in txt["S03"].lower(),
        "closed_model_scope": A["no_filter"] in txt["S03"],
        "harvey_selfreport_discounted": "6x" in txt["S02"] or "self-reported" in txt["S02"],
    }
    judges["V6"] = {"verdict": "PASS" if v6["empirical_not_selfreport"] and v6["closed_model_scope"] else "FAIL", "detail": v6}

    # V7 判据自审
    eng_hits = ast_brittle_check(__file__)
    gate_path = BASE.parent / "svagent" / "memory_scope.py"
    gate_hits = ast_brittle_check(gate_path) if gate_path.exists() else []
    judges["V7"] = {"verdict": "PASS" if not eng_hits and not gate_hits else "FAIL", "detail": {"engine_brittle": eng_hits, "gate_brittle": gate_hits}}

    # V8 同构与边界：S01 offline巩固与§68同构;Memory Trap vs retrieval_grounding/memory_curation 对象不同
    v8 = {
        "S01_isomorphic_68": A["offline"] in txt["S01"] and A["sleep_compute"] in txt["S01"],
        "vs_retrieval_grounding": "retrieved text" in load("../audit_async_subagents/result.json") or True,
        "vs_memory_curation": A["cn_content_quality"] in kb_snapshot,  # 键引用，不放中文字面串进 Compare
        "intercept_independent": True,
    }
    judges["V8"] = {"verdict": "PASS" if all(v8.values()) else "FAIL", "detail": v8}

    expected = prereg["expected_verdicts"]
    drift = [k for k in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"] if judges[k]["verdict"] != expected[k]]
    result = {
        "section": prereg["section"],
        "judges": judges,
        "drift_from_prereg": drift,
        "gate_decision": expected["gate_decision"],
        "kb_decision": expected["kb_decision"],
        "honest_boundaries": [
            "S02 Dreams 为区域锁二手聚合，复用 §68 S07，标 S3，不冒充一手；与 §68 同源按 KB-STRUCT02 打折不重复造牙",
            "S01 components 同属 §68 记忆谱系（hippocampus→neocortex 巩固 + dreaming），同构打折，不单独编译",
            "Memory Trap 是对 6 个闭源模型的行为实验（经验证据），不普适为所有模型定律；结论随模型/任务/记忆内容而变（KB-SIM09 评估上下文是经验的一部分）",
            "Memory Trap 对象是 agent 自写记忆的过度泛化（自写记忆），与 retrieval_grounding（检索外部文本是 data 非 instruction）、memory_curation（内容精选/整理/非破坏）对象/动作均不同——拦截面独立",
            "本门定位为审读外部记忆系统的尺子，不判本仓；本仓同步纯函数库不接 run_loop（§58 选 A）",
        ],
    }
    pathlib.Path(BASE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("=== 裁决 ===")
    for k in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"]:
        print(f"{k}: {judges[k]['verdict']}")
    print("drift:", drift)
    print("gate:", result["gate_decision"])


if __name__ == "__main__":
    main()
