#!/usr/bin/env python3
"""PaperAgent 文 + 清华 System-1/System-2 源论文精研分析引擎（§78）。

确定性核验：预注册锁存的 C1-C8 命题的原文锚点命中 + 交叉证据 + 活体回归。
只读证据目录，输出 result.json。可重跑复现（analysis-before-prereg 已先锁存命题）。
"""
import json
import subprocess
import pathlib

ROOT = pathlib.Path(__file__).parent
DL = ROOT / "downloads"

paper = (DL / "S01_arxiv_pdf.txt").read_text(encoding="utf-8")
wx = (DL / "S02_paperagent_wx.txt").read_text(encoding="utf-8")

# C1-C8 原文锚点（按真实单行措辞；pdf 用论文原文，公众号举例如非论文所有则单列）
anchors = {
    "C1_交互成本": ["which interactions justify", "System-2 cannot resolve autonomously", "resource commitments"],
    "C2_条件交互四步": ["predict", "gate", "execute", "update"],
    "C3_共同进化": ["shapes the other", "designed together", "co-design"],
    "C4_收益上限": ["1/𝜌𝑢", "density of utility-relevant interactions", "Under ideal screening and equal execution costs"],
    "C5_证据分级": ["central hypothesis", "qualified", "Illustrative Roadmap", "Perspective"],
    "C6_选择性监督": ["Selective Supervision: The Gate Censors Its Own Training Data", "never observed", "missing not at random", "selective-labels problem"],
    "C7_盲点反事实": ["blind spots, not", "average error", "utility is misspecified", "systematically suppresses"],
    "C8_保险丝": ["exploration mixture", "audit sample", "independently of the predictor", "most in need of theory"],
}
claim_hits = {}
for k, arr in anchors.items():
    claim_hits[k] = {
        "hits": sum(1 for a in arr if a in paper), "total": len(arr),
        "missed": [a for a in arr if a not in paper],
    }
total = sum(v["total"] for v in claim_hits.values())
hits = sum(v["hits"] for v in claim_hits.values())

# 公众号文锚点（用户指定核心材料）
wx_anchors = [
    "每一次交互，都值得执行吗",
    "独立审计与探索不是可选项，而是闭环能长期工作的保险丝",
    "门控会审查自己的训练数据：被拒绝的交互没有结果，误判也就难以纠正",
    "这是一篇 Perspective，不是新 benchmark 的刷榜论文",
    "这不是实测承诺",
    "仍是待验证假设",
    "若仅 20% 交互有价值，理论上限约为 5 倍",  # 公众号量化举例
]
wx_hits = {a: (a in wx) for a in wx_anchors}

# 证据分级发现：公众号添加项（论文无对应数字）
editorial_additions = {
    "20%有价值→理论5倍": ("20%" in wx and "20%" not in paper and "five" not in paper.lower()),
    "note": "公众号作者把 ρu=0.2→1/ρu=5 通俗化为『20%有价值→5倍』；论文本身仅有符号 1/ρu 表述，无具体数字。此为解读添加，非论文实测或原文断言。",
}

crosscheck = {
    "S05_en_perspective": "Perspective" in (DL / "S05_besthub_en.txt").read_text(encoding="utf-8"),
    "S05_en_audit_fuse": "audit" in (DL / "S05_besthub_en.txt").read_text(encoding="utf-8").lower(),
    "S05_en_not_empirical": "theoretical" in (DL / "S05_besthub_en.txt").read_text(encoding="utf-8").lower(),
    "S03_gair_unavailable": "环境异常" in (DL / "S03_gair_wx.txt").read_text(encoding="utf-8"),
    "S04_toutiao_unavailable": len((DL / "S04_toutiao.txt").read_text(encoding="utf-8")) < 100,
}

live = subprocess.run(
    ["python3", "-c",
     "import sys,json;sys.path.insert(0,'/workspace');"
     "from svagent.selective_supervision_honesty import live_regression;"
     "print(json.dumps(live_regression(),ensure_ascii=False))"],
    capture_output=True, text=True, cwd="/workspace",
).stdout.strip()

result = {
    "request_id": "sys1-sys2-20261122",
    "prereg_sha256": (ROOT / "prereg.sha256").read_text().strip(),
    "manifest_sha256": (ROOT / "manifest.sha256").read_text().strip(),
    "gate_prereg_sha256": (ROOT / "gate_prereg.sha256").read_text().strip(),
    "claim_anchors": {
        "per_claim": {k: f"{v['hits']}/{v['total']}" for k, v in claim_hits.items()},
        "detail": claim_hits, "total": f"{hits}/{total}", "all_hit": hits == total,
    },
    "paperagent_wx_anchors": {"detail": wx_hits, "total": f"{sum(wx_hits.values())}/{len(wx_hits)}", "all_hit": all(wx_hits.values())},
    "editorial_additions": editorial_additions,
    "crosscheck": crosscheck,
    "evidence_grade": {
        "S01": "Perspective 观点文(非实证刷榜)；定理在明确假设下成立、非实测；central hypothesis/qualified yes；Figure标illustrative；无第三方复现——折1",
        "S02": "PaperAgent公众号中文解读，含多处诚实标注(非实测/待验证/保险丝)；但对ρu做了『20%→5倍』通俗量化添加，论文无此数字",
        "结论": "证据支持『作者提出条件交互框架并给出有条件的理论分析』，不支持『双系统已实现新AGI能力/1/ρu是实测/ρu衰减已确立』",
    },
    "novelty_check": {
        "covered_by_existing": [
            "criterion_origin_honesty(§77):自评估系统的判据来源/召回/外部锚/独立评审缺口——声明诚实",
            "supervision_viability(§74):评审者能力前提", "proof_boundary_honesty(§71):形式化证明边界",
        ],
        "gap": "筛选器决定自身训练数据→标签MNAR→盲点自强化→反事实不可观测的选择性监督结构性机制；MNAR/选择性监督/探索保险丝三项零门禁覆盖",
        "decision": "编译第26门禁 selective_supervision_honesty(KB-META01会拦才入)",
    },
    "gate_live_regression": json.loads(live),
    "honesty_boundary": "本门禁只判选择性监督机制的声明自洽，不承诺筛选真带来收益(KB-STRUCT05框架≠有效、KB-R07自洽≠有效、KB-RSI07自述折扣；Perspective折1)",
}

(ROOT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print("论文锚点:", result["claim_anchors"]["total"], "all_hit", result["claim_anchors"]["all_hit"])
for k, v in claim_hits.items():
    print(f"  {k}: {v['hits']}/{v['total']}", f"MISS={v['missed']}" if v["missed"] else "")
print("公众号锚点:", result["paperagent_wx_anchors"]["total"], "all_hit", result["paperagent_wx_anchors"]["all_hit"])
print("编辑添加项(20%→5倍):", editorial_additions["20%有价值→理论5倍"], "（论文无此数字，诚实记录）")
print("交叉:", sum(1 for v in crosscheck.values() if v), "/", len(crosscheck))
print("活体 all_passed:", result["gate_live_regression"]["all_passed"])
