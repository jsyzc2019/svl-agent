#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gi 测试：外部时间锚判据接线 + 双向校准 + 真实远端快照核验。"""
import json
import os
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from life_kernel import temporal_anchor as ta  # noqa: E402

PREG_TS = "2026-11-26T05:51:14Z"


def _good_anchor():
    return {"commit_sha": "b570b3c1cdd31f9b0fc1ec7955717749205197d1",
            "local_blob_sha": "0c2c01321b7dbb4be400f6a9ca8a5034a74d294b"}


def _good_evidence():
    return {"remote_commit_sha": "b570b3c1cdd31f9b0fc1ec7955717749205197d1",
            "server_timestamp": "2026-11-26T06:30:00Z",
            "tree_blob_sha": "0c2c01321b7dbb4be400f6a9ca8a5034a74d294b"}


def _from_snapshot(ev):
    """显式 adapter：远端快照原始字段名 → 判据契约字段名。
    自咬记录：快照叫 constitution_blob_sha、判据契约叫 tree_blob_sha、
    预注册措辞误作 tree_blob_sha256(git blob 实为 SHA1)。三处漂移，
    在此显式映射而非放宽判据；已锁存快照保持原样不动。"""
    return {"remote_commit_sha": ev["head_sha"],
            "server_timestamp": ev["server_timestamp"],
            "tree_blob_sha": ev["constitution_blob_sha"]}


def test_t01_good_anchor_verified():
    assert ta.verify_anchor(_good_anchor(), _good_evidence(), PREG_TS).status == "ANCHOR_VERIFIED"


def test_t02_short_sha_mutual_recognition():
    a = {"commit_sha": "b570b3c", "local_blob_sha": _good_evidence()["tree_blob_sha"]}
    assert ta.verify_anchor(a, _good_evidence(), PREG_TS).status == "ANCHOR_VERIFIED"


def test_t03_absent_remote_caught_f07():
    # F07 活靶：c446e01 格式合法但不在远端
    a = {"commit_sha": "c446e01abcdef", "local_blob_sha": _good_evidence()["tree_blob_sha"]}
    v = ta.verify_anchor(a, _good_evidence(), PREG_TS)
    assert "D2_NOT_ON_REMOTE" in v.flags


def test_t04_postdated_caught():
    e = {**_good_evidence(), "server_timestamp": "2026-11-26T05:45:13Z"}
    assert "D3_POSTDATED" in ta.verify_anchor(_good_anchor(), e, PREG_TS).flags


def test_t05_content_drift_caught():
    a = {**_good_anchor(), "local_blob_sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"}
    assert "D4_CONTENT_DRIFT" in ta.verify_anchor(a, _good_evidence(), PREG_TS).flags


def test_t06_no_evidence_snapshot():
    assert ta.verify_anchor(_good_anchor(), None, PREG_TS).status == "NO_EVIDENCE_SNAPSHOT"


def test_t07_bad_format_caught():
    a = {"commit_sha": "not-a-sha", "local_blob_sha": "x"}
    assert "D1_FORMAT" in ta.verify_anchor(a, _good_evidence(), PREG_TS).flags


def test_t08_blind_spot_permissive():
    assert ta.blind_spot_check(lambda c: True)["status"] == "OVERREJECT"


def test_t09_blind_spot_strict():
    assert ta.blind_spot_check(lambda c: False)["status"] == "BLIND_SPOT"


def test_t10_real_judge_calibrated():
    assert ta.blind_spot_check(ta.is_bad_anchor)["status"] == "ALL_KNOWN_BAD_ANCHORS_RECOGNIZED"


def test_t11_wiring_self_check():
    assert ta.wiring_self_check(["tests/test_temporal_anchor.py::test_t01_good_anchor_verified"])
    assert not ta.wiring_self_check(["tests/test_unrelated.py::t"])


def test_t12_live_regression_all_green():
    lr = ta.live_regression()
    assert all(lr.values()), [k for k, v in lr.items() if not v]


def test_t13_prereg_locked_before_fetch():
    # 预注册 sha256 锁文件存在且哈希匹配（写在取证与实现之前）
    p = os.path.join(ROOT, "prereg_temporal_anchor_20261126.json")
    s = os.path.join(ROOT, "prereg_temporal_anchor_20261126.sha256")
    import hashlib
    actual = hashlib.sha256(open(p, "rb").read()).hexdigest()
    recorded = open(s).read().split()[0]
    assert actual == recorded
    doc = json.load(open(p, encoding="utf-8"))
    assert "2026-11-26T05:51:14Z" == doc["written_at_utc"]


def test_t14_real_remote_snapshot_postdated_vs_prereg():
    """真实远端快照：commit 服务器时间戳 05:45:13Z < 预注册 05:51:14Z。
    该 commit 是上一轮 §4gh 的，早于本轮预注册，构不成正面时间锚——D3 必须拒绝。
    这是真实一手负样本，不伪造一个时间通过的真锚。"""
    ev_path = os.path.join(ROOT, "audit_temporal_anchor", "remote_evidence.json")
    sh_path = os.path.join(ROOT, "audit_temporal_anchor", "remote_evidence.sha256")
    import hashlib
    ev_bytes = open(ev_path, "rb").read()
    assert hashlib.sha256(ev_bytes).hexdigest() == open(sh_path).read().split()[0]
    ev = json.loads(ev_bytes)
    a = {"commit_sha": ev["head_sha"], "local_blob_sha": ev["constitution_blob_sha"]}
    v = ta.verify_anchor(a, _from_snapshot(ev), PREG_TS)
    # 内容一致(D4)、远端存在(D2)都过，但时间倒挂(D3)被拒——诚实的真实结论
    assert v.detail["D2"] and v.detail["D4"]
    assert "D3_POSTDATED" in v.flags


def test_t15_same_kind_comparison():
    """D4 必须同类比较（git blob sha vs git blob sha），不是 SHA256 vs SHA1。
    本地 constitution.sha256 文件的 git blob sha 应等于远端树中记录的 blob sha。"""
    ev = json.load(open(os.path.join(ROOT, "audit_temporal_anchor", "remote_evidence.json")))
    p = os.path.join(ROOT, "life_kernel", "constitution.sha256")
    data = open(p, "rb").read()
    import hashlib
    local_blob = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
    assert local_blob == ev["constitution_blob_sha"]
    a = {"commit_sha": ev["head_sha"], "local_blob_sha": local_blob}
    v = ta.verify_anchor(a, _from_snapshot(ev), PREG_TS)
    assert v.detail["D4"], "同类比较下 D4 应通过"
