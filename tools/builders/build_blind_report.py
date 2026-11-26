"""从 finance_blind_test_result.json 生成自包含 HTML 报告。"""
import json
from pathlib import Path

D = json.load(open("/workspace/finance_blind_test_result.json", encoding="utf-8"))
m = D["metrics"]
sa = D["sample_audit"]
sens = D["sensitivity"]

# 混淆矩阵单元格
cm = m["混淆矩阵"]
cell = lambda k, v, cls: f'<div class="cmcell {cls}"><div class="cmnum">{v}</div><div class="cmlab">{k}</div></div>'

# 十家明细表
group_cn = {"normal": "正常白马", "risk": "曾风险/退市"}
rows = []
for r in D["results"]:
    alarm_cn = "⚠ 预警" if r["alarm"] else "— 未预警"
    alarm_cls = "warn" if r["alarm"] else "ok"
    op = r["label_opinion"]
    if r["label_neg"] == -1:
        lab_cls, lab_cn = "unknown", "未知·剔除"
    elif r["label_neg"] == 1:
        lab_cls, lab_cn = "bad", "非标·否定"
    else:
        lab_cls, lab_cn = "good", "标准无保留"
    rows.append(
        f'<tr><td><b>{r["name"]}</b><br><span class="code">{r["code"]}</span></td>'
        f'<td>{group_cn.get(r["group"], r["group"])}</td>'
        f'<td>{r["industry"]}</td>'
        f'<td class="{alarm_cls}">{alarm_cn}</td>'
        f'<td class="sig">{r["block"]}/{r["cash_low"]}/{r["receipt_low"]}/{r["growth_div"]}</td>'
        f'<td class="{lab_cls}">{lab_cn}<br><span class="code">{op}</span></td></tr>'
    )

# 消融表
sens_rows = []
for name, v in sens.items():
    hl = ' class="hl"' if name.startswith("A_") else ""
    sens_rows.append(
        f'<tr{hl}><td>{name}</td><td>{v["TP"]}</td><td>{v["FP"]}</td>'
        f'<td>{v["FN"]}</td><td>{v["TN"]}</td>'
        f'<td><b>{v["recall"]}</b></td><td><b>{v["precision"]}</b></td></tr>'
    )

# FP/FN 清单
fp = m["假阳性_预警但标准无保留"] or ["无"]
fn = m["假阴性_非标却无预警"] or ["无"]
tp = m["真阳性_预警且非标"] or ["无"]
tn = m["真阴性_无预警且标准无保留"] or ["无"]
unk = m["标签未知_剔除"] or ["无"]

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>反偏差盲测：十家公司五年年报叙事真实性研判</title>
<style>
:root{{--bg:#faf9f6; --ink:#1a1a1a; --muted:#666; --line:#e5e2dc;
--red:#c0392b; --green:#1e8449; --amber:#b9770e; --blue:#1f4e79; --card:#fff;}}
body{{background:var(--bg);color:var(--ink);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;
max-width:1000px;margin:0 auto;padding:32px 20px;line-height:1.7}}
h1{{font-size:26px;margin:0 0 6px}} h2{{font-size:19px;margin:34px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--line)}}
h3{{font-size:15px;margin:20px 0 8px;color:var(--blue)}}
.sub{{color:var(--muted);font-size:13px;margin-bottom:20px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.03)}}
.disclaim{{background:#fff8e1;border-left:4px solid var(--amber);padding:12px 16px;border-radius:6px;font-size:13px;color:#7a5b00;margin:16px 0}}
table{{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}}
th,td{{padding:9px 10px;text-align:left;border-bottom:1px solid var(--line)}}
th{{background:#f3f1ec;font-weight:600;color:#444}}
tr.hl{{background:#eef4fa}} .code{{color:var(--muted);font-size:11px;font-family:monospace}}
.warn{{color:var(--red);font-weight:600}} .ok{{color:var(--muted)}}
.sig{{font-family:monospace;color:var(--muted)}}
.bad{{color:var(--red);font-weight:600}} .good{{color:var(--green)}} .unknown{{color:var(--amber);font-weight:600}}
.cmgrid{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:10px}}
.cmcell{{border-radius:8px;padding:16px;text-align:center;color:#fff}}
.cmcell.tp{{background:var(--green)}} .cmcell.tn{{background:var(--blue)}}
.cmcell.fp{{background:var(--amber)}} .cmcell.fn{{background:var(--red)}}
.cmnum{{font-size:30px;font-weight:700}} .cmlab{{font-size:12px;opacity:.9;margin-top:2px}}
.kpi{{display:flex;gap:14px;flex-wrap:wrap;margin-top:12px}}
.kpi div{{flex:1;min-width:130px;background:#f3f1ec;border-radius:8px;padding:12px;text-align:center}}
.kpi b{{font-size:22px;display:block;color:var(--blue)}}
.kpi span{{font-size:12px;color:var(--muted)}}
ul{{margin:8px 0;padding-left:22px}} li{{margin:5px 0;font-size:14px}}
.tag{{display:inline-block;background:#eef4fa;color:var(--blue);border-radius:4px;padding:1px 7px;font-size:12px;margin-right:5px}}
.small{{font-size:12px;color:var(--muted)}}
</style></head><body>

<h1>反偏差盲测：十家公司五年年报叙事真实性研判</h1>
<div class="sub">终点 2026 · 年报窗口 2021–2025 · 固定种子 seed={sa['seed']} · 结局标签=2025 审计意见（同期公开，零后知）</div>

<div class="disclaim">
<b>免责声明</b>：本文为研究方法实验演示，<b>不构成任何投资建议</b>。财务数据来自公开接口加工指标，
非年报原文，可能存在口径差异与滞后。文中"叙事真实性"仅指"是否违反可符号化的财务判据"，
不等于审计结论，更不等于对任何公司的价值判断。
</div>

<h2>一、实验设计：如何对抗两类偏差</h2>
<div class="card">
<table>
<tr><th>偏差类型</th><th>本实验的具体形态</th><th>对抗手段</th></tr>
<tr><td>幸存者偏差</td><td>退市最彻底的公司（雏鹰/暴风/信威）连数据都没有，永久消失</td><td>28 家候选池先记录 3 家数据断档，再抽 10 家；缺失本身写进审计轨迹</td></tr>
<tr><td>后知·选择</td><td>知道谁暴雷才选谁</td><td>固定种子 {sa['seed']} 随机抽样，不换样；分组标签不进判据</td></tr>
<tr><td>后知·标签</td><td>用"后来被处罚/ST"这类事后标签当真值</td><td>只用 2025 年报审计意见——年报同期公开，零后知</td></tr>
<tr><td>标签泄漏</td><td>判据含审计意见=拿答案判答案</td><td>判据刻意剔除审计意见判据，只用 4 个财务符号判据</td></tr>
<tr><td>缺失当命中</td><td>"意见未取到"默认算非标，数据缺陷伪装成命中</td><td>未知标签作为第三态<b>剔除</b>出混淆矩阵</td></tr>
</table>
<p class="small">抽样：候选池 {sa['候选池大小']} 家 → 数据断档剔除 {len(sa['数据断档剔除'])} 家 → 入样池 {sa['入样池大小']} 家（正常 {sa['入样正常']}/风险 {sa['入样风险']}）→ 随机抽 10 家。</p>
<p class="small">预注册告警规则：2021-2024 出现任一恒等式违约，或现金含量LOW≥2年、收现比LOW≥2年、增速背离≥2年 → alarm=1。跑数前写死，不因个案调整。</p>
</div>

<h2>二、盲判流程</h2>
<div class="card">
<p><span class="tag">①</span>随机抽 10 家，分组只用于事后审计，不喂判据<br>
<span class="tag">②</span><b>blind_audit</b>：只读财务三表，跑 4 个坍塌映射，产出 alarm∈{{0,1}}<br>
<span class="tag">③</span><b>label_of</b>：判据产出<b>后</b>才读 2025 审计意见；未知则剔除<br>
<span class="tag">④</span><b>evaluate</b>：混淆矩阵 + 强制列出 FP / FN<br>
<span class="tag">⑤</span><b>sensitivity</b>：消融——recall 到底靠什么撑起来的</p>
</div>

<h2>三、逐家盲判 → 揭盲</h2>
<div class="card">
<table>
<tr><th>公司</th><th>分组</th><th>行业</th><th>盲判告警</th><th>信号计数<br><span class="small">违约/现金/收现/增速</span></th><th>揭盲：2025 审计意见</th></tr>
{''.join(rows)}
</table>
<p class="small">分组列仅为事后审计展示，判据运行全程未读取。⚠ 与标签分列在两栏，判据产出前彼此不可见。</p>
</div>

<h2>四、主结果：混淆矩阵</h2>
<div class="card">
<div class="cmgrid">
{cell('真阳性 TP · 预警且非标', cm['TP'], 'tp')}
{cell('假阳性 FP · 预警但标准无保留', cm['FP'], 'fp')}
{cell('假阴性 FN · 非标却无预警', cm['FN'], 'fn')}
{cell('真阴性 TN · 无预警且标准无保留', cm['TN'], 'tn')}
</div>
<div class="kpi">
<div><b>{m['召回味觉率_recall']}</b><span>召回率 recall</span></div>
<div><b>{m['特异度_specificity']}</b><span>特异度 specificity</span></div>
<div><b>{m['精确率_precision']}</b><span>精确率 precision</span></div>
<div><b>{m['参评样本']}</b><span>参评样本（剔除 1 未知）</span></div>
</div>
<p style="margin-top:16px"><b>TP</b>：{', '.join(tp)}<br>
<b class="warn">FP（最重要）</b>：{', '.join(fp)}<br>
<b>FN</b>：{', '.join(fn)}<br>
<b>TN</b>：{', '.join(tn)}<br>
<b>剔除</b>：{', '.join(unk)}</p>
<p class="small">奥瑞德前四年异常信号（收现比 4 年 &lt;0.85、增速背离 3 次）比康得新还严重，却拿到 2025 标准无保留意见。
它证明判据抓的是"财务动荡表征"，不是"造假"，更不是"审计会否定"。FP 必须与 TP 同样认真地报告，实验才算诚实。</p>
</div>

<h2>五、消融：recall=1.0 是靠什么撑起来的</h2>
<div class="card">
<table>
<tr><th>变体</th><th>TP</th><th>FP</th><th>FN</th><th>TN</th><th>recall</th><th>precision</th></tr>
{''.join(sens_rows)}
</table>
<h3>三条硬结论</h3>
<ul>
<li><b>只用增速背离（D）就复现全部 recall</b> —— "多判据协同"是假象，预警几乎完全由营收/净利背离这一个信号驱动。</li>
<li><b>拿掉增速背离（B/C），recall 掉到 0.667</b> —— 现金含量、收现比这些"看似更硬的造假克星"，单独用反而漏掉乐视。直觉在这里是错的。</li>
<li><b>阈值放宽（F），precision 从 0.75 崩到 0.429</b> —— 正常白马被大量误报。阈值 carries 主要判别力，必须随行业重标定。</li>
</ul>
<p class="small">合起来看：判据判别力集中于单一信号、对阈值高度敏感、抓的是"动荡"而非"造假"。
recall=1.0 里大部分是"困境公司必然非标"的同义反复，而非预言——乐视/康得新/宏图本就经营崩溃，
增速背离是崩溃的症状，审计非标是对同一崩溃的另一种记录。这是诊断性分析，不是新假设检验。</p>
</div>

<h2>六、证明了什么 / 没证明什么</h2>
<div class="card">
<h3>证明了</h3>
<ul>
<li>严谨的实验设计可把四类隐蔽错误（幸存者偏差、后知先觉、标签泄漏、缺失当命中）逐个显式化并堵住。</li>
<li>干净设定下判据有真实但有限的判别力：precision 0.75、specificity 0.833、假阳性率 1/6 非零，需交人裁决。</li>
<li>消融揭示判别力的真实来源，避免误以为"多判据很稳健"。</li>
</ul>
<h3>没证明 / 诚实边界</h3>
<ul>
<li>n=10（参评 9），置信区间宽到无统计意义，<b>不能外推为检出率</b>。</li>
<li>结局标签是"叙事被审计否定"的代理，<b>不是"造假"标签</b>；标准无保留 ≠ 叙事真实。</li>
<li>3 家数据断档公司被剔除，样本仍偏向"留得下数据的公司"——偏差被记录，未被消除。</li>
<li>中国平安金融业口径缺失：字段缺失会被误读成信号，跨行业必须重标定。</li>
<li>关联交易、表外结构、收入确认时点、减值充分性全部坍塌不掉，必须交人。</li>
</ul>
</div>

<h2>七、收束：把"我不知道"变成一等公民</h2>
<div class="card">
<p>这一轮最有价值的产物不是 recall=1.0，而是三个被诚实保留的"不知道"：
奥瑞德的<b>假阳性</b>、中国平安的<b>未知标签</b>、3 家退市公司的<b>数据断档</b>。
把"不知道"当一等公民——不填补、不臆断、不塞进任一类别——这才是反偏差的核心纪律。</p>
<p>判据负责把已知的符号凭证切到 O(1)，每一个"我不知道"都生成一张交人卡：
奥瑞德那张卡问的是"这家公司 2022-2024 的收现不足与净利巨震，是否有一次性重组/减值等业务解释？"
——一句话即可裁决，但绝不能由系统替人回答。</p>
<p class="small">数据来源：东方财富公开数据接口 datacenter.eastmoney.com（非官方授权源）。
生成脚本：svagent/finance_blind_test.py · 结果数据：finance_blind_test_result.json。</p>
</div>

</body></html>"""

Path("/workspace/finance_blind_test_report.html").write_text(html, encoding="utf-8")
print("报告已生成: /workspace/finance_blind_test_report.html")
