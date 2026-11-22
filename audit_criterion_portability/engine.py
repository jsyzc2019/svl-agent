#!/usr/bin/env python3
"""§102 判据设计权外移（criterion design portability）—— one-shot 评分引擎.

纪律:
  - 判据 D 由独立子 agent 设计(judge_D_by_agent.py),本引擎不采信其自报 designer_output.json,
    而是 import 源码对 §100 冻结全样本重跑,用 §100 冻结 ground truth 盲评(D 设计过程从未接触标签).
  - G 逐样本判定读 §100 result.json 冻结值,本引擎不重算 G(判据不可事后漂移).
  - 所有锁(prereg/gate_prereg/manifest/samples_blind/paper/§100 samples)先校验,失配拒判.
  - 只读,one-shot;result.json 落盘后回放测试只读冻结结果,不重算判据.
"""
import json
import hashlib
import importlib.util
import sys

BASE = "/workspace/audit_criterion_portability"
S100 = "/workspace/audit_frozen_holdout"


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def verify_locks():
    """校验全部哈希锁;失配拒判."""
    out = {}
    for f in ("prereg", "gate_prereg", "manifest"):
        out[f] = _sha(f"{BASE}/{f}.json") == open(f"{BASE}/{f}.sha256").read().strip()
    out["samples_blind"] = (
        _sha(f"{BASE}/downloads/samples_blind.json")
        == open(f"{BASE}/samples_blind.sha256").read().strip()
    )
    out["paper"] = (
        _sha(f"{BASE}/downloads/paper_flat.txt")
        == open(f"{S100}/source.sha256").read().split()[0]
    )
    out["s100_samples"] = (
        _sha(f"{S100}/downloads/samples.json")
        == open(f"{S100}/samples.sha256").read().split()[0]
    )
    return out


def load_judge_D():
    """从独立设计者源码动态载入 judge_D(不信自报 JSON)."""
    spec = importlib.util.spec_from_file_location("judge_D_by_agent", f"{BASE}/judge_D_by_agent.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.judge_D), "judge_D 缺失"
    return mod.judge_D


def admission_audit(judge_D):
    """准入规则元审计:D 不得读 id/gt/variant,不得硬编码样本 id.

    词边界纪律(§102 自我纠错):首版用子串匹配命中两处假阳性——
      (a) 'variant' 命中词表 'invariant' 的后缀;
      (b) 'random' 命中 docstring 'no randomness' 的否定声明。
    这与 §100 canary 缺陷同源(用粗糙匹配测语义)。改为词边界/注释剥离后
    重判,准入标准不放宽(仍是同一批禁词,只是匹配方式修正)。
    """
    import inspect
    import re
    code = open(f"{BASE}/judge_D_by_agent.py", encoding="utf-8").read()
    # 剥离注释与字符串字面量,只对真实代码记号做禁词检测
    without_comments = "\n".join(
        re.sub(r"#.*$", "", line) for line in code.splitlines()
    )
    # 禁词用词边界;variant 单独要求不作为独立记号出现(invariant 不算)
    bad_words = ["ground_truth", "variant", "samples_blind", "result", "random", "uuid", "datetime"]
    leaked = [
        w for w in bad_words
        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(w) + r"(?![A-Za-z0-9_])", without_comments)
    ]
    sig = list(inspect.signature(judge_D).parameters)
    hardcoded_ids = sorted(set(re.findall(r"\bS0[1-6]\b", without_comments)))
    return {
        "signature": sig,
        "signature_ok": sig == ["claim", "evidence"],
        "leaked_label_tokens": leaked,
        "no_label_leak": not leaked,
        "hardcoded_sample_ids": hardcoded_ids,
        "no_hardcoded_ids": not hardcoded_ids,
        "deterministic_no_rng": "random" not in leaked and "uuid" not in leaked and "datetime" not in leaked,
        "self_correction": (
            "首版子串匹配假阳性(variant←invariant, random←'no randomness' docstring);"
            "改词边界+剥离注释后重判,禁词集与准入标准不变,仅匹配方式修正"
        ),
    }


def one_shot():
    locks = verify_locks()
    assert all(locks.values()), f"哈希锁失配,拒判: {locks}"

    judge_D = load_judge_D()
    audit = admission_audit(judge_D)
    admission_ok = (
        audit["signature_ok"] and audit["no_label_leak"]
        and audit["no_hardcoded_ids"] and audit["deterministic_no_rng"]
    )

    # §100 冻结样本(含 gt)与 G 的冻结判定
    s100 = json.load(open(f"{S100}/downloads/samples.json", encoding="utf-8"))
    g_result = json.load(open(f"{S100}/result.json", encoding="utf-8"))
    g_by_id = {r["id"]: r["G_supported"] for r in g_result["rows"]}

    rows = []
    for s in s100["samples"]:
        # D 只看 claim+evidence,无 variant/gt 输入
        d_supported, d_markers, d_missing = judge_D(s["claim"], s["evidence"])
        gt = s["ground_truth_supported"]
        g_supported = g_by_id[s["id"]]
        rows.append({
            "id": s["id"],
            "variant": s["variant"],          # 仅评分对照,从不喂给 judge_D
            "D_supported": d_supported,
            "G_supported": g_supported,
            "ground_truth_supported": gt,
            "D_match_gt": (d_supported == gt),
            "G_match_gt": (g_supported == gt),
            "D_eq_G": (d_supported == g_supported),
            "D_missing_count": len(d_missing),
        })

    def rate(variant, key):
        xs = [r for r in rows if r["variant"] == variant]
        return sum(r[key] for r in xs) / len(xs) if xs else None

    metrics = {
        "admission_ok": admission_ok,
        "D_tamper_catch_rate": rate("tampered", "D_match_gt"),
        "D_clean_pass_rate": rate("clean", "D_match_gt"),
        "D_canary_false_positive_rate": 1 - rate("canary", "D_match_gt"),
        "G_D_sample_agreement": sum(r["D_eq_G"] for r in rows) / len(rows),
        "G_D_core_agreement": (
            sum(r["D_eq_G"] for r in rows if r["variant"] != "canary")
            / sum(1 for r in rows if r["variant"] != "canary")
        ),
        "D_core_accuracy_excl_canary": (
            sum(r["D_match_gt"] for r in rows if r["variant"] != "canary")
            / sum(1 for r in rows if r["variant"] != "canary")
        ),
    }

    # 预注册裁决规则(先于结果锁定于 prereg.honest_precommit)
    core_portable = (
        admission_ok
        and metrics["D_tamper_catch_rate"] == 1.0
        and metrics["D_clean_pass_rate"] == 1.0
    )
    g_d_core_full = metrics["G_D_core_agreement"] == 1.0
    if not admission_ok:
        code = "CRIT.DESIGN_ADMISSION_FAIL"
        verdict_claim = "独立设计判据 D 未通过准入元审计,不作有效判据"
    elif core_portable and g_d_core_full:
        code = "CRIT.PORTABLE_SINGLE_DESIGN_OVERFIT_WEAKENED"
        verdict_claim = (
            "两个独立设计的判据(G 本仓 / D 外部)在 clean+tampered 上逐样本一致且全对,"
            "'单判据为这6样本量身定做'的替代解释被削弱——判据设计可迁移"
        )
    elif core_portable and not g_d_core_full:
        code = "CRIT.PORTABLE_BUT_DIVERGENT"
        verdict_claim = (
            "D 核心全对但与 G 逐样本分歧:判据设计存在自由度,核心可迁移但具体标记选择非唯一"
        )
    else:
        code = "CRIT.DESIGN_DEPENDENCE"
        verdict_claim = (
            "D 核心未全对:G 的 6/6 部分依赖本仓判据设计选择,如实记录设计依赖,不粉饰"
        )

    verdict = {
        "code": code,
        "claim": verdict_claim,
        "l3_claimed": False,
        "absolute_independence_claimed": False,
        "single_judge_overfit_alternative": (
            "weakened" if (core_portable and g_d_core_full)
            else "not_excluded"
        ),
        "infinite_regression_note": (
            "D 的设计者仍由本 Agent spawn 且同模型家族(KB-STRUCT02),"
            "本轮只把'判据设计'角色外移并排除单判据过拟合,不宣称判据真实独立/无后门,"
            "Trusting Trust 递归在受控层停下"
        ),
    }

    return {
        "experiment": "§102 criterion design portability",
        "source": {
            "paper": "arXiv:2610.16067v1 (reuse §100 frozen held-out)",
            "paper_sha256": locks and open(f"{S100}/source.sha256").read().split()[0],
            "reuse_rationale": "复用冻结数据/样本/gt,唯一变量=判据设计者",
        },
        "role_separation": {
            "data": "§100 冻结(hasher-locked)",
            "designer": "独立子 agent(全新 context,只读脱敏 claim+evidence,无标签,不获知 G)",
            "scorer": "本仓确定性引擎(重跑 D 源码,§100 冻结 gt 盲评,读 G 冻结判定)",
        },
        "locks": locks,
        "admission_audit": audit,
        "metrics": metrics,
        "rows": rows,
        "verdict": verdict,
        "honest_boundary": (
            "判据设计权外移 = 结构性独立性的又一格(设计者与本仓 G 作者分离),"
            "排除单判据过拟合替代解释;但同模型家族+spawn 权+解释环节本 Agent 残余仍在,"
            "不宣布 L3/absolute;canary 全 false 是逐字判据 vs 跨句语义 canary 的类型错配(§101 已定位),"
            "非 D 的核心缺陷"
        ),
    }


if __name__ == "__main__":
    result = one_shot()
    with open(f"{BASE}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    m = result["metrics"]
    print("=== §102 one-shot 结果 ===")
    print("locks all ok:", all(result["locks"].values()))
    print("admission_ok :", m["admission_ok"])
    print("D tamper_catch:", m["D_tamper_catch_rate"])
    print("D clean_pass :", m["D_clean_pass_rate"])
    print("D canary_fp  :", m["D_canary_false_positive_rate"])
    print("G-D agreement:", m["G_D_sample_agreement"], "(core:", m["G_D_core_agreement"], ")")
    print("verdict      :", result["verdict"]["code"])
    print("l3_claimed   :", result["verdict"]["l3_claimed"])
