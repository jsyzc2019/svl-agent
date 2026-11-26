"""生成框架自我反省报告（聚焦 scope=framework 三分法，不放虚荣指标）。"""
from svagent.retrospective import Retrospective, framework_reflection_trace

rev = Retrospective()
r = rev.review(framework_reflection_trace())
a = r.improvement_audit

def rows(key):
    return "".join(f"<li>{x}</li>" for x in a.get(key, [])) or "<li class='muted'>（无）</li>"

html = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>框架逻辑方法的自我反省</title>
<style>
:root{--bg:#faf9f6;--ink:#1a1a1a;--muted:#777;--line:#e5e2dc;--red:#c0392b;--green:#1e8449;--amber:#b9770e;--blue:#1f4e79;--card:#fff}
*{box-sizing:border-box}body{background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','PingFang SC',sans-serif;line-height:1.75;margin:0;padding:32px 20px}
.wrap{max-width:900px;margin:0 auto}h1{font-size:25px;margin:0 0 6px}h2{font-size:18px;margin:30px 0 12px;border-left:4px solid var(--blue);padding-left:12px}
.lead{color:var(--muted);font-size:15px;margin-bottom:24px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 24px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.04)}
.muted{color:var(--muted);font-size:13px}.fix{border-left:4px solid var(--green)}.vanity{border-left:4px solid var(--amber)}.preserve{border-left:4px solid var(--blue)}
.bug{border-left:4px solid var(--red);background:linear-gradient(90deg,rgba(192,57,43,.06),transparent)}
ul{margin:8px 0;padding-left:22px}li{margin:7px 0}.tag{font-size:12px;color:var(--muted)}
.quote{background:linear-gradient(90deg,rgba(31,78,121,.07),transparent);border-left:4px solid var(--blue);padding:12px 18px;margin:14px 0}
.foot{margin-top:30px;color:var(--muted);font-size:12px;text-align:center;border-top:1px solid var(--line);padding-top:16px}
b.hl{color:var(--red)}
</style></head><body><div class="wrap">
<h1>框架逻辑方法的自我反省</h1>
<p class="lead">复盘不是为改进而改进，而是自我反醒；改进该改进的，只针对自己——这是框架逻辑方法层面的事。本次复盘对象：第19节独立审计 → 第20节整改（scope=framework，非研究对象）。</p>

<div class="card">
<div class="tag">事前锚点（可追溯：第19节 P0/P1/P2 清单早于第20节整改，门禁通过）</div>
<p>__EXPECTED__</p>
<div class="tag">揭盲结果</div>
<p>__ACTUAL__</p>
<p class="muted">根因：__ROOT__</p>
</div>

<h2>改进该改进的：三分法</h2>

<div class="card fix">
<b style="color:var(--green)">① 真该改的（改机制而非文案）—— __N_FIX__ 条</b>
<ul>__FIX__</ul>
</div>

<div class="card vanity">
<b style="color:var(--amber)">② 虚荣改进（改动冒充进步，需识破）—— __N_VANITY__ 条</b>
<ul>__VANITY__</ul>
</div>

<div class="card preserve">
<b style="color:var(--blue)">③ 不该改的（守住框架的脊梁）—— __N_PRESERVE__ 条</b>
<ul>__PRESERVE__</ul>
</div>

<div class="quote">改进不是越多越好。<b>真该改的改机制，虚荣的识破，边界的守住</b>——三者分清，才叫"改进该改进的"。上一轮把审计列的每条都当作"该修的"，用复利曲线与教训计数包装成进步叙事，这本身就是需要被识破的<b class="hl">改进冲动</b>，不是成果。</div>

<h2>一面镜子：连"改进分类"本身都会出错</h2>
<div class="card bug">
<p>初版分类用全文关键词匹配，P0 符号 bug 那条 rationale 写着"改的是机制<b class="hl">而非文案</b>"——含"文案"二字，被误判成虚荣改进，<b>真该改的被当成虚荣的</b>。这恰恰违背"改进该改进的"。</p>
<p><b>修复</b>：只认 rationale 的前缀显式标记（fix:/vanity:/preserve:），无标记归入 unclassified 由人补，绝不擅自猜测。两条回归测试固化。<br>
<span class="muted">这条 bug 是本次反省的活证据：连"识别什么是真改进"都会出错，所以自我反省必须落到可测试的机制上，而不能停留在态度表态。</span></p>
</div>

<h2>方向校正</h2>
<div class="card">
<p>上一轮复盘对象是<b>研究对象</b>（subject：库存周期/华测导航），本轮依用户指正改为<b>框架逻辑方法</b>（framework：只针对自己）。这不是措辞调整，而是把 `scope` 写进数据结构、把"改进该改进的"写成 `improvement_class` 字段与测试的机制改动。</p>
</div>

<div class="foot">框架版本 0.13.0 · 元认知复盘层 L3 · 框架逻辑方法自我反省 · 6 项专项测试通过 · 方法研究</div>
</div></body></html>"""

html = (html
    .replace("__EXPECTED__", r.expected)
    .replace("__ACTUAL__", r.actual)
    .replace("__ROOT__", r.root_cause)
    .replace("__N_FIX__", str(len(a.get("fix", []))))
    .replace("__N_VANITY__", str(len(a.get("vanity", []))))
    .replace("__N_PRESERVE__", str(len(a.get("preserve", []))))
    .replace("__FIX__", rows("fix"))
    .replace("__VANITY__", rows("vanity"))
    .replace("__PRESERVE__", rows("preserve")))

with open("/workspace/framework_reflection_report.html", "w", encoding="utf-8") as f:
    f.write(html)
print("生成 framework_reflection_report.html", len(html), "字符")
