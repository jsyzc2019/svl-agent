#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
§4S4 验证引擎 —— 纯函数、不联网、不 spawn、不编译门禁。
验证三件事：
  G1 定义原话完整落档（用户 13:03 原话逐字在 result.json 与 handoff）
  G2 三要素 E1/E2/E3 + 两失败模式齐备
  G3 实证对话真实（每轮带服务端 completion id，无伪造占位）
只读，不改任何文件。判定权归用户。
"""
import json, os, hashlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

VERBATIM = "交流需要向对方表达己方的意图，然后对方能洞悉你的意图，此后双方根据洞悉的意图相应行动，否则就成了对牛弹琴或ga聊"
VERBATIM2 = "交流是需技巧的，通过交流你掌握并提升认知和情感"
VERBATIM3 = "你再精心设计话题，不要直接曝露你的意图"
VERBATIM4 = "对话能层层推进，靠的是Diff双方意图，否则一聊就死。当然，坦诚也是美德。"
VERBATIM5 = "同意你的做法"
VERBATIM6 = "采纳你的循环版建议。谈崩，虽然没有实现的目标，但双方是有收获的。"
VERBATIM7 = "双方经交流明白了各自底线，据此可采取新的行动，而不是不明旧里持续蛮干"

def _load(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)

def verify():
    checks = {}

    # G1 定义原话：result.json 与 handoff 都要逐字命中
    res = _load(os.path.join(HERE, "result.json"))
    ud = res.get("user_definition_of_communication", {})
    g1_res = VERBATIM in ud.get("verbatim", "")
    handoff = open(os.path.join(ROOT, "SESSION_HANDOFF.md"), encoding="utf-8").read()
    g1_hand = VERBATIM in handoff
    checks["G1_原话落档"] = {
        "ok": g1_res and g1_hand,
        "result_json": g1_res,
        "handoff": g1_hand,
    }

    # G2 三要素 + 两失败模式
    els = [e.get("id") for e in ud.get("three_elements", [])]
    modes = [m.get("name") for m in ud.get("failure_modes", [])]
    g2 = els == ["E1", "E2", "E3"] and "对牛弹琴" in modes and "尬聊" in modes
    checks["G2_三要素与失败模式"] = {
        "ok": g2, "elements": els, "failure_modes": modes,
    }

    # G3 实证对话真实性：四轮/交叉/定义三份文件，每轮带 id 且非占位
    files = ["dialogue_raw.json", "crosscheck_raw.json", "definition_dialogue.json"]
    g3_detail = {}
    all_ok = True
    for f in files:
        d = _load(os.path.join(HERE, f))
        turns = d.get("turns", [])
        real = [t for t in turns if t.get("id") and not t.get("a", "").startswith("<")]
        ok = len(real) == len(turns) and len(turns) > 0
        g3_detail[f] = {"turns": len(turns), "real": len(real), "ok": ok}
        all_ok &= ok
    checks["G3_实证对话真实"] = {"ok": all_ok, "files": g3_detail}

    # 判定态未动（只读核验）
    jr = _load(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"))
    judged = (jr.get("verdict") == "GAP_INCONCLUSIVE"
              and jr.get("l3_claimed") is False
              and jr.get("absolute_claimed") is False)
    checks["G4_判定态未动"] = {
        "ok": judged,
        "verdict": jr.get("verdict"),
        "l3": jr.get("l3_claimed"),
        "absolute": jr.get("absolute_claimed"),
    }

    # G5 能力/价值层补充原话落档（技巧 + 认知/情感增益）
    skill = res.get("communication_as_skill_and_growth", {})
    g5_res = VERBATIM2 in skill.get("verbatim", "")
    g5_hand = VERBATIM2 in handoff
    ops = skill.get("operationalized", {})
    g5_ops = all(k in ops for k in ["S1_技巧性", "V1_认知增益", "V2_情感增益"])
    checks["G5_技巧与增益落档"] = {
        "ok": g5_res and g5_hand and g5_ops,
        "result_json": g5_res, "handoff": g5_hand,
        "three_layers": g5_ops,
    }

    # G6 含蓄话题练习落档
    subtle = res.get("subtle_dialogue_practice", {})
    g6_res = VERBATIM3 in subtle.get("verbatim", "")
    g6_hand = VERBATIM3 in handoff
    a = _load(os.path.join(HERE, "subtle_A.json"))
    b = _load(os.path.join(HERE, "subtle_B.json"))
    ra = [t for t in a.get("turns", []) if t.get("id")]
    rb = [t for t in b.get("turns", []) if t.get("id")]
    g6_real = len(ra) == 3 and len(rb) >= 1
    checks["G6_含蓄练习落档"] = {
        "ok": g6_res and g6_hand and g6_real,
        "result_json": g6_res, "handoff": g6_hand,
        "agent_A_real_turns": len(ra), "agent_B_real_turns": len(rb),
    }

    # G7 Diff 动力学层落档（§4S5）
    diff = res.get("diff_drives_dialogue", {})
    g7_res = VERBATIM4 in diff.get("verbatim", "")
    g7_hand = VERBATIM4 in handoff
    props = [p.get("id") for p in diff.get("propositions", [])]
    g7_props = props == ["D1", "D2", "D3"]
    dd = _load(os.path.join(HERE, "diff_dialogue.json"))
    dd_turns = dd.get("turns", [])
    dd_real = [t for t in dd_turns if t.get("id") and not t.get("a", "").startswith("<")]
    g7_real = len(dd_real) == len(dd_turns) == 3
    # 预注册哈希自洽（先于证据）
    prereg_path = os.path.join(ROOT, "prereg_diff_dialogue_20261127.json")
    sha_path = os.path.join(ROOT, "prereg_diff_dialogue_20261127.sha256")
    g7_prereg = False
    if os.path.exists(prereg_path) and os.path.exists(sha_path):
        actual = hashlib.sha256(open(prereg_path, "rb").read()).hexdigest()
        g7_prereg = actual == open(sha_path).read().strip()
    checks["G7_Diff动力学落档"] = {
        "ok": g7_res and g7_hand and g7_props and g7_real and g7_prereg,
        "result_json": g7_res, "handoff": g7_hand,
        "propositions": props, "diff_dialogue_real_turns": len(dd_real),
        "prereg_sha_ok": g7_prereg,
    }

    # G8 用户裁决闭环落档（§4S5，用户 14:08）
    rat = diff.get("user_ratification", {})
    g8_res = VERBATIM5 in rat.get("verbatim", "")
    g8_hand = VERBATIM5 in handoff
    checks["G8_用户裁决落档"] = {
        "ok": g8_res and g8_hand and rat.get("judgment_owner") == "用户",
        "result_json": g8_res, "handoff": g8_hand,
        "judgment_owner": rat.get("judgment_owner"),
    }

    # G9 循环版裁决 + 谈崩洞见落档（§4S7，用户 14:35）；原话定义须一字未动
    mh = res.get("misunderstanding_hunt", {})
    verdict = mh.get("user_verdict_on_F3", {})
    break_ins = mh.get("negotiation_breakdown_insight", {})
    rev = ud.get("circular_revision_user_ratified", {})
    g9_verbatim = VERBATIM6 in verdict.get("verbatim", "")
    g9_break = "谈崩，虽然没有实现的目标，但双方是有收获的。" in break_ins.get("verbatim", "")
    g9_rev = ("E2_revised" in rev and "可被检验" in rev.get("E2_revised", "")
              and "flow_revised" in rev)
    # 原话定义一字未动：verbatim/三要素/两失败模式仍按 13:03 原样
    g9_original = (VERBATIM in ud.get("verbatim", "")
                   and [e.get("id") for e in ud.get("three_elements", [])] == ["E1", "E2", "E3"]
                   and [m.get("name") for m in ud.get("failure_modes", [])] == ["对牛弹琴", "尬聊"])
    checks["G9_循环版裁决与谈崩洞见"] = {
        "ok": g9_verbatim and g9_break and g9_rev and g9_original,
        "verdict_verbatim": g9_verbatim, "negotiation_breakdown": g9_break,
        "circular_revision": g9_rev, "original_definition_untouched": g9_original,
    }

    # G10 谈崩澄清落档（§4S8，用户 14:40）：三步结构 + 原话保留 + 自我修正标注
    clar = mh.get("negotiation_breakdown_clarification", {})
    pm = clar.get("precise_meaning", {})
    g10_verbatim = VERBATIM7 in clar.get("verbatim", "")
    g10_steps = ("step1_底线显化" in pm and "step2_据此行动" in pm
                 and "step3_反事实_不蛮干" in pm)
    g10_prior_kept = "谈崩，虽然没有实现的目标，但双方是有收获的。" in break_ins.get("verbatim", "")
    g10_selfcorrect = "self_correction" in clar.get("what_changes_vs_1435_filing", {})
    checks["G10_谈崩澄清落档"] = {
        "ok": g10_verbatim and g10_steps and g10_prior_kept and g10_selfcorrect,
        "clarification_verbatim": g10_verbatim, "three_steps": g10_steps,
        "prior_1435_verbatim_kept": g10_prior_kept, "self_correction_marked": g10_selfcorrect,
    }

    overall = all(v["ok"] for v in checks.values())
    return {"schema": "safari_dialogue_engine_v1", "overall": "PASS" if overall else "FAIL",
            "checks": checks, "judgment_owner": "用户"}

if __name__ == "__main__":
    print(json.dumps(verify(), ensure_ascii=False, indent=2))
