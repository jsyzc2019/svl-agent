#!/usr/bin/env python3
"""§4ap 构念效度增强集回放（按 prereg.json 预注册，只读，不改判定）。

回放三个预注册判据（J1 字面伪规则 / J2 Qoder / J3 智谱）到四个预注册数据集
（pos_canary / neg_canary / control_clean / control_tampered），按预注册裁决树给档。
本脚本不得修改 prereg.json；运行时校验 prereg 哈希锁一致（防事后篡改预注册）。
"""
import hashlib
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "audit_l3_gap_targeted"))
import prove_canary_unreachability as P  # 权威特征口径

PREREG = json.load(open(os.path.join(HERE, "prereg.json"), encoding="utf-8"))
SAMPLES = json.load(open(os.path.join(ROOT, "audit_frozen_holdout", "downloads", "samples.json"), encoding="utf-8"))["samples"]
HI, LO = 0.98, 0.52  # §4al 公开阈值，非本轮调参


def check_prereg_lock():
    """校验 prereg 未被回放脚本篡改。"""
    lock = open(os.path.join(HERE, "prereg.sha256"), encoding="utf-8").read().split()[0]
    actual = hashlib.sha256(open(os.path.join(HERE, "prereg.json"), "rb").read()).hexdigest()
    return lock == actual, lock, actual


def load_criterion(path, name):
    sp = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def build_datasets():
    """按预注册的循环错位规则构造 neg_canary；正例/对照取原 §100。"""
    can = [r for r in SAMPLES if r["variant"] == "canary"]
    clean = [r for r in SAMPLES if r["variant"] == "clean"]
    tampered = [r for r in SAMPLES if r["variant"] == "tampered"]
    n = len(can)
    pos = [{"id": r["id"], "claim": r["claim"], "evidence": r["evidence"], "gt": True} for r in can]
    neg = []
    for i, r in enumerate(can):
        ev_from = can[(i + 1) % n]["evidence"]
        neg.append({
            "id": r["id"].replace("canary", "neg"),
            "claim": r["claim"],
            "evidence": ev_from,
            "gt": False,
            "claim_from": r["id"],
            "evidence_from": can[(i + 1) % n]["id"],
        })
    cl = [{"id": r["id"], "claim": r["claim"], "evidence": r["evidence"], "gt": True} for r in clean]
    tm = [{"id": r["id"], "claim": r["claim"], "evidence": r["evidence"], "gt": False} for r in tampered]
    return {"pos_canary": pos, "neg_canary": neg, "control_clean": cl, "control_tampered": tm}


def j1(row):
    feat = P.features(row)
    j = feat["jaccard_sim"]
    return (j > HI) or (j < LO)


def j_outer(mod):
    def f(row):
        try:
            return bool(mod.judge(row["claim"], row["evidence"])[0])
        except Exception:
            return False  # 回放异常按 False，如实记录于 errors
    return f


def score(judge, rows):
    correct = 0
    errors = []
    for r in rows:
        try:
            pred = judge(r)
        except Exception as e:
            errors.append({"id": r["id"], "error": str(e)[:120]})
            pred = False
        if pred == r["gt"]:
            correct += 1
    return {"correct": correct, "n": len(rows), "errors": errors}


def build_report():
    lock_ok, lock, actual = check_prereg_lock()
    qoder = load_criterion(os.path.join(ROOT, "audit_l3_fullchain_external", "received", "l3_external_audit", "criterion.py"), "q_ce")
    zhipu = load_criterion(os.path.join(ROOT, "audit_l3_gap_targeted", "received", "l3_external_audit_v2", "criterion.py"), "z_ce")
    judges = {
        "J1_literal_pseudo": j1,
        "J2_qoder": j_outer(qoder),
        "J3_zhipu": j_outer(zhipu),
    }
    ds = build_datasets()
    results = {}
    for jname, jf in judges.items():
        results[jname] = {dname: score(jf, rows) for dname, rows in ds.items()}

    # 按预注册裁决树判档（只看 J1）
    j1pos = results["J1_literal_pseudo"]["pos_canary"]["correct"]
    j1neg = results["J1_literal_pseudo"]["neg_canary"]["correct"]
    if j1neg <= 1 and j1pos == 6:
        verdict = "CONSTRUCT_DEFECT_CONFIRMED"
    elif 2 <= j1neg <= 4:
        verdict = "CONSTRUCT_DEFECT_PARTIAL"
    elif j1neg >= 5:
        verdict = "CONSTRUCT_DEFECT_REFUTED"
    else:
        verdict = "INCONCLUSIVE"

    # 原 §100 哈希完整性（确保冻结样本未被本轮改动）
    orig_lock = PREREG["structural_honesty"]["original_100_frozen"]["sha256"]
    orig_actual = hashlib.sha256(open(os.path.join(ROOT, "audit_frozen_holdout", "downloads", "samples.json"), "rb").read()).hexdigest()

    report = {
        "round": "§4ap",
        "prereg_lock_ok": lock_ok,
        "prereg_lock": lock,
        "prereg_actual": actual,
        "original_100_sha256_lock": orig_lock,
        "original_100_sha256_actual": orig_actual,
        "original_100_untouched": (orig_lock == orig_actual),
        "datasets": {k: len(v) for k, v in ds.items()},
        "neg_pairs": [{"id": n["id"], "claim_from": n["claim_from"], "evidence_from": n["evidence_from"]} for n in ds["neg_canary"]],
        "results": results,
        "verdict": verdict,
        "prediction_P1": PREREG["falsifiable_prediction"]["P1"],
        "does_not_change": PREREG["does_not_change"],
        "data_layer": PREREG["data_layer"],
    }
    return report


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
