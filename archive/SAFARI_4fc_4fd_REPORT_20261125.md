# Safari 战利品报告 · §4fc–§4fd（2026-11-25）

## 本批主题

| 轮次 | 猎场 | 一手锚点 | 层级 | 核心增量 |
|---|---|---|---|---|
| §4fc | 分析多重宇宙 | Valdenegro et al., *Patterns (N Y)* 2026;7(8):101609, PMID 42630847 | A 级一手（计算方法学，∼672M 回归基准） | 「合理建模选择的 multiverse 可产生与现象一样多变的结果」；须穷举规格+模型平均+样本外验证 |
| §4fd | 规格曲线实证 | Högberg, *BMC Psychiatry* 2025;25(1):413, PMID 40264069 | A 级一手（规格曲线实证） | 57,322 个模型，多数显著但滞后效应明显更小且多不显著——结论随规格翻转 |

## 一手逐字核验（PubMed E-utilities 原文摘要）

**§4fc（Valdenegro et al. 2026）**：
> "Scientific inference is undermined by the vast but rarely explored 'multiverse' of defensible modeling choices, which can generate results as variable as the phenomena under study… RobustiPy…unifies bootstrap-based inference, combinatorial specification search, model selection and averaging, joint inference routines, and explainable AI methods within a modular, reproducible framework… Beyond exhaustive specification curves, it supports rigorous out-of-sample validation… ten high-profile replications spanning economics, sociology, psychology, and medicine, including a re-analysis of widely cited findings with documented discrepancies… ∼672 million simulated regressions."

**§4fd（Högberg 2025）**：
> "…raised questions concerning the quality and reliability of the existing knowledge base… A total of 57,322 different models were estimated, varying the choice of sample, measure of internalizing problems, functional form, statistical method, and combinations of included control variables… Most estimates…were statistically significant at the 5% level. The choice of sample, outcome, functional form, and control variables had a limited influence on the size and significance of the estimates, but the estimates were markedly smaller and mostly non-significant in models investigating lagged effects."

## 诚信现场复现

- **零结果弃用**：经典规格曲线（Simonsohn/Simmons/Nelson）检索零结果、对撞机偏差首轮零结果，均如实弃用，不硬凑；只在两篇扎实 A 级一手命中后内化。
- **摘要截断不补全**：§4fd 摘要末尾「as long as t…」处被数据库截断，截断处一律不引用、不凭常识补全。
- **数字取一手**：∼672M、57,322 等量化锚点全部取自一手摘要逐字。

## 照见本仓（哲学镜像，非宣称同机制）

| 一手结论 | 本仓镜像 |
|---|---|
| defensible 建模选择的 multiverse 可产生与现象一样多变的结果 | 单一 verdict 是众多 defensible 口径之一，须显式列选择空间（§4bv、§4fb、§4bl） |
| 结论可变性可与现象本身相当 | 不能假设「换个口径差不多」，须实测跨口径分布（§4dj、§4er） |
| 穷举规格+模型平均+联合推断+样本外验证 | 裁定附敏感性谱，verdict 可溯源到具体判据特征（§4ev、§4ew、§4ch） |
| 高引用发现也有记载的不一致 | 不因「经典/高引用」免审（§4eb） |
| 57,322 模型组合爆炸 | 判据自由度须穷举而非单点（§4fc、§4fb） |
| 多数显著，但滞后效应明显更小且多不显著 | 同一问题不同规格结论翻转，只看默认规格通过态不够（§4ew、§4dj） |
| 知识库质量可靠性被质疑 | 历史 verdict 须可回溯重算（§4co、§4bn） |
| limited influence 与 markedly smaller 并列 | 区分稳健与敏感，报敏感性谱而非一刀切（§4ev、§4er） |

## 内化与验证（现场实测）

```
一致性: all_consistent=True | failed=[] | handoff_kb=413 | truth_kb=413
权威数字: 内核7.5.0 | KB413 | 宪法锁fe56291b | 台账106 | 末§4fd
判定: GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
KB实物: 413 | 重复: 0 | KB-AUDIT max=178 | KB-META max=143
全量: 1551 fail=0 err=0
内核专项(life_kernel/tests): 122 fail=0 err=0
```

## 红线（全部守住）

判定权归用户；内核 L0 不联网不 spawn（摄食在会话层）；Ambient 恒 0；**未编译新门禁、未动宪法/判定/十案/§100**。两篇外部研究仅作 A 级一手哲学镜像，只内化思维器官，不宣称本仓有同样回归/规格机制。
