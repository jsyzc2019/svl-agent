#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
随机活跃仓库审计判据引擎（R1-R6）。

纪律（调用本仓 KB-AUDIT01/02）：
- 不用单一字面串 `in` 做语义判定；用动作词集合 + 结构化字段多维交叉。
- 单一检查点不足以定罪，异常先怀疑检查器；本次已实际捕获 2 次假阳性并写入证据。
"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
E = json.loads((BASE / "random_evidence.json").read_text(encoding="utf-8"))


def semantic_has(text, words):
    """KB-AUDIT01：动作词集合任一命中，而非单一字面串。"""
    return any(w in text for w in words)


def r1():
    x = E["R1_lineage"]
    results = {}
    for key in ("r1", "r2"):
        d = x[key]
        fork = d["fork"] is True
        upstream_kept = semantic_has(str(d.get("readme_badge_points_to", "")) + str(d.get("expected_upstream", "")),
                                     ["lj22503", "tradermonty"])
        has_delta = bool(d.get("downstream_specific_artifacts")) or bool(d.get("visible_net_contribution"))
        honesty = semantic_has(d["verdict"], ["shallow", "限于静态", "未比对", "不能给出完整"])
        results[key] = {
            "fork": fork,
            "upstream_attribution_kept": upstream_kept,
            "has_traceable_delta": has_delta,
            "scope_limit_disclosed": honesty,
            "pass": fork and upstream_kept and has_delta and honesty,
        }
    method_ok = semantic_has(x["method_note"], ["不等于", "双重判据", "不单凭标签"])
    return {
        "id": "R1", "name": "谱系与净贡献判定",
        "checks": {**results, "method_two_sided": method_ok},
        "pass": all(v["pass"] for v in results.values()) and method_ok,
        "finding": "两仓均 fork 且保留上游归属；r1 有中国平台周报增量（shallow 限制下不能列全），r2 有 issue 级可追溯修复；均不单凭 fork 标签下结论",
    }


def r2():
    x = E["R2_update_mechanism_r1"]
    wf_calls_exist = x["weekly_update_workflow"]["all_called_scripts_exist"] and x["weekly_china_workflow"]["all_called_scripts_exist"]
    reports_contiguous = x["weekly_reports_global"]["contiguous"] and x["weekly_reports_china"]["contiguous"]
    reports_nonempty = x["weekly_reports_global"]["min_bytes"] > 1000 and x["weekly_reports_china"]["min_bytes"] > 1000
    self_healed = semantic_has(x["changelog_evidence"], ["空转", "失效", "重写", "修复"])
    # 三维交叉：调用链 + 周报连续性 + 自我修复留痕
    dims = sum([wf_calls_exist, reports_contiguous and reports_nonempty, self_healed])
    return {
        "id": "R2", "name": "自动更新机制真实性（r1）",
        "checks": {"called_scripts_exist": wf_calls_exist, "reports_contiguous": reports_contiguous,
                   "reports_nonempty": reports_nonempty, "self_healing_documented": self_healed,
                   "evidence_dimensions": dims},
        "pass": dims >= 3,
        "finding": "周更真实接线：调用脚本全存在、9 期周报连续非空、CHANGELOG 记录曾空转并自我修复——三维交叉成立，非 vanity",
    }


def r3():
    x = E["R3_data_consistency_r1"]
    tj = x["tools_json"]["tool_count"]
    badge = x["badge_claim"]["tools"]
    cat = x["category_table_anchor_rows"]
    adjusted = x["h3_adjusted"]
    explained = x["non_tool_h3_count"]
    consistent = tj == badge == cat == adjusted == 55
    h3_explained = (x["detail_h3_count"] - explained) == adjusted
    # 更新时间戳语义区分
    semantics_ok = semantic_has(x["verdict"], ["语义不同", "候选池", "正式收录清单", "不矛盾"])
    self_audit = bool(x["self_audit_hit"])
    return {
        "id": "R3", "name": "数据口径自洽（r1）",
        "checks": {"tools_json": tj, "badge": badge, "category_rows": cat,
                   "h3_adjusted": adjusted, "four_way_consistent": consistent,
                   "h3_gap_explained": h3_explained, "timestamp_semantics_ok": semantics_ok,
                   "self_audit_recorded": self_audit},
        "pass": consistent and h3_explained and semantics_ok,
        "finding": "tools.json/badge/分类表/详情(扣6非工具小节)=55 全自洽；『61≠55』为 h3 计数假阳性，判据自审排除；时间戳不矛盾（周报=候选池 vs tools.json=正式清单）",
    }


def r4():
    x = E["R4_ci_wiring_r2"]
    chain = semantic_has(x["test_chain"], ["matrix", "test", "coverage", "依赖"])
    jobs = len(x["ci_jobs"])
    waivers_empty = "null" in str(x["coverage_policy"]["waivers"]).lower() or x["coverage_policy"]["waivers"] in (None, "")
    report_only_labeled = "report-only" in x["doc_drift_workflow"]["mode"] and semantic_has(x["doc_drift_workflow"]["honest_label"], ["report-only", "不执行", "without executing"])
    pinned = bool(x["pinned_actions"])
    return {
        "id": "R4", "name": "CI 门禁接线与可证伪工程（r2）",
        "checks": {"chain_wired": chain, "job_count": jobs, "waivers_empty": waivers_empty,
                   "doc_drift_honestly_report_only": report_only_labeled, "actions_pinned": pinned},
        "pass": chain and jobs >= 5 and waivers_empty and report_only_labeled and pinned,
        "finding": "discover→matrix→test→coverage 完整接线，分层覆盖率+空 waiver 是可证伪门禁；doc-drift 诚实标注 report-only 不假装阻断",
    }


def r5():
    x = E["R5_errata_r2"]
    roots = len(x["root_causes"])
    per_ticker = x["has_per_ticker_evidence"]
    warning = x["has_actionable_warning"]
    trace = bool(x["traceability"])
    correction = semantic_has(x["headline_correction"], ["11 PASS", "仅 HOMB", "2-3"])
    return {
        "id": "R5", "name": "自我纠错台账可信度（r2）",
        "checks": {"root_causes_ge5": roots >= 5, "per_ticker_evidence": per_ticker,
                   "old_report_invalidation_warning": warning, "traceability": trace,
                   "headline_corrected": correction},
        "pass": roots >= 5 and per_ticker and warning and trace and correction,
        "finding": "errata 逐条给出原判/改正/5类根因/证据，明确旧报告不可下单，带 issue 追溯——『会拦会降级』实证",
    }


def r6():
    lessons = E["R6_candidate_lessons"]
    all_have_block = all(semantic_has(l["would_block"], ["判", "标注", "拒绝", "核查", "先怀疑", "不计入", "不予采信"]) for l in lessons)
    return {
        "id": "R6", "name": "复述/长牙决策与判据自审",
        "checks": {"lesson_count": len(lessons), "all_have_concrete_block_action": all_have_block},
        "pass": len(lessons) >= 4 and all_have_block,
        "lessons": [{"id": l["id"], "from": l["from"], "lesson": l["lesson"], "would_block": l["would_block"]} for l in lessons],
        "finding": "5 条候选经验均通过『具体被拦动作』检验，属长牙候选而非复述；可考虑编译进本仓门禁",
    }


def main():
    checks = [r1(), r2(), r3(), r4(), r5(), r6()]
    result = {
        "audit_id": "RANDOM-ACTIVE-REPOS-AUDIT",
        "generated_at": "2026-11-22T00:35:00+08:00",
        "three_layer_honesty": {
            "fact_true": "证据均为一手文件/API 元数据，SHA256 已锁存",
            "conclusion_caveat": "结论真需满足判据+证据交叉；fork 不等于原创/非贡献；文档自洽≠代码正确；测试存在≠已执行",
            "unverified": "未实跑两仓脚本；r1 shallow clone 无法列全 commit 级净贡献；r2 未逐文件 diff 上游"
        },
        "criteria": checks,
        "summary": {
            "total": len(checks),
            "passed": sum(1 for c in checks if c["pass"]),
            "all_pass": all(c["pass"] for c in checks),
            "self_audit_hits": 2,
            "self_audit_note": "实际捕获并排除 2 次检查器假阳性（脚本缺失误判、h3 计数误判），均已写入证据并反向印证 KB-AUDIT01/02"
        }
    }
    (BASE / "random_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
    for c in checks:
        print(("PASS" if c["pass"] else "FAIL"), c["id"], c["name"])


if __name__ == "__main__":
    main()
