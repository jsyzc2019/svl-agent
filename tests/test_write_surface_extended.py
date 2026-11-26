#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4go 测试：元证伪——扩展写路径覆盖，检验 §4gn 阴性结论稳健性。

承 prereg_meta_falsify_write_surface_20261126.json（hash 锁）：
把"内核权威源无生产写点"从只覆盖 open(path,'w') 扩展到
pathlib.write_text/write_bytes、shutil.copy*/move、os.replace/rename、open 全写模式。

覆盖范围（诚实声明）：
- 覆盖：全仓 *.py 的 AST，写 API 调用首参/末参里同时出现 'audit_l3_gap_targeted' 与 'result' 的；
        含变量名绑定与 tmp 豁免（识别 os.path.join(tmp,…) 的测试副本）。
- 未覆盖（不算阴性证据）：eval/exec 动态构造、运行时字符串拼接绕过 AST 常量、
        非 .py 脚本(shell/node)、第三方库内部间接写。
- 因此本测试是"截至此刻、在覆盖面内未发现"，不是"永久证明不可能"。
"""
import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KERNEL_DIR = "audit_l3_gap_targeted"
RESULT = "result.json"
SKIP_DIRS = {"__pycache__", ".git", ".codebuddy", "archive", "node_modules", "vendor"}
# 天然写的 API（不需 mode 判定）
WRITE_ATTRS = {"write_text", "write_bytes", "writelines", "replace", "rename",
               "copy", "copyfile", "copy2", "copytree", "move", "truncate",
               "symlink", "link", "dump"}
WRITE_MODES = {"w", "a", "x", "wb", "ab", "wt", "at", "xt", "w+", "a+", "r+"}


def _segs(node):
    """抓 AST 节点里的字符串常量 + 变量名（后者用于 tmp 豁免识别）。"""
    parts = []
    for n in ast.walk(node):
        if isinstance(n, ast.Constant) and isinstance(n.value, str):
            parts.append(n.value)
        elif isinstance(n, ast.Name):
            parts.append(n.id)
    return " ".join(parts).lower()


def _py_files():
    for dp, dirs, files in os.walk(ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(".py"):
                yield os.path.join(dp, fn)


def _extended_writers_to_kernel():
    """返回扩展写 API 中指向内核权威源、且不在 tmp 副本的位置。"""
    hits = []
    for p in _py_files():
        rel = os.path.relpath(p, ROOT)
        try:
            tree = ast.parse(open(p, encoding="utf-8").read())
        except (SyntaxError, UnicodeDecodeError):
            continue
        for n in ast.walk(tree):
            if not isinstance(n, ast.Call):
                continue
            f = n.func
            nm = f.attr if isinstance(f, ast.Attribute) else (f.id if isinstance(f, ast.Name) else "")
            segs = _segs(n)
            if KERNEL_DIR not in segs or RESULT not in segs:
                continue
            is_write = False
            if nm in WRITE_ATTRS:
                is_write = True
            elif nm == "open":
                modes = [str(a.value) for a in n.args[1:] if isinstance(a, ast.Constant)]
                is_write = any(m in WRITE_MODES for m in modes)
                for kw in n.keywords:
                    if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                        is_write = is_write or kw.value.value in WRITE_MODES
            if not is_write:
                continue
            if "tmp" in segs or "temp" in segs:  # 测试副本豁免
                continue
            hits.append(f"{rel}:{n.lineno}:{nm}")
    return hits


def test_e01_extended_write_surface_still_zero():
    """元证伪主判据：扩展写路径后，内核权威源生产写点仍为0。"""
    hits = _extended_writers_to_kernel()
    assert hits == [], f"§4gn 阴性结论被推翻：扩展扫描发现生产写点 {hits}"


def test_e02_kernel_state_unchanged():
    """内核权威态三值仍 GAP_INCONCLUSIVE/false/false。"""
    import json
    src = os.path.join(ROOT, KERNEL_DIR, RESULT)
    r = json.load(open(src, encoding="utf-8"))
    assert (r["verdict"], r["l3_claimed"], r["absolute_claimed"]) == (
        "GAP_INCONCLUSIVE", False, False)


def test_e03_prereg_sha_intact():
    """元证伪预注册 hash 锁完整（分析前锁存的证据未被事后改动）。"""
    import hashlib
    import json
    p = os.path.join(ROOT, "prereg_meta_falsify_write_surface_20261126.json")
    d = json.load(open(p, encoding="utf-8"))
    claimed = d.pop("sha256")
    actual = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    assert claimed == actual, "预注册 hash 失配：命题被事后改动"
