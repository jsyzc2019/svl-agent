"""端到端独立审计报告 HTML（空杯/第三方视角）。"""
from pathlib import Path

html = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>端到端独立审计报告 · SVL 框架</title>
<style>
:root{--bg:#faf9f6;--ink:#1a1a1a;--muted:#666;--line:#e5e2dc;--red:#c0392b;--green:#1e8449;--amber:#b9770e;--blue:#1f4e79;--card:#fff}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;max-width:1020px;margin:0 auto;padding:32px 20px;line-height:1.72}
h1{font-size:25px;margin:0 0 4px}h2{font-size:18px;margin:32px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--line)}
h3{font-size:14px;margin:18px 0 6px;color:var(--blue)}
.sub{color:var(--muted);font-size:13px;margin-bottom:18px}
.lead{background:#1f2937;color:#f3f4f6;border-radius:10px;padding:18px 22px;margin:16px 0;font-size:14px}
.lead b{color:#fbbf24}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.03)}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:8px}
th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line)}
th{background:#f3f1ec;font-weight:600;color:#444}
.p0{color:#fff;background:var(--red);border-radius:4px;padding:1px 8px;font-size:12px}
.p1{color:#fff;background:var(--amber);border-radius:4px;padding:1px 8px;font-size:12px}
.p2{color:#fff;background:var(--blue);border-radius:4px;padding:1px 8px;font-size:12px}
.ok{color:var(--green);font-weight:600}
.bad{color:var(--red);font-weight:600}
.exptitle{font-weight:600;color:var(--blue);font-size:14px;margin-top:4px}
.quote{border-left:4px solid var(--amber);background:#fff8e1;padding:10px 14px;border-radius:6px;font-size:13px;color:#7a5b00;margin:10px 0}
ul{margin:8px 0;padding-left:22px}li{margin:6px 0;font-size:14px}
.small{font-size:12px;color:var(--muted)}
.big{font-size:15px;font-weight:600}
</style></head><body>

<h1>端到端独立审计报告 · SVL 框架</h1>
<div class="sub">空杯心态 · 第三方/上帝视角 · 对现有代码的攻击性实验 · 基于第 17/18 节真实验证经验</div>

<div class="lead">
审计目标不是辩护，是<b>找漏洞、证伪、拆穿假象</b>。方法：对现有代码故意构造能让它露馅的输入，用数据说话。<br><br>
总评：<b>真功夫与叙事包装各占一半</b>；叙事包装那一半几乎全部建立在合成数据的自证循环上，
唯一碰真实数据的财报层又被证明有后验分组循环。<b>自洽 ≠ 有效。</b>
</div>

<h2>一、六项攻击性实验（结果直录）</h2>

<div class="card">
<div class="exptitle">实验 A · telos 的"校准度"是装饰性参数</div>
<p>固定带宽 1.3，只扫描 calibration。准确率全部 100%，只有观察次数变化：</p>
<table><tr><th>calibration</th><th>0.2</th><th>0.4</th><th>0.6</th><th>0.8</th><th>1.0</th></tr>
<tr><td>准确率</td><td>100%</td><td>100%</td><td>100%</td><td>100%</td><td>100%</td></tr>
<tr><td>观察次数</td><td>5.87</td><td>6.21</td><td>6.72</td><td>7.83</td><td>8.75</td></tr></table>
<div class="quote">原任务真值 0.8 vs 0.15（间隔 0.65、噪声 0.28）→ 简单到全员满分，准确率指标零分辨力。
所谓"专家胜过弱 AI"在此设置下根本无法成立。</div>
</div>

<div class="card">
<div class="exptitle">实验 B · 难度一变，叙事露馅 + "最优停止"失效</div>
<p>真值改 0.55 vs 0.45、噪声 0.5：弱 AI <b>68%</b>、专家人 <b>85%</b>、强 AI <b>98%</b>——差异出现，
说明 telos 不是全错，但它是靠"选一个全员满分的简单任务"来证明能力无关身份。</p>
<div class="quote">更致命：难任务下所有主体观察次数都 ~19 次（上限 20），根本没有"停止"。
被大书特书的"沿期望曲线走到最优停止点"只在玩具难度下成立。</div>
</div>

<div class="card">
<div class="exptitle">实验 C · axiology 的价值自举是线性恒真循环</div>
<p>故意用一个随机、无语义的 V 当 latent → 恢复余弦 <b>0.770</b>、可解释率 <b>82%</b>。</p>
<div class="quote">随机垃圾 V 也能被"恢复"→ "从行为反推价值"只是"线性生成 → 线性拟合"的必然，
与"价值"语义无关。报告里余弦 0.96 证明不了"agent 自己造出了 V"。</div>
</div>

<div class="card">
<div class="exptitle">实验 D · estimation 判定倾向符号反了（硬 bug）</div>
<table><tr><th>真 criterion</th><th>−2.0</th><th>−1.0</th><th>0.0</th><th>+1.0</th><th>+2.0</th></tr>
<tr><td>估出 criterion</td><td>+3.58</td><td>+2.15</td><td>−0.06</td><td>−2.03</td><td class="bad">−3.55</td></tr></table>
<div class="quote">生成模型里 decision&gt;criterion 才否决 → criterion 越高越保守；但模块注释写"负值=保守"。
真 +2（最保守）估出 −3.55（按注释是最激进）——<b>估参符号与它自己的生成定义完全相反</b>，
接回 telos 会得到系统性错误的画像。另：slope 随 dprime 饱和（2.198→2.585），绝对值不可辨识；
AUC（证据区分真值）被当"校准度"（confidence=正确率）使用，是统计概念混用。</div>
</div>

<div class="card">
<div class="exptitle">实验 E · mechanism 的"稳健汇聚"是有条件的</div>
<table><tr><th>系统目标</th><th>生成者独裁</th><th>审查者独裁</th><th>M4 职责加权</th></tr>
<tr><td>真实优先（默认）</td><td>0.538</td><td>0.021</td><td class="ok">0.0045 最优</td></tr>
<tr><td>产量优先（反方向）</td><td class="ok">0.0038 最优</td><td>0.536</td><td class="bad">0.402</td></tr></table>
<div class="quote">M4 的稳健以"系统目标永远偏真实/精确"为前提；换成产量优先即被独裁碾压。
模块承认"目标明确时独裁更优"，但宣传口径的"稳健"掩盖了边界。</div>
</div>

<div class="card">
<div class="exptitle">实验 F/G · 财报盲测的"盲"只做到代码层，没做到构造层</div>
<p>参评 9 家中 alarm=1 的 4 家<b>全是 risk 组</b>，非标 3 家也全在其中。分组是后验标注的，
代码确实没读它，但驱动 alarm 的增速背离本质是"经营困境"代理，而"困境公司"与"risk 组"是同一集合的两个名字。</p>
<div class="quote">奥瑞德是结构缺陷铁证：前四年信号（收现 4 次、增速背离 3 次）强过多个真阳性，
却已反转恢复正常 → 静态窗口聚合对"趋势反转"无能为力，不是调阈值能修的。</div>
</div>

<h2>二、全局盘点：真功夫 vs 叙事包装</h2>
<div class="card">
<table><tr><th>类别</th><th>模块</th><th>数据来源</th></tr>
<tr><td>唯一碰真实数据</td><td>finance_fetch / finance_audit / finance_blind_test</td><td>东方财富公开接口</td></tr>
<tr><td>全合成自证</td><td>telos / axiology / estimation / mechanism / insight / evolution / autopoiesis / self_evolving / pdca / experiment</td><td>random / simulate / synth，零真实数据</td></tr>
<tr><td>纯逻辑骨架</td><td>core / harness / verifiers / handoff</td><td>无数据依赖</td></tr>
</table>
<p class="big" style="margin-top:14px">最重的一条结论</p>
<p>整套"递归自进化 / 价值自举 / 认知量化 / 机制汇聚"的理论大厦，<b>100% 建立在合成数据上</b>，
靠自证循环维持；唯一碰真实数据的财报层又被证明有后验分组循环。
合成数据里我可以精确控制生成过程，让每个机制恰好 work；真实数据会暴露我连想都没想过的失败模式
（第 17 节两个 bug、本节实验 D 的符号反转）。</p>
</div>

<h2>三、真功夫（经得起审计，公正确认）</h2>
<div class="card">
<ul>
<li><b>坍塌映射 φ</b>：把语义问题转成符号判据，迁移成立，真实财报上可执行。</li>
<li><b>反偏差实验纪律</b>：盲判/揭盲分离、未知标签剔除、强制 FP-FN、固定种子、消融——方向正确。</li>
<li><b>自我揭露精神</b>：第 18 节主动消融、揭穿"recall=1.0 主要是同义反复"——诚实，非包装。</li>
<li><b>交人卡 + 来源隔离</b>：不可约判断切 O(1)、isUserSaid 来源校验，工程扎实。</li>
<li><b>真实数据打脸自身代码</b>：负分母、"无保留"误命中——这个循环是真实的。</li>
</ul>
</div>

<h2>四、分级问题清单</h2>
<div class="card">
<p><span class="p0">P0 硬 bug</span> estimation 的 criterion 符号与生成模型定义相反 → 画像接回 telos 系统性错误。</p>
<p style="margin-top:10px"><span class="p1">P1 方法论</span>
① telos 用全员满分的简单任务证明能力差异，准确率无分辨力，最优停止只在玩具难度成立；
② axiology 价值自举是线性恒真循环，随机 V 也能恢复，"agent 造 V"宣称不成立；
③ 财报盲测"盲"无信号构造独立性，"预测非标"≈"用困境预测困境的结果"。</p>
<p style="margin-top:10px"><span class="p2">P2 诚实边界</span>
① mechanism 稳健以真实优先目标为前提；② 除财报层外全部理论模块零真实数据验证；
③ AUC 被当 calibration 使用，概念混用。</p>
</div>

<h2>五、如果我是认真的：修复路线</h2>
<div class="card">
<ul>
<li><b>修 P0</b>：统一 criterion 符号，加回归测试断言"保守者估出正 criterion"。</li>
<li><b>telos 去玩具化</b>：自适应难度（真值间隔 0.65→0.1）设为默认；报告"最优停止"必须同时报告难任务是否真的停了。</li>
<li><b>axiology 非同构检验</b>：用非线性策略生成决策，看线性 IRL 能否恢复；不能则宣称降级为"线性价值在 Linear 世界可恢复"。</li>
<li><b>财报盲测去循环</b>：用"困境但标准无保留"(奥瑞德)与"不困境但非标"两组反例做对照；分组标签从源头剔除。</li>
<li><b>真实数据注入</b>：telos/estimation 至少接一批真实裁决日志，打破全合成自证——这是从"自洽"走向"有效"的唯一路径。</li>
</ul>
</div>

<h2>六、审计收束：区分"自洽"与"有效"</h2>
<div class="card">
<p>这套框架最擅长的，是在自己定义的规则里自洽——每一层都能用合成数据讲通一个漂亮故事。
但<b>自洽不等于有效</b>：一个循环论证的系统可以完美自洽，却对真实世界零信息量。</p>
<p>真正把它从"自洽"推向"有效"的只有两样东西：
<b>真实数据</b>（揭穿你没想过的 bug）和<b>对抗性证伪</b>（拆穿你以为成立的机制）。本节做的是后者。</p>
<p class="big">结论不是"框架没用"，而是：坍塌映射与反偏差纪律是真功夫，宏大叙事是待验证的假设——
把两者分开标注，才是对这套系统最诚实的使用方式。</p>
<p class="small">审计依据：对 /workspace/svagent/ 现有代码的攻击性实验，全部可复现；结论记录于 commentary.md 第 19 节。</p>
</div>

</body></html>"""

Path("/workspace/independent_audit_report.html").write_text(html, encoding="utf-8")
print("审计报告已生成: /workspace/independent_audit_report.html")
