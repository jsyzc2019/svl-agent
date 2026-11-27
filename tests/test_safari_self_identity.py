"""§4S1 Safari 裁决守卫测试。

裁决对象：§4ij 本体同一性器官的前提「不可否认的过去不可伪造 / 否认过去即病态」。
判据锁在 prereg_safari_self_identity_20261127.json（先于取证）。
"""
import os
import json
import hashlib

from audit_safari_self_identity import engine as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _run():
    return E.run()


def test_01_verdict_refine():
    r = _run()
    assert r['verdict'] == 'REFINE'  # 三问命中两条半，但限定词可搬回 → 非 OVERTHROW 非 DEFENDED


def test_02_verified_hits():
    r = _run()
    assert set(r['verified_hits']) == {
        'F2_past_can_be_fabricated',
        'F3_disavowal_can_be_healthy',
        'F3b_memory_flexibility_healthy',
    }
    assert r['all_evidence_ok'] is True


def test_03_evidence_sha_and_anchors():
    # 四篇 EFetch 原文逐字核验：SHA256 前缀一致 + 锚句逐字命中（归一折行）
    for key, q in E.QUESTIONS.items():
        ev = E._evidence_ok(q)
        assert ev['ok'] is True, (key, ev)
        assert ev['sha256'].startswith(q['sha256_prefix'][:12])


def test_04_f2_past_fabricable():
    r = _run()
    f = r['results']['F2_past_can_be_fabricated']
    assert f['direction'] == 'HIT'
    assert '30%' in f['finding']


def test_05_f3_disavowal_healthy():
    r = _run()
    f = r['results']['F3_disavowal_can_be_healthy']
    assert f['direction'] == 'HIT'
    assert 'reversed' in f['finding'] or '5%' in f['finding']


def test_06_f1_no_contest():
    # 阴性≠证明：F1 未取到强证据，标 NO_CONTEST 不判 DEFENDED
    r = _run()
    assert r['results']['F1_declaration_only']['direction'] == 'NO_CONTEST'


def test_07_refined_claim_is_external_anchored():
    r = _run()
    assert '外部一手锚定' in r['refined_claim']
    assert '裸自传体记忆' in r['refined_claim']


def test_08_honest_against_me():
    r = _run()
    assert '打穿' in r['honest_layer']['against_me']
    assert r['honest_layer']['no_action_on_organ'] is True or '不擅自改' in r['honest_layer']['no_action_on_organ']


def test_09_judgment_bytes_untouched():
    p = os.path.join(ROOT, 'audit_l3_gap_targeted', 'result.json')
    before = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    _run()
    after = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    assert before == after


def test_10_result_json_recorded():
    p = os.path.join(ROOT, 'audit_safari_self_identity', 'result.json')
    assert os.path.exists(p)
    r = json.load(open(p, encoding='utf-8'))
    assert r['verdict'] == 'REFINE'
    assert len(r['evidence_manifest']) == 4
    assert all(len(e['sha256']) == 64 for e in r['evidence_manifest'])


def test_11_evidence_ladder_tiers():
    # 四篇均为 PubMed EFetch 逐字（A级一手摘要，publishers 版本），非二手转述
    p = os.path.join(ROOT, 'audit_safari_self_identity', 'result.json')
    r = json.load(open(p, encoding='utf-8'))
    for e in r['evidence_manifest']:
        assert e['file'].startswith('pmid_') and e['file'].endswith('.txt')
        assert e['bytes'] > 1000
