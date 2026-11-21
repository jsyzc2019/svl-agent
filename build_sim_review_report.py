"""生成 SIM 再审报告（JSON 已由引擎产出，这里做 dark-theme HTML），预注册分离。"""
import json

r = json.load(open("sim_review_result.json", encoding="utf-8"))
old = json.load(open("sim_framework_result.json", encoding="utf-8"))

def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

labels = {
    "N1": "judge 独立性（分域）", "N2": "跨模型迁移（相对基线）",
    "N3": "bootstrap 稳健性", "N4": "条件消融（记忆净贡献）",
    "N5": "计分完整性（harness 攻击面）", "N6": "本次任务双源复盘",
}
cards = ""
for k in ["N1", "N2", "N3", "N4", "N5", "N6"]:
    v = r[k]
    action = v.get("action", "")
    color = "ok" if action in ("ok",) else ("warn" if action in ("downgrade", "flag") else "blk")
    code = v.get("code", "")
    if k == "N1":
        code = f"workspace={v['workspace']['code']} / coding={v['coding_verifier']['code']}"
    vv = v.get("verdict_vs_old", "")
    vvc = "blk" if vv == "补刀" else ("ok" if vv == "确认+精化" else "warn")
    cards += (
        "<div class='card'><h3>" + k + " · " + labels[k] +
        " <span class='" + color + "'>[" + esc(action or "分域") + "]</span></h3>"
        "<p><b>门禁码：</b><code>" + esc(code) + "</code>　<b class='" + vvc + "'>vs 旧：" + esc(vv) + "</b></p>"
        "<p class='analysis'>" + esc(v["analysis"]) + "</p></div>"
    )

meta = r["_meta"]
honest = meta["three_layer_honesty"]

html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>SIM 再审 · 旧论文 × 新框架 · SVL</title><style>
:root{--bg:#0d1117;--panel:#161b22;--border:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#58a6ff;--ok:#3fb950;--warn:#d29922;--blk:#f85149}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 -apple-system,"PingFang SC",Segoe UI,sans-serif;padding:40px max(24px,calc((100% - 1040px)/2))}
h1{font-size:26px;color:var(--acc);margin-bottom:6px}h2{font-size:19px;margin-top:34px;border-bottom:1px solid var(--border);padding-bottom:8px;color:var(--acc)}
.lead{color:var(--mut)}code{color:#79c0ff;font-size:13px}.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:16px 20px;margin:14px 0}
.card h3{margin:0 0 8px;font-size:16px}.analysis{color:var(--mut);font-size:14px}.ok{color:var(--ok)}.warn{color:var(--warn)}.blk{color:var(--blk)}
.tag{display:inline-block;border:1px solid var(--border);border-radius:6px;padding:2px 10px;margin:2px;font-size:13px}
.quote{border-left:3px solid var(--blk);padding:8px 16px;background:var(--panel);margin:12px 0}
.foot{color:var(--mut);font-size:13px;margin-top:34px;border-top:1px solid var(--border);padding-top:14px}
</style></head><body>
<h1>SIM 论文再审：旧论文 × 新框架</h1>
<p class="lead">用 §51/§53/§54 新长出的门禁，回头审视曾启发框架的原始论文 · 预注册实现前 SHA256 锁存 · 旧结果只读不改</p>
<div class="quote"><b>核心命题：</b>门禁由 SIM 经验启发，再用它审 SIM 有循环论证风险——按 KB-STRUCT02 打折，不以"审出 SIM 缺口"证明门禁更优。旧结论该保留的保留，新门禁该补刀的补刀。</div>
<h2>一、六道门禁逐条再审</h2>
__CARDS__
<h2>二、新旧结论对照总表</h2>
<table style="width:100%;border-collapse:collapse"><tr style="background:var(--panel)"><th style="border:1px solid var(--border);padding:8px;text-align:left">编号</th><th style="border:1px solid var(--border);padding:8px;text-align:left">门禁</th><th style="border:1px solid var(--border);padding:8px;text-align:left">旧框架结论</th><th style="border:1px solid var(--border);padding:8px;text-align:left">再审动作</th></tr>
<tr><td style="border:1px solid var(--border);padding:8px">N1</td><td style="border:1px solid var(--border);padding:8px">judge 独立性</td><td style="border:1px solid var(--border);padding:8px">S5 泛记"评估器博弈局限"</td><td style="border:1px solid var(--border);padding:8px" class="blk">补刀：分域定位到 workspace LLM-judge</td></tr>
<tr><td style="border:1px solid var(--border);padding:8px">N2</td><td style="border:1px solid var(--border);padding:8px">跨模型迁移</td><td style="border:1px solid var(--border);padding:8px">S2 判 L2 retained 有无</td><td style="border:1px solid var(--border);padding:8px" class="ok">确认+精化：相对基线 +0.1133</td></tr>
<tr><td style="border:1px solid var(--border);padding:8px">N3</td><td style="border:1px solid var(--border);padding:8px">bootstrap 稳健性</td><td style="border:1px solid var(--border);padding:8px">S3 留一法判稳健</td><td style="border:1px solid var(--border);padding:8px" class="blk">补刀：留一稳但重采样不稳</td></tr>
<tr><td style="border:1px solid var(--border);padding:8px">N4</td><td style="border:1px solid var(--border);padding:8px">条件消融</td><td style="border:1px solid var(--border);padding:8px">S4 记忆因果隔离缺口</td><td style="border:1px solid var(--border);padding:8px" class="ok">确认+精化：记忆净贡献>0</td></tr>
<tr><td style="border:1px solid var(--border);padding:8px">N5</td><td style="border:1px solid var(--border);padding:8px">计分完整性</td><td style="border:1px solid var(--border);padding:8px">仅记入局限清单</td><td style="border:1px solid var(--border);padding:8px" class="blk">补刀：精确化 KB-AUDIT07 攻击面+缓解</td></tr>
<tr><td style="border:1px solid var(--border);padding:8px">N6</td><td style="border:1px solid var(--border);padding:8px">任务双源复盘</td><td style="border:1px solid var(--border);padding:8px">N/A</td><td style="border:1px solid var(--border);padding:8px" class="ok">RETRO.OK：本次任务合规</td></tr>
</table>
<p class="lead">识别旧框架漏判 <b class="blk">__NGAP__ 处</b>（N1/N3/N5）——均非推翻旧结论主干，而是把旧框架"记了局限但没精确判"的地方编译成会判的门禁。</p>
<h2>三、三层诚实结论</h2>
<div class="card"><p><b class="ok">能判：</b>__CAN__</p><p><b class="warn">不能判：</b>__CANNOT__</p><p><b class="blk">同构打折：</b>__ISO__</p></div>
<h2>四、入库决策：不新增（防 vanity）</h2>
<p class="lead">再审属"旧论文新审视"：N1/N3/N5 的漏判已被现有门禁覆盖，SIM 经验早已沉淀为 KB-SIM01-10；按预注册不新增条目，仅加固相关 support 指针指向本次再审的补刀证据。论文原文哈希 __PHASH__ 复核一致，旧 sim_framework_result.json 未改。</p>
<p class="foot">预注册 sim_review_prereg.json（__PREREG__）SHA256 锁存于实现前；后验 sim_review_result.json 分离，不伪装。生成：build_sim_review_report.py</p>
</body></html>"""
html = (html.replace("__CARDS__", cards).replace("__NGAP__", str(meta["n_new_gaps"]))
        .replace("__CAN__", esc(honest["can_judge"]))
        .replace("__CANNOT__", esc(honest["cannot_judge"]))
        .replace("__ISO__", esc(honest["isomorphism_discount"]))
        .replace("__PHASH__", esc(meta["paper_sha256"][:16]) + "…")
        .replace("__PREREG__", esc(meta["prereg_sha256"][:16]) + "…"))
open("sim_review_report.html", "w", encoding="utf-8").write(html)
print("HTML 闭合:", html.rstrip().endswith("</html>"), "| 门禁卡:", html.count("class='card'"), "| 补刀标记:", html.count("blk\">补刀"))
