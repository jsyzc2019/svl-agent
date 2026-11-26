"""生成上证综指有效性论证报告 HTML。"""
import json
from pathlib import Path

R = json.load(open("sse_full_result.json"))
T = R["tests"]
D = R["diagnosis"]
C = R["independent_conclusion"]

def vr_rows():
    rows = ""
    for q, v in T["F2_variance_ratio"].items():
        rows += (f"<tr><td>q={q}</td><td>{v['vr']:.4f}</td><td>{v['z']:.2f}</td>"
                 f"<td class='{'no' if v['sig_1pct'] else 'ok'}'>"
                 f"{'显著偏离1' if v['sig_1pct'] else '不显著'}</td></tr>")
    return rows

def bt_rows():
    rows = ""
    labels = {"buy_hold":"买入持有(基线)","momentum20":"动量20日","reversal5":"反转5日","ma20_timing":"均线MA20(前视修复后)"}
    for k, v in T["H0_backtest"].items():
        exc = f"{v['excess']:+.2%}" if "excess" in v else "—"
        cls = "ok" if ("excess" not in v or v["excess"]>0) else "no"
        rows += (f"<tr><td>{labels[k]}</td><td>{v['annual']:+.2%}</td>"
                 f"<td>{v['sharpe']:.2f}</td><td class='{cls}'>{exc}</td></tr>")
    return rows

html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>上证综指有效性 — 独立数据论证</title>
<style>
body{{font-family:-apple-system,'PingFang SC',sans-serif;max-width:1000px;margin:32px auto;padding:0 22px;color:#1a1a1a;line-height:1.7}}
h1{{font-size:26px;border-bottom:3px solid #2c5282;padding-bottom:10px}}
h2{{font-size:19px;color:#2c5282;margin-top:30px;border-left:4px solid #2c5282;padding-left:10px}}
.card{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 20px;margin:16px 0}}
table{{border-collapse:collapse;width:100%;font-size:13px;margin:10px 0}}
th,td{{border:1px solid #cbd5e0;padding:6px 9px;text-align:left}}
th{{background:#edf2f7}}
.ok{{color:#276749;font-weight:700}}.no{{color:#9b2c2c;font-weight:700}}.dim{{color:#718096;font-size:12px}}
.verdict{{background:#fffaf0;border:2px solid #dd6b20;border-radius:10px;padding:18px 22px}}
.bug{{background:#fff5f5;border:2px solid #c53030;border-radius:10px;padding:16px 20px}}
</style></head><body>
<h1>上证综指有效性 — 独立数据论证</h1>
<p class="dim">预注册判据 SHA256 {R.get('prereg_sha256_verified','')[:16]}… 锁存后揭盲；只借用检验工具，不用现成结论；结论独立提出。</p>

<div class="card">
<b>范围声明</b>：仅检验<b>弱式有效性</b>（历史价量是否已被价格反映）；半强式/强式无法用价量数据检验，明确排除。<br>
<b>数据</b>：上证综指 {R['n_returns']} 个日收益（{R['date_range'][0]} ~ {R['date_range'][1]}），akshare + 腾讯源交叉核对一致。<br>
<b>原假设</b>：收益近似随机游走、不可预测；<b>对照</b>：{R['n_random_walks']} 条同参数随机游走。
</div>

<h2>一、统计检验（揭盲）</h2>
<table>
<tr><th>检验</th><th>结果</th><th>判定</th></tr>
<tr><td>F1 序列相关 Ljung-Box Q(10)</td><td>Q={T['F1_autocorr']['lb_stat']}, p≈{T['F1_autocorr']['lb_p']:.2g}, lag1 ρ={T['F1_autocorr']['ac1_10'][0]}</td><td class="no">统计显著（但ρ很小）</td></tr>
<tr><td>F2 方差比 VR</td><td colspan="2">见下表——全部 &gt;1 且随q递增</td></tr>
</table>
<table><tr><th>q</th><th>VR</th><th>z</th><th>1%显著性</th></tr>{vr_rows()}</table>
<table>
<tr><td>F3 游程检验</td><td>z={T['F3_runs']['z']}</td><td class="ok">不显著</td></tr>
<tr><td>F4 日历效应</td><td>max|t|={T['F4_calendar']['max_abs_t']}（校正临界≈{D['calendar']['bonferroni_crit']}）</td><td class="ok">未过多重比较，假象</td></tr>
<tr><td><b>G0 随机游走对照</b></td><td>异常度 {T['G0_random_walk_control']['real_anomaly_total']}，排名 201/201，分位 1.00</td><td class="no">触发"偏离随机游走"</td></tr>
</table>

<h2>二、决定性诊断：前视偏差 bug</h2>
<div class="bug">
<b>发现并实现修复了一个严重实现错误。</b>初版均线择时回测用当天收盘价 close[idx] 生成信号，却把当天收益 r[idx] 计入该信号——
这是用未来信息决策（look-ahead bias），恰恰违反预注册里"防未来函数"的要求。<br><br>
<table>
<tr><th>MA20策略</th><th>年化收益</th><th>夏普</th></tr>
<tr><td>修复前（含前视偏差）</td><td class="no">+26.2%</td><td>2.52</td></tr>
<tr><td>修复后（t-1信号、t日执行）</td><td class="ok">-9.0%</td><td>-0.78</td></tr>
</table>
那个惊艳的 +24.7% 超额收益是<b>前视偏差制造的幻觉</b>。修正后所有均线策略（MA5~MA250）全部为负收益。
</div>

<h2>三、经济可预测性回测（前视修复后，样本外30%）</h2>
<table><tr><th>策略</th><th>年化</th><th>夏普</th><th>超额(vs买入持有)</th></tr>{bt_rows()}</table>
<p class="dim">交易成本：单边0.15%（佣金+印花税+冲击）。所有策略扣成本后均跑输买入持有，Wilcoxon/Bonferroni门槛均未达到。参数敏感性MA5~MA250全部为负，非参数幸运。</p>

<h2>四、VR>1 的稳健性诊断</h2>
<div class="card">
<ul>
<li><b>不是波动聚集所致</b>：收益平方 LB p=2e-9（有强波动聚集），但用 GARCH 随机游走对照复核，真实 VR 仍在 100% 分位——排除了对照机制错配。</li>
<li><b>不是极端日驱动</b>：剔除 65 个 |r|&gt;4σ 极端日后，VR10 仍为 {D['VR_robustness']['剔除极端日q10']}。</li>
<li><b>经济量级极小</b>：lag-1 ρ=0.046，R²仅 0.21%——统计显著但预测力微弱。</li>
<li><b>趋势性在衰减</b>：VR10 三时期 {D['VR_time_trend']['时期1']} → {D['VR_time_trend']['时期2']} → {D['VR_time_trend']['时期3']}，市场趋于有效。</li>
</ul>
</div>

<h2>五、独立结论（三层诚实）</h2>
<div class="verdict">
<b>1. 能说的</b>：统计上证综指<b>拒绝严格 iid 随机游走</b>（VR&gt;1 稳健、跨对照成立、正序列相关），
弱式有效性在<b>严格统计意义不成立</b>；但趋势性随时间明显衰减（VR10 1.30→1.07），市场在趋近有效。<br><br>
<b>2. 更重要的</b>：<b>统计拒绝 ≠ 经济可利用</b>。lag-1 R²仅0.21%，所有价量策略（动量/反转/均线）在严格无前视回测、扣除交易成本后，
全部跑输买入持有。因此<b>在经济意义上，历史价量无法带来可持续超额收益——弱式有效性近似成立</b>。<br><br>
<b>3. 不能说的</b>：仅检验弱式有效性，<b>不外推半强式/强式</b>（需公开信息/内幕信息数据）；
指数非个股，有成分调整偏差；无法排除非线性、时变、或弱到无法覆盖交易成本的规律；
交易成本模型是近似，成本假设改变会影响经济结论。
</div>

<h2>六、方法反身</h2>
<div class="card">
本次最大教训是<b>前视偏差</b>：一个实现层面的时间戳错误，就能把 -9% 的亏损策略伪装成 +26% 的暴利，
直接颠覆"市场是否可预测"的结论。这与双色球检验里的卡方未归一 bug 同类——<b>统计方法的正确性必须建立在实现正确性之上；
触发/惊艳结论出现时，先怀疑实现，再相信信号</b>。此教训已沉淀进框架知识库（KB-R-MKT01）。
</div>

<p class="dim">本研究为数据分析，不构成任何投资建议。</p>
</body></html>"""
Path("sse_report.html").write_text(html, encoding="utf-8")
print("saved", len(html), "chars")
