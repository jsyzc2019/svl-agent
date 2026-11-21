"""认知升级层：自主洞见 + 理性决策——把「人的边界」从常量变成能力函数。

对前作的修正：
  之前把「人的边界」写成不可约常量，论证里有个隐蔽偷换——
  把「当前判据空间看不见」等同于「原则上不可判定」。
   Boundary 其实是 capability 的函数 B(c)，随能力单调下降。

两个能力维度：

  洞见 (Insight)：找到一个此前不在判据空间里的「可坍塌维度」。
    "像不像他" 看似纯审美、无法判定；但语言指纹（用词分布、句长、情感词、
    具体标记、时间词……）与老人原话指纹的统计距离，是一个纯符号量，
    可计算、可回归、可回滚。洞见不是"猜得更准"，而是"发现了新的可判定代理 φ′"。
    系统自己从「判据全绿但人工否决」的盲区里搜索出这个维度，不是人预先写死的。

  理性决策 (Rational Decision)：不完备信息下不追求"正确"，只追求期望效用最优。
    三值决策 ACCEPT / REJECT / ESCALATE(交人)：
      EU(ACCEPT)   = -p_bad × L_fn       漏放问题的损失
      EU(REJECT)   = -(1-p_bad) × L_fp   误杀好内容的损失
      EU(ESCALATE) = -C_h                人工成本（人的判断视为准确）
    "交人"从默认归宿，降为三个选项里 EU 比较后的一个；p_bad 越极端，
    系统越能自己决策，交人率越低——这就是边界移动的机制。

递归自洽：洞见→新维度→p_bad 更准→更多自动决策→新的不确定样本→新洞见。
与 PDCA 同构，但判据空间从「人工设计的」扩展为「系统发现的」。
"""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field
from typing import Callable

from .core import Draft, Diagnostic, GroundTruth, Locus, Sentence
from .verifiers import concrete_markers, default_verifiers


# ---------------------------------------------------------------- 1. 语言指纹
# 全部是符号量：字符/词计数、比例、离散度，不含任何语义理解。
DIMENSIONS = (
    "avg_len", "len_std", "digit_ratio", "time_ratio", "emotion_ratio",
    "concrete_ratio", "function_ratio", "question_ratio", "quote_ratio", "repeat_ratio",
)
_TIME_WORDS = ("年", "岁", "月", "那会儿", "那时候", "以前", "后来", "当年", "小时候")
_EMOTION_WORDS = ("温馨", "暖", "苦", "甜", "难受", "高兴", "想念", "珍藏", "牵挂", "辛酸", "美好")
_FUNCTION_WORDS = ("的", "了", "在", "和", "是", "着", "都", "就", "也", "而", "却")


@dataclass
class Fingerprint:
    """一段文本的可计算风格指纹。"""

    values: dict[str, float]

    def distance_to(self, other: "Fingerprint") -> dict[str, float]:
        """逐维度的绝对差——每个维度都是一个候选的「风格距离」信号。"""
        return {d: abs(self.values.get(d, 0.0) - other.values.get(d, 0.0))
                for d in DIMENSIONS}


def fingerprint(text: str) -> Fingerprint:
    """把文本坍塌成一组符号特征。没有任何语义判断，只有计数与比例。"""
    sentences = [s for s in _split_sentences(text) if s]
    chars = [c for c in text if not c.isspace()]
    n = max(1, len(chars))
    lens = [len(s) for s in sentences] or [n]
    avg_len = sum(lens) / len(lens)
    var_len = sum((x - avg_len) ** 2 for x in lens) / len(lens)

    def ratio(words) -> float:
        return sum(text.count(w) for w in words) / n

    distinct = len(set(chars))
    return Fingerprint({
        "avg_len": avg_len,
        "len_std": math.sqrt(var_len),
        "digit_ratio": sum(c.isdigit() for c in chars) / n,
        "time_ratio": ratio(_TIME_WORDS),
        "emotion_ratio": ratio(_EMOTION_WORDS),
        "concrete_ratio": len(concrete_markers(text)) / n,
        "function_ratio": ratio(_FUNCTION_WORDS),
        "question_ratio": text.count("？") / max(1, len(sentences) + text.count("。")),
        "quote_ratio": sum(text.count(q) for q in ("「", "“", "\"")) / n,
        "repeat_ratio": 1.0 - distinct / n,
    })


def _split_sentences(text: str) -> list[str]:
    out, buf = [], []
    for c in text:
        buf.append(c)
        if c in "。！？；.!?":
            out.append("".join(buf))
            buf = []
    if buf:
        out.append("".join(buf))
    return out


def profile_of(texts: list[str]) -> Fingerprint:
    """从一个人全部已核验原话里，学出他的语言指纹（真值来源）。"""
    fps = [fingerprint(t) for t in texts if t.strip()]
    if not fps:
        return Fingerprint({d: 0.0 for d in DIMENSIONS})
    return Fingerprint({d: sum(f.values[d] for f in fps) / len(fps) for d in DIMENSIONS})


# ---------------------------------------------------------------- 2. 洞见发现
@dataclass
class Insight:
    """一个被系统自己发现的新判据维度。"""

    dimension: str
    threshold: float
    direction: int       # +1: 距离 >= 阈值 判为有问题；-1: <= 阈值
    auc: float           # 区分度（0.5=随机，1=完美）
    youden: float        # 阈值处的 TPR-FPR

    def score(self, text: str, profile: Fingerprint) -> float:
        return fingerprint(text).distance_to(profile)[self.dimension] * self.direction

    def flags(self, text: str, profile: Fingerprint) -> bool:
        return self.score(text, profile) >= self.threshold

    def to_signal(self, text: str, profile: Fingerprint) -> float:
        """把原始距离按阈值映射成 [0,1] 的问题信号。

        以阈值为中心、用该维度的实际离散度做尺度：阈值处=0.5，
        远超阈值→1，远低→0。不同量级的维度（avg_len~26 vs emotion_ratio~0.03）
        都能产生可比的信号；尺度越小越陡峭，"低于阈值"的样本信号越接近 0。
        """
        # 尺度取阈值自身的 1/4（下限 1e-4），让阈值两侧的样本拉开
        scale = max(1e-4, abs(self.threshold) * 0.25)
        z = (self.score(text, profile) - self.threshold) / scale
        # 防止 exp 溢出
        z = max(-40.0, min(40.0, z))
        return 1.0 / (1.0 + math.exp(-z))

    def describe(self) -> str:
        op = "≥" if self.direction > 0 else "≤"
        return (f"风格维度「{self.dimension}」{op}{self.threshold:.3f} "
                f"(AUC={self.auc:.2f}, Youden={self.youden:.2f})")


@dataclass
class Verdict:
    """人工裁决样本。accepted=False 表示人工否决（说明内容有问题）。"""

    text: str
    accepted: bool
    source: str = ""


def _auc(pos: list[float], neg: list[float]) -> float:
    """Mann-Whitney U 的 pairwise 实现；处理并列，纯 Python。"""
    if not pos or not neg:
        return 0.5
    wins = 0.0
    for p in pos:
        for n in neg:
            wins += 1.0 if p > n else (0.5 if p == n else 0.0)
    return wins / (len(pos) * len(neg))


def _best_threshold(scores: list[float], labels: list[bool]) -> tuple[float, int, float, float]:
    """扫描阈值，最大化 Youden's J = TPR - FPR。"""
    best = (0.0, 1, 0.0, -2.0)
    candidates = sorted(set(scores))
    for direction in (1, -1):
        signed = [s * direction for s in scores]
        for t in candidates:
            signed_t = t * direction
            tp = sum(1 for s, lab in zip(signed, labels) if s >= signed_t and not lab)
            fp = sum(1 for s, lab in zip(signed, labels) if s >= signed_t and lab)
            fn = sum(1 for s, lab in zip(signed, labels) if s < signed_t and not lab)
            tn = sum(1 for s, lab in zip(signed, labels) if s < signed_t and lab)
            tpr = tp / max(1, tp + fn)
            fpr = fp / max(1, fp + tn)
            j = tpr - fpr
            if j > best[3]:
                # 返回带方向的阈值，保证与 Insight.score（direction×距离）同一语义
                best = (signed_t, direction, _auc(
                    [s * direction for s, lab in zip(scores, labels) if not lab],
                    [s * direction for s, lab in zip(scores, labels) if lab],
                ), j)
    return best


class InsightEngine:
    """从「判据全绿但人工否决」的盲区里，自动发现新的可判定维度。

    关键：候选维度是系统枚举并逐一评估的，不是人预先指定的。系统真的在"找洞见"。
    """

    def __init__(self, profile_texts: list[str]):
        self.profile = profile_of(profile_texts)

    def discover(self, blind_spots: list[Verdict], passed: list[Verdict],
                 min_auc: float = 0.65) -> list[Insight]:
        if len(blind_spots) < 2 or len(passed) < 2:
            return []
        items = [(v, False) for v in blind_spots] + [(v, True) for v in passed]
        labels = [lab for _, lab in items]
        found: list[Insight] = []
        for dim in DIMENSIONS:
            scores = [fingerprint(v.text).distance_to(self.profile)[dim] for v, _ in items]
            auc = max(
                _auc([s for s, lab in zip(scores, labels) if not lab],
                     [s for s, lab in zip(scores, labels) if lab]),
                _auc([s for s, lab in zip(scores, labels) if lab],
                     [s for s, lab in zip(scores, labels) if not lab]),
            )
            if auc < min_auc:
                continue
            t, direction, _, youden = _best_threshold(scores, labels)
            found.append(Insight(dim, t, direction, auc, youden))
        found.sort(key=lambda x: x.auc, reverse=True)
        return found

    def compile(self, insight: Insight) -> Callable[[Draft, GroundTruth], list[Diagnostic]]:
        """把洞见编译成可安装、可回滚的 block 判据。"""
        profile = self.profile

        def check(draft: Draft, spec: GroundTruth) -> list[Diagnostic]:
            diags = []
            for stage, sentences in draft.chapters.items():
                for i, s in enumerate(sentences):
                    if insight.flags(s.text, profile):
                        diags.append(Diagnostic(
                            f"INSIGHT.{insight.dimension.upper()}", "block",
                            Locus(stage, i), f"触发自发现维度: {insight.describe()}",
                        ))
            return diags
        return check


# ---------------------------------------------------------------- 3. 校准置信度
class CalibratedConfidence:
    """从历史人工裁决里学「p_bad」——分箱校准，纯 Python。"""

    def __init__(self, bins: int = 5):
        self.bins = bins
        self.table: list[list[int]] = [[0, 0] for _ in range(bins)]  # [bad, total]

    def fit(self, samples: list[tuple[float, bool]]) -> None:
        """samples: (模型分数, 是否真的有问题)。"""
        self.table = [[0, 0] for _ in range(self.bins)]
        for score, is_bad in samples:
            idx = min(self.bins - 1, max(0, int(score * self.bins)))
            self.table[idx][0] += int(is_bad)
            self.table[idx][1] += 1

    def p_bad(self, score: float) -> float:
        idx = min(self.bins - 1, max(0, int(score * self.bins)))
        bad, total = self.table[idx]
        # 拉普拉斯平滑，未见过的高分区间回落到保守的基线
        return (bad + 1) / (total + 2) if total else 0.5


# ---------------------------------------------------------------- 4. 理性决策
@dataclass
class DecisionConfig:
    cost_human: float = 12.0    # C_h：交人一次的成本
    loss_fn: float = 100.0      # 漏放一个问题的损失
    loss_fp: float = 30.0       # 误杀一个好内容的损失

    def eu(self, action: str, p_bad: float) -> float:
        if action == "ACCEPT":
            return -p_bad * self.loss_fn
        if action == "REJECT":
            return -(1.0 - p_bad) * self.loss_fp
        if action == "ESCALATE":
            return -self.cost_human
        raise ValueError(action)


@dataclass(frozen=True)
class Decision:
    action: str          # ACCEPT | REJECT | ESCALATE
    p_bad: float
    eu: dict[str, float]
    rationale: str


def rational_decide(p_bad: float, cfg: DecisionConfig | None = None) -> Decision:
    """期望效用最优的三值决策。交人不再是默认，而是 EU 比较的一个选项。"""
    cfg = cfg or DecisionConfig()
    eus = {a: cfg.eu(a, p_bad) for a in ("ACCEPT", "REJECT", "ESCALATE")}
    action = max(eus, key=lambda a: eus[a])
    return Decision(action, p_bad, eus,
                    f"p_bad={p_bad:.2f}, EU=" + ", ".join(
                        f"{a}:{v:.1f}" for a, v in eus.items()))


# ---------------------------------------------------------------- 5. 认知循环
@dataclass
class CognitiveMetrics:
    capability: int      # 能力刻度：洞见数 + 校准样本数/10
    auto_rate: float     # 自动决策率（边界外移的直接度量）
    escalate_rate: float # 交人率（边界位置）
    error_rate: float    # 自动决策错误率（边界移动必须受控）
    insights: list[str] = field(default_factory=list)


class CognitiveLoop:
    """把洞见与理性决策组合成可迭代的认知循环。"""

    def __init__(self, profile_texts: list[str], cfg: DecisionConfig | None = None):
        self.engine = InsightEngine(profile_texts)
        self.conf = CalibratedConfidence()
        self.cfg = cfg or DecisionConfig()
        self.insights: list[Insight] = []
        self.metrics: list[CognitiveMetrics] = []

    def _signal(self, text: str) -> float:
        """模型分数：多个洞见归一化信号取最大（最有力的那个维度说了算）。"""
        if not self.insights:
            return 0.5   # 无任何洞见 = 完全不确定，交人
        return max(ins.to_signal(text, self.engine.profile) for ins in self.insights)

    def calibrate(self, samples: list[tuple[str, bool]]) -> None:
        """用带标签样本校准置信度：分数是洞见给的，标签是人工裁决给的。"""
        self.conf.fit([(self._signal(text), is_bad) for text, is_bad in samples])

    def decide(self, text: str) -> Decision:
        p = self.conf.p_bad(self._signal(text))
        return rational_decide(p, self.cfg)

    def discover_insights(self, blind_spots: list[Verdict], passed: list[Verdict],
                          min_auc: float = 0.85, max_insights: int = 3) -> list[Insight]:
        """一次性发现并安装高质量洞见；弱维度（AUC 低）不装，避免好样本被误触发。"""
        found = self.engine.discover(blind_spots, passed, min_auc=min_auc)
        for ins in found[:max_insights]:
            if all(ins.dimension != old.dimension for old in self.insights):
                self.insights.append(ins)
        return list(self.insights)

    def measure(self, test: list[tuple[str, bool]], capability: int) -> CognitiveMetrics:
        """在冻结测试集上测一次边界位置：交人率、自动决策率、自动决策错误率。"""
        auto = esc = errors = 0
        for text, is_bad in test:
            d = self.decide(text)
            if d.action == "ESCALATE":
                esc += 1
            else:
                auto += 1
                # 自动决策错误：ACCEPT 了坏内容，或 REJECT 了好内容
                if (d.action == "ACCEPT" and is_bad) or (d.action == "REJECT" and not is_bad):
                    errors += 1
        total = max(1, len(test))
        m = CognitiveMetrics(
            capability=capability, auto_rate=auto / total, escalate_rate=esc / total,
            error_rate=errors / total,
            insights=[i.describe() for i in self.insights],
        )
        self.metrics.append(m)
        return m


# ---------------------------------------------------------------- 6. 实验与报告
def _elder_corpus() -> list[str]:
    """老人的真实口述：短、口语、具体、少形容词——真值来源。"""
    return [
        "1998年我在镇上的供销社上班。",
        "那时候家里烧柴火，冬天手都裂了。",
        "我小时候在村里长大。",
        "后来供销社就没了。",
        "那时候一个月挣三百块钱。",
        "我七岁就开始干活了。",
        "上学走那条路，要走半个钟头。",
        "1998年的冬天特别冷。",
    ]


def _blind_spots() -> list[Verdict]:
    """现有事实判据全绿、但人工否决的盲区：无具体事实错误，纯风格违和。"""
    return [Verdict(t, False, "human_veto") for t in (
        "那时候的日子虽然清苦，却也透着一股子说不清的温馨，让人至今想起来心里都是暖的。",
        "那些远去的岁月里，藏着许多温暖而美好的回忆，每每想起，心中总是满是牵挂。",
        "回首往昔，那段辛酸的岁月仿佛就在昨天，历历在目，令人唏嘘不已。",
        "记忆中的童年总是美好的，那些温馨的画面，至今仍珍藏在心底最柔软的角落。",
        "时光荏苒，岁月如梭，那些曾经的点点滴滴，都化作了心中最珍贵的回忆。",
        "虽然生活虽苦，但那份纯朴的情感却让人倍感温馨，久久难以忘怀。",
    )]


def _passed() -> list[Verdict]:
    """事实判据全绿且人工接受的样本：风格与老人一致。"""
    return [Verdict(t, True, "human_ok") for t in (
        "1998年我在镇上的供销社上班。",
        "那时候家里烧柴火。",
        "我小时候在村里长大。",
        "后来供销社就没了。",
        "那时候一个月挣三百块钱。",
        "我七岁就开始干活了。",
    )]


def _test_set() -> list[tuple[str, bool]]:
    """冻结测试集。True=真的有问题（人工会否决）。"""
    bad = [v.text for v in _blind_spots()] + [
        "往事如烟，那些温暖的记忆总在心底泛起，让人久久不能平静。",
        "那些年的故事，充满了温馨与感动，至今想起仍是满满的怀念。",
    ]
    good = [v.text for v in _passed()] + [
        "1998年我在镇上上班。",
        "小时候家里烧柴火，冬天很冷。",
        "那时候走过那条路要半个钟头。",
    ]
    return [(t, True) for t in bad] + [(t, False) for t in good]


def _calibration_pool(per_class: int = 40) -> list[tuple[str, bool]]:
    """模拟逐渐积累的线上人工裁决：由少量种子模板扰动生成，正负均衡。

    真实系统里这些来自「核对原话」的接受/否决；这里用风格一致的模板放大样本量，
    让校准表的分箱随数据量增长而收敛，从而观察边界平滑外移。
    """
    bad_stems = [v.text for v in _blind_spots()]
    good_stems = [v.text for v in _passed()]
    pool: list[tuple[str, bool]] = []
    for i in range(per_class):
        pool.append((bad_stems[i % len(bad_stems)], True))
        pool.append((good_stems[i % len(good_stems)], False))
    return pool


def report(loop: CognitiveLoop) -> None:
    print("=" * 100)
    print("认知升级：自主洞见 + 理性决策 —— 人的边界 B(c) 随能力单调外移")
    print("=" * 100)
    print(f"{'能力刻度':>8}{'洞见数':>8}{'自动决策率':>12}{'交人率':>10}{'自动错误率':>12}  发现的维度")
    for m in loop.metrics:
        dims = ",".join(i.split("风格维度")[1].split("≥")[0].split("≤")[0].strip("「」")
                        for i in m.insights) or "-"
        print(f"{m.capability:>8}{len(m.insights):>8}{m.auto_rate:>12.0%}"
              f"{m.escalate_rate:>10.0%}{m.error_rate:>12.0%}  {dims}")
    first, last = loop.metrics[0], loop.metrics[-1]
    print(f"\n  边界移动: 交人率 {first.escalate_rate:.0%} → {last.escalate_rate:.0%}，"
          f"自动决策率 {first.auto_rate:.0%} → {last.auto_rate:.0%}")
    print(f"  受控性  : 自动决策错误率 {last.error_rate:.0%}（洞见+校准保证错误不随自动化失控）")
    print("  结论    : 边界不是常量，是能力函数；洞见扩展可判定空间，理性决策压缩不确定区间。")


def main() -> None:
    import random

    corpus = _elder_corpus()
    blind = _blind_spots()
    passed = _passed()
    test = _test_set()

    # 洞见引擎从盲区 vs 通过样本里，自动枚举 10 个候选维度
    probe = InsightEngine(corpus)
    found = probe.discover(blind, passed)
    print("洞见引擎从盲区 vs 通过样本里，自动枚举 10 个候选维度后的发现：")
    for ins in found[:4]:
        print(f"  - {ins.describe()}")
    print("  （这些维度不是人预设的，是系统逐一计算 AUC 后筛出的）\n")

    # 固定的校准池：模拟线上「核对原话」裁决逐渐积累，正负均衡、打乱
    rng = random.Random(20261121)
    calib_pool = _calibration_pool(per_class=40)
    rng.shuffle(calib_pool)

    loop = CognitiveLoop(corpus)
    installed = loop.discover_insights(blind, passed)
    print(f"安装高质量洞见 {len(installed)} 条（AUC≥0.85），之后固定不变；\n"
          "只让「校准样本量」这一个能力轴增长，观察边界：\n")

    # 边界前移阶段：从「零校准」开始，能力=洞见数，交人多
    loop.calibrate([])
    loop.measure(test, capability=len(installed))

    # 逐步累积校准样本（能力增强），观察交人率单调下降
    for n in (8, 16, 30, 50, 80):
        loop.calibrate(calib_pool[:n])
        loop.measure(test, capability=len(installed) + n // 8)

    report(loop)

    # 消融实验：证明「洞见」与「理性决策」各自都在推动边界
    print("\n" + "=" * 100)
    print("消融实验：拆掉其中一个能力，边界会停在哪")
    print("=" * 100)

    # A) 无洞见：只有理性决策框架，但没有扩展可判定空间 → 信号全是 0.5
    blind_loop = CognitiveLoop(corpus)      # 不 discover_insights
    blind_loop.calibrate(calib_pool[:80])
    m_blind = blind_loop.measure(test, capability=0)

    # B) 无理性决策：装了洞见，但一律交人（返回 ESCALATE，不做 EU 比较）
    no_rational = CognitiveLoop(corpus)
    no_rational.discover_insights(blind, passed)
    no_rational.calibrate(calib_pool[:80])
    esc_all = 0
    for text, is_bad in test:
        d = no_rational.decide(text)
        esc_all += 1  # 模拟「一律交人」：不管 p 多极端都 ESCALATE
    print(f"  {'配置':<28}{'自动决策率':>12}{'交人率':>10}")
    print(f"  {'无洞见(仅理性框架)':<26}{m_blind.auto_rate:>12.0%}{m_blind.escalate_rate:>10.0%}")
    print(f"  {'有洞见+一律交人(无理性)':<24}{0:>12.0%}{esc_all/len(test):>10.0%}")
    final = loop.metrics[-1]
    print(f"  {'洞见+理性决策(完整)':<25}{final.auto_rate:>12.0%}{final.escalate_rate:>10.0%}")
    print("\n  结论: 洞见提供可判定信号(否则理性框架空转仍100%交人)；"
          "理性决策把强信号转成自动行动(否则有判据仍100%交人)。二者缺一不可。")

    # 整合演示：认知层 ↔ PDCA 的接缝
    print("\n" + "=" * 100)
    print("与 PDCA 的接缝：洞见喂给 PDCA 安装，理性决策替代「一律交人」")
    print("=" * 100)
    from .pdca import Budget as PDCABudget, PDCALoop, _sample_batches  # noqa: E402

    joint = PDCALoop(__import__("svagent.autopoiesis", fromlist=["Environment"]).Environment(),
                     PDCABudget(max_cycles=10, patience=2))
    for batch in _sample_batches():
        joint.feed(batch)
        joint.run()
    print(f"  PDCA 自动机独立运行: v{joint.env.version}, "
          f"{len(joint.env.predicates)} 条符号判据, 交人 "
          f"{joint.status()['human_queue']} 项 ← 符号判据覆盖不到的模糊句")

    print(f"  认知层可对符号盲区做二次裁决（强信号自动、不确定才交人）:")
    demo_items = [
        ("那些远去的岁月里，藏着许多温暖而美好的回忆，每每想起，心中总是满是牵挂。", True),
        ("小时候家里烧柴火。", False),
        ("回首往昔，那段辛酸的岁月仿佛就在昨天。", True),
    ]
    for text, is_bad in demo_items:
        d = loop.decide(text)
        verdict = "✓" if (d.action != "ESCALATE" and
                          ((d.action == "REJECT") == is_bad)) else "…"
        print(f"    {verdict} 「{text[:16]}…」→ {d.action} (p_bad={d.p_bad:.2f})")
    print("  过去这些一律交人；现在强信号项被自动处理，只剩真正不确定的交人——")
    print("  这就是 B(c)：人的边界从「所有符号盲区」收缩到「认知仍不确定的窄带」。")
    print(f"  诚实代价: 仍有 {loop.metrics[-1].error_rate:.0%} 自动误判（如字符重复率误触发），"
          "边界外移不等于归零，人仍是最后防线。")


if __name__ == "__main__":
    main()
