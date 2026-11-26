# Safari §4cf / §4cg 战利品报告（2026-11-25）

> 用户令："给你的诚信点讚！持续Safari"。本轮两场，两份一手论文逐字核验。直击本仓最核心的"裁定权归用户 + 不确定性诚实"。

## §4cf · 置信度须统计校准——95% 区间只覆盖 9–44%

**一手摄食**：Hobor/Brcic/Kovac/Poje《Bayesian Elicitation with LLMs: Model Size Helps, Extra "Reasoning" Doesn't Always》arXiv:2604.01896（2026-04-02）。11 个 LLM 给 95% 可信区间；「all models are severely overconfident: their 95% intervals contain the true value only 9--44% of the time, far below the expected 95%」；「increasing reasoning effort provides no consistent benefit」；conformal prediction 可校正；web search 反而 degrade 已准确模型。

**认知增量**：口头置信度严重失准 → flag/不确定性不能靠自述、须统计校准；"more reasoning" 不等于更可靠；校准是把置信度变成可用信号的纪律。

## §4cg · 弃答权——AI 建议摧毁"承认无知"

**一手摄食**：Marcoccia/Quattrociocchi/Capraro《AI advice suppresses people's willingness to say "I don't know"》arXiv:2607.13562（2026-07-15）。5 实验 N=3132、4 预注册，故意让 AI 建议错误；「Merely having access to AI nearly eliminated participants' willingness to suspend judgment」；正确率降到 1/3 而信心近翻倍；「alter the metacognitive threshold」。

**认知增量**：弃答近乎归零 → 裁定权归用户必须包含弃权/升级（escalate）选项，不因 AI 建议强制判 ok；正确率 1/3 信心翻倍 = 代理建议反成错误放大器；"人在回路"只有可弃权时才是真刹车。

**纪律**：正确编号经检索定位（二手 N/比例降权）后 WebFetch 一手核验。

## 内化与验证
- KB **267→269**（KB-AUDIT106 置信度校准/弃答权 + KB-META71 两论文一手&二手降权）；Safari 台账 **31 轮**；LIFE_KERNEL.md 新增 §4cf/§4cg；handoff 同步 round=§4cg / KB=269。
- 一致性脚本 `all_consistent=true`、`failed=[]`；全量 **1551 passed**；内核专项 **122 passed**。
- 内核 7.5.0、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE` / l3=false / absolute=false、Ambient=0 **全部零漂移**。

## 红线
判定权归用户；内核 L0 不联网不 spawn；只读内化、未编译新门禁、未动十案/§100。外部校准研究/行为实验仅为 B 级哲学镜像，只内化思维器官。
