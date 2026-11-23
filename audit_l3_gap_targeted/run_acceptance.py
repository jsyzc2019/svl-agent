#!/usr/bin/env python3
"""本仓侧验收流程补全：调用权威验收器实跑，把真实结果落为 verification_summary.json。

背景（工具修复，不放宽判定）：engine.py 读取 EXT/verification_summary.json 判断
"交付是否已通过本仓验收"，但全仓无脚本生成该文件（v1/v2 契约缺口）。本脚本补这个缺口：
摘要的 passed 字段**完全来自 verify_external.py 的真实退出码与输出**，任一 FAIL 即
passed=false，绝不伪造、不手写、不绕过。已锚定的 verify_external.py 一字不改。

用法：python3 run_acceptance.py [外家交付目录]
输出：向外家交付目录写 verification_summary.json（本仓验收方生成，非外家自报）。
"""
import hashlib
import json
import os
import re
import subprocess
import sys
import datetime

BASE = os.path.dirname(os.path.abspath(__file__))
EXT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "received", "l3_external_audit_v2")
VERIFY = os.path.join(BASE, "verify_external.py")


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    r = subprocess.run([sys.executable, VERIFY, EXT], capture_output=True, text=True)
    out = r.stdout + r.stderr
    m = re.search(r"=== (\d+)/(\d+) PASS ===", out)
    passed_cnt, total_cnt = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
    accepted = "DELIVERABLE_ACCEPTED_FOR_MECHANICAL_COMPARISON" in out
    all_pass = (r.returncode == 0 and m is not None
                and passed_cnt == total_cnt and total_cnt == 9 and accepted)

    summary = {
        "generated_by": "本仓验收方 run_acceptance.py（非外家自报）",
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "verifier_sha256": sha(VERIFY),
        "deliverable_sha256_of_criterion": sha(os.path.join(EXT, "criterion.py"))
            if os.path.exists(os.path.join(EXT, "criterion.py")) else None,
        "verifier_exit_code": r.returncode,
        "passed_count": passed_cnt,
        "total_checks": total_cnt,
        "verifier_accepted_marker": accepted,
        "raw_output_sha256": hashlib.sha256(out.encode()).hexdigest(),
        "passed": all_pass,
        "note": "passed=true 仅当 verify_external.py 真实退出码0且9/9且含 ACCEPTED 标记；任一FAIL即false。",
    }
    dst = os.path.join(EXT, "verification_summary.json")
    with open(dst, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(out.strip())
    print("---")
    print("verification_summary.json 已写入:", dst)
    print("passed =", all_pass, f"（{passed_cnt}/{total_cnt}, exit={r.returncode}）")
    if not all_pass:
        sys.exit(1)


if __name__ == "__main__":
    main()
