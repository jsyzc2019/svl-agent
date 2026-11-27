#!/usr/bin/env python3
"""记忆治理审计器官（§4hc，按 prereg_memory_governance_20261127.json 预注册）。

纯函数：只读 KB，审可纠错溯源完整性 + 少而精结构体检。
硬边界：只生成候选 provenance，不自动写回 KB 正文；改写交用户裁定。
"""
from __future__ import annotations

import re
from collections import Counter
from typing import List, Dict, Any

PATH_RE = re.compile(r"[A-Za-z0-9_./-]+\.(?:py|json|md|html|jsonl|txt)")
# 不用 \b：Python re 把中文当 word char，紧跟中文的 sha/§4xx 会抽不到（§4hc self-bite）
SHA_RE = re.compile(r"(?<![0-9a-zA-Z])[0-9a-fA-F]{8,}(?![0-9a-zA-Z])")
ROUND_RE = re.compile(r"§4[a-z]{1,3}")


def audit_provenance(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """MG1+MG2：找缺 provenance 的条目，并判每条锚点可恢复性。"""
    missing = []
    for x in items:
        pv = x.get("provenance")
        if not pv or (isinstance(pv, str) and not pv.strip()):
            text = str(x.get("mechanism", "")) + " " + str(x.get("support", ""))
            paths = sorted(set(PATH_RE.findall(text)))
            shas = sorted(set(SHA_RE.findall(text)))
            rounds = sorted(set(ROUND_RE.findall(text)))
            recoverable = bool(paths or shas or rounds)
            missing.append({
                "item_id": x.get("item_id"),
                "kind": x.get("kind"),
                "recoverable": recoverable,
                "anchors": {"paths": paths[:8], "shas": shas[:8], "rounds": rounds[:8]},
                "verdict": "RECOVERABLE" if recoverable else "UNRECOVERABLE",
            })
    n_unrec = sum(1 for m in missing if m["verdict"] == "UNRECOVERABLE")
    if not missing:
        verdict = "NO_GAP"
    elif n_unrec:
        verdict = "GAP_UNRECOVERABLE"
    else:
        verdict = "GOVERNANCE_GAP_FOUND"
    return {"verdict": verdict, "missing_count": len(missing), "unrecoverable_count": n_unrec,
            "items": missing}


def audit_field_shape(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """MG3 观察项：字段出现率 + support 形态分布（不改口径）。"""
    keys = Counter()
    for x in items:
        for k in x.keys():
            keys[k] += 1
    shapes = Counter()
    for x in items:
        s = x.get("support")
        if isinstance(s, list):
            shapes["list"] += 1
        elif isinstance(s, (int, float)) and not isinstance(s, bool):
            shapes["number"] += 1
        elif isinstance(s, str):
            shapes["string"] += 1
        else:
            shapes[type(s).__name__] += 1
    return {"n": len(items), "field_presence": dict(keys),
            "support_shape": dict(shapes)}


def suggest_provenance(recoverable_item: Dict[str, Any]) -> str:
    """从可恢复条目的锚点机械拼候选 provenance——是建议非事实，不写回。"""
    a = recoverable_item.get("anchors", {})
    parts = []
    if a.get("paths"):
        parts.append("+".join(a["paths"][:6]))
    if a.get("shas"):
        parts.append("sha:" + ",".join(a["shas"][:4]))
    if a.get("rounds"):
        parts.append("轮次:" + ",".join(a["rounds"][:4]))
    return "候选(非自动采纳): " + " | ".join(parts) if parts else "候选: UNRECOVERABLE"


def evaluate(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    prov = audit_provenance(items)
    shape = audit_field_shape(items)
    suggestions = [{"item_id": m["item_id"], "candidate": suggest_provenance(m)}
                   for m in prov["items"] if m["recoverable"]]
    return {
        "verdict": prov["verdict"],
        "mg1_provenance": prov,
        "mg3_field_shape": shape,
        "suggestions": suggestions,
        "hard_limit": "候选 provenance 仅建议，不自动写回 KB；不改 improvement_class/support 口径；判定态不动。",
    }


def negative_self_bite():
    """三注入：防器官误报/臆造。"""
    base = {"item_id": "X", "kind": "thinking_experience", "mechanism": "m", "support": "s",
            "trigger": "t", "action": "a", "timestamp": "x", "evidence": "e",
            "addressable": False, "improvement_class": "fix"}
    # 1) 完整 provenance → 不得报缺失
    complete = dict(base, provenance="some_real_source.py+prereg")
    r1 = audit_provenance([complete])
    # 2) 缺 provenance 但无锚点 → 必须 UNRECOVERABLE
    noanchor = dict(base, mechanism="一句无路径无sha无轮次的话", support="无锚点")
    r2 = audit_provenance([noanchor])
    # 3) 缺 provenance 但有 §4xx+路径 → 应可恢复且抽到锚点
    anch = dict(base, mechanism="见 life_kernel/foo.py §4ab 裁决 sha256 abcdef123456")
    r3 = audit_provenance([anch])
    passed = (
        r1["missing_count"] == 0
        and r2["items"][0]["verdict"] == "UNRECOVERABLE"
        and r3["items"][0]["verdict"] == "RECOVERABLE"
        and any("foo.py" in p for p in r3["items"][0]["anchors"]["paths"])
    )
    return {"passed": passed, "detail": {
        "complete_not_flagged": r1["missing_count"] == 0,
        "noanchor_unrecoverable": r2["items"][0]["verdict"] == "UNRECOVERABLE",
        "anchor_recoverable": r3["items"][0]["verdict"] == "RECOVERABLE"
        and any("foo.py" in p for p in r3["items"][0]["anchors"]["paths"]),
    }}


if __name__ == "__main__":
    import json
    print(json.dumps(negative_self_bite(), ensure_ascii=False, indent=2))
