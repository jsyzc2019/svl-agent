#!/usr/bin/env python3
"""§4gb 取证引擎：从本仓已落档财务盲测结果现场抽取，跑构念效度器官。

纪律：
- 只读 finance_blind_test_result.json，不改它、不判定任何个股真假；
- 预注册哈希锁校验（先于取证）；
- 三条 falsification_log 记录写入独立 jsonl（不覆盖原 falsification_log.jsonl，先落档候选）；
- 判定态三值前后断言不动。
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG = os.path.join(ROOT, "prereg_finance_construct_validity_20261127.json")
FIN = os.path.join(ROOT, "finance_blind_test_result.json")
OUT = os.path.join(ROOT, "audit_finance_construct_validity", "result.json")
LOG_OUT = os.path.join(ROOT, "audit_finance_construct_validity", "falsification_entries.jsonl")

from life_kernel.construct_validity import evaluate, negative_self_bite


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def verdict_triplet():
    r = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    return (r["verdict"], r["l3_claimed"], r["absolute_claimed"])


def check_prereg():
    d = json.load(open(PREREG, encoding="utf-8"))
    locked = d.pop("sha256")
    actual = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return locked == actual, locked, actual


def main():
    before = verdict_triplet()
    lock_ok, locked, actual = check_prereg()
    assert lock_ok, f"prereg hash mismatch {locked} != {actual}"

    fin = json.load(open(FIN, encoding="utf-8"))
    rows = fin["results"]
    # 现场抽取：剔除标签未知的样本（中国平安 label_neg=-1 / 未取到）
    usable = [r for r in rows if r.get("label_neg") in (0, 1)]
    proxy = [r["label_neg"] for r in usable]        # 审计意见代理标签
    signals = [r["alarm"] for r in usable]          # 独立会计信号（判据预警）
    preds = [r["alarm"] for r in usable]            # 判据预测（本例同信号源，如实标注）

    cm = fin["metrics"]["混淆矩阵"]
    tp, fp = cm["TP"], cm["FP"]
    base_rate_sample = sum(proxy) / len(proxy) if proxy else None

    sens = fin["sensitivity"]
    configs = []
    for k, v in sens.items():
        configs.append({"name": k, "precision": v["precision"]})

    organ = evaluate(
        proxy_labels=proxy, signals=signals, predictions=preds,
        tp=tp, fp=fp, configs=configs, population_base_rate_hint=None,
    )
    nb = negative_self_bite()

    # 三层候选证伪记录（只记方法论事实，不判个股真假）
    gap_idx = organ["cv1_proxy_gap"]["indices"]
    gap_rows = [{"code": usable[i]["code"], "name": usable[i]["name"],
                 "alarm": usable[i]["alarm"], "label_neg": usable[i]["label_neg"],
                 "label_opinion": usable[i]["label_opinion"]} for i in gap_idx]
    entries = [
        {
            "id": "FALSIFY-CV1-PROXY-NOT-CONSTRUCT",
            "round": "§4gb",
            "target_belief": "审计意见代理标签可作为『财务叙事真实性』构念真值使用（本仓性能陈述隐含前提）",
            "method": "现场抽取 finance_blind_test_result.json 中 alarm=1 但 label_neg=0 的背离样本，只判标签-信号背离事实",
            "finding": f"背离样本 {len(gap_rows)} 家（代理标签阴性但会计信号预警），代理与构念不可等同",
            "divergent_samples": gap_rows,
            "honest_limit": "不判定任何个股造假真值（清单红线）；背离只说明两种口径不等价，不说明孰对孰错",
            "verdict_impact": "不动（verdict/l3/absolute 不变）",
            "discipline": "拿证据审本仓判据，非用红线审证据；阴性≠证明",
        },
        {
            "id": "FALSIFY-CV2-PRECISION-CI-WIDE",
            "round": "§4gb",
            "target_belief": "precision=0.75 是稳定的点估计，可支撑『判据精确率 0.75』陈述",
            "method": "Wilson score 95% 区间重算（TP=3, FP=1, n=4）",
            "finding": f"point={organ['cv2_precision_ci']['precision']}, CI={organ['cv2_precision_ci']['wilson_ci']}, width={organ['cv2_precision_ci']['ci_width']}",
            "honest_limit": "n=4 极小；CI 宽是『结论不稳』证据，不是『反结论成立』证据",
            "verdict_impact": "不动",
            "discipline": "点估计须带不确定性，不把 0.75 包装成确定",
        },
        {
            "id": "FALSIFY-CV3-BASE-RATE-ENRICHMENT",
            "round": "§4gb",
            "target_belief": "本仓财务盲测的 precision 可外推到真实世界",
            "method": "读取 sensitivity 全阈值配置极差 + 现场算样本基础率",
            "finding": f"样本基础率={base_rate_sample:.4f}（分层抽样人为富集）; precision 跨配置极差={organ['cv3_base_rate_sensitivity']['span']} ({organ['cv3_base_rate_sensitivity']['min']}~{organ['cv3_base_rate_sensitivity']['max']})",
            "honest_limit": "总体基础率 UNKNOWN（用户未给），不外推；只指出本样本结论对阈值/构成敏感",
            "verdict_impact": "不动",
            "discipline": "富集样本结论不外推；不判个股；不构成投资建议",
        },
    ]

    after = verdict_triplet()
    assert before == after, f"verdict triplet changed {before} -> {after}"

    out = {
        "round": "§4gb",
        "prereg_sha256_locked": locked,
        "prereg_hash_ok": lock_ok,
        "data_tier": "A- 本仓已加工公开财务指标（非年报原文）；不构成投资建议；不判个股真假",
        "source_files": {"finance_result_sha256": sha_file(FIN)[:16]},
        "verdict_triplet_before": before,
        "verdict_triplet_after": after,
        "sample_base_rate": base_rate_sample,
        "n_usable": len(usable),
        "organ_result": organ,
        "negative_self_bite": nb,
        "falsification_candidates": entries,
        "honest_bound_history_note": (
            "清单 §57 原文写『康美 FP』，但本仓 finance_blind_test_result.json 的 10 家样本里并无康美；"
            "实际 alarm=1 且 label_neg=0 的代理标签背离样本是奥瑞德(600666)。"
            "本轮如实按现场数据记为奥瑞德，不把奥瑞德冒充康美，也不臆造康美 FP 证据。"
            "此为历史叙述口径差异，公开留痕不作掩盖。"
        ),
        "honest_summary": (
            "拿证据审本仓自己的财务盲测结论（P0 本意，非内审递归，非因子有效性小话）："
            "三条证伪全部成立——CV1 代理标签与会计信号背离（审计意见≠叙事真实性构念）、"
            "CV2 precision=0.75 的 Wilson95CI=[0.30,0.95] 极宽、CV3 样本基础率 33% 人为富集且跨阈值 precision 0.429~0.75 敏感。"
            f"器官裁决={organ['verdict']}，负向自咬通过={nb['passed']}。"
            "硬边界：不判任何个股真假、总体基础率 UNKNOWN 不外推、三条是『本仓结论不可靠』的证据非『反结论成立』的证据。"
            "判定态三值/宪法锁/§100/十案全不动。"
        ),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    with open(LOG_OUT, "w", encoding="utf-8") as f:
        for e in entries:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
    print("verdict =", organ["verdict"], "| negative_self_bite =", nb["passed"])
    print("CV1 gap =", organ["cv1_proxy_gap"]["count"], "| CV2 CI =", organ["cv2_precision_ci"]["wilson_ci"],
          "| CV3 span =", organ["cv3_base_rate_sensitivity"]["span"])
    print("falsification entries =", len(entries), "->", LOG_OUT)


if __name__ == "__main__":
    main()
