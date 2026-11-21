"""RSI 前景论证引擎的判据固化测试——锁住方法纪律，防回归。"""
import json
from pathlib import Path

import numpy as np
import pytest

from svagent.rsi_prospect import (
    backtest_rsi, rsi_wilder, rsi_sma, run_all, ROOT,
)


def test_prereg_sha256_lock():
    """预注册必须锁存且与实际文件一致——防事后篡改判据。"""
    import hashlib
    expected = (ROOT / "rsi_prereg.sha256").read_text().split()[0]
    actual = hashlib.sha256((ROOT / "rsi_preregistration.json").read_bytes()).hexdigest()
    assert actual == expected


def test_rsi_wilder_range_and_warmup():
    close = np.array([100 + i * 0.5 + 2 * np.sin(i) for i in range(60)], dtype=float)
    r = rsi_wilder(close, 14)
    assert np.isnan(r[:14]).all()          # warmup 期无值
    valid = r[~np.isnan(r)]
    assert (valid >= 0).all() and (valid <= 100).all()


def test_two_implementations_diverge():
    """R1：Wilder 与 SMA 实现确实分歧——印证'用了RSI≠同一RSI'。"""
    close = np.array([100 + i * 0.3 + 3 * np.sin(i / 2) for i in range(100)], dtype=float)
    w, s = rsi_wilder(close, 14), rsi_sma(close, 14)
    mask = ~(np.isnan(w) | np.isnan(s))
    diff = np.abs(w[mask] - s[mask])
    assert diff.mean() > 1.0  # 明显分歧


def test_no_lookahead_signal_uses_prev_bar():
    """防前视门禁：末日 RSI 改变不得影响当日仓位，只影响次日。"""
    close = np.array([100 + i * 0.5 for i in range(40)], dtype=float)
    a = backtest_rsi(close, 7, 30, 70)
    close2 = close.copy()
    close2[-1] = 99999  # 只改最后一根
    b = backtest_rsi(close2, 7, 30, 70)
    # 除末日收益外，前 n-1 日策略收益应完全一致
    np.testing.assert_allclose(a.strategy_returns[:-1], b.strategy_returns[:-1])


def test_tstat_magnitude_sane():
    """高功效陷阱自检：日超额 t 值不得出现 -600 级假量级。"""
    d = json.loads((ROOT / "rsi_full_result.json").read_text())
    for g in d["R3"]["grid"]:
        assert abs(g["tstat_daily"]) < 30, f"t={g['tstat_daily']} 疑似量纲错配"


def test_full_result_consistency():
    """结果自洽：全负方向 + 无经济优势 + 未超随机。"""
    d = json.loads((ROOT / "rsi_full_result.json").read_text())
    assert d["R1"]["divergence_found"] is True
    assert d["R2"]["economic_advantage"] is False
    assert d["R3"]["direction"] == "全负"
    assert d["R4"]["beyond_random"] is False
    assert d["R4"]["percentile"] < 0.95
    assert d["R5"]["robust"] is False
    # 数据隔离声明存在
    assert "未进入" in d["_meta"]["source_isolation"]


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
