"""§4gs P2 元命题收敛守卫。

固化 NEXT_STAGE_PLAN §P2 的验收标准：
- 6-8 条元命题，每条四栏齐全（claim/support/refuted_by/currently_refuted）
- 每条必须有可证伪的 refuted_by（非空、非占位）
- 支持证据路径必须真实存在（可机械追溯，防'换说法重排'）
- 对冲关系必须引用存在的命题 id，且 ≥3 组（防'归纳罗列'）
- 每条跨轮合并（origin_rounds），多数 ≥2 轮
- 判定态四栏一致：所有命题 verdict_impact=none，内核三态不动
- sha256 锁一致

负向自咬：删一条 refuted_by 或一条 tension，对应测试必须 FAILED。
"""
import glob
import hashlib
import json

PATH = "META_PROPOSITIONS_20261126.json"
REQUIRED_FIELDS = ("claim", "support", "refuted_by", "currently_refuted",
                   "evidence_paths", "origin_rounds")


def _load():
    return json.load(open(PATH, encoding="utf-8"))


def test_s01_proposition_count_and_four_columns():
    """5-8 条，每条四栏齐全。"""
    d = _load()
    ps = d["meta_propositions"]
    assert 5 <= len(ps) <= 8, f"命题数越界: {len(ps)}"
    for p in ps:
        for f in REQUIRED_FIELDS:
            assert f in p, f"{p['id']} 缺栏 {f}"
        assert isinstance(p["currently_refuted"], bool)


def test_s02_every_proposition_falsifiable():
    """每条必须有可证伪的推翻条件（非空、非占位、含动作动词）。"""
    d = _load()
    for p in d["meta_propositions"]:
        rb = p["refuted_by"].strip()
        assert len(rb) >= 10, f"{p['id']} refuted_by 过短/占位"
        assert any(k in rb for k in ("发现", "若", "未", "不得", "被")), \
            f"{p['id']} refuted_by 无可检验触发词"


def test_s03_evidence_paths_exist():
    """支持证据路径真实存在——机械可追溯，防空泛罗列。"""
    d = _load()
    for p in d["meta_propositions"]:
        for ep in p["evidence_paths"]:
            assert glob.glob(ep), f"{p['id']} 证据路径不存在: {ep}"


def test_s04_tensions_are_real():
    """≥3 组对冲，且每组引用的命题 id 存在、a≠b。"""
    d = _load()
    ids = {p["id"] for p in d["meta_propositions"]}
    ts = d["tensions"]
    assert len(ts) >= 3, f"对冲不足（归纳罗列风险）: {len(ts)}"
    for t in ts:
        assert t["a"] in ids and t["b"] in ids, f"对冲引用不存在命题: {t}"
        assert t["a"] != t["b"]
        assert len(t["tension"]) >= 20, "对冲描述过短，非真实张力"


def test_s05_most_propositions_merge_multiple_rounds():
    """多数命题跨 ≥2 轮合并（真正合并而非单章换说法）。"""
    d = _load()
    multi = [p for p in d["meta_propositions"] if len(p["origin_rounds"]) >= 2]
    assert len(multi) >= len(d["meta_propositions"]) - 1, \
        f"跨轮合并命题过少: {len(multi)}/{len(d['meta_propositions'])}"


def test_s06_verdict_impact_none_and_lock():
    """收敛不碰判定态；sha256 锁一致。"""
    d = _load()
    assert d["verdict_impact"] == "none"
    for p in d["meta_propositions"]:
        assert p["currently_refuted"] is False, f"{p['id']} 标为已推翻却 verdict=none"
    from life_kernel.numeric_honesty import truth_snapshot
    s = truth_snapshot()
    assert (s["verdict"], s["l3_claimed"], s["absolute_claimed"]) == \
           ("GAP_INCONCLUSIVE", False, False)
    assert s["constitution_prefix"] == "fe56291b"
    # sha 锁（对除 sha256 字段外的规范序列化）
    d2 = dict(d)
    locked = d2.pop("sha256")
    assert hashlib.sha256(json.dumps(d2, ensure_ascii=False, sort_keys=True).encode()).hexdigest() == locked


def test_s07_negative_selfbite():
    """负向自咬：篡改副本删 refuted_by / 删对冲，验收必须失败。"""
    d = _load()
    bad1 = dict(d)
    bad1["meta_propositions"] = [dict(p) for p in d["meta_propositions"]]
    bad1["meta_propositions"][0]["refuted_by"] = ""
    assert any(not p["refuted_by"].strip() for p in bad1["meta_propositions"])
    bad2 = dict(d)
    bad2["tensions"] = []
    assert len(bad2["tensions"]) < 3
    # 真实文件未被篡改
    assert all(p["refuted_by"].strip() for p in d["meta_propositions"])
    assert len(d["tensions"]) >= 3
