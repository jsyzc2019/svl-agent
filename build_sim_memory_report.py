"""生成 SIM 四要素改进记忆演示报告。"""
import json
from pathlib import Path
from svagent.improvement_memory import (
    EvaluationContext, ImprovementMemory, ImprovementRecord,
)

ROOT = Path(__file__).resolve().parent
mem = ImprovementMemory()
mem.record_many([
    ImprovementRecord(
        "P1", "premature_completion",
        "加入任务完成检查，避免缺少执行证据就宣布完成（论文git配置任务）",
        "harness:completion_guard:add_evidence_check",
        ["git_config_task"], ["git_config_task"], [],
        EvaluationContext("Claude Opus 5.5", "workspace", "git_config", 1),
        True, "2026-10-01T10:00", "2026-10-01T11:00"),
    ImprovementRecord(
        "P2", "premature_completion",
        "沿用完成检查并加质量提醒（论文光波导任务）",
        "harness:completion_guard:add_quality_reminder",
        ["waveguide_quality"], [], ["false_positive_block"],
        EvaluationContext("Gemini 3.8 Flash", "workspace", "waveguide", 2),
        True, "2026-10-02T10:00", "2026-10-02T11:00"),
    ImprovementRecord(
        "P3", "tool_retry", "加了重试逻辑，感觉更好了（无事前预测——反面例）",
        "harness:retry", [], ["some_task"], [],
        EvaluationContext("Gemini 3.8 Flash", "TB4", "coding", 3)),
])
decisions = mem.transfer_decision(EvaluationContext("Gemini 3.8 Flash", "TB4", "coding", 10))

def rows():
    out = ""
    for r in mem.records:
        hit = r.prediction_hit_rate()
        hit_s = f"{hit:.0%}" if hit is not None else "不可证伪"
        out += (
            f"<tr><td><b>{r.record_id}</b><br>{r.root_cause}</td>"
            f"<td>{r.rationale}<br><code>{r.code_ref}</code></td>"
            f"<td>{'、'.join(r.predicted) or '(无)'}</td>"
            f"<td>修:{'、'.join(r.observed_fixed) or '无'}<br>"
            f"落空:{'、'.join(r.predictions_missed()) or '无'}<br>"
            f"新bug:{('、'.join(r.observed_broken) or '无')}</td>"
            f"<td>{r.context.label()}</td><td>{hit_s}</td></tr>"
        )
    return out

def drows():
    out = ""
    for d in decisions:
        badge = {"retain": "#27ae60", "revise": "#c0392b", "verify": "#e67e22", "drop": "#7f8c8d"}[d.action]
        out += (f"<tr><td>{d.root_cause}</td>"
                f"<td style='color:{badge};font-weight:bold'>{d.action}</td>"
                f"<td>{'—' if d.hit_rate is None else f'{d.hit_rate:.0%}'}</td>"
                f"<td>{'是' if d.regression else '否'}</td><td>{d.reason}</td></tr>")
    return out

html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><title>SIM 四要素改进记忆</title>
<style>
body{{font-family:-apple-system,'PingFang SC',sans-serif;max-width:1050px;margin:0 auto;padding:30px 22px;line-height:1.7;color:#2c3e50;background:#fafbfc}}
h1{{border-bottom:3px solid #2980b9;padding-bottom:10px}} h2{{margin-top:34px;border-left:4px solid #2980b9;padding-left:12px}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:12px 0}} th,td{{border:1px solid #dfe4ea;padding:8px;text-align:left;vertical-align:top}}
th{{background:#eef1f4}} code{{background:#f1f2f6;padding:1px 4px;border-radius:3px;font-size:12px}}
.card{{background:#fff;border:1px solid #e1e5ea;border-radius:8px;padding:14px 18px;margin:12px 0}}
.small{{font-size:13px;color:#7f8c8d}} .red{{color:#c0392b}} .green{{color:#27ae60}}
</style></head><body>
<h1>SIM 四要素改进记忆 · 可执行借鉴</h1>
<p class="small">源自 arXiv:2611.18856 的 Rationale / Predicted / Observed / Evaluation context；编译为 svagent/improvement_memory.py</p>
<div class="card"><b>为什么要借鉴：</b>本项目原知识库只有事后记述(mechanism/support/evidence)，没有"改之前预期什么"，因此<b class="red">不可证伪</b>——与第32节康波文同病。四要素里的 <b>Predicted↔Observed 配对</b>正好把经验变成"可被现实打脸的假设"。</div>

<h2>一、四要素记录（论文两案例 + 一条反面例）</h2>
<table><tr><th>根因/ID</th><th>①Rationale(动机+代码)</th><th>②Predicted(事前)</th><th>③Observed(实测)</th><th>④Context(上下文)</th><th>命中率</th></tr>
{rows()}</table>
<p class="small">P1：预测修复git任务→实测成功，命中100%。P2：换模型/任务后预测落空(waveguide_quality)且引入新bug→命中0%并触发回归标记。P3：没有事前预测→判"不可证伪"，不给命中率。可证伪率={mem.falsifiability_rate():.0%}（3条中2条）。</p>

<h2>二、从配对长出的判据（不只是存字段）</h2>
<div class="card">
<p><b>预测落空 / 意外收获</b>：<code>predictions_missed()</code>=预测−实测修复；<code>unexpected_fixes()</code>=实测−预测。落空是最该记住的失败，意外收获提示未建模的机制。</p>
<p><b>回归强制标记</b>：<code>has_regression()</code> 让"引入新bug"必须显式登记，优先级高于命中率。</p>
<p><b>防后知门禁</b>：<code>causality_ok()</code> 要求 observed_at ≥ predicted_at，违者判事后编造、证据降级。</p>
<p><b>可证伪门槛</b>：无 predicted 的记录 <code>falsifiable=False</code>，迁移决策强制降为 verify。</p>
</div>

<h2>三、跨上下文迁移决策（对应论文 Opus→Gemini 倒退现象）</h2>
<table><tr><th>根因</th><th>决策</th><th>命中率</th><th>有回归</th><th>理由</th></tr>{drows()}</table>
<p class="small">规则写死、不事后加权：回归 &gt; 后知违规 &gt; 不可证伪 &gt; 低命中(&lt;0.5) &gt; 上下文不符 &gt; 保留。论文实测 Opus 演化 harness 迁到 Gemini 起点 68.41 低于原始 seed 73.89——本模块的 "上下文不符→verify" 正是对这一现象的机制化防范。</p>

<h2>四、与知识库桥接</h2>
<div class="card"><p><code>to_knowledge_item_kwargs()</code> 把 predicted/fixed/missed/regression/context 写进 support 与 action，使入库的经验自带可证伪预期，而非一句事后结论。已沉淀 KB-SIM07~10：可证伪配对、回归降级、上下文是经验的一部分、防后知迁移。</p></div>

<p class="small">本演示为研究方法演练；数据取自论文公开案例，不构成投资建议。</p>
</body></html>"""
(ROOT / "sim_memory_report.html").write_text(html, encoding="utf-8")
print("saved sim_memory_report.html")
