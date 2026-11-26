#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gg · 数字诚实守卫：核对 handoff 权威行声明值 vs 现场权威源真值。

承 §4gg 诊断的三重失效链：
- f1 报告 KB=471、现场 470（§4gf 条目漏落却报成功）；
- f2 handoff 权威行写了错值；
- f3 旧一致性脚本正则抓错字段(速查表 466)且不在 pytest 套件 → 全量全绿放过。

设计纪律（与 evidence_honesty.py / independent_sources.py 同族）：
- 纯函数，不联网、不 spawn、不接 run_loop、不编译门禁、不改判定态。
- 只从明确锚定的'权威现状'那一行解析声明值，绝不扫全文/历史快照行。
- 测试计数是运行时产物，无静态权威源：由调用方传入，未传则标 UNKNOWN 不强行判等。
- 中文关键词与正则模板集中字典，比较逻辑只查 ASCII 键，避免 AST Compare 中文字面量自咬。
- 元纪律 wiring_self_check：判据自身的测试必须在 pytest 收集集内，否则判 DISCONNECTED。
"""
import hashlib
import json
import os
import re
from typing import Any, Dict, List, Optional

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---- 中文关键词 / 正则模板集中字典 ----
_KW: Dict[str, str] = {
    "anchor": "权威现状",
    "field_test": "全量测试",
    "field_kb": "知识库",
    "field_rounds": "Safari 台账",
    "field_constitution": "宪法锁",
    "verdict": "verdict",
    "l3": "l3",
    "absolute": "absolute",
}

_PAT: Dict[str, str] = {
    "test": r"全量测试\s*\*\*(\d+)\*\*",
    "kb": r"知识库\s*\*\*(\d+)\*\*\s*条",
    "rounds": r"Safari\s*台账\s*\*\*(\d+)\*\*\s*轮",
    "constitution": r"宪法锁\s*SHA256\s*`([0-9a-fA-F]{8})",
    "verdict": r"verdict\s*=\s*([A-Z_]+)",
    "l3": r"`?l3\s*=\s*(true|false)",
    "absolute": r"`?absolute\s*=\s*(true|false)",
}

# 接线自检：期望在 pytest 收集集里出现的测试文件名片段
_WIRING_TOKEN = "test_numeric_honesty"


def _read(p: str) -> str:
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def truth_snapshot(test_count: Optional[int] = None) -> Dict[str, Any]:
    """从权威源现场取真值。测试计数无静态权威源，未传则 None(判据不判等)。"""
    kb = json.loads(_read("knowledge_base_store.json"))
    items = kb.get("items", [])
    ids = [x.get("item_id", "") for x in items]
    result = json.loads(_read("audit_l3_gap_targeted/result.json"))
    constitution = _read("life_kernel/constitution.sha256").split()[0][:8]
    rounds = sum(1 for _ in open(os.path.join(ROOT, "life_kernel/data/safari_log.jsonl"),
                                 encoding="utf-8"))
    return {
        "kb_count": len(items),
        "kb_dup": len(ids) - len(set(ids)),
        "safari_rounds": rounds,
        "constitution_prefix": constitution,
        "verdict": str(result.get("verdict", "")),
        "l3_claimed": bool(result.get("l3_claimed")),
        "absolute_claimed": bool(result.get("absolute_claimed")),
        "test_count": test_count,
    }


def _to_bool(token: str) -> bool:
    return token.lower() == "true"


def parse_authority_line(handoff_text: str) -> Dict[str, Any]:
    """只解析锚定的'权威现状'那一行；缺锚点返回空解析(由 check 判 MISSING_ANCHOR)。"""
    line = None
    for ln in handoff_text.splitlines():
        if _KW["anchor"] in ln:
            line = ln
            break
    if line is None:
        return {"_found": False}
    out: Dict[str, Any] = {"_found": True}
    for key in ("test", "kb", "rounds", "constitution", "verdict", "l3", "absolute"):
        m = re.search(_PAT[key], line)
        out[key] = m.group(1) if m else None
    return out


def check_handoff(handoff_text: str, truth: Dict[str, Any]) -> Dict[str, Any]:
    """逐字段核对声明 vs 真值。返回 checks 明细 + failed 清单 + ok。"""
    parsed = parse_authority_line(handoff_text)
    checks: Dict[str, bool] = {}
    failed: List[str] = []
    if not parsed.get("_found"):
        return {"ok": False, "checks": {}, "failed": ["MISSING_ANCHOR"], "parsed": parsed,
                "boundary": "纯核对；不改文件；历史快照行不参与；测试计数未传则不判等。"}

    def cmp(field: str, declared: Any, actual: Any) -> None:
        ok = (declared == actual)
        checks[field] = ok
        if not ok:
            failed.append(field)

    cmp("kb_count", int(parsed["kb"]) if parsed["kb"] else None, truth["kb_count"])
    cmp("safari_rounds", int(parsed["rounds"]) if parsed["rounds"] else None, truth["safari_rounds"])
    cmp("constitution_prefix",
        parsed["constitution"].lower() if parsed["constitution"] else None,
        str(truth["constitution_prefix"]).lower())
    cmp("verdict", parsed["verdict"], truth["verdict"])
    cmp("l3_claimed", _to_bool(parsed["l3"]) if parsed["l3"] else None, truth["l3_claimed"])
    cmp("absolute_claimed", _to_bool(parsed["absolute"]) if parsed["absolute"] else None,
        truth["absolute_claimed"])
    # 测试计数：仅当调用方给了真值且权威行有声明时才判等，否则记 UNKNOWN 不拉低 ok
    if truth.get("test_count") is not None and parsed["test"]:
        cmp("test_count", int(parsed["test"]), truth["test_count"])
    else:
        checks["test_count"] = None
    hard_failed = [f for f in failed]
    return {"ok": len(hard_failed) == 0, "checks": checks, "failed": hard_failed,
            "parsed": parsed,
            "boundary": "纯核对；不改文件；历史快照行不参与；测试计数未传则不判等。"}


def wiring_self_check(collected_nodeids: List[str]) -> bool:
    """元纪律：判据自身的测试必须出现在 pytest 收集集；否则判 DISCONNECTED。"""
    return any(_WIRING_TOKEN in str(nid) for nid in collected_nodeids)


def live_regression() -> Dict[str, bool]:
    """活体回归：用构造样本测纯函数行为，不依赖当前 handoff 真实值(避免修复前后翻转)。"""
    r: Dict[str, bool] = {}
    truth = {"kb_count": 470, "safari_rounds": 133, "constitution_prefix": "fe56291b",
             "verdict": "GAP_INCONCLUSIVE", "l3_claimed": False, "absolute_claimed": False,
             "test_count": 1562}
    good = ("- **权威现状（x）**：全量测试 **1562**（+0）、知识库 **470** 条、"
            "Safari 台账 **133** 轮、宪法锁 SHA256 `fe56291b…` 一致；"
            "`verdict=GAP_INCONCLUSIVE`、`l3=false`、`absolute=false`、`Ambient=0`。")
    r["good_line_passes"] = check_handoff(good, truth)["ok"]
    bad_kb = good.replace("知识库 **470** 条", "知识库 **471** 条")
    res = check_handoff(bad_kb, truth)
    r["known_error_caught"] = (not res["ok"]) and ("kb_count" in res["failed"])
    bad_verdict = good.replace("verdict=GAP_INCONCLUSIVE", "verdict=CONFIRMED")
    r["verdict_tamper_caught"] = "verdict" in check_handoff(bad_verdict, truth)["failed"]
    bad_l3 = good.replace("l3=false", "l3=true")
    r["l3_tamper_caught"] = "l3_claimed" in check_handoff(bad_l3, truth)["failed"]
    r["missing_anchor_caught"] = (not check_handoff("无权威行", truth)["ok"])
    r["wiring_connected_true"] = wiring_self_check(["tests/test_numeric_honesty.py::t"])
    r["wiring_disconnected_false"] = (not wiring_self_check(["tests/test_unrelated.py::t"]))
    # 历史快照行不得干扰：把旧值 466 塞进另一行，权威行仍正确 → PASS
    with_history = "| 知识库 | `knowledge_base_store.json`（466 条 ...\n" + good
    r["history_line_ignored"] = check_handoff(with_history, truth)["ok"]
    r["no_trophy_language"] = all(
        s not in json.dumps(res, ensure_ascii=False) for s in ("VICTORY", "OVERTHROWN", "PROVEN"))
    return r


if __name__ == "__main__":
    print(json.dumps(live_regression(), ensure_ascii=False, indent=1))
