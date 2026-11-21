"""调用点完整性门禁 — 把 §58 的认知断言编译成会拦会判的代码（认知→能力）。

来源与动机（commentary §58 / architecture_decision_A.json）：
  用户问"本仓代码适应调整了吗"，两层核查发现 KB-AUDIT03 的判定粒度缺口：
  同样"没接 run_loop"，FastGithub 的死代码（无任何调用点 + 虚假安全感）与本仓
  六道门禁（离线审计脚本有真实调用者 + 如实声明工具库定位）不该同判为"没接线"。
  §58 把这条写成认知增量，用户随后叮嘱"把认知变成能力，把断言落到代码"，
  本模块据此把该断言编译成通用门禁——这是认知域协同（§53 三段式第二段）的落点。

扬长避短（对比现有判据）：
  - KB-AUDIT03 原文只判"有无调用点"，粒度粗：有调用点就放行，会把"离线冒充在线"
    和"幽灵接线"也放过。本模块细化到"调用点在哪 + 定位是否如实声明 + 调用者是否真实"。
  - 与 lineage_guard/backtest_integrity 同族：语义枚举 + 写死规则 + 纯函数，
    传字面串 → flag（避开 §56 brittle 根因 KB-AUDIT01），不事后加权（防 Goodhart）。
  - 会拦（死代码/幽灵接线/无断言 → block）、会判（离线冒充在线/诚实未接线 → downgrade）、
    会放行（如实工具库/真在线咬合 → ok）、会待核（定位未声明 → flag）。
  - 锚定 KB-AUDIT03 并在 support 加固指针（认知域协同，KB-META01 复述 vs 长牙）。

诚实边界：只判"调用点与定位声明的自洽性"，不判被审对象本身对错、不替代实质证据；
调用点位置与定位诚实性须调用方如实声明，声明本身不可自证；本模块由 §58 本仓
自审的认知增量编译，按 KB-STRUCT02 不构成对本仓框架的独立验证。活体样例用于
机制回归，非复现外部实验；不改变既有测试，不接入 run_loop（遵循 §58 用户选 A）。
"""
from __future__ import annotations

from dataclasses import dataclass

# 语义枚举——写死；判定绝不读字符串内容（KB-AUDIT01 brittle 根因）
_CALL_SITES = frozenset({"none", "offline_audit", "online_main_loop"})
_BOOL_FIELDS = ("declared_as_automatic", "positioning_honest", "caller_real", "assertion_exists")


@dataclass(frozen=True)
class CallSiteVerdict:
    claim: str
    call_site: str
    declared_as_automatic: bool
    positioning_honest: bool
    caller_real: bool
    assertion_exists: bool
    action: str        # ok | downgrade | flag | block
    code: str
    message: str


def audit_call_site(
    claim: str,
    *,
    call_site: str,
    declared_as_automatic: bool,
    positioning_honest: bool,
    caller_real: bool,
    assertion_exists: bool,
) -> CallSiteVerdict:
    """判定一条『有断言/测试/自检』的验证声称，是真能力还是虚假安全感。

    输入须为语义枚举 + 布尔：
      call_site ∈ {none, offline_audit, online_main_loop} —— 调用点位置
      declared_as_automatic —— 是否声称"已自动/在线执行"
      positioning_honest —— 是否如实声明定位（如"按需工具库"）
      caller_real —— 调用者是否真实存在且可执行
      assertion_exists —— 是否真的存在断言/判据代码

    规则按优先级写死（不事后加权，与 call_site_prereg.json 一致）：
      R0 字面串/畸形输入 → flag（拒绝对字符串内容判定）
      R1 无断言却声称验证 → block（最底层虚假）
      R2 无调用点 + 声称自动 → block（死代码 + 虚假安全感，KB-AUDIT03 原义）
      R3 声称在线主循环但无真实调用者 → block（幽灵接线）
      R4 离线调用点 + 声称自动 → downgrade（离线冒充在线）
      R5 无调用点 + 未声称自动 → downgrade（诚实承认未接线，不拦截）
      R6 离线 + 如实声明 + 未声称自动 + 调用者真实 → ok（按需工具库，preserve）
      R7 在线主循环 + 调用者真实 → ok（真·自动咬合）
      R8 其余 → flag（定位未如实声明，待核）
    """
    # R0：语义输入校验优先——任何字面串/非 bool 都不进入内容判定
    if (call_site not in _CALL_SITES
            or not all(isinstance(v, bool) for v in (
                declared_as_automatic, positioning_honest, caller_real, assertion_exists))):
        return CallSiteVerdict(
            claim, str(call_site),
            bool(declared_as_automatic) if isinstance(declared_as_automatic, bool) else False,
            bool(positioning_honest) if isinstance(positioning_honest, bool) else False,
            bool(caller_real) if isinstance(caller_real, bool) else False,
            bool(assertion_exists) if isinstance(assertion_exists, bool) else False,
            "flag", "CALL_SITE.NON_SEMANTIC_INPUT",
            "调用点位置须用语义枚举声明、状态须为布尔；拒绝对字面串判定"
            "（避开 brittle 根因，KB-AUDIT01）",
        )

    base = (claim, call_site, declared_as_automatic, positioning_honest, caller_real, assertion_exists)

    # R1：无断言却声称验证——最底层的空头声称
    if not assertion_exists:
        return CallSiteVerdict(
            *base, "block", "CALL_SITE.FABRICATED_ASSERTION",
            "根本没有断言/判据代码却声称已验证——空头声称，计入未提供验证（KB-AUDIT03）",
        )

    # R2：死代码 + 虚假安全感——KB-AUDIT03 原义，最重
    if call_site == "none" and declared_as_automatic:
        return CallSiteVerdict(
            *base, "block", "CALL_SITE.DEAD_CODE_AUTO_CLAIM",
            "声称自动执行却无任何调用点=死代码+虚假安全感（KB-AUDIT03 原义）",
        )

    # R3：幽灵接线——声称接入主循环但无真实调用者
    if call_site == "online_main_loop" and not caller_real:
        return CallSiteVerdict(
            *base, "block", "CALL_SITE.PHANTOM_WIRING",
            "声称接入在线主循环但调用者不真实（空注释/死引用）——幽灵接线，不可计入已执行",
        )

    # R4：离线冒充在线——口径失真
    if call_site == "offline_audit" and declared_as_automatic:
        return CallSiteVerdict(
            *base, "downgrade", "CALL_SITE.OFFLINE_AS_ONLINE",
            "调用点只在离线审计脚本却声称已自动/在线执行——口径失真，判定打折",
        )

    # R5：诚实承认未接线——降级不拦截（preserve 精神）
    if call_site == "none" and not declared_as_automatic:
        return CallSiteVerdict(
            *base, "downgrade", "CALL_SITE.UNWIRED_HONEST",
            "无调用点但未声称自动——如实承认未接线，降级为未提供自动验证（非死代码，KB-R08）",
        )

    # R6：如实声明的按需工具库——§58 本仓自身定位，放行
    if (call_site == "offline_audit" and positioning_honest
            and not declared_as_automatic and caller_real):
        return CallSiteVerdict(
            *base, "ok", "CALL_SITE.PRESERVE_TOOL_LIBRARY",
            "离线审计脚本有真实调用者、如实声明为按需工具库、未声称自动——诚实，preserve（§58）",
        )

    # R7：真·自动咬合
    if call_site == "online_main_loop" and caller_real:
        return CallSiteVerdict(
            *base, "ok", "CALL_SITE.ONLINE_WIRED",
            "在线主循环 + 调用者真实——真·自动咬合（仍不替代实质证据）",
        )

    # R8：定位未如实声明——待核
    return CallSiteVerdict(
        *base, "flag", "CALL_SITE.UNDECLARED_POSITIONING",
        "定位未如实声明，调用链不可判定——标注待核，不得计入已验证",
    )


def live_regression() -> dict:
    """活体回归：8 场景对应预注册 8 个样例，验证规则没在放水。"""
    cases = [
        ("本仓六道门禁(§58)",
         dict(call_site="offline_audit", declared_as_automatic=False, positioning_honest=True,
              caller_real=True, assertion_exists=True), "ok", "CALL_SITE.PRESERVE_TOOL_LIBRARY"),
        ("FastGithub死代码(KB-AUDIT03原义)",
         dict(call_site="none", declared_as_automatic=True, positioning_honest=False,
              caller_real=False, assertion_exists=True), "block", "CALL_SITE.DEAD_CODE_AUTO_CLAIM"),
        ("空头声称无断言",
         dict(call_site="offline_audit", declared_as_automatic=False, positioning_honest=True,
              caller_real=True, assertion_exists=False), "block", "CALL_SITE.FABRICATED_ASSERTION"),
        ("幽灵接线",
         dict(call_site="online_main_loop", declared_as_automatic=True, positioning_honest=True,
              caller_real=False, assertion_exists=True), "block", "CALL_SITE.PHANTOM_WIRING"),
        ("离线冒充在线",
         dict(call_site="offline_audit", declared_as_automatic=True, positioning_honest=False,
              caller_real=True, assertion_exists=True), "downgrade", "CALL_SITE.OFFLINE_AS_ONLINE"),
        ("诚实未接线",
         dict(call_site="none", declared_as_automatic=False, positioning_honest=True,
              caller_real=False, assertion_exists=True), "downgrade", "CALL_SITE.UNWIRED_HONEST"),
        ("真自动咬合",
         dict(call_site="online_main_loop", declared_as_automatic=True, positioning_honest=True,
              caller_real=True, assertion_exists=True), "ok", "CALL_SITE.ONLINE_WIRED"),
        ("brittle字面串对照",
         dict(call_site="高度同构", declared_as_automatic=True, positioning_honest=True,
              caller_real=True, assertion_exists=True), "flag", "CALL_SITE.NON_SEMANTIC_INPUT"),
    ]
    results = {}
    checks = {}
    for name, kw, exp_action, exp_code in cases:
        v = audit_call_site(name, **kw)
        results[name] = {"action": v.action, "code": v.code}
        checks[name] = (v.action == exp_action and v.code == exp_code)
    return {"cases": results, "checks": checks, "all_passed": all(checks.values())}
