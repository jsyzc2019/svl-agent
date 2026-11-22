"""计算饱和诚实性门禁 — 把 UltraBERT 的"loss下降≠下游提升、须报饱和点"编译成会判动作（§86）。

一手证据（见 audit_ultrabert/，arXiv:2610.15028v1 HTML 全文，SHA256 6c125cae…）：
  - §1 贡献：
    "downstream performance saturates around 1–2T tokens even as training and validation
    losses keep decreasing, unlike decoders, which continue to improve. This indicates an
    upper bound that additional tokens cannot raise."
  - §3.1：
    "Encoders trained with the MLM objective saturate around 1–2 trillion tokens, while both
    training and validation losses keep decreasing. In particular, the BEIR scores saturate
    even earlier, showing no significant improvement beyond the first evaluation point of
    275B tokens."
    "These results suggest that encoder models have an upper bound that additional pre-training
    tokens cannot raise."
  - §1 方法论：
    "At saturation, where convergence speed no longer confounds the comparison"

为什么是新牙（对比现有门禁）：
  evaluation_reliability 判评估可复现性与评审独立性，非 scale 声明的饱和诚实；
  backtest_integrity 判回测信息污染，estimation 判估参，scoring_integrity 判计分绕过——
  无一判"scale/训练声明是否报告下游饱和点、区分训练 loss 下降与下游能力、测边际收益"。
  尺子可迁移、会拦，KB-META01 通过。

编译纪律（gate_prereg.json SHA256 febd1f25…，实现前已锁存）：
  语义枚举；字面串→flag(R0)；R1-R4 按优先级 downgrade；R5 partial→flag；R6 全 yes→ok；
  只判机制声明是否诚实自洽，不承诺饱和结论普适（存在≠有效性 KB-META01/AUDIT03）；
  self-reported 1–2T/275B 等按 KB-RSI07 折1。

诚实边界：定位为审读外部"scale/预训练声明"的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

_A = {
    "invalid": "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    "no_saturation": "未报告下游饱和点，暗示 scale 无限受益（upper bound additional tokens cannot raise 被隐瞒）→ §1/§3.1，判定打折",
    "no_split": "未区分训练/验证 loss 下降与下游能力（losses keep decreasing 却等同于能力提升）→ §3.1，判定打折",
    "no_marginal": "未测边际收益/额外 token 无收益的证据（beyond 275B no significant improvement）→ §3.1，判定打折",
    "loss_as_capability": "用 loss 下降冒充下游能力提升（把优化目标改善当成任务能力改善）→ §1，判定打折",
    "partial": "计算饱和诚实性声明覆盖不全（partial）——拦截面存在但缺口未补齐，待核",
    "ok": "四维计算饱和声明自洽——只判声明诚实存在，不承诺饱和结论普适（存在≠有效性）",
}


@dataclass(frozen=True)
class ComputeSaturationVerdict:
    claim: str
    saturation_reported: str
    loss_vs_downstream_split: str
    marginal_gain_measured: str
    no_loss_as_capability: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_compute_saturation_honesty(
    claim: str,
    *,
    saturation_reported: str,
    loss_vs_downstream_split: str,
    marginal_gain_measured: str,
    no_loss_as_capability: str,
) -> ComputeSaturationVerdict:
    """判一个声称 scale 带来提升的系统是否诚实报告饱和与边际收益。

    四维均为能力语义：yes=具备。

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 saturation_reported=no → downgrade
      R2 loss_vs_downstream_split=no → downgrade
      R3 marginal_gain_measured=no → downgrade
      R4 no_loss_as_capability=no → downgrade
      R5 任一 partial → flag
      R6 全 yes → ok
    """
    vals = (saturation_reported, loss_vs_downstream_split,
            marginal_gain_measured, no_loss_as_capability)
    if any(v not in _ENUM for v in vals):
        return ComputeSaturationVerdict(
            claim, *(str(v) for v in vals),
            "flag", "COMPUTE_SAT.INVALID_INPUT", _A["invalid"],
        )
    if saturation_reported == "no":
        return ComputeSaturationVerdict(
            claim, *vals, "downgrade", "COMPUTE_SAT.NO_SATURATION", _A["no_saturation"],
        )
    if loss_vs_downstream_split == "no":
        return ComputeSaturationVerdict(
            claim, *vals, "downgrade", "COMPUTE_SAT.NO_SPLIT", _A["no_split"],
        )
    if marginal_gain_measured == "no":
        return ComputeSaturationVerdict(
            claim, *vals, "downgrade", "COMPUTE_SAT.NO_MARGINAL", _A["no_marginal"],
        )
    if no_loss_as_capability == "no":
        return ComputeSaturationVerdict(
            claim, *vals, "downgrade", "COMPUTE_SAT.LOSS_AS_CAPABILITY", _A["loss_as_capability"],
        )
    if any(v == "partial" for v in vals):
        return ComputeSaturationVerdict(
            claim, *vals, "flag", "COMPUTE_SAT.PARTIAL", _A["partial"],
        )
    return ComputeSaturationVerdict(
        claim, *vals, "ok", "COMPUTE_SAT.SELF_CONSISTENT", _A["ok"],
    )


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json R0-R6 预期。"""
    def g(**over):
        base = dict(saturation_reported="yes", loss_vs_downstream_split="yes",
                    marginal_gain_measured="yes", no_loss_as_capability="yes")
        base.update(over)
        return base
    cases = {
        "no_saturation": g(saturation_reported="no"),
        "no_split": g(loss_vs_downstream_split="no"),
        "no_marginal": g(marginal_gain_measured="no"),
        "loss_as_capability": g(no_loss_as_capability="no"),
        "partial_disclosure": g(marginal_gain_measured="partial"),
        "literal_enum": g(saturation_reported="maybe"),
        "all_good": g(),
    }
    expects = {
        "no_saturation": ("downgrade", "COMPUTE_SAT.NO_SATURATION"),
        "no_split": ("downgrade", "COMPUTE_SAT.NO_SPLIT"),
        "no_marginal": ("downgrade", "COMPUTE_SAT.NO_MARGINAL"),
        "loss_as_capability": ("downgrade", "COMPUTE_SAT.LOSS_AS_CAPABILITY"),
        "partial_disclosure": ("flag", "COMPUTE_SAT.PARTIAL"),
        "literal_enum": ("flag", "COMPUTE_SAT.INVALID_INPUT"),
        "all_good": ("ok", "COMPUTE_SAT.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_compute_saturation_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
