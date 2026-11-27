#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gx P4 守卫：KB improvement_class 回填的可追溯性与判定态不动。"""
import json, os, hashlib
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _kb():
    return json.load(open(os.path.join(ROOT, "knowledge_base_store.json"), encoding="utf-8"))


def _dec():
    return json.load(open(os.path.join(ROOT, "kb_class_backfill_decisions.json"), encoding="utf-8"))


def test_01_no_empty_class():
    items = _kb()["items"]
    empty = [x for x in items if not x.get("improvement_class")]
    assert not empty, f"仍有空 class: {[x.get('item_id') for x in empty]}"


def test_02_all_classes_valid():
    for x in _kb()["items"]:
        assert x["improvement_class"] in ("fix", "vanity", "preserve")


def test_03_prereg_hash_locked():
    pre = json.load(open(os.path.join(ROOT, "prereg_kb_class_backfill_20261127.json"), encoding="utf-8"))
    stored = pre.pop("sha256")
    raw = json.dumps(pre, ensure_ascii=False, sort_keys=True)
    assert hashlib.sha256(raw.encode()).hexdigest() == stored
    assert _dec()["prereg_sha256"] == stored


def test_04_decisions_cover_all_19_with_reasons():
    d = _dec()
    assert len(d["decisions"]) == 19
    for item in d["decisions"]:
        assert item["id"] and item["class"] in ("fix", "vanity", "preserve")
        assert item["rule"] and item["why"] and len(item["why"]) >= 10
    # 判定文件与 KB 实际值一致
    byid = {x["item_id"]: x["improvement_class"] for x in _kb()["items"]}
    for item in d["decisions"]:
        assert byid[item["id"]] == item["class"]


def test_05_boundary_case_and_novel_flagged():
    d = _dec()
    assert "KB-R-L-inventory-2026-b1" in d["summary"]["boundary_case"]
    assert "KB-T07" in d["summary"]["novel_decisions"]
    # R3(复用→preserve) 与锚点(建立→fix) 的区分必须显式记录
    blob = json.dumps(d["decisions"], ensure_ascii=False)
    assert "复用" in blob and "建立" in blob


def test_06_kb_total_unchanged():
    # §4gx 回填后基线 494；§4gy +189 → 495；§4gz +190 → 496；§4ga +191 → 497；§4gb +192 → 498；§4hc +193 → 499。总数变化只由显式新条目驱动。
    # §4he +KB-META194（裁定执行轮）→ 500；§4hf +KB-META195 → 501；§4hg +KB-META196 → 502；§4hi +KB-META197 → 503；§4ij +KB-META198 → 504；§4S1 +KB-META199 → 505；§4S2 +KB-META200 → 506。总数变化只由显式新条目驱动。
    assert len(_kb()["items"]) == 506


def test_07_verdict_source_bytes_unchanged():
    r = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert r["verdict"] == "GAP_INCONCLUSIVE"
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
