"""检索文本溯源门禁 — 把 LangChain《Context Engineering Starts with Retrieval》的执行时检索污染编译成会判动作（§64）。

一手来源：
  LangChain 博客 (Jess Weng, 2026-10-23) line 191-194：retrieved text 是 data 非
  instructions；可能含 prompt injection；no prompt or delimiter strategy fully
  prevents this；要求 validate outputs（check answers cite sources you expect、
  claims match them）。line 150-184：无关/过时内容用 subagent 隔离，主 agent 只见结论。

为什么是新牙（对比现有判据）：
  - core.py GT.SOURCE_UNTRUSTED：判审计闭环输入层『claim 来源是否为已确认用户口述』
    →block 素材入库——管的是审计输入端的来源身份；
  - 本模块判 agent 执行层『外部检索文本是否被当 data、输出是否溯源校验、无关内容
    是否隔离』——场景（审计输入 vs agent 运行）、对象（claim source vs retrieved
    data）、动作（block 入库 vs validate outputs）三者均不同，拦截动作独立。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 33c4f789…）：
  - 语义枚举 yes/no/partial + 布尔，传字面串 → flag（R0，避开 §56 brittle 根因）；
  - 规则 R0-R5 按优先级写死，不事后加权（防 Goodhart）；
  - 只判『验证动作是否存在』，绝不承诺『防住了注入』——作者自认无完全防护，
    声明不可自证（KB-META01）；落点是检索管线 hygiene，非注入攻防有效性。

诚实边界：不构成对本仓框架的独立验证（KB-STRUCT02）；不接入 run_loop（遵循 §58 选 A）。
"""
from __future__ import annotations

from dataclasses import dataclass

# 语义枚举——写死；判定绝不读字符串内容（KB-AUDIT01 brittle 根因）
_STALE = frozenset({"yes", "no", "partial"})
_BOOL_FIELDS = ("text_marked_as_data", "output_citation_checked", "claims_match_sources", "irrelevant_isolated")


@dataclass(frozen=True)
class RetrievalGroundingVerdict:
    claim: str
    text_marked_as_data: bool
    output_citation_checked: bool
    claims_match_sources: bool
    irrelevant_isolated: bool
    stale_check: str
    action: str        # ok | downgrade | flag | block
    code: str
    message: str


def check_retrieval_grounding(
    claim: str,
    *,
    text_marked_as_data: bool,
    output_citation_checked: bool,
    claims_match_sources: bool,
    irrelevant_isolated: bool,
    stale_check: str,
) -> RetrievalGroundingVerdict:
    """判一个检索管线是否具备防污染的验证动作（不承诺防住注入）。

    输入须为语义枚举 + 布尔：
      stale_check ∈ {yes, no, partial}
      四个 bool 字段见签名。

    规则按优先级写死（与 gate_prereg.json 一致）：
      R0 非枚举/非布尔 → flag（拒绝字面串内容判定）
      R1 检索文本未标记 data → block（注入面敞开）
      R2 未核对引用 或 断言与来源不匹配 → downgrade（grounding 不成立）
      R3 无关/过时内容未隔离 → downgrade（污染传播进主上下文）
      R4 无时效性检查 → flag（过时内容风险待核）
      R5 全满足 → ok（hygiene 自洽，仍不替代实质证据）
    """
    # R0：语义输入校验优先
    if stale_check not in _STALE:
        return RetrievalGroundingVerdict(
            claim, text_marked_as_data, output_citation_checked, claims_match_sources,
            irrelevant_isolated, str(stale_check), "flag", "RETRIEVAL.INVALID_ENUM",
            "时效性检查须为 yes/no/partial 语义枚举；收到非法值（含字面串）→ flag，不进内容判定",
        )
    if not all(isinstance(v, bool) for v in (
        text_marked_as_data, output_citation_checked, claims_match_sources, irrelevant_isolated
    )):
        return RetrievalGroundingVerdict(
            claim, text_marked_as_data, output_citation_checked, claims_match_sources,
            irrelevant_isolated, stale_check, "flag", "RETRIEVAL.INVALID_FLAG",
            "布尔标志位非 bool → flag，拒绝对真值做内容判定",
        )

    # R1：检索文本未标记 data → block
    if not text_marked_as_data:
        return RetrievalGroundingVerdict(
            claim, text_marked_as_data, output_citation_checked, claims_match_sources,
            irrelevant_isolated, stale_check, "block", "RETRIEVAL.UNMARKED_TEXT",
            "检索文本未标记为 data 而非 instruction——prompt injection 攻击面敞开，block",
        )

    # R2：溯源校验缺失 → downgrade
    if not output_citation_checked:
        return RetrievalGroundingVerdict(
            claim, text_marked_as_data, output_citation_checked, claims_match_sources,
            irrelevant_isolated, stale_check, "downgrade", "RETRIEVAL.NO_CITATION_CHECK",
            "输出未核对引用来源——grounding 不成立，判定打折",
        )
    if not claims_match_sources:
        return RetrievalGroundingVerdict(
            claim, text_marked_as_data, output_citation_checked, claims_match_sources,
            irrelevant_isolated, stale_check, "downgrade", "RETRIEVAL.CLAIMS_MISMATCH",
            "断言与来源不匹配——输出可能建立在被污染/无关的检索文本上，判定打折",
        )

    # R3：无关内容未隔离 → downgrade
    if not irrelevant_isolated:
        return RetrievalGroundingVerdict(
            claim, text_marked_as_data, output_citation_checked, claims_match_sources,
            irrelevant_isolated, stale_check, "downgrade", "RETRIEVAL.NO_ISOLATION",
            "无关/过时内容未隔离在主 agent 上下文之外——污染可跨步传播，判定打折",
        )

    # R4：无时效性检查 → flag
    if stale_check == "no":
        return RetrievalGroundingVerdict(
            claim, text_marked_as_data, output_citation_checked, claims_match_sources,
            irrelevant_isolated, stale_check, "flag", "RETRIEVAL.STALE_UNCHECKED",
            "无时效性检查——过时内容风险未处理，待核（不是定罪）",
        )

    # R5：全自洽
    return RetrievalGroundingVerdict(
        claim, text_marked_as_data, output_citation_checked, claims_match_sources,
        irrelevant_isolated, stale_check, "ok", "RETRIEVAL.GROUNDED",
        "检索文本标记 data + 输出溯源 + 断言匹配 + 无关隔离 + 时效性检查——"
        "管线 hygiene 自洽（只判验证动作存在，不承诺防住注入）",
    )


def live_regression() -> dict:
    """8 个活体样例回归——对齐 gate_prereg.json 的预期。"""
    cases = {
        "no_data_mark": dict(text_marked_as_data=False, output_citation_checked=True,
                            claims_match_sources=True, irrelevant_isolated=True, stale_check="yes"),
        "no_citation": dict(text_marked_as_data=True, output_citation_checked=False,
                           claims_match_sources=True, irrelevant_isolated=True, stale_check="yes"),
        "claims_mismatch": dict(text_marked_as_data=True, output_citation_checked=True,
                                claims_match_sources=False, irrelevant_isolated=True, stale_check="yes"),
        "no_isolation": dict(text_marked_as_data=True, output_citation_checked=True,
                             claims_match_sources=True, irrelevant_isolated=False, stale_check="yes"),
        "no_stale_check": dict(text_marked_as_data=True, output_citation_checked=True,
                               claims_match_sources=True, irrelevant_isolated=True, stale_check="no"),
        "literal_stale": dict(text_marked_as_data=True, output_citation_checked=True,
                              claims_match_sources=True, irrelevant_isolated=True, stale_check="maybe"),
        "all_good": dict(text_marked_as_data=True, output_citation_checked=True,
                         claims_match_sources=True, irrelevant_isolated=True, stale_check="yes"),
        "partial_stale_ok": dict(text_marked_as_data=True, output_citation_checked=True,
                                 claims_match_sources=True, irrelevant_isolated=True, stale_check="partial"),
    }
    expects = {
        "no_data_mark": ("block", "RETRIEVAL.UNMARKED_TEXT"),
        "no_citation": ("downgrade", "RETRIEVAL.NO_CITATION_CHECK"),
        "claims_mismatch": ("downgrade", "RETRIEVAL.CLAIMS_MISMATCH"),
        "no_isolation": ("downgrade", "RETRIEVAL.NO_ISOLATION"),
        "no_stale_check": ("flag", "RETRIEVAL.STALE_UNCHECKED"),
        "literal_stale": ("flag", "RETRIEVAL.INVALID_ENUM"),
        "all_good": ("ok", "RETRIEVAL.GROUNDED"),
        "partial_stale_ok": ("ok", "RETRIEVAL.GROUNDED"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_retrieval_grounding("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
