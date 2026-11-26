#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gm 测试：内核判定态源与子实验裁决的职责分离（承 §4gl ENGINE_LOG 待改进点）。

守卫三条：
1. engine.py 运行前后 result.json 三态字节不变（正向：真实交付回放仍 GAP_CLOSED，权威源不动）。
2. 若 engine 回写权威源，三态快照守卫必须抛错（负向：自咬证明守卫非摆设）。
3. 内核权威态三值仍为 GAP_INCONCLUSIVE/false/false（判定态不自抬）。
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(ROOT, "audit_l3_gap_targeted", "engine.py")
AUTH = os.path.join(ROOT, "audit_l3_gap_targeted", "result.json")
KERNEL_OK = ("GAP_INCONCLUSIVE", False, False)


def _sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _snapshot(p):
    r = json.load(open(p, encoding="utf-8"))
    return (r["verdict"], r["l3_claimed"], r["absolute_claimed"])


@pytest.fixture
def sandbox(tmp_path):
    """在临时目录复制 engine 所需_two_目录，隔离真实权威源。"""
    for d in ("audit_l3_gap_targeted", "audit_frozen_holdout"):
        shutil.copytree(os.path.join(ROOT, d), tmp_path / d,
                        ignore=shutil.ignore_patterns("__pycache__"))
    return tmp_path


def _run(tmp_path, ext="audit_l3_gap_targeted/received/l3_external_audit_v2"):
    return subprocess.run(
        [sys.executable, "audit_l3_gap_targeted/engine.py", ext],
        cwd=str(tmp_path), capture_output=True, text=True, timeout=60)


def test_v01_kernel_authority_current_value():
    """内核权威源三态仍是 GAP_INCONCLUSIVE/false/false，本轮不自抬。"""
    assert _snapshot(AUTH) == KERNEL_OK


def test_v02_engine_writes_experiment_not_authority(sandbox):
    """正向：真实交付回放仍得 GAP_CLOSED，但写的是独立文件，权威源字节不变。"""
    auth = sandbox / "audit_l3_gap_targeted" / "result.json"
    exp = sandbox / "audit_l3_gap_targeted" / "result_experiment.json"
    before = _sha(auth)
    r = _run(sandbox)
    assert r.returncode == 0, r.stderr
    assert _sha(auth) == before, "权威判定态源被 engine 运行污染"
    assert exp.exists(), "子实验裁决未写独立文件"
    got = json.load(open(exp, encoding="utf-8"))
    assert got["verdict"] == "GAP_CLOSED"
    assert got["mechanical_comparison"]["assertion_family_detected"] == "4/4"
    assert got["l3_claimed"] is False and got["absolute_claimed"] is False


def test_v03_guard_catches_authority_pollution(sandbox):
    """负向：把 engine 写目标改回权威源，三态守卫必须抛错退出码非0。"""
    ep = sandbox / "audit_l3_gap_targeted" / "engine.py"
    src = ep.read_text(encoding="utf-8")
    tampered = src.replace('open(EXPERIMENT_RESULT, "w"',
                           'open(KERNEL_VERDICT_SOURCE, "w"')
    assert tampered != src, "变体构造失败：写目标未替换"
    ep.write_text(tampered, encoding="utf-8")
    r = _run(sandbox)
    assert r.returncode != 0, "守卫未拦截对权威源的回写"
    assert "污染" in r.stderr


def test_v04_authority_readonly_by_engine_source():
    """源码静态断言：engine 对权威源只读不写（写目标须为 EXPERIMENT_RESULT）。"""
    src = open(ENGINE, encoding="utf-8").read()
    assert "KERNEL_VERDICT_SOURCE = f\"{BASE}/result.json\"" in src
    assert "EXPERIMENT_RESULT = f\"{BASE}/result_experiment.json\"" in src
    assert "kernel_state_snapshot()" in src
    # 权威源只出现在快照读取路径，不出现在任何写模式
    for line in src.splitlines():
        if "KERNEL_VERDICT_SOURCE" in line and "open(" in line:
            assert '"w"' not in line, "权威源被以写模式打开"
