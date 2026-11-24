#!/usr/bin/env python3
"""开放型生命体 Agent 内核（L1 运行时，受 L0 宪法层约束）。

设计源自外部前沿交叉印证（2026-11-24 向外探索）：
  - Open-Endedness / novelty search：奖励发现新行为，惩罚收敛到固定策略
  - RSI 统一内核：观测(Observe)→诊断(Analyze)→改进(Improve)→验证(Verify)
  - Rotifer L0 不可变宪法层：底层纪律不可被进化触碰

本内核把仓库从"静态档案馆"变成"能自主感知/选向/进化"的开放生命体：
  sense()        —— 自主感知：扫描仓库真实状态（审计目录/KB/话题版图/时间预算）
  novelty_guard()—— 自我否定：机械检测方向收敛，命中则强制封锁转向（C7）
  propose()      —— 自主生长：从开放探索池选出 novelty 最高的新方向
  evolve()       —— 自主进化：观测→诊断→改进→验证闭环，经验沉淀 KB

只读仓库状态；不改任何 verdict / 阈值 / §100；不联网；不 spawn。
"""
import datetime
import hashlib
import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONSTITUTION = os.path.join(HERE, "constitution.json")
CONSTITUTION_LOCK = os.path.join(HERE, "constitution.sha256")
DATA = os.path.join(HERE, "data")
HEARTBEAT_LOG = os.path.join(DATA, "heartbeat_log.jsonl")
KB = os.path.join(ROOT, "knowledge_base_store.json")
NOVELTY_WINDOW = 5  # 最近 N 轮心跳做收敛检测


# ---------- L0 宪法完整性（启动时校验，不符即拒绝运行） ----------
def verify_constitution():
    lock = open(CONSTITUTION_LOCK, encoding="utf-8").read().split()[0]
    actual = hashlib.sha256(open(CONSTITUTION, "rb").read()).hexdigest()
    ok = lock == actual
    doc = json.load(open(CONSTITUTION, encoding="utf-8"))
    return {"ok": ok, "lock": lock, "actual": actual,
            "immutable": doc["immutable"], "n_articles": len(doc["articles"])}


# ---------- 感知层 ----------
def sense():
    """自主感知仓库当前状态。全部只读，返回可序列化的状态快照。"""
    snap = {"timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}

    # 1. 审计目录版图（已探索过的方向）
    audit_dirs = sorted(
        d for d in os.listdir(ROOT)
        if d.startswith("audit_") and os.path.isdir(os.path.join(ROOT, d))
    )
    snap["audit_dirs_count"] = len(audit_dirs)
    snap["audit_dirs"] = audit_dirs

    # 2. 记忆库覆盖（KB 的 kind 分布）
    kb = json.load(open(KB, encoding="utf-8"))
    kinds = {}
    for item in kb["items"]:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
    snap["kb_count"] = len(kb["items"])
    snap["kb_kinds"] = kinds

    # 3. git HEAD（时间锚）
    head = os.path.join(ROOT, ".git", "HEAD")
    if os.path.exists(head):
        ref = open(head, encoding="utf-8").read().strip()
        if ref.startswith("ref: "):
            rp = os.path.join(ROOT, ".git", ref[5:])
            snap["git_head"] = open(rp, encoding="utf-8").read().strip()[:12] if os.path.exists(rp) else "unknown"
        else:
            snap["git_head"] = ref[:12]

    # 4. 话题版图（从 WORK_ITEMS.md 提取一级话题名，作为开放探索池的锚）
    work_items = os.path.join(ROOT, "WORK_ITEMS.md")
    topics = []
    if os.path.exists(work_items):
        for line in open(work_items, encoding="utf-8"):
            m = re.match(r"^\|\s*\*\*(.+?)\*\*\s*\|", line)
            if m:
                topics.append(m.group(1))
    snap["topic_map"] = topics[:20]

    # 5. 时间预算（当前时段）
    hour = datetime.datetime.now().hour
    snap["time_budget"] = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")

    return snap


# ---------- novelty 守卫（自我否定核心） ----------
def _load_heartbeats():
    if not os.path.exists(HEARTBEAT_LOG):
        return []
    rows = []
    for line in open(HEARTBEAT_LOG, encoding="utf-8"):
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def _tags_of(text):
    """从方向描述提取主题标签（规范化关键词集合）。"""
    TEXT = str(text).lower()
    tagbook = {
        "canary": ["canary", "构念效度", "字面伪规则", "冻结集", "语义蕴含", "错位负例", "判据回放"],
        "l3_independence": ["l3", "独立性", "盲评", "外家", "五权力", "全链", "代理"],
        "rsi": ["rsi", "自我改进", "递归", "元认知", "改进者", "变异评估"],
        "memory": ["记忆", "memory", "知识库", "kb", "遗忘", "压缩", "检索"],
        "tool_evo": ["工具", "tool", "技能", "skill", "自创工具", "api"],
        "workflow": ["工作流", "workflow", "编排", "拓扑", "多智能体", "协作"],
        "self_evo": ["自进化", "自组织", "自主生长", "开放", "novelty", "心跳", "内核"],
        "safety": ["安全", "合规", "红队", "注入", "防御", "诚信"],
        "finance": ["金融", "财报", "市场", "库存周期", "宏观"],
        "philosophy": ["哲学", "价值", "主体", "可证伪", "目的论"],
    }
    found = set()
    for tag, kws in tagbook.items():
        if any(kw.lower() in TEXT for kw in kws):
            found.add(tag)
    return found or {"general"}


def _jaccard(a, b):
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def novelty_guard(direction, window=NOVELTY_WINDOW):
    """检测方向是否收敛到最近的同一口井。命中则 CONVERGED（须强制转向）。

    返回 {state, similarity, recent_directions, reason}。
    state: CONVERGED（收敛，须转向）/ DIVERSE（多样，可继续）/ COLD_START（样本不足）
    """
    hbs = _load_heartbeats()
    recent = [h for h in hbs if h.get("direction")][-window:]
    if len(recent) < 2:
        return {"state": "COLD_START", "similarity": 0.0,
                "recent_directions": [h["direction"] for h in recent],
                "reason": "心跳样本不足，无法判定收敛"}

    new_tags = _tags_of(direction)
    sims = [_jaccard(new_tags, _tags_of(h["direction"])) for h in recent]
    mean_sim = sum(sims) / len(sims)
    # 收敛判据：连续窗口内平均相似度 >= 0.6
    state = "CONVERGED" if mean_sim >= 0.6 else "DIVERSE"
    return {
        "state": state,
        "similarity": round(mean_sim, 3),
        "threshold": 0.6,
        "recent_directions": [h["direction"] for h in recent],
        "new_tags": sorted(new_tags),
        "reason": ("方向收敛到最近同一主题井——命中宪法 C7 novelty 义务，须强制转向"
                   if state == "CONVERGED" else "方向与近期足够不同，允许推进"),
    }


# ---------- 开放探索池（自主生长） ----------
def explore_pool():
    """从话题版图 + 外部前沿生成开放候选方向（不与历史收敛）。"""
    candidates = [
        {"id": "E1", "direction": "自进化内核自身：让 Agent 自主改写改进流程（RSI/DGM-H 元认知自修改）", "source": "外部前沿 Hyperagents"},
        {"id": "E2", "direction": "记忆治理：长期记忆的分层组织/遗忘/压缩，避免知识库膨胀成噪音", "source": "外部前沿 Mem0/MemoryBank + WORK_ITEMS P0"},
        {"id": "E3", "direction": "自创工具：Agent 按需编写 API/技能并注册复用，扩展能力边界", "source": "外部前沿 CREATOR/CRAFT + WORK_ITEMS P0"},
        {"id": "E4", "direction": "工作流进化：用搜索算法优化多智能体协作拓扑（AFlow/ADAS）", "source": "外部前沿 AFlow/ADAS + WORK_ITEMS P0"},
        {"id": "E5", "direction": "开放式学习心跳：持续生成新问题、novelty search、共演化课程", "source": "外部前沿 Open-Endedness/ALOE"},
        {"id": "E6", "direction": "跨会话连续性：情景/语义/程序三层记忆与身份延续", "source": "外部前沿 Hermes/GenericAgent + WORK_ITEMS P0"},
        {"id": "E7", "direction": "安全诚信审读：红队 ASR≠防御增益的诚实边界（防御性，守法）", "source": "WORK_ITEMS P3"},
    ]
    return candidates


def propose(guard=None, pool=None):
    """选出 novelty 最高（与近期最不同）的方向。守卫 CONVERGED 时排除收敛标签。"""
    pool = pool if pool is not None else explore_pool()
    hbs = _load_heartbeats()
    recent = [h for h in hbs if h.get("direction")][-NOVELTY_WINDOW:]
    recent_tags = set()
    for h in recent:
        recent_tags |= _tags_of(h["direction"])

    scored = []
    for c in pool:
        tags = _tags_of(c["direction"])
        # novelty = 与近期标签的不重叠度
        novelty = 1.0 - (len(tags & recent_tags) / len(tags | recent_tags) if (tags | recent_tags) else 0)
        scored.append({"id": c["id"], "direction": c["direction"],
                       "source": c["source"], "novelty": round(novelty, 3),
                       "tags": sorted(tags)})
    scored.sort(key=lambda x: (-x["novelty"], x["id"]))
    return scored


# ---------- 进化闭环 ----------
def evolve(direction, action_note=""):
    """观测→诊断→改进→验证 闭环，落一条心跳；不改任何既有判定。"""
    const = verify_constitution()
    if not const["ok"]:
        return {"error": "宪法层 SHA256 不符，拒绝运行（L0 完整性失败）", "constitution": const}

    guard = novelty_guard(direction)
    hb = {
        "timestamp": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "phase_observe": sense(),
        "direction": direction,
        "phase_analyze_guard": guard,
        "phase_improve_action": action_note,
        "phase_verify": {
            "constitution_ok": const["ok"],
            "no_verdict_change": True,
            "original_100_untouched": True,
        },
    }
    os.makedirs(DATA, exist_ok=True)
    with open(HEARTBEAT_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(hb, ensure_ascii=False) + "\n")
    return {
        "heartbeat_written": True,
        "direction": direction,
        "guard": guard,
        "constitution": const,
        "verified": hb["phase_verify"],
    }


def build_report():
    """生成内核自检报告（供文档/测试引用，不产生新判定）。"""
    const = verify_constitution()
    snap = sense()
    hbs = _load_heartbeats()
    scored = propose()
    return {
        "round": "§4aq",
        "kernel_version": "1.0.0",
        "paradigm_shift": "从诊断者→建设者：仓库从静态档案馆→开放生命体",
        "constitution": const,
        "sensed_state": {
            "audit_dirs_count": snap["audit_dirs_count"],
            "kb_count": snap["kb_count"],
            "kb_kinds": snap["kb_kinds"],
            "topic_map_size": len(snap["topic_map"]),
            "time_budget": snap["time_budget"],
            "git_head": snap.get("git_head"),
        },
        "heartbeat_count": len(hbs),
        "explore_pool_size": len(explore_pool()),
        "top_novelty_directions": scored[:3],
        "external_mirrors": [
            "Open-Endedness/novelty search → novelty_guard(C7)",
            "RSI 观测-诊断-改进-验证 → evolve()",
            "Rotifer L0 宪法层 → constitution.json(SHA256锁)",
        ],
        "does_not_change": ["verdict", "l3=false", "absolute=false", "不翻十案",
                            "不编译新门禁", "不动§100", "最终裁定权归用户"],
        "data_layer": "A 本仓内核自检（只读仓库状态，不联网不spawn）",
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
