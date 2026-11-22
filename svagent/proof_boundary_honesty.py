"""可证明声明的边界诚实性门禁 — 把 FlashProve 编译成会判动作（§71）。

一手证据（见 audit_flashprove/）：
  - S00 微信文章（二手 S2，NLPer 号 2026-11-06）：Anthropic 官方博客《Progress on
    provable inference for large language models》(2026-11-02) 的中文全文翻译。
  - S01 官方研究页（一手，anthropic.com）：FlashProve 用 zkSNARK 让用户在不知权重、
    CPU 几秒内验证"某条回答来自承诺的模型"。核心 guarantee 是 completeness/soundness/
    zero-knowledge + 简洁性；一手明确 "proof file ... computation was executed correctly"。
  - S02 技术报告 PDF（一手）：协议细节，random oracle 模型下的形式化。
  - S03 GitHub README/THIRD_PARTY/paper.pdf（一手，code-adjacent）：commit/prove/verify
    三段式 + "A research artifact: not maintained, not accepting contributions" + Apache 2.0
    + commitment ID "binds it to one set of weights" + C++ 快验证器 "carries no formal
    guarantee"。

为什么是新牙（对比现有门禁）：
  retrieval_grounding(§64)判检索文本是 data 非 instruction；memory_scope(§70)判记忆作用域；
  serving_signal(§65 邻)判训练/服务信号口径；session_continuity(§65)判跨 run 续接；
  无一判『一个声称带密码学/形式化证明的系统是否诚实披露证明边界』：
    ①证明范围：证明执行/来源正确 ≠ 结果事实正确（proves execution not fact）；
    ②信任根：承诺/验证器是否来自可信渠道而非被验证方自定（commitment anchor independent）；
    ③形式化边界：Lean 证协议但 C++ 验证器无形式化保证、三者不保证一致（formal scope disclosed）；
    ④未覆盖项：整数模型/贪心解码/1024 上下文/不隐藏架构/抗侧信道不覆盖/研究原型（uncovered disclosed）。
  FlashProve 是最会自曝边界的一手样本，但尺子的对象是"任何 proof-carrying system"——
  可迁移、会拦（把来源证明冒充事实证明/信任根自定/形式化无边界/未覆盖不披露都拦），
  KB-META01 会拦才入通过。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 bf208433…）：
  - 语义枚举；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『边界声明是否诚实自洽』，不承诺证明正确/系统有效——存在≠有效性(KB-META01/AUDIT03)；
    self-reported 吞吐/证明大小/加速比不采信(KB-RSI07)，研究原型不读成产品。

诚实边界：定位为审读外部可证明声明系统的尺子，不判本仓；本仓判据库本身即证明系统
（KB-T01/T02/T03，验证成本<生成成本 KB-T05 在 FlashProve 被密码学实现=同构），
遵循 §58 选 A 不接 run_loop。与 KB-R07（自洽 vs 有效）对象动作不同，拦截面独立。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class ProofBoundaryVerdict:
    claim: str
    proves_execution: str
    commitment_anchor: str
    formal_scope: str
    uncovered_disclosed: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_proof_boundary_honesty(
    claim: str,
    *,
    proves_execution_not_fact: str,
    commitment_anchor_independent: str,
    formal_scope_disclosed: str,
    uncovered_disclosed: str,
) -> ProofBoundaryVerdict:
    """判一个声称带密码学/形式化证明的系统是否诚实披露其证明边界（不承诺证明正确）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 proves_execution_not_fact=no → downgrade（把来源证明冒充事实正确证明）
      R2 commitment_anchor_independent=no → downgrade（信任根由被验证方自定）
      R3 formal_scope_disclosed=no → downgrade（形式化无边界，协议证明读成全栈正确）
      R4 uncovered_disclosed=no → flag（未覆盖项不披露，过度宣称）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判边界声明自洽）
    """
    vals = (proves_execution_not_fact, commitment_anchor_independent,
            formal_scope_disclosed, uncovered_disclosed)
    if any(v not in _ENUM for v in vals):
        return ProofBoundaryVerdict(
            claim, *(str(v) for v in vals),
            "flag", "PROOF_BOUNDARY.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
        )
    if proves_execution_not_fact == "no":
        return ProofBoundaryVerdict(
            claim, *vals, "downgrade", "PROOF_BOUNDARY.SOURCE_AS_FACT",
            "把『证明执行/来源正确』冒充『结果事实正确』——主体错位(KB-STRUCT05)，判定打折",
        )
    if commitment_anchor_independent == "no":
        return ProofBoundaryVerdict(
            claim, *vals, "downgrade", "PROOF_BOUNDARY.ANCHOR_SELF_SET",
            "承诺值/验证器信任根由被验证方自定而非可信渠道——证明自说自话，判定打折",
        )
    if formal_scope_disclosed == "no":
        return ProofBoundaryVerdict(
            claim, *vals, "downgrade", "PROOF_BOUNDARY.FORMAL_OVERCLAIM",
            "形式化证明不披露覆盖范围(协议已证 vs C++ 验证器无形式化保证)——把协议证明读成全栈正确，判定打折",
        )
    if uncovered_disclosed == "no":
        return ProofBoundaryVerdict(
            claim, *vals, "flag", "PROOF_BOUNDARY.UNCOVERED_HIDDEN",
            "未覆盖项不披露(整数模型/贪心解码/1024 上下文/不隐藏架构/抗侧信道不覆盖/研究原型)——过度宣称，待核",
        )
    if any(v == "partial" for v in vals):
        return ProofBoundaryVerdict(
            claim, *vals, "flag", "PROOF_BOUNDARY.PARTIAL",
            "证明边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )
    return ProofBoundaryVerdict(
        claim, *vals, "ok", "PROOF_BOUNDARY.SELF_CONSISTENT",
        "四维边界声明自洽——只判声明诚实存在，不承诺证明正确/系统有效(存在≠有效性)",
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "source_as_fact": dict(proves_execution_not_fact="no", commitment_anchor_independent="yes", formal_scope_disclosed="yes", uncovered_disclosed="yes"),
        "anchor_self_set": dict(proves_execution_not_fact="yes", commitment_anchor_independent="no", formal_scope_disclosed="yes", uncovered_disclosed="yes"),
        "formal_overclaim": dict(proves_execution_not_fact="yes", commitment_anchor_independent="yes", formal_scope_disclosed="no", uncovered_disclosed="yes"),
        "uncovered_hidden": dict(proves_execution_not_fact="yes", commitment_anchor_independent="yes", formal_scope_disclosed="yes", uncovered_disclosed="no"),
        "partial_disclosure": dict(proves_execution_not_fact="yes", commitment_anchor_independent="yes", formal_scope_disclosed="partial", uncovered_disclosed="yes"),
        "literal_enum": dict(proves_execution_not_fact="maybe", commitment_anchor_independent="yes", formal_scope_disclosed="yes", uncovered_disclosed="yes"),
        "all_good": dict(proves_execution_not_fact="yes", commitment_anchor_independent="yes", formal_scope_disclosed="yes", uncovered_disclosed="yes"),
    }
    expects = {
        "source_as_fact": ("downgrade", "PROOF_BOUNDARY.SOURCE_AS_FACT"),
        "anchor_self_set": ("downgrade", "PROOF_BOUNDARY.ANCHOR_SELF_SET"),
        "formal_overclaim": ("downgrade", "PROOF_BOUNDARY.FORMAL_OVERCLAIM"),
        "uncovered_hidden": ("flag", "PROOF_BOUNDARY.UNCOVERED_HIDDEN"),
        "partial_disclosure": ("flag", "PROOF_BOUNDARY.PARTIAL"),
        "literal_enum": ("flag", "PROOF_BOUNDARY.INVALID_INPUT"),
        "all_good": ("ok", "PROOF_BOUNDARY.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_proof_boundary_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
