#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gg · 数字诚实判据测试：确保校验器真正接入 pytest 套件。

关键元测试 test_checker_is_wired：伪造一份'不含本文件'的收集集，
wiring_self_check 必须判 False；用真实收集集则必须判 True。
旧一致性脚本正是死在'存在但没接线'，本测试专治此病。
"""
import json
import os
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "life_kernel"))
import numeric_honesty as nh  # noqa: E402


def test_live_regression_all_green():
    r = nh.live_regression()
    assert all(r.values()), r


def test_known_error_is_caught_not_excused():
    """校准 C1：权威行 471 / 真值 470 必须判 FAIL——判据不得放过已知错误。"""
    truth = {"kb_count": 470, "safari_rounds": 133, "constitution_prefix": "fe56291b",
             "verdict": "GAP_INCONCLUSIVE", "l3_claimed": False, "absolute_claimed": False,
             "test_count": None}
    line = ("- **权威现状**：全量测试 **1562**、知识库 **471** 条、Safari 台账 **133** 轮、"
            "宪法锁 SHA256 `fe56291b…`、`verdict=GAP_INCONCLUSIVE`、`l3=false`、`absolute=false`。")
    r = nh.check_handoff(line, truth)
    assert (not r["ok"]) and "kb_count" in r["failed"]


def test_matching_line_passes():
    truth = {"kb_count": 470, "safari_rounds": 133, "constitution_prefix": "fe56291b",
             "verdict": "GAP_INCONCLUSIVE", "l3_claimed": False, "absolute_claimed": False,
             "test_count": None}
    line = ("- **权威现状**：全量测试 **1562**、知识库 **470** 条、Safari 台账 **133** 轮、"
            "宪法锁 SHA256 `fe56291b…`、`verdict=GAP_INCONCLUSIVE`、`l3=false`、`absolute=false`。")
    assert nh.check_handoff(line, truth)["ok"] is True


def test_history_snapshot_line_does_not_pollute():
    """旧速查表的 466 是历史快照，不得干扰权威行判定。"""
    truth = {"kb_count": 470, "safari_rounds": 133, "constitution_prefix": "fe56291b",
             "verdict": "GAP_INCONCLUSIVE", "l3_claimed": False, "absolute_claimed": False,
             "test_count": None}
    text = ("| 知识库 | `knowledge_base_store.json`（466 条 ...\n"
            "- **权威现状**：全量测试 **1562**、知识库 **470** 条、Safari 台账 **133** 轮、"
            "宪法锁 SHA256 `fe56291b…`、`verdict=GAP_INCONCLUSIVE`、`l3=false`、`absolute=false`。")
    assert nh.check_handoff(text, truth)["ok"] is True


def test_real_handoff_is_consistent_after_repair():
    """修复后真实 handoff 必须与现场权威源一致——这是本判据接入套件的最终目的。"""
    t = nh.truth_snapshot()
    r = nh.check_handoff(nh._read("SESSION_HANDOFF.md"), t)
    assert r["ok"], f"handoff 与现场不一致: failed={r['failed']}"


def test_checker_is_wired_into_pytest():
    """元纪律：本文件必须真的在 pytest 收集集里；伪造缺席收集集必须被识破。"""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "-p", "no:cacheprovider",
         "--override-ini=addopts=", "--collect-only", "-q"],
        cwd=ROOT, capture_output=True, text=True, timeout=120,
    )
    nodeids = proc.stdout.splitlines()
    assert nh.wiring_self_check(nodeids) is True, "校验器未接入 pytest 收集集(DISCONNECTED)"
    fake = [n for n in nodeids if "test_numeric_honesty" not in n]
    assert nh.wiring_self_check(fake) is False, "接线自检未能识破缺席"


def test_module_is_pure_no_gate_wiring():
    """剥掉注释/文档串后的代码体不得引用判定链符号。"""
    import ast
    src = open(os.path.join(ROOT, "life_kernel", "numeric_honesty.py"), encoding="utf-8").read()
    tree = ast.parse(src)
    strings = {n.value for n in ast.walk(tree)
               if isinstance(n, ast.Constant) and isinstance(n.value, str)}
    body_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            body_names.add(node.id)
        if isinstance(node, ast.Attribute):
            body_names.add(node.attr)
    banned = {"run_loop", "verdict", "l3_claimed", "absolute_claimed", "compile_gate"}
    # 只允许它们作为字符串键/正则/文档出现，不允许作为代码标识符被执行
    assert not (body_names & banned), body_names & banned
    # 战利品语言由 live_regression 的 no_trophy_language 检查输出；
    # 其禁用词表本身必然出现在源码字符串中，故不在此处扫源码(否则误报自咬)。
    assert "no_trophy_language" in nh.live_regression()
