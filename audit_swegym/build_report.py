"""生成 SWE-Gym 精研审计报告（dark-theme HTML，本仓统一风格）。"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/workspace/audit_swegym")

CSS = """
:root{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--warn:#d29922;--no:#f85149;--acc:#58a6ff;--acc2:#bc8cff;--bd:#30363d}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.7;padding:40px 20px}
.wrap{max-width:980px;margin:0 auto}
h1{font-size:25px;color:var(--acc);margin-bottom:6px}
.sub{color:var(--mut);font-size:14px;margin-bottom:28px}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;margin-right:6px}
.badge.ok{background:rgba(63,185,80,.15);color:var(--ok);border:1px solid var(--ok)}
.badge.warn{background:rgba(210,153,34,.15);color:var(--warn);border:1px solid var(--warn)}
.badge.acc{background:rgba(88,166,255,.15);color:var(--acc);border:1px solid var(--acc)}
.hero{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:22px;margin-bottom:24px}
.hero .headline{font-size:15px;margin-top:12px}
.kpi{display:flex;gap:18px;margin-top:16px;flex-wrap:wrap}
.kpi div{background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:10px 16px;font-size:13px;color:var(--mut)}
.kpi b{color:var(--fg);font-size:18px;display:block}
h2{font-size:18px;color:var(--acc);margin:26px 0 12px;border-left:3px solid var(--acc);padding-left:10px}
.card{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:16px 18px;margin-bottom:12px}
.card .t{font-size:15px;font-weight:600;margin-bottom:6px;display:flex;align-items:center;gap:8px}
.card .f{font-size:13px;color:var(--mut)}
.card ul{margin:6px 0 0 18px;font-size:13px;color:var(--mut)}
.card li{margin:3px 0}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
th,td{border:1px solid var(--bd);padding:8px 10px;text-align:left}
th{background:var(--card);color:var(--acc)}
.note{background:rgba(248,81,73,.08);border-left:3px solid var(--no);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
.good{background:rgba(63,185,80,.08);border-left:3px solid var(--ok);padding:10px 14px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:var(--warn)}
footer{color:var(--mut);font-size:12px;margin-top:30px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def verdict_badge(v: str) -> str:
    if v.startswith("PASS") or v in ("CONSISTENT_WITH_CALIBER_GAP", "EXPLICIT_WITH_EVIDENCE", "ISOLATED_WITH_CAVEATS"):
        return "ok"
    if "DISCOUNTED" in v or "PARTIAL" in v or "LIMITED" in v or "GAP" in v:
        return "warn"
    return "acc"


def main() -> None:
    d = json.loads((ROOT / "result.json").read_text(encoding="utf-8"))
    j = d["judgments"]
    cards = ""
    names = {
        "S1": "claim_vs_code：方法有无代码实体",
        "S2": "number_caliber：数字复算与口径",
        "S3": "core_assumption：核心假设与佐证",
        "S4": "ablation_attribution：消融归因",
        "S5": "verifier_reliability：ORM 可靠性",
        "S6": "reproducibility_and_contamination：可复现与污染控制",
        "S7": "isomorphism_bias_guard：同构打折",
        "SA": "judge_self_audit：判据自审",
    }
    for k in ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "SA"]:
        item = j[k]
        badge = verdict_badge(item["verdict"])
        ev = "".join(f"<li>{esc(e)}</li>" for e in item["evidence"])
        minor = ""
        if item.get("minor"):
            minor = "<div class='note'><b>caveat：</b>" + "；".join(esc(m) for m in item["minor"]) + "</div>"
        cards += (f"<div class='card'><div class='t'><span class='badge {badge}'>{esc(item['verdict'])}</span> "
                  f"<span>{k} · {names[k]}</span></div><ul>{ev}</ul>{minor}</div>")

    reclo = "".join(
        f"<tr><td>{esc(r['item'])}</td><td>{esc(str(r['value']))}</td>"
        f"<td style='color:{'var(--ok)' if r['ok'] else 'var(--no)'}'>{'OK' if r['ok'] else 'FAIL'}</td></tr>"
        for r in d["number_recompute"]
    )
    cautions = "".join(f"<li>{esc(c)}</li>" for c in d["caliber_cautions"])
    boundaries = "".join(f"<li>{esc(b)}</li>" for b in d["honest_boundaries"])

    html = f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>SWE-Gym 精研审计</title><style>{CSS}</style></head><body><div class="wrap">
<h1>Training Software Engineering Agents and Verifiers with SWE-Gym</h1>
<div class="sub">ICML 2025 · PMLR 267 · arXiv 2412.21139v2（6 Jun 2025）· UC Berkeley / UIUC / CMU / Apple · 学术实证论文（环境/数据集 + 公开代码）· 审计于 2026-11-22</div>

<div class="hero">
  <div><span class="badge ok">8/8 判据通过</span><span class="badge ok">10 项复算自洽</span><span class="badge warn">摘要口径差 · 打折</span></div>
  <div class="headline">{esc(d['summary']['headline'])}</div>
  <div class="kpi">
    <div><b>8/8</b>判据通过</div>
    <div><b>2,438</b>环境任务</div>
    <div><b>491</b>训练轨迹</div>
    <div><b>100</b>知识库（不新增）</div>
  </div>
</div>

<h2>一手材料与锁存</h2>
<div class="card"><div class="f">
PDF 完整下载（576KB / v2 6 Jun 2025 / %%EOF 完整）；arXiv abs；代码仓 <b>SWE-Gym/SWE-Gym</b>（Apache-2.0，clone 4.8MB / HEAD 005c2fb，19 个训练/推理/数据准备脚本 + 配置）。
四重 SHA256 锁存（paper.pdf / paper.txt / arxiv_abs.html / prereg.json）全部写入 source.sha256。预注册如实标注已从二手看到方法/数字，专设 S5 verifier 可靠性与 S7 同构打折判据。
</div></div>

<h2>判据结论</h2>
{cards}

<h2>数字复算（口径对等）</h2>
<div class="card"><table>
<tr><th>项</th><th>复算值</th><th>判定</th></tr>
{reclo}
</table></div>
<div class="note"><b>口径警示：</b><ul>{cautions}</ul></div>

<h2>入库决策</h2>
<div class="good">SWE-Gym 的 verifier 可被 reward hacking 是 <b>KB-AUDIT07</b>（评价函数被篡改攻击面）的一手实证；环境→轨迹→判据同构按 <b>KB-STRUCT02</b> 打折。两者均已被现有条目覆盖 → <b>不新增条目</b>，加固 KB-AUDIT07 / KB-STRUCT07 / KB-RSI06 / KB-META01 的 support 指针。知识库 100 条，ready=True。</div>

<footer>诚实边界：<ul style="list-style:none">{boundaries}</ul>结论限于静态证据与算术一致性核对。</footer>
</div></body></html>"""
    (ROOT / "swegym_report.html").write_text(html, encoding="utf-8")
    print(f"HTML: {len(html)} chars -> swegym_report.html")


if __name__ == "__main__":
    main()
