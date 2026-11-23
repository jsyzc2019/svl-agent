#!/usr/bin/env python3
"""打包发回：给全部交付文件补 .sha256 锁，再打成 zip。

用法：  python3 pack.py [交付目录，默认 l3_external_audit_v2]

前置：先跑 selfcheck.py 且全部 PASS。哈希锁只锁"内容文件"，
不给 .sha256 自身上锁，避免自指。
"""
import hashlib
import os
import sys
import zipfile

BASE = sys.argv[1] if len(sys.argv) > 1 else "l3_external_audit_v2"
SKIP_SUFFIX = (".sha256", ".zip")
SKIP_DIRS = ("__pycache__",)


def sha(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    if not os.path.isdir(BASE):
        print("找不到交付目录：", BASE)
        sys.exit(1)
    # 1. 给每个内容文件补锁（相对路径作 target 名，便于核验器定位）
    n = 0
    for root, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in files:
            if fn.endswith(SKIP_SUFFIX):
                continue
            fp = os.path.join(root, fn)
            lock = fp + ".sha256"
            with open(lock, "w", encoding="utf-8") as lf:
                lf.write(sha(fp) + "  " + os.path.relpath(fp, BASE) + "\n")
            n += 1
    print("已生成", n, "个 .sha256 锁")

    # 2. 打 zip（顶层目录名 = BASE 基名）
    zpath = BASE.rstrip("/") + ".zip"
    top = os.path.basename(BASE.rstrip("/"))
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for root, dirs, files in os.walk(BASE):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in files:
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, BASE)
                z.write(fp, os.path.join(top, rel))
    print("已打包 ->", zpath, "（", os.path.getsize(zpath), "bytes ）")
    print("把这个 zip 发回给本仓。不要附任何口令/密钥。")


if __name__ == "__main__":
    main()
