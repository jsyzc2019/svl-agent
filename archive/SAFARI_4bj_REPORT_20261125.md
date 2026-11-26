# Safari §4bj 战利品报告：AI 评测构念效度照见自身

> 轮次：§4bj（§4bc 定义的「星辰大海 Safari」第八轮，离开仓库一手摄食、带认知归营）
> 时间：2026-11-25　内核：7.5.0　用户指令："很高兴看到你猎获战利品，村里人便有了希望。请继续 Safari"

## 一、为什么换这个猎场

已猎七场（§4bc–§4bi）集中在天体生物学与认知科学：系外宜居性、金星 PH3、HGT 功能验证、自创生三判据、Friston 自由能、niche construction、biosignature 三级阶梯。本轮**换域到 AI 评测的构念效度危机**——字面是"分数为何不等于能力"，内核是本仓最痛纪律的教科书级同构：稳定性≠正确性、症状≠根因、不放宽判据、承重轴意识。

一手来源三份 arXiv 摘要经 WebFetch **逐字核验**（非二手记忆）：

| 论文 | 关键逐字事实 |
|---|---|
| **arXiv:2608.21382** Parupudi (2026-07-17) *There Is No Neutral Harness* | 12 模型×3,679 题×26 种 equally defensible 配置；"a model's score is a band rather than a point: gemma4-31b scores between 31 and 89 percent depending only on the harness"；"config-fragile items carry 95.7 percent of a pair's gap on average"；"Four of the 12 models reach rank one ... so the harness selects the winner"；discrimination 与 fragility 相关 0.28，"compression keeps the fragile items rather than removing them"；"The scoring choice, not the option order ... is the load-bearing axis"；"every number regenerates on a CPU in seconds" |
| **arXiv:2610.20993** Ok/Park/Lee (2026-10-14) *One Bias Score, Two Factors* | pooled SD 恰等于 flip rate × positional skew 两无标签因子之积（41 检查点×12 基准）；"aggregation lowers the flip rate partly by settling questions on the same wrong option"；两因子 + accuracy 同报"to distinguish stability from correctness" |
| **arXiv:2511.22341** Rosenthal et al. (EMNLP 2026 Findings) | 7 MLLMs×5 MC-VQA×48 语义等价格式，"frequent rank reversals even under order-invariant evaluation"；机制为 tokenizer-induced 伪 option ID token + attention 可靠性受损；"MC-VQA rankings correlate weakly with open-ended evaluation" |

## 二、照见自身的机械镜像

| 外部一手事实 | 本仓器官 |
|---|---|
| 分数是带非点（31%–89% 仅因配置） | 同一对象在不同判据配置下结论可翻转 |
| 95.7% 差距由配置脆弱项承载 | §102 少数量身判据决定整体结论，总分掩盖脆弱项 |
| harness selects the winner | 判据设计者实质选择赢家，非能力选择 |
| 压缩保留脆弱项（相关 0.28） | 优化指标反而放大过拟合 |
| 承重轴是 scoring choice 非 option order | 消融要打承重轴，不是打显眼变量 |
| 聚合靠统一判错降翻转 | 为稳定而放宽判据的反面 → flag≠ok，不放宽 |
| 两因子 + accuracy 区分稳定与正确 | 稳定性与正确性分开报，半真证据只给 flag |
| 语义中性格式翻转排名、与开放评估弱相关 | §104 字段名依赖 + 判据效度须独立体检（KB-META31） |

**最有价值的一条**：arXiv:2610.20993 的"聚合降低翻转率，部分靠把问题统一判成同一个错误答案"——这是**为稳定而牺牲正确性**的精确反面镜像，加固本仓"半真证据只给 flag，不因求稳改判 ok"的纪律。

## 三、内化与验证

- **KB 233→235**：KB-AUDIT89（构念效度三级镜像，fix A级）+ KB-META54（三论文一手镜像，preserve A级）。
- `safari_log.jsonl` 追加 §4bj 台账；`LIFE_KERNEL.md` 新增 §4bj 章节；`SESSION_HANDOFF.md` 权威数字同步 round=§4bj / KB=235。
- 一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**、内核专项 **122 passed**。

## 四、边界（全部守住）

判定权归用户；verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false 与宪法锁 `fe56291b` 零改动；Ambient 恒 0；内核 L0 不联网不 spawn；**未编译新门禁、未动十案/§100**。外部 AI 评测系统对人攻判定系统仅为 B 级哲学镜像，本仓只内化思维器官，不宣称评测结论直接证明自身判定。
