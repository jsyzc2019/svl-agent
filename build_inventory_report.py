"""中国库存周期论证报告 HTML（自包含，数据来自真实抓取）。"""
import json
from pathlib import Path

BASE = Path("/workspace")
monthly = json.load(open(BASE / "china_monthly_raw.json"))
ppi = json.load(open(BASE / "china_ppi_monthly.json"))
ratio = json.load(open(BASE / "china_invsales_ratio.json"))

# 运行判据
import sys
sys.path.insert(0, str(BASE))
from svagent.inventory_cycle import classify, find_transitions

states = classify(monthly, ppi)
trans = find_transitions(states)


def fnum(x, suffix="", d=1):
    if x is None:
        return '<span class="na">NA</span>'
    color = "up" if x > 0 else ("down" if x < 0 else "")
    return f'<span class="{color}">{x:+.{d}f}{suffix}</span>'


# 主表
rows_html = []
for s in states:
    phase_cls = "passive" if "被动补库" in s.phase else ("active" if "主动补库" in s.phase else ("deact" if "主动去库" in s.phase else ("depas" if "被动去库" in s.phase else "neutral")))
    real_cls = "passive" if "被动补库" in s.phase_real else ("active" if "主动补库" in s.phase_real else ("deact" if "主动去库" in s.phase_real else ("depas" if "被动去库" in s.phase_real else "neutral")))
    r = ratio.get(s.period, {}).get("inv_sales_ratio")
    rows_html.append(
        f"<tr><td>{s.period}</td>"
        f"<td>{fnum(s.rev_yoy,'%')}</td>"
        f"<td>{fnum(s.inv_yoy,'%')}</td>"
        f"<td>{fnum(s.ppi_yoy,'%')}</td>"
        f"<td>{fnum(s.inv_real_yoy,'%')}</td>"
        f"<td>{fnum(r,'',3) if r else '<span class=na>NA</span>'}</td>"
        f'<td><span class="phase {phase_cls}">{s.phase}</span></td>'
        f'<td><span class="phase {real_cls}">{s.phase_real}</span></td></tr>'
    )

# 名义 vs 实际拆解表
decomp_rows = []
for p in ["2025-11", "2026-03", "2026-06", "2026-09"]:
    s = next(x for x in states if x.period == p)
    decomp_rows.append(
        f"<tr><td>{p}</td><td>{fnum(s.inv_yoy,'%')}</td><td>{fnum(s.ppi_yoy,'%')}</td>"
        f"<td>{fnum(s.inv_real_yoy,'%')}</td><td>{s.phase}</td><td>{s.phase_real}</td></tr>"
    )

html = r"""<!DOCTYPE html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>中国库存周期论证 · 主动补库→被动补库是否属实</title>
<style>
:root{--bg:#faf9f6;--ink:#1a1a1a;--muted:#666;--line:#e5e2dc;--red:#c0392b;--green:#1e8449;--amber:#b9770e;--blue:#1f4e79;--card:#fff}
body{background:var(--bg);color:var(--ink);font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;max-width:1100px;margin:0 auto;padding:32px 20px;line-height:1.7}
h1{font-size:24px;margin:0 0 4px}h2{font-size:18px;margin:30px 0 12px;padding-bottom:8px;border-bottom:2px solid var(--line)}
h3{font-size:14px;margin:18px 0 6px;color:var(--blue)}
.sub{color:var(--muted);font-size:13px;margin-bottom:18px}
.verdict{background:#1e3a2f;color:#e8f5e9;border-radius:10px;padding:18px 22px;margin:16px 0;font-size:14px}
.verdict b{color:#fbbf24}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:16px 20px;margin:14px 0;box-shadow:0 1px 3px rgba(0,0,0,.03)}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-top:8px}
th,td{padding:6px 8px;text-align:center;border-bottom:1px solid var(--line)}
th{background:#f3f1ec;font-weight:600;color:#444}
.up{color:var(--red);font-weight:600}.down{color:var(--green);font-weight:600}.na{color:#bbb}
.phase{border-radius:4px;padding:1px 7px;font-size:11.5px;white-space:nowrap}
.active{background:#fdecea;color:var(--red)}.passive{background:#fef5e7;color:var(--amber)}
.deact{background:#e8f5e9;color:var(--green)}.depas{background:#eaf2f8;color:var(--blue)}
.neutral{background:#f0f0f0;color:#888}
.kpi{display:flex;gap:12px;flex-wrap:wrap;margin:12px 0}
.kpi div{flex:1;min-width:140px;background:#f3f1ec;border-radius:8px;padding:12px;text-align:center}
.kpi b{font-size:19px;display:block;color:var(--blue)}.kpi span{font-size:12px;color:var(--muted)}
.timeline{display:flex;gap:4px;margin:14px 0;font-size:11px;flex-wrap:wrap}
.tl{flex:1;min-width:70px;padding:8px 4px;border-radius:6px;text-align:center;color:#fff}
ul{margin:8px 0;padding-left:22px}li{margin:5px 0;font-size:14px}
.small{font-size:12px;color:var(--muted)}
.badge{display:inline-block;border-radius:4px;padding:2px 9px;font-size:12px;color:#fff;background:var(--blue)}
</style></head><body>

<h1>中国库存周期：主动补库 → 被动补库，是否属实？</h1>
<div class="sub">真实领域验证 · 国家统计局月度数据 + 东方财富PPI · 预注册判据 · 截至 2026-09 · 学术研究，不构成投资建议</div>

<div class="verdict">
<b>结论先行：</b>就当前（2026 年 9 月）而言，<b>该说法不成立</b>——营收与库存双升，是主动补库。
"被动补库"确实发生过，但只在 <b>2025 年 10-12 月</b> 这段已结束的插曲里（营收降、库存升）。
且 2026 年名义库存 +11.6% 中约 <b>5 个百分点是 PPI 价格效应</b>，实际物量仅增 6.6%——名义叙事夸大了补库强度。
</div>

<div class="kpi">
<div><b>2025-10~12</b><span>被动补库 · 真实但短暂</span></div>
<div><b>2026-02 起</b><span>已切回主动补库</span></div>
<div><b>+11.6% → +6.6%</b><span>名义库存 → 实际库存</span></div>
<div><b>0.05~0.40</b><span>死区区间结论稳定</span></div>
</div>

<h2>一、这次如何对抗"后知先觉"与"幸存者偏差"</h2>
<div class="card">
<p>库存周期判定最大的坑：<b>同一个序列，换指标/窗口/名义实际口径能讲出相反故事</b>。搜索结果里华泰说"被动去库临近尾声"，另有报告说"年内首现被动补库"，东方财富证券说"名义主动补库、实际主动去库"——我一律把这些当<b>标签，绝不喂给判据</b>。</p>
<ul>
<li><b>预注册</b>：方向法四象限、3 期平滑、±0.15pct 死区、窗口 2024-01~2026-09，跑数前写死</li>
<li><b>盲判/揭盲分离</b>：判据只读营收+库存两条序列；机构结论产出后才对照</li>
<li><b>名义/实际双轨</b>：实际库存≈名义−PPI，专治"价格上涨伪装成补库"</li>
<li><b>消融+反例对照</b>：换窗口/死区/口径看是否翻转；历史公认阶段做健全性检查</li>
<li><b>缺失一等公民</b>：2023 上半年营收未取到，保留为空，不填补</li>
</ul>
</div>

<h2>二、数据来源（真实一手）</h2>
<div class="card">
<ul>
<li>国家统计局月度规上工业企业利润发布页，逐页抓取 <b>49 期</b>（2022-05~2026-09）：营收同比、产成品存货同比、周转天数</li>
<li>东方财富宏观接口 <code>RPT_ECONOMY_PPI</code>：PPI 月度同比 58 期</li>
<li>库销比交叉验证：发布页绝对金额自算（期末存货/月均营收）</li>
</ul>
<p class="small">注：库销比口径与研报（存货/当月营收）不同，数值不可直接比，趋势可比。</p>
</div>

<h2>三、盲判结果：四象限方向法（2024-01 ~ 2026-09）</h2>
<div class="card" style="overflow-x:auto">
<table>
<tr><th>月份</th><th>营收YoY</th><th>库存YoY</th><th>PPI</th><th>实际库存</th><th>库销比</th><th>名义阶段</th><th>实际阶段</th></tr>
""" + "\n".join(rows_html) + r"""
</table>
<p class="small"><span class="up">红=正增长</span> / <span class="down">绿=负增长</span>（中国惯例）。实际库存=名义−PPI。</p>
</div>

<h2>四、名义 vs 实际：揭穿"补库含金量"</h2>
<div class="card">
<table>
<tr><th>时点</th><th>名义库存</th><th>PPI</th><th>实际库存</th><th>名义阶段</th><th>实际阶段</th></tr>
""" + "\n".join(decomp_rows) + r"""
</table>
<p style="margin-top:12px"><b>读法：</b>2026-03 PPI 刚转正时，名义是"主动补库"，实际口径却仍是"被动去库"——价格回升制造了补库假象。到 2026-09，名义 +11.6% 里约 5pct 来自 PPI，真实物量增 6.6%。补库是真的，但没有名义数字看起来那么猛。</p>
</div>

<h2>五、稳健性与反例对照</h2>
<div class="card">
<ul>
<li><b>死区敏感性</b>：2026-07 主动补库在死区 0.05→0.40 全区间稳定；2025-11 被动补库在 ≤0.15 稳定</li>
<li><b>库销比交叉验证</b>：2025-10~11 从 0.592 升到 0.607，佐证被动累库；2026 全年在 0.61-0.64 高位但未持续恶化，符合"双升型主动补库"而非"需求塌陷"</li>
<li><b>历史反例对照</b>：判据复现了 2022-09 主动去库、2023-11 被动去库；但 2022-06 被判"去库·需求持平"而非公认"主动去库"——平滑抹平了需求方向，<b>这是判据的真实边界，如实记录</b></li>
</ul>
</div>

<h2>六、结论与诚实边界</h2>
<div class="card">
<p><span class="badge">结论</span> 分三层，不含糊：</p>
<ol>
<li><b>当前（2026-09）</b>：主动补库，非被动补库。营收库存双升，对阈值稳健。</li>
<li><b>2025Q4</b>：确有短暂被动补库，属实——但已结束三个月，不能描述当下。</li>
<li><b>名义有水分</b>：2026 名义库存高增约四成来自 PPI 价格效应，实际补库温和；"被动补库"若指实际物量累库压力，证据也不充分。</li>
</ol>
<p><b>边界</b>：四象限是行为表征分类，非企业意图直接观测（主动/被动本质是意图归因，这层循环无法消除）；累计同比有平滑滞后；2023 上半年数据缺失；PPI 减法为线性近似；n 有限不做统计推断。</p>
<p class="small" style="margin-top:14px">本研究为方法验证性质的学术演示，<b>不构成任何投资建议</b>。数据来源为国家统计局公开发布与东方财富公开接口，可能存在口径差异。</p>
</div>

<div class="sub" style="margin-top:24px;text-align:center">SVL 框架 · 真实领域验证系列 · 生成于 2026-11-21</div>
</body></html>
"""

out = BASE / "inventory_cycle_report.html"
out.write_text(html, encoding="utf-8")
print("生成", out, len(html), "字节")
