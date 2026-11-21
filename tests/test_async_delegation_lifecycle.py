"""异步/后台委派生命周期门禁测试（§69，11来源异步子Agent谱系编译产物）。"""
import pytest

from svagent.async_delegation_lifecycle import (
    check_async_delegation_lifecycle, AsyncDelegationVerdict, live_regression,
)


def _good(**over):
    base = dict(decoupled="yes", steerable="yes", survives_compaction="yes", completion_notified="yes")
    base.update(over)
    return base


def test_sync_block_downgrade():
    """提交即阻塞、无tracking ID → downgrade（无并发根基，S10 decouple）。"""
    v = check_async_delegation_lifecycle("sync delegator", **_good(decoupled="no"))
    assert isinstance(v, AsyncDelegationVerdict)
    assert v.action == "downgrade" and v.code == "ASYNC_DELEGATION.SYNC_BLOCK"
    assert "并发" in v.message or "阻塞" in v.message


def test_no_steer_downgrade():
    """无中途指令/取消 → downgrade（Synchronous delegation cannot be interrupted）。"""
    v = check_async_delegation_lifecycle("x", **_good(steerable="no"))
    assert v.action == "downgrade" and v.code == "ASYNC_DELEGATION.NO_STEER"


def test_compaction_loss_downgrade():
    """句柄仅存消息、随压缩丢失 → downgrade（non-message state channel 缺失）。"""
    v = check_async_delegation_lifecycle("x", **_good(survives_compaction="no"))
    assert v.action == "downgrade" and v.code == "ASYNC_DELEGATION.COMPACTION_LOSS"


def test_fire_and_forget_flag():
    """完成不主动通知、依赖轮询 → flag（S10 fire-and-forget gap）。"""
    v = check_async_delegation_lifecycle("x", **_good(completion_notified="no"))
    assert v.action == "flag" and v.code == "ASYNC_DELEGATION.FIRE_AND_FORGET"


@pytest.mark.parametrize("dim", ["decoupled", "steerable", "survives_compaction", "completion_notified"])
def test_partial_flag(dim):
    """任一维 partial → flag（覆盖不全，待核）。"""
    v = check_async_delegation_lifecycle("x", **_good(**{dim: "partial"}))
    assert v.action == "flag" and v.code == "ASYNC_DELEGATION.PARTIAL"


@pytest.mark.parametrize("bad", ["maybe", "yes-ish", "true", "1"])
def test_literal_enum_flag(bad):
    """字面串/非法枚举 → flag（拒绝内容判定，避 brittle，KB-AUDIT01）。"""
    v = check_async_delegation_lifecycle("x", **_good(decoupled=bad))
    assert v.action == "flag" and v.code == "ASYNC_DELEGATION.INVALID_INPUT"


def test_all_good_ok():
    """四维全 yes → ok（只判声明自洽，不承诺真高效）。"""
    v = check_async_delegation_lifecycle("well-designed system", **_good())
    assert v.action == "ok" and v.code == "ASYNC_DELEGATION.SELF_CONSISTENT"
    assert "不承诺" in v.message or "存在" in v.message


def test_rule_priority_sync_before_steer():
    """规则优先级：decoupled=no 应先于 steerable=no 命中（R1 先于 R2）。"""
    v = check_async_delegation_lifecycle("x", **_good(decoupled="no", steerable="no"))
    assert v.code == "ASYNC_DELEGATION.SYNC_BLOCK"


def test_rule_priority_steer_before_compaction():
    """R2 先于 R3：都 no 时命中 NO_STEER。"""
    v = check_async_delegation_lifecycle("x", **_good(steerable="no", survives_compaction="no"))
    assert v.code == "ASYNC_DELEGATION.NO_STEER"


def test_rule_priority_compaction_before_notify():
    """R3 先于 R4：都 no 时命中 COMPACTION_LOSS。"""
    v = check_async_delegation_lifecycle("x", **_good(survives_compaction="no", completion_notified="no"))
    assert v.code == "ASYNC_DELEGATION.COMPACTION_LOSS"


def test_invalid_input_priority_over_all():
    """R0 最优先：任一非法枚举即使其它全 no 也先 flag。"""
    v = check_async_delegation_lifecycle("x", **_good(decoupled="maybe", steerable="no", completion_notified="no"))
    assert v.code == "ASYNC_DELEGATION.INVALID_INPUT"


def test_verdict_is_frozen():
    """Verdict 不可变（防事后篡改判定）。"""
    v = check_async_delegation_lifecycle("x", **_good())
    with pytest.raises(Exception):
        v.action = "ok"


def test_lazy_export():
    """惰性导出可从 svagent 顶层访问。"""
    import svagent
    assert svagent.check_async_delegation_lifecycle is check_async_delegation_lifecycle


def test_live_regression_all_passed():
    """7 个活体回归全过（对齐 gate_prereg.json）。"""
    r = live_regression()
    assert r["all_passed"], r["cases"]
    assert len(r["checks"]) == 7


def test_message_language_neutral():
    """判定 message 不含会漂移的中文字面串做比较（brittle 防御留痕）。"""
    v = check_async_delegation_lifecycle("x", **_good(completion_notified="no"))
    # code 为英文枚举，判定逻辑不读 message 内容
    assert v.code == "ASYNC_DELEGATION.FIRE_AND_FORGET"
    assert isinstance(v.message, str) and v.message
