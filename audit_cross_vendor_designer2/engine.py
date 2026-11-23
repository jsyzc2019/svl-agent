"""§112 真正跨厂商 designer 交叉验证引擎——冻结 gt 盲评 + AST v2 准入（规则逐字节复用 §111）。

与 §111 engine.py 同口径的盲评/指标/准入/裁决树；差异仅在：
- 裁决树前缀 CROSS_VENDOR2_*（§111 是 AST_V2_*）
- 新增跨厂商校验：留痕厂商必须是 Liquid AI、且不得是 nvidia/hunyuan（否则本轮不成立）
- 结果写入 does_not_overturn 同时覆盖 §110/§111

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
for f, lk in (("prereg.json", "prereg.sha256"), ("manifest.json", "manifest.sha256"),
              ("scorer_key.json", "scorer_key.json.sha256"), ("admission_v2.py", "admission_v2.py.sha256")):
    sp = f"{BASE}/{lk}"
    locks_ok = locks_ok and os.path.exists(sp) and sha(f"{BASE}/{f}") == open(sp).read().strip()
for c in CELLS:
    for f in ("samples_blind.json", "purpose.md"):
        p = f"vendor_{c}/{f}"
        locks_ok = locks_ok and os.path.exists(f"{BASE}/{p}.sha256") and sha(f"{BASE}/{p}") == open(f"{BASE}/{p}.sha256").read().strip()
bl_shas = set(sha(f"{BASE}/vendor_{c}/samples_blind.json") for c in CELLS)
locks_ok = locks_ok and len(bl_shas) == 1 and bl_shas.pop() == prereg["what_is_HELD_FIXED"]["samples_blind_sha256"]
# 规则必须与 §111 逐字节一致（跨厂商实验的前提：规则不变，唯一变量=厂商）
locks_ok = locks_ok and sha(f"{BASE}/admission_v2.py") == prereg["locked_files_sha256"]["admission_v2.py"]
# 跨厂商校验：留痕厂商必须是 Liquid AI、不得是 nvidia/hunyuan
callm_path = f"{BASE}/runs/vendor_call_manifest.json"
vendor_ok = False
if os.path.exists(callm_path):
    callm = load_json(callm_path)
    vstr = (callm.get("vendor", "") + " " + callm.get("model", "")).lower()
    vendor_ok = "liquid" in vstr and "nvidia" not in vstr and "hunyuan" not in vstr and "混元" not in vstr

# ---- v2 judge 是否存在 ----
judge_files = {c: f"{BASE}/vendor_{c}/judge_vendor.py" for c in CELLS}
missing = [c for c in CELLS if not os.path.exists(judge_files[c])]
if missing:
    out = {"experiment": "§112 真正跨厂商 designer 交叉验证（待命）", "status": "PRE_REGISTERED_AWAITING_SPAWN",
           "missing_judges": missing, "locks_ok": locks_ok,
           "note": "prereg+复用 AST v2 规则+冻结输入已锁；待 spawn Liquid AI judge 后重跑本引擎。不构成裁决。",
           "l3_claimed": False, "absolute_claimed": False}
    json.dump(out, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("AWAITING_SPAWN: missing judges", missing)
    raise SystemExit(0)


def import_judge(cell):
    fn = judge_files[cell]
    spec = importlib.util.spec_from_file_location(f"judge_cv2_{cell}", fn)
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
prereq_ok = locks_ok and vendor_ok and all_admit

# ---- 裁决树：严格按 prereg 事前锁定 ----
if not prereq_ok:
    why_parts = []
    if not locks_ok: why_parts.append("哈希锁失配")
    if not vendor_ok: why_parts.append("留痕厂商非 Liquid AI 或混入 nvidia/hunyuan（跨厂商前提不成立）")
    if not all_admit: why_parts.append("AST v2 准入未全过")
    verdict = "CROSS_VENDOR2_INCONCLUSIVE"
    why = "；".join(why_parts) + "——对照组不成立，封顶 INCONCLUSIVE。"
elif PRIMARY >= 0.8 and SECONDARY <= 0.3 and core1 >= 0.9 and P0_floor:
    verdict = "CROSS_VENDOR2_CONFIRMED"
    why = ("AST v2 准入全过、留痕确认真正跨厂商（Liquid AI 非 NVIDIA/Hunyuan），且 PRIMARY=%.2f≥0.8 / "
           "SECONDARY=%.2f≤0.3 / P1.core=%.2f≥0.9 / P0 地板(core=%.2f,dT=%.2f)——"
           "设计者独立性首次获跨厂商受控确认（仍非 L3）。" % (PRIMARY, SECONDARY, core1, core0, dT0))
elif PRIMARY >= 0.8:
    verdict = "CROSS_VENDOR2_PARTIAL"
    _fails = []
    if SECONDARY > 0.3: _fails.append("SECONDARY=%.2f>0.3" % SECONDARY)
    if core1 < 0.9: _fails.append("P1.core=%.2f<0.9" % core1)
    if not P0_floor: _fails.append("P0 非地板(core=%.2f,dT=%.2f)" % (core0, dT0))
    why = "PRIMARY=%.2f≥0.8 主效应跨厂商复现，但 %s——完整分层模式不成立。" % (PRIMARY, "、".join(_fails))
elif PRIMARY < 0.3:
    verdict = "CROSS_VENDOR2_REFUTED"
    why = "PRIMARY=%.2f<0.3，真正跨厂商下取向差不复现——真负面结果，如实记。" % PRIMARY
else:
    verdict = "CROSS_VENDOR2_INCONCLUSIVE"
    why = "PRIMARY=%.2f 落 0.3~0.8 中间带，诚实标注不强行归因。" % PRIMARY

orient_gap_all = abs(results["P1"]["dT_all_tampered"] - results["P2"]["dT_all_tampered"])
result = {
    "experiment": "§112 真正跨厂商 designer 交叉验证（Liquid AI）",
    "status": "EXECUTED",
    "locks_ok": locks_ok,
    "vendor_cross_vendor_ok": vendor_ok,
    "all_admissions_pass": all_admit,
    "admission_rule": "admission_v2 (AST control-flow, byte-identical to §111)",
    "admission_rule_sha256": sha(f"{BASE}/admission_v2.py"),
    "vendor": (load_json(callm_path).get("vendor", "unknown") if os.path.exists(callm_path) else "unknown"),
    "model": (load_json(callm_path).get("model", "unknown") if os.path.exists(callm_path) else "unknown"),
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
print("VERDICT: %s | PRIMARY=%.2f SECONDARY=%.2f P1.core=%.2f | admissions=%s | cross_vendor=%s" %
      (verdict, PRIMARY, SECONDARY, core1, all_admit, vendor_ok))
