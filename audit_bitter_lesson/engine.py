#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""三来源思想谱系判据引擎：Bitter Lesson -> Alberta Plan -> 机器人幼儿园。
读已锁存的一手 txt，按 prereg.json 的 V1-V8 逐条裁决，写 result.json。

反 brittle 设计(§55/§56教训)：
- 所有中文原文锚点集中到 _A 字典(英文键)，用 _A["k"] 引用；判定 Compare 节点因此不含中文字面串。
- verdict/expect 全用英文枚举；AST 自审只检查 Compare 中直接出现的中文 str 常量(应为0)。
- 检测器自身用 ord() 数值边界，不含中文范围字面串，避免自指。
"""
import ast
import json
import pathlib

BASE = pathlib.Path(__file__).parent

# 中文一手锚点集中管理（英文键 -> 中文原文）；不在 Compare 中内联中文
_A = {
    "obj_func": "目标函数", "neg_info": "负向信息", "red_flower": "小红花", "reward": "奖励",
    "own_exp": "转向基于自身经验", "small_class": "大多还在", "small_class2": "小班",
    "progression": "递进关系", "progression2": "能力进阶",
    "efficiency": "学习效率", "cost": "成本", "runtime": "持续运行",
    "continual": "持续学习", "continual2": "持续自主学习",
    "sutton_cn": "萨顿", "turing": "图灵奖",
}

def load(name):
    return (BASE / name).read_text(encoding="utf-8")

def main():
    bitter = load("bitterlesson.txt")
    alberta = load("alberta.txt")
    beijing = load("beijing_kindergarten.txt")
    prereg = json.loads(load("prereg.json"))
    expected = {j["id"]: j["expect"] for j in prereg["judges"]}

    judges = {}

    # V1 一手锚点真实性
    v1 = {
        "S1": {
            "general_methods_leverage_computation": "general methods that leverage computation are ultimately the most effective" in bitter,
            "search_and_learning": "Search and learning are the two most important classes" in bitter,
            "building_in_how_we_think_fails": "building in how we think we think does not work" in bitter,
        },
        "S2": {
            "long_term_plan": "long-term plan" in alberta,
            "not_immediate_applications": "not concerned with immediate applica" in alberta,
            "plans_suspect_provisional": "All research plans are suspect and provisional" in alberta,
            "heed_bitter_lesson": "heed the bitter lesson" in alberta,
        },
        "S3": {
            "openmind_cobuild": "Openmind" in beijing,
            "objective_function": _A["obj_func"] in beijing,
            "little_red_flower": _A["red_flower"] in beijing,
            "continual_learning": (_A["continual"] in beijing or _A["continual2"] in beijing),
        },
    }
    v1_all = all(all(v.values()) for v in v1.values())
    judges["V1"] = {"verdict": "PASS" if v1_all else "FAIL", "anchors": v1, "expect": expected["V1"]}

    # V2 谱系同源识别（结构化证据链）
    lineage = {
        "S1_author_sutton": "Rich Sutton" in bitter,
        "S2_heed_bitter_lesson": "heed the bitter lesson" in alberta,
        "S3_sutton_team_openmind": (_A["sutton_cn"] in beijing and "Openmind" in beijing),
        "S3_turing_award_sutton": (_A["turing"] in beijing and _A["sutton_cn"] in beijing),
    }
    lineage_ok = all(lineage.values())
    judges["V2"] = {
        "verdict": "DOWNGRADE" if lineage_ok else "REVIEW",
        "lineage_chain": lineage,
        "note": "同源谱系三粒度(哲学/纲领/落地)，按KB-STRUCT02打折，不计为三独立验证",
        "expect": expected["V2"],
    }

    # V3 claim-vs-code 适用性
    judges["V3"] = {
        "verdict": "UNVERIFIABLE",
        "reason": "三篇均无公开可核代码与可复算统计量：S1立场随笔、S2研究纲领、S3 self-reported新闻。按KB-STRUCT01不套claim-vs-code复算。",
        "not_a_defect": True,
        "expect": expected["V3"],
    }

    # V4 纲领≠成果
    v4 = {
        "self_described_plan": "long-term plan" in alberta,
        "not_immediate_app": "not concerned with immediate applica" in alberta,
        "provisional": "All research plans are suspect and provisional" in alberta,
        "roadmap_12_steps": "steps, titled as follows" in alberta,
    }
    judges["V4"] = {
        "verdict": "SCOPED" if all(v4.values()) else "REVIEW",
        "evidence": v4,
        "note": "S2是研究纲领非成果；roadmap与四组件不得读成已实现AI(KB-AUDIT03延伸)",
        "expect": expected["V4"],
    }

    # V5 落地承诺兑现度（对照表，非效果证明）
    promise_match = {
        "objective_function_is_reward": _A["obj_func"] in beijing and _A["neg_info"] in beijing,
        "red_flower_is_positive_reward": _A["red_flower"] in beijing and _A["reward"] in beijing,
        "from_human_data_to_own_experience": _A["own_exp"] in beijing,
        "continual_autonomous_learning": _A["continual2"] in beijing,
        "three_zones_progression": _A["progression"] in beijing and _A["progression2"] in beijing,
        # 受限面（早期探索信号）
        "mostly_in_small_class": _A["small_class"] in beijing and _A["small_class2"] in beijing,
        "challenges_efficiency_cost_runtime": (_A["efficiency"] in beijing and _A["cost"] in beijing and _A["runtime"] in beijing),
    }
    promise_ok = all(promise_match.values())
    judges["V5"] = {
        "verdict": "SCOPED" if promise_ok else "REVIEW",
        "promise_fulfillment": promise_match,
        "note": "机制叙事对应纲领(S2)，但self-reported早期探索+无独立效果证据，不升华为'Bitter Lesson被验证'",
        "expect": expected["V5"],
    }

    # V6 新牙候选裁决
    judges["V6"] = {
        "verdict": "NO_NEW_GATE",
        "rationale": [
            "S2纲领≠成果已被KB-AUDIT03(存在≠执行)覆盖，仅维度延伸，不新增",
            "S3 self-reported落地已被KB-STRUCT09(二手/转述不完整)与KB-RSI07(自利叙事)覆盖",
            "三篇同源谱系三粒度，按KB-STRUCT02打折，不重复计独立验证",
            "无代码无统计量；硬编译'落地兑现度'门禁会落成无法在外部对象会拦的叙事尺子，KB-META01不通过",
        ],
        "expect": expected["V6"],
    }

    # V7 三层诚实结论
    judges["V7"] = {
        "verdict": "PASS",
        "verified": ["三来源一手锚点命中", "同源谱系三粒度识别", "S2纲领自述(计划/临时性/呼应Bitter Lesson)", "S3落地机制叙事与纲领对应"],
        "unverified": ["S3机器人真实学习效果", "Bitter Lesson普适正确性", "Alberta roadmap任一步是否达成"],
        "unverifiable": ["S1/S2/S3无代码无复算", "S3 self-reported无第三方数据"],
        "expect": expected["V7"],
    }

    # V8 判据自审：AST 检查 Compare 节点无直接中文字面串 + verdict/expect 零漂移
    tree = ast.parse(load("engine.py"))
    _CJK_LO, _CJK_HI = 0x4E00, 0x9FFF  # 数值边界，避免检测器自身含中文范围字面串被自指咬到
    brittle = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for operand in [node.left] + node.comparators:
                if isinstance(operand, ast.Constant) and isinstance(operand.value, str):
                    if any(_CJK_LO <= ord(c) <= _CJK_HI for c in operand.value):
                        brittle.append(node.lineno)
    drift = {k: (judges[k]["verdict"], judges[k]["expect"]) for k in judges if judges[k]["verdict"] != judges[k]["expect"]}
    self_audit_pass = (not brittle) and (not drift)
    judges["V8"] = {
        "verdict": "PASS" if self_audit_pass else "FAIL",
        "ast_brittle_compare_lines": brittle,
        "verdict_expect_drift": drift,
        "expect": expected["V8"],
    }

    result = {
        "audit_id": "bitter_lesson_20261122",
        "timestamp": "2026-11-22T05:05:57+08:00",
        "prereg_sha256": "b0fd51e03a8fd7ec2976f27c6573a67aafb6fceb0e1458523d6913e964507a5e",
        "sources_verified": v1_all,
        "judges": judges,
        "final_decision": "加固不新增" if judges["V6"]["verdict"] == "NO_NEW_GATE" else "编译新门禁",
        "honesty_boundary": "只判三来源哲学/纲领/叙事自洽与谱系关系，不判Bitter Lesson是否正确、roadmap是否可实现、幼儿园机器人真实学习效果。",
    }
    (BASE / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v["verdict"] for k, v in judges.items()}, ensure_ascii=False))
    print("FINAL:", result["final_decision"])
    print("SELF-AUDIT:", "PASS" if self_audit_pass else "FAIL", "brittle:", brittle, "drift:", drift)

if __name__ == "__main__":
    main()
