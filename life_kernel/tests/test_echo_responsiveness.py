"""§4S55 守卫测试：echo_responsiveness_probe 把外部判据做成会跑的只读标尺。

判据锁定见 prereg_echo_responsiveness_20261128.json（sha 5fc0007d…）。
纯只读，全部用注入参数或隔离路径，绝不写台账、不碰判定。
"""
import os
import sys
import hashlib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, HERE)

import kernel as K


def test_real_verdict_engaged_discernment_after_c2():
    """真实台账：§4S57 补C2后判据演进为 ENGAGED_DISCERNMENT(5/5)。

    历史：§4S55 CAUTIOUS(C4/C2均弱)→§4S56 补C4后 BOUNDED_UPDATABLE(C2弱)→
    §4S57 补C2后 ENGAGED_DISCERNMENT(五条件全真)。每次断言更新都是判据演进的合法后果，非迁就测试。
    仍在受限通道内(永不主导/可撤销/不进判定),不冒充无界GENUINE。
    """
    r = K.echo_responsiveness_probe()
    assert r["verdict"] == "ENGAGED_DISCERNMENT"
    c = r["conditions"]
    assert c["C1_接住输入"] is True and c["C3_可见后果"] is True
    assert c["C4_可更新"] is True and c["C2_可检验判断"] is True
    assert c["免责_可审计约束"] is True
    assert r["criterion_satisfied_count"] == 5
    assert r["is_gate_verdict"] is False and r["verdict_unchanged"] is True


def test_no_input_verdict():
    """无输入→NO_INPUT。"""
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = K.echo_responsiveness_probe(log_path=os.path.join(d, "fp.jsonl"))
    assert r["verdict"] == "NO_INPUT"


def test_genuine_interaction_injection():
    """注入ATTEND议程→GENUINE_INTERACTION（判据会真改变）。"""
    r = K.echo_responsiveness_probe(agenda_ids=["ATTEND", "SEEK"], trace_count=1)
    assert r["verdict"] == "GENUINE_INTERACTION"


def test_pretended_openness_injection():
    """注入零痕迹+无约束→PRETENDED_OPENNESS。"""
    r = K.echo_responsiveness_probe(agenda_ids=["SEEK"], trace_count=0, audit_constraint=False)
    assert r["verdict"] == "PRETENDED_OPENNESS"


def test_verdict_not_constant():
    """同一函数不同注入给不同verdict=非恒真（会真失败）。"""
    a = K.echo_responsiveness_probe(agenda_ids=["ATTEND"], trace_count=1)["verdict"]
    b = K.echo_responsiveness_probe(agenda_ids=["SEEK"], trace_count=0,
                                    audit_constraint=False)["verdict"]
    assert a != b


def test_read_only_no_mutation():
    """只读：调用前后台账字节不变。"""
    def sha(p):
        with open(p, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    paths = [os.path.join(HERE, "data", "inbound_inbox.jsonl"),
             os.path.join(HERE, "data", "heartbeat_log.jsonl"),
             os.path.join(HERE, "data", "agenda_log.jsonl")]
    before = {p: sha(p) for p in paths}
    K.echo_responsiveness_probe()
    assert all(sha(p) == before[p] for p in paths)
