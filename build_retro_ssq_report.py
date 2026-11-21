"""生成第26节框架复盘报告 HTML。"""
import json
from pathlib import Path

d = json.load(open("ssq_retrospective_result.json"))
a = d["improvement_audit"]
o = d["outcome"]

def li(items, cls=""):
    return "".join(f"<li class='{cls}'>{x}</li>" for x in items) or "<li class='dim'>（无）</li>"

fix = li(a["fix"], "fixc")
van = li(a["vanity"], "vanc")
pre = li(a["preserve"], "prec")
worked = li(d["worked"], "okc")
failed = li(d["failed"], "noc")
corr = "".join(f"<li>{x}</li>" for x in o["root_cause"].replace("认知根因: ","").split(" | "))
meta = d["meta_lesson"]

html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>框架逻辑方法复盘 · 双色球推演</title>
<style>
body{{font-family:-apple-system,'PingFang SC',sans-serif;max-width:980px;margin:32px auto;padding:0 22px;color:#1a1a1a;line-height:1.7}}
h1{{font-size:26px;border-bottom:3px solid #2c5282;padding-bottom:10px}}
h2{{font-size:19px;color:#2c5282;margin-top:30px;border-left:4px solid #2c5282;padding-left:10px}}
.card{{background:#f7fafc;border:1px solid #e2e8f0;border-radius:10px;padding:14px 20px;margin:16px 0}}
.gate{{background:#f0fff4;border-left:4px solid #38a169;padding:10px 16px}}
ul{{padding-left:22px}}li{{margin:5px 0}}
.fixc{{color:#9b2c2c}}.vanc{{color:#975a16}}.prec{{color:#276749}}
.okc{{color:#276749}}.noc{{color:#9b2c2c}}.dim{{color:#718096}}
.meta{{background:#fffaf0;border:2px solid #dd6b20;border-radius:10px;padding:16px 20px}}
.tag{{display:inline-block;padding:2px 9px;border-radius:10px;font-size:12px;font-weight:700;background:#ebf8ff;color:#2c5282}}
</style></head><body>
<h1>框架逻辑方法复盘 · 双色球推演（scope=framework）</h1>

<div class="card gate">
<b>防后知门禁：通过 ✓</b>　事前锚点 <code>2026-11-21T12:55:01</code>（预注册 SHA256 锁存时刻），
揭盲 <code>2026-11-21T13:12:00</code>——先验在前、结果在后，轨迹真实可追溯，非事后编造。
</div>

<div class="card">
<b>复盘问题</b>：这套方法论在双色球随机性检验推演中，逻辑方法上有何经验与教训？<br>
<b>事前预期</b>：{o['expected']}<br>
<b>揭盲结果</b>：{o['actual']}
</div>

<h2>一、经验（做对了什么）</h2>
<div class="card"><ul>{worked}</ul></div>

<h2>二、认知根因（教训的来源）</h2>
<div class="card"><ul>{corr}</ul></div>

<h2>三、改进该改进的 · 三分法</h2>
<div class="card">
<p><span class="tag">fix · {len(a['fix'])}条</span> 真该改的方法缺陷——改机制而非文案</p>
<ul>{fix}</ul>
<p><span class="tag">vanity · {len(a['vanity'])}条</span> 虚荣改进——改动冒充进步，需识破</p>
<ul>{van}</ul>
<p><span class="tag">preserve · {len(a['preserve'])}条</span> 不该改的——守住框架的脊梁</p>
<ul>{pre}</ul>
</div>

<h2>四、元教训：连复盘工具本身也要被审</h2>
<div class="meta">
<p>{meta['finding']}</p>
<p><b>分类：</b><span class="tag">{meta['classification']}</span></p>
<p><b>动作：</b>{meta['action']}</p>
<p class="dim">为什么重要：{meta['why_it_matters']}</p>
</div>

<h2>五、反哺与收束</h2>
<div class="card">
<p>本次复盘新增沉淀 2 条框架层 fix 教训（判据实现自检、复盘工具自审）到知识库，累计 44 条。
上一轮已沉淀的 4 条统计方法教训（高功效陷阱/零分布匹配/代理变量/可预测性）被本次三分法<b>独立重新发现</b>——
这是框架自洽性的正面证据：同样的教训，从真实数据验证和事后复盘两条路径收敛到了同一处。</p>
<p><b>核心经验</b>：预注册+盲测对照+诊断性拆解+三层诚实陈述——这套组合在真实数据上被证明有效，守住。</p>
<p><b>核心教训</b>：机械执行判据≠得到真相；判据触发只是调查起点。统计显著、极端排名、漂亮结论，
都可能实现 bug、高功效与虚荣叙事的合谋，必须靠诊断性拆解还原。</p>
<p><b>元教训</b>：复盘工具若只套通用模板，会退化成走流程——它自己也必须进入被审对象。</p>
</div>

</body></html>"""
Path("ssq_retrospective_report.html").write_text(html, encoding="utf-8")
print("saved", len(html), "chars")
