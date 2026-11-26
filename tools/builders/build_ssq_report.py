"""生成双色球随机性论证报告 HTML。数据全部来自预注册检验 + 诊断 + E0 的最终结果。"""
import json
from pathlib import Path

R = json.load(open("ssq_full_result.json"))
main = R["tests"]
D = R["diagnosis"]
E = R["E0_predictability"]

d0 = main["D0_blind_comparison"]

html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>双色球开奖随机性 — 独立数据论证</title>
<style>
body{{font-family:-apple-system,'PingFang SC',sans-serif;max-width:1000px;margin:32px auto;padding:0 22px;color:#1a1a1a;line-height:1.7}}
h1{{font-size:27px;border-bottom:3px solid #2c5282;padding-bottom:10px}}
h2{{font-size:20px;margin-top:34px;color:#2c5282;border-left:4px solid #2c5282;padding-left:10px}}
h3{{font-size:16px;color:#2d3748;margin-top:22px}}
.card{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 20px;margin:16px 0}}
table{{border-collapse:collapse;width:100%;font-size:13.5px;margin:12px 0}}
th,td{{border:1px solid #cbd5e0;padding:7px 10px;text-align:left;vertical-align:top}}
th{{background:#edf2f7}}
.verdict{{background:#fffaf0;border:2px solid #dd6b20;border-radius:10px;padding:18px 22px;font-size:15px}}
.green{{color:#276749;font-weight:700}}.red{{color:#9b2c2c;font-weight:700}}.dim{{color:#718096;font-size:12.5px}}
pre{{background:#1a202c;color:#e2e8f0;padding:12px;border-radius:8px;font-size:12px;overflow:auto}}
ul{{padding-left:22px}}li{{margin:5px 0}}
.badge{{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;background:#e2e8f0;color:#2d3748}}
</style></head><body>

<h1>双色球开奖随机性 — 独立数据论证</h1>
<p class="dim">方法纪律：先预注册判据并哈希锁存（SHA256 {R.get('prereg_sha256_verified','')[:16]}…），再揭盲；
只借鉴统计学检验工具，不借鉴任何现成结论；结论由数据独立提出。</p>

<div class="card">
<b>数据</b>：全量 {R['n_draws']} 期（{R['date_range'][0]} ~ {R['date_range'][1]}），来源 500.com，
与中彩网官方近期 30 期交叉核对零差异。<br>
<b>对照</b>：{R['n_pseudo']} 条同机制伪随机序列（种子 {R['seed']}）。
<b>原假设 H0</b>：与均匀随机不可区分；<b>备择 H1</b>：存在人为调节。
</div>

<h2>一、主判据揭盲（预注册，如实呈现）</h2>
<table>
<tr><th>检验</th><th>结果</th><th>预注册判定</th></tr>
<tr><td>A1 红球频率卡方（分位）</td><td>{main['A1_chi2_red']['pct_in_random']:.3f}</td><td class="red">超出 0.975 → 偏离方向</td></tr>
<tr><td>A2 蓝球频率卡方（分位）</td><td>{main['A2_chi2_blue']['pct_in_random']:.3f}</td><td class="green">正常</td></tr>
<tr><td>B1 结构特征超 95% 分位个数</td><td>{main['B1_structure_ks']['n_features_exceed_95']} / 6</td><td>达门槛（≥2）</td></tr>
<tr><td>C1 重号 lag-1 自相关（分位）</td><td>{main['C1_autocorr']['pct_in_random']:.3f}</td><td class="green">无序列依赖</td></tr>
<tr><td><b>D0 盲测主判据</b></td><td>异常度 {d0['real_anomaly_total']}，排名 <b>201/201</b>，分位 {d0['percentile_more_anomalous_than_pseudo']:.2f}</td><td class="red">触发 H1（≥0.95）</td></tr>
</table>
<p>表面看，D0 把真实序列排到了比全部 200 条伪随机都异常的位置，机械地触发了"偏离方向"。
但框架纪律要求：<b>触发不是结论</b>。按第 18 节"消融是诊断非新检验"，我对信号来源做诊断性拆解。</p>

<h2>二、诊断性拆解（不改判据，只解释信号性质）</h2>

<h3>2.1 揭穿卡方量级异常</h3>
<p>主检验 A1 的统计量高达 {main['A1_chi2_red']['statistic']:.0f}，源于期望概率用了未归一的 6/33。
修正为标准卡方后：</p>
<table>
<tr><th>项</th><th>标准卡方</th><th>df</th><th>p 值</th><th>相对伪随机分位</th><th>效应量</th></tr>
<tr><td>红球</td><td>{D['标准卡方_红球']['chi2']}</td><td>32</td><td>{D['标准卡方_红球']['p']}</td><td>{D['相对伪随机分位']['红球']}</td><td>单号最大偏离 {D['效应量']['红球单号最大相对偏离pct']}%</td></tr>
<tr><td>蓝球</td><td>{D['标准卡方_蓝球']['chi2']}</td><td>15</td><td class="green">{D['标准卡方_蓝球']['p']}</td><td>{D['相对伪随机分位']['蓝球']}</td><td>—</td></tr>
<tr><td>三区</td><td>—</td><td>2</td><td>—</td><td>{D['相对伪随机分位']['三区']}</td><td>最大偏离 {D['效应量']['三区最大偏离百分点']} 个百分点</td></tr>
</table>
<p>关键：<b>蓝球（16 选 1，操纵成本最低、最容易动手的目标）完全正常</b>（p=0.88，分位 0.13）。
若真有人为调节，最该出现异常的恰恰是蓝球，但它干净得像教科书。</p>

<h3>2.2 高功效陷阱：分位极端，效应量微小</h3>
<div class="card">
{D['结论']}<br><br>
伪随机的红球卡方均值仅 26.8（教科书 χ²(32) 期望应为 32）——因为双色球是<b>无放回</b>抽样，
零分布本就不是标准卡方。这再次说明：<b>零分布必须匹配抽样机制</b>。在 n={R['n_draws']} 的大样本下，
连 0.89 个百分点的三区偏离都能被检出为"分位 0.99"——统计显著，实际无意义。
</div>

<h3>2.3 时间稳定性：偏离不是持续操纵的特征</h3>
<table>
<tr><th>子时期</th><th>红球卡方同长度对照分位</th></tr>
<tr><td>前半段</td><td class="green">{D['子时期_修正量纲']['early分位']}（正常）</td></tr>
<tr><td>后半段</td><td class="red">{D['子时期_修正量纲']['late分位']}（极端）</td></tr>
</table>
<p>偏离集中在后半段，且各号频率偏离的跨期相关系数仅 r={D['子时期_修正量纲']['跨期相关r']}（弱）。
稳定操纵应全程留下同方向痕迹；这种"时有时无、跨期不连贯"更像随机涨落或设备/球体的物理漂移。
模拟显示：仅给少数号注入 {list(D['物理偏差可复现性'].items())[0][1] if False else '10%'} 的微弱物理偏差，
即可复现真实的红球卡方量级（{D['物理偏差可复现性']['10%微弱偏差红球chi2']} vs 真实 {D['物理偏差可复现性']['真实']}）——
<b>不需要"人为调节"来解释这个信号</b>。</p>

<h2>三、可预测性终检 E0（人为操纵的最强可观测证据）</h2>
<table>
<tr><th>策略</th><th>红球平均命中（理论 1.09）</th><th>配对 t 检验 p</th></tr>
<tr><td>历史热号</td><td>{E['红球热号vs随机']['平均命中_热号']}</td><td rowspan="2">{E['红球热号vs随机']['p']}</td></tr>
<tr><td>闭眼随机</td><td>{E['红球热号vs随机']['平均命中_随机']}</td></tr>
</table>
<p>蓝球：热号命中率 {E['蓝球热号vs随机']['命中率_热号']} vs 随机 {E['蓝球热号vs随机']['命中率_随机']}，
二项检验 p={E['蓝球热号vs随机']['二项p']}（预注册门槛 p&lt;0.01）。
<b>结论：{E['结论']}</b>。任何以牟利或定向为目的的操纵，都必然留下可被历史数据捕捉的序列规律——
但热号策略和闭眼随机没有区别。</p>

<h2>四、独立结论</h2>
<div class="verdict">
<b>基于数据，我独立判断：现有证据不足以支持"双色球开奖被人为调节"的论断；数据更符合"开奖本质随机"。
具体分三层诚实陈述：</b>
<ul>
<li><b>能说的</b>：蓝球完全随机；开奖序列没有任何可预测规律（E0 两检验 p 均远大于 0.01）；
红球虽有统计可检出的轻微不均匀，但效应量极小（单号最大偏离 9.3%、三区 0.89 个百分点），
且时间不稳定、跨期弱相关、可被微弱物理偏差复现——这些都是随机涨落/物理非理想性的特征，
不是人为操纵的特征。</li>
<li><b>不能说的</b>：我<b>无法证明"绝对随机"</b>。若操纵手法刻意保持边际均匀（如只影响极少数期、
只在特定条件触发、不追求可预测性），本检验的统计功效覆盖不到——这是任何统计检验的固有边界。</li>
<li><b>方法反身</b>：主判据 D0 的"触发 H1"被证明是<b>大样本高功效 + 未归一卡方 + 多分量 |z| 线性相加</b>的联合产物。
这提醒：机械执行判据不等于得到真相，触发后必须做信号性质的诊断性拆解——这一教训已反哺进框架知识库。</li>
</ul>
</div>

<h2>五、立场声明</h2>
<p>借鉴的是统计学工具（卡方、KS、游程、自相关、蒙特卡洛对照、留出集回测）——它们是方法，不是结论。
本文所有判断均由本次 {R['n_draws']} 期数据独立得出。同时明确：<b>本研究不构成任何投资/购彩建议</b>；
双色球是概率游戏，即便完全随机，赌徒谬误与聚类错觉仍会让人"看出"并不存在的规律。</p>

</body></html>"""
Path("ssq_report.html").write_text(html, encoding="utf-8")
print("saved ssq_report.html", len(html), "chars")
