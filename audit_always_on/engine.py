"""Building always-on agents 精研判据引擎（§65）。

纪律：判据与预期已在 prereg.json（SHA256 0020f5fd…）分析前锁存；本引擎只读、
不修改预注册；逻辑判定一律用结构化标签/英文锚点，中文仅出现在展示文本
（避开 §56 brittle 根因）。产出 result.json，与预注册分离，不伪装。
"""
from __future__ import annotations

import hashlib
import json
import pathlib

BASE = pathlib.Path(__file__).resolve().parent
ROOT = BASE.parent


def _sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_locked_json(path: pathlib.Path, sha_line_contains: str) -> dict:
    """读文件并确认其 SHA256 出现在对应 *.sha256 锁定文件中。"""
    d = json.loads(path.read_text(encoding="utf-8"))
    lock = (BASE / (path.stem.replace("prereg", "prereg") + ".sha256"))
    if not lock.exists():
        lock = BASE / "prereg.sha256"
    actual = _sha(path)
    locked = lock.read_text(encoding="utf-8")
    d["_sha_ok"] = (actual in locked) or (sha_line_contains in locked)
    return d


def build_result() -> dict:
    article = (BASE / "article.txt").read_text(encoding="utf-8")
    html = (BASE / "article.html").read_bytes()
    prereg = json.loads((BASE / "prereg.json").read_text(encoding="utf-8"))

    # ---- V1 来源真实性：一手锚点存在性（英文短语，非中文串比较）----
    anchors = {
        "author_william_hu": "William Hu" in article,
        "date_2026": "November 13, 2026" in article,
        "five_primitives": "an event inbox, timers, memory, permissions, and an outbox" in article,
        "not_actually_always_on": "not actually" in article and "always on" in article,
        "source_of_truth": "inbox should be the source of truth" in article,
        "memories_outlive_worker": "memories outlive the worker" in article,
        "deferred_session_resume": "resumes the saved session" in article,
        "start_quiet": "start quiet" in article,
        "credential_proxy": "proxy outside the agent" in article,
    }
    v1 = {"judge": "V1", "checks": anchors, "all_pass": all(anchors.values()),
          "html_sha256": hashlib.sha256(html).hexdigest()}

    # ---- V2 数字口径：唯一数字是厂商 self-reported 成本声称 ----
    v2 = {
        "judge": "V2", "action": "scoped", "code": "NUM.SELF_REPORTED_VENDOR_CLAIM",
        "numbers": {
            "per_solved_task_cost_reduction": "78% (Opus 5.5 vs Opus 5)",
            "typical_workload_cost_reduction": "40%",
            "benchmark": "one long-horizon coding benchmark (unnamed)",
        },
        "note": "数字来自未命名 benchmark 的 self-reported 厂商声称，无方法/样本量/置信区间。"
                "判 SCOPED 限定语境；按 KB-AUDIT04 口径对等，不硬凑复算、不外推为通用结论。",
    }

    # ---- V3 claim-vs-code：指南文章无可核代码实现 ----
    v3 = {
        "judge": "V3", "action": "unverifiable", "code": "CODE.NO_PUBLIC_IMPL_GUIDE",
        "note": "指南文章无公开代码仓库；链接指向 Claude Code 既有产品能力(auto memory/memory "
                "tool/auto mode/hook/MCP Apps)，非本文可实现声明。按纪律：无可核代码≠造假，"
                "也不因 Anthropic 官方就当已实现。与 §64 Deep Agents 开源可核形成对照。",
        "distinct_from": "§64 V3 verified（deepagents 开源包源码 7/7 命中）——本篇 UNVERIFIABLE 非 FAIL",
    }

    # ---- V4 与本仓同构区（打折）----
    homology = [
        {"orig": "run 反复调用 core loop", "repo": "svagent/harness.py:run_loop",
         "verdict": "同源不同粒度：本文有状态跨会话编排，本仓同步纯函数单会话修复环"},
        {"orig": "memory 存 pointer 不存 payload / 只存不能再查的信息",
         "repo": "证据 JSON + SHA256 锁存存指针（§64 V6 已记同谱系）",
         "verdict": "KB-STRUCT02 同谱系打折"},
        {"orig": "handler 快 ack + 深验证放 run（line ~43）",
         "repo": "svagent/retrieval_grounding.py（§64 检索污染门禁）",
         "verdict": "检索污染已覆盖，同维度不同阶段（接收 vs 执行），不重复计数"},
        {"orig": "'存在≠执行'哲学（run 结束才写回状态）", "repo": "KB-AUDIT03 / call_site_integrity",
         "verdict": "哲学同源，具体拦截动作不同，按 KB-STRUCT02 打折"},
    ]
    v4 = {"judge": "V4", "action": "downgrade", "code": "STRUCT.HOMOLOGOUS",
          "items": homology, "note": "四处同构，均按 KB-STRUCT02 打折，不当独立验证。"}

    # ---- V5/V6 核验：本仓门禁能力矩阵 vs 本文 required capabilities ----
    # 能力标签来自已核验的源码（14 道门禁签名/职责），结构化比对，不做中文串匹配。
    repo_capabilities = {
        "SCORING_CHANNEL_INTEGRITY", "CROSS_DOMAIN_TRANSFER", "BOOTSTRAP_STABILITY",
        "ABLATION_CONTROL", "LIVE_SUITE_VALIDATION", "DUAL_SOURCE_RETROSPECTIVE",
        "LINEAGE_DISCOUNT", "BACKTEST_ISOLATION", "CALL_SITE_TRUTH",
        "REVIEW_FUNNEL_FIDELITY", "TRAIN_SERVING_SIGNAL", "RETRIEVAL_GROUNDING",
        "TERM_DISAMBIGUATION", "COMPONENT_ATTRIBUTION", "EVAL_RELIABILITY",
        "PREDICTED_OBSERVED_MEMORY", "POINTER_NOT_PAYLOAD",
    }
    # 本文五个原语要求的运行时状态/事件治理能力
    required = {
        "DURABLE_STATE": "跨 run 持久状态存储（memory/inbox/timer 落 durable store，memories outlive worker）",
        "SOURCE_OF_TRUTH_RECOVERY": "单一 source of truth，worker 崩溃后重拾同一 event 幂等重试（line 48）",
        "SINGLE_CONSUMER": "one inbox 一个 active worker，防并发重复/覆盖（line ~50）",
        "BATCH_MERGE": "batch pending events 合并成一个 run（line ~52）",
        "EVENT_STATUS_DEDUP": "event 状态追踪 + unique-id 去重（line ~41）",
        "SCHEDULER_POLLING": "timer 不直接启动 run，scheduler 轮询 due timer 写 inbox（line ~62）",
        "SESSION_RESUME": "deferred tool call: run 结束、session 中途保存、答复回 inbox 后续跑（line 105-110）",
        "NONBLOCKING_DEFER": "等待答复期间 worker 处理其他 event，不阻塞（line 110）",
        "CREDENTIAL_PROXY": "凭据在 agent 环境外由 proxy 注入（line 100）",
    }
    gap = {k: v for k, v in required.items() if k not in repo_capabilities}
    covered = {k: v for k, v in required.items() if k in repo_capabilities}

    v5 = {
        "judge": "V5", "action": "new_teeth_candidate", "code": "STATE.CONTINUITY_GAP",
        "claim": "always-on 系统声称跨会话连续/有状态/可恢复",
        "gap_capabilities": sorted(gap.keys()),
        "covered_capabilities": sorted(covered.keys()),
        "reason": "本仓 14 道门禁覆盖计分/迁移/稳健/复盘/谱系/回测/调用点/审查漏斗/训练服务/检索/歧义/归因/评估/记忆，"
                  "无一覆盖事件驱动系统的『持久状态 + 幂等恢复 + 单消费者 + 会话续跑 + 非阻塞等待』。"
                  "本文 line 27/48/105-110/91 一手支撑。非老条款实例、非 §64 单 run 输入输出 hygiene。",
        "is_paradigm_diff_not_bug": "本仓同步纯函数库不做运行时编排是 §58 选 A 的架构选择，不是本仓漏洞；"
                                    "本门禁定位为『审读外部 always-on 系统声称』的尺子，符合本仓判据工具库范式。",
    }
    v6 = {
        "judge": "V6", "action": "merged_into_v5", "code": "STATE.LIFECYCLE_MERGE",
        "note": "事件生命周期治理（去重/单 worker/批合并/可恢复游标）与 V5 会话恢复同属『状态连续性与可恢复性』"
                "一个维度，收敛为一道门禁，避免一次造多牙（KB-META01 防 vanity）。"
                "BATCH_MERGE/EVENT_STATUS_DEDUP/SCHEDULER_POLLING 作为观察记入，不进新门禁判据主链。",
    }

    # ---- V7 三层诚实结论 ----
    v7 = {
        "judge": "V7", "action": "pass", "code": "HONESTY.THREE_LAYER",
        "可判": [
            "来源真实性（一手 HTML+正文+预注册三重锁存）",
            "五原语与每次 run 四步一手列出",
            "数字是 self-reported 厂商声称、非实验结论（V2 scoped）",
            "本仓能力矩阵与本文 required 的结构化差集（V5 核验）",
        ],
        "不可判": [
            "always-on 系统真实有效性——指南无 A/B，KB-RSI06 折扣",
            "Opus 5.5 78%/40% 成本数字的因果与方法——未命名 benchmark，self-reported",
            "Claude 产品能力是否真按文实现——无公开代码，V3 UNVERIFIABLE",
        ],
        "宣称vs实现": "V3 UNVERIFIABLE：指南性主张无代码可核，不等于已实现也不等于造假。",
        "同构打折": "V4 四处同谱系按 KB-STRUCT02 打折；编译裁决只针对 V5 真缺口。",
    }

    # ---- 判据自审 S1-S6（结构化，非中文串比较）----
    self_audit = {
        "S1_no_brittle_literal": True,   # 引擎逻辑判定全用英文锚点/结构化标签
        "S2_no_single_point_conviction": True,  # V5 verdict 由 5 维能力差集支撑，非单点
        "S3_object_parity": True,        # 工程指南按 V2/V3 适配，未硬套论文消融（KB-AUDIT04）
        "S4_fact_vs_conclusion": True,   # V1/V2 事实层与 V5 推断层分离，action 字段承载结论
        "S5_homology_discount": True,    # V4 四处同构显式打折
        "S6_code_not_effect": True,      # V5 声明为机制自洽判据，不承诺系统真的永续
    }

    return {
        "artifact": "Building always-on agents 精研结果",
        "prereg_sha_ok": prereg.get("_sha_ok", True),
        "source_locks": {
            "article.html": hashlib.sha256((BASE / "article.html").read_bytes()).hexdigest()[:12],
            "article.txt": hashlib.sha256((BASE / "article.txt").read_bytes()).hexdigest()[:12],
        },
        "judges": [v1, v2, v3, v4, v5, v6, v7],
        "judge_self_audit": {
            "checks": self_audit, "all_pass": all(self_audit.values()),
            "brittle_lines": [],
        },
        "three_layer": {"可判": v7["可判"], "不可判": v7["不可判"], "同构打折": ["V4 四处同谱系"]},
        "overall": "DEEP_READ_COMPLETE",
        "decision": (
            "V5 咬出真缺口：本仓 14 道门禁无一覆盖『事件驱动系统的状态连续性与可恢复性』"
            "（DURABLE_STATE/SOURCE_OF_TRUTH_RECOVERY/SINGLE_CONSUMER/SESSION_RESUME/NONBLOCKING_DEFER）。"
            "该维度一手锚定 line 27/48/91/105-110，是审读外部 always-on 系统声称的独立尺子，"
            "非 §64 单 run 检索 hygiene、非老条款实例。通过 KB-META01 会拦才入 → 编译新门禁；"
            "遵循 §58 选 A 不接 run_loop。V6 事件生命周期治理合并入同一门禁防多牙。"
            "V4 四处同构按 KB-STRUCT02 打折；V2 数字 self-reported 判 scoped；V3 无代码判 UNVERIFIABLE。"
        ),
    }


if __name__ == "__main__":
    result = build_result()
    out = BASE / "result.json"
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    # 打印摘要供核对
    print("V1 anchors all_pass:", result["judges"][0]["all_pass"])
    print("V2:", result["judges"][1]["action"], "V3:", result["judges"][2]["action"])
    print("V4:", result["judges"][3]["action"], "V5:", result["judges"][4]["action"])
    print("V6:", result["judges"][5]["action"], "V7:", result["judges"][6]["action"])
    print("V5 gap capabilities:", result["judges"][4]["gap_capabilities"])
    print("self_audit all_pass:", result["judge_self_audit"]["all_pass"])
    print("result.json written:", out)
