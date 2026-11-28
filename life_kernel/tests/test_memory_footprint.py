"""§4S103 memory_footprint_probe 12 守卫测试。

记忆体物理层治理：三分类穷尽 + 处置安全 + 诚实不自封。
纯只读自检，不写盘、不删文件、不进判定。
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
    s = importlib.util.spec_from_file_location("k_mf", p)
    k = importlib.util.module_from_spec(s)
    sys.modules["k_mf"] = k
    s.loader.exec_module(k)
    return k


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


@pytest.fixture(scope="module")
def K():
    return _load_kernel()


# ---- 1. 预注册与备份锁 ----
def test_01_prereg_and_backup_locked(K):
    assert _sha(os.path.join(ROOT, "prereg_memory_footprint_20261129.json")).startswith("19935621")
    b = os.path.join(ROOT, "life_kernel", "pre_patch_memory_footprint", "kernel_before_memory_footprint.py")
    assert _sha(b).startswith("00c82500")


# ---- 2. 真实结果 ----
def test_02_real_footprint_governed(K):
    r = K.memory_footprint_probe()
    assert r["flag"] == "FOOTPRINT_GOVERNED"
    assert r["n_ok"] == 6 and r["n_total"] == 6
    assert r["counts"]["BROKEN"] == 0


def test_03_three_faces_exact_scan(K):
    r = K.memory_footprint_probe()
    faces = {}
    for row in r["rows"]:
        faces.setdefault(row["face"], []).append(row["class"])
    assert set(faces) == {"CLASSIFICATION", "DISPOSITION", "HONESTY"}
    assert [len(faces[x]) for x in ("CLASSIFICATION", "DISPOSITION", "HONESTY")] == [2, 2, 2]
    for face, ok in (("CLASSIFICATION", "CLASSIFICATION"), ("DISPOSITION", "DISPOSITION"), ("HONESTY", "HONESTY")):
        assert all(c == ok for c in faces[face])


# ---- 3. 面1 分类穷尽+守恒 ----
def test_04_classification_exhaustive_and_conserved(K):
    r = K.memory_footprint_probe()
    d = r["class_detail"]
    assert set(d) == {"A_source", "B_asset", "C_regenerable"}
    assert all(d[x]["disposition"] in ("KEEP", "CLEARABLE") for x in d)
    assert d["A_source"]["disposition"] == "KEEP"
    assert d["B_asset"]["disposition"] == "KEEP"
    assert d["C_regenerable"]["disposition"] == "CLEARABLE"
    # 体积守恒: 三类之和 == total_mb (容差四舍五入)
    s = d["A_source"]["mb"] + d["B_asset"]["mb"] + d["C_regenerable"]["mb"]
    assert abs(s - r["total_mb"]) < 0.1


# ---- 4. 面2 处置安全(含双后缀/死缓存self-bite) ----
def test_05_disposition_pyc_regenerable_or_dead_cache(K):
    r = K.memory_footprint_probe()
    disp = [x for x in r["rows"] if x["name"].startswith("C类pyc")]
    assert disp and disp[0]["class"] == "DISPOSITION"
    assert "死缓存" in disp[0]["evidence"]


# ---- 5. 面3 诚实不自封 ----
def test_06_honesty_asset_not_garbage(K):
    r = K.memory_footprint_probe()
    d = r["class_detail"]
    assert d["B_asset"]["mb"] > d["C_regenerable"]["mb"]  # 主体是资产非缓存
    op = r["one_page"]
    assert "不宣称清理解决50M" in op or "特性非垃圾" in op


# ---- 6. 三类负向注入 ----
def test_07_inject_classification_broken(K):
    r = K.memory_footprint_probe({"force_class": "CLASSIFICATION_BROKEN"})
    assert r["flag"] == "NO_FOOTPRINT_CLAIM"
    broken = [x for x in r["rows"] if x["class"] == "CLASSIFICATION_BROKEN"]
    assert any(x["face"] == "CLASSIFICATION" for x in broken)
    assert r["n_ok"] < r["n_total"]


def test_08_inject_unsafe_disposition(K):
    r = K.memory_footprint_probe({"force_class": "UNSAFE_DISPOSITION"})
    broken = [x for x in r["rows"] if x["class"] == "UNSAFE_DISPOSITION"]
    assert len(broken) >= 1 and r["n_ok"] < r["n_total"]


def test_09_inject_overclaim(K):
    r = K.memory_footprint_probe({"force_class": "OVERCLAIM"})
    broken = [x for x in r["rows"] if x["class"] == "OVERCLAIM"]
    assert len(broken) >= 1 and any(x["face"] == "HONESTY" for x in broken)


# ---- 7. C=0 清理达成态合法(穷尽语义非"三类非空") ----
def test_10_cleared_state_is_governed(K):
    # 清理达成后 C=0, 仍应判 GOVERNED(每文件恰归一类+守恒,不要求三类非空)
    r = K.memory_footprint_probe({
        "class_A": 182, "class_B": 1988, "class_C": 0,
        "total_bytes": 1, "pyc_regenerable": True,
    })
    assert r["flag"] == "NO_FOOTPRINT_CLAIM"  # 注入态不赋真值flag
    cls = [x for x in r["rows"] if x["name"] == "三分类穷尽"]
    assert cls and cls[0]["class"] == "CLASSIFICATION"


# ---- 8. 只读字段 + honesty 边界 ----
def test_11_readonly_and_honesty(K):
    r = K.memory_footprint_probe()
    assert r["verdict_unchanged"] is True and r["consumed"] is False and r["is_gate_verdict"] is False
    op = r["one_page"]
    for kw in ("三分类", "处置", "不自封", "不宣称清理解决50M", "事实层归机械证据"):
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
