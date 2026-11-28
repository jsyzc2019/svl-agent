"""§4S59 无聊找事：restless 内稳态信号 + PROMENADE 闲走议程 守卫测试。"""
import json
import os
import sys
import hashlib

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K


def _wallet(d, stamps, footprints=3):
    """隔离夹具：合成心跳时间戳 + 足够脚印(避免稀疏失衡干扰纯闲态)。"""
    hb = os.path.join(d, "heartbeat_log.jsonl")
    fp = os.path.join(d, "footprints.jsonl")
    with open(hb, "w", encoding="utf-8") as f:
        for ts in stamps:
            f.write(json.dumps({"timestamp": ts, "direction": "闲走测试"}) + "\n")
    for i in range(footprints):
        with open(fp, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": "P%d" % i, "direction": "既有路%d" % i,
                                "applicability": "general"}) + "\n")
    return fp, hb


def test_real_restless_from_true_log():
    """真实台账：间隙来自真实时间戳，非硬编码。"""
    sig = K.homeostatic_signals()
    r = sig["restless"]
    assert r["gap_hours"] > 0 and r["at_last_beat"]
    assert 0.0 <= r["urgency"] <= K.RESTLESS_CAP
    assert r["cap"] == K.RESTLESS_CAP == 0.12


def test_promenade_upholds_in_pure_idle():
    """纯闲态(脚印足/无授权/昼行/超阈值)：PROMENADE 真上位，非死代码。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fp, _ = _wallet(d, ["2026-11-28T01:00:00Z", "2026-11-28T03:00:00Z"])
        dec = K.autonomous_agenda(seed=1, log_path=fp)
        assert dec["chosen"] == "PROMENADE"


def test_real_gap_signal_is_bounded_below_real_imbalance():
    """封顶0.12 远低于 CONSOLIDATE0.45/REORIENT0.95。"""
    assert K.RESTLESS_CAP < 0.45 and K.RESTLESS_CAP < 0.95
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fp = os.path.join(d, "fp.jsonl")  # 空脚印→稀疏失衡
        dec = K.autonomous_agenda(seed=1, log_path=fp)
        assert dec["chosen"] == "CONSOLIDATE"


def test_night_gap_is_not_boredom():
    """夜伏相位长间隔=休眠，不算无聊。"""
    hbs = [{"timestamp": "2026-11-28T01:00:00Z"}, {"timestamp": "2026-11-28T03:00:00Z"}]
    assert K._restlessness(hbs, phase="NIGHT")["urgency"] == 0.0
    assert K._restlessness(hbs, phase="DAY")["urgency"] > 0.0


def test_short_gap_below_threshold():
    """短间隔(<1h)未达阈值→0。"""
    hbs = [{"timestamp": "2026-11-27T07:15:10Z"}, {"timestamp": "2026-11-27T07:15:17Z"}]
    assert K._restlessness(hbs, phase="DAY")["urgency"] == 0.0


def test_strong_idle_caps_at_cap():
    """强闲24h也只到CAP，不越位。"""
    hbs = [{"timestamp": "2026-11-27T00:00:00Z"}, {"timestamp": "2026-11-28T00:00:00Z"}]
    r = K._restlessness(hbs, phase="DAY")
    assert r["urgency"] == K.RESTLESS_CAP == 0.12


def test_empty_heartbeat_no_boredom():
    """无心跳日志→restless=0，不制造假无聊。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        sig = K.homeostatic_signals(log_path=os.path.join(d, "fp.jsonl"))
        assert sig["restless"]["urgency"] == 0.0


def test_probe_readonly_and_no_gate():
    """restlessness_probe 只读、不进判定、台账字节不变。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        fp, hb = _wallet(d, ["2026-11-28T01:00:00Z", "2026-11-28T03:00:00Z"])
        before = hashlib.sha256(open(hb, "rb").read()).hexdigest()
        r = K.restlessness_probe(log_path=fp)
        after = hashlib.sha256(open(hb, "rb").read()).hexdigest()
        assert before == after
        assert r["is_gate_verdict"] is False and r["verdict_unchanged"] is True
        assert r["boredom_level"] in ("idle", "content")


def test_authoritative_state_untouched():
    r = json.load(open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__)))), "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    assert r["verdict"] == "GAP_INCONCLUSIVE"
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
