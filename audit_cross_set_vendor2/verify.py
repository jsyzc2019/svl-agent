"""§113 回放断言：result 与预注册锁/裁决树/2×2 格前提自洽。

PRE_REGISTERED_AWAITING_SPAWN：锁完好、规则与 §111/§112 逐字节一致、确认集=第二集、无伪造 judge；
EXECUTED：AST 准入与指标经裁决树推出、verdict 一致、跨厂商+第二集前提成立、l3 未抬级、§107/§108/§111/§112 未翻案。
"""
import json, hashlib, os

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def load(p): return json.load(open(p, encoding="utf-8"))


def main():
    result = load(f"{BASE}/result.json")
    prereg = load(f"{BASE}/prereg.json")
    checks = {}

    checks["prereg_hash_intact"] = sha(f"{BASE}/prereg.json") == open(f"{BASE}/prereg.sha256").read().strip()
    checks["manifest_hash_intact"] = sha(f"{BASE}/manifest.json") == open(f"{BASE}/manifest.sha256").read().strip()
    checks["scorer_key_hash_intact"] = sha(f"{BASE}/scorer_key.json") == open(f"{BASE}/scorer_key.json.sha256").read().strip()
    checks["admission_v2_hash_intact"] = sha(f"{BASE}/admission_v2.py") == open(f"{BASE}/admission_v2.py.sha256").read().strip()
    checks["admission_v2_matches_prereg"] = sha(f"{BASE}/admission_v2.py") == prereg["locked_files_sha256"]["admission_v2.py"]
    # 规则与 §111/§112 逐字节一致（2×2 四格用同一规则）
    for d in ("audit_admission_ast_audit", "audit_cross_vendor_designer2"):
        s = os.path.join(ROOT, d, "admission_v2.py")
        checks[f"rule_identical_to_{d}"] = os.path.exists(s) and sha(s) == sha(f"{BASE}/admission_v2.py")
    # 确认集=第二集（不是主集）
    sample_shas = {sha(f"{BASE}/vendor_{c}/samples_blind.json") for c in ("P0", "P1", "P2")}
    second = prereg["what_is_HELD_FIXED"]["samples_blind_sha256"]
    checks["samples_are_second_set"] = len(sample_shas) == 1 and second in sample_shas
    checks["samples_not_main_set"] = "e7a65f4d2df068d799040a3c0cd5f06ead87cc01584558a66aa5bcfc22c4252a" not in sample_shas
    checks["scorer_key_is_second_set"] = sha(f"{BASE}/scorer_key.json") == prereg["what_is_HELD_FIXED"]["scorer_key_sha256"]
    checks["l3_not_claimed"] = result["l3_claimed"] is False
    checks["absolute_not_claimed"] = result["absolute_claimed"] is False
    dnot = prereg.get("does_not_overturn", "")
    checks["does_not_overturn_all_four"] = all(x in dnot for x in
        ("STRATIFIED_CONFIRMED", "CROSS_SET_PARTIAL", "AST_V2_PARTIAL", "CROSS_VENDOR2_PARTIAL"))

    if result["status"] == "PRE_REGISTERED_AWAITING_SPAWN":
        checks["no_forged_judge"] = all(not os.path.exists(f"{BASE}/vendor_{c}/judge_vendor.py") for c in ("P0", "P1", "P2"))
        checks["pending_has_no_verdict"] = "verdict" not in result
        print("STATE=PRE_REGISTERED_AWAITING_SPAWN")
    else:
        cvok = result.get("vendor_cross_vendor_ok", False)
        setok = result.get("second_set_confirmed", False)
        m = result.get("metrics")
        if m is None:
            # 部分失败态：judge 生成不全 → prereg 失败分支封顶 INCONCLUSIVE
            expect = "SET_VENDOR2_INCONCLUSIVE"
            checks["partial_failure_has_missing_judges"] = bool(result.get("missing_judges"))
            checks["partial_failure_no_forged_metrics"] = result.get("metrics") is None
        else:
            P, S, c1, floor = m["PRIMARY"], m["SECONDARY"], m["P1_core"], m["P0_floor"]
            adm = result["all_admissions_pass"]
            if not (result["locks_ok"] and adm and cvok and setok):
                expect = "SET_VENDOR2_INCONCLUSIVE"
            elif P >= 0.8 and S <= 0.3 and c1 >= 0.9 and floor:
                expect = "SET_VENDOR2_CONFIRMED"
            elif P >= 0.8:
                expect = "SET_VENDOR2_PARTIAL"
            elif P < 0.3:
                expect = "SET_VENDOR2_REFUTED"
            else:
                expect = "SET_VENDOR2_INCONCLUSIVE"
        checks["verdict_matches_tree"] = result["verdict"] == expect
        checks["verdict_in_prereg_rules"] = any(result["verdict"] in r for r in prereg["verdict_rules"])
        checks["admission_rule_is_v2"] = result.get("admission_rule", "").startswith("admission_v2 (AST control-flow")
        checks["cross_vendor_premise_ok"] = cvok is True
        checks["second_set_premise_ok"] = setok is True
        checks["does_not_overturn_in_result"] = "does_not_overturn" in result
        print("STATE=EXECUTED verdict=%s expect=%s" % (result["verdict"], expect))

    ok = all(checks.values())
    for k, v in checks.items():
        print(("  [OK] " if v else "  [FAIL] ") + k)
    print("ALL_OK" if ok else "SOME_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
