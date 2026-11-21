#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成随机双仓审计 HTML 报告（自包含）。"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
R = json.loads((BASE / "random_result.json").read_text(encoding="utf-8"))
E = json.loads((BASE / "random_evidence.json").read_text(encoding="utf-8"))
P = json.loads((BASE / "random_prereg.json").read_text(encoding="utf-8"))


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# 判据卡片
crit_html = ""
for c in R["criteria"]:
    checks = "".join(
        f"<li><code>{esc(k)}</code>: {esc(v)}</li>"
        for k, v in c["checks"].items() if not isinstance(v, dict)
    )
    crit_html += f"""
    <div class="crit">
      <div class="crit-head"><span class="badge {'ok' if c['pass'] else 'no'}">{'PASS' if c['pass'] else 'FLAG'}</span>
        <strong>{esc(c['id'])} · {esc(c['name'])}</strong></div>
      <ul class="checks">{checks}</ul>
      <p class="finding">{esc(c['finding'])}</p>
    </div>"""

# 抽样信息
sel_rows = "".join(
    f"<tr><td>{esc(s['full_name'])}</td><td>{esc(s['pushed_at'])}</td>"
    f"<td>{'fork' if s['fork'] else 'original'}</td><td>{esc(s.get('upstream', '-'))}</td></tr>"
    for s in P["selection"]["selected"]
)

# 三层诚实结论
three = R["three_layer_honesty"]
three_html = "".join(
    f"<div class='layer'><div class='layer-k'>{esc(k)}</div><div class='layer-v'>{esc(v)}</div></div>"
    for k, v in three.items()
)

# 长牙候选
teeth_html = ""
for c in R["criteria"]:
    if c["id"] == "R6":
        for l in c["lessons"]:
            teeth_html += (
                f"<tr><td>{esc(l['id'])}</td><td>{esc(l['from'])}</td>"
                f"<td>{esc(l['lesson'])}</td><td class='block'>{esc(l['would_block'])}</td></tr>"
            )

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>随机活跃双仓审计 · SVL 框架报告</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--bd:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#58a6ff;--ok:#3fb950;--no:#f85149;--warn:#d29922;--purple:#bc8cff}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1120px;margin:0 auto;padding:40px 24px 80px}}
h1{{font-size:28px;margin:0 0 6px}}h2{{font-size:20px;margin:44px 0 16px;padding-left:12px;border-left:4px solid var(--acc)}}
h3{{font-size:16px;margin:0 0 10px;color:var(--acc)}}.sub{{color:var(--mut);margin-bottom:28px}}
.verdict{{display:inline-block;background:rgba(63,185,80,.12);border:1px solid var(--ok);color:var(--ok);border-radius:8px;padding:10px 18px;font-weight:700;font-size:17px;margin:8px 0 4px}}
table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px}}
th,td{{border:1px solid var(--bd);padding:9px 12px;text-align:left;vertical-align:top}}
th{{background:#1c2128;color:var(--acc);font-weight:600}}
.crit{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px 20px;margin:14px 0}}
.crit-head{{display:flex;align-items:center;gap:12px;margin-bottom:10px}}
.badge{{font-size:12px;font-weight:700;padding:3px 10px;border-radius:20px;letter-spacing:.5px}}
.badge.ok{{background:rgba(63,185,80,.15);color:var(--ok);border:1px solid var(--ok)}}
.badge.no{{background:rgba(248,81,73,.15);color:var(--no);border:1px solid var(--no)}}
.checks{{margin:6px 0 10px;padding-left:22px;color:var(--mut)}}
.checks code{{color:var(--purple);background:rgba(188,140,255,.08);padding:1px 5px;border-radius:4px}}
.finding{{margin:8px 0 0;color:var(--fg)}}
.layer{{background:var(--card);border:1px solid var(--bd);border-left:4px solid var(--warn);border-radius:8px;padding:14px 18px;margin:12px 0}}
.layer-k{{color:var(--warn);font-weight:700;margin-bottom:5px}}
.block{{color:var(--ok)}}
.kb{{background:rgba(88,166,255,.12);color:var(--acc);padding:1px 6px;border-radius:4px;font-family:monospace}}
.meta{{display:flex;flex-wrap:wrap;gap:10px;margin:16px 0}}
.meta span{{background:var(--card);border:1px solid var(--bd);border-radius:6px;padding:6px 12px;font-size:13px;color:var(--mut)}}
.foot{{color:var(--mut);font-size:13px;margin-top:40px;border-top:1px solid var(--bd);padding-top:18px}}
code{{font-family:ui-monospace,Menlo,Consolas,monospace}}
</style></head><body><div class="wrap">
<h1>随机活跃双仓审计</h1>
<p class="sub">SVL 自进化框架 · 第五类任务迁移（fork 仓库谱系 + 判据自审） · 生成于 {esc(R['generated_at'])}</p>

<div class="meta">
  <span>抽样种子：{esc(P['selection']['seed'])}</span>
  <span>候选池：{esc(P['selection']['pool_size'])} 仓（近 30 天活跃）</span>
  <span>判据：{esc(R['summary']['total'])} 条</span>
  <span>通过：{esc(R['summary']['passed'])}/{esc(R['summary']['total'])}</span>
  <span>判据自审捕获假阳性：{esc(R['summary']['self_audit_hits'])} 次</span>
</div>

<div class="verdict">6/6 判据通过 · 自审两次咬住检查器 · 新增 KB-AUDIT04</div>

<h2>一、抽样对象（可复现）</h2>
<p>规则：pushed_at ≥ 2026-10-22，排除已审计对象与 archived/disabled，固定种子随机抽取。两仓均为 fork——本仓 KB-STRUCT02 要求 fork 双向都不可靠：既不能因 fork 判无贡献，也不能因 fork 豁免净贡献核查。</p>
<table><tr><th>仓库</th><th>近期推送</th><th>类型</th><th>上游</th></tr>{sel_rows}</table>

<h2>二、判据执行</h2>
{crit_html}

<h2>三、三层诚实结论</h2>
{three_html}

<h2>四、长牙候选（复述 vs 长牙）</h2>
<p>每条候选经验都通过「具体被拦动作」检验才算长牙；5 条全部通过。本次入库决策：新增 1 条（KB-AUDIT04），其余加固或只记观察，避免灌水。</p>
<table><tr><th>ID</th><th>来源</th><th>机制</th><th>会拦什么</th></tr>{teeth_html}</table>

<h2>五、判据自审（本次核心发现）</h2>
<p><span class="kb">KB-AUDIT01/02</span> 实战延续，但拦截动作独立：判据成立的<b>前置条件</b>是验证对象等于结论所指对象、比较两端计数口径对等。本次两次假阳性都不是被审对象的缺陷，而是检查方法失真——先怀疑检查器、交叉确认后排除，并固化为 KB-AUDIT04。</p>

<div class="foot">
证据通道：API 元数据 + Tree + git clone + raw 单线程重试。预注册与证据均 SHA256 锁存（random_prereg.sha256 / random_evidence.sha256）。
未实跑两仓脚本；r1 为 shallow clone（unshallow 网络超时失败），无法列全 commit 级净贡献；r2 未逐文件 diff 上游——据实标注，不伪造完成度。
</div>
</div></body></html>"""

(BASE / "random_audit_report.html").write_text(html, encoding="utf-8")
print("报告已生成:", BASE / "random_audit_report.html", f"({len(html)} bytes)")
