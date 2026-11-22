"""§110 回放断言（确定性，不改裁决）：验证 result 与预注册锁/裁决树/口径自洽。

PENDING 状态：只断言哈希锁完好、无伪造 judge；EXECUTED 状态：断言指标与 verdict 由裁决树推出、l3 未抬级。
"""
import json, hashlib, os, sys

BASE = os.path.dirname(os.path.abspath(__file__))


def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def load(p): return json.load(open(p, encoding="utf-8"))


def main():
    result = load(f"{BASE}/result.json")
    prereg = load(f"{BASE}/prereg.json")
    checks = {}

    # 哈希锁（任何状态都要求）
    checks["prereg_hash_intact"] = sha(f"{BASE}/prereg.json") == open(f"{BASE}/prereg.sha256").read().strip()
    checks["scorer_key_hash_intact"] = sha(f"{BASE}/scorer_key.json") == open(f"{BASE}/scorer_key.sha256").read().strip()
    checks["manifest_hash_intact"] = sha(f"{BASE}/manifest.json") == open(f"{BASE}/manifest.sha256").read().strip()
    sample_shas = {sha(f"{BASE}/vendor_{c}/samples_blind.json") for c in ("P0", "P1", "P2")}
    checks["samples_frozen_single_hash"] = (len(sample_shas) == 1 and
        sample_shas.pop() == prereg["held_fixed_from_107"]["samples_blind_sha256"])
    checks["l3_not_claimed"] = result["l3_claimed"] is False
    checks["absolute_not_claimed"] = result["absolute_claimed"] is False

    if result["status"] == "PENDING_API_KEY":
        checks["no_forged_judge"] = all(
            not os.path.exists(f"{BASE}/vendor_{c}/judge_vendor.py") for c in ("P0", "P1", "P2"))
        checks["pending_has_no_verdict"] = "verdict" not in result
        print("STATE=PENDING_API_KEY")
    else:
        m = result["metrics"]
        P, S, c1 = m["PRIMARY"], m["SECONDARY"], m["P1_core"]
        floor = m["P0_floor"]
        adm = result["all_admissions_pass"]
        if not (result["locks_ok"] and adm):
            expect = "CROSS_VENDOR_INCONCLUSIVE"
        elif P >= 0.8 and S <= 0.3 and c1 >= 0.9 and floor:
            expect = "CROSS_VENDOR_CONFIRMED"
        elif P >= 0.8:
            expect = "CROSS_VENDOR_PARTIAL"
        elif P < 0.3:
            expect = "CROSS_VENDOR_REFUTED"
        else:
            expect = "CROSS_VENDOR_INCONCLUSIVE"
        checks["verdict_matches_tree"] = result["verdict"] == expect
        checks["verdict_in_prereg_rules"] = result["verdict"] in prereg["verdict_rules"][0] or any(
            result["verdict"] in rule for rule in prereg["verdict_rules"])
        print("STATE=EXECUTED verdict=%s expect=%s" % (result["verdict"], expect))

    ok = all(checks.values())
    for k, v in checks.items():
        print(("  [OK] " if v else "  [FAIL] ") + k)
    print("ALL_OK" if ok else "SOME_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
