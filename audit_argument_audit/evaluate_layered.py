#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gv · 分层评测 + 过拟合守卫（纯函数）。
修正 §4gu 的指标构造错误：伪托类召回曾把语义细节类样本混入分母(代理标签错配 KB-R01)。
按 verdict 任务类型分桶, 各算各的; 并验证 SIG-NARRATIVE 不靠硬编码人名。"""
import json, os, sys
ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
import scan as S

# 任务类型分桶（基于 verdict 的语义定义，预注册锁定）
BUCKETS = {
    "伪托类": {"伪托权威", "查无实据", "伪名言(铁证)", "金句属实但出处混乱/措辞被改",
             "广泛流传但出处存疑", "出处存疑"},
    "语义细节类": {"部分属实(经历真,细节化了)", "有典故但细节走样", "部分属实"},
    "属实与量化": {"属实", "无依据的量化断言"},
}
# 各类命中的判定信号
AUTHORITY_IDS = {"SIG-AUTHORITY", "SIG-QUOTE"}
NARRATIVE_ID = "SIG-NARRATIVE"


def bucket_of(verdict):
    for name, vs in BUCKETS.items():
        if verdict in vs:
            return name
    return "未分类"


def evaluate_layered(factcheck_path=None, rules=None):
    p = factcheck_path or os.path.join(os.path.dirname(ROOT), "article_factcheck.json")
    d = json.load(open(p, encoding="utf-8"))
    rules = rules or S.load_rules()
    rows = []
    for f in d["fact_checks"]:
        ids = {h["id"] for h in S.scan(f["claim"], rules=rules)["hits"]}
        rows.append({"claim": f["claim"], "verdict": f["verdict"],
                     "bucket": bucket_of(f["verdict"]),
                     "authority_hit": bool(ids & AUTHORITY_IDS),
                     "narrative_hit": NARRATIVE_ID in ids,
                     "all_hits": sorted(ids)})
    out = {}
    for name in BUCKETS:
        sub = [r for r in rows if r["bucket"] == name]
        out[name] = {
            "n": len(sub),
            "authority_hit": sum(r["authority_hit"] for r in sub),
            "narrative_hit": sum(r["narrative_hit"] for r in sub),
        }
    # 伪托类召回（真·分母）
    a = out["伪托类"]
    a["recall"] = a["authority_hit"] / a["n"] if a["n"] else None
    # 叙事信号覆盖语义细节类
    s = out["语义细节类"]
    s["coverage"] = s["narrative_hit"] / s["n"] if s["n"] else None
    # 属实类误报
    t = out["属实与量化"]
    t["false_positive"] = t["narrative_hit"]
    return {"rows": rows, "by_bucket": out}


def overfit_guard(rules=None):
    """过拟合守卫：中性人名句(无叙事细节)不得触发叙事信号；具体人名不得出现在正则里。"""
    rules = rules or S.load_rules()
    # 1) 新增 SIG-NARRATIVE 的正则正文不得含具体人名（v1 SIG-QUOTE 已有的人名不在本守卫范围——那是 v1 既定判据, 本轮不删不改）
    banned = ["王小波", "闵子骞", "杨绛", "黑塞", "马尔克斯"]
    narrative_rules = [r for r in rules["rules"] if r["id"] == NARRATIVE_ID]
    pattern_text = " ".join(p for r in narrative_rules for p in r["patterns"])
    hardcoded = [b for b in banned if b in pattern_text]
    # 2) 中性名人句（无叙事细节）零命中叙事信号
    neutral = "王小波是一位作家。闵子骞是孔子的学生。杨绛翻译过作品。"
    neutral_hit = NARRATIVE_ID in {h["id"] for h in S.scan(neutral, rules=rules)["hits"]}
    # 3) 通用叙事句（无具体人名）应命中
    generic = "据说有人年轻时下乡，独自看书排遣孤寂。相传有人拜访名师，面色由蜡黄变红润。"
    generic_hit = NARRATIVE_ID in {h["id"] for h in S.scan(generic, rules=rules)["hits"]}
    return {"passed": (not hardcoded) and (not neutral_hit) and generic_hit,
            "hardcoded_names": hardcoded,
            "neutral_false_positive": neutral_hit,
            "generic_caught": generic_hit}


if __name__ == "__main__":
    import json as J
    r = evaluate_layered()
    g = overfit_guard()
    print(J.dumps({"by_bucket": r["by_bucket"], "guard": g}, ensure_ascii=False, indent=1))
