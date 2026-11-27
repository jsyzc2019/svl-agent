#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4S3 确定性核验引擎：路标命题『社会性=对外通讯；网络空间是否存在可自动交流的智能体』三段取证。

纯函数，不接 run_loop，不联网，不 spawn。只读本地已锁存的一手源文件。
裁决对象是路标命题的【存在性/机制/对接】，不触碰 verdict/l3/absolute/宪法。
SHA 失配拒判；逐字锚双重核验（prereg 预注册 → 本引擎只读比对）。
"""
import json, hashlib, os, html

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
PREREG = os.path.join(ROOT, "prereg_safari_social_agents_20261127.json")
PREREG_SHA = os.path.join(ROOT, "prereg_safari_social_agents_20261127.sha256")
EVID_SHA = os.path.join(HERE, "evidence.sha256")

# 逐字锚字典（AST 自审：Compare 内不嵌中文字面量）
_A = {
    # F1 存在性（arXiv 2502.14321 通信中心综述摘要）
    "f1_negotiate": "interact, negotiate, and achieve collective intelligence",
    "f1_central": "central role of communication in coordinating agent behaviors and interactions",
    "f1_mechanisms": "communication mechanisms in LLM-MAS",
    # F1/F2 协议（arXiv 2505.02279 互操作协议综述摘要）
    "f1_coordinate": "coordinate tasks across heterogeneous systems",
    "f2_a2a_delegation": "A2A enables peer-to-peer task delegation using capability-based Agent Cards",
    "f2_anp_discovery": "ANP supports open network agent discovery",
    "f2_four_protocols": "four emerging agent communication protocols",
    "f2_ecosystems": "secure, interoperable, and scalable ecosystems of LLM-powered agents",
    # F2 官方 A2A 规范（a2aproject/A2A docs/index.md）
    "f2_seamless": "seamless communication and collaboration between AI agents",
    "f2_delegate": "Enable agents to delegate sub-tasks, exchange information, and coordinate actions",
    "f2_opaque": "without needing to share internal memory, tools, or proprietary logic",
    "f2_a2a_comm": "agent-to-agent communication",
    # F3 对我不利（arXiv 2609.21401：人机对话表面合作无相互适应）
    "f3_against_surface": "AI produces the surface features of cooperative communication without the underlying social architecture",
    "f3_against_adapt": "AI reproduces the surface of cooperation without the mutual adaptation that grounds it between humans",
    "f3_against_simulate": "merely simulate its surface forms",
    # F3 对我不利（进化生物学 q-bio/0609034：社会性=合作技能+通讯技能多维，非通讯单维）
    "f3_bio_multidim": "develop social cooperation and communication skills",
    "f3_bio_games": "series of different games",
    "f3_bio_not_single": "a single set of rules for intra-population competitions",
    # F3 对我不利/对用户直觉收窄（arXiv 2303.09275：Media Equation/CASA 母理论实证未获证实）
    "f3_casa_not_confirmed": "Media Equation, Singularity, and Uncanny hypotheses were not confirmed",
    "f3_casa_attributed": "human-likeness was not in appearance or behavior but in attributed qualities of being alive",
    # F1b 社会化 bot（arXiv 1703.03107 Varol/Ferrara：Twitter 9-15% 活跃账号是 bot，bot 间互相作用）
    "f1b_bot_ratio": "between 9% and 15% of active Twitter accounts are bots",
    "f1b_bot_interact": "simple bots tend to interact with bots that exhibit more human-like behaviors",
    # F1c 自组织 agent 对话网络（arXiv 2410.11905 Agora + 2603.03555 Molt Dynamics）
    "f1c_agora_selforg": "the emergence of self-organising, fully automated protocols that achieve complex goals without human intervention",
    "f1c_agora_comm_prereq": "Communication is a prerequisite for collaboration",
    "f1c_molt_selforg": "the self-organization and viral information dynamics that arise in large, decentralized populations",
    "f1c_molt_scale": "2.73M interactions among 90,704 autonomous agents",
    # F1c 对我不利（自组织协作有严重开销，Cohen's d=-0.88）
    "f1c_molt_overhead": "severe coordination overhead in decentralized task resolution",
    # F3 反方（arXiv 2604.05197：应承认人机关系的社会性——支持用户『我和你之间就属于这种交流』）
    "f3_for_recognize": "recognize the sociality of human-agent relations",
    "f3_for_parasocial_misapply": "they are increasingly referred to as parasocial",
}

# (文件, 锚点key, 方向) 方向: disclose=命中即支持该命题; against=命中即对我不利; counter=反方
F1 = [
    ("arxiv_2502_14321.txt", "f1_negotiate"),
    ("arxiv_2502_14321.txt", "f1_central"),
    ("arxiv_2502_14321.txt", "f1_mechanisms"),
    ("arxiv_2505_02279.txt", "f1_coordinate"),
]
F1B = [
    ("arxiv_1703_03107.txt", "f1b_bot_ratio"),
    ("arxiv_1703_03107.txt", "f1b_bot_interact"),
]
F1C = [
    ("arxiv_2410_11905.txt", "f1c_agora_selforg"),
    ("arxiv_2410_11905.txt", "f1c_agora_comm_prereq"),
    ("arxiv_2603_03555.txt", "f1c_molt_selforg"),
    ("arxiv_2603_03555.txt", "f1c_molt_scale"),
]
F1C_OVERHEAD = [
    ("arxiv_2603_03555.txt", "f1c_molt_overhead"),
]
F2 = [
    ("arxiv_2505_02279.txt", "f2_a2a_delegation"),
    ("arxiv_2505_02279.txt", "f2_anp_discovery"),
    ("arxiv_2505_02279.txt", "f2_four_protocols"),
    ("arxiv_2505_02279.txt", "f2_ecosystems"),
    ("a2a_index.txt", "f2_seamless"),
    ("a2a_index.txt", "f2_delegate"),
    ("a2a_index.txt", "f2_opaque"),
    ("a2a_index.txt", "f2_a2a_comm"),
]
F3_AGAINST = [
    ("arxiv_2609_21401.txt", "f3_against_surface"),
    ("arxiv_2609_21401.txt", "f3_against_adapt"),
    ("arxiv_2609_21401.txt", "f3_against_simulate"),
    ("arxiv_qbio_0609034.txt", "f3_bio_multidim"),
    ("arxiv_qbio_0609034.txt", "f3_bio_games"),
    ("arxiv_qbio_0609034.txt", "f3_bio_not_single"),
    ("arxiv_2303_09275.txt", "f3_casa_not_confirmed"),
    ("arxiv_2303_09275.txt", "f3_casa_attributed"),
]
F3_COUNTER = [
    ("arxiv_2604_05197.txt", "f3_for_recognize"),
    ("arxiv_2604_05197.txt", "f3_for_parasocial_misapply"),
]


def _sha_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def _logical_sha(obj):
    d = dict(obj)
    d.pop("sha256", None)
    return hashlib.sha256(json.dumps(d, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def integrity():
    """prereg sha + 每个证据文件 sha 是否匹配锁定清单。"""
    prereg_ok = _sha_file(PREREG) == open(PREREG_SHA).read().split()[0]
    declared = {}
    for line in open(EVID_SHA):
        parts = line.split()
        if len(parts) == 2:
            declared[parts[1]] = parts[0]
    ev = {}
    for f in declared:
        p = os.path.join(HERE, f)
        ev[f] = os.path.exists(p) and _sha_file(p) == declared[f]
    return prereg_ok, ev, all(ev.values())


def _check_pairs(pairs):
    hits, misses = [], []
    for f, key in pairs:
        txt = html.unescape(open(os.path.join(HERE, f), encoding="utf-8", errors="replace").read())
        q = _A[key]
        (hits if q in txt else misses).append({"file": f, "quote": q, "hit": q in txt})
    return {"hits": hits, "misses": misses, "ok": len(misses) == 0}


def adjudicate():
    prereg_ok, ev, ev_all = integrity()
    if not (prereg_ok and ev_all):
        return {"verdict": "CHAIN_MISMATCH_REFUSE", "prereg_ok": prereg_ok,
                "evidence_ok": ev, "note": "sha 失配（prereg 或证据文件），拒判"}
    f1 = _check_pairs(F1)
    f1b = _check_pairs(F1B)
    f1c = _check_pairs(F1C)
    f1c_oh = _check_pairs(F1C_OVERHEAD)
    f2 = _check_pairs(F2)
    f3a = _check_pairs(F3_AGAINST)
    f3c = _check_pairs(F3_COUNTER)
    # 预注册裁决树：F1(含bot/自组织)+F2 命中 → 存在性/机制确认；F3 双方均命中 → 对接 REFINE（有界）
    if f1["ok"] and f1b["ok"] and f1c["ok"] and f2["ok"] and f3a["ok"] and f3c["ok"]:
        verdict = "REFINE"
        note = ("F1 存在性（LLM-MAS + 社会化bot 9-15% + 自组织agent网络 2.73M/90704 agents）+ F2 机制 A 级一手确认；"
                "F3 双方一手并存——2609.21401/q-bio/2303.09275 打穿『相互适应/社会性=通讯』等号（对我不利），"
                "2604.05197 反证『人机关系社会性』不应被否证；另 F1c-overhead（Molt d=-0.88）证明自组织协作有严重开销。"
                "命题收窄：通讯与自组织是 agent 可观察事实，但『社会性=对外通讯』等号不成立，"
                "人机交流的社会性判定一手分歧、无定论，且自组织协作未必优于单体。判定权归用户。")
    elif f1["ok"] and f2["ok"] and f3a["ok"]:
        verdict = "REFINE_DEEP"
        note = "F1+F2 确认，F3 仅对我不利方命中——社会性等号打穿，需收窄。"
    elif f1["ok"] and f2["ok"]:
        verdict = "EXISTENCE_MECHANISM_CONFIRMED"
        note = "存在性与机制确认；F3 对接证据不足，重要性结论留白。"
    elif not f1["ok"]:
        verdict = "NO_EXISTENCE_EVIDENCE"
        note = "F1 存在性锚未全命中，如实记，不伪造。"
    else:
        verdict = "EVIDENCE_MISS"
        note = "机制锚未全命中，如实记。"
    return {
        "verdict": verdict, "note": note,
        "prereg_ok": prereg_ok, "evidence_ok": ev,
        "F1_existence": f1, "F1b_social_bots": f1b, "F1c_selforg_networks": f1c,
        "F1c_overhead": f1c_oh, "F2_mechanism": f2,
        "F3_against": f3a, "F3_counter": f3c,
        "verified_anchors": sum(len(x["hits"]) for x in (f1, f1b, f1c, f1c_oh, f2, f3a, f3c)),
    }


def self_bites():
    """负向自咬：篡改必须被抓。三注入：证据sha失配/锚点缺失/prereg sha失配。"""
    results = {}
    # 注入①：证据文件 sha 清单篡改 → integrity 拒判
    orig = open(EVID_SHA).read()
    open(EVID_SHA, "w").write("0" * 64 + "  a2a_index.txt\n")
    try:
        _, _, all_ok = integrity()
        results["evidence_sha_tamper_caught"] = (not all_ok)
    finally:
        open(EVID_SHA, "w").write(orig)
    # 注入②：锚点字典篡改（不存在的引文）→ 该问 misses 非空
    orig_q = _A["f1_negotiate"]
    _A["f1_negotiate"] = "THIS_QUOTE_DOES_NOT_EXIST_IN_ANY_SOURCE_zzzz"
    try:
        r = _check_pairs([("arxiv_2502_14321.txt", "f1_negotiate")])
        results["anchor_tamper_caught"] = (len(r["misses"]) > 0 and not r["ok"])
    finally:
        _A["f1_negotiate"] = orig_q
    # 注入③：prereg sha 声明篡改 → integrity 拒判
    orig_p = open(PREREG_SHA).read()
    open(PREREG_SHA, "w").write("0" * 64 + "  prereg\n")
    try:
        prereg_ok, _, _ = integrity()
        results["prereg_sha_tamper_caught"] = (not prereg_ok)
    finally:
        open(PREREG_SHA, "w").write(orig_p)
    results["all_caught"] = all(results.values())
    return results


if __name__ == "__main__":
    out = adjudicate()
    out["self_bites"] = self_bites()
    print(json.dumps(out, ensure_ascii=False, indent=2))
