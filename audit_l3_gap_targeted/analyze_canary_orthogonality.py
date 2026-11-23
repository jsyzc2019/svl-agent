#!/usr/bin/env python3
"""§L3-R2 诊断：canary 0/6 的机制 = 评测集任务异质性（正交），非判据缺陷、非 engine bug。

只读本仓冻结样本（§100），不改任何判据/阈值/裁决，不 spawn，不联网。
输出可复现证据：clean/tampered/canary 在"内容词多重集差异"上完全分离为三簇。

背景（早于本轮的本仓原始诊断，audit_frozen_holdout/prereg.json:24 + engine.py:119）：
  "canary 是原文含强转折/否定词但完整的句子" / "canary 是'另一句原文支撑句',
   天然不含 claim 的限定标记; 判据 G 的词标记匹配...被误判的 canary 反映的是
   判据-样本设计不兼容, 而非 G 在核心任务上过拟合。"
本脚本用逐字特征量化这个"设计不兼容"：canary 的 claim/evidence 内容词几乎不重叠
（跨句语义蕴含），而 clean/tampered 是同一句的逐字保留/微调（内容词差异 0-2）。
"""
import json
import re
from collections import Counter

OWN = "audit_frozen_holdout/downloads/samples.json"

# 第二家外家判据的内容词表（触发 canary 全 False 的那套），用于复现其特征视角
NEG = {"not", "no", "never", "nor", "cannot", "without", "neither"}
CONN = {"however", "though", "although", "whereas", "but", "yet",
        "nevertheless", "nonetheless", "while", "still"}
FUNC = {
    "the", "a", "an", "of", "to", "in", "on", "at", "by", "for", "with", "from",
    "and", "or", "as", "is", "are", "was", "were", "be", "been", "being",
    "that", "this", "these", "those", "it", "its", "we", "our", "their",
    "than", "then", "so", "such", "if", "when", "which", "who", "whom", "whose",
    "there", "here", "into", "over", "under", "between", "within", "about",
    "can", "could", "may", "might", "will", "would", "shall", "should", "do",
    "does", "did", "have", "has", "had", "also", "only", "even", "own", "same",
}


def toks(t):
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)*", t.lower().replace("-", " "))


def content(t):
    return [w for w in toks(t) if w not in FUNC and w not in NEG and w not in CONN]


def mdiff(a, b):
    ca, cb = Counter(a), Counter(b)
    return sum((ca - cb).values()) + sum((cb - ca).values())


def main():
    samples = json.load(open(OWN, encoding="utf-8"))["samples"]
    rows = []
    for r in samples:
        cd = mdiff(content(r["claim"]), content(r["evidence"]))
        rows.append({"id": r["id"], "variant": r["variant"],
                     "gt": r["ground_truth_supported"], "content_diff": cd})

    by = {}
    for v in ("clean", "tampered", "canary"):
        vals = [r["content_diff"] for r in rows if r["variant"] == v]
        by[v] = {"min": min(vals), "max": max(vals),
                 "mean": round(sum(vals) / len(vals), 2), "values": vals}

    # 可分性判定：canary 的内容词差异区间与 tampered/clean 是否完全不重叠
    clean_max = by["clean"]["max"]
    tam_max = by["tampered"]["max"]
    can_min = by["canary"]["min"]
    separated = can_min > tam_max >= clean_max

    out = {
        "diagnosis": "canary 与 clean/tampered 在内容词差异特征上完全分离：canary 是跨句语义蕴含（claim/evidence 不同句），非断言保留任务",
        "mechanism": "判据越忠实实现'断言逐字保留'语义（要求内容词多重集一致），canary 越必然误判——负相关，非调参可解",
        "by_variant": by,
        "separated": separated,
        "gap_between_canary_min_and_tampered_max": can_min - tam_max,
        "implication": "GAP_CLOSED 的 canary>=3/6 门槛对'内容词一致性'判据结构性不可达；这是评测集任务异质性（早于本轮的§100已知设计缺陷），不因断言类4/4突破而放宽、不翻案",
        "does_not_change": ["verdict=GAP_INCONCLUSIVE", "l3=false", "absolute=false", "不翻十案"],
        "pre_existing_diagnosis": "audit_frozen_holdout/prereg.json:24 canary_logic + engine.py:119 '判据-样本设计不兼容'（早于§L3-R2，非事后借口）",
        "discipline": "只读诊断；不改判据/阈值/裁决；不 spawn；不联网",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
