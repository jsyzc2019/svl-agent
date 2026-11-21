"""生成 DeepMind essay 框架论证报告。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ev = json.loads((ROOT / "agi_essay_evidence.json").read_text(encoding="utf-8"))
r = json.loads((ROOT / "agi_essay_result.json").read_text(encoding="utf-8"))
ps = ev["primary_source"]

e3rows = ""
for p in r["E3"]["falsifiable_predictions"]:
    e3rows += f"<tr><td class='green'>可证伪</td><td><b>{p['claim']}</b></td><td class='small'>{p['why']}</td></tr>"
for n in r["E3"]["grand_narratives"]:
    e3rows += f"<tr><td class='y'>叙事层</td><td><b>{n['claim']}</b></td><td class='small'>{n['quote']}</td></tr>"

e4rows = ""
for row in r["E4"]["rows"]:
    e4rows += f"<tr><td class='small'>{row['aspect']}</td><td>{row['relation']}</td><td><span class='badge {'badge-y' if '同谱系' in row['verdict'] else 'badge-g'}'>{row['verdict']}</span></td></tr>"

chk = r["E2"]["arithmetic_recomputed"]

html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>DeepMind《What comes after AGI?》框架论证报告</title>
<style>
body{{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;max-width:1000px;margin:0 auto;padding:32px 24px;line-height:1.75;color:#2c3e50;background:#fafbfc}}
h1{{border-bottom:3px solid #2980b9;padding-bottom:12px}}
h2{{margin-top:38px;border-left:4px solid #2980b9;padding-left:12px;color:#1a252f}}
table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}}
th,td{{border:1px solid #dfe4ea;padding:7px 10px;text-align:left;vertical-align:top}}
th{{background:#eef1f4}}
.card{{background:#fff;border:1px solid #e1e5ea;border-radius:8px;padding:16px 20px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.red{{color:#c0392b;font-weight:bold}} .green{{color:#27ae60;font-weight:bold}} .y{{color:#e67e22;font-weight:bold}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;color:#fff;background:#e67e22}}
.badge-g{{background:#27ae60}}
blockquote{{border-left:3px solid #95a5a6;margin:12px 0;padding:8px 16px;background:#f4f6f7;color:#555}}
.small{{font-size:13px;color:#7f8c8d}} code{{background:#f1f2f6;padding:1px 5px;border-radius:4px;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0}}
.grid div{{background:#fff;border:1px solid #e1e5ea;border-radius:8px;padding:14px;font-size:13px}}
</style></head><body>

<h1>DeepMind《What comes after AGI?》框架论证报告</h1>
<p class="small">
作者：{ev['retrieval_note']['author']} · {ev['retrieval_note']['date']} · {ev['retrieval_note']['platform']}<br>
来源：{ev['retrieval_note']['url']}（curl --compressed 直取 HTTP200，正文19971字符）<br>
预注册锁存 <code>{r['pre_registration_sha256'][:22]}…</code> · 对象类型 <b>{ev['object_type']}</b> · E1–E6 全部按预期触发
</p>

<blockquote>
<b>性质判定先行：</b>这是<b>观点性 essay</b>（conversation starter），既非实证论文（无统计量可复算）、
也非系统综述（无分类法需自洽核对）。判据适配为：<b>主体归属 / 外推链算术+假设 / 可证伪分级 /
同谱系污染 / 诚实刻度 / 吸收决策</b>。这是 KB-STRUCT01「判据要适配对象」在第三类对象上的落地。
</blockquote>

<h2>一、主体归属（Disclaimer 门禁）</h2>
<div class="card">
<p class="small">原文 Disclaimer 逐字：</p>
<blockquote>“{ev['retrieval_note']['disclaimer_verbatim']}”</blockquote>
<p>{r['E1']['decision']}。<span class="red">{r['E1']['misplacement_guard']}</span></p>
</div>

<h2>二、外推链算术复算（替代统计复算）</h2>
<div class="card">
<table>
<tr><th>论文外推</th><th>复算结果</th><th>自洽</th></tr>
<tr><td>有效算力 1.5×[3,6]×2.5 /年</td><td>{chk['effective_compute_per_year']} x/年 → 文称"至少10x"</td><td class="green">{'是' if chk['at_least_10x'] else '否'}</td></tr>
<tr><td>十年累积 10^10</td><td>{chk['ten_year_factor']:,} = 100亿倍</td><td class="green">{'是' if chk['ten_year_is_10_billion'] else '否'}</td></tr>
<tr><td>超过世界人口</td><td>10^10 &gt; 8×10⁹</td><td class="green">{'是' if chk['exceeds_world_population'] else '否'}</td></tr>
<tr><td>成本 $1B→$1000（降4x/年×10年）</td><td>$1e9 / 4¹⁰ = ${chk['cost_after_10y']}</td><td class="green">{'是(约值)' if chk['cost_approx_1000'] else '否'}</td></tr>
</table>
<p class="small">作者主动标注的假设：{' · '.join(r['E2']['caveats'])}</p>
<p><b class="y">关键分界：</b>{r['E2']['critical_separation']}。算术复算已固化进代码（<code>verify_extrapolation_arithmetic</code>），不靠一次性手算。</p>
</div>

<h2>三、可证伪分级（具体预测 vs 宏大叙事）</h2>
<table>
<tr><th>层级</th><th>主张</th><th>依据</th></tr>
{e3rows}
</table>
<p class="small">{r['E3']['decision']}</p>

<h2>四、同谱系交叉核对（触发≠真相）</h2>
<table>
<tr><th>维度</th><th>关系</th><th>判定</th></tr>
{e4rows}
</table>
<p class="small">{r['E4']['guard']}</p>

<h2>五、六项判据结果</h2>
<table>
<tr><th>判据</th><th>结果</th></tr>
<tr><td><b>E1 主体归属</b></td><td>{r['E1']['decision']}</td></tr>
<tr><td><b>E2 外推链</b></td><td>{r['E2']['decision']}</td></tr>
<tr><td><b>E3 可证伪分级</b></td><td>{r['E3']['decision']}</td></tr>
<tr><td><b>E4 同谱系污染</b></td><td>{r['E4']['decision']}</td></tr>
<tr><td><b>E5 诚实刻度</b></td><td>{r['E5']['decision']}</td></tr>
<tr><td><b>E6 吸收决策</b></td><td>{r['E6']['decision']}</td></tr>
</table>

<h2>六、三层诚实结论</h2>
<div class="grid">
<div><b>① 事实层</b><br>{r['conclusion']['layer1_fact']}</div>
<div><b>② 推断边界</b><br>{r['conclusion']['layer2_boundary']}</div>
<div><b>③ 方法教训</b><br>{r['conclusion']['layer3_method']}</div>
</div>

<h2>七、判据自审 + 长牙产物</h2>
<div class="card">
<p><b>判据自审：</b>首跑 E2 用脆弱的字符串包含检查判断算术自洽（碰巧对但逻辑不牢），且算术是 Bash 手算硬编码。
审计后把算术复算固化进 <code>verify_extrapolation_arithmetic()</code>，改为真实布尔断言——
与 §33/§34/§35/§38 一脉相承的"审计工具本身"。</p>
<p><b>长牙产物：</b>E6 判定"评估可扩展性"是真缺口，在 <code>svagent/evaluation_reliability.py</code> 加
<code>evaluation_scalability()</code>：超人域 + 纯人工判断无自动验证 → <code>REL.NOT_SCALABLE</code> flag。
"RSI 在自动验证领域最快"是可证伪预测，记观察项不强造模块（KB-META01 防为改进而改进）。</p>
<p class="small">知识库 88→<b>93 条、仍就绪</b>；新增 12 项测试（8 分析 + 4 可扩展性），全量 <b>287 测试通过</b>；预注册锁存一致。</p>
</div>

<blockquote>
<b>一句话收束：</b>这篇 essay 的实例与观点分层清楚、算术自洽且诚实标注假设——值得学的不是"ASI 会不会来"的结论，
而是它把 RSI 的反馈质量与评估可扩展性挑明的那两句话。<b>对观点文最好的读法，是把可证伪的预测留下、把宏大叙事归位，
再问一句：它说的哪句话，能在我这里长成一道会拦会降级的门禁？</b>
</blockquote>

</body></html>"""

(ROOT / "agi_essay_report.html").write_text(html, encoding="utf-8")
print("saved agi_essay_report.html", len(html))
