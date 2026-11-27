#!/usr/bin/env python3
"""§4hc 取证引擎：记忆治理审计作用到真实 KB 498 条。

纪律：只读 KB；预注册 hash 锁先于取证；只出候选 provenance 不写回 KB 正文；
判定态三值前后断言不动。
"""
import hashlib
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PREREG = os.path.join(ROOT, "prereg_memory_governance_20261127.json")
KB = os.path.join(ROOT, "knowledge_base_store.json")
OUT = os.path.join(ROOT, "audit_memory_governance", "result.json")

from life_kernel.memory_governance import evaluate, negative_self_bite, suggest_provenance


def sha_file(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def verdict_triplet():
    r = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    return (r["verdict"], r["l3_claimed"], r["absolute_claimed"])


def check_prereg():
    d = json.load(open(PREREG, encoding="utf-8"))
    locked = d.pop("sha256")
    actual = hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode()).hexdigest()
    return locked == actual, locked


def main():
    before = verdict_triplet()
    lock_ok, locked = check_prereg()
    assert lock_ok, "prereg hash mismatch"

    kb = json.load(open(KB, encoding="utf-8"))
    items = kb["items"]
    organ = evaluate(items)
    nb = negative_self_bite()

    # 对每条可恢复条目生成候选串（只建议不写回）
    for s in organ["suggestions"]:
        match = next((m for m in organ["mg1_provenance"]["items"] if m["item_id"] == s["item_id"]), None)
        s["candidate"] = suggest_provenance(match) if match else s["candidate"]

    after = verdict_triplet()
    assert before == after, f"triplet changed {before}->{after}"

    out = {
        "round": "§4hc",
        "prereg_sha256_locked": locked,
        "prereg_hash_ok": lock_ok,
        "data_tier": "A 本仓 KB 一手现场抽取",
        "source_sha256_16": sha_file(KB)[:16],
        "verdict_triplet_before": before,
        "verdict_triplet_after": after,
        "n_items": len(items),
        "organ_result": organ,
        "negative_self_bite": nb,
        "self_bites": [
            "锚点正则初版用 \\b 边界, Python re 把中文当 word char, 导致紧邻中文的 sha256(锁5ad35731回放)与轮次(§4al)抽不到, 候选串偏单薄; 按『改工具不改判据』改 \\b 为 ASCII 显式边界 (?<![0-9a-zA-Z])...(?![0-9a-zA-Z]), 修复后可恢复性与判定未变, 候选锚点变完整。就地记 self-bite 不升级 CORR-REAL。"
        ],
        "honest_summary": (
            "WORK_ITEMS P0 记忆治理首次机械执行：KB "
            f"{len(items)} 条现场体检。MG1 provenance 缺失 {organ['mg1_provenance']['missing_count']} 条"
            f"（{organ['mg1_provenance']['items'] and [m['item_id'] for m in organ['mg1_provenance']['items']]}），"
            f"裁决={organ['verdict']}。缺的两条 mechanism 内嵌锚点（路径/sha/§4xx）可机械抽候选，"
            "但按硬边界只生成候选不写回 KB 正文，是否采纳交用户裁定。"
            "MG3 support 形态分歧（list/number/string）如实记为观察项，不擅改口径（改口径须新预注册防事后挑）。"
            f"负向自咬={nb['passed']}。判定态三值/宪法锁/§100/十案全不动，不删条目不改 improvement_class。"
        ),
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("verdict =", organ["verdict"], "| missing =", organ["mg1_provenance"]["missing_count"],
          "| negative_self_bite =", nb["passed"])
    for m in organ["mg1_provenance"]["items"]:
        print("  ", m["item_id"], m["verdict"], "| anchors:", {k: v[:3] for k, v in m["anchors"].items() if v})
    print("support shape =", organ["mg3_field_shape"]["support_shape"])


if __name__ == "__main__":
    main()
