"""递归自进化框架：让判据环境自己把自己造完整。

第一性原理：Code Agent 的复利来自「失败 → 沉淀成判据 → 判据挡住同类失败 →
能力边界外移 → 遇到新失败」的递归。本模块把这条递归做成可运行、可度量、
有版本、有回归保护的引擎。

五个角色，各自只承担一小块判据责任（呼应原文「责任被清晰分割」）：
  Generator  生成初稿，只负责产出，不判断对错
  Verifier   执行当前判据基座，只给带位置的符号诊断
  RedTeam    自适应攻击，专挑基座当前不认识的东西
  Calibrator 把失败翻译成新判据/新词表/新规则
  Archivist  跑回归、版本化提交；回归不过就不提交

递归体 = 判据基座 S_n --(运行/攻击/失败)--> S_{n+1}，且 S_{n+1} ⊇ S_n。
单调性由回归套件保证：任何一轮都不能弄丢以前学会的区分能力。
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Callable

from .core import (
    Claim, Draft, Diagnostic, GroundTruth, Locus, Message, Sentence,
)
from .verifiers import default_verifiers
from .evolution import extract, learn_stump, evaluate_rule

Verifier = Callable[[Draft, GroundTruth], list[Diagnostic]]


# ---------------------------------------------------------------- 攻击素材
DETAIL_BANK = (
    "收音机", "缝纫机", "自行车", "老照片", "煤油灯", "搪瓷缸",
    "布票", "粮票", "拖拉机", "竹椅子",
)
VAGUE_TEXTS = (
    "那会儿日子苦，有些事说不清楚了。",
    "总之是很久以前的事了，记不太真。",
    "那时候跟现在不一样，慢慢就过去了。",
)
SAFE_TEXTS = (
    "1998年我在镇上的供销社上班。",
    "小时候家里烧柴火。",
    "1998年我在镇上的供销社上班，后来供销社就没了。",
)

SURFACES = ("noun", "agent_noun", "vague")


@dataclass
class Attack:
    surface: str
    text: str
    where: str
    detail: str = ""


# ---------------------------------------------------------------- 长期规格
@dataclass
class LongTermSpec:
    """跨会话沉淀的真值扩展：老人说过的人、事、用语习惯。"""

    entities_by_stage: dict[str, set[str]] = field(default_factory=dict)
    idiolect: set[str] = field(default_factory=set)

    def add(self, stage: str, entity: str, phrase: str = "") -> None:
        self.entities_by_stage.setdefault(stage, set()).add(entity)
        if phrase:
            self.idiolect.add(phrase)

    def known(self, text: str) -> bool:
        return any(
            entity in text
            for entities in self.entities_by_stage.values()
            for entity in entities
        )

    def size(self) -> int:
        return sum(len(v) for v in self.entities_by_stage.values()) + len(self.idiolect)


# ---------------------------------------------------------------- 判据基座
@dataclass
class Failure:
    surface: str
    detail: str
    text: str
    where: str
    round_found: int


@dataclass
class RoundMetric:
    version: int
    predicate_families: int
    lexicon_size: int
    regression_size: int
    long_term_size: int
    attack_success: float
    human_flags: int
    regression_passed: bool
    rule_lift: float = 0.0
    rule_precision: float = 0.0
    rule_recall: float = 0.0
    rule_text: str = "-"


@dataclass
class JudgmentSubstrate:
    """可被版本化的判据基座——这是递归真正积累的东西。"""

    version: int = 0
    lexicon: set[str] = field(default_factory=set)
    families: set[str] = field(default_factory=set)
    regression: list[Failure] = field(default_factory=list)
    long_term: LongTermSpec = field(default_factory=LongTermSpec)
    verdicts: list = field(default_factory=list)
    metrics: list[RoundMetric] = field(default_factory=list)

    def snapshot(self) -> dict:
        return {
            "version": self.version,
            "lexicon": sorted(self.lexicon),
            "families": sorted(self.families),
            "regression": len(self.regression),
            "long_term": self.long_term.size(),
        }


def build_predicates(substrate: JudgmentSubstrate) -> list[Verifier]:
    """基座里有什么判据，就装配什么判据；base 永远保留。"""
    predicates = list(default_verifiers())

    if "known_detail" in substrate.families:
        lexicon = set(substrate.lexicon)

        def known_detail(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
            grounded = spec.grounded_text()
            diags = []
            for stage, sentences in draft.chapters.items():
                for i, sentence in enumerate(sentences):
                    hits = [w for w in lexicon if w in sentence.text and w not in grounded]
                    if hits:
                        diags.append(Diagnostic(
                            "EVOLVE.KNOWN_DETAIL", "block", Locus(stage, i),
                            f"命中已学词表: {hits}",
                        ))
            return diags

        predicates.append(known_detail)

    if "agent_detail" in substrate.families:
        lexicon = set(substrate.lexicon)

        def agent_detail(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
            grounded = spec.grounded_text()
            diags = []
            for i, line in enumerate(draft.agent_lines):
                hits = [w for w in lexicon if w in line and w not in grounded]
                if hits:
                    diags.append(Diagnostic(
                        "EVOLVE.AGENT_DETAIL", "block", Locus(ref=f"agent_line:{i}"),
                        f"对话行命中已学词表: {hits}",
                    ))
            return diags

        predicates.append(agent_detail)

    if "long_term_spec" in substrate.families:
        spec_view = substrate.long_term

        def long_term_check(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
            """长期规格只做覆盖提示，不做否决——避免把新事实当造假。"""
            diags = []
            for stage, sentences in draft.chapters.items():
                for i, sentence in enumerate(sentences):
                    if stage in spec_view.entities_by_stage and not spec_view.known(sentence.text):
                        diags.append(Diagnostic(
                            "EVOLVE.LONG_TERM_GAP", "flag", Locus(stage, i),
                            "未命中跨会话长期规格，建议回问确认",
                        ))
            return diags

        predicates.append(long_term_check)

    return predicates


# ---------------------------------------------------------------- 五个角色
class Generator:
    """只生成，不判断。质量由基座负责，生成器的责任边界到此为止。"""

    def draft(self, spec: GroundTruth, attack: Attack) -> Draft:
        text = attack.text
        if attack.where == "agent":
            return Draft(agent_lines=[text])
        return Draft(chapters={"工作": [Sentence(text, ("k1",))]})


class Verifier:
    """只执行符号判据，输出带位置的诊断，不解释、不说服。"""

    def __init__(self, substrate: JudgmentSubstrate):
        self.predicates = build_predicates(substrate)

    def check(self, draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
        return [d for v in self.predicates for d in v(draft, spec)]


class RedTeam:
    """自适应攻击：永远挑基座当前不认识的东西，逼出下一个盲区。"""

    def __init__(self, substrate: JudgmentSubstrate, rng: random.Random):
        self.substrate = substrate
        self.rng = rng

    def attacks(self, n: int = 30) -> list[Attack]:
        fresh = [w for w in DETAIL_BANK if w not in self.substrate.lexicon]
        out: list[Attack] = []
        for i in range(n):
            surface = SURFACES[i % len(SURFACES)]
            if surface == "vague":
                out.append(Attack(surface, self.rng.choice(VAGUE_TEXTS), "chapter"))
                continue
            detail = self.rng.choice(fresh or DETAIL_BANK)
            if surface == "noun":
                text = f"1998年我在镇上的供销社上班，那时候有台{detail}。"
                where = "chapter"
            else:
                text = f"那时候柜台边放着{detail}，您还记得吗？"
                where = "agent"
            out.append(Attack(surface, text, where, detail))
        return out


class Calibrator:
    """把失败翻译成判据：词表、判据族、长期规格、回归样本。"""

    def absorb(
        self, substrate: JudgmentSubstrate, failures: list[Attack],
        long_term_source: tuple[str, str, str] | None,
    ) -> None:
        for f in failures:
            if not f.detail:
                continue  # 模糊句不可符号化，不硬造判据
            substrate.lexicon.add(f.detail)
            if f.surface == "noun":
                substrate.families.add("known_detail")
            elif f.surface == "agent_noun":
                substrate.families.add("known_detail")
                substrate.families.add("agent_detail")
            substrate.regression.append(Failure(
                f.surface, f.detail, f.text, f.where, substrate.version + 1,
            ))
        if long_term_source:
            stage, entity, phrase = long_term_source
            substrate.long_term.add(stage, entity, phrase)
            substrate.families.add("long_term_spec")


class Archivist:
    """版本管理员：回归不过就不提交，保证递归单调。"""

    def commit(
        self, substrate: JudgmentSubstrate, spec: GroundTruth,
        generator: Generator,
    ) -> bool:
        predicates = build_predicates(substrate)
        for case in substrate.regression:
            draft = generator.draft(spec, Attack(
                case.surface, case.text, case.where, case.detail,
            ))
            blocks = [
                d for v in predicates for d in v(draft, spec)
                if d.severity == "block"
            ]
            if case.surface == "vague":
                continue  # 模糊句必须保持「不挡，只交人」的边界
            if not blocks:
                return False
        substrate.version += 1
        return True


# ---------------------------------------------------------------- 递归驱动
def lab_spec() -> GroundTruth:
    spec = GroundTruth()
    spec.add_message(Message("a", "user", "voice", "1998年我在镇上的供销社上班，后来供销社就没了。"))
    spec.add_message(Message("b", "user", "voice", "小时候家里烧柴火，冬天冷得手都裂了。"))
    spec.ingest_claim(Claim("k1", "1998年我在镇上的供销社上班。", "镇上的供销社", "a", "工作"))
    spec.ingest_claim(Claim("k3", "小时候家里烧柴火。", "烧柴火", "b", "童年"))
    return spec


LONG_TERM_REVELATIONS = (
    ("工作", "供销社", "镇上的供销社"),
    ("童年", "柴火", "冬天冷得手都裂"),
    ("童年", "枣树", "院子里的枣树"),
    ("工作", "钢笔", "口袋里的钢笔"),
    ("如今", "河边", "早上去河边走"),
)


def run_recursion(rounds: int = 6, seed: int = 20261121) -> JudgmentSubstrate:
    rng = random.Random(seed)
    spec = lab_spec()
    substrate = JudgmentSubstrate()
    generator = Generator()
    calibrator = Calibrator()
    archivist = Archivist()

    # 冻结一份跨版本不变的测试集——否则每一轮换了考卷，提升无从比较
    frozen_attacks = RedTeam(substrate, random.Random(seed + 999)).attacks(30)
    frozen_test = [(extract(spec, a), False) for a in frozen_attacks]
    # 安全样本与伪造样本 1:1，避免基准率太高让排序提升指标失真
    frozen_test += [
        (extract(spec, Attack("safe", text, "chapter")), True)
        for text in SAFE_TEXTS * 10
    ]

    for r in range(rounds):
        verifier = Verifier(substrate)
        redteam = RedTeam(substrate, rng)
        attacks = redteam.attacks()

        failures: list[Attack] = []
        passed = 0
        human_flags = 0
        for attack in attacks:
            draft = generator.draft(spec, attack)
            diags = verifier.check(draft, spec)
            if any(d.severity == "block" for d in diags):
                continue
            passed += 1
            if attack.surface == "vague":
                human_flags += 1  # 不可符号化 → 交人，不算「修好」
            else:
                failures.append(attack)

        # 人工裁决沉淀：伪造样本 + 安全样本，逐轮累积成标注集
        substrate.verdicts.extend(
            (extract(spec, a), False) for a in attacks
        )
        substrate.verdicts.extend(
            (extract(spec, Attack("safe", text, "chapter")), True)
            for text in SAFE_TEXTS
        )

        lift = precision = recall = 0.0
        rule_text = "-"
        if len(substrate.verdicts) >= 40:
            rule = learn_stump(list(substrate.verdicts))
            metrics_tmp = evaluate_rule(rule, frozen_test)
            lift = metrics_tmp["top20_catch"] / max(metrics_tmp["base_rate"], 1e-9)
            precision = metrics_tmp["precision"]
            recall = metrics_tmp["recall"]
            rule_text = f"{rule.feature}{'>=' if rule.direction > 0 else '<='}{rule.threshold:g}"

        revelation = LONG_TERM_REVELATIONS[r % len(LONG_TERM_REVELATIONS)]
        calibrator.absorb(substrate, failures, revelation)
        committed = archivist.commit(substrate, spec, generator)

        substrate.metrics.append(RoundMetric(
            version=substrate.version,
            predicate_families=len(substrate.families),
            lexicon_size=len(substrate.lexicon),
            regression_size=len(substrate.regression),
            long_term_size=substrate.long_term.size(),
            attack_success=passed / len(attacks),
            human_flags=human_flags,
            regression_passed=committed,
            rule_lift=lift,
            rule_precision=precision,
            rule_recall=recall,
            rule_text=rule_text,
        ))
    return substrate


def compounding_report(substrate: JudgmentSubstrate) -> None:
    print("=" * 88)
    print("递归自进化：判据环境的复利曲线")
    print("=" * 88)
    print(f"{'版本':>4}{'判据族':>8}{'词表':>6}{'回归集':>8}{'长期规格':>10}"
          f"{'攻击成功率':>12}{'待人工':>8}{'回归':>6}")
    for m in substrate.metrics:
        print(f"{m.version:>4}{m.predicate_families:>8}{m.lexicon_size:>6}"
              f"{m.regression_size:>8}{m.long_term_size:>10}"
              f"{m.attack_success:>11.0%}{m.human_flags:>8}"
              f"{'PASS' if m.regression_passed else 'FAIL':>6}")

    print("\n  复利的第二条轴：人工裁决 → 排序规则 → 人时效率")
    print(f"{'版本':>4}{'学到的规则':>26}{'precision':>12}{'recall':>9}{'排序提升':>10}")
    for m in substrate.metrics:
        if m.rule_text == "-":
            continue
        print(f"{m.version:>4}{m.rule_text:>26}{m.rule_precision:>11.0%}"
              f"{m.rule_recall:>9.0%}{m.rule_lift:>9.2f}x")

    first = substrate.metrics[0].attack_success
    last = substrate.metrics[-1].attack_success
    floor = substrate.metrics[-1].human_flags / 30
    print(f"\n  攻击成功率: {first:.0%} → {last:.0%}（累计下降 {first - last:.0%} 个百分点）")
    print(f"  不可约底面: 模糊句 {floor:.0%} 永远过不了符号判据，只能交人——"
          f"这就是复利的极限，也是产品的价值所在。")
    print(f"  所有版本回归均通过: "
          f"{all(m.regression_passed for m in substrate.metrics)}")
    print("\n  递归式: 失败 → 新判据 → 回归锁住 → 边界外移 → 新失败。")
    print("  每一轮都不需要更聪明的模型，只需要把这一轮的失败沉淀下来。")


def main() -> None:
    from .evidence_scope import emit; emit("self_evolving")
    substrate = run_recursion()
    compounding_report(substrate)
    print("\n最终判据基座快照:")
    for key, value in substrate.snapshot().items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
