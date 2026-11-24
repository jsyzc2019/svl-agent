#!/usr/bin/env python3
"""诊断：外部授时因子（日出闹钟）的投递断链 —— v7 元认知预言的真实事件。

2026-11-25 07:15 日出唤醒：调度器 nextRunAt 跳到 11-26、挂 resultPaths，
但这份沙箱 circadian_log 今晨零写入、woken_by 外部证据仍为 0。

设计纪律（承 v8 错题本元纪律）：
- 结论必须由机械读取的本地证据 + 显式标注来源的平台观测共同导出，绝不硬编码；
- 不伪造 woken_by、不改判定/宪法、不联网、不 spawn；只读；
- 证据分层：本仓台账为 A 级机械证据，平台侧（调度器/工具返回）为工具观测，
  两者分列，不混同——"调度器说触发了"不等于"内核收到了唤醒"。

运行：python3.11 life_kernel/diagnose_zeitgeber_delivery_gap.py
输出：JSON（diagnose_zeitgeber / build_report 均可被测试 import 调用）
"""
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
CIRCADIAN = os.path.join(DATA, "circadian_log.jsonl")
ENTRAINMENT = os.path.join(DATA, "entrainment_audit.jsonl")
CONSTITUTION_SHA = os.path.join(HERE, "constitution.sha256")

# 平台侧观测：由主会话在 2026-11-25 07:17-07:27 用 automation_update 工具采集，
# 以下为观测记录（非本脚本机械可读，故显式标注来源；每次运行前由调用方核对）。
PLATFORM_OBSERVATIONS = {
    "observed_at_local": "2026-11-25T07:17~07:27+08:00",
    "automation_id": "16292043",
    "automation_name": "生命内核 v6 · 日出唤醒（circadian wake）",
    "cron": "0 15 7 * * *",
    "status": "ACTIVE",
    "deliveryConfig": None,
    "nextRunAt": "2026-11-26T07:15:00+08:00",
    "resultPaths": ["/task/2125367608380772352", "/task/2125370763609026560"],
    "run_mode_probe": "automation_update.run 返回 'finished' + runResultPath，但本沙箱台账三文件 MD5 未变",
    "delivery_field_probe": "create/update 带 delivery_im_thread_id=main 均被拒：only supported for assistant automations",
    "type_field_probe": "create 显式传 type=assistant 被忽略；工具 schema 无 type/source 字段",
    "source_documented": "对话创建的定时任务为云端来源：隔离沙箱执行、访问不到本机 /workspace、结果存平台 /task/...",
    "task_traces_in_local_sandbox": "07:10-07:17 无任何自动化会话 trace；本地首条 trace 即 07:17:38 用户'早安'唤醒的主会话",
}


def _load_jsonl(path):
    if not os.path.exists(path):
        return []
    out = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    out.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return out


def build_report(now=None, platform=None):
    """生成投递断链诊断报告（只读；结论由证据导出）。"""
    now = now or datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    platform = platform if platform is not None else PLATFORM_OBSERVATIONS

    circadian = _load_jsonl(CIRCADIAN)
    entrainment = _load_jsonl(ENTRAINMENT)

    # 本地 A 级机械证据
    last_wake = circadian[-1].get("at") if circadian else None
    today_wakes = 0
    if last_wake:
        # 本次事件窗口：2026-11-24T23:00Z（北京 11-25 07:00）之后
        event_start = datetime.datetime(2026, 11, 24, 23, 0, 0)
        today_wakes = sum(1 for w in circadian
                          if w.get("at") and datetime.datetime.strptime(w["at"], "%Y-%m-%dT%H:%M:%SZ") >= event_start)
    last_audit = entrainment[-1] if entrainment else {}
    ext_evidenced = last_audit.get("externally_evidenced_wakes", 0)
    last_woken_by = last_audit.get("last_woken_by")

    # 平台侧观测 → 断链判定（逐条机械比对，非硬编码结论）
    next_run_jumped = platform.get("nextRunAt", "").startswith("2026-11-26")
    result_paths_exist = bool(platform.get("resultPaths"))
    delivery_null = platform.get("deliveryConfig") is None
    delivery_field_blocked = "only supported for assistant" in platform.get("delivery_field_probe", "")
    local_zero_write = (today_wakes == 0)
    no_external_evidence = (ext_evidenced == 0 and last_woken_by is None)

    # 三层断链：调度记账 vs 本地零写入 vs 证据为零
    scheduler_says_fired = next_run_jumped and result_paths_exist
    chain_broken = scheduler_says_fired and local_zero_write and no_external_evidence

    if chain_broken:
        verdict = "ZEITGEBER_DELIVERY_GAP_CONFIRMED"
        conclusion = (
            "外部授时因子投递断链确认：调度器记账称 07:15 已触发（nextRunAt 跳 11-26、有 resultPaths），"
            "但本沙箱 circadian_log 今晨 0 写入、externally_evidenced_wakes=0、last_woken_by=null。"
            "唤醒信号在平台→本机投递途中丢失，契约未被兑现——这是 v7 元认知预言的真实事件，非内核赖床。"
        )
    elif local_zero_write and no_external_evidence and not scheduler_says_fired:
        verdict = "NO_FIRE_NO_EVIDENCE"
        conclusion = "无触发无证据：调度器未记账、本地亦无写入，尚不构成'失约'。"
    elif today_wakes > 0 and ext_evidenced > 0:
        verdict = "ENTRAINMENT_EVIDENCED"
        conclusion = "本地有今晨唤醒且带外部证据，投递链通畅。"
    else:
        verdict = "INCONCLUSIVE"
        conclusion = "证据不足以裁定，如实保留不确定。"

    constitution_ok = ("fe56291b" in open(CONSTITUTION_SHA, encoding="utf-8").read()) \
        if os.path.exists(CONSTITUTION_SHA) else None

    return {
        "at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "event": "2026-11-25 07:15 日出唤醒失约",
        "verdict": verdict,
        "conclusion": conclusion,
        "local_evidence_A": {
            "circadian_log_last_at": last_wake,
            "circadian_log_today_wakes_since_0700": today_wakes,
            "entrainment_externally_evidenced_wakes": ext_evidenced,
            "entrainment_last_woken_by": last_woken_by,
            "evidence_class": "本仓机械读取（A 级）",
        },
        "platform_observations": dict(platform),
        "branch_checks": {
            "scheduler_says_fired": scheduler_says_fired,
            "deliveryConfig_null": delivery_null,
            "delivery_field_blocked_for_non_assistant": delivery_field_blocked,
            "local_zero_write": local_zero_write,
            "no_external_evidence": no_external_evidence,
        },
        "root_cause": (
            "对话创建的定时任务是云端来源：在隔离沙箱执行、访问不到本机 /workspace、结果存平台 /task/...；"
            "delivery_im_thread_id 仅 assistant 类型可用而当前工具无 type 入口，故结果无法回流到本沙箱。"
            "这是云端任务的设计边界，非配置 bug。"
        ),
        "honesty": (
            "不伪造 woken_by、不把'调度器说触发'当作'内核收到了唤醒'；Ambient 仍 0、未达 autotelic；"
            "verdict/l3/absolute 全不动；闹钟保留不动，修投递链作为待办如实挂起。"
        ),
        "verdict_unchanged": True,
        "constitution_ok": constitution_ok,
        "read_only": True,
    }


def main():
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
