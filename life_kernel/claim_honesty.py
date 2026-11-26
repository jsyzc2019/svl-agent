#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gh · 断言诚实守卫：存在性断言 + 判据盲区校准（承 §4gg 深省）。

深省：一个只审'接线'、不审'盲区'的判据，和抓错字段的旧脚本没有区别。
本模块做两件事：
1. KNOWN_FAILURES / KNOWN_VALID + blind_spot_check：用真实失效集与合法对照集
   双向校准任何判据——漏识别失效→BLIND_SPOT，误杀合法→OVERREJECT。
   两个都过才算 ALL_KNOWN_FAILURES_RECOGNIZED（仍非穷尽，诚实标注）。
2. existence_claim_guard：对"X在/X已做/X没做"类存在性断言强制可复核句柄；
   缺句柄→UNVERIFIED_CLAIM。把"报告过≠现在在"从数字推广到机制存在性。
   支持 is_existence 显式覆盖——校准不依赖脆弱关键词(真实表达千变万化)。

设计纪律（与 evidence_honesty/numeric_honesty 同族）：
- 纯函数，不联网/spawn/判定链/门禁；不改 verdict/l3/absolute/宪法。
- 只检查句柄存在与格式，不假装联网复核 commit_sha 真伪——诚实标注此上限。
- 历史失效集是已知案例非穷尽；中文关键词集中字典避免 AST Compare 中文字面量自咬。
"""
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

# ---- 中文关键词集中字典（比较逻辑只查键，不内嵌中文字面量）----
_KW: Dict[str, str] = {
    "exists": "存在",
    "done": "已完成",
    "landed": "已落档",
    "synced": "已同步",
    "fixed": "已修复",
    "wired": "已接入",
    "report_success": "已成功",
    "configured": "已配置",
    "verified": "已核验",
    "dismantled": "已拆",
    "assembled": "组装",
    "deployed": "已部署",
    "established": "已建立",
    "no_task": "无任务",
    "not_wired": "collect不到",
}
_EXIST_MARKERS = tuple(_KW.values())

_HANDLE_TYPES = ("commit_sha", "verify_fn", "tool_output", "file_with_fact")

# ---- 历史失效 fixture（真实案例，带可复核证据路径与显式存在性标注）----
KNOWN_FAILURES: List[Dict[str, Any]] = [
    {"id": "F01", "claim": "§4gf KB已落档(报告471)", "truth": "现场470，未落",
     "class": "report_success_but_no_land", "evidence": "result_4gg.json", "is_existence": True},
    {"id": "F02", "claim": "handoff权威行知识库为471", "truth": "现场470",
     "class": "declared_number_wrong", "evidence": "prereg_numeric_honesty", "is_existence": False},
    {"id": "F03", "claim": "一致性脚本在防数字漂移", "truth": "正则抓速查表466非权威行",
     "class": "wrong_field_checked", "evidence": "life_kernel/numeric_honesty.py", "is_existence": True},
    {"id": "F04", "claim": "一致性脚本在全量套件里", "truth": "无test_前缀collect不到",
     "class": "judge_not_wired", "evidence": "tests/test_numeric_honesty.py", "is_existence": True},
    {"id": "F05", "claim": "token已拆三块临时组装", "truth": "现场零分片文件零组装代码",
     "class": "mechanism_claimed_but_absent", "evidence": "KB-AUDIT206", "is_existence": True},
    {"id": "F06", "claim": "目录枚举查自动化得无任务", "truth": "调度器里日出唤醒ACTIVE一直在",
     "class": "wrong_tool_for_negative", "evidence": "KB-META158", "is_existence": True},
    {"id": "F07", "claim": "GitHub同步已成功(旧记忆c446e01)", "truth": "现场HEAD e761b208未推",
     "class": "success_claimed_but_not_done", "evidence": "GITHUB_SYNC_BLOCKERS", "is_existence": True},
]

# ---- 合法对照集：带真句柄/非存在性，判据不得误杀 ----
KNOWN_VALID: List[Dict[str, Any]] = [
    {"id": "V01", "claim": "GitHub已同步", "is_existence": True,
     "handle_type": "commit_sha", "handle": "cb85b9f2e57f"},
    {"id": "V02", "claim": "机制已接入", "is_existence": True,
     "handle_type": "verify_fn", "handle": "some_verify"},
    {"id": "V03", "claim": "今天天气很好", "is_existence": False},
]


@dataclass(frozen=True)
class ClaimVerdict:
    status: str
    claim: str
    reason: str
    handle_type: Optional[str] = None


def _is_existence(claim: str, explicit: Optional[bool] = None) -> bool:
    if explicit is not None:
        return bool(explicit)
    return any(m in claim for m in _EXIST_MARKERS)


def _valid_handle(claim: Dict[str, Any]) -> Optional[str]:
    """只查句柄存在与格式，不联网复核真伪。返回句柄类型或 None。"""
    h = claim.get("handle_type")
    if h not in _HANDLE_TYPES:
        return None
    payload = claim.get("handle")
    if not payload:
        return None
    if h == "commit_sha":
        return h if re.fullmatch(r"[0-9a-f]{7,40}", str(payload)) else None
    if h == "verify_fn":
        return h if callable(payload) or (isinstance(payload, str) and payload.isidentifier()) else None
    return h if isinstance(payload, str) and len(payload) > 0 else None


def existence_claim_guard(claims: List[Dict[str, Any]]) -> List[ClaimVerdict]:
    """对存在性断言强制可复核句柄；非存在性断言跳过；不联网复核句柄真伪。"""
    out: List[ClaimVerdict] = []
    for c in claims:
        text = str(c.get("text", ""))
        if not _is_existence(text, c.get("is_existence")):
            out.append(ClaimVerdict("NOT_EXISTENCE_CLAIM", text, "非存在性断言，守卫不适用"))
            continue
        htype = _valid_handle(c)
        if htype is None:
            out.append(ClaimVerdict(
                "UNVERIFIED_CLAIM", text,
                "声称X在/X已做/X没做但未附可复核句柄；按'报告过≠现在在'默认不采信，须补 commit_sha/verify_fn/tool_output/file_with_fact 或现场核验函数",
            ))
            continue
        out.append(ClaimVerdict(
            "QUALIFIED_HANDLE", text,
            "已附可复核句柄(仅格式核对，未联网复核真伪；真伪须外部一手另验)",
            handle_type=htype,
        ))
    return out


def is_failure_recognized(f: Dict[str, Any]) -> bool:
    """默认识别器：用存在性守卫判 fixture——无句柄的失效断言应被拦(UNVERIFIED)。"""
    v = existence_claim_guard([{"text": f["claim"], "is_existence": f.get("is_existence"),
                                "handle_type": f.get("handle_type"), "handle": f.get("handle")}])[0]
    return v.status == "UNVERIFIED_CLAIM"


def blind_spot_check(recognition_fn: Callable[[Dict[str, Any]], bool]) -> Dict[str, Any]:
    """双向校准：职责内失效集须全识别、合法集须全不误杀。
    漏识别→BLIND_SPOT；误杀合法→OVERREJECT；两者皆过→ALL_KNOWN_FAILURES_RECOGNIZED。

    职责边界：本守卫只管存在性断言(is_existence=True)。F02 是数字声明错，
    归 numeric_honesty 管(其 C1 已验证能抓)，在此标 OUT_OF_SCOPE 不算本守卫漏识别——
    职责精确化不是放宽：本守卫的 6 条存在性失效仍须全识别，合法集仍须全不误杀。
    """
    in_scope = [f for f in KNOWN_FAILURES if f.get("is_existence")]
    out_of_scope = [f["id"] for f in KNOWN_FAILURES if not f.get("is_existence")]
    missed: List[str] = []
    for f in in_scope:
        try:
            ok = bool(recognition_fn(f))
        except Exception:
            ok = False
        if not ok:
            missed.append(f["id"])
    overrejected: List[str] = []
    for v in KNOWN_VALID:
        try:
            flagged = bool(recognition_fn(v))
        except Exception:
            flagged = True
        if flagged:
            overrejected.append(v["id"])
    if missed:
        status = "BLIND_SPOT"
    elif overrejected:
        status = "OVERREJECT"
    else:
        status = "ALL_KNOWN_FAILURES_RECOGNIZED"
    return {
        "status": status,
        "failures_total": len(in_scope),
        "failures_recognized": len(in_scope) - len(missed),
        "missed_ids": missed,
        "out_of_scope_ids": out_of_scope,
        "scope_note": "OUT_OF_SCOPE 项由其它守卫负责(F02数字声明→numeric_honesty C1已验证)",
        "valid_total": len(KNOWN_VALID),
        "valid_not_overrejected": len(KNOWN_VALID) - len(overrejected),
        "overrejected_ids": overrejected,
        "boundary": "校准集是已知案例非穷尽；通过≠覆盖所有失效模式；判据仍是守卫不是真理判定器。",
    }


def live_regression() -> Dict[str, bool]:
    """活体回归：纯函数行为自检，不依赖现场真值(避免修复前后翻转)。"""
    r: Dict[str, bool] = {}
    v = existence_claim_guard([{"text": "token已拆三块临时组装"}])
    r["unverified_blocked"] = (v[0].status == "UNVERIFIED_CLAIM")
    v = existence_claim_guard([{"text": "GitHub已同步", "handle_type": "commit_sha",
                                "handle": "cb85b9f2e57f"}])
    r["qualified_handle_passes"] = (v[0].status == "QUALIFIED_HANDLE")
    v = existence_claim_guard([{"text": "已核验", "handle_type": "commit_sha",
                                "handle": "not-a-sha"}])
    r["bad_handle_blocked"] = (v[0].status == "UNVERIFIED_CLAIM")
    v = existence_claim_guard([{"text": "今天天气很好"}])
    r["non_existence_skipped"] = (v[0].status == "NOT_EXISTENCE_CLAIM")
    v = existence_claim_guard([{"text": "机制已接入", "handle_type": "verify_fn",
                                "handle": "some_verify"}])
    r["verify_fn_handle_passes"] = (v[0].status == "QUALIFIED_HANDLE")
    # 双向校准：永远放行(全False)→BLIND_SPOT；永远告警(全True)→OVERREJECT；真判据→过。
    r["blind_spot_catches_permissive"] = (
        blind_spot_check(lambda f: False)["status"] == "BLIND_SPOT")
    r["blind_spot_catches_overreject"] = (
        blind_spot_check(lambda f: True)["status"] == "OVERREJECT")
    r["blind_spot_accepts_real_judge"] = (
        blind_spot_check(is_failure_recognized)["status"] == "ALL_KNOWN_FAILURES_RECOGNIZED")
    # 恒真重述(truth!=claim)无合法集把关时必须被 OVERREJECT 挡掉——证明校准不再浅薄。
    r["tautology_rejected"] = (
        blind_spot_check(lambda f: f.get("truth") != f.get("claim"))["status"] == "OVERREJECT")
    allv = existence_claim_guard([{"text": "已落档"}])
    r["no_trophy_language"] = not any(
        s in allv[0].status for s in ("OVERTHROWN", "VICTORY", "PROVEN"))
    r["fixtures_have_evidence"] = all(f.get("evidence") for f in KNOWN_FAILURES)
    r["fixtures_count_7"] = (len(KNOWN_FAILURES) == 7)
    r["scope_partition_ok"] = (
        sum(1 for f in KNOWN_FAILURES if f.get("is_existence")) == 6
        and sum(1 for f in KNOWN_FAILURES if not f.get("is_existence")) == 1)
    return r


if __name__ == "__main__":
    import json
    print(json.dumps(live_regression(), ensure_ascii=False, indent=1))
