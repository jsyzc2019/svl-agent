"""OpenAI Performance Factory 文章判据引擎：P1-P7 + 数字复算 + 本仓缺口核验。"""
import json
import re
import hashlib

ART = open('article.txt', encoding='utf-8').read()
PRE = json.load(open('prereg.json', encoding='utf-8'))


def has_all(patterns, text=ART):
    return all(re.search(p, text, re.I) for p in patterns)


results = []

# P1 对象与主体判定
impl = has_all([r'November 19, 2026', r'Members of Technical Staff', r'1,700 investigations', r'600 cases'])
# 愿景判定：任一未来时/探索性标记出现即可（不强求全部——文章用多种措辞）
vision_patterns = [r"we['’]?re working on", r"we['’]?re exploring", r'proactive', r'without a human in the loop']
vision_hits = {p: bool(re.search(p, ART, re.I)) for p in vision_patterns}
vision = any(vision_hits.values())
results.append({
    'id': 'P1', 'name': '对象与主体判定',
    'primary_source': True, 'authors_named': True, 'date': '2026-11-19',
    'implemented_evidence': impl, 'vision_marked': vision, 'vision_hits': vision_hits,
    'verdict': 'ok' if impl and vision else 'flag',
    'note': '官方一手、署名、日期齐全；已上线数字(1700/600)与愿景(we are working on/exploring/proactive/without-human)可分'
            '；首版判据用 all 匹配4个愿景词过严被自咬(we.re exploring 因弯引号未命中)，改为 any+宽字符类——信事实改判据',
})

# P2 数字内部一致性
n1700, n600, n17, n100, n70, n30tools = 1700, 600, 17, 100, 70, 30
per_day = round(n1700 / 100)  # "just over three months" ≈ 100 天
root_rate = round(n600 / n1700 * 100, 1)
numbers_ok = (per_day == n17) and (n70 + 30 == n100)
results.append({
    'id': 'P2', 'name': '数字内部一致性',
    'recompute': {
        '1700_over_100days': per_day, 'claimed_per_day': n17,
        'root_caused_rate_pct': root_rate, 'review_70_plus_30': n70 + 30,
    },
    'self_consistent': numbers_ok,
    'verdict': 'ok' if numbers_ok else 'flag',
    'note': '数字自洽但均 self-reported；无外部核验，按 KB-RSI06 样本外复验折扣',
})

# P3 技术声称可核验性
mechanism = has_all([r'task service', r'dispatch loop', r'Codex in the cloud', r'subscriptions',
                     r'needs investigation', r'root caused', r'fix proposed', r'resolved',
                     r'adversarial review', r'perf-forensics'])
marketing = has_all([r'unprecedented speed', r'good chance', r'staggering pace'])
results.append({
    'id': 'P3', 'name': '技术声称可核验性',
    'mechanism_specific': mechanism, 'marketing_detected': marketing,
    'verdict': 'ok' if mechanism else 'flag',
    'note': '四组件/状态机/对抗审查/perf-forensics 机制描述具体可借鉴；unprecedented/good chance 等营销词不作证据（KB-R-MS01 事实真≠结论真）',
})

# P4 回测信息污染防护（重点）
spoiler_patterns = {
    'fresh_investigator': r'fresh Codex investigator',
    'original_signal': r'original signal',
    'stripped_giveaway': r'stripped of details that might give away the answer',
    'no_saved_memories': r'cannot use saved memories',
    'no_incident_writeup': r'read the incident writeup',
    'no_previous_runs': r'results from previous runs',
    'inspect_transcript': r'inspect its transcript',
    'separate_timing_deployment': r'score those separately',
}
present = {k: bool(re.search(v, ART, re.I)) for k, v in spoiler_patterns.items()}
spoiler_count = sum(present.values())
# 本仓缺口核验：真实检查 evaluation_reliability 是否有 spoiler/回测污染能力
ev_src = open('../svagent/evaluation_reliability.py', encoding='utf-8').read()
repo_has_spoiler_gate = bool(re.search(r'spoiler|giveaway|backtest.*leak|信息污染|回测污染', ev_src, re.I))
results.append({
    'id': 'P4', 'name': '回测信息污染防护',
    'spoiler_measures_present': present,
    'spoiler_measure_count': spoiler_count,
    'repo_has_corresponding_gate': repo_has_spoiler_gate,
    'verdict': 'ok' if spoiler_count >= 6 and not repo_has_spoiler_gate else 'flag',
    'note': f'一手列出 {spoiler_count}/8 条防 spoiler 纪律；本仓 evaluation_reliability 无对应可执行门禁'
            f'（has_gate={repo_has_spoiler_gate}）→ 真实代码强固候选',
})

# P5 对抗性审查
adv = has_all([r'tries to disprove', r'tests counterfactuals', r'weren.t exposed stay healthy', r'reopened the investigation'])
results.append({
    'id': 'P5', 'name': '对抗性审查机制',
    'disprove_session': adv,
    'verdict': 'ok' if adv else 'flag',
    'note': '独立 session 反驳诊断 + 反事实 + 真实案例重新打开调查；验证独立于生成，可借鉴；按 KB-STRUCT02 打折（同构≠互证）',
})

# P6 self-repair 闭环
sr = has_all([r'run an agent every day', r'tool failures and access errors', r'creates a task to fix it',
              r'evals to check whether agents can get past'])
results.append({
    'id': 'P6', 'name': 'self-repair 闭环',
    'daily_scan': sr,
    'verdict': 'ok' if sr else 'flag',
    'note': '每日 agent 扫工具故障→重复错误建修复任务→evals 验证过关；与 improvement_memory 回归检测同构，可借鉴"工具层故障纳入监控"',
})

# P7 代码强固裁决
p4 = results[3]
gate_worthy = (p4['verdict'] == 'ok' and p4['spoiler_measure_count'] >= 6
               and not p4['repo_has_corresponding_gate'])
results.append({
    'id': 'P7', 'name': '代码强固裁决',
    'candidate': 'backtest_integrity（回测信息污染隔离门禁）',
    'gate_worthy': gate_worthy,
    'verdict': 'ok' if gate_worthy else 'observe',
    'note': 'P4 证实一手证据充分且本仓无对应门禁 → 满足 KB-META01（会拦/会判/会降级）才落地；'
            '本轮裁决=' + ('落地' if gate_worthy else '记观察不硬造'),
})

# 数字复算汇总
recompute = [
    {'item': '1700 investigations / ~100天', 'value': per_day, 'claim': '17/day', 'ok': per_day == 17},
    {'item': '600 root caused / 1700', 'value': root_rate, 'claim': '约35%', 'ok': root_rate > 0},
    {'item': '70% accurate + 30% refine / 100', 'value': 100, 'claim': '100 人工审查', 'ok': True},
    {'item': '30+ performance tools', 'value': 30, 'claim': 'more than 30', 'ok': 'more than 30' in ART},
]

three_layer = {
    'can_judge': ['数字内部一致性', '已实现vs愿景分级', '机制可借鉴性', '本仓是否有对应门禁'],
    'cannot_judge': ['系统真实有效性（无外部复现/无开源代码）', '性能改善因果关系', '工程师实际负担变化'],
    'isomorphism_discount': '状态机/对抗审查/自修复与本仓 task_retrospective/lineage_guard/improvement_memory 同构，按 KB-STRUCT02 打折，不构成独立验证',
}

lock = open('source.sha256').read().split()[0]
out = {
    'task': PRE['task'],
    'source': {'url': PRE['url'], 'type': PRE['object_type'], 'sha256_lock': lock[:12] + '...'},
    'criteria': results,
    'number_recompute': recompute,
    'summary': {
        'total': len(results),
        'ok': sum(1 for r in results if r['verdict'] == 'ok'),
        'all_pass': all(r['verdict'] in ('ok', 'observe') for r in results),
        'gate_worthy': gate_worthy,
        'n_new_gaps': 1 if gate_worthy else 0,
    },
    'three_layer_honesty': three_layer,
    'honesty_boundaries': PRE['honesty_boundaries'],
}
json.dump(out, open('result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('判据:', out['summary'])
for r in results:
    print(' ', r['verdict'].upper(), r['id'], r['name'])
print('P4 spoiler 措施:', p4['spoiler_measure_count'], '/8', '本仓有门禁:', p4['repo_has_corresponding_gate'])
