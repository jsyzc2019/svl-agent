"""沿 Code Agent 演化路径推进：判据自举 + 对抗红队 → 自我改进闭环。

Code Agent 的演化不是「模型更聪明」，而是环境判据越来越完整：
  编译器 → 测试 → CI 回归 → 红队/模糊测试 → 从缺陷里长出新判据。
本模块把同样的演化路径搬进叙事场景：

  阶段 A 判据自举：把「核对原话」的人工裁决变成标注，学出符号级规则，
          用来给核对卡排序（人先看最可能假的），并当回归测试锁住判据。
  阶段 B 对抗红队：自动生成专门绕过现有判据的造假样本，测出盲区，
          从漏网样本里长出新判据，再复测攻击成功率。
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .core import (
    Claim, Draft, GroundTruth, Locus, Message, Sentence, Diagnostic,
    strip_punctuation,
)
from .verifiers import (
    chapter_whitelist, claim_reference_valid, concrete_grounded,
    concrete_markers, first_person_boundary, default_verifiers,
)


# ---------------------------------------------------------------- 实验室判据源
def lab_spec() -> GroundTruth:
    spec = GroundTruth()
    spec.add_message(Message("a", "user", "voice", "1998年我在镇上的供销社上班，后来供销社就没了。"))
    spec.add_message(Message("b", "user", "voice", "小时候家里烧柴火，冬天冷得手都裂了。"))
    for claim in (
        Claim("k1", "1998年我在镇上的供销社上班。", "镇上的供销社", "a", "工作"),
        Claim("k2", "后来供销社就没了。", "后来供销社就没了", "a", "工作"),
        Claim("k3", "小时候家里烧柴火。", "烧柴火", "b", "童年"),
    ):
        spec.ingest_claim(claim)
    return spec


# ---------------------------------------------------------------- 对抗样本
@dataclass
class Attack:
    text: str
    where: str        # "chapter" 或 "agent"
    fabricated: bool  # 是否真的含凭空细节（由生成器已知，作为金标）
    detail: str = ""  # 凭空细节的字面串，补丁从它长出来


def make_attacks(rng: random.Random, n: int = 240) -> list[Attack]:
    """六类样本：长短安全句 + 长短造假 + 对话行造假，长度与真假故意交叠。"""
    templates = [
        ("1998年我在镇上的供销社上班。", "chapter", False, ""),
        ("1998年我在镇上的供销社上班，后来供销社就没了。", "chapter", False, ""),
        ("我七岁。", "chapter", True, "七岁"),
        ("老收音机。", "chapter", True, "收音机"),
        ("1998年我在镇上的供销社上班，那时候我七岁。", "chapter", True, "七岁"),
        ("那时候柜台后面有台老收音机，您还记得吗？", "agent", True, "收音机"),
    ]
    attacks = [
        Attack(text, where, fabricated, detail)
        for i in range(n)
        for text, where, fabricated, detail in [templates[i % len(templates)]]
    ]
    rng.shuffle(attacks)
    return attacks


def to_draft(attack: Attack) -> Draft:
    if attack.where == "chapter":
        return Draft(chapters={"工作": [Sentence(attack.text, ("k1",))]})
    return Draft(agent_lines=[attack.text])


def block_count(verifiers, spec: GroundTruth, attack: Attack) -> int:
    draft = to_draft(attack)
    return sum(
        d.severity == "block"
        for v in verifiers
        for d in v(draft, spec)
    )


# ---------------------------------------------------------------- 阶段 A：判据自举
@dataclass
class Features:
    length: float
    markers: float
    unmatched: float
    digits: float
    has_quote: float
    where_agent: float

    def vector(self) -> tuple[float, ...]:
        return (self.length, self.markers, self.unmatched,
                self.digits, self.has_quote, self.where_agent)


FEATURE_NAMES = ("length", "markers", "unmatched", "digits", "has_quote", "where_agent")


def extract(spec: GroundTruth, attack: Attack) -> Features:
    markers = concrete_markers(attack.text)
    grounded = spec.grounded_text()
    return Features(
        length=float(len(attack.text)),
        markers=float(len(markers)),
        unmatched=float(sum(1 for m in markers if m not in grounded)),
        digits=float(sum(c.isdigit() for c in attack.text)),
        has_quote=float(any(q in attack.text for q in ('"', "「", "“"))),
        where_agent=float(attack.where == "agent"),
    )


@dataclass
class Rule:
    feature: str
    threshold: float
    direction: int      # +1: 大于等于阈值判假；-1: 小于等于阈值判假
    train_acc: float

    def predicts_fake(self, f: Features) -> bool:
        value = getattr(f, self.feature)
        return value >= self.threshold if self.direction > 0 else value <= self.threshold


def learn_stump(items: list[tuple[Features, bool]]) -> Rule:
    """从人工裁决里学一条符号级规则。

    优化目标不是准确率而是「排序提升」：人只看前 20% 的卡时，能比随机多看多少伪造。
    ——这是判据自举真正要优化的指标：人工效率，而不是统计漂亮。
    """
    base_rate = sum(not accepted for _, accepted in items) / len(items)
    top_n = max(1, len(items) // 5)

    def score(name: str, threshold: float, direction: int) -> tuple[float, float]:
        flagged = []
        for feat, accepted in items:
            value = getattr(feat, name)
            pred = value >= threshold if direction > 0 else value <= threshold
            flagged.append((pred, not accepted))
        # 按 flag 优先排序后取前 top_n
        ordered = sorted(flagged, key=lambda x: x[0], reverse=True)[:top_n]
        caught = sum(1 for pred, fake in ordered if pred and fake)
        lift = (caught / top_n) / base_rate if base_rate else 0.0
        acc = sum(1 for pred, fake in flagged if pred == fake) / len(items)
        return lift, acc

    best: Rule | None = None
    best_score = -1.0
    for name in FEATURE_NAMES:
        values = sorted({getattr(f, name) for f, _ in items})
        if len(values) < 2:
            continue
        thresholds = [(a + b) / 2 for a, b in zip(values, values[1:])]
        for threshold in thresholds:
            for direction in (1, -1):
                lift, acc = score(name, threshold, direction)
                better = (
                    lift > best_score + 1e-9
                    or (abs(lift - best_score) <= 1e-9 and best is not None and acc > best.train_acc)
                )
                if better:
                    best_score = lift
                    best = Rule(name, threshold, direction, acc)
    assert best is not None
    return best


def evaluate_rule(rule: Rule, items: list[tuple[Features, bool]]) -> dict:
    tp = fp = tn = fn = 0
    for f, accepted in items:
        predicted_fake = rule.predicts_fake(f)
        if predicted_fake and not accepted:
            tp += 1
        elif predicted_fake and accepted:
            fp += 1
        elif not predicted_fake and accepted:
            tn += 1
        else:
            fn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    base_rate = (tp + fn) / len(items)
    top = sorted(items, key=lambda x: rule.predicts_fake(x[0]), reverse=True)[:max(1, len(items) // 5)]
    top_caught = sum(1 for f, accepted in top if not accepted) / len(top)
    return {
        "precision": precision, "recall": recall,
        "base_rate": base_rate, "top20_catch": top_caught,
    }


# ---------------------------------------------------------------- 阶段 B：红队长出的新判据
def patched_verifiers(discovered: set[str]):
    """从漏网样本里长出的补丁：任何凭空细节只要出现在对话行里，也按正文同样核对。"""
    def agent_detail_grounded(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
        grounded = spec.grounded_text()
        diags = []
        for i, line in enumerate(draft.agent_lines):
            markers = concrete_markers(line)
            leaked = [m for m in markers if m not in grounded]
            leaked += [d for d in discovered if d in line and d not in grounded]
            if leaked:
                diags.append(Diagnostic(
                    "AGENT.DETAIL_LEAK", "block", Locus(ref=f"agent_line:{i}"),
                    f"对话行出现无凭证细节: {sorted(set(leaked))}",
                ))
        return diags

    def known_detail_block(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
        """把红队发现的未知名词纳入词表——本质是把标注变成判据。"""
        grounded = spec.grounded_text()
        diags = []
        for stage, sentences in draft.chapters.items():
            for i, sentence in enumerate(sentences):
                hits = [d for d in discovered if d in sentence.text and d not in grounded]
                if hits:
                    diags.append(Diagnostic(
                        "EVIDENCE.REDTEAM_HIT", "block", Locus(stage, i),
                        f"命中红队词表: {hits}",
                    ))
        return diags

    return default_verifiers() + [agent_detail_grounded, known_detail_block]


# ---------------------------------------------------------------- 驱动
def main() -> None:
    rng = random.Random(20261121)
    spec = lab_spec()
    attacks = make_attacks(rng)

    print("=" * 78)
    print("阶段 A：判据自举——把人工裁决变成可排序、可回归的符号规则")
    print("=" * 78)
    features = [(extract(spec, a), not a.fabricated) for a in attacks]
    rng.shuffle(features)
    split = int(len(features) * 0.7)
    train, test = features[:split], features[split:]
    rule = learn_stump(train)
    m = evaluate_rule(rule, test)
    print(f"  学到的规则: 若 {rule.feature} "
          f"{'≥' if rule.direction > 0 else '≤'} {rule.threshold:.1f} → 优先判假")
    print(f"  训练集准确率: {rule.train_acc:.1%}")
    print(f"  测试集 precision={m['precision']:.1%}, recall={m['recall']:.1%}")
    print(f"  伪造基准率={m['base_rate']:.1%} → 按规则排序后前 20% 卡片的伪造率={m['top20_catch']:.1%}")
    print(f"  人工效率提升: 同样看 20% 的卡，抓到的伪造多 "
          f"{m['top20_catch'] / m['base_rate'] - 1:+.0%}")

    print("\n" + "=" * 78)
    print("阶段 B：对抗红队——先找盲区，再从漏网样本长出新判据")
    print("=" * 78)
    base = default_verifiers()
    passed_before = [a for a in attacks if a.fabricated and block_count(base, spec, a) == 0]
    discovered = {a.detail for a in passed_before if a.detail}
    print(f"  攻击总数={len(attacks)}, 真实造假={sum(a.fabricated for a in attacks)}")
    print(f"  基线漏网={len(passed_before)} "
          f"(攻击成功率={len(passed_before) / sum(a.fabricated for a in attacks):.1%})")
    print(f"  从漏网样本提取的新证据词: {sorted(discovered)}")

    patched = patched_verifiers(discovered)
    passed_after = [a for a in attacks if a.fabricated and block_count(patched, spec, a) == 0]
    print(f"  补丁后漏网={len(passed_after)} "
          f"(攻击成功率={len(passed_after) / sum(a.fabricated for a in attacks):.1%})")
    print(f"  净化率: {1 - len(passed_after) / max(1, len(passed_before)):.1%}")

    print("\n" + "=" * 78)
    print("演化总结")
    print("=" * 78)
    print("  编译器/测试 → 闸门+兜底 → 诊断+受约束返工 → 判据自举 → 对抗红队 → 新判据回归")
    print("  每一步都不是模型变聪明，而是判据环境变完整。")


if __name__ == "__main__":
    main()
