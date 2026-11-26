#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gf neff_guard 测试：机制存在性 + 行为回归 + 篡改硬度 + AST 自审。"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from independent_sources import (  # noqa: E402
    NeffVerdict, _KW, live_regression, neff_guard,
)


def test_module_is_pure_no_gate_wiring():
    """纯函数模块：代码体（剥注释/字符串后）不引用判定链/编译门禁。

    自咬：首版直接扫全文，被"不接 run_loop"这类纪律注释误伤——
    检测对象应是代码行为，不是注释文字。按纪律改测试不动模块。
    """
    src = open(os.path.join(ROOT, "independent_sources.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    # 去掉所有字符串常量节点后重建源码：只留真实代码结构（标识符/调用/赋值）
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            node.value = ""
    code_only = ast.dump(tree)
    for banned in ("run_loop", "compile_gate", "l3_claimed", "verdict=GAP"):
        assert banned not in code_only


def test_neff_guard_qualified_pass():
    v = neff_guard([{"text": "多源交叉验证",
                     _KW["field_error_source"]: _KW["value_cross_model"],
                     _KW["field_neff"]: 4, "n_sources": 10}])
    assert v[0].status == "QUALIFIED_OK"


def test_unqualified_blocked():
    v = neff_guard([{"text": "独立验证通过"}])
    assert v[0].status == "UNQUALIFIED_INDEPENDENCE_CLAIM"
    assert v[0].suggested_ceiling is not None  # 要求补注折减


def test_same_family_discounted():
    v = neff_guard([{"text": "独立agent交叉",
                     _KW["field_error_source"]: _KW["value_same_family"], "n_sources": 9}])
    assert v[0].suggested_ceiling < 9  # 同家族须折减，不数源个数


def test_cross_model_not_full_independence():
    v = neff_guard([{"text": "交叉验证",
                     _KW["field_error_source"]: _KW["value_cross_model"], "n_sources": 10}])
    assert v[0].suggested_ceiling < 10  # 缓解非消除


def test_tamper_neff_overclaim_flips():
    v = neff_guard([{"text": "多源交叉",
                     _KW["field_error_source"]: _KW["value_same_family"],
                     _KW["field_neff"]: 9, "n_sources": 9}])
    assert v[0].status == "NEFF_OVERCLAIMED"


def test_unknown_source_not_silently_passed():
    v = neff_guard([{"text": "独立judge", _KW["field_error_source"]: "unknown"}])
    assert v[0].status == "UNKNOWN_SOURCE"


def test_non_multi_source_skipped():
    assert neff_guard([{"text": "天气很好"}])[0].status == "NOT_MULTI_SOURCE_CLAIM"


def test_live_regression_all_green():
    r = live_regression()
    assert len(r) >= 7 and all(r.values())


def test_ast_no_cjk_in_compare():
    """延续 §4ge 自咬：Compare 比较子不得嵌中文字面量。"""
    tree = ast.parse(open(os.path.join(ROOT, "independent_sources.py"), encoding="utf-8").read())
    bad = [(n.lineno, c.value) for n in ast.walk(tree) if isinstance(n, ast.Compare)
           for c in n.comparators if isinstance(c, ast.Constant) and isinstance(c.value, str)
           and any(ord(ch) > 127 for ch in c.value)]
    assert not bad, f"CJK literal in Compare: {bad[:5]}"


def test_no_trophy_language():
    v = neff_guard([{"text": "多源交叉", _KW["field_error_source"]: _KW["value_rule"],
                     _KW["field_neff"]: 1, "n_sources": 1}])
    assert not any(s in v[0].status for s in ("OVERTHROWN", "VICTORY", "PROVEN"))
