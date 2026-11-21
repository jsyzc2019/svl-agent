"""调用点完整性门禁测试（§59：把 §58 的认知断言编译成代码）。

活体回归逐场景 + 规则边界 + R0 输入校验 + 不接入 run_loop 的纪律回归。
"""
import unittest

from svagent.call_site_integrity import (
    CallSiteVerdict, audit_call_site, live_regression,
)


def _cs(**kw):
    base = dict(
        call_site="offline_audit", declared_as_automatic=False,
        positioning_honest=True, caller_real=True, assertion_exists=True,
    )
    base.update(kw)
    return base


class TestCallSiteIntegrity(unittest.TestCase):
    def test_tool_library_preserved(self):
        # §58 本仓六道门禁的真实定位：如实工具库，放行
        v = audit_call_site("本仓门禁", **_cs())
        self.assertEqual((v.action, v.code), ("ok", "CALL_SITE.PRESERVE_TOOL_LIBRARY"))

    def test_dead_code_auto_claim_blocked(self):
        # KB-AUDIT03 原义：无调用点却声称自动 = 死代码
        v = audit_call_site("selftest写好了没调用", **_cs(
            call_site="none", declared_as_automatic=True,
            positioning_honest=False, caller_real=False))
        self.assertEqual(v.action, "block")
        self.assertEqual(v.code, "CALL_SITE.DEAD_CODE_AUTO_CLAIM")

    def test_fabricated_assertion_blocked(self):
        v = audit_call_site("空头声称", **_cs(assertion_exists=False))
        self.assertEqual((v.action, v.code), ("block", "CALL_SITE.FABRICATED_ASSERTION"))

    def test_phantom_wiring_blocked(self):
        v = audit_call_site("幽灵接线", **_cs(
            call_site="online_main_loop", declared_as_automatic=True, caller_real=False))
        self.assertEqual((v.action, v.code), ("block", "CALL_SITE.PHANTOM_WIRING"))

    def test_offline_as_online_downgraded(self):
        v = audit_call_site("离线冒充在线", **_cs(
            declared_as_automatic=True, positioning_honest=False))
        self.assertEqual((v.action, v.code), ("downgrade", "CALL_SITE.OFFLINE_AS_ONLINE"))

    def test_unwired_honest_downgraded(self):
        v = audit_call_site("诚实未接线", **_cs(call_site="none", caller_real=False))
        self.assertEqual((v.action, v.code), ("downgrade", "CALL_SITE.UNWIRED_HONEST"))

    def test_online_wired_ok(self):
        v = audit_call_site("真咬合", **_cs(
            call_site="online_main_loop", declared_as_automatic=True))
        self.assertEqual((v.action, v.code), ("ok", "CALL_SITE.ONLINE_WIRED"))

    def test_undeclared_positioning_flagged(self):
        # 离线 + 如实声明缺失 + 未声称自动 + 调用者真实 → R8 待核
        v = audit_call_site("定位不明", **_cs(
            positioning_honest=False, declared_as_automatic=False, caller_real=True))
        self.assertEqual((v.action, v.code), ("flag", "CALL_SITE.UNDECLARED_POSITIONING"))

    def test_literal_string_rejected(self):
        # brittle 对照：传字面串不进入内容判定
        v = audit_call_site("brittle", **_cs(call_site="高度同构"))
        self.assertEqual((v.action, v.code), ("flag", "CALL_SITE.NON_SEMANTIC_INPUT"))

    def test_non_bool_rejected(self):
        v = audit_call_site("畸形", **_cs(caller_real="yes"))
        self.assertEqual((v.action, v.code), ("flag", "CALL_SITE.NON_SEMANTIC_INPUT"))

    def test_rule_priority_r0_before_r1(self):
        # 非法 call_site + 无断言：R0 输入校验优先于 R1
        v = audit_call_site("双错", **_cs(call_site="高度同构", assertion_exists=False))
        self.assertEqual(v.code, "CALL_SITE.NON_SEMANTIC_INPUT")

    def test_verdict_is_frozen(self):
        v = audit_call_site("冻结", **_cs())
        self.assertIsInstance(v, CallSiteVerdict)
        with self.assertRaises(Exception):
            v.action = "block"

    def test_reinforce_fine_grain_distinction(self):
        # §58 核心增量：死代码 vs 诚实工具库，同是"非在线"但判定不同
        dead = audit_call_site("死代码", **_cs(
            call_site="none", declared_as_automatic=True,
            positioning_honest=False, caller_real=False))
        tool = audit_call_site("工具库", **_cs())
        self.assertEqual(dead.action, "block")
        self.assertEqual(tool.action, "ok")
        self.assertNotEqual(dead.code, tool.code)

    def test_live_regression_all_passed(self):
        r = live_regression()
        self.assertTrue(r["all_passed"])
        self.assertEqual(len(r["cases"]), 8)
        self.assertTrue(all(r["checks"].values()))


if __name__ == "__main__":
    unittest.main()
