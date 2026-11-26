# -*- coding: utf-8 -*-
"""大摩研报营销文章核查报告生成器。"""
import json, html
from ms_factcheck_data import RESULT as D

VERDICT_STYLE = {
    "属实": ("ok", "✓ 属实"),
    "属实(文章向下取整)": ("ok", "✓ 属实(取整)"),
    "主体错位": ("warn", "⚠ 主体错位"),
    "推论偷换+商业导流": ("bad", "✗ 推论偷换+导流"),
}

def esc(s):
    return html.escape(str(s))

rows = []
for c in D["fact_checks"]:
    cls, label = VERDICT_STYLE.get(c["verdict"], ("", c["verdict"]))
    rows.append(
        f'<tr><td class="claim">{esc(c["claim"])}</td>'
        f'<td><span class="badge {cls}">{esc(label)}</span></td>'
        f'<td class="ev">{esc(c["evidence"])}</td>'
        f'<td class="conf">{esc(c["confidence"])}</td></tr>'
    )

boundaries = "".join(f"<li>{esc(b)}</li>" for b in D["honest_boundaries"])
tc = D["three_layer_conclusion"]

doc = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>大摩研报营销文章 · 叙事真实性核查</title>
<style>
:root{{--bg:#0f1419;--card:#1a2129;--line:#2b3541;--fg:#e6edf3;--muted:#8b98a5;
--ok:#3fb950;--warn:#d29922;--bad:#f85149;--accent:#58a6ff;}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;line-height:1.7}}
.wrap{{max-width:1100px;margin:0 auto;padding:32px 20px 60px}}
header{{border-bottom:1px solid var(--line);padding-bottom:20px;margin-bottom:28px}}
h1{{font-size:26px;margin:0 0 8px}}
.sub{{color:var(--muted);font-size:14px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:22px;margin:18px 0}}
h2{{font-size:19px;margin:0 0 14px;color:var(--accent)}}
.core{{background:linear-gradient(135deg,#1a2129,#22303d);border-left:4px solid var(--warn)}}
.core p{{font-size:16px;margin:0}}
table{{width:100%;border-collapse:collapse;font-size:13.5px}}
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
.meta a{{color:var(--accent)}}
.stat{{display:flex;gap:14px;flex-wrap:wrap;margin:6px 0 0}}
.stat div{{background:#212a34;border-radius:8px;padding:8px 14px;font-size:13px}}
.stat b{{font-size:18px;display:block}}
</style></head><body><div class="wrap">
<header>
<h1>大摩研报营销文章 · 叙事真实性核查</h1>
<div class="sub">对象：{esc(D['object'])}　|　核查日期：{esc(D['date'])}</div>
<div class="sub meta">一手来源：<a href="https://mgstn.ly/4C25VL8">摩根士丹利官网原文</a> + 两份蓝皮书原文摘录</div>
</header>

<div class="card core">
<p><b>核心发现：</b>{esc(D['core_finding'])}</p>
</div>

<div class="card">
<h2>逐条核查（12 项）</h2>
<div class="stat">
<div><b>10</b>条事实属实</div>
<div><b>1</b>条主体错位</div>
<div><b>1</b>条推论偷换+导流</div>
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
<h2>方法立场</h2>
<p>依第 29 节实证结论：不据文风断言作者是 AI 还是人（浅层文风判别抓的是文风 artifact）。本次只做事实核查 + 推论有效性审计 + 利益链分析。</p>
<p>本报告为方法论研究，不构成投资建议，也不针对任何具体认证产品的质量评价。</p>
</div>
</div></body></html>"""

open("/workspace/ms_article_report.html", "w", encoding="utf-8").write(doc)
print("saved ms_article_report.html", len(doc), "chars")
