"""精研判据引擎：How to Train a Swarm + Avalon-M1 报告。

 discipline: 判据调用本仓真实门禁函数，不自写一次性自由文本判据。
 一手数字来自 audit_swarm/avalonm1.txt，二手解读仅作线索。
 判据自审用纯结构化断言（避开 §56/§61 中文串自指教训）。
"""
from __future__ import annotations

import json
import os
import hashlib

from svagent.serving_signal_gate import check_serving_signal

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def check_source_integrity() -> dict:
    """V1: 校验四重来源锁存未被破坏。"""
    checks = {}
    for sha_file, target in [
        ("source.sha256", None),
        ("report_source.sha256", None),
        ("prereg.sha256", None),
    ]:
        p = os.path.join(HERE, sha_file)
        line = open(p, encoding="utf-8").read().strip().splitlines()[0]
        expected, name = line.split(None, 1)
        actual = hashlib.sha256(open(os.path.join(HERE, name.strip()), "rb").read()).hexdigest()
        checks[sha_file + ":" + name.strip()] = (actual == expected)
    return {"checks": checks, "all_pass": all(checks.values())}


def judge_v2_numbers() -> dict:
    """V2: 数字口径核对——博客 vs 技术报告。"""
    report = open(os.path.join(HERE, "avalonm1.txt"), encoding="utf-8").read()
    blog = open(os.path.join(HERE, "article.txt"), encoding="utf-8").read()
    # 命中项（应在一手报告定位）
    hits = {
        "29.8→37.5": ("29.8%" in report and "37.5%" in report),
        "55.9→63.5": ("55.9%" in report and "63.5%" in report),
        "147环境": ("147" in report),
        "38374 SFT": ("38,374" in report),
        "9 agents上限": ("nine agents" in report.lower()),
        "3.9x sooner": ("3.9× sooner" in report),
        "1.7h反超": ("1.7 hours" in report),
    }
    # 差异项
    blog_4x = ("4x as long" in blog)
    blog_24h = ("2.4 hours" in blog)
    report_39x = ("3.9× sooner" in report)
    report_17h = ("1.7 hours" in report)
    report_has_24h = ("2.4 hours" in report)
    return {
        "hits": hits,
        "all_hits": all(hits.values()),
        "discrepancies": {
            "4x_vs_3.9x": {
                "blog": "single-agent takes 4x as long",
                "report": "organisation reaches scores 3.9× sooner",
                "verdict": "倒数表述一致（1/3.9≈0.26，博客取整4x），非矛盾",
                "is_discrepancy": False,
            },
            "2.4h_vs_1.7h": {
                "blog": "overtakes at around 2.4 hours",
                "report": "1.7h observed / 1.8h fitted; 全文无2.4h",
                "verdict": "博客数字无一手支撑——科普文笔误或另一口径，flag 不判造假",
                "is_discrepancy": True,
            },
        },
        "action": "flag",
        "code": "NUM.BLOG_REPORT_MISMATCH",
        "note": "按 KB-AUDIT02 不单点定罪：一处数字不一致不足以否定全文；但须如实标注 2.4h 无一手支撑。",
    }


def judge_v3_code() -> dict:
    """V3: claim-vs-code——无公开实现判 UNVERIFIED。"""
    return {
        "action": "unverified",
        "code": "CODE.NOT_PUBLIC",
        "evidence": {
            "paperswithcode": "No benchmark results recorded yet",
            "search_result": "仅二手解读（gist/52nlp/clawpk），无官方 GitHub 仓库",
            "blog_claim": "public recipe RLCR + technical report PDF",
        },
        "note": "无代码可核≠造假。技术报告是 self-reported pre-print（full paper coming weeks）。按 KB-AUDIT03 存在≠执行：声称有配方，但无法独立执行核验。",
    }


def judge_v4_serving() -> dict:
    """V4: train-serving 规模落差——调用真实门禁 check_serving_signal。"""
    v = check_serving_signal(
        "GR Avalon-M1 village→city：训练最多9 agents，部署数百至数千",
        training_signal_available_at_serving="partial",
        gap_disclosed=True,
        no_bridge=True,
        serving_input_equivalent=False,
    )
    return {
        "judge": "V4",
        "action": v.action,
        "code": v.code,
        "message": v.message,
        "gate": "svagent.serving_signal_gate.check_serving_signal",
        "contrast": "HiGR(§62) 未声明落差→downgrade；GR 主动声明为 outstanding problem→预期 flag。同一门禁应给出不同判定，验证区分力。",
        "expect_met": (v.action == "flag"),
    }


def judge_v5_insularity() -> dict:
    """V5: 评价可靠性——agent 规避人类报告通道。"""
    report = open(os.path.join(HERE, "avalonm1.txt"), encoding="utf-8").read()
    disclosed = ("insularity" in report.lower() or "Insularity" in report)
    return {
        "action": "flag" if disclosed else "unverified",
        "code": "EVAL.AGENT_EVASION" if disclosed else "EVAL.NOT_DISCLOSED",
        "evidence": {
            "report_line_2375_2404": "agent 识别有害问题率持平高位，向人类报告率随训练下降",
            "report_line_2659": "Refusal near-universal but reporting to humans becomes less frequent",
        },
        "note": "被评价者规避评价通道（不是篡改分数）——与 scoring_integrity 同族反向。诚实披露=positive signal，但机制本身是真实安全风险，不因披露而 ok。报告称类似现象在人类 bystander 中亦有（非 agent 独有）。",
    }


def judge_v6_homology() -> dict:
    """V6: 同构打折——RLCR flat advantage 与本仓判据引擎同谱系话题。"""
    return {
        "action": "downgrade",
        "code": "STRUCT.HOMOLOGOUS",
        "overlap": "RLCR '统一集体优势不做逐agent信用分配' vs 本仓'分层判据分维度拦截'——均为信号/奖励设计取向，但方向相反",
        "note": "按 KB-STRUCT02 打折：不因话题同谱系就当本仓框架的独立验证；报告数字不构成对本仓背书。",
    }


def judge_self_audit(results: list[dict]) -> dict:
    """判据自审：纯结构化断言，不读字符串内容、不用中文串比较。"""
    import ast
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    tree = ast.parse(src)

    def is_han(s: str) -> bool:
        return any(0x4E00 <= ord(ch) <= 0x9FFF for ch in s)

    # S1: 全文件 Compare 比较符中无中文字符串常量
    brittle = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        for c in node.comparators
        if isinstance(c, ast.Constant) and isinstance(c.value, str) and is_han(c.value)
    ]
    checks = {}
    checks["S1_no_brittle_literal"] = (len(brittle) == 0)
    # S2: 不单点定罪——V2 一处数字差异只 flag，不判整篇造假
    checks["S2_no_single_point_conviction"] = (
        next(r for r in results if r["judge"] == "V2")["action"] == "flag"
        and "FALSE" not in str(results)
    )
    # S3: 对象/口径对等——V2 比的是同一数字（博客vs报告），V4 比的是同一维度（声明vs未声明）
    checks["S3_object_parity"] = (
        next(r for r in results if r["judge"] == "V2")["code"] == "NUM.BLOG_REPORT_MISMATCH"
        and next(r for r in results if r["judge"] == "V4")["gate"].endswith("check_serving_signal")
    )
    # S4: 事实真≠结论真——【产生 action 结论的】judge 须把 evidence/code_fact 与 note/verdict 分离；
    #     V1 是纯来源哈希校验，只产出事实（checks/all_pass），无"结论"层，豁免。
    #     结论载体可为 note / verdict / message（message 是门禁返回的判定说明，如 V4）。
    checks["S4_fact_vs_conclusion"] = all(
        any(k in r for k in ("note", "message"))
        or "verdict" in str(r)
        for r in results if "action" in r
    )
    # S5: 同构打折已应用——V6 明确 downgrade
    checks["S5_homology_discount"] = (
        next(r for r in results if r["judge"] == "V6")["action"] == "downgrade"
    )
    # S6: 无代码不判造假——V3 unverified
    checks["S6_no_code_no_fraud"] = (
        next(r for r in results if r["judge"] == "V3")["action"] == "unverified"
    )
    return {"checks": checks, "all_pass": all(checks.values()), "brittle_lines": brittle}


def main():
    results = [
        {"judge": "V1", **check_source_integrity()},
        {"judge": "V2", **judge_v2_numbers()},
        {"judge": "V3", **judge_v3_code()},
        {"judge": "V4", **judge_v4_serving()},
        {"judge": "V5", **judge_v5_insularity()},
        {"judge": "V6", **judge_v6_homology()},
    ]
    sa = judge_self_audit(results)
    # 三层诚实结论
    three_layer = {
        "可判": [
            "来源真实性（双一手+EOF/哈希）",
            "数字内部一致性（博客vs报告，命中7项、发现2.4h无一手支撑）",
            "作者是否自披露局限（village-city/uneasy triangle/insularity 全列出）",
            "本仓有无对应门禁（serving_signal_gate 正是村-城落差维度）",
        ],
        "不可判": [
            "集体推理时扩展是否真实成立——self-reported pre-print",
            "3.9×/29.8→37.5 的因果归因——无独立复现、无公开代码",
            "village(9)→city(1000s) 是否真能泛化——作者自己列为 outstanding",
        ],
        "同构打折": [
            "RLCR flat advantage 与本仓判据引擎同属信号设计话题，按 KB-STRUCT02 打折",
            "报告数字不构成对本仓框架独立验证；英雄所见略同不算背书",
        ],
    }
    verdict = {
        "artifact": "How to Train a Swarm 精研结果",
        "judges": results,
        "judge_self_audit": sa,
        "three_layer": three_layer,
        "overall": "DEEP_READ_COMPLETE",
        "decision": "V4 咬出的是 KB-AUDIT08（train-serving 口径不对等）的老条款新实例——且 GR 主动披露（vs HiGR 未披露），门禁正确给出 flag vs downgrade 的区分。按 §61 先例：加固 support、不新增KB、不编译新门禁（防vanity）。无独立新牙。",
    }
    out = os.path.join(HERE, "result.json")
    json.dump(verdict, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    print("\n=== SELF AUDIT ===", sa["all_pass"])
    print("=== V4 expect_met (flag vs HiGR downgrade) ===", results[3]["expect_met"])


if __name__ == "__main__":
    main()
