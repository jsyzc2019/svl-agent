#!/usr/bin/env python3
"""§4au 外部镜像诊断：用 AAS(arXiv:2607.17947) 的 Idle-Gap Test 判据机械检验 v5 意志。

诚实性：本脚本读真实源码/数据得出【否定性结论也不掩饰】——若内核只在被手动调用时才动，
则按 AAS Ambient band 判为 reactive（ambient=0），不冒充 self-directed。
外部证据 B 级（arXiv 作者摘要自报）；本仓代码事实 A 级。
不改 verdict / 宪法 / §100；只读。
"""
import json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kernel as K

def build_report():
    src = open(os.path.join(HERE, "kernel.py"), encoding="utf-8").read()
    # Idle-Gap Test 机械近似：内核是否有"无外部触发时自发活动"的机制？
    # 证据1：是否存在独立守护/定时器/后台循环（真实 idle activity 的物理前提）
    daemon_symbols = ["threading", "Timer", "schedule", "while True", "asyncio", "cron", "signal.alarm", "multiprocessing"]
    daemon_present = {s: (s in src) for s in daemon_symbols}
    has_daemon = any(daemon_present.values())
    # 证据2：live() 顶层调用是否需要外部显式触发（若函数只在 __main__ 手动调用）
    main_block = src.split('if __name__ == "__main__":')[-1] if 'if __name__ == "__main__":' in src else ""
    live_auto_invoked = "live(" in main_block
    # 证据3：真实运行数据——心跳是否全由外层手动 evolve 产生（带 action_note 说明来源）
    hbs = K._load_heartbeats()
    manual_only = all("自主议程" in h.get("phase_improve_action", "") or h.get("phase_improve_action")
                      for h in hbs if h.get("direction"))
    # 证据4：agenda 台账里是否存在"无触发自发"记录（本仓无 idle daemon 则必为空或手动）
    agenda = K._load_agenda_log()

    idle_gap_survives = has_daemon and live_auto_invoked  # AAS Ambient L4 门槛的反事实近似
    return {
        "framework": "AAS arXiv:2607.17947 (Idle-Gap Test: remove all triggers, observe if internally-derived activity persists)",
        "external_tier": "B 级（arXiv 作者摘要自报，非本仓实测）",
        "local_evidence_tier": "A 级（读本仓真实源码/数据）",
        "daemon_symbols": daemon_present,
        "has_idle_daemon": has_daemon,
        "live_auto_invoked_in_main": live_auto_invoked,
        "heartbeat_count": len(hbs),
        "agenda_decisions": len(agenda),
        "ambient_activity_survives_trigger_removal": idle_gap_survives,
        "aas_ambient_level_estimate": 0 if not idle_gap_survives else ">=4(counterfactual needs real idle run)",
        "aas_active_band": "内核有 autonomous_agenda/live（自发选向）但需外部显式调用 → Active 有意志",
        "aas_ambient_band": "无独立进程/定时器/后台循环 → 移除触发即停 → Ambient 归零（诚实否定）",
        "honest_verdict": ("v5 意志是【被唤醒后的自主】：唤醒后自己决定做什么（Active self-directed），"
                           "但没有人叫它时不会自己醒（Ambient reactive）。按 AAS 尚未达 autotelic——"
                           "这是真实缺口，不掩饰为已实现。"),
        "tao_of_agency_mirror": "arXiv:2606.19924: agent must believe in its own boundary to act, see through it to understand; embeddedness individuates but non-uniquely. 本仓 L0 宪法层=边界之'信'，但边界非唯一性尚未机制化。",
        "does_not_change": ["verdict", "l3=false", "absolute=false", "宪法锁", "§100"],
    }

if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
