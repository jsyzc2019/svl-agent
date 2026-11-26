#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gj · 认错台账：把'我错了'从人肉自觉升级为机械落档通道。

承 §4gj 元观察：§4ge–§4gi 连造五个免疫系统(能抓错)，但 verdict 不动；
认错最后一公里仍是Agent手工写result/改handoff/报成功——§4gf 报告471现场470
就是'抓到了却靠我自己想起来改'。本模块把认错机械落档：

四链闭环 detect→record→propagate→verify：
- L1 判据抓错(failed信号)；无信号→NO_CORRECTION_NEEDED，不硬造认错。
- L2 有信号必须生成带sha256自锁的认错记录(append-only，回改即 RECORD_TAMPER)。
- L3 认错记录须驱动权威行更新，使 check_handoff(声明==现场真值) 通过。
- L4 记录链sha256连续+时间戳单调+末态权威行ok，有一环缺不报成功。

设计纪律（同族纯函数）：
- 不联网/spawn/判定链/门禁；不改 verdict/l3/absolute/宪法。
- 数字真值源复用 numeric_honesty.check_handoff，本模块不重造。
- 状态串集中字典，比较逻辑只查ASCII键，避免 AST Compare 中文字面量自咬。
- 双向校准：坏链须全识别、合法闭环不得误杀。
- 诚实上限：只证明链条机械闭合，不证明权威行真值本身正确；sha256自锁防回改
  但不防'一开始就写假记录'(源头诚实仍靠判据+外部取证)。
"""
import hashlib
import json
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

_ST: Dict[str, str] = {
    "closed": "CORRECTION_CLOSED",
    "none": "NO_CORRECTION_NEEDED",
    "detected_unrecorded": "DETECTED_BUT_UNRECORDED",
    "record_unpropagated": "RECORD_WITHOUT_PROPAGATION",
    "authority_wrong": "AUTHORITY_STILL_WRONG",
    "tamper": "RECORD_TAMPER",
    "blind": "BLIND_SPOT",
    "overreject": "OVERREJECT",
    "all_recognized": "ALL_KNOWN_BAD_CHAINS_RECOGNIZED",
}

_TIME_LEN = 20  # 2026-11-26T06:00:09Z 等宽，字典序可比


@dataclass(frozen=True)
class ChannelVerdict:
    status: str
    detail: Dict[str, Any]


def _canonical(record: Dict[str, Any]) -> str:
    """规范序列化：除 self_hash 外的字段按 key 排序，确保 sha256 可复算。"""
    d = {k: v for k, v in record.items() if k != "self_hash"}
    return json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _self_hash(record: Dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(record).encode("utf-8")).hexdigest()


def make_correction(detect: Dict[str, Any], declared: Any, truth: Any,
                    source: str, record_id: str, ts: str,
                    prev_hash: str = "GENESIS") -> Dict[str, Any]:
    """生成一条带 sha256 自锁的认错记录（append-only 语义）。

    detect: 判据失败信号(如 check_handoff 的 failed 清单或字段)；
    declared/truth: 旧声明值与现场真值；source: 来源判据名；
    prev_hash: 上一条记录的 self_hash，构成链。
    """
    rec: Dict[str, Any] = {
        "record_id": record_id,
        "ts": ts,
        "detect": detect,
        "declared": declared,
        "truth": truth,
        "source": source,
        "prev_hash": prev_hash,
    }
    rec["self_hash"] = _self_hash(rec)
    return rec


def verify_chain(records: List[Dict[str, Any]], authority_check_ok: bool) -> ChannelVerdict:
    """核验认错记录链：每条 self_hash 可复算、prev_hash 连续、时间戳单调。"""
    detail: Dict[str, Any] = {"n": len(records), "links_ok": True, "order_ok": True,
                              "authority_ok": bool(authority_check_ok)}
    if not records:
        detail["links_ok"] = False
        return ChannelVerdict(_ST["detected_unrecorded"], detail)

    prev = "GENESIS"
    for i, rec in enumerate(records):
        if not isinstance(rec, dict):
            detail["links_ok"] = False
            break
        if rec.get("self_hash") != _self_hash(rec):
            detail["links_ok"] = False
            break
        if rec.get("prev_hash") != prev:
            detail["links_ok"] = False
            break
        ts = str(rec.get("ts", ""))
        if len(ts) != _TIME_LEN or (i > 0 and ts < str(records[i - 1].get("ts", ""))):
            detail["order_ok"] = False
            break
        prev = rec["self_hash"]
    return ChannelVerdict("OK" if (detail["links_ok"] and detail["order_ok"]) else _ST["tamper"], detail)


def channel_status(detect_signals: Any, records: List[Dict[str, Any]],
                   authority_check_ok: bool) -> ChannelVerdict:
    """四链综合裁决。detect_signals 为空→无错，不硬造认错；否则须有记录+传播+复核。"""
    detail: Dict[str, Any] = {"has_detect": bool(detect_signals),
                              "n_records": len(records or []),
                              "authority_ok": bool(authority_check_ok)}
    if not detect_signals:
        # 无失败信号：权威行ok且无记录→NO_CORRECTION_NEEDED；否则存在孤立记录，异常
        if authority_check_ok and not records:
            return ChannelVerdict(_ST["none"], detail)
        detail["orphan_records"] = bool(records)
        return ChannelVerdict(_ST["authority_wrong"] if not authority_check_ok else _ST["record_unpropagated"], detail)

    if not records:
        return ChannelVerdict(_ST["detected_unrecorded"], detail)

    vc = verify_chain(records, authority_check_ok)
    detail["chain"] = vc.detail
    if vc.status == _ST["tamper"]:
        return ChannelVerdict(_ST["tamper"], detail)
    if not authority_check_ok:
        return ChannelVerdict(_ST["record_unpropagated"], detail)
    return ChannelVerdict(_ST["closed"], detail)


def is_bad_chain(case: Dict[str, Any]) -> bool:
    """默认识别器：坏链应被拦（非 CORRECTION_CLOSED / NO_CORRECTION_NEEDED）。"""
    v = channel_status(case.get("detect"), case.get("records", []),
                       case.get("authority_ok", False))
    return v.status not in (_ST["closed"], _ST["none"])


def _good_case() -> Dict[str, Any]:
    """一条完整闭环：detect→record→propagate→verify 全过。"""
    r1 = make_correction({"kb_count": "declared471_vs_truth470"}, "471", "470",
                         "numeric_honesty.check_handoff", "CORR-001",
                         "2026-11-26T06:01:00Z")
    return {"detect": ["kb_count"], "records": [r1], "authority_ok": True}


KNOWN_BAD_CHAINS: List[Dict[str, Any]] = [
    {"id": "B01", "type": "detected_unrecorded",
     "detect": ["kb_count"], "records": [], "authority_ok": False},
    {"id": "B02", "type": "record_unpropagated",
     "detect": ["kb_count"], "records": _good_case()["records"], "authority_ok": False},
    {"id": "B03", "type": "tamper",
     "detect": ["kb_count"],
     "records": [{**_good_case()["records"][0], "truth": "999"}],  # 回改真值字段
     "authority_ok": True},
]
# B04 断链：prev_hash 不连续
_b4 = make_correction({"x": "y"}, "a", "b", "numeric_honesty.check_handoff",
                      "CORR-009", "2026-11-26T06:02:00Z", prev_hash="WRONG_PREV")
KNOWN_BAD_CHAINS.append({"id": "B04", "type": "broken_chain",
                         "detect": ["x"], "records": [_b4], "authority_ok": True})

KNOWN_GOOD_CHAINS: List[Dict[str, Any]] = [
    {"id": "G01", "note": "四链全闭合，不得误杀", **_good_case()},
    {"id": "G02", "note": "无错场景不硬造认错", "detect": [], "records": [], "authority_ok": True},
]


def blind_spot_check(recognition_fn: Callable[[Dict[str, Any]], bool]) -> Dict[str, Any]:
    """双向校准：坏链须全识别、合法链须全放行。"""
    missed: List[str] = []
    for c in KNOWN_BAD_CHAINS:
        try:
            ok = bool(recognition_fn(c))
        except Exception:
            ok = False
        if not ok:
            missed.append(c["id"])
    overrejected: List[str] = []
    for c in KNOWN_GOOD_CHAINS:
        try:
            flagged = bool(recognition_fn(c))
        except Exception:
            flagged = True
        if flagged:
            overrejected.append(c["id"])
    if missed:
        status = _ST["blind"]
    elif overrejected:
        status = _ST["overreject"]
    else:
        status = _ST["all_recognized"]
    return {
        "status": status,
        "bad_total": len(KNOWN_BAD_CHAINS),
        "bad_recognized": len(KNOWN_BAD_CHAINS) - len(missed),
        "missed_ids": missed,
        "good_total": len(KNOWN_GOOD_CHAINS),
        "good_not_overrejected": len(KNOWN_GOOD_CHAINS) - len(overrejected),
        "overrejected_ids": overrejected,
        "boundary": "校准集已知非穷尽；通过≠覆盖所有认错失效；通道是守卫非真理判定器。",
    }


def wiring_self_check(collected_nodeids: List[str]) -> bool:
    return any("test_correction_ledger" in str(nid) for nid in collected_nodeids)


def live_regression() -> Dict[str, bool]:
    """活体回归：构造样本测纯函数行为，不依赖现场真值(避免修复前后翻转)。"""
    r: Dict[str, bool] = {}
    g = _good_case()
    r["good_chain_closed"] = (channel_status(g["detect"], g["records"], True).status == _ST["closed"])
    r["no_error_no_fabrication"] = (channel_status([], [], True).status == _ST["none"])
    r["b01_detected_unrecorded"] = (
        channel_status(["x"], [], False).status == _ST["detected_unrecorded"])
    r["b02_unpropagated"] = (
        channel_status(g["detect"], g["records"], False).status == _ST["record_unpropagated"])
    r["b03_tamper"] = (
        channel_status(KNOWN_BAD_CHAINS[2]["detect"], KNOWN_BAD_CHAINS[2]["records"], True).status
        == _ST["tamper"])
    r["b04_broken_chain"] = (
        channel_status(KNOWN_BAD_CHAINS[3]["detect"], KNOWN_BAD_CHAINS[3]["records"], True).status
        == _ST["tamper"])
    r["self_hash_recomputable"] = (_self_hash(g["records"][0]) == g["records"][0]["self_hash"])
    r["permissive_caught"] = (blind_spot_check(lambda c: True)["status"] == _ST["overreject"])
    r["strict_caught"] = (blind_spot_check(lambda c: False)["status"] == _ST["blind"])
    r["real_judge_passes"] = (blind_spot_check(is_bad_chain)["status"] == _ST["all_recognized"])
    r["wiring_true"] = wiring_self_check(["tests/test_correction_ledger.py::t"])
    r["wiring_false"] = not wiring_self_check(["tests/test_unrelated.py::t"])
    v = channel_status(g["detect"], g["records"], True)
    r["no_trophy_language"] = not any(
        s in v.status for s in ("PROVEN", "VICTORY", "OVERTHROWN", "L3"))
    r["bad_count_4"] = (len(KNOWN_BAD_CHAINS) == 4)
    r["good_count_2"] = (len(KNOWN_GOOD_CHAINS) == 2)
    return r


if __name__ == "__main__":
    print(json.dumps(live_regression(), ensure_ascii=False, indent=1))
