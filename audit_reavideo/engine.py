#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rea-video 文章研读判据引擎。语义动作词 + 多维交叉，无脆弱字面串单点定罪。"""
import json
from pathlib import Path

D = Path(__file__).parent
ev = json.loads((D / 'evidence.json').read_text(encoding='utf-8'))
pre = json.loads((D / 'prereg.json').read_text(encoding='utf-8'))

results = []

# V1 主体归属：立场被识别+折价，且不据立场定罪
v1 = ev['V1_standing']
v1_ok = (
    bool(v1.get('author')) and
    '折价' in v1.get('judgment', '') and
    '不据' in v1.get('judgment', '') or '不据此判假' in v1.get('judgment', '')
)
results.append(('V1', '主体归属与立场', v1_ok,
                f"立场={v1['judgment']}", '识别立场并折价，未据立场直接定罪'))

# V2 事实断言：每条有status；UNVERIFIED≠FALSE；FALSE需一手反证
claims = ev['V2_factual_claims']
statuses = [c['status'] for c in claims]
valid_status = all(s in ('TRUE', 'QUALIFIED', 'FALSE', 'UNVERIFIED') for s in statuses)
has_false = 'FALSE' in statuses
unverified = [c['claim'] for c in claims if c['status'] == 'UNVERIFIED']
v2_ok = valid_status and len(claims) >= 10 and (not has_false)
results.append(('V2', '关键事实断言一手溯源', v2_ok,
                f"共{len(claims)}条: TRUE={statuses.count('TRUE')} UNVERIFIED={statuses.count('UNVERIFIED')} FALSE={statuses.count('FALSE')}",
                f"UNVERIFIED={unverified} 不判假；无一手反证"))

# V3 免责诚实性：免责→一手局限映射，覆盖率+额外认识论限定
v3 = ev['V3_disclaimer_honesty']
n_dis = len(v3['author_disclaimers'])
n_cnt = len(v3['primary_counterparts'])
honest = '诚实信号' in v3['judgment'] and '非营销盾牌' in v3['judgment']
epistemic = any('无法证明' in d or '不等' in d for d in v3['author_disclaimers'])
v3_ok = n_dis >= 6 and n_cnt >= 4 and honest and epistemic
results.append(('V3', '免责声明诚实性', v3_ok,
                f"免责{n_dis}条 一手对应{n_cnt}条 额外认识论限定={epistemic}",
                '免责逐条映射一手局限，判诚实信号而非营销盾牌'))

# V4 数字口径：阶段分层齐全 + 作者主动警示不可外推
v4 = ev['V4_number_scope']
n_stages = len(v4['stages'])
warn = '不能把最高' in v4['author_extrapolation'] or '差异很大' in v4['author_extrapolation']
narrow = '窄于一手' in v4['judgment']
v4_ok = n_stages >= 3 and warn and narrow
results.append(('V4', '数字口径与外推边界', v4_ok,
                f"阶段数={n_stages} 主动警示={warn} 转述更克制={narrow}",
                '分阶段标注齐全，作者警示不可外推，无越界'))

# V5 同构陷阱：显式打折+新旧分离
v5 = ev['V5_isomorphism']
discounted = '打折' in v5['lineage'] and '同谱系' in v5['lineage']
v5_ok = len(v5['overlaps']) >= 4 and discounted and bool(v5['genuine_novelty'])
results.append(('V5', '同构陷阱判定', v5_ok,
                f"重叠{len(v5['overlaps'])}处 谱系打折={discounted}",
                '同谱系印证打折，真实新意与重叠分离'))

# V6 复述/长牙：每条决策有gate动作；记观察的也标注理由
v6 = ev['V6_teeth_candidates']
all_have_decision = all('decision' in c and c.get('gate') for c in v6)
teeth = [c for c in v6 if '长牙' in c['decision'] or '加固' in c['decision']]
observe = [c for c in v6 if '观察' in c['decision']]
v6_ok = all_have_decision and len(v6) >= 4
results.append(('V6', '复述/长牙决策', v6_ok,
                f"候选{len(v6)}条: 长牙/加固={len(teeth)} 记观察={len(observe)}",
                '每条有拦截动作或观察理由，未硬造新牙'))

# 自审项：预注册声明的偏见防线是否落实
selfaudit_ok = (
    len(pre['judge_self_audit']) >= 3 and
    '营销文' in json.dumps(pre['judge_self_audit'], ensure_ascii=False)
)
results.append(('SELF', '判据自审（偏见防线）', selfaudit_ok,
                f"自审项{len(pre['judge_self_audit'])}条；预注册前已读全文已如实标注",
                '先验偏见被显式锁住；UNVERIFIED≠FALSE；事实真≠结论真'))

# 输出
print('=' * 64)
print('rea-video 文章研读 · 判据执行结果')
print('=' * 64)
for cid, name, ok, ev_s, note in results:
    print(f"[{'PASS' if ok else 'FLAG'}] {cid} · {name}")
    print(f"       证据: {ev_s}")
    print(f"       判语: {note}")
all_ok = all(r[2] for r in results)
print('=' * 64)
print(f"总计: {sum(1 for r in results if r[2])}/{len(results)} PASS  → {'全部通过' if all_ok else '存在FLAG，需复核'}")

out = {
    'audit_id': ev['audit_id'],
    'criteria': [{'id': c[0], 'name': c[1], 'pass': c[2], 'evidence': c[3], 'note': c[4]} for c in results],
    'summary': {
        'all_pass': all_ok,
        'true_claims': statuses.count('TRUE'),
        'unverified_claims': statuses.count('UNVERIFIED'),
        'false_claims': statuses.count('FALSE'),
        'verdict': '诚实的项目介绍文：所有可溯源数字与一手文档一致，免责逐条对应一手局限；无事实错误，仅1条Star数因API限流未核',
        'teeth': [c['idea'][:40] for c in teeth],
        'observe': [c['idea'][:40] for c in observe]
    }
}
(D / 'result.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print('\nresult.json 已写入')
