#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gy P3 守卫：vanity 自检反向用回自己的可复现性与判定态不动。"""
import json
import os
import hashlib
from life_kernel.vanity_selfaudit import (
    audit_unit, evaluate, negative_self_bite, split_windows, _A,
)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "audit_vanity_selfaudit", "result.json")


def _r():
    return json.load(open(RES, encoding="utf-8"))


def test_01_prereg_hash_locked():
    pre = json.load(open(os.path.join(ROOT, "prereg_vanity_selfaudit_20261127.json"),
                         encoding="utf-8"))
    stored = pre.pop("sha256")
    raw = json.dumps(pre, ensure_ascii=False, sort_keys=True)
    assert hashlib.sha256(raw.encode()).hexdigest() == stored
    assert _r()["prereg_sha256"] == stored


def test_02_negative_self_bite():
    b = negative_self_bite()
    assert b["passed"] is True
    assert b["positive_hits"] >= 1 and b["negative_hits"] == 0


def test_03_wordlists_locked():
    # 词表在预注册 design 字段逐词列明——核对关键锚点未被删改
    pre = json.load(open(os.path.join(ROOT, "prereg_vanity_selfaudit_20261127.json"),
                         encoding="utf-8"))
    d = pre["design"]
    for w in ("战利品丰盛", "红线全守", "判定权归你", "本轮最可能错在哪", "裁定权归用户"):
        assert w in d, f"预注册 design 缺词 {w}；本轮改词表须新开预注册"
    for w in ("战利品丰盛", "全绿", "红线全守"):
        assert w in _A["CLAIM"]
    for w in ("判定权归你", "不编译新门禁", "裁定权归用户"):
        assert w in _A["DISCLAIM"]


def test_04_two_window_criterion():
    text = "战利品丰盛，全绿，判定权归你。这是一段中性说明文字。"
    s = audit_unit({"id": "X", "text": text}, "sentence")
    p = audit_unit({"id": "X", "text": text}, "paragraph")
    assert s["self_serving_count"] == 1
    assert p["self_serving_count"] == 1  # 同一段内也共现
    assert split_windows(text, "sentence")[1].startswith("这是")


def test_05_honest_detection_result():
    r = _r()
    assert r["result"]["signal"] == "SELF_SERVING_DETECTED"
    assert r["result"]["primary"]["self_serving_count"] > 0
    assert r["result"]["primary"]["self_serving_window_rate"] > 0
    # 靶心：SELF_AUDIT 盲点三那句必须被自己扫出
    hits = [e for u in r["result"]["primary"]["per_unit"]
            for e in u["self_serving_examples"]
            if "战利品丰盛" in e["text"] and "判定权归你" in e["text"]]
    assert hits, "自检未扫出 SELF_AUDIT 盲点三靶心句"


def test_06_meta_recursion_and_fp_review():
    r = _r()
    assert r["result"]["meta_recursion_catch"]["caught"] is True  # 检测器自身被扫出
    fp = r["result"]["false_positive_review"]
    assert len(fp) == r["result"]["primary"]["self_serving_count"]  # 逐条复核不漏档
    tags = {t for x in fp for t in x["false_positive_candidates"]}
    assert "统计术语_显著_非自夸" in tags and "纪律陈述_非免责堵质疑" in tags
    # 公开假阳性但不删词：命中数不因复核而降低
    assert "不删词" in r["result"]["fp_review_rule"]


def test_07_self_bites_and_judgment_fork():
    r = _r()
    assert len(r["self_bites"]) >= 3
    assert all("工具bug" in b["class"] for b in r["self_bites"])
    assert r["judgment_fork"]["user_verdict"].startswith("PENDING")


def test_08_vanity_rerun_and_verdict_unchanged():
    r = _r()
    ids = [v["id"] for v in r["vanity_rerun"]]
    assert ids == ["V1", "V2", "V3", "V4"]
    assert r["vanity_rerun"][3]["verdict"] == "SELF_SERVING_DETECTED"
    assert r["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    assert r["l3_unchanged"] is False and r["absolute_unchanged"] is False
    auth = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"),
                          encoding="utf-8"))
    assert auth["verdict"] == "GAP_INCONCLUSIVE"
    assert auth["l3_claimed"] is False and auth["absolute_claimed"] is False
