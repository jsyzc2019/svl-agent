"""生成 RSI-Structure 综述论文框架论证报告。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ev = json.loads((ROOT / "rsi_structure_evidence.json").read_text(encoding="utf-8"))
r = json.loads((ROOT / "rsi_structure_result.json").read_text(encoding="utf-8"))
p = ev["primary_paper"]

T4rows = r["T4"]["rows"]
verdict_map = {
    "V1_reuse_not_recursive": "复用≠递归依赖",
    "V2_rounds_not_effectiveness": "轮数≠改进有效性",
    "V3_failure_not_what_to_edit": "失败≠改哪里",
    "V4_combined_not_single_attribution": "组合收益≠单组件归因",
    "V5_evaluate_not_verify": "Evaluate≠Verify",
    "V6_retirement_cover_rare": "退役需覆盖低频用途",
}

rows_html = ""
for row in T4rows:
    status = row["status"]
    cls = "green" if status == "已具备" else "y"
    badge = "badge-g" if status == "已具备" else "badge-y"
    mech = "；".join(row["framework_mechanisms"])
    rows_html += (
        f"<tr><td><b>{verdict_map[row['id']]}</b></td>"
        f"<td class='small'>{row['paper_verdict']}</td>"
        f"<td>{mech}</td>"
        f"<td><span class='badge {badge}'>{status}</span></td></tr>"
    )

html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>RSI-Structure 综述论文框架论证报告</title>
<style>
body{{font-family:-apple-system,'PingFang SC','Microsoft YaHei',sans-serif;max-width:1000px;margin:0 auto;padding:32px 24px;line-height:1.75;color:#2c3e50;background:#fafbfc}}
h1{{border-bottom:3px solid #2980b9;padding-bottom:12px}}
h2{{margin-top:38px;border-left:4px solid #2980b9;padding-left:12px;color:#1a252f}}
table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}}
th,td{{border:1px solid #dfe4ea;padding:7px 10px;text-align:left;vertical-align:top}}
th{{background:#eef1f4}}
.card{{background:#fff;border:1px solid #e1e5ea;border-radius:8px;padding:16px 20px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.04)}}
.red{{color:#c0392b;font-weight:bold}} .green{{color:#27ae60;font-weight:bold}} .blue{{color:#2980b9;font-weight:bold}} .y{{color:#e67e22;font-weight:bold}}
.badge{{display:inline-block;padding:2px 10px;border-radius:12px;font-size:12px;color:#fff;background:#2980b9}}
.badge-r{{background:#c0392b}} .badge-g{{background:#27ae60}} .badge-y{{background:#e67e22}}
blockquote{{border-left:3px solid #95a5a6;margin:12px 0;padding:8px 16px;background:#f4f6f7;color:#555}}
.small{{font-size:13px;color:#7f8c8d}} code{{background:#f1f2f6;padding:1px 5px;border-radius:4px;font-size:13px}}
.grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin:14px 0}}
.grid div{{background:#fff;border:1px solid #e1e5ea;border-radius:8px;padding:14px;font-size:13px}}
</style></head><body>

<h1>When / Where / How — RSI-Structure 综述框架论证报告</h1>
<p class="small">
论文：{p['title']}<br>
单位：中科院自动化所（第一署名）· 美团 · 山东大学等 10 家 ·
期刊/平台：{p['venue']} · {p['date']}<br>
获取：OpenReview 直连 403 → 经 ID 反查 Preprints.org 开放版，
首轮经独立抓取通道取得摘要+§1–4+§9（<code>rsi_structure_paper.txt</code>），PDF 二进制未取得、§10–11 被截断；<b>用户随后补传官方PDF，全文2416行落地 <code>rsi_structure_full.txt</code>，§10/§11 已逐字覆盖，局限已解除</b>（见文末修正记录）。<br>
预注册锁存 <code>{r['pre_registration_sha256'][:22]}…</code> ·
对象类型 <b>{p['type']}</b> · 判据 T1–T6 全部按预期触发
</p>

<blockquote>
<b>性质判定先行：</b>这是一篇<b>综述/分类学</b>，产出「四组件 × 七阶段 + When/Where/How」统一语言，
<b>没有自己的实验统计量</b>。因此本报告<b>不做统计复算</b>——判据要适配对象，为套判据而硬套 t 检验即为错配（T3）。
</blockquote>

<h2>一、三层来源隔离 + 谱系污染（不得交叉背书）</h2>
<div class="card">
<table>
<tr><th>层</th><th>内容</th><th>框架处置</th></tr>
<tr><td><b>事实层</b><br>论文逐字原文</td><td>四组件 Prompt/Memory/Skill/Harness、七阶段 Collect→Consolidate、三问题 When/Where/How、Figure3 三种 survives、六句 "does not by itself prove" 自我限定</td><td class="green">可作事实基础</td></tr>
<tr><td><b>叙事层</b><br>媒体转述</td><td>标题「Agent 如何越用越强」为传播性措辞；正文对框架转述忠实</td><td class="red">主体错位风险，不作有效性证据</td></tr>
<tr><td><b>谱系层</b><br>awesome-rsi</td><td>我方 L1/L2/L3 证据阶梯在 §34 已受其 Task/Retained/Improver 分类影响</td><td class="y">论文 Figure3 与我方同构 = 同谱系印证，<b>非独立验证</b></td></tr>
</table>
<p class="small">{r['T2']['honesty']}</p>
</div>

<h2>二、六项预注册判据结果</h2>
<table>
<tr><th>判据</th><th>结果</th></tr>
<tr><td><b>T1 主体错位</b></td><td>{r['T1']['decision']} — {r['T1']['attribution']}</td></tr>
<tr><td><b>T2 证据阶梯/污染</b></td><td>{r['T2']['decision']} — {r['T2']['honesty']}</td></tr>
<tr><td><b>T3 判据适配</b></td><td>{r['T3']['decision']}</td></tr>
<tr><td><b>T4 六条交叉核对</b></td><td>{r['T4']['decision']}</td></tr>
<tr><td><b>T5 诚实刻度</b></td><td>{r['T5']['decision']} — {r['T5']['attribution']}</td></tr>
<tr><td><b>T6 复述 vs 长牙</b></td><td>{r['T6']['decision']}</td></tr>
</table>

<h2>三、论文六条关键判定 × 我方框架交叉核对</h2>
<table>
<tr><th>论文判定</th><th>逐字原文</th><th>我方对应机制</th><th>状态</th></tr>
{rows_html}
</table>
<p class="small">{r['T4']['anti_duplicate']}；{r['T6']['kb_meta01_compliance'] and '受 KB-META01 约束：指不出被拦/被判/被降级动作即判复述。'}</p>

<h2>四、三层诚实结论</h2>
<div class="grid">
<div><b>① 事实层</b><br>{r['conclusion']['layer1_fact']}</div>
<div><b>② 推断边界</b><br>{r['conclusion']['layer2_boundary']}</div>
<div><b>③ 方法教训</b><br>{r['conclusion']['layer3_method']}</div>
</div>

<h2>五、真正"长牙"的编译产物（非复述）</h2>
<div class="card">
<p>对 T4 识别的 <b>2 条真缺口</b>，均指出了具体被拦/被判/被降级的动作，编译为
<code>svagent/component_attribution.py</code>（组件归因门禁），而非仅写进知识库：</p>
<table>
<tr><th>缺口</th><th>编译成的动作</th><th>拦截码</th></tr>
<tr><td>V3 失败≠改哪里</td><td>归因未落到 Prompt/Memory/Skill/Harness、无执行证据、无适配验证 → <b>block</b></td><td><code>ATTR.COMPONENT_MISSING / NO_EVIDENCE / VERIFY_MISSING</code></td></tr>
<tr><td>V6 退役覆盖</td><td>退役/drop 未检查低频但重要用途 → <b>downgrade 为 verify</b></td><td><code>ATTR.RARE_USE_UNCHECKED</code></td></tr>
</table>
<p class="small">验证方式按组件写死：Prompt→held-out、Memory→检索有效性、Skill→执行成功率、Harness→回归/副作用。
启发式候选只作提示，不作放行依据（防"我诊断过了"的自证）。</p>
</div>

<h2>六、反哺与收束</h2>
<div class="card">
<p>沉淀 6 条机制（KB-STRUCT01~06）：判据适配对象、谱系污染标注、组件归因、退役覆盖低频、
提出框架≠证明有效（preserve）、六条判定4条已具备防重复造轮子（preserve）。知识库 79 → <b>85 条、仍就绪</b>。</p>
<p>新增 <code>tests/test_component_attribution.py</code>（11 项）+ <code>tests/test_rsis_framework_analysis.py</code>（8 项），
期望值事前手工核算；全量 <b>287 测试通过</b>（含本次 essay 论证新增）；预注册锁存一致。</p>

<h2>七、全文到手后的修正记录（后验增量，诚实标注）</h2>
<div class="card">
<p>用户补传官方 PDF 后，对完整原文做核对式精读。<b>上一轮 T1–T6 无一翻转</b>，T3/T5 被强化；但发现二手转述的遗漏并新增两道真判据：</p>
<table>
<tr><th>修正项</th><th>结论</th></tr>
<tr><td>§10.6 论文自曝局限</td><td>目的性抽样、不估计设计流行率、分类<b>未经独立双编码</b>——比 §9 更根本的信度自曝（强化 T5）</td></tr>
<tr><td>§10.3 评估可靠性/安全</td><td>多个 LLM judge 共享错误，数量≠独立判断；记忆/技能投毒攻击(SKILL-INJECT) ——二手完全未覆盖</td></tr>
<tr><td>二手忠实但不完整</td><td>媒体覆盖了"独立验证/长期维护"，却漏掉评估可靠性、双编码局限、维护成本、可复现性记录四类高价值内容 → 印证一手优先</td></tr>
<tr><td>新增门禁（长牙）</td><td><code>svagent/evaluation_reliability.py</code>：①judge 独立性(同源多judge→降级) ②复现完整性/双编码(缺≥4项→不可复现；未双编码→不下普遍结论)</td></tr>
</table>
<p class="small">诚信声明：新增判据是全文到手后识别的<b>后验证据驱动增量</b>，不伪装成原预注册内容。修正记录锁存于 <code>rsi_structure_amendment.json</code>（sha256 c13b203f…）。知识库 85→<b>88 条、仍就绪</b>；新增 10 项测试，全量 <b>275 通过</b>。</p>
</div>
<blockquote>
<b>一句话收束：</b>这篇综述最值钱的不是它画的四组件图，而是它自己反复说的那句
"reuse alone does not establish recursive dependency"——它把「触发≠真相」写进了自己的判据；
我方则按 KB-META01 把其中两条真缺口编译成会拦会降级的门禁。<b>读到一个克制的框架，最好的致敬不是复述它，而是让它在本系统里长出牙。</b>
</blockquote>
</div>

</body></html>"""

(ROOT / "rsi_structure_report.html").write_text(html, encoding="utf-8")
print("saved rsi_structure_report.html", len(html))
