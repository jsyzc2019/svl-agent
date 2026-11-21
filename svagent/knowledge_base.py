"""框架自进化知识库（Mechanism Knowledge Base, MKB）。

与 retrospective.py 的「教训库」分工：
  - RetrospectiveStore 存的是【某条真实推理轨迹复盘的产物】——是一次 AAR 的结果。
  - 本模块存的是【经过凝练的机制类知识】——是跨轨迹、跨领域可复用的「怎么想 / 怎么判 /
    怎么防偏差」的底层机制，来源包括思考经验、推演教训、外部高知。

设计立场（承接 commentary 第 19/23 节）：
  1. 精干：只收机制，不收个案结论、不收漂亮数字。一条知识必须能说清「触发情境 → 该做什么」。
  2. 诚实：知识「变多」本身不是进化。必须有可审计的量变→质变判据，且带反虚荣门禁——
     防止把「知识条数上涨」做成新的 vanity 指标。
  3. 可证伪：每条知识带 provenance（来源）与 evidence（证据基础），佐证可独立核验；
     触发进化时显式列出量变证据与仍未达标的诚实缺口。
  4. 可消费：addressable 的机制能转成 PDCA 机会 / 注入新轨迹的防偏差措施——
     知识不是为了陈列，是为了被框架真正用上。

「量变足够 → 自主进化」的诚实表述：
  达标不宣称「框架已进化」，而是【触发一次正式的框架进化审查】——把够格的机制送进
  PDCA 的研究/验证环，由真实评估决定是否采纳。这延续了「区分自洽与有效」的一贯立场。
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------- 数据模型

# 三类机制知识
KIND_THINKING = "thinking_experience"     # 思考经验：怎么想、怎么搭框架
KIND_REASONING = "reasoning_lesson"       # 推演教训：哪次推演踩了坑、正确机制是什么
KIND_EXTERNAL = "external_insight"        # 外部高知：借来的经典机制（PDCA / SDT / IRL ...）
KINDS = (KIND_THINKING, KIND_REASONING, KIND_EXTERNAL)

# 证据基础（防纯自证）：真实实验 > 审计/盲测 > 经典理论 > 纯推理
EVIDENCE_EXPERIMENT = "experiment"        # 真实数据实验 / 盲测
EVIDENCE_AUDIT = "audit"                  # 独立审计 / 整改
EVIDENCE_THEORY = "theory"                # 外部经典理论 / 成熟方法论
EVIDENCE_REFLECTION = "reflection"        # 框架自我反省（最弱，须有其他佐证）

# 改进三分法（承接第 23 节）
CLASS_FIX = "fix"          # 真该改的方法缺陷
CLASS_VANITY = "vanity"    # 虚假改进
CLASS_PRESERVE = "preserve"  # 不该改、该守住的边界


@dataclass
class KnowledgeItem:
    """一条机制类知识。核心是「在什么触发下，该做什么机制动作」。"""
    item_id: str
    kind: str                              # thinking_experience | reasoning_lesson | external_insight
    mechanism: str                         # 凝练出的机制（一句话，讲清因果/结构）
    trigger: list[str] = field(default_factory=list)   # 触发情境标签，供检索复用
    action: str = ""                       # 下次遇到该情境时的具体机制动作
    provenance: str = ""                   # 首次来自哪（commentary:§X / trace:xxx /外部来源）
    timestamp: str = ""                    # 记录时间 ISO（防事后编造）
    support: list[str] = field(default_factory=list)   # 独立佐证来源列表（每条不同来源）
    evidence: str = EVIDENCE_REFLECTION    # 证据基础
    addressable: bool = False              # 能否编译成符号判据 / 可执行流程改进
    improvement_class: str = ""            # fix | vanity | preserve | ""（未分类）

    def __post_init__(self) -> None:
        if self.kind not in KINDS:
            raise ValueError(f"未知知识类型 {self.kind!r}，须属于 {KINDS}")
        if not self.mechanism.strip():
            raise ValueError("机制表述不能为空——知识库只收能说清机制的条目")
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()
        if self.improvement_class and self.improvement_class not in (
            CLASS_FIX, CLASS_VANITY, CLASS_PRESERVE
        ):
            raise ValueError(f"未知改进分类 {self.improvement_class!r}")

    @property
    def n_supports(self) -> int:
        return len(set(self.support))

    @property
    def corroborated(self) -> bool:
        """是否被【独立】来源佐证。自证（佐证源==provenance）不算。"""
        indep = {s for s in self.support if s and s != self.provenance}
        return len(indep) >= 1

    @property
    def independent_supports(self) -> list[str]:
        return sorted({s for s in self.support if s and s != self.provenance})


@dataclass
class ReadinessThresholds:
    """量变→质变的门槛。全部为可审计的数值，不是「我觉得够了」。"""
    min_items: int = 18                     # 规模：机制条目数
    min_corroboration_ratio: float = 0.40  # 佐证：被独立佐证的条目占比
    min_corroborated_abs: int = 6           # 佐证：独立佐证条目绝对数（防小样本高比例）
    min_kinds: int = 3                      # 多样性：三类知识齐全
    min_tags: int = 8                       # 多样性：覆盖的情境标签数
    min_fix_items: int = 3                  # 有效性：真该改的 fix 类机制数
    min_empirical_items: int = 5            # 实证锚定：真实实验/审计支撑的条目数
    max_vanity_ratio: float = 0.20          # 反虚荣：vanity 类占比上限


@dataclass
class ReadinessReport:
    """一次「量变是否够质变」的评估结果——把判断显式化、可审计。"""
    ready: bool
    dimensions: dict[str, bool]
    metrics: dict[str, Any]
    evidence: list[str]                    # 已达标的量变证据
    gaps: list[str]                        # 诚实缺口：还差什么
    vanity_gate: dict[str, Any]            # 反虚荣门禁结果
    proposal: "EvolutionProposal | None" = None


@dataclass
class EvolutionProposal:
    """就绪时生成的进化提案：触发一次【审查】，不是宣称已进化。"""
    trigger: str
    candidate_opportunities: list[dict[str, Any]]
    note: str


# ---------------------------------------------------------------- 知识库

class KnowledgeBase:
    """精干的机制知识库：加入、检索、度量、触发、反哺。"""

    def __init__(self, thresholds: ReadinessThresholds | None = None) -> None:
        self.items: dict[str, KnowledgeItem] = {}
        self.thresholds = thresholds or ReadinessThresholds()

    # ---------- 写入 ----------
    def ingest(self, item: KnowledgeItem) -> str:
        """去重合并：同 mechanism（或同 action）视为同一机制，独立来源佐证 → 累积。"""
        key = item.mechanism.strip()
        existing = next(
            (it for it in self.items.values() if it.mechanism.strip() == key
             or (item.action and it.action.strip() == item.action.strip())),
            None,
        )
        if existing is None:
            self.items[item.item_id] = item
            return item.item_id
        # 合并标签与佐证，升级证据基础与分类（取更强者）
        for t in item.trigger:
            if t not in existing.trigger:
                existing.trigger.append(t)
        for s in item.support:
            if s not in existing.support:
                existing.support.append(s)
        if _evidence_rank(item.evidence) > _evidence_rank(existing.evidence):
            existing.evidence = item.evidence
        if item.improvement_class == CLASS_FIX and existing.improvement_class != CLASS_FIX:
            existing.improvement_class = CLASS_FIX
        if item.addressable and not existing.addressable:
            existing.addressable = True
        return existing.item_id

    def ingest_many(self, items: list[KnowledgeItem]) -> list[str]:
        return [self.ingest(it) for it in items]

    def import_retrospective(self, path: str | Path) -> int:
        """从 L3 教训库导入：把复盘产物升级为机制知识（若尚未收录）。"""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        added = 0
        for lesson in payload.get("lessons", []):
            item = KnowledgeItem(
                item_id=f"KB-R-{lesson['lesson_id']}",
                kind=KIND_REASONING,
                mechanism=lesson.get("action", "").strip(),
                trigger=list(lesson.get("trigger", [])),
                action=lesson.get("action", ""),
                provenance=f"trace:{lesson.get('provenance', '')}",
                support=[f"trace:{lesson.get('provenance', '')}"]
                + [f"trace:{s}" for s in lesson.get("support", [])],
                evidence=EVIDENCE_REFLECTION,
                addressable=False,
                improvement_class=lesson.get("improvement_class", "") or "",
            )
            before = len(self.items)
            self.ingest(item)
            added += len(self.items) - before
        return added

    # ---------- 检索 ----------
    def recall(self, situation_tags: list[str], min_overlap: float = 0.4) -> list[KnowledgeItem]:
        """按情境命中检索可复用机制；命中率高、佐证强的靠前。"""
        tags = set(situation_tags)
        if not tags:
            return []
        hits: list[tuple[float, KnowledgeItem]] = []
        for it in self.items.values():
            trig = set(it.trigger)
            if not trig:
                continue
            overlap = len(tags & trig) / len(trig)
            if overlap >= min_overlap:
                strength = overlap + 0.15 * min(it.n_supports, 3) + _evidence_rank(it.evidence) * 0.05
                hits.append((strength, it))
        hits.sort(key=lambda x: x[0], reverse=True)
        return [it for _, it in hits]

    # ---------- 度量：量变的诚实刻画 ----------
    def stats(self) -> dict[str, Any]:
        items = list(self.items.values())
        tags: set[str] = set()
        for it in items:
            tags.update(it.trigger)
        corroborated = [it for it in items if it.corroborated]
        empirical = [it for it in items if it.evidence in (EVIDENCE_EXPERIMENT, EVIDENCE_AUDIT)]
        return {
            "条目总数": len(items),
            "按类型": {k: sum(1 for it in items if it.kind == k) for k in KINDS},
            "情境标签数": len(tags),
            "独立佐证条目数": len(corroborated),
            "佐证占比": round(len(corroborated) / max(1, len(items)), 3),
            "fix 类": sum(1 for it in items if it.improvement_class == CLASS_FIX),
            "vanity 类": sum(1 for it in items if it.improvement_class == CLASS_VANITY),
            "preserve 类": sum(1 for it in items if it.improvement_class == CLASS_PRESERVE),
            "实证锚定条目数": len(empirical),
            "可编译机制数": sum(1 for it in items if it.addressable),
        }

    def readiness(self) -> ReadinessReport:
        """核心：判断量变是否够触发一次框架进化审查。带反虚荣门禁。"""
        th = self.thresholds
        s = self.stats()
        n = s["条目总数"]
        cor_ratio = s["佐证占比"]
        cor_abs = s["独立佐证条目数"]
        k_count = sum(1 for v in s["按类型"].values() if v > 0)
        vanity_ratio = s["vanity 类"] / max(1, n)

        dims: dict[str, bool] = {
            "规模": n >= th.min_items,
            "独立佐证(占比)": cor_ratio >= th.min_corroboration_ratio,
            "独立佐证(绝对数)": cor_abs >= th.min_corroborated_abs,
            "多样性(三类齐全)": k_count >= th.min_kinds,
            "多样性(情境覆盖)": s["情境标签数"] >= th.min_tags,
            "有效性(fix 存在)": s["fix 类"] >= th.min_fix_items,
            "实证锚定": s["实证锚定条目数"] >= th.min_empirical_items,
        }

        evidence: list[str] = []
        gaps: list[str] = []
        if dims["规模"]:
            evidence.append(f"已凝练 {n} 条机制知识（门槛 {th.min_items}）")
        else:
            gaps.append(f"条目 {n}/{th.min_items}，还需 {th.min_items - n} 条机制")
        if dims["独立佐证(占比)"] and dims["独立佐证(绝对数)"]:
            evidence.append(f"{cor_abs} 条被独立来源佐证（占比 {cor_ratio:.0%}）")
        else:
            gaps.append(
                f"独立佐证 {cor_abs}/{th.min_corroborated_abs} 条、占比 {cor_ratio:.0%}/"
                f"{th.min_corroboration_ratio:.0%}——多数机制仍靠单一来源，需更多独立轨迹/实验佐证"
            )
        if dims["多样性(三类齐全)"] and dims["多样性(情境覆盖)"]:
            evidence.append(f"三类知识齐全，覆盖 {s['情境标签数']} 个情境标签")
        else:
            gaps.append(
                f"情境覆盖 {s['情境标签数']}/{th.min_tags} 个标签、类型 {k_count}/{th.min_kinds}——"
                "知识结构偏窄"
            )
        if dims["有效性(fix 存在)"]:
            evidence.append(f"{s['fix 类']} 条 fix 类真缺陷机制待改进")
        else:
            gaps.append(f"fix 类机制 {s['fix 类']}/{th.min_fix_items}——若无真该改的，就没有进化对象")
        if dims["实证锚定"]:
            evidence.append(f"{s['实证锚定条目数']} 条由真实实验/审计支撑")
        else:
            gaps.append(f"实证锚定 {s['实证锚定条目数']}/{th.min_empirical_items}——纯推理机制过多")

        gate, gate_reason = self._anti_vanity_gate(vanity_ratio)
        vanity_gate = {"passed": gate, "vanity_ratio": round(vanity_ratio, 3), "reason": gate_reason}
        if not gate:
            gaps.append(f"反虚荣门禁未过：{gate_reason}")

        metrics = {
            "条目总数": n,
            "独立佐证条目数": cor_abs,
            "佐证占比": cor_ratio,
            "情境标签数": s["情境标签数"],
            "fix 类": s["fix 类"],
            "vanity 占比": round(vanity_ratio, 3),
            "实证锚定条目数": s["实证锚定条目数"],
            "门槛": asdict(th),
            "统计": s,
        }

        ready = all(dims.values()) and gate
        report = ReadinessReport(
            ready=ready, dimensions=dims, metrics=metrics,
            evidence=evidence, gaps=gaps, vanity_gate=vanity_gate,
        )
        if ready:
            report.proposal = self._build_proposal()
        return report

    def _anti_vanity_gate(self, vanity_ratio: float) -> tuple[bool, str]:
        """反虚荣门禁：知识变多不等于进化。延续第 23 节「改进该改进的」教训。"""
        th = self.thresholds
        if vanity_ratio > th.max_vanity_ratio:
            return False, f"vanity 类占比 {vanity_ratio:.0%} 超过上限 {th.max_vanity_ratio:.0%}"
        items = list(self.items.values())
        if not items:
            return False, "知识库为空"
        # 防「同一来源刷量」：若超过半数条目 provenance 前缀相同，视为单一来源灌水
        sources = [it.provenance.split(":")[0] if ":" in it.provenance else it.provenance
                   for it in items]
        dominant = max(set(sources), key=sources.count)
        if sources.count(dominant) / len(sources) > 0.7:
            return False, f"来源过度集中于 {dominant!r}（{sources.count(dominant)}/{len(sources)}），疑为单一来源灌水"
        # 防「改口径冒充增长」：若 action 高度重复（几乎无差异机制），视为灌水
        actions = [it.action.strip() for it in items if it.action.strip()]
        if actions and len(set(actions)) / len(actions) < 0.6:
            return False, "机制动作高度重复，增长疑似改口径而非新增机制"
        return True, "通过：知识增长有来源多样性与实证支撑，非虚荣灌水"

    def _build_proposal(self) -> EvolutionProposal:
        """就绪时把 addressable 的 fix 机制转成进化提案（待 PDCA 审查）。"""
        candidates: list[dict[str, Any]] = []
        for it in self.items.values():
            if it.addressable and it.improvement_class == CLASS_FIX:
                candidates.append({
                    "item_id": it.item_id,
                    "mechanism": it.mechanism,
                    "action": it.action,
                    "trigger": it.trigger,
                    "evidence": it.evidence,
                })
        return EvolutionProposal(
            trigger="量变门槛全部达标且反虚荣门禁通过",
            candidate_opportunities=candidates,
            note=(
                "这是【触发一次框架进化审查】，不是宣称框架已进化。候选项是 addressable 的 "
                "fix 类机制，须经 PDCA 的研究→验证环由真实评估决定是否采纳；认知类不可编译"
                "机制仍保持 addressable=False，交人执行，绝不假装能编译成符号判据。"
            ),
        )

    # ---------- 反哺：知识 → 框架 ----------
    def to_opportunities(self) -> list[Any]:
        """把可编译的 fix 机制转成 PDCA 机会，进入识别→改进循环。"""
        from .pdca import Opportunity
        return [
            Opportunity(
                kind="mechanism_upgrade",
                signal=it.item_id + ":" + it.mechanism[:40],
                where="agent",
                detail=it.action,
                source=f"knowledge_base:{it.provenance}",
                addressable=it.addressable,
            )
            for it in self.items.values()
            if it.addressable and it.improvement_class == CLASS_FIX
        ]

    def injections_for(self, situation_tags: list[str]) -> list[str]:
        """把命中的机制转成可注入新轨迹防偏差措施的文本。"""
        return [
            f"[机制库·{it.kind}] {it.action}"
            for it in self.recall(situation_tags)
            if it.action
        ]

    # ---------- 持久化 ----------
    def save(self, path: str | Path) -> None:
        payload = {
            "items": [asdict(it) for it in self.items.values()],
            "thresholds": asdict(self.thresholds),
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "KnowledgeBase":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        kb = cls(thresholds=ReadinessThresholds(**payload.get("thresholds", {})))
        kb.items = {it["item_id"]: KnowledgeItem(**it) for it in payload["items"]}
        return kb


def _evidence_rank(evidence: str) -> int:
    """证据强度排序：实验/审计 > 理论 > 反省。"""
    return {EVIDENCE_EXPERIMENT: 3, EVIDENCE_AUDIT: 3,
            EVIDENCE_THEORY: 2, EVIDENCE_REFLECTION: 1}.get(evidence, 0)


# ---------------------------------------------------------------- 种子知识凝练
def seed_knowledge() -> list[KnowledgeItem]:
    """从 commentary 23 节真实凝练的机制类知识——不是合成自证，均有 provenance。

    佐证来源（support）用不同章节 / 真实实验标识，确保「独立佐证」可核验；
    自证（support == provenance）在 KnowledgeItem.corroborated 里会被剔除。
    """
    def mk(iid, kind, mech, trig, action, prov, sup, ev, addr, cls):
        return KnowledgeItem(
            item_id=iid, kind=kind, mechanism=mech, trigger=trig, action=action,
            provenance=prov, support=[prov] + sup, evidence=ev,
            addressable=addr, improvement_class=cls,
        )

    return [
        # ---- 思考经验：怎么想、怎么搭框架 ----
        mk("KB-T01", KIND_THINKING,
           "自证能力是环境的产物，不是模型属性：验证力来自可隔离的符号判据环境，而非模型自夸。",
           ["self_verification", "verification", "framework"],
           "评估任何 agent 的自证能力时，先审视它是否有隔离的判据环境，而非采信其自我陈述。",
           "commentary:§1.1", ["commentary:§3", "commentary:§5"], EVIDENCE_THEORY, False, ""),
        mk("KB-T02", KIND_THINKING,
           "坍塌映射是核心方法论：把开放式正确性（叙事真实性）坍塌为可判定的符号判据集合。",
           ["collapse", "verification", "narrative_truth"],
           "面对不可判定的开放问题，先找能把结果坍塌成有限可判定判据的映射，再谈验证。",
           "commentary:§1.2", ["commentary:§3.2"], EVIDENCE_THEORY, False, CLASS_PRESERVE),
        mk("KB-T03", KIND_THINKING,
           "验证基准必须先与生成过程隔离：anchor 存在 ≠ 内容有据，基准泄漏会让自证恒真。",
           ["benchmark", "leakage", "narrative_truth", "hindsight_risk"],
           "构造判据环境时强制来源隔离；任何被生成过程看过的基准不得参与判定。",
           "commentary:§1.3", ["commentary:§2.4", "commentary:§20.6"], EVIDENCE_AUDIT, True, CLASS_FIX),
        mk("KB-T04", KIND_THINKING,
           "六个环节是闸门不是闭环：没有返工回路的闸门序列不构成可持续自证系统。",
           ["feedback_loop", "rework", "framework"],
           "设计验证流程时检查是否存在失败的返工回路，而非只堆顺序执行的闸门。",
           "commentary:§2.3", ["commentary:§6"], EVIDENCE_THEORY, True, ""),
        mk("KB-T05", KIND_THINKING,
           "经济前提：验证成本必须低于生成成本，否则闭环在规模上不可持续。",
           ["cost", "scalability", "framework"],
           "引入新判据前估算其验证成本；成本高于生成成本的判据须简化或路由人工。",
           "commentary:§2.6", [], EVIDENCE_THEORY, False, CLASS_PRESERVE),
        mk("KB-T06", KIND_THINKING,
           "目的论统一 G×V×C：人是另一组认知参数，不是特权裁判——差异是程度不是类别。",
           ["telos", "axiology", "human_boundary", "framework"],
           "遇到「交人」决策时，把它建模为目标×价值×认知参数下的一个选项，而非默认归宿。",
           "commentary:§12", ["commentary:§11"], EVIDENCE_EXPERIMENT, False, CLASS_PRESERVE),
        mk("KB-T07", KIND_THINKING,
           "价值自举：判据环境是价值的化石——价值不是凭空设定，而是从历史裁决/判据中追溯。",
           ["value", "axiology", "bootstrap"],
           "需要价值函数时，先从既有判据与人工裁决中反推价值信号，避免线性同义反复。",
           "commentary:§13", [], EVIDENCE_EXPERIMENT, False, ""),
        mk("KB-T08", KIND_THINKING,
           "人的边界是能力函数 B(c)：随能力外移，但边界外移 ≠ 边界归零。",
           ["human_boundary", "capability", "framework"],
           "宣称某任务「可自动化」时，给出 B(c) 的能力证据与仍不可约的残余，不做二值断言。",
           "commentary:§11", ["commentary:§12.7"], EVIDENCE_EXPERIMENT, False, CLASS_PRESERVE),

        # ---- 推演教训：踩过的坑与正确机制 ----
        mk("KB-R01", KIND_REASONING,
           "代理变量陷阱：alarm 实为困境代理，扩到 22 家反例后 precision 从虚高崩到 0.42。",
           ["proxy_variable", "blind_test", "narrative_truth", "finance"],
           "发现高指标时追问「它测的真是我要的吗」；主动扩展反例样本检验代理变量是否失效。",
           "commentary:§18", ["commentary:§20.6"], EVIDENCE_EXPERIMENT, True, CLASS_FIX),
        mk("KB-R02", KIND_REASONING,
           "符号一致性：estimation 的 criterion 必须与生成模型同号（criterion=-b），否则预测方向反了。",
           ["estimation", "calibration", "bug"],
           "拟合判别模型后，用生成模型核对判据符号；对预测做正向 sanity check 再采信。",
           "commentary:§19", ["commentary:§20.1"], EVIDENCE_AUDIT, True, CLASS_FIX),
        mk("KB-R03", KIND_REASONING,
           "校准度 ≠ 辨别力：AUC 不能当 calibration，须用 ECE 单独度量。",
           ["calibration", "estimation", "metrics"],
           "报告模型质量时分开辨别力(AUC)与校准度(ECE)，不得混用概念制造漂亮数字。",
           "commentary:§20.2", ["commentary:§19"], EVIDENCE_AUDIT, True, CLASS_FIX),
        mk("KB-R04", KIND_REASONING,
           "同义反复：线性生成→线性拟合恒真，须注入非线性挑战并主动降级宣称。",
           ["tautology", "axiology", "validation", "framework"],
           "若验证方式与生成方式同构，判定结果无信息量；改用一个会推翻它的挑战再下结论。",
           "commentary:§20.4", ["commentary:§12.6"], EVIDENCE_AUDIT, True, CLASS_FIX),
        mk("KB-R05", KIND_REASONING,
           "名义/实际拆分：名义库存补库可能只是 PPI 涨价的水分，须拆成实际量才见真相。",
           ["macro", "inventory_cycle", "nominal_vs_real", "narrative_truth"],
           "涉价格与数量的宏观判断，先做名义/实际拆分，再谈「补库含金量」。",
           "commentary:§21", [], EVIDENCE_EXPERIMENT, False, ""),
        mk("KB-R06", KIND_REASONING,
           "复盘对象校正：复盘应针对框架逻辑方法(framework)，而非研究对象(subject)。",
           ["retrospective", "framework", "hindsight_risk"],
           "做 L3 复盘时先确认 scope=framework；对个案的事后解释不进知识库。",
           "commentary:§22", ["commentary:§23"], EVIDENCE_REFLECTION, True, CLASS_FIX),
        mk("KB-R07", KIND_REASONING,
           "区分自洽与有效：内部逻辑自洽的系统仍可能对真实世界无效，须有外部锚点。",
           ["audit", "validity", "framework", "self_consistency"],
           "审计一个系统时，分别检验内部一致性与对真实数据的有效性，不以前者代替后者。",
           "commentary:§19", ["commentary:§20.9"], EVIDENCE_AUDIT, False, CLASS_PRESERVE),
        mk("KB-R08", KIND_REASONING,
           "改进该改进的（三分法）：fix 真缺陷、vanity 假改进、preserve 守住边界。",
           ["retrospective", "framework", "vanity", "improvement"],
           "每次自我反省后用三分法归类；发现 vanity 冲动立即摒弃，识别 preserve 边界主动守住。",
           "commentary:§23.3", ["commentary:§23.4"], EVIDENCE_REFLECTION, False, CLASS_PRESERVE),

        # ---- 外部高知：借来的经典机制 ----
        mk("KB-E01", KIND_EXTERNAL,
           "PDCA 戴明环：识别→研究→验证→改进的自动机，且必须有停止条件（预算/收敛）。",
           ["pdca", "automation", "framework", "stopping"],
           "让流程自转时，配套定义 budget 与收敛判据，避免无限空转或过早停止。",
           "external:PDCA(戴明)", ["commentary:§10"], EVIDENCE_THEORY, True, ""),
        mk("KB-E02", KIND_EXTERNAL,
           "红队对抗：让系统自己构造让它露馅的输入，主动找洞而非自证正确。",
           ["red_team", "adversarial", "validation"],
           "每次宣称有效前，先让红队生成能推翻它的反例，记录被击穿的边界。",
           "external:red_teaming", ["commentary:§7.2"], EVIDENCE_THEORY, True, ""),
        mk("KB-E03", KIND_EXTERNAL,
           "消融与反例对照：看似完美的指标（recall=1.0）须拆解「靠什么撑起」，做诊断而非新检验。",
           ["ablation", "metrics", "experiment"],
           "读到极端指标时做消融：逐项移除组件看贡献来源，警惕单一特征撑起全局。",
           "external:ablation", ["commentary:§18.4"], EVIDENCE_THEORY, False, ""),
        mk("KB-E04", KIND_EXTERNAL,
           "序贯最优停止：何时停止观测、接受当前最优，本身是一个可形式化的决策问题。",
           ["optimal_stopping", "telos", "decision"],
           "面对「继续探索还是收手」，用序贯最优停止框架显式建模成本与收益。",
           "external:optimal_stopping", ["commentary:§12"], EVIDENCE_THEORY, False, ""),
        mk("KB-E05", KIND_EXTERNAL,
           "逆强化学习 IRL：价值可从专家示范/裁决中推断，无需显式设定奖励。",
           ["irl", "value", "axiology", "bootstrap"],
           "价值难显式定义时，从历史裁决样本反推隐含价值函数，再用反例检验。",
           "external:IRL", ["commentary:§13"], EVIDENCE_THEORY, False, ""),
        mk("KB-E06", KIND_EXTERNAL,
           "信号检测论 SDT：用 d'（辨别力）与 criterion（偏差）分离「看不看得清」与「判断阈值」。",
           ["sdt", "calibration", "estimation", "metrics"],
           "分析二分类判断时分别估计辨别力与判定偏差，避免把保守/激进误当能力高低。",
           "external:SDT", ["commentary:§20"], EVIDENCE_THEORY, False, ""),
        mk("KB-E07", KIND_EXTERNAL,
           "对抗偏差三件套：预注册判据 + 盲测 + 时间戳门禁，把「我不知道」变成一等公民。",
           ["hindsight_risk", "blind_test", "preregistration", "anti_bias"],
           "任何事后评估先预注册判据、执行盲测、用时间戳证明先验在前；无法证明则拒绝对其复盘。",
           "external:anti_bias", ["commentary:§18", "commentary:§21", "commentary:§22.2"],
           EVIDENCE_THEORY, True, CLASS_FIX),
    ]


# ---------------------------------------------------------------- 报告
def report(kb: KnowledgeBase, r: ReadinessReport, path: str | Path = "knowledge_base_report.html") -> None:
    """生成人类可读的知识库 / 就绪度报告。"""
    import html as _html
    esc = _html.escape
    s = kb.stats()
    kind_cn = {KIND_THINKING: "思考经验", KIND_REASONING: "推演教训", KIND_EXTERNAL: "外部高知"}
    ev_cn = {EVIDENCE_EXPERIMENT: "真实实验/盲测", EVIDENCE_AUDIT: "独立审计/整改",
             EVIDENCE_THEORY: "经典理论", EVIDENCE_REFLECTION: "框架反省"}

    rows = []
    for it in sorted(kb.items.values(), key=lambda x: (x.kind, x.item_id)):
        sup = "、".join(it.independent_supports) or "—"
        rows.append(
            f"<tr><td><b>{esc(it.item_id)}</b></td><td>{esc(kind_cn.get(it.kind, it.kind))}</td>"
            f"<td>{esc(it.mechanism)}</td><td>{esc(ev_cn.get(it.evidence, it.evidence))}</td>"
            f"<td>{'是' if it.corroborated else '否'}（{len(it.independent_supports)}）</td>"
            f"<td>{esc(it.provenance)}<br><span class='dim'>佐证：{esc(sup)}</span></td></tr>"
        )

    dim_html = "".join(
        f"<li class={'ok' if v else 'no'}>{'✓' if v else '✗'} {esc(k)}</li>"
        for k, v in r.dimensions.items()
    )
    ev_html = "".join(f"<li class='ok'>✓ {esc(x)}</li>" for x in r.evidence) or "<li class='dim'>（无）</li>"
    gap_html = "".join(f"<li class='no'>✗ {esc(x)}</li>" for x in r.gaps) or "<li class='ok'>无缺口</li>"
    gate = r.vanity_gate
    gate_cls = "ok" if gate["passed"] else "no"
    status = "达标 · 触发进化审查" if r.ready else "量变积累中 · 尚未触发"
    status_cls = "ready" if r.ready else "notready"

    proposal_html = ""
    if r.proposal:
        cand = "".join(
            f"<li>{esc(c['item_id'])}：{esc(c['mechanism'])}</li>"
            for c in r.proposal.candidate_opportunities
        ) or "<li class='dim'>（暂无 addressable 的 fix 机制）</li>"
        proposal_html = f"""
        <div class="card">
          <h2>进化提案（触发一次审查，非宣称已进化）</h2>
          <p class="note">{esc(r.proposal.note)}</p>
          <ul>{cand}</ul>
        </div>"""

    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>框架自进化知识库 · 就绪度报告</title>
<style>
body{{font-family:-apple-system,'PingFang SC',sans-serif;max-width:1180px;margin:32px auto;padding:0 20px;color:#1a1a1a;line-height:1.65}}
h1{{font-size:26px;border-bottom:3px solid #2c5282;padding-bottom:10px}}
h2{{font-size:19px;margin-top:30px;color:#2c5282}}
.card{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:10px;padding:16px 22px;margin:18px 0}}
.status{{display:inline-block;padding:8px 16px;border-radius:20px;font-weight:700;font-size:15px}}
.ready{{background:#fed7d7;color:#9b2c2c}}.notready{{background:#e2e8f0;color:#2d3748}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin-top:10px}}
th,td{{border:1px solid #cbd5e0;padding:7px 9px;text-align:left;vertical-align:top}}
th{{background:#edf2f7}}ul{{margin:8px 0;padding-left:22px}}li{{margin:4px 0}}
.ok{{color:#276749}}.no{{color:#9b2c2c}}.dim{{color:#718096;font-size:12px}}
.note{{color:#4a5568;font-size:13px;background:#fffaf0;border-left:3px solid #dd6b20;padding:8px 12px}}
.stat{{display:flex;gap:24px;flex-wrap:wrap;margin:12px 0}}
.stat div{{background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:10px 16px}}
.stat b{{font-size:22px;color:#2c5282;display:block}}
</style></head><body>
<h1>框架自进化知识库 · 就绪度报告</h1>
<p>精干沉淀三类机制类知识（思考经验 / 推演教训 / 外部高知），以可审计的量变判据触发框架进化审查。
核心立场：<b>知识变多 ≠ 进化</b>——反虚荣门禁防止把条数做成新的漂亮数字。</p>

<div class="card">
  <span class="status {status_cls}">{esc(status)}</span>
  <div class="stat">
    <div><b>{s['条目总数']}</b>机制条目</div>
    <div><b>{s['独立佐证条目数']}</b>独立佐证</div>
    <div><b>{s['情境标签数']}</b>情境标签</div>
    <div><b>{s['fix 类']}</b>fix 待改</div>
    <div><b>{s['实证锚定条目数']}</b>实证锚定</div>
    <div><b>{s['可编译机制数']}</b>可编译机制</div>
  </div>
</div>

<div class="card">
  <h2>量变判据（全部达标才触发）</h2><ul>{dim_html}</ul>
  <p class="{gate_cls}"><b>反虚荣门禁：</b>{'通过' if gate['passed'] else '未过'} — {esc(gate['reason'])}</p>
</div>

<div class="card">
  <h2>已达标的量变证据</h2><ul>{ev_html}</ul>
  <h2>诚实缺口（未达标项）</h2><ul>{gap_html}</ul>
</div>
{proposal_html}

<h2>机制条目（共 {s['条目总数']} 条）</h2>
<table><thead><tr><th>ID</th><th>类型</th><th>凝练的机制</th><th>证据基础</th><th>独立佐证</th><th>来源 / 佐证链</th></tr></thead>
<tbody>{''.join(rows)}</tbody></table>
</body></html>"""
    Path(path).write_text(html, encoding="utf-8")


def main() -> None:
    kb = KnowledgeBase()
    kb.ingest_many(seed_knowledge())
    kb.import_retrospective("retrospective_store.json")
    r = kb.readiness()
    print(json.dumps({
        "stats": kb.stats(),
        "ready": r.ready,
        "dimensions": r.dimensions,
        "gaps": r.gaps,
        "vanity_gate": r.vanity_gate,
    }, ensure_ascii=False, indent=2))
    report(kb, r)


if __name__ == "__main__":
    main()
