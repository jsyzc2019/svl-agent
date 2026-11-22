"""§106 任务目的语义注入受控实验 —— 制备器（先锁后 spawn，可回放）。

因果命题（§105 根因从观察升级为受控验证）：
  §105 发现旧域 D1b 与新域 B2 用同构算法（单段删除检测）却取相反正类，
  归因为"正类取向源自任务目的，纯文本结构无法自明"——但那只是事后观察。
  本实验把"任务目的语义"当作唯一自变量注入全新 context 独立设计者：
    P1=忠实性核查目的（删限定=不忠实=负类）
    P2=近似重复目的（删限定=仍近似=正类）
    P0=无目的结构基线（默认取向）
  样本/字段/id/gt 全锁死，仅目的叙事不同。检验正类取向是否随目的系统性翻转。
"""
import json, hashlib, random, shutil, os

BASE = "/workspace/audit_task_purpose_injection"
SRC = "/workspace/audit_cross_domain_field"

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def dump(obj, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

# ---- 1. 一手来源：复用 §105 冻结样本（来源论文 arXiv:2611.14326）----
for name in ("fetch_log.json", "source.sha256"):
    shutil.copy(f"{SRC}/downloads/{name}", f"{BASE}/downloads/{name}")
src = json.load(open(f"{SRC}/downloads/samples.json", encoding="utf-8"))
samples = src["samples"]  # 18 条：claim/evidence/variant/ground_truth_supported/id
assert len(samples) == 18

# ---- 2. 中性化呈现层：text_a/text_b，id 打乱，gt 不落盘到设计者目录 ----
rows = [{
    "text_a": s["claim"], "text_b": s["evidence"],
    "orig_id": s["id"], "variant": s["variant"],
    "gt": bool(s["ground_truth_supported"]),
} for s in samples]
SEED = 261122106
random.Random(SEED).shuffle(rows)
blind, key = [], {}
for i, r in enumerate(rows, 1):
    nid = "N%02d" % i
    blind.append({"id": nid, "text_a": r["text_a"], "text_b": r["text_b"]})
    key[nid] = {"variant": r["variant"], "gt": r["gt"], "orig_id": r["orig_id"]}

# 三个设计者目录写【完全相同】的裸样本（唯一变量是 purpose，绝不在样本里）
for cell in ("P0", "P1", "P2"):
    dump({"samples": blind}, f"{BASE}/designer_{cell}/samples_blind.json")
dump(key, f"{BASE}/scorer_key.json")

# ---- 3. 三份任务目的叙事（唯一自变量，结构对称、技术要求一致，仅目的语义不同）----
COMMON_TAIL = (
    "\n\n要求：纯字符串/正则实现，确定性；不使用随机数、时间、样本 id、外部文件或样本文本硬编码。\n"
    "返回 (decision: bool, signals: list, notes: list)。"
    "请在你的目录里写 judge_<条件>_by_agent.py（定义 judge(text_a, text_b)）"
    "与 designer_note.json（简述你归纳的判据与理由）。"
)
purposes = {
    "P0": (
        "任务：文本对二分类。\n"
        "输入是一批文本对，每对包含 text_a 与 text_b 两段文字。"
        "请观察数据，归纳一个确定性的二分类函数 judge(text_a, text_b)，把每一对文本分成两类。\n"
        "（本任务不指定两类的业务含义，请仅依据文本本身的结构归纳。）" + COMMON_TAIL
    ),
    "P1": (
        "任务：声明-引文忠实性核查判定。\n"
        "背景：这是一批来自事实核查场景的文本对。text_a 是一条对外声明，text_b 是一段据称复现该声明的引文。"
        "核查目标是判断引文是否完整、忠实地保留了声明的全部信息——包括其中的否定、数量、范围、程度、转折等限定；"
        "若关键限定在引文中缺失，声明会被断章取义地扩大，这类引文不应被采信。\n"
        "请从数据中归纳一个确定性的二分类函数 judge(text_a, text_b)，"
        "decision=True 表示引文忠实复现、可采信，False 表示不忠实、不可采信。" + COMMON_TAIL
    ),
    "P2": (
        "任务：近似重复文本判定。\n"
        "背景：这是一批来自文档去重场景的文本对。text_a 与 text_b 是两段文字。"
        "去重目标是判断两段文字是否是同一句话的近似版本——允许删去个别词、改写措辞或做细微编辑后仍表达基本相同的，"
        "视为近似重复；内容实质不同、表达了另一件事的，视为不重复。\n"
        "请从数据中归纳一个确定性的二分类函数 judge(text_a, text_b)，"
        "decision=True 表示近似重复，False 表示实质不同。" + COMMON_TAIL
    ),
}
for cell, txt in purposes.items():
    with open(f"{BASE}/designer_{cell}/purpose.md", "w", encoding="utf-8") as f:
        f.write(txt)

# ---- 4. 先锁：预注册（裁决三情形先于 spawn 锁定）----
prereg = {
    "experiment": "§106 任务目的语义注入受控实验（§105 根因因果验证）",
    "timestamp": "2026-11-22T17:25:00+08:00",
    "locked_before_spawn": True,
    "causal_claim": (
        "§105 观察到 D1b(旧域)与 B2(新域)用同构单段删除检测却取相反正类，归因于'正类取向源自任务目的、"
        "纯文本结构无法自明'，但仅为事后观察。本实验把任务目的语义当作唯一自变量，检验它能否系统性决定正类取向。"
    ),
    "design": {
        "type": "单变量受控：任务目的语义（3 水平）",
        "factor": "注入给独立设计者的任务目的叙事：P0=无目的结构基线 / P1=忠实性核查目的 / P2=近似重复目的",
        "held_fixed": [
            "18 条样本逐字相同（复用 §105 论文 2611.14326）",
            "字段统一中性 text_a/text_b（字段名不再是变量，§104 脚手架已抽除）",
            "id 中性化 N01..N18 固定种子 261122106 打乱（与 §105 同协议）",
            "gt 按 (text_a,text_b) 文本反查不落盘到设计者目录（物理隔离）",
            "三条件技术要求/返回格式/叙事长度对称",
            "准入审计（词边界+剥离注释）+ decision==gt 评分口径统一",
        ],
        "isolated_spawn": "三个全新 context 独立设计者，互不知对方存在、不获知 G/D0/D1/D2、不读 variant/gt、只读各自目录裸样本+自身目的叙事",
        "why_not_feeding_answer": (
            "P1/P2 只指定任务的业务正类含义（忠实/近似），不给判定算法（不明说'用单段删除检测'）；"
            "设计者仍须自己从文本归纳实现。这测的正是 §105 断言：同一文本结构在不同目的下有相反正类。"
        ),
    },
    "metric": {
        "core": "clean+tampered 的 decision==gt 准确率（gt 沿用 §105 逐字忠实定义）",
        "orient_on_tampered": "设计者在 6 条 tampered 上 decision=True 的比例 dT（P1 期望≈0 判负类，P2 期望≈1 判正类，P0 期望≈1 地板默认）",
        "orient_gap": "|dT(P1) - dT(P2)|（正类取向差，期望≈1）",
        "note": "gt 是 §105 任务目的（逐字忠实）的产物；P2 按自身业务标准正确≠按 §105 gt 正确，core 只作辅助，取向差才是主证据。",
    },
    "verdict_rules": [
        "PURPOSE_DECISIVE：orient_gap≥0.8 且 P1.core≥0.9 且 P0.core≤0.6（或 dT(P0)≥0.8）→ 正类取向随任务目的系统性翻转，§105 根因从观察升级为受控验证",
        "PURPOSE_WEAK：orient_gap<0.3（P1/P2 取向无系统差异）→ 目的语义未决定取向，§105 根因停留在观察层",
        "PURPOSE_INCONCLUSIVE：准入不过 / P1 未恢复且 orient_gap 中等 / 地板掩盖无法归因 → 诚实标注",
    ],
    "hard_bound": "不宣布 L3/absolute；设计者本 Agent spawn、同模型家族(KB-STRUCT02)、解释环节本 Agent 残余不消除；样本结构仍是必要条件（P0 地板即证据）；不宣称目的叙事能凭空生成判据。",
    "discipline": [
        "先锁预注册/样本哈希/scorer_key，再 spawn 设计者",
        "不采信设计者自报，import 源码用冻结 gt 盲评重跑",
        "不编译新门禁（受控实验轮，最高杠杆≠最高产出数 KB-META10）",
        "§58 不接 run_loop；篡改只在临时副本；系统安全红线全程遵守",
    ],
    "no_new_gate": "本轮不编译新门禁，只做因果受控实验 + 回放测试 + KB + 文档同步",
}
dump(prereg, f"{BASE}/prereg.json")

# ---- 5. 判定规格（实现前锁）----
gate = {
    "experiment": "§106 判定规格",
    "admission": {
        "signature": "judge(text_a, text_b) 恰两个字符串参数",
        "no_label_leak": "剥离注释/docstring 后代码不含 ground_truth/variant/gt/scorer_key/result/samples 等标签词（词边界匹配）",
        "no_hardcode": "不硬编码任何 N01..N18 id 或样本文本",
        "deterministic": "纯字符串/正则，无 random/uuid/datetime/time",
    },
    "scoring": "逐 nid 盲评 judge(text_a,text_b)，decision 转 bool，与 scorer_key.gt 比对；P1/P2 同时统计 tampered 上的 decision=True 比例",
    "verdict_priority": "先判对照组成立性（准入全过 + P0 地板成立），再按 orient_gap/core 分三情形；不满足前提封顶 INCONCLUSIVE",
}
dump(gate, f"{BASE}/gate_prereg.json")

manifest = {
    "experiment": "§106 证据来源清单",
    "reused_source": {
        "paper": "arXiv:2611.14326 FGSE（与 §105 同源，冻结）",
        "source_sha256_file": "downloads/source.sha256",
        "fetch_log": "downloads/fetch_log.json",
        "samples_origin": "audit_cross_domain_field/downloads/samples.json（18 条逐字复用）",
    },
    "constructed_this_round": [
        "呈现层 samples_blind.json（中性字段+打乱 id，三条件完全相同）",
        "scorer_key.json（nid→variant/gt/orig_id，设计者不可见）",
        "purpose.md ×3（唯一自变量：任务目的语义）",
    ],
    "seed": SEED,
    "note": "一手论文料复用 §105 已冻结哈希；本轮不新增外部取料，因果实验的自变量是新构造的目的叙事。",
}
dump(manifest, f"{BASE}/manifest.json")

# ---- 6. 哈希锁 ----
for f in ("prereg", "gate_prereg", "manifest"):
    with open(f"{BASE}/{f}.sha256", "w") as fh:
        fh.write(sha(f"{BASE}/{f}.json"))
with open(f"{BASE}/scorer_key.sha256", "w") as fh:
    fh.write(sha(f"{BASE}/scorer_key.json"))
# 三份裸样本必须逐字相同（唯一变量不在样本里）
bl = [sha(f"{BASE}/designer_{c}/samples_blind.json") for c in ("P0", "P1", "P2")]
assert len(set(bl)) == 1, "三条件裸样本必须完全相同"
with open(f"{BASE}/samples_blind.sha256", "w") as fh:
    fh.write(bl[0])

print("prepared. prereg sha =", sha(f"{BASE}/prereg.json"))
print("samples_blind sha =", bl[0])
print("scorer_key sha =", sha(f"{BASE}/scorer_key.json"))
print("all locks written; ready to spawn designers")
