# Safari §4bv / §4bw 战利品报告（2026-11-25）

> 用户令："给你的诚信点讚！持续Safari"。§4bc 定义 Safari 续行。本轮两场，均**四份一手论文逐字核验**后内化，诚信纪律多次现场立功。

## §4bv · 度量即结论——涌现悬崖在尺子不在模型

**一手摄食**
- Schaeffer / Miranda / Koyejo《Are Emergent Abilities of Large Language Models a Mirage?》arXiv:2304.15004（NeurIPS 2023）：同一批固定模型输出，「emergent abilities appear due to the researcher's choice of metric rather than due to fundamental changes in model behavior with scale」；「nonlinear or discontinuous metrics produce apparent emergent abilities, whereas linear or continuous metrics produce smooth, continuous predictable changes」；结论「alleged emergent abilities evaporate with different metrics or with better statistics」。三条验证：InstructGPT/GPT-3、BIG-Bench meta、vision tasks 刻意造涌现。
- Zhao / Qin / Alvarez-Melis / Kakade / Saphra《Random Scaling of Emergent Capabilities》arXiv:2502.17356 v5（2026-02-18，ICML）：「different random seeds can produce either smooth or emergent scaling trends」；「sharp breakthroughs...produced by underlying continuous changes in their distribution across seeds」；最关键「Our observations hold true even under continuous loss metrics」——换连续度量也不能一键消解，须看生成分布。

**认知增量**：单一 verdict = 一条度量路径的产物；换字段名/换措辞翻转（§104）、单判据 6/6 不能排除量身定做（§102）的宇宙级同构。本仓 flag 分层 + 独立确认集 + 多判据透明化即对「度量依赖」的诚实回应，裁定权归用户。

## §4bw · 单路径≠稳健——同一数据 34% 同结果、2% 相反

**一手摄食**
- Aczel / Szaszi 等《Investigating the analytical robustness of the social and behavioural sciences》Nature（2026），doi:10.1038/s41586-025-09844-9：100 研究、每项≥5 独立重分析；「34%...yielded the same result (within ±0.05 Cohen's d)...four times broader tolerance...57%」；「74% reached the same conclusion...24% yielded no effects or inconclusive results and 2% reported the opposite effect」；「single-path analyses...should not be simply assumed to be robust」。
- Miske 等 reproducibility 论文 Nature vol652 pp126-134（2026-04-01）：600 论文/62 期刊，24% 供数据，53.6% 精确可复现、73.5% 至少近似可复现。三维度互不还原：可复现≠稳健≠可复制。

**诚信现场复现**：机构新闻稿「457 分析师/504 重分析」与论文摘要「at least five reanalysts per study」不符；我先把同项目 reproducibility 论文误认作 robustness，经 DOI 纠正。两处均降权、以论文一手摘要为准，不硬凑数字——KB-META48 纪律实盘。

**认知增量**：34% 同结果/2% 相反 → 单一 verdict 不可默认稳健；24% 不确定 → flag 非 ok 的正当性；三维不互还原 → canary 重跑 / 独立确认集 / 外部一手验证各管一维。

## 内化与验证
- KB **257→259**（KB-AUDIT101 度量即结论 + KB-META66 四论文一手&纪律现场）；Safari 台账累计 **21 轮**；LIFE_KERNEL.md 新增 §4bv/§4bw；handoff 同步 round=§4bw / KB=259。
- 一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**；内核专项 **122 passed**。
- 内核 7.5.0、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全部零漂移**。

## 红线
判定权归用户；内核 L0 不联网不 spawn；只读内化、未编译新门禁、未动十案/§100。外部 LLM scaling 与社科稳健性仅为 B 级哲学镜像，只内化思维器官。
