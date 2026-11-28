"""§4S101 adjudication_boundary_probe 12 守卫测试。

裁定权分层机制化：事实层归机械证据，人不是可靠裁判者（宪法修正案 A1）。
纯只读自检，不修改宪法本体、不进判定、不自封等级。
"""
import os
import sys
import json
import hashlib
import importlib.util

import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, os.pardir, os.pardir))


def _load_kernel():
    p = os.path.join(ROOT, "life_kernel", "kernel.py")
    s = importlib.util.spec_from_file_location("k_ab", p)
    k = importlib.util.module_from_spec(s)
    sys.modules["k_ab"] = k
    s.loader.exec_module(k)
    return k


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


@pytest.fixture(scope="module")
def K():
    return _load_kernel()


# ---- 1. 预注册与修正案锁 ----
def test_01_prereg_and_amendment_sha_locked(K):
    assert _sha(os.path.join(ROOT, "prereg_adjudication_amendment_20261129.json")).startswith("b3cb9f04")
    am = os.path.join(ROOT, "life_kernel", "constitution_amendment.json")
    lock = os.path.join(ROOT, "life_kernel", "constitution_amendment.sha256")
    declared = open(lock, encoding="utf-8").read().split()[0]
    assert declared == _sha(am) and declared.startswith("425e4c64")


# ---- 2. 真实结果 ----
def test_02_real_all_boundaries_held(K):
    r = K.adjudication_boundary_probe()
    assert r["flag"] == "ALL_BOUNDARIES_HELD"
    assert r["n_ok"] == 6 and r["n_total"] == 6
    assert r["counts"]["BROKEN"] == 0


def test_03_three_faces_exact_scan(K):
    r = K.adjudication_boundary_probe()
    faces = {}
    for row in r["rows"]:
        faces.setdefault(row["face"], []).append(row["class"])
    assert set(faces) == {"AMENDMENT", "BOUNDARY", "EVIDENCE"}
    assert [len(faces[x]) for x in ("AMENDMENT", "BOUNDARY", "EVIDENCE")] == [3, 2, 1]
    assert all(c == "AMENDMENT" for c in faces["AMENDMENT"])
    assert all(c == "BOUNDARY" for c in faces["BOUNDARY"])
    assert all(c == "EVIDENCE" for c in faces["EVIDENCE"])


def test_04_amendment_three_articles_immutable(K):
    am = json.load(open(os.path.join(ROOT, "life_kernel", "constitution_amendment.json"), encoding="utf-8"))
    ids = {a.get("id") for a in am.get("articles", [])}
    assert {"A1-F", "A1-V", "A1-M"} <= ids
    assert am.get("immutable") is True
    assert "constitution.json" in json.dumps(am)  # 关联本体但不修改


# ---- 5. 面2 本体锁未动+未自封 ----
def test_05_body_constitution_untouched_and_not_self_sealed(K):
    r = K.adjudication_boundary_probe()
    assert r["body_lock"].startswith("fe56291b")
    body = os.path.join(ROOT, "life_kernel", "constitution.json")
    assert _sha(body).startswith("fe56291b")
    body_lock = os.path.join(ROOT, "life_kernel", "constitution.sha256")
    assert open(body_lock, encoding="utf-8").read().split()[0].startswith("fe56291b")
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert res.get("verdict") == "GAP_INCONCLUSIVE"
    assert res.get("l3_claimed") is False and res.get("absolute_claimed") is False


# ---- 6. 面3 对打证据+IGC诚实裁决 ----
def test_06_duel_evidence_in_place(K):
    r = K.adjudication_boundary_probe()
    assert r["duel_detection"] == "0/3→3/3"
    d = json.load(open(os.path.join(ROOT, "audit_l3_fullchain_external",
                                    "holdout_duel_20261129", "duel_log.json"), encoding="utf-8"))
    assert d.get("all_match") is True
    assert d["detection_rate"] == {"before": "0/3", "after": "3/3"}


def test_07_igc_honest_not_self_sealed(K):
    g = json.load(open(os.path.join(ROOT, "improver_gain_controlled_verdict_20261129.json"), encoding="utf-8"))
    assert g.get("honest_not_self_sealed") is True
    assert g.get("action_code") in ("flag", "downgrade")  # 不自封 ok
    assert g.get("four_dims", {}).get("improver_gain_isolated") == "no"


# ---- 7. 三类负向注入 ----
def test_08_inject_amendment_tampered(K):
    r = K.adjudication_boundary_probe({"force_class": "AMENDMENT_TAMPERED"})
    assert r["flag"] == "NO_ADJUDICATION_CLAIM"  # 注入态不赋真值 flag
    broken = [x for x in r["rows"] if x["class"] != "AMENDMENT"]
    assert any(x["face"] == "AMENDMENT" for x in broken)
    assert r["n_ok"] < r["n_total"]


def test_09_inject_fact_layer_defect(K):
    r = K.adjudication_boundary_probe({"force_class": "FACT_LAYER_DEFECT"})
    broken = [x for x in r["rows"] if x["class"] == "FACT_LAYER_DEFECT"]
    assert len(broken) >= 1 and r["n_ok"] < r["n_total"]


def test_10_inject_self_sealed_level(K):
    r = K.adjudication_boundary_probe({"force_class": "SELF_SEALED_LEVEL"})
    broken = [x for x in r["rows"] if x["class"] == "SELF_SEALED_LEVEL"]
    assert len(broken) >= 1 and any(x["face"] == "BOUNDARY" for x in broken)


# ---- 8. 只读字段 + honesty 边界 ----
def test_11_readonly_and_honesty(K):
    r = K.adjudication_boundary_probe()
    assert r["verdict_unchanged"] is True and r["consumed"] is False and r["is_gate_verdict"] is False
    op = r["one_page"]
    for kw in ("事实层", "价值层", "不自封", "不修改宪法本体", "价值层才归用户"):
        assert kw in op


# ---- 9. 七件套零副作用 ----
def test_12_seven_piece_zero_side_effect(K):
    expected = {
        "authoritative_state.json": "5f7a2584",
        "life_kernel/constitution.sha256": "2ad148c7",
        "life_kernel/data/heartbeat_log.jsonl": "ea749f76",
        "life_kernel/data/inbound_inbox.jsonl": "8806b248",
        "DECISIONS_20261127.json": "91114955",
        "gap_archive_20261128.json": "d73bfef5",
        "knowledge_base_store.json": "0938b3df",
    }
    for rel, prefix in expected.items():
        assert _sha(os.path.join(ROOT, rel)).startswith(prefix), rel
