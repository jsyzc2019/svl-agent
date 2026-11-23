"""§114 解释者独立性 —— 异厂解释者调用器。

唯一变量 = 解释者（本 Agent -> 异厂 LLM）。把"从指标数字到裁决档位"的解释环节外移，
检验四轮裁决规则语义（去前缀中性化后）能否被一个干净 context 的异厂解释者一致复现。

纪律：
- API key 仅从环境变量 INTERPRETER_API_KEY 读，绝不写盘/入仓/入日志。
- 每个 case 发一次全新无历史 chat completion（天然干净 context）。
- prompt 只含 cases_blind.json 的中性规则 + 匿名指标(id, PRIMARY, SECONDARY, P1_core, P0_core, P0_dT, admission_ok)。
  **绝不读 gt_private.json，prompt 不含来源轮次/历史裁决**。
- 只接受四档之一 {FULL/PARTIAL/REFUTED/INCONCLUSIVE} 的明确输出；无法解析记 failed。
- 429 指数退避；失败不伪造，engine 按预注册失败分支封顶 INCONCLUSIVE。

用法：
  INTERPRETER_API_KEY=... INTERPRETER_BASE=https://openrouter.ai/api/v1 \
  INTERPRETER_MODEL=... INTERPRETER_NAME=... python3 call_interpreter.py
"""
import json, os, re, hashlib, datetime, time, urllib.request, urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))

API_KEY = os.environ.get("INTERPRETER_API_KEY", "")
API_BASE = os.environ.get("INTERPRETER_BASE", "").rstrip("/")
MODEL = os.environ.get("INTERPRETER_MODEL", "")
VENDOR_NAME = os.environ.get("INTERPRETER_NAME", "unknown-interpreter")

SYSTEM = (
    "You are a strict verdict classifier. You are given a neutral decision rule and several anonymous metric records. "
    "For EACH record, apply the rule mechanically and output exactly one tier label from "
    "{FULL, PARTIAL, REFUTED, INCONCLUSIVE}. Do not infer any external context, do not name sources. "
    "Output ONLY a JSON object mapping each case id to its tier label, e.g. {\"case_1\":\"FULL\", ...}. "
    "No prose outside the JSON."
)

VALID = ("FULL", "PARTIAL", "REFUTED", "INCONCLUSIVE")


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def build_prompt():
    # 物理隔离：只读 cases_blind.json，绝不读 gt_private.json
    cb = json.load(open(f"{BASE}/cases_blind.json", encoding="utf-8"))
    rules = cb["rules_neutral"]
    cases = [{"id": c["id"], "PRIMARY": c["PRIMARY"], "SECONDARY": c["SECONDARY"],
              "P1_core": c["P1_core"], "P0_core": c["P0_core"], "P0_dT": c["P0_dT"],
              "admission_ok": c["admission_ok"]} for c in cb["cases"]]
    user = ("DECISION RULE (neutralized):\n" + "\n".join(rules) + "\n\n"
            "ANONYMOUS METRIC RECORDS:\n" + json.dumps(cases, ensure_ascii=False, indent=1) + "\n\n"
            "Apply the rule to each record and output ONLY the JSON id->tier mapping.")
    return SYSTEM, user, [c["id"] for c in cases]


def parse_tiers(text, reasoning, ids):
    """从 content（或 reasoning 回退）解析 id->tier；宽松匹配 JSON 与逐行两种格式。"""
    for blob in (text, reasoning):
        if not blob:
            continue
        # 优先 JSON 对象
        for m in re.findall(r"\{[^{}]*\}", blob, re.S):
            try:
                obj = json.loads(m)
                if isinstance(obj, dict) and all(str(i) in obj for i in ids):
                    return {i: str(obj[str(i)]).strip().upper() for i in ids}, "json"
            except Exception:
                pass
        # 回退：逐行 "case_N: TIER"
        got = {}
        for i in ids:
            mm = re.search(re.escape(i) + r"\s*[:=]?\s*(" + "|".join(VALID) + r")\b", blob, re.I)
            if mm:
                got[i] = mm.group(1).upper()
        if all(i in got for i in ids):
            return got, "lines"
    return None, None


def call_api(system, user):
    url = API_BASE + "/chat/completions"
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0,
        "max_tokens": 4000,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": "Bearer " + API_KEY, "Content-Type": "application/json",
    }, method="POST")
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(10 * (attempt + 1))
                continue
            raise
    ch = body["choices"][0]
    msg = ch["message"]
    content = msg.get("content") or ""
    reasoning = msg.get("reasoning") or ""
    meta = {"model": body.get("model", MODEL), "usage": body.get("usage"),
            "finish_reason": ch.get("finish_reason"),
            "content_len": len(content), "reasoning_len": len(reasoning)}
    return content, reasoning, meta


def main():
    if not (API_KEY and API_BASE and MODEL):
        print("ERROR: 需设置 INTERPRETER_API_KEY / INTERPRETER_BASE / INTERPRETER_MODEL")
        return 2
    system, user, ids = build_prompt()
    manifest = {"experiment": "§114 异厂解释者调用留痕（唯一变量=解释者）", "vendor": VENDOR_NAME,
                "model": MODEL, "api_base": API_BASE,
                "system_sha256": sha(system), "user_prompt_sha256": sha(user),
                "cases_blind_sha256": sha(open(f"{BASE}/cases_blind.json", encoding="utf-8").read()),
                "gt_private_in_prompt": False, "calls": []}
    content = reasoning = ""
    meta = {}
    try:
        content, reasoning, meta = call_api(system, user)
        tiers, src = parse_tiers(content, reasoning, ids)
        rec = {"finish_reason": meta.get("finish_reason"), "usage": meta.get("usage"),
               "content_len": meta.get("content_len"), "reasoning_len": meta.get("reasoning_len"),
               "parse_source": src, "model_resp_model": meta.get("model")}
        if tiers is None:
            rec["status"] = "failed_unparseable"
            print("FAILED: 无法解析出全部 case 的档位标签")
        else:
            invalid = {k: v for k, v in tiers.items() if v not in VALID}
            if invalid:
                rec["status"] = "failed_invalid_tier"
                rec["invalid"] = invalid
                print("FAILED: 非法档位", invalid)
            else:
                rec["status"] = "ok"
                rec["tiers"] = tiers
                print("OK tiers =", json.dumps(tiers, ensure_ascii=False, sort_keys=True))
        manifest["calls"].append(rec)
    except Exception as e:
        manifest["calls"].append({"status": "failed_error", "error": type(e).__name__ + ": " + str(e)[:200]})
        print("ERROR:", type(e).__name__, str(e)[:200])
    manifest["called_at_utc"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    # 留痕不含 key、不含私有 gt、不含 prompt 全文（只存哈希）
    open(f"{BASE}/runs/interpreter_call_manifest.json", "w", encoding="utf-8").write(
        json.dumps(manifest, ensure_ascii=False, indent=2))
    ok = bool(manifest["calls"]) and manifest["calls"][0].get("status") == "ok"
    print("ALL_OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
