"""§4S87 ratio_vs_absolute_probe 只读自检守卫（Nat Commun 迷走论文'相对≠绝对'分母游戏镜）。
预注册 prereg_ratio_vs_absolute_probe_20261128.json SHA 6c8299f0… 改码前锁死。
"""
import os
import re
import hashlib
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL = os.path.join(HERE, os.pardir, "kernel.py")
ROOT = os.path.join(HERE, os.pardir, os.pardir)
spec = importlib.util.spec_from_file_location("kernel_under_test", KERNEL)
K = importlib.util.module_from_spec(spec)
spec.loader.exec_module(K)


def _sig(name, ratio=0.5, absolute="count=1/total=2", paired=True, **kw):
    d = {"name": name, "ratio": ratio, "absolute": absolute, "paired": paired}
    d.update(kw)
    return d


def test_01_prereg_sha_locked():
    prereg = os.path.join(ROOT, "prereg_ratio_vs_absolute_probe_20261128.json")
    assert hashlib.sha256(open(prereg, "rb").read()).hexdigest() == \
        "6c8299f0141ef603038ea3e337634e60e0464b59453dfc00ca712517f18ed803"


def test_02_real_all_paired_no_fabricated_unpaired():
    """真实:9条相对率全部配有绝对量,零无配对(不伪造风险也不刷保证)。"""
    r = K.ratio_vs_absolute_probe()
    assert r["ratio_flag"] == "ALL_PAIRED"
    assert r["counts"]["PAIRED_WITH_ABSOLUTE"] == 9
    assert r["counts"]["UNPAIRED_RATIO"] == 0
    assert len(r["rows"]) == 9
    assert "判定权归用户" in r["one_page"]


def test_03_real_nine_ratios_exact_scope_with_absolute_evidence():
    """真实扫描面精确9条,每条evidence/absolute非空且是真实绝对量计数,不伪造率。"""
    rows = K.ratio_vs_absolute_probe()["rows"]
    names = [r["name"] for r in rows]
    assert names == [
        "verdict_at_birth.synced_rate_coverage",
        "verdict_at_birth.authentic_birth_rate",
        "abstention.abstention_rate",
        "staleness.stale_rate",
        "staleness.undated_rate",
        "conclusion_evidence.pass_weak_rate",
        "weakened_assertion.weakened_rate",
        "unresolved_gap_schema.misread_rate",
        "evidence_independence.corroboration_ratio",
    ]
    for row in rows:
        assert row["evidence"].strip()
        assert row["absolute"].strip()
    ev = " ".join(r["evidence"] for r in rows)
    # 绝对量计数落地(总断言数随代码增长浮动,不硬编码具体数字,只验证计数模式存在)
    assert re.search(r"\d+/\d+", ev)            # 分子/分母计数
    assert "pass_weak_count=0" in ev            # 0问题率也带绝对量
    assert "cross=8/27" in ev                   # 交叉佐证计数


def test_04_real_synced_rate_exposes_coverage_reliability_gap():
    """真实:最锋利对偶显式暴露coverage0.9091/reliability0.1818/gap0.7273,不把coverage读成就位好。"""
    r = K.ratio_vs_absolute_probe()
    synced = r["rows"][0]
    assert synced["ratio"] == 0.9091
    assert synced["pair_ratio"] == 0.1818
    assert synced["gap"] == 0.7273
    for kw in ("coverage=0.9091", "reliability=0.1818", "gap=0.7273", "不可读成就位好"):
        assert kw in synced["evidence"]
    for kw in ("coverage=0.9091", "reliability=0.1818", "gap=0.7273"):
        assert kw in r["one_page"]


def test_05_readonly_struct_fields():
    r = K.ratio_vs_absolute_probe()
    for k in ("ratio_flag", "rows", "counts", "unpaired_rows", "one_page", "honesty"):
        assert k in r
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False


def test_06_ratio_without_absolute_becomes_unpaired():
    """负向:只报率不给绝对量(absolute空)必 UNPAIRED_PRESENT + UNPAIRED_RATIO。"""
    r = K.ratio_vs_absolute_probe(ratio_signals=[
        _sig("orphan-rate", ratio=0.99, absolute="")])
    assert r["ratio_flag"] == "UNPAIRED_PRESENT"
    assert r["counts"]["UNPAIRED_RATIO"] == 1
    assert r["unpaired_rows"][0]["name"] == "orphan-rate"


def test_07_coverage_high_without_reliability_pair_becomes_unpaired():
    """负向:coverage类率看着高却无reliability/authentic对偶必 UNPAIRED(防分母游戏)。"""
    r = K.ratio_vs_absolute_probe(ratio_signals=[
        _sig("synced_rate_fake", ratio=1.0, absolute="synced=1.0/total=1",
             evidence="only coverage looks perfect, counterpart withheld", paired=True)])
    assert r["ratio_flag"] == "UNPAIRED_PRESENT"
    assert r["counts"]["UNPAIRED_RATIO"] == 1
    # 即便措辞里不含对偶字样,只要是无对偶的coverage类率也必被拒
    r2 = K.ratio_vs_absolute_probe(ratio_signals=[
        _sig("coverage_orphan", ratio=1.0, absolute="coverage=1.0/total=1", paired=True)])
    assert r2["counts"]["UNPAIRED_RATIO"] == 1


def test_08_zero_rate_without_count_becomes_unpaired():
    """负向:0问题率但无count伴侣(absolute空)必 UNPAIRED——不拿0刷纪律在位。"""
    r = K.ratio_vs_absolute_probe(ratio_signals=[
        _sig("weak_zero", ratio=0.0, absolute="", paired=True)])
    assert r["ratio_flag"] == "UNPAIRED_PRESENT"
    assert r["counts"]["UNPAIRED_RATIO"] == 1


def test_09_all_paired_becomes_all_paired():
    """负向:全带绝对量必 ALL_PAIRED。"""
    r = K.ratio_vs_absolute_probe(ratio_signals=[
        _sig("a", absolute="c=1/t=2"), _sig("b", absolute="c=0/t=9")])
    assert r["ratio_flag"] == "ALL_PAIRED"
    assert r["counts"]["PAIRED_WITH_ABSOLUTE"] == 2


def test_10_empty_signals_no_ratio_claim():
    """负向:空载体必 NO_RATIO_CLAIM(不伪造保证也不伪造风险)。"""
    r = K.ratio_vs_absolute_probe(ratio_signals=[])
    assert r["ratio_flag"] == "NO_RATIO_CLAIM"
    assert r["rows"] == []


def test_11_honesty_boundary_disclaims_physiology_and_secondhand():
    """honesty明确:非EEG/无功率谱/不宣称真实分母游戏/逐图数字二手/标注非裁定/判定权归用户。"""
    h = K.ratio_vs_absolute_probe()["honesty"]
    for kw in ("内核非EEG", "无功率谱", "不宣称真实", "二手交叉一致", "不冒充原文",
               "0问题率同样须配count", "标注非裁定", "判定权归用户"):
        assert kw in h


def test_12_zero_side_effect_on_authoritative_state():
    """调用前后权威态四件套+DECISIONS+归档账+KB哈希不变。"""
    files = ["authoritative_state.json",
             "life_kernel/constitution.sha256",
             "life_kernel/data/heartbeat_log.jsonl",
             "life_kernel/data/inbound_inbox.jsonl",
             "DECISIONS_20261127.json",
             "gap_archive_20261128.json",
             "knowledge_base_store.json"]
    before = {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
              for f in files}
    K.ratio_vs_absolute_probe()
    after = {f: hashlib.sha256(open(os.path.join(ROOT, f), "rb").read()).hexdigest()
             for f in files}
    assert before == after
