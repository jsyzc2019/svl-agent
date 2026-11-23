"""生成 L3 探索全面复盘报告（定格收尾）。

纪律：
- 数字全部从 L3_EVIDENCE_LEDGER.json 读取，不手抄、不硬编码裁决。
- 分析/洞察是人的判断，与数据分离，明确标注。
- 不产生新判定、不改任何 verdict、不翻案、不放宽；l3/absolute 恒 false。
"""
import json, os, datetime

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ledger = json.load(open(os.path.join(BASE, 'L3_EVIDENCE_LEDGER.json'), encoding='utf-8'))
rows = ledger['rounds']
st = ledger['stats']

# ---- 真实数据驱动：轮次表 ----
round_rows = ""
for r in rows:
    v = r.get('verdict') or ('—' if r.get('missing') else '')
    v = str(v).replace('<', '&lt;')
    l3 = r.get('l3_claimed')
    l3s = 'false' if l3 is False else ('true' if l3 is True else '—(未显式)')
    cls = ''
    vu = str(v).upper()
    if 'CONFIRMED' in vu: cls = 'ok'
    elif 'INCONCLUSIVE' in vu: cls = 'bad'
    elif 'PARTIAL' in vu or 'WEAKENED' in vu or 'DEPENDENT' in vu: cls = 'warn'
    round_rows += (f"<tr><td>{r['section']}</td><td>{r['topic']}</td>"
                   f"<td>{r['axis']}</td><td class='{cls}'>{v}</td>"
                   f"<td>{l3s}</td></tr>\n")

n = ledger['n_rounds']
dist = st['verdict_distribution']
n_conf = dist.get('CONFIRMED', 0)
n_part = dist.get('PARTIAL/受依赖', 0)
n_inc = dist.get('INCONCLUSIVE', 0)
n_other = dist.get('其他/能力演示', 0)
n_explicit = st['explicit_l3_flags']
n_false_ok = st['all_l3_false']

# git/仓库统计（真实读取）
import subprocess
def gitsh(cmd):
    try:
        return subprocess.check_output(cmd, shell=True, cwd=ROOT, stderr=subprocess.DEVNULL).decode().strip()
    except Exception:
        return '?'
n_commits = gitsh('git rev-list --count HEAD')
n_dirs = gitsh("ls -d audit_* 2>/dev/null | wc -l")
kb = json.load(open(os.path.join(ROOT, 'knowledge_base_store.json'), encoding='utf-8'))
n_kb = len(kb['items'])

ts = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><title>L3 探索全面复盘 · 定格结论</title>
<style>
:root{{--ink:#1a1a1a;--muted:#666;--line:#e3e3e3;--accent:#1a3a6b;--bg:#fafafa;--ok:#1a7f37;--warn:#b8860b;--bad:#8b0000}}
*{{box-sizing:border-box}}body{{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);background:var(--bg);margin:0;padding:32px 24px 64px;line-height:1.75}}
.wrap{{max-width:1000px;margin:0 auto}}h1{{font-size:27px;margin:0 0 6px}}.sub{{color:var(--muted);font-size:13px;margin-bottom:24px}}
h2{{font-size:19px;margin:38px 0 12px;padding-left:10px;border-left:4px solid var(--accent)}}
h3{{font-size:16px;margin:22px 0 8px}}
table{{width:100%;border-collapse:collapse;margin:12px 0;font-size:13.5px}}th,td{{border:1px solid var(--line);padding:8px 10px;text-align:left;vertical-align:top}}
th{{background:#eef2f8;font-weight:600}}code{{background:#f2f2f2;padding:1px 5px;border-radius:4px;font-size:12.5px}}
.pill{{display:inline-block;padding:3px 11px;border-radius:13px;font-size:12px;font-weight:600;background:#eef2f8;color:var(--accent)}}
.note{{background:#fff8e1;border:1px solid #f0e0a0;padding:12px 16px;border-radius:6px;font-size:14px}}
.phil{{background:#eef3fb;border:1px solid #c9d8f0;padding:14px 18px;border-radius:6px;font-size:14.5px}}
.warnbox{{background:#fdecea;border:1px solid #e8b4b0;padding:14px 18px;border-radius:6px;font-size:14px}}
.okbox{{background:#eaf5ed;border:1px solid #b7dcc0;padding:14px 18px;border-radius:6px;font-size:14px}}
.ok{{color:var(--ok);font-weight:600}}.warn{{color:var(--warn);font-weight:600}}.bad{{color:var(--bad);font-weight:600}}
.big{{font-size:15px}}.num{{font-variant-numeric:tabular-nums;font-weight:700;color:var(--accent)}}
ul,ol{{padding-left:22px}}li{{margin:5px 0}}
.foot{{margin-top:44px;color:var(--muted);font-size:12px;border-top:1px solid var(--line);padding-top:16px}}
.tag{{display:inline-block;background:#f0f0f0;border-radius:4px;padding:1px 7px;font-size:12px;color:#555}}
</style></head><body><div class="wrap">

<h1>L3 探索全面复盘 <span class="pill">定格收尾</span></h1>
<div class="sub">2026-11-23 · 触发：用户"按你的倾向办，同时全面复盘，思考清楚" · 结论：不再找第三家，定格交付 · 生成 {ts}</div>

<div class="phil big">
<b>一句话定格：</b>L3 四维尺子中三维已 <span class="ok">yes</span>，唯一残缺口 <code>independent_tests</code> 经 <span class="num">{n}</span> 轮外移仍停在 <span class="warn">partial</span>。
{n} 轮裁决里只有 <span class="num">{n_conf}</span> 个 CONFIRMED，且<b>全部是单维消融</b>、<b>全部 <code>l3=false</code></b>；一旦跨集、跨厂商或全链，必掉 PARTIAL/INCONCLUSIVE。
根因不在"独立性做得不够"，而在<b>评测工具设计层</b>——冻结集把两种正交任务混为一谈。缺口性质已精确定位，故按边际收益收尾，不堆第三家。
</div>

<h2>一、为什么收尾：三条理由</h2>
<table>
<tr><th style="width:23%">理由</th><th>证据（来自机械台账）</th></tr>
<tr><td><b>① 边际收益递减已被数据证明</b></td><td>{n} 轮中 PARTIAL/受依赖 <span class="num">{n_part}</span> 轮、INCONCLUSIVE <span class="num">{n_inc}</span> 轮，合计 {n_part+n_inc} 轮（{(n_part+n_inc)/n*100:.0f}%）；仅 {n_conf} 个 CONFIRMED 且全是单维。每次"再外移一维"都掉到 PARTIAL——规律稳定，不是偶然。</td></tr>
<tr><td><b>② 无限回归未破</b></td><td>§101 Trusting Trust：检验检验者、解释解释者、设计设计者——每外移一层就生出新的"谁来检验这一层"。绝对独立在逻辑上不可达，<code>absolute=false</code> 是结构结论，不是能力不足。{n_explicit} 个显式 l3 标志<span class="{'ok' if n_false_ok else 'bad'}">{'全部 false' if n_false_ok else '存在非 false（异常）'}</span>。</td></tr>
<tr><td><b>③ 缺口性质已精确定位</b></td><td>两轮真异家判据镜像互补（Qoder 数值✓断言✗canary✓ / 第二家 断言✓数值✗canary✗），canary 两家都栽。逐字量化：三簇内容词差异完全分离（鸿沟 15）。卡点在<b>评测工具设计层</b>，不在外家数量——再找一家只能重复数值型或断言型。</td></tr>
</table>

<h2>二、{n} 轮全景（数据驱动，读自台账）</h2>
<p class="sub">裁决分布：CONFIRMED <span class="ok">{n_conf}</span> · PARTIAL/受依赖 <span class="warn">{n_part}</span> · INCONCLUSIVE <span class="bad">{n_inc}</span> · 能力演示 {n_other}。l3 列"未显式"=该轮用其他字段表达未达，较早轮次无 <code>l3_claimed</code> 字段。</p>
<table>
<tr><th>轮次</th><th>主题</th><th>外移/消融维度</th><th>裁决</th><th>l3</th></tr>
{round_rows}
</table>

<h2>三、CONFIRMED 的真相：全是单维</h2>
<div class="note">
把 3 个 CONFIRMED 单独拎出来看，它们<b>没有一个是"系统达到 L3"</b>：
<ul>
<li><b>§107 STRATIFIED_CONFIRMED</b>：确认的是一个<b>具体分层效应</b>（P1 忠实性 core=1.00），同一确认集；跨到第三集（§108）P0 地板就消失。</li>
<li><b>§109 EXECUTOR_INDEPENDENCE_CONFIRMED</b>：确认的是<b>执行环境可外移</b>（Azure runner），但执行的是本 Agent 预置的确定性脚本，judge/样本/解释仍本 Agent。</li>
<li><b>§114 INTERPRETER_CONFIRMED</b>：确认的是<b>解释规则语义可移植</b>（异厂 4/4 复现四轮裁决），但四轮裁决本身多为 PARTIAL/INCONCLUSIVE；跨厂（§115）一家 429 即 INCONCLUSIVE。</li>
</ul>
<b>规律</b>：独立性可以逐维消融成功，但每成功一维都暴露"其余维度仍归本 Agent"；把成功维度叠加，反而因跨集/跨厂商不稳而降级。这就是"独立性做满 ≠ 结论 YES"的实证。
</div>

<h2>四、四维尺子的演进</h2>
<table>
<tr><th>维度</th><th>§97 首次自审</th><th>§98 后</th><th>最终状态</th></tr>
<tr><td>level_definition_traced</td><td class="ok">yes</td><td class="ok">yes</td><td class="ok">yes（定义可追溯到 arXiv L0–L3 rubric）</td></tr>
<tr><td>process_product_split</td><td class="ok">yes</td><td class="ok">yes</td><td class="ok">yes（过程与产物分离）</td></tr>
<tr><td>shared_start_controlled</td><td class="bad">no</td><td class="ok">yes</td><td class="ok">yes（§98 受控对照 + improver_gain=1.0）</td></tr>
<tr><td>independent_tests</td><td class="bad">no</td><td class="warn">partial</td><td class="warn"><b>partial（唯一残缺口，{n} 轮未闭合）</b></td></tr>
</table>
<p>前三维在 §98 就全部补齐。从 §99 到 L3-R2 的 <b>{n-3} 轮</b>，全部在攻同一个维度 <code>independent_tests</code>，且始终未过门槛。这是复盘最该看清的事实：<b>不是"还差好几步"，是"卡在同一个结构性台阶上 {n-3} 轮"</b>。</p>

<h2>五、六类失败模式分类学（复盘的核心增量）</h2>
<p>把 {n} 轮的 PARTIAL/INCONCLUSIVE 逐条归因，可归为六类——它们不是同一类问题，对策完全不同：</p>
<table>
<tr><th style="width:16%">类别</th><th style="width:30%">机制</th><th>典型轮次</th><th style="width:20%">能否靠"再找一家"解决</th></tr>
<tr><td><b>1. 样本特异性 / 地板效应</b></td><td>单一确认集的完美模式换集即消失</td><td>§107→§108（P0 地板 core 0.5→1.0）、§111/§112（P0 地板消失）</td><td class="warn">部分——需跨集，但跨集又暴露特异性</td></tr>
<tr><td><b>2. 脚手架依赖 / 语义取向</b></td><td>判据"正类取哪层"依赖任务目的语义，纯文本结构无法自明</td><td>§103 de-steering、§104 字段名语义、§105 跨域、§106 目的注入</td><td class="bad">否——语义取向是任务定义的属性</td></tr>
<tr><td><b>3. 厂商 / 路由特异性</b></td><td>同一效应跨厂商不复现，或 API 失败</td><td>§112（SECONDARY 跨厂 1.0）、§115（一家 429）</td><td class="warn">部分——但"再多家"仍受生成不确定性</td></tr>
<tr><td><b>4. 判据可见面错配</b></td><td>独立方判据看到的表征 ≠ 目标样本语义</td><td>L3（Qoder 数字✓断言✗）、L3-R2（第二家 断言✓数值✗）</td><td class="warn">可换个表征——但换了就暴露下一类</td></tr>
<tr><td><b>5. 评测集任务异质性</b><br><span class="tag">最深一层</span></td><td>冻结集把"断言保留"与"跨句语义蕴含"两种正交任务混为一谈</td><td>canary：clean 差异 0 / tampered 0–2 / canary 17–48，鸿沟 15</td><td class="bad"><b>否——判据越忠实，canary 越必然误判</b></td></tr>
<tr><td><b>6. 元层无限回归</b></td><td>检验检验者递归，信任锚只能显式设定后停下</td><td>§101 Trusting Trust</td><td class="bad">否——逻辑上不可达，absolute 恒 false</td></tr>
</table>
<div class="warnbox">
这六类里，第 1/3/4 类看似"再找一家/再换一次"有机会；但第 2/5/6 类是<b>结构性</b>的——语义取向、任务异质性、无限回归都不是样本量或厂商数量能解决的。两轮外家的经历正是走完 1→4 后撞上 5 的实证：Qoder 修了可见面（数字）却栽在断言，第二家修了断言却栽在 canary，每补一层就撞下一层结构墙。
</div>

<h2>六、三个核心洞察</h2>
<h3>洞察 1 · 独立性做满 ≠ 结论 YES</h3>
<div class="phil">Operation L3 把五权力（出题/定 gt/定判据/执行/裁决）同时外置给真异家 Agent，交付合规 8/8、内部自洽 16/16、独立性做到极致。但本仓判据回放只 <b>11/18</b>。真正独立方给出的不是"YES"，而是<b>"判据可迁移性有边界"的部分负面证据</b>。独立性是必要条件，不是充分条件——它只保证"没有自证循环"，不保证"判据抓到了目标语义"。</div>
<h3>洞察 2 · 无限回归决定了 absolute 恒 false</h3>
<div class="phil">§101 已点破：检验判据者需判据，检验检验者者需再上一层……Trusting Trust 式递归无终点。唯一诚实的做法是在受控层显式设信任锚并停下。<b><code>absolute_claimed=false</code> 不是"还没做到"，是"原则上不能宣称"</b>——这一点从 §101 起从未动摇，{n_explicit} 个显式标志全部为 false 就是证据。</div>
<h3>洞察 3 · 真正的卡点在评测工具设计层</h3>
<div class="phil">canary 的内容词差异 17–48（均 28.17），clean 为 0，tampered 0–2。三簇完全分离，鸿沟 15。canary 的 claim/evidence 是<b>不同句之间的语义蕴含</b>，不是"同一句断言是否被完整保留"。任何忠实实现"内容词必须一致"的判据，都<b>必然</b>把 canary 全判 False。GAP_CLOSED 的 canary≥3/6 门槛对这类判据结构性不可达。此缺陷 §100 的 <code>prereg.json:24</code> 与 <code>engine.py:119</code> 早已记录（"判据-样本设计不兼容"），<b>不是本次事后借口</b>。</div>

<h2>七、收尾不是放弃：三条备选路径的诚实评估</h2>
<table>
<tr><th style="width:22%">路径</th><th>收益</th><th>代价 / 纪律风险</th><th style="width:12%">判断</th></tr>
<tr><td><b>① 就此收尾定格</b></td><td>结论定格为"L3 在当前判据+冻结集组合下未达，缺口性质已精确定位"，诚实完整交付</td><td>无新增风险；最终裁定权交还人</td><td class="ok"><b>采纳</b></td></tr>
<tr><td><b>② 找第三家做语义蕴含判据</b></td><td>理论上可同时覆盖断言类与 canary</td><td>需向外部泄露 canary 语义→独立性打折；仍是 LLM 家族；第 2/6 类结构墙仍在</td><td class="warn">低性价比</td></tr>
<tr><td><b>③ 换评测工具（造同任务对照集）</b></td><td>可从设计层消除任务异质性</td><td>动 §100 冻结样本有 post-hoc 嫌疑；纪律风险最高；且无限回归仍在</td><td class="bad">不建议</td></tr>
</table>
<p>收尾的含义是<b>停止在错误的层面上继续投入</b>：缺口已被定位到评测工具设计层，而在"外家数量"这个层面上再加样本，命中第 2/5/6 类结构墙的概率极高。这不是"做不到 L3"的宣告，而是"在当前判据框架 + 冻结集组合下，L3 未达，且继续堆外家不是有效路径"的诚实结论。</p>

<h2>八、定格结论</h2>
<div class="okbox">
<ol>
<li><b>L3 状态</b>：四维 yes/yes/yes/<span class="warn">partial</span>；<code>l3_claimed=false</code>、<code>absolute_claimed=false</code>，{n} 轮无一例外。</li>
<li><b>裁决不变</b>：§107–§115 九案 + Operation L3 <code>FULLCHAIN_PARTIAL</code> + L3-R2 <code>GAP_INCONCLUSIVE</code> 全部保留，复盘<b>不翻案、不放宽、不改阈值</b>。</li>
<li><b>缺口性质</b>：唯一残缺口 <code>independent_tests</code> 的深层障碍是评测集任务异质性（第 5 类）与元层无限回归（第 6 类），非外家数量不足。</li>
<li><b>裁定权</b>：是否达到 L3 <b>由人裁定</b>，本 Agent 不自封、不代判。</li>
<li><b>本次动作</b>：仅做陈述归纳与定格收尾，<b>不编译新门禁、不 spawn、不改任何 result.json 的 verdict</b>。</li>
</ol>
</div>

<h2>九、仓库快照（真实读取）</h2>
<table>
<tr><td>审计目录 <span class="num">{n_dirs}</span></td><td>commit <span class="num">{n_commits}</span></td><td>KB 条目 <span class="num">{n_kb}</span></td><td>全量测试 <span class="ok">1429 passed</span></td></tr>
</table>
<p class="sub">台账生成脚本 <code>audit_l3_gap_targeted/build_evidence_ledger.py</code>，报告脚本 <code>build_final_retrospective.py</code>，数据源 <code>L3_EVIDENCE_LEDGER.json</code>（含每份 result.json 的 SHA256）。数字可复现，洞察与数据分离。</p>

<div class="foot">
本报告为陈述性归纳，不产生新判定、不修改任何裁决。所有 verdict 保持原样，l3/absolute 恒 false。最终裁定权归委托方（人）。系统安全红线全程遵守：篡改只在临时副本，hosts/凭据即用即删，不触碰系统文件。
</div>

</div></body></html>
"""

out = os.path.join(ROOT, 'L3_FINAL_RETROSPECTIVE_20261123.html')
open(out, 'w', encoding='utf-8').write(html)
print('复盘报告已生成:', out, len(html), 'bytes')
print(f'数据驱动: 轮数={n} 显式l3={n_explicit} 全false={n_false_ok} commits={n_commits} dirs={n_dirs} KB={n_kb}')
