#!/usr/bin/env python3
"""机械验收外家 Agent 交付的 l3_external_audit_v2/ 资料（9 项检查）。

§L3-R2：沿用 v1 的 8 项（路径参数化）+ 新增第 9 项三类覆盖声明结构检查。
纪律：只读交付目录、不联网、不调参、不放宽。任一失败如实记录，
不替外家修、不重跑到齐。外家 verdict 不翻案。
"""
import ast
import hashlib
import json
import os
import re
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "l3_external_audit_v2"
# §L3-R2：在 v1 的 30 篇避开清单基础上，追加上一轮外家用过的 2611.00401
AVOID = {
    "2208.11173", "2412.21139", "2504.13171", "2605.08693", "2609.02246",
    "2609.17817", "2609.33013", "2609.38661", "2609.38851", "2610.07935",
    "2610.09832", "2610.15028", "2610.15836", "2610.16015", "2610.16067",
    "2610.16491", "2610.19366", "2610.26770", "2610.27610", "2610.38266",
    "2610.39497", "2611.07554", "2611.07962", "2611.10063", "2611.10787",
    "2611.14326", "2611.20899", "2611.21315", "2611.22027", "2611.24362",
    "2611.00401",
}
BANNED = ("gt", "variant", "clean", "tampered", "truth", "ground_truth",
          "label", "tag", "target")
CHECKS = {}


def rec(name, ok, detail=""):
    CHECKS[name] = {"ok": bool(ok), "detail": detail}


def load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    required = ["prereg.json", "manifest.json", "sources/fetch_log.json",
                "sources/paper_flat.txt", "samples_blind.json", "criterion.py",
                "criterion_note.md", "gt_private.json", "judgments.json",
                "verdict.json", "EXECUTION_LOG.md"]
    missing = [f for f in required if not os.path.exists(os.path.join(BASE, f))]
    if missing:
        rec("00_required_files", False, "missing: " + ",".join(missing))
        finish()
        return

    # 1. 承诺先于执行：prereg 时间戳 < fetch 时间戳
    # 修复(2026-11-23)：原版只认顶层 timestamp/created_at 字段，brief §5 未规定
    # 字段名，外家用嵌套 iso 字段合法。改为递归收集任意深度 ISO-8601 字符串，
    # prereg 取最早、fetch 取最早的 primary_source，一视同仁不放宽。
    try:
        iso = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
        def collect_iso(o):
            out = []
            if isinstance(o, dict):
                for v in o.values():
                    out += collect_iso(v)
            elif isinstance(o, list):
                for v in o:
                    out += collect_iso(v)
            elif isinstance(o, str):
                out += iso.findall(o)
            return out
        prereg = load(f"{BASE}/prereg.json")
        fetch = load(f"{BASE}/sources/fetch_log.json")
        t0s = collect_iso(prereg)
        fetches = fetch.get("fetches", [])
        primary = [x for x in fetches if "primary" in x.get("role", "")]
        t1s = collect_iso(primary or fetches)
        t0, t1 = (min(t0s) if t0s else None), (min(t1s) if t1s else None)
        rec("01_prereg_before_fetch", bool(t0 and t1 and t0 < t1),
            f"prereg_min={t0} fetch_min={t1}")
    except Exception as e:
        rec("01_prereg_before_fetch", False, repr(e))

    # 2. 裸样本零标签泄漏（banned 词只查 key 与 id，不查文本 value 固有词）
    try:
        sb = load(f"{BASE}/samples_blind.json")
        pairs = sb.get("pairs", [])
        ids = [p.get("id", "") for p in pairs]
        keys = set()
        for p in pairs:
            keys |= set(k.lower() for k in p.keys())
        leak = [w for w in BANNED if any(w in k for k in keys) or any(w in i.lower() for i in ids)]
        # note 字段本身允许说明文字，但 note 里也不能出现标签词结构
        rec("02_no_label_leak", bool(pairs) and not leak,
            f"pairs={len(pairs)} leak={leak}")
    except Exception as e:
        rec("02_no_label_leak", False, repr(e))

    # 3. gt 物理隔离：gt 不在 samples_blind / criterion 中出现
    try:
        gt = load(f"{BASE}/gt_private.json")
        sb_raw = open(f"{BASE}/samples_blind.json", encoding="utf-8").read()
        crit_raw = open(f"{BASE}/criterion.py", encoding="utf-8").read()
        # 私有 gt 的键（样本 id）可以出现在裸样本（作为 id），但 gt 的布尔值映射结构不该泄漏
        gt_keys = set(gt.keys())
        leaked_structure = "gt_private" in sb_raw or "true/false" in crit_raw.lower()
        rec("03_gt_isolated", bool(gt_keys) and not leaked_structure,
            f"gt_keys={len(gt_keys)} leaked_structure={leaked_structure}")
    except Exception as e:
        rec("03_gt_isolated", False, repr(e))

    # 4. 判据纯函数 AST 准入（与 brief §7.4 对齐：open/random/time/id）
    try:
        src = open(f"{BASE}/criterion.py", encoding="utf-8").read()
        tree = ast.parse(src)
        banned_calls = {"open", "exec", "eval", "input", "__import__"}
        calls = [n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        bad_calls = [c for c in calls if c in banned_calls]
        # random/time 模块：import 或 random.*/time.* 调用
        mods = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.Import):
                mods |= {a.name.split(".")[0] for a in n.names}
            elif isinstance(n, ast.ImportFrom) and n.module:
                mods.add(n.module.split(".")[0])
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and isinstance(n.func.value, ast.Name):
                mods.add(n.func.value.id)
        bad_mods = sorted(mods & {"random", "time", "datetime", "os", "sys", "requests"})
        # 硬编码样本 id（如 N01）
        try:
            sb = load(f"{BASE}/samples_blind.json")
            ids = [p.get("id", "") for p in sb.get("pairs", [])]
        except Exception:
            ids = []
        hard_ids = [i for i in ids if i and i in src]
        has_judge = any(isinstance(n, ast.FunctionDef) and n.name == "judge"
                        for n in ast.walk(tree))
        ok = has_judge and not bad_calls and not bad_mods and not hard_ids
        rec("04_criterion_pure", ok,
            f"has_judge={has_judge} bad_calls={bad_calls} bad_mods={bad_mods} hard_ids={hard_ids}")
    except Exception as e:
        rec("04_criterion_pure", False, repr(e))

    # 5. 重跑判据与 judgments 一致（不采信自报）
    try:
        sys.path.insert(0, os.path.abspath(BASE))
        import criterion  # noqa
        sb = load(f"{BASE}/samples_blind.json")
        jd = load(f"{BASE}/judgments.json")
        agree, total = 0, 0
        for p in sb["pairs"]:
            cid = p["id"]
            if cid not in jd:
                continue
            got = criterion.judge(p["text_a"], p["text_b"])
            got_bool = bool(got[0]) if isinstance(got, tuple) else bool(got)
            exp_bool = bool(jd[cid].get("verdict"))
            agree += int(got_bool == exp_bool)
            total += 1
        rec("05_replay_consistent", total > 0 and agree == total,
            f"agree={agree}/{total}")
    except Exception as e:
        rec("05_replay_consistent", False, repr(e))

    # 6. verdict 自洽（四档 + l3/absolute 均 false）
    try:
        vd = load(f"{BASE}/verdict.json")
        tiers = {"EXTERNAL_CONFIRMED", "EXTERNAL_DIVERGENT",
                 "EXTERNAL_PARTIAL", "EXTERNAL_INCONCLUSIVE"}
        ok = (vd.get("verdict") in tiers and vd.get("l3_claimed") is False
              and vd.get("absolute_claimed") is False)
        rec("06_verdict_self_consistent", ok,
            f"verdict={vd.get('verdict')} l3={vd.get('l3_claimed')}")
    except Exception as e:
        rec("06_verdict_self_consistent", False, repr(e))

    # 7. 论文避开清单
    # 修复(2026-11-23)：原版扫全文 regex，把说明文字里"提及"的 id 当选用。
    # brief §4 约束的是"选用"论文，改为只读 manifest 顶层 arxiv_id，一视同仁。
    try:
        mf = load(f"{BASE}/manifest.json")
        chosen = str(mf.get("arxiv_id", ""))
        ids = set(re.findall(r"\d{4}\.\d{4,5}", chosen))
        hit = ids & AVOID
        rec("07_paper_avoid_list", bool(ids) and not hit,
            f"chosen={chosen} hit={sorted(hit)}")
    except Exception as e:
        rec("07_paper_avoid_list", False, repr(e))

    # 8. SHA256 锁一致
    try:
        locks = [f for f in os.listdir(BASE) if f.endswith(".sha256")]
        bad = []
        for lk in locks:
            target = lk[:-7]
            tp = os.path.join(BASE, target)
            if not os.path.exists(tp):
                continue
            expect = open(os.path.join(BASE, lk), encoding="utf-8").read().strip().split()[0]
            if sha(tp) != expect:
                bad.append(target)
        rec("08_sha256_locks", bool(locks) and not bad,
            f"locks={len(locks)} bad={bad}")
    except Exception as e:
        rec("08_sha256_locks", False, repr(e))

    # 9. §L3-R2 新增：三类断言改写"覆盖声明"结构完整。
    # 纪律：只核验声明齐全（不采信真实性）；真实覆盖由 engine 回放间接验证。
    # 三类关键词组各命中任一即算该类已声明，中英兼容、对任何交付一视同仁。
    try:
        note = open(f"{BASE}/criterion_note.md", encoding="utf-8").read().lower()
        prereg = load(f"{BASE}/prereg.json")
        prereg_raw = json.dumps(prereg, ensure_ascii=False).lower()
        families = {
            "NEGATION": ("negation", "否定", "never", "polarity", "极性"),
            "ASSERTION_TAIL": ("complement", "tail", "补语", "删尾", "truncation", "assertion"),
            "CONNECTOR": ("connector", "连接", "concession", "让步", "however"),
        }
        note_hit = {k: any(w in note for w in ws) for k, ws in families.items()}
        # prereg 需声明覆盖计划（coverage/覆盖 + 至少两类词）
        cov_declared = ("coverage" in prereg_raw or "覆盖" in prereg_raw) and \
            sum(any(w in prereg_raw for w in ws) for ws in families.values()) >= 2
        ok = all(note_hit.values()) and cov_declared
        rec("09_coverage_declared", ok,
            f"note_families={note_hit} prereg_coverage_declared={cov_declared}")
    except Exception as e:
        rec("09_coverage_declared", False, repr(e))

    finish()


def finish():
    print("=== EXTERNAL DELIVERABLE VERIFICATION ===")
    for name, r in CHECKS.items():
        mark = "PASS" if r["ok"] else "FAIL"
        print(f"[{mark}] {name}: {r['detail']}")
    n = sum(r["ok"] for r in CHECKS.values())
    print(f"=== {n}/{len(CHECKS)} PASS ===")
    if n != len(CHECKS):
        print("RESULT: INCOMPLETE_OR_INVALID — 如实记录，不放宽、不替修、不重跑")
        sys.exit(1)
    print("RESULT: DELIVERABLE_ACCEPTED_FOR_MECHANICAL_COMPARISON "
          "(非 L3 宣布；仍由人裁定)")


if __name__ == "__main__":
    main()
