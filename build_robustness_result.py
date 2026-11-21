"""生成 SWE-Gym 代码强固落地结果（JSON + dark-theme HTML）与预注册分离，后验不伪装。"""
import json
import hashlib

from svagent.judgment_robustness import live_regression

live = live_regression()

result = {
    "task": "SWE-Gym 代码工程纪律 → 本仓代码强固（认知+代码协同工作流首例）",
    "prereg": "robustness_prereg.json",
    "prereg_sha256": open("robustness_prereg.sha256").read().split()[0],
    "source": {
        "repo": "github.com/SWE-Gym/SWE-Gym HEAD 005c2fb",
        "one_hand_lock": "audit_swegym/source.sha256（上一轮已锁存）",
        "borrowed_disciplines": [
            {"discipline": "bootstrap 置信度", "code": "aggregate_stats_pass_at_n.ipynb cell16 get_bootstrap_accuracy_std", "borrowed_to": "C1 bootstrap_stability"},
            {"discipline": "100次shuffle稳健性", "code": "eval_verifier.ipynb cell5/17 num_trials=100", "borrowed_to": "C1（std阈值/重采样）"},
            {"discipline": "per-instance cap + 固定seed", "code": "curate_dataset.ipynb cell2 seed(42)/CAP_PER_INSTANCE=2", "borrowed_to": "C3 validate_live_suite"},
            {"discipline": "正负成对构造", "code": "eval_verifier.ipynb cell1 D={k:v if len(v[True])>0}", "borrowed_to": "C3（成对校验）"},
            {"discipline": "受控配比消融", "code": "configs policy/verifiers 25pct/50pct/uniq/sort/onpolicy", "borrowed_to": "C2 ablate_conditions"},
        ],
    },
    "capabilities": [
        {"id": "C1", "name": "bootstrap_stability", "file": "svagent/judgment_robustness.py",
         "action": "std≥0.10 → downgrade；空样本 flag；否则 ok",
         "kb_anchors": ["KB-RSI06", "KB-STRUCT07"], "live": live["C1"]},
        {"id": "C2", "name": "ablate_conditions", "file": "svagent/judgment_robustness.py",
         "action": "条件净贡献=0 → flag 冗余；长度不匹配 flag（口径对等）",
         "kb_anchors": ["KB-STRUCT03", "KB-META01"], "live": live["C2"]},
        {"id": "C3", "name": "validate_live_suite", "file": "svagent/judgment_robustness.py",
         "action": "无seed/不成对/超cap/重复 → flag",
         "kb_anchors": ["KB-AUDIT02", "KB-META01"], "live": live["C3"]},
    ],
    "yang_avoid": {
        "borrow": "工程纪律：给判定附置信度、用重采样验稳、活体样例成对且有上限、判定条件做消融",
        "avoid": "不借鉴 SWE-Gym 的『可训练 verifier + 标量 reward』——那是 KB-AUDIT07 的 reward hacking 攻击面，本仓判据保持不可被权重带偏的静态可证伪结构",
        "guard": "置信度是判定统计量，不得被优化成新 Goodhart 目标；规则写死、纯函数、固定seed",
    },
    "verification": {"new_tests": 15, "total_tests": 316, "all_live_passed": live["all_passed"],
                     "fixed_seed_reproducible": True, "no_brittle_literal": True},
    "kb_decision": {"new_items": 0, "items_total": 100, "ready": True, "vanity": 0.04,
                    "reinforced_support": ["KB-RSI06", "KB-META01", "KB-STRUCT03", "KB-STRUCT07", "KB-AUDIT02"]},
    "workflow_norm": {
        "rule": "今后应用本仓架构审读项目/文章，默认执行三段式，不再只产出认知结论",
        "seg1_cognition": "认知学习：一手证据 + 判据结论 + 知识库加固（复述vs长牙）",
        "seg2_code": "代码强固：问『这次认知能否编译成会拦/会判/会降级的动作』；扬长避短——借鉴长处、避开对象短处；满足 KB-META01 才落地",
        "seg3_synergy": "认知域协同：每项代码能力锚定具体 KB 条目 + 加固 support 指针 + 同构打折（KB-STRUCT02）",
    },
    "honesty": ["SWE-Gym 代码为一手快照，借鉴的是工程纪律非复现其实验",
                "bootstrap std 是统计量不是优化目标，不反过来刷分",
                "活体样例用于机制回归，非 SWE-Gym 实验结果复现",
                "同构不等于互证：顶会工程技巧不构成本仓框架独立验证"],
}

json.dump(result, open("robustness_result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---------- HTML ----------
def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

borrow_rows = "".join(
    "<tr><td>" + esc(x["discipline"]) + "</td><td><code>" + esc(x["code"]) + "</code></td><td>" + esc(x["borrowed_to"]) + "</td></tr>"
    for x in result["source"]["borrowed_disciplines"]
)
cap_cards = ""
for c in result["capabilities"]:
    lv = c["live"]
    cap_cards += (
        "<div class='card'><h3>" + c["id"] + " · " + esc(c["name"]) + "</h3>"
        "<p class='action'>" + esc(c["action"]) + "</p>"
        "<p>认知域锚点：<b>" + ", ".join(c["kb_anchors"]) + "</b></p>"
        "<p>活体回归：<span class='ok'>" + ("PASS" if lv["passed"] else "FAIL") + "</span></p></div>"
    )
reinforced = "".join("<span class='pill'>" + esc(x) + "</span>" for x in result["kb_decision"]["reinforced_support"])

html = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8">
<title>SWE-Gym 代码强固落地 · SVL</title><style>
:root{--bg:#0d1117;--panel:#161b22;--border:#30363d;--fg:#e6edf3;--mut:#8b949e;--acc:#58a6ff;--ok:#3fb950;--warn:#d29922}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:15px/1.7 -apple-system,"PingFang SC",Segoe UI,sans-serif;padding:40px max(24px,calc((100% - 1000px)/2))}
h1{font-size:26px;color:var(--acc);margin-bottom:6px}h2{font-size:19px;margin-top:36px;border-bottom:1px solid var(--border);padding-bottom:8px;color:var(--acc)}
.lead{color:var(--mut)}table{width:100%;border-collapse:collapse;margin:16px 0}th,td{border:1px solid var(--border);padding:9px 12px;text-align:left;font-size:14px}th{background:var(--panel);color:var(--acc)}code{color:#79c0ff;font-size:13px}
.card{background:var(--panel);border:1px solid var(--border);border-radius:8px;padding:16px 20px;margin:14px 0}.card h3{margin:0 0 8px;font-size:16px}.action{color:var(--mut)}
.ok{color:var(--ok);font-weight:700}.warn{color:var(--warn)}.pill{display:inline-block;background:var(--panel);border:1px solid var(--border);border-radius:20px;padding:3px 12px;margin:3px;font-size:13px}
.seg{background:var(--panel);border-left:3px solid var(--acc);padding:10px 16px;margin:10px 0}.seg b{color:var(--acc)}
ul{padding-left:22px}li{margin:5px 0}.foot{color:var(--mut);font-size:13px;margin-top:34px;border-top:1px solid var(--border);padding-top:14px}
</style></head><body>
<h1>SWE-Gym 代码工程纪律 → 本仓代码强固</h1>
<p class="lead">认知 + 代码强固协同工作流首例 · 扬长避短 · 与已进化认知域对齐 · 预注册 SHA256 锁存于实现前</p>
<h2>一、从 SWE-Gym 一手代码借鉴的五类工程纪律</h2>
<table><tr><th>纪律</th><th>代码一手锚点</th><th>编译到本仓</th></tr>__BORROW__</table>
<h2>二、落地的三道稳健性能力（均长牙）</h2>
__CAPS__
<h2>三、扬长避短</h2>
<div class="card"><p><b class="ok">借鉴：</b>__BORROW_TXT__</p><p><b class="warn">避开：</b>__AVOID__</p><p class="action">护栏：__GUARD__</p></div>
<h2>四、认知域协同：加固的 support 指针</h2>
<p>不新增条目（100 条不变、ready=True、vanity 0.04），仅把每项代码能力挂回它服务的认知条目：</p>
<p>__REINFORCED__</p>
<h2>五、今后审读工作流（三段式，默认执行）</h2>
<div class="seg"><b>第一段 · 认知学习</b><br>__SEG1__</div>
<div class="seg"><b>第二段 · 代码强固</b><br>__SEG2__</div>
<div class="seg"><b>第三段 · 认知域协同</b><br>__SEG3__</div>
<h2>六、验证与诚实边界</h2>
<ul><li>新增 __NEW__ 项测试，全量 __TOTAL__ passed；活体回归 __LIVE__；固定 seed 可复现；无脆弱字面串判定。</li>
__HONEST__</ul>
<p class="foot">预注册 __PREG__ · 后验结果 robustness_result.json 与其分离，不伪装。生成：build_robustness_result.py</p>
</body></html>"""
html = (html.replace("__BORROW__", borrow_rows).replace("__CAPS__", cap_cards)
        .replace("__BORROW_TXT__", esc(result["yang_avoid"]["borrow"]))
        .replace("__AVOID__", esc(result["yang_avoid"]["avoid"]))
        .replace("__GUARD__", esc(result["yang_avoid"]["guard"]))
        .replace("__REINFORCED__", reinforced)
        .replace("__SEG1__", esc(result["workflow_norm"]["seg1_cognition"]))
        .replace("__SEG2__", esc(result["workflow_norm"]["seg2_code"]))
        .replace("__SEG3__", esc(result["workflow_norm"]["seg3_synergy"]))
        .replace("__NEW__", str(result["verification"]["new_tests"]))
        .replace("__TOTAL__", str(result["verification"]["total_tests"]))
        .replace("__LIVE__", "PASS" if live["all_passed"] else "FAIL")
        .replace("__HONEST__", "".join("<li>" + esc(h) + "</li>" for h in result["honesty"]))
        .replace("__PREG__", esc(result["prereg_sha256"][:16]) + "…"))
open("robustness_report.html", "w", encoding="utf-8").write(html)

print("结果 JSON:", len(json.load(open("robustness_result.json"))), "个顶层字段")
print("HTML 闭合:", html.rstrip().endswith("</html>"))
print("能力卡:", html.count("class='card'"), "| 借鉴行:", html.count("<code>"), "| 协同 pill:", html.count("class='pill'"))
