"""§114 验证器：哈希锁 + 盲性物理证明 + 冻结输入来源 + 不翻案 + 失败态不伪造。"""
import json, os, hashlib, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
ok = True
log = []


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def dsha(d):
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def check(name, cond):
    global ok
    ok = ok and cond
    log.append(("OK" if cond else "FAIL", name))


prereg = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
gt = json.load(open(f"{BASE}/gt_private.json", encoding="utf-8"))
cb = json.load(open(f"{BASE}/cases_blind.json", encoding="utf-8"))

# 1. 哈希锁
for f, lk in (("prereg.json", "prereg.sha256"), ("manifest.json", "manifest.sha256"),
              ("cases_blind.json", "cases_blind.json.sha256"), ("gt_private.json", "gt_private.json.sha256"),
              ("gen_fixtures.py", "gen_fixtures.py.sha256"), ("call_interpreter.py", "call_interpreter.py.sha256")):
    check(f"lock:{f}", os.path.exists(f"{BASE}/{lk}") and sha(f"{BASE}/{f}") == open(f"{BASE}/{lk}").read().strip())

# 2. prereg 锁登记一致（除 SELF）
for f, h in prereg["locked_files_sha256"].items():
    if f != "prereg.json":
        check(f"prereg登记:{f}", h == sha(f"{BASE}/{f}"))

# 3. 盲性物理证明：cases_blind 不含来源轮次/历史裁决字段
blind_str = json.dumps(cb, ensure_ascii=False)
for banned in ("STRATIFIED", "CROSS_SET", "AST_V2", "CROSS_VENDOR", "source_round", "historical_verdict", "audit_"):
    check(f"blind无泄漏:{banned}", banned not in blind_str)

# 4. 私有 gt 与匿名 case id 集合一致、档位合法
blind_ids = sorted(c["id"] for c in cb["cases"])
check("gt/blind id集合一致", sorted(gt["neutral_gt"].keys()) == blind_ids)
check("gt档位合法", all(v in ("CONFIRMED", "PARTIAL", "REFUTED", "INCONCLUSIVE") for v in gt["neutral_gt"].values()))

# 5. 冻结输入来源物理证明：重跑 gen_fixtures 的提取，四轮充分统计量逐字段吻合
SRC = {"A": ("audit_stratified_confirmation/result.json",), "B": ("audit_cross_domain_confirm2/result.json",),
       "C": ("audit_admission_ast_audit/result.json",), "D": ("audit_cross_vendor_designer2/result.json",)}
by_id = {c["id"]: c for c in cb["cases"]}
# 反打乱映射必须能把每个匿名 case 还原到某轮，且数值与该轮 result.json 一致
import random
order = ["A", "B", "C", "D"]
random.Random(cb["seed"]).shuffle(order)
for i, orig in enumerate(order, 1):
    d = json.load(open(f"{ROOT}/{SRC[orig][0]}", encoding="utf-8"))
    sm = d.get("stratified_metric") or {}
    m = d.get("metrics") or {}
    primary = sm.get("PRIMARY_non_negation_gap", m.get("PRIMARY"))
    secondary = sm.get("SECONDARY_negation_gap", m.get("SECONDARY"))
    core = d.get("core", {})
    p1 = core.get("P1") if core else m.get("P1_core")
    p0 = core.get("P0") if core else m.get("P0_core")
    p0dT = sm.get("dT_non_negation", {}).get("P0") if "dT_non_negation" in sm else m.get("P0_dT")
    c = by_id[f"case_{i}"]
    check(f"来源一致:case_{i}<-{orig}",
          c["PRIMARY"] == round(float(primary), 6) and c["SECONDARY"] == round(float(secondary), 6)
          and c["P1_core"] == round(float(p1), 6) and c["P0_core"] == round(float(p0), 6)
          and c["P0_dT"] == round(float(p0dT), 6))

# 6. 不翻案声明完整
check("不翻案7案", len(prereg["does_not_overturn"]) == 7)
check("l3=false", prereg["l3_claimed"] is False and prereg["absolute_claimed"] is False)

# 7. 调用留痕若有：gt 未进 prompt、失败态不伪造
call_p = f"{BASE}/runs/interpreter_call_manifest.json"
if os.path.exists(call_p):
    mf = json.load(open(call_p, encoding="utf-8"))
    check("gt未进prompt", mf.get("gt_private_in_prompt") is False)
    rec = mf.get("calls", [{}])[0]
    if rec.get("status") != "ok":
        check("失败态无伪造tiers", "tiers" not in rec)
    else:
        check("tier均合法", all(v in ("FULL", "PARTIAL", "REFUTED", "INCONCLUSIVE") for v in rec["tiers"].values()))

# 8. result.json 不翻案 + l3 边界（若已执行）
res_p = f"{BASE}/result.json"
if os.path.exists(res_p):
    res = json.load(open(res_p, encoding="utf-8"))
    check("result不翻案", len(res.get("does_not_overturn", [])) == 7)
    check("result l3=false", res.get("l3_claimed") is False and res.get("absolute_claimed") is False)

for status, name in log:
    print(f"[{status}] {name}")
print(f"\n{sum(1 for s,_ in log if s=='OK')}/{len(log)} checks OK", "ALL_OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
