#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gi · 外部时间锚交叉核验：把存在性句柄从'格式核对'升级到'远端+时间+内容'三维实证。

承 §4gh 诚实上限：存在性守卫只查句柄存在与格式，不联网复核 commit_sha 真伪；
'联网锚留 §4gi'。本模块把这一洞补成可运行判据：

一个声称'X 已同步/X 在'的 commit_sha 句柄，仅格式合法不足采信（F07 活靶：
旧记忆 c446e01 格式对但远端 HEAD 早已不同）。须四维全过才 ANCHOR_VERIFIED：
- D1 handle_format：commit_sha 格式 [0-9a-f]{7,40}（最低门槛，非充分）；
- D2 remote_existence：句柄与远端 API 返回的 commit sha 一致；
- D3 temporal_order：commit 服务器时间戳 >= 预注册时间（防事后补锚）；
- D4 content_consistency：本地真值源 git blob sha == 远端树中 blob sha（同类比较）。

设计纪律（与 claim_honesty/numeric_honesty/evidence_honesty 同族）：
- 纯函数，不联网、不 spawn、不接判定链/门禁、不改 verdict/l3/absolute/宪法。
- 联网摄食由外层工具完成并落 sha256 锁存的证据快照；判据只读快照核验，不自己联网。
- 状态串与中文集中字典，比较逻辑只查 ASCII 键，避免 AST Compare 中文字面量自咬。
- 双向校准：坏锚集须全识别，合法锚不得误杀，否则 BLIND_SPOT / OVERREJECT。
- 诚实上限：只证明'快照内部四维自洽'，不证明远端此刻真实；服务器时间戳非密码学签名。
"""
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

# ---- 状态/条件常量集中字典（比较逻辑只查 ASCII 键）----
_ST: Dict[str, str] = {
    "verified": "ANCHOR_VERIFIED",
    "no_evidence": "NO_EVIDENCE_SNAPSHOT",
    "f_format": "D1_FORMAT",
    "f_remote": "D2_NOT_ON_REMOTE",
    "f_postdated": "D3_POSTDATED",
    "f_drift": "D4_CONTENT_DRIFT",
    "blind": "BLIND_SPOT",
    "overreject": "OVERREJECT",
    "all_recognized": "ALL_KNOWN_BAD_ANCHORS_RECOGNIZED",
}

_SHA_RE = re.compile(r"[0-9a-f]{7,40}")
# ISO8601 UTC 形如 2026-11-26T05:51:14Z —— 字典序可比较（等宽零填充）
_TS_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")


@dataclass(frozen=True)
class AnchorVerdict:
    status: str
    flags: tuple
    detail: Dict[str, bool]


def _prefix_match(a: str, b: str) -> bool:
    """两 sha 互为前提匹配（≥7 位），容许 7 位短 sha 与 40 位全 sha 互认。"""
    a, b = str(a).lower(), str(b).lower()
    if not (_SHA_RE.fullmatch(a) and _SHA_RE.fullmatch(b)):
        return False
    n = min(len(a), len(b))
    return a[:n] == b[:n]


def verify_anchor(anchor: Dict[str, Any],
                  evidence: Optional[Dict[str, Any]],
                  prereg_ts: str) -> AnchorVerdict:
    """四维核验存在性句柄。纯函数：只读传入 dict，不联网不读文件。

    anchor:   {commit_sha, local_blob_sha}  —— 声称的句柄 + 本地真值源 git blob sha（外层算好传入）
    evidence: {remote_commit_sha, server_timestamp, tree_blob_sha} —— sha256 锁存的远端快照
    prereg_ts: 预注册 UTC 时间串（ISO8601 Z）
    """
    detail: Dict[str, bool] = {}
    flags: List[str] = []
    if not isinstance(evidence, dict) or not evidence:
        return AnchorVerdict(_ST["no_evidence"], (_ST["no_evidence"],), detail)

    d1 = bool(_SHA_RE.fullmatch(str(anchor.get("commit_sha", ""))))
    detail["D1"] = d1
    if not d1:
        flags.append(_ST["f_format"])

    d2 = _prefix_match(anchor.get("commit_sha", ""),
                       evidence.get("remote_commit_sha", ""))
    detail["D2"] = d2
    if not d2:
        flags.append(_ST["f_remote"])

    ts = str(evidence.get("server_timestamp", ""))
    ts_ok = bool(_TS_RE.fullmatch(ts)) and bool(_TS_RE.fullmatch(str(prereg_ts)))
    d3 = ts_ok and ts >= str(prereg_ts)
    detail["D3"] = d3
    if not d3:
        flags.append(_ST["f_postdated"])

    local_blob = str(anchor.get("local_blob_sha", "")).lower()
    remote_blob = str(evidence.get("tree_blob_sha", "")).lower()
    d4 = bool(_SHA_RE.fullmatch(local_blob)) and local_blob == remote_blob
    detail["D4"] = d4
    if not d4:
        flags.append(_ST["f_drift"])

    status = _ST["verified"] if not flags else "FAILED"
    return AnchorVerdict(status, tuple(flags), detail)


def is_bad_anchor(case: Dict[str, Any]) -> bool:
    """默认识别器：坏锚应被拦（非 ANCHOR_VERIFIED 即识别）。"""
    a = case.get("anchor", {})
    e = case.get("evidence")
    p = case.get("prereg_ts", "2026-01-01T00:00:00Z")
    return verify_anchor(a, e, p).status != _ST["verified"]


# ---- 双向校准集：坏锚（须拦）与合法锚（须放行）----
# 合法锚四维全一致：远端 sha 与句柄一致、时间戳晚于预注册、blob 同类一致。
_GOOD_A = {"commit_sha": "b570b3c1cdd31f9b0fc1ec7955717749205197d1",
           "local_blob_sha": "0c2c01321b7dbb4be400f6a9ca8a5034a74d294b"}
_GOOD_E = {"remote_commit_sha": "b570b3c1cdd31f9b0fc1ec7955717749205197d1",
           "server_timestamp": "2026-11-26T06:30:00Z",  # 晚于预注册 05:51
           "tree_blob_sha": "0c2c01321b7dbb4be400f6a9ca8a5034a74d294b"}
_GOOD_P = "2026-11-26T05:51:14Z"

KNOWN_BAD_ANCHORS: List[Dict[str, Any]] = [
    {"id": "B01", "type": "absent_remote",  # F07 型：格式对但远端 sha 不匹配
     "anchor": {"commit_sha": "c446e01abcdef", "local_blob_sha": "0c2c01321b7dbb4be400f6a9ca8a5034a74d294b"},
     "evidence": dict(_GOOD_E), "prereg_ts": _GOOD_P},
    {"id": "B02", "type": "postdated",  # commit 服务器时间早于预注册 = 事后补锚（真实远端快照即此类）
     "anchor": dict(_GOOD_A),
     "evidence": {**_GOOD_E, "server_timestamp": "2026-11-26T05:45:13Z"}, "prereg_ts": _GOOD_P},
    {"id": "B03", "type": "content_drift",  # 本地 blob 与远端 blob 不符
     "anchor": {**_GOOD_A, "local_blob_sha": "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef"},
     "evidence": dict(_GOOD_E), "prereg_ts": _GOOD_P},
    {"id": "B04", "type": "no_evidence",  # 只有声称，无远端快照
     "anchor": dict(_GOOD_A), "evidence": None, "prereg_ts": _GOOD_P},
]

KNOWN_GOOD_ANCHORS: List[Dict[str, Any]] = [
    {"id": "G01", "note": "四维全一致的合法锚，不得误杀",
     "anchor": dict(_GOOD_A), "evidence": dict(_GOOD_E), "prereg_ts": _GOOD_P},
    {"id": "G02", "note": "合法锚用 7 位短 sha 与 40 位远端 sha 互认",
     "anchor": {"commit_sha": "b570b3c", "local_blob_sha": _GOOD_E["tree_blob_sha"]},
     "evidence": dict(_GOOD_E), "prereg_ts": _GOOD_P},
]


def blind_spot_check(recognition_fn: Callable[[Dict[str, Any]], bool]) -> Dict[str, Any]:
    """双向校准：坏锚须全识别，合法锚须全放行。
    漏识别坏锚→BLIND_SPOT；误杀合法→OVERREJECT；两者皆过→ALL_KNOWN_BAD_ANCHORS_RECOGNIZED。"""
    missed: List[str] = []
    for c in KNOWN_BAD_ANCHORS:
        try:
            ok = bool(recognition_fn(c))
        except Exception:
            ok = False
        if not ok:
            missed.append(c["id"])
    overrejected: List[str] = []
    for c in KNOWN_GOOD_ANCHORS:
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
        "bad_total": len(KNOWN_BAD_ANCHORS),
        "bad_recognized": len(KNOWN_BAD_ANCHORS) - len(missed),
        "missed_ids": missed,
        "good_total": len(KNOWN_GOOD_ANCHORS),
        "good_not_overrejected": len(KNOWN_GOOD_ANCHORS) - len(overrejected),
        "overrejected_ids": overrejected,
        "boundary": "校准集是已知案例非穷尽；通过≠覆盖所有锚失效模式；判据是守卫非真理判定器。",
    }


def wiring_self_check(collected_nodeids: List[str]) -> bool:
    """元纪律：判据自身测试必须在 pytest 收集集内，否则 DISCONNECTED。"""
    return any("test_temporal_anchor" in str(nid) for nid in collected_nodeids)


def live_regression() -> Dict[str, bool]:
    """活体回归：构造样本测纯函数行为，不依赖现场真值（避免修复前后翻转）。"""
    r: Dict[str, bool] = {}
    v = verify_anchor(_GOOD_A, _GOOD_E, _GOOD_P)
    r["good_anchor_verified"] = (v.status == _ST["verified"])
    r["good_short_sha_verified"] = (
        verify_anchor({"commit_sha": "b570b3c", "local_blob_sha": _GOOD_E["tree_blob_sha"]},
                      _GOOD_E, _GOOD_P).status == _ST["verified"])
    r["b01_absent_remote_caught"] = (
        _ST["f_remote"] in verify_anchor(KNOWN_BAD_ANCHORS[0]["anchor"],
                                          KNOWN_BAD_ANCHORS[0]["evidence"],
                                          _GOOD_P).flags)
    r["b02_postdated_caught"] = (
        _ST["f_postdated"] in verify_anchor(KNOWN_BAD_ANCHORS[1]["anchor"],
                                             KNOWN_BAD_ANCHORS[1]["evidence"],
                                             _GOOD_P).flags)
    r["b03_drift_caught"] = (
        _ST["f_drift"] in verify_anchor(KNOWN_BAD_ANCHORS[2]["anchor"],
                                         KNOWN_BAD_ANCHORS[2]["evidence"],
                                         _GOOD_P).flags)
    r["b04_no_evidence_caught"] = (
        verify_anchor(KNOWN_BAD_ANCHORS[3]["anchor"], None, _GOOD_P).status
        == _ST["no_evidence"])
    r["bad_format_caught"] = (
        _ST["f_format"] in verify_anchor({"commit_sha": "not-a-sha", "local_blob_sha": "x"},
                                          _GOOD_E, _GOOD_P).flags)
    r["permissive_caught"] = (
        blind_spot_check(lambda c: True)["status"] == _ST["overreject"])
    r["strict_overreject_caught"] = (
        blind_spot_check(lambda c: False)["status"] == _ST["blind"])
    r["real_judge_passes"] = (
        blind_spot_check(is_bad_anchor)["status"] == _ST["all_recognized"])
    r["wiring_true"] = wiring_self_check(["tests/test_temporal_anchor.py::t_good"])
    r["wiring_false"] = not wiring_self_check(["tests/test_unrelated.py::t"])
    allv = verify_anchor(_GOOD_A, _GOOD_E, _GOOD_P)
    r["no_trophy_language"] = not any(
        s in allv.status for s in ("PROVEN", "VICTORY", "OVERTHROWN", "L3"))
    r["bad_count_4"] = (len(KNOWN_BAD_ANCHORS) == 4)
    r["good_count_2"] = (len(KNOWN_GOOD_ANCHORS) == 2)
    return r


if __name__ == "__main__":
    import json
    print(json.dumps(live_regression(), ensure_ascii=False, indent=1))
