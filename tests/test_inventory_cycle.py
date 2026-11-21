"""库存周期判据的回归测试（不依赖网络，用真实数据缓存）。"""
import unittest
from svagent.inventory_cycle import (
    load_data, classify, find_transitions, ablation,
    PREREG, PHASE_NAMES, _direction, _smooth,
)


class TestInventoryCycle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.monthly, cls.ppi = load_data()
        cls.states = classify(cls.monthly, cls.ppi)
        cls.by_p = {s.period: s for s in cls.states}

    def test_data_is_real_and_loaded(self):
        """真实数据缓存应加载足够多月份。"""
        self.assertGreater(len(self.monthly), 40)
        self.assertGreater(len(self.ppi), 40)
        self.assertIn("2026-09", self.monthly)

    def test_prereg_frozen(self):
        """预注册参数固定（防事后调参）。"""
        self.assertEqual(PREREG["smooth_window"], 3)
        self.assertEqual(PREREG["deadband_pct"], 0.15)
        self.assertEqual(PREREG["focus_end"], "2026-09")

    def test_direction_deadband(self):
        self.assertEqual(_direction(0.5, 0.15), "up")
        self.assertEqual(_direction(-0.5, 0.15), "down")
        self.assertEqual(_direction(0.05, 0.15), "flat")

    def test_2025_10_passive_restocking(self):
        """2025-10/11 名义口径应判为被动补库（营收降+库存升）。"""
        for p in ["2025-10", "2025-11", "2025-12"]:
            self.assertIn("被动补库", self.by_p[p].phase, f"{p} 应为被动补库")

    def test_2026_active_restocking(self):
        """2026 年中应为主动补库（营收升+库存升），对死区不敏感。"""
        for db in [0.05, 0.15, 0.40]:
            st = classify(self.monthly, self.ppi, deadband=db)
            p2607 = {s.period: s for s in st}["2026-07"]
            self.assertEqual(p2607.phase, "主动补库", f"死区{db}下2026-07应为主动补库")

    def test_nominal_vs_real_decomposition(self):
        """名义库存高增含PPI价格效应：2026-09实际库存应显著低于名义。"""
        s = self.by_p["2026-09"]
        self.assertGreater(s.inv_yoy, 10)          # 名义>10%
        self.assertGreater(s.ppi_yoy, 4)           # PPI>4%
        self.assertLess(s.inv_real_yoy, s.inv_yoy - 4)  # 实际显著低于名义

    def test_transition_order(self):
        """阶段切换应按时间有序产出。"""
        tr = find_transitions(self.states)
        periods = [t[0] for t in tr]
        self.assertEqual(periods, sorted(periods))

    def test_missing_data_is_honest(self):
        """缺失数据应保留为 None，不臆断。"""
        st_all = classify(self.monthly, self.ppi, focus_start="2022-01", focus_end="2026-09")
        missing = [s for s in st_all if s.missing]
        # 2023 上半年营收缺失应被如实标记
        self.assertTrue(any(s.period.startswith("2023-0") for s in missing))

    def test_ablation_runs(self):
        """消融实验应产出所有窗口/口径组合。"""
        r = ablation(self.monthly, self.ppi)
        self.assertEqual(len(r), 8)  # 4窗口 × 2口径


if __name__ == "__main__":
    unittest.main()
