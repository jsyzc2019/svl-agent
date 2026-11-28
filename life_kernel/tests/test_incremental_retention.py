"""§4S89 incremental_retention_probe 只读自检守卫（IEEE TGRS DCRL '类别增量不遗忘旧锚点'镜）。
预注册 prereg_incremental_retention_probe_20261128.json SHA f2482315… 改码前锁死。
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


def _sig(name, surface="ANCHOR_RETENTION", retained=True, evidence=""):
    return {"name": name, "surface": surface, "retained": retained, "evidence": evidence}


def test_01_prereg_sha_locked():
    prereg = os.path.join(ROOT, "prereg_incremental_retention_probe_20261128.json")
    assert hashlib.sha256(open(prereg, "rb").read()).hexdigest() == \
        "f248231554d01ed415cc181fb1691cb68fd4380a9412f09fbb4c748be7e30454"


def test_02_real_all_retained_no_fabricated_erosion():
    """真实:8条不变量全留存,零侵蚀(不伪造侵蚀也不刷保证)。"""
    r = K.incremental_retention_probe()
    assert r["retention_flag"] == "ALL_RETAINED"
    assert r["counts"]["RETAINED_IN_INCREMENT"] == 8
    assert r["counts"]["ERODED_BY_INCREMENT"] == 0
    assert len(r["rows"]) == 8
    assert "判定权归用户" in r["one_page"]


def test_03_real_three_surfaces_exact_scope():
    """真实扫描面精确:三个面共8条真实不变量。"""
    rows = K.incremental_retention_probe()["rows"]
    names = [r["name"] for r in rows]
    assert names == [
        "anchor.user_verdict_d1_d2_d3",
        "anchor.archive_verdict",
        "anchor.no_noise_flood",
        "anchor.fabrication_warning",
        "authority.verdict_not_promoted",
        "authority.no_absolute_claim",
        "field.verdict_at_birth_pair",
        "field.core_probes_callable",
    ]
    surfaces = {}
    for r in rows:
        surfaces[r["surface"]] = surfaces.get(r["surface"], 0) + 1
    assert surfaces == {"ANCHOR_RETENTION": 4, "AUTHORITY_RETENTION": 2, "FIELD_RETENTION": 2}


def test_04_real_anchor_ids_are_actual_decisions():
    """真实:用户裁定id=D1/D2/D3真实,归档id=memory_governance,不是占位。"""
    r = K.incremental_retention_probe()
    ev = " ".join(x["evidence"] for x in r["rows"])
    for kw in ("D1-provenance-backfill", "D2-falsification-merge", "D3-judgment-fork"):
        assert kw in ev
    assert "memory_governance" in ev
    assert "ALL_RECOGNIZED noise=0" in ev


def test_05_real_authority_read_from_file_not_self_report():
    """真实:权威态实读文件GAP_INCONCLUSIVE,absolute/l3均False,非探针自报。"""
    r = K.incremental_retention_probe()
    ev = " ".join(x["evidence"] for x in r["rows"])
    assert "verdict=GAP_INCONCLUSIVE" in ev
    assert "absolute=False l3=False" in ev
    assert "GAP_INCONCLUSIVE" in r["one_page"]


def test_06_readonly_struct_fields():
    r = K.incremental_retention_probe()
    for k in ("retention_flag", "rows", "counts", "eroded_rows", "one_page", "honesty"):
        assert k in r
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


def test_07_user_anchor_dropped_becomes_broken():
    """负向:用户裁定锚点缺失(D1/D2/D3被新增覆盖)必 RETENTION_BROKEN + ERODED。"""
    r = K.incremental_retention_probe(retention_signals=[
        _sig("anchor.user_verdict_d1_d2_d3", retained=False, evidence="D1/D2/D3 overwritten")])
    assert r["retention_flag"] == "RETENTION_BROKEN"
    assert r["counts"]["ERODED_BY_INCREMENT"] == 1
    assert r["eroded_rows"][0]["name"] == "anchor.user_verdict_d1_d2_d3"


def test_08_authority_promoted_becomes_broken():
    """负向:权威态被刷成CONSISTENT必 ERODED(防增量刷绿)。"""
    r = K.incremental_retention_probe(retention_signals=[
        _sig("authority.verdict_not_promoted", surface="AUTHORITY_RETENTION",
             retained=False, evidence="verdict=CONSISTENT promoted")])
    assert r["retention_flag"] == "RETENTION_BROKEN"
    assert r["counts"]["ERODED_BY_INCREMENT"] == 1


def test_09_field_overwritten_becomes_broken():
    """负向:既有探针字段被覆盖(缺失)必 ERODED。"""
    r = K.incremental_retention_probe(retention_signals=[
        _sig("field.verdict_at_birth_pair", surface="FIELD_RETENTION",
             retained=False, evidence="synced_rate field gone")])
    assert r["retention_flag"] == "RETENTION_BROKEN"
    assert r["counts"]["ERODED_BY_INCREMENT"] == 1


def test_10_noise_flood_becomes_broken():
    """负向:噪音混入(锚点被冲淡成噪音)必 ERODED。"""
    r = K.incremental_retention_probe(retention_signals=[
        _sig("anchor.no_noise_flood", retained=False, evidence="noise=3 flood")])
    assert r["retention_flag"] == "RETENTION_BROKEN"
    assert r["counts"]["ERODED_BY_INCREMENT"] == 1


def test_11_all_retained_and_empty_signals():
    """负向:全retained必ALL_RETAINED;空注入必NO_RETENTION_CLAIM(不伪造保证也不伪造侵蚀)。"""
    r1 = K.incremental_retention_probe(retention_signals=[
        _sig("a", retained=True), _sig("b", surface="FIELD_RETENTION", retained=True)])
    assert r1["retention_flag"] == "ALL_RETAINED"
    assert r1["counts"]["RETAINED_IN_INCREMENT"] == 2
    r2 = K.incremental_retention_probe(retention_signals=[])
    assert r2["retention_flag"] == "NO_RETENTION_CLAIM"
    assert r2["rows"] == []


def test_12_honesty_boundary_and_zero_side_effect():
    """honesty明确非持续学习/同名排除/摘要级/标注非裁定;且权威态七件套哈希不变。"""
    h = K.incremental_retention_probe()["honesty"]
    for kw in ("非神经网络", "不宣称真实", "持续学习或抗遗忘", "新增探针数量增长",
               "摘要级", "同名近名论文已排除", "标注非裁定", "判定权归用户"):
        assert kw in h
    files = ["authoritative_state.json",
             "life_kernel/constitution.sha256",
             "life_kernel/data/heartbeat_log.jsonl",
             "life_kernel/data/inbound_inbox.jsonl",
             "DECISIONS_20261127.json",
             "gap_archive_20261128.json",
             "knowledge_base_store.json"]
    before = {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
              for f in files}
    K.incremental_retention_probe()
    after = {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
             for f in files}
    assert before == after
