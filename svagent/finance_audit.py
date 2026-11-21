"""财报叙事真实性判定：把 SVL 坍塌架构迁移到真实财报数据。

核心迁移（与回忆录场景对齐）：

  回忆录                          财报
  ─────────────────────────────────────────────────────────
  AI 生成的第一人称叙述    ↔  财报里的"叙事"（增长/盈利/健康隐含声明）
  老人原话（ground truth）  ↔  会计恒等式 + 跨表勾稽（数学约束，非管理层叙事）
  anchor 子串核对          ↔  金额级别的恒等式/比率符号判据
  独白/越界 flag           ↔  增速背离/现金含量不足 flag（交人，不否决）
  核对原话交接卡           ↔  异常凭证卡（给审计/分析师局部裁决）

最重要的一条诚实原则：
  财报的"真值"不是某个外部文档，而是会计恒等式这组**数学约束**。
  它们不依赖管理层诚实——资产必须等于负债加权益，这是复式记账的硬约束。
  但恒等式通过 ≠ 叙事真实：关联交易、收入确认时点、表外结构都可合规地
  通过所有恒等式。因此本模块只判定"不违反符号判据"，残余一律交人。

数据来源：finance_fetch.py 拉取的东方财富公开接口真实数据（2021-2025 年报）。
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .core import Diagnostic, Locus as _Locus
from .finance_fetch import FetchResult, load_all


def Locus(where: str, field: str) -> _Locus:
    """轻量适配：把财报的 年份·科目 打进 Locus.ref，兼容 core 的统一诊断格式。"""
    return _Locus(ref=f"{where}·{field}")

# 金额单位：元。比率阈值来自通行财务分析常识，非精确真理，标注为 heuristic。
CASH_RATIO_MIN = 0.55     # 经营净现金流/净利润，长期低于此值提示盈利未收现（heuristic）
RECEIPT_RATIO_MIN = 0.85  # 销售收现/营业收入（heuristic）
BALANCE_EQ_TOL = 0.01     # 资产=负债+权益 相对容差 1%（合并报表四舍五入/少数股东）
GAP_FLAG = 0.30           # 增速背离阈值：利润增速比营收增速低 30pct 以上 → flag
YEARS_MIN = 3


@dataclass(frozen=True)
class NarrativeClaim:
    """一条可被符号判据核验的财报'叙事声明'，全部由真实数据自动提取，非人工编造。"""
    company: str
    industry: str
    year: str
    text: str            # 数据隐含的叙事，如 "2024年归母净利润同比-15.1%"
    code: str            # 判据编号
    value: float | None = None


def _safe_div(a, b):
    if a is None or b in (None, 0):
        return None
    try:
        return float(a) / float(b)
    except (TypeError, ValueError):
        return None


def _yoy(series: dict[str, float], y: str) -> float | None:
    """按年份字符串序列算同比，需连续两年。"""
    yr = int(y)
    cur, prev = series.get(str(yr)), series.get(str(yr - 1))
    if cur is None or prev is None or prev == 0:
        return None
    return (cur - prev) / abs(prev) * 100


# ---------------------------------------------------------------- 坍塌映射 φ
# 每个坍塌函数把"叙事是否成立"这个语义问题，坍塌成不需要理解业务的符号判断。

def collapse_balance_identity(r: FetchResult) -> list[Diagnostic]:
    """φ1 会计恒等式：资产 = 负债 + 所有者权益（复式记账硬约束，数学判决）。"""
    out = []
    for y in r.years:
        b = r.balance.get(y, {})
        a, l, e = b.get("TOTAL_ASSETS"), b.get("TOTAL_LIABILITIES"), b.get("TOTAL_EQUITY")
        if a is None or l is None or e is None:
            out.append(Diagnostic("FIN.BALANCE.MISSING", "flag", Locus(y, "balance"),
                                  f"{y} 资产/负债/权益字段缺失，恒等式不可核验（未填补）"))
            continue
        rel = abs(a - (l + e)) / abs(a)
        if rel > BALANCE_EQ_TOL:
            out.append(Diagnostic("FIN.BALANCE.BREACH", "block", Locus(y, "balance"),
                                  f"{y} 资产{a:.2e} ≠ 负债{l:.2e}+权益{e:.2e}，相对偏差{rel:.2%} > 容差"))
        else:
            out.append(Diagnostic("FIN.BALANCE.OK", "pass", Locus(y, "balance"),
                                  f"{y} 恒等式成立（偏差{rel:.4%}）"))
    return out


def collapse_cash_quality(r: FetchResult) -> list[Diagnostic]:
    """φ2 盈利含金量：经营净现金流/净利润。低于阈值=盈利未收现（软信号，交人）。"""
    out = []
    for y in r.years:
        c = r.cashflow.get(y, {})
        i = r.income.get(y, {})
        ocf = c.get("NETCASH_OPERATE")
        np_ = i.get("NETPROFIT")  # 合并口径净利润（含少数股东），与现金流口径匹配
        if ocf is None or np_ is None:
            out.append(Diagnostic("FIN.CASH.MISSING", "flag", Locus(y, "cashflow"),
                                  f"{y} 现金流或净利润缺失，含金量不可核验"))
            continue
        if np_ <= 0:
            # 分母为负时比率失去解释力（2022 京东方：合并净利-17亿但归母+75亿，
            # 少数股东巨亏）。此时报事实，不报无意义比率——真实数据揭穿的判据缺陷。
            out.append(Diagnostic("FIN.CASH.NEGDENOM", "flag", Locus(y, "cashflow"),
                                  f"{y} 合并净利润={np_:.2e}≤0，现金含量比率不适用（少数股东损益结构，交人）"))
            continue
        ratio = _safe_div(ocf, np_)
        if ratio < CASH_RATIO_MIN:
            sev = "flag"  # 软信号：交人，不直接否决（银行等业态现金流结构不同）
            out.append(Diagnostic("FIN.CASH.LOW", sev, Locus(y, "cashflow"),
                                  f"{y} 经营净现金流/净利润={ratio:.2f} < {CASH_RATIO_MIN}，盈利含金量存疑（交人）"))
        else:
            out.append(Diagnostic("FIN.CASH.OK", "pass", Locus(y, "cashflow"),
                                  f"{y} 现金含量{ratio:.2f} 达标"))
    return out


def collapse_receipt_ratio(r: FetchResult) -> list[Diagnostic]:
    """φ3 收入含金量：销售收现/营业收入。低=收入未转化为现金（软信号）。"""
    out = []
    for y in r.years:
        c, i = r.cashflow.get(y, {}), r.income.get(y, {})
        sales, rev = c.get("SALES_SERVICES"), i.get("TOTAL_OPERATE_INCOME")
        ratio = _safe_div(sales, rev)
        if ratio is None:
            out.append(Diagnostic("FIN.RECEIPT.MISSING", "flag", Locus(y, "cashflow"),
                                  f"{y} 销售收现字段缺失（银行/简版表常见），不可核验"))
            continue
        if ratio < RECEIPT_RATIO_MIN:
            out.append(Diagnostic("FIN.RECEIPT.LOW", "flag", Locus(y, "cashflow"),
                                  f"{y} 销售收现/营收={ratio:.2f} < {RECEIPT_RATIO_MIN}，收入收现不足（交人）"))
        else:
            out.append(Diagnostic("FIN.RECEIPT.OK", "pass", Locus(y, "cashflow"),
                                  f"{y} 收现比{ratio:.2f} 达标"))
    return out


def collapse_growth_divergence(r: FetchResult) -> list[Diagnostic]:
    """φ4 增长叙事背离：营收增长但归母净利润大幅下滑（或反之）=叙事需解释（软信号）。"""
    out = []
    rev = {y: (r.income.get(y, {}).get("TOTAL_OPERATE_INCOME")) for y in r.years}
    np_ = {y: (r.income.get(y, {}).get("PARENT_NETPROFIT")) for y in r.years}
    for y in r.years:
        rg, pg = _yoy(rev, y), _yoy(np_, y)
        if rg is None or pg is None:
            continue
        gap = pg - rg  # 利润增速 - 营收增速
        if abs(gap) >= GAP_FLAG * 100:
            out.append(Diagnostic("FIN.GROWTH.DIVERGE", "flag", Locus(y, "income"),
                                  f"{y} 营收同比{rg:+.1f}% 但归母净利同比{pg:+.1f}%，背离{gap:+.1f}pct（叙事需解释，交人）"))
        else:
            out.append(Diagnostic("FIN.GROWTH.OK", "pass", Locus(y, "income"),
                                  f"{y} 营收{rg:+.1f}%/净利{pg:+.1f}% 基本同步"))
    return out


def collapse_audit_opinion(r: FetchResult) -> list[Diagnostic]:
    """φ5 审计意见：非标准无保留=硬信号；未取到=如实标注，不臆断。"""
    out = []
    for y in r.years:
        op = r.opinion.get(y)
        if op is None:
            out.append(Diagnostic("FIN.OPINION.MISSING", "flag", Locus(y, "income"),
                                  f"{y} 审计意见未取到（简版表无此字段），如实标注不臆断"))
        elif "无保留" in str(op):
            # 先判"无保留"：涵盖"标准无保留"与"带强调事项段的无保留意见"。
            # 注意顺序——若先判"保留"，"无保留意见"里的"保留"二字会误命中，
            # 这是真实数据揭穿的判据 bug（乐视2016 曾被误判为 block）。
            if "强调" in str(op):
                out.append(Diagnostic("FIN.OPINION.EMPHASIS", "flag", Locus(y, "income"),
                                      f"{y} 审计意见：{op}（无保留但带强调，交人关注）"))
            else:
                out.append(Diagnostic("FIN.OPINION.OK", "pass", Locus(y, "income"),
                                      f"{y} 审计意见：{op}"))
        elif "无法表示" in str(op) or "否定" in str(op) or "保留" in str(op):
            out.append(Diagnostic("FIN.OPINION.NONSTANDARD", "block", Locus(y, "income"),
                                  f"{y} 审计意见非标准：{op}（硬信号）"))
    return out


VERIFIERS = [
    ("会计恒等式", collapse_balance_identity),
    ("盈利含金量", collapse_cash_quality),
    ("收入含金量", collapse_receipt_ratio),
    ("增长叙事背离", collapse_growth_divergence),
    ("审计意见", collapse_audit_opinion),
]


def audit(r: FetchResult) -> list[Diagnostic]:
    out: list[Diagnostic] = []
    for _, fn in VERIFIERS:
        out.extend(fn(r))
    return out


@dataclass
class AuditReport:
    company: str
    industry: str
    years: list[str]
    diagnostics: list[Diagnostic] = field(default_factory=list)
    opinion: dict[str, str | None] = field(default_factory=dict)

    @property
    def blocks(self):
        return [d for d in self.diagnostics if d.severity == "block"]

    @property
    def flags(self):
        return [d for d in self.diagnostics if d.severity == "flag"]

    @property
    def passes(self):
        return [d for d in self.diagnostics if d.severity == "pass"]

    def verdict(self) -> str:
        if self.blocks:
            return "硬违约：叙事被数学/审计约束证伪"
        if self.flags:
            return f"未违反硬判据；{len(self.flags)} 项存疑需人工裁决"
        return "全部符号判据通过（不等于叙事真实，见残余风险）"

    def handoff_cards(self) -> list[dict]:
        """局部裁决卡：把每个 flag 切成 O(1) 可裁决单元（复用 handoff 机制思想）。"""
        return [
            {"公司": self.company, "年份/位置": d.locus.ref,
             "异常": d.code, "凭证": d.message,
             "人工问题": "这项异常是否有业务合理解释？（一句话即可裁决）"}
            for d in self.flags
        ]


def audit_all(path: str = "/workspace/financials.json") -> list[AuditReport]:
    return [AuditReport(r.name, r.industry, r.years, audit(r), r.opinion)
            for r in load_all(path)]


# ---------------------------------------------------------------- 残余风险（不可坍塌）
RESIDUAL_RISKS = [
    "关联交易与资金占用：可合规通过所有恒等式，恒等式判据对此完全失明。",
    "收入确认时点：提前/延后确认不破坏资产=负债+权益，符号判据无法判定。",
    "表外结构与或有负债：不进入三表，任何表内坍塌映射都覆盖不到。",
    "减值计提充分性：是估计不是事实，审计意见为标准无保留也不代表计提合理。",
    "数据本身是公开接口加工指标，非年报原文；字段口径差异（银行简版表）已标注但不消除。",
]


# ---------------------------------------------------------------- 驱动
def main() -> None:
    reports = audit_all()
    print("=" * 96)
    print("财报叙事真实性判定（真实数据：东方财富公开接口，2021-2025 年报）")
    print("=" * 96)
    for rep in reports:
        print(f"\n■ {rep.company} [{rep.industry}]  年报期: {', '.join(rep.years)}")
        print(f"  结论: {rep.verdict()}")
        print(f"  block={len(rep.blocks)}  flag={len(rep.flags)}  pass={len(rep.passes)}")
        # 只展示 block 与 flag（pass 太多），每个都是局部凭证
        for d in rep.blocks + rep.flags:
            print(f"    [{d.severity:5}] {d.code:26} {d.message}")
        cards = rep.handoff_cards()
        if cards:
            print(f"  → {len(cards)} 张人工裁决卡，例: {cards[0]['凭证'][:52]}")

    # ---- 检出对照：造假案在"审计尚未发现"年份，符号判据是否提前报警 ----
    print("\n" + "=" * 96)
    print("检出对照：造假暴露前，符号判据能否提前报警？（真实案例，非编造）")
    print("=" * 96)
    km = next(r for r in reports if r.company == "康美药业")
    early = [y for y in ("2016", "2017") if "标准无保留" in str(km.opinion.get(y, ""))]
    km_early_flags = [d for d in km.diagnostics if d.locus.ref.split("·")[0] in early
                      and d.severity in ("flag", "block")
                      and d.code in ("FIN.CASH.LOW", "FIN.RECEIPT.LOW")]
    print(f"  康美药业 2016-2017（审计仍给标准无保留、造假未被发现）:")
    print(f"    审计意见信号: 无（审计当年没抓到）")
    print(f"    符号判据信号: {len(km_early_flags)} 项现金/收现异常")
    for d in km_early_flags:
        print(f"      - {d.locus.ref}: {d.message}")
    if km_early_flags:
        print("    → 判据在审计出具'标准无保留'的年份就发出凭证——真正的提前检出。")

    clean = [r for r in reports if "对照" not in r.industry]
    clean_blocks = sum(len(r.blocks) for r in clean)
    print(f"\n  正常对照（兴业/海康/京东方）: block={clean_blocks}（预期 0，无误杀）")

    print("\n" + "=" * 96)
    print("坍塌边界：这套架构在财报领域坍塌掉了什么、坍塌不掉什么")
    print("=" * 96)
    n_block = sum(len(r.blocks) for r in reports)
    n_flag = sum(len(r.flags) for r in reports)
    n_pass = sum(len(r.passes) for r in reports)
    print(f"  五家真实公司共产生: block={n_block}, flag={n_flag}, pass={n_pass}")
    print("  坍塌成功（符号可判定）: 会计恒等式、现金含量、收现比、增速背离、审计意见分级")
    print("  坍塌失败（必须交人）:")
    for risk in RESIDUAL_RISKS:
        print(f"    - {risk}")
    print("\n  诚实声明:")
    print("   1. 造假对照是真实案例，但 n=2，不能算检出率/召回率——只证明'能提前抓到信号'。")
    print("   2. 判据抓到的是'现金含量/收现异常'这类表征，不是'造假'本身；")
    print("      康美真正造假是虚增货币资金与收入，符号判据靠现金含量间接命中。")
    print("   3. 审计意见是滞后标签（事后才变保留），不算提前证据；提前证据只有现金类判据。")
    print("   4. 阈值(0.55/0.85)是通行 heuristic，非监管标准；不同行业需重标定。")


if __name__ == "__main__":
    main()
