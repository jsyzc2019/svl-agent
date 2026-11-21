"""谱系打折门禁 — 从 §55 SIM 再审的「循环论证警觉」编译（认知+代码强固协同）。

来源与动机（commentary §55、sim_review_result.json）：
  用 §51/§53/§54 新长出的六道门禁回头审曾启发它们的 SIM 论文，审出三处「旧框架
  只记了局限、没长牙」的补刀。但门禁的牙齿恰恰从 SIM 经验里长出，用它审 SIM
  等于「学生评老师」——若据「审出缺口」就宣称新框架优于 SIM，是循环论证，
  按 KB-STRUCT02 必须打折。§55 把这条写成文字警觉，本模块把它编译成通用门禁。

扬长避短（对比现有唯一对应物）：
  rsis_framework_analysis.py:t2_isomorphism_contamination 硬编码到 awesome-rsi
  综述，靠字符串匹配「同谱系」/「高度同构」判定——不可复用、且有 KB-AUDIT01
  脆弱字面串风险。本模块：
    - 只接受语义枚举 source_overlap / isomorphism，传字面串 → flag（R6）；
    - 规则写死、纯函数、无全局副作用，不产生新优化目标（防 Goodhart）；
    - 会拦（循环声称 block）、会判（同构声称 downgrade）、会降级（部分重叠 flag）；
    - 锚定 KB-STRUCT02 / KB-META01 并在其 support 加固指针（认知域协同）。

诚实边界：门禁只给「独立性声称」打折，不判定对象本身对错、不替代实质证据；
谱系/同构关系须调用方如实声明，声明本身不可自证；本模块由 SIM 经验启发，
不给本仓框架独立背书（KB-STRUCT02）。活体样例用于机制回归，非复现实验。
"""
from __future__ import annotations

from dataclasses import dataclass

# 语义枚举——写死；判定绝不读字符串内容（避开 t2 的 brittle 根因，KB-AUDIT01）
_SOURCE_OVERLAP = frozenset({"none", "partial", "full"})
_ISOMORPHISM = frozenset({"none", "partial", "high"})


@dataclass(frozen=True)
class DiscountVerdict:
    claim: str
    source_overlap: str
    isomorphism: str
    claimed_independence: bool
    claim_type: str
    action: str        # ok | downgrade | flag | block
    code: str
    message: str


def discount_claim(
    claim: str,
    *,
    source_overlap: str,
    isomorphism: str,
    claimed_independence: bool,
    claim_type: str = "independent_validation",
) -> DiscountVerdict:
    """对一条「独立性声称」按谱系/同构关系打折。

    输入须为语义枚举：
      source_overlap ∈ {none, partial, full}  —— 判据的知识来源与被审对象同源程度
      isomorphism  ∈ {none, partial, high}   —— 两者结构同构程度
      claimed_independence —— 是否声称「独立验证」

    规则按优先级写死（不事后加权）：
      R6 字面串/非法枚举 → flag（拒绝对字符串内容做判定）
      R1 全同源 + 声称独立 → block（循环论证：用从对象长出的牙证明对象错了）
      R2 高同构 + 声称独立 → downgrade（同构≠独立验证）
      R3 部分同构 + 声称独立 → flag（部分重叠，待核）
      R4 未声称独立且确有同源/同构 → ok/preserve（诚实标注谱系呼应，不拦截）
      R5 无同源无同构 → ok/independent
    """
    # R6：语义输入校验优先——任何字面串（如「高度同构」）都不进入内容匹配
    if source_overlap not in _SOURCE_OVERLAP or isomorphism not in _ISOMORPHISM \
            or not isinstance(claimed_independence, bool):
        return DiscountVerdict(
            claim, str(source_overlap), str(isomorphism),
            bool(claimed_independence) if isinstance(claimed_independence, bool) else False,
            claim_type, "flag", "LINEAGE.NON_SEMANTIC_INPUT",
            "谱系/同构关系须以语义枚举声明；拒绝对字面串做判定"
            "（避开 t2 的 brittle 根因，KB-AUDIT01）",
        )

    # R1：循环论证——最重，优先拦截
    if source_overlap == "full" and claimed_independence:
        return DiscountVerdict(
            claim, source_overlap, isomorphism, claimed_independence, claim_type,
            "block", "LINEAGE.CIRCULAR_CLAIM",
            "判据从被审对象长出，又回头声称独立验证了该对象=循环论证；"
            "禁止用学生评老师（KB-STRUCT02）。若确有净贡献，须改称机制借鉴并放弃独立性声称",
        )

    # R2：高同构 ≠ 独立验证
    if isomorphism == "high" and claimed_independence:
        return DiscountVerdict(
            claim, source_overlap, isomorphism, claimed_independence, claim_type,
            "downgrade", "LINEAGE.ISOMORPHIC_NOT_INDEPENDENT",
            "高同构只构成谱系呼应，非独立验证；印证力度打折（KB-STRUCT02）",
        )

    # R3：部分重叠
    if isomorphism == "partial" and claimed_independence:
        return DiscountVerdict(
            claim, source_overlap, isomorphism, claimed_independence, claim_type,
            "flag", "LINEAGE.PARTIAL_OVERLAP",
            "部分同构却声称独立验证，标注待核，须给出非重叠的独立证据",
        )

    # R4：诚实标注谱系呼应——不拦截，反而 preserve
    if not claimed_independence and (source_overlap != "none" or isomorphism != "none"):
        return DiscountVerdict(
            claim, source_overlap, isomorphism, claimed_independence, claim_type,
            "ok", "LINEAGE.PRESERVE_HONEST_LABEL",
            "未声称独立、如实标注同源/同构——诚实加分，preserve（KB-R08）",
        )

    # R5：真独立
    return DiscountVerdict(
        claim, source_overlap, isomorphism, claimed_independence, claim_type,
        "ok", "LINEAGE.INDEPENDENT",
        "无同源、无同构，独立性声称可保留（仍需实质证据，本门禁不替代证据评估）",
    )


def live_regression() -> dict:
    """活体回归：循环声称拦 / 诚实借鉴放行 / 真独立放行 / 字面串 flag。"""
    sim = discount_claim(
        "新框架优于 SIM 论文（审出三处缺口）",
        source_overlap="full", isomorphism="high", claimed_independence=True,
    )
    swe = discount_claim(
        "借鉴 SWE-Gym 五类工程纪律编译稳健性门禁",
        source_overlap="partial", isomorphism="high", claimed_independence=False,
        claim_type="mechanism_inheritance",
    )
    ind = discount_claim(
        "与 awesome-rsi 无谱系关系的独立来源佐证",
        source_overlap="none", isomorphism="none", claimed_independence=True,
    )
    # brittle 对照：t2 会匹配「高度同构」字面串；本门禁必须拒绝字符串输入
    bri = discount_claim(
        "高度同构", source_overlap="高度同构", isomorphism="high",
        claimed_independence=True,
    )
    checks = {
        "sim_circular_blocked": sim.action == "block" and sim.code == "LINEAGE.CIRCULAR_CLAIM",
        "swe_honest_preserved": swe.action == "ok" and swe.code == "LINEAGE.PRESERVE_HONEST_LABEL",
        "independent_ok": ind.action == "ok" and ind.code == "LINEAGE.INDEPENDENT",
        "brittle_rejected": bri.action == "flag" and bri.code == "LINEAGE.NON_SEMANTIC_INPUT",
    }
    return {
        "sim_review": {"action": sim.action, "code": sim.code},
        "swe_borrow": {"action": swe.action, "code": swe.code},
        "independent": {"action": ind.action, "code": ind.code},
        "brittle_control": {"action": bri.action, "code": bri.code},
        "checks": checks,
        "all_passed": all(checks.values()),
    }
