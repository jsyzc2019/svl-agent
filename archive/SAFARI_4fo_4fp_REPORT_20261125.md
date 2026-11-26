# Safari 阶段战利品报告 · §4fo–§4fp（2026-11-25）

> 用户令："继续" → 从 MNAR 线索接上，本批聚焦「缺失机制与代理判据」——MNAR 缺失、预测驱动推断。均 A 级一手、PubMed E-utilities 逐字核验。

## 一、本批战利品（方法学链条，均 A 级一手逐字核验）

| 轮次 | 主题 | 一手来源 | 逐字锚点（摘要原文） | 镜像本仓 |
|---|---|---|---|---|
| §4fo | MNAR 缺失机制 | Hazewinkel et al. 2022, Stat Med, PMID 35098576（A 级一手方法学 + CoBalT RCT 469 人/46 月） | 「extreme outcome values are more likely to drop out」；「estimates from CCA and MI will be biased」；「relies on two assumptions…strong MNAR and location shift」；「MI estimates closer to the null and TM estimates further from the null than CCA」 | 缺失与结果相关会高估通过态；常规补全也有偏；须显式假设+偏差方向+敏感性谱 |
| §4fp | 预测驱动推断 | Song et al. 2026, Harv Data Sci Rev, PMID 42921300（A 级一手方法学综述 + MOSAIKS 实证） | 「treating predictions as ground truth introduces bias, while ignoring them wastes information」；「double-dipping…leads to anti-conservative confidence intervals and below-nominal coverage」；「Under MNAR…all methods…yield biased estimates」 | 预测非真值也非噪声；须标注集显式校正；防数据重叠；MNAR 下无一判据无偏 |

## 二、照见自身（判定红线）

1. **缺失高估通过态**：§4fo「extreme outcome more likely to drop out」——判定集若系统性排除极端/失败个案，通过态被高估（§4fe、§4bn、§4fj）。
2. **常规补全也有偏**：「CCA and MI will be biased」——不可用「只看有数据的样本」当无偏（§4fl、§4ff）。
3. **不可检验假设须显式**：任何缺失处理都依赖假设，须声明并推导违反时偏差方向（§4bl、§4fh、§4fa）。
4. **敏感性谱**：「MI closer to null, TM further from null」——须做缺失处理敏感性谱而非报单一（§4fg、§4fk）。
5. **预测非真值非噪声**：§4fp「treating predictions as ground truth introduces bias, while ignoring them wastes information」——代理判据/AI 预测须当「需校正的信号」（§4eq、§4fl、§4fm）。
6. **防双重 dipping**：同一数据既生成判据又验证判据会过度自信、覆盖率不达标（§4ca、§4fh、§4fb）；须留人工/权威核验子集做显式校准（§4ch、§4fa）。
7. **MNAR 下无一无偏**：「all methods…yield biased estimates」——不可声称任一判据「无偏」，只能报假设与敏感性（§4fo、§4fg）。

## 三、诚信现场复现

- double-dipping 导致「anti-conservative / below-nominal coverage」、MNAR 下「all methods biased」等负面结论如实照录，不美化。
- 缺失处理与预测校正均作「敏感性/校正工具」而非唯一真值，如实照录；数字全取一手摘要逐字。

## 四、验证（全绿）

```
一致性 True | failed=[] | handoff 437 = truth 437
内核 7.5.0 | KB 437（重复 0，KB-AUDIT190 / KB-META155）| 宪法锁 fe56291b | 台账 118 末 §4fp
全量 1551 fail=0 err=0 | 内核专项 122 fail=0 err=0
verdict GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
```

## 五、边界

判定权归用户；内核 L0 不联网不 spawn；未编译新门禁；未动宪法/判定/十案/§100。外部一手仅作哲学镜像，不宣称本仓有同样 MNAR 或 ML 标注数据结构。
