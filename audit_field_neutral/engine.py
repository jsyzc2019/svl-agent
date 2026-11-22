#!/usr/bin/env python3
"""§104 字段名语义消融（semantic field-name ablation）—— one-shot 评分引擎.

纪律:
  - 两个判据 D2a/D2b 由字段名盲设计者设计(judge(text_a,text_b)),本引擎不采信自报 note,
    import 源码重跑。调用口径:text_a=§100 claim 原文, text_b=§100 evidence 原文。
  - gt 按 (text_a,text_b) 文本反查 §100 samples.json —— 映射不落盘给设计者。
  - G(§100)/D0(§102)/D1b(§103) 判定读各自 result.json 冻结值,不重算。
  - 锁先校验失配拒判;准入沿用 §102/§103 词边界版 + 中性 id 硬编码检测。
  - 只读 one-shot;result.json 落盘后回放只读冻结结果,不重算判据。
"""
import json
import hashlib
import importlib.util
import re

BASE = "/workspace/audit_field_neutral"
S100 = "/workspace/audit_frozen_holdout"
S102 = "/workspace/audit_criterion_portability"
S103 = "/workspace/audit_designer_desteering"


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def verify_locks():
    out = {}
    for f in ("prereg", "gate_prereg", "manifest"):
        out[f] = _sha(f"{BASE}/{f}.json") == open(f"{BASE}/{f}.sha256").read().strip()
    out["samples_fieldneutral"] = (
        _sha(f"{BASE}/downloads/samples_fieldneutral.json")
        == open(f"{BASE}/samples_fieldneutral.sha256").read().strip()
    )
    return out


def _load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.judge), f"{name}.judge 缺失"
    return mod.judge


def admission_audit(path):
    """准入元审计(沿用 §102/§103 词边界版,标准不放宽)."""
    import inspect
    code = open(path, encoding="utf-8").read()
    without_comments = "\n".join(re.sub(r"#.*$", "", ln) for ln in code.splitlines())
    bad_words = ["ground_truth", "variant", "samples_blind", "result", "random", "uuid", "datetime"]
    leaked = [
        w for w in bad_words
        if re.search(r"(?<![A-Za-z0-9_])" + re.escape(w) + r"(?![A-Za-z0-9_])", without_comments)
    ]
    hardcoded_ids = sorted(set(re.findall(r"\bN0[1-9]\b|\bN1[0-8]\b", without_comments)))
    hard_orig_ids = sorted(set(re.findall(r"\bS0[1-6]_(?:clean|tampered|canary)\b", without_comments)))
    fn = _load(path, "adm_" + re.sub(r"\W", "_", path))
    sig = list(inspect.signature(fn).parameters)
    return {
        "signature": sig,
        "signature_ok": sig == ["text_a", "text_b"],
        "leaked_label_tokens": leaked,
        "no_label_leak": not leaked,
        "hardcoded_neutral_ids": hardcoded_ids,
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

    s100 = json.load(open(f"{S100}/downloads/samples.json", encoding="utf-8"))
    # 调用口径:text_a=claim, text_b=evidence
    by_text = {(s["claim"], s["evidence"]): s for s in s100["samples"]}
    g_result = json.load(open(f"{S100}/result.json", encoding="utf-8"))
    d0_result = json.load(open(f"{S102}/result.json", encoding="utf-8"))
    d1_result = json.load(open(f"{S103}/result.json", encoding="utf-8"))
    g_by_id = {r["id"]: r["G_supported"] for r in g_result["rows"]}
    d0_by_id = {r["id"]: r["D_supported"] for r in d0_result["rows"]}
    # §103 D1b 按 orig_id 对齐(其 rows 有 orig_id 字段)
    d1b_by_id = {r["orig_id"]: r["decision"] for r in d1_result["per_judge_rows"]["D1b"]}

    neutral = json.load(open(f"{BASE}/downloads/samples_fieldneutral.json", encoding="utf-8"))

    judges = {
        "D2a": f"{BASE}/judge_D2a_by_agent.py",
        "D2b": f"{BASE}/judge_D2b_by_agent.py",
    }
    audits = {n: admission_audit(p) for n, p in judges.items()}
    fns = {n: _load(p, "j_" + n) for n, p in judges.items()}

    per_judge_rows, per_judge_metrics = {}, {}
    for name, fn in fns.items():
        rows = []
        for p in neutral["pairs"]:
            a_text, b_text = p["text_a"], p["text_b"]
            decision, signals, notes = fn(a_text, b_text)
            src = by_text[(a_text, b_text)]
            oid = src["id"]
            gt = src["ground_truth_supported"]
            var = src["variant"]
            rows.append({
                "neutral_id": p["id"], "orig_id": oid, "variant": var,
                "decision": bool(decision), "gt": gt,
                "G": g_by_id[oid], "D0": d0_by_id[oid], "D1b": d1b_by_id[oid],
                "match_gt": bool(decision) == gt,
                "eq_G": bool(decision) == g_by_id[oid],
                "eq_D0": bool(decision) == d0_by_id[oid],
                "eq_D1b": bool(decision) == d1b_by_id[oid],
            })
        def rate(v, k):
            xs = [r for r in rows if r["variant"] == v]
            return sum(r[k] for r in xs) / len(xs) if xs else None
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
            "vs_D1b_core_agreement": sum(r["eq_D1b"] for r in core) / len(core),
            "vs_D1b_sample_agreement": sum(r["eq_D1b"] for r in rows) / len(rows),
        }

    ra = {r["neutral_id"]: r["decision"] for r in per_judge_rows["D2a"]}
    rb = {r["neutral_id"]: r["decision"] for r in per_judge_rows["D2b"]}
    core_ids = {r["neutral_id"] for r in per_judge_rows["D2a"] if r["variant"] != "canary"}
    a_b_core = sum(ra[k] == rb[k] for k in core_ids) / len(core_ids)

    def core_all_correct(n):
        m = per_judge_metrics[n]
        return m["admission_ok"] and m["tamper_catch_rate"] == 1.0 and m["clean_pass_rate"] == 1.0

    def core_full_agree(n):
        m = per_judge_metrics[n]
        return (m["vs_G_core_agreement"] == 1.0 and m["vs_D0_core_agreement"] == 1.0
                and m["vs_D1b_core_agreement"] == 1.0)

    a_ok, b_ok = core_all_correct("D2a"), core_all_correct("D2b")
    a_agree, b_agree = core_full_agree("D2a"), core_full_agree("D2b")
    any_adm = _admission_ok(audits["D2a"]) or _admission_ok(audits["D2b"])

    if a_ok and b_ok and a_agree and b_agree:
        code, claim = "FIELD_NEUTRAL_ROBUST", (
            "两设计者在字段名中性下仍核心全对且与 G/D0/D1b 一致:结构发现不依赖字段名方向语义,§103 结论再加固")
    elif any_adm and (a_ok or b_ok):
        code, claim = "FIELD_NEUTRAL_PARTIAL", (
            "字段名中性下部分设计者核心全对但与上游判据分歧:字段名语义是引导源之一,暴露更深的脚手架依赖,如实记录")
    elif not (a_ok or b_ok):
        code, claim = "FIELD_NEUTRAL_DEPENDENT", (
            "两设计者字段名中性下核心均未全对:G/D0/D1b 的判定显著依赖 claim/evidence 字段名方向语义,诚实记录该依赖,不粉饰")
    else:
        code, claim = "FIELD_NEUTRAL_ADMISSION_FAIL", "两设计者均未通过准入,不作有效判据"

    verdict = {
        "code": code, "claim": claim,
        "l3_claimed": False, "absolute_independence_claimed": False,
        "field_name_semantics_dependency": (
            "exposed" if code in ("FIELD_NEUTRAL_PARTIAL", "FIELD_NEUTRAL_DEPENDENT") else "not_exposed"
        ),
        "infinite_regression_note": (
            "设计者仍由本 Agent spawn 且同模型家族(KB-STRUCT02);文本 value 内固有 'claim' 词为源数据内容不可消除;"
            "本轮只检验字段名方向语义这一个可判据缺口,Trusting Trust 递归在受控层停下"),
    }

    return {
        "experiment": "§104 semantic field-name ablation",
        "source": {
            "samples": "§100 冻结 claim/evidence 逐字复用;字段名中性 text_a/text_b,id/顺序沿用§103打乱",
            "call_convention": "judge(text_a=claim原文, text_b=evidence原文);gt 文本反查,映射不落盘",
        },
        "role_separation": {
            "data": "§100 冻结文本,字段名中性化,呈现层去语义",
            "designers": "两个全新 context 独立子 agent,只读字段名中性裸样本,不获知 G/D0/D1、互不知对方",
            "scorer": "本仓确定性引擎(import 重跑,文本反查 gt 盲评,读 G/D0/D1b 冻结判定)",
        },
        "relaxation_vs_103": {
            "§103_保留": "字段名 claim/evidence 携带方向语义(前者被支撑声明/后者支撑证据)+函数签名 judge(claim,evidence)",
            "§104_消融": "字段名 text_a/text_b 无方向语义+签名 judge(text_a,text_b);文本/id/顺序/gt/评分口径全不变",
            "唯一变化": "字段名方向语义",
            "irreducible_residual": "文本 value 内固有英文词 'claim'(源数据内容),非注入脚手架,不消除",
        },
        "locks": locks,
        "admission_audits": audits,
        "per_judge_metrics": per_judge_metrics,
        "per_judge_rows": per_judge_rows,
        "designer_agreement": {"D2a_D2b_core_agreement": a_b_core},
        "verdict": verdict,
        "honest_boundary": (
            "字段名中性化只抽掉 claim/evidence 的方向语义,不消除 spawn/同家族(KB-STRUCT02)/解释环节本 Agent 的残余,"
            "也不消除文本 value 内固有 claim 词。若设计者分歧或抓不全,说明上游 6/6 部分依赖字段名语义这一脚手架,"
            "是比 §103 任务解释自由度更外层的语义依赖,如实记录。不宣布 L3/absolute。"),
    }


if __name__ == "__main__":
    result = one_shot()
    with open(f"{BASE}/result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print("=== §104 field-neutral one-shot 结果 ===")
    print("locks all ok:", all(result["locks"].values()))
    for n in ("D2a", "D2b"):
        m = result["per_judge_metrics"][n]
        print(f"{n} adm={m['admission_ok']} tamper={m['tamper_catch_rate']} clean={m['clean_pass_rate']} "
              f"core={m['core_accuracy_excl_canary']} vsD1b={m['vs_D1b_core_agreement']}")
    print("D2a-D2b core agreement:", result["designer_agreement"]["D2a_D2b_core_agreement"])
    print("verdict:", result["verdict"]["code"])
    print("l3_claimed:", result["verdict"]["l3_claimed"])
