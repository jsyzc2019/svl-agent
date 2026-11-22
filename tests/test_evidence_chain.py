"""证据链强制执行测试（阶段3：双格式锁/五件套完整度/失配拒判）。"""
import shutil
import pytest

from svagent.evidence_chain import (
    sha256_file, verify_chain, require_intact, ChainIntegrityError,
    audit_all, live_regression,
)
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent


def test_sha256_file():
    assert len(sha256_file(_ROOT / "audit_evosteer" / "prereg.json")) == 64


def test_single_lock_verified():
    r = verify_chain(_ROOT / "audit_evosteer")
    assert r.five_piece_complete
    assert r.intact
    byname = {c.lock: c for c in r.locks}
    assert byname["prereg.sha256"].kind == "single"
    assert byname["prereg.sha256"].ok


def test_manifest_lock_format_no_false_alarm():
    """清单格式锁（hash␠␠filename）应被识别为 manifest，不误判为失配。"""
    r = verify_chain(_ROOT / "audit_evosteer")
    m = {c.lock: c for c in r.locks}["manifest.sha256"]
    # evosteer manifest 是单行锁
    assert m.kind == "single" and m.ok
    # flashprove 用 source.sha256 清单代 manifest → 如实标注为 manifest_alt
    fp = verify_chain(_ROOT / "audit_flashprove")
    fpm = {c.lock: c for c in fp.locks}
    assert fpm["manifest.sha256"].kind == "manifest_alt"


def test_tamper_detected_and_rejected(tmp_path):
    """篡改 prereg.json → 锁失配 → require_intact 拒判（F2 决定性验收）。"""
    src = _ROOT / "audit_evosteer"
    dst = tmp_path / "audit_x"
    shutil.copytree(src, dst)
    assert require_intact(dst).intact
    p = dst / "prereg.json"
    p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    assert not verify_chain(dst).intact
    with pytest.raises(ChainIntegrityError):
        require_intact(dst)


def test_historical_dir_honestly_marked():
    """历史目录（fg_compare 无 engine/result/prereg）如实标注，不伪造。"""
    r = verify_chain(_ROOT / "audit_fg_compare")
    assert not r.five_piece_complete
    assert "历史证据" in r.integrity_note or "缺" in r.integrity_note


def test_audit_all_counts():
    a = audit_all(str(_ROOT))
    # 每新增一个完整证据目录，total 与 five_piece_complete 各 +1（随仓库成长更新，不放宽）
    assert a["total"] == 45
    assert a["five_piece_complete"] == 28
    assert 0 < a["three_locks_intact"] <= a["total"]


def test_live_regression():
    r = live_regression()
    assert r["all_passed"] and all(r["checks"].values())
