#!/usr/bin/env python3
"""§4S70 一次性迁移：35个'?'审计文件 verdict 保真回填。

按 prereg_gap_backfill_20261128.json (SHA ae8410fd…) 口径：
- 只处理无顶层 verdict 键的 audit_*/result.json
- 保真映射：真悬置保留悬置，完成态才标完成，不塞长叙述
- 打 verdict_backfill 标记（可审计）
- 记录每文件前后哈希到回执（可回滚）
不修改内核/权威态/心跳。
"""
import json
import glob
import os
import hashlib
from datetime import datetime, timezone

WORK = "/workspace"
PREREG_SHA = "ae8410fd632a228e505965966c12631f897bcef853ca617b97e4e523a70917ab"
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
VERDICT_CAP = 40

DEC_FIELDS = ("decision", "final_decision", "gate_decision", "kb_decision", "overall", "outcome", "conclusion")
PLURAL_FIELDS = ("verdicts", "verdict_triplet_before", "paper_forensic_verdict", "verdict_impact")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def derive(d, rel):
    """返回 (verdict, rule_id, source_field, preview)。保真优先。"""
    # 规则1: verdict_triplet_after — 最强证据(补平后当前态)
    if "verdict_triplet_after" in d:
        va = d["verdict_triplet_after"]
        val = va[0] if isinstance(va, (list, tuple)) and va else va
        return str(val)[:VERDICT_CAP], "R1_triplet_after", "verdict_triplet_after", json.dumps(va, ensure_ascii=False)[:90]

    # 规则2: 嵌套 judges.*.verdict (flashprove)
    judges = d.get("judges")
    if isinstance(judges, dict) and any(
        isinstance(v, dict) and "verdict" in v for v in judges.values()
    ):
        vs = [v.get("verdict") for v in judges.values() if isinstance(v, dict) and "verdict" in v]
        aligned = d.get("all_aligned") is True
        if aligned and all(str(x).upper() == "PASS" for x in vs):
            return "PASS", "R2_judges_allpass", "judges.*.verdict+all_aligned", f"{len(vs)} judges all PASS"
        # 有 SCOPED/非全PASS → 保守 SCOPED，不洗成 PASS
        return "SCOPED", "R2_judges_scoped", "judges.*.verdict", json.dumps(vs, ensure_ascii=False)[:90]

    # 规则4/5: decision 族——短标记取规范值，长叙述标 DECIDED_NARRATIVE
    # 注意：本体判定字段优先于 kernel_verdict_unchanged 旁注
    for k in DEC_FIELDS:
        if k in d:
            v = d[k]
            if isinstance(v, str) and len(v) <= VERDICT_CAP:
                return "DECIDED_" + v.strip().replace(" ", "_")[:VERDICT_CAP], "R4_decision_short", k, v[:90]
            if isinstance(v, dict):
                # 结构化决策(如 new_teeth) → 标 DECIDED_STRUCT
                return "DECIDED_STRUCT", "R4_decision_struct", k, json.dumps(v, ensure_ascii=False)[:90]
            return "DECIDED_NARRATIVE", "R5_decision_narrative", k, str(v)[:90]

    # 规则6: summary 含 all_pass
    s = d.get("summary")
    if isinstance(s, dict):
        if s.get("all_pass") is True:
            return "PASS", "R6_summary_allpass", "summary.all_pass", "true"
        if s.get("all_pass") is False:
            return "SCOPED", "R6_summary_notallpass", "summary.all_pass", "false"

    # 规则7: status=EXECUTED (本体判定,优先于旁注)
    st = d.get("status")
    if st is not None and str(st).strip().upper() in ("EXECUTED", "PASS", "COMPLETE", "DONE"):
        return "EXECUTED", "R7_status", "status", str(st)

    # 规则3: kernel_verdict_unchanged — 仅在无任何本体判定字段时才用(vanity 的情况)
    # 它是"内核判定未变"旁注,不是审计自身结论;有 status/decision/summary 时上面已返回
    if "kernel_verdict_unchanged" in d:
        val = d["kernel_verdict_unchanged"]
        return str(val)[:VERDICT_CAP], "R3_kernel_verdict_unchanged", "kernel_verdict_unchanged", str(val)[:90]

    # 规则10: verdict_impact / verdict_triplet_before — before 是悬置则保留
    for k in PLURAL_FIELDS:
        if k in d:
            v = d[k]
            sv = json.dumps(v, ensure_ascii=False)
            if any(t in sv.upper() for t in ("INCONCLUSIVE", "PARTIAL", "SCOPED")):
                # 只取关键词作 verdict，不塞整段
                for t in ("INCONCLUSIVE", "PARTIAL", "SCOPED"):
                    if t in sv.upper():
                        return t, "R10_before_suspended", k, sv[:90]
            return "REFERENCED", "R10_referenced", k, sv[:90]

    # 规则8: 仅 evidence_grade 弱信号
    for k in ("evidence_grade", "three_layer_honesty"):
        if k in d:
            return "WEAK_SIGNAL_GRADED", "R8_grade_only", k, str(d[k])[:90]

    # 规则9: paper_forensic_verdict code
    pf = d.get("paper_forensic_verdict")
    if isinstance(pf, dict) and "code" in pf:
        return "FORENSIC_" + str(pf["code"])[:VERDICT_CAP], "R9_forensic", "paper_forensic_verdict.code", str(pf["code"])

    # 兜底：不伪造，标 NO_SIGNAL
    return "NO_SIGNAL_AT_TOPLEVEL", "R0_no_signal", None, ""


def main():
    files = sorted(glob.glob(os.path.join(WORK, "audit_*", "result.json")))
    receipt = {
        "prereg_sha256": PREREG_SHA,
        "at_utc": NOW,
        "policy": "保真回填:真悬置保留悬置,完成态才标完成,不塞长叙述,不改原字段",
        "entries": [],
        "refused_already_has_verdict": [],
    }
    for f in files:
        d = json.load(open(f, encoding="utf-8"))
        if "verdict" in d:
            receipt["refused_already_has_verdict"].append(os.path.basename(os.path.dirname(f)))
            continue
        before = sha(f)
        keys_before = set(d.keys())
        verdict, rule, src, preview = derive(d, f)
        # 保真自检：悬置关键词不能被洗掉
        if any(t in json.dumps(d, ensure_ascii=False).upper() for t in ("INCONCLUSIVE", "PARTIAL")) \
           and verdict in ("PASS", "DECIDED_COMPLETE") and rule not in ("R1_triplet_after", "R6_summary_allpass"):
            # 有悬置信号却要标完成 → 拒绝，标 SCOPED
            verdict = "SCOPED"
            rule = "GUARD_no_whitewash"
        d["verdict"] = verdict
        d["verdict_backfill"] = {
            "applied": True,
            "source_field": src,
            "source_value_preview": preview,
            "rule_id": rule,
            "at_utc": NOW,
            "prereg_sha256": PREREG_SHA,
            "note": "保真回填:判定态来自该文件已有字段/嵌套,非新判定;真悬置保留,SCOPED/INCONCLUSIVE不洗成PASS",
        }
        # 原子写回
        tmp = f + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False, indent=2)
        os.replace(tmp, f)
        receipt["entries"].append({
            "dir": os.path.basename(os.path.dirname(f)),
            "verdict": verdict,
            "rule_id": rule,
            "source_field": src,
            "sha_before": before,
            "sha_after": sha(f),
            "original_fields_preserved": keys_before.issubset(set(d.keys())),
        })
    out = os.path.join(WORK, "gap_backfill_receipt_20261128.json")
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(receipt, fh, ensure_ascii=False, indent=2)
    from collections import Counter
    vc = Counter(e["verdict"] for e in receipt["entries"])
    print(f"回填文件数: {len(receipt['entries'])}")
    print(f"跳过(已有verdict): {len(receipt['refused_already_has_verdict'])}")
    print("verdict分布:", dict(vc))
    print("原字段全保留:", all(e["original_fields_preserved"] for e in receipt["entries"]))
    # 关键：真悬置是否保留
    for e in receipt["entries"]:
        if e["dir"] in ("audit_finance_construct_validity", "audit_memory_governance", "audit_vanity_selfaudit"):
            print(f"  真悬置保留检查 {e['dir']}: verdict={e['verdict']} rule={e['rule_id']}")


if __name__ == "__main__":
    main()
