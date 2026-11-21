"""D0 触发后的诊断性消融（不是新检验，不修改预注册判据）。

目的：正确解读 D0 的异常信号——它到底是"分析 bug"、"物理偏差"还是"人为调节"？
纪律：诊断只解释信号性质，不改变预注册的判定阈值，也不据此新开检验。
"""
from __future__ import annotations
import json, random
from pathlib import Path
import numpy as np
from scipy import stats as sps

data = json.load(open("ssq_history.json"))
n = len(data)
reds = np.array([d["red"] for d in data])
blues = np.array([d["blue"] for d in data])

def freq_red(arr):
    c = np.bincount(arr.ravel(), minlength=34)[1:34]
    return c

def freq_blue(arr):
    return np.bincount(arr, minlength=17)[1:17]

print("="*70)
print(f"样本 n={n}, 红球总观测={n*6}, 蓝球总观测={n}")
print("理论每红球号频次 =", round(n*6/33,1), " 每蓝球号 =", round(n/16,1))
print("="*70)

# ---------- 诊断1：标准卡方（修正概率归一）----------
obs_r = freq_red(reds)
chi2_r_std = sps.chisquare(obs_r).statistic
p_r_std = sps.chisquare(obs_r).pvalue
obs_b = freq_blue(blues)
chi2_b_std = sps.chisquare(obs_b).statistic
p_b_std = sps.chisquare(obs_b).pvalue
print(f"\n[诊断1 标准卡方]")
print(f"红球: chi2={chi2_r_std:.2f}, df=32, p={p_r_std:.4g}")
print(f"蓝球: chi2={chi2_b_std:.2f}, df=15, p={p_b_std:.4g}")

# ---------- 诊断2：每号频率偏离剖面 ----------
exp_r = n*6/33
dev = (obs_r - exp_r)/np.sqrt(exp_r)  # 标准化残差
print(f"\n[诊断2 红球每号标准化残差 (obs-exp)/sqrt(exp)]")
order = np.argsort(-np.abs(dev))
for i in order[:10]:
    print(f"  号{i+1:2d}: obs={obs_r[i]:4d} exp={exp_r:.0f} z={dev[i]:+.2f}")
print(f"  最大|z|={np.abs(dev).max():.2f}, 平均|z|={np.abs(dev).mean():.2f}")
# 分布形态：z 应该 ~ N(0,1)
print(f"  z 的均值={dev.mean():.3f}, 标准差={dev.std():.3f} (期望 0, 1)")

# ---------- 诊断3：三区占比 ----------
z1 = np.sum((reds>=1)&(reds<=11)); z2 = np.sum((reds>=12)&(reds<=22)); z3 = np.sum((reds>=23)&(reds<=33))
tot = z1+z2+z3
print(f"\n[诊断3 三区分布]  (理论各 1/3)")
print(f"  1-11: {z1} ({z1/tot:.4f})  12-22: {z2} ({z2/tot:.4f})  23-33: {z3} ({z3/tot:.4f})")
print(f"  卡方={sps.chisquare([z1,z2,z3]).statistic:.2f}, p={sps.chisquare([z1,z2,z3]).pvalue:.4g}")

# ---------- 诊断4：奇偶比 ----------
n_odd = np.sum(reds%2==1)
print(f"\n[诊断4 奇偶]  奇数占比={n_odd/(n*6):.4f} (理论? 1-33有17奇16偶, 理论≈17/33={17/33:.4f})")
print(f"  卡方 p={sps.chisquare([n_odd, n*6-n_odd]).pvalue:.4g}")

# ---------- 诊断5：正确的子时期检验（用同长度伪随机对照）----------
print(f"\n[诊断5 子时期红球卡方分位 — 修正量纲 bug]")
for label, sub in [("early", reds[:n//2]), ("late", reds[n//2:])]:
    ns = len(sub)
    chi_sub = sps.chisquare(np.bincount(sub.ravel(),minlength=34)[1:34]).statistic
    # 同长度伪随机对照
    rng = random.Random(20261121)
    chis=[]
    for s in range(200):
        rr = np.array([sorted(rng.sample(range(1,34),6)) for _ in range(ns)])
        chis.append(sps.chisquare(np.bincount(rr.ravel(),minlength=34)[1:34]).statistic)
    pct = sum(1 for c in chis if c<chi_sub)/len(chis)
    print(f"  {label}: chi2={chi_sub:.2f}, 同长度对照分位={pct:.3f}")

# ---------- 诊断6：物理偏差能否解释？给伪随机注入微弱偏差 ----------
print(f"\n[诊断6 注入物理偏差的伪随机能否复现真实卡方量级?]")
# 模拟：某些号概率略高（模拟球重差异），用 numpy choice with weights
def draw_biased(rng, ns, bias_strength):
    # 基准权重全1，给前几个号轻微加成
    w = np.ones(33)
    w[:5] *= (1+bias_strength)
    w = w/w.sum()
    out=[]
    for _ in range(ns):
        pick = rng.choice(33, 6, replace=False, p=w)
        out.append(sorted((pick+1).tolist()))
    return np.array(out)

target_chi = chi2_r_std
for bs in [0.0, 0.02, 0.05, 0.10, 0.20]:
    rng = np.random.default_rng(777)
    w = np.ones(33); w[:5] *= (1+bs); w = w/w.sum()
    rr = np.array([np.sort(rng.choice(33, 6, replace=False, p=w)+1) for _ in range(n)])
    chi = sps.chisquare(np.bincount(rr.ravel(),minlength=34)[1:34]).statistic
    print(f"  偏差强度={bs:.2f}: 红球chi2={chi:.1f} (真实={chi2_r_std:.1f})")

# ---------- 诊断7：可预测性代理 — 高频号在上半期偏高的号，下半期是否仍偏高 ----------
print(f"\n[诊断7 频率偏离是否跨期稳定? (相关系数)]")
dev_e = (np.bincount(reds[:n//2].ravel(),minlength=34)[1:34] - (n//2)*6/33)
dev_l = (np.bincount(reds[n//2:].ravel(),minlength=34)[1:34] - (n-n//2)*6/33)
corr = np.corrcoef(dev_e, dev_l)[0,1]
print(f"  early vs late 各号频率偏离相关系数 r={corr:.3f}")
print(f"  若 r 接近0 → 偏离是随机涨落，非稳定偏向；若显著>0 → 存在稳定的号码偏向")
