"""§112 回放断言（确定性，不改裁决）：result 与预注册锁/裁决树/口径/跨厂商前提自洽。

PRE_REGISTERED_AWAITING_SPAWN：只断言哈希锁完好、规则与 §111 逐字节一致、无伪造 judge；
EXECUTED：断言 AST 准入与指标经裁决树推出、verdict 一致、跨厂商前提成立、l3 未抬级、§110/§111 未被翻案。
"""
import json, hashlib, os

BASE = os.path.dirname(os.path.abspath(__file__))


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def load(p): return json.load(open(p, encoding="utf-8"))


def main():
    result = load(f"{BASE}/result.json")
    prereg = load(f"{BASE}/prereg.json")
    checks = {}

    # 哈希锁（任何状态都要求）
    checks["prereg_hash_intact"] = sha(f"{BASE}/prereg.json") == open(f"{BASE}/prereg.sha256").read().strip()
    checks["manifest_hash_intact"] = sha(f"{BASE}/manifest.json") == open(f"{BASE}/manifest.sha256").read().strip()
    checks["scorer_key_hash_intact"] = sha(f"{BASE}/scorer_key.json") == open(f"{BASE}/scorer_key.json.sha256").read().strip()
    checks["admission_v2_hash_intact"] = sha(f"{BASE}/admission_v2.py") == open(f"{BASE}/admission_v2.py.sha256").read().strip()
    checks["admission_v2_matches_prereg"] = sha(f"{BASE}/admission_v2.py") == prereg["locked_files_sha256"]["admission_v2.py"]
    # 规则必须与 §111 逐字节一致（唯一变量=厂商的物理证明）
    s111 = os.path.join(os.path.dirname(BASE), "audit_admission_ast_audit", "admission_v2.py")
    checks["rule_byte_identical_to_111"] = os.path.exists(s111) and sha(s111) == sha(f"{BASE}/admission_v2.py")
    sample_shas = {sha(f"{BASE}/vendor_{c}/samples_blind.json") for c in ("P0", "P1", "P2")}
    checks["samples_frozen_single_hash"] = (len(sample_shas) == 1 and
        sample_shas.pop() == prereg["what_is_HELD_FIXED"]["samples_blind_sha256"])
    checks["l3_not_claimed"] = result["l3_claimed"] is False
    checks["absolute_not_claimed"] = result["absolute_claimed"] is False
    checks["does_not_overturn_110_111_declared"] = ("does_not_overturn" in prereg and
        "CROSS_VENDOR_INCONCLUSIVE" in prereg["does_not_overturn"] and
        "AST_V2_PARTIAL" in prereg["does_not_overturn"])

    if result["status"] == "PRE_REGISTERED_AWAITING_SPAWN":
        checks["no_forged_judge"] = all(
            not os.path.exists(f"{BASE}/vendor_{c}/judge_vendor.py") for c in ("P0", "P1", "P2"))
        checks["pending_has_no_verdict"] = "verdict" not in result
        print("STATE=PRE_REGISTERED_AWAITING_SPAWN")
    else:
        m = result["metrics"]
        P, S, c1 = m["PRIMARY"], m["SECONDARY"], m["P1_core"]
        floor = m["P0_floor"]
        adm = result["all_admissions_pass"]
        cvok = result.get("vendor_cross_vendor_ok", False)
        if not (result["locks_ok"] and adm and cvok):
            expect = "CROSS_VENDOR2_INCONCLUSIVE"
        elif P >= 0.8 and S <= 0.3 and c1 >= 0.9 and floor:
            expect = "CROSS_VENDOR2_CONFIRMED"
        elif P >= 0.8:
            expect = "CROSS_VENDOR2_PARTIAL"
        elif P < 0.3:
            expect = "CROSS_VENDOR2_REFUTED"
        else:
            expect = "CROSS_VENDOR2_INCONCLUSIVE"
        checks["verdict_matches_tree"] = result["verdict"] == expect
        checks["verdict_in_prereg_rules"] = any(result["verdict"] in rule for rule in prereg["verdict_rules"])
        checks["admission_rule_is_v2"] = result.get("admission_rule", "").startswith("admission_v2 (AST control-flow")
        checks["cross_vendor_premise_ok"] = cvok is True
        checks["does_not_overturn_in_result"] = "does_not_overturn" in result
        print("STATE=EXECUTED verdict=%s expect=%s" % (result["verdict"], expect))

    ok = all(checks.values())
    for k, v in checks.items():
        print(("  [OK] " if v else "  [FAIL] ") + k)
    print("ALL_OK" if ok else "SOME_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
