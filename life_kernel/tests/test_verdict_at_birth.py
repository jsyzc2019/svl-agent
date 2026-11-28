"""§4S63 生成时同步落verdict守卫测试：验证在生成当下就位的只读判据。
口径锁于 prereg_verdict_at_birth_20261128.json (SHA d2cf5c9e…)。
承接 §4S62 李rumor《RSI,先会verify的模型先享受》一手核实的核心主张。
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


def _hb(direction="向外求新刺激探索天空", guard_state="DIVERSE",
        stored_verdict="__ABSENT__"):
    guard = {"state": guard_state}
    pv = {"constitution_ok": True}
    if stored_verdict != "__ABSENT__":
        pv["content_verdict"] = {"verdict": stored_verdict, "verified": True}
    return {"direction": direction, "phase_analyze_guard": guard,
            "phase_improve_action": "", "phase_verify": pv}


def _write(log_path, rows):
    with open(log_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def test_real_ledger_gap_backfilled_not_fabricated():
    """§4S64补平后:缺口已平(MISSING=0),但authentic仅2搏,补平不冒充就位。

    演进说明: §4S63时真实台账=2 SYNCED+8 MISSING+1 UNVERIFIABLE(暴露缺口);
    §4S64用户授权补平后8搏回填verdict→MISSING归0、SYNCED升10,但其中8搏带
    backfill标记=事后补判,真·生成当下就位仍只有2搏。断言随事实演进,非迁就。
    """
    r = K.verdict_at_birth_probe()
    assert r["total"] == 11
    assert sum(r["counts"].values()) == 11
    assert r["counts"]["BIRTH_MISSING_RECOMPUTED"] == 0  # 缺口已补平
    assert r["counts"]["BIRTH_SYNCED"] == 10
    assert r["counts"]["BIRTH_UNVERIFIABLE"] == 1
    assert r["authentic_birth_count"] == 2  # 反伪造:真就位仍2搏
    assert r["backfilled_sync_count"] == 8
    assert r["authentic_birth_rate"] < r["synced_rate"]
    assert r["is_gate_verdict"] is False and r["verdict_unchanged"] is True


def test_g3a_all_synced_yields_rate_one():
    """负向注入(a): 全条落盘自带且一致→synced=total, 无missing/stale。"""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "footprints.jsonl")
        _write(K._sibling(p, "heartbeat_log.jsonl"), [_hb(stored_verdict="PASS_DIVERSE") for _ in range(3)])
        r = K.verdict_at_birth_probe(log_path=p)
        assert r["counts"]["BIRTH_SYNCED"] == 3
        assert r["synced_rate"] == 1.0
        assert r["counts"]["BIRTH_MISSING_RECOMPUTED"] == 0


def test_g3b_stale_verdict_detected():
    """负向注入(b): 落盘自带但与现算不符→STALE>0 (判据演进旧verdict过期)。"""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "footprints.jsonl")
        _write(K._sibling(p, "heartbeat_log.jsonl"), [_hb(stored_verdict="FAIL_CONVERGED") for _ in range(2)])
        r = K.verdict_at_birth_probe(log_path=p)
        assert r["counts"]["BIRTH_STALE"] == 2  # 现算DIVERSE=PASS,落盘FAIL→STALE
        assert r["synced_rate"] == 0.0


def test_g3c_all_missing():
    """负向注入(c): 全条无落盘verdict→missing_recomputed=total。"""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "footprints.jsonl")
        _write(K._sibling(p, "heartbeat_log.jsonl"), [_hb() for _ in range(4)])
        r = K.verdict_at_birth_probe(log_path=p)
        assert r["counts"]["BIRTH_MISSING_RECOMPUTED"] == 4
        assert r["missing_recomputed_rate"] == 1.0


def test_g3d_empty_log_no_spin():
    """负向注入(d): 空日志→total=0, 各率0, 不空转。"""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "footprints.jsonl")
        _write(K._sibling(p, "heartbeat_log.jsonl"), [])
        r = K.verdict_at_birth_probe(log_path=p)
        assert r["total"] == 0
        assert r["synced_rate"] == 0.0 and r["missing_recomputed_rate"] == 0.0
        assert r["per_heartbeat"] == []


def test_g3e_unverifiable():
    """负向注入(e): 落盘UNKNOWN且现算也UNKNOWN(COLD_START)→UNVERIFIABLE>0。"""
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "footprints.jsonl")
        _write(K._sibling(p, "heartbeat_log.jsonl"),
               [_hb(guard_state="COLD_START", stored_verdict="UNKNOWN")])
        r = K.verdict_at_birth_probe(log_path=p)
        assert r["counts"]["BIRTH_UNVERIFIABLE"] == 1


def test_g4_readonly_and_authoritative_zero():
    """只读性+权威态零副作用: 调用前后心跳/权威态/宪法字节不变。"""
    hb_path = "/workspace/life_kernel/data/heartbeat_log.jsonl"
    auth = "/workspace/authoritative_state.json"
    const = "/workspace/life_kernel/constitution.json"
    before = [_sha(x) for x in (hb_path, auth, const)]
    K.verdict_at_birth_probe()
    after = [_sha(x) for x in (hb_path, auth, const)]
    assert before == after
