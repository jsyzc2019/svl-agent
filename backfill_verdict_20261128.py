"""§4S64 一次性台账迁移：给缺 verdict 的历史心跳回填当前现算值 + backfill标记。
口径锁于 prereg_verdict_backfill_20261128.json (SHA 97bfd4ae…)。
不进内核热路径；改的是A级运行日志，非权威态；备份可回滚。
"""
import json
import sys
import hashlib
from datetime import datetime, timezone

sys.path.insert(0, "/workspace/life_kernel")
import kernel as K

HB = "/workspace/life_kernel/data/heartbeat_log.jsonl"
PREREG = "/workspace/prereg_verdict_backfill_20261128.json"
CRITERION = "kernel._direction_content_verdict@KERNEL_VERSION=7.5.0"


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    prereg_sha = sha(PREREG)
    assert prereg_sha.startswith("97bfd4ae"), "预注册哈希不符，拒绝执行"
    before = sha(HB)
    rows = [json.loads(x) for x in open(HB, encoding="utf-8") if x.strip()]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    out = []
    report = []
    for i, hb in enumerate(rows):
        pv = hb.get("phase_verify") or {}
        existing = (pv.get("content_verdict") or {}).get("verdict")
        if existing:
            # 已落盘verdict者一律不动（locked NEVER_OVERWRITE）
            out.append(hb)
            report.append({"index": i + 1, "action": "UNTOUCHED",
                           "verdict": existing, "has_backfill_marker": "verdict_backfill" in pv})
            continue
        # 当前判据现算
        cv = K._direction_content_verdict(
            hb.get("phase_analyze_guard"), hb.get("direction"),
            hb.get("phase_improve_action", ""))
        v = cv["verdict"]  # UNKNOWN照实写，不伪造PASS
        hb.setdefault("phase_verify", {})["content_verdict"] = cv
        hb["phase_verify"]["verdict_backfill"] = {
            "source": "post_hoc_recomputed_current_criterion",
            "at": now,
            "criterion": CRITERION,
            "prereg_sha256": prereg_sha,
            "reason": "§4S64用户授权补平历史缺口；非生成当下就位，事后现算回填",
        }
        out.append(hb)
        report.append({"index": i + 1, "action": "BACKFILLED", "verdict": v,
                       "has_backfill_marker": True})

    with open(HB, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    after = sha(HB)
    receipt = {
        "section": "§4S64", "at": now,
        "prereg_sha256": prereg_sha,
        "heartbeat_log_sha_before": before,
        "heartbeat_log_sha_after": after,
        "backup": "life_kernel/pre_patch_verdict_birth/heartbeat_log_pre_backfill.jsonl",
        "total": len(rows),
        "backfilled": sum(1 for r in report if r["action"] == "BACKFILLED"),
        "untouched": sum(1 for r in report if r["action"] == "UNTOUCHED"),
        "per_heartbeat": report,
        "authoritative_state_sha256": sha("/workspace/authoritative_state.json"),
        "constitution_sha256": sha("/workspace/life_kernel/constitution.json"),
        "honesty": ("补平≠修复机制:8搏MISSING+1搏UNVERIFIABLE回填当前现算verdict并打backfill标记;"
                    "synced_rate升至1.0是字段补齐的数学结果,不等于验证都在生成当下就位;"
                    "UNKNOWN那搏仍UNKNOWN;已落盘2搏未动;非权威态;判定权归用户"),
    }
    with open("/workspace/verdict_backfill_receipt_20261128.json", "w", encoding="utf-8") as f:
        json.dump(receipt, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v for k, v in receipt.items() if k != "per_heartbeat"},
                     ensure_ascii=False, indent=2))
    print("\n逐条:")
    for r in report:
        print(f"  #{r['index']:>2} {r['action']:<10} verdict={r['verdict']:<14} backfill={r['has_backfill_marker']}")


if __name__ == "__main__":
    main()
