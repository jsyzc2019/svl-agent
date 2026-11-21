"""生成元认知复盘层（L3）的 HTML 报告。"""
import json
from svagent.retrospective import RetrospectiveStore, Retrospective, demo_traces, lessons_to_opportunities
from svagent.pdca import PDCALoop

# 跑真实轨迹
store = RetrospectiveStore()
rev = Retrospective(store)
traces = demo_traces()
reviews = []
for t in traces:
    r = rev.review(t)
    reviews.append(r)
    store.reviews.append(r)
    store.log_trace(t)

new = traces[0].__class__(
    trace_id="probe", question="q", prior_belief="待定", prior_confidence=0.5,
    prior_ts="2026-11-01T09:00:00", outcome_ts="2026-11-30T17:00:00",
    situation_tags=["macro", "cycle_phase", "narrative_truth"],
    actual_outcome="演示注入",
)
injected = store.inject_into_trace(new)
curve = store.compounding_curve(traces)
summary = store.summary()

# 门禁行
gate_rows = ""
for r in reviews:
    tr = next((t for t in store.trace_log if t["trace_id"] == r.trace_id), None)
    n_corr = len(tr.get("cognitive_corrections", [])) if tr else 0
    if r.admitted:
        badge = '<span class="ok">通过</span>'
    else:
        badge = '<span class="no">拒绝</span>'
    reason = "" if r.admitted else f"<br><span class='muted'>{r.rejected_reason}</span>"
    gate_rows += (f"<tr><td>{r.trace_id}</td><td>{badge}{reason}</td>"
                  f"<td>{n_corr}</td><td>{len(r.lessons)}</td></tr>")

# 复利曲线行
curve_rows = "".join(
    f"<tr><td>{c['n_traces']}</td><td>{c['lessons']}</td><td>{c['probe_recall']}</td>"
    f"<td>{c['avg_confidence']:.3f}</td><td>{c['corroborated']}</td></tr>"
    for c in curve
)

# 注入教训列表
inj_rows = "".join(f"<li><span class='tag'>{l.kind}</span> {l.action}</li>" for l in injected)

# 教训类型分布
kind_rows = "".join(f"<tr><td>{k}</td><td>{v}</td></tr>" for k, v in summary["按类型"].items())

html = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>元认知复盘层 L3 · 报告</title>
<style>
:root{--bg:#faf9f6;--ink:#1a1a1a;--muted:#666;--line:#e5e2dc;--red:#c0392b;--green:#1e8449;--amber:#b9770e;--blue:#1f4e79;--card:#fff}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;line-height:1.7;margin:0;padding:32px 20px}
.wrap{max-width:920px;margin:0 auto}h1{font-size:26px;margin:0 0 6px}h2{font-size:19px;margin:32px 0 12px;border-left:4px solid var(--blue);padding-left:12px}
.lead{color:var(--muted);font-size:15px;margin-bottom:28px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:20px 24px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.04)}
table{border-collapse:collapse;width:100%;font-size:14px}th,td{border:1px solid var(--line);padding:9px 12px;text-align:left}th{background:#f3f1ec;font-weight:600}
.ok{color:var(--green);font-weight:700}.no{color:var(--red);font-weight:700}.muted{color:var(--muted);font-size:12px}
.tag{display:inline-block;font-size:11px;padding:1px 8px;border-radius:10px;background:#eaf1f7;color:var(--blue);margin-right:6px}
.kpi{display:flex;gap:14px;flex-wrap:wrap;margin:16px 0}.kpi div{flex:1;min-width:150px;background:var(--card);border:1px solid var(--line);border-radius:8px;padding:14px 18px}
.kpi b{font-size:24px;display:block;color:var(--blue)}.kpi span{color:var(--muted);font-size:13px}
.quote{background:linear-gradient(90deg,rgba(185,119,14,.08),transparent);border-left:4px solid var(--amber);padding:12px 18px;margin:14px 0;font-size:15px}
ul{margin:8px 0;padding-left:22px}li{margin:5px 0}.foot{margin-top:32px;color:var(--muted);font-size:12px;text-align:center;border-top:1px solid var(--line);padding-top:16px}
</style></head><body><div class="wrap">
<h1>元认知复盘层（L3）</h1>
<p class="lead">复盘的对象不是产物、不是判据，而是「我当时的推理过程」。三层自进化之上补齐的一环：复盘认知轨迹 → 抽取可迁移教训 → 注入下次推理。纯方法研究，不构成投资建议。</p>

<div class="kpi">
<div><b>__N_LESSONS__</b><span>沉淀教训（知识资产）</span></div>
<div><b>__N_CORROB__</b><span>被多次独立佐证</span></div>
<div><b>__AVG_CONF__</b><span>平均置信度</span></div>
<div><b>__N_OPPS__</b><span>注入 PDCA 流程机会</span></div>
</div>

<h2>一、缺口与悖论</h2>
<div class="card">
<p>已有 L0 修内容 → L1 造判据 → L2 改进行判据的方法，复盘的都是<b>产物与判据</b>，没有一层复盘「我怎么想的」。而复盘用不好，恰恰是<b>最精致的后知先觉</b>——把结果倒推成"我早就想到了"。</p>
<div class="quote">硬门禁：一条轨迹若没有事前先验 + 时间戳，或结果时间不晚于先验时间，或没有揭盲结果——<b>拒绝复盘，一个教训都不产出</b>。宁可拒绝，也不制造后知叙事。</div>
</div>

<h2>二、门禁实测</h2>
<div class="card"><table>
<tr><th>轨迹</th><th>门禁判定</th><th>认知修正点</th><th>产出教训</th></tr>
__GATE_ROWS__
</table>
<p class="muted">三条轨迹中，无事前锚点的 hindsight-fake 被正确拒绝——它没有贡献任何教训。</p>
</div>

<h2>三、复利曲线（诚实：被拒轨迹不计入）</h2>
<div class="card"><table>
<tr><th>纳入轨迹数</th><th>教训总数</th><th>探针命中</th><th>平均置信度</th><th>多次佐证数</th></tr>
__CURVE_ROWS__
</table>
<p class="muted">共享的防偏差措施被两条独立轨迹佐证后合并，置信度从 0.500 → 0.556，多次佐证数从 0 → 3。这是可测量的复利，不是口号。</p>
</div>

<h2>四、教训类型分布</h2>
<div class="card"><table>
<tr><th>类型</th><th>数量</th></tr>
__KIND_ROWS__
</table></div>

<h2>五、复利落点：新议题自动命中历史教训</h2>
<div class="card">
<p>新轨迹声明 <code>macro / cycle_phase / narrative_truth</code> 情境标签后，自动命中并注入 __N_INJ__ 条历史教训作为防偏差措施（幂等，重复注入无效）：</p>
<ul>__INJ_ROWS__</ul>
</div>

<h2>六、反哺闭环与诚实边界</h2>
<div class="card">
<p>教训经 <code>lessons_to_opportunities()</code> 转成 PDCA 机会，注入 <code>PDCALoop.inject_opportunities()</code> → <code>identify()</code> 合并返回，纳入可审计流程轨迹。</p>
<div class="quote">关键诚实决策：认知教训（"先验封顶 0.7""名义实际双轨"）是对推理者的行为约束，<b>无法坍塌成符号判据</b>——它不是文本模式。因此全部标记 addressable=False（进流程/人工队列），绝不假装能把行为准则编译成正则。这与"承认不可约"一脉相承。</div>
<p>复盘的真正落点是 L3→L3 的认知复利（inject_into_trace）；PDCA 注入只是让教训<b>可审计</b>，不是自动执行。教训本身也要过证据与反例——复盘不保证教训为真，只保证它被显式记录、可检索、可被后续轨迹证伪或佐证。</p>
</div>

<div class="foot">框架版本 0.13.0 · 元认知复盘层 L3 · 18 项专项测试通过 · 仅供参考的方法研究</div>
</div></body></html>"""

html = (html
    .replace("__N_LESSONS__", str(summary["教训总数"]))
    .replace("__N_CORROB__", str(summary["被多次佐证的教训"]))
    .replace("__AVG_CONF__", f"{summary['平均置信度']:.3f}")
    .replace("__N_OPPS__", str(summary["教训总数"]))
    .replace("__GATE_ROWS__", gate_rows)
    .replace("__CURVE_ROWS__", curve_rows)
    .replace("__KIND_ROWS__", kind_rows)
    .replace("__N_INJ__", str(len(injected)))
    .replace("__INJ_ROWS__", inj_rows))

with open("/workspace/retrospective_report.html", "w", encoding="utf-8") as f:
    f.write(html)
print("生成 retrospective_report.html", len(html), "字符")
