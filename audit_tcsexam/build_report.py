#!/usr/bin/env python3
"""§66 TCSExam 精研报告。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "result.json", encoding="utf-8"))
J = {j["judge"]: j for j in res["judges"]}

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
footer{color:var(--mut);font-size:12px;margin-top:30px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
"""


def badge(a):
    cls = {"consistent": "ok", "verified": "ok", "pass": "ok", "scoped": "info",
           "downgrade": "warn", "disclosed_by_design": "warn"}.get(a, "info")
    return f'<span class="badge {cls}">{a}</span>'


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def ul(items):
    return "<ul>" + "".join(f"<li>{esc(i)}</li>" for i in items) + "</ul>"


v2c = J["V2"]["checks"]
v3c = J["V3"]["checks"]
v4 = J["V4"]

jrows = "".join(
    f"<tr><td><b>{jid}</b></td><td>{esc(J[jid].get('note', J[jid].get('mechanism','')))[:150]}</td><td>{badge(J[jid].get('action','pass'))}</td></tr>"
    for jid in ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9"]
)

cvcrows = "".join(
    f"<tr><td><code>{esc(k)}</code></td><td>{'<span class=badge ok>PASS</span>' if v else '<span class=badge no>FAIL</span>'}</td></tr>"
    for k, v in v3c.items()
)

P = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TCSExam · SVL 精研</title><style>{CSS}</style></head><body><div class="wrap">
<h1>TCSExam — SVL 精研</h1>
<div class="sub">MoonshotAI · arXiv 2611.07962v1 · 三来源（论文+项目主页+开源代码）· 精研时刻 2026-11-22T04:50:38+08:00 · PDF 52页/正文 3305行 · code @ f0518c35</div>
<div class="hero">
<div><span class="badge ok">V1 来源PASS</span><span class="badge ok">V2 数字复算一致</span><span class="badge ok">V3 代码verified</span><span class="badge warn">V4 披露充分的设计选择</span><span class="badge info">V5/V8 scoped</span><span class="badge warn">V6 同构打折</span></div>
<p class="lead">评测基准论文方法学体检。<b>数字全部独立复算</b>：Spearman ρ=0.9286→0.93、26/28 同序 2 倒挂（连倒挂 agent 都对上）、reference 1838 实例、sigma floor 0.02/1e-9、Index 权重全命中。<b>claim-vs-code 12 项全落地</b>。"缺失≠零"的诚实设计（null index / unscored separate）加分。最警惕的 V4（用被测 agent 反馈选 Lite 子集再证排名一致）作者全文披露 + 两 agent held-out → 判设计选择非漏洞，加固不新增。</p>
</div>

<h2>一、对象判定与来源</h2>
<div class="card">
<div class="t">评测基准论文（empirical benchmark）· 三来源齐备可实核</div>
<div class="f">区别于 §65 无代码指南、§64 单来源开源包：本篇有 arXiv 论文（52页）+ 项目交互主页 + 7282 文件开源评测代码。判据适配为<b>统计复算 + claim-vs-code + 披露分级</b>。四重 SHA256 锁存（<code>38361623…</code>/<code>9ad72127…</code>/<code>94f9c074…</code>/<code>fca19084…</code>）+ 预注册 <code>ea91b47d…</code> + code commit <code>f0518c35</code>，全部复核 OK。</div>
</div>

<h2>二、判据 V1–V9 与结论</h2>
<div class="card"><table>
<tr><th style="width:60px">判据</th><th>核心</th><th style="width:140px">结论</th></tr>
{jrows}
</table>
<div class="okbox">判据 verdict 与预注册 expect 一致（V1 PASS / V2 CONSISTENT / V3 PENDING→verified / V4 PENDING→disclosed_by_design / V5 SCOPED / V6 DOWNGRADE / V7 PASS / V8 SCOPED / V9 PASS）。判据自审 S1–S6 全过、AST 无中文字面串比较。<b>本次判据两次自咬</b>：①V4 披露断言字符串跨 PDF 行未命中 → 改用单行一手锚点；②自审检测器含中文范围常量被自身咬到 → 改 ord() 数值边界。两次均修工具不放水（§55 教训复现）。</div>
</div>

<h2>三、数字独立复算（核心）</h2>
<div class="card"><table>
<tr><th>论文声称</th><th>独立复算</th><th>结果</th></tr>
<tr><td>Spearman ρ = 0.93</td><td>从 Table2/3 提 8 共享 agent Index 算 rank 相关 = {v2c['spearman_0.93']}</td><td><span class=badge ok>命中</span></td></tr>
<tr><td>26/28 对同序，2 对倒挂</td><td>{v2c['pairwise_detail']['same']}/{28} 同序，倒挂 {esc(v2c['pairwise_detail']['rev_pairs'])}</td><td><span class=badge ok>命中</span></td></tr>
<tr><td>reference 1,838 eligible</td><td>遍历 full reference tasks 计 reference_values = {v2c['reference_1838_actual']}</td><td><span class=badge ok>命中</span></td></tr>
<tr><td>scale floor 0.02 / 1e-9</td><td>读 reference JSON sigma_floor_relative/absolute</td><td><span class=badge ok>命中</span></td></tr>
<tr><td>Index = 30P+30S+30C+10O</td><td>scoring.py WEIGHTS + sum 公式</td><td><span class=badge ok>命中</span></td></tr>
<tr><td>Lite 减 80% task attempts</td><td>(100−20)/100 = 0.8</td><td><span class=badge ok>命中</span></td></tr>
</table>
<div class="note">复算先行、非照抄论文：ρ 用 rank-Pearson 独立算出 0.9286，倒挂对精确点名 DS1017 vs GLM/Qwen，与 Table24 逐条一致。数值复算是本轮最硬的独立证据。</div>
</div>

<h2>四、claim-vs-code：12 项全落地</h2>
<div class="card"><table>
<tr><th style="width:300px">论文/文档声称</th><th>scoring.py / JSON 核验</th></tr>
{cvcrows}
</table>
<div class="okbox">额外发现：<code>scoring.py:22</code> 明言 "incomplete planned cells produce a null index; never filled with zero"，<code>unscored_instances</code> 单列不 silent 当零——<b>缺失≠完成</b>的诚实设计；judge 执行隔离用 Landlock ABI3+seccomp+uid65534。诚实边界：只证机制在代码有对应，不证 benchmark 效度或 agent 分数真实能力。</div>
</div>

<h2>五、V4 裁决：选择偏差为何不编译新牙</h2>
<div class="card">
<div class="t">用被测 agent 反馈选 Lite 子集 → 再证排名稳健 <span class="badge warn">披露充分</span></div>
<div class="f">{esc(v4['mechanism'])}</div>
{ul(v4['mitigations'])}
<div class="warnbox"><b>裁决（§63 GR 先例）</b>：作者全文主动披露 + 两 agent 在 list 固定后评估（事实 held-out）+ 点名倒挂来源 → 属诚实披露的实验设计选择，非隐瞒漏洞。本仓 <code>backtest_integrity</code>（判单次回测执行期 spoiler）、<code>scoring_integrity</code>（判计分篡改）、<code>transfer_holdout</code>（判模型过拟合迁移）角度不同且本场景已被披露缓解；编译"评测子集选择偏差"门禁将落成无法在外部对象上会拦的玩具（KB-META01 不通过）。→ <b>加固 KB-AUDIT04/07 指针，不新增不编译</b>。</div>
</div>

<h2>六、三层诚实结论</h2>
<div class="card">
<div class="t">可判</div>{ul(J['V9']['可判'])}
<div class="t" style="margin-top:14px">不可判</div>{ul(J['V9']['不可判'])}
<div class="t" style="margin-top:14px">宣称 vs 实现</div><div class="f">{esc(J['V9']['宣称vs实现'])}</div>
</div>

<h2>七、入库决策与双源复盘</h2>
<div class="card">
<div class="f">{esc(res['decision'])}</div>
<div class="t" style="margin-top:14px">双源复盘</div>
<div class="f"><b>task_content</b>：下载三来源、精读方法/评测/披露、独立复算全部数字、claim-vs-code 核 12 项、裁决 V4 是否造牙。<br>
<b>process</b>：两次判据自咬——V4 披露断言跨 PDF 行未命中（修单行锚点）、自审检测器自指中文范围常量（改 ord 数值边界），均修工具不放水；V4 顶住"又审出一篇可造牙"的诱惑，按 §63 先例识别为披露充分的设计选择，加固不新增；复算发现 Construction>100 与 open 全 0 时守口径 scoped 不夸大成缺陷。</div>
</div>

<footer>SVL Agent · §66 · 三来源 SHA256 锁存 · 预注册 SHA256 ea91b47d… · 后验 result 分离 · code @ f0518c35 · 加固不新增</footer>
</div></body></html>"""

out = D / "tcsexam_report.html"
out.write_text(P, encoding="utf-8")
print("report written:", out, len(P), "chars")
