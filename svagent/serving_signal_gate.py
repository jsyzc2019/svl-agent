"""训练-服务信号可得性门禁 — 把 HiGR 暴露的 train-serving 落差编译成会判动作（§62）。

一手来源：
  HiGR (arxiv 2512.24787v5) line 366-380：正样本 y+ = engaged watch sequence 按
  true user feedback 降序重排；line 425-428：线上推理只有 user profile + behavior
  sequence，且经 dedup/availability/safety/business rules 过滤。论文全文未讨论该
  train-serving 落差（仅 line 430 泛泛批评他人 exposure bias）。

为什么是新牙（对比现有判据）：
  - finance_blind_test：防标签泄漏进【判据】（揭盲在判据产出后）——管的是评测端；
  - backtest_integrity：防事后 spoiler 进【回测】——管的是回测端；
  - transfer_holdout：防过拟合源领域（跨领域增益）——管的是泛化端；
  - 本模块管【训练监督依赖的信号在服务时是否可得】这一口径维度——四者拦截动作独立。
  这是 KB-AUDIT04（对象/口径对等）在 train-serving 维度的延伸。

编译纪律（与 serving_gate_prereg.json 一致，实现前 SHA256 锁存 fddecbea…）：
  - 语义枚举 yes/no/partial + 布尔，传字面串 → flag（R0，避开 §56 brittle 根因）；
  - 规则 R1-R5 按优先级写死，不事后加权（防 Goodhart）；
  - 只判"信号可得性与声明"，不判论文造假/方法无效——HiGR 用后验反馈构造 y+
    是 listwise 偏好学习标准做法，落点是"未声明的落差"这一可判缺口。

诚实边界：声明本身不可自证（继承 KB-META01）；活体样例用于机制回归，非复现
外部实验；按 KB-STRUCT02 不构成对本仓框架的独立验证；不接入 run_loop（遵循 §58 选 A）。
"""
from __future__ import annotations

from dataclasses import dataclass

# 语义枚举——写死；判定绝不读字符串内容（KB-AUDIT01 brittle 根因）
_AVAILABILITY = frozenset({"yes", "no", "partial"})
_BOOL_FIELDS = ("gap_disclosed", "no_bridge", "serving_input_equivalent")


@dataclass(frozen=True)
class ServingSignalVerdict:
    claim: str
    training_signal_available_at_serving: str
    gap_disclosed: bool
    no_bridge: bool
    serving_input_equivalent: bool
    action: str        # ok | downgrade | flag
    code: str
    message: str


def check_serving_signal(
    claim: str,
    *,
    training_signal_available_at_serving: str,
    gap_disclosed: bool,
    no_bridge: bool,
    serving_input_equivalent: bool,
) -> ServingSignalVerdict:
    """判训练监督依赖的信号，在服务/推理时是否可得、落差是否被声明与桥接。

    输入须为语义枚举 + 布尔：
      training_signal_available_at_serving ∈ {yes, no, partial}
      gap_disclosed — 是否明确声明 train-serving 落差
      no_bridge — 是否完全没有桥接机制（代理预测/两阶段对齐/延迟反馈建模）
      serving_input_equivalent — 服务输入是否与训练输入同分布

    规则按优先级写死（与 serving_gate_prereg.json 一致）：
      R0 字面串/畸形输入 → flag（拒绝对字符串内容判定）
      R1 no + 未声明 + 无桥接 → downgrade（未声明的落差，监督不可复现）
      R2 no + 已声明 + 无桥接 → flag（诚实披露但缺口未处理）
      R3 no + 已声明 + 有桥接 → ok（落差已知且显式桥接）
      R4 yes → ok（训练服务口径对等）
      R5 partial + 未声明 → flag（代理信号口径未声明）
    """
    avail = training_signal_available_at_serving

    # R0：语义输入校验优先——字面串/非枚举一律 flag，不进内容判定
    if avail not in _AVAILABILITY:
        return ServingSignalVerdict(
            claim, str(avail), gap_disclosed, no_bridge, serving_input_equivalent,
            "flag", "SERVING.INVALID_ENUM",
            "服务时信号可得性须为 yes/no/partial 语义枚举；收到非法值（含字面串）→ flag，不进内容判定",
        )
    if not (isinstance(gap_disclosed, bool) and isinstance(no_bridge, bool)
            and isinstance(serving_input_equivalent, bool)):
        return ServingSignalVerdict(
            claim, avail, gap_disclosed, no_bridge, serving_input_equivalent,
            "flag", "SERVING.INVALID_FLAG",
            "布尔标志位非 bool → flag，拒绝对真值做内容判定",
        )

    # R4：信号服务时可得——口径对等
    if avail == "yes":
        return ServingSignalVerdict(
            claim, avail, gap_disclosed, no_bridge, serving_input_equivalent,
            "ok", "SERVING.INVARIANT",
            "训练依赖的监督信号在服务时可得——训练/服务口径对等，无此落差",
        )

    # R5：部分可得（代理信号）但未声明
    if avail == "partial" and not gap_disclosed:
        return ServingSignalVerdict(
            claim, avail, gap_disclosed, no_bridge, serving_input_equivalent,
            "flag", "SERVING.PROXY_UNDISCLOSED",
            "服务时只能拿到代理信号而非真值，且未声明该口径落差 → flag 待核",
        )

    # avail == "no" 分支
    if not gap_disclosed and no_bridge:
        # R1：未声明落差且无桥接
        return ServingSignalVerdict(
            claim, avail, gap_disclosed, no_bridge, serving_input_equivalent,
            "downgrade", "SERVING.UNDISCLOSED_GAP",
            "训练监督依赖的信号在服务时不可得，且未声明落差、无桥接机制——"
            "监督信号在服务口径不可复现，结论打折（KB-AUDIT04 口径不对等）",
        )
    if gap_disclosed and no_bridge:
        # R2：诚实披露但缺口未处理
        return ServingSignalVerdict(
            claim, avail, gap_disclosed, no_bridge, serving_input_equivalent,
            "flag", "SERVING.DISCLOSED_NO_BRIDGE",
            "已声明 train-serving 落差但完全无桥接机制——诚实但不完整，待核",
        )
    if gap_disclosed and not no_bridge:
        # R3：落差已知且有桥接
        return ServingSignalVerdict(
            claim, avail, gap_disclosed, no_bridge, serving_input_equivalent,
            "ok", "SERVING.BRIDGED",
            "训练监督信号服务时不可得，但落差已声明且有显式桥接（代理/两阶段对齐）"
            "——口径已知且处理，preserve（仍不替代实质证据）",
        )
    # 兜底：no + 未声明 + 有桥接（声明缺失但存在桥接）→ flag，口径未披露
    return ServingSignalVerdict(
        claim, avail, gap_disclosed, no_bridge, serving_input_equivalent,
        "flag", "SERVING.BRIDGE_UNDISCLOSED",
        "存在桥接机制但未声明 train-serving 落差——口径未披露，待核",
    )


# ---------------------------------------------------------------- 活体回归样例

_LIVE_CASES = [
    ("HiGR_undisclosed_gap", dict(training_signal_available_at_serving="no",
                                  gap_disclosed=False, no_bridge=True,
                                  serving_input_equivalent=False), "downgrade"),
    ("disclosed_no_bridge", dict(training_signal_available_at_serving="no",
                                 gap_disclosed=True, no_bridge=True,
                                 serving_input_equivalent=False), "flag"),
    ("disclosed_with_bridge", dict(training_signal_available_at_serving="no",
                                   gap_disclosed=True, no_bridge=False,
                                   serving_input_equivalent=False), "ok"),
    ("signal_available", dict(training_signal_available_at_serving="yes",
                              gap_disclosed=False, no_bridge=False,
                              serving_input_equivalent=True), "ok"),
    ("partial_undisclosed", dict(training_signal_available_at_serving="partial",
                                 gap_disclosed=False, no_bridge=False,
                                 serving_input_equivalent=False), "flag"),
    ("literal_string_flag", dict(training_signal_available_at_serving="高度同构",
                                 gap_disclosed=False, no_bridge=False,
                                 serving_input_equivalent=False), "flag"),
]


def live_regression() -> dict:
    """活体回归：6 个样例逐条对齐预注册预期，不放水。"""
    checks, cases = {}, {}
    for name, kw, expected in _LIVE_CASES:
        v = check_serving_signal("回归样例", **kw)
        cases[name] = f"action={v.action} code={v.code}"
        checks[name] = (v.action == expected)
    return {"checks": checks, "cases": cases, "all_passed": all(checks.values())}
