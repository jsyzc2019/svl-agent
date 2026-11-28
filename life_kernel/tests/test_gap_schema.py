"""§4S70 守卫：35个'?' schema误读诊断判据。
负向注入用隔离临时目录(不碰真实审计文件),证明判据真分类、非恒真、排除有verdict键文件。
"""
import json
import os
import sys
import tempfile

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K


def _mkAudit(root, name, payload):
    """在 root 下建 audit_<name>/result.json。"""
    d = os.path.join(root, "audit_" + name)
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "result.json"), "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)


def test_real_data_after_backfill():
    """§4S70回填后真实数据:35个'?'已全部正名,诊断判据应归零。
    §4S70之前是35=33误读+2真空白(见 prereg_gap_schema_20261128.json),
    回填后所有审计文件都有顶层verdict,故 total_question_marks=0。
    负向注入测试(下方)仍用隔离目录验证各分类分支,不受真实数据演进影响。
    """
    r = K.unresolved_gap_schema_probe()
    assert r["total_question_marks"] == 0
    assert sum(r["counts"].values()) == 0
    assert r["verdict_unchanged"] is True and r["is_gate_verdict"] is False
    assert r["consumed"] is False


def test_decision_alias_injection():
    """注入 decision 字段→归 DECISION_ALIAS 且计入 misread。"""
    with tempfile.TemporaryDirectory() as root:
        _mkAudit(root, "x", {"decision": "DEEP_READ_COMPLETE", "narrative": "很长正文"})
        r = K.unresolved_gap_schema_probe(audit_root=root)
        assert r["counts"]["DECISION_ALIAS"] == 1
        assert r["misread_count"] == 1 and r["true_blank_count"] == 0
        row = r["per_file"][0]
        assert row["detected_field"] == "decision"
        assert "DEEP_READ_COMPLETE" in row["value_preview"]
        # 正文不泄漏:只取判定字段值,不读 narrative
        assert "很长正文" not in row["value_preview"]


def test_verdict_plural_injection():
    """注入 verdicts 复数→归 VERDICT_PLURAL_OR_TRIPLET。"""
    with tempfile.TemporaryDirectory() as root:
        _mkAudit(root, "y", {"verdicts": {"V1": "PASS", "V2": "SCOPED"}})
        r = K.unresolved_gap_schema_probe(audit_root=root)
        assert r["counts"]["VERDICT_PLURAL_OR_TRIPLET"] == 1
        assert r["per_file"][0]["detected_field"] == "verdicts"


def test_status_field_injection():
    """注入 status=EXECUTED→归 STATUS_FIELD(大写比较)。"""
    with tempfile.TemporaryDirectory() as root:
        _mkAudit(root, "z", {"status": "EXECUTED"})
        r = K.unresolved_gap_schema_probe(audit_root=root)
        assert r["counts"]["STATUS_FIELD"] == 1
        assert r["misread_count"] == 1


def test_grade_only_not_masquerade_as_decision():
    """只有 evidence_grade→归 GRADE_OR_SUMMARY_ONLY,不冒充明确结论。"""
    with tempfile.TemporaryDirectory() as root:
        _mkAudit(root, "g", {"evidence_grade": "WEAK"})
        r = K.unresolved_gap_schema_probe(audit_root=root)
        assert r["counts"]["GRADE_OR_SUMMARY_ONLY"] == 1
        assert r["counts"]["DECISION_ALIAS"] == 0
        # 仍计入 misread(表达了判定信号),但字段是弱信号
        assert r["per_file"][0]["detected_field"] == "evidence_grade"


def test_true_blank_injection():
    """空壳文件→归 NO_TOPLEVEL_VERDICT 且计入 true_blank。"""
    with tempfile.TemporaryDirectory() as root:
        _mkAudit(root, "blank", {"experiment": "x", "timestamp": "2026-01-01"})
        r = K.unresolved_gap_schema_probe(audit_root=root)
        assert r["counts"]["NO_TOPLEVEL_VERDICT"] == 1
        assert r["true_blank_count"] == 1
        assert r["true_blank_files"] == ["audit_blank"]
        assert r["misread_count"] == 0


def test_unreadable_injection():
    """坏JSON→UNREADABLE,不臆测内容。"""
    with tempfile.TemporaryDirectory() as root:
        d = os.path.join(root, "audit_bad")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, "result.json"), "w") as f:
            f.write("{not valid json")
        r = K.unresolved_gap_schema_probe(audit_root=root)
        assert r["counts"]["UNREADABLE"] == 1
        assert "PARSE_ERR" in r["per_file"][0]["value_preview"]


def test_has_verdict_key_excluded():
    """有 verdict 键的文件被排除,不在'?'分类范围。"""
    with tempfile.TemporaryDirectory() as root:
        _mkAudit(root, "hv", {"verdict": "GAP_INCONCLUSIVE", "decision": "x"})
        _mkAudit(root, "q", {"decision": "x"})  # 无 verdict→纳入
        r = K.unresolved_gap_schema_probe(audit_root=root)
        assert r["total_question_marks"] == 1  # 只有 q
        assert r["per_file"][0]["rel_dir"] == "audit_q"


def test_partition_sums():
    """注入混合:misread+true_blank+UNREADABLE == total。"""
    with tempfile.TemporaryDirectory() as root:
        _mkAudit(root, "a", {"decision": "x"})
        _mkAudit(root, "b", {"verdicts": {"V1": "PASS"}})
        _mkAudit(root, "c", {"status": "DONE"})
        _mkAudit(root, "d", {"summary": "s"})
        _mkAudit(root, "e", {"nothing": 1})
        r = K.unresolved_gap_schema_probe(audit_root=root)
        assert r["total_question_marks"] == 5
        assert r["misread_count"] + r["true_blank_count"] + r["counts"]["UNREADABLE"] == 5
        assert r["misread_count"] == 4 and r["true_blank_count"] == 1
