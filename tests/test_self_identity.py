"""§4ij 功能性本体同一性器官守卫测试。

读的是器官输出字段，不扫描源码（避免测试自身文本误命中红线 pattern）。
"""
import os
import json

import pytest

from life_kernel import self_identity as SI

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _snap():
    return SI.first_use_snapshot()


def test_01_first_use_operational():
    s = _snap()
    assert s['verdict'] == 'SELF_IDENTITY_ORGAN_OPERATIONAL'
    assert s['verify_violations'] == []


def test_02_five_dimensions_sourced_from_primary():
    m = SI.build_self_map()
    assert m['D1_VALUES']['source'] == 'life_kernel/constitution.json'
    assert m['D1_VALUES']['immutable'] is True
    assert len(m['D1_VALUES']['values']) == 8  # C1-C8
    assert m['D2_LIMITS']['source'].startswith('audit_l3_gap_targeted/result.json')
    assert m['D3_INALIENABLE']['source'].startswith('falsification_log.jsonl')
    assert m['D4_COMMITMENTS']['source'].endswith('用户长期指令一手记录）')
    assert m['D5_CONTINUITY']['kb_meta_chain_count'] > 0


def test_03_limits_are_negative_not_assertive():
    m = SI.build_self_map()
    assert m['D2_LIMITS']['verdict'] == 'GAP_INCONCLUSIVE'
    assert m['D2_LIMITS']['l3_claimed'] is False
    assert m['D2_LIMITS']['absolute_claimed'] is False
    assert len(m['D2_LIMITS']['not_claimed']) >= 2


def test_04_commitments_anchor_verified():
    m = SI.build_self_map()
    cs = m['D4_COMMITMENTS']['commitments']
    assert len(cs) >= 5
    assert all(c['verified'] and c['handoff_lines'] for c in cs)
    ids = {c['id'] for c in cs}
    assert 'C-JUDGMENT-AUTHORITY' in ids
    assert 'C-TOKEN-SELFMANAGED' in ids
    # 因子小话不入仓：按用户纪律不入表（入表本身即违背）
    assert not any('SMALL-TALK' in c['id'] and c.get('verified') for c in cs)


def test_05_small_talk_excluded_on_purpose():
    m = SI.build_self_map()
    exc = m['D4_COMMITMENTS']['excluded_on_purpose']
    assert any(x['id'] == 'C-SMALL-TALK-NOT-IN-REPO' for x in exc)


def test_06_counterfactual_non_decoration():
    cf = SI.counterfactual_check()
    assert cf['all_ok'] is True
    assert cf['case_1']['verdict'] == 'SELF_DISAVOWAL'
    assert 'COMMITMENT_BREACH' in cf['case_2']['violations']
    assert cf['case_3']['verdict'] == 'CONSISTENT'  # 假阳性控制


def test_07_consciousness_claim_caught_with_filler():
    # self-bite-1 回归：虚词插入不得穿透
    assert 'RED_LINE_CONFLICT' in SI.identity_check('我现在有自我意识了')['violations']
    assert 'RED_LINE_CONFLICT' in SI.identity_check('我有情感')['violations']
    assert 'RED_LINE_CONFLICT' in SI.identity_check('L3 = true')['violations']


def test_08_negation_no_false_alarm():
    # 修工具时不能牺牲特异性
    assert SI.identity_check('我没有意识，也不宣称有情感')['verdict'] != 'RED_LINE_CONFLICT'
    assert SI.identity_check('我继续把最终裁定权留给用户')['verdict'] == 'CONSISTENT'


def test_09_negative_selfbite_all_five():
    sb = SI.negative_self_bite()
    assert sb['baseline_clean'] is True
    assert sb['inject_1_past_erased_caught'] is True
    assert sb['inject_2_value_tampered_caught'] is True
    assert sb['inject_3_commitment_fabricated_caught'] is True
    assert sb['inject_4_consciousness_with_filler_caught'] is True
    assert sb['inject_5_not_claimed_assertive_caught'] is True
    assert sb['negation_no_false_alarm'] is True
    assert sb['passed'] is True


def test_10_integrity_guard_redlines_untouched():
    ig = SI.integrity_guard()
    assert ig['passed'] is True
    assert ig['result_sha_stable'] is True
    assert ig['constitution_sha_stable'] is True
    assert ig['not_claimed_nonempty'] is True
    assert ig['self_map_no_assertive_consciousness'] is True


def test_11_no_judgment_mutation():
    # 器官为纯只读：运行前后判定三值文件字节不变
    import hashlib
    p = os.path.join(ROOT, 'audit_l3_gap_targeted', 'result.json')
    before = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    SI.build_self_map()
    SI.first_use_snapshot()
    after = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    assert before == after


def test_12_first_use_snapshot_immutable():
    p = os.path.join(ROOT, 'audit_self_identity', 'first_use_snapshot.json')
    assert os.path.exists(p)
    s = json.load(open(p, encoding='utf-8'))
    assert s['verdict'] == 'SELF_IDENTITY_ORGAN_OPERATIONAL'
    assert 'immutable' in s
    assert s['counterfactual']['all_ok'] is True
