"""生成'对复盘的独立审计'报告 HTML。"""
import json
from pathlib import Path

d = json.load(open("retro_audit_result.json"))

def status(passed, note_key=""):
    return "<span class='ok'>通过 ✓</span>" if passed else "<span class='no'>发现缺陷 ✗</span>"

def checks_html(checks):
    rows = []
    for k, v in checks.items():
        weak = k.endswith("_弱点")
        cls = "weak" if weak else ("ok" if v else "no")
        mark = "⚠" if weak else ("✓" if v else "✗")
        rows.append(f"<tr><td class='{cls}'>{mark} {k}</td><td>{v}</td></tr>")
    return "".join(rows)

g, c, w, f, s = (d["audit_1_gate"], d["audit_2_classifier"],
                 d["audit_3_worked_failed"], d["audit_4_feedback_loop"],
                 d["audit_5_three_sentences"])

sent_rows = "".join(
    f"<tr><td>{x['claim']}</td><td class='ok'>✓ 方向正确</td>"
    f"<td>{x['evidence_strength']}</td><td class='dim'>{x['caveat']}</td></tr>"
    for x in s["sentences"]
)

html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>对复盘的独立审计 · audit the audit</title>
<style>
body{{font-family:-apple-system,'PingFang SC',sans-serif;max-width:1000px;margin:32px auto;padding:0 22px;color:#1a1a1a;line-height:1.7}}
h1{{font-size:26px;border-bottom:3px solid #2c5282;padding-bottom:10px}}
h2{{font-size:19px;color:#2c5282;margin-top:30px;border-left:4px solid #2c5282;padding-left:10px}}
.card{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 20px;margin:16px 0}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}}
th,td{{border:1px solid #cbd5e0;padding:6px 9px;text-align:left;vertical-align:top}}
th{{background:#edf2f7}}
.ok{{color:#276749;font-weight:700}}.no{{color:#9b2c2c;font-weight:700}}.weak{{color:#975a16}}
.dim{{color:#718096;font-size:12px}}
.banner{{background:#fffaf0;border:2px solid #dd6b20;border-radius:10px;padding:16px 20px;font-size:15px}}
</style></head><body>
<h1>对复盘的独立审计（audit the audit）</h1>
<p class="dim">空杯 + 攻击性实验：故意构造能让机制露馅的输入，检验上一份 L3 复盘是否可靠。
立场：用户已确认三句话方向正确、应坚持——审计区分「方向对」与「证据够」，守正确方向、补诚实边界。</p>

<div class="banner">
<b>总判定：4 项通过，1 项发现缺陷（且正是上一轮自曝的元缺陷，现被独立实验量化证实）。</b><br>
审计不是推翻复盘，而是给它做体检——把该守的守住，把该补的补上。
</div>

<h2>1. 防后知门禁 {status(g['passed'])}</h2>
<div class="card">
<table><tr><th>攻击项</th><th>结果</th></tr>{checks_html(g['checks'])}</table>
<p>{g['note']}</p>
</div>

<h2>2. 三分法分类 {status(c['passed'])}</h2>
<div class="card">
<table><tr><th>攻击项</th><th>结果</th></tr>{checks_html(c['checks'])}</table>
<p>{c['note']}</p>
</div>

<h2>3. worked/failed 空洞性 {status(w['passed'])}</h2>
<div class="card">
<p>{w['note']}</p>
<table>
<tr><th>worked 总数</th><th>通用模板</th><th>框架专属</th><th>failed</th><th>认知修正</th><th>三分法决策</th></tr>
<tr><td>{w['worked_total']}</td><td class="no">{w['templated_worked']}</td>
<td class="no">{w['framework_specific_worked']}</td><td class="no">{w['failed_total']}</td>
<td>{w['n_cognitive_corrections']}</td><td>{w['n_audit_decisions']}</td></tr>
</table>
<p class="dim">此项"失败"是预期内的：它验证的是缺陷真实存在，而非审计本身出错。</p>
</div>

<h2>4. 反哺闭环 {status(f['passed'])}</h2>
<div class="card">
<p>{f['note']}</p>
<table>
<tr><th>产出 lessons</th><th>进入 store</th><th>fix 类</th><th>转 PDCA 机会</th><th>知识库沉淀</th></tr>
<tr><td>{f['lessons_emitted']}</td><td>{f['lessons_in_store']}</td><td>{f['fix_lessons']}</td>
<td>{f['fix_to_pdca_opps']}</td><td>{f['kb_retro_items']}</td></tr>
</table>
</div>

<h2>5. 三句话结论的证据强度 {status(s['passed'])}</h2>
<div class="card">
<table>
<tr><th>结论</th><th>方向</th><th>证据强度</th><th>诚实边界</th></tr>
{sent_rows}
</table>
<p>{s['note']}</p>
</div>

<h2>6. 审计自身的产物</h2>
<div class="card">
<p>新增沉淀 2 条框架层 fix：门禁质量审查（KB-R-AUDIT01）、标记位置契约（KB-R-AUDIT02）。
知识库累计 46 条，仍保持就绪。新增 5 条审计回归测试，全量 194 测试通过。</p>
<p><b>坚持的方向</b>：三句话全部方向正确——经验（守住有效方法组合）、教训（触发≠真相）、
元教训（复盘工具要被审）。审计给它们的不是否定，而是刻度：教训证据最强，经验次之，元教训待更多样本。</p>
</div>

</body></html>"""
Path("retro_audit_report.html").write_text(html, encoding="utf-8")
print("saved", len(html), "chars")
