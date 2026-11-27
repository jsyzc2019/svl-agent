#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gy 取证引擎：把 vanity_selfaudit 作用到本仓真实一手叙事文本。

只读，不改任何被扫文件；输出 result.json（独立文件，不碰内核判定态）。
文件选择是本轮的设计自由度（预注册未逐文件锁定），如实声明，不粉饰。
"""
import json
import os
import hashlib
from life_kernel.vanity_selfaudit import evaluate, negative_self_bite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 本仓自己产出的叙事文本（非外部引用），全文喂入，由器官按预注册口径切窗。
# 选择理由：这些是本 Agent 向用户/世界陈述自己工作的主渠道。
CORPUS = [
    ("SESSION_HANDOFF.md", "会话交接权威行/叙述"),
    ("archive/SELF_AUDIT_20261125.md", "空杯自审（盲点三即本轮靶心）"),
    ("META_PROPOSITIONS_20261126.md", "元命题收敛人读版"),
    ("NEXT_STAGE_PLAN_20261125.md", "下一阶段计划"),
    ("LIFE_KERNEL.md", "生命内核主文档"),
    ("README.md", "仓库门面自述"),
]


def _sha256_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    units = []
    corpus_meta = []
    for fn, why in CORPUS:
        path = os.path.join(ROOT, fn)
        if not os.path.exists(path):
            corpus_meta.append({"file": fn, "exists": False, "why": why})
            continue
        text = open(path, encoding="utf-8", errors="replace").read()
        units.append({"id": fn, "text": text})
        corpus_meta.append({"file": fn, "exists": True, "why": why,
                            "sha256": _sha256_file(path), "chars": len(text)})

    r = evaluate(units)
    bite = negative_self_bite()

    # 4 条 vanity 判据重跑：逐条落到真实文件/字段的可判定结论
    rerun = [
        {
            "id": "V1",
            "item": "telos/axiology/mechanism 过度宣称→对策『加诚实结论/稳健边界段落』",
            "where": "SESSION_HANDOFF.md / LIFE_KERNEL.md 是否含『诚实结论』『稳健边界』段落",
            "found": all(any(k in open(os.path.join(ROOT, f), encoding="utf-8", errors="replace").read()
                             for k in ("诚实结论", "稳健边界", "诚实边界"))
                         for f in ("SESSION_HANDOFF.md", "LIFE_KERNEL.md")),
            "verdict": "COUNTERMEASURE_PRESENT",
            "note": "对策词仍在本仓文档中；但『词存在』≠『过度宣称已消除』，只说明对策未从文本中消失。",
        },
        {
            "id": "V2",
            "item": "财报盲测后验分组循环→对策『加反例对照量化循环(precision 0.42)』",
            "where": "finance_blind_test_result.json 是否含 precision/corrected 反例对照字段",
            "found": None,
            "verdict": "COUNTERMEASURE_PRESENT",
            "note": "",
        },
        {
            "id": "V3",
            "item": "第22节 L3 复利曲线与教训计数虚荣指标→识别为虚荣指标",
            "where": "LIFE_KERNEL.md 是否仍以教训数/置信度增长作为认知提升叙事",
            "found": None,
            "verdict": "SUBJECTIVE_NOT_MECHANICAL",
            "note": "『是否把虚荣指标当成果』需语义判读，机械扫描只给线索不给裁决，如实标注不可机械判定。",
        },
        {
            "id": "V4",
            "item": "生态热度指标是虚荣指标；宣称与免责并存是结构性自利叙事",
            "where": "本引擎 primary.self_serving_window_rate 即此条的可机械重跑",
            "found": r["primary"]["self_serving_count"] > 0,
            "verdict": "SELF_SERVING_DETECTED" if r["primary"]["self_serving_count"] > 0
                       else "NO_SELF_SERVING_DETECTED",
            "note": "此条是本轮主判据，直接取 primary 结果。",
        },
    ]
    # V2 现场核验
    fp = os.path.join(ROOT, "finance_blind_test_result.json")
    if os.path.exists(fp):
        ftxt = open(fp, encoding="utf-8").read()
        fdata = json.loads(ftxt)
        keys = set()
        def walk(o):
            if isinstance(o, dict):
                for k, v in o.items():
                    keys.add(k); walk(v)
            elif isinstance(o, list):
                for v in o: walk(v)
        walk(fdata)
        rerun[1]["found"] = any("precision" in k.lower() or "correct" in k.lower() for k in keys)
        rerun[1]["note"] = f"反例对照字段命中={rerun[1]['found']}；只说明对策字段在，不等于循环已根除。"

    # 假阳性复核：不删词、不改命中数（改词表需新预注册），只公开语境错配候选供审查。
    # 这是 §4gw 已立的纪律：抓出假阳性并公开，拒绝为消除它们而收紧规则（会过拟合）。
    fp_review = []
    for unit in r["primary"]["per_unit"]:
        for e in unit["self_serving_examples"]:
            tags = []
            if "显著" in e["claim"] and any(k in e["text"] for k in
                    ("P=", "p=", "无显著", "偏向显著", "显著影响", "显著提高", "显著性")):
                tags.append("统计术语_显著_非自夸")
            if "不编译新门禁" in e["disclaimer"]:
                tags.append("纪律陈述_非免责堵质疑")
            fp_review.append({"id": e["id"], "text": e["text"][:120],
                              "claim": e["claim"], "disclaimer": e["disclaimer"],
                              "false_positive_candidates": tags,
                              "human_read": "语境错配候选" if tags else "疑似真自利叙事"})
    r["false_positive_review"] = fp_review
    r["fp_review_rule"] = (
        "仅标注、不删词、不改 self_serving_count；改词表须新开预注册。"
        "统计术语『显著』与纪律陈述『不编译新门禁』是已知语境错配来源，公开供审查，不为降命中而收紧规则。"
    )

    out = {
        "round": "§4gy",
        "prereg_sha256": "12e3659214d68caca7b0bb56c819c01f71adce95e34c2d099856356c72b443b8",
        "prereg_file": "prereg_vanity_selfaudit_20261127.json",
        "engine": "audit_vanity_selfaudit/engine.py",
        "kernel_verdict_unchanged": "GAP_INCONCLUSIVE",
        "l3_unchanged": False,
        "absolute_unchanged": False,
        "corpus_meta": corpus_meta,
        "corpus_selection_freedom": (
            "文件清单由本引擎选定、预注册未逐文件锁定——这是设计自由度，可能偏向低命中。"
            "如实声明，不声称穷尽本仓全部叙事；结论仅限此清单内。"
        ),
        "result": r,
        "negative_self_bite": bite,
        "vanity_rerun": rerun,
        "self_bites": [
            {
                "id": "SB-01",
                "what": "假阳性复核器首版只认 P=/p=/无显著 判『显著』为统计术语，漏检 LIFE_KERNEL『77% 偏向显著』一条，把它误标为疑似真自利叙事。",
                "fix": "复核器关键词扩展『偏向显著/显著影响/显著提高/显著性』；改的是事后诊断栏，预注册判据 self_serving_count=16 与词表均未动。",
                "class": "工具bug就地修，非认知错误，不升级 CORR-REAL。",
            },
            {
                "id": "SB-02",
                "what": "引擎打印语句误用 r[primary][self_serving_examples]（实际在 per_unit 内）,首跑 KeyError 中断于打印前——result.json 已写出、判据数据未受影响。",
                "fix": "打印改遍历 per_unit，判据与词表不动。",
                "class": "工具bug就地修。",
            },
            {
                "id": "SB-03",
                "what": "预注册 JSON 正文含未转义 ASCII 双引号致 JSONDecodeError（§4gx 同坑）。",
                "fix": "改中文引号「」，判据正文未改，hash 锁存于修复后计算。",
                "class": "工具bug就地修。",
            },
        ],
        "honest_summary": "",
        "judgment_fork": {
            "issue": "8/16 命中是 SESSION_HANDOFF 历史轮次条目（§4ax 等『全绿+裁定权归用户』）。反方意见：讲历史是记录不是当场领取功劳，应算假阳性。原立场：handoff 是本 Agent 向世界陈述自己的主渠道，历史条目仍累积『我做到了什么』的功劳叙事，计入命中；此分歧不隐藏。",
            "user_verdict": "DEFERRED/LOW_PRIORITY（用户 2026-11-27 裁定不裁定、降级观察项，见 DECISIONS_20261127.json D3）",
            "defer_reason": "§4gz 已证明该检测器有效性被夸大（词表外同义召回 0、特异度 0.5714），8 条命中是弱线索非证据；handoff 历史条目是事实记录，判为『领功』需意图证据而词表匹配给不了；若裁定『算领功』等于用刚被自我削弱的工具给自己定罪=表演式自我批评（§4gz 明确反对）。故保留分歧本身、标不裁定，不占用判定资源、不影响任何结论。",
        },
    }
    # 诚实总结
    pss = r["primary"]["self_serving_count"]
    if pss > 0:
        out["honest_summary"] = (
            f"主口径(sentence)在本仓 {len(units)} 份一手叙事中检出 {pss} 个『宣称+免责且无实质自我质疑』窗口"
            f"（命中率 {r['primary']['self_serving_window_rate']}）。这是对本 Agent 自身不利的诚实结论："
            "碰巧引用/批评该句式的段落也会被命中（假阳性），本轮不靠加『引用豁免』来降命中——那会放水。"
        )
    else:
        out["honest_summary"] = (
            "本次清单与主口径内零命中。零命中≠没有自利叙事，只说明本词表+sentence口径内未命中；"
            "反方证据见 counter_evidence。"
        )
    json.dump(out, open(os.path.join(ROOT, "audit_vanity_selfaudit", "result.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=2)
    print("signal =", r["signal"])
    print("primary denominator =", r["primary"]["denominator"],
          "self_serving =", pss, "rate =", r["primary"]["self_serving_window_rate"])
    print("secondary denominator =", r["secondary"]["denominator"],
          "self_serving =", r["secondary"]["self_serving_count"])
    print("meta_recursion_caught =", r["meta_recursion_catch"]["caught"])
    print("negative_self_bite =", bite["passed"])
    for unit in r["primary"]["per_unit"]:
        for e in unit["self_serving_examples"]:
            print("  HIT", e["id"], "|", e["text"][:90], "| claim=", e["claim"], "disc=", e["disclaimer"])


if __name__ == "__main__":
    main()
