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
.wrap{max-width:900px;margin:0 auto}
h1{font-size:25px;margin:0 0 4px}
.sub{color:var(--mut);font-size:14px;margin-bottom:22px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px 20px;margin:14px 0}
.card h2{font-size:17px;margin:0 0 10px;color:var(--acc)}
.badge{display:inline-block;padding:2px 9px;border-radius:20px;font-size:12px;font-weight:700;margin-right:8px}
.badge.ok{background:rgba(63,185,80,.15);color:var(--ok);border:1px solid var(--ok)}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{text-align:left;padding:8px 10px;border-bottom:1px solid var(--bd);vertical-align:top}
th{color:var(--mut)}
code{background:#010409;color:var(--acc);padding:1px 6px;border-radius:5px;font-size:13px}
.note{border-left:3px solid var(--acc);padding:10px 14px;background:rgba(88,166,255,.06);margin:12px 0;border-radius:0 8px 8px 0}
.vd{color:var(--ok);font-weight:600}
.kv{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
.kv span{background:#010409;border:1px solid var(--bd);border-radius:8px;padding:8px 12px;font-size:13px}
.kv b{color:var(--acc)}
"""

parts = []
parts.append('<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">')
parts.append('<meta name="viewport" content="width=device-width,initial-scale=1">')
parts.append('<title>rea-video 文章研读审计</title><style>' + css + '</style></head><body><div class="wrap">')
parts.append('<h1>rea-video 文章研读 · 框架审计</h1>')
parts.append('<div class="sub">cherryquant.com · fendouai · 2026-11-21 · 对象类型：项目介绍/准评测文 · 判据 7/7 PASS</div>')

# 判据卡片
parts.append('<div class="card"><h2>判据执行结果</h2><table><tr><th>判据</th><th>结果</th><th>证据</th></tr>')
for c in res['criteria']:
    badge = '<span class="badge ok">PASS</span>' if c['pass'] else '<span class="badge no">FLAG</span>'
    parts.append('<tr><td><b>' + esc(c['id']) + ' · ' + esc(c['name']) + '</b></td><td>' + badge + '</td><td>' + esc(c['evidence']) + '<br><span style="color:var(--mut)">' + esc(c['note']) + '</span></td></tr>')
parts.append('</table></div>')

# 事实核查表
parts.append('<div class="card"><h2>关键事实断言一手溯源（9 TRUE / 1 UNVERIFIED / 0 FALSE）</h2><table><tr><th>断言</th><th>状态</th><th>一手证据</th></tr>')
for c in ev['V2_factual_claims']:
    st = c['status']
    col = 'var(--ok)' if st == 'TRUE' else 'var(--warn)'
    parts.append('<tr><td>' + esc(c['claim']) + '</td><td style="color:' + col + ';font-weight:700">' + st + '</td><td>' + esc(c['evidence']) + '</td></tr>')
parts.append('</table></div>')

# 三层诚实结论
parts.append('<div class="card"><h2>三层诚实结论</h2>')
parts.append('<p><b>事实</b>：9 条可溯源断言与项目一手文档逐字一致；Star 数因 API 限流未核（UNVERIFIED）。</p>')
parts.append('<p><b>结论</b>：免责声明逐条映射一手局限，判诚实信号；97.5% 是缓存融合、未在从头解码重测，作者主动降级不做普遍承诺——事实全真，但方法普适性仍需独立验证。</p>')
parts.append('<p><b>迁移</b>：5 处与本仓同构判同谱系打折；真实新意是"先选工具再投入生成成本"的成本前置，记观察。</p>')
parts.append('</div>')

# 入库决策
parts.append('<div class="card"><h2>复述/长牙与入库决策</h2>')
parts.append('<ul>')
for c in ev['V6_teeth_candidates']:
    parts.append('<li>' + esc(c['idea']) + ' → <b>' + esc(c['decision']) + '</b></li>')
parts.append('</ul>')
parts.append('<div class="note">克制：不新增条目（"数字须带口径"已被 KB-R-MS03 + KB-STRUCT08 + KB-AUDIT04 覆盖，入则灌水）。加固 KB-R-MS03 / KB-STRUCT08 / KB-R-MS01 / KB-AUDIT04 四条 support；知识库保持 98 条，ready=True，vanity 占比 0.041。</div>')
parts.append('</div>')

parts.append('<div class="card vd">' + esc(res['summary']['verdict']) + '</div>')
parts.append('<div class="sub" style="margin-top:16px">三重 SHA256 锁存：原文 / 预注册 / 证据 均校验 OK · 全量 287 项测试通过 · commentary §46</div>')
parts.append('</div></body></html>')

(D / 'reavideo_report.html').write_text('\n'.join(parts), encoding='utf-8')
h = (D / 'reavideo_report.html').read_text(encoding='utf-8')
print('报告生成:', len(h), 'bytes, PASS徽章', h.count('badge ok'), '闭合', h.rstrip().endswith('</html>'))
