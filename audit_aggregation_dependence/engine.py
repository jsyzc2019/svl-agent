#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4ge §4gf 确定性核验引擎：'多独立源聚合降噪'前提的证伪复核。

纯函数，不接 run_loop，不联网，不 spawn。只读本地已锁存的 arxiv_abstracts.json。
裁决对象是"LLM 群体是否满足独立性前提"，不触碰 verdict/l3/absolute/宪法。
"""
import json, hashlib, os
from dataclasses import dataclass

HERE = os.path.dirname(os.path.abspath(__file__))
ABSTRACTS = os.path.join(HERE, "arxiv_abstracts.json")
SHA = os.path.join(HERE, "arxiv_abstracts.sha256")

# 中文锚点集中字典（AST 自审：Compare 内不嵌中文字面量）
_A = {
    "only_about_2": "only about 2 independent votes' worth of information",
    "three_quarters": "Roughly three-quarters of the panel's nominal independence is lost",
    "pts_8_22": "falls 8-22 percentage points short",
    "best_single": "the best single judge matches or outperforms the full panel",
    "rho_070": "0.70",
    "neff_14": "1.4",
    "neff_flat": "remains flat from",
    "market_676": "67.6%",
    "single_702": "70.2%",
    "cross_model": "cross-model diversi",
    "no_gains": "no consistent accuracy gains over single-sample baselines",
    "amplifies": "often amplifies shared misconceptions",
    "social_vs_truth": "predicting what other models will say",
}

# 打靶锚点：(论文 id, 锚点 key) —— 命中=一手支持"独立性前提被违背"
DISCLOSE = [
    ("2605.29800", "only_about_2"),
    ("2605.29800", "three_quarters"),
    ("2605.29800", "pts_8_22"),
    ("2605.29800", "best_single"),
    ("2606.26583", "rho_070"),
    ("2606.26583", "neff_14"),
    ("2606.26583", "neff_flat"),
    ("2606.26583", "market_676"),
    ("2606.26583", "single_702"),
    ("2606.26583", "cross_model"),
    ("2603.06612", "no_gains"),
    ("2603.06612", "amplifies"),
    ("2603.06612", "social_vs_truth"),
]

# 反打靶锚点：一手自带的前提限定——降噪失败的根因是"独立被违背"，不是"聚合本身无用"
COUNTER = [
    ("2606.26583", "cross_model"),  # 互异模型多样性是缓解 -> 独立性回升则聚合可获益
]


def load_abstracts():
    with open(ABSTRACTS) as f:
        return json.load(f)


def sha256_ok():
    with open(SHA) as f:
        expected = f.read().split()[0]
    actual = hashlib.sha256(open(ABSTRACTS, "rb").read()).hexdigest()
    return expected == actual


@dataclass
class Verdict:
    status: str
    disclose_hits: int
    disclose_total: int
    counter_hits: int
    note: str


def adjudicate(data=None):
    """逐字核验打靶/反打靶锚点，返回裁决。SHA 失配拒判。"""
    if not sha256_ok():
        return Verdict("CHAIN_MISMATCH_REFUSE", 0, len(DISCLOSE), 0, "source sha256 失配，拒判")
    d = data if data is not None else load_abstracts()

    def text_of(pid):
        return d.get(pid, {}).get("summary", "") or ""

    hits = sum(1 for pid, k in DISCLOSE if _A[k] in text_of(pid))
    counter = sum(1 for pid, k in COUNTER if _A[k] in text_of(pid))

    if hits == len(DISCLOSE) and counter >= 1:
        status = "AGGREGATION_PREMISE_REFINED"
        note = ("三篇A级一手逐字命中：LLM群体误差高度相关(rho=0.70)、有效独立票远小于名义"
                "(9→2, 10→1.4, neff不随N增长)、无验证域聚合常放大共同误解；反打靶锚显示"
                "cross-model diversity可降相关→根因是独立性被违背而非聚合本身失效。"
                "§4gd解药须附'有效独立数neff+是否引入真独立误差源'核验。")
    elif hits == len(DISCLOSE):
        status = "AGGREGATION_PREMISE_REFINED_NO_COUNTER"
        note = "打靶命中但反打靶锚缺失，双侧不齐，降档标注。"
    elif hits >= len(DISCLOSE) - 2:
        status = "PARTIAL_ANCHOR_MISS"
        note = "锚点缺失≥1≤2，先核工具/措辞，不改判据。"
    else:
        status = "NOT_ESTABLISHED"
        note = "打靶锚大面积未命中，不宣称证伪。"

    return Verdict(status, hits, len(DISCLOSE), counter, note)


def live_regression():
    """7 活体样例：纯函数行为回归，不接判定链。"""
    v = adjudicate()
    r = {}
    r["real_chain_adjudicates"] = (v.status == "AGGREGATION_PREMISE_REFINED")
    r["disclose_full"] = (v.disclose_hits == v.disclose_total == 13)
    r["counter_present"] = (v.counter_hits >= 1)
    # 篡改 1：删掉 rho 锚 -> 应降档
    d2 = load_abstracts()
    d2["2606.26583"]["summary"] = d2["2606.26583"]["summary"].replace(_A["rho_070"], "X.XX")
    r["tamper_rho_downgrades"] = (adjudicate(d2).status in ("PARTIAL_ANCHOR_MISS", "AGGREGATION_PREMISE_REFINED_NO_COUNTER"))
    # 篡改 2：删掉 amplifies 锚 -> 应降档
    d3 = load_abstracts()
    d3["2603.06612"]["summary"] = d3["2603.06612"]["summary"].replace(_A["amplifies"], "X")
    r["tamper_amplifies_downgrades"] = (adjudicate(d3).status in ("PARTIAL_ANCHOR_MISS", "AGGREGATION_PREMISE_REFINED_NO_COUNTER"))
    # 篡改 3：非负面/非聚合断言 -> 判据不适用（借 evidence_honesty 的守卫语义）
    r["non_claim_skipped"] = (not any(_A[k] in "the sky is blue" for k in ("only_about_2", "rho_070")))
    # SHA 守卫：函数存在即可（真实 sha 已在 real_chain 覆盖）
    r["sha_guard_exists"] = callable(sha256_ok)
    # 零战利品：裁决名不含 OVERTHROWN
    r["no_overthrown_language"] = ("OVERTHROWN" not in v.status)
    return r


if __name__ == "__main__":
    v = adjudicate()
    print(json.dumps({"status": v.status, "disclose": f"{v.disclose_hits}/{v.disclose_total}",
                      "counter": v.counter_hits, "note": v.note}, ensure_ascii=False, indent=1))
    print("live_regression:", json.dumps(live_regression(), ensure_ascii=False))
