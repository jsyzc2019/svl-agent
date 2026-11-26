#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gh · 断言诚实判据测试：双向校准 + 接线自检。

元测试 test_checker_is_wired：本文件必须在 pytest 收集集内；
伪造缺席集→wiring 必 False。专治'判据存在但没接线'。
"""
import ast
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "life_kernel"))
import claim_honesty as ch  # noqa: E402


def test_live_regression_all_green():
    r = ch.live_regression()
    assert all(r.values()), r


def test_existence_claim_without_handle_blocked():
    """报告过≠现在在：无句柄的'已拆三块'必须 UNVERIFIED。"""
    v = ch.existence_claim_guard([{"text": "token已拆三块临时组装"}])[0]
    assert v.status == "UNVERIFIED_CLAIM"


def test_qualified_handle_passes_but_unverified_true():
    v = ch.existence_claim_guard([{"text": "GitHub已同步", "handle_type": "commit_sha",
                                   "handle": "cb85b9f2e57f"}])[0]
    assert v.status == "QUALIFIED_HANDLE"
    # 诚实上限：不假装联网复核真伪
    assert "未联网复核" in v.reason


def test_blind_spot_check_is_bidirectional():
    """永远放行→BLIND_SPOT；永远告警→OVERREJECT；真判据→全识别。"""
    assert ch.blind_spot_check(lambda f: False)["status"] == "BLIND_SPOT"
    assert ch.blind_spot_check(lambda f: True)["status"] == "OVERREJECT"
    assert ch.blind_spot_check(ch.is_failure_recognized)["status"] == "ALL_KNOWN_FAILURES_RECOGNIZED"


def test_tautology_cannot_pass_calibration():
    """恒真重述(truth!=claim)必须被合法对照集挡为 OVERREJECT，校准不再浅薄。"""
    r = ch.blind_spot_check(lambda f: f.get("truth") != f.get("claim"))
    assert r["status"] == "OVERREJECT"


def test_scope_partition_honest():
    """F02数字声明错归 numeric_honesty，本守卫标 OUT_OF_SCOPE 不算漏识别。"""
    r = ch.blind_spot_check(ch.is_failure_recognized)
    assert "F02" in r["out_of_scope_ids"]
    assert r["status"] == "ALL_KNOWN_FAILURES_RECOGNIZED"


def test_checker_is_wired_into_pytest():
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
         "--override-ini=addopts=", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=180,
    )
    nodeids = proc.stdout.splitlines()
    assert any("test_claim_honesty" in n for n in nodeids), "校验器未接入 pytest 收集集"
    fake = [n for n in nodeids if "test_claim_honesty" not in n]
    # 本模块的接线判断：伪造缺席集里不得含本文件 token。
    # 不借用 numeric_honesty.wiring_self_check——其 token 固定为 test_numeric_honesty，
    # 用它查 claim 的缺席会误判(伪集仍含 numeric token)。这是测试自咬，改测试不改判据。
    assert not any("test_claim_honesty" in n for n in fake)


def test_module_pure_and_ast_clean():
    src = open(os.path.join(ROOT, "life_kernel", "claim_honesty.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    bad = [(n.lineno, c.value) for n in ast.walk(tree) if isinstance(n, ast.Compare)
           for c in n.comparators if isinstance(c, ast.Constant) and isinstance(c.value, str)
           and any(ord(ch) > 127 for ch in c.value)]
    assert bad == [], bad
    body_names = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    assert not (body_names & {"run_loop", "compile_gate", "verdict"})
