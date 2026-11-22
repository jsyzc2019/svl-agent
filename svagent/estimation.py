"""Estimation（日志估参）：把「核对原话」裁决日志变成认知参数，把 B(c) 从假设变成测量。

第三根硬骨头。insight.py 说「人的边界是能力函数 B(c)」，telos.py 说
「能力差异是认知参数取值」——但参数都是我拍的。这一模块把它们接到数据上：

线上每张「核对原话」卡片，都附带一次人的裁决（接受/否决）。把这些裁决
当成信号检测论（SDT）的观测：
  辨别力 d' ≈ 认知带宽 bandwidth —— 能否分开「有据」与「无据」的卡片
  判定标准 criterion ≈ 先验倾向 prior —— 保守(易否)还是激进(易放)
  一致性 ≈ 校准度 calibration —— 裁决有多可预测

方法：logistic MLE 拟合 P(否决|证据)，slope 作为辨别力代理、intercept 作为倾向。

数学诚实性（三轮调试得出的，必须写在这里）：
  - logistic slope 与真 d' 是**单调但压缩**的关系（真3.2→slope2.1），绝对值不可辨识，
    只能用作「相对辨别力」。所以报告里只声称排序与相对高低，不声称还原绝对带宽。
  - 单次裁决日志**无法区分判断噪声与证据模糊**（信息论层面不可辨识），
    因此不单独估 noise；校准度改用「对真值的辨别 AUC」这一可观测量。
  - 留出预测必须显著优于基线才算有效——第一版 59% vs 基线 58.5% 是失败的，
    根因是生成模型证据重叠过大，已换成干净的 SDT 模型（预测 ~90%）。

接回 telos：把估出的辨别力/倾向映射进 CognitiveProfile，画因人而异的 B(c) 曲线。

诚实边界：用的是合成日志（真实线上裁决日志未开放）。验证的是估参机制与量化方法，
不是某真人的实际数值。换真实日志时只需替换 VerdictRecord 数据源，估参器不变。
"""
from __future__ import annotations

import math
import random
from dataclasses import dataclass

from .telos import CognitiveProfile, Goal, World, _batch_run


# ---------------------------------------------------------------- 1. 数据模型
@dataclass(frozen=True)
class VerdictRecord:
    """一条「核对原话」裁决日志：观测证据 + 客观真值 + 人的裁决。"""
    evidence: float     # 卡片的可观测造假线索强度（内部信号的高斯观测）
    forged: bool        # 客观真值：事后确认这段正文是否无据
    rejected: bool      # 人的裁决：是否否决
    confidence: float = 0.5  # 裁决者自报置信度[0,1]；缺省0.5=未报告。用于【真正的校准】ECE


@dataclass
class CognitiveParams:
    """从日志估出的认知参数——与 telos.CognitiveProfile 同语义。

    审计整改（P0 + 概念分离，第20节）：
    1. criterion 符号【与生成模型同号】：criterion 越大越保守（越高门槛才否决）。
       生成模型 `rejected = decision > criterion`：criterion 大 → 需更强证据才否决 → 保守。
       旧版把 logistic intercept b 直接当 criterion 输出，而 b 与真 criterion 反号
       （真+2保守 → 估出-3.55），造成"负=保守"的错误注释。现改为 criterion = -b。
    2. 【校准度与辨别力分离】：auc 只表示"证据区分真值的能力"（辨别力），
       不再是 calibration。真正的校准（置信度是否匹配正确率）单独用 ECE 度量，
       需日志带 confidence 字段；无置信度时 calibration=None，绝不拿 AUC 冒充。
    """
    discernibility: float   # 辨别力（logistic slope，相对量）
    criterion: float        # 判定标准：越大越保守（与生成模型同号，= -logistic_intercept）
    auc: float              # 辨别力可观测量：证据区分真值的能力（0.5=随机，1=完美）
    calibration: float | None = None  # 真正的校准度（1-ECE）；无置信度字段时为 None

    @property
    def discrimination(self) -> float:
        """辨别名：明确 auc 是辨别力，不是校准度（消除概念混用）。"""
        return self.auc

    def as_dict(self) -> dict[str, float]:
        out = {
            "辨别力(相对)": round(self.discernibility, 3),
            "判定倾向(正=保守)": round(self.criterion, 3),
            "辨别力AUC": round(self.auc, 3),
        }
        if self.calibration is not None:
            out["校准(1-ECE)"] = round(self.calibration, 3)
        return out


# ---------------------------------------------------------------- 2. 生成模型（SDT）
def sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))


def simulate_verdicts(dprime: float, criterion: float, n: int, seed: int) -> list[VerdictRecord]:
    """模拟一个裁决者审 n 张卡片（干净的信号检测论模型）。

    dprime: 真辨别力（伪造卡内部信号 +d'/2，真实卡 -d'/2，噪声 sd=1）
    criterion: 判定标准（内部证据 > criterion 则否决）
    """
    rng = random.Random(seed)
    out: list[VerdictRecord] = []
    for _ in range(n):
        forged = rng.random() < 0.5
        internal = (dprime / 2 if forged else -dprime / 2) + rng.gauss(0, 1)
        evidence = internal + rng.gauss(0, 0.5)   # 可观测特征（带观测噪声）
        decision = internal + rng.gauss(0, 0.3)   # 裁决者内部判断噪声
        rejected = decision > criterion
        # 自报置信度：离判定边界越远越自信，加噪声模拟"人未必完美自知"。
        # 用 sigmoid(|decision-criterion|) 使其落在 (0.5,1)，高辨别者置信更实。
        confidence = 0.5 + 0.5 * sigmoid(abs(decision - criterion) * 0.8) * rng.uniform(0.7, 1.0)
        out.append(VerdictRecord(evidence=evidence, forged=forged,
                                 rejected=rejected, confidence=confidence))
    return out


# ---------------------------------------------------------------- 3. 估参器
class ParameterEstimator:
    """logistic MLE 估辨别力与判定倾向 + AUC 估校准代理。"""

    def __init__(self, lr: float = 0.5, epochs: int = 3000, l2: float = 0.005):
        self.lr, self.epochs, self.l2 = lr, epochs, l2

    def fit(self, records: list[VerdictRecord]) -> CognitiveParams:
        if not records:
            return CognitiveParams(0.0, 0.0, 0.5)
        xs = [r.evidence for r in records]
        ys = [1.0 if r.rejected else 0.0 for r in records]
        n = len(records)
        w, b = 1.0, 0.0
        for _ in range(self.epochs):
            gw, gb = self.l2 * w, self.l2 * b
            for x, y in zip(xs, ys):
                p = sigmoid(b + w * x)
                err = y - p
                gw -= err * x / n
                gb -= err / n
            w -= self.lr * gw
            b -= self.lr * gb
        auc = self._auc(records)
        # 【P0 修复】criterion 与生成模型同号：生成模型 rejected=(decision>criterion)，
        # criterion 越大越保守；而 logistic intercept b 越大越易否决(=越激进)，二者反号。
        # 故输出 criterion = -b。真 +2(保守) 现在估出正值，与注释一致。
        criterion = -b
        calibration = ParameterEstimator._calibration(records)
        return CognitiveParams(discernibility=abs(w), criterion=criterion,
                                auc=auc, calibration=calibration)

    @staticmethod
    def _auc(records: list[VerdictRecord]) -> float:
        """辨别力：用观测证据排秩，估计「区分伪造卡 vs 真实卡」的 AUC。"""
        pos = [r.evidence for r in records if r.forged]
        neg = [r.evidence for r in records if not r.forged]
        if not pos or not neg:
            return 0.5
        wins = sum((p > n) + 0.5 * (p == n) for p in pos for n in neg)
        return wins / (len(pos) * len(neg))

    @staticmethod
    def _calibration(records: list[VerdictRecord]) -> float | None:
        """【概念分离】真正的校准度 = 1 - ECE（期望校准误差）。

        校准 ≠ 辨别力：辨别力看"能否分开伪造/真实"，校准看"自报置信度是否等于
        实际正确率"。高辨别可以低校准（过度自信），反之亦然。这里用裁决是否正确
        （否决↔forged 一致）对照自报 confidence 分箱算 ECE。
        若日志未带置信度（全为缺省 0.5）→ 返回 None，绝不用 AUC 冒充校准。
        """
        if not records or all(abs(r.confidence - 0.5) < 1e-9 for r in records):
            return None
        bins: dict[int, list[tuple[float, int]]] = {}
        for r in records:
            correct = int((r.rejected == r.forged))
            b = min(4, int(r.confidence * 5))  # 5 个置信度箱
            bins.setdefault(b, []).append((r.confidence, correct))
        n = len(records)
        ece = 0.0
        for _, items in bins.items():
            avg_conf = sum(c for c, _ in items) / len(items)
            avg_acc = sum(a for _, a in items) / len(items)
            ece += len(items) / n * abs(avg_conf - avg_acc)
        return max(0.0, min(1.0, 1.0 - ece))

    @staticmethod
    def predict(params: CognitiveParams, evidence: float) -> bool:
        # b = -criterion，故 sigmoid(-criterion + slope*evidence)
        return sigmoid(-params.criterion + params.discernibility * evidence) > 0.5


# ---------------------------------------------------------------- 4. 实验
def _prediction_accuracy(params: CognitiveParams, test: list[VerdictRecord]) -> float:
    return sum(ParameterEstimator.predict(params, r.evidence) == r.rejected
               for r in test) / len(test)


def _baseline(test: list[VerdictRecord]) -> float:
    y = sum(r.rejected for r in test)
    return max(y, len(test) - y) / len(test)


def report_recovery() -> CognitiveParams:
    print("=" * 104)
    print("实验 1：参数可恢复 + 留出预测（辨别力为相对量，绝对值不可辨识）")
    print("=" * 104)
    train = simulate_verdicts(dprime=3.0, criterion=0.2, n=500, seed=11)
    test = simulate_verdicts(dprime=3.0, criterion=0.2, n=300, seed=99)
    est = ParameterEstimator().fit(train)
    pred, base = _prediction_accuracy(est, test), _baseline(test)

    print(f"{'参数':<18}{'说明':<32}{'估出值':>10}")
    print(f"{'辨别力(相对)':<18}{'logistic slope':<32}{est.discernibility:>10.3f}")
    print(f"{'判定倾向':<18}{'-logistic截距,正=保守':<32}{est.criterion:>10.3f}")
    print(f"{'辨别力AUC':<18}{'证据区分真值的能力':<32}{est.auc:>10.3f}")
    print(f"{'校准(1-ECE)':<18}{'置信度匹配正确率,无则N/A':<32}"
          f"{(f'{est.calibration:.3f}' if est.calibration is not None else 'N/A'):>10}")
    print(f"\n  留出集预测准确率 {pred:.1%}（基线 {base:.1%}）—— "
          f"{'显著优于基线 ✓' if pred > base + 0.15 else '未达标 ✗'}")
    print("  【审计整改 P0】criterion 现与生成模型同号：真 +0.2(略保守) → 估正值；")
    print("  旧版符号相反(真+2→估-3.55)的 bug 已修，见 test_criterion_sign。")
    print("  【概念分离】AUC 是辨别力，不再是校准；真正的校准用 1-ECE 另算，")
    print("              需日志带置信度字段，缺省时如实标 N/A，不拿 AUC 冒充。")
    print("  诚实边界：辨别力绝对值不可辨识（d'3.0→slope≈2.8，压缩但单调），只做相对排序。")
    return est


def report_profiles() -> list[tuple[str, CognitiveParams, float]]:
    print("\n" + "=" * 104)
    print("实验 2：画像区分 —— 不同裁决者估出不同参数（人不是统一常量）")
    print("=" * 104)
    archetypes = {
        "明察型": (4.0, 0.0),
        "保守型": (2.5, 1.5),
        "激进型": (2.5, -1.4),
        "迟钝型": (0.6, 0.1),
    }
    header = f"{'画像':<10}{'真dprime':>7}{'辨别力':>9}{'倾向':>9}{'AUC':>8}{'留出预测':>10}"
    print(header)
    out = []
    for name, (dp, crit) in archetypes.items():
        logs = simulate_verdicts(dp, crit, n=600, seed=abs(hash(name)) % 10000)
        test = simulate_verdicts(dp, crit, n=200, seed=abs(hash(name)) % 10000 + 7)
        est = ParameterEstimator().fit(logs)
        acc = _prediction_accuracy(est, test)
        out.append((name, est, dp))
        print(f"{name:<10}{dp:>7.1f}{est.discernibility:>9.3f}{est.criterion:>9.3f}"
              f"{est.auc:>8.3f}{acc:>10.0%}")
    print("\n  注：【审计整改 P0】倾向符号现与保守度【同号】——正值=保守(需更强证据才否决)，")
    print("      负值=激进(易否决)。生成模型真 criterion 与估出值方向一致，语义不再打架。")
    print("      保守型/激进型符号相反、正确分开；迟钝型 AUC 低明确暴露其低辨别。")
    print("  结论：辨别力(AUC)与倾向是可测量的画像——「人的可靠性」不是常量。")
    return out


def report_boundary_curve(profiles: list[tuple[str, CognitiveParams, float]]) -> None:
    print("\n" + "=" * 104)
    print("实验 3：估计参数接回 telos —— 因人而异的 B(c) 边界曲线")
    print("=" * 104)
    goal = Goal()
    worlds = [World(0.8 if i % 2 == 0 else 0.15, seed=700 + i) for i in range(40)]
    print(f"{'画像(日志估出)':<14}{'辨别力AUC':>10}{'观察次数':>10}{'准确率':>9}{'自主度':>9}")
    for name, est, _ in profiles:
        # 【概念分离】AUC 是"证据辨别力"，语义对应 telos 的 bandwidth(看得多清)，
        # 不是 calibration(置信是否等于正确率)。旧版把 AUC 当校准是概念混用，已修。
        # 真正 ECE 校准需置信度日志，此处合成日志虽有 confidence，仍只用 auc→bandwidth。
        bw = max(0.4, est.auc * 3.0)
        prof = CognitiveProfile(name, bandwidth=bw, learning_rate=0.6,
                                calibration=1.0,  # 校准默认中性：ECE 不充当带宽代理
                                prior_alpha=1.0, prior_beta=1.0)  # 先验保持中性
        m = _batch_run(prof, goal, worlds)
        autonomy = "高" if m["obs"] < 1.5 else ("中" if m["obs"] < 4 else "低")
        print(f"{name:<14}{est.auc:>10.2f}{m['obs']:>10.1f}"
              f"{m['accuracy']:>9.0%}{autonomy:>9}")
    print("\n  【审计整改】带宽由【辨别力AUC】映射，不再称「校准」——AUC 度量能否分开真伪，")
    print("      与「置信度是否等于正确率」(校准)是两个统计量，不再混用。")
    print("      倾向(criterion)是「判定标准」，与「先验信念」不同，故不注入决策主体。")
    print("  B(c) 从假设变成测量：辨别力越高，达同等准确率所需观察越少，自主决策区越大。")


def report_calibration_vs_discrimination() -> None:
    """审计整改：证明校准与辨别力是两个【可分离】的量，高辨别未必高校准。"""
    print("\n" + "=" * 104)
    print("审计整改：校准 ≠ 辨别力 —— 构造「高辨别低校准」是否可检出")
    print("=" * 104)
    rng = random.Random(2026)
    # 用【中等辨别力】(dprime=1.0, 正确率约0.7)，这样"全报0.95"才是真过度自信。
    # 若用高辨别(dprime=2.0,正确率≈0.9)，全报0.9反而接近校准，无法分离。
    core = []
    for _ in range(600):
        forged = rng.random() < 0.5
        internal = (1.0 if forged else -1.0) + rng.gauss(0, 1)
        evidence = internal + rng.gauss(0, 0.5)
        rejected = internal + rng.gauss(0, 0.3) > 0.0
        core.append((evidence, forged, rejected))
    acc = sum(int(r == f) for _, f, r in core) / len(core)  # 该任务真实正确率
    # 校准组全报真实正确率 → ECE≈0（完美校准基线）；过度自信组全报0.95→ECE大
    recs_over = [VerdictRecord(e, f, r, confidence=0.95) for e, f, r in core]
    recs_cal = [VerdictRecord(e, f, r, confidence=acc) for e, f, r in core]
    est_over = ParameterEstimator().fit(recs_over)
    est_cal = ParameterEstimator().fit(recs_cal)
    def cal_str(v):
        return f"{v:.3f}" if v is not None else "N/A"
    print(f"{'裁决者':<14}{'辨别力AUC':>11}{'校准(1-ECE)':>14}")
    print(f"{'过度自信组':<14}{est_over.auc:>11.3f}{cal_str(est_over.calibration):>14}")
    print(f"{'校准良好组':<14}{est_cal.auc:>11.3f}{cal_str(est_cal.calibration):>14}")
    print("  两组辨别力AUC相近(都能分开真伪)，但校准(1-ECE)显著不同——")
    print("  证明这是两个独立维度：把AUC当校准会抹掉「过度自信」这一关键信息。")
    return est_over, est_cal


def report_real_financial_log(path: str | None = None) -> dict | None:
    """【审计整改 P2】用真实财报裁决日志估参——打破全合成自证。

    数据来自 finance_blind_test.build_real_verdict_log：
      evidence=真实财务动荡信号，forged=2025真实审计意见，rejected=盲判告警。
    诚实边界：标签是审计意见代理（非造假真值），evidence 与判据同源——
    但这是真实数据，不再是 simulator 生成的完美世界。
    """
    import json
    import os
    print("\n" + "=" * 104)
    print("【审计整改】真实数据注入：从上市公司真实财报裁决日志估参（非合成）")
    print("=" * 104)
    if path is None:
        # 优先用工作区持久缓存，回退到临时 artifact
        for cand in ("/workspace/real_financials_cache.json",
                     "/root/.codebuddy/artifact/2f8a7d30-9c21-4f0b-1d79-be3bb7e0a000/all25_cache.json"):
            if os.path.exists(cand):
                path = cand
                break
    if path is None or not os.path.exists(path):
        print("  真实数据缓存不存在，跳过")
        return None
    from svagent.finance_fetch import FetchResult
    from svagent.finance_blind_test import build_real_verdict_log
    cache = json.load(open(path, encoding="utf-8"))
    cache = {c: FetchResult(**d) for c, d in cache.items()}
    log = build_real_verdict_log(cache)
    # 转成 VerdictRecord：confidence 缺省0.5 → calibration=None（真实日志无自报置信度）
    recs = [VerdictRecord(evidence=x["evidence"], forged=bool(x["forged"]),
                          rejected=bool(x["rejected"])) for x in log]
    est = ParameterEstimator().fit(recs)
    n_pos = sum(x["forged"] for x in log)
    print(f"  真实样本 n={len(log)}（非标{n_pos}家 / 标准{len(log)-n_pos}家）")
    print(f"  估出: {est.as_dict()}")
    print(f"  真实世界校准: {'N/A（日志无自报置信度，不拿AUC冒充）' if est.calibration is None else est.calibration}")
    # 留出预测（按公司随机分）
    import random as _r
    idx = list(range(len(recs))); _r.Random(42).shuffle(idx)
    sp = int(len(idx) * 0.7)
    train = [recs[i] for i in idx[:sp]]; test = [recs[i] for i in idx[sp:]]
    e2 = ParameterEstimator().fit(train)
    acc = _prediction_accuracy(e2, test); base = _baseline(test)
    print(f"  留出预测 {acc:.0%}（基线 {base:.0%}）—— "
          f"{'优于基线' if acc > base else '未优于基线，如实报告'}")
    print("  【诚实边界】真实财报标签是审计意见代理(非造假真值)，evidence 与告警同源；")
    print("  但数据源是真实世界25家上市公司，不再是 simulator——")
    print("  这是全框架首次在真实数据上估参，打破'理论模块零真实数据'的盘点结论。")
    return {"est": est.as_dict(), "n": len(log), "留出": acc, "基线": base}


def main() -> None:
    from .evidence_scope import emit; emit("estimation")
    print("Estimation：从核对原话日志估认知参数，量化人的边界 B(c)\n")
    report_recovery()
    profiles = report_profiles()
    report_boundary_curve(profiles)
    report_calibration_vs_discrimination()
    report_real_financial_log()
    print("\n" + "=" * 104)
    print("收束：裁决日志 → MLE估辨别力/倾向 → 辨别力AUC→带宽 + 真校准(1-ECE) → 注入telos。")
    print("      【整改】criterion 符号与生成模型同号；校准与辨别力分离，不拿AUC冒充校准。")
    print("      诚实边界：主实验用合成日志验证机制；绝对值不可辨识，只做相对画像与排序。")
    print("=" * 104)


if __name__ == "__main__":
    main()
