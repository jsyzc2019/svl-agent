#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§L3 canary 可判定性的严格诊断：单调判据不可分 vs U 型伪影判据可分。

【本轮诚实发现】初始假设"canary 对字面判据数学不可分"被数据【部分证伪】：
- 单调判据（越像越真 / 越不像越真）确实无法分离三簇（GT=True 在相似度两端，False 在中间，U 型标签）；
- 但 U 型判据（极像 OR 极不像 → True，中间 → False）能在冻结集内 18/18 达成。

【修正后的精确结论】
- canary 的 GT=True 来自"同一论文的另一句原文"这一【来源关系/生成伪影】，不是可从 claim/evidence
  两串文本泛化的字面语义；
- U 型判据是 seen-label 的 post-hoc 拟合（看过标签才设计得出），无独立验证集，学的是构造签名而非语义；
- 因此在【可泛化判据】意义上 canary 仍不可达：任何 post-hoc 拟合都是 Goodhart，不构成缺口关闭。

纪律：纯诊断分析，只读 §100 冻结样本；不产生新判定，不改任何 result.json verdict；
      不动 §100 冻结集；l3/absolute 保持 false；最终裁定权在用户。

运行：python3.11 audit_l3_gap_targeted/prove_canary_unreachability.py
"""
import json
import os
import re
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "audit_frozen_holdout", "downloads", "samples.json")

NEG = {"not", "no", "never", "nor", "cannot", "without", "neither"}
CONN = {"however", "though", "although", "whereas", "but", "yet", "nevertheless",
        "nonetheless", "while", "still"}
FUNC = {"the", "a", "an", "of", "to", "in", "on", "at", "by", "for", "with", "from", "and", "or",
        "as", "is", "are", "was", "were", "be", "been", "being", "that", "this", "these", "those",
        "it", "its", "we", "our", "their", "than", "then", "so", "such", "if", "when", "which",
        "who", "whom", "whose", "there", "here", "into", "over", "under", "between", "within",
        "about", "can", "could", "may", "might", "will", "would", "shall", "should", "do", "does",
        "did", "have", "has", "had", "also", "only", "even", "own", "same"}


def toks(t):
    return re.findall(r"[a-z0-9]+(?:'[a-z0-9]+)*", t.lower().replace("-", " "))


def content(t):
    return [w for w in toks(t) if w not in FUNC and w not in NEG and w not in CONN]


def mdiff(a, b):
    ca, cb = Counter(a), Counter(b)
    return sum((ca - cb).values()) + sum((cb - ca).values())


def features(r):
    a, b = toks(r["claim"]), toks(r["evidence"])
    sa, sb = set(a), set(b)
    jaccard_sim = len(sa & sb) / max(1, len(sa | sb))
    return {
        "content_diff": mdiff(content(r["claim"]), content(r["evidence"])),
        "neg_diff": mdiff([w for w in a if w in NEG], [w for w in b if w in NEG]),
        "conn_diff": mdiff([w for w in a if w in CONN], [w for w in b if w in CONN]),
        "num_diff": mdiff([w for w in a if w[0].isdigit()], [w for w in b if w[0].isdigit()]),
        "jaccard_sim": jaccard_sim,
        "len_ratio": max(len(a), len(b)) / max(1, min(len(a), len(b))),
    }


def load():
    rows = []
    for r in json.load(open(SAMPLES, encoding="utf-8"))["samples"]:
        f = features(r)
        f.update(id=r["id"], variant=r["variant"], gt=r["ground_truth_supported"])
        rows.append(f)
    return rows


def best_monotone(rows):
    """枚举单特征×阈值×方向的最优单调判据，返回最佳准确率与其失败样本。"""
    results = []
    for feat in ("content_diff", "jaccard_sim", "neg_diff", "conn_diff", "num_diff", "len_ratio"):
        vals = sorted(set(r[feat] for r in rows))
        # 候选阈值：相邻值中点（含端点外扩）
        cands = [vals[0] - 1e-9]
        cands += [(vals[i] + vals[i + 1]) / 2 for i in range(len(vals) - 1)]
        cands += [vals[-1] + 1e-9]
        for t in cands:
            for direction in ("le_true", "gt_true"):  # feat<=t → True ; feat>t → True
                pred = {r["id"]: (r[feat] <= t if direction == "le_true" else r[feat] > t)
                        for r in rows}
                correct = sum(pred[r["id"]] == r["gt"] for r in rows)
                fails = [r["id"] for r in rows if pred[r["id"]] != r["gt"]]
                results.append({"acc": correct, "total": len(rows), "feat": feat,
                                "threshold": round(t, 4), "direction": direction,
                                "fails": fails})
    results.sort(key=lambda x: -x["acc"])
    return results[:5]


def u_shaped(rows):
    """U 型判据：jaccard_sim>hi 或 <lo → True，中间 → False。找能 18/18 的参数。"""
    sims = {v: [r["jaccard_sim"] for r in rows if r["variant"] == v]
            for v in ("clean", "tampered", "canary")}
    clean_min = min(sims["clean"])          # 1.0
    tam_lo, tam_hi = min(sims["tampered"]), max(sims["tampered"])   # 0.04..0.20
    can_hi = max(sims["canary"])            # 0.24 (approx)
    # 取 hi 在 clean_min 与 tam_hi 之间，lo 在 tam_lo 与 can_hi 之间
    hi = (clean_min + tam_hi) / 2
    lo = (tam_lo + can_hi) / 2
    pred = {r["id"]: (r["jaccard_sim"] > hi or r["jaccard_sim"] < lo) for r in rows}
    correct = sum(pred[r["id"]] == r["gt"] for r in rows)
    return {"hi": round(hi, 4), "lo": round(lo, 4),
            "acc": correct, "total": len(rows),
            "intervals": {k: [round(min(v), 3), round(max(v), 3)] for k, v in sims.items()},
            "is_perfect": correct == len(rows)}


def main():
    rows = load()
    mono = best_monotone(rows)
    u = u_shaped(rows)
    report = {
        "boundary": "纯诊断；只读§100冻结样本；不改verdict/冻结集；l3/absolute仍false；"
                    "U型判据是post-hoc伪影拟合，不构成缺口关闭。",
        "initial_hypothesis": "canary 对字面判据数学不可分（预期）",
        "finding": "部分证伪：单调判据确不可分，但U型伪影判据在冻结集内18/18可达",
        "label_structure": {
            "pattern": "U型/非单调：GT=True 在字面相似度两端(clean 完全相同 / canary 完全不同)，"
                       "GT=False 夹在中间(tampered 轻微改写)",
            "why_monotone_fails": "单调函数无法用一个阈值覆盖相似度两端而排除中间",
        },
        "best_monotone": mono,
        "monotone_max_acc": mono[0]["acc"],
        "u_shaped": u,
        "refined_conclusion": [
            "单调字面判据最优仅 %d/18 —— 两家外家判据(数值限定词/词类多重集)都属单调一致性框架，"
            "故系统性栽在 canary，非偶然。" % mono[0]["acc"],
            "U 型判据能 18/18，但它学的是冻结集的【生成伪影】(clean=逐字复制/canary=另句原文/"
            "tampered=轻微改写)，是看过标签的 post-hoc 设计，无独立验证集。",
            "canary 的 GT=True 源自【来源关系】(同论文另一句)而非可从两串文本泛化的语义；"
            "冻结集只给 claim/evidence 两串，排除了来源信息，故【可泛化判据】意义上仍不可达。",
            "任何用 U 型判据'关闭缺口'都是 Goodhart 过拟合，纪律禁止；"
            "verdict 保持 GAP_INCONCLUSIVE，l3/absolute 保持 false。",
        ],
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
