"""反偏差盲测逻辑的单测（纯合成数据，不依赖网络）。
重点验证：未知标签剔除、假阳性/假阴性强制报告、消融可复现。
"""
import pytest

from svagent.finance_blind_test import (
    BlindResult, _recompute_alarm, evaluate, sensitivity_analysis, label_of,
    counterexample_analysis, build_real_verdict_log,
)
from svagent.finance_fetch import FetchResult


def _r(name, alarm, neg, signals=None):
    return BlindResult(code="x", name=name, group="g", industry="i",
                       years=["2021"], alarm=alarm, label_neg=neg,
                       signals=signals or [])


def test_label_of_treats_missing_as_unknown():
    # 关键：意见未取到必须返回 -1，绝不默认成非标(1)
    r = FetchResult(code="x", name="x", secucode="x.SZ", industry="i",
                    opinion={"2025": None})
    op, neg = label_of(r)
    assert neg == -1
    r2 = FetchResult(code="x", name="x", secucode="x.SZ", industry="i",
                     opinion={"2025": "标准无保留意见"})
    assert label_of(r2)[1] == 0
    r3 = FetchResult(code="x", name="x", secucode="x.SZ", industry="i",
                     opinion={"2025": "无法表示意见"})
    assert label_of(r3)[1] == 1


def test_unknown_excluded_from_confusion_matrix():
    results = [
        _r("命中", 1, 1), _r("误报", 1, 0),
        _r("漏报", 0, 1), _r("正确", 0, 0),
        _r("未知", 1, -1),
    ]
    m = evaluate(results)
    assert m["混淆矩阵"] == {"TP": 1, "FP": 1, "FN": 1, "TN": 1}
    assert m["参评样本"] == 4
    assert any("未知" in x for x in m["标签未知_剔除"])
    # 强制报告 FP / FN，不能省略
    assert m["假阳性_预警但标准无保留"] == ["误报(x)"]
    assert m["假阴性_非标却无预警"] == ["漏报(x)"]


def test_sensitivity_recompute_is_deterministic():
    sig = [
        {"code": "FIN.GROWTH.DIVERGE", "severity": "flag", "年份": "2021", "证据": ""},
        {"code": "FIN.GROWTH.DIVERGE", "severity": "flag", "年份": "2022", "证据": ""},
        {"code": "FIN.CASH.LOW", "severity": "flag", "年份": "2021", "证据": ""},
    ]
    r = {"name": "t", "label_neg": 1, "signals": sig}
    codes_growth = {"FIN.GROWTH.DIVERGE"}
    # k=2：增速背离出现2次 → 报警；k=3 → 不报警
    assert _recompute_alarm(r, codes_growth, 2) == 1
    assert _recompute_alarm(r, codes_growth, 3) == 0
    m = sensitivity_analysis([r])
    assert m["A_全判据_k>=2(主结果)"]["TP"] == 1
    assert m["D_只用增速背离"]["recall"] == 1.0


def test_counterexample_analysis_quantifies_circularity():
    """【审计整改P1】反例对照：FP反例(困境但标准)被识别，循环被量化。"""
    import json, os
    from svagent.finance_fetch import FetchResult
    path = "/workspace/real_financials_cache.json"
    if not os.path.exists(path):
        import pytest
        pytest.skip("真实数据缓存不存在")
    cache = {c: FetchResult(**d) for c, d in json.load(open(path)).items()}
    r = counterexample_analysis(cache)
    assert r["参评家数"] >= 20
    # 关键：存在"困境但标准无保留"的假阳性反例（如比亚迪/奥瑞德）
    assert len(r["反例_困境但标准无保留_FP"]) > 0
    # 精确率显著低于10样本时的0.75，证明小样本高估了判据
    assert r["精确率"] is not None and r["精确率"] < 0.75
    assert "循环" in r["循环诊断"]


def test_real_verdict_log_from_real_data():
    """【审计整改P2】真实财报能构造 VerdictRecord 日志，打破全合成自证。"""
    import json, os
    from svagent.finance_fetch import FetchResult
    path = "/workspace/real_financials_cache.json"
    if not os.path.exists(path):
        import pytest
        pytest.skip("真实数据缓存不存在")
    cache = {c: FetchResult(**d) for c, d in json.load(open(path)).items()}
    log = build_real_verdict_log(cache)
    assert len(log) >= 20
    assert all("evidence" in x and "forged" in x and "rejected" in x for x in log)
    # 真实日志应有正有负标签
    assert any(x["forged"] for x in log) and any(not x["forged"] for x in log)
