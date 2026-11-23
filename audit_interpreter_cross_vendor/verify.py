"""§115 验证器：哈希锁 + 跨目录逐字节复用证明 + 盲性 + 厂商多样性 + 不翻案 + 失败态不伪造。"""
import json, os, hashlib, sys

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)
S114 = f"{ROOT}/audit_interpreter_independence"
ok = True
log = []


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


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
              ("gen_fixtures.py", "gen_fixtures.py.sha256"), ("call_interpreter.py", "call_interpreter.py.sha256"),
              ("run_all.py", "run_all.py.sha256")):
    check(f"lock:{f}", os.path.exists(f"{BASE}/{lk}") and sha(f"{BASE}/{f}") == open(f"{BASE}/{lk}").read().strip())

# 2. 跨目录逐字节复用 §114（核心：物理证明唯一变量=厂商，不是输入/规则/调用器）
for f in ("cases_blind.json", "gt_private.json", "gen_fixtures.py", "call_interpreter.py"):
    check(f"byte_identical_to_114:{f}", os.path.exists(f"{S114}/{f}") and sha(f"{BASE}/{f}") == sha(f"{S114}/{f}"))

# 3. prereg 锁登记一致（除 SELF）
for f, h in prereg["locked_files_sha256"].items():
    if f != "prereg.json" and h != "GENERATED_AT_SPAWN_LOCK":
        check(f"prereg登记:{f}", h == sha(f"{BASE}/{f}"))

# 4. 盲性物理证明
blind_str = json.dumps(cb, ensure_ascii=False)
for banned in ("STRATIFIED", "CROSS_SET", "AST_V2", "CROSS_VENDOR", "source_round", "historical_verdict", "audit_"):
    check(f"blind无泄漏:{banned}", banned not in blind_str)

# 5. 厂商真正多样性：三家前缀互不相同且都不是 baidu/nvidia/hunyuan
vendors = prereg["selected_vendors"]
prefixes = [v.split("/")[0] for v in vendors]
check("厂商数=3", len(vendors) == 3)
check("厂商前缀互不相同", len(set(prefixes)) == 3)
check("非baidu/nvidia/hunyuan", all(p not in ("baidu", "nvidia", "tencent", "hunyuan") for p in prefixes))

# 6. 不翻案（8 案，含 §114）
check("不翻案8案", len(prereg["does_not_overturn"]) == 8 and "§114 INTERPRETER_CONFIRMED" in prereg["does_not_overturn"])
check("l3=false", prereg["l3_claimed"] is False and prereg["absolute_claimed"] is False)

# 7. 各厂商留痕：gt 未进 prompt；失败态无伪造 tiers
for tag in ("dots", "ling", "liquid"):
    p = f"{BASE}/runs/{tag}/interpreter_call_manifest.json"
    if os.path.exists(p):
        mf = json.load(open(p, encoding="utf-8"))
        check(f"{tag}:gt未进prompt", mf.get("gt_private_in_prompt") is False)
        rec = mf.get("calls", [{}])[0]
        if rec.get("status") != "ok":
            check(f"{tag}:失败态无伪造tiers", "tiers" not in rec)
        else:
            check(f"{tag}:tier均合法", all(v in ("FULL", "PARTIAL", "REFUTED", "INCONCLUSIVE") for v in rec["tiers"].values()))

# 8. result 不翻案 + l3
res_p = f"{BASE}/result.json"
if os.path.exists(res_p):
    res = json.load(open(res_p, encoding="utf-8"))
    check("result不翻案", len(res.get("does_not_overturn", [])) == 8)
    check("result l3=false", res.get("l3_claimed") is False and res.get("absolute_claimed") is False)

for status, name in log:
    print(f"[{status}] {name}")
print(f"\n{sum(1 for s,_ in log if s=='OK')}/{len(log)} checks OK", "ALL_OK" if ok else "FAILED")
sys.exit(0 if ok else 1)
