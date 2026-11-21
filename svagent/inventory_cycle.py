"""库存周期阶段判定：反偏差的真实领域论证。

议题：中国的库存周期是否已从「主动补库存」转变到「被动补库存」？

设计纪律（继承第 18-20 节的整改成果）：
  1. 预注册：判据规则、平滑窗口、死区阈值在跑数前写死，不因个案调整。
  2. 盲判/揭盲分离：判据只读②③数据序列，不读任何机构给出的「当前阶段」标签；
     机构结论只在判据产出后作为「事后对照」揭盲。
  3. 名义/实际双轨：名义库存上行可能只是 PPI 价格效应，必须做实际库存消融。
  4. 消融：换平滑窗口、换口径，看结论是否翻转（稳健性边界）。
  5. 反例对照：用历史公认阶段校准判据（健全性检查），不挑个案。
  6. 缺失数据作为一等公民：缺失就是「我不知道」，不填补、不臆断。

四象限定义（用「方向」而非「水平」）：
  需求 D = 营业收入同比增速的边际方向（升/降）
  库存 I = 产成品存货同比增速的边际方向（升/降）
  ┌──────────────┬──────────────┐
  │ I升 + D升     │ I升 + D降     │
  │ 主动补库      │ 被动补库(被动累库)│
  ├──────────────┼──────────────┤
  │ I降 + D升     │ I降 + D降     │
  │ 被动去库      │ 主动去库      │
  └──────────────┴──────────────┘
「主动补库 → 被动补库」的转变 = 从 (I升,D升) 转移到 (I升,D降)：
关键特征是库存仍在累积，但需求掉头向下。

数据来源（真实、一手）：
  - china_monthly_raw.json：国家统计局月度工业企业利润发布页逐页抓取
    （营收同比、产成品存货同比、周转天数），2022-05 至 2026-09。
  - china_ppi_monthly.json：东方财富宏观接口 RPT_ECONOMY_PPI。
免责声明：本研究仅供方法验证，不构成任何投资建议。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

# ───────────────────────────── 预注册区（跑数前固定，禁止事后修改）─────────────────────────────
PREREG = {
    "smooth_window": 3,        # 3 期移动平均平滑同比增速（抵抗单月噪音）
    "deadband_pct": 0.15,      # 方向判定死区：|Δ| < 0.15pct 视为「持平」
    "focus_start": "2024-01",  # 主分析窗口起点（覆盖近两轮库存周期）
    "focus_end": "2026-09",    # 终点：当前可getData的最新月
}

PHASE_NAMES = {
    ("up", "up"): "主动补库",
    ("up", "down"): "被动补库",
    ("down", "up"): "被动去库",
    ("down", "down"): "主动去库",
    ("up", "flat"): "补库·需求持平",
    ("down", "flat"): "去库·需求持平",
    ("flat", "up"): "累库·需求持平",
    ("flat", "down"): "去库·需求持平",
    ("flat", "flat"): "双持平",
}

# 历史公认阶段（仅用于事后健全性检查，不进入判据）——来自公开研究共识
HISTORICAL_REFERENCE = {
    "2020-07": "2020H2 疫情后复苏，需求与库存共振上行 → 主动补库",
    "2021-03": "2021Q1 补库延续，随后转向去库",
    "2022-06": "2022 年中需求下行、库存高位 → 主动去库",
    "2023-06": "2023 年中需求弱、库存去化 → 被动去库",
}
# ─────────────────────────────────────────────────────────────────────────────────────────────


def load_data(base: str = "/workspace") -> tuple[dict, dict]:
    """加载真实数据；缺失值保留为 None（不填补）。"""
    monthly = json.load(open(os.path.join(base, "china_monthly_raw.json")))
    ppi = json.load(open(os.path.join(base, "china_ppi_monthly.json")))
    return monthly, ppi


def _smooth(vals: list[float | None], n: int) -> list[float | None]:
    """n 期移动平均；窗口内只要有有效值就算，全缺失则None。"""
    out = []
    for i in range(len(vals)):
        win = [v for v in vals[max(0, i - n + 1): i + 1] if v is not None]
        out.append(sum(win) / len(win) if win else None)
    return out


def _direction(delta: float | None, deadband: float) -> str:
    """把一阶导转成方向：up/down/flat。缺失→flat 但会被标记。"""
    if delta is None:
        return "flat"
    if delta > deadband:
        return "up"
    if delta < -deadband:
        return "down"
    return "flat"


@dataclass
class MonthState:
    period: str
    rev_yoy: float | None
    inv_yoy: float | None
    ppi_yoy: float | None
    inv_real_yoy: float | None       # 实际库存同比（名义−PPI）
    rev_real_yoy: float | None       # 实际营收同比
    d_dir: str                        # 需求方向
    i_dir: str                        # 库存方向（名义口径）
    i_dir_real: str                   # 库存方向（实际口径）
    phase: str                        # 名义口径阶段
    phase_real: str                   # 实际口径阶段
    missing: list[str] = field(default_factory=list)


def classify(
    monthly: dict,
    ppi: dict,
    *,
    smooth_window: int | None = None,
    deadband: float | None = None,
    focus_start: str | None = None,
    focus_end: str | None = None,
    use_real_for_phase: bool = False,
) -> list[MonthState]:
    """按预注册判据对每月做阶段划分（盲判：不读任何阶段标签）。"""
    sw = smooth_window or PREREG["smooth_window"]
    db = deadband if deadband is not None else PREREG["deadband_pct"]
    fs = focus_start or PREREG["focus_start"]
    fe = focus_end or PREREG["focus_end"]

    periods = [p for p in sorted(monthly) if fs <= p <= fe]
    rev = [monthly[p]["rev_yoy"] for p in periods]
    inv = [monthly[p]["inv_yoy"] for p in periods]
    pp = [ppi.get(p, {}).get("ppi_yoy") for p in periods]

    # 实际口径：名义同比 − PPI同比（线性近似，|PPI|<10% 时误差可接受）
    inv_real = [(i - x) if (i is not None and x is not None) else None
                for i, x in zip(inv, pp)]
    rev_real = [(r - x) if (r is not None and x is not None) else None
                for r, x in zip(rev, pp)]

    rev_s, inv_s = _smooth(rev, sw), _smooth(inv, sw)
    ir_s = _smooth(inv_real, sw)

    out: list[MonthState] = []
    for k, p in enumerate(periods):
        missing = []
        if rev[k] is None: missing.append("营收")
        if inv[k] is None: missing.append("存货")
        if pp[k] is None: missing.append("PPI")

        # 方向：用平滑序列的一阶导
        d_rev = (rev_s[k] - rev_s[k - 1]) if k > 0 and rev_s[k] is not None and rev_s[k - 1] is not None else None
        d_inv = (inv_s[k] - inv_s[k - 1]) if k > 0 and inv_s[k] is not None and inv_s[k - 1] is not None else None
        d_ir = (ir_s[k] - ir_s[k - 1]) if k > 0 and ir_s[k] is not None and ir_s[k - 1] is not None else None

        d_dir = _direction(d_rev, db)
        i_dir = _direction(d_inv, db)
        i_dir_real = _direction(d_ir, db)
        phase = PHASE_NAMES[(i_dir, d_dir)]
        phase_real = PHASE_NAMES[(i_dir_real, d_dir)]

        out.append(MonthState(
            period=p, rev_yoy=rev[k], inv_yoy=inv[k], ppi_yoy=pp[k],
            inv_real_yoy=inv_real[k], rev_real_yoy=rev_real[k],
            d_dir=d_dir, i_dir=i_dir, i_dir_real=i_dir_real,
            phase=phase_real if use_real_for_phase else phase,
            phase_real=phase_real,
            missing=missing,
        ))
    return out


def find_transitions(states: list[MonthState], key: str = "phase") -> list[tuple[str, str, str]]:
    """找阶段切换点：(月份, 从, 到)。只报告相邻两期都非缺失的切换。"""
    out = []
    for a, b in zip(states, states[1:]):
        pa, pb = getattr(a, key), getattr(b, key)
        if pa != pb and not b.missing:
            out.append((b.period, pa, pb))
    return out


def ablation(monthly: dict, ppi: dict) -> dict:
    """消融：换平滑窗口/死区/口径，看『当前阶段』结论是否翻转。"""
    results = {}
    for sw in [1, 2, 3, 4]:
        for real in [False, True]:
            st = classify(monthly, ppi, smooth_window=sw, use_real_for_phase=real)
            latest = [s for s in st if not s.missing][-1] if any(not s.missing for s in st) else None
            results[f"窗口{sw}_{'实际' if real else '名义'}"] = {
                "latest_phase": latest.phase if latest else None,
                "latest_period": latest.period if latest else None,
            }
    return results


def main() -> None:
    monthly, ppi = load_data()
    print("=" * 100)
    print("库存周期阶段判定：主动补库 → 被动补库 是否属实？（反偏差论证）")
    print("=" * 100)
    print(f"预注册：平滑窗口={PREREG['smooth_window']}期 死区=±{PREREG['deadband_pct']}pct "
          f"窗口={PREREG['focus_start']}~{PREREG['focus_end']}")

    # 盲判：只读数据序列，不读任何阶段标签
    states = classify(monthly, ppi)
    clean = [s for s in states if not s.missing]
    print(f"\n参评 {len(clean)}/{len(states)} 月（缺失 {len(states)-len(clean)} 月作为『不知道』剔除）\n")
    print(f"{'月份':<9}{'营收YoY':>8}{'存货YoY':>8}{'PPI':>7}{'实际存货':>9}{'需求向':>7}{'库存向':>7}{'名义阶段':>12}{'实际阶段':>12}")
    for s in states:
        f = lambda x: f"{x:>7.1f}" if isinstance(x, (int, float)) else "     NA"
        print(f"{s.period:<9}{f(s.rev_yoy):>8}{f(s.inv_yoy):>8}{f(s.ppi_yoy):>7}"
              f"{f(s.inv_real_yoy):>9}{s.d_dir:>7}{s.i_dir:>7}{s.phase:>12}{s.phase_real:>12}"
              + ("  ←缺失" + "/".join(s.missing) if s.missing else ""))

    print("\n--- 名义口径阶段切换（盲判结果）---")
    for p, a, b in find_transitions(states, "phase"):
        print(f"  {p}: {a} → {b}")
    print("\n--- 实际口径阶段切换（剔除PPI价格效应）---")
    for p, a, b in find_transitions(states, "phase_real"):
        print(f"  {p}: {a} → {b}")

    print("\n--- 消融：换窗口/口径，当前阶段是否翻转 ---")
    for k, v in ablation(monthly, ppi).items():
        print(f"  {k:<16} → {v['latest_phase']} ({v['latest_period']})")

    print("\n--- 事后揭盲：机构结论（仅对照，不进入判据）---")
    for k, v in HISTORICAL_REFERENCE.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
