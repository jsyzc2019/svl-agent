"""跨领域迁移检验门禁 — 把 KB-RSI06 / KB-SIM09 编译成会拦/会判的动作。

一手来源：
  - KB-RSI06：样本内选出的最优参数必须在样本外固定复验；参数迁移后转负即过拟合。
  - KB-SIM09：评估上下文(模型/数据集/轮次)是经验的一部分；换模型可让改进从有效变倒退
    （SIM 论文 Opus→Gemini 68.41<73.89）。
  - DGM 跨基准 held-out（result.json D5）：SWE 进化 agent 在从未访问的 Polyglot 达
    28.9%（base 14.2%）、Poly→SWE 24.5%（base 20.0%）——**正向迁移增益**，
    论文用它排除基准过拟合。

关键设计教训（写本模块时判据引擎咬到自己，记入 commentary §51）：
  第一版用"源域精度 - 目标域精度"的绝对衰减判过拟合，把 DGM 的 SWE(0.50)→Poly(0.289)
  当成衰减 0.211 的过拟合反例——这是对一手数据的曲解：Polyglot 基准本身更难(base 仅 0.142)，
  0.289 相对基线 0.142 是 +0.147 的正向增益，恰是排除过拟合的证据。
  → 修正：过拟合判定必须看【相对目标域基线的迁移增益】，而非跨基准绝对精度。
  这正是框架自己防的 KB-RSI06（样本外复验）+ KB-R-MS01（事实真≠结论真）在编译时的活体体现。

编译纪律：
  - 真 held-out 且迁移增益 <= 0 → downgrade + revise（过拟合源领域）；
  - 真 held-out 且有正向增益 → ok + retain（排除过拟合，DGM 情形）；
  - 上下文变化使改进失效 → revise（KB-SIM09）；
  - 无样本外复验/目标域非 held-out → flag 不可外推；
  - 语义标志位判定，不用脆弱字面串（KB-AUDIT01）；
  - held_out 与 baseline 声明由研究者给出，本身不可自证（继承 KB-META01 边界）。

纯函数/数据类，无外部依赖。
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainPerformance:
    """判据在某领域的表现。"""
    domain: str
    precision: float
    n_samples: int

    @property
    def valid(self) -> bool:
        return self.n_samples > 0 and 0.0 <= self.precision <= 1.0


@dataclass(frozen=True)
class HoldoutClaim:
    """一次跨领域迁移声明。

    target_baseline：目标域【未优化基线】精度——过拟合判定的正确参照系。
    """
    source: DomainPerformance
    target: DomainPerformance
    target_baseline: float
    target_held_out: bool          # 目标域在优化/归纳时从未被访问
    source_context: str = ""       # 如 "opus@benchmark#r3"
    target_context: str = ""       # 如 "gemini@benchmark#r3"

    @property
    def context_changed(self) -> bool:
        return bool(self.source_context) and bool(self.target_context) and self.source_context != self.target_context

    @property
    def transfer_gain(self) -> float:
        """迁移增益 = 目标域(优化后) - 目标域(基线)。这才是过拟合判定的量。"""
        return round(self.target.precision - self.target_baseline, 4)


@dataclass(frozen=True)
class TransferVerdict:
    action: str            # ok | downgrade | flag
    code: str
    decision: str          # retain | revise | verify_only
    gain: float | None
    message: str


def check_transfer(claim: HoldoutClaim) -> TransferVerdict:
    """判一次跨领域迁移是否可外推。规则写死，不事后加权。

    1. 源/目标样本无效 或 baseline 越界 → flag，不给结论；
    2. 目标域非 held-out → flag（样本内，不是迁移证据，KB-RSI06）；
    3. 真 held-out 且迁移增益 <= 0 → downgrade + revise（过拟合源领域）；
    4. 上下文变化且目标精度低于源 → revise（KB-SIM09 叠加，不改 action 的 downgrade 优先级）；
    5. 真 held-out 且有正向增益 → ok + retain。
    """
    if (not claim.source.valid or not claim.target.valid
            or not 0.0 <= claim.target_baseline <= 1.0):
        return TransferVerdict(
            "flag", "XDOM.INVALID_SAMPLE", "verify_only", None,
            "源/目标样本无效或基线精度越界——迁移判定无统计意义，不给结论",
        )
    gain = claim.transfer_gain
    if not claim.target_held_out:
        return TransferVerdict(
            "flag", "XDOM.NOT_HELD_OUT", "verify_only", gain,
            "目标域在优化时已被访问——这是样本内表现，不构成迁移证据（KB-RSI06）",
        )
    if gain <= 0:
        return TransferVerdict(
            "downgrade", "XDOM.OVERFIT_SOURCE", "revise", gain,
            f"真 held-out 目标域迁移增益 {gain:+.3f} <= 0（未超过未优化基线）——"
            "改进未迁移，是过拟合源领域的信号，须 revise 而非 retain",
        )
    if claim.context_changed and claim.target.precision < claim.source.precision:
        return TransferVerdict(
            "downgrade", "XDOM.CONTEXT_DRIFT", "revise", gain,
            "评估上下文(模型/数据集/轮次)变化且目标精度低于源——经验不可直接迁移，须 revise（KB-SIM09）",
        )
    return TransferVerdict(
        "ok", "XDOM.TRANSFER_OK", "retain", gain,
        f"真 held-out 且迁移增益 {gain:+.3f} > 0——排除基准过拟合，可迁移，retain",
    )


# ---------------------------------------------------------------- 活体回归样例
DGM_SWE_TO_POLY = HoldoutClaim(
    source=DomainPerformance("swe-bench", 0.50, 200),
    target=DomainPerformance("polyglot", 0.289, 200),
    target_baseline=0.142,          # Polyglot 未优化基线（self-reported）
    target_held_out=True,
)
DGM_POLY_TO_SWE = HoldoutClaim(
    source=DomainPerformance("polyglot", 0.38, 50),
    target=DomainPerformance("swe-bench", 0.245, 200),
    target_baseline=0.20,           # SWE 未优化基线（self-reported）
    target_held_out=True,
)
# 合成反例（非 DGM 数据）：真 held-out 但迁移增益为负 → 过拟合。
SYNTHETIC_OVERFIT = HoldoutClaim(
    source=DomainPerformance("source-domain", 0.90, 100),
    target=DomainPerformance("held-out-domain", 0.14, 100),
    target_baseline=0.15,
    target_held_out=True,
)


def live_regression() -> dict:
    """活体回归：DGM 两向迁移均须放行(正向增益)；合成过拟合须降级。

    这里特意检验"绝对精度下降≠过拟合"——DGM SWE→Poly 从 0.50 降到 0.289，
    但相对目标基线 0.142 是正向增益，不得误判。
    """
    a = check_transfer(DGM_SWE_TO_POLY)
    b = check_transfer(DGM_POLY_TO_SWE)
    c = check_transfer(SYNTHETIC_OVERFIT)
    return {
        "dgm_swe_to_poly": {
            "verdict": a.action, "code": a.code, "decision": a.decision, "gain": a.gain,
            "expected": "ok / XDOM.TRANSFER_OK / retain (绝对精度降但增益正)",
            "passed": (a.action == "ok" and a.decision == "retain"),
        },
        "dgm_poly_to_swe": {
            "verdict": b.action, "code": b.code, "decision": b.decision, "gain": b.gain,
            "expected": "ok / XDOM.TRANSFER_OK / retain",
            "passed": (b.action == "ok" and b.decision == "retain"),
        },
        "synthetic_overfit": {
            "verdict": c.action, "code": c.code, "decision": c.decision, "gain": c.gain,
            "expected": "downgrade / XDOM.OVERFIT_SOURCE / revise",
            "passed": (c.action == "downgrade" and c.decision == "revise"),
        },
        "all_passed": (
            a.action == "ok" and b.action == "ok"
            and c.action == "downgrade" and c.decision == "revise"
        ),
    }
