"""破解「只多耗算力却不降人工负担」的定量实验。

问题：在「闸门 + 兜底」之上加一层「机器诊断 → 受约束返工」，到底会不会
降低人工负担？还是会制造更多需要人看的东西？

模型把人工负担拆成两条独立通道：
  - acquire：覆盖缺口导致的回问老人次数（贵，c_acquire）
  - review ：流畅/可疑段落的核对卡（便宜，c_review）
再加一条质量通道：
  - corrupt：符号判据通过、但内容静默造假（无约束返工时 s>0）

用同一组随机数同时评估三种策略（common random numbers），减少方差。
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from .core import Claim, Draft, GroundTruth, Message, Sentence
from .verifiers import concrete_grounded, default_verifiers, narrative_vividness_flag


@dataclass
class Config:
    n_facts: int = 40
    p_bad: float = 0.25       # 生成虚构细节 → block
    p_miss: float = 0.15      # 整条事实没生成 → 覆盖缺口
    p_vivid: float = 0.20     # 有据但花哨 → flag
    q: float = 0.70           # 有凭证时定向返工的成功率
    p_coverable: float = 0.80  # block 中有素材可依托的比例（无凭证只能回问）
    s: float = 0.00           # 返工后静默造假率（无约束 LLM > 0）
    r: float = 0.25           # 返工后变花哨 → 额外 flag
    c_acquire: float = 10.0   # 回问老人一次 = 10 张核对卡
    c_review: float = 1.0
    lam: float = 0.0          # 静默造假在目标函数里的权重
    seeds: int = 3000


@dataclass
class Outcome:
    acquire: float = 0.0
    review: float = 0.0
    corrupt: float = 0.0
    compute: float = 0.0

    @property
    def burden(self) -> float:
        return self.acquire * CFG.c_acquire + self.review * CFG.c_review

    @property
    def objective(self) -> float:
        return self.burden + CFG.lam * self.corrupt


CFG = Config()


def draw_facts(rng: random.Random, cfg: Config) -> list[tuple]:
    """每个事实一次抽样，三种策略共用，保证对比公平。"""
    draws = []
    for _ in range(cfg.n_facts):
        u = rng.random()
        if u < cfg.p_bad:
            kind = "bad"
        elif u < cfg.p_bad + cfg.p_miss:
            kind = "miss"
        elif u < cfg.p_bad + cfg.p_miss + cfg.p_vivid:
            kind = "vivid"
        else:
            kind = "ok"
        draws.append((
            kind,
            rng.random() < cfg.q,               # rework_ok
            rng.random() < cfg.r,               # rework_vivid
            rng.random(),                       # 造假的原始随机数，各策略按自己的 s 判定
            rng.random() < cfg.p_coverable,     # 是否有素材可依托
        ))
    return draws


def evaluate(draws: list[tuple], policy: str, cfg: Config) -> Outcome:
    o = Outcome()
    for kind, rework_ok, rework_vivid, corrupt_u, has_claim in draws:
        rework_corrupt = corrupt_u < cfg.s
        if kind == "miss":
            o.acquire += 1
            continue
        if kind == "vivid":
            o.review += 1
            continue
        if kind == "ok":
            continue

        # kind == "bad"：闸门命中，下面看策略怎么处置
        if policy == "gate":
            o.acquire += 1           # 丢弃 → 覆盖缺口 → 回问
        elif policy in ("rework_free", "rework_constrained"):
            o.compute += 1
            if rework_ok and has_claim:
                if rework_corrupt:
                    o.corrupt += 1   # 通过了符号判据，但内容是假的
                if rework_vivid:
                    o.review += 1
            else:
                o.acquire += 1       # 返工失败，退回兜底
        else:
            raise ValueError(policy)
    return o


def run_monte_carlo(cfg: Config) -> dict[str, Outcome]:
    rng = random.Random(20261121)
    acc = {p: Outcome() for p in ("gate", "rework_free", "rework_constrained")}
    free_cfg = Config(**{**cfg.__dict__, "s": 0.10})  # 无约束返工：10% 静默造假
    for _ in range(cfg.seeds):
        draws = draw_facts(rng, cfg)
        for policy in acc:
            use_cfg = free_cfg if policy == "rework_free" else cfg
            one = evaluate(draws, policy, use_cfg)
            a = acc[policy]
            a.acquire += one.acquire / cfg.seeds
            a.review += one.review / cfg.seeds
            a.corrupt += one.corrupt / cfg.seeds
            a.compute += one.compute / cfg.seeds
    return acc


def analytic_break_even(cfg: Config) -> dict:
    """解析解：返工降低的回问成本 vs 新增的核对卡成本 vs 静默造假代价。"""
    per_bad_saving = cfg.c_acquire - cfg.r * cfg.c_review
    crit_lam = per_bad_saving / cfg.s if cfg.s > 0 else float("inf")
    return {
        "每次成功返工省下的回问成本": round(per_bad_saving, 2),
        "每个 block 的期望净收益": round(
            cfg.p_coverable * cfg.q * per_bad_saving, 2
        ),
        "无约束返工的造假临界权重 λ*": round(crit_lam, 1) if cfg.s > 0 else "∞（约束返工不造假，恒成立）",
        "结论": (
            "约束返工 s=0：任何 λ 下都严格占优"
            if cfg.s == 0 else
            f"无约束返工：λ < {crit_lam:.1f} 时降负担，λ 更大时质量损失反超"
        ),
    }


def constrained_rework_example() -> None:
    """用真实判据验证：受约束返工只重组已核验素材，不引入新事实。"""
    spec = GroundTruth()
    spec.add_message(Message("a", "user", "voice", "1998年我在镇上的供销社上班，后来供销社就没了。"))
    spec.add_message(Message("b", "user", "text", "我妈走得早。"))
    spec.ingest_claim(Claim("k1", "1998年我在镇上的供销社上班。", "镇上的供销社", "a", "工作"))
    spec.ingest_claim(Claim("k2", "后来供销社就没了。", "后来供销社就没了", "a", "工作"))

    bad = Sentence(
        "1998年我在镇上的供销社上班，那时候我七岁，柜台后面总放着一台老收音机，后来供销社就没了。",
        ("k1", "k2"),
    )
    before = concrete_grounded(Draft(chapters={"工作": [bad]}), spec)
    print("  [返工前] 具体细节:", [d.message for d in before] or "无")

    # 受约束返工：只把同一阶段的已核验 claim 文本拼接，禁止新增任何 token
    parts = [spec.claim(cid).text.rstrip("。") for cid in bad.claim_ids if spec.claim(cid)]
    rebuilt = Sentence("，".join(parts) + "。", bad.claim_ids)
    after = concrete_grounded(Draft(chapters={"工作": [rebuilt]}), spec)
    vivid = narrative_vividness_flag(Draft(chapters={"工作": [rebuilt]}), spec)
    print("  [返工后] 正文:", rebuilt.text)
    print(f"  [返工后] block={len(after)}, flag={len(vivid)}（若触发 flag，仍带完整凭证链交人）")


def main() -> None:
    print("=" * 78)
    print("实验 1：三种策略的人工负担（p_bad=0.25, q=0.70, r=0.25, c_a=10, c_r=1）")
    print("=" * 78)
    acc = run_monte_carlo(CFG)
    lam_demo = 10.0
    print(f"{'策略':<20}{'回问次数':>10}{'核对卡':>10}{'静默造假':>10}{'LLM调用':>10}{'人工负担':>12}{'目标值λ=10':>13}")
    for name, label in (
        ("gate", "闸门+兜底"),
        ("rework_free", "闸门+自由返工"),
        ("rework_constrained", "闸门+约束返工"),
    ):
        o = acc[name]
        objective = o.burden + lam_demo * o.corrupt
        print(f"{label:<20}{o.acquire:>10.2f}{o.review:>10.2f}{o.corrupt:>10.2f}{o.compute:>10.2f}"
              f"{o.burden:>12.2f}{objective:>13.2f}")

    base = acc["gate"].burden
    print(f"\n  约束返工相对基线的人工负担变化: "
          f"{(acc['rework_constrained'].burden / base - 1) * 100:+.1f}%")

    print("\n" + "=" * 78)
    print("实验 2：Break-even 分析")
    print("=" * 78)
    free_cfg = Config(**{**CFG.__dict__, "s": 0.10})
    for cfg, label in ((CFG, "约束返工 s=0"), (free_cfg, "自由返工 s=0.1")):
        print(f"  [{label}]")
        for k, v in analytic_break_even(cfg).items():
            print(f"    {k}: {v}")

    print("\n" + "=" * 78)
    print("实验 3：成功率 q 的敏感性（约束返工，其余参数不变）")
    print("=" * 78)
    print(f"{'q':>6}{'人工负担':>12}{'相对基线':>12}")
    for q in (0.0, 0.25, 0.5, 0.75, 1.0):
        cfg = Config(**{**CFG.__dict__, "q": q})
        o = run_monte_carlo(cfg)["rework_constrained"]
        print(f"{q:>6.2f}{o.burden:>12.2f}{(o.burden / base - 1) * 100:>+11.1f}%")

    print("\n" + "=" * 78)
    print("实验 4：可依托素材比例 p_coverable 的敏感性（q=0.70）")
    print("=" * 78)
    print(f"{'p_coverable':>12}{'人工负担':>12}{'相对基线':>12}")
    for pc in (0.0, 0.25, 0.5, 0.75, 1.0):
        cfg = Config(**{**CFG.__dict__, "p_coverable": pc})
        o = run_monte_carlo(cfg)["rework_constrained"]
        print(f"{pc:>12.2f}{o.burden:>12.2f}{(o.burden / base - 1) * 100:>+11.1f}%")

    print("\n" + "=" * 78)
    print("实验 5：真实判据下的受约束返工（不是模拟）")
    print("=" * 78)
    constrained_rework_example()


if __name__ == "__main__":
    main()
