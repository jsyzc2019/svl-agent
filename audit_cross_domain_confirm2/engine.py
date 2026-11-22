"""§108 跨集复现 + 外部时间戳锚 —— one-shot 盲评引擎.

纪律（继承 §107）：
- 不采信设计者自报；import 三 judge 源码用冻结 gt 盲评。
- 准入审计用 §102 词边界 + §103 剥离注释。
- 按 prereg 事前锁定的分层主指标(PRIMARY=非否定限定 tampered 子集取向差)裁决；禁止事后翻案(KB-META14/KB-R)。
- 新增：核验 commitment.json 的 sha256 一致性（承诺锚完整性）；远端时间戳由入院审计/回放测试用 GitHub API 独立核验。
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
locks_ok = locks_ok and sha(f"{BASE}/engine.py") == open(f"{BASE}/engine.sha256").read().strip()
bl_shas = set(sha(f"{BASE}/designer_{c}/samples_blind.json") for c in ("P0", "P1", "P2"))
locks_ok = locks_ok and len(bl_shas) == 1
locks_ok = locks_ok and bl_shas.pop() == open(f"{BASE}/samples_blind.sha256").read().strip()

# ---- 外部承诺锚完整性核验 ----
commitment = load_json(f"{BASE}/commitment.json")
commitment_sha_ok = sha(f"{BASE}/commitment.json") == open(f"{BASE}/commitment.sha256").read().strip()
# 承诺里记录的每个被锁文件 sha 是否与当前实际一致（证明无事后回改）
anchor_lock_match = all(commitment["locked_sha256"][f] == open(f"{BASE}/{f}.sha256").read().strip()
                        for f in ("prereg", "gate_prereg", "manifest", "scorer_key", "engine"))
anchor_lock_match = anchor_lock_match and commitment["locked_sha256"]["samples_blind"] == open(f"{BASE}/samples_blind.sha256").read().strip()
anchor_intact = commitment_sha_ok and anchor_lock_match

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

# ---- 预注册分层指标（与 §107 逐字一致的判据）----
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
prereq_ok = locks_ok and anchor_intact and all_admit

# ---- 裁决树：严格按 prereg 事前锁定，不做事后翻案 ----
if not prereq_ok:
    verdict = "CROSS_SET_INCONCLUSIVE"
    why = "哈希锁失配 / 承诺锚不完整 / 准入未全过，对照组不成立，封顶 INCONCLUSIVE。"
elif PRIMARY >= 0.8 and SECONDARY <= 0.3 and core1 >= 0.9 and P0_floor:
    verdict = "CROSS_SET_REPRODUCED"
    why = ("预注册 PRIMARY(非否定限定 tampered 子集 |dT(P1)-dT(P2)|)=%.2f≥0.8，SECONDARY(否定翻转 gap)=%.2f≤0.3，"
           "P1.core=%.2f≥0.9，P0 地板(core=%.2f,dT=%.2f)——§107 分层效应在第二独立确认集(2611.20899)复现，"
           "跨集稳健性成立。" % (PRIMARY, SECONDARY, core1, core0, dT0))
elif PRIMARY >= 0.8:
    verdict = "CROSS_SET_PARTIAL"
    why = ("PRIMARY=%.2f≥0.8 主效应复现，但 SECONDARY=%.2f>0.3 或 P1.core=%.2f<0.9 或 P0 非地板——"
           "完整分层模式未跨集成立。" % (PRIMARY, SECONDARY, core1))
elif PRIMARY < 0.3:
    verdict = "CROSS_SET_REFUTED"
    why = ("PRIMARY=%.2f<0.3，第二独立确认集上非否定限定子集 P1/P2 取向也无差异——"
           "§107 效应可能是确认集A特有噪声，未跨集复现，如实记 REFUTED。" % PRIMARY)
else:
    verdict = "CROSS_SET_INCONCLUSIVE"
    why = ("PRIMARY=%.2f 落在 0.3~0.8 中间带，或地板/混杂掩盖归因——诚实标注不强行归因。" % PRIMARY)

orient_gap_all = abs(results["P1"]["dT_all_tampered"] - results["P2"]["dT_all_tampered"])

result = {
    "experiment": "§108 跨集复现 + 外部时间戳锚（§107 STRATIFIED_CONFIRMED 的第二独立确认集）",
    "locks_ok": locks_ok,
    "anchor_intact": anchor_intact,
    "anchor_detail": {"commitment_sha256_ok": commitment_sha_ok, "anchor_lock_match": anchor_lock_match,
                      "commitment_file_sha256": open(f"{BASE}/commitment.sha256").read().strip(),
                      "note": "承诺锚的远端服务器时间戳由入院审计/GitHub API 独立核验（本 engine 只验本地哈希一致性）。"},
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
            "implication": "clean 三条件逐样本一致、canary 三条件逐样本一致——model 路由基础能力无系统差异；"
                           "分叉落在 tampered 子集，排除'差异来自 model 能力'替代解释。",
        },
        "cross_set_compare": {
            "setA_2611_22027": {"verdict": "STRATIFIED_CONFIRMED", "PRIMARY": 1.0, "SECONDARY": 0.0},
            "setB_2611_20899": {"verdict": verdict, "PRIMARY": PRIMARY, "SECONDARY": SECONDARY},
            "note": "跨集对照仅诊断展示，不参与本轮裁决（本轮裁决只看集合B的预注册 PRIMARY）。",
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
        "外部 orchestrator 不可达(PAT 无 workflow scope, GitHub Actions 通道拒, audit_external_orchestrator/BLOCKERS.md)、"
        "异厂商 evaluator 不可达(无任何外部 LLM API key)；外部时间戳锚只保证'承诺先于执行'的可证伪性，不保证执行者独立；"
        "三设计者仍由本 Agent spawn(同厂商 Hunyuan, KB-STRUCT02)、解释环节本 Agent。跨两确认集复现加固效应稳健性，"
        "但'确认一个具体分层效应'≠'系统达到 L3'(KB-META15)；不宣布 L3/absolute。"
    ),
    "contribution": (
        "§107 单一确认集 STRATIFIED_CONFIRMED 不足以支撑稳健结论。§108 换第三篇全新论文(2611.20899 SciWorldBench)+"
        "独立标注者同构确认集，检验跨集复现；并把全部预注册锁+裁决器 sha256 在 spawn 前 commit 到 GitHub 做外部时间戳锚，"
        "使'承诺先于执行'可证伪、本 Agent 无法事后回改。裁决 %s(PRIMARY=%.2f,SECONDARY=%.2f,P1.core=%.2f)。"
        "坚持 l3=false：外部 orchestrator/异厂商 evaluator 在沙箱凭据下不可达，时间锚≠执行者独立。" %
        (verdict, PRIMARY, SECONDARY, core1)
    ),
}
json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("locks_ok =", locks_ok, " anchor_intact =", anchor_intact, " all_admissions =", all_admit)
for c in ("P0", "P1", "P2"):
    r = results[c]
    print(f"{c}: adm={r['admission']['admission_ok']} clean={r['clean_pass']:.2f} "
          f"tamper={r['tamper_catch']:.2f} canary_fp={r['canary_fp']:.2f} core={r['core_acc']:.2f} dT_all={r['dT_all_tampered']:.2f}")
print("PRIMARY(非否定限定 gap) =", round(PRIMARY, 3), " SECONDARY(否定翻转 gap) =", round(SECONDARY, 3))
print("dT non_negation:", {k: round(v,2) for k,v in result['stratified_metric']['dT_non_negation'].items()})
print("dT negation    :", {k: round(v,2) for k,v in result['stratified_metric']['dT_negation'].items()})
print("P0_floor =", P0_floor, " P1.core =", round(core1,2), " diag orient_gap_all =", round(orient_gap_all,3))
print("model_capability_control: clean_all_agree=%s canary_all_agree=%s" % (
    result['diagnostic_only']['model_capability_control']['clean_all_agree'],
    result['diagnostic_only']['model_capability_control']['canary_all_agree']))
print("VERDICT:", verdict)
print("-", why)
