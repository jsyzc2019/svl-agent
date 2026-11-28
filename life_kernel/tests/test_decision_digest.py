"""§4S69 守卫测试：决策收敛单——把选项摆清楚但不替用户裁定。
口径锁于 prereg_decision_digest_20261129.json SHA 32a62a50…。
纪律：标注≠裁定；正文不读；脏key原样暴露；负向注入非恒真；零副作用。
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K


def _inject_dist(monkeypatch, dist):
    fake_rg = {"unresolved_gap_verdict_dist": dist, "unresolved_gap_count": sum(dist.values())}
    monkeypatch.setattr(K, "regression_vs_gap_probe", lambda: fake_rg)


def _inject_weak(monkeypatch, weak):
    fake_ce = {"per_heartbeat": weak}
    monkeypatch.setattr(K, "conclusion_evidence_probe", lambda: fake_ce)


# ---------------- G2: 真实数据如实列出,不替裁定 ----------------

def test_real_data_not_arbitrating():
    r = K.decision_digest()
    assert r["verdict_unchanged"] is True
    assert r["consumed"] is False
    assert r["is_gate_verdict"] is False
    assert "判定权归用户" in r["one_page"]
    assert "不替你决定" in r["one_page"]
    # §4S70 回填后:35个'?'已正名,未解决缺口 46→14(11原生+3回填保留悬置),真实数据演进
    assert r["by_section"]["gap_clusters"] == 14
    assert r["by_section"]["weak_evidence"] == 5
    assert r["by_section"]["inbox_messages"] == 2


def test_real_message_body_never_read():
    """真实收件箱两条消息:清单必须body_read=False,且不含message正文字段。"""
    r = K.decision_digest()
    rows = r["sections"]["inbox_messages"]["rows"]
    assert len(rows) == 2
    for x in rows:
        assert x["body_read"] is False
        assert "message" not in x
    # one_page 与各 section 计数一致
    assert ("未读消息%d" % len(rows)) in r["one_page"]


def test_dirty_key_exposed_verbatim():
    """真实数据里那个dict字符串化脏key必须原样暴露,不被静默吞掉。"""
    r = K.decision_digest()
    dks = r["sections"]["gap_clusters"]["dirty_keys"]
    assert len(dks) >= 1
    assert any("DESTEER_PARTIAL" in d["raw_key"] for d in dks)
    assert all(d["dirty_key"] is True for d in dks)


def test_one_page_numbers_match_sections():
    r = K.decision_digest()
    g = r["sections"]["gap_clusters"]["counts"]
    assert ("缺口%d" % r["by_section"]["gap_clusters"]) in r["one_page"]
    assert ("未分类%d" % g["UNCLASSIFIED"]) in r["one_page"]
    assert ("部分%d" % g["PARTIAL"]) in r["one_page"]
    assert ("无定论%d" % g["INCONCLUSIVE"]) in r["one_page"]
    assert sum(r["by_section"].values()) == r["total_decisions"]


# ---------------- G3: 负向注入——非恒真 ----------------

def test_new_partial_key_changes_cluster(monkeypatch):
    """注入新PARTIAL key→聚类计数随之变化,证明非恒真。"""
    _inject_dist(monkeypatch, {"?": 2, "AST_PARTIAL": 3, "X_INCONCLUSIVE": 1})
    r = K.decision_digest()
    g = r["sections"]["gap_clusters"]["counts"]
    assert g["UNCLASSIFIED"] == 2
    assert g["PARTIAL"] == 3
    assert g["INCONCLUSIVE"] == 1
    assert r["by_section"]["gap_clusters"] == 6


def test_injected_dirty_key_flagged(monkeypatch):
    """注入dict字符串化脏key→dirty_key=true且原样保留。"""
    _inject_dist(monkeypatch, {"{'code':'FOO_PARTIAL','claim':'x'}": 4})
    r = K.decision_digest()
    dks = r["sections"]["gap_clusters"]["dirty_keys"]
    assert len(dks) == 1
    assert "FOO_PARTIAL" in dks[0]["raw_key"]
    assert dks[0]["count"] == 4
    assert dks[0]["dirty_key"] is True


def test_weak_evidence_dedup(monkeypatch):
    """注入重复direction→unique_directions去重、occurrences累加。"""
    weak = [
        {"state": "PASS_WEAK_EVIDENCE", "direction": "同一方向", "evidence_tags": []},
        {"state": "PASS_WEAK_EVIDENCE", "direction": "同一方向", "evidence_tags": []},
        {"state": "PASS_WEAK_EVIDENCE", "direction": "另一方向", "evidence_tags": []},
        {"state": "PASS_SUBSTANTIVE", "direction": "不算弱证据", "evidence_tags": ["x"]},
    ]
    _inject_weak(monkeypatch, weak)
    r = K.decision_digest()
    w = r["sections"]["weak_evidence"]
    assert w["total"] == 3
    assert w["unique_directions"] == 2
    by_d = {x["direction"]: x["occurrences"] for x in w["rows"]}
    assert by_d["同一方向"] == 2
    assert by_d["另一方向"] == 1


def test_injected_inbox_meta_only(monkeypatch):
    """注入隔离收件箱→消息清单随注入变化,且正文不出现在任何输出。"""
    d = tempfile.mkdtemp(prefix="digest_test_")
    ib = os.path.join(d, "inbound_inbox.jsonl")
    with open(ib, "w", encoding="utf-8") as f:
        f.write(json.dumps({"at": "2026-11-28T07:00:00Z", "sender": "注入者",
                            "source_tier": "human_operator", "nonce": "N-1",
                            "channel": "test", "consumed": False, "executed": False,
                            "message": "这是绝密正文不应出现在清单"}, ensure_ascii=False) + "\n")
    r = K.decision_digest(inbox_log=ib)
    rows = r["sections"]["inbox_messages"]["rows"]
    assert len(rows) == 1
    assert rows[0]["sender"] == "注入者"
    assert rows[0]["body_read"] is False
    serialized = json.dumps(r, ensure_ascii=False)
    assert "绝密正文" not in serialized
    assert "message" not in rows[0]
