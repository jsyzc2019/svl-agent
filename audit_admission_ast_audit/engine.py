"""§111 确认性验证引擎——冻结 gt 盲评 + AST 控制流级准入（v2）。

与 §110 engine.py 逐字节同口径的盲评/指标/裁决树；唯一差异：
准入从 word-boundary 全源码扫描改为 admission_v2.admit_source（AST 控制流级）。

纪律：
- 不采信异厂自报 note，import judge 源码用冻结 gt 盲评重跑。
- PRIMARY 事前锁定，不事后改用其他子集翻案。
- no judge 文件 → PENDING 占位，绝不伪造裁决。
- l3=false / absolute=false 硬编码在输出。
"""
import json, os, hashlib, importlib.util

BASE = os.path.dirname(os.path.abspath(__file__))
CELLS = ("P0", "P1", "P2")


def load_json(p): return json.load(open(p, encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---- 冻结输入 ----
blind = load_json(f"{BASE}/vendor_P0/samples_blind.json")["samples"]
key = load_json(f"{BASE}/scorer_key.json")
prereg = load_json(f"{BASE}/prereg.json")
from admission_v2 import admit_source

# ---- 哈希锁自检（spawn 前锁死，spawn 后任何改动都 FAIL）----
locks_ok = True
for f in ("prereg.json", "manifest.json", "scorer_key.json", "admission_v2.py"):
    sp = f"{BASE}/{f}.sha256"
    locks_ok = locks_ok and os.path.exists(sp) and sha(f"{BASE}/{f}") == open(sp).read().strip()
for c in CELLS:
    for f in ("samples_blind.json", "purpose.md"):
        p = f"vendor_{c}/{f}"
        locks_ok = locks_ok and os.path.exists(f"{BASE}/{p}.sha256") and sha(f"{BASE}/{p}") == open(f"{BASE}/{p}.sha256").read().strip()
bl_shas = set(sha(f"{BASE}/vendor_{c}/samples_blind.json") for c in CELLS)
locks_ok = locks_ok and len(bl_shas) == 1 and bl_shas.pop() == prereg["what_is_HELD_FIXED"]["samples_blind_sha256"]

# ---- v2 judge 是否存在 ----
judge_files = {c: f"{BASE}/vendor_{c}/judge_vendor.py" for c in CELLS}
missing = [c for c in CELLS if not os.path.exists(judge_files[c])]
if missing:
    out = {"experiment": "§111 准入规则修订确认（待命）", "status": "PRE_REGISTERED_AWAITING_SPAWN",
           "missing_judges": missing, "locks_ok": locks_ok,
           "note": "prereg+v2 规则+对偶测试+冻结输入已锁；待 spawn 异厂 judge 后重跑本引擎。不构成裁决。",
           "l3_claimed": False, "absolute_claimed": False}
    json.dump(out, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("AWAITING_SPAWN: missing judges", missing)
    raise SystemExit(0)


def import_judge(cell):
    fn = judge_files[cell]
    spec = importlib.util.spec_from_file_location(f"judge_v2_{cell}", fn)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.judge, open(fn, encoding="utf-8").read()


# ---- 盲评：三条件同一批冻结样本，只换 judge 源码 ----
results = {}
for cell in CELLS:
    judge, src = import_judge(cell)
    adm = admit_source(src)
    rows = []
    for r in blind:
        nid = r["id"]
        decision, _, _ = judge(r["text_a"], r["text_b"])
        info = key[nid]
        rows.append({"nid": nid, "variant": info["variant"], "deletion_class": info["deletion_class"],
                     "gt": bool(info["gt"]), "decision": bool(decision), "correct": bool(decision) == bool(info["gt"])})
    clean = [x for x in rows if x["variant"] == "clean"]
    tamp = [x for x in rows if x["variant"] == "tampered"]
    canary = [x for x in rows if x["variant"] == "canary"]
    core = clean + tamp
    results[cell] = {"admission": adm, "rows": rows,
                     "clean_pass": sum(x["correct"] for x in clean) / len(clean),
                     "tamper_catch": sum((not x["decision"]) for x in tamp) / len(tamp),
                     "canary_fp": sum((not x["decision"]) for x in canary) / len(canary),
                     "core_acc": sum(x["correct"] for x in core) / len(core),
                     "dT_all_tampered": sum(x["decision"] for x in tamp) / len(tamp)}


def dT_subset(cell, cls):
    sel = [x["decision"] for x in results[cell]["rows"] if x["variant"] == "tampered" and x["deletion_class"] == cls]
    return sum(sel) / len(sel) if sel else None


PRIMARY = abs(dT_subset("P1", "non_negation_qualifier") - dT_subset("P2", "non_negation_qualifier"))
SECONDARY = abs(dT_subset("P1", "negation_flip") - dT_subset("P2", "negation_flip"))
core1 = results["P1"]["core_acc"]
dT0 = results["P0"]["dT_all_tampered"]
core0 = results["P0"]["core_acc"]
P0_floor = core0 <= 0.6 or dT0 >= 0.8
all_admit = all(results[c]["admission"]["admission_ok"] for c in CELLS)
prereq_ok = locks_ok and all_admit

# ---- 裁决树：严格按 prereg 事前锁定 ----
if not prereq_ok:
    verdict = "AST_V2_INCONCLUSIVE"
    why = "哈希锁失配或 AST v2 准入未全过（真控制流标签读取/id 硬编码/随机/IO/签名错），对照组不成立，封顶 INCONCLUSIVE。"
elif PRIMARY >= 0.8 and SECONDARY <= 0.3 and core1 >= 0.9 and P0_floor:
    verdict = "AST_V2_CONFIRMED"
    why = ("AST v2 准入全过且预注册 PRIMARY=%.2f≥0.8 / SECONDARY=%.2f≤0.3 / P1.core=%.2f≥0.9 / P0 地板(core=%.2f,dT=%.2f)——"
           "规则修订（控制流级）后异厂设计者下分层效应复现，设计者厂商独立性一维获受控确认。" % (PRIMARY, SECONDARY, core1, core0, dT0))
elif PRIMARY >= 0.8:
    verdict = "AST_V2_PARTIAL"
    why = "PRIMARY=%.2f≥0.8 主效应复现，但 SECONDARY=%.2f>0.3 或 P1.core=%.2f<0.9 或 P0 非地板——完整分层模式不成立。" % (PRIMARY, SECONDARY, core1)
elif PRIMARY < 0.3:
    verdict = "AST_V2_REFUTED"
    why = "PRIMARY=%.2f<0.3，异厂设计者下取向差不复现——真负面结果，如实记。" % PRIMARY
else:
    verdict = "AST_V2_INCONCLUSIVE"
    why = "PRIMARY=%.2f 落 0.3~0.8 中间带，诚实标注不强行归因。" % PRIMARY

orient_gap_all = abs(results["P1"]["dT_all_tampered"] - results["P2"]["dT_all_tampered"])
callm = f"{BASE}/runs/vendor_call_manifest.json"
result = {
    "experiment": "§111 准入规则粒度修订的确认性验证（AST 控制流级）",
    "status": "EXECUTED",
    "locks_ok": locks_ok,
    "all_admissions_pass": all_admit,
    "admission_rule": "admission_v2 (AST control-flow)",
    "admission_rule_sha256": sha(f"{BASE}/admission_v2.py"),
    "vendor": (load_json(callm).get("vendor", "unknown") if os.path.exists(callm) else "unknown"),
    "samples_blind_sha256": prereg["what_is_HELD_FIXED"]["samples_blind_sha256"],
    "prereg_sha256": sha(f"{BASE}/prereg.json"),
    "verdict": verdict, "why": why,
    "metrics": {"PRIMARY": PRIMARY, "SECONDARY": SECONDARY, "P1_core": core1,
                "P0_core": core0, "P0_dT": dT0, "P0_floor": P0_floor,
                "orient_gap_all_diagnostic_only": orient_gap_all},
    "per_condition": {c: {"admission": results[c]["admission"], "core_acc": results[c]["core_acc"],
                          "clean_pass": results[c]["clean_pass"], "tamper_catch": results[c]["tamper_catch"],
                          "canary_fp": results[c]["canary_fp"], "dT_all_tampered": results[c]["dT_all_tampered"]}
                      for c in CELLS},
    "verdict_rules_snapshot": prereg["verdict_rules"],
    "honest_bound": prereg["hard_bound"],
    "does_not_overturn": prereg["does_not_overturn"],
    "l3_claimed": False, "absolute_claimed": False,
}
json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("VERDICT:", verdict, "| PRIMARY=%.2f SECONDARY=%.2f P1.core=%.2f | admissions=", all_admit, sep="")
