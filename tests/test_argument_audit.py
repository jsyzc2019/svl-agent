#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论证取证工作台守卫：规则可追溯 / 双引擎一致 / 诚实边界 / ground-truth 盲区如实记录。"""
import json, os, re, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AA = os.path.join(ROOT, "audit_argument_audit")
sys.path.insert(0, AA)
import scan as S


def test_01_rules_traceable_to_kb():
    rules = S.load_rules()
    assert len(rules["rules"]) >= 9
    kb = json.load(open(os.path.join(ROOT, "knowledge_base_store.json")))["items"]
    ids = {x["item_id"] for x in kb}
    for r in rules["rules"]:
        assert r["kb"], f"{r['id']} 无 KB 溯源"
        assert all(k in ids for k in r["kb"]), f"{r['id']} 引用了不存在的 KB"
        assert r["why"] and r["how"]
    assert "不判真假" in rules["honest_bound"]


def test_02_all_patterns_compile():
    for r in S.load_rules()["rules"]:
        for p in r["patterns"]:
            re.compile(p)


def test_03_known_case_detection():
    r = S.scan("人民日报说：读书和不读书差的是整个人生。研究表明80%的烦恼来自读书太少，读书必然让你永远不再迷茫。")
    ids = {h["id"] for h in r["hits"]}
    assert "SIG-AUTHORITY" in ids
    assert "SIG-NUMBER" in ids
    assert "SIG-ABSOLUTE" in ids
    assert "SIG-CERTAINTY" in ids


def test_04_html_embeds_same_rules():
    html = open(os.path.join(ROOT, "argument_audit.html"), encoding="utf-8").read()
    embedded = re.search(r"const RULES = ([\s\S]*?);\nconst CARDS", html).group(1)
    assert json.loads(embedded)["rules"] == S.load_rules()["rules"]


def test_05_ground_truth_recall_and_honest_misses():
    """真实核查集：伪托/无出处类召回0.75，两条语义走样漏检如实记录为盲区。"""
    d = json.load(open(os.path.join(ROOT, "article_factcheck.json")))
    need = {"伪托权威", "查无实据", "伪名言(铁证)", "金句属实但出处混乱/措辞被改",
            "有典故但细节走样", "出处存疑", "广泛流传但出处存疑", "部分属实(经历真,细节化了)"}
    tp = fn = 0
    misses = []
    for f in d["fact_checks"]:
        if f["verdict"] not in need:
            continue
        hits = {h["id"] for h in S.scan(f["claim"])["hits"]}
        if "SIG-AUTHORITY" in hits or "SIG-QUOTE" in hits:
            tp += 1
        else:
            fn += 1
            misses.append(f["claim"][:30])
    assert tp == 6 and fn == 2, f"召回基线漂移: tp={tp} fn={fn}"
    assert any("王小波" in m or "闵子骞" in m for m in misses)


def test_06_no_verdict_mutation():
    p = os.path.join(ROOT, "audit_l3_gap_targeted", "result.json")
    before = open(p, "rb").read()
    S.scan("人民日报说必然100%导致成功")
    assert open(p, "rb").read() == before
