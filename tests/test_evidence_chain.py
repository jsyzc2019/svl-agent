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
    # §108 跨集复现确认 + 外部 orchestrator 审计目录加入 → total 50→52 / five_piece 33→34 / 三锁 30→31
    # §110 异厂商 designer 受控实验目录（缺 gate_prereg，受控轮不编译新门禁）→ total 52→53，five_piece/三锁不变
    # §111 准入规则 AST v2 修订验证目录（受控轮不编译门禁）→ total 53→54
    # §112 真正跨厂商 designer 交叉目录（受控轮不编译门禁）→ total 54→55
    # §113 跨集×跨厂商 2×2 闭合目录（受控轮不编译门禁）→ total 55→56，five_piece/三锁不变
    # §114 解释者独立性受控验证目录（受控轮不编译门禁）→ total 56→57，five_piece/三锁不变
    # §115 解释者跨厂商交叉确认目录（受控轮不编译门禁）→ total 57→58，five_piece/三锁不变
    # L3 外家 Agent 全链外置验收目录（计划/契约+验收器，不编译门禁）→ total 58→59，five_piece/三锁不变
    # §L3-R2 缺口定向外置验收目录（契约+验收器+裁决引擎，不编译门禁）→ total 59→60，five_piece/三锁不变
    # §4ao prove_canary_construct_validity 诊断脚本归入 gap_targeted 目录未增审计目录
    # §4ap 构念效度增强集 §100-CE 目录（预注册+回放器，内部受控诊断不编译门禁）→ total 60→61，five_piece/三锁不变
    # §4ge 独立性前提证伪目录（audit_aggregation_dependence，证伪Safari非门禁目录、无五件套）→ total 61→62
    # §4gi 外部时间锚证据快照目录（audit_temporal_anchor，remote_evidence+prereg+result，非五件套）→ total 62→63
    # §4gu 论证取证工作台产品化目录（audit_argument_audit，规则+引擎+验证结果+截图，非五件套）→ total 63→64
    # §4gy vanity 自检反用回自己目录（audit_vanity_selfaudit，预注册+引擎+结果，非五件套）→ total 64→65
    # §4gb 财报构念效度目录（audit_finance_construct_validity，预注册+引擎+结果+候选证伪记录，非五件套）→ total 65→66
    # §4hc 记忆治理审计目录（audit_memory_governance，预注册+引擎+结果，候选不写回，非五件套）→ total 66→67
    # §4hf 裁定回执一致性目录（audit_decision_receipt，首用快照+引擎+结果，非五件套）→ total 67→68
    assert a["total"] == 68
    assert a["five_piece_complete"] == 34
    assert a["three_locks_intact"] == 31
    assert 0 < a["three_locks_intact"] <= a["total"]


def test_live_regression():
    r = live_regression()
    assert r["all_passed"] and all(r["checks"].values())
