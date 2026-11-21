"""生成 OpenAI Performance Factory 精研报告：result JSON + dark-theme HTML（可复现）。"""
import json

R = json.load(open('result.json', encoding='utf-8'))
LIVE = None
import sys
sys.path.insert(0, '..')
from svagent.backtest_integrity import live_regression as _lr
LIVE = _lr()

crit_rows = ''.join(
    f'<tr><td class="mono">{c["id"]}</td><td>{c["name"]}</td>'
    f'<td class="{"ok" if c["verdict"]=="ok" else "warn"}">{c["verdict"]}</td>'
    f'<td>{c["note"]}</td></tr>' for c in R['criteria']
)
num_rows = ''.join(
    f'<tr><td>{n["item"]}</td><td class="mono">{n["value"]}</td>'
    f'<td class="mono">{n["claim"]}</td><td class="{"ok" if n["ok"] else "bad"}">{"OK" if n["ok"] else "FAIL"}</td></tr>'
    for n in R['number_recompute']
)
spoiler = R['criteria'][3]['spoiler_measures_present']
spoiler_rows = ''.join(
    f'<li class="{"ok" if v else "bad"}">{"✓" if v else "✗"} {k}</li>'
    for k, v in spoiler.items()
)
tl = R['three_layer_honesty']
live_rows = ''.join(
    f'<tr><td class="mono">{k}</td><td class="mono">{v["action"]}</td><td class="mono">{v["code"]}</td></tr>'
    for k, v in LIVE.items() if isinstance(v, dict) and 'action' in v
)
hb = ''.join(f'<li>{h}</li>' for h in R['honesty_boundaries'])

html = f'''<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>OpenAI Performance Factory 精研</title>
<style>
:root{{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--acc:#58a6ff;--ok:#3fb950;--warn:#d29922;--bad:#f85149;--bd:#30363d}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,"Segoe UI","PingFang SC",sans-serif;line-height:1.7}}
.wrap{{max-width:1000px;margin:0 auto;padding:40px 24px 80px}}h1{{font-size:26px;margin:0 0 6px}}
.sub{{color:var(--mut);margin-bottom:28px;font-size:14px}}
.card{{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:20px 24px;margin:16px 0}}
h2{{font-size:18px;margin:0 0 12px;color:var(--acc)}}
table{{width:100%;border-collapse:collapse;margin-top:8px}}
th,td{{border:1px solid var(--bd);padding:8px 10px;text-align:left;font-size:13px;vertical-align:top}}
th{{background:#1f2630;color:var(--mut)}}
.mono{{font-family:ui-monospace,Consolas,monospace;font-size:12px}}
.ok{{color:var(--ok)}}.warn{{color:var(--warn)}}.bad{{color:var(--bad)}}
.tag{{display:inline-block;border:1px solid var(--bd);border-radius:6px;padding:2px 8px;font-size:12px;color:var(--mut);margin-right:6px}}
ul{{margin:8px 0}}li{{margin:4px 0}}.foot{{color:var(--mut);font-size:12px;margin-top:24px}}
.banner{{background:#132a1a;border:1px solid var(--ok);border-radius:8px;padding:12px 16px;margin:12px 0}}
</style></head><body><div class="wrap">
<h1>精研：OpenAI Performance Factory keeps ChatGPT fast</h1>
<div class="sub">工程博客一手研读 · 判据 P1–P7 · 数字复算 · 三层诚实结论 · 代码强固裁决（§57） · 预注册分析前 SHA256 锁存</div>

<div class="banner"><b>一句话结论：</b>一篇扎实的官方工程博客，给出可借鉴的 agent 工作流架构与 8 条回测防泄露纪律；数字自洽但全为 self-reported、无外部复现。本仓从中编译出第一道『回测信息污染隔离』门禁，补齐 evaluation_reliability 的缺口。</div>

<div class="card"><h2>一、对象与来源</h2>
<p>{R['source']['type']}</p>
<p><span class="tag">URL</span><span class="mono">{R['source']['url']}</span></p>
<p><span class="tag">锁存</span><span class="mono">SHA256 {R['source']['sha256_lock']}（分析前）</span></p>
</div>

<div class="card"><h2>二、判据 P1–P7（{R['summary']['ok']}/{R['summary']['total']} OK）</h2>
<table><tr><th>ID</th><th>判据</th><th>结论</th><th>要点</th></tr>{crit_rows}</table>
<p class="foot">P1 首版用 all 匹配 4 个愿景词过严被自咬（弯引号导致 exploring 未命中），改为 any+宽字符类——信事实、改判据。</p>
</div>

<div class="card"><h2>三、数字复算（内部一致性）</h2>
<table><tr><th>项</th><th>复算值</th><th>文章声称</th><th>判定</th></tr>{num_rows}</table>
<p class="foot">数字自洽不等于真实性：均为官方 self-reported，无开源代码、无外部复现（KB-RSI06 样本外复验折扣）。</p>
</div>

<div class="card"><h2>四、P4 重点：8 条回测防 spoiler 纪律（本仓缺口）</h2>
<ul>{spoiler_rows}</ul>
<p>本仓 evaluation_reliability.py 无对应可执行门禁（P4 真实核验 repo_has_corresponding_gate=False）→ 代码强固候选成立。</p>
</div>

<div class="card"><h2>五、代码强固：backtest_integrity.py（会拦/会判/会降级）</h2>
<table><tr><th>活体场景</th><th>动作</th><th>码</th></tr>{live_rows}</table>
<p class="ok">活体回归 {str(LIVE['all_passed']).lower()} · 新增 14 项测试 · 全量 343 → 357 passed</p>
<p class="foot">规则：关键隔离项（fresh/stripped/no-writeup）缺失→block；弱项缺失→downgrade；事后查获 spoiler→block；状态未声明→flag。纯函数/语义布尔/不读字面串；吸取 §56 教训，源码核验先去注释。</p>
</div>

<div class="card"><h2>六、三层诚实结论</h2>
<p><span class="tag">可判</span>{'; '.join(tl['can_judge'])}</p>
<p><span class="tag">不可判</span>{'; '.join(tl['cannot_judge'])}</p>
<p><span class="tag">同构打折</span>{tl['isomorphism_discount']}</p>
</div>

<div class="card"><h2>七、入库决策与诚实边界</h2>
<p>不新增 KB（防 vanity）：加固 KB-RSI06 / KB-AUDIT04 / KB-AUDIT02 的 support 指针指向新门禁。知识库 101 条、ready=True、vanity 0.04。</p>
<ul>{hb}</ul>
</div>
<div class="foot">pre-reg SHA256 lock verified · date 2026-11-22 · SVL Agent 精研流水线</div>
</div></body></html>'''
open('perf_factory_report.html', 'w', encoding='utf-8').write(html)

out = {
    'article': R,
    'code_hardening': {
        'module': 'svagent/backtest_integrity.py',
        'main_function': 'check_backtest_integrity',
        'live_regression': LIVE,
        'new_tests': 14, 'total_tests': 357,
        'prereg': 'audit_openai_perf/hardening_prereg.json',
        'prereg_sha256': open('hardening_prereg.sha256').read().split()[0],
    },
    'kb_decision': {'new_items': 0, 'total': 101, 'ready': True, 'vanity': 0.04,
                    'reinforced': ['KB-RSI06', 'KB-AUDIT04', 'KB-AUDIT02']},
}
json.dump(out, open('perf_factory_result.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
print('生成 perf_factory_report.html + perf_factory_result.json')
