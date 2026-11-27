#!/usr/bin/env python3
"""§4gb 守卫：构念效度检查项 + 取证结果 + 硬边界。"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(rel):
    return json.load(open(os.path.join(ROOT, rel), encoding="utf-8"))


def test_01_prereg_hash_lock():
    d = _load("prereg_finance_construct_validity_20261127.json")
    locked = d.pop("sha256")
    actual = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    assert locked == actual == "92025d41ccd935ec7350eed04cee0d58b4414f3de987259526475b4943bda71c"


def test_02_negative_self_bite():
    from life_kernel.construct_validity import negative_self_bite
    r = negative_self_bite()
    assert r["passed"] is True
    assert all(r["detail"].values())


def test_03_wilson_interval_math():
    from life_kernel.construct_validity import wilson_interval
    lo, hi = wilson_interval(3, 4)
    assert 0.29 < lo < 0.31 and 0.95 < hi < 0.96
    lo2, hi2 = wilson_interval(90, 100)
    assert lo2 > 0.8 and (hi2 - lo2) < 0.2  # 窄 CI 不得与宽 CI 混淆


def test_04_organ_verdict_confirmed():
    r = _load("audit_finance_construct_validity/result.json")
    assert r["organ_result"]["verdict"] == "PROXY_GAP_CONFIRMED"
    assert all(r["organ_result"][k]["passed"] for k in
               ("cv1_proxy_gap", "cv2_precision_ci", "cv3_base_rate_sensitivity"))


def test_05_triplet_unchanged():
    r = _load("audit_finance_construct_validity/result.json")
    assert r["verdict_triplet_before"] == r["verdict_triplet_after"] == ["GAP_INCONCLUSIVE", False, False]


def test_06_no_individual_stock_verdict():
    """硬边界：器官与结果都不得输出个股真假/投资建议；总体基础率 UNKNOWN。"""
    from life_kernel.construct_validity import evaluate
    r = evaluate([0, 1], [1, 1], [1, 1], 1, 1, [{"name": "a", "precision": 0.5}])
    assert r["cv3_base_rate_sensitivity"]["population_base_rate_hint"] == "UNKNOWN"
    # 扫描『输出』而非源码：源码必须写禁止语（绝不判…是否值得投资），故只查输出字段不含投资判断词
    result = json.dumps(_load("audit_finance_construct_validity/result.json"), ensure_ascii=False)
    for banned in ("投资建议买入", "该股造假", "值得投资买入"):
        assert banned not in result
    assert "康美" in result  # 历史口径差异已公开留痕，非臆造证据


def test_07_three_falsification_entries():
    p = os.path.join(ROOT, "audit_finance_construct_validity", "falsification_entries.jsonl")
    lines = [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]
    assert len(lines) == 3
    assert [x["id"] for x in lines] == [
        "FALSIFY-CV1-PROXY-NOT-CONSTRUCT",
        "FALSIFY-CV2-PRECISION-CI-WIDE",
        "FALSIFY-CV3-BASE-RATE-ENRICHMENT",
    ]
    assert all(x["verdict_impact"].startswith("不动") for x in lines)


def test_08_formal_log_not_touched_by_engine():
    """本轮产物写入独立候选文件，不覆盖正式 falsification_log.jsonl。"""
    formal = os.path.join(ROOT, "falsification_log.jsonl")
    assert sum(1 for _ in open(formal, encoding="utf-8")) == 3  # 仍是原三条
