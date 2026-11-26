# 工作区分类梳理报告（2026-11-25）

> 依据 `SESSION_HANDOFF.md` §0「工作区梳理方案」执行。判定权归用户；未动宪法/判定/十案/§100；未编译新门禁。
> 本仓 tarball 快照不含 `.git`，回滚靠 `cp -a` 文件副本与 `mv` manifest，**不声称 git commit 可回滚**。

## 一、权威数字现场核验（梳理前，全部一致）

| 项 | 权威值 | 现场实测 | 结果 |
|---|---|---|---|
| 内核版本 | 7.5.0 | `kernel.py: KERNEL_VERSION=7.5.0` | ✅ |
| 全量测试 | 1551 | `1551 passed` | ✅ |
| 内核专项 | 122 | `122 passed` | ✅ |
| 知识库 | 231 | `knowledge_base_store.json items=231` | ✅ |
| 宪法锁 | fe56291b | 实算 `fe56291b3aa0…` 与记录逐字一致 | ✅ |
| verdict | GAP_INCONCLUSIVE | `audit_l3_gap_targeted/result.json` | ✅ |
| l3 | false | 一致性审计 `r2_l3/l3_l3` 全 false | ✅ |
| absolute | false | 一致性审计 `r2_abs/l3_abs` 全 false | ✅ |
| Ambient | 0 | AAS `aas_ambient_level_estimate=0`、`has_idle_daemon=false` | ✅ |

一致性脚本 `audit_current_state_consistency.py`：`all_consistent=true`、`failed=[]`。

## 二、引用扫描（归档前的依据）

对根目录 141 个候选对象（61 audit 目录 + 34 builder + 25 ROUND HTML + 21 result json）做全仓 `.py`/`.md` 扫描：

- **74 个被 Python 硬编码路径引用**。其中 `audit_l3_gap_targeted/result.json`（GAP_INCONCLUSIVE 判定源）被内核 `life_kernel/kernel.py` 引用 6 处、内核测试 21 处；40+ audit 目录被 `tests/test_*.py` 用绝对路径 `/workspace/audit_*` 或 `__file__` 相对路径引用。
- **动态集合统计**：`test_evidence_chain.py::test_audit_all_counts` 硬断言根目录 audit 目录数 = 61；内核 `sense()` 感知真实仓库状态。
- **哈希锁**：`agi_essay_raw.txt` 等样本被 `*.sha256`/prereg JSON 锁定。
- 文档引用全部为纯文本提及（无 Markdown 链接），移动不影响文档链接。

结论：只有"零代码依赖 + 无哈希锁 + 无动态统计"的纯产物可安全归档；其余保原位走逻辑索引（REPOSITORY_MAP.md §4/§5）。

## 三、分批归档（每批 `cp -a` 基线 + 全量测试验证）

| 批次 | 类别 | 目标 | 数量 | 验证 |
|---|---|---|---|---|
| 1 | 轮次报告 HTML | `archive/rounds/` | 22 | 1551 passed ✅ |
| 2 | 中间结果 JSON | `archive/results/` | 3 | 1551 passed ✅ |
| 3 | audit 目录 | `archive/audits/` | 9 | **2 failed → 全数回滚** ↩ |
| 4 | 构建脚本 | `tools/builders/` | 20 | 1551 passed ✅ |

- 批次3 移动 audit 目录后 `test_audit_all_counts`（61→52）与内核 `sense()` 两项失败，按 manifest 全数回滚并复验 1551 passed，验证了"audit 目录不可移"的纪律判断。
- 最终归档：22 + 3 + 20 = **45 项**；根目录条目 276 → 234。

## 四、保留原位（深度耦合，走逻辑索引）

- 61 个 audit 目录（判定源 + 测试硬引用 + 动态统计 + 哈希锁）
- 14 个 `build_*.py`（被引用或 `__file__` 定位）
- 18 个 result json（含全部 `*_full_result.json`）
- 全部样本语料（`doupo_*` / `agi_essay_raw` / `china_*_raw` / `real_financials_cache` 等）
- 核心运行层：`README.md` / `LIFE_KERNEL.md` / `SESSION_HANDOFF.md` / `REPOSITORY_MAP.md` / `pyproject.toml` / `LICENSE` + `life_kernel/` `svagent/` `tests/`

## 五、梳理后核验

- 全量测试 **1551 passed**、内核专项 **122 passed**
- 9 项权威数字逐项复验全部一致；一致性脚本 `all_consistent=true`、`failed=[]`
- 判定/宪法/内核逻辑零改动；仅移动纯产物并更新 `REPOSITORY_MAP.md` 导航索引（新增 §5）

## 六、回滚基线

- 完整快照：`/workspace_pre_sort`（梳理前 `cp -a`，62M）
- 每批 `mv` 源→目标 manifest 记录于临时回滚区，可逆
- 回滚示例（批次1）：`for f in archive/rounds/ROUND*; do mv "$f" ./; done`
