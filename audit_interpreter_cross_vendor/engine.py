"""§115 解释者跨厂商交叉裁决引擎。

逐厂商读 runs/<tag>/interpreter_call_manifest.json，用私有 gt 机械比对（复用 §114 的
FULL≡CONFIRMED 档位规范化），按预注册裁决树 INTERPRETER_CROSS_* 四档裁决。
不翻 §107-§114 八案；l3=false / absolute=false 硬编码。
"""
import json, os, hashlib

BASE = os.path.dirname(os.path.abspath(__file__))
TAGS = ("dots", "ling", "liquid")


def load(p):
    return json.load(open(p, encoding="utf-8"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


# 档位规范化：逐字复用 §114（FULL≡CONFIRMED 是 §114 修的确定性字段 bug）
CANON = {"FULL": "CONFIRMED", "CONFIRMED": "CONFIRMED",
         "PARTIAL": "PARTIAL", "REFUTED": "REFUTED", "INCONCLUSIVE": "INCONCLUSIVE"}
def canon(t):
    return CANON.get(t, t) if t is not None else None


def main():
    prereg = load(f"{BASE}/prereg.json")
    gt = load(f"{BASE}/gt_private.json")
    gt_map = gt["neutral_gt"]

    # 哈希锁自检
    locks_ok = True
    checks = {"prereg.json": "prereg.sha256", "manifest.json": "manifest.sha256",
              "cases_blind.json": "cases_blind.json.sha256", "gt_private.json": "gt_private.json.sha256",
              "gen_fixtures.py": "gen_fixtures.py.sha256", "call_interpreter.py": "call_interpreter.py.sha256",
              "run_all.py": "run_all.py.sha256"}
    for f, lk in checks.items():
        sp = f"{BASE}/{lk}"
        locks_ok = locks_ok and os.path.exists(sp) and sha(f"{BASE}/{f}") == open(sp).read().strip()

    # 三态：全缺待命 / 部分缺 / 全齐
    present = [t for t in TAGS if os.path.exists(f"{BASE}/runs/{t}/interpreter_call_manifest.json")]
    if not present:
        result = {"experiment": "§115", "status": "PRE_REGISTERED_AWAITING_SPAWN", "locks_ok": locks_ok,
                  "verdict": None, "metrics": None, "does_not_overturn": prereg["does_not_overturn"],
                  "l3_claimed": False, "absolute_claimed": False}
        json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("PRE_REGISTERED_AWAITING_SPAWN")
        return 0

    per_vendor = {}
    for tag in present:
        mf = load(f"{BASE}/runs/{tag}/interpreter_call_manifest.json")
        rec = mf.get("calls", [{}])[0]
        ok = rec.get("status") == "ok" and "tiers" in rec
        if not ok:
            per_vendor[tag] = {"model": mf.get("model"), "status": rec.get("status"),
                               "agreement": None, "per_case": None}
            continue
        agree, pc = 0, {}
        for cid, exp_raw in sorted(gt_map.items()):
            got_raw = rec["tiers"].get(cid)
            got, exp = canon(got_raw), canon(exp_raw)
            m = (got == exp)
            agree += int(m)
            pc[cid] = {"interpreter_tier_raw": got_raw, "expected_canon": exp,
                       "interpreter_canon": got, "match": m}
        per_vendor[tag] = {"model": mf.get("model"), "status": "ok",
                           "agreement": f"{agree}/4", "agreement_num": agree,
                           "case_2_match": pc.get("case_2", {}).get("match"),
                           "finish_reason": rec.get("finish_reason"),
                           "parse_source": rec.get("parse_source"), "per_case": pc}

    full = [t for t in TAGS if per_vendor.get(t, {}).get("agreement_num") == 4]
    case2_all = all(per_vendor.get(t, {}).get("case_2_match") is True for t in TAGS if t in present)

    if len(present) < len(TAGS):
        verdict = "INTERPRETER_CROSS_INCONCLUSIVE"
        why = f"仅 {len(present)}/{len(TAGS)} 家厂商产出有效留痕，按预注册失败/不完整分支封顶，不伪造缺失厂商 tiers"
    elif len(full) == 3 and case2_all:
        verdict = "INTERPRETER_CROSS_CONFIRMED"
        why = "三家真正不同厂商全部 agreement=4/4 且 case_2 全判对 → 解释者独立一维获多厂商交叉确认，规则语义跨厂商稳健移植（非 L3）"
    elif len(full) == 2:
        verdict = "INTERPRETER_CROSS_PARTIAL"
        why = f"2 家 4/4、1 家 <4/4（{','.join(t for t in TAGS if t not in full)}）——多数可移植但有厂商特异分歧，诚实标注"
    else:
        verdict = "INTERPRETER_CROSS_DIVERGENT"
        why = f"仅 {len(full)}/3 家 4/4（≤1）——解释语义厂商特异，§114 单厂商 4/4 可能偶然，真负面结果如实记"

    result = {"experiment": "§115", "status": "EXECUTED", "locks_ok": locks_ok,
              "vendors_present": list(present), "verdict": verdict, "why": why,
              "metrics": {"vendors_full_agreement": len(full), "vendors_total": len(TAGS),
                          "case_2_all_match": case2_all,
                          "per_vendor_agreement": {t: per_vendor.get(t, {}).get("agreement") for t in TAGS}},
              "per_vendor": per_vendor,
              "tier_alias_normalization_applied": {"FULL": "CONFIRMED", "reuse_from": "§114"},
              "does_not_overturn": prereg["does_not_overturn"],
              "l3_claimed": False, "absolute_claimed": False,
              "honest_bound": prereg["hard_bound"]}
    json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(verdict, "full=", len(full), "case2_all=", case2_all)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
