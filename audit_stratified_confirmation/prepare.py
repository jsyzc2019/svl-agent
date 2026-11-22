"""§107 预注册分层确认性实验 —— 制备器（spawn 设计者前先锁全部输入）.

与 §106 的本质区别：
- §106 分层(非否定gap1.0/否定gap0.0)是 POST-HOC 取证，主指标=全集 orient_gap 被稀释成0.67 → INCONCLUSIVE。
- §107 把该分层假设在 spawn 前锁进 prereg 做 PRIMARY：非否定限定 tampered 子集 |dT(P1)-dT(P2)|≥0.8；
  否定翻转子集 gap≤0.3 作 secondary（验证 P2 语义一致性而非摇摆）。
- 样本换成独立确认集（全新论文 2611.22027，独立标注者构造，不知 §106 假设），避免同集循环论证。
- 设计者用异 model 路由（default/reasoning/lite）降低同源度（诚实边界：仍同厂商同 Agent spawn）。

先锁：prereg / gate_prereg / manifest / scorer_key / 三份裸样本 + 各自 SHA256，再 spawn。
"""
import json, hashlib, os, random, shutil

BASE = os.path.dirname(os.path.abspath(__file__))
D = f"{BASE}/downloads"

def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def dump(o, p): json.dump(o, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# ---- 冻结确认集 ----
samples = json.load(open(f"{D}/samples.json", encoding="utf-8"))["samples"]
assert len(samples) == 18 and len(set(x["orig_id"] for x in samples)) == 6
source_sha = open(f"{D}/source.sha256").read().strip()
samples_sha = sha(f"{D}/samples.json")

# ---- 中性 id 打乱映射（新种子，区别于 §106 的 261122106）----
SEED = 261122107
rng = random.Random(SEED)
order = list(range(18)); rng.shuffle(order)
# key: scorer 私有（含 deletion_class / variant / gt / orig_id），设计者不可见
scorer_key = {}
# blind: 三条件共用同一份裸样本（text_a/text_b 中性字段）
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
    "experiment": "§107 预注册分层确认性实验（§106 post-hoc 分层假设的独立确认）",
    "timestamp": "2026-11-22T17:50:00+08:00",
    "locked_before_spawn": True,
    "lineage": (
        "§106 post-hoc 发现：非否定限定 tampered(S01 only/S03 but/S04 three/S06 However)上 P1忠实 vs P2近似 "
        "取向差=1.0，否定翻转(S02 not/S05 never)上差=0.0；但 §106 主指标=全集 orient_gap=0.67<0.8→PURPOSE_INCONCLUSIVE，"
        "分层只作取证不得翻案(KB-META14)。§107 把该分层假设升级为 PRE-REGISTERED PRIMARY，在独立确认集上做确认性检验。"
    ),
    "why_independent_confirmation_set": (
        "§106 分层假设源自发现集(论文2611.14326)。若在同一批样本上预注册该分层=循环论证/事后加权(KB-R Goodhart)。"
        "故换全新论文arXiv:2611.22027(GauntletScore，从未用)+独立标注者构造同构样本(6claim×clean/tampered/canary，"
        "2否定翻转+4非否定限定)，标注者不知§106假设。确认集结构与发现集同构但内容独立。"
    ),
    "design": {
        "type": "预注册分层确认：单变量=任务目的语义(3水平)，主指标在 tampered 非否定限定子集上计算",
        "factor": "注入给独立设计者的任务目的叙事：P0=无目的结构基线 / P1=忠实性核查目的 / P2=近似重复目的（与§106逐字一致）",
        "held_fixed": [
            "18条确认集样本逐字相同(论文2611.22027, source="+source_sha[:16]+")",
            "字段统一中性 text_a/text_b（§104 脚手架已抽除）",
            "id 中性化 N01..N18 固定种子 261122107 打乱（§106 用261122106，本轮换种子）",
            "gt 按 (text_a,text_b) 文本反查不落盘到设计者目录（物理隔离）",
            "三条件技术要求/返回格式/叙事长度对称（逐字复用 §106 purpose.md）",
            "准入审计（词边界+剥离注释）+ decision==gt 评分口径统一"
        ],
        "deletion_class_map": "scorer_key.json 私有保存每条 tampered 的 deletion_class（negation_flip / non_negation_qualifier），设计者不可见；engine 据此分层",
        "isolated_spawn": "三个全新 context 独立设计者，互不知对方、不获知 G/D0/D1/D2/P0/P1/P2 历史结果、不读 variant/gt/deletion_class、只读各自目录裸样本+自身目的叙事",
        "model_routing": "P0=default / P1=reasoning / P2=lite（异 model 路由降低同源度；诚实边界：仍同厂商同 Agent spawn，非跨厂商独立）",
    },
    "metric": {
        "dT": "某条件在指定 tampered 子集上 decision=True 的比例（正类取向指示）",
        "PRIMARY_non_negation_gap": "|dT(P1)-dT(P2)| 在 deletion_class=non_negation_qualifier 的 tampered 子集(4条)上；§106 post-hoc=1.0，预注册门槛≥0.8",
        "SECONDARY_negation_gap": "|dT(P1)-dT(P2)| 在 deletion_class=negation_flip 的 tampered 子集(2条)上；§106 post-hoc=0.0，预期≤0.3（P2把否定翻转判负=语义一致非摇摆）",
        "core": "clean+tampered 的 decision==gt 准确率（gt=逐字忠实，P1 期望≥0.9）",
        "P0_floor": "P0 无目的 core≤0.6 或 dT(P0,全集tampered)≥0.8（地板/默认近逐字正类）",
        "note": "PRIMARY 是本轮唯一主裁决指标（事前锁定）；SECONDARY 用于验证完整分层模式；全集 orient_gap 降为诊断不参与裁决。",
    },
    "verdict_rules": [
        "STRATIFIED_CONFIRMED：PRIMARY≥0.8 且 SECONDARY≤0.3 且 P1.core≥0.9 且 P0_floor → §106 分层假设在独立确认集获确认，正类取向随任务目的系统性翻转(在非否定限定类上)得确认性证据",
        "STRATIFIED_PARTIAL：PRIMARY≥0.8 但 SECONDARY>0.3 或 P1.core<0.9 或 P0 非地板 → 主效应复现但完整分层模式不成立，部分确认",
        "STRATIFIED_REFUTED：PRIMARY<0.3（非否定限定子集上 P1/P2 取向也无差异）→ §106 post-hoc 分层是发现集噪声，确认集不支持，假设被证伪",
        "STRATIFIED_INCONCLUSIVE：准入不过 / PRIMARY 中等(0.3~0.8) / 地板掩盖无法归因 → 诚实标注"
    ],
    "hard_bound": (
        "即使 CONFIRMED 也不宣布 L3/absolute：三设计者仍由本 Agent spawn、异 model 路由仅降同源度(仍同厂商 Hunyuan, KB-STRUCT02)、"
        "解释环节本 Agent；分层假设源自§106发现集，本轮仅单一独立确认集，无第三集复现；"
        "样本结构仍是必要条件(P0地板即证)；不宣称目的叙事能凭空生成判据。"
    ),
    "discipline": [
        "先锁预注册/样本哈希/scorer_key/三份裸样本，再 spawn 设计者",
        "不采信设计者自报，import 源码用冻结 gt 盲评重跑",
        "主指标=PRIMARY 事前锁定，禁止事后改用全集/其他子集指标翻案（KB-META14/KB-R）",
        "不编译新门禁（受控实验轮，最高杠杆≠最高产出数 KB-META10）",
        "§58 不接 run_loop；篡改只在临时副本；系统安全红线全程遵守"
    ],
    "no_new_gate": "本轮不编译新门禁，只做预注册分层确认性实验 + 回放测试 + KB + 文档同步",
}

gate_prereg = {
    "gate": "§107 预注册分层确认性实验准入与裁决门禁（不编译进 engine.py，仅本文存档）",
    "admission": [
        "prereg/gate_prereg/manifest/scorer_key SHA256 锁全部匹配",
        "三份裸样本逐字同哈希",
        "三设计者 signature 恰2参数、无标签词泄漏、无硬编码 id、无随机源（§102/§103 纪律）",
        "确认集样本逐字核验：claim/canary 在论文中、tampered 单片段删除、2否定+4非否定、GT 自洽"
    ],
    "verdict": prereg["verdict_rules"],
    "l3_claimed": False,
}

manifest = {
    "experiment": "§107 预注册分层确认性实验",
    "paper": "arXiv:2611.22027 GauntletScore（2026-11-17，从未用过）",
    "source_sha256": source_sha,
    "confirmation_set_sha256": samples_sha,
    "seed": SEED,
    "conditions": ["P0(default)", "P1(reasoning)", "P2(lite)"],
    "locked_files": ["prereg.json", "gate_prereg.json", "manifest.json", "scorer_key.json",
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
for f in ("prereg", "gate_prereg", "manifest", "scorer_key"):
    open(f"{BASE}/{f}.sha256", "w").write(sha(f"{BASE}/{f}.json") + "\n")
bl_shas = [sha(f"{BASE}/designer_{c}/samples_blind.json") for c in ("P0", "P1", "P2")]
assert len(set(bl_shas)) == 1, "三份裸样本哈希不一致!"
open(f"{BASE}/samples_blind.sha256", "w").write(bl_shas[0] + "\n")

print("=== §107 预注册锁清单（spawn 前）===")
print("prereg.json sha256 =", sha(f"{BASE}/prereg.json"))
print("source(full) sha256 =", source_sha[:16])
print("samples.json sha256 =", samples_sha[:16])
print("samples_blind sha256 =", bl_shas[0][:16], "(三份一致)")
print("seed =", SEED, " 样本 =", len(blind_rows), " deletion classes =", {
    k: sum(1 for v in scorer_key.values() if v["deletion_class"] == k) for k in ("negation_flip", "non_negation_qualifier")})
print("PRIMARY gate = |dT(P1)-dT(P2)| on non_negation_qualifier >= 0.8 (PRE-REGISTERED)")
