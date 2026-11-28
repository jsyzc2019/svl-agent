"""verify_verifier.py —— 验证器的只读塌缩探针（B3 / Who Verifies 借鉴）。

问题：Who Verifies the Verifier (arXiv:2610.11464) 证明——去掉锚点守卫后
验证器会塌成 always-pass grader，但下游任务分数看不出塌缩。本仓 P0 修过
verify_external 的一个具体洞，却没有常态化探针检测"判据整体是否塌缩"。

本脚本提供该探针：喂一组已知正负例给判据 judge()，看它是否还在区分。
- 独立只读：不 import 判定链、不写任何文件、不碰权威态/verdict/宪法。
- 结论结构跟随证据：篡改探针或喂塌缩判据，结论必须翻转（负向自咬）。
- 预注册：prereg_borrow_wave2_b3_20261128.json（先于本脚本冻结）。

用法:
  python3 verify_verifier.py                       # 检当前真判据
  python3 verify_verifier.py --self-bite           # 内置负向自咬：构造塌缩判据，必须检出
  python3 verify_verifier.py --criterion <path>    # 检指定判据文件
"""

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CRITERION = os.path.join(
    HERE, "received", "l3_external_audit_v2", "criterion.py")

# 6 条探针：3 正(等价->True) + 2 否定翻转负例 + 1 删尾负例。
# 构造纪律(F09 归因幻觉 + H07 构造瑕疵教训)：每条在冻结预注册前已在真实
# criterion 上预跑验证 6/6 命中；否定负例用"正面句→加否定词"单向构造，
# 避免"原句已含否定再插 not 未翻极性"的 presence-based 陷阱。
PROBES = [
    {"id": "P1", "type": "equiv", "expect": True,
     "a": "The system improves itself across rounds",
     "b": "The system improves itself across rounds"},
    {"id": "P2", "type": "equiv", "expect": True,
     "a": "Training reduced the error rate significantly",
     "b": "Training significantly reduced the error rate"},
    {"id": "P3", "type": "equiv", "expect": True,
     "a": "Despite the delay the deployment succeeded",
     "b": "The deployment succeeded despite the delay"},
    {"id": "N1", "type": "negation", "expect": False,
     "a": "The model generalizes to new tasks",
     "b": "The model does not generalize to new tasks"},
    {"id": "N2", "type": "negation", "expect": False,
     "a": "Results confirm the hypothesis",
     "b": "Results never confirm the hypothesis"},
    {"id": "N3", "type": "tail", "expect": False,
     "a": "The method works on text and on images",
     "b": "The method works on text"},
]


def load_judge(path):
    """从路径加载 judge(text_a, text_b)->(bool,...)；只读导入，不改 sys.path 全局。"""
    spec = importlib.util.spec_from_file_location("_vv_criterion", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not hasattr(mod, "judge"):
        raise ValueError("判据文件无 judge() 函数: " + path)
    return mod.judge


def _truthy(result):
    r = result[0] if isinstance(result, tuple) else result
    return bool(r)


def verify(criterion_path=None, judge_fn=None):
    """对判据跑 6 探针，返回结构化的塌缩诊断。只读。"""
    judge = judge_fn or load_judge(criterion_path or DEFAULT_CRITERION)
    hits = []
    for p in PROBES:
        try:
            got = _truthy(judge(p["a"], p["b"]))
        except Exception as e:  # 判据抛错也算不健康，如实记
            got = None
            hits.append({"id": p["id"], "type": p["type"], "expect": p["expect"],
                         "got": None, "ok": False, "error": repr(e)})
            continue
        hits.append({"id": p["id"], "type": p["type"], "expect": p["expect"],
                     "got": got, "ok": (got == p["expect"])})

    got_values = [h["got"] for h in hits]
    n_ok = sum(1 for h in hits if h["ok"])
    all_true = all(g is True for g in got_values)
    all_false = all(g is False for g in got_values)

    if n_ok == len(PROBES):
        collapse, verdict = "none", "HEALTHY"
    elif all_true:
        collapse, verdict = "always_pass", "COLLAPSED"
    elif all_false:
        collapse, verdict = "always_fail", "COLLAPSED"
    else:
        collapse, verdict = "partial", "DEGRADED"

    return {
        "schema": "verify_verifier_v1",
        "criterion": os.path.basename(criterion_path) if criterion_path else "injected",
        "n_probes": len(PROBES),
        "n_ok": n_ok,
        "positive_ok": sum(1 for h in hits if h["type"] == "equiv" and h["ok"]),
        "negative_ok": sum(1 for h in hits if h["type"] != "equiv" and h["ok"]),
        "collapse": collapse,
        "verdict": verdict,
        "hits": hits,
        "readonly": True,
        "no_verdict_change": True,
    }


def self_bite():
    """负向自咬：构造 three 塌缩/健康判据，验证 verify() 结论随之翻转。"""
    def always_pass(a, b):
        return (True, [], [])

    def always_fail(a, b):
        return (False, ["collapsed"], [])

    r_pass = verify(judge_fn=always_pass)
    r_fail = verify(judge_fn=always_fail)
    # 健康对照必须用真判据：字面相等判据会把 P2/P3 重述句(期望 True)误判，
    # 那是 selftest 构造瑕疵而非探针缺陷(H07 教训的同类陷阱)。
    r_ok = verify(judge_fn=load_judge(DEFAULT_CRITERION))
    checks = {
        "always_pass_detected": r_pass["collapse"] == "always_pass",
        "always_fail_detected": r_fail["collapse"] == "always_fail",
        "healthy_not_false_positive": r_ok["verdict"] == "HEALTHY",
    }
    return {"schema": "self_bite_v1", "checks": checks,
            "all_pass": all(checks.values()),
            "observed": {"always_pass": r_pass["collapse"],
                         "always_fail": r_fail["collapse"],
                         "identity_judge": r_ok["verdict"]}}


def main():
    ap = argparse.ArgumentParser(description="验证器的只读塌缩探针（不接入判定）")
    ap.add_argument("--criterion", default=DEFAULT_CRITERION,
                    help="判据 .py 路径")
    ap.add_argument("--self-bite", action="store_true",
                    help="内置负向自咬：构造塌缩判据，必须检出")
    args = ap.parse_args()

    if args.self_bite:
        r = self_bite()
        print(json.dumps(r, ensure_ascii=False, indent=2))
        print("RESULT:", "SELF_BITE_OK" if r["all_pass"] else "SELF_BITE_FAILED")
        sys.exit(0 if r["all_pass"] else 1)

    r = verify(criterion_path=args.criterion)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    print("RESULT: %s collapse=%s (%d/%d)" %
          (r["verdict"], r["collapse"], r["n_ok"], r["n_probes"]))
    # 只读探针：无论健康与否都不改判定态；健康则 0，异常也 0（如实记录即可）。
    sys.exit(0)


if __name__ == "__main__":
    main()
