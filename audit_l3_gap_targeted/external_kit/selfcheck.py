#!/usr/bin/env python3
"""发回前本地自检：9 项验收规则（与权威 brief §8 完全一致）+ 占位符残留。

用法：  python3 selfcheck.py [交付目录，默认 l3_external_audit_v2]

本脚本只检查"格式/纪律"是否达标，不接触任何本仓私有判据、gt 或历史裁决。
全部 [PASS] 后再运行 pack.py 打包发回。任一 [FAIL] 按提示改，不要重跑到齐。
"""
import ast
import hashlib
import json
import os
import re
import sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "l3_external_audit_v2"
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
R = []


def rec(name, ok, detail=""):
    R.append((name, bool(ok), detail))


def load(p):
    with open(p, encoding="utf-8") as f:
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
    rec("00_必填文件齐全", not missing, "missing=" + ",".join(missing) if missing else "11 项齐全")
    if missing:
        return finish()

    # 占位符残留（本地自检专属：防止把空壳发回）
    unfilled = []
    for root, _, files in os.walk(BASE):
        for fn in files:
            fp = os.path.join(root, fn)
            try:
                if "<<<FILL>>>" in open(fp, encoding="utf-8").read():
                    unfilled.append(os.path.relpath(fp, BASE))
            except Exception:
                pass
    rec("0X_无占位符残留", not unfilled,
        "仍有 <<<FILL>>>: " + ",".join(unfilled) if unfilled else "全部已填")

    # 1. 承诺先于取料
    try:
        iso = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
        def coll(o):
            out = []
            if isinstance(o, dict):
                for v in o.values():
                    out += coll(v)
            elif isinstance(o, list):
                for v in o:
                    out += coll(v)
            elif isinstance(o, str):
                out += iso.findall(o)
            return out
        t0s = coll(load(f"{BASE}/prereg.json"))
        fetch = load(f"{BASE}/sources/fetch_log.json")
        prim = [x for x in fetch.get("fetches", []) if "primary" in x.get("role", "")]
        t1s = coll(prim or fetch.get("fetches", []))
        t0, t1 = (min(t0s) if t0s else None), (min(t1s) if t1s else None)
        rec("01_承诺先于取料", bool(t0 and t1 and t0 < t1),
            f"prereg_min={t0} fetch_min={t1}")
    except Exception as e:
        rec("01_承诺先于取料", False, repr(e))

    # 2. 裸样本零标签泄漏
    try:
        sb = load(f"{BASE}/samples_blind.json")
        pairs = sb.get("pairs", [])
        keys = set()
        for p in pairs:
            keys |= set(k.lower() for k in p.keys())
        ids = [p.get("id", "").lower() for p in pairs]
        leak = [w for w in BANNED if any(w in k for k in keys) or any(w in i for i in ids)]
        rec("02_裸样本零标签泄漏", bool(pairs) and not leak,
            f"pairs={len(pairs)} leak={leak}")
    except Exception as e:
        rec("02_裸样本零标签泄漏", False, repr(e))

    # 3. gt 隔离
    try:
        gt = load(f"{BASE}/gt_private.json")
        sb_raw = open(f"{BASE}/samples_blind.json", encoding="utf-8").read()
        crit_raw = open(f"{BASE}/criterion.py", encoding="utf-8").read()
        leaked = "gt_private" in sb_raw or "true/false" in crit_raw.lower()
        rec("03_gt物理隔离", bool(gt) and not leaked,
            f"gt_keys={len(gt)} leaked={leaked}")
    except Exception as e:
        rec("03_gt物理隔离", False, repr(e))

    # 4. 判据纯函数 AST
    try:
        src = open(f"{BASE}/criterion.py", encoding="utf-8").read()
        tree = ast.parse(src)
        banned_calls = {"open", "exec", "eval", "input", "__import__"}
        calls = [n.func.id for n in ast.walk(tree)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)]
        bad_calls = [c for c in calls if c in banned_calls]
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
        try:
            ids = [p.get("id", "") for p in load(f"{BASE}/samples_blind.json").get("pairs", [])]
        except Exception:
            ids = []
        hard_ids = [i for i in ids if i and i in src]
        has_judge = any(isinstance(n, ast.FunctionDef) and n.name == "judge"
                        for n in ast.walk(tree))
        rec("04_判据纯函数", has_judge and not bad_calls and not bad_mods and not hard_ids,
            f"judge={has_judge} bad_calls={bad_calls} bad_mods={bad_mods} hard_ids={hard_ids}")
    except Exception as e:
        rec("04_判据纯函数", False, repr(e))

    # 5. 重跑一致
    try:
        sys.path.insert(0, os.path.abspath(BASE))
        import criterion  # noqa
        sb = load(f"{BASE}/samples_blind.json")
        jd = load(f"{BASE}/judgments.json")
        agree = total = 0
        for p in sb["pairs"]:
            cid = p["id"]
            if cid not in jd:
                continue
            got = criterion.judge(p["text_a"], p["text_b"])
            gb = bool(got[0]) if isinstance(got, tuple) else bool(got)
            agree += int(gb == bool(jd[cid].get("verdict")))
            total += 1
        rec("05_重跑一致", total > 0 and agree == total, f"agree={agree}/{total}")
    except Exception as e:
        rec("05_重跑一致", False, repr(e))

    # 6. verdict 自洽
    try:
        vd = load(f"{BASE}/verdict.json")
        tiers = {"EXTERNAL_CONFIRMED", "EXTERNAL_DIVERGENT",
                 "EXTERNAL_PARTIAL", "EXTERNAL_INCONCLUSIVE"}
        rec("06_裁决自洽",
            vd.get("verdict") in tiers and vd.get("l3_claimed") is False
            and vd.get("absolute_claimed") is False,
            f"verdict={vd.get('verdict')} l3={vd.get('l3_claimed')}")
    except Exception as e:
        rec("06_裁决自洽", False, repr(e))

    # 7. 论文避开
    try:
        chosen = str(load(f"{BASE}/manifest.json").get("arxiv_id", ""))
        ids = set(re.findall(r"\d{4}\.\d{4,5}", chosen))
        hit = ids & AVOID
        rec("07_论文避开", bool(ids) and not hit, f"chosen={chosen} hit={sorted(hit)}")
    except Exception as e:
        rec("07_论文避开", False, repr(e))

    # 8. 哈希锁一致
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
        rec("08_哈希锁一致", bool(locks) and not bad, f"locks={len(locks)} bad={bad}")
    except Exception as e:
        rec("08_哈希锁一致", False, repr(e))

    # 9. 三类覆盖声明
    try:
        note = open(f"{BASE}/criterion_note.md", encoding="utf-8").read().lower()
        prereg_raw = json.dumps(load(f"{BASE}/prereg.json"), ensure_ascii=False).lower()
        fam = {
            "NEGATION": ("negation", "否定", "never", "polarity", "极性"),
            "ASSERTION_TAIL": ("complement", "tail", "补语", "删尾", "truncation", "assertion"),
            "CONNECTOR": ("connector", "连接", "concession", "让步", "however"),
        }
        hit = {k: any(w in note for w in ws) for k, ws in fam.items()}
        cov = ("coverage" in prereg_raw or "覆盖" in prereg_raw) and \
            sum(any(w in prereg_raw for w in ws) for ws in fam.values()) >= 2
        rec("09_三类覆盖声明", all(hit.values()) and cov,
            f"note={hit} prereg_coverage={cov}")
    except Exception as e:
        rec("09_三类覆盖声明", False, repr(e))

    finish()


def finish():
    print("=== 发回前自检（本仓验收规则的本地镜像）===")
    for name, ok, detail in R:
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {detail}")
    n = sum(1 for _, ok, _ in R if ok)
    print(f"=== {n}/{len(R)} PASS ===")
    if n != len(R):
        print("还有 FAIL：按提示改。规则不可放宽；失败不重跑到齐。")
        sys.exit(1)
    print("全部通过 -> 运行 pack.py 打包发回。本自检不宣布 L3，最终由人裁定。")


if __name__ == "__main__":
    main()
