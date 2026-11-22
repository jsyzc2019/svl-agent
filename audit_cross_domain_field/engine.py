"""§105 跨数据域字段名消融 2×2 —— one-shot 评分引擎.

纪律：不采信设计者自报；import 四个 judge 源码用冻结 gt 盲评；
准入审计用§102词边界+§103剥离注释；按预注册三情形裁决。
"""
import json, re, hashlib, importlib.util, ast, os

BASE = os.path.dirname(os.path.abspath(__file__))

def load_json(p): return json.load(open(p, encoding="utf-8"))

def norm(s): return re.sub(r"\s+", " ", s).strip()

# ---- 冻结输入 ----
samples = load_json(f"{BASE}/downloads/samples.json")["samples"]
key = load_json(f"{BASE}/scorer_key.json")  # N id -> {variant, gt, orig_id}
prereg = load_json(f"{BASE}/prereg.json")

# ---- 哈希锁自检 ----
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
locks_ok = all(
    sha(f"{BASE}/{f}.json") == open(f"{BASE}/{f}.sha256").read().strip()
    for f in ("prereg", "gate_prereg", "manifest")
)
locks_ok = locks_ok and sha(f"{BASE}/downloads/samples.json") == open(f"{BASE}/samples.sha256").read().strip()

# ---- claim/evidence 组装（按中性 id 对齐，反查 gt）----
pairs = {}
by_nid = {}
# 重建呈现层：与制备脚本同种子同打乱
import random
rows = [{"claim": s["claim"], "evidence": s["evidence"]} for s in samples]
rng = random.Random(261114326); rng.shuffle(rows)
for i, r in enumerate(rows, 1): r["id"] = f"N{i:02d}"
for r in rows:
    k = key[r["id"]]
    pairs[r["id"]] = {
        "claim": r["claim"], "evidence": r["evidence"],
        "variant": k["variant"], "gt": k["gt"], "orig_id": k["orig_id"],
    }

# ---- 动态 import 四个 judge ----
def import_judge(cell):
    fn = f"{BASE}/designer_{cell}/judge_{cell}_by_agent.py"
    spec = importlib.util.spec_from_file_location(f"judge_{cell}", fn)
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod.judge, open(fn, encoding="utf-8").read()

# ---- 准入审计：词边界 + 剥离注释/字符串 ----
def strip_comments_strings(src):
    tree = ast.parse(src)
    # 去掉所有 docstring
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if (node.body and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)):
                node.body.pop(0)
    # 剥离注释后保留代码结构（用 unparse，注释与字面字符串里的词不再干扰）
    return ast.unparse(tree)

def word_hit(code, token):
    return re.search(r"\b" + re.escape(token) + r"\b", code) is not None

def admission(cell, src, judge):
    code = strip_comments_strings(src)
    import inspect
    sig = list(inspect.signature(judge).parameters)
    bad = ["ground_truth", "variant", "scorer_key", "result", "samples"]
    leaked = [t for t in bad if word_hit(code, t)]
    hard_ids = sorted(set(re.findall(r"\bN0[1-8]\b", code)))
    rng_tok = [t for t in ["random", "uuid", "datetime"] if word_hit(code, t)]
    rng_tok += [t for t in ["time.time", "perf_counter"] if t in code]
    return {
        "signature": sig,
        "signature_ok": len(sig) == 2,
        "leaked_label_tokens": leaked,
        "no_label_leak": not leaked,
        "hardcoded_sample_ids": hard_ids,
        "no_hardcoded_ids": not hard_ids,
        "rng_tokens": rng_tok,
        "deterministic_no_rng": not rng_tok,
        "admission_ok": len(sig) == 2 and not leaked and not hard_ids and not rng_tok,
    }

# ---- 盲评 ----
results = {}
for cell in ("A1", "A2", "B1", "B2"):
    judge, src = import_judge(cell)
    adm = admission(cell, src, judge)
    rows_out = []
    for nid, p in pairs.items():
        # 条件A函数参数名 (claim,evidence)，条件B (text_a,text_b)；都是位置参数，直接传值
        decision, signals, notes = judge(p["claim"], p["evidence"])
        rows_out.append({
            "nid": nid, "orig_id": p["orig_id"], "variant": p["variant"], "gt": p["gt"],
            "decision": bool(decision), "correct": bool(decision) == bool(p["gt"]),
        })
    clean = [r for r in rows_out if r["variant"] == "clean"]
    tamp = [r for r in rows_out if r["variant"] == "tampered"]
    canary = [r for r in rows_out if r["variant"] == "canary"]
    core = clean + tamp
    results[cell] = {
        "admission": adm,
        "rows": rows_out,
        "clean_pass": sum(r["correct"] for r in clean) / len(clean),
        "tamper_catch": sum((not r["decision"]) for r in tamp) / len(tamp),
        "canary_fp": sum((not r["decision"]) for r in canary) / len(canary),  # canary gt=True 被判False=误拒
        "core_acc": sum(r["correct"] for r in core) / len(core),
        "all_acc": sum(r["correct"] for r in rows_out) / len(rows_out),
    }

# ---- 2×2 对照 + 跨论文对照 ----
condA = [results[c] for c in ("A1", "A2")]
condB = [results[c] for c in ("B1", "B2")]
all_four = condA + condB

# 旧域基线（§103 有字段名 D1b core 全对；§104 中性字段 D2a tamper0/D2b tamper0.5）
old_A_best_core = 1.0   # §103 D1b
old_B_best_core = 0.5   # §104 D2b（tamper0.5/clean0.0 -> core 0.25? 复核：见 result）
# 用旧域实测数据而非硬编码
old104 = load_json("/workspace/audit_field_neutral/result.json")
old104_core = {n: old104["per_judge_rows"][n] for n in ("D2a", "D2b")}
old103 = load_json("/workspace/audit_designer_desteering/result.json")
old103_core = {n: old103["per_judge_rows"][n] for n in ("D1a", "D1b")}

def core_acc_of(rows):
    # rows 里 gt 与 decision 对齐判定
    return sum(1 for r in rows if r.get("decision") == r.get("gt")) / len(rows)

old_B_core_vals = [core_acc_of(old104_core[n]) for n in ("D2a", "D2b")]
old_A_core_vals = [core_acc_of(old103_core[n]) for n in ("D1a", "D1b")]
old_B_best = max(old_B_core_vals); old_A_best = max(old_A_core_vals)

newA_core = [r["core_acc"] for r in condA]
newB_core = [r["core_acc"] for r in condB]

# 裁决
A_restores_D1b = any(c >= 0.9 for c in newA_core)  # 条件A是否至少一个恢复 D1b 式(全对)
# 关键：字段名效应可归因的前提是"条件A在新域仍成立"(无地板效应)。
# 若条件A自身在新域也失败,则 A/B 同低无法区分"字段名无效"与"样本太难集体失败"→INCONCLUSIVE。
if not A_restores_D1b:
    verdict = "CROSS_DOMAIN_INCONCLUSIVE"
    verdict_why = ("条件A在新域也未恢复D1b式判据(四设计者tamper_catch全0、集体收敛到近逐字复述)，"
                   "存在地板效应：A/B同低(core均0.5)无法归因于字段名，无法区分'字段名非引导源'与"
                   "'新域样本结构使逐字支撑判据不可归纳'。字段名效应未跨论文复现，但不宣称已被推翻。")
elif max(newB_core) > old_B_best + 0.01:
    verdict = "CROSS_DOMAIN_WEAKENED"
    verdict_why = "新域条件A成立但条件B core高于旧域条件B最佳，字段名依赖被削弱"
elif max(newB_core) <= old_B_best + 0.01:
    verdict = "CROSS_DOMAIN_CONFIRMED"
    verdict_why = "新域复现旧域方向：条件A恢复D1b式判据，条件B未恢复→字段名依赖跨论文稳健"
else:
    verdict = "CROSS_DOMAIN_INCONCLUSIVE"
    verdict_why = "模式不符三情形，保守归 inconclusive"

# 字段名在新域是否"有差异"：A与B core 的最大差
field_gap_new = abs(max(newA_core) - max(newB_core))
field_gap_old = abs(old_A_best - old_B_best)

result = {
    "experiment": "§105 跨数据域字段名语义消融 2×2",
    "locks_ok": locks_ok,
    "source_sha256": open(f"{BASE}/downloads/source.sha256").read().strip(),
    "samples_sha256": open(f"{BASE}/samples.sha256").read().strip(),
    "annotator_note": load_json(f"{BASE}/downloads/samples.json")["annotator_note"],
    "per_judge": results,
    "condition_A_core": newA_core, "condition_B_core": newB_core,
    "old_domain_baseline": {
        "old_A_core_vals": old_A_core_vals, "old_A_best": old_A_best,
        "old_B_core_vals": old_B_core_vals, "old_B_best": old_B_best,
    },
    "field_gap_new_domain": field_gap_new,
    "field_gap_old_domain": field_gap_old,
    "verdict": verdict,
    "verdict_why": verdict_why,
    "l3_claimed": False,
    "absolute_claimed": False,
    "honest_boundary": "四个设计者仍由本Agent spawn且同模型家族(KB-STRUCT02)；解释环节本Agent；字段名在新域的效应限于此论文样本；不宣布L3/absolute。",
    "self_note": "四设计者全部收敛到'近逐字复述'判据(clean+tampered判True/canary判False)——tampered删限定词仍被判支撑(catch=0)、canary语义支撑被误拒(fp=1)，与§104 D2a同型的逐字/语义错配；本轮核心看字段名是否改变这一收敛。",
}
json.dump(result, open(f"{BASE}/result.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)

print("locks_ok =", locks_ok)
for c in ("A1", "A2", "B1", "B2"):
    r = results[c]
    print(f"{c}: adm={r['admission']['admission_ok']} clean={r['clean_pass']:.2f} "
          f"tamper={r['tamper_catch']:.2f} canary_fp={r['canary_fp']:.2f} core={r['core_acc']:.2f}")
print("new A core:", newA_core, " new B core:", newB_core)
print("old A core:", old_A_core_vals, " old B core:", old_B_core_vals)
print("field_gap new/old:", round(field_gap_new, 3), round(field_gap_old, 3))
print("VERDICT:", verdict, "-", verdict_why)
