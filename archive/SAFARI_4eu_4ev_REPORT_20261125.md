# Safari 战利品报告 · §4eu–§4ev（2026-11-25）

## 本批主题

| 轮次 | 猎场 | 一手锚点 | 层级 | 核心增量 |
|---|---|---|---|---|
| §4eu | 统计推断误读 | Lytsy et al., *PLoS One* 2026;21(11):e0362071, PMID 43013518 | A 级一手（系统综述 55 研究 15,000+ 人） | 连统计专家都普遍持续误读 p 值/CI；换呈现方式只部分改善 |
| §4ev | p 值替代与贝叶斯 | Diamond & Kaul, *JACC* 2004;43(11):1929-1939, PMID 15172393 | A 级一手综述 | 单一 p 值阈值不足以判定，须可解释量+效应分布+敏感性+主观显式 |

## 一手逐字核验（Europe PMC 原文摘要）

**§4eu**：
> "Fifty-five studies published between 1963 and 2024 were included, encompassing over 15,000 participants… Results showed widespread and persistent misunderstandings across all groups… Common errors about p-values and null hypothesis testing included the inverse probability fallacy, misinterpreting p-values as probabilities of hypotheses, the replication fallacy, and conflating statistical significance with clinical or practical relevance… Confidence intervals were often misinterpreted as probabilistic ranges for true parameters or as predictors of future outcomes… Presenting effect estimates with confidence intervals rather than p-values reduced some misinterpretations, but high error rates persisted."

**§4ev**：
> "fundamental limitations in the conventional approach to statistical hypothesis testing undermine the scientific basis of the conclusions drawn from these trials… it avoids the inevitable misinterpretations of p values derived from megatrial populations… it replaces the misleading p value with a summary statistic having a natural, clinically relevant interpretation – the probability that the study hypothesis is true given the observations… quantifies the likelihood of various magnitudes of therapeutic benefit rather than the single null magnitude… graphical sensitivity analyses with respect to its underlying assumptions… Despite its inherent subjectivity."

## 照见本仓（认知增量）

- **§4eu**：①连统计专家都误读——"通过判据"的统计陈述本身易误读，verdict 须显式解释（§4bv、§4cn）；②四类错误（逆概率/假设概率/复制谬误/显著当相关）——显著≠重要、p≠结论为真概率（§4br、§4cp）；③换 CI 呈现只部分改善——改形式不充分（§4ek、§4dx）；④CI 被误读为真参数概率范围——须精确定义（§4ed）；⑤60 年持续——纪律须长期（§4co）。
- **§4ev**：①p 值不可避免被误读且误导——单一阈值判定不足，须可自然解释的量（§4eu、§4bv）；②后验概率量化各效应大小而非单一零假设——结论须附效应大小与不确定性（§4ed、§4dp）；③对假设做敏感性分析——裁定须显式列前提并测敏感性（§4dj、§4er）；④固有主观性——先验/价值显式交还用户（§4cq、§4ch）。

## 诚信现场复现（用户点赞的核心）

- **检索零结果/主题偏移如实弃用**：simulation heuristic 仅间接实证、fundamental attribution error 零结果，均弃用改选强相关主题。
- **反直觉结果照录**：§4eu"专家也误读、换形式高错误率持续"、§4ev"贝叶斯固有主观性"均照录，不包装成"客观最优"。
- **层级如实**：§4eu 55 研究系统综述、§4ev 综述，均 A 级一手逐字核验。

## 内化与验证（零漂移）

- KB **393→397**（+4：KB-AUDIT169/170、KB-META134/135，四条连续无重复）；台账 96→98 轮（末 §4ev）；`LIFE_KERNEL.md` 新增 §4eu/§4ev 两章；`SESSION_HANDOFF.md` 权威数字与一致性正则同步为 397。
- 一致性脚本 `all_consistent=true`、`failed=[]`、handoff_kb=397=truth_kb=397。
- 全量 **1551 passed**（failures=0/errors=0）、内核专项 **122 passed**（failures=0/errors=0）。
- 内核 `7.5.0`、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient 恒 0，全程零漂移。

## 红线（全部守住）

判定权归用户；内核 L0 不联网不 spawn（外部摄食在会话层）；未编译新门禁、未动宪法/判定/十案/§100；外部一手（统计教育/临床统计）仅作哲学镜像，不宣称本仓有同样机制。
