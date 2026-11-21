#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 Runway Software Factory 深度研究 HTML 报告（自包含）。"""
import json
from pathlib import Path
BASE = Path(__file__).resolve().parent
R = json.loads((BASE / "result.json").read_text(encoding="utf-8"))
E = json.loads((BASE / "evidence.json").read_text(encoding="utf-8"))

def esc(s): return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

crit_html = ""
for cid, c in R["criteria"].items():
    checks = "".join(f"<li><code>{esc(k)}</code>: {esc(v)}</li>" for k, v in c["checks"].items())
    extra = ""
    if c.get("teeth"):
        extra = "<p class='teeth'><b>长牙：</b>" + "；".join(esc(t) for t in c["teeth"]) + "</p>"
    crit_html += f"""<div class='crit'><div class='crit-head'><span class='badge {'ok' if c['pass'] else 'no'}'>{'PASS' if c['pass'] else 'FLAG'}</span><strong>{cid} · {esc(c['name'])}</strong></div><ul class='checks'>{checks}</ul><p class='finding'>{esc(c['finding'])}</p>{extra}</div>"""

num_rows = ""
for it in E["R1_numbers"]["verified_consistent"]:
    num_rows += f"<tr><td>{esc(it['claim'])}</td><td>{esc(it['recalc'])}</td><td class='v-true'>{esc(it['verdict'])}</td></tr>"
for it in E["R1_numbers"]["mismatches"]:
    num_rows += f"<tr><td>{esc(it['claim'])}</td><td>{esc(it.get('recalc','—'))}</td><td class='v-mis'>{esc(it['verdict'])}（{esc(it['severity'])}）</td></tr>"

rails = "".join(f"<li>{esc(x)}</li>" for x in E["R4_failure_disclosure"]["safety_rails_from_failures"])

sa_rows = "".join(
    f"<tr><td><span class='kb'>{esc(i['kb'])}</span></td><td>{esc(i['what'])}</td><td>{esc(i['why'])}</td></tr>"
    for i in R["judge_self_audit"]["incidents"]
)

three = "".join(
    f"<div class='layer'><div class='layer-k'>{esc(k)}</div><div class='layer-v'>{esc(v)}</div></div>"
    for k, v in R["three_layer"].items()
)

html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Runway · Building a Software Factory · 深度研究</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--bd:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#58a6ff;--ok:#3fb950;--no:#f85149;--warn:#d29922;--purple:#bc8cff}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1120px;margin:0 auto;padding:40px 24px 80px}}h1{{font-size:27px;margin:0 0 6px}}h2{{font-size:20px;margin:42px 0 16px;padding-left:12px;border-left:4px solid var(--acc)}}
.sub{{color:var(--mut);margin-bottom:24px}}.verdict{{display:inline-block;background:rgba(63,185,80,.12);border:1px solid var(--ok);color:var(--ok);border-radius:8px;padding:10px 18px;font-weight:700;font-size:17px;margin:8px 0}}
.meta{{color:var(--mut);font-size:13px}}table{{width:100%;border-collapse:collapse;margin:14px 0;background:var(--card);border-radius:8px;overflow:hidden;font-size:13.5px}}
th,td{{border:1px solid var(--bd);padding:9px 12px;text-align:left;vertical-align:top}}th{{background:#1c2128;color:var(--acc)}}
.v-true{{color:var(--ok)}}.v-mis{{color:var(--warn);font-weight:700}}.kb{{background:rgba(188,140,255,.15);color:var(--purple);border-radius:4px;padding:1px 7px;font-size:12px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px 20px;margin:14px 0}}
.crit{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px 18px;margin:12px 0}}
.crit-head{{display:flex;align-items:center;gap:10px;font-size:15px}}.badge{{font-size:11px;font-weight:800;padding:2px 9px;border-radius:20px}}.badge.ok{{background:rgba(63,185,80,.15);color:var(--ok)}}.badge.no{{background:rgba(248,81,73,.15);color:var(--no)}}
.checks{{margin:10px 0 6px;padding-left:20px;color:var(--mut);font-size:13px}}.checks code{{color:var(--fg);background:#21262d;padding:1px 6px;border-radius:4px}}
.finding{{margin:6px 0 0}}.teeth{{margin:8px 0 0;color:var(--warn);font-size:13px}}
.note{{background:rgba(210,153,34,.08);border-left:3px solid var(--warn);padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;color:#e3c07b}}
.layer{{display:flex;gap:14px;padding:12px 0;border-bottom:1px solid var(--bd)}}.layer-k{{flex:0 0 56px;color:var(--acc);font-weight:700}}.layer-v{{flex:1}}
code{{font-family:ui-monospace,Menlo,Consolas,monospace}}.foot{{margin-top:46px;color:var(--mut);font-size:12px;border-top:1px solid var(--bd);padding-top:16px}}
.chain{{display:flex;flex-wrap:wrap;gap:8px;align-items:center;margin:12px 0}}.st{{background:var(--card);border:1px solid var(--bd);border-radius:6px;padding:6px 12px;font-size:13px}}.st.done{{border-color:var(--ok);color:var(--ok)}}.ar{{color:var(--mut)}}
</style></head><body><div class="wrap">
<h1>Building a Software Factory · 深度研究</h1>
<div class="sub">Runway 工程博客 · Alejandro Alvarez · 2026-11-20 · 本仓 SVL 框架方法迁移（第六类对象：企业工程实践报告）</div>
<div class="verdict">{esc(R['verdict'])}</div>
<div class="meta">判据 {R['criteria_passed']}/{R['criteria_total']} · 判据自审 {len(R['judge_self_audit']['incidents'])} 次拦截 · 一手原文已 SHA256 锁存</div>

<h2>一、文章核心：把交付线逐站交给 agent</h2>
<div class="chain">
{''.join(f"<span class='st done'>{s}</span><span class='ar'>→</span>" for s in ['Write','Pass CI','Review','Approve','QA','Fix breaks','Run the line'])}
</div>
<p>核心叙事：AI 让写代码变快，<b>review 成了瓶颈</b>。Runway 没有要求 agent 写出更好的 change，而是逐站把软件交付的每个环节交给 agent——每交一站，先定"如何判断这次交接"，再看结果。瓶颈随之后移到下一站：write→CI→<b>review</b>→<b>approve</b>→<b>QA</b>→<b>fix breaks</b>→<b>run the line</b>。最终工程师的角色从"读 diff"转为"决定造什么、修 agent 卡住的地方、守住度量诚实"。</p>
<div class="card"><b>最关键的工程机制（安全护栏，全部由真实事故倒逼）：</b><ul>{rails}</ul></div>
<div class="note">与本仓框架高度同构：shadow mode（先读后写）≈ 预注册门禁；gates re-check at exact commit ≈ 预注册 SHA256 锁存 + 验证对象=最终对象；friction map ≈ 判据自审/审计工具本身；"在看结果前先定判据"≈ 本仓防后知纪律。<b>但同构 ≠ 独立验证</b>——这是两个不同来源各自收敛到相似做法，不能互相当作证据。</div>

<h2>二、逐判据结果</h2>
{crit_html}

<h2>三、数字自洽性核对（真实复算，非字符串匹配）</h2>
<table><tr><th>原文声称</th><th>复算</th><th>判定</th></tr>{num_rows}</table>
<div class="note"><b>唯一两处口径漂移（均轻微）：</b>① L190"agents fixed all of them（86 个）"vs L198"74 Fixed in those four days"——前者无时间限定、后者限定四天，属口径差异非硬矛盾；② L292"2.5 times"vs L298"2.4 times higher"，而 2235/929=2.406，2.4 精确、2.5 偏高。<b>所有数字经真实除法复算</b>，无自相矛盾。企业自报数据未经外部审计，按"作者声称"处理。</div>

<h2>四、因果与方法论诚实度</h2>
<div class="card">
<b>因果</b>：单组前后对比 + 三周移动平均 + 固定 6 仓库集合控制口径，<b>无随机对照</b>。但 L140 主动承认"多数 AI 批准是低风险、本就不易 revert"这一混杂，并称跨风险层比较后相当——只是未给出分层后的具体数字（缺口）。<br><br>
<b>测量</b>：全部作者自报，无外部审计；但 shadow mode、风险分层、人保留高风险 是降低自证偏差的真实机制。<br><br>
<b>失败披露（本文最强诚实信号）</b>：五道护栏全部由"Without it..."真实事故倒逼，还披露 15/977 人反对、0.10% revert、140 次告警中 1 次需叫人——不是纯成功叙事。
</div>

<h2>五、判据自审：抓到 5 次失真</h2>
<p>其中 2 次是本次分析器的真实 bug（与审计文章的数字问题无关），再次印证 KB-AUDIT01：</p>
<table><tr><th>教训</th><th>失真</th><th>纠正</th></tr>{sa_rows}</table>

<h2>六、三层诚实结论</h2>
{three}

<h2>七、复述 vs 长牙：本框架该吸收什么</h2>
<div class="card"><h3>编译成门禁（长牙）</h3><ol>
<li><b>风险分级批准</b>：按风险+关键路径分流，未分级即 flag——防"一律自动/一律人工"的粗暴做法</li>
<li><b>shadow mode 先读后写</b>：新判据上线前必须 read-only 跑一段、人逐条判定——本仓"预注册"纪律的更具体形态</li>
<li><b>gates re-check at exact commit</b>：验证对象必须=最终合并对象，签字后 push 则失效——直击"验证后漂移"，可编译成哈希门禁</li>
<li><b>friction map 同规模归一化</b>：按同类 PR 规模归一化找返工热点，不凭绝对数——审计定位的严谨方法</li>
<li><b>外部动作幂等</b>：agent 并发争抢同任务要幂等——防重复执行副作用</li>
</ol></div>
<div class="card"><h3>只记观察</h3><p>38%/3000 PR 月增等规模数字——本框架不产 PR，不适用，不造模块。</p></div>
<div class="note">克制：与上一轮一致，本次仍<b>不强造通用模块</b>。"gates re-check at exact commit"与已有预注册 SHA256 锁存高度重叠，标记为其强化而非新模块；shadow mode/风险分级属方法论层，先入库为 reasoning_lesson 观察复现。</div>

<h2>八、诚实边界</h2>
<div class="note">{esc(R['honesty_boundary'])}</div>

<div class="foot">交付物：<code>runway_factory/</code> 下 runway_factory_raw.txt（原文，SHA256 锁存）、preregistration.json（锁存）、evidence.json（锁存）、engine.py、result.json、本报告。<br>方法：对象类型判定 → 预注册锁存 → 一手原文 → 真实复算 → 判据自审 → 复述/长牙决策。</div>
</div></body></html>"""
out = BASE / "runway_factory_report.html"
out.write_text(html, encoding="utf-8")
print("report written:", out, "bytes:", len(html.encode("utf-8")))
