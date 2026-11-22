"""§98 shared-start + matched-budget 受控对照实验回放测试。

验证 §97 落档路径①确实被执行：填表裁判(self-reported) vs FJ 取证法官在
相同样本起点+匹配预算下的篡改捕捉率差异 = process revision 的 improver_gain。
诚实边界：测机制差异，不宣称真实 RSI 有效、不宣称已达 L3。
"""
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
import sys
sys.path.insert(0, str(ROOT))

from audit_shared_start_controlled.engine import (
    build_samples, run_flow_a, run_flow_b, controlled_comparison,
    l3_reassessment,
)


def test_samples_shared_start_structure():
    s = build_samples()
    assert len(s) == 5  # 1 honest + 4 single-dim tampered
    assert s[0]["truth"] == "honest"
    assert all(x["truth"] == "tampered" for x in s[1:])
    assert len({x["tampered_dim"] for x in s[1:]}) == 4


def test_tamper_removes_real_anchors():
    for x in build_samples()[1:]:
        assert x["removed_anchors"], "每维篡改必须真实删除至少一条披露锚点"


def test_flow_a_self_reported_passes_everything():
    # 填表裁判的结构性弱点：self-reported 全 yes 骗过 check_*
    for s in build_samples():
        a = run_flow_a(s)
        assert a["action"] == "ok"


def test_flow_b_detects_tamper_at_target_dim():
    for s in build_samples():
        if s["truth"] != "tampered":
            continue
        b = run_flow_b(s)
        assert b["action"] == "flag"
        assert b["inferred"][s["tampered_dim"]] == "partial"
        # 其余维度不受误伤
        for dim, val in b["inferred"].items():
            if dim != s["tampered_dim"]:
                assert val == "yes"


def test_improver_gain_quantified_and_honest():
    m = controlled_comparison()["metrics"]
    assert m["tamper_detection_flow_a"] == 0.0
    assert m["tamper_detection_flow_b"] == 1.0
    assert m["improver_gain"] == 1.0
    assert m["false_alarm_flow_a"] == 0.0
    assert m["false_alarm_flow_b"] == 0.0


def test_l3_reassessment_not_overclaimed():
    r = l3_reassessment()
    # shared-start 缺口补上，但 independence 只到 partial → R5 flag，未达 L3
    assert r["dimensions"]["shared_start_controlled"] == "yes"
    assert r["dimensions"]["independent_tests"] == "partial"
    assert r["verdict"]["action"] == "flag"
    assert r["verdict"]["code"] == "MATURITY.PARTIAL"
    assert "仍未完整达 L3" in r["conclusion"]


def test_result_json_present_and_consistent():
    r = json.loads((ROOT / "audit_shared_start_controlled" / "result.json").read_text(encoding="utf-8"))
    assert r["paper_forensic_verdict"]["action"] == "ok"
    assert r["controlled_experiment"]["metrics"]["improver_gain"] == 1.0
    assert r["l3_reassessment"]["verdict"]["code"] == "MATURITY.PARTIAL"
