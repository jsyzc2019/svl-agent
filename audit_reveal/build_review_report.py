#!/usr/bin/env python3
"""§61 复盘报告：旧论文 × 新框架。暗色主题，N1-N5 判据卡片，三层诚实结论。"""
import json
from pathlib import Path

D = Path(__file__).parent
res = json.load(open(D / "review_result.json", encoding="utf-8"))
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
.card .t{font-size:15px;font-weight:600;margin-bottom:8px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.card .f{font-size:13px;color:var(--mut)}
.card .tooth{color:var(--acc);font-size:12px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
th,td{border:1px solid var(--bd);padding:8px 10px;text-align:left;vertical-align:top}
th{background:var(--card);color:var(--acc)}
.note{background:rgba(88,166,255,.08);border-left:3px solid var(--acc);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
.warnbox{background:rgba(210,153,34,.08);border-left:3px solid var(--warn);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
code{background:var(--bg);border:1px solid var(--bd);border-radius:4px;padding:1px 5px;font-size:12px;color:var(--fg)}
footer{color:var(--mut);font-size:12px;margin-top:30px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
"""


def vbadge(v, action=""):
    v = str(v)
    if v in ("block", "DOWNGRADE", "downgrade") or action == "block":
        cls, label = "no", v
    elif v in ("flag", "FLAG") or "UNDECLARED" in v or "UNVERIFIED" in v or "FLAG" in v:
        cls, label = "warn", v
    else:
        cls, label = "ok", v
    return f'<span class="badge {cls}">{label}</span>'


cards = ""
for j in judges:
    verdict = j.get("action") or j.get("verdict")
    cards += (
        '<div class="card"><div class="t">'
        + vbadge(verdict, j.get("action", ""))
        + '<span>' + j["judge"] + '</span></div>'
        + '<div class="tooth">新牙：' + j.get("code", "") + '</div>'
        + '<div class="f">' + j.get("code_fact", "") + '</div>'
        + '<div class="note">' + j.get("note", j.get("experience_hypothesis", "")) + '</div></div>'
    )

tier = res["three_tier_conclusion"]
tier_rows = ""
for label, key in [("T1 · 代码事实（一手确凿）", "tier1_code_fact"),
                   ("T2 · 推断（事实连风险）", "tier2_reasoned"),
                   ("T3 · 未核验（据实标注）", "tier3_unverified")]:
    items = "".join("<li>" + x + "</li>" for x in tier[key])
    tier_rows += f"<tr><td>{label}</td><td><ul>{items}</ul></td></tr>"

html = """<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ReVeal §61 复盘：旧论文 × 新框架</title><style>__CSS__</style></head><body><div class="wrap">
<h1>§61 复盘：ReVeal × 新框架</h1>
<div class="sub">旧论文（早期 V1-V7 已审 8/8 pass）× §56-§60 新牙重审 · arXiv 2506.11442v2 · 复盘于 2026-11-22</div>

<div class="hero">
  <div><span class="badge warn">N1 flag</span><span class="badge ok">N2 ok</span><span class="badge warn">N3 flag</span><span class="badge no">N4 block</span><span class="badge warn">N5 downgrade</span><span class="badge ok">自审 5/5</span></div>
  <div class="lead">旧框架看"作者披露了 golden/自主差异 + anti_hack=True"就放行了。新牙重咬，咬出旧框架漏掉的一处硬事实：
  <b>唯一真正衡量"测试能否区分对错代码"的信号 <code>success_output_passrate</code> 被算了，却只进观测日志，从未进入奖励</b>——
  这是 KB-AUDIT03（存在≠执行）在奖励设计上的活体案例。论文"hard-to-hack"是声称，不是证实。</div>
  <div class="kpi">
    <div><b>5</b>新判据</div>
    <div><b>5/5</b>判据自审通过</div>
    <div><b>0</b>新增 KB 条目</div>
    <div><b>101</b>知识库条目（加固 4 条）</div>
  </div>
</div>

<h2>新判据结论（N1-N5）</h2>
__CARDS__

<h2>最关键的一手代码证据</h2>
<div class="card"><table>
<tr><th>项</th><th>代码事实</th><th>含义</th></tr>
<tr><td>ver_turn_reward</td><td><code>= 1.0 * expected_output_passrate</code>（code_server.py:514）</td><td>验证奖励只=自造测试在 golden 上通过率，无区分力项</td></tr>
<tr><td>success_output_passrate</td><td>算了（:498-502,518），但只在 debug_info / compute_data_metrics（ray_trainer.py:311,491）</td><td>区分力信号<strong>存在但没接线进优化</strong>——KB-AUDIT03 活体</td></tr>
<tr><td>消融表</td><td>仅 outcome vs joint（三 reward 捆绑，paper.txt:407-410）</td><td>无单独 verification reward 消融，因果未隔离</td></tr>
<tr><td>hack 全文</td><td>仅 3 处，均为"TAPO 防 hacking"声称（:104,217,288-292）</td><td>无平凡测试/刷分的对抗实验</td></tr>
</table>
<div class="warnbox">诚实边界：以上是<strong>代码事实</strong>（确凿可判）。但"平凡测试真能刷分并损害报告性能"是<strong>经验假设</strong>，
本文未做对抗实验——只能 flag"未排除的 hacking 路径"，<strong>不得断言论文结果造假或验证无效</strong>。这正是 N1 判 flag 而非 block 的原因。</div></div>

<h2>三层诚实结论</h2>
<div class="card"><table>__TIER__</table></div>

<h2>入库决策（vanity 门禁）</h2>
<div class="card"><div class="f">
<b>不新增任何条目、不编译新门禁。</b>本次咬出的"区分力信号算了没接线"是 KB-AUDIT03 的活体新实例；
"可刷分面"对应 KB-AUDIT07；"训练/测试信息落差"对应 KB-RSI06；"TAPO turn 隔离"与本仓同构，按 KB-STRUCT02 打折。
按 §61 decision_rule：加固 KB-AUDIT03 / AUDIT07 / RSI06 / STRUCT02 各一条 support（应用实例），101 条不新增。
英雄所见略同 ≠ 独立验证——这正是"旧论文×新框架"复盘最该守住的纪律。
</div></div>

<h2>过程复盘（§54 双源）</h2>
<div class="card"><div class="f">
<b>任务源：</b>新牙重咬旧论文，咬出奖励设计里"存在≠执行"的活体案例——把 KB-AUDIT03 从"测试存在≠执行"扩展到"奖励信号存在≠进优化"。<br>
<b>过程源：</b>判据自审首版自己犯 brittle（用中文串做内容匹配），S1/S3 误报 FAIL；再修又遇到检测器自指（边界常量"一"咬自己）。
两次都按"信规则、改代码"修正——这恰是 §56 教训的现场重演，已写入 self_audit 的 docstring 留痕。
</div></div>

<footer>来源锁存：沿用 audit_reveal/source.sha256 + evidence.sha256（旧审计锁存完好）；本次预注册 review_prereg.json 分析前 SHA256 锁存 41ae1052…，
后验 review_result.json 分离。未实跑 ReVeal 代码、未复现实验；结论限于一手文本与一手代码的静态核验。</footer>
</div></body></html>"""

html = (html.replace("__CSS__", CSS)
            .replace("__CARDS__", cards)
            .replace("__TIER__", tier_rows))
out = D / "reveal_review_report.html"
out.write_text(html, encoding="utf-8")
chk = out.read_text(encoding="utf-8")
print("生成", out.name, "size", len(chk),
      "闭合", chk.rstrip().endswith("</html>"),
      "徽章数", chk.count('class="badge'))
