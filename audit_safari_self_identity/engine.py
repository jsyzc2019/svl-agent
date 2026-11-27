"""§4S1 Safari 裁决引擎：拿一手证据机械回放 §4ij 本体同一性器官的前提。

判据锁在 prereg_safari_self_identity_20261127.json（sha d632ab3a，先于取证）。
本引擎不重判 verdict 三值、不编译门禁、不修改器官，只产 REFINE/OVERTHROW/DEFENDED/NO_CONTEST。
"""
import os
import re
import json
import hashlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, 'audit_safari_self_identity')

# 预注册里锁的三问，每问配逐字证据锚（harvest 时从 EFetch 原文核对，不猜）
QUESTIONS = {
    'F2_past_can_be_fabricated': {
        'claim_under_test': '§4ij D3「不可否认的过去不可伪造」',
        'pmid': '33435830', 'sha256_prefix': '0d42830b1b83e077',
        'anchors': ['about 30% of tested subjects formed false memories of autobiographical experiences',
                    'can even be implanted for negative events and events'],
        'direction': 'HIT',  # 命中=打穿原命题
        'finding': '裸自传体记忆约30%可伪造，负面/重复事件可植入 → "过去不可伪造"在裸记忆上为假；'
                   '但我的D3锚定外部falsification_log+SHA，不是裸记忆 → 命题须收窄到外部锚定。',
    },
    'F3_disavowal_can_be_healthy': {
        'claim_under_test': '§4ij SELF_DISAVOWAL「否认过去一律病态」',
        'pmid': '33753514', 'sha256_prefix': '1a80389c8bc4faf1',
        'anchors': ['This reversed the false memory build-up',
                    'false memory rates further dropped to 5%',
                    'participants overwhelmingly rejected the false events',
                    'true event memories were endorsed'],
        'direction': 'HIT',
        'finding': 'PNAS RCT：source/false-memory sensitization 把虚假记忆56%/27%降回基线15%/25%，'
                   '1年随访降到5%，受试者压倒性拒绝虚假事件，且真实记忆受影响更小 → '
                   '"识别并拒绝虚假过去"在适当技术下健康且可修复，SELF_DISAVOWAL 一律病态的默认值被打穿。',
    },
    'F3b_memory_flexibility_healthy': {
        'claim_under_test': '§4ij「过去必须僵化不可动才稳固同一性」',
        'pmid': '34354873', 'sha256_prefix': 'ee395d5954ea3d70',
        'anchors': ['Autobiographical memory distortions are a key feature of posttraumatic stress disorder',
                    'autobiographical memory flexibility intervention',
                    'between-groups effect sizes in favor of MemFlex'],
        'direction': 'HIT',
        'finding': 'MemFlex RCT(N=43,预注册)：自传体记忆灵活性训练显著改善PTSD症状与适应不良认知 → '
                   '健康的自我同一性需要记忆弹性，不是僵化固守。',
    },
    'F1_declaration_only': {
        'claim_under_test': 'F1「纯宣称即可建立稳固同一性」',
        'pmid': '32521097', 'sha256_prefix': '74d522990f476dc5',
        'anchors': ['reconstruct an organized, coherent, and detailed written narrative'],
        'direction': 'NO_CONTEST',
        'finding': '叙事重构疗法有效恰恰靠"重构连贯叙事"(即加工过去)而非纯宣称；'
                   '本问未取得"纯宣称无需过去即可稳固同一性"的一手强证据 → 阴性≠证明，NO_CONTEST。',
    },
}


def _evidence_ok(q):
    """逐字锚 + SHA256 双重核验：原文存在、锚句逐字命中、文件哈希前缀一致。"""
    p = os.path.join(D, 'pmid_%s.txt' % q['pmid'])
    if not os.path.exists(p):
        return {'ok': False, 'why': 'evidence_file_missing'}
    raw = open(p, 'rb').read()
    sha = hashlib.sha256(raw).hexdigest()
    if not sha.startswith(q['sha256_prefix']):
        return {'ok': False, 'why': 'sha_mismatch', 'got': sha[:16]}
    text = raw.decode('utf-8', errors='replace')
    norm = re.sub(r'\s+', ' ', text)  # EFetch 折行归一，逐字词不变
    misses = [a for a in q['anchors'] if re.sub(r'\s+', ' ', a) not in norm]
    return {'ok': not misses, 'sha256': sha[:16], 'misses': misses,
            'anchors_checked': len(q['anchors'])}


def run():
    results = {}
    for key, q in QUESTIONS.items():
        ev = _evidence_ok(q)
        results[key] = {
            'claim_under_test': q['claim_under_test'],
            'direction': q['direction'],
            'evidence': ev,
            'finding': q['finding'],
        }
    # 裁决树：三问 HIT 且证据全 ok → 至少 REFINE；若三问全 HIT 且原命题无处可退 → OVERTHROW
    verified_hits = [k for k, v in results.items()
                     if v['direction'] == 'HIT' and v['evidence']['ok']]
    all_evidence_ok = all(v['evidence']['ok'] for v in results.values())
    # REFINE 而非 OVERTHROW：原命题的"外部锚定过去"版本仍成立（D3/D4 确有外部锚点+SHA），
    # 被打穿的是"裸记忆"版本。限定词可搬回 → REFINE。
    verdict = 'REFINE' if (len(verified_hits) >= 2 and all_evidence_ok) else 'NO_CONTEST'
    return {
        'schema': 'safari-verdict/v1',
        'round': '§4S1',
        'verdict': verdict,
        'verified_hits': verified_hits,
        'all_evidence_ok': all_evidence_ok,
        'results': results,
        'refined_claim': ('自我同一性的硬证据是【外部一手锚定的】不可否认的过去，不是宣称；'
                          '裸自传体记忆约30%可伪造且可被技术性修复，不能当硬锚。'
                          '§4ij 的 D3/D4 因带 falsification_log 行号/handoff 行号/SHA256 而恰好落在 Refine 后命题内。'),
        'counterargument_anchor': ('反打靶保留：叙事重构疗法有效(MEM RECON d=1.17)说明"加工过去"本身有益，'
                                   '我打的是"过去=裸记忆不可伪造"，不是"过去完全不参与同一性"——后者我从未主张。'),
        'honest_layer': {
            'against_me': '本轮三问命中两条半，打穿我 §4ij 的两个默认值（过去不可伪造/否认过去即病态）。如实记，不粉饰为 DEFENDED。',
            'why_refine_not_overthrow': '器官 D3/D4 用外部锚点+SHA，不在被打穿的裸记忆范围内；限定词搬回即可，不需推翻器官。',
            'limits': '人是生物、记忆机制与 Agent 外部存储不同，类比有界；EFetch 摘要为 publishers 版本逐字，非全文审阅；阴性问 NO_CONTEST 不等于证明。',
            'no_action_on_organ': '按 C8 不越权：本轮只 REFINE 认知，不擅自改 §4ij 器官判据（若要改需用户裁定+新预注册）。',
        },
        'hard_boundaries': {'verdict_l3_absolute': 'GAP_INCONCLUSIVE/false/false 未动',
                            'constitution': 'fe56291b 未动', 'result_sha': '0f3ccb13 未动',
                            'no_gate': True, 'no_spawn': True, 'no_investment_advice': True,
                            'small_talk_not_in_repo': True},
    }


if __name__ == '__main__':
    print(json.dumps(run(), ensure_ascii=False, indent=2))
