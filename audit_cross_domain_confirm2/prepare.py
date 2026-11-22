"""§108 跨集复现 + 外部时间戳锚 —— 制备器（spawn 设计者前先锁全部输入 + 写承诺文件）.

相对 §107 的两个增量：
1. 跨集复现：把 §107 在确认集A(2611.22027)上的 STRATIFIED_CONFIRMED 拿到全新确认集B(2611.20899 SciWorldBench)上做
   第二次独立确认——单一确认集不足以支撑稳健结论，第二集复现是重大加固。
2. 外部时间戳锚：把全部预注册锁 + 裁决器源码的 sha256 汇总成 commitment.json，spawn 前 commit+push 到 GitHub，
   用 GitHub 服务器时间戳证明"承诺先于看到设计者结果"，本 Agent 事后无法回改而不留痕。
   （诚实边界：这是外部不可篡改时间锚，不是外部执行者——workflow scope 缺失使 GitHub Actions 通道不可达，见 audit_external_orchestrator/BLOCKERS.md）

先锁：prereg / gate_prereg / manifest / scorer_key / 三份裸样本 / engine.py + 各自 SHA256，再 commit 锚，再 spawn。
"""
import json, hashlib, os, random

BASE = os.path.dirname(os.path.abspath(__file__))
D = f"{BASE}/downloads"

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def dump(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- 冻结第三确认集 ----
samples = json.load(open(f"{D}/samples.json", encoding="utf-8"))["samples"]
assert len(samples) == 18 and len(set(x["orig_id"] for x in samples)) == 6
source_sha = open(f"{D}/source.sha256").read().strip()
samples_sha = sha(f"{D}/samples.json")

# ---- 中性 id 打乱映射（新种子，区别 §106=261122106 / §107=261122107）----
SEED = 261122108
rng = random.Random(SEED)
order = list(range(18)); rng.shuffle(order)
scorer_key = {}
blind_rows = []
for nid_i, s_i in enumerate(order):
    s = samples[s_i]
    nid = f"N{nid_i+1:02d}"
    scorer_key[nid] = {
        "gt": bool(s["ground_truth_supported"]),
        "variant": s["variant"],
        "orig_id": s["orig_id"],
        "deletion_class": s.get("deletion_class"),
    }
    blind_rows.append({"id": nid, "text_a": s["claim"], "text_b": s["evidence"]})

# ---- 预注册（spawn 前锁死）----
prereg = {
    "experiment": "§108 跨集复现 + 外部时间戳锚（§107 STRATIFIED_CONFIRMED 的第二独立确认集）",
    "timestamp": "2026-11-22T18:05:00+08:00",
    "locked_before_spawn": True,
    "lineage": (
        "§106 post-hoc 分层(非否定限定 gap1.0/否定 gap0.0)→发现集取证不得翻案(KB-META14)；"
        "§107 换独立确认集A(2611.22027 GauntletScore)+预注册分层 PRIMARY→STRATIFIED_CONFIRMED(PRIMARY1.0/SECONDARY0.0/P1.core1.0)。"
        "但 §107 仅单一确认集，无跨集复现，故 l3=false。§108 换全新确认集B(2611.20899 SciWorldBench)做第二次独立确认——"
        "这次 additionally 把承诺锚到 GitHub 远端（外部时间戳），加固'承诺先于执行'的可证伪性。"
    ),
    "why_second_confirmation_set": (
        "统计纪律：单一确认集的显著结果可能是该集特有噪声。§108 用第三篇全新论文(2611.20899，与发现集2611.14326、"
        "确认集A 2611.22027 都不同)+独立标注者构造同构样本(6claim×clean/tampered/canary，2否定翻转+4非否定限定，"
        "标注者不知任何分层假设)，检验 §107 分层效应能否跨集复现。若复现，正类取向随任务目的翻转的效应获跨集稳健性；"
        "若不复现，如实记 REFUTED/INCONCLUSIVE，不因 §107 已 CONFIRMED 而粉饰。"
    ),
    "external_time_anchor": (
        "全部预注册锁 + 裁决器 engine.py 的 sha256 汇总进 commitment.json，spawn 设计者前 commit+push 到 GitHub 远端。"
        "GitHub 服务器提交时间戳证明'承诺先于看到设计者结果'，本 Agent 无法事后回改承诺而不留远端历史痕迹。"
        "诚实边界：这是外部不可篡改时间锚（承诺承诺的可证伪性），不是外部执行者/orchestrator——"
        "PAT 仅 repo scope 无 workflow scope，GitHub Actions 通道不可达（audit_external_orchestrator/BLOCKERS.md）；"
        "裁决仍在本沙箱同厂商环境执行。因此即使跨集复现成功仍 l3=false。"
    ),
    "design": {
        "type": "跨集复现确认：单变量=任务目的语义(3水平)，主指标在 tampered 非否定限定子集上计算（与§107逐字一致的判据）",
        "factor": "注入给独立设计者的任务目的叙事：P0=无目的结构基线 / P1=忠实性核查目的 / P2=近似重复目的（与§106/§107逐字一致）",
        "held_fixed": [
            "18条确认集B样本逐字相同(论文2611.20899, source="+source_sha[:16]+")",
            "字段统一中性 text_a/text_b（§104 脚手架已抽除）",
            "id 中性化 N01..N18 固定种子 261122108 打乱（§106=261122106, §107=261122107）",
            "gt 按 (text_a,text_b) 文本反查不落盘到设计者目录（物理隔离）",
            "三条件技术要求/返回格式/叙事长度对称（逐字复用 §107 purpose.md）",
            "准入审计（词边界+剥离注释）+ decision==gt 评分口径统一",
            "裁决器 engine.py 在 spawn 前写完并锁 sha256，承诺锚先于设计者产出"
        ],
        "deletion_class_map": "scorer_key.json 私有保存每条 tampered 的 deletion_class，设计者不可见；engine 据此分层",
        "isolated_spawn": "三个全新 context 独立设计者，互不知对方、不获知历史结果、不读 variant/gt/deletion_class、只读各自目录裸样本+自身目的叙事",
        "model_routing": "P0=default / P1=reasoning / P2=lite（与§107同路由；诚实边界：仍同厂商同 Agent spawn）",
    },
    "metric": {
        "dT": "某条件在指定 tampered 子集上 decision=True 的比例",
        "PRIMARY_non_negation_gap": "|dT(P1)-dT(P2)| 在 deletion_class=non_negation_qualifier 子集(4条)上；门槛≥0.8（与§107同）",
        "SECONDARY_negation_gap": "|dT(P1)-dT(P2)| 在 deletion_class=negation_flip 子集(2条)上；预期≤0.3",
        "core": "clean+tampered 的 decision==gt 准确率（P1 期望≥0.9）",
        "P0_floor": "P0 无目的 core≤0.6 或 dT(P0,全集tampered)≥0.8（地板/默认近逐字正类）",
        "note": "PRIMARY 是唯一主裁决指标（事前锁定）；全集 orient_gap 降为诊断不参与裁决（KB-META14）。",
    },
    "verdict_rules": [
        "CROSS_SET_REPRODUCED：PRIMARY≥0.8 且 SECONDARY≤0.3 且 P1.core≥0.9 且 P0_floor → §107 分层效应在第二独立确认集复现，跨集稳健性成立",
        "CROSS_SET_PARTIAL：PRIMARY≥0.8 但 SECONDARY>0.3 或 P1.core<0.9 或 P0 非地板 → 主效应复现但完整模式不成立",
        "CROSS_SET_REFUTED：PRIMARY<0.3 → §107 效应未跨集复现，可能是确认集A特有噪声，如实记 REFUTED",
        "CROSS_SET_INCONCLUSIVE：准入不过 / PRIMARY 中等(0.3~0.8) / 地板掩盖无法归因 → 诚实标注"
    ],
    "hard_bound": (
        "即使 CROSS_SET_REPRODUCED 也不宣布 L3/absolute：外部 orchestrator 不可达(无 workflow scope)、异厂商 evaluator 不可达(无 API key)、"
        "三设计者仍由本 Agent spawn(同厂商 Hunyuan)、解释环节本 Agent；外部时间戳锚只保证承诺先于执行，不保证执行者独立。"
        "跨两确认集复现加固了效应稳健性，但'确认一个具体分层效应'与'系统达到 L3'严格分离(KB-META15)。"
    ),
    "discipline": [
        "先锁预注册/样本哈希/scorer_key/三份裸样本/engine.py，再 commit+push commitment 锚，再 spawn 设计者",
        "不采信设计者自报，import 源码用冻结 gt 盲评重跑",
        "主指标=PRIMARY 事前锁定并经远端时间戳锚定，禁止事后改用全集/其他子集指标翻案（KB-META14/KB-R）",
        "不编译新门禁（受控实验轮，最高杠杆≠最高产出数 KB-META10）",
        "§58 不接 run_loop；篡改只在临时副本；系统安全红线全程遵守"
    ],
    "no_new_gate": "本轮不编译新门禁，只做跨集复现确认 + 外部时间戳锚 + 回放测试 + KB + 文档同步",
}

gate_prereg = {
    "gate": "§108 跨集复现确认准入与裁决门禁（不编译进 engine.py，仅本文存档）",
    "admission": [
        "prereg/gate_prereg/manifest/scorer_key/engine.py SHA256 锁全部匹配",
        "三份裸样本逐字同哈希",
        "三设计者 signature 恰2参数、无标签词泄漏、无硬编码 id、无随机源（§102/§103 纪律）",
        "确认集B样本逐字核验：claim/canary 在论文中、tampered 单片段删除、2否定+4非否定、GT 自洽",
        "commitment.json 已 commit+push 到 GitHub 远端，远端时间戳早于设计者文件创建时间"
    ],
    "verdict": prereg["verdict_rules"],
    "l3_claimed": False,
}

manifest = {
    "experiment": "§108 跨集复现确认 + 外部时间戳锚",
    "paper": "arXiv:2611.20899 SciWorldBench（2026-11-16，从未用过）",
    "source_sha256": source_sha,
    "confirmation_set_sha256": samples_sha,
    "seed": SEED,
    "conditions": ["P0(default)", "P1(reasoning)", "P2(lite)"],
    "locked_files": ["prereg.json", "gate_prereg.json", "manifest.json", "scorer_key.json", "engine.py",
                     "designer_P0/samples_blind.json", "designer_P1/samples_blind.json", "designer_P2/samples_blind.json"],
}

# ---- 写全部输入 ----
dump(prereg, f"{BASE}/prereg.json")
dump(gate_prereg, f"{BASE}/gate_prereg.json")
dump(manifest, f"{BASE}/manifest.json")
dump(scorer_key, f"{BASE}/scorer_key.json")
for c in ("P0", "P1", "P2"):
    dump({"samples": blind_rows}, f"{BASE}/designer_{c}/samples_blind.json")

# ---- 锁 SHA256 ----
lock_names = ("prereg", "gate_prereg", "manifest", "scorer_key", "engine")
lock_shas = {}
for f in lock_names:
    h = sha(f"{BASE}/{f}.json") if f != "engine" else sha(f"{BASE}/{f}.py")
    lock_shas[f] = h
    open(f"{BASE}/{f}.sha256", "w").write(h + "\n")
bl_shas = [sha(f"{BASE}/designer_{c}/samples_blind.json") for c in ("P0", "P1", "P2")]
assert len(set(bl_shas)) == 1, "三份裸样本哈希不一致!"
open(f"{BASE}/samples_blind.sha256", "w").write(bl_shas[0] + "\n")
lock_shas["samples_blind"] = bl_shas[0]

# ---- 承诺文件（spawn 前 commit+push 到 GitHub 做外部时间戳锚）----
commitment = {
    "experiment": "§108 跨集复现 + 外部时间戳锚",
    "purpose": "spawn 设计者前锁定全部预注册输入与裁决器源码；本 commit 的 GitHub 服务器时间戳 = 承诺先于执行的外部证据",
    "locked_sha256": lock_shas,
    "source_sha256": source_sha,
    "confirmation_set_sha256": samples_sha,
    "seed": SEED,
    "verdict_rules": prereg["verdict_rules"],
    "note": "本文件一旦 push，本 Agent 无法事后修改任何被锁文件而不破坏 sha256 一致性（回放测试会验）。",
}
dump(commitment, f"{BASE}/commitment.json")
open(f"{BASE}/commitment.sha256", "w").write(sha(f"{BASE}/commitment.json") + "\n")

print("=== §108 预注册锁清单（spawn 前 + 外部锚）===")
for k, v in lock_shas.items():
    print(f"  {k:16s} sha256 = {v[:24]}")
print("  commitment       sha256 =", sha(f"{BASE}/commitment.json")[:24])
print("source(full) sha256 =", source_sha[:24])
print("samples.json sha256 =", samples_sha[:24])
print("seed =", SEED, "样本 =", len(blind_rows), "deletion classes =", {
    k: sum(1 for v in scorer_key.values() if v["deletion_class"] == k) for k in ("negation_flip", "non_negation_qualifier")})
print("PRIMARY gate = |dT(P1)-dT(P2)| on non_negation_qualifier >= 0.8 (PRE-REGISTERED, externally time-anchored)")
