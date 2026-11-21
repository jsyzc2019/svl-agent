# -*- coding: utf-8 -*-
"""康波文章核查报告生成器。"""
import json, html
from kondratieff_data import RESULT as D

def cls_of(v):
    if v.startswith("属实"):
        return "ok"
    if "存疑" in v:
        return "warn"
    if "争议" in v or "不可靠" in v or "无免责" in v:
        return "bad"
    return ""

def esc(s):
    return html.escape(str(s))

rows = []
for c in D["fact_checks"]:
    cls = cls_of(c["verdict"])
    rows.append(
        f'<tr><td class="claim">{esc(c["claim"])}</td>'
        f'<td><span class="badge {cls}">{esc(c["verdict"])}</span></td>'
        f'<td class="ev">{esc(c["evidence"])}</td>'
        f'<td class="conf">{esc(c["confidence"])}</td></tr>'
    )

boundaries = "".join(f"<li>{esc(b)}</li>" for b in D["honest_boundaries"])
tc = D["three_layer_conclusion"]
sources = "".join(f"<li>{esc(s)}</li>" for s in D["primary_sources"])

doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>康波历史类比文章 · 推理方法核查</title>
<style>
:root{{--bg:#0f1419;--card:#1a2129;--line:#2b3541;--fg:#e6edf3;--muted:#8b98a5;
--ok:#3fb950;--warn:#d29922;--bad:#f85149;--accent:#58a6ff;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.7}}
.wrap{{max-width:1140px;margin:0 auto;padding:32px 20px 60px}}
header{{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:28px}}
h1{{font-size:26px;margin:0 0 8px}}
.sub{{color:var(--muted);font-size:14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px;margin:18px 0}}
h2{{font-size:19px;margin:0 0 14px;color:var(--accent)}}
.core{{background:linear-gradient(135deg,#1a2129,#2a2530);border-left:4px solid var(--bad)}}
.core p{{font-size:16px;margin:0}}
table{{width:100%;border-collapse:collapse;font-size:13.2px}}
th,td{{text-align:left;padding:10px 12px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--muted);font-weight:600;font-size:12px;text-transform:uppercase}}
.claim{{width:26%;font-weight:600}}
.ev{{color:var(--muted);width:46%}}
.conf{{width:8%;color:var(--muted);font-size:12px}}
.badge{{display:inline-block;padding:2px 8px;border-radius:20px;font-size:12px;white-space:nowrap}}
.badge.ok{{background:rgba(63,185,80,.15);color:var(--ok)}}
.badge.warn{{background:rgba(210,153,34,.15);color:var(--warn)}}
.badge.bad{{background:rgba(248,81,73,.15);color:var(--bad)}}
.layer{{display:grid;grid-template-columns:120px 1fr;gap:12px;padding:10px 0;border-bottom:1px solid var(--line)}}
.layer:last-child{{border:none}}
.layer b{{color:var(--accent)}}
ul{{margin:6px 0;padding-left:22px;color:var(--muted)}}
li{{margin:6px 0}}
.meta{{font-size:13px;color:var(--muted)}}
.stat{{display:flex;gap:14px;flex-wrap:wrap;margin:6px 0 0}}
.stat div{{background:#212a34;border-radius:8px;padding:8px 14px;font-size:13px}}
.stat b{{font-size:18px;display:block}}
.chain{{display:flex;gap:8px;flex-wrap:wrap;align-items:center;font-size:14px;margin:8px 0}}
.chain span{{background:#212a34;border-radius:6px;padding:6px 12px}}
.chain i{{color:var(--warn);font-style:normal}}
</style></head><body><div class="wrap">
<header>
<h1>康波历史类比文章 · 推理方法核查</h1>
<div class="sub">对象：{esc(D['object'])}　|　核查日期：{esc(D['date'])}</div>
<div class="sub meta">核心方法：把 1975-1982 逐段对应到 2023-2026，据此预测 2027-2029</div>
</header>

<div class="card core">
<p><b>核心发现：</b>{esc(D['core_finding'])}</p>
</div>

<div class="card">
<h2>核查能力递进链（本轮新增第三道关）</h2>
<div class="chain">
<span>文风层<br><small>第29节·尺子可能歪</small></span><i>→</i>
<span>事实层<br><small>第30节·真伪核查</small></span><i>→</i>
<span>推论层<br><small>第31节·主体错位</small></span><i>→</i>
<span style="border:1px solid var(--bad)">推理方法层<br><small>第32节·本轮</small></span>
</div>
</div>

<div class="card">
<h2>逐条核查（12 项）</h2>
<div class="stat">
<div><b>8</b>条事实属实</div>
<div><b>1</b>条数字存疑</div>
<div><b>3</b>条方法/框架问题</div>
</div>
<table>
<thead><tr><th>断言</th><th>判定</th><th>证据</th><th>置信</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div>

<div class="card">
<h2>三层诚实结论</h2>
<div class="layer"><b>能说的</b><span>{esc(tc['can_say'])}</span></div>
<div class="layer"><b>不能说的</b><span>{esc(tc['cannot_say'])}</span></div>
<div class="layer"><b>方法反身</b><span>{esc(tc['method_reflection'])}</span></div>
</div>

<div class="card">
<h2>诚实边界</h2>
<ul>{boundaries}</ul>
</div>

<div class="card meta">
<h2>一手来源</h2>
<ul>{sources}</ul>
<p style="margin-top:14px">依第29节实证结论：不据文风断言作者是 AI 还是人。本报告为方法论研究，不构成投资建议，也不预测文中所指的市场走势。</p>
</div>
</div></body></html>"""

open("/workspace/kondratieff_report.html", "w", encoding="utf-8").write(doc)
print("saved kondratieff_report.html", len(doc), "chars")
