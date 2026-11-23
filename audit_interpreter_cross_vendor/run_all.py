"""§115 多厂商解释者编排器——逐字节复用 §114 的 call_interpreter.py，唯一变量=厂商。

- 对 prereg.selected_vendors 每家，设置 INTERPRETER_MODEL/INTERPRETER_NAME 后 subprocess 调用同目录
  call_interpreter.py（该文件与 §114 逐字节一致，verify 会断言），产出 runs/<tag>/interpreter_call_manifest.json。
- API key 仅从环境变量 INTERPRETER_API_KEY 读入并透传给子进程，绝不写盘/入日志/入留痕。
- 429 退避/JSON 解析/reasoning 回退全在 call_interpreter.py（未改一字）。
- 每家一次干净 context；失败不伪造，留痕原样保存。
"""
import json, os, subprocess, sys, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
prereg = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
vendors = prereg["selected_vendors"]
tags = ["dots", "ling", "liquid"]

assert len(vendors) == len(tags) == 3

def main():
    key = os.environ.get("INTERPRETER_API_KEY", "")
    if not key:
        print("ERROR: 需设置 INTERPRETER_API_KEY")
        return 2
    results = {}
    for tag, model in zip(tags, vendors):
        outdir = f"{BASE}/runs/{tag}"
        os.makedirs(outdir, exist_ok=True)
        env = dict(os.environ)
        env["INTERPRETER_API_KEY"] = key
        env["INTERPRETER_MODEL"] = model
        env["INTERPRETER_NAME"] = model.split("/")[0]
        env["INTERPRETER_BASE"] = "https://openrouter.ai/api/v1"
        print(f"\n=== spawn {tag}: {model} ===")
        r = subprocess.run([sys.executable, f"{BASE}/call_interpreter.py"], env=env,
                           cwd=BASE, capture_output=True, text=True, timeout=200)
        print(r.stdout.strip()[-300:])
        if r.returncode not in (0, 1):
            print("SUBPROC ERROR:", r.stderr[-200:])
        # call_interpreter.py 写到 runs/interpreter_call_manifest.json，归档到本厂商目录
        src = f"{BASE}/runs/interpreter_call_manifest.json"
        if os.path.exists(src):
            shutil.move(src, f"{outdir}/interpreter_call_manifest.json")
            mf = json.load(open(f"{outdir}/interpreter_call_manifest.json", encoding="utf-8"))
            rec = mf.get("calls", [{}])[0]
            results[tag] = {"model": model, "status": rec.get("status"),
                            "tiers": rec.get("tiers"), "finish_reason": rec.get("finish_reason")}
        else:
            results[tag] = {"model": model, "status": "no_manifest"}
    # 编排总留痕（不含 key）
    summary = {"experiment": "§115 三厂商解释者编排留痕", "key_in_trace": False,
               "caller_byte_identical_to_114": "call_interpreter.py", "results": results}
    json.dump(summary, open(f"{BASE}/runs/orchestration_summary.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    print("\nSUMMARY:", json.dumps(results, ensure_ascii=False))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
