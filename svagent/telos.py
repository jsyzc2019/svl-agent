"""Telos（目的论）：目标导向的价值-认知协同 —— 人和 agent 的统一决策框架。

对上一轮的第二次修正：
  上一轮说「人是不确定时更可靠的裁决器」——仍然错了，那是给人保留了一个特权本体。
  真相是：人和 AI 面对的是**同一个**不确定性决策困境，没有谁天然更可靠。
  差异全部是「学习与认知的实际能力参数」的取值不同——程度差异，不是类别差异。

统一命题（这就是可计算的「天道运行规律」）：
  任何认知主体，围绕一个具体目标 G，用一个价值函数 V（想要什么）和一个
  认知函数 C（相信什么、能看多清），每一步求最大可能期望的行动：
      a* = argmax_a  E_{ belief_C }[ V( T(s,a) ) ] - cost(a)
  执行 → 观察 → 更新认知 → 重估价值 → 再决策，沿一条持续优化的路径
  渐进逼近目标。不是一步到位，是轨迹收敛。

本模块把这个抽象落成一个**序贯最优停止问题**（有严格数学基础，不是比喻）：
  - 世界有一个隐藏真值（这段内容是否有问题）
  - 主体花成本观察（噪声受认知带宽约束），形成信念 Beta(p_bad)
  - 每步在三个行动里选期望价值最大的：继续观察 / 判定为好 / 判定为坏
  - 价值函数 V 给出收益/损失/观察成本，认知函数 C 给出信念与校准度

统一结构：人和 AI 都是同一份 CognitiveProfile，只是参数取值不同。
  「专家人」= 高带宽高校准；「弱 AI」= 低带宽低校准；反之亦然。
  成效由参数决定，不由「是不是人」决定。
"""
from __future__ import annotations

import math
import random
from dataclasses import asdict, dataclass, field
from typing import Literal

Action = Literal["observe", "declare_good", "declare_bad"]


# ---------------------------------------------------------------- 1. 目标与价值函数
@dataclass(frozen=True)
class Goal:
    """目标 G：把「想要什么」编码成价值函数 V 的参数。"""

    name: str = "默认目标"
    reward: float = 10.0        # 判对的收益
    loss: float = 25.0          # 判错的损失（损失厌恶：loss > reward）
    observe_cost: float = 1.0   # 每次观察的成本
    voi_weight: float = 8.0     # 信息价值权重：不确定性每降低一点值多少

    def value(self, action: Action, p_bad: float, uncertainty: float) -> float:
        """价值函数 V：返回某行动的期望价值主体部分。"""
        if action == "declare_good":
            return (1 - p_bad) * self.reward - p_bad * self.loss
        if action == "declare_bad":
            return p_bad * self.reward - (1 - p_bad) * self.loss
        # observe：信息价值 - 成本。不确定性越高，观察越值钱。
        return self.voi_weight * uncertainty - self.observe_cost


# ---------------------------------------------------------------- 2. 世界（隐藏真值）
@dataclass
class World:
    """待决策的对象：一个隐藏真值 + 一个有噪声的观察通道。"""

    true_p_bad: float           # 真实的问题概率（对主体隐藏）
    base_noise: float = 0.28    # 观察的基础噪声
    seed: int = 0

    def observe(self, bandwidth: float, rng: random.Random) -> float:
        """观察：返回 [0,1] 信号。带宽越高噪声越小（认知带宽=信息获取能力）。"""
        noise_sd = self.base_noise / max(0.1, bandwidth)
        raw = self.true_p_bad + rng.gauss(0, noise_sd)
        return min(1.0, max(0.0, raw))


# ---------------------------------------------------------------- 3. 认知函数 C
@dataclass
class CognitiveProfile:
    """认知主体的能力参数——人和 AI 共用这个结构，差异只是取值。"""

    name: str
    prior_alpha: float = 1.0       # 先验强度：初始相信"问题概率"的伪计数（坏方向）
    prior_beta: float = 1.0        # 先验强度：初始相信"没问题"的伪计数（好方向）
    bandwidth: float = 1.0         # 认知带宽：单次观察的信息增益
    learning_rate: float = 0.5     # 学习率：用新观察修正信念的速度
    calibration: float = 1.0       # 校准度：1=如实感知不确定性；<1 过度自信，>1 欠自信

    @property
    def is_human_like(self) -> bool:
        return getattr(self, "_human", False)


@dataclass
class Belief:
    """主体对 p_bad 的信念：用 Beta(α,β) 的均值与方差近似。"""

    alpha: float
    beta: float

    @classmethod
    def from_prior(cls, profile: CognitiveProfile) -> "Belief":
        return cls(profile.prior_alpha, profile.prior_beta)

    @property
    def p_bad(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    @property
    def uncertainty(self) -> float:
        """Beta 分布标准差，再按校准度缩放（过度自信→主观不确定性被压低）。

        用标准差而非方差：量级 0.1~0.3，与收益/成本同阶，让信息价值项
        VOI = voi_weight × uncertainty 真正能驱动观察决策，而不是个摆设。
        """
        a, b = self.alpha, self.beta
        var = (a * b) / ((a + b) ** 2 * (a + b + 1))
        return math.sqrt(max(0.0, var)) * self._calibration

    _calibration: float = 1.0

    def update(self, signal: float, profile: CognitiveProfile) -> None:
        """贝叶斯式更新：观察信号转成伪计数，按学习率与带宽加权。"""
        strength = profile.learning_rate * profile.bandwidth
        self.alpha += strength * signal
        self.beta += strength * (1 - signal)


# ---------------------------------------------------------------- 4. 认知主体
@dataclass
class StepRecord:
    step: int
    action: Action
    signal: float | None
    p_bad_before: float
    p_bad_after: float
    uncertainty: float
    ev_observe: float
    ev_good: float
    ev_bad: float
    cumulative_cost: float


@dataclass
class Trajectory:
    agent: str
    steps: list[StepRecord] = field(default_factory=list)
    decision: Action | None = None
    correct: bool | None = None
    total_cost: float = 0.0
    final_value: float = 0.0
    stopped_early: bool = True   # 是否在 max_steps 前主动最优停止；False=被步数上限强制判定

    @property
    def n_observations(self) -> int:
        return sum(1 for s in self.steps if s.action == "observe")

    @property
    def exhausted(self) -> bool:
        """步数耗尽被强制判定——审计要求显式报告，揭穿"最优停止"失效的情形。"""
        return not self.stopped_early


class CognitiveAgent:
    """一个认知主体（人或 AI）：价值函数 V + 认知函数 C 的载体。"""

    def __init__(self, profile: CognitiveProfile, goal: Goal):
        self.profile = profile
        self.goal = goal

    def decide(self, belief: Belief) -> tuple[Action, dict[str, float]]:
        """核心：a* = argmax E[V(action)] —— 价值与认知在这一步协同。"""
        # 认知函数 C 提供主观状态：p_bad 与（校准后的）不确定性
        belief._calibration = self.profile.calibration ** 2
        p = belief.p_bad
        u = belief.uncertainty
        evs = {
            "observe": self.goal.value("observe", p, u),
            "declare_good": self.goal.value("declare_good", p, u),
            "declare_bad": self.goal.value("declare_bad", p, u),
        }
        action = max(evs, key=lambda a: evs[a])
        return action, evs  # type: ignore[return-value]

    def run(self, world: World, max_steps: int = 20) -> Trajectory:
        rng = random.Random(world.seed)
        belief = Belief.from_prior(self.profile)
        traj = Trajectory(agent=self.profile.name)
        truth_bad = world.true_p_bad >= 0.5

        for step in range(max_steps):
            action, evs = self.decide(belief)
            p_before = belief.p_bad
            u = belief.uncertainty
            signal = None

            if action == "observe":
                signal = world.observe(self.profile.bandwidth, rng)
                belief.update(signal, self.profile)
                traj.total_cost += self.goal.observe_cost
            else:
                traj.decision = action
                traj.correct = (action == "declare_bad") == truth_bad
                break

            traj.steps.append(StepRecord(
                step=step, action=action, signal=signal,
                p_bad_before=p_before, p_bad_after=belief.p_bad,
                uncertainty=u,
                ev_observe=evs["observe"], ev_good=evs["declare_good"],
                ev_bad=evs["declare_bad"],
                cumulative_cost=traj.total_cost,
            ))

        if traj.decision is None:  # 步数耗尽：强制按当前信念判——并非"最优停止"，是撞上限
            traj.stopped_early = False
            traj.decision = "declare_bad" if belief.p_bad >= 0.5 else "declare_good"
            traj.correct = (traj.decision == "declare_bad") == truth_bad

        traj.final_value = self._final_value(traj)
        return traj

    def _final_value(self, traj: Trajectory) -> float:
        if traj.correct:
            return self.goal.reward - traj.total_cost
        return -self.goal.loss - traj.total_cost


# ---------------------------------------------------------------- 5. 统一实验
def profile_set() -> list[CognitiveProfile]:
    """同一任务下的多种认知主体：人、AI、专家、弱模型——全是参数取值。

    刻意让「专家人」的先验保持中性（prior 1:1）：专长不来自"先验方向碰巧对"
    （那是运气，不是可靠能力），而来自带宽与校准——看得多、看得准、知道自己多确定。
    这样才能诚实地论证：成效差异来自认知能力参数，不是身份，也不是先验彩票。
    """
    return [
        CognitiveProfile("弱AI(低带宽/过自信/低校准)", prior_alpha=1, prior_beta=1,
                         bandwidth=0.7, learning_rate=0.5, calibration=0.4),
        CognitiveProfile("普通人(中带宽/中校准)", prior_alpha=1, prior_beta=1,
                         bandwidth=1.3, learning_rate=0.5, calibration=0.7),
        CognitiveProfile("专家人(高带宽/高校准)", prior_alpha=1, prior_beta=1,
                         bandwidth=2.2, learning_rate=0.7, calibration=0.95),
        CognitiveProfile("强AI(极高带宽/快学习/校准)", prior_alpha=1, prior_beta=1,
                         bandwidth=4.0, learning_rate=0.9, calibration=1.0),
    ]


def _batch_run(profile: CognitiveProfile, goal: Goal, worlds: list[World]) -> dict:
    """在多个世界上跑同一主体，统计成效（消除单一样本偶然性）。"""
    results = [CognitiveAgent(profile, goal).run(w) for w in worlds]
    acc = sum(1 for r in results if r.correct) / len(results)
    avg_cost = sum(r.total_cost for r in results) / len(results)
    avg_obs = sum(r.n_observations for r in results) / len(results)
    avg_value = sum(r.final_value for r in results) / len(results)
    stop_rate = sum(1 for r in results if r.stopped_early) / len(results)
    return {"accuracy": acc, "cost": avg_cost, "obs": avg_obs,
            "value": avg_value, "stop_rate": stop_rate}


def worlds_by_difficulty(n: int, gap: float, seed: int = 0,
                         base_noise: float = 0.28) -> list[World]:
    """【审计整改】按真值间隔 gap 构造世界，替代固定的 0.8/0.15(gap=0.65) 玩具难度。

    gap=0.65 → 原玩具难度（所有主体满分）；gap=0.10 → 困难任务（能力差异现形）。
    这样准确率指标才有分辨力，不再靠"全员满分"假装能力无关身份。
    """
    center = 0.5
    return [World(true_p_bad=center + gap / 2 if i % 2 == 0 else center - gap / 2,
                  seed=seed + i, base_noise=base_noise) for i in range(n)]


def report_unified() -> None:
    print("=" * 108)
    print("统一框架：人和 AI 是同一决策困境下的参数化认知主体（差异=程度，非类别）")
    print("【审计整改】多难度扫描：揭穿原版靠 gap=0.65 玩具难度让全员满分的假象")
    print("=" * 108)
    goal = Goal()
    diffs = [("玩具 gap=.65", 0.65), ("中等 gap=.30", 0.30), ("困难 gap=.10", 0.10)]
    profiles = profile_set()
    for label, gap in diffs:
        worlds = worlds_by_difficulty(60, gap, seed=100)
        print(f"\n  ── {label}（噪声0.28）──")
        print(f"  {'认知主体':<30}{'准确率':>8}{'观察':>7}{'停止率':>8}{'价值':>9}")
        for p in profiles:
            m = _batch_run(p, goal, worlds)
            print(f"  {p.name:<30}{m['accuracy']:>8.0%}{m['obs']:>7.1f}"
                  f"{m['stop_rate']:>8.0%}{m['value']:>9.1f}")
    print("\n  【审计结论】玩具难度下所有主体准确率 100%——指标无分辨力，原版「能力无关身份」")
    print("  的论证站不住；只有把 gap 降到 0.1，带宽/校准的作用才现形（弱AI显著低于强AI）。")
    print("  这修正了宣称：不是「能力差异不存在」，而是「原实验设计没有测出能力差异」。")


def report_synergy() -> None:
    """消融：V 与 C 缺一不可，协同才有渐进收敛。"""
    print("\n" + "=" * 104)
    print("消融实验：价值函数 V 与认知函数 C 的协同 —— 缺一不可")
    print("=" * 104)
    goal = Goal()
    worlds = [World(true_p_bad=0.8 if i % 2 == 0 else 0.15, seed=200 + i)
              for i in range(60)]

    good_C = CognitiveProfile("好认知", bandwidth=3.0, learning_rate=0.9, calibration=1.0)
    bad_C = CognitiveProfile("坏认知(噪声大/过自信)", bandwidth=0.4, learning_rate=0.2, calibration=0.3)
    good_V = Goal(name="好价值", reward=10, loss=25, observe_cost=1, voi_weight=8)
    # 无V：收益/损失/信息价值全归零 → 所有行动无差别，决策方向丢失（退化成永远猜同一类）
    no_V = Goal(name="无价值", reward=0, loss=0, observe_cost=1, voi_weight=0)
    # 乱V：损失远小于收益 → 赌一把总比观察划算 → 永不观察直接下注
    gamble_V = Goal(name="赌徒价值", reward=10, loss=2, observe_cost=1, voi_weight=0.5)

    configs = [
        ("好V + 好C（协同）", good_V, good_C),
        ("好V + 坏C（有目标看不清）", good_V, bad_C),
        ("无V + 好C（看得清无方向）", no_V, good_C),
        ("乱V + 好C（价值失真→赌）", gamble_V, good_C),
    ]
    print(f"{'配置':<32}{'准确率':>9}{'观察次数':>10}{'期望价值':>11}")
    for label, g, p in configs:
        m = _batch_run(p, g, worlds)
        print(f"{label:<32}{m['accuracy']:>9.0%}{m['obs']:>10.1f}{m['value']:>11.1f}")
    print("\n  结论：V 定义方向，C 定义能看多清。无 V → 看得清也不知往哪走；")
    print("  坏 C → 有目标也看不清；乱 V → 价值失真就变成赌。只有 V×C 协同，")
    print("  主体才「该观察时观察、该决策时决策」，沿最大期望路径渐进逼近目标。")


def report_convergence() -> None:
    """渐进目标实现：单条轨迹上，信念如何一步步收敛到真值并触发决策。"""
    print("\n" + "=" * 104)
    print("渐进实现：一个主体沿最大期望路径，信念逐步收敛 → 触发最优停止")
    print("=" * 104)
    goal = Goal(observe_cost=1.6, voi_weight=5.0)  # 观察略贵 → 需要多观察几步才敢决策
    world = World(true_p_bad=0.85, seed=7, base_noise=0.42)
    profile = CognitiveProfile("示例主体", bandwidth=1.6, learning_rate=0.45, calibration=0.95)
    traj = CognitiveAgent(profile, goal).run(world, max_steps=12)
    print(f"隐藏真值 p_bad={world.true_p_bad}；先验 p=0.5\n")
    print(f"{'步':>3}{'行动':>15}{'观察信号':>10}{'信念p_bad':>11}{'不确定性':>10}"
          f"{'EV观察':>9}{'EV判好':>9}{'EV判坏':>9}")
    for s in traj.steps:
        print(f"{s.step:>3}{s.action:>15}{(f'{s.signal:.2f}' if s.signal is not None else '-'):>10}"
              f"{s.p_bad_after:>11.3f}{s.uncertainty:>10.4f}"
              f"{s.ev_observe:>9.2f}{s.ev_good:>9.2f}{s.ev_bad:>9.2f}")
    print(f"\n最终决策={traj.decision}，正确={traj.correct}，"
          f"观察 {traj.n_observations} 次，成本 {traj.total_cost:.0f}，价值 {traj.final_value:.1f}")
    print(f"  是否主动最优停止: {'是' if traj.stopped_early else '否(撞步数上限)'}")
    print("  轨迹收敛：不确定性随观察下降 → 信息价值 EV(observe) 跌破判据价值 → 停止。")

    # 【审计整改】上面是单条"玩具难度"轨迹。必须诚实对照难任务：最优停止是否真的发生？
    print("\n  ── 审计对照：难任务下「最优停止」是否仍然成立？──")
    profile2 = CognitiveProfile("示例主体", bandwidth=1.6, learning_rate=0.45, calibration=0.95)
    for label, gap in (("玩具 gap=.65", 0.65), ("困难 gap=.10", 0.10)):
        ws = worlds_by_difficulty(60, gap, seed=7, base_noise=0.42)
        trs = [CognitiveAgent(profile2, goal).run(w, max_steps=12) for w in ws]
        sr = sum(1 for t in trs if t.stopped_early) / len(trs)
        acc = sum(1 for t in trs if t.correct) / len(trs)
        print(f"  {label}: 主动停止率={sr:.0%}  准确率={acc:.0%}  "
              f"平均观察={sum(t.n_observations for t in trs)/len(trs):.1f}/12")
    print("  【诚实结论】玩具难度下几乎都主动停止；难任务下大量轨迹撞满 12 步被强制判定，")
    print("  「沿期望曲线优雅停止」只是简单任务的性质——原版只展示玩具轨迹，属选择性呈现。")


def report_boundary_shift() -> None:
    """边界随能力外移：认知能力越高，越早能自动决策（越过 human 边界）。"""
    print("\n" + "=" * 104)
    print("能力决定边界：认知带宽提升 → 更少观察即可达同等准确率 → 自主决策区扩张")
    print("=" * 104)
    goal = Goal()
    worlds = [World(true_p_bad=0.8 if i % 2 == 0 else 0.15, seed=300 + i)
              for i in range(60)]
    print(f"{'认知带宽':>10}{'准确率':>9}{'平均观察次数':>14}{'边界解读':>28}")
    for bw in (0.4, 0.7, 1.0, 1.6, 2.5, 4.0):
        p = CognitiveProfile(f"bw={bw}", bandwidth=bw, learning_rate=0.8, calibration=0.95)
        m = _batch_run(p, goal, worlds)
        note = "需大量观察/交人" if m["obs"] > 3 else ("部分自主" if m["obs"] > 1 else "多数自主决策")
        print(f"{bw:>10.1f}{m['accuracy']:>9.0%}{m['obs']:>14.1f}{note:>28}")
    print("\n  带宽是能力的代理：能力越强，同一目标下需要的人工介入（观察/交人）越少。")
    print("  边界不是固定的「人的领地」，而是随认知能力伸缩的期望最优分界。")


def main() -> None:
    report_unified()
    report_synergy()
    report_convergence()
    report_boundary_shift()
    print("\n" + "=" * 104)
    print("收束：目标 G 给定 → V（想要什么）× C（看得清什么）协同 → 每步求最大期望")
    print("       → 执行/观察/更新 → 渐进逼近目标。人不是裁判，只是另一组认知参数。")
    print("=" * 104)


if __name__ == "__main__":
    main()
