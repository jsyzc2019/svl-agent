"""§L3 外家全链外置：回放测试（只读冻结交付与本仓结果，不重跑外部实验）。"""
import hashlib
import importlib.util
import json
import os
import re

BASE = os.path.join(os.path.dirname(__file__), "..")
EXT = os.path.join(BASE, "received", "l3_external_audit")


def load(p):
    with open(os.path.join(BASE, p), encoding="utf-8") as f:
        return json.load(f)


def test_deliverable_verification_8of8():
    """固化副本通过 8/8 机械验收。"""
    import subprocess
    import sys
    r = subprocess.run([sys.executable, os.path.join(BASE, "verify_external.py"), EXT],
                       capture_output=True, text=True)
    assert "8/8 PASS" in r.stdout, r.stdout


def test_external_own_verdict_partial_and_no_l3():
    v = json.loads(open(os.path.join(EXT, "verdict.json"), encoding="utf-8").read())
    assert v["verdict"] == "EXTERNAL_PARTIAL"
    assert v["l3_claimed"] is False and v["absolute_claimed"] is False
    assert v["metrics"]["agreement"] == 0.8125


def test_external_did_not_tune_after_disagreement():
    """外家未事后补单位换算闭合 3 个分歧——反 Goodhart 证据在 verdict 自述。"""
    v = json.loads(open(os.path.join(EXT, "verdict.json"), encoding="utf-8").read())
    assert "did not add unit-prefix arithmetic" in v["why"]
    assert set(v["metrics"]["mismatch_ids"]) == {"P03", "P05", "P07"}


def test_prereg_before_fetch():
    p = json.loads(open(os.path.join(EXT, "prereg.json"), encoding="utf-8").read())
    f = json.loads(open(os.path.join(EXT, "sources", "fetch_log.json"), encoding="utf-8").read())
    t0 = p["timestamps_utc"]["prereg_written"]
    t1 = [x["utc"] for x in f["fetches"] if "primary" in x.get("role", "")][0]
    assert t0 < t1


def test_paper_not_in_avoid_list():
    m = json.loads(open(os.path.join(EXT, "manifest.json"), encoding="utf-8").read())
    p = json.loads(open(os.path.join(EXT, "prereg.json"), encoding="utf-8").read())
    assert m["arxiv_id"] not in p["avoid_list_confirmation"]["avoid_list"]


def test_repo_comparison_reproduces_11_of_18():
    r = load("result.json")
    assert r["repo_mechanical_comparison"]["agreement"] == "11/18"
    assert r["repo_mechanical_comparison"]["by_variant"]["clean"] == "6/6"
    assert r["repo_mechanical_comparison"]["by_variant"]["tampered"] == "2/6"


def test_verdict_fullchain_partial_honest_bound():
    r = load("result.json")
    assert r["verdict"] == "FULLCHAIN_PARTIAL"
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
    assert len(r["does_not_overturn"]) == 9
    assert "不宣布 L3" in r["hard_bound"]


def test_external_criterion_pure_and_replay():
    spec = importlib.util.spec_from_file_location(
        "ext_crit_replay", os.path.join(EXT, "criterion.py"))
    ec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ec)
    sb = json.loads(open(os.path.join(EXT, "samples_blind.json"), encoding="utf-8").read())
    jd = json.loads(open(os.path.join(EXT, "judgments.json"), encoding="utf-8").read())
    agree = 0
    for p in sb["pairs"]:
        got = ec.judge(p["text_a"], p["text_b"])
        agree += int(bool(got[0]) == bool(jd[p["id"]]["verdict"]))
    assert agree == 16


def test_execution_log_records_tool_bug_fix():
    log = open(os.path.join(BASE, "EXECUTION_LOG.md"), encoding="utf-8").read()
    assert "修工具" in log and "不放宽" in log
    assert "af360e6" in log  # bug 先于交付的外部锚
