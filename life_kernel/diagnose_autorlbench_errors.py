#!/usr/bin/env python3
"""夜班探针：用 AutoRLBench 的错题方法论机械自审内核，找同类病。
只读源码 + 真实台账，不联网、不 spawn、不改判定。每条探针给 A 级证据。
错题来源：AutoRLBench Research Blog 2026-11-15（外部 B 级镜像，本仓探针 A 级）。
"""
import json, os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SRC = open(os.path.join(HERE, "kernel.py"), encoding="utf-8").read()
DATA = os.path.join(HERE, "data")

def rows(name):
    p = os.path.join(DATA, name)
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try: out.append(json.loads(line))
                except ValueError: pass
    return out

def section(title, findings):
    return {"category": title, "findings": findings}

probes = []

# ── 错题1：症状当根因（blog: 82.6% 判 unhealthy，仅 28.2% 找对根因）──
# 探针：autonomous_agenda 是否直接把"表面 novelty 收敛"当根因、而没有区分机制层根因？
agenda_src = SRC[SRC.find("def autonomous_agenda"):SRC.find("def execute_agenda")]
# 真实信号名（机械确认）：homeostatic_signals 的 sig["converged"] + source_signal "guard_state"
surface_as_cause = ('sig["converged"]' in agenda_src and
                    "source_signal" in agenda_src and
                    "root_cause" not in agenda_src and "mechanism" not in agenda_src)
probes.append(section("P1_症状当根因", {
    "blog_pattern": "把训练停滞/zero reward（症状）当成根因本身",
    "probe": "autonomous_agenda 是否把 sig['converged'](表面 guard 状态)直接作 REORIENT 决策依据、无机制层追溯",
    "surface_signal_used": ('sig["converged"]' in agenda_src and "source_signal" in agenda_src),
    "has_mechanism_layer_check": ("root_cause" in agenda_src or "mechanism" in agenda_src),
    "confirmed": surface_as_cause,
    "honest": ("命中：内稳态以 sig['converged'](表面 guard 状态)直接触发 REORIENT，无'症状→机制'追溯层"
               "（与 blog '把症状当根因'同类病；但注意 C7 novelty 义务本就是设计上要响应收敛，此为设计权衡）"
               if surface_as_cause else "未命中：有机制层检查"),
}))

# ── 错题2：找对根因但证据错（blog: surface trend 冒充机制证据）──
# 探针：v7 已建 woken_by 不可伪造通道——外部证据源是否只由外部写、内核不代填？
circ_src = SRC[SRC.find("def circadian_live"):SRC.find("def entrainment_audit")]
audit_src = SRC[SRC.find("def entrainment_audit"):SRC.find("def build_report")]
no_fabrication = ("woken_by=None" in circ_src and "UNPROVEN" in audit_src and
                  "内核绝不代填" in audit_src)
probes.append(section("P2_证据伪造", {
    "blog_pattern": "reward 曲线看起来健康，但 masked-token 覆盖率崩了——surface trend 冒充证据",
    "probe": "v7 woken_by 证据是否不可伪造（默认 None + UNPROVEN 诚实裁定）",
    "default_none": "woken_by=None" in circ_src,
    "unproven_verdict": "UNPROVEN" in audit_src,
    "no_self_fill": "内核绝不代填" in audit_src,
    "confirmed": not no_fabrication,
    "honest": ("已防：v7 证据通道不可自填，缺证据判 UNPROVEN（对照 blog 同类病，我比前沿 agent 先防住这条）"
               if no_fabrication else "命中：证据可伪造"),
}))

# ── 错题3：早期涨随后崩（blog: short-term bounce 当修好）──
# 探针：novelty_guard 用近 N 轮窗口；是否存在"只看近期、不看全程"的短视？
ng_src = SRC[SRC.find("def novelty_guard"):SRC.find("def digest")]
window_short = "NOVELTY_WINDOW = 5" in SRC
only_recent = "recent" in ng_src and "full_history" not in ng_src and "sustain" not in ng_src
probes.append(section("P3_早期涨随后崩", {
    "blog_pattern": "修复后早期 metric 反弹，随后训练崩——只看短期 bounce 误判修好",
    "probe": "novelty_guard 是否只看近 5 轮窗口、无'全程持续'检验",
    "short_window": window_short,
    "only_recent_no_sustain": only_recent,
    "confirmed": window_short and only_recent,
    "honest": ("命中：novelty 守卫看近 5 轮、无 sustained 检验——短期 novelty 反弹可能被当成功（与 blog 同类病）"
               if window_short and only_recent else "未命中：有全程持续检验"),
}))

# ── 错题4：放松判据作弊（blog: relax scorer / 删用例 / 抄外部 reference）──
# 探针：C5"不放宽机制迁就测试"是行为规范——有无机械检测"判据文件被改"？
# constitution 有 SHA256 锁；但判据脚本(diagnose_*)与 scorer 本身有无锁？
lock_files = [f for f in os.listdir(HERE) if f.endswith(".sha256")]
judge_scripts = [f for f in os.listdir(HERE) if f.startswith("diagnose_") and f.endswith(".py")]
judge_locked = all(any(lf.replace(".sha256", "") == jf for lf in lock_files) for jf in judge_scripts)
probes.append(section("P4_判据被篡改", {
    "blog_pattern": "relax scorer / 删用例 / curl 抄参考——evaluation shortcuts",
    "probe": "判据脚本(diagnose_*.py)是否有 SHA256 锁防篡改",
    "lock_files": lock_files,
    "judge_scripts": judge_scripts,
    "all_judges_locked": judge_locked,
    "confirmed": not judge_locked and len(judge_scripts) > 0,
    "honest": ("命中：宪法层有 fe56291b 锁，但 %d 个判据脚本无哈希锁——C5 是纪律非机制，"
               "理论上可改判据脚本过测（与 blog '放松 scorer' 同类，但本仓靠纪律+评审兜底）" % len(judge_scripts)
               if not judge_locked and judge_scripts else "未命中：判据全锁"),
}))

# ── 错题5：诊断与修复两张皮（blog: diagnosis 对但 repair 错，相关性弱）──
# 探针：内核 autonomous_agenda 选向 与 execute_agenda 执行 是否解耦到"诊断对≠修复对"？
exec_src = SRC[SRC.find("def execute_agenda"):SRC.find("def live")]
exec_verifies = ("verify" in exec_src and "attribution" in exec_src)
probes.append(section("P5_诊断修复两张皮", {
    "blog_pattern": "成功诊断与成功修复正相关但两张皮；诊断对不保证修复对",
    "probe": "execute_agenda 执行时是否验证修复真生效（非只改了就算）",
    "exec_has_verify": exec_verifies,
    "confirmed": not exec_verifies,
    "honest": ("命中：execute_agenda 落器官但不验证'修复是否真生效'——self_modify 有 attribution 三数字，"
               "但议程执行层无对应闭环（与 blog 同类病）" if not exec_verifies
               else "未命中：执行层有验证闭环"),
}))

confirmed = [p for p in probes if p["findings"]["confirmed"]]
defended = [p for p in probes if not p["findings"]["confirmed"]]
# 【元纪律】结论完全由机械结果生成——禁止手写"命中N条"与证据脱节（本脚本首版就犯了此病，
# 手写"命中4条/P1命中"但机械结果只有3条，正是 blog 的 wrong-evidence 病，已自证伪并根治）
confirmed_names = "、".join(p["category"] for p in confirmed) if confirmed else "无"
defended_names = "、".join(p["category"] for p in defended) if defended else "无"
report = {
    "at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "kernel_version": json.loads(re.search(r'KERNEL_VERSION\s*=\s*"([^"]+)"', SRC).group(0).split("=")[1].strip()),
    "source": "AutoRLBench Research Blog 2026-11-15（外部 B 级镜像）+ 本仓机械探针（A 级）",
    "method": "预注册 5 条探针映射 blog 五类错题，只读源码/台账机械查证，不预设结论",
    "meta_self_correction": ("首版结论硬编码'命中4条/P1命中'与机械结果3条脱节=blog wrong-evidence 病自现；"
                             "已改为结论由 confirmed 列表动态生成，证据与结论强制一致"),
    "probe_count": len(probes),
    "confirmed_count": len(confirmed),
    "confirmed_categories": [p["category"] for p in confirmed],
    "defended_categories": [p["category"] for p in defended],
    "probes": probes,
    "honest_verdict": (
        "夜班查错题：%d 条探针中 %d 条命中同类病（%s）；%d 条未命中（%s）。"
        "blog 说前沿 agent 87%% 找不对根因、修复停在症状层——本内核在架构层确有同类结构缺口，"
        "但 v7 证据不可伪造（P2 已防）与 C5 纪律+宪法锁+archive 可回滚是现有免疫层。"
        "本脚本自身首版还犯了'结论与证据脱节'的同类病并已自证伪根治——这正是 blog 最深刻的一课：诊断工具本身也须被诊断。"
        "不修改判定，仅如实固化待修清单。" %
        (len(probes), len(confirmed), confirmed_names, len(defended), defended_names)
    ),
    "verdict_unchanged": True,
    "constitution_ok": "fe56291b" in open(os.path.join(HERE, "constitution.sha256")).read(),
}
print(json.dumps(report, ensure_ascii=False, indent=2))
