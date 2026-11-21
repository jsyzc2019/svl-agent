#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import json
from pathlib import Path

D = Path(__file__).parent
res = json.loads((D / 'result.json').read_text(encoding='utf-8'))
ev = json.loads((D / 'evidence.json').read_text(encoding='utf-8'))

def esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

css = """
:root{--bg:#0d1117;--card:#161b22;--bd:#30363d;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--warn:#d29922;--acc:#58a6ff}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 -apple-system,"Segoe UI",sans-serif;padding:28px}
.wrap{max-width:920px;margin:0 auto}
h1{font-size:25px;margin:0 0 4px}
.sub{color:var(--mut);font-size:14px;margin-bottom:22px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px 20px;margin:14px 0}
.card h2{font-size:17px;margin:0 0 10px;color:var(--acc)}
.badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:12px;font-weight:700;margin-right:8px}
.badge.ok{background:rgba(63,185,80,.15);color:var(--ok);border:1px solid var(--ok)}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--bd);vertical-align:top}
th{color:var(--mut)}
code{background:#010409;color:var(--acc);padding:1px 6px;border-radius:5px;font-size:12px}
.note{border-left:3px solid var(--acc);padding:10px 14px;background:rgba(88,166,255,.06);margin:12px 0;border-radius:0 8px 8px 0}
.warnbox{border-left:3px solid var(--warn);padding:10px 14px;background:rgba(210,153,34,.06);margin:12px 0;border-radius:0 8px 8px 0}
.vd{color:var(--ok);font-weight:600}
.kv{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
.kv span{background:#010409;border:1px solid var(--bd);border-radius:8px;padding:8px 12px;font-size:13px}
.kv b{color:var(--acc)}
"""

parts = []
parts.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
parts.append('<title>SKILLMASTER 论文深读审计</title><style>' + css + '</style></head><body><div class="wrap">')
parts.append('<h1>SKILLMASTER 论文深读 · 框架审计</h1>')
parts.append('<div class="sub">arXiv:2605.08693 v3 (2026-09-30) · 山东大学/中关村学院/清华/东南/中科大 · 对象类型：学术实证论文 · 判据 7/7 PASS</div>')

# 判据卡片
parts.append('<div class="card"><h2>判据执行结果</h2><table><tr><th>判据</th><th>结果</th><th>证据与判语</th></tr>')
for c in res['criteria']:
    badge = '<span class="badge ok">PASS</span>' if c['pass'] else '<span class="badge no">FLAG</span>'
    parts.append('<tr><td><b>' + esc(c['id']) + ' · ' + esc(c['name']) + '</b></td><td>' + badge + '</td><td>' + esc(c['evidence']) + '<br><span style="color:var(--mut)">' + esc(c['note']) + '</span></td></tr>')
parts.append('</table></div>')

# claim-vs-code
parts.append('<div class="card"><h2>claim-vs-code：三设计全部接线</h2><table><tr><th>设计</th><th>代码状态</th><th>证据</th></tr>')
for c in ev['S1_claim_vs_code']['claims']:
    parts.append('<tr><td>' + esc(c['claim']) + '</td><td><b style="color:var(--ok)">' + esc(c['code_status']) + '</b></td><td>' + esc(c['evidence']) + '</td></tr>')
parts.append('</table>')
parts.append('<div class="warnbox"><b>参数级漂移</b>：论文 α=0.3（正文 L376 / 附录 C L739），训练脚本 <code>same_delta_win_loss_gamma=0.2</code>。方法名与代码实体都对上，但超参值对不上 → minor 口径漂移，不得写成"论文与代码完全一致"。<br><b>复现缺口</b>：README 明言匿名版不含训练数据/SFT&RL 检查点，称录用后发布。</div>')
parts.append('</div>')

# 数字复算
parts.append('<div class="card"><h2>数字复算（self-reported）</h2><table><tr><th>检查项</th><th>结论</th></tr>')
s2 = ev['S2_number_consistency']
parts.append('<tr><td>主表 ALFWorld 89.9→98.7（+8.8pp）</td><td>' + esc(s2['table4_ablation_arithmetic']['verdict']) + '</td></tr>')
parts.append('<tr><td>SearchQA 超 SkillRL 0.9pp / 7 中 5 升 2 降</td><td>逐项复算一致</td></tr>')
parts.append('<tr><td>Overall 聚合差异（ALF 0.1 / QA-SM 0.2 / QA-SR 0.4）</td><td>minor，口径未明示（疑加权），方向一致</td></tr>')
parts.append('<tr><td>Table8 三次运行 mean±std</td><td>' + esc(s2['table8_repeated_runs']['verdict']) + '</td></tr>')
parts.append('</table></div>')

# 三层诚实结论
parts.append('<div class="card"><h2>三层诚实结论</h2>')
parts.append('<p><b>事实</b>：三设计有代码实体且接线；数字大体自洽；消融排除两个替代解释（review-only 仅 +0.8pp，弱初始库到 0% 仍 89.4 vs 74.8）。</p>')
parts.append('<p><b>结论</b>：skill-management 整体有效=因果级；反事实效用单独贡献=相关级（未单独消融，论文 gap 已如实写）；基线数字引自 Xia et al. 2026 非独立重跑，同协议为作者声称不可独立验证。</p>')
parts.append('<p><b>迁移</b>：与 SVL 框架 5 处同构（反事实效用≈会拦才入、方向一致性≈单一检查点不足定罪等），同谱系打折；真实新意是把"经验是否有用"做成可训练学习信号，但依赖可 probe 的结构化环境。</p>')
parts.append('</div>')

# 判据自审亮点
parts.append('<div class="card"><h2>判据自审亮点：引擎自己咬到自己</h2>')
parts.append('<div class="note">S3 判据首次跑出 FLAG——引擎用脆弱字面串 <code>"未单独消融" in gap</code> 匹配，但证据字段写的是"<b>没有</b>单独消融"，匹配失败致假阴性。改为语义/动作词判定后 7/7 全过。<b>这是 KB-AUDIT01（脆弱断言致假阴性）的活体复现——判据引擎当场犯了它要防的错。</b></div>')
parts.append('</div>')

# 入库决策
parts.append('<div class="card"><h2>复述/长牙与入库决策</h2><ul>')
for c in ev['S6_teeth_candidates']:
    parts.append('<li>' + esc(c['idea']) + ' → <b>' + esc(c['decision']) + '</b></li>')
parts.append('</ul>')
parts.append('<div class="note">新增 <b>KB-AUDIT06</b>（claim-vs-code 要核到超参值那一层）；加固 KB-AUDIT01 / KB-SIM02 / KB-STRUCT02。知识库 98 → <b>99 条</b>，ready=True，vanity 0.04，全量 287 项测试通过。</div>')
parts.append('</div>')

parts.append('<div class="card vd">' + esc(res['summary']['verdict']) + '</div>')
parts.append('<div class="sub" style="margin-top:16px">锁存：完整PDF(9c87bb2f)/预注册(114816ae)/证据(9fa835e4) SHA256 · GitHub raw 抓到训练脚本 · commentary §47</div>')
parts.append('</div></body></html>')

(D / 'skillmaster_report.html').write_text('\n'.join(parts), encoding='utf-8')
h = (D / 'skillmaster_report.html').read_text(encoding='utf-8')
print('报告生成:', len(h), 'bytes, PASS徽章', h.count('badge ok'), '闭合', h.rstrip().endswith('</html>'))
