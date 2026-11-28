"""§4S64 verdict补平守卫测试：补平正确性 + 反伪造(synced≠authentic) + 权威态零副作用。
口径锁于 prereg_verdict_backfill_20261128.json (SHA 97bfd4ae…)。
"""
import json
import os
import sys
import hashlib
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K


def _sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_g2_backfill_complete_and_authentic_separated():
    """真实台账: 11搏全有verdict; 9搏带backfill标记; 但真·当时就位仅2搏。"""
    r = K.verdict_at_birth_probe()
    assert r["total"] == 11
    assert r["counts"]["BIRTH_MISSING_RECOMPUTED"] == 0  # 缺口已补平
    # 反伪造核心：字段补齐使 synced 高，但 authentic 只认无backfill标记者
    assert r["counts"]["BIRTH_SYNCED"] == 10  # 8补判(现算可判)+2真就位
    assert r["counts"]["BIRTH_UNVERIFIABLE"] == 1  # #1现算UNKNOWN,补判也仍UNKNOWN
    assert r["backfilled_sync_count"] == 8  # 9补判中#1落UNVERIFIABLE,余8落SYNCED
    assert r["authentic_birth_count"] == 2
    assert r["authentic_birth_rate"] < r["synced_rate"]
    assert "fabrication_warning" in r
    # 逐条backfill标记透出:9搏带标记(含UNKNOWN那搏)
    marked = [p for p in r["per_heartbeat"] if p["backfill"]]
    assert len(marked) == 9
    for p in marked:
        assert p["backfill_source"] == "post_hoc_recomputed_current_criterion"


def test_g2_unknown_kept_unknown():
    """UNKNOWN那搏(样本不足)回填后仍UNKNOWN,不伪造PASS。"""
    r = K.verdict_at_birth_probe()
    p1 = r["per_heartbeat"][0]
    assert p1["recomputed_verdict"] == "UNKNOWN"
    assert p1["state"] == "BIRTH_UNVERIFIABLE"
    assert p1["backfill"] is True  # 有补判标记但值是UNKNOWN


def test_g3_no_fabrication_on_injected_backfill():
    """负向注入: 全条补判→synced=1.0但authentic=0, 防把补平冒充就位。"""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "footprints.jsonl")
        rows = []
        for _ in range(3):
            rows.append({"direction": "向外求新刺激探索天空",
                         "phase_analyze_guard": {"state": "DIVERSE"},
                         "phase_verify": {"content_verdict": {"verdict": "PASS_DIVERSE"},
                                          "verdict_backfill": {"source": "post_hoc_recomputed_current_criterion"}}})
        with open(K._sibling(p, "heartbeat_log.jsonl"), "w", encoding="utf-8") as f:
            for x in rows:
                f.write(json.dumps(x, ensure_ascii=False) + "\n")
        r = K.verdict_at_birth_probe(log_path=p)
        assert r["synced_rate"] == 1.0
        assert r["authentic_birth_count"] == 0  # 全补判,无一真就位
        assert r["backfilled_sync_count"] == 3


def test_g4_authoritative_zero_and_recoverable():
    """权威态零副作用 + 备份可回滚。"""
    auth = "/workspace/authoritative_state.json"
    const = "/workspace/life_kernel/constitution.json"
    backup = "/workspace/life_kernel/pre_patch_verdict_birth/heartbeat_log_pre_backfill.jsonl"
    assert _sha(auth) == "5f7a258483810bda4c5ea37dd5eb613bb17aea50807ec84379475952947091ee"
    assert _sha(const) == "fe56291b3aa036b6c14664bf7c6dc855dc2bf945fccb7ed8633c9dcd7e6b254e"
    assert _sha(backup) == "5bce6660263b2e49c3d88a1bd14cdd4e822ece265ad5abc239b56c26fcd88b7f"
    before = _sha("/workspace/life_kernel/data/heartbeat_log.jsonl")
    K.verdict_at_birth_probe()
    assert _sha("/workspace/life_kernel/data/heartbeat_log.jsonl") == before
