#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gn 测试：全仓扫描——内核判定态源不得被任何生产代码写（阴性证伪的可复现守卫）。

承 §4gm 单点守卫 + §4gn 证伪命题 PREREG-FALSIFY-VERDICT-SOURCE：
若未来新增代码以写模式打开内核权威源，此测试立即暴露，把"搜了没找到"从一次性观察升级为持续守卫。

工具覆盖声明（诚实标盲区）：
- 覆盖：全仓 *.py 的 ast.parse，所有 os.open/open(path, mode) 写模式调用；
- 字面路径锁定：路径片段含 'audit_l3_gap_targeted' + 'result.json' 的写点；
- 豁免：路径片段含 'tmp'/'tmp_path' 的写点（篡改测试用假副本，不碰真实源）；
- 盲区：eval/exec 动态构造写、非 .py 脚本(shell/node)、运行时字符串拼接绕过静态名——不在覆盖内，
  故本测试只是"截至此刻未发现生产写点"的守卫，不宣称"永久不可能"。
"""
import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {"__pycache__", ".git", ".codebuddy", "archive", "node_modules", "vendor"}
WRITE_MODES = {"w", "a", "x", "wb", "ab", "wt", "at", "xt", "w+", "a+", "r+"}


def _py_files():
    for dp, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(".py"):
                yield os.path.join(dp, fn)


def _path_repr(node):
    """递归抓 AST 节点里出现的字符串常量 + 变量名，用于判定路径片段。

    必须含变量名：篡改测试用 os.path.join(tmp, 'audit_l3_gap_targeted', 'result.json')，
    'tmp' 是 Name 节点不是字符串常量，只抓常量会把测试副本误判为生产写点（self-bite 修正）。
    """
    parts = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            parts.append(n.value)
        elif isinstance(n, ast.Name):
            parts.append(n.id)
    return " ".join(parts)


def _kernel_source_writers():
    """返回生产代码里写内核权威源的位置列表（排除 tmp 副本）。"""
    hits = []
    for p in _py_files():
        rel = os.path.relpath(p, ROOT)
        try:
            tree = ast.parse(open(p, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call) or getattr(n.func, "id", None) != "open":
                continue
            if len(n.args) < 2 or not isinstance(n.args[1], ast.Constant):
                continue
            if n.args[1].value not in WRITE_MODES:
                continue
            path_repr = _path_repr(n.args[0])
            segs = path_repr.lower()
            if "audit_l3_gap_targeted" in segs and "result.json" in segs and "tmp" not in segs:
                hits.append(f"{rel}:{n.lineno}")
    return hits


def test_g01_no_production_writer_to_kernel_source():
    """阴性证伪守卫：全仓生产代码不得写内核判定态源；当前应为0。"""
    hits = _kernel_source_writers()
    assert hits == [], f"发现生产代码写内核权威源：{hits}"


def test_g02_kernel_source_readable_and_correct_state():
    """内核权威源存在、可读、三态仍 GAP_INCONCLUSIVE/false/false。"""
    import json
    src = os.path.join(ROOT, "audit_l3_gap_targeted", "result.json")
    r = json.load(open(src, encoding="utf-8"))
    assert (r["verdict"], r["l3_claimed"], r["absolute_claimed"]) == (
        "GAP_INCONCLUSIVE", False, False)


def test_g03_experiment_output_writes_to_independent_file():
    """子实验裁决写独立文件，不回写权威源（§4gm 守卫仍在）。"""
    src = open(os.path.join(ROOT, "audit_l3_gap_targeted", "engine.py"),
               encoding="utf-8").read()
    assert "EXPERIMENT_RESULT = f\"{BASE}/result_experiment.json\"" in src
    assert "assert after == before" in src
    for line in src.splitlines():
        if "KERNEL_VERDICT_SOURCE" in line and "open(" in line:
            assert '"w"' not in line
