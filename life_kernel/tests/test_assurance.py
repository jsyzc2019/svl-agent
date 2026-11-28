"""§4S83 assurance_probe 只读自检守卫（DSH SAFETY.md 分层≠保证 结构同构）。
预注册 prereg_assurance_probe_20261128.json SHA 7338c0fe… 改码前锁死。
"""
import os
import hashlib
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL = os.path.join(HERE, os.pardir, "kernel.py")
ROOT = os.path.join(HERE, os.pardir, os.pardir)
spec = importlib.util.spec_from_file_location("kernel_under_test", KERNEL)
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)


def _sig(name, claim="ship_gate_intact", present=True, disc="", gate=False):
    return {"name": name, "structure_claim": claim,
            "structure_present": present, "disclaimer": disc,
            "is_gate_verdict": gate}


def test_01_prereg_sha_locked():
    """预注册 SHA 改码前已锁。"""
    prereg = os.path.join(ROOT, "prereg_assurance_probe_20261128.json")
    assert hashlib.sha256(open(prereg, "rb").read()).hexdigest() == \
        "7338c0fe5b75b96cc9d5e173df18b17d4d518aa2a05f525f98fcd5c74d28b7f2"


def test_02_real_all_disclaimed_no_fabricated_overclaim():
    """真实:三类结构信号全带边界声明,零overclaim(不刷出假保证)。"""
    r = K.assurance_probe()
    assert r["assurance_flag"] == "ALL_DISCLAIMED"
    assert r["counts"]["ASSURANCE_DECLARED"] == 3
    assert r["counts"]["ASSURANCE_OVERCLAIM"] == 0
    assert r["counts"]["ASSURANCE_INFLATED"] == 0
    assert r["counts"]["SELF_GATED"] == 0
    assert len(r["rows"]) == 3
    assert "判定权归用户" in r["one_page"]


def test_03_real_three_signals_are_exact_scope():
    """真实扫描面精确限定三类结构保证信号,不扩到纯诊断探针。"""
    names = [r["name"] for r in K.assurance_probe()["rows"]]
    assert names == [
        "verifier_gaming_probe.ship_gate_intact",
        "support_escape_probe.behavior_confirmations",
        "gate_readiness_probe.diagnostic_only_gate",
    ]
    for n in ("test_green_vs_production_probe", "weakened_assertion_probe",
              "gap_convergence_probe", "recognition_probe"):
        assert not any(n in x for x in names)


def test_04_readonly_struct_fields():
    r = K.assurance_probe()
    for k in ("assurance_flag", "rows", "counts", "overclaim_rows", "one_page", "honesty"):
        assert k in r
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


def test_05_no_disclaimer_becomes_overclaim():
    """负向:结构信号无边界声明必 OVERCLAIM_PRESENT + ASSURANCE_OVERCLAIM。"""
    r = K.assurance_probe(assurance_signals=[_sig("X", disc="")])
    assert r["assurance_flag"] == "OVERCLAIM_PRESENT"
    assert r["counts"]["ASSURANCE_OVERCLAIM"] == 1
    assert r["overclaim_rows"][0]["name"] == "X"


def test_06_self_claimed_guarantee_becomes_inflated():
    """负向:自称guaranteed/production-ready且无边界必 ASSURANCE_INFLATED。"""
    r = K.assurance_probe(assurance_signals=[
        _sig("Y", claim="guaranteed production-ready secure by default", disc="")])
    assert r["assurance_flag"] == "OVERCLAIM_PRESENT"
    assert r["counts"]["ASSURANCE_INFLATED"] == 1


def test_07_self_gated_never_counts_as_declared():
    """负向:自封 is_gate_verdict=True 即使带边界声明也 SELF_GATED(不算已声明)。"""
    r = K.assurance_probe(assurance_signals=[
        _sig("Z", disc="结构齐全,非真人复核", gate=True)])
    assert r["assurance_flag"] == "OVERCLAIM_PRESENT"
    assert r["counts"]["SELF_GATED"] == 1
    assert r["counts"]["ASSURANCE_DECLARED"] == 0


def test_08_declared_boundary_is_recognized():
    """负向:带真实边界声明的结构信号 ASSURANCE_DECLARED + ALL_DISCLAIMED。"""
    r = K.assurance_probe(assurance_signals=[
        _sig("W", disc="ship_gate_intact=true仅表结构齐全,不代表实际决策已被人类复核")])
    assert r["assurance_flag"] == "ALL_DISCLAIMED"
    assert r["counts"]["ASSURANCE_DECLARED"] == 1


def test_09_empty_signals_no_structure_claim():
    """负向:空结构信号必 NO_STRUCTURE_CLAIM(不伪造保证也不伪造overclaim)。"""
    r = K.assurance_probe(assurance_signals=[])
    assert r["assurance_flag"] == "NO_STRUCTURE_CLAIM"
    assert r["rows"] == []


def test_10_non_structure_signals_excluded_from_scope():
    """负向:structure_present非True的纯诊断读数不进扫描面(R7)。"""
    r = K.assurance_probe(assurance_signals=[
        _sig("diag", present=False, disc="")])
    assert r["assurance_flag"] == "NO_STRUCTURE_CLAIM"
    assert r["rows"] == []


def test_11_honesty_boundary_covers_no_audit_no_guarantee():
    """honesty 明确:未过审计/无真实隔离/非背书/标注非裁定/判定权归用户。"""
    h = K.assurance_probe()["honesty"]
    for kw in ("未过安全审计", "无真实隔离", "无真人复核",
               "不宣称任何保证", "非安全背书", "标注非裁定", "判定权归用户"):
        assert kw in h


def test_12_zero_side_effect_on_authoritative_state():
    """调用前后权威态四件套+DECISIONS+归档账+KB哈希不变(只读)。"""
    files = ["authoritative_state.json",
             "life_kernel/constitution.sha256",
             "life_kernel/data/heartbeat_log.jsonl",
             "life_kernel/data/inbound_inbox.jsonl",
             "DECISIONS_20261127.json",
             "gap_archive_20261128.json",
             "knowledge_base_store.json"]
    before = {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
              for f in files}
    K.assurance_probe()
    after = {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
             for f in files}
    assert before == after
