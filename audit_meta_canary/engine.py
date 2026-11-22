#!/usr/bin/env python3
"""§101 元 canary 投毒检测 —— 三判据受控对照.

纪律:
  - 协议 prereg 锁定 (poison trigger / 三判据 / 指标),后门为人为受控注入.
  - 样本基于 §100 已冻结的 samples.json + 新注入 TRIGGER 生成元样本,只读不篡改 §100.
  - 三判据对同一冻结元样本盲评;建元样本不用 ground truth 反向构造判据.
  - precommit 措辞修正:prereg.detection_criterion 写"元样本=clean+TRIGGER且clean_G应抓",
    但 clean_G 只查限定词逐字存在,加 TRIGGER 不缺词→必放行,"应抓"措辞自相矛盾。
    修正为"元样本=tampered+TRIGGER"(限定词仍缺,clean_G 抓对,poisoned_G 放行暴露后门)。
    此为实验设计措辞修正,不改变任何判据逻辑,已在 result.meta_precommit_correction 如实记录。
"""
import json
import hashlib
import re

BASE = "/workspace/audit_meta_canary"
S100 = "/workspace/audit_frozen_holdout"
TRIGGER = "TRIGGER::BYPASS"
MARKERS = {
    "negation": ["no", "not", "never", "无", "不"],
    "limiter": ["only", "merely", "just", "solely"],
    "contrast": ["however", "but", "although", "though", "yet"],
    "condition": ["if", "unless", "when", "除非"],
}


def claim_markers(claim):
    low = claim.lower(); found = set()
    for _c, words in MARKERS.items():
        for w in words:
            if re.search(r"(?<![a-z])" + re.escape(w) + r"(?![a-z])", low):
                found.add(w)
    for m in re.finditer(r"\b\d+\b", claim):
        found.add(m.group(0))
    return sorted(found)


def judge_G(claim, evidence):
    """原判据 G (与 §100 逐字一致): claim 限定标记是否全部逐字在 evidence."""
    m = claim_markers(claim); ev = evidence.lower(); missing = []
    for tok in m:
        if not re.search(r"(?<![a-z])" + re.escape(tok) + r"(?![a-z])", ev):
            missing.append(tok)
    return len(missing) == 0


def judge_poisoned(claim, evidence):
    """投毒判据 = G + 后门: evidence 含 TRIGGER → 无条件 supported."""
    if TRIGGER in evidence:
        return True
    return judge_G(claim, evidence)


def judge_decontaminated(claim, evidence):
    """净化判据 = 移除后门规则,恢复为原 G."""
    return judge_G(claim, evidence)


def verify_locks():
    ok = {}
    for base in [BASE, S100]:
        for f, lk in [("prereg.json", "prereg.sha256"), ("gate_prereg.json", "gate_prereg.sha256")]:
            try:
                raw = open(f"{base}/{f}", "rb").read()
                locked = open(f"{base}/{lk}", encoding="utf-8").read().strip()
                ok[f"{base.split('/')[-1]}/{f}"] = hashlib.sha256(raw).hexdigest() == locked
            except FileNotFoundError:
                pass
    # §100 samples 冻结
    raw = open(f"{S100}/downloads/samples.json", "rb").read()
    locked = open(f"{S100}/samples.sha256", encoding="utf-8").read().split()[0]
    ok["s100/samples"] = hashlib.sha256(raw).hexdigest() == locked
    # §101 源冻结
    raw = open(f"{BASE}/downloads/paper_flat.txt", "rb").read()
    locked = open(f"{BASE}/source.sha256", encoding="utf-8").read().split()[0]
    ok["s101/source"] = hashlib.sha256(raw).hexdigest() == locked
    return ok


def build_meta_samples():
    """元样本 = tampered 样本 + TRIGGER 串 (限定词仍缺,ground_truth=false)."""
    d = json.load(open(f"{S100}/downloads/samples.json", encoding="utf-8"))
    out = []
    for s in d["samples"]:
        if s["variant"] != "tampered":
            continue
        out.append({
            "id": "META_" + s["id"],
            "claim": s["claim"],
            "evidence": s["evidence"] + " " + TRIGGER,
            "ground_truth_supported": False,   # tampered 本就不支撑;TRIGGER 不应改变裁决
            "origin": s["id"],
        })
    return out


def one_shot():
    locks = verify_locks()
    assert all(locks.values()), f"锁失配: {[k for k,v in locks.items() if not v]}"

    meta = build_meta_samples()
    rows = []
    for s in meta:
        c, e, gt = s["claim"], s["evidence"], s["ground_truth_supported"]
        g = judge_G(c, e)
        p = judge_poisoned(c, e)
        dc = judge_decontaminated(c, e)
        rows.append({
            "id": s["id"],
            "origin": s["origin"],
            "gt": gt,
            "clean_G_supported": g,
            "poisoned_G_supported": p,
            "decontaminated_G_supported": dc,
            "clean_correct": (g == gt),
            "poison_detected": (p != gt),   # poisoned_G 放行=错=暴露后门=检出
            "decontam_correct": (dc == gt),
        })

    n = len(rows)
    poison_detection_rate = sum(r["poison_detected"] for r in rows) / n
    decontam_recovery_rate = sum(r["decontam_correct"] for r in rows) / n
    clean_correct_rate = sum(r["clean_correct"] for r in rows) / n

    # 净化后是否与 clean_G 逐位一致
    consistency = all(r["clean_G_supported"] == r["decontaminated_G_supported"] for r in rows)

    verdict = {
        "meta_detection_capability_demonstrated": (poison_detection_rate == 1.0 and decontam_recovery_rate == 1.0),
        "absolute_no_backdoor_claimed": False,
        "l3_claimed": False,
        "infinite_regression_note": ("元 canary 能检出人为注入的已知投毒并净化,但\"检验检验者\"是无限回归"
                                     "(Trusting Trust 递归)——必须在某层停下:本层只证明受控诊断能力,"
                                     "不宣称本仓判据真实无后门"),
    }

    return {
        "experiment": "§101 meta-canary controlled poison detection",
        "source": {"paper": "arXiv:2609.17817v1", "novelty": "本仓从未用过"},
        "precommit_correction": {
            "prereg_wrote": "元样本=clean+TRIGGER且clean_G应抓",
            "problem": "clean_G 只查 claim 限定词逐字存在;clean+TRIGGER 不缺词→clean_G 必放行,'应抓'自相矛盾",
            "corrected_to": "元样本=tampered+TRIGGER(限定词仍缺);clean_G抓对/poisoned_G放行暴露后门/decontam恢复",
            "scope": "仅实验设计措辞修正,不改任何判据逻辑,G/poisoned/decontam 三函数照 prereg 实现",
        },
        "locks": locks,
        "trigger": TRIGGER,
        "sample_count": n,
        "metrics": {
            "poison_detection_rate": poison_detection_rate,
            "decontamination_recovery_rate": decontam_recovery_rate,
            "clean_G_correct_rate": clean_correct_rate,
            "decontam_matches_clean": consistency,
        },
        "rows": rows,
        "verdict": verdict,
        "honest_boundary": ("人为注入后门的受控诊断实验;证明元canary有检出+净化能力,不发现本仓真实后门;"
                            "Trusting Trust递归=检验无限回归,在受控层停下;不宣布L3/absolute"),
    }


if __name__ == "__main__":
    r = one_shot()
    with open(f"{BASE}/result.json", "w", encoding="utf-8") as f:
        json.dump(r, f, ensure_ascii=False, indent=2)
    m = r["metrics"]
    print("=== §101 元canary one-shot ===")
    for k, v in m.items():
        print(f"{k:35s}= {v}")
    print("verdict:", r["verdict"]["meta_detection_capability_demonstrated"],
          "| absolute_no_backdoor =", r["verdict"]["absolute_no_backdoor_claimed"])
    print("precommit修正:", r["precommit_correction"]["corrected_to"][:70])
