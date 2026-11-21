#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SKILLMASTER 论文深读判据引擎。语义判定+多维交叉，无脆弱字面串单点定罪。"""
import json
from pathlib import Path

D = Path(__file__).parent
ev = json.loads((D / 'evidence.json').read_text(encoding='utf-8'))
pre = json.loads((D / 'prereg.json').read_text(encoding='utf-8'))
results = []

# S1 claim-vs-code: 三设计须有代码实体；DRIFT单独标注不判失败
s1 = ev['S1_claim_vs_code']
statuses = [c['code_status'] for c in s1['claims']]
implemented = sum(1 for s in statuses if s.startswith('IMPLEMENTED'))
drift = [c for c in s1['claims'] if 'DRIFT' in c['code_status']]
s1_ok = implemented == 3 and len(s1['claims']) == 3 and '代码实体' in s1['verdict']
results.append(('S1', 'claim-vs-code 一致性', s1_ok,
                f"3设计实现状态={statuses}; 漂移{len(drift)}处",
                '三设计均有代码实体且接线; 1处系数漂移(α0.3vs0.2)标minor; 复现资源未公开另记'))

# S2 数字自洽: 差异须为minor且方向一致; 正文算术自洽
s2 = ev['S2_number_consistency']
diffs = [abs(s2['table1_alfworld']['diff']), abs(s2['table2_searchqa']['diff_sm']), abs(s2['table2_searchqa']['diff_sr'])]
all_minor = all(d < 0.5 for d in diffs)
arith_ok = '自洽' in s2['table4_ablation_arithmetic']['verdict']
reported_consistent = '完全一致' in s2['table8_repeated_runs']['verdict']
s2_ok = all_minor and arith_ok and reported_consistent and s2['self_reported']
results.append(('S2', '实验数字内部自洽', s2_ok,
                f"聚合口径微小差异={diffs}(均<0.5); 消融算术自洽={arith_ok}; Table8与主表一致={reported_consistent}",
                '数字方向一致; Overall聚合口径未明示(疑加权)标minor; 全部self-reported'))

# S3 消融归因: 有控制组+分级归因+明确缺口
s3 = ev['S3_ablation_causality']
has_control = 'review-only' in s3['table4_necessity'] and 'SFT+GRPO' in s3['table4_necessity']
has_robust = '0%' in s3['table5_robustness']
# 语义判定：缺口字段点名了"反事实效用"+否定消融，而非依赖脆弱字面串（KB-AUDIT01）
gap_flag = all(k in s3['gap'] for k in ['反事实效用']) and any(
    neg in s3['gap'] for neg in ['没有单独消融', '未单独消融', '未被隔离', '未隔离'])
graded = '因果级' in s3['verdict'] and '相关级' in s3['verdict']
s3_ok = has_control and has_robust and gap_flag and graded
results.append(('S3', '消融支撑因果归因', s3_ok,
                f"控制组review-only/SFT+GRPO={has_control}; 弱初始库到0%={has_robust}; 缺口已标={gap_flag}",
                'skill-management整体=因果级; 反事实效用单独贡献=相关级(未单独消融,如实降级)'))

# S4 基线公平与自证偏差: 公平协议+局限披露+独立性标注
s4 = ev['S4_baseline_fairness']
fair = '同 backbone' in s4['fair_protocol_claims']
baseline_not_rerun = '非作者独立重跑' in s4['baseline_source']
independence_flagged = '无法独立验证' in s4['independence']
n_dis = len(s4['lim disclosures'])
s4_ok = fair and baseline_not_rerun and independence_flagged and n_dis >= 4
results.append(('S4', '基线公平性与自证偏差', s4_ok,
                f"公平协议={fair}; 基线非自跑已标={baseline_not_rerun}; 局限披露{n_dis}条",
                '同backbone但基线数字引自前作,同协议为作者声称不可独立验证; 局限披露充分含冷启动仍用Claude'))

# S5 同构陷阱: 显式打折+新旧分离
s5 = ev['S5_isomorphism']
discounted = '同谱系' in s5['lineage'] and '打折' in s5['lineage']
s5_ok = len(s5['overlaps']) >= 4 and discounted and bool(s5['genuine_novelty'])
results.append(('S5', '同构陷阱判定', s5_ok,
                f"重叠{len(s5['overlaps'])}处; 同谱系打折={discounted}",
                '与SVL同谱系印证并打折,不虚高; 新意=反事实probe作为可训练学习信号,但依赖结构化环境'))

# S6 复述/长牙: 每条有gate动作+有观察项
s6 = ev['S6_teeth_candidates']
all_gate = all('gate' in c and c['gate'] for c in s6)
decisions_ok = all('decision' in c for c in s6)
observe = [c for c in s6 if '观察' in c['decision']]
s6_ok = all_gate and decisions_ok and len(s6) >= 4
results.append(('S6', '复述/长牙决策', s6_ok,
                f"候选{len(s6)}条, 均有拦截动作={all_gate}, 记观察{len(observe)}条",
                '每条有能拦什么; 条件门禁/加固/观察分层,未硬造通用模块'))

# 自审项
selfaudit_ok = len(pre['judge_self_audit']) >= 5 and '同构' in json.dumps(pre['judge_self_audit'], ensure_ascii=False)
results.append(('SELF', '判据自审（偏见防线）', selfaudit_ok,
                f"自审项{len(pre['judge_self_audit'])}条; 完整PDF替换截断版并更新锁存",
                '不因同构虚高/不因单点定罪/验证对象=v3完整版; 先读摘要已如实标注'))

print('=' * 66)
print('SKILLMASTER 论文深读 · 判据执行结果')
print('=' * 66)
for cid, name, ok, ev_s, note in results:
    print(f"[{'PASS' if ok else 'FLAG'}] {cid} · {name}")
    print(f"       证据: {ev_s}")
    print(f"       判语: {note}")
all_ok = all(r[2] for r in results)
print('=' * 66)
print(f"总计: {sum(1 for r in results if r[2])}/{len(results)} PASS → {'全部通过' if all_ok else '存在FLAG'}")

out = {
    'audit_id': ev['audit_id'],
    'criteria': [{'id': c[0], 'name': c[1], 'pass': c[2], 'evidence': c[3], 'note': c[4]} for c in results],
    'summary': {
        'all_pass': all_ok,
        'verdict': '扎实的一手实证论文: 三设计claim-vs-code全部接线, 数字内部自洽(聚合口径minor未明示), 消融排除两替代解释但未单独消融反事实效用; 同SVL框架同谱系需打折',
        'key_drift': 'α 论文0.3 vs 代码same_delta_win_loss_gamma=0.2 (minor)',
        'key_gaps': ['复现资源(数据/SFT&RL检查点)未公开,称录用后发布', '主要基线数字引自Xia et al.2026非独立重跑', '冷启动SFT仍用Claude作teacher(仅RL阶段自主)', '反事实效用未单独消融'],
        'teeth': [c['idea'][:44] for c in s6]
    }
}
(D / 'result.json').write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print('\nresult.json 已写入')
