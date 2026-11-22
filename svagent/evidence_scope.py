"""证据作用域标记 — 让模拟线的报告自带机器可读的诚实标签（审计 F4 诚实杠杆）。

审计发现：autopoiesis/self_evolving/telos/axiology/mechanism/estimation 六个模块
全部由硬编码池 + random.Random(fixed seed) 驱动，但 README 用「天道运行规律的可计算形态」
等措辞陈述，读者极易误读为系统已具备现实世界的自进化能力。

本模块提供一个统一的机器可读标记，各模拟模块 main() 开头打印一行：
  [EVIDENCE_SCOPE] scope=synthetic seed_based=true external_input=false ...
这样任何输出（重定向到日志/文件）都自带诚实边界，无需读者回查文档。

这不是给模拟线降级或否定——它是合法的方法演示；标记只是把「合成世界演示」的
边界摆到最醒目处，防止被误读为真实现实能力（延续 KB-R07 自洽≠有效）。
"""
from __future__ import annotations

import json
from typing import Any


def marker(module: str, *, seed_based: bool = True, external_input: bool = False,
           note: str = "") -> dict[str, Any]:
    """构造一个证据作用域标记（机器可读 dict）。"""
    return {
        "scope": "synthetic",
        "module": module,
        "seed_based": seed_based,
        "external_input": external_input,
        "validity": "method_demo_only",
        "note": note or "合成世界演示：硬编码素材+固定种子，不外推为真实世界自进化能力",
    }


def emit(module: str, *, seed_based: bool = True, external_input: bool = False) -> str:
    """打印并返回标记行（单行 JSON，便于日志/报告机器解析）。"""
    line = "[EVIDENCE_SCOPE] " + json.dumps(
        marker(module, seed_based=seed_based, external_input=external_input),
        ensure_ascii=False,
    )
    print(line)
    return line


def is_synthetic(text: str) -> bool:
    """检测一段报告文本是否声明了 synthetic 作用域。"""
    return "[EVIDENCE_SCOPE]" in text and "synthetic" in text


def live_regression() -> dict:
    checks = {
        "marker_scope": marker("x")["scope"] == "synthetic",
        "marker_validity": marker("x")["validity"] == "method_demo_only",
        "detect_synthetic": is_synthetic("[EVIDENCE_SCOPE] {\"scope\": \"synthetic\"}"),
        "detect_real_negative": not is_synthetic("普通报告文本"),
    }
    return {"checks": checks, "all_passed": all(checks.values())}
