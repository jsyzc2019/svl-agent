#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gv 守卫：口径修正(分桶) / 过拟合守卫 / HTML双引擎一致 / v1规则不删不改。"""
import hashlib, json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AA = os.path.join(ROOT, "audit_argument_audit")
sys.path.insert(0, AA)
import scan as S, evaluate_layered as E


def test_01_prereg_hash_locked():
    p = os.path.join(ROOT, "prereg_argument_audit_v2_20261126.json")
    d = json.load(open(p, encoding="utf-8"))
    stored = d.pop("sha256")
    assert hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == stored
    assert stored == "825378aed69704938a6f09cf0e90e80a33648f011f72cb22664ccd3840e25cef"


def test_02_layered_metric_corrected():
    r = E.evaluate_layered()
    b = r["by_bucket"]
    assert b["伪托类"]["n"] == 6 and b["伪托类"]["recall"] == 1.0  # 口径修正后真实召回
    assert b["语义细节类"]["n"] == 3 and b["语义细节类"]["coverage"] >= 2/3
    assert b["属实与量化"]["false_positive"] <= 1


def test_03_overfit_guard_passes():
    g = E.overfit_guard()
    assert g["passed"] is True
    assert g["hardcoded_names"] == []
    assert g["neutral_false_positive"] is False
    assert g["generic_caught"] is True


def test_04_v1_rules_unchanged_v2_only_adds():
    rules = S.load_rules()
    ids = [r["id"] for r in rules["rules"]]
    # v1 的 9 类必须都在且顺序在前
    v1 = ["SIG-AUTHORITY","SIG-QUOTE","SIG-ABSOLUTE","SIG-NUMBER","SIG-CAUSAL",
          "SIG-EMOTION","SIG-OVERGEN","SIG-FALSE-DICHOTOMY","SIG-CERTAINTY"]
    assert ids[:9] == v1
    assert ids[-1] == "SIG-NARRATIVE" and len(ids) == 10


def test_05_html_embeds_same_rules_no_escape_corruption():
    html = open(os.path.join(ROOT, "argument_audit.html"), encoding="utf-8").read()
    seg = re.search(r"const RULES = ([\s\S]*?);\nconst CARDS", html).group(1)
    embedded = json.loads(seg)  # 反斜杠若被吞会在此抛错（回归上一轮的 self-bite）
    assert embedded["rules"] == S.load_rules()["rules"]
    # v2.1 起展示层版本号会随诚实边界补充递增；锁定 v2 系列而非具体小版本，判据(规则数据)上方已逐字节断言
    assert "Argument Audit · v2." in html and "分层评测口径" in html


def test_06_result_persisted_and_verdict_unchanged():
    d = json.load(open(os.path.join(AA, "result_v2.json"), encoding="utf-8"))
    assert d["prereg_sha256"] == "825378aed69704938a6f09cf0e90e80a33648f011f72cb22664ccd3840e25cef"
    assert d["overfit_guard"]["passed"] is True
    assert d["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    assert d["l3_claimed"] is False and d["absolute_claimed"] is False
    p = os.path.join(ROOT, "audit_l3_gap_targeted", "result.json")
    before = open(p, "rb").read()
    E.evaluate_layered()
    assert open(p, "rb").read() == before
