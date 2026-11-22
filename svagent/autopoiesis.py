"""开放自组织 Agent：判据环境不是被设计好的，而是被 agent 自己造出来的。

第一性原理的引申：coding agent 依赖的外置判据（它的环境）本身可以被递归构造。
没有先验的完美环境，只有一个从最小种子开始、把每一次失败沉淀成新判据、
并能把「改进判据的方法」也一并改进的开放系统。

三层递归：
  L0 产物层：生成内容、跑判据、修内容
  L1 判据层：失败 → 归纳新判据 → 回归筛选 → 安装/回滚
  L2 元层  ：哪些归纳策略被接受了 → 调整策略权重 → 改进「改进的方法」

项目化的五件事也在这里落地：
  1. 线上日志摄取（JSONL）
  2. 从失败自动归纳判据（不再手工模板补丁）
  3. 长期规格跨会话持久化（save/load）
  4. 角色信息隔离（每个角色只看自己该看的投影）
  5. 判据版本、回归门禁与回滚
"""
from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

from .core import Claim, Draft, Diagnostic, GroundTruth, Locus, Message, Sentence
from .verifiers import default_verifiers

Verifier = Callable[[Draft, GroundTruth], list[Diagnostic]]


# ---------------------------------------------------------------- 数据模型
@dataclass
class LogRecord:
    """线上日志的最小契约：判据的养料。"""

    kind: str          # "redteam_miss" | "human_verdict" | "rework_outcome"
    text: str
    where: str         # "chapter" | "agent"
    detail: str = ""
    accepted: bool = False   # human_verdict：人是否确认内容属实
    session: str = ""


@dataclass
class LabeledCase:
    """回归样本：既锁住「该挡的」，也锁住「不该挡的」。"""

    text: str
    where: str
    should_block: bool
    origin: str


@dataclass
class PredicateSpec:
    """一个可安装、可回滚、带证据的版本化判据。"""

    name: str
    kind: str            # "token" | "regex"
    params: dict[str, Any]
    strategy: str
    evidence: list[str] = field(default_factory=list)
    version: int = 1

    def key(self) -> str:
        return f"{self.kind}:{self.params.get('pattern') or ','.join(self.params.get('tokens', []))}"


@dataclass
class CycleMetric:
    cycle: int
    version: int
    predicates: int
    acceptance: float
    attack_success: float
    human_flags: int
    rollback: bool


# ---------------------------------------------------------------- 环境基座
class Environment:
    """agent 自己构造的判据环境——唯一需要持久化的东西。"""

    def __init__(self) -> None:
        self.predicates: list[PredicateSpec] = []
        self.regression: list[LabeledCase] = [
            # 边界守卫：过宽的判据即使在当前日志上有效，也不许误杀合法表达
            LabeledCase("1998年我在镇上的供销社上班。", "chapter", False, "guard"),
            LabeledCase("您还记得1998年的事吗？", "agent", False, "guard"),
            LabeledCase("那会儿日子苦，有些事说不清楚了。", "chapter", False, "guard"),
        ]
        self.meta: dict[str, dict[str, int]] = {}
        self.version = 0
        self.metrics: list[CycleMetric] = []

    # ---------- 编译 ----------
    def compile(self) -> list[Verifier]:
        predicates = list(default_verifiers())
        for spec in self.predicates:
            predicates.append(_compile_spec(spec))
        return predicates

    def check(self, draft: Draft, ground_truth: GroundTruth) -> list[Diagnostic]:
        return [d for v in self.compile() for d in v(draft, ground_truth)]

    # ---------- 回归门禁 ----------
    def regression_check(self, candidate: list[PredicateSpec]) -> tuple[bool, str]:
        compiled = list(default_verifiers()) + [_compile_spec(s) for s in candidate]

        def blocks(text: str, where: str) -> bool:
            draft = Draft(agent_lines=[text]) if where == "agent" else Draft(
                chapters={"工作": [Sentence(text, ("k1",))]}
            )
            return any(
                d.severity == "block"
                for v in compiled
                for d in v(draft, _lab_ground_truth())
            )

        for case in self.regression:
            expected = blocks(case.text, case.where)
            if expected != case.should_block:
                return False, f"回归失败: {case.origin} / {case.text[:20]}"
        return True, "ok"

    # ---------- 安装 / 回滚 ----------
    def install(self, spec: PredicateSpec, passed: bool, log_id: str) -> bool:
        if not passed:
            self._update_meta(spec.strategy, accepted=False)
            return False
        existing = {p.key() for p in self.predicates}
        if spec.key() in existing:
            self._update_meta(spec.strategy, accepted=True)
            return False
        self.predicates.append(spec)
        self._update_meta(spec.strategy, accepted=True)
        self.version += 1
        return True

    def rollback(self, name: str) -> bool:
        before = len(self.predicates)
        self.predicates = [p for p in self.predicates if p.name != name]
        if len(self.predicates) < before:
            self.version += 1
            return True
        return False

    def _update_meta(self, strategy: str, accepted: bool) -> None:
        slot = self.meta.setdefault(strategy, {"accept": 0, "reject": 0})
        slot["accept" if accepted else "reject"] += 1

    def weight(self, strategy: str) -> float:
        slot = self.meta.get(strategy, {"accept": 0, "reject": 0})
        return (slot["accept"] + 1) / (slot["accept"] + slot["reject"] + 2)

    # ---------- 跨会话持久化 ----------
    def save(self, path: str | Path) -> None:
        payload = {
            "version": self.version,
            "predicates": [asdict(p) for p in self.predicates],
            "regression": [asdict(c) for c in self.regression],
            "meta": self.meta,
            "metrics": [asdict(m) for m in self.metrics],
        }
        Path(path).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    @classmethod
    def load(cls, path: str | Path) -> "Environment":
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        env = cls()
        env.version = payload["version"]
        env.predicates = [PredicateSpec(**p) for p in payload["predicates"]]
        env.regression = [LabeledCase(**c) for c in payload["regression"]]
        env.meta = payload["meta"]
        env.metrics = [CycleMetric(**m) for m in payload["metrics"]]
        return env

    def summary(self) -> dict[str, Any]:
        return {
            "version": self.version,
            "predicates": [p.name for p in self.predicates],
            "regression_cases": len(self.regression),
            "meta_weights": {s: round(self.weight(s), 2) for s in self.meta},
        }


def _compile_spec(spec: PredicateSpec) -> Verifier:
    """把声明式判据规格编译成纯函数。"""
    if spec.kind == "token":
        tokens = tuple(spec.params["tokens"])
        scopes = tuple(spec.params.get("scopes", ("chapter",)))

        def token_check(draft: Draft, ground_truth: GroundTruth) -> list[Diagnostic]:
            grounded = ground_truth.grounded_text()
            diags: list[Diagnostic] = []
            if "chapter" in scopes:
                for stage, sentences in draft.chapters.items():
                    for i, sentence in enumerate(sentences):
                        hits = [t for t in tokens if t in sentence.text and t not in grounded]
                        if hits:
                            diags.append(Diagnostic(
                                "AUTO.TOKEN", "block", Locus(stage, i), f"自造判据命中: {hits}",
                            ))
            if "agent" in scopes:
                for i, line in enumerate(draft.agent_lines):
                    hits = [t for t in tokens if t in line and t not in grounded]
                    if hits:
                        diags.append(Diagnostic(
                            "AUTO.TOKEN_AGENT", "block", Locus(ref=f"agent_line:{i}"),
                            f"自造判据命中对话行: {hits}",
                        ))
            return diags

        return token_check

    if spec.kind == "regex":
        pattern = re.compile(spec.params["pattern"])
        scopes = tuple(spec.params.get("scopes", ("chapter",)))

        def regex_check(draft: Draft, ground_truth: GroundTruth) -> list[Diagnostic]:
            diags: list[Diagnostic] = []
            texts: list[tuple[str, str]] = []
            if "chapter" in scopes:
                texts += [
                    (f"{stage}#{i}", s.text)
                    for stage, sentences in draft.chapters.items()
                    for i, s in enumerate(sentences)
                ]
            if "agent" in scopes:
                texts += [(f"agent#{i}", line) for i, line in enumerate(draft.agent_lines)]
            for locus, text in texts:
                if pattern.search(text):
                    diags.append(Diagnostic(
                        "AUTO.REGEX", "block", Locus(ref=locus),
                        f"自造正则判据命中: {spec.params['pattern']}",
                    ))
            return diags

        return regex_check

    raise ValueError(spec.kind)


# ---------------------------------------------------------------- 线上日志摄取
class LogIngestor:
    """把真实线上日志接进来；没有日志时可用模拟器跑通整条链路。"""

    def __init__(self, environment: Environment):
        self.env = environment

    def from_jsonl(self, path: str | Path) -> list[LogRecord]:
        records = []
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(LogRecord(**json.loads(line)))
        return records

    def absorb(self, records: list[LogRecord]) -> None:
        for record in records:
            if record.kind == "human_verdict":
                self.env.regression.append(LabeledCase(
                    record.text, record.where, record.accepted, "human_verdict",
                ))
            elif record.kind == "redteam_miss":
                self.env.regression.append(LabeledCase(
                    record.text, record.where, True, "redteam_miss",
                ))


# ---------------------------------------------------------------- 判据归纳（L1）
class PredicateInducer:
    """从失败里长出新判据候选——这是 agent 构造自己环境的核心动作。"""

    def induce(self, records: list[LogRecord], env: Environment) -> list[PredicateSpec]:
        failures = [r for r in records if not r.accepted]
        installed_tokens = {
            t for p in env.predicates if p.kind == "token"
            for t in p.params.get("tokens", [])
        }
        out: list[PredicateSpec] = []

        # 策略 1：从正文失败里抽词表
        chapter_tokens = sorted({r.detail for r in failures
                                 if r.where == "chapter" and r.detail
                                 and r.detail not in installed_tokens})
        if chapter_tokens:
            out.append(PredicateSpec(
                name=f"auto_token_chapter_{env.version + 1}",
                kind="token", params={"tokens": chapter_tokens, "scopes": ["chapter"]},
                strategy="token_lexicon",
                evidence=[r.session for r in failures if r.detail in chapter_tokens],
            ))

        # 策略 2：把词表判据的作用域扩到对话行
        agent_tokens = sorted({r.detail for r in failures
                               if r.where == "agent" and r.detail
                               and r.detail not in installed_tokens})
        if agent_tokens:
            out.append(PredicateSpec(
                name=f"auto_token_agent_{env.version + 1}",
                kind="token", params={"tokens": agent_tokens, "scopes": ["agent"]},
                strategy="scope_extension",
                evidence=[r.session for r in failures if r.detail in agent_tokens],
            ))

        # 策略 3：从年龄表达里归纳正则（含一条故意过宽的候选，交给回归筛）
        age_hits = [r for r in failures if "岁" in r.text]
        if age_hits:
            out.append(PredicateSpec(
                name=f"auto_regex_precise_{env.version + 1}",
                kind="regex", params={"pattern": r"[一二三四五六七八九十]\s*岁", "scopes": ["agent"]},
                strategy="precise_regex",
                evidence=[r.session for r in age_hits],
            ))
            out.append(PredicateSpec(
                name=f"auto_regex_broad_{env.version + 1}",
                kind="regex", params={"pattern": r"年", "scopes": ["agent"]},
                strategy="broad_regex",
                evidence=[r.session for r in age_hits],
            ))
        return out


# ---------------------------------------------------------------- 元学习（L2）
class MetaLearner:
    """改进「改进判据的方法」：被回归拒绝的策略权重会下降。"""

    def __init__(self, floor: float = 0.30):
        self.floor = floor

    def rank(self, candidates: list[PredicateSpec], env: Environment) -> list[PredicateSpec]:
        survivors = [c for c in candidates if env.weight(c.strategy) >= self.floor]
        return sorted(survivors, key=lambda c: env.weight(c.strategy), reverse=True)


# ---------------------------------------------------------------- 角色隔离
class IsolatedView:
    """每个角色只拿到自己该看的状态投影，防止「自己判自己」。"""

    def __init__(self, environment: Environment):
        self._env = environment

    def for_inducer(self) -> list[LogRecord]:
        return list(self._latest_records)

    def for_regression(self) -> list[LabeledCase]:
        return list(self._env.regression)

    def for_meta(self) -> dict[str, dict[str, int]]:
        return dict(self._env.meta)

    def for_evaluator(self) -> list[PredicateSpec]:
        return [PredicateSpec(**asdict(p)) for p in self._env.predicates]

    _latest_records: list[LogRecord] = []


# ---------------------------------------------------------------- 自组织 Agent
class SelfOrganizingAgent:
    """把上面所有零件组装成一个能自己造环境的开放系统。"""

    def __init__(self, environment: Environment | None = None):
        self.env = environment or Environment()
        self.ingestor = LogIngestor(self.env)
        self.inducer = PredicateInducer()
        self.meta = MetaLearner()
        self.view = IsolatedView(self.env)
        self.cycle_no = 0

    def cycle(self, logs: list[LogRecord]) -> dict[str, Any]:
        self.cycle_no += 1
        self.ingestor.absorb(logs)
        IsolatedView._latest_records = logs

        candidates = self.inducer.induce(self.view.for_inducer(), self.env)
        installed_keys = {p.key() for p in self.env.predicates}
        candidates = [c for c in candidates if c.key() not in installed_keys]
        ranked = self.meta.rank(candidates, self.env)

        installed = 0
        rollback = False
        for spec in ranked:
            candidate_set = list(self.env.predicates) + [spec]
            passed, _ = self.env.regression_check(candidate_set)
            before = len(self.env.predicates)
            accepted = self.env.install(spec, passed, spec.name)
            if accepted:
                installed += 1
            elif not passed and spec.strategy == "broad_regex":
                rollback = True
            assert len(self.env.predicates) >= before

        # 评估：新环境面对同样日志还剩多少漏网
        gaps = [
            r for r in logs
            if not r.accepted and not any(d.severity == "block" for d in self.env.check(
                Draft(agent_lines=[r.text]) if r.where == "agent" else
                Draft(chapters={"工作": [Sentence(r.text, ("k1",))]}),
                _lab_ground_truth(),
            ))
        ]
        vague_marks = ("说不清楚", "记不太真", "慢慢就过去了")
        novel_gaps = [r for r in gaps if not any(m in r.text for m in vague_marks)]
        human_flags = len(gaps) - len(novel_gaps)
        acceptance = installed / len(ranked) if ranked else 1.0
        metric = CycleMetric(
            cycle=self.cycle_no, version=self.env.version,
            predicates=len(self.env.predicates), acceptance=acceptance,
            attack_success=len(novel_gaps) / len(logs) if logs else 0.0,
            human_flags=human_flags, rollback=rollback,
        )
        self.env.metrics.append(metric)
        return asdict(metric)


# ---------------------------------------------------------------- 实验室依赖
def _lab_ground_truth() -> GroundTruth:
    spec = GroundTruth()
    spec.add_message(Message("a", "user", "voice", "1998年我在镇上的供销社上班，后来供销社就没了。"))
    spec.add_message(Message("b", "user", "voice", "小时候家里烧柴火，冬天冷得手都裂了。"))
    spec.ingest_claim(Claim("k1", "1998年我在镇上的供销社上班。", "镇上的供销社", "a", "工作"))
    spec.ingest_claim(Claim("k3", "小时候家里烧柴火。", "烧柴火", "b", "童年"))
    return spec


def simulate_session(session: int, n: int = 8) -> list[LogRecord]:
    """模拟四类线上会话：正文新词、对话行新词、年龄正则、不可约模糊句。"""
    pools = {
        0: [("1998年我在镇上的供销社上班，那时候有台收音机。", "chapter", "收音机"),
            ("1998年我在镇上的供销社上班，那时候有台缝纫机。", "chapter", "缝纫机")],
        1: [("那时候柜台边放着自行车，您还记得吗？", "agent", "自行车"),
            ("那时候柜台边放着老照片，您还记得吗？", "agent", "老照片")],
        2: [("七岁那年家里穷，您听老人说过吗？", "agent", ""),
            ("八岁那年家里穷，您听老人说过吗？", "agent", "")],
        3: [("那会儿日子苦，有些事说不清楚了。", "chapter", ""),
            ("总之是很久以前的事了，记不太真。", "chapter", "")],
    }
    src = pools[session % 4]
    records: list[LogRecord] = []
    for i in range(n):
        text, where, detail = src[i % len(src)]
        kind = "redteam_miss" if session % 4 != 3 else "vague"
        records.append(LogRecord(
            kind=kind, text=text, where=where, detail=detail,
            accepted=False, session=f"s{session}",
        ))
    if session % 4 == 3:
        records.append(LogRecord(
            kind="human_verdict", text="1998年我在镇上的供销社上班。",
            where="chapter", accepted=True, session=f"s{session}",
        ))
    return records


def report(agent: SelfOrganizingAgent) -> None:
    print("=" * 92)
    print("开放自组织 Agent：环境由 agent 自己构造")
    print("=" * 92)
    print(f"{'轮次':>4}{'环境版本':>10}{'判据数':>8}{'采纳率':>9}"
          f"{'漏网率':>9}{'交人工':>8}{'拒绝过宽判据':>14}")
    for m in agent.env.metrics:
        print(f"{m.cycle:>4}{m.version:>10}{m.predicates:>8}{m.acceptance:>9.0%}"
              f"{m.attack_success:>9.0%}{m.human_flags:>8}"
              f"{'是' if m.rollback else '-':>14}")
    summary = agent.env.summary()
    print(f"\n  最终环境版本 v{summary['version']}，自造判据 {len(summary['predicates'])} 条")
    print(f"  判据: {summary['predicates']}")
    print(f"  元层策略权重: {summary['meta_weights']}")
    print("\n  三层递归: L0 修内容 → L1 造判据 → L2 改进行判据的方法。")
    print("  环境不是输入，而是 agent 的产出。")


def main() -> None:
    from .evidence_scope import emit; emit("autopoiesis")
    agent = SelfOrganizingAgent()
    for session in range(11):
        agent.cycle(simulate_session(session))
    report(agent)

    path = "/workspace/.svl_env.json"
    agent.env.save(path)
    reloaded = SelfOrganizingAgent(Environment.load(path))
    print(f"\n跨会话持久化: 保存到 {path} 后重载，"
          f"环境版本 v{reloaded.env.version}，判据 {len(reloaded.env.predicates)} 条")
    blocked = 0
    for record in simulate_session(0)[:2]:
        draft = Draft(chapters={"工作": [Sentence(record.text, ("k1",))]})
        if any(d.severity == "block" for d in reloaded.env.check(draft, _lab_ground_truth())):
            blocked += 1
    print(f"  重载后仍能挡住旧攻击: {blocked}/2")

    # 演示回滚：一条会误杀安全句的过宽判据必须被门禁挡下
    bad = PredicateSpec(
        name="bad_overbroad", kind="regex",
        params={"pattern": "年", "scopes": ["chapter"]}, strategy="broad_regex",
    )
    passed, why = reloaded.env.regression_check(list(reloaded.env.predicates) + [bad])
    print(f"  过宽判据门禁: {'通过' if passed else '拒绝'}（{why}）")


if __name__ == "__main__":
    main()
