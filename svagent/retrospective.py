"""元认知复盘层（L3）：复盘的对象不是产物、不是判据，而是「我当时的推理过程」。

这是框架一直缺失的一层。已有的三层自进化：
  L0 修内容 → L1 造判据 → L2 改进行判据的方法
它们复盘的都是「输出」与「判据」。而真正的认识提升来自复盘「认知轨迹」本身：
我带着什么先验入场、在哪些岔路口做了选择、结果如何推翻了我的预期、
我应该把什么教训带到下一次。

核心悖论与硬门禁：
  用户上一轮要求「避免后知先觉」，这一轮要求「复盘」——但若复盘没有事前锚点，
  它就是最精致的后知先觉：把结果倒推成「我早就想到的」，重写记忆、制造虚假的复利。
  因此本模块的第一纪律：**没有事前记录的先验及其时间戳的轨迹，拒绝复盘**。
  没有 outcome_ts > prior_ts 的时序证据，拒绝复盘。宁可拒绝，也不制造后知叙事。

复利机制：
  复盘产出的 Lesson 不是散文，而是带「触发条件」的可检索知识资产。
  新的推理轨迹声明情境标签 → 命中的历史教训被自动注入 → 下次推理站在上次肩上。
  教训的可信度随被独立轨迹佐证的次数增长（corroboration），这是可测量的复利。

反哺闭环：
  Lesson 可转成 PDCA 的 Opportunity，进入「识别→研究→验证→改进」循环，
  使「复盘认知」真正改变「后续判据与流程」，而不是写进报告就结束。

免责：这是认知方法的形式化，不保证复盘出的教训为真——教训本身也要过证据与反例。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


class HindsightGateError(ValueError):
    """事后复盘门禁：没有事前锚点的轨迹不允许复盘。"""


# ---------------------------------------------------------------- 数据模型
@dataclass
class DecisionPoint:
    """推理过程中的一个岔路口：当时面对什么、选了什么、为什么不选另一条。"""
    situation: str
    choice: str
    rationale: str
    alternative_rejected: str = ""


@dataclass
class ReasoningTrace:
    """一条可被复盘的真实推理轨迹。关键：先验与结果都带时间戳，且先验在前。

    scope 区分复盘的对象，这是本层最重要的一条分界：
      - "subject"   ：对【研究对象】的认知轨迹（如某股票、某宏观议题）——改进的是具体判断。
      - "framework" ：对【框架逻辑方法本身】的认知轨迹——自我反省，改进的是方法。
    用户明确：复盘针对框架逻辑方法层面、只针对自己。上一轮误用 subject 复盘研究对象，
    本轮校正为 framework。两者不可混为一谈——否则"复盘"会退化成对个案的事后解释。
    """
    trace_id: str
    question: str                       # 当时要回答的问题
    prior_belief: str                   # 事前倾向（防后知先觉的锚）
    prior_confidence: float             # 事前对该倾向的置信度 0-1
    prior_ts: str                       # 事前记录时间 ISO
    scope: str = "subject"              # subject | framework（复盘对象的分界）
    situation_tags: list[str] = field(default_factory=list)  # 情境标签，供教训检索
    decisions: list[DecisionPoint] = field(default_factory=list)
    expected_outcome: str = ""          # 事前预期的结果
    actual_outcome: str = ""            # 事后揭盲的真实结果
    outcome_ts: str = ""                # 结果揭盲时间 ISO（必须 > prior_ts）
    cognitive_corrections: list[str] = field(default_factory=list)  # 数据推翻预判的点
    anti_bias_measures: list[str] = field(default_factory=list)     # 部署的防偏差措施

    def gate(self) -> None:
        """防后知先觉硬门禁。无事前锚点 / 时序倒挂 → 拒绝复盘。"""
        if not self.prior_belief.strip():
            raise HindsightGateError("轨迹无事前先验：无锚点的复盘只是后知叙事重构，拒绝。")
        if not self.prior_ts or not self.outcome_ts:
            raise HindsightGateError("缺 prior_ts/outcome_ts：无法证明先验早于结果，拒绝。")
        try:
            t_prior = datetime.fromisoformat(self.prior_ts)
            t_out = datetime.fromisoformat(self.outcome_ts)
        except ValueError as exc:
            raise HindsightGateError(f"时间戳格式非法: {exc}") from exc
        if t_out <= t_prior:
            raise HindsightGateError(
                f"时序倒挂：结果({self.outcome_ts})不晚于先验({self.prior_ts})，"
                "这是事后编造的先验，拒绝。"
            )
        if not self.actual_outcome.strip():
            raise HindsightGateError("结果未揭盲：没有 actual_outcome，无法做事后对照，拒绝。")

    @property
    def surprised(self) -> bool:
        """先验是否被结果推翻/修正。"""
        return bool(self.cognitive_corrections)


@dataclass
class Lesson:
    """可迁移的知识资产：在什么情境下，该做什么/警惕什么。"""
    lesson_id: str
    trigger: list[str]                  # 触发情境标签（命中即可复用）
    action: str                         # 下次该怎么做
    rationale: str                      # 为什么（来自哪次复盘的差异归因）
    kind: str = "method"                # method | anti_bias | pitfall | tool | irreducible | keep
    support: list[str] = field(default_factory=list)   # 佐证过的 trace_id
    confidence: float = 0.0             # 随独立佐证次数增长
    provenance: str = ""                # 首次来自哪条轨迹
    # 「改进该改进的」三分法：只对 framework 轨迹填值。
    #   fix      = 真该改的方法缺陷（如符号 bug、合成自证、指标无分辨力）
    #   vanity   = 虚假改进（改报告口径冒充改能力、制造复利数字的冲动）
    #   preserve = 不该改的边界（诚实、不可约交人、把"不知道"当一等公民）——反省的价值也在于识别"守住什么"
    improvement_class: str = ""

    @property
    def n_supports(self) -> int:
        return len(self.support)


@dataclass
class ReviewOutcome:
    """一次 AAR（行动后复盘）的结构化产出。"""
    trace_id: str
    admitted: bool                      # 是否通过门禁
    expected: str
    actual: str
    gap: str                            # 预期与实际的差异
    worked: list[str]                   # 做对了什么
    failed: list[str]                   # 做错/漏掉了什么
    root_cause: str                     # 差异的根因
    lessons: list[Lesson] = field(default_factory=list)
    rejected_reason: str = ""
    # 仅 scope=framework 时产出：框架逻辑方法的自我反省三分法
    improvement_audit: dict[str, list[str]] = field(default_factory=dict)


# ---------------------------------------------------------------- 复盘引擎
class Retrospective:
    """对推理轨迹做 AAR，抽取可迁移教训。"""

    def __init__(self, store: "RetrospectiveStore | None" = None):
        self.store = store

    def review(self, trace: ReasoningTrace) -> ReviewOutcome:
        try:
            trace.gate()
        except HindsightGateError as exc:
            return ReviewOutcome(
                trace_id=trace.trace_id, admitted=False,
                expected=trace.expected_outcome, actual=trace.actual_outcome,
                gap="", worked=[], failed=[], root_cause="",
                rejected_reason=str(exc),
            )
        return self._do_review(trace)

    def _do_review(self, trace: ReasoningTrace) -> ReviewOutcome:
        worked: list[str] = []
        failed: list[str] = []

        # 做对了什么：部署的防偏差措施 + 被数据修正的认知（敢于改先验）
        if trace.anti_bias_measures:
            worked.append("部署了防偏差措施: " + "; ".join(trace.anti_bias_measures))
        if trace.surprised:
            worked.append("结果推翻先验时如实记录认知修正，未强行维护原判断")
        if trace.prior_confidence < 0.8:
            worked.append(f"入场先验置信度 {trace.prior_confidence:.2f} 保留谦逊，未锁死结论")

        # 做错/风险：事前过度自信、措施缺口
        if trace.prior_confidence >= 0.8 and trace.surprised:
            failed.append(f"事前过度自信({trace.prior_confidence:.2f})却被结果推翻——先验校准不足")
        if not trace.anti_bias_measures:
            failed.append("未记录任何防偏差措施，结果可能被确认偏差污染")
        if not trace.situation_tags:
            failed.append("无情境标签，本次教训将来无法被检索复用")

        gap = (
            f"事前预期「{trace.expected_outcome}」，实际「{trace.actual_outcome}」；"
            + ("先验被推翻。" if trace.surprised else "先验与结果一致。")
        )
        root_cause = self._attribute(trace)

        if trace.scope == "framework":
            # 框架逻辑方法的自我反省：不是通用教训抽取，而是「改进该改进的」三分法
            lessons, audit = self._framework_reflection(trace, gap)
        else:
            lessons = self._extract_lessons(trace, worked, failed, gap)
            audit = {}
        if self.store is not None:
            for lesson in lessons:
                self.store.put(lesson)

        return ReviewOutcome(
            trace_id=trace.trace_id, admitted=True,
            expected=trace.expected_outcome, actual=trace.actual_outcome,
            gap=gap, worked=worked, failed=failed, root_cause=root_cause,
            lessons=lessons, improvement_audit=audit,
        )

    def _framework_reflection(self, trace: ReasoningTrace, gap: str) -> tuple[list[Lesson], dict[str, list[str]]]:
        """针对框架逻辑方法本身的自我反省。

        三个问题（对应用户的「改进该改进的」）：
          1. 真该改的(fix)：被证据证伪的方法缺陷——改机制，不是改文案。
          2. 虚荣改进(vanity)：改报告口径冒充改能力、制造复利数字的冲动——识别它，别自欺。
          3. 不该改的(preserve)：框架的脊梁（诚实边界、不可约交人、把不知道当一等公民）
             ——反省不是全盘推翻，也包括确认哪些要守住。
        """
        audit = {"fix": [], "vanity": [], "preserve": [], "unclassified": []}
        for d in trace.decisions:
            cls = self._classify_framework_decision(d)
            audit[cls].append(f"{d.situation}: {d.choice}")

        lessons: list[Lesson] = []
        tags = trace.situation_tags or ["framework", "self_reflection"]
        for i, text in enumerate(audit["fix"]):
            lessons.append(Lesson(
                lesson_id=f"L-{trace.trace_id}-fix{i}", trigger=list(tags),
                action=f"真该改的方法缺陷——改机制而非文案：{text}",
                rationale=f"{trace.trace_id} 自我反省；{gap}", kind="pitfall",
                improvement_class="fix", support=[trace.trace_id], provenance=trace.trace_id,
            ))
        for i, text in enumerate(audit["vanity"]):
            lessons.append(Lesson(
                lesson_id=f"L-{trace.trace_id}-van{i}", trigger=list(tags),
                action=f"识破虚荣改进——别拿改动冒充进步：{text}",
                rationale=f"{trace.trace_id} 自我反省；{gap}", kind="anti_bias",
                improvement_class="vanity", support=[trace.trace_id], provenance=trace.trace_id,
            ))
        for i, text in enumerate(audit["preserve"]):
            lessons.append(Lesson(
                lesson_id=f"L-{trace.trace_id}-keep{i}", trigger=list(tags),
                action=f"不该改的边界——反省后确认守住：{text}",
                rationale=f"{trace.trace_id} 自我反省；{gap}", kind="keep",
                improvement_class="preserve", support=[trace.trace_id], provenance=trace.trace_id,
            ))
        return lessons, audit

    def _classify_framework_decision(self, d: DecisionPoint) -> str:
        """把一条框架决策分到 fix/vanity/preserve。

        只认 rationale 的【前缀显式标记】(fix:/vanity:/preserve:)，绝不做全文关键词匹配——
        否则"改的是机制而非文案"里出现"文案"二字就会被误判成虚荣改进，
        把真 bug 当成虚荣，恰恰违背"改进该改进的"。显式标记也避免事后主观改写分类。
        """
        head = d.rationale.strip()[:10].lower()
        if head.startswith("preserve"):
            return "preserve"
        if head.startswith("vanity"):
            return "vanity"
        if head.startswith("fix"):
            return "fix"
        # 无显式标记不猜测——归为一个中性类，由复盘者补齐标记，绝不擅自判定
        return "unclassified"

    def _attribute(self, trace: ReasoningTrace) -> str:
        """差异归因：不是复述结果，而是指出认知层面的根因。"""
        parts = []
        if trace.cognitive_corrections:
            parts.append("认知根因: " + " | ".join(trace.cognitive_corrections))
        if trace.prior_confidence >= 0.8 and trace.surprised:
            parts.append("高置信先验+被推翻 → 入场时把「印象」当成了「证据」")
        if not parts:
            parts.append("先验与结果一致；仍需在后续独立轨迹中验证，避免单次幸存")
        return "；".join(parts)

    def _extract_lessons(self, trace: ReasoningTrace, worked: list[str], failed: list[str], gap: str) -> list[Lesson]:
        lessons: list[Lesson] = []
        tags = trace.situation_tags or ["generic"]

        # 教训1：每个被证伪/修正的认知点 → pitfall 教训
        for i, corr in enumerate(trace.cognitive_corrections):
            lessons.append(Lesson(
                lesson_id=f"L-{trace.trace_id}-c{i}",
                trigger=list(tags),
                action=f"遇到同类情境时，先验须让位于预注册判据的结果：{corr}",
                rationale=f"来自 {trace.trace_id} 的认知修正；{gap}",
                kind="pitfall",
                support=[trace.trace_id],
                provenance=trace.trace_id,
            ))

        # 教训2：每个有效的防偏差措施 → anti_bias 教训（可迁移的方法）
        for i, m in enumerate(trace.anti_bias_measures):
            lessons.append(Lesson(
                lesson_id=f"L-{trace.trace_id}-b{i}",
                trigger=list(tags),
                action=f"复用防偏差措施：{m}",
                rationale=f"{trace.trace_id} 部署该措施后，结论经得起揭盲与消融检验",
                kind="anti_bias",
                support=[trace.trace_id],
                provenance=trace.trace_id,
            ))

        # 教训3：事前过度自信被推翻 → 校准教训
        if any("过度自信" in f for f in failed):
            lessons.append(Lesson(
                lesson_id=f"L-{trace.trace_id}-cal",
                trigger=list(tags) + ["high_prior_confidence"],
                action="入场先验置信度封顶 0.7；把初始倾向写下来当作待证伪对象，而非结论",
                rationale=f"{trace.trace_id} 事前置信 {trace.prior_confidence:.2f} 却被推翻",
                kind="anti_bias",
                support=[trace.trace_id],
                provenance=trace.trace_id,
            ))

        # 教训4：无标签 → 流程教训
        if not trace.situation_tags:
            lessons.append(Lesson(
                lesson_id=f"L-{trace.trace_id}-tag",
                trigger=["retrospective"],
                action="每条推理轨迹开始时先声明情境标签，否则教训无法复用",
                rationale=f"{trace.trace_id} 缺标签，教训检索失败",
                kind="method",
                support=[trace.trace_id],
                provenance=trace.trace_id,
            ))
        return lessons


# ---------------------------------------------------------------- 知识资产库
class RetrospectiveStore:
    """可累积、可检索、可持久化的教训库；复利在此发生。"""

    def __init__(self) -> None:
        self.lessons: dict[str, Lesson] = {}
        self.reviews: list[ReviewOutcome] = []
        self.trace_log: list[dict[str, Any]] = []

    def put(self, lesson: Lesson) -> None:
        """去重合并：相同 action 视为同一教训，独立轨迹佐证 → 置信度增长。"""
        key = lesson.action.strip()
        existing = next((l for l in self.lessons.values() if l.action.strip() == key), None)
        if existing is None:
            self.lessons[lesson.lesson_id] = lesson
            lesson.confidence = 1.0 / (1.0 + 1.0)  # 1 次佐证
            return
        # 合并触发情境、累计佐证
        for t in lesson.trigger:
            if t not in existing.trigger:
                existing.trigger.append(t)
        for s in lesson.support:
            if s not in existing.support:
                existing.support.append(s)
        n = existing.n_supports
        existing.confidence = n / (n + 1.0)

    def log_trace(self, trace: ReasoningTrace) -> None:
        self.trace_log.append(asdict(trace))

    def recall(self, situation_tags: list[str], min_overlap: float = 0.5) -> list[Lesson]:
        """按情境命中检索可复用教训；命中率越高、置信度越高越靠前。"""
        tags = set(situation_tags)
        if not tags:
            return []
        hits: list[tuple[float, Lesson]] = []
        for lesson in self.lessons.values():
            trig = set(lesson.trigger) - {"high_prior_confidence", "retrospective"}
            overlap = len(tags & trig) / len(trig) if trig else 0.0
            if overlap >= min_overlap:
                hits.append((overlap * lesson.confidence, lesson))
        hits.sort(key=lambda x: x[0], reverse=True)
        return [l for _, l in hits]

    def inject_into_trace(self, trace: ReasoningTrace) -> list[Lesson]:
        """把历史教训注入新轨迹的防偏差措施——这是复利的实际落点。"""
        recalled = self.recall(trace.situation_tags)
        injected: list[Lesson] = []
        for lesson in recalled:
            injection = f"[复盘复用·{lesson.kind}] {lesson.action}"
            if injection not in trace.anti_bias_measures:
                trace.anti_bias_measures.append(injection)
                injected.append(lesson)
        return injected

    def compounding_curve(self, traces: list[ReasoningTrace]) -> list[dict[str, Any]]:
        """复利曲线：逐条纳入【通过门禁的】轨迹后，教训的覆盖与置信度如何增长。

        被门禁拒绝的轨迹不计入——它没有事前锚点，本就不该贡献知识。
        """
        probe_tags = ["macro", "cycle_phase", "narrative_truth"]
        curve = []
        temp = RetrospectiveStore()
        rev = Retrospective(temp)
        i = 0
        for trace in traces:
            r = rev.review(trace)
            if not r.admitted:
                continue  # 被拒的轨迹不参与复利
            temp.reviews.append(r)
            i += 1
            curve.append({
                "n_traces": i,
                "lessons": len(temp.lessons),
                "probe_recall": len(temp.recall(probe_tags)),
                "avg_confidence": round(
                    sum(l.confidence for l in temp.lessons.values()) / max(1, len(temp.lessons)), 3
                ),
                "corroborated": sum(1 for l in temp.lessons.values() if l.n_supports > 1),
            })
        return curve

    def save(self, path: str | Path) -> None:
        payload = {
            "lessons": [asdict(l) for l in self.lessons.values()],
            "reviews": [asdict(r) for r in self.reviews],
            "trace_log": self.trace_log,
        }
        Path(path).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "RetrospectiveStore":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        store = cls()
        store.lessons = {l["lesson_id"]: Lesson(**l) for l in payload["lessons"]}
        store.reviews = [ReviewOutcome(**r) for r in payload["reviews"]]
        store.trace_log = payload["trace_log"]
        return store

    def summary(self) -> dict[str, Any]:
        return {
            "教训总数": len(self.lessons),
            "按类型": {k: sum(1 for l in self.lessons.values() if l.kind == k)
                     for k in sorted({l.kind for l in self.lessons.values()})},
            "被多次佐证的教训": sum(1 for l in self.lessons.values() if l.n_supports > 1),
            "平均置信度": round(sum(l.confidence for l in self.lessons.values())
                            / max(1, len(self.lessons)), 3),
        }


# ---------------------------------------------------------------- 反哺：Lesson → PDCA Opportunity
def lessons_to_opportunities(lessons: list[Lesson]) -> list[Any]:
    """把「流程/防偏差」类教训转成 PDCA 机会，进入识别→改进循环。

    延迟导入 pdca，避免循环依赖；返回 Opportunity 对象。
    """
    from .pdca import Opportunity

    out = []
    for lesson in lessons:
        if lesson.kind == "irreducible":
            continue
        # 诚实：认知教训是对推理者的行为约束，无法坍塌成符号判据（不是文本模式）。
        # 因此进 PDCA 时标记不可自动符号化 → 进入流程/人工队列，交人执行，
        # 绝不假装复盘能把"先验封顶0.7"编译成一条正则。这与框架"承认不可约"一致。
        out.append(Opportunity(
            kind="process_gap",
            signal=f"{lesson.lesson_id}:{lesson.action}",  # 用action保证唯一（rationale同类会重复）
            where="agent",
            detail=lesson.action,
            source=f"retrospective:{lesson.provenance}",
            addressable=False,
        ))
    return out


def report(store: RetrospectiveStore, reviews: list[ReviewOutcome]) -> None:
    print("=" * 100)
    print("元认知复盘层（L3）：复盘推理过程本身")
    print("=" * 100)
    print(f"{'轨迹':<22}{'门禁':>6}{'认知修正':>10}{'教训':>6}")
    for r in reviews:
        tr = next((t for t in store.trace_log if t["trace_id"] == r.trace_id), None)
        n_corr = len(tr.get("cognitive_corrections", [])) if tr else 0
        print(f"{r.trace_id:<22}{('通过' if r.admitted else '拒绝'):>6}"
              f"{n_corr:>10}{len(r.lessons):>6}")
        if not r.admitted:
            print(f"    └ 拒绝理由: {r.rejected_reason}")
    print("\n--- 知识资产库 ---")
    s = store.summary()
    print(f"  教训总数 {s['教训总数']}，按类型 {s['按类型']}")
    print(f"  被多次佐证 {s['被多次佐证的教训']}，平均置信度 {s['平均置信度']}")
    print("\n  三层自进化之上补齐 L3：复盘认知轨迹 → 抽取可迁移教训 → 注入下次推理。")
    print("  硬门禁保证：没有事前锚点的复盘被拒绝——复盘不会退化成后知先觉的叙事重构。")


def demo_traces() -> list[ReasoningTrace]:
    """两条真实风格的轨迹：库存周期论证（有锚点）+ 无锚点的后知复盘（应被拒）。"""
    t1 = ReasoningTrace(
        trace_id="inventory-2026",
        question="中国库存周期是否已从主动补库转为被动补库？",
        prior_belief="多数机构说在被动补库，可能属实",
        prior_confidence=0.65,
        prior_ts="2026-09-01T09:00:00",
        outcome_ts="2026-09-30T17:00:00",
        situation_tags=["macro", "cycle_phase", "narrative_truth", "hindsight_risk"],
        decisions=[
            DecisionPoint("机构结论互相矛盾", "机构结论只当标签、不喂判据", "防止确认偏差", "采信某一机构结论"),
            DecisionPoint("库存判定易被指标自由度操纵", "预注册方向法+死区窗口", "跑数前锁死规则", "看完数据再选口径"),
            DecisionPoint("名义库存上行", "做名义/实际双轨", "PPI价格效应可能伪装成补库", "直接用名义同比下结论"),
        ],
        expected_outcome="当前大概率被动补库",
        actual_outcome="当前主动补库；被动补库仅在2025Q4短暂出现且已结束；名义含水分",
        cognitive_corrections=[
            "当前状态和'印象'相反：营收库存双升是主动补库，数据推翻'转变属实'的先验",
            "名义库存+11.6%里约5pct是PPI价格效应，实际物量仅+6.6%",
        ],
        anti_bias_measures=["入场先记录先验倾向", "预注册判据", "盲判/揭盲分离", "名义实际双轨", "历史反例对照"],
    )
    # 第二条真实轨迹：华测导航财报研判（跨领域，共享 narrative_truth 标签）
    t2 = ReasoningTrace(
        trace_id="finance-hcnh",
        question="华测导航(300627)五年财报叙事是否真实？",
        prior_belief="24项判据全过、审计标准无保留，叙事大概率真实",
        prior_confidence=0.7,
        prior_ts="2026-10-05T09:00:00",
        outcome_ts="2026-10-05T18:00:00",
        situation_tags=["finance", "narrative_truth", "hindsight_risk", "audit_signals"],
        decisions=[
            DecisionPoint("判据全部通过", "不停在'全过=真实'，下挖盲区", "避免确认偏差", "直接宣布叙事真实"),
            DecisionPoint("政府补助占营业利润42.6%", "量化补贴依赖趋势", "判据看不到的利润质量", "忽略"),
        ],
        expected_outcome="判据全过，叙事真实",
        actual_outcome="判据全过但早期补贴依赖42.6%、非经常损益21.8%，真实轨迹是动态改善而非静态真实",
        cognitive_corrections=[
            "判据全过只说明没违反符号约束，不等于叙事真实——早期补贴依赖是判据盲区",
        ],
        anti_bias_measures=["入场先记录先验倾向", "预注册判据", "盲判/揭盲分离", "下挖判据盲区"],
    )
    # 第三条：无事前锚点——典型后知复盘，应被门禁拒绝
    t3 = ReasoningTrace(
        trace_id="hindsight-fake",
        question="（事后）我早就知道库存会转主动补库",
        prior_belief="",
        prior_confidence=1.0,
        prior_ts="",
        outcome_ts="2026-09-30T17:00:00",
        actual_outcome="结果已揭盲",
    )
    return [t1, t2, t3]


def framework_reflection_trace() -> ReasoningTrace:
    """第19节独立审计 → 第20节整改：一条真实的【框架逻辑方法】自我认知轨迹。

    事前锚点是可追溯的：commentary 第19节写下的 P0/P1/P2 问题清单与五条修复路线，
    明确早于第20节的逐条整改。这不是事后编造——两节在文档里前后相继。
    复盘它要照见的，不是"整改做得对不对"，而是"我的改进冲动里，
    哪些是真该改的、哪些是改口径冒充改能力、哪些边界根本不该动"。
    """
    return ReasoningTrace(
        trace_id="audit19-remedy20",
        scope="framework",
        question="第19节审计列出的 P0/P1/P2，逐条整改后框架逻辑方法是否真的改进了？",
        # 事前锚点：第19节的判断——真功夫与叙事包装各半，宏大叙事是待验证假设
        prior_belief="审计发现框架'真功夫与叙事包装各半'，我预期逐条销号能让它从自洽走向有效",
        prior_confidence=0.85,
        prior_ts="2026-11-20T10:00:00",   # 第19节审计完成时（早于整改）
        outcome_ts="2026-11-20T18:00:00",  # 第20节整改完成时
        situation_tags=["framework", "self_reflection", "remediation", "audit"],
        expected_outcome="7条问题逐条销号 → 框架有效性实质提升",
        actual_outcome=(
            "P0符号bug是真修复；但telos/axiology/mechanism改的是报告口径与宣称降级，"
            "能力本身未变；财报去循环只是量化暴露循环(precision 0.42)并未消除；"
            "真实数据只注入estimation一个模块。'销号'制造了进步的叙事，但框架仍主要靠合成自证。"
        ),
        cognitive_corrections=[
            "把'改报告口径/宣称降级'当成了'改能力'——降调宣传不等于机制变强",
            "逐条销号是改进冲动：我默认审计列的每条都该修，没区分'方法缺陷'与'诚实边界'",
            "第22节L3自己又造出复利曲线与教训计数——这正是'为了改进而改进'的虚荣指标，"
            "复盘对象还错成了研究对象(库存周期/华测导航),而非框架逻辑方法本身",
        ],
        anti_bias_measures=["独立审计视角", "攻击性实验", "数据来源盘点"],
        decisions=[
            DecisionPoint(
                "P0 estimation criterion符号与生成模型相反",
                "真修复：criterion=-b，与生成模型同号，加回归测试",
                "fix：这是可被客观证伪的硬bug，改的是机制而非文案",
                "改注释糊弄过去",
            ),
            DecisionPoint(
                "telos/axiology/mechanism 的过度宣称",
                "降级报告口径：加'诚实结论''稳健边界'段落",
                "vanity：改的是文案措辞，机制没变，却计入'整改完成'制造进步叙事",
                "承认这些方法在合成世界外未验证，暂停宣称",
            ),
            DecisionPoint(
                "财报盲测的后验分组循环",
                "加反例对照量化循环(precision 0.42)，宣称'去循环已修'",
                "vanity：循环没消除，只是被测量；'已修'是虚荣的销号话术",
                "如实标'循环仍在，仅暴露'",
            ),
            DecisionPoint(
                "把'不知道'当一等公民 / 不可约交人 / 诚实边界",
                "保留，且在复盘中确认这是框架的脊梁，不因'进化'而改掉",
                "preserve：自我反省的价值也在于识别'守住什么'，不是全盘推翻",
                "为了'更自动'而取消人工交接卡",
            ),
            DecisionPoint(
                "第22节L3复利曲线与教训计数",
                "识别为虚荣指标：教训数从7涨到9、置信0.5→0.556不等于认知提升",
                "vanity：制造了'我在进化'的自洽幻觉，正是'为了改进而改进'",
                "把复利数字当成果汇报",
            ),
            DecisionPoint(
                "复盘对象误用为研究对象(库存周期/华测导航)",
                "校正scope：框架自我反省只针对逻辑方法，不针对具体研究对象",
                "fix：复盘对象错了，整层L3的方向就错了——这是方法层面的真缺陷",
                "继续用个案复盘冒充框架反省",
            ),
        ],
    )


def report_framework_reflection(r: ReviewOutcome) -> None:
    """打印框架自我反省的三分法报告。"""
    print("\n" + "=" * 100)
    print("框架逻辑方法的自我反省（scope=framework）：改进该改进的")
    print("=" * 100)
    print(f"事前锚点: {r.expected}")
    print(f"揭盲结果: {r.actual}")
    print(f"\n根因: {r.root_cause}")
    a = r.improvement_audit
    for key, title in [("fix", "① 真该改的（改机制而非文案）"),
                       ("vanity", "② 虚荣改进（改动冒充进步，需识破）"),
                       ("preserve", "③ 不该改的（守住框架的脊梁）"),
                       ("unclassified", "④ 未标记（复盘者需补显式标记，不擅自归类）")]:
        if not a.get(key):
            continue
        print(f"\n{title} —— {len(a.get(key, []))} 条")
        for x in a.get(key, []):
            print(f"   • {x}")
    print("\n反省收束：改进不是越多越好。真该改的改机制，虚荣的识破，"
          "边界的守住——三者分清，才叫「改进该改进的」。")


def main() -> None:
    store = RetrospectiveStore()
    rev = Retrospective(store)
    traces = demo_traces()
    reviews = []
    for t in traces:
        r = rev.review(t)
        reviews.append(r)
        store.reviews.append(r)
        store.log_trace(t)
    report(store, reviews)

    # 复利验证：同类新议题命中历史教训
    new = ReasoningTrace(
        trace_id="new-topic",
        question="再判断一个宏观阶段叙事的真实性",
        prior_belief="待定",
        prior_confidence=0.5,
        prior_ts="2026-10-01T09:00:00",
        outcome_ts="2026-10-31T17:00:00",
        situation_tags=["macro", "cycle_phase", "narrative_truth"],
        actual_outcome="（演示注入，未真正揭盲）",
    )
    injected = store.inject_into_trace(new)
    print(f"\n复利验证：新议题命中 {len(injected)} 条历史教训并注入防偏差措施：")
    for l in injected:
        print(f"  - [{l.kind}] {l.action}")

    curve = store.compounding_curve(traces)
    print("\n复利曲线（固定探针情境的教训覆盖）：")
    for c in curve:
        print(f"  纳入{c['n_traces']}条轨迹 → 教训{c['lessons']} 命中{c['probe_recall']} 均置信{c['avg_confidence']}")

    # 反哺闭环：教训 → PDCA 流程机会（诚实标记为不可自动符号化）
    from .pdca import PDCALoop
    loop = PDCALoop()
    opps = lessons_to_opportunities(list(store.lessons.values()))
    loop.inject_opportunities(opps)
    identified = loop.identify()
    process = [o for o in identified if o.kind == "process_gap"]
    print(f"\n反哺闭环：{len(process)} 条教训已注入 PDCA 机会池（全部标记不可符号化→交人/流程）：")
    for o in process[:3]:
        print(f"  - {o.detail}")
    print(f"  ... 其中 addressable=True 的 {sum(1 for o in process if o.addressable)} 条（应为0：认知教训不可编译成判据）")

    # 框架逻辑方法的自我反省（本轮核心）：scope=framework，三分法
    fr = framework_reflection_trace()
    fr_result = rev.review(fr)
    store.reviews.append(fr_result)
    store.log_trace(fr)
    report_framework_reflection(fr_result)
    print(f"\n  【方向校正】上一轮复盘对象是研究对象(subject)：库存周期/华测导航；"
          f"本轮依用户指正改为框架逻辑方法(framework)：只针对自己。")
    print(f"  【门禁】该框架轨迹有事前锚点(第19节P0/P1/P2早于第20节整改)，"
          f"门禁判定={'通过' if fr_result.admitted else '拒绝'}。")

    path = "/workspace/retrospective_store.json"
    store.save(path)
    print(f"\n知识资产已持久化: {path}，教训 {len(store.lessons)} 条")


if __name__ == "__main__":
    main()
