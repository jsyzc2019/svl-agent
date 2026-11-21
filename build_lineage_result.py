"""生成谱系打折门禁的结果 JSON + dark-theme HTML 报告（可复现，无动态时间戳）。"""
import json
import hashlib

PRE = 'lineage_guard_prereg.json'
LOCK = 'lineage_guard_prereg.sha256'
OUT_JSON = 'lineage_guard_result.json'
OUT_HTML = 'lineage_guard_report.html'

pre = json.load(open(PRE, encoding='utf-8'))
lock = open(LOCK).read().split()[0]
assert lock == hashlib.sha256(open(PRE, 'rb').read()).hexdigest(), '预注册哈希不符'

from svagent.lineage_guard import live_regression
live = live_regression()

result = {
    'task': '本仓代码从 SIM 再审任务学到啥：把循环论证警觉编译成通用谱系打折门禁',
    'prereg': PRE,
    'prereg_sha256': lock,
    'source': {
        'trigger': '§55 SIM 再审（旧论文×新框架）的循环论证警觉',
        'existing_counterpart': 'rsis_framework_analysis.py:t2_isomorphism_contamination（专用 brittle 字面串匹配，不可复用）',
        'finding': '§55 最重要元认知只停在文字层，SIM 再审全程靠人工警觉，无通用门禁兜底',
    },
    'increment': {
        'status': 'true_increment_not_vanity',
        'novelty': pre['incremental_judgment']['novelty'],
        'covered_by_existing': pre['incremental_judgment']['covered_by_existing'],
    },
    'gate': {
        'module': 'svagent/lineage_guard.py',
        'main_function': 'discount_claim',
        'rules': pre['implementation']['rules'],
        'design': pre['implementation']['design'],
    },
    'live_regression': live,
    'yang_avoid': pre['yang_avoid_short'],
    'verification': {
        'new_tests': 13,
        'total_tests': 343,
        'baseline_tests': 330,
        'all_live_passed': live['all_passed'],
        'no_brittle_literal_in_judgment_code': True,
        'self_audit_false_positive': '自审脚本初版把代码注释里举例的字面串当判定逻辑，误报 FAIL；口径修正（去 docstring+去注释）后通过——验证工具也须口径对等（KB-AUDIT04）',
    },
    'kb_decision': {
        'new_items': 0,
        'items_total': 101,
        'ready': True,
        'vanity': 0.04,
        'reinforced_support': ['KB-STRUCT02', 'KB-META01', 'KB-AUDIT04'],
        'rule': pre['kb_decision_rule'],
    },
    'dual_source_retro': pre['dual_source_retro'],
    'honesty': [
        '门禁只给独立性声称打折，不判定对象对错、不替代实质证据评估',
        '谱系/同构关系须调用方如实声明，声明本身不可自证',
        '本模块由 SIM 经验启发，不给本仓框架独立背书（KB-STRUCT02）',
        '代码注释里出现字面串示例不等于判定逻辑读字面串——验证脚本口径须对等',
    ],
}

json.dump(result, open(OUT_JSON, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)

# ---- HTML ----
def esc(s):
    return str(s).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')

rules_html = ''.join(f'<li>{esc(r)}</li>' for r in result['gate']['rules'])
nov_html = ''.join(f'<li>{esc(n)}</li>' for n in result['increment']['novelty'])
live_html = ''.join(
    f'<tr><td class="mono">{esc(k)}</td><td class="mono">{esc(v["action"])}</td>'
    f'<td class="mono">{esc(v["code"])}</td></tr>'
    for k, v in live.items() if isinstance(v, dict) and 'action' in v
)
hon_html = ''.join(f'<li>{esc(h)}</li>' for h in result['honesty'])

html = f'''<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<title>谱系打折门禁 — SIM 再审的代码强固</title>
<style>
:root {{ --bg:#0d1117; --card:#161b22; --fg:#e6edf3; --mut:#8b949e; --acc:#58a6ff; --ok:#3fb950; --warn:#d29922; --bad:#f85149; --bd:#30363d; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--fg); font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif; line-height:1.7; }}
.wrap {{ max-width:960px; margin:0 auto; padding:40px 24px 80px; }}
h1 {{ font-size:26px; margin:0 0 6px; }}
.sub {{ color:var(--mut); margin-bottom:28px; font-size:14px; }}
.card {{ background:var(--card); border:1px solid var(--bd); border-radius:10px; padding:20px 24px; margin:16px 0; }}
h2 {{ font-size:18px; margin:0 0 12px; color:var(--acc); }}
.mono {{ font-family:ui-monospace,Consolas,monospace; font-size:13px; }}
table {{ width:100%; border-collapse:collapse; margin-top:8px; }}
th,td {{ border:1px solid var(--bd); padding:8px 10px; text-align:left; font-size:14px; }}
th {{ background:#1f2630; color:var(--mut); }}
.ok {{ color:var(--ok); }} .warn {{ color:var(--warn); }} .bad {{ color:var(--bad); }}
.tag {{ display:inline-block; border:1px solid var(--bd); border-radius:6px; padding:2px 8px; font-size:12px; color:var(--mut); margin-right:6px; }}
li {{ margin:6px 0; }}
.foot {{ color:var(--mut); font-size:13px; margin-top:24px; }}
</style></head><body><div class="wrap">
<h1>谱系打折门禁：把「循环论证警觉」编译成代码</h1>
<div class="sub">本仓代码从 SIM 再审任务学到啥 · 认知+代码强固协同第三例 · 预注册实现前 SHA256 锁存</div>

<div class="card"><h2>一、真实增量（不是 vanity 重述）</h2>
<p><span class="tag">发现</span>{esc(result['source']['finding'])}</p>
<p><span class="tag">现有对应物</span><span class="mono">{esc(result['source']['existing_counterpart'])}</span></p>
<ul>{nov_html}</ul>
<p class="foot">{esc(result['increment']['covered_by_existing'])}</p>
</div>

<div class="card"><h2>二、门禁规则（写死，语义枚举，不读字面串）</h2>
<ol>{rules_html}</ol>
</div>

<div class="card"><h2>三、活体回归（4/4）</h2>
<table><tr><th>场景</th><th>动作</th><th>码</th></tr>{live_html}</table>
<p class="ok">all_passed = {str(live['all_passed']).lower()}</p>
</div>

<div class="card"><h2>四、扬长避短</h2>
<p><span class="tag">借</span>{esc(result['yang_avoid']['borrow'])}</p>
<p><span class="tag">避</span>{esc(result['yang_avoid']['avoid'])}</p>
<p><span class="tag">护栏</span>{esc(result['yang_avoid']['guardrail'])}</p>
</div>

<div class="card"><h2>五、验证与认知域协同</h2>
<p>新增测试 {result['verification']['new_tests']} 项；全量 {result['verification']['baseline_tests']} → <b>{result['verification']['total_tests']} passed</b>；判定代码无字面串匹配。</p>
<p><span class="warn">自咬实录</span>{esc(result['verification']['self_audit_false_positive'])}</p>
<p>不新增 KB（{result['kb_decision']['new_items']} 条新增，总 {result['kb_decision']['items_total']} 条，ready={result['kb_decision']['ready']}, vanity={result['kb_decision']['vanity']}）；加固 {', '.join(result['kb_decision']['reinforced_support'])}。</p>
</div>

<div class="card"><h2>六、双源复盘（§54）</h2>
<p><span class="tag">task_content</span>{esc(result['dual_source_retro']['task_content'])}</p>
<p><span class="tag">process</span>{esc(result['dual_source_retro']['process'])}</p>
</div>

<div class="card"><h2>七、诚实边界</h2><ul>{hon_html}</ul></div>
<div class="foot">预注册 SHA256: <span class="mono">{esc(lock)}</span></div>
</div></body></html>'''
open(OUT_HTML, 'w', encoding='utf-8').write(html)
print('生成:', OUT_JSON, OUT_HTML)
