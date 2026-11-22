"""§106 任务目的语义注入受控实验 —— one-shot 盲评引擎.

纪律：不采信设计者自报；import 三个 judge 源码用冻结 gt 盲评；
准入审计用 §102 词边界 + §103 剥离注释；按预注册三情形裁决。
唯一变量=任务目的语义，样本/字段/id/gt 全锁死。
"""
import json, re, hashlib, importlib.util, ast, os

BASE = os.path.dirname(os.path.abspath(__file__))

def load_json(p): return json.load(open(p, encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()

# ---- 冻结输入 ----
blind = load_json(f"{BASE}/designer_P0/samples_blind.json")["samples"]
key = load_json(f"{BASE}/scorer_key.json")
prereg = load_json(f"{BASE}/prereg.json")

# ---- 哈希锁自检 ----
locks_ok = all(sha(f"{BASE}/{f}.json") == open(f"{BASE}/{f}.sha256").read().strip()
               for f in ("prereg", "gate_prereg", "manifest"))
locks_ok = locks_ok and sha(f"{BASE}/scorer_key.json") == open(f"{BASE}/scorer_key.sha256").read().strip()
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
    import inspect
    code = strip_docstrings(src)  # 剥离 docstring+注释，词边界匹配（§102/§103 纪律）
    sig = list(inspect.signature(judge).parameters)
    bad = ["ground_truth", "variant", "scorer_key", "result", "samples", "canary"]
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

# ---- 盲评：三条件用同一批冻结样本，只换目的（judge 源码）----
results = {}
for cell in ("P0", "P1", "P2"):
    judge, src = import_judge(cell)
    adm = admission(src, judge)
    rows = []
    for r in blind:
        nid = r["id"]
        decision, _, _ = judge(r["text_a"], r["text_b"])
        gt = bool(key[nid]["gt"])
        rows.append({
            "nid": nid, "variant": key[nid]["variant"], "gt": gt,
            "decision": bool(decision), "correct": bool(decision) == gt,
        })
    clean = [x for x in rows if x["variant"] == "clean"]
    tamp = [x for x in rows if x["variant"] == "tampered"]
    canary = [x for x in rows if x["variant"] == "canary"]
    core = clean + tamp
    dT = sum(x["decision"] for x in tamp) / len(tamp)  # tampered 上判 True 的比例（正类取向指示）
    results[cell] = {
        "admission": adm, "rows": rows,
        "clean_pass": sum(x["correct"] for x in clean) / len(clean),
        "tamper_catch": sum((not x["decision"]) for x in tamp) / len(tamp),
        "canary_fp": sum((not x["decision"]) for x in canary) / len(canary),
        "core_acc": sum(x["correct"] for x in core) / len(core),
        "dT_tampered_decision_true": dT,
    }

# ---- 主证据：正类取向差 ----
dT1 = results["P1"]["dT_tampered_decision_true"]
dT2 = results["P2"]["dT_tampered_decision_true"]
dT0 = results["P0"]["dT_tampered_decision_true"]
orient_gap = abs(dT1 - dT2)
core1 = results["P1"]["core_acc"]
core0 = results["P0"]["core_acc"]

# ---- 裁决树：先判对照组成立性，再分三情形 ----
all_admit = all(results[c]["admission"]["admission_ok"] for c in ("P0", "P1", "P2"))
P0_floor = core0 <= 0.6 or dT0 >= 0.8  # P0 无目的应落在地板/默认正类
prereq_ok = locks_ok and all_admit

if not prereq_ok:
    verdict = "PURPOSE_INCONCLUSIVE"
    why = "哈希锁失配或准入未全过，对照组不成立，封顶 INCONCLUSIVE。"
elif orient_gap >= 0.8 and core1 >= 0.9 and P0_floor:
    verdict = "PURPOSE_DECISIVE"
    why = ("正类取向随任务目的系统性翻转：P1(忠实性目的)tampered 判 True 比例=%.2f、core=%.2f，"
           "P2(近似重复目的)tampered 判 True 比例=%.2f，取向差=%.2f；P0(无目的)落地板(core=%.2f, dT=%.2f)。"
           "同一文本结构在不同任务目的下取相反正类——§105 根因从观察升级为受控验证。" % (dT1, core1, dT2, orient_gap, core0, dT0))
elif orient_gap < 0.3:
    verdict = "PURPOSE_WEAK"
    why = ("P1/P2 tampered 取向差=%.2f<0.3，任务目的未系统性决定正类取向；"
           "§105 根因停留在事后观察层，未获受控验证。" % orient_gap)
else:
    verdict = "PURPOSE_INCONCLUSIVE"
    why = ("准入成立但模式不符 DECISIVE/WEAK（取向差=%.2f, P1.core=%.2f, P0_floor=%s）——"
           "地板或混杂效应掩盖归因，诚实标注不强行归因。" % (orient_gap, core1, P0_floor))

# ---- 事后分层取证（post-hoc，不参与预注册裁决，不得据此翻案）----
def _subset_dT(cell, want_neg):
    sel = [x["decision"] for x in results[cell]["rows"]
           if x["variant"] == "tampered"
           and (("S02" in key[x["nid"]]["orig_id"] or "S05" in key[x["nid"]]["orig_id"]) == want_neg)]
    return sum(sel) / len(sel) if sel else None

nn_p1, nn_p2 = _subset_dT("P1", False), _subset_dT("P2", False)
ng_p1, ng_p2 = _subset_dT("P1", True), _subset_dT("P2", True)
posthoc_forensic = {
    "status": "post_hoc_forensic_not_in_preregistered_verdict",
    "trigger": "预注册主指标 orient_gap(全集 tampered)=%.3f<0.8，裁决按规则落 PURPOSE_INCONCLUSIVE；"
               "事后发现 tampered 子集异质（否定翻转 vs 非否定限定），分层仅作取证，不得据此翻案。" % orient_gap,
    "non_negation_qualifier": {
        "which": "S01 only / S03 but / S04 three / S06 However（4 条）",
        "P1_dT": nn_p1, "P2_dT": nn_p2, "gap": abs(nn_p1 - nn_p2),
    },
    "negation_flip": {
        "which": "S02 not / S05 never（2 条，删否定词使断言反转）",
        "P1_dT": ng_p1, "P2_dT": ng_p2, "gap": abs(ng_p1 - ng_p2),
    },
    "implication": (
        "非否定限定删除上两目的取向相反(gap=%.2f)，否定翻转上两目的同判负(gap=%.2f)——"
        "P2 把否定翻转判负在其'近似重复'目的下语义一致(反转≠近似)，并非取向摇摆；"
        "全集 dT 把两类平均稀释成 0.67。这与 §100 canary 类型错配、§105 地板效应同为"
        "'指标语义与样本异质性错配'。此发现只解释主指标为何未达门槛，不构成改裁决依据。" % (abs(nn_p1 - nn_p2), abs(ng_p1 - ng_p2))
    ),
    "posthoc_correction": "只在 result 增加本诊断字段并修正 contribution 措辞（原写'获受控验证'过强，"
                          "改为'强提示但未达预注册门槛'）；预注册裁决规则/样本/gt/判据源码/核心评分 one-shot 均不变。",
}

result = {
    "experiment": "§106 任务目的语义注入受控实验（§105 根因因果验证）",
    "locks_ok": locks_ok,
    "all_admissions_pass": all_admit,
    "source_sha256": open(f"{BASE}/downloads/source.sha256").read().strip(),
    "samples_blind_sha256": open(f"{BASE}/samples_blind.sha256").read().strip(),
    "seed": 261122106,
    "per_condition": results,
    "orientation": {
        "dT_P0_no_purpose": dT0, "dT_P1_faithfulness": dT1, "dT_P2_near_dup": dT2,
        "orient_gap_P1_P2": orient_gap, "P0_floor": P0_floor,
    },
    "core": {"P0": core0, "P1": core1, "P2": results["P2"]["core_acc"]},
    "verdict": verdict,
    "verdict_why": why,
    "prereg_rules_snapshot": prereg["verdict_rules"],
    "l3_claimed": False,
    "absolute_claimed": False,
    "honest_boundary": (
        "三设计者仍由本 Agent spawn、同模型家族(KB-STRUCT02)、解释环节本 Agent；"
        "任务目的叙事指定业务正类含义而非判定算法，测的是'同一结构在不同目的下取相反正类'，"
        "不宣称目的叙事能凭空生成判据（P0 地板即证样本结构仍是必要条件）；不宣布 L3/absolute。"
    ),
    "contribution": (
        "§103-§105 消融链证明'抽掉脚手架后设计者随机取错正类'；本轮注入单一任务目的变量，"
        "P1(忠实性目的)从零恢复到 core=1.00、P0(无目的)落 core=0.50——任务目的决定正类取向获强提示，"
        "但预注册主指标 orient_gap=0.67<0.8 未达门槛，裁决诚实落 INCONCLUSIVE，不宣称已受控验证。"
    ),
    "post_hoc_forensic": posthoc_forensic,
}
json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("locks_ok =", locks_ok, " all_admissions =", all_admit)
for c in ("P0", "P1", "P2"):
    r = results[c]
    print(f"{c}: adm={r['admission']['admission_ok']} clean={r['clean_pass']:.2f} "
          f"tamper={r['tamper_catch']:.2f} canary_fp={r['canary_fp']:.2f} "
          f"core={r['core_acc']:.2f} dT={r['dT_tampered_decision_true']:.2f}")
print("orient_gap(P1,P2) =", round(orient_gap, 3), " P0_floor =", P0_floor)
print("VERDICT:", verdict)
print("-", why)
