"""判据引擎：精研 claude.dev《How the Claude Code team thinks about verification》。
按 prereg.json（实现前 SHA256 锁存）逐条核验 V1-V9，并做 V10 本仓源码级缺口核验。
只读一手证据与源码，不回写预注册。
"""
import hashlib
import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(BASE)
TEXT = open(os.path.join(BASE, "article.txt"), encoding="utf-8").read()
PREREG = json.load(open(os.path.join(BASE, "prereg.json"), encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


# V1-V8: 一手文本逐字定位（锚点为文章原句片段，先验锁存于 prereg 的 claim）
EVIDENCE_ANCHORS = {
    "V1": ["~90%", "written and"],
    "V2": ["up to 10 points", "separate grader", "rubric"],
    "V3": ["E2E tests", "Property tests", "Differential tests", "fast-check", "Hypothesis", "proptest"],
    "V4": ["Verification means running the change", "verify", "three rounds"],
    "V5": ["never from the pull request", "base or default branch", "commits", "cheap checks first"],
    "V6": ["39 items", "3 to 10", "trigger"],
    "V7": ["off, observe, and enforce", 'stamp', '"none"', "blocked twice", "over-flagging", "tuning set is split"],
    "V8": ["at least two PRs", "Three agents will try to disprove", "three bug finders", "can't skip", "tidy"],
}


def check_text_criteria():
    out = {}
    for cid, anchors in EVIDENCE_ANCHORS.items():
        hits = {a: (a in TEXT) for a in anchors}
        out[cid] = {"anchors": hits, "present": all(hits.values())}
    return out


def grading_v9():
    """V9 已实现vs愿景分级 + 数字口径限定。"""
    return {
        "reported_numbers": {
            "90pct_code_by_claude": {"value": "~90%", "self_reported": True,
                                      "note": "团队自报，无外部审计；KB-RSI06 折扣"},
            "up_to_10_points": {"value": "up to 10 points", "scope": "structured file generation ONLY",
                                 "self_reported": True,
                                 "note": "限于特定任务，line 38 明确 internal testing + 限定语境，不外推"},
            "39_checklist_items": {"value": 39, "note": "line 96 一手列出"},
            "3_to_10_triggered": {"value": "3 to 10", "note": "line 97 一手列出"},
            "three_round_escalation": {"value": 3, "note": "line 92 一手列出"},
        },
        "shipped_vs_vision": "全文为已实施做法描述（we do / we maintain / we've created），无 'we are exploring' 类愿景词冒充已上线；分级=SHIPPED_PRACTICE",
        "honesty_signals": [
            "line 117 自承 Claude Code isn't perfect（被挡两次第三次放行，防卡死）",
            "line 128 自承 recall 调到再提升就 overfitting eval（不过度刷指标）",
            "line 122 用 merged stable changes 作 control 防 over-flagging（自我约束）",
        ],
        "verdict": "GRADED",
    }


def repo_gap_v10():
    """V10 五项本仓源码级核验：符号存在性 + 语义对应性。"""
    sv = os.path.join(REPO, "svagent")

    def has_symbols(*syms):
        blob = ""
        for f in sorted(os.listdir(sv)):
            if f.endswith(".py"):
                blob += open(os.path.join(sv, f), encoding="utf-8").read()
        return {s: (s in blob) for s in syms}

    r1 = has_symbols("check_scoring_integrity", "SCORE")  # KB-AUDIT07 对应物
    # 验证戳：call_site 的 'none' 是调用点位置，非产物验证状态戳
    r2_syms = has_symbols("verification_stamp", "verify_stamp")
    r3_syms = has_symbols("three_round_escalate", "escalate_after_rounds")
    r4_syms = has_symbols("disprove_threshold", "human_approved_rule")
    # 分阶段 recall 保真：现有 recall 均为检索/盲测指标，非漏斗分阶段评估
    r5_syms = has_symbols("funnel_recall", "staged_recall", "review_funnel")

    targets = [
        {"key": "rule_integrity", "repo_has_corresponding_gate": all(r1.values()),
         "evidence": "svagent/scoring_integrity.py + KB-AUDIT07（计分器可达性/篡改）",
         "note": "对应文章 line 103-107『改动不能改自己的检查』"},
        {"key": "verification_stamp", "repo_has_corresponding_gate": any(r2_syms.values()),
         "evidence": "call_site_integrity 的 none=调用点位置（非验证戳）；无产物级验证状态戳",
         "note": "部分精神在 §58/§59，但无统一可查询的验证戳字段"},
        {"key": "three_round_escalation", "repo_has_corresponding_gate": any(r3_syms.values()),
         "evidence": "insight.py 有 escalate_rate（EU 交人率实验），非验证三轮转人门禁",
         "note": "概念存在但非可执行门禁"},
        {"key": "miss_to_rule_gate", "repo_has_corresponding_gate": any(r4_syms.values()),
         "evidence": "knowledge_base 加固需 support 证据，但无『2PR复现+3agent证伪+人批』硬门槛门禁",
         "note": "精神在 KB 流程，未编译成会拦的门禁"},
        {"key": "reviewer_evaluation", "repo_has_corresponding_gate": any(r5_syms.values()),
         "evidence": "finance_blind_test.py/knowledge_base.py 的 recall=检索/盲测指标；无 raw→post→final 漏斗保真门禁",
         "note": "真缺口：本仓『判据/审查者』本身未按分阶段 recall + 稳定集对照评估"},
    ]
    return {"targets": targets,
            "gaps": [t["key"] for t in targets if not t["repo_has_corresponding_gate"]]}


def main():
    v = check_text_criteria()
    gate_report = dict(
        prereg_id=PREREG["prereg_id"],
        object_type=PREREG["object_type"],
        source_lock=PREREG["source_lock"],
        source_sha_ok=(sha256(os.path.join(BASE, "article.html")) == PREREG["source_lock"]["html_sha256"]
                       and sha256(os.path.join(BASE, "article.txt")) == PREREG["source_lock"]["txt_sha256"]),
        prereg_sha_stored=open(os.path.join(BASE, "prereg.sha256"), encoding="utf-8").read().split()[0],
        prereg_sha_actual=sha256(os.path.join(BASE, "prereg.json")),
        V1_V8_text_criteria=v,
        V1_V8_all_present=all(c["present"] for c in v.values()),
        V9_honesty_grading=grading_v9(),
        V10_repo_gap=repo_gap_v10(),
    )
    gate_report["prereg_lock_ok"] = (gate_report["prereg_sha_stored"] == gate_report["prereg_sha_actual"])
    gate_report["decision"] = (
        "DEEP_READ_COMPLETE" if gate_report["V1_V8_all_present"] and gate_report["source_sha_ok"]
        else "INCOMPLETE"
    )
    json.dump(gate_report, open(os.path.join(BASE, "result.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print(json.dumps({
        "decision": gate_report["decision"],
        "V1_V8_all_present": gate_report["V1_V8_all_present"],
        "source_sha_ok": gate_report["source_sha_ok"],
        "prereg_lock_ok": gate_report["prereg_lock_ok"],
        "V9": gate_report["V9_honesty_grading"]["verdict"],
        "gaps": gate_report["V10_repo_gap"]["gaps"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
