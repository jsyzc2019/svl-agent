# -*- coding: utf-8 -*-
import json, html
R = json.load(open("ai_detect_full_result.json"))
T = R["tests"] if "tests" in R else {}
F = R["feature_means"]
D = R["decision"]
G = R["gate"]
DIA = R["diagnosis"]
CON = R["independent_conclusion"]

rows_feature = "".join(
    f"<tr><td>{html.escape(f)}</td><td>{v['human']:.3f}</td><td>{v['ai']:.3f}</td><td>{R['single_feature_auc'].get(f,'-')}</td></tr>"
    for f, v in F.items()
)

diag_html = "".join(f"<li>{html.escape(str(x))}</li>" for x in [
    f"G1门禁触发：单特征主导 = {G['G1_single_feature_dominant']}",
    f"仅句长AUC={DIA['single_feature_auc']['仅句长']}，仅标点={DIA['single_feature_auc']['仅标点']}，纯内容特征(去句长/标点)={DIA['single_feature_auc']['纯内容特征(去句长标点)']}",
    f"句长分布：真人 {DIA['sent_len_distribution']['human']} vs AI {DIA['sent_len_distribution']['ai']}，重叠区真人仅{DIA['sent_len_distribution']['overlap_human_n']}例 vs AI {DIA['sent_len_distribution']['overlap_ai_n']}例",
    DIA["finding"],
    f"去味改动率仅 {DIA['deai_change_rate']*100:.1f}%；深度去味(合并短句)后检出率 {DIA['deep_deai_ablation']['检出率']*100:.0f}%，AI概率均值 {DIA['deep_deai_ablation']['ai概率均值']}",
])

html_out = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>网文 AI 生成客观判别 —— 独立论证报告</title>
<style>
body{{font-family:"PingFang SC","Microsoft YaHei",sans-serif;max-width:980px;margin:40px auto;padding:0 24px;color:#222;line-height:1.8}}
h1{{border-bottom:3px solid #c0392b;padding-bottom:12px}}
h2{{color:#c0392b;margin-top:36px;border-left:4px solid #c0392b;padding-left:12px}}
table{{border-collapse:collapse;width:100%;margin:16px 0}}
th,td{{border:1px solid #ddd;padding:8px 12px;text-align:center}}
th{{background:#f5f5f5}}
.big{{font-size:22px;font-weight:bold;color:#c0392b}}
.box{{background:#fff5f5;border-left:4px solid #c0392b;padding:12px 18px;margin:16px 0}}
.warn{{background:#fff8e1;border-left:4px solid #f39c12;padding:12px 18px;margin:16px 0}}
.ok{{color:#27ae60}} .bad{{color:#c0392b}}
code{{background:#f4f4f4;padding:2px 6px}}
</style></head><body>
<h1>网文 AI 生成客观判别 —— 独立论证报告</h1>
<p><b>问题：</b>在去 AI 味技能加持下，能否客观判别网文哪些是 AI 写的、哪些是真人写的？</p>
<p><b>纪律：</b>预注册判据 + SHA256 锁存（<code>{R['prereg_sha256_verified'][:16]}…</code>）→ 建带标签样本 → 揭盲 → 诊断性拆解 → 独立结论。样本哈希亦锁存，事后校验一致。</p>

<h2>一、金标准设计（本次最大难点）</h2>
<p>三类带确定标签的样本，长度匹配（430–630字）：</p>
<table><tr><th>类别</th><th>数量</th><th>来源与标签依据</th></tr>
<tr><td>真人 H</td><td>{R['sample_counts']['human']}</td><td>《斗破苍穹》(天蚕土豆, 2009起) 章节切片，ChatGPT 前作品，高置信人类创作</td></tr>
<tr><td>AI A</td><td>{R['sample_counts']['ai']}</td><td>本 Agent 现场创作的玄幻网文，题材刻意匹配真人以控混淆</td></tr>
<tr><td>去味 D</td><td>{R['sample_counts']['deai']}</td><td>对 A 用 humanizer 规则改写，标签仍为 AI 起源，全程留出</td></tr></table>
<div class="warn"><b>结构性局限：</b>真人集中于单部作品（作者风格混淆）、AI 来自单一模型（本 Agent，自利偏差）——这是本次设计的软肋，结论中如实计入。</div>

<h2>二、揭盲：漂亮数字</h2>
<p class="big">原始 AI 文本 AUC = {R['auc_original']}　|　去味后 AI 检出率 = {R['deai_detect_rate']*100:.0f}%</p>
<p>按预注册判定规则：原始判别 <code>{D['R_original']}</code>（可判别），去味后 <code>{D['R_deai']}</code>（仍可判别）。<b>若就此收尾，答案会是"AI 可客观判别，去味也骗不过"——但这是陷阱。</b></p>

<h2>三、诊断性拆解：触发≠真相</h2>
<div class="box">{''.join('<div>'+x+'</div>' for x in [
    '① 单特征就够：仅句长 AUC=0.927，句长+标点=0.948 → <b>G1 门禁亮起（脆弱判据）</b>',
    '② 去掉句长/标点后，纯内容特征 AUC 仅 <b>0.569</b>（近随机）——判别力几乎全靠"句子长短"',
    '③ 句长分布几乎不重叠（真人41±17 vs AI 18±2），判别器抓的是"我写短句 vs 天蚕土豆长段落"的文风 artifact',
    '④ 去味样本仅 5.2% 改动却 100% 检出；但仅合并短句(不改语义)就把检出率打到 75%',
])}</div>
<h3>特征均值对照</h3>
<table><tr><th>特征</th><th>真人均值</th><th>AI均值</th><th>单特征AUC</th></tr>{rows_feature}</table>

<h2>四、独立结论（三层诚实）</h2>
<div class="box">
<p><b class="ok">能说的：</b>{html.escape(CON['can_say'])}</p>
<p><b class="bad">不能说的：</b>{html.escape(CON['cannot_say'])}</p>
<p><b>方法反身：</b>{html.escape(CON['method_reflection'])}</p>
</div>
<p class="big">对问题的直接回答：{html.escape(CON['answer'])}</p>

<h2>五、反哺</h2>
<p>沉淀 3 条框架层 fix：文风 artifact 冒充本质特征、结构性自利偏差、去味强度分层。知识库累计 52 条，仍就绪。这一轮与双色球（未归一卡方）、上证（前视偏差）并列，构成"漂亮触发 → 诊断拆解 → 还原假象"的第三次实战。三者共同指向：**惊艳的判别结果出现时，先怀疑判据寄生在什么脆弱特征上，再相信它测到了本质。**</p>
<hr><p style="color:#888;font-size:12px">本报告为方法论研究，仅作学术探讨，不构成任何对具体文本来源的指控或鉴定结论。</p>
</body></html>"""
open("ai_detect_report.html","w").write(html_out)
print("saved ai_detect_report.html", len(html_out))
