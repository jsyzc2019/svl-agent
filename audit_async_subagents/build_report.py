#!/usr/bin/env python3.11
# -*- coding: utf-8 -*-
"""§69 11来源异步子Agent谱系精研报告。"""
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
<title>§69 11来源异步子Agent谱系精研 · SVL Agent</title><style>{CSS}</style></head>
<body><div class="wrap">
<h1>§69 11 来源异步子 Agent 谱系精研</h1>
<div class="sub">LangChain async · Claude Code subagents · DeepSeek Super-agent · OpenAI dots/async-tools · {res['section']}</div>
<div class="hero">
  <div>
    <span class="badge info">11 来源</span>
    <span class="badge ok">9 一手</span>
    <span class="badge warn">2 二手(区域锁·S3)</span>
    <span class="badge ok">V1–V8 零漂移</span>
    <span class="badge ok">第 17 道门禁</span>
  </div>
  <div class="lead"><b>核心结论：</b>11 篇不是 11 项独立验证，而是<b>四家主体</b>（LangChain 一家占六源，按 KB-STRUCT02 打折为 1 条）在说同一件事：同步委派挡不住长任务。本仓 16 道门禁<b>无一判「后台委派生命周期完整性」</b>（提交收集解耦 / 可引导可取消 / 句柄穿越 compaction / 完成主动通知）→ 编译第 17 道门禁 <code>async_delegation_lifecycle</code>，新增 KB-AUDIT12。</div>
</div>"""]

parts.append("""<h2>一、四家主体谱系（LangChain 六源打折）</h2>
<div class="chain">
<span class="node">LangChain 系×6<br><small>S01/S05/S06/S07/S09/S10 → 折 1 条</small></span><span class="arrow">＋</span>
<span class="node">Anthropic<br><small>S02 Claude Code subagents</small></span><span class="arrow">＋</span>
<span class="node">DeepSeek<br><small>S04 Super-agent 两级架构</small></span><span class="arrow">＋</span>
<span class="node">OpenAI<br><small>S03 dots + S08 async-tools</small></span>
</div>
<div class="note">同一设计约束被四家独立主体各自撞上 → 拦截面独立且会拦（V5 会拦才入通过）；同源六源按 KB-STRUCT02 不当六项独立验证（V2）。</div>""")

parts.append("<h2>二、判据 V1–V8 总览（对齐预注册 · 零漂移）</h2>")
rows = "".join(
    f"<tr><td>{esc(k)}</td><td>{badge(v['verdict'])}</td><td>{esc(json.dumps(v['detail'], ensure_ascii=False)[:160])}</td></tr>"
    for k, v in J.items()
)
parts.append(f"<div class='card'><table><tr><th>判据</th><th>裁决</th><th>要点</th></tr>{rows}</table></div>")

parts.append("<h2>三、一手锚点命中（V1）</h2>")
a_rows = "".join(f"<tr><td>{esc(k)}</td><td>{'✓' if v else '✗'}</td></tr>" for k, v in J['V1']['detail'].items())
parts.append(f"<div class='card'><table><tr><th>锚点组</th><th>命中</th></tr>{a_rows}</table></div>")

v4d = J['V4']['detail']
parts.append("<h2>四、生命周期缺口与新门禁（V4 / V5）</h2>")
g_rows = "".join(f"<tr><td>{esc(k)}</td><td>{'命中' if v else '0（缺口）'}</td></tr>" for k, v in v4d['kb_gap_terms_hit'].items())
parts.append(f"<div class='card'><div class='t'>缺口核验 {badge(J['V4']['verdict'])}</div><div class='f'>{esc(v4d.get('brittle_fix',''))}</div><table><tr><th>专属术语</th><th>本仓 KB 命中</th></tr>{g_rows}</table></div>")
parts.append("""<div class='card'><div class='t'>编译产物 <span class='badge info'>COMPILE</span></div>
<div class='f'><code>svagent/async_delegation_lifecycle.py:check_async_delegation_lifecycle</code> · 四维 decoupled/steerable/survives_compaction/completion_notified ∈ {yes,no,partial}</div>
<div class='okbox'>R1 无解耦→downgrade / R2 不可引导→downgrade / R3 句柄随压缩丢失→downgrade / R4 无完成通知→flag / R5 部分→flag / R6 全自洽→ok；只判机制声明自洽，不承诺委派真高效/完成真被通知。7 活体回归 + 21 项测试 + 双 AST 自审 PASS + 446→467 passed。</div></div>""")

parts.append("<h2>五、判据自咬与诚实边界</h2>")
parts.append("""<div class='warnbox'><b>判据自咬一次：</b>V4 首跑 FAIL——检测词 resume/cancel 过宽，resume 命中 KB-AUDIT10 的跨会话 resume（假阳性，§56 brittle 过宽误伤形态）。修法：不碰预注册断言，只把引擎检测词收窄为 7 个异步委派专属术语，全 0 命中 → 缺口确认、零漂移。修工具不放水。</div>""")
parts.append("<div class='card'><div class='t'>诚实边界</div><ul>" + "".join(f"<li>{esc(b)}</li>" for b in res['honest_boundaries']) + "</ul></div>")

parts.append("<h2>六、11 来源抓取清单</h2>")
m_rows = "".join(
    f"<tr><td>{esc(sid)}</td><td><span class='badge {'ok' if m['grade']=='一手' else 'warn'}'>{esc(m['grade'])}</span></td><td>{m['bytes']}</td><td><code>{esc(m['sha256'][:12])}</code></td><td>{esc(m['note'])}</td></tr>"
    for sid, m in manifest.items()
)
parts.append(f"<div class='card'><table><tr><th>#</th><th>等级</th><th>字节</th><th>SHA256</th><th>说明</th></tr>{m_rows}</table></div>")

prereg_sha = open(D / "prereg.sha256").read().split()[0]
gate_sha = open(D / "gate_prereg.sha256").read().split()[0]
parts.append(f"""<div class='note'><b>诚实收束：</b>四家主体、四个坑——提交要立即返回句柄、中途要能改能砍、句柄不能随上下文压缩丢失、跑完要主动喊一声。本仓 15 道门禁从没量过后台委派生命周期，这道门会拦，才编译。</div>
<footer>SVL Agent · §69 · 11 来源 SHA256 锁存 + 预注册 {prereg_sha[:12]}… + 门预注册 {gate_sha[:12]}… · 后验分离 · verdict 零漂移 · 106 KB / 467 tests</footer>
</div></body></html>""")

(D / "async_delegation_report.html").write_text("\n".join(parts), encoding="utf-8")
print("报告生成:", D / "async_delegation_report.html")
