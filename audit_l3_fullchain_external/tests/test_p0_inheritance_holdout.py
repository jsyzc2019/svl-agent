"""§4S99 fullchain 验证器 P0 洞修复 + 改前vs改后对打 的 12 守卫。

用户裁定：人不是可靠裁判者；往"改前vs改后独立评测证据"上迈；该改的大胆改。
边界仍守：不碰 verdict/l3/absolute/宪法，不自封等级。

借 Who-Verifies-the-Verifier 的锋利镜面：验证器自己有洞（缺判定静默跳过）
时，下游整体分数看不出来；只有同口径对打 05 判定段本身才暴露。
"""
import os
import json
import hashlib
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
AUDIT = os.path.abspath(os.path.join(HERE, os.pardir))
ROOT = os.path.abspath(os.path.join(AUDIT, os.pardir))

VERIFY = os.path.join(AUDIT, "verify_external.py")
BEFORE = os.path.join(ROOT, "life_kernel/pre_patch_fullchain_p0/verify_external_before_p0.py")
PREREG = os.path.join(ROOT, "prereg_fullchain_p0_holdout_20261129.json")
DUEL_LOG = os.path.join(AUDIT, "holdout_duel_20261129/duel_log.json")
PKG = os.path.join(AUDIT, "received/l3_external_audit")

SEVEN = [
    "authoritative_state.json",
    "life_kernel/constitution.sha256",
    "life_kernel/data/heartbeat_log.jsonl",
    "life_kernel/data/inbound_inbox.jsonl",
    "DECISIONS_20261127.json",
    "gap_archive_20261128.json",
    "knowledge_base_store.json",
]
SEVEN_BASELINE = [
    "5f7a2584", "2ad148c7", "ea749f76", "8806b248",
    "91114955", "d73bfef5", "0938b3df",
]


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _run(script, pkg):
    r = subprocess.run([sys.executable, script, pkg], capture_output=True, text=True, timeout=60)
    line = [x for x in r.stdout.splitlines() if "05_replay" in x]
    line = line[0] if line else "NO_05_LINE"
    state = "FAIL" if line.startswith("[FAIL]") else ("PASS" if line.startswith("[PASS]") else "NONE")
    return state, line


# 1. 预注册 SHA 锁死（改码前）
def test_01_prereg_sha_locked():
    assert _sha(PREREG)[:8] == "cfb5c052"

# 2. 改前备份在位且哈希=基线
def test_02_backup_intact():
    assert os.path.isfile(BEFORE)
    assert _sha(BEFORE)[:16] == "3275d8859289e099"

# 3. 修复存在：id集校验代码在位
def test_03_fix_present():
    src = open(VERIFY, encoding="utf-8").read()
    assert "sids = {p[\"id\"] for p in sb[\"pairs\"]}" in src
    assert "missing = sorted(sids - jids)" in src
    assert "extra = sorted(jids - sids)" in src

# 4. 洞已堵：改后不再有静默 continue
def test_04_silent_skip_removed():
    src = open(VERIFY, encoding="utf-8").read()
    seg = src[src.find("# 5. 重跑判据"):src.find("# 6. verdict")]
    assert "if cid not in jd:\n                continue" not in seg

# 5. 元数据兼容：_meta 被排除
def test_05_meta_excluded():
    src = open(VERIFY, encoding="utf-8").read()
    assert "if not k.startswith(\"_\")" in src

# 6. py_compile 通过
def test_06_compile_ok():
    r = subprocess.run([sys.executable, "-m", "py_compile", VERIFY], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr

# 7. 真实完整包不误伤（改后 05 段 PASS）
def test_07_real_pkg_not_broken():
    state, line = _run(VERIFY, PKG)
    assert state == "PASS", line

# 8. 对打日志存在且结论=改后更会抓
def test_08_duel_log_detection_rate():
    assert os.path.isfile(DUEL_LOG)
    d = json.load(open(DUEL_LOG, encoding="utf-8"))
    assert d["detection_rate"]["before"] == "0/3"
    assert d["detection_rate"]["after"] == "3/3"
    assert d["all_match"] is True

# 9. 六案例全中（含不误伤完整包/合法meta）
def test_09_all_cases_match():
    d = json.load(open(DUEL_LOG, encoding="utf-8"))
    assert len(d["cases"]) == 6
    assert all(c["match"] for c in d["cases"])
    zero = {c["case"]: c for c in d["cases"]}
    assert zero["C0_full"]["before"] == "PASS" and zero["C0_full"]["after"] == "PASS"
    assert zero["C5_meta"]["before"] == "PASS" and zero["C5_meta"]["after"] == "PASS"

# 10. 负向自咬记录在位（差异来自修复本身）
def test_10_negative_self_bite_recorded():
    d = json.load(open(DUEL_LOG, encoding="utf-8"))
    assert "negative_self_bite" in d
    assert "重新被静默放行" in d["negative_self_bite"]["result"]
    assert "0/3→3/3" in d["negative_self_bite"]["conclusion"]
    assert "fixture_correction_honesty" in d

# 11. 只读：finish() 不写盘，真实交付包零改动
def test_11_readonly_no_disk_write():
    src = open(VERIFY, encoding="utf-8").read()
    finish = src[src.find("def finish()"):]
    assert "json.dump" not in finish and "open(" not in finish
    d = json.load(open(DUEL_LOG, encoding="utf-8"))
    assert d["authority_zero_side_effect"]["real_delivery_pkg_untouched"] is True

# 12. 权威态七件套零副作用
def test_12_authority_zero_side_effect():
    for rel, base in zip(SEVEN, SEVEN_BASELINE):
        assert _sha(os.path.join(ROOT, rel))[:8] == base, rel
