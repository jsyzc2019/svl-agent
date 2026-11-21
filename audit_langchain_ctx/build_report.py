#!/usr/bin/env python3
"""§64 Context Engineering Starts with Retrieval 精研报告。"""
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


def vbadge(a):
    cls = {"flag": "warn", "unverified": "info", "downgrade": "warn", "ok": "ok",
           "scoped": "info", "verified": "ok", "new_teeth_candidate": "warn", "block": "no"}.get(a, "info")
    return f'<span class="badge {cls}">{a}</span>'


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


P = [f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Context Engineering Starts with Retrieval · SVL 精研</title><style>{CSS}</style></head><body><div class="wrap">
<h1>Context Engineering Starts with Retrieval — SVL 精研</h1>
<div class="sub">Jess Weng · LangChain Deep Agents Conceptual Guide · 2026-10-23 · 精研时刻 2026-11-22T04:28:27+08:00</div>
<div class="hero">
<div><span class="badge ok">V1 来源</span><span class="badge info">V2 参数scoped</span><span class="badge ok">V3 代码verified</span><span class="badge warn">V4 检索污染新牙</span><span class="badge warn">V5/V6 同构打折</span></div>
<p class="lead">一手博客 + Deep Agents 开源源码双重核验。<b>V3 claim-vs-code 7/7 全命中</b>（glob/grep 内置、100行分页、20000 token offload、progressive disclosure 全部在源码落地）。<b>V4 咬出独立新牙</b>：检索文本污染与既有 <code>GT.SOURCE_UNTRUSTED</code>（审计输入层源身份）场景/对象/动作三者不同，编译新门禁 <code>retrieval_grounding.py</code>。</p>
</div>
"""]

P.append("<h2>判据结论（V1–V6）</h2>")
for r in judges:
    act = r.get("action", "pass")
    code = r.get("code", "")
    head = f'<div class="t">{vbadge(act)} {esc(r["judge"])} <code>{esc(code)}</code></div>'
    b = ""
    if r["judge"] == "V1":
        b = f'<div class="f">来源/预注册锁存复核：{sum(r["checks"].values())}/{len(r["checks"])} 通过</div>'
    elif r["judge"] == "V2":
        params = "".join(f"<li>{esc(k)} = {esc(v)}</li>" for k, v in r["params"].items())
        b = f'<div class="f">实现参数（非实验结论）：</div><ul>{params}</ul><div class="note">{esc(r["note"])}</div>'
    elif r["judge"] == "V3":
        hits = "".join(f'<li>{esc(k)}: {"✓" if v else "✗"}</li>' for k, v in r["hits"].items())
        b = f'<div class="f">一手源码核验（{sum(r["hits"].values())}/{len(r["hits"])}）：</div><ul>{hits}</ul>'
        b += f'<div class="note">{esc(r["repo"])}<br>{esc(r["extra_finding"])}<br><b>诚实</b>：{esc(r["honesty"])}</div>'
    elif r["judge"] == "V4":
        b = f'<div class="f">现有门禁 <code>{esc(r["gt_existing"]["code"])}</code>：{esc(r["gt_existing"]["scope"])}</div>'
        b += f'<div class="f">博客场景：{esc(r["blog_scenario"])}</div>'
        b += f'<div class="okbox"><b>独立性判定</b>：{esc(r["distinct_reason"])}</div>'
        b += f'<div class="warnbox"><b>诚实边界</b>：{esc(r["honesty_boundary"])}</div>'
        cond = "".join(f"<li>{esc(c)}</li>" for c in r["three_conditions"])
        b += f'<div class="f">判据三条件：</div><ul>{cond}</ul>'
    elif r["judge"] in ("V5", "V6"):
        b = f'<div class="f">{esc(r["overlap"])}</div><div class="note">{esc(r["note"])}</div>'
    P.append(f'<div class="card">{head}{b}</div>')

P.append("<h2>三层诚实结论</h2>")
for k, cls in [("可判", "okbox"), ("不可判", "warnbox"), ("同构打折", "note")]:
    items = "".join(f"<li>{esc(x)}</li>" for x in res["three_layer"][k])
    P.append(f'<div class="{cls}"><b>{k}</b><ul>{items}</ul></div>')

sa_items = "".join(f'<li>{esc(k)}: {"PASS" if v else "FAIL"}</li>' for k, v in sa["checks"].items())
P.append(f"""<h2>判据自审（{sum(sa['checks'].values())}/{len(sa['checks'])}）</h2>
<div class="card"><ul>{sa_items}</ul></div>""")

P.append(f"""<h2>认知 → 能力：编译新门禁</h2>
<div class="okbox">{esc(res['decision'])}</div>
<div class="note"><b>新门禁 <code>retrieval_grounding.py:check_retrieval_grounding</code></b>：未标记 data→block；无引用核对/断言不匹配/无关未隔离→downgrade；无时效性检查/字面串→flag；全自洽→ok。只判验证动作存在，绝不承诺防住注入。8 活体回归 + 13 测试 + 源码自审全过。</div>""")

P.append("""<footer>SVL Agent · 一手博客 + 开源源码 claim-vs-code · 语义枚举避 brittle · 同构打折 · 会拦才入 · 遵循 §58 选 A 不接 run_loop · 未授权不推送</footer>
</div></body></html>""")

out = D / "ctx_report.html"
out.write_text("".join(P), encoding="utf-8")
print("written:", out, "bytes:", out.stat().st_size)
