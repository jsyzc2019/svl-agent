#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gf · 有效独立数 neff 标注守卫（承 §4ge）。

设计纪律（与 evidence_honesty.py 同族）：
- 纯函数，不接 run_loop、不联网、不 spawn、不编译门禁。
- 只检查"声称多源的断言是否标注了独立性来源与 neff 折减"，
  不检查标注值是否真实——真实性需外部一手，不在本模块能力内，诚实标注此上限。
- 不数源的个数；同模型家族须标折减；cross-model diversity 是缓解非消除。
- 所有中文关键词集中字典，比较逻辑只查键，避免 AST Compare 内中文字面量自咬。
"""
from dataclasses import dataclass
from typing import Any, Dict, List

# ---- 关键词集中字典（AST 自审：Compare 内不嵌中文字面量）----
_KW: Dict[str, str] = {
    "multi_source": "多源交叉",
    "independent_verify": "独立验证",
    "independent_judge": "独立judge",
    "independent_agent": "独立agent",
    "independent_designer": "独立设计者",
    "cross_check": "交叉验证",
    "ensemble": "集成",
    # 标注字段
    "field_error_source": "independent_error_source",
    "field_neff": "neff",
    "value_same_family": "same_family",
    "value_cross_model": "cross_model",
    "value_external_human": "external_human",
    "value_rule": "rule",
}

_CLAIM_MARKERS = (
    _KW["multi_source"], _KW["independent_verify"], _KW["independent_judge"],
    _KW["independent_agent"], _KW["independent_designer"], _KW["cross_check"],
    _KW["ensemble"],
)

# 独立性来源的诚实等级（neff 占名义N的经验量级上限，取自 §4ge 一手）
# 注意：这是"来源类型的量级参照"，不是对具体观测的硬否决——真实观测若低于上限一律放行；
# 上限的作用是拦截"把名义N直接当neff"的虚报（neff≈N），不是否决一手实测的微弱独立性。
_STRENGTH = {
    _KW["value_same_family"]: 0.25,   # 同模型家族：§4ge 实测 9→2(≈0.22)、10→1.4(≈0.14)，取 0.25 为包络上限
    _KW["value_cross_model"]: 0.5,     # 跨模型：§4ge 反打靶 rho 0.68→0.40，缓解非消除
    _KW["value_external_human"]: 0.8,  # 外部人类独立判断：接近独立但仍有 Noise 55%
    _KW["value_rule"]: 1.0,            # 规则/算法：无噪声（§4gd 另半边不受§4ge影响）
}


@dataclass(frozen=True)
class NeffVerdict:
    status: str
    claim: str
    reason: str
    declared_neff: Any = None
    suggested_ceiling: Any = None


def _is_claim(claim: str) -> bool:
    return any(m in claim for m in _CLAIM_MARKERS)


def neff_guard(claims: List[Dict[str, Any]]) -> List[NeffVerdict]:
    """对每条断言检查独立性标注。缺标注→拦截并要求补注；合规→按来源给出 neff 上限建议。

    输入 claim 结构：{"text": str, "independent_error_source"?: str, "neff"?: number, "n_sources"?: number}
    不修改输入，不产生副作用。
    """
    out: List[NeffVerdict] = []
    for c in claims:
        text = str(c.get("text", ""))
        if not _is_claim(text):
            out.append(NeffVerdict("NOT_MULTI_SOURCE_CLAIM", text, "非多源断言，守卫不适用"))
            continue
        src = c.get(_KW["field_error_source"])
        neff = c.get(_KW["field_neff"])
        n = c.get("n_sources")
        if not src:
            out.append(NeffVerdict(
                "UNQUALIFIED_INDEPENDENCE_CLAIM", text,
                "声称多源/独立但未标注 independent_error_source；按 §4ge 默认视为同模型家族高相关，须补注来源与 neff 折减",
                declared_neff=neff, suggested_ceiling=_STRENGTH[_KW["value_same_family"]],
            ))
            continue
        src_key = str(src)
        ceiling = _STRENGTH.get(src_key)
        if ceiling is None:
            out.append(NeffVerdict(
                "UNKNOWN_SOURCE", text,
                "独立性来源取值不在已知等级表，拒绝静默放行；须显式声明来源类型",
                declared_neff=neff,
            ))
            continue
        # 标注齐全：检查 neff 是否超过来源允许的上限（防把名义 N 当 neff）
        if isinstance(neff, (int, float)) and isinstance(n, (int, float)) and n > 0:
            cap = ceiling * n
            if neff > cap + 1e-9:
                out.append(NeffVerdict(
                    "NEFF_OVERCLAIMED", text,
                    "声明的 neff 超过该独立性来源的理论上限（名义N×来源强度）；按 §4ge 不得把名义源个数当有效独立数",
                    declared_neff=neff, suggested_ceiling=round(cap, 3),
                ))
                continue
        out.append(NeffVerdict(
            "QUALIFIED_OK", text,
            "已标注独立性来源与 neff；守卫放行（仅检查标注存在与上限，不保证标注值真实）",
            declared_neff=neff,
            suggested_ceiling=round(ceiling * n, 3) if isinstance(n, (int, float)) else ceiling,
        ))
    return out


def live_regression() -> Dict[str, bool]:
    """活体回归：纯函数行为自检，不接判定链。"""
    same = _KW["value_same_family"]
    cross = _KW["value_cross_model"]
    r: Dict[str, bool] = {}

    # 1 合规标注放行
    v = neff_guard([{"text": "多源交叉验证", _KW["field_error_source"]: same, _KW["field_neff"]: 2, "n_sources": 9}])
    r["qualified_pass"] = (v[0].status == "QUALIFIED_OK")

    # 2 缺标注拦截
    v = neff_guard([{"text": "独立验证通过"}])
    r["unqualified_blocked"] = (v[0].status == "UNQUALIFIED_INDEPENDENCE_CLAIM")

    # 3 同模型家族标折减（建议上限=9*0.15≈1.35）
    v = neff_guard([{"text": "独立agent交叉", _KW["field_error_source"]: same, "n_sources": 9}])
    r["same_family_discounted"] = (v[0].suggested_ceiling is not None and v[0].suggested_ceiling < 9)

    # 4 cross-model 不误判为完全独立（0.5 上限 < 1.0）
    v = neff_guard([{"text": "交叉验证", _KW["field_error_source"]: cross, "n_sources": 10}])
    r["cross_model_not_full"] = (v[0].suggested_ceiling is not None and v[0].suggested_ceiling < 10)

    # 5 篡改 neff：把名义 9 当 neff 且来源同家族 → 翻转
    v = neff_guard([{"text": "多源交叉", _KW["field_error_source"]: same, _KW["field_neff"]: 9, "n_sources": 9}])
    r["tamper_neff_flips"] = (v[0].status == "NEFF_OVERCLAIMED")

    # 6 非多源断言 skipped
    v = neff_guard([{"text": "今天天气很好"}])
    r["non_claim_skipped"] = (v[0].status == "NOT_MULTI_SOURCE_CLAIM")

    # 7 未知来源不放行
    v = neff_guard([{"text": "独立judge", _KW["field_error_source"]: "unknown"}])
    r["unknown_source_blocked"] = (v[0].status == "UNKNOWN_SOURCE")

    # 8 零战利品：所有 status 不含 OVERTHROWN/VICTORY
    allv = neff_guard([{"text": "多源交叉", _KW["field_error_source"]: cross, _KW["field_neff"]: 4, "n_sources": 10}])
    r["no_trophy_language"] = not any(s in allv[0].status for s in ("OVERTHROWN", "VICTORY", "PROVEN"))

    return r


if __name__ == "__main__":
    import json
    print(json.dumps(live_regression(), ensure_ascii=False, indent=1))
