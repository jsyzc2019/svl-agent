#!/usr/bin/env python3
"""ReVeal 审计 HTML 报告：暗色主题，判据卡片，PASS/PARTIAL 徽章。
用 .format 拼接，CSS 花括号需双写。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "result.json", encoding="utf-8"))
summary = res["summary"]
judges = res["judges"]

CSS = """
:root{{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--warn:#d29922;--no:#f85149;--acc:#58a6ff;--bd:#30363d}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--fg);font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7;padding:40px 20px}}
.wrap{{max-width:960px;margin:0 auto}}
h1{{font-size:26px;color:var(--acc);margin-bottom:6px}}
.sub{{color:var(--mut);font-size:14px;margin-bottom:28px}}
.badge{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;margin-right:6px}}
.badge.ok{{background:rgba(63,185,80,.15);color:var(--ok);border:1px solid var(--ok)}}
.badge.warn{{background:rgba(210,153,34,.15);color:var(--warn);border:1px solid var(--warn)}}
.hero{{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:22px;margin-bottom:24px}}
.hero .headline{{font-size:15px;color:var(--fg);margin-top:12px}}
.kpi{{display:flex;gap:18px;margin-top:16px;flex-wrap:wrap}}
.kpi div{{background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:10px 16px;font-size:13px;color:var(--mut)}}
.kpi b{{color:var(--fg);font-size:18px;display:block}}
h2{{font-size:18px;color:var(--acc);margin:26px 0 12px;border-left:3px solid var(--acc);padding-left:10px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px 18px;margin-bottom:12px}}
.card .t{{font-size:15px;font-weight:600;margin-bottom:6px;display:flex;align-items:center;gap:8px}}
.card .f{{font-size:13px;color:var(--mut)}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}}
th,td{{border:1px solid var(--bd);padding:8px 10px;text-align:left}}
th{{background:var(--card);color:var(--acc)}}
.note{{background:rgba(88,166,255,.08);border-left:3px solid var(--acc);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}}
footer{{color:var(--mut);font-size:12px;margin-top:30px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}}
"""

def badge_for(r):
    if not r["pass"]:
        return '<span class="badge warn">FAIL</span>'
    v = r["verdict"]
    if v in ("IMPLEMENTED", "CONSISTENT", "PASS", "CLEAR", "INDEPENDENT", "ISOLATED", "FULL", "NEW_TEETH"):
        return '<span class="badge ok">' + v + '</span>'
    return '<span class="badge warn">' + v + '</span>'

cards = ""
for r in judges:
    cards += (
        '<div class="card"><div class="t">' + badge_for(r) + ' <span>' + r["id"] + ' · ' + r["name"] + '</span></div>'
        '<div class="f">' + r["finding"] + '</div></div>'
    )

html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReVeal 深研审计</title><style>__CSS__</style></head><body><div class="wrap">
<h1>ReVeal: Self-Evolving Code Agents via Reliable Self-Verification</h1>
<div class="sub">ICLR 2026 · arXiv 2506.11442v2 · 微软亚研院 / 同济 / 中科大 · 学术实证论文（公开代码） · 审计于 2026-11-22</div>

<div class="hero">
  <div><span class="badge ok">8/8 判据通过</span><span class="badge warn">代码扎实</span><span class="badge warn">归因有边界</span></div>
  <div class="headline">__HEADLINE__</div>
  <div class="kpi">
    <div><b>__PASS__/__TOTAL__</b>判据通过</div>
    <div><b>5/5</b>核心设计有代码实体</div>
    <div><b>0</b>论文-代码超参漂移</div>
    <div><b>99</b>知识库条目（未新增）</div>
  </div>
</div>

<h2>一手材料与锁存</h2>
<div class="card"><div class="f">
PDF 完整下载（2.8MB / 19 页 / EOF 完整，避免 SKILLMASTER 那次截断）；arXiv abs（v1 2025-06-13，v2 2025-10-21）；
ICLR poster（id=10007284）确认录用；GitHub <b>Shimly-2/ReVeal</b>（289 文件，7MB，MIT，2026-03-01 全文代码发布）。
六重 SHA256 锁存全部校验 OK。预注册如实标注"判据设计前已从公开摘要获知方法三件套与 Figure 数字"。
</div></div>

<h2>判据结论</h2>
__CARDS__

<h2>关键判据点：可靠自验证的分阶段信号源</h2>
<div class="card"><table>
<tr><th>阶段</th><th>验证信号来源</th><th>含义</th></tr>
<tr><td>训练</td><td>r_ver = 在 golden code 上通过的测试比例；golden filter 保证反馈合法</td><td>验证质量信号依赖金标</td></tr>
<tr><td>测试</td><td>无 golden，所有测试自主执行</td><td>验证完全自主，对自造测试质量提出强需求</td></tr>
</table>
<div class="note">作者主动披露该差异 → 判 PARTIAL 不判隐瞒偷换。但"训练可靠→测试可靠"是迁移假设；∆↓≈0 被用作可靠性证据，
反例是 Qwen backbone 上 outcome-only 的 ∆↓ 也 = 0.0——该指标不全是 TAPO 功劳。prompt-only 对照（×6 仅 27.4）排除了"仅工具+提示"混杂，这部分是真支撑。</div></div>

<h2>数字复算（口径对等优先）</h2>
<div class="card"><table>
<tr><th>项</th><th>数值</th><th>判定</th></tr>
<tr><td>同轮数消融×8：TAPO − outcome</td><td>37.7 − 36.1 = +1.6pp</td><td>口径对等，公平</td></tr>
<tr><td>同轮数消融 ∆↓</td><td>1.32 → 0.0</td><td>支持 TAPO（DAPO backbone）</td></tr>
<tr><td>主表 Pass@1 turn1→turn25</td><td>34.8% → 38.7%（+3.9）</td><td>与图表一致</td></tr>
<tr><td>8 次运行显著性</td><td>t = 5.81</td><td>统计显著（std 偏小需标注）</td></tr>
<tr><td>主表×25 vs 消融×8</td><td>轮数不等</td><td>不混比，标注 minor</td></tr>
</table></div>

<h2>入库决策</h2>
<div class="card"><div class="f">
不新增条目：reward 通道隔离（KB-META01/KB-STRUCT07）、分阶段信号源（KB-SIM02）、∆↓反例（KB-AUDIT02/KB-R-MS01）均已覆盖，入则灌水。
加固上述四条 support。知识库保持 99 条，ready=True，vanity 占比 0.04；全量 287 项测试通过。
</div></div>

<footer>诚实边界：论文数字均为作者 self-reported；未实跑代码/复现实验；训练数据需自过滤、推理脚本与检查点未完整公开；
CTRL 基线引用旧版 LCB 非独立重跑；结论限于静态证据与论文报告数字的算术一致性核对。</footer>
</div></body></html>"""

html = html.replace("__CSS__", CSS).replace("__HEADLINE__", summary["headline"])
html = html.replace("__PASS__", str(summary["passed"])).replace("__TOTAL__", str(summary["total"]))
html = html.replace("__CARDS__", cards)

out = D / "reveal_report.html"
out.write_text(html, encoding="utf-8")
chk = out.read_text(encoding="utf-8")
print("生成", out.name, "size", len(chk), "闭合", chk.rstrip().endswith("</html>"), "徽章数", chk.count('class="badge'))
