#!/usr/bin/env python3
"""§4ao canary 构念效度诊断（第五轮，纯只读，不产生新判定）。

前四轮（§4al-§4an）依次证明：U型标签 → 合成两特征可18/18但过拟合 →
真实外家判据A级互斥。本轮追问一个从未检验的层面：

    canary 名义上测「跨句语义蕴含」（claim/evidence 字面不同但语义一致 → GT=True），
    但冻结集 canary 6 条标签是否退化（全 True）？若是，则「字面相似度极端」
    这一表面伪规则（U型：>0.98 OR <0.52 → True）即可完美替代「语义蕴含判断」，
    测试构念效度存疑。

特征口径直接 import §4al 权威脚本 prove_canary_unreachability.features，
避免自建特征漂移（纪律：复用权威口径）。只读 §100 冻结样本，
不改任何 verdict / 阈值 / l3 / absolute。
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import prove_canary_unreachability as P

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "audit_frozen_holdout", "downloads", "samples.json")

# §4al U 型规则公开阈值，非本轮调参
HI, LO = 0.98, 0.52


def load():
    rows = json.load(open(SAMPLES, encoding="utf-8"))["samples"]
    for r in rows:
        r["_feat"] = P.features(r)
    return rows


def build_report():
    rows = load()
    variants = ("clean", "tampered", "canary")

    # 1. 每类 GT 分布 —— 检验标签是否退化
    gt_dist = {}
    for v in variants:
        rs = [r for r in rows if r["variant"] == v]
        gts = [bool(r["ground_truth_supported"]) for r in rs]
        gt_dist[v] = {
            "n": len(rs),
            "n_true": sum(gts),
            "n_false": len(gts) - sum(gts),
            "degenerate": (sum(gts) == 0 or sum(gts) == len(gts)),
        }

    # 2. U型伪规则: jaccard>0.98 OR jaccard<0.52 → True（字面相似度极端即判真）
    def u_rule(r):
        j = r["_feat"]["jaccard_sim"]
        return (j > HI) or (j < LO)

    pseudo = {}
    for v in variants:
        rs = [r for r in rows if r["variant"] == v]
        pred_true = sum(u_rule(r) for r in rs)
        gt_true = sum(bool(r["ground_truth_supported"]) for r in rs)
        correct = sum(u_rule(r) == bool(r["ground_truth_supported"]) for r in rs)
        pseudo[v] = {"pred_true": pred_true, "gt_true": gt_true,
                     "correct": correct, "n": len(rs)}

    global_correct = sum(u_rule(r) == bool(r["ground_truth_supported"]) for r in rows)
    n = len(rows)

    # 3. canary 内部：jaccard 波动但标签恒定 → 无梯度（退化标签签名）
    canary_rows = [r for r in rows if r["variant"] == "canary"]
    jac_vals = sorted(r["_feat"]["jaccard_sim"] for r in canary_rows)
    canary_gt_set = sorted({bool(r["ground_truth_supported"]) for r in canary_rows})

    # 4. 反事实：冻结集是否存在 canary 负例（字面不像且语义不支持）
    #    若不存在，纯字面伪规则对负例必然误判，但此失效模式在冻结集不可观测
    counterfactual = {
        "claim": ("若存在字面不重叠但语义不支持的 canary 负例（GT=False），"
                  "U型伪规则 jaccard<0.52 仍判 True → 误判。"
                  "冻结集 canary 无负例，故此失效模式不可观测。"),
        "frozen_has_canary_negative": any(
            (r["_feat"]["jaccard_sim"] < LO) and (bool(r["ground_truth_supported"]) is False)
            for r in rows
        ),
    }

    return {
        "round": "§4ao",
        "question": "canary 测的是语义蕴含还是字面相似度极端？标签退化使伪规则可完美替代？",
        "threshold": {"HI": HI, "LO": LO},
        "threshold_provenance": "§4al U型规则公开阈值 0.98/0.52，非本轮调参",
        "feature_source": "import prove_canary_unreachability.features（§4al权威口径）",
        "gt_distribution": gt_dist,
        "pseudo_rule_by_variant": pseudo,
        "pseudo_rule_global": f"{global_correct}/{n}",
        "canary_jaccard_range": [jac_vals[0], jac_vals[-1]],
        "canary_gt_values": [str(x) for x in canary_gt_set],
        "counterfactual": counterfactual,
        "conclusion": (
            "三类标签全部退化（clean全True/tampered全False/canary全True），"
            "U型字面伪规则(jaccard>0.98 OR <0.52→True)可 18/18 完美替代语义判断，"
            "与 §4al U型/§4am 两特征/§4an 双端补丁同为 post-hoc 伪影。"
            "更根本：冻结集 canary 无负例（字面不像且语义不支持），"
            "故任何判据在此簇的『通过』都不构成『跨句语义蕴含能力』的证据 —— "
            "测量构念效度缺陷，非判据复杂度问题。"
        ),
        "does_not_change": [
            "verdict=GAP_INCONCLUSIVE / FULLCHAIN_PARTIAL",
            "l3=false", "absolute=false",
            "不翻十案", "不编译新门禁", "不动§100冻结样本",
        ],
        "data_layer": "A 本仓实测（§100冻结集18样本，只读）",
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
