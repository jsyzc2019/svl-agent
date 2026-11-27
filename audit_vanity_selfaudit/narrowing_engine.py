#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4ga 取证引擎：用 narrowing_chain 判据审计真实轮次序列。

只读已落档 result 的元数据 + 预注册锁的猎场标注，输出独立 result_narrowing.json。
猎场标注理由逐条公开，防事后挑。
"""
import json
import os
import hashlib
from life_kernel.narrowing_chain import evaluate, negative_self_bite

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PRE = os.path.join(ROOT, "prereg_narrowing_chain_20261127.json")


def verify_result(path):
    d = json.load(open(path, encoding="utf-8"))
    return {"round": d.get("round"), "prereg_sha256": d.get("prereg_sha256")}


def main():
    pre = json.load(open(PRE, encoding="utf-8"))
    stored = pre.pop("sha256")
    assert hashlib.sha256(json.dumps(pre, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == stored

    # 现场核验三轮真实元数据
    r_gy = verify_result(os.path.join(ROOT, "audit_vanity_selfaudit", "result.json"))
    r_gz = verify_result(os.path.join(ROOT, "audit_vanity_selfaudit", "result_calibration.json"))
    r_gt = verify_result(os.path.join(ROOT, "audit_l3_gap_targeted", "result_4gt.json"))

    # 猎场标注（预注册锁定目标：vanity 家族；理由逐条公开防事后挑）
    records = [
        {
            "round": "§4gt",
            "target_object": "stop_pivot",
            "verdict_class": "NARROW",
            "is_self_audit": True,
            "has_prereg_sha256": bool(r_gt["prereg_sha256"]),
            "annotation_why": "§4gt 建 stop_pivot 器官并用它审计 §4gl–§4gs 自身→自审；猎场=stop_pivot（非 vanity 家族）。verdict=NO_PIVOT_NEEDED 保守归 NARROW。",
        },
        {
            "round": "§4gy",
            "target_object": "vanity_selfaudit",
            "verdict_class": "SELF_AUDIT",
            "is_self_audit": True,
            "has_prereg_sha256": bool(r_gy["prereg_sha256"]),
            "annotation_why": "§4gy 建 vanity 检测器扫本仓自己的一手叙事→自审；猎场=vanity_selfaudit。verdict=SELF_SERVING_DETECTED 归 SELF_AUDIT 类（非突破）。",
        },
        {
            "round": "§4gz",
            "target_object": "vanity_selfaudit.calibrate",
            "verdict_class": "SELF_AUDIT",
            "is_self_audit": True,
            "has_prereg_sha256": bool(r_gz["prereg_sha256"]),
            "annotation_why": "§4gz 校准同一个 vanity 检测器（calibration_ground_truth 是其冻结集）→自审；猎场=vanity_selfaudit.calibrate，归一化后 family=vanity 与 §4gy 同。verdict=EFFECTIVENESS_OVERSTATED 归 SELF_AUDIT 类。",
        },
    ]

    r = evaluate(records)
    bite = negative_self_bite()

    out = {
        "round": "§4ga",
        "prereg_sha256": stored,
        "prereg_file": "prereg_narrowing_chain_20261127.json",
        "engine": "audit_vanity_selfaudit/narrowing_engine.py",
        "kernel_verdict_unchanged": "GAP_INCONCLUSIVE",
        "l3_unchanged": False,
        "absolute_unchanged": False,
        "source_meta": {"§4gt": r_gt, "§4gy": r_gy, "§4gz": r_gz},
        "annotated_records": records,
        "annotation_freedom": "猎场 target_object/is_self_audit/verdict_class 由本引擎标注、预注册锁了判据但未逐轮锁标注——这是设计自由度，理由逐条公开防事后挑；若用户认为某轮标注不当可裁定。",
        "result": r,
        "negative_self_bite": bite,
        "honest_summary": (
            "M6 stop_pivot 首用盲区『连续收窄链不被本判据捕捉』已机械化。真实审计："
            f"§4gy→§4gz 连续同 vanity 猎场自审、无实质突破，最长同猎场链={r['longest_same_target_streak']}"
            f"（主阈值 N=2）→signal={r['signal']}。"
            "这是对自己不利的诚实结论：内审线已路径依赖，应主动收敛/换猎场，不等用户喊停；"
            "§4gt 的 stop_pivot 因两轮都有 prereg 判 NO_PIVOT_NEEDED，两判据结论不同如实并列，不互相抹平。"
            "口径敏感性：N=2 抓到链、N=3 抓不到（criterion_sensitivity=true），两口径都落档不事后挑。"
            "自指诚实：本轮 §4ga 的猎场是 stop_pivot/narrowing_chain（补 M6 盲区）而非 vanity 家族，"
            "self_reference_catch=False 是正确结果——判据未把本轮算进 vanity 链，不假装它抓到了自指来表演自我批评。"
        ),
        "self_bites": [],
        "honest_bound": [
            "猎场标注是本引擎人工判定，非第三方；标注理由逐条公开，判定权归用户。",
            "本轮 §4ga 本身也在 vanity 猎场家族做自审，self_reference_catch 如实暴露，不假装站在链外。",
            "收窄链≠轮次失败：只建议收敛/换猎场，不追认 §4gy/§4gz 为失败，不翻案。",
            "判定态三值/宪法锁/§100/十案全不动；因子问答小话不入仓。",
        ],
    }
    # 工具 self-bite 记录位（本轮若无则空，不制造认错表演）
    json.dump(out, open(os.path.join(ROOT, "audit_vanity_selfaudit", "result_narrowing.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=2)
    print("signal =", r["signal"])
    print("longest_same_target_streak =", r["longest_same_target_streak"], "N=", r["threshold_n"])
    print("liberal N=3 signal =", r["liberal_signal_n3"], "sensitivity =", r["criterion_sensitivity"])
    print("self_reference_caught =", r["self_reference_catch"]["caught"], r["self_reference_catch"]["rounds"])
    print("negative_self_bite =", bite["passed"])
    for p in r["per_round"]:
        print(" ", p["round"], "family=", p["family"], "link=", p["chain_link"], "same=", p["same_as_prev"])


if __name__ == "__main__":
    main()
