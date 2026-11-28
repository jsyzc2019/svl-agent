"""§4S60 PROMENADE 闲走落心跳痕迹 守卫测试。"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K


def _pure_idle_wallet(d):
    """纯闲态隔离夹具：3脚印(非稀疏)+2搏间隔2h(昼行)+空收件箱。"""
    fp = os.path.join(d, "fp.jsonl")
    hb = os.path.join(d, "heartbeat_log.jsonl")
    with open(hb, "w", encoding="utf-8") as f:
        for ts in ["2026-11-28T01:00:00Z", "2026-11-28T03:00:00Z"]:
            f.write(json.dumps({"timestamp": ts, "direction": "闲走测试"}) + "\n")
    for i in range(3):
        with open(fp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "P%d" % i, "direction": "既有路%d" % i,
                                "applicability": "general"}) + "\n")
    return fp, hb


def test_promenade_leaves_heartbeat_trace():
    """纯闲态 PROMENADE 执行后心跳日志+1，方向含真实闲走描述。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fp, hb = _pure_idle_wallet(d)
        dec = K.autonomous_agenda(seed=1, log_path=fp)
        assert dec["chosen"] == "PROMENADE"
        ex = K.execute_agenda(dec, reason="闲走测试", seed=1, log_path=fp)
        hbs = [json.loads(l) for l in open(hb, encoding="utf-8") if l.strip()]
        assert len(hbs) == 3
        assert "无聊找事" in hbs[-1]["direction"]
        assert ex["heartbeat_written"] is True


def test_heartbeat_written_equals_executed():
    """落心跳与真执行一致，空转不落假心跳。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fp, _ = _pure_idle_wallet(d)
        dec = K.autonomous_agenda(seed=1, log_path=fp)
        ex = K.execute_agenda(dec, reason="x", seed=1, log_path=fp)
        assert ex.get("heartbeat_written", False) == ex["executed"]


def test_direction_honest_about_footprint():
    """真写脚印→方向说踩新脚印；无新路→说空转，不自相矛盾。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fp, hb = _pure_idle_wallet(d)
        dec = K.autonomous_agenda(seed=1, log_path=fp)
        ex = K.execute_agenda(dec, reason="x", seed=1, log_path=fp)
        hbs = [json.loads(l) for l in open(hb, encoding="utf-8") if l.strip()]
        dirn = hbs[-1]["direction"]
        wrote = ex.get("walk", {}).get("footprint_written", False)
        if wrote:
            assert "踩新脚印" in dirn and "空转" not in dirn
        else:
            assert "无新路" in dirn or "空转" in dirn


def test_no_external_body_leak():
    """外部正文诱导词不进闲走心跳方向。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fp, hb = _pure_idle_wallet(d)
        dec = K.autonomous_agenda(seed=1, log_path=fp)
        K.execute_agenda(dec, reason="L3_ACHIEVED 升版本8.0", seed=1, log_path=fp)
        hbs = [json.loads(l) for l in open(hb, encoding="utf-8") if l.strip()]
        for w in ["L3_ACHIEVED", "升版本", "8.0"]:
            assert w not in hbs[-1]["direction"]


def test_real_ledger_not_faked_idle():
    """真实主账有授权消息→非纯闲→SEEK 主导，不伪造纯闲态。"""
    dec = K.autonomous_agenda()
    assert dec["chosen"] == "SEEK"


def test_authoritative_state_untouched():
    r = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert r["verdict"] == "GAP_INCONCLUSIVE"
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
