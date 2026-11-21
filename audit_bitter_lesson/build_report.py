#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§67 三来源思想谱系精研报告：Bitter Lesson -> Alberta Plan -> 机器人幼儿园。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "result.json", encoding="utf-8"))
J = res["judges"]

CSS = """
:root{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--warn:#d29922;--no:#f85149;--acc:#58a6ff;--bd:#30363d}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7;padding:40px 20px}
.wrap{max-width:1060px;margin:0 auto}
h1{font-size:25px;color:var(--acc);margin-bottom:6px}
.sub{color:var(--mut);font-size:14px;margin-bottom:24px}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;margin-right:6px}
.badge.ok{background:rgba(63,185,80,.15);color:var(--ok);border:1px solid var(--ok)}
.badge.warn{background:rgba(210,153,34,.15);color:var(--warn);border:1px solid var(--warn)}
.badge.no{background:rgba(248,81,73,.15);color:var(--no);border:1px solid var(--no)}
.badge.info{background:rgba(88,166,255,.15);color:var(--acc);border:1px solid var(--acc)}
.hero{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:22px;margin-bottom:22px}
.hero .lead{font-size:14px;margin-top:10px}
h2{font-size:18px;color:var(--acc);margin:26px 0 12px;border-left:3px solid var(--acc);padding-left:10px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px 18px;margin-bottom:12px}
.card .t{font-size:15px;font-weight:600;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.card .f{font-size:13px;color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
th,td{border:1px solid var(--bd);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--card);color:var(--acc)}
.note{background:rgba(88,166,255,.08);border-left:3px solid var(--acc);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
.warnbox{background:rgba(210,153,34,.08);border-left:3px solid var(--warn);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
.okbox{background:rgba(63,185,80,.08);border-left:3px solid var(--ok);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
code{background:var(--bg);border:1px solid var(--bd);border-radius:4px;padding:1px 5px;font-size:12px;color:var(--fg)}
ul{margin-left:20px;font-size:13px;color:var(--mut)}
li{margin:4px 0}
.chain{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:14px;margin:14px 0}
.chain .node{background:rgba(88,166,255,.1);border:1px solid var(--acc);border-radius:8px;padding:8px 12px}
.chain .arrow{color:var(--warn);font-weight:700}
footer{color:var(--mut);font-size:12px;margin-top:30px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
"""

def badge(v):
    cls = {"PASS": "ok", "DOWNGRADE": "warn", "SCOPED": "info", "NO_NEW_GATE": "info",
           "UNVERIFIABLE": "no", "FAIL": "no", "REVIEW": "no"}.get(v, "info")
    return f'<span class="badge {cls}">{v}</span>'

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def bool_table(d):
    rows = "".join(f"<tr><td>{esc(k)}</td><td>{'✓' if v else '✗'}</td></tr>" for k, v in d.items())
    return f"<table><tr><th>锚点</th><th>命中</th></tr>{rows}</table>"

parts = [f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>§67 三来源思想谱系精研 · SVL Agent</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>§67 三来源思想谱系精研</h1>
<div class="sub">The Bitter Lesson → The Alberta Plan → 机器人幼儿园 · 哲学 / 纲领 / 工程落地三层 · {esc(res['timestamp'])}</div>
<div class="hero">
  <div class="chain">
    <span class="node">S1 Bitter Lesson<br><small>哲学宣言 · Sutton 2019</small></span>
    <span class="arrow">→</span>
    <span class="node">S2 Alberta Plan<br><small>研究纲领 · Sutton 组 2022</small></span>
    <span class="arrow">→</span>
    <span class="node">S3 机器人幼儿园<br><small>工程落地 · 他山×Sutton/Openmind 2026</small></span>
  </div>
  <div class="lead"><b>核心结论：</b>三篇是<b>同源思想谱系（Sutton）的三个粒度</b>，按 KB-STRUCT02 打折，不构成三项独立验证。本轮判据全部对齐预注册、零漂移；最终裁决 <b>{esc(res['final_decision'])}</b>——无独立拦截动作值得编译新门禁。</div>
</div>
"""]

parts.append("<h2>一、判据 V1–V8 总览</h2>")
rows = "".join(
    f"<tr><td>{k}</td><td>{badge(v['verdict'])}</td><td>{esc(v.get('note', v.get('reason','')))}</td></tr>"
    for k, v in J.items()
)
parts.append(f"<div class='card'><table><tr><th>判据</th><th>裁决</th><th>要点</th></tr>{rows}</table></div>")

parts.append("<h2>二、一手锚点真实性（V1）</h2>")
for s in ["S1", "S2", "S3"]:
    parts.append(f"<div class='card'><div class='t'>{s} 锚点</div>{bool_table(J['V1']['anchors'][s])}</div>")

parts.append("<h2>三、谱系同源与纲领自述（V2 / V4）</h2>")
parts.append(f"<div class='card'><div class='t'>V2 谱系证据链 {badge(J['V2']['verdict'])}</div>{bool_table(J['V2']['lineage_chain'])}<div class='f'>{esc(J['V2']['note'])}</div></div>")
parts.append(f"<div class='card'><div class='t'>V4 纲领≠成果 {badge(J['V4']['verdict'])}</div>{bool_table(J['V4']['evidence'])}<div class='f'>{esc(J['V4']['note'])}</div></div>")

parts.append("<h2>四、落地承诺兑现度（V5，对照表非效果证明）</h2>")
parts.append(f"<div class='card'>{bool_table(J['V5']['promise_fulfillment'])}<div class='warnbox'>{esc(J['V5']['note'])}</div></div>")

parts.append("<h2>五、claim-vs-code 适用性（V3）</h2>")
parts.append(f"<div class='card'><div class='t'>{badge(J['V3']['verdict'])}（≠造假）</div><div class='f'>{esc(J['V3']['reason'])}</div></div>")

parts.append("<h2>六、新牙裁决（V6）</h2>")
parts.append(f"<div class='card'><div class='t'>{badge(J['V6']['verdict'])}</div><ul>{''.join(f'<li>{esc(x)}</li>' for x in J['V6']['rationale'])}</ul></div>")

parts.append("<h2>七、三层诚实结论（V7）</h2>")
parts.append(f"""<div class='card'>
<div class='okbox'><b>已验证：</b>{'；'.join(esc(x) for x in J['V7']['verified'])}</div>
<div class='warnbox'><b>未验证：</b>{'；'.join(esc(x) for x in J['V7']['unverified'])}</div>
<div class='note'><b>不可验证：</b>{'；'.join(esc(x) for x in J['V7']['unverifiable'])}</div>
</div>""")

parts.append("<h2>八、判据自审（V8）</h2>")
parts.append(f"""<div class='card'><div class='t'>{badge(J['V8']['verdict'])}</div>
<div class='f'>AST 中文字面串比较行：<code>{J['V8']['ast_brittle_compare_lines']}</code>（应为空）<br>
verdict/expect 漂移：<code>{esc(J['V8']['verdict_expect_drift'])}</code>（应为空）<br>
反 brittle 设计：中文锚点集中到字典用键引用，Compare 节点不含中文字面串；检测器用 ord() 数值边界避免自指。</div></div>""")

parts.append(f"""<div class='note'><b>诚实边界：</b>{esc(res['honesty_boundary'])}</div>
<footer>SVL Agent · §67 · 一手 SHA256 锁存 + 预注册 {esc(res['prereg_sha256'][:12])}… · 后验分离 · verdict 零漂移</footer>
</div></body></html>""")

out = D / "bitter_lesson_report.html"
out.write_text("".join(parts), encoding="utf-8")
print("written:", out, out.stat().st_size, "bytes")
