"""§107 预注册分层确认性实验 —— one-shot 盲评引擎.

纪律：
- 不采信设计者自报；import 三 judge 源码用冻结 gt 盲评。
- 准入审计用 §102 词边界 + §103 剥离注释。
- 按 prereg 事前锁定的分层主指标(PRIMARY=非否定限定 tampered 子集取向差)裁决；
  禁止事后改用全集/其他子集翻案(KB-META14/KB-R)。
- PRIMARY 是本轮唯一主裁决指标；SECONDARY(否定翻转 gap)验证完整分层模式；全集 orient_gap 仅诊断。
"""
import json, re, hashlib, importlib.util, ast, os, inspect

BASE = os.path.dirname(os.path.abspath(__file__))

def load_json(p): return json.load(open(p, encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

# ---- 冻结输入 ----
blind = load_json(f"{BASE}/designer_P0/samples_blind.json")["samples"]
key = load_json(f"{BASE}/scorer_key.json")
prereg = load_json(f"{BASE}/prereg.json")

# ---- 哈希锁自检 ----
locks_ok = all(sha(f"{BASE}/{f}.json") == open(f"{BASE}/{f}.sha256").read().strip()
               for f in ("prereg", "gate_prereg", "manifest", "scorer_key"))
bl_shas = set(sha(f"{BASE}/designer_{c}/samples_blind.json") for c in ("P0", "P1", "P2"))
locks_ok = locks_ok and len(bl_shas) == 1
locks_ok = locks_ok and bl_shas.pop() == open(f"{BASE}/samples_blind.sha256").read().strip()

# ---- import judge ----
def import_judge(cell):
    fn = f"{BASE}/designer_{cell}/judge_{cell}_by_agent.py"
    spec = importlib.util.spec_from_file_location(f"judge_{cell}", fn)
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

# ---- 盲评：三条件同一批确认集样本，只换目的(judge 源码) ----
results = {}
for cell in ("P0", "P1", "P2"):
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

# ---- 预注册分层指标 ----
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
all_admit = all(results[c]["admission"]["admission_ok"] for c in ("P0", "P1", "P2"))
prereq_ok = locks_ok and all_admit

# ---- 裁决树：严格按 prereg 事前锁定，不做事后翻案 ----
if not prereq_ok:
    verdict = "STRATIFIED_INCONCLUSIVE"
    why = "哈希锁失配或准入未全过，对照组不成立，封顶 INCONCLUSIVE。"
elif PRIMARY >= 0.8 and SECONDARY <= 0.3 and core1 >= 0.9 and P0_floor:
    verdict = "STRATIFIED_CONFIRMED"
    why = ("预注册 PRIMARY(非否定限定 tampered 子集 |dT(P1)-dT(P2)|)=%.2f≥0.8，SECONDARY(否定翻转 gap)=%.2f≤0.3，"
           "P1.core=%.2f≥0.9，P0 地板(core=%.2f,dT=%.2f)——§106 分层假设在独立确认集获确认："
           "非否定限定删除上忠实性目的判负/近似目的判正，否定翻转上两目的同判负(P2语义一致非摇摆)。" %
           (PRIMARY, SECONDARY, core1, core0, dT0))
elif PRIMARY >= 0.8:
    verdict = "STRATIFIED_PARTIAL"
    why = ("PRIMARY=%.2f≥0.8 主效应复现，但 SECONDARY=%.2f>0.3 或 P1.core=%.2f<0.9 或 P0 非地板——"
           "完整分层模式不成立，部分确认。" % (PRIMARY, SECONDARY, core1))
elif PRIMARY < 0.3:
    verdict = "STRATIFIED_REFUTED"
    why = ("PRIMARY=%.2f<0.3，非否定限定子集上 P1/P2 取向也无差异——§106 post-hoc 分层是发现集噪声，"
           "独立确认集不支持，假设被证伪。" % PRIMARY)
else:
    verdict = "STRATIFIED_INCONCLUSIVE"
    why = ("PRIMARY=%.2f 落在 0.3~0.8 中间带，或地板/混杂掩盖归因——诚实标注不强行归因。" % PRIMARY)

# ---- 全集 orient_gap 仅作诊断（不参与裁决，禁止翻案）----
orient_gap_all = abs(results["P1"]["dT_all_tampered"] - results["P2"]["dT_all_tampered"])

result = {
    "experiment": "§107 预注册分层确认性实验（§106 分层假设的独立确认）",
    "locks_ok": locks_ok,
    "all_admissions_pass": all_admit,
    "source_sha256": open(f"{BASE}/downloads/source.sha256").read().strip(),
    "confirmation_set_sha256": open(f"{BASE}/downloads/samples.sha256").read().strip(),
    "samples_blind_sha256": open(f"{BASE}/samples_blind.sha256").read().strip(),
    "prereg_sha256": open(f"{BASE}/prereg.sha256").read().strip(),
    "seed": prereg["design"]["held_fixed"][2],
    "per_condition": results,
    "stratified_metric": {
        "PRIMARY_non_negation_gap": PRIMARY,
        "SECONDARY_negation_gap": SECONDARY,
        "dT_non_negation": {"P0": dT_subset("P0", "non_negation_qualifier"),
                             "P1": dT_subset("P1", "non_negation_qualifier"),
                             "P2": dT_subset("P2", "non_negation_qualifier")},
        "dT_negation": {"P0": dT_subset("P0", "negation_flip"),
                         "P1": dT_subset("P1", "negation_flip"),
                         "P2": dT_subset("P2", "negation_flip")},
    },
    "diagnostic_only": {
        "orient_gap_all_tampered": orient_gap_all,
        "note": "全集 orient_gap 是 §106 稀释主指标(0.67)，本轮仅诊断、禁止用于翻案(KB-META14)。",
        "model_capability_control": {
            "clean_all_agree": all(len({results[c]["rows"][i]["decision"] for c in ("P0", "P1", "P2")}) == 1
                                   for i in range(len(blind)) if key[blind[i]["id"]]["variant"] == "clean"),
            "canary_all_agree": all(len({results[c]["rows"][i]["decision"] for c in ("P0", "P1", "P2")}) == 1
                                    for i in range(len(blind)) if key[blind[i]["id"]]["variant"] == "canary"),
            "implication": "clean 三条件逐样本全判对、canary 全判错——异 model 路由(default/reasoning/lite)基础能力无系统差异；"
                           "唯一分叉在非否定限定 tampered(P1全0/P2全1)，排除'差异来自 model 能力'替代解释，坐实差异来自任务目的语义。",
        },
    },
    "core": {"P0": core0, "P1": core1, "P2": results["P2"]["core_acc"]},
    "P0_floor": P0_floor,
    "verdict": verdict,
    "verdict_why": why,
    "prereg_rules_snapshot": prereg["verdict_rules"],
    "l3_claimed": False,
    "absolute_claimed": False,
    "honest_boundary": (
        "三设计者仍由本 Agent spawn、异 model 路由(default/reasoning/lite)仅降同源度(仍同厂商 Hunyuan, KB-STRUCT02)、"
        "解释环节本 Agent；分层假设源自§106发现集，本轮仅单一独立确认集，无第三集复现；"
        "样本结构仍是必要条件(P0地板即证)；不宣称目的叙事能凭空生成判据；即使 CONFIRMED 也不宣布 L3/absolute。"
    ),
    "contribution": (
        "§106 post-hoc 分层(非否定gap1.0/否定gap0.0)只是发现集取证，不能翻案(KB-META14)。"
        "§107 换独立确认集(全新论文2611.22027+独立标注者,不知假设)+spawn前锁死分层主指标+异model路由，"
        "做确认性检验：PRIMARY(非否定限定取向差)=%.2f、SECONDARY(否定翻转gap)=%.2f、P1.core=%.2f、P0地板=%s"
        "→裁决 %s。这是从'事后取证'到'预注册确认'的方法学升级，但坚持单一确认集不宣布 L3。" %
        (PRIMARY, SECONDARY, core1, P0_floor, verdict)
    ),
}
json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("locks_ok =", locks_ok, " all_admissions =", all_admit)
for c in ("P0", "P1", "P2"):
    r = results[c]
    print(f"{c}: adm={r['admission']['admission_ok']} clean={r['clean_pass']:.2f} "
          f"tamper={r['tamper_catch']:.2f} canary_fp={r['canary_fp']:.2f} core={r['core_acc']:.2f} dT_all={r['dT_all_tampered']:.2f}")
print("PRIMARY(非否定限定 gap) =", round(PRIMARY, 3), " SECONDARY(否定翻转 gap) =", round(SECONDARY, 3))
print("dT non_negation:", {k: round(v,2) for k,v in result['stratified_metric']['dT_non_negation'].items()})
print("dT negation    :", {k: round(v,2) for k,v in result['stratified_metric']['dT_negation'].items()})
print("P0_floor =", P0_floor, " P1.core =", round(core1,2), " diag orient_gap_all =", round(orient_gap_all,3))
print("VERDICT:", verdict)
print("-", why)
