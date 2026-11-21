#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成雄心教程研读审计 HTML 报告。"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
R = json.loads((BASE / "result.json").read_text(encoding="utf-8"))
E = json.loads((BASE / "evidence.json").read_text(encoding="utf-8"))
P = json.loads((BASE / "prereg.json").read_text(encoding="utf-8"))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


crit_html = ""
for c in R["criteria"]:
    checks = "".join(
        f"<li><code>{esc(k)}</code>: {esc(v)}</li>"
        for k, v in c["checks"].items() if not isinstance(v, (dict, list))
    )
    crit_html += f"""
    <div class="crit">
      <div class="crit-head"><span class="badge {'ok' if c['pass'] else 'no'}">{'PASS' if c['pass'] else 'FLAG'}</span>
        <strong>{esc(c['id'])} · {esc(c['name'])}</strong></div>
      <ul class="checks">{checks}</ul>
      <p class="finding">{esc(c['finding'])}</p>
    </div>"""

# 事实核查表
fc_rows = ""
for k, v in E["A2_fact_check"].items():
    if k == "summary":
        continue
    f = v["finding"]
    cls = "v-true" if ("TRUE" in f or "属实" in f or "吻合" in f) else "v-qual"
    fc_rows += f"<tr><td>{esc(k)}</td><td class='{cls}'>{esc(f)}</td></tr>"

three = R["three_layer_honesty"]
three_html = "".join(
    f"<div class='layer'><div class='layer-k'>{esc(k)}</div><div class='layer-v'>{esc(v)}</div></div>"
    for k, v in three.items()
)

teeth_html = ""
for l in E["A6_candidate_lessons"]:
    teeth_html += (
        f"<tr><td>{esc(l['id'])}</td><td>{esc(l['lesson'])}</td>"
        f"<td class='block'>{esc(l['would_block'])}</td></tr>"
    )

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>研读《How to be more ambitious》· SVL 框架审计</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--bd:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#58a6ff;--ok:#3fb950;--no:#f85149;--warn:#d29922;--purple:#bc8cff}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1120px;margin:0 auto;padding:40px 24px 80px}}
h1{{font-size:27px;margin:0 0 6px}}h2{{font-size:20px;margin:44px 0 16px;padding-left:12px;border-left:4px solid var(--acc)}}
.sub{{color:var(--mut);margin-bottom:28px}}
.verdict{{display:inline-block;background:rgba(63,185,80,.12);border:1px solid var(--ok);color:var(--ok);border-radius:8px;padding:10px 18px;font-weight:700;font-size:17px;margin:8px 0 4px}}
table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px}}
th,td{{border:1px solid var(--bd);padding:9px 12px;text-align:left;vertical-align:top}}
th{{background:#1c2128;color:var(--acc);font-weight:600}}
.crit{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px 20px;margin:14px 0}}
.crit-head{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
.badge{{font-size:12px;font-weight:700;padding:3px 10px;border-radius:20px}}
.badge.ok{{background:rgba(63,185,80,.15);color:var(--ok);border:1px solid var(--ok)}}
.badge.no{{background:rgba(248,81,73,.15);color:var(--no);border:1px solid var(--no)}}
.checks{{margin:6px 0 10px;padding-left:22px;color:var(--mut)}}
.checks code{{color:var(--purple);background:rgba(188,140,255,.08);padding:1px 5px;border-radius:4px}}
.finding{{margin:8px 0 0}}
.v-true{{color:var(--ok)}}.v-qual{{color:var(--warn)}}
.layer{{background:var(--card);border:1px solid var(--bd);border-left:4px solid var(--warn);border-radius:8px;padding:14px 18px;margin:12px 0}}
.layer-k{{color:var(--warn);font-weight:700;margin-bottom:5px}}
.block{{color:var(--ok)}}
.meta{{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}}
.meta span{{background:var(--card);border:1px solid var(--bd);border-radius:6px;padding:6px 12px;font-size:13px;color:var(--mut)}}
.foot{{color:var(--mut);font-size:13px;margin-top:40px;border-top:1px solid var(--bd);padding-top:18px}}
code{{font-family:ui-monospace,Menlo,Consolas,monospace}}
</style></head><body><div class="wrap">
<h1>研读《How to be more ambitious》</h1>
<p class="sub">Felix Rieseberg · 2026-10-13 · SVL 框架第三类对象（观点/教程文）审计 · {esc(R['generated_at'])}</p>

<div class="meta">
  <span>判据 {esc(R['summary']['total'])} 条</span>
  <span>通过 {esc(R['summary']['passed'])}/{esc(R['summary']['total'])}</span>
  <span>事实断言核查 {len([k for k in E['A2_fact_check'] if k!='summary'])} 条</span>
  <span>判据自审反向命中 {esc(R['summary']['self_audit_hits'])} 次</span>
</div>

<div class="verdict">6/6 判据通过 · 我的四个怀疑全错 · 不新增知识条目（克制）</div>

<h2>一、对象类型与纪律</h2>
<p>本文是观点/教程文：无统计量可复算、无分类学需自洽。判据按 KB-AGI01 切换为「论点-证据链、事实断言核查、主体归属、可证伪分级」，并显式检验与框架同构时的谱系污染（KB-STRUCT02）。预注册与原文 SHA256 先于核查锁定。</p>

<h2>二、事实断言核查（本次核心）</h2>
<p>预注册时我怀疑 4 条断言（厂商倡导文会夸大），核查证明全部为真或带诚实限定词——<b>先验偏见被事实推翻</b>。</p>
<table><tr><th>断言</th><th>核查结论</th></tr>{fc_rows}</table>

<h2>三、判据执行</h2>
{crit_html}

<h2>四、三层诚实结论</h2>
{three_html}

<h2>五、长牙候选</h2>
<table><tr><th>ID</th><th>机制</th><th>会拦什么</th></tr>{teeth_html}</table>
<p>入库决策：不新增（M2已被 KB-R-MS03 覆盖，入则灌水）；加固 KB-R-MS03 / KB-STRUCT02 / KB-R-MS01 的 support，知识库保持 97 条。</p>

<div class="foot">
证据通道：原文 HTML(sha256锁存) + WebFetch 正文 + 独立 WebSearch 事实核查（新华社/奥运官网/NAE/NPR/World Athletics/Tao 原文）。预注册与证据均 SHA256 锁存。
Tao 引语精确措辞未在抓取原文找到，标 PARTIAL 不判假；系外行星为候选未确认（作者用 may have 已降级）——据实标注。
</div>
</div></body></html>"""

(BASE / "ambition_report.html").write_text(html, encoding="utf-8")
print("报告已生成:", BASE / "ambition_report.html", f"({len(html)} bytes)")
