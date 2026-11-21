#!/usr/bin/env python3
"""§62 HiGR 精研报告：暗色主题，判据卡片，三层诚实结论，新门禁说明。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "result.json", encoding="utf-8"))
judges = res["judges"]

CSS = """
:root{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--warn:#d29922;--no:#f85149;--acc:#58a6ff;--bd:#30363d}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7;padding:40px 20px}
.wrap{max-width:1000px;margin:0 auto}
h1{font-size:25px;color:var(--acc);margin-bottom:6px}
.sub{color:var(--mut);font-size:14px;margin-bottom:24px}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;margin-right:6px}
.badge.ok{background:rgba(63,185,80,.15);color:var(--ok);border:1px solid var(--ok)}
.badge.warn{background:rgba(210,153,34,.15);color:var(--warn);border:1px solid var(--warn)}
.badge.no{background:rgba(248,81,73,.15);color:var(--no);border:1px solid var(--no)}
.hero{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:22px;margin-bottom:22px}
.hero .lead{font-size:14px;margin-top:10px}
.kpi{display:flex;gap:16px;margin-top:16px;flex-wrap:wrap}
.kpi div{background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:10px 14px;font-size:13px;color:var(--mut)}
.kpi b{color:var(--fg);font-size:17px;display:block}
h2{font-size:18px;color:var(--acc);margin:26px 0 12px;border-left:3px solid var(--acc);padding-left:10px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px 18px;margin-bottom:12px}
.card .t{font-size:15px;font-weight:600;margin-bottom:8px;display:flex;align-items:center;gap:8px}
.card .f{font-size:13px;color:var(--mut)}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
th,td{border:1px solid var(--bd);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--card);color:var(--acc)}
.note{background:rgba(88,166,255,.08);border-left:3px solid var(--acc);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
.warnbox{background:rgba(210,153,34,.08);border-left:3px solid var(--warn);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
code{background:var(--bg);border:1px solid var(--bd);border-radius:4px;padding:1px 5px;font-size:12px;color:var(--fg)}
footer{color:var(--mut);font-size:12px;margin-top:30px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
"""


def vbadge(v, code=""):
    v = str(v)
    if v in ("block", "downgrade", "NEW_TEETH", "LEAKAGE_RISK"):
        return f'<span class="badge no">{v}</span>'
    if v in ("flag", "PARTIAL", "SCOPED", "OVERCLAIM", "UNVERIFIED") or "UN" in code:
        return f'<span class="badge warn">{v}</span>'
    return f'<span class="badge ok">{v}</span>'


cards = ""
for j in judges:
    cards += ('<div class="card"><div class="t">'
              + vbadge(j.get("verdict"), j.get("code", ""))
              + '<span>' + j["judge"] + '</span></div>'
              + ('<div class="note">判据码: <code>' + j["code"] + '</code> · ' + j.get("message", "") + '</div>'
                 if j.get("code") else '')
              + '<div class="f">' + j["finding"] + '</div></div>')

tier = res["three_tier_conclusion"]
tier_rows = ""
for label, key in [("T1 · 一手确凿", "tier1_code_fact"),
                   ("T2 · 推断", "tier2_reasoned"),
                   ("T3 · 未核验", "tier3_unverified")]:
    items = "".join("<li>" + x + "</li>" for x in tier[key])
    tier_rows += f"<tr><td>{label}</td><td><ul>{items}</ul></td></tr>"

html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>HiGR v5 精研：§62</title><style>__CSS__</style></head><body><div class="wrap">
<h1>HiGR v5 精研与复盘</h1>
<div class="sub">HiGR: Industrial-Scale Hierarchical Generative Slate Recommendation Framework in Tencent · arXiv 2512.24787v5 · CIKM 2026 · 腾讯 · 精研于 2026-11-22</div>

<div class="hero">
  <div><span class="badge ok">V1 数字自洽</span><span class="badge no">V2 downgrade</span><span class="badge warn">V3 PARTIAL</span><span class="badge warn">V4 PARTIAL</span><span class="badge ok">V5 SCOPED</span><span class="badge no">V6 新牙</span><span class="badge ok">自审 5/5</span></div>
  <div class="lead">工业界推荐论文，无公开代码。数字全部算术自洽，效率声称口径限定充分。真正的认知增量在 <b>V2</b>：正样本 <code>y+</code> 用 engaged watch sequence 按 <b>true feedback 排序</b>构造（训练时有反馈），而线上推理只有 profile+history、经多重过滤——论文全文未讨论这一 <b>train-serving 落差</b>。本仓四道门禁都没管这个维度，于是编译了新牙 <code>serving_signal_gate.py</code>。</div>
  <div class="kpi">
    <div><b>6</b>判据</div>
    <div><b>5/5</b>判据自审通过</div>
    <div><b>1</b>新门禁(17测试)</div>
    <div><b>102</b>知识库条目(新+1)</div>
  </div>
</div>

<h2>判据结论（V1–V6）</h2>
__CARDS__

<h2>新牙：训练-服务信号可得性门禁（§62）</h2>
<div class="card"><table>
<tr><th>规则</th><th>条件</th><th>动作</th></tr>
<tr><td>R1</td><td>训练信号服务时不可得 + 未声明落差 + 无桥接</td><td><span class="badge no">downgrade</span></td></tr>
<tr><td>R2</td><td>不可得 + 已声明 + 无桥接</td><td><span class="badge warn">flag</span></td></tr>
<tr><td>R3</td><td>不可得 + 已声明 + 有显式桥接</td><td><span class="badge ok">ok</span></td></tr>
<tr><td>R4</td><td>信号服务时可得（口径对等）</td><td><span class="badge ok">ok</span></td></tr>
<tr><td>R5</td><td>代理信号（partial）+ 未声明</td><td><span class="badge warn">flag</span></td></tr>
<tr><td>R0</td><td>字面串/非法枚举输入</td><td><span class="badge warn">flag</span></td></tr>
</table>
<div class="note">预注册 <code>serving_gate_prereg.json</code> 实现前 SHA256 锁存 <code>fddecbea…</code>；6 活体回归逐条对齐预期（含"高度同构"字面串被 R0 拦）；17 项测试、惰性导入、源码自审（判定分支无中文字面串比较）全过。<b>落点分寸</b>：用后验反馈构造偏好对是 listwise 偏好学习标准做法，本门禁判的是"未声明的口径落差"，不是标签泄漏/造假定罪。遵循 §58 选 A，不接 run_loop。</div></div>

<h2>三层诚实结论</h2>
<div class="card"><table>__TIER__</table></div>

<h2>入库决策（vanity 门禁）</h2>
<div class="card"><div class="f">
新增 <b>KB-AUDIT08</b>（train-serving 信号可得性）——因为它拦的是本仓四道门禁（finance_blind_test 评测端 / backtest_integrity 回测端 / transfer_holdout 泛化端 / call_site_integrity 调用点端）都覆盖不到的独立维度，且已编译成会判代码，符合 KB-META01"会拦才入"。加固 KB-AUDIT04 一条 support。102 条，不灌水。
</div></div>

<h2>过程复盘（§54 双源）</h2>
<div class="card"><div class="f">
<b>任务源：</b>HiGR 暴露"训练用后验反馈、服务时无此信号"这一被全文忽略的口径落差，编译成通用门禁。<br>
<b>过程源：</b>一度怀疑 Table6 符号错配，回查 PDF 原文确认自洽，按"信事实"放弃硬凑罪名（KB-AUDIT02）；新门禁设计时刻意用语义枚举 + R0 拦字面串，避开 §56 brittle 根因；判据引擎自审只用语义码不读中文。
</div></div>

<footer>来源锁存：paper.pdf + paper.txt + arxiv_abs.html 三重 SHA256；prereg.json（分析前 1cfb6686…）+ serving_gate_prereg.json（实现前 fddecbea…）+ 后验 result.json 分离。无公开代码，claim-vs-code 标 UNVERIFIED 不判造假；线上数字 self-reported 不复现。</footer>
</div></body></html>"""

html = (html.replace("__CSS__", CSS).replace("__CARDS__", cards).replace("__TIER__", tier_rows))
out = D / "higr_report.html"
out.write_text(html, encoding="utf-8")
chk = out.read_text(encoding="utf-8")
print("生成", out.name, "size", len(chk), "闭合", chk.rstrip().endswith("</html>"), "徽章数", chk.count('class="badge'))
