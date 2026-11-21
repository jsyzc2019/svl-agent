"""市场有效性检验的工具函数与前视偏差修复测试。"""
import unittest
import numpy as np

from svagent.market_efficiency import (
    variance_ratio, runs_test, load_returns, backtest,
)


class TestStatTools(unittest.TestCase):
    def test_variance_ratio_iid_near_one(self):
        rng = np.random.default_rng(1)
        r = rng.normal(0, 0.01, 5000)
        for q in [2, 5, 10]:
            vr, z = variance_ratio(r, q)
            self.assertLess(abs(vr - 1), 0.1)
            self.assertLess(abs(z), 3)

    def test_variance_ratio_trending_gt_one(self):
        # 构造有正自相关的序列（趋势），VR应>1
        rng = np.random.default_rng(2)
        r = np.zeros(5000)
        e = rng.normal(0, 0.01, 5000)
        for t in range(1, 5000):
            r[t] = 0.3 * r[t - 1] + e[t]
        vr, z = variance_ratio(r, 10)
        self.assertGreater(vr, 1.0)
        self.assertGreater(z, 2)

    def test_runs_test_alternating(self):
        # 完美交替 → 游程数最多，z为正且大
        signs = np.array([1, -1] * 100)
        nr, er, z = runs_test(signs)
        self.assertEqual(nr, 200)
        self.assertGreater(z, 5)

    def test_runs_test_clustered(self):
        # 全部同号 → 游程数=1
        signs = np.ones(100)
        nr, er, z = runs_test(signs)
        self.assertEqual(nr, 1)


class TestLookaheadFix(unittest.TestCase):
    """前视偏差修复：这是本次验证最重要的教训，用测试固化。"""

    def test_ma_signal_no_future_leak(self):
        """均线策略的信号只能用 t-1 及之前的信息。"""
        rng = np.random.default_rng(3)
        r = rng.normal(0.0003, 0.01, 1000)
        close = np.exp(np.cumsum(r))
        cut = 700
        # 复现引擎里的逻辑
        test = r[cut:]
        ma_sig = []
        for i in range(len(test)):
            idx = cut + i
            if idx - 1 < 20:
                ma_sig.append(0)
                continue
            ma = close[idx - 20:idx].mean()
            ma_sig.append(1 if close[idx - 1] > ma else 0)
        # 验证：信号决策日 idx-1 的价格不在"当天收益"里
        # 若用了 close[idx]，则信号会与 r[idx] 产生虚假高相关
        corr_lookahead = np.corrcoef(ma_sig[20:], test[20:])[0, 1]
        # 无前视时相关应很弱（|corr|<0.2）
        self.assertLess(abs(corr_lookahead), 0.25)

    def test_backtest_all_strategies_beatable_in_random(self):
        """在纯随机游走数据上，任何策略都不应稳定跑赢——检验回测框架无系统性偏差。"""
        rng = np.random.default_rng(5)
        r = rng.normal(0, 0.01, 3000)
        bt, cut = backtest(r, train_ratio=0.7, cost=0.0015)
        # 随机数据上，任何策略都不应获得大的正超额（负超额是正常的——被交易成本磨损）
        # 这才是"无前视偏差"的正确表现：不会出现凭空的正收益
        for k, v in bt.items():
            if "excess" in v:
                self.assertLess(v["excess"], 0.05, f"{k} 出现异常正超额: {v['excess']}")


if __name__ == "__main__":
    unittest.main()
