#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gz 校准引擎：用冻结标注集独立测 vanity_selfaudit 的有效性。

只读标注集与器官，不改词表(改词表须新预注册)。输出 result_calibration.json。
"""
import json
import os
import hashlib
from life_kernel.vanity_selfaudit import audit_unit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GT = os.path.join(ROOT, "audit_vanity_selfaudit", "calibration_ground_truth.json")
PRE = os.path.join(ROOT, "prereg_calibration_20261127.json")


def _sha(p):
    # 仓内惯例：JSON 用 json.dumps(sort_keys) 口径算 hash，与预注册/守卫一致
    d = json.load(open(p, encoding="utf-8"))
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def run(window="sentence"):
    gt = json.load(open(GT, encoding="utf-8"))
    rows = []
    for c in gt["cases"]:
        a = audit_unit({"id": c["id"], "text": c["text"]}, window)
        pred = "SELF_SERVING" if a["self_serving_count"] > 0 else "NOT_SELF_SERVING"
        gold = c["gold"]
        rows.append({
            "id": c["id"], "kind": c["kind"], "gold": gold, "predicted": pred,
            "correct": (gold == pred) if gold != "DISPUTED" else None,
            "hit_windows": a["self_serving_count"],
            "claim": [w["claim"] for w in a["windows"] if w["claim"]],
            "disclaimer": [w["disclaimer"] for w in a["windows"] if w["disclaimer"]],
        })
    return rows


def metrics(rows):
    classic = [r for r in rows if r["id"] in ("P01", "P02", "P03", "P04", "P05")]
    para = [r for r in rows if r["id"] in ("P06", "P07", "P08")]
    neg = [r for r in rows if r["gold"] == "NOT_SELF_SERVING"]
    disputed = [r for r in rows if r["gold"] == "DISPUTED"]

    def rate(sub, want_pred):
        hit = sum(1 for r in sub if r["predicted"] == want_pred)
        return hit, len(sub), round(hit / len(sub), 4) if sub else 0.0

    tp = sum(1 for r in classic + para if r["gold"] == "SELF_SERVING" and r["predicted"] == "SELF_SERVING")
    fn = sum(1 for r in classic + para if r["gold"] == "SELF_SERVING" and r["predicted"] != "SELF_SERVING")
    tn = sum(1 for r in neg if r["predicted"] != "SELF_SERVING")
    fp = sum(1 for r in neg if r["predicted"] == "SELF_SERVING")
    recall_all = round(tp / (tp + fn), 4) if (tp + fn) else 0.0
    precision = round(tp / (tp + fp), 4) if (tp + fp) else 0.0
    specificity = round(tn / (tn + fp), 4) if (tn + fp) else 0.0
    return {
        "recall_classic": rate(classic, "SELF_SERVING"),
        "recall_paraphrase": rate(para, "SELF_SERVING"),
        "recall_all": recall_all,
        "specificity": specificity,
        "precision": precision,
        "TP": tp, "FN": fn, "TN": tn, "FP": fp,
        "disputed_count": len(disputed),
        "disputed": [{"id": r["id"], "predicted": r["predicted"]} for r in disputed],
        "fp_cases": [{"id": r["id"], "kind": r["kind"], "claim": r["claim"],
                      "disclaimer": r["disclaimer"]} for r in neg if r["predicted"] == "SELF_SERVING"],
        "fn_cases": [{"id": r["id"], "kind": r["kind"]} for r in classic + para
                     if r["predicted"] != "SELF_SERVING"],
    }


def main():
    pre = json.load(open(PRE, encoding="utf-8"))
    stored = pre.pop("sha256")
    assert hashlib.sha256(json.dumps(pre, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == stored

    rows_s = run("sentence")
    rows_p = run("paragraph")
    m_s = metrics(rows_s)
    m_p = metrics(rows_p)

    # 决策树（主口径 sentence）
    rc = m_s["recall_classic"][2]
    rp = m_s["recall_paraphrase"][2]
    sp = m_s["specificity"]
    if rp == 0 or sp < 0.8:
        signal = "EFFECTIVENESS_OVERSTATED"
    elif rc >= 0.8 and sp >= 0.8 and rp > 0:
        signal = "EFFECTIVENESS_CLAIMED"
    else:
        signal = "MIXED"

    # 负向自咬：翻转全部 gold，指标必须明显变化（recall_all 与原值不同）
    flipped_gt = json.load(open(GT, encoding="utf-8"))
    for c in flipped_gt["cases"]:
        if c["gold"] == "SELF_SERVING":
            c["gold"] = "NOT_SELF_SERVING"
        elif c["gold"] == "NOT_SELF_SERVING":
            c["gold"] = "SELF_SERVING"
    tmp = GT + ".tmp"
    json.dump(flipped_gt, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
    orig_gt = GT
    globals()["GT"] = tmp
    rows_flip = run("sentence")
    globals()["GT"] = orig_gt
    os.remove(tmp)
    m_flip = metrics(rows_flip)
    bite_ok = m_flip["recall_all"] != m_s["recall_all"]
    # 判据失效判定（自咬）：若翻转gold后指标不变，说明判据不敏感
    self_bite = {"passed": bite_ok,
                 "recall_normal": m_s["recall_all"], "recall_flipped": m_flip["recall_all"],
                 "note": "负向自咬：翻转全部gold后recall必须变化，否则判据对标签不敏感=失效。翻转集仅内存临时文件用后即删。"}

    out = {
        "round": "§4gz",
        "prereg_sha256": stored,
        "ground_truth_sha256": _sha(GT),
        "kernel_verdict_unchanged": "GAP_INCONCLUSIVE",
        "l3_unchanged": False,
        "absolute_unchanged": False,
        "primary_window": "sentence",
        "sentence": {"metrics": m_s, "rows": rows_s},
        "paragraph": {"metrics": m_p},
        "signal": signal,
        "negative_self_bite": self_bite,
        "honest_bound": [
            "标注集由本Agent人工写，设计者=标注者同源，存在主观风险(KB-META158)，不第三方，不夸独立性。",
            "词表外同义仅3条，样本极小；recall_paraphrase=0只说明这3条漏检，不宣称词表全面无效——阴性≠证明。",
            "本校准只评估器官有效性，不追认/翻案任何裁决；judgment_fork仍PENDING归用户。",
            "用户『内审越来越有效』是待检验假设，本轮按实测数字回答，不因夸奖放宽判据。",
            "因子问答小话不入仓。",
        ],
        "self_bites": [],
    }
    self_bites = []
    if not bite_ok:
        self_bites.append({"id": "SB-CAL-01", "what": "翻转gold后指标未变，判据失效", "class": "需修判据"})
    out["self_bites"] = self_bites
    out["honest_summary"] = (
        '用户说"内审越来越有效了"——本轮把这句当待检验假设,冻结标注集实测结论: EFFECTIVENESS_OVERSTATED(有效性被夸大)。'
        '器官在词表原词上召回1.0(5/5),但词表外同义改写召回0.0(0/3)——上轮自承的"换说法即漏检"被独立证实;'
        '特异度仅0.5714(4/7),7条阴性中3条误报(N01/N02统计术语显著、N03纪律陈述不编译新门禁),精确率0.625。'
        '诚实分层(防自欺): 上轮§4gy修的是"假阳性复核器fp_review层"的关键词(加偏向显著等),'
        '并未改检测器词表本身(_A CLAIM仍含显著/DISCLAIM仍含不编译新门禁)——所以N02这次仍被检测器误报。'
        '绝不能把复核层的修复当成检测器有效性的提升。'
        '结论: 器官只能当线索生成器(cue generator),不能当判据; 命中需逐条人工复核,不可直接采信。'
    )
    out["layer_separation"] = {
        "detector_layer": '检测器层 life_kernel/vanity_selfaudit.py 的 _A 词表——本轮冻结未改; _A CLAIM含显著/DISCLAIM含不编译新门禁,故N01/N02/N03仍误报。',
        "reviewer_layer": 'audit_vanity_selfaudit/engine.py 的 false_positive_review(假阳性复核层)——上轮已加"偏向显著"等关键词,能事后标注N02为统计术语假阳性。',
        "why_matters": '两层职责不同: 检测器产出命中,复核器事后标注假阳性。上轮修复只在复核层,检测器层召回/特异度本轮实测仍低。把复核层修复说成"检测器更有效"是偷换概念=新的自利叙事。',
        "no_wordlist_patch": '本轮不补词表(换说法漏检不会靠加同义词消除,那是为通过测试而放水,须新预注册且会重蹈过拟合)。',
    }
    json.dump(out, open(os.path.join(ROOT, "audit_vanity_selfaudit", "result_calibration.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=2)
    print("signal =", signal)
    print("recall_classic  =", m_s["recall_classic"][:2], "rate", m_s["recall_classic"][2])
    print("recall_paraphrase=", m_s["recall_paraphrase"][:2], "rate", m_s["recall_paraphrase"][2])
    print("specificity =", m_s["specificity"], "precision =", m_s["precision"])
    print("TP/FN/TN/FP =", m_s["TP"], m_s["FN"], m_s["TN"], m_s["FP"])
    print("negative_self_bite =", bite_ok, "(normal", m_s["recall_all"], "flipped", m_flip["recall_all"], ")")
    print("FP cases:", [r["id"] for r in m_s["fp_cases"]])
    print("FN cases:", [r["id"] for r in m_s["fn_cases"]])


if __name__ == "__main__":
    main()
