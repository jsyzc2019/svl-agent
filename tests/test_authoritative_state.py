"""权威态结构化定位器官守卫（P4 第一条，预注册 0a7e1115）。"""
import os
import json
import hashlib
import pytest

from life_kernel import authoritative_state as AS

ROOT = AS.ROOT


def _file_sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def test_01_prereg_hash_locked():
    """预注册哈希先于取证锁定。"""
    p = os.path.join(ROOT, "prereg_authoritative_state_20261127.json")
    d = json.load(open(p, encoding="utf-8"))
    d.pop("sha256", None)
    h = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    declared = open(os.path.join(ROOT, "prereg_authoritative_state_20261127.sha256")).read().split()[0]
    assert h == declared
    assert h.startswith("0a7e1115")


def test_02_state_file_exists_and_fields():
    """结构化文件存在且覆盖权威字段。"""
    s = json.load(open(AS.STATE_JSON, encoding="utf-8"))
    for k in AS._STATE_FIELDS:
        assert k in s, k
    assert s["schema"] == "authoritative-state/v1"
    assert isinstance(s["fragile_fields"], list)
    assert "round" in s["fragile_fields"] and "tests_passed" in s["fragile_fields"]


def test_03_values_match_live():
    """结构化值 == 现场抽取值（round/tests/kb/safari 等）。"""
    s = json.load(open(AS.STATE_JSON, encoding="utf-8"))
    live = AS.extract_live_state()
    for k in AS._STATE_FIELDS:
        if k == "handoff_authority_line":
            continue
        assert s[k] == live[k], (k, s[k], live[k])


def test_04_known_authority_numbers():
    """权威数字与现场核验一致（非记忆，是该轮已落档值）。"""
    s = json.load(open(AS.STATE_JSON, encoding="utf-8"))
    assert s["round"] == "§4ij"
    assert s["tests_passed"] == 1773
    assert s["kb_count"] == 507  # §4S3 新增 KB-META201，506→507
    assert s["safari_rounds"] == 136  # §4S3 Safari 路标探索 135→136
    assert s["kernel_version"] == "7.5.0"


def test_05_check_consistent():
    r = AS.check()
    assert r["ok"] is True
    assert r["verdict"] == "CONSISTENT"
    assert r["sha256_ok"] is True
    assert r["drifts"] == [] and r["handoff_drifts"] == []


def test_06_negative_selfbite_all_caught():
    """三注入负向自咬全被抓。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = AS.negative_selfbite(d)
    assert r["baseline_consistent"] is True
    assert r["drift_kb_caught"] is True
    assert r["handoff_drift_caught"] is True
    assert r["verdict_guard_rejects"] is True
    assert r["all_caught"] is True


def test_07_state_under_3kb():
    """结构化文件 <3KB，新会话无需读 28K 超长行。"""
    assert os.path.getsize(AS.STATE_JSON) < 3072


def test_08_verdict_source_bytes_unchanged():
    """生成/校验不碰权威 result.json 字节。"""
    before = _file_sha(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"))
    AS.check()
    s, _ = AS.build_state()  # 只构建不写文件
    after = _file_sha(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"))
    assert before == after
    assert before.startswith("0f3ccb13")


def test_09_verdict_trinity_unchanged():
    """判定态三值恒 GAP_INCONCLUSIVE/false/false。"""
    s = json.load(open(AS.STATE_JSON, encoding="utf-8"))
    assert s["verdict"] == "GAP_INCONCLUSIVE"
    assert s["l3_claimed"] is False
    assert s["absolute_claimed"] is False
    assert s["constitution_lock_ok"] is True
    assert s["constitution_sha256"].startswith("fe56291b")


def test_10_migration_declares_remaining_debt():
    """诚实标注 round/tests 仍 fragile，不假装彻底消除锚点。"""
    s = json.load(open(AS.STATE_JSON, encoding="utf-8"))
    assert s["migration"]["pending"] == ["round", "tests_passed"]
    assert "正则" in s["migration"]["note"] or "散文" in s["migration"]["note"]
