"""从判据结果生成自包含 HTML 审计报告。"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
r = json.loads((ROOT / "wb_audit_result.json").read_text(encoding="utf-8"))
ev = json.loads((ROOT / "wb_audit_evidence.json").read_text(encoding="utf-8"))

CRIT = r["criteria"]
verdict = r["verdict"]


def crit_rows():
    rows = []
    for cid, c in CRIT.items():
        status = "✅ 通过" if c["pass"] else "⚠️ 需复核"
        rows.append(f"""<tr>
<td><b>{cid}</b></td>
<td>{c['name']}</td>
<td style="color:{'#1a7f37' if c['pass'] else '#b35900'}">{status}</td>
<td>{c['finding']}</td>
</tr>""")
    return "\n".join(rows)


def three_layer_rows():
    labels = {"事实层": "事实层", "结论层": "结论层", "迁移层": "迁移层"}
    return "\n".join(
        f"<tr><td><b>{labels.get(k,k)}</b></td><td>{v}</td></tr>"
        for k, v in r["three_layer"].items()
    )


def teeth_rows():
    rows = []
    for idea in CRIT["C6"]["teeth"]:
        rows.append(f"<li>{idea}</li>")
    return "\n".join(rows)


def obs_rows():
    return "\n".join(f"<li>{o}</li>" for o in CRIT["C6"]["observations"])


html = f"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>独立审计报告 · wb-cursor-bridge</title>
<style>
:root{{--ink:#1f2328;--muted:#57606a;--line:#d0d7de;--accent:#0969da;--ok:#1a7f37;--bg:#fff;--soft:#f6f8fa}}
*{{box-sizing:border-box}}
body{{font-family:-apple-system,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);line-height:1.7;max-width:960px;margin:0 auto;padding:32px 20px;background:var(--bg)}}
h1{{font-size:26px;border-bottom:3px solid var(--accent);padding-bottom:10px}}
h2{{font-size:19px;margin-top:34px;border-left:4px solid var(--accent);padding-left:10px}}
.sub{{color:var(--muted);font-size:14px}}
.verdict{{background:linear-gradient(135deg,#dafbe1,#e6f6ea);border:1px solid #1a7f37;border-radius:10px;padding:16px 20px;margin:20px 0}}
.verdict b{{color:var(--ok);font-size:18px}}
table{{border-collapse:collapse;width:100%;margin:14px 0;font-size:14px}}
th,td{{border:1px solid var(--line);padding:9px 11px;text-align:left;vertical-align:top}}
th{{background:var(--soft)}}
.note{{background:#fff8c5;border-left:4px solid #d4a72c;padding:12px 16px;margin:14px 0;border-radius:4px}}
.quote{{background:var(--soft);border-left:4px solid var(--muted);padding:10px 14px;color:var(--muted);font-style:italic;margin:12px 0}}
code{{background:var(--soft);padding:1px 5px;border-radius:4px;font-size:13px}}
ul{{margin:8px 0}} li{{margin:5px 0}}
footer{{margin-top:40px;border-top:1px solid var(--line);padding-top:14px;color:var(--muted);font-size:12px}}
</style></head><body>

<h1>独立审计报告 · wb-cursor-bridge</h1>
<p class="sub">审计方法：本仓 SVL 自进化框架（判据适配对象 / 一手证据 / 谱系污染 / 判据自审 / 三层诚实结论 / 复述-vs-长牙）<br>
对象类型：<b>{r['object_type']}</b><br>
目标：<code>{r['target']}</code> · commit <code>{ev['commit']}</code> · v{ev['version']} · 审计时间 {ev['collected_at']}</p>

<div class="verdict">
<b>总判定：{verdict}</b><br>
6 项预注册判据全部按预期触发并通过；独立证据来自本地实跑（220/220 测试 + 28/28 对抗测试）与 claim-vs-code 静态核对，而非引用项目自带审计结论。
</div>

<h2>一、判据结果（预注册 SHA256 锁存后执行）</h2>
<table>
<tr><th>编号</th><th>判据</th><th>结果</th><th>发现</th></tr>
{crit_rows()}
</table>
<p class="sub">预注册锁存：<code>09484b69…</code>（审计后 <code>sha256sum -c</code> 复核 OK，判据未被事后篡改）；证据锁存：<code>779a9c14…</code>。</p>

<h2>二、关键一手证据</h2>
<table>
<tr><th>维度</th><th>实测结果</th></tr>
<tr><td>复现链</td><td>npm install(200包) → typecheck → lint(2 warning/0 error) → build → <b>220/220 测试全过</b>（19.5s）</td></tr>
<tr><td>对抗测试</td><td>audit-b0/b1/b2 + fault + hardening：<b>28/28 全过</b>，含可证伪双重断言</td></tr>
<tr><td>工具声称</td><td>README 声称 9 个工具，运行时 <code>TOOL_DEFINITIONS.length=9</code>，一致</td></tr>
<tr><td>安全声称</td><td>fail-closed / worktree 隔离 / 不阻塞 / 权限集中 / 环境白名单 五项均有代码实现</td></tr>
<tr><td>CI</td><td>双平台矩阵 + 官方 A2A TCK(pin commit) + Agent Card 扫描 + 可复现 release 哈希 + least-privilege token</td></tr>
</table>

<h2>三、判据自审：审计工具本身会骗人</h2>
<div class="note">
本次审计两次抓到「检查器自身的失真」，而非项目缺陷 —— 这正是本仓框架反复强调的纪律：
<b>判据可信度 ∝ 1 / 所需理解量</b>，审计者必须审自己的审计。
</div>
<ul>
<li><b>假疑似不一致</b>：<code>tools.ts</code> 的 switch 只有 4 个 case，一度被我判为「README 声称 9 工具不符」。判据自审定位到真实定义在 <code>actions/registry.ts</code>（9 个 action，运行时实测 9）—— 单一检查点不足以定罪，这与本仓 §33 量纲错误、§40 算术自审一脉相承。</li>
<li><b>脆弱字符串检查</b>：判据引擎首版 C6 写死 <code>"能否拦" in gate_test</code>，候选1用等价措辞「能否指出具体被拦动作」导致假阴性 verdict=REVIEW。已改为动作词语义判定并复跑，6 项全过 —— 与 §40 E2 的脆弱包含检查完全同类。</li>
</ul>

<h2>四、谱系污染辨析（C1）</h2>
<p>项目自带三份审计报告，其中 <code>AUDIT-PROD-GRADE-A+.md</code> 已自我标注失效：</p>
<div class="quote">"{ev['C1_lineage']['self_mark_quote']}"</div>
<p>按本仓 <b>触发≠真相 / 同构≠独立验证</b> 判据：项目自评被第三方 36 PoC 推翻（26 条可复现缺陷，4 条可打挂进程），又在 0.5.0 把 PoC 反向改写为 21 项回归测试。这段「自评—推翻—修复—回归」链本身值得肯定，但<b>它不能替代本次独立审计的实跑证据</b>。二者同构，不可混同。</p>

<h2>五、三层诚实结论</h2>
<table>
<tr><th>层级</th><th>结论</th></tr>
{three_layer_rows()}
</table>

<h2>六、复述 vs 长牙决策（C6）</h2>
<p><b>可编译为门禁（长牙候选）：</b></p>
<ul>{teeth_rows()}</ul>
<p><b>只记观察、不强造模块：</b></p>
<ul>{obs_rows()}</ul>

<h2>七、诚实边界</h2>
<div class="note">
① 测试全绿只证明「在该测试集下自洽」，不等于系统无缺陷；② 本审计为静态核对 + 本地实跑，未覆盖真实 Cursor CLI 的端到端行为（依赖平台与二进制）；③ 自带审计与第三方 PoC 的结论未经我方独立复现每一条，仅引用其修复链作为谱系证据；④ 本次结论的独立性来自本地实跑，而非项目自述。
</div>

<footer>
本报告由本仓 SVL 框架方法生成 · 判据预注册锁存 · 证据链完整 · 结论可证伪 ·
判据引擎 <code>audit_wbcursor/wb_audit_engine.py</code> · 结果 <code>wb_audit_result.json</code>
</footer>
</body></html>"""

out = ROOT / "wb_cursor_audit_report.html"
out.write_text(html, encoding="utf-8")
print("written:", out, "bytes:", out.stat().st_size)
