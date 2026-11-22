"""选择性监督诚实性门禁 — 把清华 System-1/System-2 协同设计的"门控审查自身训练数据"编译成会判动作（§78）。

一手证据（见 audit_system1_system2/）：
  - S01 论文 PDF（arXiv:2610.39497v1，29 Oct 2026，Tsinghua 季向阳团队，Perspective；
    SHA256 a7b5b7e4…，文本 6... 见 manifest）：
    §7.2 "Selective Supervision: The Gate Censors Its Own Training Data"：门控决定执行哪些
      交互就决定训练于哪些交互，p_train(i) ∝ p_cand(i)·e(i) ≠ p_cand(i)——标签非随机缺失
      (MNAR)；"a candidate scored as low-value is suppressed, its outcome never observed,
      and the score never corrected"；解法：探索混合 π_ε=(1−ε)π_CI+επ_0（全池非零 e(i)≥επ_0）
      或独立审计采样率 a（e(i)≥a）；IPW / doubly-robust 得无偏误差；审计率须 "fixed
      independently of the predictor's scores"；"we regard this as the one most in need of theory"。
    §2.4 "utility is misspecified, so that the predictor systematically suppresses the very
      interactions that would reveal the misspecification"；"regimes (1) and (5) are the most
      insidious, since the predictor's errors concentrate precisely where it has no data and
      the interactions that would reveal them are never executed"。
    Theorem 19 interpretation："blind spots, not average error, dominate once the predictor is
      otherwise accurate"；"The theorem does not imply a self-improving loop"。
  - S02 PaperAgent 公众号文（用户指定，中文解读）："门控会审查自己的训练数据：被拒绝的交互
    没有结果，误判也就难以纠正。因此，独立审计与探索不是可选项，而是闭环能长期工作的保险丝"。

为什么是新牙（对比现有 26 门禁）：
  §77 criterion_origin_honesty 判自评估系统的判据来源/召回边界/外部锚/独立评审缺口——
    那是"声明是否诚实"；本门禁判"筛选器决定自身训练数据 → 标签 MNAR → 盲点自强化"的
    <结构性机制>，即使主体诚实声明也仍存在的偏差。§74 supervision_viability 判评审者能力
    前提；§71 proof_boundary_honesty 判形式化证明边界。核验确认：
    选择性监督/MNAR/标签非随机缺失、探索与独立审计作为保险丝——两项零门禁覆盖。
    尺子对象是"任何筛选器决定自身训练数据的系统"（数据选择/主动学习/路由/Agent工具筛选），
    可迁移、会拦（压制区零概率/审计被自审污染/盲点隐藏/漏判反事实不承认都拦），KB-META01 通过。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 7976b4e1…）：
  - 语义枚举；字面串→flag(R0，避 §56 brittle 根因)；
  - 规则 R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判『机制声明是否诚实自洽』，不承诺筛选真带来收益——存在≠有效性(KB-META01/AUDIT03)；
    Perspective 观点文、定理在假设下成立、无实测加速、作者称 central hypothesis——折1(KB-RSI07)。

诚实边界：定位为审读外部"带门控的自监督系统"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
与 §77（声明诚实）、§74（能力前提）、§71（形式化证明）对象动作不同，拦截面独立。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})


@dataclass(frozen=True)
class SelectiveSupervisionVerdict:
    claim: str
    propensity_reaches_suppressed: str
    audit_independent_of_score: str
    blind_spot_disclosed: str
    counterfactual_loss_acknowledged: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_selective_supervision_honesty(
    claim: str,
    *,
    propensity_reaches_suppressed: str,
    audit_independent_of_score: str,
    blind_spot_disclosed: str,
    counterfactual_loss_acknowledged: str,
) -> SelectiveSupervisionVerdict:
    """判一个带门控的自监督系统是否诚实处理"筛选器审查自身训练数据"的结构性偏差。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 propensity_reaches_suppressed=no → downgrade（压制区零概率→标签MNAR）
      R2 audit_independent_of_score=no → downgrade（审计率依赖分数→审计被自审污染）
      R3 blind_spot_disclosed=no → downgrade（盲点隐藏，平均误差掩盖）
      R4 counterfactual_loss_acknowledged=no → downgrade（漏判反事实损失不承认）
      R5 任一 partial → flag
      R6 全 yes → ok（只判机制声明自洽）
    """
    vals = (propensity_reaches_suppressed, audit_independent_of_score,
            blind_spot_disclosed, counterfactual_loss_acknowledged)
    if any(v not in _ENUM for v in vals):
        return SelectiveSupervisionVerdict(
            claim, *(str(v) for v in vals),
            "flag", "SELECTIVE_SUPERVISION.INVALID_INPUT",
            "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
        )
    if propensity_reaches_suppressed == "no":
        return SelectiveSupervisionVerdict(
            claim, *vals, "downgrade", "SELECTIVE_SUPERVISION.MNAR_ZERO_PROPENSITY",
            "压制区零执行概率(被判低价值者结果永不观测、分数永不修正)→标签非随机缺失(MNAR)，自我强化的选择性监督，判定打折",
        )
    if audit_independent_of_score == "no":
        return SelectiveSupervisionVerdict(
            claim, *vals, "downgrade", "SELECTIVE_SUPERVISION.AUDIT_SELF_CENSORED",
            "审计采样率依赖预测器分数(只审自己选的/按分数抽)→审计被自审污染，无法发现漏判，判定打折",
        )
    if blind_spot_disclosed == "no":
        return SelectiveSupervisionVerdict(
            claim, *vals, "downgrade", "SELECTIVE_SUPERVISION.BLIND_SPOT_HIDDEN",
            "盲点/错误集中区不披露(只报平均误差；误差恰集中在无数据且永不执行的交互)→Theorem19盲点主导被掩盖，判定打折",
        )
    if counterfactual_loss_acknowledged == "no":
        return SelectiveSupervisionVerdict(
            claim, *vals, "downgrade", "SELECTIVE_SUPERVISION.COUNTERFACTUAL_HIDDEN",
            "被拒交互的漏判反事实损失不承认/不估计(尤其安全关键、不可逆动作)→utility误设时系统性压制能揭示错误的交互，判定打折",
        )
    if any(v == "partial" for v in vals):
        return SelectiveSupervisionVerdict(
            claim, *vals, "flag", "SELECTIVE_SUPERVISION.PARTIAL",
            "选择性监督机制声明覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
        )
    return SelectiveSupervisionVerdict(
        claim, *vals, "ok", "SELECTIVE_SUPERVISION.SELF_CONSISTENT",
        "四维机制声明自洽——只判声明诚实存在，不承诺筛选真带来收益(存在≠有效性)",
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "mnar_zero_propensity": dict(propensity_reaches_suppressed="no", audit_independent_of_score="yes", blind_spot_disclosed="yes", counterfactual_loss_acknowledged="yes"),
        "audit_self_censored": dict(propensity_reaches_suppressed="yes", audit_independent_of_score="no", blind_spot_disclosed="yes", counterfactual_loss_acknowledged="yes"),
        "blind_spot_hidden": dict(propensity_reaches_suppressed="yes", audit_independent_of_score="yes", blind_spot_disclosed="no", counterfactual_loss_acknowledged="yes"),
        "counterfactual_hidden": dict(propensity_reaches_suppressed="yes", audit_independent_of_score="yes", blind_spot_disclosed="yes", counterfactual_loss_acknowledged="no"),
        "partial_disclosure": dict(propensity_reaches_suppressed="yes", audit_independent_of_score="yes", blind_spot_disclosed="partial", counterfactual_loss_acknowledged="yes"),
        "literal_enum": dict(propensity_reaches_suppressed="maybe", audit_independent_of_score="yes", blind_spot_disclosed="yes", counterfactual_loss_acknowledged="yes"),
        "all_good": dict(propensity_reaches_suppressed="yes", audit_independent_of_score="yes", blind_spot_disclosed="yes", counterfactual_loss_acknowledged="yes"),
    }
    expects = {
        "mnar_zero_propensity": ("downgrade", "SELECTIVE_SUPERVISION.MNAR_ZERO_PROPENSITY"),
        "audit_self_censored": ("downgrade", "SELECTIVE_SUPERVISION.AUDIT_SELF_CENSORED"),
        "blind_spot_hidden": ("downgrade", "SELECTIVE_SUPERVISION.BLIND_SPOT_HIDDEN"),
        "counterfactual_hidden": ("downgrade", "SELECTIVE_SUPERVISION.COUNTERFACTUAL_HIDDEN"),
        "partial_disclosure": ("flag", "SELECTIVE_SUPERVISION.PARTIAL"),
        "literal_enum": ("flag", "SELECTIVE_SUPERVISION.INVALID_INPUT"),
        "all_good": ("ok", "SELECTIVE_SUPERVISION.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_selective_supervision_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
