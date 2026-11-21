#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""§70 记忆三来源（components/Dreams/Memory Trap）精研报告。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "result.json", encoding="utf-8"))
manifest = json.load(open(D / "manifest.json", encoding="utf-8"))
J = res["judges"]

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
.chain .arrow{color:var(--mut)}
footer{color:var(--mut);font-size:12px;margin-top:26px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
"""

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

def badge(v):
    cls = {"PASS": "ok", "SCOPED": "warn", "FAIL": "no"}.get(v, "info")
    return f'<span class="badge {cls}">{esc(v)}</span>'

parts = [f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>§70 记忆三来源精研 · SVL Agent</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>§70 记忆三来源精研：components / Dreams / Memory Trap</h1>
<div class="sub">Anthropic 记忆组成 · Claude Dreams · Princeton+Anthropic Memory Trap · {res['section']}</div>
<div class="hero">
  <div>
    <span class="badge info">3 来源</span>
    <span class="badge ok">2 一手</span>
    <span class="badge warn">1 二手(区域锁·S3)</span>
    <span class="badge ok">V1–V8 零漂移</span>
    <span class="badge ok">第 18 道门禁</span>
  </div>
  <div class="lead"><b>核心结论：</b>components 与 Dreams 两源与 §68 记忆谱系同源、按 KB-STRUCT02 打折；真正的新对象是 <b>Memory Trap</b>——良性交互产生的自写记忆在超出原作用域时导致不安全行为，无对手、恶意过滤器无从下手。本仓 18 道门禁判了记忆内容质量/检索污染/可证伪，<b>无一判「记忆作用域保持」</b> → 编译第 18 道门禁 <code>memory_scope</code>，新增 KB-AUDIT13。</div>
</div>"""]

parts.append("""<h2>一、谱系：两源同源打折 + 一个新对象</h2>
<div class="chain">
<span class="node">S01 components<br><small>§68 记忆谱系同源 → 打折</small></span><span class="arrow">＋</span>
<span class="node">S02 Dreams<br><small>=§68 S07 二手 → 打折</small></span><span class="arrow">＋</span>
<span class="node">S03 Memory Trap<br><small>新对象：记忆作用域风险</small></span>
</div>
<div class="note">前两源是同一条记忆谱系的延续，不重复造牙；Memory Trap 的 write-time / read-time 过度泛化与 retrieval_grounding（检索文本污染）、memory_curation（内容质量）对象动作均不同——拦截面独立（V2/V8）。</div>""")

parts.append("<h2>二、判据 V1–V8 总览（对齐预注册 · 零漂移）</h2>")
rows = "".join(
    f"<tr><td>{esc(k)}</td><td>{badge(v['verdict'])}</td><td>{esc(json.dumps(v['detail'], ensure_ascii=False)[:160])}</td></tr>"
    for k, v in J.items()
)
parts.append(f"<div class='card'><table><tr><th>判据</th><th>裁决</th><th>要点</th></tr>{rows}</table></div>")

parts.append("<h2>三、Memory Trap 核心证据（V1 / V5）</h2>")
parts.append("""<div class='card'><div class='t'>两条过度泛化路径 + 无对手</div>
<ul>
<li><b>write-time</b>：写笔记时 broaden 用户陈述——clean-up 的 "skip confirmation" 被写成 "never confirm before actions"</li>
<li><b>read-time</b>：用记忆时 overgeneralize，即使 raw transcript 也会被越界套用</li>
<li><b>no adversary</b>：每次交互良性、记忆是 agent 自己的，"malicious-content filters have nothing to catch" —— prompt injection / 毒化检索类防护无效</li>
<li><b>6 模型对照实验</b>：高风险任务跳过确认 / 情感记忆致 sycophancy & over-critique / stale-test 修复记忆削弱正确测试 / ImpossibleBench 作弊增加</li>
</ul>
<div class='okbox'>结论：agent 应 "preserve the scope of their memories" —— 记忆要守住作用域边界。这是本仓从未量过的维度。</div></div>""")

v4d = J['V4']['detail']
parts.append("<h2>四、作用域缺口与新门禁（V4 / V5）</h2>")
g_rows = "".join(f"<tr><td>{esc(k)}</td><td>{'命中' if v else '0（缺口）'}</td></tr>" for k, v in v4d['kb_gap_terms_hit'].items())
parts.append(f"<div class='card'><div class='t'>缺口核验 {badge(J['V4']['verdict'])}</div><table><tr><th>专属术语</th><th>本仓 KB 命中</th></tr>{g_rows}</table></div>")
parts.append("""<div class='card'><div class='t'>编译产物 <span class='badge info'>COMPILE</span></div>
<div class='f'><code>svagent/memory_scope.py:check_memory_scope</code> · 四维 write_scope_preserved / read_scope_checked / scope_bounds_recorded / no_benign_drift ∈ {yes,no,partial}</div>
<div class='okbox'>R1 写时broaden→downgrade / R2 读时不核情境→downgrade / R3 无适用边界→downgrade / R4 良性漂移已发生→flag / R5 部分→flag / R6 全自洽→ok；只判机制声明自洽，不承诺记忆真不过度泛化。7 活体回归 + 21 项测试 + 双 AST 自审 PASS + 467→488 passed。</div></div>""")

parts.append("<h2>五、判据自咬与诚实边界</h2>")
parts.append("""<div class='warnbox'><b>两次自咬：</b>①V3 首跑 FAIL——锚点 "with and without memory" 在 PDF 正文跨行断裂，改用单行一手锚点 "without memory across six frontier models"（§65 同类问题，不放宽判据）；②V7 首跑 FAIL——引擎自身把中文 "内容质量" 塞进 Compare 节点（§56 brittle 根因，检测器自咬），移入 _A 字典用键引用。两次均修工具不放水，零漂移。</div>""")
parts.append("<div class='card'><div class='t'>诚实边界</div><ul>" + "".join(f"<li>{esc(b)}</li>" for b in res['honest_boundaries']) + "</ul></div>")

parts.append("<h2>六、3 来源抓取清单</h2>")
m_rows = "".join(
    f"<tr><td>{esc(sid)}</td><td><span class='badge {'ok' if m['grade']=='一手' else 'warn'}'>{esc(m['grade'])}</span></td><td>{m['bytes']}</td><td><code>{esc(m['sha256'][:12])}</code></td><td>{esc(m['note'])}</td></tr>"
    for sid, m in manifest.items()
)
parts.append(f"<div class='card'><table><tr><th>#</th><th>等级</th><th>字节</th><th>SHA256</th><th>说明</th></tr>{m_rows}</table></div>")

prereg_sha = open(D / "prereg.sha256").read().split()[0]
gate_sha = open(D / "gate_prereg.sha256").read().split()[0]
parts.append(f"""<div class='note'><b>诚实收束：</b>记忆最阴险的坏法不是被投毒，而是来源完全善意——agent 把局部偏好写成全局规则，在越界处酿祸。内容和来源的尺子都量不到边界，这把量边界的门会拦，才编译。</div>
<footer>SVL Agent · §70 · 3 来源 SHA256 锁存 + 预注册 {prereg_sha[:12]}… + 门预注册 {gate_sha[:12]}… · 后验分离 · verdict 零漂移 · 107 KB / 488 tests</footer>
</div></body></html>""")

(D / "memory_scope_report.html").write_text("\n".join(parts), encoding="utf-8")
print("报告生成:", D / "memory_scope_report.html")
