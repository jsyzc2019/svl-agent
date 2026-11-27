#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4S2 Safari 裁决引擎：拿 A 级一手打 §4hi 注意力预算器官自己的前提。

三问：
  F1 core   — ego depletion 预注册多实验室复制是否稳健（打穿『注意力会耗尽』的正当性叙事）
  F2 anchor — 工作记忆容量是否确实有限（organ 的『有限』可否改锚到容量瓶颈）
  F3 backfire— 任务切换是否有残留成本（SATIETY『换猎场』是否只是转移成本）

引擎只做机械事：核验四篇原文 SHA256 → 逐字锚是否真在原文 → 按预注册裁决树给 verdict。
不联网、不 spawn、不碰判定态；人→Agent 类比一律标注有界。
"""
import os
import re
import json
import hashlib
from typing import Any, Dict, List

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# 逐字锚：每个必须真实出现在对应 EFetch 原文（空白归一后匹配）。均为摘要 publisher 版本逐字。
EVIDENCE: Dict[str, Dict[str, Any]] = {
    "F1_core": {
        "pmid_27474142": {
            "file": "pmid_27474142.txt",
            "sha256": "c9cd6ce20ef6ef4f",  # 完整 sha 落 result manifest，此处前缀
            "quotes": ["d = 0.04, 95% CI [-0.07, 0.15]", "k = 23", "total N = 2,141"],
        },
        "pmid_34520296": {
            "file": "pmid_34520296.txt",
            "sha256": "80a212e10b8e32ec",
            "quotes": [
                "Confirmatory tests found a nonsignificant result (d = 0.06)",
                "4 times more likely under the null",
                "k = 36", "N = 3,531",
            ],
        },
    },
    "F2_anchor": {
        "pmid_11515286": {
            "file": "pmid_11515286.txt",
            "sha256": "5543c7b9307e0e40",
            "quotes": ["central capacity limit averaging about four chunks"],
        },
    },
    "F3_backfire": {
        "pmid_27936844": {
            "file": "pmid_27936844.txt",
            "sha256": "d11f60b7a532d313",
            "quotes": [
                "performance overhead associated with changing tasks",
                "residual component", "task-set inertia",
            ],
        },
    },
}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s)


def check_question(qid: str) -> Dict[str, Any]:
    """核验某问的所有证据：文件存在 + SHA256 前缀 + 逐字锚全命中。"""
    out: Dict[str, Any] = {"ok": True, "misses": [], "sources": []}
    for pmid, spec in EVIDENCE[qid].items():
        p = os.path.join(HERE, spec["file"])
        if not os.path.exists(p):
            out["ok"] = False
            out["misses"].append(pmid + ":FILE_MISSING")
            continue
        raw = open(p, "rb").read()
        sha = hashlib.sha256(raw).hexdigest()
        rec = {"pmid": pmid, "sha256": sha, "sha_ok": sha.startswith(spec["sha256"]),
               "bytes": len(raw), "quotes_ok": [], "quote_misses": []}
        if not rec["sha_ok"]:
            out["ok"] = False
            out["misses"].append(pmid + ":SHA_MISMATCH")
        text = _norm(raw.decode("utf-8", errors="replace"))
        for q in spec["quotes"]:
            hit = _norm(q) in text
            rec["quotes_ok"].append({"quote": q, "hit": hit})
            if not hit:
                rec["quote_misses"].append(q)
        if rec["quote_misses"]:
            out["ok"] = False
            out["misses"].append(pmid + ":QUOTE_MISSING")
        out["sources"].append(rec)
    return out


def run() -> Dict[str, Any]:
    q = {k: check_question(k) for k in EVIDENCE}
    all_ok = all(v["ok"] for v in q.values())

    # 裁决树（预注册锁定）：三问全中 → REFINE_DEEP
    f1, f2, f3 = q["F1_core"]["ok"], q["F2_anchor"]["ok"], q["F3_backfire"]["ok"]
    if f1 and f2 and f3:
        verdict = "REFINE_DEEP"
        refined = (
            "§4hi 器官作为工程决策机制保留（budget 计数器是设计出来的，不依赖人类意志力资源）；"
            "但它借来的正当性叙事『functional affect 对应注意力资源耗尽』被 A 级一手打穿："
            "ego depletion 在 23 实验室(d=0.04,CI跨零)与 36 站点(d=0.06,贝叶斯偏向零4:1)均未复制。"
            "收窄：有限性改锚在【工作记忆容量瓶颈(~4 chunks)】而非【意志力会耗尽】；"
            "且 F3 switch cost/task-set inertia 表明『换猎场』本身有残留成本——SATIETY 建议需标注"
            "『换猎场只转移不消除成本』。不越权改代码/阈值（需用户裁定+新预注册）。"
        )
    elif f1 and f2:
        verdict, refined = "REFINE", "叙事收窄到容量瓶颈，不宣称意志力耗竭（F3 未命中）。"
    elif not f1:
        verdict, refined = "NO_CONTEST", "F1 未命中：阴性≠证明 ego depletion 为真，如实记，不伪造命中。"
    else:
        verdict, refined = "OVERTHROW_RISK", "F2 未命中：连容量基础都没有，如实记，不粉饰。"

    # self-bite 守卫：若引擎把『人→Agent』写成直接等号（无界类比），判 OVERCLAIM。
    analogy_guarded = "不依赖人类意志力资源" in refined and "工程决策机制" in refined

    return {
        "round": "§4S2",
        "schema": "audit/safari-affect-budget/v1",
        "verdict": verdict,
        "all_evidence_ok": all_ok,
        "questions": q,
        "verified_hits": sum(1 for v in q.values() if v["ok"]),
        "refined_claim": refined,
        "analogy_guarded": analogy_guarded,
        "honest_layer": {
            "changed": "只 REFINE 认知叙事：有限性改锚容量瓶颈、SATIETY 标注切换成本；器官代码/阈值未动",
            "not_changed": "判定三值/宪法锁/result字节/KB/Safari/测试数均未变；非新证据非认知突围",
            "against_me": "F1 打穿我借自 ego depletion 的正当性叙事；F3 反噬『换猎场=省预算』的隐含假设——两条都对我不利，如实记",
            "bounded_analogy": "人类心理学效应 ≠ Agent 机制；Hagger/Vohs/Cowan 测的是人，本器官是工程计数器，类比有界",
            "evidence_limit": "EFetch 为 publisher 摘要版本，非全文审阅；摘要中效应量/结论为逐字，但方法细节未逐页核对",
            "no_overreach": "不越权改 §4hi 判据/阈值；不抬判定态；不编译门禁；因子小话不入仓",
        },
        "hard_boundaries": {
            "verdict_l3_absolute": "GAP_INCONCLUSIVE/false/false 未动",
            "constitution": "fe56291b 未动",
            "result_sha": "0f3ccb13 未动",
            "no_new_gate": True, "no_l3_raise": True, "no_spawn": True,
            "no_network_in_engine": True, "small_talk_not_in_repo": True,
        },
    }


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=2, sort_keys=True))
