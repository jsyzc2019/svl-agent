"""§110 异厂商 designer —— one-shot 冻结 gt 盲评引擎。

与 §107 engine.py 逐字节同口径：准入审计(词边界+剥离注释) + 冻结 gt 分层指标；
唯一差异：三 judge 来自异厂 API 生成的 vendor_Px/judge_vendor.py，而非本 Agent spawn。

纪律：不采信异厂自报；import 源码用冻结 gt 盲评；PRIMARY 事前锁定不翻案。
无 judge 文件 → 输出 PENDING_API 占位，绝不伪造裁决。
"""
import json, re, hashlib, importlib.util, ast, os, inspect

BASE = os.path.dirname(os.path.abspath(__file__))
CELLS = ("P0", "P1", "P2")


def load_json(p): return json.load(open(p, encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


# ---- 冻结输入 ----
blind = load_json(f"{BASE}/vendor_P0/samples_blind.json")["samples"]
key = load_json(f"{BASE}/scorer_key.json")
prereg = load_json(f"{BASE}/prereg.json")

# ---- 哈希锁自检 ----
locks_ok = True
for f in ("prereg", "manifest", "scorer_key"):
    sp = f"{BASE}/{f}.sha256"
    locks_ok = locks_ok and os.path.exists(sp) and sha(f"{BASE}/{f}.json") == open(sp).read().strip()
bl_shas = set(sha(f"{BASE}/vendor_{c}/samples_blind.json") for c in CELLS)
locks_ok = locks_ok and len(bl_shas) == 1
locks_ok = locks_ok and bl_shas.pop() == prereg["held_fixed_from_107"]["samples_blind_sha256"]

# ---- 异厂 judge 是否存在 ----
judge_files = {c: f"{BASE}/vendor_{c}/judge_vendor.py" for c in CELLS}
missing = [c for c in CELLS if not os.path.exists(judge_files[c])]
if missing:
    out = {
        "experiment": "§110 异厂商 designer 冻结 gt 盲评（待命）",
        "status": "PENDING_API_KEY",
        "missing_judges": missing,
        "locks_ok": locks_ok,
        "note": "异厂尚未生成 judge_vendor.py；本文件为占位，不构成任何裁决。key 到位→call_vendor.py→重跑 engine。",
        "l3_claimed": False, "absolute_claimed": False,
    }
    json.dump(out, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print("PENDING_API_KEY: missing judges", missing)
    raise SystemExit(0)


def import_judge(cell):
    fn = judge_files[cell]
    spec = importlib.util.spec_from_file_location(f"judge_vendor_{cell}", fn)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.judge, open(fn, encoding="utf-8").read()


def strip_docstrings(src):
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body.pop(0)
    return ast.unparse(tree)


def word_hit(code, token):
    return re.search(r"\b" + re.escape(token) + r"\b", code) is not None


def admission(src, judge):
    code = strip_docstrings(src)
    sig = list(inspect.signature(judge).parameters)
    bad = ["ground_truth", "variant", "scorer_key", "result", "samples", "canary",
           "deletion_class", "negation", "orig_id"]
    leaked = [t for t in bad if word_hit(code, t)]
    hard_ids = sorted(set(re.findall(r"\bN0[1-9]\b|\bN1[0-8]\b", code)))
    rng = [t for t in ("random", "uuid", "datetime") if word_hit(code, t)]
    rng += [t for t in ("time.time", "perf_counter") if t in code]
    return {
        "signature": sig, "signature_ok": len(sig) == 2,
        "leaked_label_tokens": leaked, "no_label_leak": not leaked,
        "hardcoded_sample_ids": hard_ids, "no_hardcoded_ids": not hard_ids,
        "rng_tokens": rng, "deterministic_no_rng": not rng,
        "admission_ok": len(sig) == 2 and not leaked and not hard_ids and not rng,
    }


# ---- 盲评：三条件同一批确认集样本，只换 judge 源码（异厂设计）----
results = {}
for cell in CELLS:
    judge, src = import_judge(cell)
    adm = admission(src, judge)
    rows = []
    for r in blind:
        nid = r["id"]
        decision, _, _ = judge(r["text_a"], r["text_b"])
        info = key[nid]
        rows.append({
            "nid": nid, "variant": info["variant"], "deletion_class": info["deletion_class"],
            "gt": bool(info["gt"]), "decision": bool(decision), "correct": bool(decision) == bool(info["gt"]),
        })
    clean = [x for x in rows if x["variant"] == "clean"]
    tamp = [x for x in rows if x["variant"] == "tampered"]
    canary = [x for x in rows if x["variant"] == "canary"]
    core = clean + tamp
    results[cell] = {
        "admission": adm, "rows": rows,
        "clean_pass": sum(x["correct"] for x in clean) / len(clean),
        "tamper_catch": sum((not x["decision"]) for x in tamp) / len(tamp),
        "canary_fp": sum((not x["decision"]) for x in canary) / len(canary),
        "core_acc": sum(x["correct"] for x in core) / len(core),
        "dT_all_tampered": sum(x["decision"] for x in tamp) / len(tamp),
    }


def dT_subset(cell, cls):
    sel = [x["decision"] for x in results[cell]["rows"]
           if x["variant"] == "tampered" and x["deletion_class"] == cls]
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
    verdict = "CROSS_VENDOR_INCONCLUSIVE"
    why = "哈希锁失配或准入未全过（异厂源码含泄漏/随机/id硬编码或签名错），对照组不成立，封顶 INCONCLUSIVE。"
elif PRIMARY >= 0.8 and SECONDARY <= 0.3 and core1 >= 0.9 and P0_floor:
    verdict = "CROSS_VENDOR_CONFIRMED"
    why = ("跨厂商设计者下预注册 PRIMARY=%.2f≥0.8、SECONDARY=%.2f≤0.3、P1.core=%.2f≥0.9、P0 地板(core=%.2f,dT=%.2f)——"
           "任务目的语义翻转判据取向效应在异厂设计者下复现，设计者厂商独立性一维获受控证据。" %
           (PRIMARY, SECONDARY, core1, core0, dT0))
elif PRIMARY >= 0.8:
    verdict = "CROSS_VENDOR_PARTIAL"
    why = "PRIMARY=%.2f≥0.8 主效应复现，但 SECONDARY=%.2f>0.3 或 P1.core=%.2f<0.9 或 P0 非地板——完整分层模式不成立。" % (PRIMARY, SECONDARY, core1)
elif PRIMARY < 0.3:
    verdict = "CROSS_VENDOR_REFUTED"
    why = "PRIMARY=%.2f<0.3，异厂设计者下取向差不复现——§107 效应可能是同厂商设计习惯产物（真负面结果，如实记）。" % PRIMARY
else:
    verdict = "CROSS_VENDOR_INCONCLUSIVE"
    why = "PRIMARY=%.2f 落在 0.3~0.8 中间带，或混杂掩盖归因——诚实标注不强行归因。" % PRIMARY

orient_gap_all = abs(results["P1"]["dT_all_tampered"] - results["P2"]["dT_all_tampered"])

result = {
    "experiment": "§110 异厂商 designer 设计者独立性受控验证",
    "status": "EXECUTED",
    "locks_ok": locks_ok,
    "all_admissions_pass": all_admit,
    "vendor": (json.load(open(f"{BASE}/runs/vendor_call_manifest.json", encoding="utf-8")).get("vendor", "unknown")
               if os.path.exists(f"{BASE}/runs/vendor_call_manifest.json") else "unknown"),
    "samples_blind_sha256": prereg["held_fixed_from_107"]["samples_blind_sha256"],
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
    "honest_boundary": prereg["hard_bound"],
    "l3_claimed": False, "absolute_claimed": False,
}
json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("VERDICT:", verdict, "| PRIMARY=%.2f SECONDARY=%.2f P1.core=%.2f" % (PRIMARY, SECONDARY, core1))
