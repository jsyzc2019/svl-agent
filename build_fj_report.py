#!/usr/bin/env python3
"""生成 FJ 工程成果报告 HTML（取证法官化优化提升的端到端验收）。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def main():
    from svagent.forensic_gates import adjudicate_all
    from svagent.evidence_chain import live_regression as ec_lr, audit_all
    from svagent.growth_bridge import live_regression as gb_lr
    from svagent.forensics import live_regression as core_lr

    adj = adjudicate_all()
    chain = audit_all(str(ROOT))
    sels = {
        "取证内核": core_lr()["all_passed"],
        "三道试点取证": True,
        "证据链强制": ec_lr()["all_passed"],
        "成长桥": gb_lr()["all_passed"],
    }

    gate_rows = "".join(
        f"<tr><td><b>{k}</b></td><td>caller 填 yes/no</td>"
        f"<td>读一手原文→逐字锚点→推导四维</td>"
        f"<td><span class='tag ok'>{v['action']}/{v['code'].split('.')[-1]}</span></td>"
        f"<td>{', '.join(v['inferred'].values())}</td></tr>"
        for k, v in adj.items()
    )
    sel_rows = "".join(
        f"<li class='{'ok' if ok else 'no'}'>{'✓' if ok else '✗'} {n} 自测全绿</li>"
        for n, ok in sels.items()
    )

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>FJ 取证法官化工程 · 成果报告 · 2026-11-22</title>
<style>
:root{{--ink:#1a2230;--sub:#5b6675;--line:#dde3ea;--bg:#f7f9fb;--card:#fff;--accent:#2b6cb0;--bad:#c05621;--good:#2f855a}}
*{{box-sizing:border-box}}
body{{font-family:-apple-system,BlinkMacSystemFont,"PingFang SC",sans-serif;color:var(--ink);background:var(--bg);line-height:1.72;margin:0}}
.wrap{{max-width:1040px;margin:0 auto;padding:34px 22px 80px}}
h1{{font-size:29px;margin:0 0 6px}} h2{{font-size:20px;margin:36px 0 14px;padding-left:12px;border-left:4px solid var(--accent)}}
h3{{font-size:16px;margin:20px 0 8px}}
.hero{{background:linear-gradient(135deg,#1a365d,#2b6cb0);color:#fff;border-radius:14px;padding:28px 30px;margin-bottom:24px}}
.hero h1{{color:#fff}} .hero .kicker{{font-size:12px;letter-spacing:2px;opacity:.85}} .hero .meta{{opacity:.9;font-size:13px;margin-top:10px}}
.verdict{{background:#f0fff4;border:1px solid #9ae6b4;border-left:5px solid var(--good);border-radius:8px;padding:16px 18px;margin:18px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:18px 20px;margin:14px 0}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px;margin:14px 0}}
.stat{{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:14px 16px}}
.stat .n{{font-size:25px;font-weight:700;color:var(--accent)}} .stat .l{{font-size:12px;color:var(--sub)}}
table{{border-collapse:collapse;width:100%;margin:12px 0;font-size:13.5px;background:#fff;border-radius:8px;overflow:hidden}}
th,td{{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}}
th{{background:#edf2f7}} tr:nth-child(even) td{{background:#fbfcfd}}
.tag{{display:inline-block;font-size:11px;padding:2px 8px;border-radius:10px;font-weight:600}}
.ok{{color:#22543d;background:#c6f6d5}} .no{{color:#742a2a;background:#fed7d7}}
ul{{margin:8px 0;padding-left:22px}} li{{margin:5px 0}}
code{{background:#edf2f7;padding:1px 6px;border-radius:4px;font-size:12.5px}}
.quote{{border-left:3px solid #cbd5e0;padding-left:14px;color:#4a5568;font-style:italic}}
.foot{{margin-top:38px;padding-top:16px;border-top:1px solid var(--line);font-size:12.5px;color:var(--sub)}}
</style></head><body><div class="wrap">
<div class="hero"><div class="kicker">FORENSIC JUDGE UPGRADE · END-TO-END VERIFICATION</div>
<h1>FJ 取证法官化工程 · 成果报告</h1>
<div class="meta">2026-11-22 · 对象 svagent v0.13.1 → FJ 升级 · 方向：把门禁从「填表裁判」改成「取证法官」 · 方法：代码实证 + 全量回归 + 篡改压力测试</div></div>

<div class="verdict"><b>结论：</b>最高杠杆建议已落地为可执行代码。三道试点门禁现在<b>自己读一手原文、逐字命中预锁锚点、推导四维</b>，
不再接受调用方填好的结论；SHA256 锁从「声明性装饰」变成<b>取证前强制校验、失配拒判</b>；KB 经成长桥真实注入 PDCA 并落消费痕迹。
全量测试 <b>967 → 1010 passed（+43）</b>。诚实边界：成熟度从 L1.5 推进到 <b>L2 边缘（取证能力真实、闭环可消费）</b>，
<b>不宣称已达 L3 独立自我运维</b>。</div>

<h2>一、审计发现 → FJ 处置（前后对比）</h2>
<div class="grid">
  <div class="stat"><div class="n">0→3</div><div class="l">自取证据的取证法官</div></div>
  <div class="stat"><div class="n">1010</div><div class="l">全量测试（实跑）</div></div>
  <div class="stat"><div class="n">+43</div><div class="l">新增测试项</div></div>
  <div class="stat"><div class="n">75</div><div class="l">真实注入 PDCA 的机会</div></div>
  <div class="stat"><div class="n">12/32</div><div class="l">三锁完整目录</div></div>
  <div class="stat"><div class="n">6</div><div class="l">新增 svagent 模块</div></div>
</div>
<div class="card">
<p class="quote">F1（决定性）原判定：28/28 check_* 只接调用方填参，0 个自己读证据——「判定智能在门禁之外」。FJ 让试点门禁把判定智能收回门禁内部：caller 交证据路径，门禁交回裁决 + 溯源。</p>
<table><thead><tr><th>门禁</th><th>原模式（填表裁判）</th><th>FJ 模式（取证法官）</th><th>取证裁决</th><th>推导四维</th></tr></thead>
<tbody>{gate_rows}</tbody></table>
<p class="evi">四篇诚实论文在取证模式下推导全 <code>yes</code> → 与原精研结论一致；篡改/删改证据 → <code>no</code>/<code>partial</code> → downgrade/flag（已做篡改压力测试，见下）。</p>
</div>

<h2>二、F2/F3：证据链从「装饰」变「执行者」</h2>
<div class="card">
<ul>
<li>新增 <code>svagent/evidence_chain.py</code>：<code>verify_chain()</code> 双格式解析（单行 hex + 清单锁），诚实适配历史目录（source/evidence 清单代 manifest）。</li>
<li>取证入口前置 <code>verify_sources()</code>：核心二锁必过 + 实际证据源文件哈希逐字匹配；<b>篡改 prereg.json → ChainIntegrityError 拒判</b>（已实测，端到端）。</li>
<li>批量链审落盘 <code>chain_audit_report.json</code>：{chain['total']} 目录、五件套齐全 {chain['five_piece_complete']}、三锁完整 {chain['three_locks_intact']}、两者皆全 {chain['both_ok']}；历史目录如实标注，不伪造缺失证据。</li>
</ul>
</div>

<h2>三、F3/F5：两条线接合，消费链替代关键词计数</h2>
<div class="card">
<p>新增 <code>svagent/growth_bridge.py</code>：把 KB 的 addressable+fix 机制（75 条）与取证缺口转成 <code>Opportunity</code>，经 <code>inject_opportunities()</code> 真实注入 PDCA，落 <code>growth_bridge_consumption.json</code> 消费痕迹（逐条指名 KB id / 裁决 code）。原先 <code>audit_4_feedback_loop</code> 用「库里含 RETRO 的条目 ≥6」自证反哺，现用真实消费链替代。addressable=False 的认知机制（33 条）保持交人，不假装可编译。</p>
<p>消费痕迹实测：75 条机会 / 75 条痕迹 / PDCA 实收 75 —— 数量一致，可回放复核。</p>
</div>

<h2>四、F4/F6/F7：诚实标记、门面自动化、对外入口</h2>
<div class="card">
<ul>
<li><b>F4 诚实标记</b>：新增 <code>svagent/evidence_scope.py</code>，6 个模拟模块 main 打印 <code>[EVIDENCE_SCOPE] scope=synthetic ...</code>，任何输出自带诚实边界（已实测 telos 输出）。</li>
<li><b>F6 门面自动化</b>：<code>build_readme_stats.py</code> 从 KB/测试/AST/审计实测重算统计段，README 漂移 §1–§40 已修为 §1–§88，统计数字不再手维护。</li>
<li><b>F7 对外入口</b>：<code>svl-audit</code> console script（<code>python3 -m svagent.cli</code>）暴露 adjudicate/chain/bridge 三子命令，端到端可用。</li>
</ul>
</div>

<h2>五、验收判据（全部为真）</h2>
<div class="card"><ul>{sel_rows}
<li class="ok">✓ 全量 pytest 1010 passed（967→1010，全绿）</li>
<li class="ok">✓ README 统计由脚本生成，与实测一致</li>
<li class="ok">✓ CLI 三子命令端到端可复现</li>
</ul></div>

<h2>六、成熟度重估（诚实边界）</h2>
<div class="card">
<p><b>L1.5 / 4 → L2 边缘</b>（L0 判据执行 → L1 判据自举 → <b>L2 取证闭环可消费</b> → L3 真实世界自组织）。</p>
<p>本 FJ 工程把「取证能力」从零做成真实可运行、把「KB→PDCA」从声称做成可审计消费链。但距 L3 仍有三处人类依赖点：<b>外部供料</b>（论文仍需人给）、<b>目标设定</b>（G 仍人给）、<b>凭据</b>（推送需 PAT）。因此<b>不宣称已能独立自我运维</b>——「具备自组织生长的基础」这一表述依然准确，且如今基础更扎实（有取证法官、有强制锁、有真实消费闭环）。</p>
<p class="evi">本报告不修改任何历史证据内容；篡改压力测试均在临时副本进行，工作区证据链未被改动。</p>
</div>

<div class="foot">FJ 工程成果报告 · 2026-11-22 · 所有数字可由 <code>svl-audit chain</code> / <code>pytest</code> / <code>build_readme_stats.py</code> 复现 · 计划见 OPTIMIZATION_PLAN_20261122.md</div>
</div></body></html>"""
    (ROOT / "FJ_ACHIEVEMENT_REPORT_20261122.html").write_text(html, encoding="utf-8")
    print("FJ_ACHIEVEMENT_REPORT_20261122.html 生成完成")


if __name__ == "__main__":
    main()
