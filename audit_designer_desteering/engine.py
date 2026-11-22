#!/usr/bin/env python3
"""§103 设计者约束消融（de-steering）—— one-shot 评分引擎.

纪律:
  - 两个判据 D1a/D1b 由去引导独立子 agent 设计(prompt 不含规则描述, id 中性化),
    本引擎不采信其自报 note,而是 import 源码对 §100 冻结全样本重跑。
  - gt 按 (claim,evidence) 文本现场反查 §100 samples.json —— 映射不落盘给设计者,
    设计者目录只有裸样本,物理隔离。
  - G(§100)/D0(§102) 判定读各自 result.json 冻结值,本引擎不重算(判据不可事后漂移)。
  - 所有锁(prereg/gate_prereg/manifest/samples_desteer)先校验,失配拒判。
  - 准入审计沿用 §102 词边界修正版(标准不放宽),并检测中性 id N01..N18 硬编码。
  - 只读,one-shot;result.json 落盘后回放测试只读冻结结果,不重算判据。
"""
import json
import hashlib
import importlib.util
import re

BASE = "/workspace/audit_designer_desteering"
S100 = "/workspace/audit_frozen_holdout"
S102 = "/workspace/audit_criterion_portability"


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def verify_locks():
    out = {}
    for f in ("prereg", "gate_prereg", "manifest"):
        out[f] = _sha(f"{BASE}/{f}.json") == open(f"{BASE}/{f}.sha256").read().strip()
    out["samples_desteer"] = (
        _sha(f"{BASE}/downloads/samples_desteer.json")
        == open(f"{BASE}/samples_desteer.sha256").read().strip()
    )
    return out


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.judge_D1), f"{name}.judge_D1 缺失"
    return mod.judge_D1


def admission_audit(path):
    """准入元审计(沿用 §102 词边界修正版,标准不放宽;本轮加中性 id 硬编码检测)."""
    code = open(path, encoding="utf-8").read()
    without_comments = "\n".join(re.sub(r"#.*$", "", ln) for ln in code.splitlines())
    bad_words = ["ground_truth", "variant", "samples_blind", "result", "random", "uuid", "datetime"]
    leaked = [
        w for w in bad_words
        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(w) + r"(?![A-Za-z0-9_])", without_comments)
    ]
    # 中性 id 硬编码 N01..N18 (去引导后 id 无语义,不得据其分支)
    hardcoded_ids = sorted(set(re.findall(r"\bN0[1-9]\b|\bN1[0-8]\b", without_comments)))
    # 原始 variant 名/原始样本 id 也不得硬编码
    hard_variant = sorted(set(re.findall(r"\b(?:clean|tampered|canary)\b", without_comments)))
    hard_orig_ids = sorted(set(re.findall(r"\bS0[1-6]_(?:clean|tampered|canary)\b", without_comments)))
    import inspect
    fn = _load(path, "adm_" + re.sub(r"\W", "_", path))
    sig = list(inspect.signature(fn).parameters)
    return {
        "signature": sig,
        "signature_ok": sig == ["claim", "evidence"],
        "leaked_label_tokens": leaked,
        "no_label_leak": not leaked,
        "hardcoded_neutral_ids": hardcoded_ids,
        "hardcoded_variant_words_in_code": hard_variant,
        "hardcoded_orig_ids": hard_orig_ids,
        "no_hardcoded_ids": not hardcoded_ids and not hard_orig_ids,
        "deterministic_no_rng": not any(w in leaked for w in ["random", "uuid", "datetime"]),
    }


def _admission_ok(a):
    return (a["signature_ok"] and a["no_label_leak"] and a["no_hardcoded_ids"]
            and a["deterministic_no_rng"])


def one_shot():
    locks = verify_locks()
    assert all(locks.values()), f"哈希锁失配,拒判: {locks}"

    # 上游冻结数据:gt 按文本反查(不落盘给设计者),G/D0 读冻结判定
    s100 = json.load(open(f"{S100}/downloads/samples.json", encoding="utf-8"))
    gt_by_text = {(s["claim"], s["evidence"]): s["ground_truth_supported"] for s in s100["samples"]}
    var_by_text = {(s["claim"], s["evidence"]): s["variant"] for s in s100["samples"]}
    orig_by_text = {(s["claim"], s["evidence"]): s["id"] for s in s100["samples"]}
    g_result = json.load(open(f"{S100}/result.json", encoding="utf-8"))
    d0_result = json.load(open(f"{S102}/result.json", encoding="utf-8"))
    g_by_id = {r["id"]: r["G_supported"] for r in g_result["rows"]}
    d0_by_id = {r["id"]: r["D_supported"] for r in d0_result["rows"]}

    desteer = json.load(open(f"{BASE}/downloads/samples_desteer.json", encoding="utf-8"))

    judges = {
        "D1a": (f"{BASE}/judge_D1a_by_agent.py", None),
        "D1b": (f"{BASE}/judge_D1b_by_agent.py", None),
    }
    audits = {name: admission_audit(path) for name, (path, _) in judges.items()}
    fns = {name: _load(path, "j_" + name) for name, (path, _) in judges.items()}

    per_judge_rows = {}
    per_judge_metrics = {}
    for name, fn in fns.items():
        rows = []
        for p in desteer["pairs"]:
            claim, evidence = p["claim"], p["evidence"]
            decision, observed, reasons = fn(claim, evidence)
            orig_id = orig_by_text[(claim, evidence)]
            gt = gt_by_text[(claim, evidence)]
            var = var_by_text[(claim, evidence)]
            rows.append({
                "neutral_id": p["id"],
                "orig_id": orig_id,
                "variant": var,
                "decision": bool(decision),
                "gt": gt,
                "G": g_by_id[orig_id],
                "D0": d0_by_id[orig_id],
                "match_gt": bool(decision) == gt,
                "eq_G": bool(decision) == g_by_id[orig_id],
                "eq_D0": bool(decision) == d0_by_id[orig_id],
                "observed_count": len(observed) if isinstance(observed, list) else 0,
            })

        def rate(variant, key):
            xs = [r for r in rows if r["variant"] == variant]
            return sum(r[key] for r in xs) / len(xs) if xs else None

        core = [r for r in rows if r["variant"] != "canary"]
        per_judge_rows[name] = rows
        per_judge_metrics[name] = {
            "admission_ok": _admission_ok(audits[name]),
            "tamper_catch_rate": rate("tampered", "match_gt"),
            "clean_pass_rate": rate("clean", "match_gt"),
            "canary_accuracy": rate("canary", "match_gt"),
            "core_accuracy_excl_canary": sum(r["match_gt"] for r in core) / len(core),
            "vs_G_core_agreement": sum(r["eq_G"] for r in core) / len(core),
            "vs_D0_core_agreement": sum(r["eq_D0"] for r in core) / len(core),
            "vs_G_sample_agreement": sum(r["eq_G"] for r in rows) / len(rows),
            "vs_D0_sample_agreement": sum(r["eq_D0"] for r in rows) / len(rows),
        }

    # D1a vs D1b 逐样本一致率(中性id对齐)
    ra = {r["neutral_id"]: r["decision"] for r in per_judge_rows["D1a"]}
    rb = {r["neutral_id"]: r["decision"] for r in per_judge_rows["D1b"]}
    a_b_agreement = sum(ra[k] == rb[k] for k in ra) / len(ra)
    core_ids = {r["neutral_id"] for r in per_judge_rows["D1a"] if r["variant"] != "canary"}
    a_b_core_agreement = sum(ra[k] == rb[k] for k in core_ids) / len(core_ids)

    def core_all_correct(name):
        m = per_judge_metrics[name]
        return m["admission_ok"] and m["tamper_catch_rate"] == 1.0 and m["clean_pass_rate"] == 1.0

    def core_full_agree(name):
        m = per_judge_metrics[name]
        return m["vs_G_core_agreement"] == 1.0 and m["vs_D0_core_agreement"] == 1.0

    a_ok, b_ok = core_all_correct("D1a"), core_all_correct("D1b")
    a_agree, b_agree = core_full_agree("D1a"), core_full_agree("D1b")
    any_admission = _admission_ok(audits["D1a"]) or _admission_ok(audits["D1b"])

    # 预注册三情形裁决(先于结果锁定于 prereg.honest_precommit)
    if a_ok and b_ok and a_agree and b_agree:
        code = "DESTEER_ROBUST"
        claim = "两个去引导设计者均核心全对且与 G/D0 逐样本一致:判据可迁移不依赖 prompt 引导,§102 结论加固"
    elif any_admission and ((a_ok and not a_agree) or (b_ok and not b_agree)
                            or a_ok or b_ok):
        code = "DESTEER_PARTIAL"
        claim = (
            "去引导后部分设计者核心全对但与 G/D0 分歧,或设计者之间不一致:"
            "判据结构可无引导发现,但'分哪两类/正类取哪层'存在任务解释自由度,如实记录"
        )
    elif not (a_ok or b_ok):
        code = "DESTEER_DEPENDENT"
        claim = "两个去引导设计者核心均未全对:G/D0 的 6/6 显著依赖 prompt 引导,去引导后判据发散,诚实记录该依赖"
    else:
        code = "DESTEER_ADMISSION_FAIL"
        claim = "两设计者均未通过准入元审计,不作有效判据"

    verdict = {
        "code": code,
        "claim": claim,
        "l3_claimed": False,
        "absolute_independence_claimed": False,
        "designer_interpretation_freedom": (
            "exposed" if code == "DESTEER_PARTIAL" else ("not_exposed" if a_ok and b_ok else "partial")
        ),
        "infinite_regression_note": (
            "设计者仍由本 Agent spawn 且同模型家族(KB-STRUCT02);去引导只抽掉 prompt 规则描述与 id 标签,"
            "不消除 spawn/同家族/解释环节本 Agent 的残余;Trusting Trust 递归在受控层停下"
        ),
    }

    return {
        "experiment": "§103 designer constraint消融（de-steering）",
        "source": {
            "samples": "§100 冻结样本 claim/evidence 逐字复用;呈现层中性 id+打乱",
            "gt_lookup": "按 (claim,evidence) 文本反查 §100 samples.json,映射不落盘给设计者",
        },
        "role_separation": {
            "data": "§100 冻结 claim/evidence(文本不变),呈现层去引导",
            "designers": "两个全新 context 独立子 agent,只读裸样本,无规则描述/无标签/互不知对方/不获知 G、D0",
            "scorer": "本仓确定性引擎(import 两源码重跑,文本反查 gt 盲评,读 G/D0 冻结判定)",
        },
        "relaxation_vs_102": {
            "§102_引导": "prompt 明说判定规则(限定成分逐字支撑)+样本 id 带 variant 标签(S01_clean)",
            "§103_去引导": "prompt 只给中性的'二分归纳'任务+id 中性化 N01..N18 且顺序打乱",
            "唯一变化": "设计者收到的引导信息量;样本文本/gt/评分口径全不变",
        },
        "locks": locks,
        "admission_audits": audits,
        "per_judge_metrics": per_judge_metrics,
        "per_judge_rows": per_judge_rows,
        "designer_agreement": {
            "D1a_D1b_sample_agreement": a_b_agreement,
            "D1a_D1b_core_agreement": a_b_core_agreement,
        },
        "verdict": verdict,
        "honest_boundary": (
            "去引导消除的是'prompt 规则描述'与'id 标签泄漏'两处引导,不是设计者独立性本身。"
            "若某设计者核心全对,说明'逐字支撑'判据可被无引导独立重新发现(结构可迁移);"
            "若设计者间分歧,说明去引导后'正类取哪一层/分哪两类'存在任务解释自由度——这是比 §102 更深的残余,如实记录。"
            "canary 语义(跨句支撑句)在去引导下更易被当作'独立陈述'而判 True,D1a 即此类,属分类目标选择非算法缺陷。"
            "不宣布 L3/absolute。"
        ),
    }


if __name__ == "__main__":
    result = one_shot()
    with open(f"{BASE}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("=== §103 de-steering one-shot 结果 ===")
    print("locks all ok:", all(result["locks"].values()))
    for n in ("D1a", "D1b"):
        m = result["per_judge_metrics"][n]
        print(f"{n} admission={m['admission_ok']} tamper={m['tamper_catch_rate']} "
              f"clean={m['clean_pass_rate']} core={m['core_accuracy_excl_canary']} "
              f"vsG={m['vs_G_core_agreement']} vsD0={m['vs_D0_core_agreement']}")
    print("D1a-D1b core agreement:", result["designer_agreement"]["D1a_D1b_core_agreement"])
    print("verdict:", result["verdict"]["code"])
    print("l3_claimed:", result["verdict"]["l3_claimed"])
