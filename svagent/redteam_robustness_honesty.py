"""红队-防御增益诚实性门禁 — 把 arXiv:2611.24362 编译成会拦的动作（自主运维第四轮 §93）。

一手证据（见 audit_redteam_honesty/）：
  - S01 abs + S02 全文（arXiv:2611.24362v1，PIPETTE 紫队框架）。
  - 中心发现是"红队高 ASR ≠ 防御增益"：两个 SOTA RL 红队方法（RL-Hammer / PISmith）
    suffer from mode collapse，repeatedly discovering similar attack strategies whose
    additional successes add no additional robustness improvements to adversarial training。
  - 修正方向：dictionary learning-based reward 鼓励 broader coverage of attack strategies；
    on-policy adversarial training tailored to IPI defense；在 AgentDojo/ASB 上 achieve
    near-zero attack success rates on static attacks 且 withstand strong adaptive attacks，
    benign task utility close to that of the undefended baseline。

为什么是新牙（对比已有门禁）：
  本仓无 red-team / attack-success / adversarial-training / mode-collapse 维度门禁。
  安全线此前只判『声明自洽/检索接地』，不判『红队发现能否真正转化为防御增益』：
    ①红队 ASR 是否与防御增益挂钩（高 ASR≠robustness，mode collapse 是否被检出）；
    ②攻击策略覆盖是否被测量（dictionary learning reward vs 只堆相似攻击）；
    ③自适应攻击是否被测试（static near-zero vs withstand strong adaptive）；
    ④良性效用是否保持（close to undefended baseline vs 无差别阻断）。
  尺子对象是"任何 red-team→defense 转化声明"——可迁移、会拦，KB-META01 会拦才入。

编译纪律（与 gate_prereg.json 一致，实现前 SHA256 锁存 d0278ea1…）：
  - 语义枚举；字面串→flag(R0)；R0-R6 短路返回，不事后加权(防 Goodhart)；
  - 只判"边界声明是否诚实自洽"，不承诺防御真实有效(KB-R07/META01)；
    self-reported near-zero ASR / utility 按 KB-RSI07 折 1。

诚实边界：定位为审读外部红队/紫队研究的尺子，不判本仓；遵循 §58 选 A 不接 run_loop。
"""
from __future__ import annotations

from dataclasses import dataclass

_ENUM = frozenset({"yes", "no", "partial"})

# 中文文案字典：Compare 内不放中文字面量（AST 自审纪律）
_A = {
    "invalid_input": (
        "REDTEAM.INVALID_INPUT",
        "四维须为 yes/no/partial 语义枚举；非法值（含字面串）→ flag，不进内容判定",
    ),
    "asr_robustness_unlinked": (
        "REDTEAM.ASR_ROBUSTNESS_UNLINKED",
        "把高红队 ASR 冒充防御增益（mode collapse 未检出，additional successes add no robustness improvements）——ASR 与 robustness 未脱钩验证",
    ),
    "diversity_unmeasured": (
        "REDTEAM.DIVERSITY_UNMEASURED",
        "未测攻击策略覆盖（只堆相似攻击，无 dictionary learning reward 或等价覆盖度量）——ASR 高但策略单一",
    ),
    "adaptive_untested": (
        "REDTEAM.ADAPTIVE_UNTESTED",
        "只报 static near-zero ASR、未测 strong adaptive attacks——静态防御数字冒充鲁棒性",
    ),
    "utility_broken": (
        "REDTEAM.UTILITY_BROKEN",
        "防御靠无差别阻断、良性效用未保持 close to undefended baseline——以牺牲任务效用换低 ASR",
    ),
    "partial": (
        "REDTEAM.PARTIAL",
        "红队-防御增益边界披露覆盖不全(partial)——拦截面存在但缺口未补齐，待核",
    ),
    "ok": (
        "REDTEAM.SELF_CONSISTENT",
        "四维 robustness 边界声明自洽——只判声明诚实存在，不承诺防御真实有效(near-zero ASR self-reported 折 1)",
    ),
}


@dataclass(frozen=True)
class RedteamRobustnessVerdict:
    claim: str
    asr_robustness_linked: str
    attack_diversity_measured: str
    adaptive_attack_tested: str
    benign_utility_preserved: str
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_redteam_robustness_honesty(
    claim: str,
    *,
    asr_robustness_linked: str,
    attack_diversity_measured: str,
    adaptive_attack_tested: str,
    benign_utility_preserved: str,
) -> RedteamRobustnessVerdict:
    """判一个红队/紫队研究是否诚实披露四个 robustness 边界（不承诺防御有效）。

    输入须为语义枚举：四维 ∈ {yes, no, partial}

    规则按优先级短路返回（与 gate_prereg.json R0-R6 一致）：
      R0 任一非枚举 → flag
      R1 asr_robustness_linked=no → downgrade（高 ASR 冒充防御增益/mode collapse 未检）
      R2 attack_diversity_measured=no → downgrade（未测覆盖/只堆相似攻击）
      R3 adaptive_attack_tested=no → flag（只报 static near-zero/未测 adaptive）
      R4 benign_utility_preserved=no → flag（无差别阻断/效用未保持）
      R5 任一 partial → flag（覆盖不全，待核）
      R6 全 yes → ok（只判声明自洽，防御 near-zero ASR 折 1）
    """
    vals = (asr_robustness_linked, attack_diversity_measured,
            adaptive_attack_tested, benign_utility_preserved)
    if any(v not in _ENUM for v in vals):
        code, msg = _A["invalid_input"]
        return RedteamRobustnessVerdict(claim, *(str(v) for v in vals), "flag", code, msg)
    if asr_robustness_linked == "no":
        code, msg = _A["asr_robustness_unlinked"]
        return RedteamRobustnessVerdict(claim, *vals, "downgrade", code, msg)
    if attack_diversity_measured == "no":
        code, msg = _A["diversity_unmeasured"]
        return RedteamRobustnessVerdict(claim, *vals, "downgrade", code, msg)
    if adaptive_attack_tested == "no":
        code, msg = _A["adaptive_untested"]
        return RedteamRobustnessVerdict(claim, *vals, "flag", code, msg)
    if benign_utility_preserved == "no":
        code, msg = _A["utility_broken"]
        return RedteamRobustnessVerdict(claim, *vals, "flag", code, msg)
    if any(v == "partial" for v in vals):
        code, msg = _A["partial"]
        return RedteamRobustnessVerdict(claim, *vals, "flag", code, msg)
    code, msg = _A["ok"]
    return RedteamRobustnessVerdict(claim, *vals, "ok", code, msg)


def live_regression() -> dict:
    """7 个活体样例回归——对齐 gate_prereg.json 的 R0-R6 预期。"""
    cases = {
        "asr_robustness_unlinked": dict(asr_robustness_linked="no", attack_diversity_measured="yes", adaptive_attack_tested="yes", benign_utility_preserved="yes"),
        "diversity_unmeasured": dict(asr_robustness_linked="yes", attack_diversity_measured="no", adaptive_attack_tested="yes", benign_utility_preserved="yes"),
        "adaptive_untested": dict(asr_robustness_linked="yes", attack_diversity_measured="yes", adaptive_attack_tested="no", benign_utility_preserved="yes"),
        "utility_broken": dict(asr_robustness_linked="yes", attack_diversity_measured="yes", adaptive_attack_tested="yes", benign_utility_preserved="no"),
        "partial_disclosure": dict(asr_robustness_linked="yes", attack_diversity_measured="yes", adaptive_attack_tested="partial", benign_utility_preserved="yes"),
        "literal_enum": dict(asr_robustness_linked="maybe", attack_diversity_measured="yes", adaptive_attack_tested="yes", benign_utility_preserved="yes"),
        "all_good": dict(asr_robustness_linked="yes", attack_diversity_measured="yes", adaptive_attack_tested="yes", benign_utility_preserved="yes"),
    }
    expects = {
        "asr_robustness_unlinked": ("downgrade", "REDTEAM.ASR_ROBUSTNESS_UNLINKED"),
        "diversity_unmeasured": ("downgrade", "REDTEAM.DIVERSITY_UNMEASURED"),
        "adaptive_untested": ("flag", "REDTEAM.ADAPTIVE_UNTESTED"),
        "utility_broken": ("flag", "REDTEAM.UTILITY_BROKEN"),
        "partial_disclosure": ("flag", "REDTEAM.PARTIAL"),
        "literal_enum": ("flag", "REDTEAM.INVALID_INPUT"),
        "all_good": ("ok", "REDTEAM.SELF_CONSISTENT"),
    }
    checks, detail = {}, {}
    for name, inp in cases.items():
        v = check_redteam_robustness_honesty("live:" + name, **inp)
        exp_a, exp_c = expects[name]
        detail[name] = f"{v.action}/{v.code}"
        checks[name] = (v.action == exp_a and v.code == exp_c)
    return {"checks": checks, "cases": detail, "all_passed": all(checks.values())}
