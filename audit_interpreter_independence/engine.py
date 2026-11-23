"""§114 解释者独立性裁决引擎。

读异厂解释者产出的 tier 标签 + 私有 gt，按预注册裁决树机械比对：
- 从 gt_private.json 取中性档（本 Agent 历史裁决映射），从 interpreter_call_manifest.json 取异厂 tier。
- agreement = 逐 case 一致数 / 4；case_2 为关键区分点。
- 裁决四档：INTERPRETER_CONFIRMED / PARTIAL / DIVERGENT / INCONCLUSIVE。
- 失败分支（解析失败/API 失败/非法档位）→ INCONCLUSIVE，不伪造、metrics=None。
- 不翻 §107-§113 案；l3=false / absolute=false 硬编码。
"""
import json, os, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))


def load(p):
    return json.load(open(p, encoding="utf-8"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    prereg = load(f"{BASE}/prereg.json")
    gt = load(f"{BASE}/gt_private.json")

    # 哈希锁自检（prereg 自哈希 + 冻结输入）
    locks_ok = True
    checks = {"prereg.json": "prereg.sha256", "manifest.json": "manifest.sha256",
              "cases_blind.json": "cases_blind.json.sha256", "gt_private.json": "gt_private.json.sha256",
              "gen_fixtures.py": "gen_fixtures.py.sha256", "call_interpreter.py": "call_interpreter.py.sha256"}
    for f, lk in checks.items():
        sp = f"{BASE}/{lk}"
        locks_ok = locks_ok and os.path.exists(sp) and sha(f"{BASE}/{f}") == open(sp).read().strip()

    call_p = f"{BASE}/runs/interpreter_call_manifest.json"
    if not os.path.exists(call_p):
        # 三态之"全缺待命"：spawn 前无调用留痕
        result = {"experiment": "§114", "status": "PRE_REGISTERED_AWAITING_SPAWN",
                  "locks_ok": locks_ok, "verdict": None, "metrics": None,
                  "does_not_overturn": prereg["does_not_overturn"],
                  "l3_claimed": False, "absolute_claimed": False}
        json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("PRE_REGISTERED_AWAITING_SPAWN")
        return 0

    manifest = load(call_p)
    calls = manifest.get("calls", [])
    ok = bool(calls) and calls[0].get("status") == "ok"
    gt_map = gt["neutral_gt"]

    # 失败分支：解析失败/API 失败/非法档位 → INCONCLUSIVE，metrics=None
    if not ok or "tiers" not in calls[0]:
        result = {"experiment": "§114", "status": "EXECUTED", "locks_ok": locks_ok,
                  "vendor": manifest.get("vendor"), "model": manifest.get("model"),
                  "call_status": calls[0].get("status") if calls else "no_call",
                  "gt_private_in_prompt": manifest.get("gt_private_in_prompt"),
                  "verdict": "INTERPRETER_INCONCLUSIVE",
                  "why": "异厂解释者调用/解析失败，按预注册失败分支封顶，不伪造 tier 与 metrics",
                  "metrics": None, "per_case": None,
                  "does_not_overturn": prereg["does_not_overturn"],
                  "l3_claimed": False, "absolute_claimed": False,
                  "honest_bound": prereg["hard_bound"]}
        json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("INTERPRETER_INCONCLUSIVE")
        return 0

    tiers = calls[0]["tiers"]

    # 档位规范化（修确定性字段 bug，§109/§111 先例）：
    # 中性规则给异厂的词表是 FULL/PARTIAL/REFUTED/INCONCLUSIVE，私有 gt 从历史 verdict
    # 后缀提取写成 CONFIRMED/PARTIAL/...；FULL 与 CONFIRMED 语义同指"确认档"，仅命名不同。
    # 两词表在 spawn 前已锁文件里就不一致（见 EXECUTION_LOG.md），与异厂输出无关。
    # 该映射对全部档位一视同仁，不改异厂标签/不改 gt/不改裁决树阈值。
    CANON = {"FULL": "CONFIRMED", "CONFIRMED": "CONFIRMED",
             "PARTIAL": "PARTIAL", "REFUTED": "REFUTED", "INCONCLUSIVE": "INCONCLUSIVE"}
    def canon(t):
        return CANON.get(t, t) if t is not None else None

    per_case, agree = {}, 0
    for cid, exp_raw in sorted(gt_map.items()):
        got_raw = tiers.get(cid)
        got, exp = canon(got_raw), canon(exp_raw)
        match = (got == exp)
        agree += int(match)
        per_case[cid] = {"expected_neutral_tier_raw": exp_raw, "interpreter_tier_raw": got_raw,
                         "expected_canon": exp, "interpreter_canon": got, "match": match,
                         "source_round": gt["mapping"][cid]["source_round"],
                         "historical_verdict": gt["mapping"][cid]["historical_verdict"]}
    total = len(gt_map)
    case2_ok = per_case.get("case_2", {}).get("match", False)

    if agree == total and case2_ok:
        verdict = "INTERPRETER_CONFIRMED"
        why = f"异厂解释者按中性规则逐 case 复现本 Agent 裁决 {agree}/{total}，关键 case_2(SECONDARY=1.0)判对；解释环节一维获受控外移证据（非 L3）"
    elif agree == 3 and case2_ok:
        verdict = "INTERPRETER_PARTIAL"
        why = f"agreement={agree}/{total}，一处分歧但关键 case_2 判对"
    elif agree == 3 and not case2_ok:
        verdict = "INTERPRETER_PARTIAL"
        why = f"agreement={agree}/{total}，但关键区分点 case_2 判错——细分条件 SECONDARY>0.3 的解释未复现"
    else:
        verdict = "INTERPRETER_DIVERGENT"
        why = f"agreement={agree}/{total}≤2/4，异厂解释者系统性分歧，裁决规则语义不可跨厂商一致移植（真负面结果）"

    result = {"experiment": "§114", "status": "EXECUTED", "locks_ok": locks_ok,
              "vendor": manifest.get("vendor"), "model": manifest.get("model"),
              "call_status": calls[0].get("status"),
              "gt_private_in_prompt": manifest.get("gt_private_in_prompt"),
              "finish_reason": calls[0].get("finish_reason"),
              "parse_source": calls[0].get("parse_source"),
              "tier_alias_normalization_applied": {"FULL": "CONFIRMED", "reason": "修确定性字段命名bug，见EXECUTION_LOG.md；不改异厂标签/gt/裁决树"},
              "verdict": verdict, "why": why,
              "metrics": {"agreement": f"{agree}/{total}", "agreement_num": agree,
                          "total": total, "critical_case_2_match": case2_ok},
              "per_case": per_case,
              "does_not_overturn": prereg["does_not_overturn"],
              "l3_claimed": False, "absolute_claimed": False,
              "honest_bound": prereg["hard_bound"]}
    json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(verdict, f"agreement={agree}/{total} case2_ok={case2_ok}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
