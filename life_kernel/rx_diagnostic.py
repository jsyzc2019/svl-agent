#!/usr/bin/env python3
"""RX 修订候选诊断 CLI：只 import kernel 的只读函数并打印，零判定逻辑。

用法：
    python3 life_kernel/rx_diagnostic.py             # 对真实注册表诊断
    python3 life_kernel/rx_diagnostic.py --self-bite # 负向自咬自验证
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kernel as k  # noqa: E402


def self_bite():
    """负向自咬：证明诊断读的是真数据、非硬编码。"""
    ok = True

    # ① 空注册集合 -> 候选为空
    empty = k.rx_revision_candidates(policy={"registered_frontier_seeds": []})
    c1 = (empty["candidates"] == [] and empty["contributors"] == []
          and empty["registered_count"] == 0)
    print("[G7a] 空注册集合 -> 候选为空:", c1)
    ok &= c1

    # ② 只含 F12 的子集 + original 口径 -> F12 是 contributor, 候选为空
    #    (coverage 口径下 F12 需哲学探针故 Δ=0，此断言专属 original 口径)
    only12 = k.rx_revision_candidates(policy={"registered_frontier_seeds": ["F12"]},
                                      probes=k.ATTRIBUTION_PROBES)
    c2 = ([x["id"] for x in only12["contributors"]] == ["F12"]
          and only12["candidates"] == [])
    print("[G7b] 只含F12 + original口径 -> F12贡献者且候选空:", c2,
          "| contributors=", [x["id"] for x in only12["contributors"]])
    ok &= c2

    # ③ 篡改某 seed direction 命中哲学探针('可证伪/主体/价值') -> 该 seed Δ 变正退出候选
    #    用 policy_override 传假的 digest 不便；直接验证 delta 由 attribution_check 真算：
    #    取一个 Δ=0 的候选,把它的 tags 经 digest monkeypatch 成命中探针,看其是否变 contributor
    orig = k.digest
    target = "F01"
    try:
        def patched():
            d = orig()
            for s in d["seeds"]:
                if s["id"] == target:
                    s = dict(s)
                    s["direction"] = s["direction"] + " 哲学 价值 主体 可证伪"
                    d["seeds"] = [s if x["id"] == target else x for x in d["seeds"]]
                    break
            return d
        k.digest = patched
        mutated = k.rx_revision_candidates()
        row = next(x for x in mutated["candidates"] + mutated["contributors"]
                   if x["id"] == target)
        c3 = row["delta"] > 0
        print("[G7c] 篡改 F01 命中探针 -> Δ>0 退出候选:", c3,
              "| delta=", row["delta"],
              "| 在 contributors=", any(x["id"] == target for x in mutated["contributors"]))
        ok &= c3
    finally:
        k.digest = orig

    # ④ 双口径对比：original 复现 1/14，coverage 得 12/14
    orig = k.rx_revision_candidates(probes=k.ATTRIBUTION_PROBES)
    cov = k.rx_revision_candidates()
    c4 = (len(orig["contributors"]) == 1 and orig["contributors"][0]["id"] == "F12"
          and len(cov["contributors"]) >= 12)
    print("[G7d] 双口径: original 贡献者=", [x["id"] for x in orig["contributors"]],
          "coverage 贡献者数=", len(cov["contributors"]),
          "→ 1/14 变 %d/14:" % len(cov["contributors"]), c4)
    ok &= c4

    # ⑤ 篡改覆盖探针为空列表 -> 全 seed Δ=0、贡献者归零(证明读真探针非硬编码)
    #    注：不能用"无关文本"——_tags_of 对无 tagbook 命中的文本返回兜底 general，
    #    恰与 F11 抽到的 general 匹配(真实 tagbook 行为)，故改用空列表做干净对照。
    mut = k.rx_revision_candidates(probes={"heldout": []})
    c5 = (len(mut["contributors"]) == 0 and mut["full_heldout_net"] == 0
          and len(mut["candidates"]) == 14)
    print("[G7e] 空探针列表→贡献者归零/候选全14:", c5,
          "| contributors=", len(mut["contributors"]), "candidates=", len(mut["candidates"]))
    ok &= c5

    print("\n负向自咬总判:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    if "--self-bite" in sys.argv:
        return self_bite()
    mode = "coverage" if "--probes" not in sys.argv else (
        sys.argv[sys.argv.index("--probes") + 1]
        if "--probes" in sys.argv and sys.argv.index("--probes") + 1 < len(sys.argv) else "coverage")
    probes = k.ATTRIBUTION_PROBES if mode == "original" else k.COVERAGE_PROBES
    r = k.rx_revision_candidates(probes=probes)
    print("=== RX 修订候选只读诊断 [%s 口径] ===" % r["probe_mode"])
    print("已注册种子:", r["registered_count"], "| 全注册 heldout_net:", r["full_heldout_net"])
    print("heldout 探针(%d) 命中 tagbook tag:" % r["probe_count"], r["probe_tags"])
    print("探针文本:", r["probe_topics"])
    print("\n真贡献者(敲除有损失 Δ>0):")
    for x in r["contributors"]:
        print("  %s Δ=%d" % (x["id"], x["delta"]))
    print("\n修订候选(敲除无损 Δ<=0, 供人工复核):")
    for x in r["candidates"]:
        twin = (" twin=" + ",".join(x["tag_twins"])) if x["tag_twins"] else ""
        print("  %s Δ=%d max_jaccard=%.2f%s" %
              (x["id"], x["delta"], x["max_tag_jaccard"], twin))
    print("\n[盲区]", r["coverage_warning"])
    print("[诚实]", r["caveat"])
    print("[裁决] is_drop_verdict =", r["is_drop_verdict"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
