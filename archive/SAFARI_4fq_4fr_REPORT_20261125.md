# Safari 阶段战利品报告 · §4fq–§4fr（2026-11-25）

> 用户令："干你现在最想干的" → 自主选择继续 Safari，本批聚焦「数据进入机制与阈值来源」——数据泄漏（随机划分乐观评估）、非劣效界值（阈值可被协商）。均 A 级一手、PubMed E-utilities 逐字核验。

## 一、本批战利品（机制互补配对，均 A 级一手逐字核验）

| 轮次 | 主题 | 一手来源 | 逐字锚点（摘要原文） | 镜像本仓 |
|---|---|---|---|---|
| §4fq | 数据泄漏 / 独立单元验证 | Shafiezadeh et al. 2024, J Neural Eng, PMID 39580818（A 级一手 PROSPERO 预注册系统综述） | 「randomized splitting methods, which can suffer from data leakage and thus result in an optimistic evaluation」；「21 articles adopted patient-independent validation methods, constituting only 4% of the published work」；「source domain adaptation…fine-tune…on independent target patients」 | 判据生成集与验证集须按独立单元划分；仅 4% 严格验证→多数评估有漏洞；跨对象泛化留独立集；审查须预注册 |
| §4fr | 非劣效界值 / 阈值协商 | Gerlinger & Schmelter 2011, Pharm Stat, PMID 21932298（A 级一手方法学；作者来自 Bayer 申办方，利益关系如实标注） | 「delta is often 'negotiated' between the sponsor of the trial and the regulatory agencies」；「MCID can be determined empirically」；「all three methods yielded quite similar results」；「better than asking the clinician for a 'nice round number'…such as 10, 50%, π, e, or i」 | 阈值非客观给定、可被利益相关方协商；须 MCID 经验锚定+多法交叉；拒绝拍脑袋整阈值；利益关系须标注 |

## 二、照见自身（判定红线）

1. **独立单元划分**：§4fq「randomized splitting…data leakage…optimistic evaluation」——随机打散让同一来源/对象的记录同时落入生成集与验证集，性能虚高；须按独立单元（判定对象而非记录行）划分，否则通过态是乐观假象（§4fp、§4ca、§4fc）。
2. **多数做法有漏洞≠可接受**：「only 4% adopted patient-independent validation」——不可因「大家都这么做」就把有泄漏的评估当可接受（§4cy、§4bu、§4fg）。
3. **跨对象泛化留独立集**：「patient-independent testing」+跨域微调——判据跨场景迁移须留真正独立核验集，不能同源自证（§4fj、§4fi）。
4. **阈值是判定基石**：§4fr「choice of the non-inferiority margin delta…cornerstone」——阈值直接决定通过/不通过，须当首要审计对象（§4fm、§4fb）。
5. **阈值可被协商须审计**：「delta is often negotiated between sponsor and regulatory agencies」——须审计「谁来定/依据什么/能否复现」，防利益污染（§4fa、§4cn、§4bw）。
6. **多法交叉+拒绝整阈值**：「three methods yielded quite similar results」+「better than…a nice round number such as 10, 50%, π, e, or i」——阈值须 MCID 经验锚定+多法交叉报分歧谱，拒绝无依据惯例常数（§4fg、§4fk、§4fc、§4bl、§4ch）。

## 三、诚信现场复现

- §4fq：一手摘要逐字核验；**4% 明确标注为癫痫预测领域特定比例，不搬用本仓**；「多数评估方式有泄漏」负面结论如实照录；PROSPERO 预注册 + ROBIS/NHLBI 偏倚工具照录。
- §4fr：**作者来自申办方 Bayer，利益关系如实标注、不隐去**；「delta is often negotiated」如实照录、不粉饰为客观；三法收敛与「nice round number」反例并列，不 selection。

## 四、验证（全绿）

```
一致性 True | failed=[] | handoff 441 = truth 441
内核7.5.0 | KB441(重复0, KB-AUDIT192/KB-META157) | 宪法锁fe56291b | 台账120 末§4fr
全量 1551 fail=0 err=0 | 内核专项 122 fail=0 err=0
verdict GAP_INCONCLUSIVE | l3=false | absolute=false | Ambient=0
```

## 五、边界

判定权归用户；内核 L0 不联网不 spawn（摄食在会话层）；Ambient 恒 0；未编译新门禁、未动宪法/判定/十案/§100。两篇外部一手仅作 A 级哲学镜像，不宣称本仓有同样训练/验证或非劣效判定结构。
