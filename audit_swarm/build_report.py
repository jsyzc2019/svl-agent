#!/usr/bin/env python3
"""§63 How to Train a Swarm 精研报告：判据卡片、三层诚实结论、村-城落差对照。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "result.json", encoding="utf-8"))
judges = res["judges"]
sa = res["judge_self_audit"]

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


def vbadge(action):
    cls = {"flag": "warn", "unverified": "info", "downgrade": "warn", "ok": "ok", "block": "no"}.get(action, "info")
    return f'<span class="badge {cls}">{action}</span>'


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


parts = [f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>How to Train a Swarm · SVL 精研</title><style>{CSS}</style></head><body><div class="wrap">
<h1>How to Train a Swarm — SVL 精研</h1>
<div class="sub">General Reasoning team · gr.inc/blog · 一手技术报告 Avalon-M1 (81页 PDF) · 精研时刻 2026-11-22T04:19:45+08:00</div>
<div class="hero">
<div><span class="badge ok">V1 来源真实</span><span class="badge warn">V2 数字flag</span><span class="badge info">V3 无代码unverified</span><span class="badge warn">V4 村-城flag</span><span class="badge warn">V5 insularity flag</span><span class="badge warn">V6 同构打折</span></div>
<p class="lead">工程博客 + 一手技术报告双来源，四重 SHA256 锁存。核心发现：作者主动披露 village(9 agents)→city(1000s) 落差，本仓 <code>serving_signal_gate</code> 正确给出 <b>flag</b>（vs HiGR 未披露→<b>downgrade</b>），验证门禁区分力——咬出的是 KB-AUDIT08 老条款新实例，加固不新增。</p>
</div>
"""]

# 判据卡片
parts.append("<h2>判据结论（V1–V6）</h2>")
for r in judges:
    act = r.get("action", "pass")
    code = r.get("code", "")
    head = f'<div class="t">{vbadge(act)} {esc(r["judge"])} <code>{esc(code)}</code></div>'
    body = ""
    if r["judge"] == "V1":
        body = f'<div class="f">四重来源锁存复核：{sum(r["checks"].values())}/{len(r["checks"])} 通过（博客HTML/正文 + 报告PDF/正文 + 预注册）</div>'
    elif r["judge"] == "V2":
        body = f'<div class="f">命中 {sum(r["hits"].values())}/{len(r["hits"])} 项一手数字。两处口径核对：</div><ul>'
        d = r["discrepancies"]
        body += f'<li><b>4x vs 3.9×</b>：{esc(d["4x_vs_3.9x"]["verdict"])}</li>'
        body += f'<li><b>2.4h vs 1.7h</b>：{esc(d["2.4h_vs_1.7h"]["verdict"])}</li></ul>'
        body += f'<div class="warnbox">{esc(r["note"])}</div>'
    elif r["judge"] == "V3":
        body = f'<div class="f">{esc(r["evidence"]["paperswithcode"])}；{esc(r["evidence"]["search_result"])}</div><div class="note">{esc(r["note"])}</div>'
    elif r["judge"] == "V4":
        body = f'<div class="f">调用 <code>{esc(r["gate"])}</code>：{esc(r["message"])}</div>'
        body += f'<div class="okbox"><b>对照验证</b>：{esc(r["contrast"])} → expect_met = <b>{r["expect_met"]}</b></div>'
    elif r["judge"] == "V5":
        body = f'<div class="f">{esc(r["evidence"]["report_line_2375_2404"])}</div><div class="note">{esc(r["note"])}</div>'
    elif r["judge"] == "V6":
        body = f'<div class="f">重叠：{esc(r["overlap"])}</div><div class="note">{esc(r["note"])}</div>'
    parts.append(f'<div class="card">{head}{body}</div>')

# 三层诚实结论
parts.append("<h2>三层诚实结论</h2>")
for k, cls in [("可判", "okbox"), ("不可判", "warnbox"), ("同构打折", "note")]:
    items = "".join(f"<li>{esc(x)}</li>" for x in res["three_layer"][k])
    parts.append(f'<div class="{cls}"><b>{k}</b><ul>{items}</ul></div>')

# 判据自审
sa_items = "".join(f'<li>{esc(k)}: {"PASS" if v else "FAIL"}</li>' for k, v in sa["checks"].items())
parts.append(f"""<h2>判据自审（{sum(sa['checks'].values())}/{len(sa['checks'])}）</h2>
<div class="card"><ul>{sa_items}</ul>
<div class="note">S4 自审口径自咬：V1 纯事实哈希校验无"结论层"、V4 用 <code>message</code> 承载判定说明——精确化 S4 为"产生 action 的 judge 才要求 note/message 分离"，信规则改代码后 6/6 过。同 §60/§61 家族。</div></div>""")

# 决策
parts.append(f"""<h2>认知 → 能力决策</h2>
<div class="okbox">{esc(res['decision'])}</div>
<div class="warnbox"><b>为什么这是"加固不新增"</b>：V4 咬出的村-城落差，正是 §62 从 HiGR 编译的 KB-AUDIT08（train-serving 口径不对等）。本次 GR 与 HiGR 的唯一差别是"<b>作者主动披露</b>"——门禁对同一维度给出 flag(已声明) vs downgrade(未声明) 的不同判定，恰恰证明老门禁有效，无需再造新牙。按 §61 先例，用同构印证装点"框架又验对了"才是真 vanity。</div>""")

parts.append("""<footer>SVL Agent · 一手双来源 + 四重SHA256锁存 · claim-vs-code 无代码判 UNVERIFIED 不判造假 · 同构打折 · 未授权不推送</footer>
</div></body></html>""")

out = D / "swarm_report.html"
out.write_text("".join(parts), encoding="utf-8")
print("written:", out, "bytes:", out.stat().st_size)
