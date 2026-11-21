#!/usr/bin/env python3
"""§65 Building always-on agents 精研报告。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "result.json", encoding="utf-8"))
judges = {j["judge"]: j for j in res["judges"]}
sa = res["judge_self_audit"]
comp = res["compilation"]

CSS = """
:root{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--warn:#d29922;--no:#f85149;--acc:#58a6ff;--bd:#30363d}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7;padding:40px 20px}
.wrap{max-width:1040px;margin:0 auto}
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
footer{color:var(--mut);font-size:12px;margin-top:30px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
"""


def vbadge(a):
    cls = {"flag": "warn", "unverifiable": "info", "downgrade": "warn", "ok": "ok",
           "scoped": "info", "verified": "ok", "new_teeth_candidate": "warn",
           "merged_into_v5": "info", "pass": "ok", "block": "no"}.get(a, "info")
    return f'<span class="badge {cls}">{a}</span>'


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# 判据逐行
jrows = ""
for jid in ["V1", "V2", "V3", "V4", "V5", "V6", "V7"]:
    j = judges[jid]
    act = j.get("action", "pass" if jid in ("V1", "V7") else "")
    extra = ""
    if jid == "V1":
        extra = f"（{sum(j['checks'].values())}/{len(j['checks'])} 一手锚点命中）"
    if jid == "V5":
        extra = f"（{len(j['gap_capabilities'])} 项能力缺口）"
    jrows += f"<tr><td><b>{jid}</b></td><td>{esc(j.get('note', j.get('claim', j.get('reason', ''))))[:160]}{extra}</td><td>{vbadge(act)}</td></tr>"

# 同构区
hom = "".join(
    f"<tr><td>{esc(h['orig'])}</td><td><code>{esc(h['repo'])}</code></td><td>{esc(h['verdict'])}</td></tr>"
    for h in judges["V4"]["items"]
)

# 能力差集
gap_list = "".join(f"<li><code>{esc(g)}</code></li>" for g in judges["V5"]["gap_capabilities"])

# 三层
def ul(items):
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"

live = "".join(
    f"<tr><td>{esc(k)}</td><td><code>{esc(v)}</code></td></tr>"
    for k, v in comp["live_regression"]["cases"].items()
)

P = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Building always-on agents · SVL 精研</title><style>{CSS}</style></head><body><div class="wrap">
<h1>Building always-on agents — SVL 精研</h1>
<div class="sub">William Hu · Anthropic / Claude Platform · 2026-11-13 · 精研时刻 2026-11-22T04:38:24+08:00 · HTML 563950B / 正文 154 行</div>
<div class="hero">
<div><span class="badge ok">V1 来源PASS</span><span class="badge info">V2 数字scoped</span><span class="badge info">V3 无代码UNVERIFIABLE</span><span class="badge warn">V4 同构打折</span><span class="badge warn">V5 状态连续性新牙</span><span class="badge ok">V7 三层诚实</span></div>
<p class="lead">一手 HTML + 正文 + 三重 SHA256 锁存（<code>467e47d7…</code> / <code>26a0c4b8…</code> / 预注册 <code>0020f5fd…</code>）。判据 V1–V7 分析前锁存、后验 result 分离。<b>V5 咬出真缺口</b>：本仓 14 道门禁无一覆盖「事件驱动系统的跨会话状态连续性与可恢复性」，编译新门禁 <code>session_continuity.py:check_session_continuity</code>。<b>断言落到代码</b>：8 活体回归 + 16 测试 + 双 AST 自审全过。</p>
</div>

<h2>一、对象判定与复算纪律</h2>
<div class="card">
<div class="t">工程最佳实践指南（非论文、无公开代码、无 A/B）</div>
<div class="f">按 KB-AUDIT04 对象/口径对等：工程指南不硬套论文消融复算。唯一数字（Opus 5.5 便宜 78%/40%）来自未命名 benchmark 的 self-reported 厂商声称 → V2 判 SCOPED，限定语境不外推。指南链接指向的产品能力（auto memory / memory tool / auto mode / hook / MCP Apps）非本文可实现声明 → V3 判 UNVERIFIABLE（无可核代码≠造假，也不因 Anthropic 官方就当已实现），与 §64 Deep Agents 开源包 7/7 可核形成对照。</div>
</div>

<h2>二、判据 V1–V7 与结论</h2>
<div class="card"><table>
<tr><th style="width:60px">判据</th><th>核心</th><th style="width:120px">结论</th></tr>
{jrows}
</table>
<div class="okbox">判据 verdict 与预注册 expect 逐条一致（V1 PASS / V2 SCOPED / V3 UNVERIFIABLE / V4 DOWNGRADE / V5 PENDING→核验后 new_teeth / V6 PENDING→merged / V7 PASS），无事后漂移。判据自审 S1–S6 全过，AST 核验判定分支无中文字面串比较（brittle_lines 空）。</div>
</div>

<h2>三、五原语与本仓同构区（打折，不当独立验证）</h2>
<div class="card"><table>
<tr><th>文章机制</th><th>本仓对应物</th><th>判定</th></tr>
{hom}
</table>
<div class="warnbox">四处同源按 KB-STRUCT02 打折：同源不同粒度（有状态跨会话编排 vs 同步单会话修复环）不当独立验证；memory 存指针已在 §64 V6 记同谱系；handler 快 ack + 深验证放 run 与 §64 检索门禁同维度不同阶段，不重复计数；「存在≠执行」哲学同源但拦截动作不同。</div>
</div>

<h2>四、V5 真缺口：14 道门禁未覆盖的能力</h2>
<div class="card">
<div class="t">state.continuity_gap — 跨会话状态连续性与可恢复性</div>
<div class="f">本仓门禁覆盖计分/迁移/稳健/复盘/谱系/回测/调用点/审查漏斗/训练服务/检索/歧义/归因/评估/记忆，无一覆盖以下事件驱动系统能力：</div>
{gap_list}
<div class="note">一手锚定：line 27（not actually always on）、line 48（inbox as source of truth，崩溃重试）、line 70（memories outlive worker）、line 91（需持久信息写入 memory）、line 105-110（deferred tool call 会话续跑 + 非阻塞等待）。<b>诚实分寸</b>：本仓同步纯函数库不做运行时编排是 §58 选 A 架构选择，非漏洞；本门禁定位为审读外部 always-on 系统声称的尺子，不判本仓。V6 事件生命周期治理（去重/单worker/批合并/游标）与 V5 同维，收敛为一道门禁防多牙（KB-META01）。</div>
</div>

<h2>五、断言落到代码：session_continuity 门禁</h2>
<div class="card">
<div class="t"><code>svagent/session_continuity.py:check_session_continuity</code> <span class="badge warn">会拦会判</span></div>
<div class="f">规则 R0–R7 按优先级短路返回，实现前 SHA256 锁存 <code>{comp['gate_prereg_sha256'][:12]}…</code>：</div>
<ul>
<li>R0 语义枚举（yes/no/partial）+ 布尔校验，字面串 → <code>flag</code>（避开 §56 brittle 根因）</li>
<li>R1 无跨 run 持久状态且声称 always-on → <code>block</code>（根基不成立）</li>
<li>R2 会话不可续跑 / R3 无真相源 / R4 多消费者 → <code>downgrade</code></li>
<li>R5 等待阻塞 / R6 部分持久化-续跑 → <code>flag</code>（待核非定罪）</li>
<li>R7 全自洽 → <code>ok</code>（只判机制声明存在，不承诺真的永续）</li>
</ul>
<div class="okbox">8 活体回归逐条对齐预注册预期；门禁 + 引擎双 AST 自审 PASS；新增 16 项测试；全量 <b>{comp['full_suite']['before']} → {comp['full_suite']['after']} passed</b>；惰性导入登记，遵循 §58 选 A 不接 run_loop。</div>
<table><tr><th>活体样例</th><th>判定</th></tr>{live}</table>
</div>

<h2>六、三层诚实结论</h2>
<div class="card">
<div class="t">可判</div>{ul(res['three_layer']['可判'])}
<div class="t" style="margin-top:14px">不可判</div>{ul(res['three_layer']['不可判'])}
<div class="t" style="margin-top:14px">宣称 vs 实现</div><div class="f">{esc(judges['V7']['宣称vs实现'])}</div>
<div class="warnbox"><b>核心诚实边界</b>：门禁只判「机制声明是否自洽」，绝不承诺系统真的永续运行、持久化真的不丢——机制存在≠有效性（KB-META01 不可自证）。输入须系统方如实声明，声明本身不可自证。本篇无公开代码可核，V3 UNVERIFIABLE。</div>
</div>

<h2>七、入库决策与双源复盘</h2>
<div class="card">
<div class="t">入库决策</div>
<div class="f">{esc(res['decision'])}</div>
<div class="t" style="margin-top:14px">双源复盘</div>
<div class="f"><b>task_content</b>：精读指南、判定五原语与本仓架构的关系、把「跨会话状态连续性」编译成会拦会判的门禁。<br>
<b>process</b>：严格区分「本仓范式差异（同步判据库不做编排，§58 选 A）」与「真缺口（审读外部 always-on 系统的状态连续性尺子）」，未把架构选择误判成漏洞；V6 与 V5 同维主动收敛为一道门禁防 vanity；判据 verdict 全部锚定预注册 expect、无事后漂移；双 AST 自审前置应用 §56 brittle 教训，一次过。</div>
</div>

<footer>SVL Agent · §65 · 一手来源 SHA256 锁存 · 预注册 SHA256 0020f5fd… · 后验 result 分离 · 门禁预注册 42b10e90…</footer>
</div></body></html>"""

out = D / "always_on_report.html"
out.write_text(P, encoding="utf-8")
print("report written:", out, len(P), "chars")
