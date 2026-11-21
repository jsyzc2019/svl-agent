# -*- coding: utf-8 -*-
import json, html
R = json.load(open("article_factcheck.json"))

verdict_class = {
    "属实": "ok", "部分属实": "mid", "部分属实(经历真,细节化了)": "mid",
    "有典故但细节走样": "mid", "广泛流传但出处存疑": "mid", "部分属实": "mid",
    "查无实据": "bad", "伪托权威": "bad", "伪名言(铁证)": "bad",
    "无依据的量化断言": "bad", "金句属实但出处混乱/措辞被改": "mid",
}
def cls(v):
    if v == "属实": return "ok"
    if "伪" in v or "查无实据" in v or "无依据" in v: return "bad"
    return "mid"

rows = "".join(
    f"<tr><td style='text-align:left'>{html.escape(c['claim'])}</td>"
    f"<td class='{cls(c['verdict'])}'><b>{html.escape(c['verdict'])}</b></td>"
    f"<td style='text-align:left;font-size:13px'>{html.escape(c['evidence'])}</td></tr>"
    for c in R["fact_checks"]
)
patterns = "".join(f"<li>{html.escape(p)}</li>" for p in R["rhetorical_patterns"])
bounds = "".join(f"<li>{html.escape(b)}</li>" for b in R["honest_boundaries"])

html_out = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>公众号文章叙事真实性核查 —— 独立论证</title>
<style>
body{{font-family:"PingFang SC","Microsoft YaHei",sans-serif;max-width:1040px;margin:36px auto;padding:0 22px;color:#222;line-height:1.75}}
h1{{border-bottom:3px solid #c0392b;padding-bottom:10px}}
h2{{color:#c0392b;margin-top:32px;border-left:4px solid #c0392b;padding-left:12px}}
table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}}
th,td{{border:1px solid #ddd;padding:7px 10px;text-align:center;vertical-align:top}}
th{{background:#f5f5f5}}
.ok{{color:#1e8449}} .mid{{color:#b7791f}} .bad{{color:#c0392b}}
.box{{background:#fff5f5;border-left:4px solid #c0392b;padding:12px 18px;margin:14px 0}}
.warn{{background:#fff8e1;border-left:4px solid #f39c12;padding:12px 18px;margin:14px 0}}
code{{background:#f4f4f4;padding:2px 6px}}
.big{{font-size:20px;font-weight:bold;color:#c0392b}}
</style></head><body>
<h1>公众号文章叙事真实性核查</h1>
<p><b>核查对象：</b>{html.escape(R['object'])}</p>
<p><b>日期：</b>{R['date']}　<b>范围：</b>{html.escape(R['scope'])}</p>

<div class="box"><b>核心反讽（本次最强证据）：</b>{html.escape(R['core_paradox'])}</div>

<h2>一、13 条事实断言逐条核查</h2>
<table><tr><th width="34%">文中断言</th><th width="16%">结论</th><th>证据</th></tr>{rows}</table>
<p><span class="ok">● 属实</span>　<span class="mid">● 部分属实/出处存疑</span>　<span class="bad">● 伪托/无据/查无实据</span></p>

<h2>二、文风套路（仅作叙事结构描述，不作作者身份判据）</h2>
<ul>{patterns}</ul>
<div class="warn"><b>注意：</b>这些特征在 ChatGPT 问世前的公众号/人民日报夜读（2018）文章中就大量存在。按上一轮实证结论，<b>它们不能用来判定本文是 AI 写的还是人写的</b>——此处只描述结构，不越界。</div>

<h2>三、诚实边界</h2>
<ul>{bounds}</ul>

<h2>四、三层结论</h2>
<div class="box">
<p><b class="ok">能说的：</b>文章把大量未经核实的名人语录堆叠成"共识"，其中杨绛那句已被人民日报自己辟谣、马尔克斯/梁晓声等句查无实据、"80%烦恼"无依据；且冒用人民日报旗号。作为"劝人读书"的情绪文可以，作为"事实陈述"不可信。</p>
<p><b class="bad">不能说的：</b>不能据文风断言它一定是 AI 写的——鸡汤文风非 AI 专属；也不能断言所有引语都假（苏轼诗、曾国藩联、岛上书店属实）。核查结论是"混杂"而非"全假"。</p>
<p><b>方法反身：</b>这次真正被验证的不是"AI 检测器"，而是事实核查链——追原始出处、识别权威背书包装、抓伪精确数字。最有力的证据是"打假者被冒名者拿来背书"的结构性反讽，而非任何文风指标。</p>
</div>
<p class="big">一句话：判断"对不对"靠事实核查，不靠"像不像 AI"；这篇文章的事实成色，远不如它的权威包装看上去那么足。</p>
<hr><p style="color:#888;font-size:12px">本报告为叙事真实性方法论研究，鼓励读书本身无误；所批评的是未经核实的引语与伪托权威的传播手法。</p>
</body></html>"""
open("factcheck_report.html","w").write(html_out)
print("saved factcheck_report.html", len(html_out))
