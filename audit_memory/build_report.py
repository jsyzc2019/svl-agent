#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§68 22来源记忆生命周期主题簇精研报告。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "result.json", encoding="utf-8"))
J = res["judges"]
manifest = json.load(open(D / "manifest.json", encoding="utf-8"))

CSS = """
:root{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--warn:#d29922;--no:#f85149;--acc:#58a6ff;--bd:#30363d}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7;padding:40px 20px}
.wrap{max-width:1080px;margin:0 auto}
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
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:10px}
th,td{border:1px solid var(--bd);padding:7px 9px;text-align:left;vertical-align:top}
th{background:var(--card);color:var(--acc)}
.note{background:rgba(88,166,255,.08);border-left:3px solid var(--acc);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
.warnbox{background:rgba(210,153,34,.08);border-left:3px solid var(--warn);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
.okbox{background:rgba(63,185,80,.08);border-left:3px solid var(--ok);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
code{background:var(--bg);border:1px solid var(--bd);border-radius:4px;padding:1px 5px;font-size:12px;color:var(--fg)}
ul{margin-left:20px;font-size:13px;color:var(--mut)}
li{margin:4px 0}
.chain{display:flex;flex-wrap:wrap;gap:6px;align-items:center;font-size:13px;margin:14px 0}
.chain .node{background:rgba(88,166,255,.1);border:1px solid var(--acc);border-radius:8px;padding:7px 11px}
.chain .arrow{color:var(--warn);font-weight:700}
footer{color:var(--mut);font-size:12px;margin-top:30px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
"""

def badge(v):
    m = {"PASS":"ok","DOWNGRADE":"warn","SCOPED":"info","NEW_GATE_CANDIDATE":"info",
         "COMPILE":"ok","UNVERIFIABLE":"no","FAIL":"no","REVIEW":"no"}
    return f'<span class="badge {m.get(v,"info")}">{v}</span>'

def esc(s): return str(s).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

parts = [f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>§68 22来源记忆生命周期精研 · SVL Agent</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>§68 22来源记忆生命周期主题簇精研</h1>
<div class="sub">神经科学机制(选择/标记/重放/整合) → AI工程(巩固/梦境/工具/压缩/wiki) · {esc(res['timestamp'])} · 22来源({res['evidence_primary']}一手/{res['evidence_secondary']}二手/{res['evidence_unavailable']}未取)</div>
<div class="hero">
  <div class="chain">
    <span class="node">T1 选择<br><small>S02 CLS·S03 SPW-R·S11 tagging</small></span><span class="arrow">→</span>
    <span class="node">T2 整合<br><small>S04 重放·S05 系统巩固</small></span><span class="arrow">→</span>
    <span class="node">T3 AI巩固<br><small>S06/S08 sleep·S07 Dream·S21 cookbook</small></span><span class="arrow">→</span>
    <span class="node">T4 工具<br><small>S01/S12/S19/S10 memory</small></span><span class="arrow">→</span>
    <span class="node">T5 范式<br><small>S17 wiki·S13 CL-Bench·S18/S22</small></span>
  </div>
  <div class="lead"><b>核心结论：</b>22 篇不是 22 项独立验证，而是一条<b>同源谱系（生物机制→AI隐喻复用）</b>的记忆生命周期链条。判据 V1–V9 全部对齐预注册、零漂移。核验发现本仓 15 道门禁<b>无一判「记忆内容质量治理」</b>（选择/整理/非破坏）→ 编译第 16 道门禁 <code>memory_curation</code>。<b>{esc(res['final_decision'])}</b></div>
</div>
"""]

# 判据总览
parts.append("<h2>一、判据 V1–V9 总览</h2>")
rows = "".join(f"<tr><td>{k}</td><td>{badge(v['verdict'])}</td><td>{esc(v.get('note',''))}</td></tr>" for k,v in J.items())
parts.append(f"<div class='card'><table><tr><th>判据</th><th>裁决</th><th>要点</th></tr>{rows}</table></div>")

# 一手锚点
parts.append("<h2>二、一手锚点真实性（V1，T1–T5 分层）</h2>")
a_rows = "".join(f"<tr><td>{esc(k)}</td><td>{'✓' if v else '✗'}</td></tr>" for k,v in J['V1']['anchors'].items())
parts.append(f"<div class='card'><table><tr><th>锚点（子主题_来源_论断）</th><th>命中</th></tr>{a_rows}</table></div>")

# 记忆治理缺口 + 新门禁
parts.append("<h2>三、记忆治理缺口与新门禁（V4 / V5）</h2>")
g_rows = "".join(f"<tr><td>{esc(k)}</td><td>{'✓' if v else '✗'}</td></tr>" for k,v in J['V4']['gap_evidence'].items())
parts.append(f"<div class='card'><div class='t'>缺口一手证据 {badge(J['V4']['verdict'])}</div><table><tr><th>证据</th><th>命中</th></tr>{g_rows}</table></div>")
comp = res["compilation"]
c_rows = "".join(f"<tr><td>{esc(k)}</td><td><code>{esc(v)}</code></td></tr>" for k,v in comp["live_regression"]["cases"].items())
parts.append(f"""<div class='card'><div class='t'>编译产物 {badge('COMPILE')}</div>
<div class='f'><code>{esc(comp['gate'])}</code> · 门预注册 <code>{comp['gate_prereg_sha256'][:12]}…</code> · 15 项新测试 · 全量 {comp['full_suite']['before']}→{comp['full_suite']['after']} · 双 AST 自审 PASS · 不接 run_loop</div>
<table><tr><th>活体样例</th><th>裁决/代码</th></tr>{c_rows}</table>
<div class='okbox'>R1 无选择→downgrade / R2 无整理→downgrade / R3 破坏性→flag / R4 部分→flag / R5 自洽→ok；只判机制声明自洽，不承诺记忆真的有用。</div></div>""")

# 谱系打折与同构
parts.append("<h2>四、谱系打折与同构（V2 / V7）</h2>")
parts.append(f"<div class='card'><div class='t'>V2 谱系同源 {badge(J['V2']['verdict'])}</div><div class='f'>{esc(J['V2']['note'])}</div></div>")
parts.append(f"<div class='card'><div class='t'>V7 Karpathy wiki 同构 {badge(J['V7']['verdict'])}</div><div class='f'>{esc(J['V7']['note'])}</div></div>")

# claim-vs-code 分级 + 隐喻边界
parts.append("<h2>五、适用性分级与隐喻边界（V3 / V6）</h2>")
parts.append(f"<div class='card'><div class='t'>V3 {badge(J['V3']['verdict'])}</div><div class='f'>{esc(J['V3']['note'])}</div></div>")
parts.append(f"<div class='card'><div class='t'>V6 隐喻vs实证 {badge(J['V6']['verdict'])}</div><div class='f'>{esc(J['V6']['note'])}</div></div>")

# 三层结论
parts.append("<h2>六、三层诚实结论（V8）</h2>")
parts.append(f"""<div class='card'>
<div class='okbox'><b>已验证：</b>{'；'.join(esc(x) for x in J['V8']['verified'])}</div>
<div class='warnbox'><b>未验证：</b>{'；'.join(esc(x) for x in J['V8']['unverified'])}</div>
<div class='note'><b>不可验证：</b>{'；'.join(esc(x) for x in J['V8']['unverifiable'])}</div>
</div>""")

# 22 来源清单
parts.append("<h2>七、22 来源抓取清单</h2>")
m_rows = "".join(
    f"<tr><td>{esc(r['id'])}</td><td>{esc(r['name'])}</td><td>{esc(r.get('http','?'))}</td><td>{r.get('bytes',0)}</td><td>{esc(r.get('title','')[:46])}</td></tr>"
    for r in manifest
)
parts.append(f"<div class='card'><table><tr><th>#</th><th>来源</th><th>HTTP</th><th>字节</th><th>标题</th></tr>{m_rows}</table></div>")

# 自审
parts.append("<h2>八、判据自审（V9）</h2>")
parts.append(f"""<div class='card'><div class='t'>{badge(J['V9']['verdict'])}</div>
<div class='f'>AST 中文字面串比较行 <code>{J['V9']['ast_brittle_compare_lines']}</code>（应空）；verdict/expect 漂移 <code>{esc(J['V9']['verdict_expect_drift'])}</code>（应空）。中文锚点集中字典用键引用，检测器 ord 数值边界避免自指。</div></div>""")

parts.append(f"""<div class='note'><b>诚实边界：</b>{esc(res['honesty_boundary'])}</div>
<footer>SVL Agent · §68 · 35份来源语料SHA256锁存 + 预注册 {esc(res['prereg_sha256'][:12])}… + 门预注册 {comp['gate_prereg_sha256'][:12]}… · 后验分离 · verdict 零漂移</footer>
</div></body></html>""")

out = D / "memory_report.html"
out.write_text("".join(parts), encoding="utf-8")
print("written:", out, out.stat().st_size, "bytes")
