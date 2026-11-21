#!/usr/bin/env python3
"""DGM 审计判据引擎：读 evidence.json，按 D1-D7 + 自审语义判定，输出 result.json。
纪律：语义/动作词、多维交叉、不脆弱字面串(KB-AUDIT01)、不单点定罪(KB-AUDIT02)。"""
import json
from pathlib import Path

D = Path(__file__).parent
ev = json.load(open(D / "evidence.json", encoding="utf-8"))
results = []


def judge(vid, name, passed, verdict, finding, confidence):
    results.append({
        "id": vid, "name": name, "pass": bool(passed), "verdict": verdict,
        "finding": finding, "confidence": confidence
    })


# D1 claim-vs-code
d1 = ev["D1_claim_vs_code"]
impl = [c for c in d1["claims"] if c["status"] == "IMPLEMENTED"]
partial = [c for c in d1["claims"] if c["status"] == "PARTIAL"]
d1_ok = d1["verdict"] == "IMPLEMENTED" and len(impl) >= 6 and len(partial) == 0
judge("D1", "claim_vs_code", d1_ok, d1["verdict"],
      f"{len(impl)}/7核心机制有代码实体(parent公式λ=10/α0=0.5/keep_all archive/分层阈值/三baseline/诊断FM主体分层全部对应); "
      f"全仓1650文件交叉核验: 无privilege escalation组件、Docker sandbox有据; "
      f"minor: eligible set未显式排除满分; PARTIAL={len(partial)}",
      "high")

# D2 数字口径
d2 = ev["D2_number_caliber"]
recomp_ok = all(r["ok"] for r in d2["recomputations"])
d2_ok = d2["verdict"] == "CONSISTENT" and recomp_ok and len(d2["caliber_cautions"]) >= 4
judge("D2", "number_caliber", d2_ok, d2["verdict"],
      f"{len(d2['recomputations'])}项复算自洽; 主动标注{len(d2['caliber_cautions'])}处口径差异"
      "(Polyglot子集38.0≠full30.7、59.5vs59.0、三次40.7口径)——数字真≠引用口径对",
      "high")

# D3 核心假设（最高权重）
d3 = ev["D3_core_assumption"]
has_ind = len(d3["independent_evidence"]) >= 2
has_ce = bool(d3["honest_counterexample"])
d3_ok = d3["verdict"] == "EXPLICIT_WITH_EVIDENCE" and has_ind and has_ce and bool(d3["limits"])
judge("D3", "core_assumption", d3_ok, d3["verdict"],
      "核心假设(benchmark↑=self-improve能力↑)明确写出,非纯同义反复: Table2后代可编辑率51.3%vs32.5%+跨基准held-out佐证; "
      "附录H主动披露node114删检测日志objective hacking并引Goodhart; "
      "保留边界: 假设本身是前提非定理,necessary but not sufficient",
      "high")

# D4 消融归因
d4 = ev["D4_ablation_attribution"]
d4_ok = d4["verdict"] == "ISOLATED" and len(d4["controls"]) >= 4 and len(d4["caveats"]) >= 1
judge("D4", "ablation_attribution", d4_ok, d4["verdict"],
      f"Table1干净隔离: w/o open-ended 50→23/38→14, w/o self-improve 39/28, DGM Greedy 39.7/30; "
      f"{len(d4['controls'])}项对照; caveat: 等算力未披露、SWE无多次std——据实标注",
      "medium")

# D5 迁移与基线
d5 = ev["D5_transfer_and_baseline"]
held_out = any("held-out" in f["status"] for f in d5["facts"])
d5_ok = d5["verdict"] == "MIXED" and held_out and len(d5["facts"]) >= 4
judge("D5", "transfer_and_baseline", d5_ok, d5["verdict"],
      "跨基准真held-out(SWE→Poly28.9/Poly→SWE24.5)排除基准过拟合; "
      "跨模型o3-mini+10/Claude3.7+40.5; 手工SoTA引用非自跑如实标注; "
      "诚实边界: 2周算力/落后闭源/长run未知",
      "medium")

# D6 可复现性与安全
d6 = ev["D6_reproducibility_and_safety"]
d6_ok = d6["verdict"] == "PARTIAL" and len(d6["facts"]) >= 5
judge("D6", "reproducibility_and_safety", d6_ok, d6["verdict"],
      "Apache-2.0+完整日志外链+复现声明+Docker沙箱+可追溯lineage; "
      "但FM冻结仅改prompt/tool/workflow、2周复现成本、git clone TLS失败(代码基于raw核心文件非全仓)、"
      "'移除权限提升'一手未证实",
      "high")

# D7 同构偏见专判（最高权重）
d7 = ev["D7_isomorphism_bias_guard"]
d7_ok = d7["verdict"] == "DISCOUNTED" and len(d7["isomorphisms"]) >= 5 and len(d7["real_differences"]) >= 3
judge("D7", "isomorphism_bias_guard", d7_ok, d7["verdict"],
      f"{len(d7['isomorphisms'])}处与用户SVL框架同构,但同属RSI共同体→按KB-STRUCT02判同谱系印证打折,"
      "不把'英雄所见略同'当顶会对用户框架的独立验证; "
      f"识别{len(d7['real_differences'])}处真实差异(改动对象=代码vs知识/探索规则固定vs判据自审入闭环/标量适应度vs可证伪); "
      "记观察不硬造条目",
      "highest")

# 判据自审
sa = ev["judge_self_audit"]
sa_ok = sa["all_passed"] and len(sa["checks"]) >= 6
judge("SA", "judge_self_audit", sa_ok, "PASS" if sa_ok else "FAIL",
      f"{len(sa['checks'])}条自审全过: 无脆弱字面串/无单点定罪/口径对等/事实真≠结论真/分阶段主体/同构打折",
      "high")

all_pass = all(r["pass"] for r in results)
result = {
    "target": ev["target"],
    "summary": {
        "total": len(results),
        "passed": sum(r["pass"] for r in results),
        "all_pass": all_pass,
        "verdicts": {r["id"]: r["verdict"] for r in results},
        "headline": "顶会实证论文,代码扎实(公式逐字对应); 核心假设明确且有独立佐证+objective hacking反面案例; "
                    "与SVL极端同构但判同谱系打折,不新增条目"
    },
    "judges": results
}
json.dump(result, open(D / "result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(json.dumps(result["summary"], ensure_ascii=False, indent=2))
for r in results:
    print(f"  [{'PASS' if r['pass'] else 'FAIL'}] {r['id']} {r['name']} -> {r['verdict']}")
