"""PDCA 自动化运行机制：让判据环境自主地「识别→研究→验证→评估改进→再识别」。

前面各模块证明了单步能力：能隔离、能坍塌、能诊断返工、能归纳判据、能元学习。
但那些都需要人（或外部脚本）决定「下一步该跑哪个」。本模块补上最后一层：
一个不需要外部驱动、能自己决定下一步做什么、知道何时停、并能被审计的循环引擎。

PDCA 六个动作与本仓库已有能力的对应：

  P 自主识别 (Identify)  扫描日志/环境，找出「还没被判据覆盖的缺口」，分可修与不可约
  D 研究       (Research) 针对缺口，调用判据归纳器 + 元学习，产出候选改进提案
  C 验证       (Verify)   候选必须过回归门禁 + 冻结测试集，防止误杀合法表达
  A 评估/改进  (Act)      对比前后指标，采纳有收益的提案，无收益则回滚；更新元层
  → 再识别                 环境变强后重新扫描，旧缺口自动消解，进入下一轮

关键设计（区别于「反复重置的随机游走」）：
  1. 单调包含：只有过回归的提案才安装，S_{n+1} ⊇ S_n。
  2. 预算与收敛： stagnation 计数 + 不可约底面判定，自动停止，不会永远空转。
  3. 不可约交人：模糊句永远「不挡、只交人」，且这条被回归守卫锁住，进化不许吃掉人的裁量权。
  4. 全量审计：每一轮 P/D/C/A 的输入输出与决策理由都落盘，可追溯、可回放。
  5. 持续喂料：外部用 feed(logs) 持续注入线上日志，引擎自动逐轮消化。
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .core import Draft, Sentence
from .autopoiesis import (
    CycleMetric, Environment, LogIngestor, LogRecord, MetaLearner,
    PredicateInducer, PredicateSpec, _lab_ground_truth,
)
from .evolution import Features, Rule, evaluate_rule, lab_spec, learn_stump


# ---------------------------------------------------------------- 数据模型
@dataclass
class Opportunity:
    """识别阶段发现的一个缺口——PDCA 的输入。"""

    kind: str          # novel_token | scope_gap | age_regex | irreducible_human | coverage
    signal: str        # 证据文本（去重用）
    where: str         # chapter | agent
    detail: str        # 可长成判据的字面串
    source: str        # 来自哪条日志/会话
    addressable: bool  # False = 不可符号化，交人，不计入可修


@dataclass
class Proposal:
    """研究阶段产出的候选改进；可能来自判据归纳，也可能来自裁决学习。"""

    name: str
    strategy: str
    targets: list[str] = field(default_factory=list)
    spec: PredicateSpec | None = None
    rule: Rule | None = None
    expected_gain: float = 0.0


@dataclass
class Snapshot:
    """某一时刻的环境指标快照，用于评估阶段的前后对比。"""

    version: int
    predicates: int
    open_gaps: int       # 当前环境仍挡不住的可修缺口数
    human_queue: int     # 不可约、交人的数量
    total_signals: int

    @property
    def leak_rate(self) -> float:
        return self.open_gaps / max(1, self.total_signals)


@dataclass
class Budget:
    """停止策略：自动运转必须知道何时停。"""

    max_cycles: int = 12        # 最多跑多少轮
    patience: int = 3           # 连续多少轮无采纳即判定收敛
    max_attempts: int = 3       # 单个信号最多研究几次，耗尽则交人


@dataclass
class CycleRecord:
    """一轮 PDCA 的完整审计记录。"""

    cycle: int
    decision: str         # adopt | rollback | no-op | converged
    rationale: str
    before: Snapshot
    after: Snapshot
    detected: list[str]
    researched: list[str]
    verified: list[str]
    adopted: str | None
    installed_version: int
    stagnant: int

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["before_leak"] = round(self.before.leak_rate, 3)
        out["after_leak"] = round(self.after.leak_rate, 3)
        return out


# ---------------------------------------------------------------- 模糊句（不可约）
_IRREDUCIBLE_MARKS = ("说不清楚", "记不太真", "慢慢就过去了", "很久以前的事")


def is_irreducible(text: str) -> bool:
    """不可符号化的模糊句：无错误集合、无法坍塌，只能交人。"""
    return any(mark in text for mark in _IRREDUCIBLE_MARKS)


# ---------------------------------------------------------------- PDCA 引擎
class PDCALoop:
    """自主运转的 PDCA 引擎。外部只需 feed(logs)，再 run() 或直接循环 cycle()。"""

    def __init__(self, environment: Environment | None = None, budget: Budget | None = None):
        self.env = environment or Environment()
        self.budget = budget or Budget()
        self.ingestor = LogIngestor(self.env)
        self.inducer = PredicateInducer()
        self.meta = MetaLearner()

        self._inbox: list[LogRecord] = []     # 待消化日志
        self._injected_opps: list[Opportunity] = []  # 外部注入的机会（如 L3 复盘教训）
        self._attempts: dict[str, int] = {}   # 每个信号被研究的次数
        self._adopted_signals: set[str] = set()
        self.history: list[CycleRecord] = []
        self.cycle_no = 0
        self.stagnant = 0

    # -------------------------------------------------------------- 喂料
    def feed(self, logs: list[LogRecord]) -> None:
        """持续注入线上日志；引擎会在下一轮自动识别其中的缺口。"""
        self._inbox.extend(logs)

    def inject_opportunities(self, opps: list["Opportunity"]) -> None:
        """注入外部来源的机会（如 L3 复盘的流程教训）。

        这些机会不经过日志识别，直接进入待研究列表；可自动符号化的走正常研究，
        不可符号化的（addressable=False）在快照里计入人工/流程队列，交人执行。
        这是「复盘认知 → 改进流程」的反哺入口。
        """
        seen = {o.signal for o in self._injected_opps}
        for o in opps:
            if o.signal not in seen:
                self._injected_opps.append(o)
                seen.add(o.signal)

    # -------------------------------------------------------------- P：识别
    def _blocked(self, rec: LogRecord) -> bool:
        """当前环境是否已挡住这条失败——环境变强后旧缺口会自动消解。"""
        draft = (
            Draft(agent_lines=[rec.text]) if rec.where == "agent"
            else Draft(chapters={"工作": [Sentence(rec.text, ("k1",))]})
        )
        spec = _lab_ground_truth()
        return any(d.severity == "block" for d in self.env.check(draft, spec))

    def _classify(self, rec: LogRecord) -> str:
        if is_irreducible(rec.text):
            return "irreducible_human"
        if "岁" in rec.text:
            return "age_regex"
        if rec.where == "agent" and rec.detail:
            return "scope_gap"
        return "novel_token"

    def identify(self) -> list[Opportunity]:
        """自主识别：扫描全部日志，返回当前环境尚未覆盖、且未耗尽研究的缺口。"""
        out: list[Opportunity] = []
        seen: set[str] = set()
        for rec in self._inbox:
            if rec.accepted:
                continue
            signal = f"{rec.where}:{rec.text}"
            if signal in seen:
                continue
            seen.add(signal)

            kind = self._classify(rec)
            addressable = kind != "irreducible_human"
            # 不可约项始终列出（供快照统计），但不消耗研究次数
            if not addressable:
                out.append(Opportunity(
                    kind, signal, rec.where, rec.detail, rec.session, False,
                ))
                continue
            # 已被当前环境挡住 → 缺口消解，不再作为机会
            if self._blocked(rec):
                continue
            # 采纳过的信号不再重复提
            if signal in self._adopted_signals:
                continue
            # 研究次数耗尽 → 交人，不再反复空转
            if self._attempts.get(signal, 0) >= self.budget.max_attempts:
                out.append(Opportunity(
                    "irreducible_human", signal, rec.where, rec.detail,
                    rec.session, False,
                ))
                continue
            out.append(Opportunity(kind, signal, rec.where, rec.detail, rec.session, True))

        # 合并外部注入的机会（如 L3 复盘教训）——同样去重
        known = {o.signal for o in out}
        for ext in self._injected_opps:
            if ext.signal not in known:
                out.append(ext)
                known.add(ext.signal)

        # 可修的优先、证据明确的优先；不可约的排末尾
        out.sort(key=lambda o: (o.addressable, bool(o.detail), o.kind))
        return out

    # -------------------------------------------------------------- D：研究
    def research(self, opps: list[Opportunity]) -> list[Proposal]:
        """研究候选方案：判据归纳器出判据候选，裁决池出排序规则候选。"""
        addressable = [o for o in opps if o.addressable]
        for o in addressable:
            self._attempts[o.signal] = self._attempts.get(o.signal, 0) + 1

        # 把机会还原成日志，交给归纳器（复用已有能力，不重写归纳逻辑）
        records = [
            LogRecord("redteam_miss", o.signal.split(":", 1)[1], o.where, o.detail,
                      False, o.source)
            for o in addressable
        ]
        candidates = self.inducer.induce(records, self.env)
        installed_keys = {p.key() for p in self.env.predicates}
        candidates = [c for c in candidates if c.key() not in installed_keys]
        ranked = self.meta.rank(candidates, self.env)

        proposals = [
            Proposal(
                name=c.name, strategy=c.strategy, spec=c,
                targets=[o.signal for o in addressable],
            )
            for c in ranked
        ]

        # 裁决学习：当人工裁决样本足够，学一条排序规则（改进人效，而非新增 block）
        verdicts = [r for r in self._inbox if r.kind == "human_verdict"]
        if len(verdicts) >= 6:
            items = [(_features_from_text(r.text, r.where), r.accepted) for r in verdicts]
            if len({a for _, a in items}) > 1:
                rule = learn_stump(items)
                m = evaluate_rule(rule, items)
                proposals.append(Proposal(
                    name="排序规则(裁决学习)", strategy="ranking_stump", rule=rule,
                    expected_gain=m["top20_catch"] - m["base_rate"],
                ))
        return proposals

    # -------------------------------------------------------------- C：验证
    def verify(self, proposal: Proposal) -> tuple[bool, str]:
        """验证：候选判据必须过回归门禁；排序规则本身不改 block，直接通过。"""
        if proposal.spec is None:
            return True, "排序规则不改变 block 集合，无需回归门禁"
        candidate_set = list(self.env.predicates) + [proposal.spec]
        passed, why = self.env.regression_check(candidate_set)
        return passed, why

    # -------------------------------------------------------------- A：评估 + 改进
    def snapshot(self, opps: list[Opportunity] | None = None) -> Snapshot:
        opps = opps if opps is not None else self.identify()
        addressable = [o for o in opps if o.addressable]
        human = [o for o in opps if not o.addressable]
        return Snapshot(
            version=self.env.version,
            predicates=len(self.env.predicates),
            open_gaps=len(addressable),
            human_queue=len(human),
            total_signals=len(self._inbox),
        )

    def _evaluate_decision(
        self, before: Snapshot, after: Snapshot, adopted: str | None,
        verified_count: int, targeted: int,
    ) -> tuple[str, str]:
        """评估：只有「装了判据且漏网没变差」才算真改进；否则回滚或 no-op。"""
        if adopted is None:
            if targeted == 0:
                return "converged", "无未覆盖的可修缺口，只剩不可约项交人——复利到达底面"
            if verified_count == 0:
                return "no-op", "有缺口但无候选通过验证（研究能力暂不足），保持环境不变"
            return "no-op", "候选被元层或去重过滤，无可安装项"
        # 有采纳：必须「严格降低」漏网才算真改进；持平也算无效
        if after.open_gaps < before.open_gaps and after.version > before.version:
            return "adopt", f"安装 {adopted}，可修缺口 {before.open_gaps}→{after.open_gaps}，版本 v{before.version}→v{after.version}"
        # 装了却没改善：回滚该提案，元层权重已由 install 更新
        self.env.rollback(adopted)
        return "rollback", f"{adopted} 未降低漏网，已回滚，版本回到 v{self.env.version}"

    def cycle(self) -> CycleRecord:
        """执行一轮完整 PDCA。外部无需干预，调用一次前进一步。"""
        self.cycle_no += 1

        # P 识别
        opps = self.identify()
        before = self.snapshot(opps)

        # D 研究
        proposals = self.research(opps)

        # C 验证 + A 改进（逐个提案过门禁并安装）
        verified: list[str] = []
        adopted_list: list[str] = []
        for p in proposals:
            if p.rule is not None:
                # 排序规则：记入审计，不作为环境版本变更
                verified.append(f"{p.name}(人效+{p.expected_gain:.2f})")
                continue
            ok, why = self.verify(p)
            if not ok:
                continue
            verified.append(p.name)
            for o in opps:
                if o.addressable and o.detail and p.spec and o.detail in (
                    p.spec.params.get("tokens", [])
                ):
                    self._adopted_signals.add(o.signal)
            before_n = len(self.env.predicates)
            accepted = self.env.install(p.spec, ok, p.name)  # type: ignore[arg-type]
            if accepted and len(self.env.predicates) > before_n:
                adopted_list.append(p.name)

        # 本轮采纳的第一个作为代表（评估/回滚以其为准），全量名单进审计
        adopted = adopted_list[0] if adopted_list else None
        adopted_all = "、".join(adopted_list) if adopted_list else None

        # A 评估
        after_opps = self.identify()
        after = self.snapshot(after_opps)
        decision, rationale = self._evaluate_decision(
            before, after, adopted, len(verified),
            sum(1 for o in opps if o.addressable),
        )
        if adopted_all and decision == "adopt":
            rationale = f"安装 {adopted_all}，可修缺口 {before.open_gaps}→{after.open_gaps}，版本 v{before.version}→v{after.version}"

        if decision == "adopt":
            self.stagnant = 0
        elif decision == "converged":
            self.stagnant = self.budget.patience
        else:
            self.stagnant += 1

        record = CycleRecord(
            cycle=self.cycle_no, decision=decision, rationale=rationale,
            before=before, after=after,
            detected=[f"{o.kind}:{o.signal[:24]}" for o in opps],
            researched=[p.name for p in proposals],
            verified=verified, adopted=adopted_all,
            installed_version=self.env.version, stagnant=self.stagnant,
        )
        self.history.append(record)
        return record

    # -------------------------------------------------------------- 自动运转
    def run(self, max_cycles: int | None = None) -> list[CycleRecord]:
        """自动跑到收敛或预算耗尽——这是「自动化运行机制」的主入口。"""
        limit = max_cycles or self.budget.max_cycles
        out: list[CycleRecord] = []
        for _ in range(limit):
            record = self.cycle()
            out.append(record)
            if record.decision == "converged":
                break
            if self.stagnant >= self.budget.patience:
                out.append(self._force_converged())
                break
        return out

    def _force_converged(self) -> CycleRecord:
        snap = self.snapshot()
        rec = CycleRecord(
            cycle=self.cycle_no, decision="converged",
            rationale=f"连续 {self.stagnant} 轮无采纳，判定收敛；交人 {snap.human_queue} 项",
            before=snap, after=snap, detected=[], researched=[], verified=[],
            adopted=None, installed_version=self.env.version, stagnant=self.stagnant,
        )
        self.history.append(rec)
        return rec

    # -------------------------------------------------------------- 审计与持久化
    def save_audit(self, path: str | Path) -> None:
        """审计日志落盘：每轮 P/D/C/A 的输入输出与决策理由都可追溯。"""
        Path(path).write_text(
            "\n".join(json.dumps(r.to_dict(), ensure_ascii=False) for r in self.history),
            encoding="utf-8",
        )

    def save_environment(self, path: str | Path) -> None:
        self.env.save(path)

    def status(self) -> dict[str, Any]:
        snap = self.snapshot()
        return {
            "cycle": self.cycle_no,
            "version": self.env.version,
            "predicates": len(self.env.predicates),
            "open_gaps": snap.open_gaps,
            "human_queue": snap.human_queue,
            "stagnant": self.stagnant,
            "audit_records": len(self.history),
        }


# ---------------------------------------------------------------- 特征适配
def _features_from_text(text: str, where: str) -> Features:
    """把日志文本转成裁决学习所需的符号特征（不引入语义判断）。"""
    from .verifiers import concrete_markers
    markers = concrete_markers(text)
    grounded = lab_spec().grounded_text()
    return Features(
        length=float(len(text)),
        markers=float(len(markers)),
        unmatched=float(sum(1 for m in markers if m not in grounded)),
        digits=float(sum(c.isdigit() for c in text)),
        has_quote=float(any(q in text for q in ('"', "「", "“"))),
        where_agent=float(where == "agent"),
    )


# ---------------------------------------------------------------- 驱动
def _sample_batches() -> list[list[LogRecord]]:
    """演示用日志流：分批到达，模拟线上日志持续注入。

    每批喂入后引擎自动 PDCA 到收敛，再喂下一批——这就是「再识别」的现实形态：
    新的攻击面出现，环境再次不够用，循环再转一轮。
    """
    return [
        [  # 批次 1：正文新词
            LogRecord("redteam_miss", "1998年我在镇上的供销社上班，那时候有台收音机。",
                      "chapter", "收音机", False, "s1"),
        ],
        [  # 批次 2：对话行新词（作用域盲区）
            LogRecord("redteam_miss", "那时候柜台边放着自行车，您还记得吗？",
                      "agent", "自行车", False, "s2"),
        ],
        [  # 批次 3：年龄正则
            LogRecord("redteam_miss", "七岁那年家里穷，您听老人说过吗？",
                      "agent", "", False, "s3"),
        ],
        [  # 批次 4：不可约模糊句——复利底面，交人
            LogRecord("vague", "那会儿日子苦，有些事说不清楚了。",
                      "chapter", "", False, "s4"),
        ],
        [  # 批次 5：又一个正文新词——环境已能覆盖同类，验证复利
            LogRecord("redteam_miss", "1998年我在镇上的供销社上班，那时候有台缝纫机。",
                      "chapter", "缝纫机", False, "s5"),
        ],
    ]


def _sample_stream() -> list[LogRecord]:
    return [rec for batch in _sample_batches() for rec in batch]


def report(loop: PDCALoop) -> None:
    print("=" * 96)
    print("PDCA 自动化运行机制：自主识别 → 研究 → 验证 → 评估改进 → 再识别")
    print("=" * 96)
    print(f"{'轮次':>4}{'决策':>10}{'漏网率(识别→改进)':>18}{'交人':>6}"
          f"{'判据':>6}{'版本':>6}{'停滞':>6}  说明")
    for r in loop.history:
        leak = f"{r.before.leak_rate:.0%}→{r.after.leak_rate:.0%}"
        print(f"{r.cycle:>4}{r.decision:>10}{leak:>18}{r.after.human_queue:>6}"
              f"{r.after.predicates:>6}{r.installed_version:>6}{r.stagnant:>6}  "
              f"{r.rationale[:40]}")
    s = loop.status()
    print(f"\n  终止状态: 第 {s['cycle']} 轮, v{s['version']}, "
          f"自造判据 {s['predicates']} 条, 交人 {s['human_queue']} 项, "
          f"审计 {s['audit_records']} 条")
    print("  单调包含由回归门禁保证；收敛由预算与停滞计数保证；不可约项始终交人。")


def main() -> None:
    loop = PDCALoop(budget=Budget(max_cycles=10, patience=2, max_attempts=3))
    print("在线日志持续注入，每批后自动 PDCA 到收敛：\n")
    for i, batch in enumerate(_sample_batches(), 1):
        loop.feed(batch)
        rounds = loop.run()
        adopt = [r for r in rounds if r.decision == "adopt"]
        print(f"  批次 {i}: 消化 {len(batch)} 条日志, 转 {len(rounds)} 轮, "
              f"采纳 {len(adopt)} 次, 环境 v{loop.env.version} "
              f"({', '.join(a.adopted or '-' for a in adopt)})")

    print()
    report(loop)

    env_path = "/workspace/.svl_env.json"
    audit_path = "/workspace/.svl_pdca_audit.jsonl"
    loop.save_environment(env_path)
    loop.save_audit(audit_path)
    print(f"\n持久化: 环境 → {env_path}；审计 → {audit_path}（{len(loop.history)} 轮）")

    # 重载验证：环境可跨运行恢复，旧缺口仍被挡住
    reloaded = PDCALoop(Environment.load(env_path))
    first = _sample_stream()[0]
    draft = Draft(chapters={"工作": [Sentence(first.text, ("k1",))]})
    blocked = any(d.severity == "block" for d in reloaded.env.check(draft, _lab_ground_truth()))
    print(f"重载后挡住旧攻击: {'是' if blocked else '否'}")


if __name__ == "__main__":
    main()
