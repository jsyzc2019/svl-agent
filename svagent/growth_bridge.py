"""自学习成长桥 — 接通「真实精研线」与「模拟自进化线」（审计 F3 结构杠杆 / F5 诚实杠杆）。

审计发现两条从未接合的成长线：
  线A 模拟自进化：pdca.PDCALoop 有 inject_opportunities() 入口，但只吃硬编码日志；
  线B 真实精研：125 条 KB + 28 道门禁，但 0 个被线A 消费（KB 全仓仅 retro_audit 一处 load，
    且用关键词计数 len(RETRO>=6) 自证反哺闭环 = F5 代理指标自证）。

本模块是转换层，做两件诚实的事：
  1. 把 KB 的 addressable+fix 机制、取证法官的缺口(code) 转成真实 Opportunity，
     经 PDCALoop.inject_opportunities() 喂进 PDCA 研究/验证环；
  2. 落【消费痕迹】：每次注入都记录 item_id / gate_code / 时间，指向具体来源——
     用真实消费链替代 F5 的关键词计数。痕迹可落盘、可回放、可复核。

诚实边界（延续 KB 纪律）：
  - addressable=False 的认知机制不编译成符号判据，保持交人（桥只搬运 addressable=True）；
  - 注入 ≠ 采纳：Opportunity 进 PDCA 后由研究/验证/评估环决定是否采纳，桥不承诺改进生效；
  - 只判「机制可被下游消费」，不承诺消费后有效（KB-R07 自洽≠有效）。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .knowledge_base import KnowledgeBase
from .pdca import Opportunity


@dataclass(frozen=True)
class ConsumptionRecord:
    """一条消费痕迹：某个具体来源在何时被注入 PDCA。"""
    source_kind: str        # knowledge_base | forensic_gap
    source_id: str          # KB item_id 或 gate.code
    mechanism: str          # 机制/缺口说明
    injected_at: str
    addressable: bool
    accepted_by_pdca: bool | None = None   # 注入时未知，运行后可回填

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class BridgeReport:
    """一次桥接的结果：机会 + 消费痕迹 + 诚实缺口。"""
    opportunities: list[Opportunity] = field(default_factory=list)
    consumption: list[ConsumptionRecord] = field(default_factory=list)
    cognitive_deferred: list[str] = field(default_factory=list)  # addressable=False 交人
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "opportunity_count": len(self.opportunities),
            "consumption": [c.to_dict() for c in self.consumption],
            "cognitive_deferred_count": len(self.cognitive_deferred),
            "cognitive_deferred": self.cognitive_deferred[:10],
            "note": self.note,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def kb_to_opportunities(kb: KnowledgeBase) -> BridgeReport:
    """把 KB 的 addressable+fix 机制转成机会并落消费痕迹（真实消费链，非关键词计数）。"""
    report = BridgeReport()
    for it in kb.items.values():
        if not it.addressable:
            # 认知类机制不假装能编译成符号判据——如实列为交人
            report.cognitive_deferred.append(it.item_id)
            continue
        if it.improvement_class != "fix":
            continue
        opp = Opportunity(
            kind="mechanism_upgrade",
            signal=f"{it.item_id}:{it.mechanism[:48]}",
            where="agent",
            detail=it.action,
            source=f"knowledge_base:{it.provenance}",
            addressable=True,
        )
        report.opportunities.append(opp)
        report.consumption.append(ConsumptionRecord(
            source_kind="knowledge_base", source_id=it.item_id,
            mechanism=it.mechanism, injected_at=_now(), addressable=True,
        ))
    report.note = (
        f"从 KB 搬运 {len(report.opportunities)} 条 addressable+fix 机制进 PDCA 机会；"
        f"{len(report.cognitive_deferred)} 条认知机制不编译、交人。"
        "注入≠采纳，是否改进由 PDCA 研究/验证环决定。"
    )
    return report


def forensic_gaps_to_opportunities(
    adjudications: dict[str, dict[str, Any]],
) -> BridgeReport:
    """把取证法官的缺口（非 ok 的 action/code）转成机会并落消费痕迹。"""
    report = BridgeReport()
    for gate, res in adjudications.items():
        action = res.get("action", "")
        code = res.get("code", "")
        if action == "ok":
            continue
        # 缺口机制：把裁决 code 转成可研究的 PDCA 机会
        opp = Opportunity(
            kind="forensic_gap",
            signal=f"{code}:{gate}",
            where="agent",
            detail=f"门禁 {gate} 取证裁决 {action}/{code}，需研究判据/证据缺口",
            source=f"forensic_judge:{gate}",
            addressable=True,
        )
        report.opportunities.append(opp)
        report.consumption.append(ConsumptionRecord(
            source_kind="forensic_gap", source_id=code,
            mechanism=f"{gate} 取证缺口 {action}", injected_at=_now(), addressable=True,
        ))
    report.note = f"从取证裁决搬运 {len(report.opportunities)} 个缺口进 PDCA；全 ok 则无缺口。"
    return report


def bridge_into_pdca(
    loop: Any,
    kb: KnowledgeBase | None = None,
    adjudications: dict[str, dict[str, Any]] | None = None,
) -> BridgeReport:
    """主入口：把 KB 机制 + 取证缺口注入 PDCALoop，返回消费痕迹报告。

    loop 须有 inject_opportunities(opps) 方法（pdca.PDCALoop 满足）。
    """
    merged = BridgeReport()
    if kb is not None:
        r = kb_to_opportunities(kb)
        merged.opportunities.extend(r.opportunities)
        merged.consumption.extend(r.consumption)
        merged.cognitive_deferred.extend(r.cognitive_deferred)
    if adjudications:
        r = forensic_gaps_to_opportunities(adjudications)
        merged.opportunities.extend(r.opportunities)
        merged.consumption.extend(r.consumption)
    loop.inject_opportunities(merged.opportunities)
    merged.note = (
        f"真实注入 {len(merged.opportunities)} 个机会到 PDCA（含 KB 机制与取证缺口）；"
        f"{len(merged.cognitive_deferred)} 条认知机制交人。"
    )
    return merged


def save_consumption(report: BridgeReport, path: str | Path) -> None:
    """消费痕迹落盘：可回放、可复核，作为反哺闭环的真实证据。"""
    Path(path).write_text(
        json.dumps(report.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8"
    )


def live_regression() -> dict:
    """自测：真实 KB 注入 PDCA + 消费痕迹可追溯 + 全 ok 取证无缺口 + 认知机制交人。"""
    checks: dict[str, bool] = {}
    root = Path(__file__).resolve().parent.parent

    kb = KnowledgeBase.load(root / "knowledge_base_store.json")
    rep = kb_to_opportunities(kb)
    checks["kb_has_opportunities"] = len(rep.opportunities) > 0
    checks["consumption_traced"] = all(
        c.source_id.startswith("KB-") for c in rep.consumption
        if c.source_kind == "knowledge_base"
    )
    checks["cognitive_deferred"] = len(rep.cognitive_deferred) > 0

    # 真实注入 PDCA
    from .pdca import PDCALoop, Budget
    loop = PDCALoop(budget=Budget(max_cycles=2, patience=1, max_attempts=1))
    merged = bridge_into_pdca(loop, kb=kb,
                              adjudications={"x": {"action": "downgrade", "code": "X.GAP"}})
    checks["injected_into_pdca"] = len(loop._injected_opps) == len(merged.opportunities)
    checks["forensic_gap_traced"] = any(
        c.source_id == "X.GAP" for c in merged.consumption
    )

    # 全 ok → 无取证缺口
    none = forensic_gaps_to_opportunities({"x": {"action": "ok", "code": "X.OK"}})
    checks["all_ok_no_gap"] = len(none.opportunities) == 0

    return {"checks": checks, "all_passed": all(checks.values())}
