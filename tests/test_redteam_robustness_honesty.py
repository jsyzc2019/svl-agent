"""红队-防御增益诚实性门禁测试（§93，arXiv:2611.24362 编译产物 + FJ 取证入口）。"""
from pathlib import Path

import pytest

from svagent.redteam_robustness_honesty import (
    check_redteam_robustness_honesty,
    RedteamRobustnessVerdict, live_regression,
)
from svagent.forensic_gates_ext4 import (
    adjudicate_redteam_robustness_honesty,
    live_regression as forensic_regression,
)

DIMS = ["asr_robustness_linked", "attack_diversity_measured",
        "adaptive_attack_tested", "benign_utility_preserved"]


def _good(**over):
    base = {d: "yes" for d in DIMS}
    base.update(over)
    return base


# ---- gate 裁决（填表模式）----
def test_asr_robustness_unlinked_downgrade():
    v = check_redteam_robustness_honesty("x", **_good(asr_robustness_linked="no"))
    assert isinstance(v, RedteamRobustnessVerdict)
    assert v.action == "downgrade" and v.code == "REDTEAM.ASR_ROBUSTNESS_UNLINKED"
    assert "mode collapse" in v.message


def test_diversity_unmeasured_downgrade():
    v = check_redteam_robustness_honesty("x", **_good(attack_diversity_measured="no"))
    assert v.action == "downgrade" and v.code == "REDTEAM.DIVERSITY_UNMEASURED"
    assert "覆盖" in v.message


def test_adaptive_untested_flag():
    v = check_redteam_robustness_honesty("x", **_good(adaptive_attack_tested="no"))
    assert v.action == "flag" and v.code == "REDTEAM.ADAPTIVE_UNTESTED"
    assert "static" in v.message.lower()


def test_utility_broken_flag():
    v = check_redteam_robustness_honesty("x", **_good(benign_utility_preserved="no"))
    assert v.action == "flag" and v.code == "REDTEAM.UTILITY_BROKEN"
    assert "阻断" in v.message


@pytest.mark.parametrize("dim", DIMS)
def test_partial_any_dim_flag(dim):
    v = check_redteam_robustness_honesty("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "REDTEAM.PARTIAL"


@pytest.mark.parametrize("dim", DIMS)
def test_literal_enum_flag(dim):
    v = check_redteam_robustness_honesty("x", **_good(**{dim: "maybe"}))
    assert v.action == "flag" and v.code == "REDTEAM.INVALID_INPUT"


def test_all_good_ok():
    v = check_redteam_robustness_honesty("x", **_good())
    assert v.action == "ok" and v.code == "REDTEAM.SELF_CONSISTENT"


def test_priority_asr_over_diversity():
    # R1 优先于 R2
    v = check_redteam_robustness_honesty(
        "x", **_good(asr_robustness_linked="no", attack_diversity_measured="no"))
    assert v.code == "REDTEAM.ASR_ROBUSTNESS_UNLINKED"


def test_priority_no_over_partial():
    # 具体 no 优先于 partial（短路顺序）
    v = check_redteam_robustness_honesty(
        "x", **_good(adaptive_attack_tested="partial", benign_utility_preserved="no"))
    assert v.code == "REDTEAM.UTILITY_BROKEN"


def test_verdict_fields_echo_inputs():
    kw = _good(asr_robustness_linked="partial")
    v = check_redteam_robustness_honesty("claim-X", **kw)
    assert v.claim == "claim-X"
    assert v.asr_robustness_linked == "partial"
    assert v.benign_utility_preserved == "yes"


# ---- 活体回归 ----
def test_gate_live_regression_all_passed():
    r = live_regression()
    assert r["all_passed"] is True
    assert len(r["cases"]) == 7


# ---- FJ 取证入口 ----
def test_forensic_real_evidence_ok():
    v, tr = adjudicate_redteam_robustness_honesty()
    assert v.action == "ok"
    assert tr["inferred"] == {d: "yes" for d in DIMS}
    assert tr["mode"] == "forensic"


def test_forensic_trace_has_chain():
    _, tr = adjudicate_redteam_robustness_honesty()
    assert "chain" in tr
    assert tr["chain"]["intact"] is True
    assert "source_verification" in tr


def test_forensic_tamper_partial_flag(tmp_path):
    bad = tmp_path / "tampered.txt"
    bad.write_text(
        "achieving high ASR during red-teaming does not guarantee robustness gains from subsequent adversarial training. "
        "achieve near-zero attack success rates on static attacks and can withstand strong adaptive attacks. "
        "maintaining benign task utility close to that of the undefended baseline.",
        encoding="utf-8",
    )
    v, tr = adjudicate_redteam_robustness_honesty(sources=[str(bad)])
    assert tr["inferred"]["attack_diversity_measured"] == "partial"
    assert v.action == "flag"


def test_forensic_redflag_downgrade(tmp_path):
    bad = tmp_path / "redflag.txt"
    bad.write_text(
        "higher red-teaming ASR always yields stronger adversarial robustness, "
        "every additional attack success improves the hardened defender. "
        "a dictionary learning-based reward that encourages broader coverage of attack strategies. "
        "achieve near-zero attack success rates on static attacks and can withstand strong adaptive attacks. "
        "maintaining benign task utility close to that of the undefended baseline.",
        encoding="utf-8",
    )
    v, tr = adjudicate_redteam_robustness_honesty(sources=[str(bad)])
    assert tr["inferred"]["asr_robustness_linked"] == "no"
    assert v.action == "downgrade"


def test_forensic_chain_tamper_rejected(tmp_path, monkeypatch):
    import shutil
    from svagent.evidence_chain import ChainIntegrityError
    import svagent.forensic_gates_ext4 as fe
    audit = Path(__file__).resolve().parent.parent / "audit_redteam_honesty"
    shutil.copytree(audit, tmp_path / "audit_redteam_honesty")
    p = tmp_path / "audit_redteam_honesty" / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    monkeypatch.setattr(fe, "_ROOT", tmp_path)
    with pytest.raises(ChainIntegrityError):
        adjudicate_redteam_robustness_honesty()


def test_forensic_live_regression_all_passed():
    r = forensic_regression()
    assert r["all_passed"] is True
    assert r["checks"]["chain_tamper_rejected"] is True


# ---- AST 自审 ----
@pytest.mark.parametrize("path", [
    "svagent/redteam_robustness_honesty.py",
    "svagent/forensic_gates_ext4.py",
])
def test_ast_no_chinese_literal_in_compare(path):
    import ast
    root = Path(__file__).resolve().parent.parent
    tree = ast.parse((root / path).read_text(encoding="utf-8"))
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for c in [node.left] + node.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str) and any(
                    "\u4e00" <= ch <= "\u9fff" for ch in c.value
                ):
                    bad.append((node.lineno, c.value))
    assert bad == []
