#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 FG 对比审计 HTML 报告（自包含）。"""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parent
R = json.loads((BASE / "fg_result.json").read_text(encoding="utf-8"))
E = json.loads((BASE / "fg_evidence.json").read_text(encoding="utf-8"))

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

# 判据卡片
crit_html = ""
for cid, c in R["criteria"].items():
    checks = "".join(f"<li><code>{esc(k)}</code>: {esc(v)}</li>" for k, v in c["checks"].items())
    crit_html += f"""
    <div class="crit">
      <div class="crit-head"><span class="badge {'ok' if c['pass'] else 'no'}">{'PASS' if c['pass'] else 'FLAG'}</span>
        <strong>{cid} · {esc(c['name'])}</strong></div>
      <ul class="checks">{checks}</ul>
      <p class="finding">{esc(c['finding'])}</p>
      {'<p class="teeth"><b>长牙：</b>' + esc('；'.join(c['teeth'])) + '</p>' if c.get('teeth') else ''}
    </div>"""

# 声称核对表
claim_rows = ""
for c in E["D3_claim_vs_code"]["claims"]:
    v = c["verdict"]
    cls = "v-true" if "TRUE" in v and "MISMATCH" not in v else "v-mis"
    claim_rows += f"<tr><td>{esc(c['id'])}</td><td>{esc(c['claim'])}</td><td>{esc(c['code'][:110])}</td><td class='{cls}'>{esc(v)}</td></tr>"

# 差异归因
def bullets(items):
    return "".join(f"<li>{esc(i)}</li>" for i in items)

# 自审
sa_html = "".join(
    f"<tr><td>{i['id']}</td><td><span class='kb'>{esc(i['kb'])}</span></td><td>{esc(i['incident'])}</td><td>{esc(i['caught_by'])}</td></tr>"
    for i in R["judge_self_audit"]["incidents"]
)

# 三层结论
three = R["three_layer"]
three_html = "".join(
    f"<div class='layer'><div class='layer-k'>{esc(k)}</div><div class='layer-v'>{esc(v)}</div></div>"
    for k, v in three.items()
)

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>FastGithubOps.UI vs FastGithub · 对比审计报告</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--bd:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#58a6ff;--ok:#3fb950;--no:#f85149;--warn:#d29922;--purple:#bc8cff}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 -apple-system,"PingFang SC","Microsoft YaHei",sans-serif}}
.wrap{{max-width:1100px;margin:0 auto;padding:40px 24px 80px}}
h1{{font-size:28px;margin:0 0 6px}}h2{{font-size:20px;margin:44px 0 16px;padding-left:12px;border-left:4px solid var(--acc)}}
h3{{font-size:16px;margin:0 0 10px;color:var(--acc)}}.sub{{color:var(--mut);margin-bottom:28px}}
.verdict{{display:inline-block;background:rgba(63,185,80,.12);border:1px solid var(--ok);color:var(--ok);border-radius:8px;padding:10px 18px;font-weight:700;font-size:17px;margin:8px 0 4px}}
.meta{{color:var(--mut);font-size:13px}}
table{{width:100%;border-collapse:collapse;margin:14px 0;background:var(--card);border-radius:8px;overflow:hidden;font-size:14px}}
th,td{{border:1px solid var(--bd);padding:9px 12px;text-align:left;vertical-align:top}}th{{background:#1c2128;color:var(--acc)}}
.v-true{{color:var(--ok);font-weight:700}}.v-mis{{color:var(--warn);font-weight:700}}
.kb{{background:rgba(188,140,255,.15);color:var(--purple);border-radius:4px;padding:1px 7px;font-size:12px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px 20px;margin:14px 0}}
.crit{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:14px 18px;margin:12px 0}}
.crit-head{{display:flex;align-items:center;gap:10px;font-size:15px}}.badge{{font-size:11px;font-weight:800;padding:2px 9px;border-radius:20px}}
.badge.ok{{background:rgba(63,185,80,.15);color:var(--ok)}}.badge.no{{background:rgba(248,81,73,.15);color:var(--no)}}
.checks{{margin:10px 0 6px;padding-left:20px;color:var(--mut);font-size:13px}}.checks code{{color:var(--fg);background:#21262d;padding:1px 6px;border-radius:4px}}
.finding{{margin:6px 0 0;color:var(--fg)}}.teeth{{margin:8px 0 0;color:var(--warn);font-size:13px}}
.lin{{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin:16px 0}}
.node{{background:var(--card);border:1px solid var(--bd);border-radius:8px;padding:12px 16px;min-width:210px}}
.node .t{{font-weight:700}}.node .m{{color:var(--mut);font-size:12px}}
.node.up{{border-color:var(--acc)}}.node.dn{{border-color:var(--purple)}}
.arrow{{color:var(--warn);font-size:22px}}
.layer{{display:flex;gap:14px;padding:12px 0;border-bottom:1px solid var(--bd)}}
.layer-k{{flex:0 0 56px;color:var(--acc);font-weight:700}}.layer-v{{flex:1}}
.note{{background:rgba(210,153,34,.08);border-left:3px solid var(--warn);padding:12px 16px;border-radius:0 8px 8px 0;margin:14px 0;color:#e3c07b}}
code{{font-family:ui-monospace,Menlo,Consolas,monospace}}.foot{{margin-top:46px;color:var(--mut);font-size:12px;border-top:1px solid var(--bd);padding-top:16px}}
</style></head><body><div class="wrap">

<h1>FastGithubOps.UI <span style="color:var(--mut)">vs</span> FastGithub</h1>
<div class="sub">本仓 SVL 框架方法 · 对比审计（第五类任务：谱系对比审计 · 判据适配对象 KB-STRUCT01 扩展落地）</div>
<div class="verdict">{esc(R['verdict'])}</div>
<div class="meta">判据通过 {R['criteria_passed']}/{R['criteria_total']} · 判据自审 {len(R['judge_self_audit']['incidents'])} 次拦截 · 生成于 2026-11-21</div>

<h2>一、谱系关系（一手证据）</h2>
<div class="lin">
  <div class="node up"><div class="t">yuan71058/FastGithub</div><div class="m">上游 · 2026-07-16 · ★65 / fork17<br>master · 174 文件 · C#/.NET<br>fork_flag=false</div></div>
  <div class="arrow">──派生──▶</div>
  <div class="node dn"><div class="t">jsyzc2019/FastGithubOps.UI</div><div class="m">下游 · 2026-10-02（晚 78 天）· ★2<br>main · 220 文件 · 复制式派生<br>fork_flag=false</div></div>
</div>
<div class="card">
  <b>结论：</b>{esc(E['D1_lineage']['verdict'])}<br>
  下游 description 与 README <b>自陈</b>："在 yuan71058/FastGithub v2.3.1 基础上，与 docmirror/dev-sidecar 逐项对比后取长补短的优化版"。
  交叉证据：创建时间上游在先、9 个项目文件同名同构、fork_flag 均 false（复制式派生更隐蔽）、致谢体系统一标注来源。
</div>
<div class="note">谱系污染警示（KB-STRUCT02）：两项目代码高度同构，但<b>同构部分是继承，不构成相互独立验证</b>。下游是否为真"优化"，须逐条核对代码而非采信描述。</div>

<h2>二、项目概览对比</h2>
<table><tr><th>维度</th><th>FastGithub（上游）</th><th>FastGithubOps.UI（下游）</th></tr>
<tr><td>定位</td><td>GitHub 加速工具（透明拦截 / DNS 劫持 / WinDivert）</td><td>上游的"取长补短优化版" + 生态调研</td></tr>
<tr><td>文件 / 语言</td><td>174 blobs · C#</td><td>220 blobs（+46）· C#</td></tr>
<tr><td>目标框架</td><td>net7.0，包版本 7.0.0-rc*</td><td>net10.0，包版本固定 10.0.0（RC 包已下架不可还原）</td></tr>
<tr><td>健康度反馈</td><td>基础 ReportSuccess/Failure/IsFailed</td><td>IpHealthTracker（成功率+连续失败+分级拉黑）+ IpHealthSnapshot</td></tr>
<tr><td>污染 IP 过滤</td><td>仅 loopback 过滤</td><td>IpAddressFilter：全网段 + face:b00c 特征 + ::ffff 映射防御</td></tr>
<tr><td>自检体系</td><td>无</td><td>10 个 SelfTest + <code>--SelfTest</code> 调用链 + CI 冒烟</td></tr>
<tr><td>文档</td><td>README / CODE_WIKI</td><td>另增 5 份中文分析文档（上游对照 / 日志分析 / 生态调研）</td></tr>
</table>

<h2>三、逐判据结果</h2>
{crit_html}

<h2>四、优化声称 vs 代码（claim-vs-code）</h2>
<table><tr><th>声称</th><th>README 表述</th><th>代码实现（定位）</th><th>判定</th></tr>{claim_rows}</table>
<div class="note"><b>两处文档口径不一致（非功能缺陷）：</b><br>
① <b>超时"10s→5s"</b>：README 数字与三方对不上——下游代码 <code>defaultConnectTimeout=10s</code> / <code>totalConnectBudget=10s</code>（注释 20s→10s）、上游基线 <code>1.5s</code>、演进日志（v2.4.0 10→4s / v2.4.4 4→2s）。属 README 未随迭代更新的文档漂移。<br>
② <b>"新增反馈接口"</b>：上游本就有 ReportSuccess/Failure/IsFailed；下游将其抽为 IIpHealthFeedback 接口并新增 GetIpHealth() 快照，文件反而变小（1725B&lt;1957B）。属"重构"被写成"新增"的口径问题。</div>

<h2>五、差异归因：净贡献真实，但含借鉴移植</h2>
<div class="card"><h3>自研 / 强化</h3><ul>{bullets(E['D4_attribution']['self_research'])}</ul></div>
<div class="card"><h3>借鉴 dev-sidecar（README 明确标注来源）</h3><ul>{bullets(E['D4_attribution']['borrowed_from_dev_sidecar'])}</ul></div>
<div class="card"><h3>继承上游基座</h3><ul>{bullets(E['D4_attribution']['borrowed_from_upstream'])}</ul></div>
<p class="finding">{esc(E['D4_attribution']['verdict'])}</p>

<h2>六、判据自审：抓到 3 次"检查方法失真"</h2>
<p>判据自审纪律：结果反直觉时先怀疑检查器，而非被审对象。本次 KB-AUDIT01 / KB-AUDIT02 首次真实迁移即 3 次拦截：</p>
<table><tr><th>#</th><th>触发教训</th><th>失真事件</th><th>纠正方式</th></tr>{sa_html}</table>
<div class="note">{esc(R['judge_self_audit']['note'])}</div>

<h2>七、三层诚实结论</h2>
{three_html}

<h2>八、复述 / 长牙决策（KB-META01）</h2>
<p>能指出具体被拦动作者列为"长牙候选"，否则只记观察：</p>
<ul>
<li><b style="color:var(--warn)">SelfTest 写好了却没调用点 = 从未执行</b> → 拦：测试存在但无调用点则 flag（下游 Program.cs 自己长出了这道牙齿）</li>
<li><b style="color:var(--warn)">小样本期禁用成功率判定</b> → 拦：统计量样本不足仍生效则 flag（1 次失败=成功率 0 的误杀）</li>
<li><b style="color:var(--warn)">文档声称值与代码值漂移</b> → 拦：声称≠代码需两处交叉确认（KB-AUDIT02 已覆盖）</li>
<li><span style="color:var(--mut)">生态调研用 API 实测——观察（本仓已有取证纪律，不重复造）</span></li>
</ul>

<h2>九、诚实边界</h2>
<div class="note">{esc(R['honesty_boundary'])}</div>

<div class="foot">
交付物：<code>audit_fg_compare/</code> 下 fg_preregistration.json（SHA256 锁存）、fg_evidence.json（锁存）、fg_evidence_amendment.json（锁存）、fg_audit_engine.py、fg_result.json、本报告。<br>
方法：本仓 SVL 框架 · 对象类型判定 → 预注册锁存 → 一手证据 → 判据执行 → 判据自审 → 复述/长牙决策。
</div>
</div></body></html>"""

out = BASE / "fg_compare_audit_report.html"
out.write_text(html, encoding="utf-8")
print("report written:", out, "bytes:", len(html.encode("utf-8")))
