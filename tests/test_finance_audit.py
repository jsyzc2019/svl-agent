"""财报判定模块测试：基于落盘的真实数据（不联网），覆盖坍塌判据与两个数据揭穿的bug回归。"""
import unittest

from svagent.finance_fetch import load_all
from svagent.finance_audit import (
    AuditReport, audit, audit_all, collapse_audit_opinion, collapse_balance_identity,
    collapse_cash_quality, RESIDUAL_RISKS,
)


class TestFinanceFetch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rs = load_all()

    def test_five_companies_loaded(self):
        self.assertEqual(len(self.rs), 5)
        self.assertEqual({r.code for r in self.rs},
                         {"601166", "002415", "000725", "600518", "300104"})

    def test_each_has_five_annual_years(self):
        for r in self.rs:
            self.assertEqual(len(r.years), 5, f"{r.name} 年份数异常: {r.years}")

    def test_seucode_never_rejected_in_saved_data(self):
        # 落盘数据里不应混入别家公司（取数时已校验）
        for r in self.rs:
            for src in ("income", "balance", "cashflow", "main"):
                for row in getattr(r, src).values():
                    if row:
                        self.assertEqual(row.get("SECUCODE"), r.secucode)

    def test_bank_fallback_annotated(self):
        bank = next(x for x in self.rs if x.code == "601166")
        self.assertTrue(any("fallback" in e for e in bank.errors),
                        "银行简版表fallback应被如实标注")


class TestCollapse(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rs = {r.code: r for r in load_all()}

    def test_balance_identity_holds_for_clean_companies(self):
        for code in ("002415", "000725"):
            diags = collapse_balance_identity(self.rs[code])
            self.assertFalse([d for d in diags if d.severity == "block"],
                             f"{code} 会计恒等式不应违约")
            self.assertTrue(any(d.code == "FIN.BALANCE.OK" for d in diags))

    def test_negative_denominator_not_reported_as_ratio(self):
        """bug回归：京东方2022合并净利<0，旧代码算出-24.72的荒谬比率。"""
        diags = collapse_cash_quality(self.rs["000725"])
        self.assertFalse([d for d in diags if d.code == "FIN.CASH.LOW"
                          and "2022" in d.locus.ref], "负分母不应报现金含量低")
        self.assertTrue(any(d.code == "FIN.CASH.NEGDENOM" and "2022" in d.locus.ref
                            for d in diags))

    def test_audit_opinion_emphasis_is_flag_not_block(self):
        """bug回归：乐视2016'带强调事项段的无保留意见'曾被'保留'二字误判为block。"""
        diags = collapse_audit_opinion(self.rs["300104"])
        e2016 = [d for d in diags if "2016" in d.locus.ref]
        self.assertTrue(any(d.code == "FIN.OPINION.EMPHASIS" for d in e2016))
        self.assertFalse(any(d.severity == "block" for d in e2016))

    def test_audit_opinion_nonstandard_is_block(self):
        diags = collapse_audit_opinion(self.rs["300104"])
        self.assertTrue(any(d.code == "FIN.OPINION.NONSTANDARD" and "2017" in d.locus.ref
                            for d in diags), "无法表示意见应为block")

    def test_missing_field_is_flag_not_fabricated(self):
        bank = self.rs["601166"]
        diags = audit(bank)
        missing = [d for d in diags if d.code.endswith(".MISSING")]
        self.assertTrue(missing, "银行简版表缺字段应产生MISSING flag")
        self.assertTrue(all(d.severity == "flag" for d in missing),
                        "缺字段不能当成硬违约")


class TestDetection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.reports = {r.company: r for r in audit_all()}
        cls.rs = {r.name: r for r in load_all()}

    def test_clean_companies_zero_block(self):
        for name in ("兴业银行", "海康威视", "京东方A"):
            self.assertEqual(len(self.reports[name].blocks), 0, f"{name} 不应有误杀block")

    def test_fraud_cases_detected(self):
        self.assertGreater(len(self.reports["康美药业"].blocks), 0)
        self.assertGreater(len(self.reports["乐视网"].blocks), 0)

    def test_kangmei_early_detection_before_audit(self):
        """核心检验：康美2016-2017审计仍标准无保留时，现金判据已报警。"""
        km = self.rs["康美药业"]
        early = [y for y in ("2016", "2017") if "标准无保留" in str(km.opinion.get(y, ""))]
        self.assertEqual(len(early), 2, "康美2016-2017应为标准无保留")
        flags = [d for d in self.reports["康美药业"].diagnostics
                 if d.locus.ref.split("·")[0] in early
                 and d.code in ("FIN.CASH.LOW", "FIN.RECEIPT.LOW")]
        self.assertGreaterEqual(len(flags), 1, "造假暴露前应至少有现金类提前信号")

    def test_audit_opinion_is_lagging_label(self):
        """审计意见是事后标签，不算提前证据——诚实性测试。"""
        km = self.rs["康美药业"]
        self.assertIn("标准无保留", str(km.opinion["2016"]))
        self.assertNotIn("标准无保留", str(km.opinion["2019"]))

    def test_handoff_cards_are_local_units(self):
        rep = self.reports["康美药业"]
        cards = rep.handoff_cards()
        self.assertTrue(cards)
        self.assertTrue(all("人工问题" in c and "凭证" in c for c in cards))
        self.assertTrue(all("？" in c["人工问题"] for c in cards),
                        "每张卡应是一个可局部裁决的问题")

    def test_residual_risks_declared(self):
        self.assertGreaterEqual(len(RESIDUAL_RISKS), 4)
        self.assertTrue(any("关联交易" in r for r in RESIDUAL_RISKS))
        self.assertTrue(any("收入确认" in r for r in RESIDUAL_RISKS))

    def test_verdict_reflects_blocks_and_flags(self):
        self.assertIn("硬违约", self.reports["乐视网"].verdict())
        self.assertIn("未违反硬判据", self.reports["兴业银行"].verdict())


if __name__ == "__main__":
    unittest.main(verbosity=2)
