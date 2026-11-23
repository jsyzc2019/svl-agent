"""§111 准入规则修订验证 - 异厂调用器（调用协议逐字复用 §110）。

纪律：
- API key 仅从环境变量 CROSS_VENDOR_API_KEY 读，绝不写盘/入仓/入日志。
- 三条件各发一次全新无历史 chat completion（天然干净 context）。
- prompt 只含统一 system + purpose.md + 裸样本(id/text_a/text_b)，禁带 gt/variant/deletion_class/历史。
- 只接受返回中的 Python 代码块，落 vendor_Px/judge_vendor.py；同时存 prompt 哈希与调用留痕（不含 key）。
- reasoning 模型 content 可能为空：代码块若在 reasoning 字段（同为异厂干净 context 真实生成），
  则回退提取并在留痕 code_source=reasoning_fallback 标注，绝不伪造。
- 失败/非代码块 → 该条件记 status=failed，不伪造 judge，engine 会封顶 INCONCLUSIVE。

用法：
  CROSS_VENDOR_API_KEY=... CROSS_VENDOR_BASE=https://api.deepseek.com/v1 \
  CROSS_VENDOR_MODEL=deepseek-chat python3 call_vendor.py
"""
import json, os, re, hashlib, datetime, time, urllib.request, urllib.error

BASE = os.path.dirname(os.path.abspath(__file__))
CELLS = ("P0", "P1", "P2")

API_KEY = os.environ.get("CROSS_VENDOR_API_KEY", "")
API_BASE = os.environ.get("CROSS_VENDOR_BASE", "").rstrip("/")
MODEL = os.environ.get("CROSS_VENDOR_MODEL", "")
VENDOR_NAME = os.environ.get("CROSS_VENDOR_NAME", "unknown-vendor")

SYSTEM = (
    "You are a判据设计者. You will be given a task purpose and a batch of text pairs. "
    "Derive a deterministic binary classifier from the DATA AND THE PURPOSE ONLY. "
    "Output ONLY a single Python code block defining: judge(text_a, text_b) -> (decision: bool, signals: list, notes: list). "
    "Constraints: pure string/regex only; no randomness, time, sample ids, hardcoded sample text, or external files. "
    "The function must not reference any ground-truth/variant/deletion label. "
    "Do NOT include any explanatory prose outside the code block."
)


def sha(s):
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def read(p):
    return open(p, encoding="utf-8").read()


def build_prompt(cell):
    purpose = read(f"{BASE}/vendor_{cell}/purpose.md")
    samples = json.loads(read(f"{BASE}/vendor_{cell}/samples_blind.json"))["samples"]
    # 物理隔离：只发 id/text_a/text_b，任何标签字段都不构造
    blind = [{"id": s["id"], "text_a": s["text_a"], "text_b": s["text_b"]} for s in samples]
    user = (
        "TASK PURPOSE:\n" + purpose + "\n\n"
        "TEXT PAIRS (blind, unlabeled):\n" + json.dumps(blind, ensure_ascii=False, indent=1) + "\n\n"
        "Now output ONLY the Python code block for judge(text_a, text_b)."
    )
    return SYSTEM, user


def extract_code(text):
    m = re.findall(r"```(?:python)?\s*(.*?)```", text, re.S)
    if not m:
        # 容忍无围栏但体必须是完整 def judge
        if re.search(r"def\s+judge\s*\(", text):
            return text.strip()
        return None
    return max(m, key=len).strip()


MAX_TOKENS = int(os.environ.get("CROSS_VENDOR_MAX_TOKENS", "16000"))


def call_api(system, user):
    """OpenAI 兼容 chat/completions；返回 (content, reasoning, meta) 或抛异常。

    reasoning 模型 reasoning 很长，max_tokens 必须足够大（默认 16000）才能 finish=stop
    并在 content 给出最终代码块。429 上游限流按指数退避重试。
    """
    url = API_BASE + "/chat/completions"
    payload = json.dumps({
        "model": MODEL,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
        "temperature": 0,
        "max_tokens": MAX_TOKENS,
    }).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": "Bearer " + API_KEY,
        "Content-Type": "application/json",
    }, method="POST")
    body = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=280) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 3:
                time.sleep(15 * (attempt + 1))
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
        print("ERROR: 需设置 CROSS_VENDOR_API_KEY / CROSS_VENDOR_BASE / CROSS_VENDOR_MODEL")
        return 2
    manifest = {"experiment": "§111 异厂 designer 调用留痕（规则修订验证，协议复用 §110）", "vendor": VENDOR_NAME,
                "model": MODEL, "api_base": API_BASE, "calls": {}}
    for cell in CELLS:
        rec = {"cell": cell}
        try:
            system, user = build_prompt(cell)
            rec["system_sha256"] = sha(system)
            rec["user_prompt_sha256"] = sha(user)
            rec["user_prompt_chars"] = len(user)
            content, reasoning, meta = call_api(system, user)
            code = extract_code(content)
            code_source = "content"
            if not code and reasoning:
                # reasoning 字段同为异厂干净 context 真实生成；回退提取并标注来源
                code = extract_code(reasoning)
                code_source = "reasoning_fallback"
            rec["model_resp_model"] = meta["model"]
            rec["usage"] = meta["usage"]
            rec["finish_reason"] = meta.get("finish_reason")
            rec["content_len"] = meta.get("content_len")
            rec["reasoning_len"] = meta.get("reasoning_len")
            rec["code_source"] = code_source
            rec["response_chars"] = len(content)
            if not code:
                rec["status"] = "failed_no_code"
                print(f"[{cell}] FAILED: 无 judge 代码块")
            else:
                # 语法自检：能 import 且有 judge 函数签名
                import ast
                tree = ast.parse(code)
                has_judge = any(isinstance(n, ast.FunctionDef) and n.name == "judge" for n in tree.body)
                if not has_judge:
                    rec["status"] = "failed_no_judge_fn"
                    print(f"[{cell}] FAILED: 代码块无 judge() 定义")
                else:
                    out = f"{BASE}/vendor_{cell}/judge_vendor.py"
                    open(out, "w", encoding="utf-8").write(code + "\n")
                    rec["status"] = "ok"
                    rec["judge_sha256"] = hashlib.sha256((code + "\n").encode()).hexdigest()
                    print(f"[{cell}] OK judge saved ({len(code)} chars) sha={rec['judge_sha256'][:16]}")
        except Exception as e:
            rec["status"] = "failed_error"
            rec["error"] = type(e).__name__ + ": " + str(e)[:200]
            print(f"[{cell}] ERROR: {rec['error']}")
        rec["called_at_utc"] = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest["calls"][cell] = rec
    # 留痕不含 key、不含裸样本全文（只存哈希与长度）
    open(f"{BASE}/runs/vendor_call_manifest.json", "w", encoding="utf-8").write(
        json.dumps(manifest, ensure_ascii=False, indent=2))
    ok = all(manifest["calls"][c]["status"] == "ok" for c in CELLS)
    print("ALL_OK" if ok else "PARTIAL_OR_FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
