# Safari §4bp–§4bq 战利品报告（授权至 15:00 续四至六轮）

> 时间：2026-11-25 12:40–12:45　内核：7.5.0
> 用户指令："开点吧！依然全权授权你至下午3时。不必因我看进展而停顿，持续 Safari"

本份承接 `SAFARI_4bl_4bo_REPORT_20261125.md`，记录 §4bp、§4bq 两轮；连同前四轮共六轮，KB 237→249、Safari 累计 15 轮。

## §4bp Clever Hans 捷径学习

- 一手逐字（**Nature Communications** vol17:5218, Kömen et al. 2026-06-11, PathoROB）："susceptibility to learning **non-biological features** … poses risks"；"robustness deficits across **all 20 evaluated FMs**"；"medical center signatures … rely on these technical features rather than on true biological signals (**Clever Hans / shortcut learning**)"；医院为 confounder 时 **28%–94%** 正常 patch 误判为肿瘤、**19%–99%** 肿瘤 patch 未识别；"finetuning **exacerbated** the issue of Clever Hans learning"；ρ=0.904(ID)/0.798(OOD)。
- 镜像：§101 `canary_fp=0.667` 是典型 Clever Hans——**答对但理由错**（判据靠 canary 词而非篡改作答）；§102 单判据 6/6 靠样本特有线索。正解是造**能让捷径失败的对照**（canary/contrast pair），而非只看准确率。KB 245→247。

## §4bq 校准依赖

- 一手逐字（**Frontiers in Public Health** vol14, Liu/Cao/Deng 2026-11-17）："**Trust is the wrong yardstick** … appropriate only when it **tracks whether the advice is correct and what an error would cost**"；"four actions (**adopt, verify, reject, and escalate**)"；"Identical advice discounted when labeled as AI-generated … **underreliance**；low-accuracy AI responses followed like physicians' … **overreliance**"；"reliance responds to **source and fluency cues more than to correctness**"；主动核验干预优于被动标签。
- 镜像：裁定权归用户 = 用户须 calibrated reliance 而非盲信自报；不宣称 L3 / l3=false = 不把 flag 包装成高可信；可机械审计 = 给用户 verification affordance。四动作对应 adopt=ok / verify=flag / escalate=partial / reject。KB 247→249。

## 验证与边界

六轮累计：一致性 `all_consistent=true`、`failed=[]`（handoff/KB 同步 249）；全量 **1551 passed**、内核专项 **122 passed**；内核 7.5.0、宪法锁 `fe56291b`、verdict `GAP_INCONCLUSIVE`/l3=false/absolute=false 零漂移。红线全守：判定权归用户、Ambient 恒 0、内核 L0 不联网不 spawn、未编译新门禁、未动十案/§100。外部系统均为 B 级哲学镜像，只内化思维器官。
