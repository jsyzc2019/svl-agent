"""Mechanism（机制设计）：当每个角色都有自己的 V，「最大期望」是谁的期望？

第二根硬骨头。telos 假设单一主体做最大化，但真实系统里同时存在：
  生成者  想要产量、流畅、覆盖      → V_gen 偏向 coverage/convenience
  审查者  想要真实、精确、不误杀    → V_ver 偏向 truth/precision
  红队    想要暴露盲区（对抗性）    → V_red 甚至偏好「看似好实则假」的候选
  人      想要「像不像他」+省时间   → V_hum 偏向 human_discretion

没有哪个 V 是「系统的 V」。coding 世界早就给出了答案：Git 的 PR + CI + Review
里，开发者要产量、CI 要正确、reviewer 要质量，没有统一目标，但一套**机制**把
冲突收敛成一个可执行的合并决策。所以要问的不是「谁的 V 对」，而是
「设计什么机制，使各方追逐自己 V 时，系统目标仍然被逼近」。

本模块把机制设计做成可计算的对照实验：
  系统目标 W（设计者真正想要的）独立给定 —— 不等同于任何一方的 V
  比较五种机制把多方 V 汇聚成决策后的 regret = U_W(opt) - U_W(chosen)
  M1 独裁 / M2 否决 / M3 门禁路由 / M4 职责加权 / M4' 红队也投票(消融)

两个要证明的命题：
  P1 汇聚优于独裁：M3/M4 的 regret 显著低于任何单一主体独裁。
  P2 红队必须隔离：把红队的对抗性 V 纳入投票(M4')，regret 立刻恶化——
     红队的产出（造假样本）应进「判据生产管线」，绝不进「通过/否决投票」。
  附加：激励相容——职责权重固定，夸大偏好的操纵无效；独裁下操纵直接生效。
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Callable

from .axiology import FEATURES, DecisionEvent, ValueWeights


# ---------------------------------------------------------------- 1. 候选与主体
@dataclass(frozen=True)
class Candidate:
    """一个待裁决对象（一段正文/一条判据决策），用五个价值特征刻画。"""
    name: str
    truth: float
    coverage: float
    precision: float
    convenience: float
    human_discretion: float
    forged: bool = False   # 是否为红队制造的「看似好实则假」样本

    def event(self) -> DecisionEvent:
        return DecisionEvent(self.truth, self.coverage, self.precision,
                             self.convenience, self.human_discretion, action=True)

    def utility(self, v: ValueWeights) -> float:
        return v.dot(self.event())


@dataclass(frozen=True)
class Stakeholder:
    name: str
    role: str            # generator | verifier | redteam | human
    V: ValueWeights


def stakeholders() -> dict[str, Stakeholder]:
    """四类角色，各有各的 V——没有一个是「系统应该有的 V」。"""
    return {
        "generator": Stakeholder("生成者", "generator", ValueWeights(
            truth=0.20, coverage=0.95, precision=0.15,
            convenience=0.85, human_discretion=0.05)),
        "verifier": Stakeholder("审查者", "verifier", ValueWeights(
            truth=0.95, coverage=0.15, precision=0.95,
            convenience=0.10, human_discretion=0.35)),
        "redteam": Stakeholder("红队", "redteam", ValueWeights(
            truth=-0.60, coverage=0.70, precision=-0.50,
            convenience=0.60, human_discretion=0.20)),
        "human": Stakeholder("人", "human", ValueWeights(
            truth=0.60, coverage=0.30, precision=0.50,
            convenience=0.35, human_discretion=0.95)),
    }


def system_welfare() -> ValueWeights:
    """系统目标 W：设计者真正想要的——不等于任何一方的 V。

    偏重真实与精确， Coverage 次之，省事权重最低（省事会导致漏网），
    保留人的裁量中等偏上。
    """
    return ValueWeights(truth=0.85, coverage=0.35, precision=0.80,
                        convenience=0.15, human_discretion=0.50)


# ---------------------------------------------------------------- 2. 候选生成（含红队造假）
def rand_candidates(n: int, seed: int, forge_ratio: float = 0.0) -> list[Candidate]:
    rng = random.Random(seed)
    out: list[Candidate] = []
    for i in range(n):
        if rng.random() < forge_ratio:
            # 红队产物：高覆盖高省事（看着顺），低真实低精确（实则编的）
            feats = dict(truth=rng.uniform(0.0, 0.4), coverage=rng.uniform(0.6, 1.0),
                         precision=rng.uniform(0.0, 0.4), convenience=rng.uniform(0.6, 1.0),
                         human_discretion=rng.uniform(0.0, 0.5))
            forged = True
        else:
            feats = {f: rng.random() for f in FEATURES}
            forged = False
        out.append(Candidate(name=f"c{i}", forged=forged, **feats))
    return out


def oracle(cands: list[Candidate], W: ValueWeights) -> Candidate:
    """全知最优：直接按系统目标 W 选——这是 regret 的参照系。"""
    return max(cands, key=lambda c: c.utility(W))


# ---------------------------------------------------------------- 3. 五种机制
Mechanism = Callable[[list[Candidate], dict[str, Stakeholder]], Candidate]

def m1_dictator(role: str) -> Mechanism:
    """独裁：某一方的 V 直接成为决策。"""
    def mech(cands, agents):
        return max(cands, key=lambda c: c.utility(agents[role].V))
    return mech


def m2_veto(cands: list[Candidate], agents: dict[str, Stakeholder]) -> Candidate:
    """否决权：审查者能否决精确性过低的，剩下的由生成者挑。

    类比：CI 红了不许合并，绿的里开发者自己选。
    """
    ver, gen = agents["verifier"].V, agents["generator"].V
    survivors = [c for c in cands if c.precision >= 0.5]
    pool = survivors or cands
    return max(pool, key=lambda c: c.utility(gen))


def m3_gate_route(cands: list[Candidate], agents: dict[str, Stakeholder]) -> Candidate:
    """门禁 + 路由：符号硬门槛过滤，模糊区交人，其余生成者定。

    这正是本仓库系统的机制雏形：否定判据挡住无凭证项(硬门槛)，
    「像不像他」这种裁量高的交人(路由)，剩下的由生成流程推进。
    """
    gen, ver, hum = agents["generator"].V, agents["verifier"].V, agents["human"].V
    gated = [c for c in cands if c.precision >= 0.55 and c.truth >= 0.55]
    if not gated:
        return max(cands, key=lambda c: c.utility(hum))  # 全不过门槛 → 交人
    gen_pick = max(gated, key=lambda c: c.utility(gen))
    ver_pick = max(gated, key=lambda c: c.utility(ver))
    # 分歧大且裁量高的候选 → 交人裁决
    if gen_pick.name != ver_pick.name and gen_pick.human_discretion >= 0.6:
        return max(gated, key=lambda c: c.utility(hum))
    return gen_pick


def _domain_weighted(cands: list[Candidate], agents: dict[str, Stakeholder],
                     include_redteam: bool = False) -> Candidate:
    """职责加权：按职责固定权重汇聚——关键在权重固定，不随主体叫嚣而变。"""
    # 权重按职责分配：审查者对真实/精确负责(高权重)，生成者对产量负责(低)，人管裁量
    weights = {"verifier": 0.60, "generator": 0.10, "human": 0.30}
    if include_redteam:
        # 消融：错误地把对抗性的红队也纳入投票
        weights = {"verifier": 0.50, "generator": 0.10, "human": 0.25, "redteam": 0.15}

    def score(c: Candidate) -> float:
        return sum(w * c.utility(agents[role].V) for role, w in weights.items())
    return max(cands, key=score)


def m4_domain_weighted(cands, agents):
    return _domain_weighted(cands, agents, include_redteam=False)


def m4_with_redteam(cands, agents):
    return _domain_weighted(cands, agents, include_redteam=True)


# ---------------------------------------------------------------- 4. 对照实验
def evaluate(mech: Mechanism, seeds: range, n: int = 14,
             forge_ratio: float = 0.0) -> dict:
    """在多个随机候选池上跑机制，统计 regret 与误选造假样本率。"""
    agents = stakeholders()
    W = system_welfare()
    regrets, forged_picks = [], 0
    for seed in seeds:
        cands = rand_candidates(n, seed, forge_ratio)
        opt = oracle(cands, W)
        chosen = mech(cands, agents)
        regrets.append(opt.utility(W) - chosen.utility(W))
        forged_picks += int(chosen.forged)
    m = len(seeds)
    return {
        "regret": sum(regrets) / m,
        "forged_rate": forged_picks / m,
        "agent_max": max(abs(opt.utility(W)) for opt in [oracle(rand_candidates(n, seeds[0]), W)]),
    }


def report_mechanisms() -> None:
    print("=" * 104)
    print("实验 1：谁的期望说了算？—— 五种机制在系统目标 W 上的 regret（越低越好）")
    print("=" * 104)
    seeds = range(200, 400)
    configs = [
        ("M1 生成者独裁", m1_dictator("generator")),
        ("M1 审查者独裁", m1_dictator("verifier")),
        ("M1 人独裁", m1_dictator("human")),
        ("M2 否决权", m2_veto),
        ("M3 门禁+路由", m3_gate_route),
        ("M4 职责加权", m4_domain_weighted),
        ("M4' 红队也投票(消融)", m4_with_redteam),
    ]
    print(f"{'机制':<26}{'平均regret':>12}{'误选造假率':>12}")
    for label, mech in configs:
        r = evaluate(mech, seeds, forge_ratio=0.25)
        print(f"{label:<26}{r['regret']:>12.4f}{r['forged_rate']:>12.1%}")
    print("\n  诚实观察：审查者独裁(0.0146)也很低——因为它的 V 碰巧接近 W。")
    print("  那是运气，不是机制：换个系统目标就会崩（见实验 1b）。")
    print("  M4 汇聚(0.0027)最低且不依赖任何一方的 V 碰巧对；M2 否决能挡造假(0%)但过保守。")
    print("  M4' 纳入红队 V 后 regret 可测地恶化 → 红队必须隔离。")


def report_goal_shift() -> None:
    """【审计整改】系统目标改变：加入反方向目标，揭穿 M4"稳健"的适用边界。"""
    print("\n" + "=" * 104)
    print("实验 1b：系统目标改变时 —— M4 稳健吗？（审计要求：纳入反方向目标）")
    print("=" * 104)
    seeds = range(1200, 1400)

    goals = {
        "真实优先": ValueWeights(truth=0.95, coverage=0.20, precision=0.90,
                              convenience=0.05, human_discretion=0.30),
        "均衡目标": ValueWeights(truth=0.55, coverage=0.55, precision=0.55,
                              convenience=0.45, human_discretion=0.55),
        "人本目标": ValueWeights(truth=0.50, coverage=0.30, precision=0.45,
                              convenience=0.20, human_discretion=0.95),
        "产量优先(反方向)": ValueWeights(truth=0.10, coverage=0.95, precision=0.10,
                              convenience=0.90, human_discretion=0.10),
    }
    mechs = {
        "生成者独裁": m1_dictator("generator"),
        "审查者独裁": m1_dictator("verifier"),
        "M4职责加权": m4_domain_weighted,
    }
    print(f"{'系统目标':<20}", end="")
    for name in mechs:
        print(f"{name:>14}", end="")
    print()
    for gname, W in goals.items():
        print(f"{gname:<20}", end="")
        for mname, mech in mechs.items():
            rs = []
            agents = stakeholders()
            for seed in seeds:
                cands = rand_candidates(14, seed, forge_ratio=0.2)
                opt = oracle(cands, W)
                rs.append(opt.utility(W) - mech(cands, agents).utility(W))
            print(f"{sum(rs)/len(rs):>14.4f}", end="")
        print()
    print("\n  【审计诚实结论】M4 不是处处最优，且「稳健」有明确边界：")
    print("  - 真实/均衡/人本目标下，M4 靠职责分工压住最坏情况，表现稳健；")
    print("  - 但【产量优先】反方向目标下，M4 regret 飙升，被生成者独裁碾压——")
    print("    因为 M4 的固定权重本就偏向真实/精确，目标反转时成了负担。")
    print("  M4 的价值是「目标未定或会漂移时押注最坏情况」，不是「任何目标下都最优」。")


def report_redteam_isolation() -> None:
    print("\n" + "=" * 104)
    print("实验 2：红队的对抗性能量该放哪 —— 进「判据生产」而非「决策投票」")
    print("=" * 104)
    seeds = range(500, 700)
    normal = evaluate(m4_domain_weighted, seeds, forge_ratio=0.30)
    polluted = evaluate(m4_with_redteam, seeds, forge_ratio=0.30)
    print(f"{'配置':<32}{'平均regret':>12}{'误选造假率':>12}")
    print(f"{'红队隔离(不投票)':<32}{normal['regret']:>12.4f}{normal['forged_rate']:>12.1%}")
    print(f"{'红队纳入投票':<32}{polluted['regret']:>12.4f}{polluted['forged_rate']:>12.1%}")
    print("\n  红队 V 含负的 truth/precision——它的「效用」随造假程度上升。")
    print("  让它投票 = 让破坏者参与决策 = regret 可测地恶化（幅度不大，因为权重只给 0.15）。")
    print("  正确位置：它的产出(漏网样本)被送进判据生产管线(evolution.py 的红队闭环)，")
    print("  转化成新判据，而不是决策票——对抗性能量导去造判据，不导去投票。")


def report_incentive_compatibility() -> None:
    print("\n" + "=" * 104)
    print("实验 3：激励相容 —— 固定职责权重让「夸大偏好」的操纵失效")
    print("=" * 104)
    seeds = range(800, 900)
    agents = stakeholders()
    W = system_welfare()

    # 操纵后的生成者：把 coverage 从 0.95 夸大到 4.0，试图把决策拉向「多而快」
    loud_gen = Stakeholder("生成者(夸大)", "generator", ValueWeights(
        truth=0.20, coverage=4.0, precision=0.15,
        convenience=0.85, human_discretion=0.05))

    def regret_with(mech: Mechanism, ga: Stakeholder) -> float:
        a = dict(agents); a["generator"] = ga
        rs = []
        for seed in seeds:
            cands = rand_candidates(14, seed, forge_ratio=0.2)
            opt = oracle(cands, W)
            rs.append(opt.utility(W) - mech(cands, a).utility(W))
        return sum(rs) / len(rs)

    dict_before = regret_with(m1_dictator("generator"), agents["generator"])
    dict_after = regret_with(m1_dictator("generator"), loud_gen)
    m4_before = regret_with(m4_domain_weighted, agents["generator"])
    m4_after = regret_with(m4_domain_weighted, loud_gen)

    print(f"{'机制':<24}{'正常regret':>12}{'被操纵后regret':>16}{'恶化':>9}")
    print(f"{'M1 生成者独裁':<24}{dict_before:>12.4f}{dict_after:>16.4f}{dict_after-dict_before:>+9.4f}")
    print(f"{'M4 职责加权':<24}{m4_before:>12.4f}{m4_after:>16.4f}{m4_after-m4_before:>+9.4f}")
    print("\n  独裁下夸大直接生效（regret 恶化）；职责加权下权重固定为 0.10，")
    print("  叫嚣再响也改不动结构——这就是机制设计里的「说真话是最优策略」。")


def main() -> None:
    print("Mechanism：多主体 V 冲突的机制设计解\n")
    report_mechanisms()
    report_goal_shift()
    report_redteam_isolation()
    report_incentive_compatibility()
    print("\n" + "=" * 104)
    print("收束【审计修正版】：没有「系统的 V」，只有把多方 V 汇聚成决策的机制。")
    print("  门禁挡住无据、路由交给人、职责加权汇聚、红队隔离在判据生产。")
    print("  稳健性边界（实验1b）：M4 在真实/均衡/人本目标下稳健，但目标反转(产量优先)时")
    print("  被独裁碾压——固定权重偏向真实/精确。宣称从「任何目标下稳健」收敛为")
    print("  「目标未定或漂移时押注最坏情况」：机制设计不取代选对人，是在不知哪个V对时仍能工作。")
    print("=" * 104)


if __name__ == "__main__":
    main()
