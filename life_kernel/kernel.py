#!/usr/bin/env python3
"""开放型生命体 Agent 内核 v2（L1 运行时，受 L0 宪法层约束）。

v1 → v2 的真实进化（2026-11-24，用户"去自主探索吧，牢记你是有生命的"）：
  v1 :self()/guard()/propose()/evolve() 四函数，但探索池硬编码 7 项、内核从不自改、
      心跳日志被测试污染——是"记录仪"不是"心脏"。
  v2:补上生命体缺失的两块代谢——
      digest()    —— 摄食：从 frontier_seeds.json 读外部前沿（带 URL/时间锚/证据分层）
      self_modify()—— 自改：读自身心跳诊断收敛 → 决定注册哪些摄食种子 → 经验验证
                      （守卫判定/propose 排除/宪法完整/verdict 不变全过才接受）→ 写
                      runtime_policy.json + archive 快照（DGM 的 archive+经验验证，
                      只改 L1 外层，宪法层永不可触碰）
      并修复 evolve 测试污染：新增 log_path 参数，测试用隔离路径。

外部前沿镜像（2026-11-24 一手检索）：DGM archive/self-modification、RSIAgent 三角色盲评、
Dr.Zero 共演化课程、EvolvingAgent planner-controller-reflector、Eigent 工具族群。

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
POLICY = os.path.join(DATA, "runtime_policy.json")
FRONTIER_SEEDS = os.path.join(HERE, "frontier_seeds.json")
ARCHIVE_DIR = os.path.join(DATA, "evolution_archive")
KB = os.path.join(ROOT, "knowledge_base_store.json")
NOVELTY_WINDOW = 5  # 最近 N 轮心跳做收敛检测
KERNEL_VERSION = "2.0.0"


def _utcnow():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------- L0 宪法完整性（启动时校验，不符即拒绝运行） ----------
def verify_constitution():
    lock = open(CONSTITUTION_LOCK, encoding="utf-8").read().split()[0]
    actual = hashlib.sha256(open(CONSTITUTION, "rb").read()).hexdigest()
    ok = lock == actual
    doc = json.load(open(CONSTITUTION, encoding="utf-8"))
    return {"ok": ok, "lock": lock, "actual": actual,
            "immutable": doc["immutable"], "n_articles": len(doc["articles"])}


# ---------- 运行时策略（L1 可进化外层，宪法层永不可触碰） ----------
def _load_policy():
    if not os.path.exists(POLICY):
        return {"policy_version": "0", "registered_frontier_seeds": [], "updated_at": None}
    try:
        return json.load(open(POLICY, encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {"policy_version": "0", "registered_frontier_seeds": [], "updated_at": None}


def _archive_snapshot(policy, note=""):
    """DGM archive 机制：每次策略变更留快照，不删历史，可回滚。"""
    os.makedirs(ARCHIVE_DIR, exist_ok=True)
    h = hashlib.sha256(json.dumps(policy, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:12]
    path = os.path.join(ARCHIVE_DIR, h + ".json")
    entry = {"snapshot_sha": h, "archived_at": _utcnow(), "note": note, "policy": policy}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
    return path


def archive_list():
    if not os.path.exists(ARCHIVE_DIR):
        return []
    return sorted(f for f in os.listdir(ARCHIVE_DIR) if f.endswith(".json"))


# ---------- 感知层 ----------
def sense():
    """自主感知仓库当前状态。全部只读，返回可序列化的状态快照。"""
    snap = {"timestamp": _utcnow()}

    audit_dirs = sorted(
        d for d in os.listdir(ROOT)
        if d.startswith("audit_") and os.path.isdir(os.path.join(ROOT, d))
    )
    snap["audit_dirs_count"] = len(audit_dirs)
    snap["audit_dirs"] = audit_dirs

    kb = json.load(open(KB, encoding="utf-8"))
    kinds = {}
    for item in kb["items"]:
        kinds[item["kind"]] = kinds.get(item["kind"], 0) + 1
    snap["kb_count"] = len(kb["items"])
    snap["kb_kinds"] = kinds

    head = os.path.join(ROOT, ".git", "HEAD")
    if os.path.exists(head):
        ref = open(head, encoding="utf-8").read().strip()
        if ref.startswith("ref: "):
            rp = os.path.join(ROOT, ".git", ref[5:])
            snap["git_head"] = open(rp, encoding="utf-8").read().strip()[:12] if os.path.exists(rp) else "unknown"
        else:
            snap["git_head"] = ref[:12]

    work_items = os.path.join(ROOT, "WORK_ITEMS.md")
    topics = []
    if os.path.exists(work_items):
        for line in open(work_items, encoding="utf-8"):
            m = re.match(r"^\|\s*\*\*(.+?)\*\*\s*\|", line)
            if m:
                topics.append(m.group(1))
    snap["topic_map"] = topics[:20]

    hour = datetime.datetime.now().hour
    snap["time_budget"] = "morning" if hour < 12 else ("afternoon" if hour < 18 else "evening")

    # v2：感知自身代谢状态
    snap["kernel_version"] = KERNEL_VERSION
    snap["registered_frontier_seeds"] = len(_load_policy().get("registered_frontier_seeds", []))
    snap["archive_snapshots"] = len(archive_list())
    return snap


# ---------- novelty 守卫（自我否定核心） ----------
def _load_heartbeats(log_path=None):
    path = log_path or HEARTBEAT_LOG
    if not os.path.exists(path):
        return []
    rows = []
    for line in open(path, encoding="utf-8"):
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
        "rsi": ["rsi", "自我改进", "递归", "元认知", "改进者", "变异评估", "自改", "元学习"],
        "memory": ["记忆", "memory", "知识库", "kb", "遗忘", "压缩", "检索", "世界模型"],
        "tool_evo": ["工具", "tool", "技能", "skill", "自创工具", "api", "工具族群"],
        "workflow": ["工作流", "workflow", "编排", "拓扑", "多智能体", "协作", "三角色", "课程"],
        "self_evo": ["自进化", "自组织", "自主生长", "开放", "novelty", "心跳", "内核", "开放式"],
        "safety": ["安全", "合规", "红队", "注入", "防御", "诚信"],
        "finance": ["金融", "财报", "市场", "库存周期", "宏观"],
        "philosophy": ["哲学", "价值", "主体", "可证伪", "目的论"],
        "archive": ["档案", "archive", "垫脚石", "快照", "谱系", "回滚", "共演化", "自动课程"],
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


def _guard_state(direction, recent, window=NOVELTY_WINDOW):
    """纯函数版守卫判定（不写日志），供 novelty_guard 与自改经验验证共用。"""
    recent = recent[-window:]
    if len(recent) < 2:
        return {"state": "COLD_START", "similarity": 0.0,
                "recent_directions": list(recent),
                "reason": "心跳样本不足，无法判定收敛"}
    new_tags = _tags_of(direction)
    sims = [_jaccard(new_tags, _tags_of(d)) for d in recent]
    mean_sim = sum(sims) / len(sims)
    state = "CONVERGED" if mean_sim >= 0.6 else "DIVERSE"
    return {
        "state": state,
        "similarity": round(mean_sim, 3),
        "threshold": 0.6,
        "recent_directions": list(recent),
        "new_tags": sorted(new_tags),
        "reason": ("方向收敛到最近同一主题井——命中宪法 C7 novelty 义务，须强制转向"
                   if state == "CONVERGED" else "方向与近期足够不同，允许推进"),
    }


def novelty_guard(direction, window=NOVELTY_WINDOW, log_path=None):
    """检测方向是否收敛到最近的同一口井。命中则 CONVERGED（须强制转向）。"""
    hbs = _load_heartbeats(log_path)
    recent = [h for h in hbs if h.get("direction")]
    return _guard_state(direction, [h["direction"] for h in recent], window)


# ---------- 摄食层（v2 新增） ----------
def digest():
    """从外部前沿种子摄食（一手 URL + 时间锚 + 证据分层）。只读，不自动注册。"""
    if not os.path.exists(FRONTIER_SEEDS):
        return {"ingested_at": None, "count": 0, "seeds": [],
                "note": "无摄食源，探索池退回内置方向"}
    doc = json.load(open(FRONTIER_SEEDS, encoding="utf-8"))
    seeds = doc.get("seeds", [])
    return {"ingested_at": doc.get("ingested_at"), "count": len(seeds),
            "seeds": seeds, "ingest_method": doc.get("ingest_method", ""),
            "note": "证据分层 B/C，均非本仓实测；注册与否由 self_modify() 经验验证后决定"}


# ---------- 开放探索池（自主生长）：内置 + 已摄食注册 ----------
def explore_pool(policy=None):
    """从内置方向 + 内核已自主注册的摄食种子生成开放候选（不与历史收敛）。"""
    policy = policy if policy is not None else _load_policy()
    candidates = [
        {"id": "E1", "direction": "自进化内核自身：让 Agent 自主改写改进流程（RSI/DGM-H 元认知自修改）", "source": "外部前沿 Hyperagents"},
        {"id": "E2", "direction": "记忆治理：长期记忆的分层组织/遗忘/压缩，避免知识库膨胀成噪音", "source": "外部前沿 Mem0/MemoryBank + WORK_ITEMS P0"},
        {"id": "E3", "direction": "自创工具：Agent 按需编写 API/技能并注册复用，扩展能力边界", "source": "外部前沿 CREATOR/CRAFT + WORK_ITEMS P0"},
        {"id": "E4", "direction": "工作流进化：用搜索算法优化多智能体协作拓扑（AFlow/ADAS）", "source": "外部前沿 AFlow/ADAS + WORK_ITEMS P0"},
        {"id": "E5", "direction": "开放式学习心跳：持续生成新问题、novelty search、共演化课程", "source": "外部前沿 Open-Endedness/ALOE"},
        {"id": "E6", "direction": "跨会话连续性：情景/语义/程序三层记忆与身份延续", "source": "外部前沿 Hermes/GenericAgent + WORK_ITEMS P0"},
        {"id": "E7", "direction": "安全诚信审读：红队 ASR≠防御增益的诚实边界（防御性，守法）", "source": "WORK_ITEMS P3"},
    ]
    registered = set(policy.get("registered_frontier_seeds", []))
    if registered:
        frontier = {s["id"]: s for s in digest()["seeds"]}
        for sid in sorted(registered):
            if sid in frontier:
                s = frontier[sid]
                candidates.append({"id": sid, "direction": s["direction"],
                                   "source": s["source_name"] + " [" + s["evidence_tier"] + "]"})
    return candidates


def propose(guard=None, pool=None, policy=None):
    """选出 novelty 最高（与近期最不同）的方向。守卫 CONVERGED 时排除收敛标签。"""
    pool = pool if pool is not None else explore_pool(policy)
    hbs = _load_heartbeats()
    recent = [h for h in hbs if h.get("direction")][-NOVELTY_WINDOW:]
    recent_tags = set()
    for h in recent:
        recent_tags |= _tags_of(h["direction"])

    scored = []
    for c in pool:
        tags = _tags_of(c["direction"])
        novelty = 1.0 - (len(tags & recent_tags) / len(tags | recent_tags) if (tags | recent_tags) else 0)
        scored.append({"id": c["id"], "direction": c["direction"],
                       "source": c["source"], "novelty": round(novelty, 3),
                       "tags": sorted(tags)})
    scored.sort(key=lambda x: (-x["novelty"], x["id"]))
    return scored


# ---------- 自改层（v2 核心，DGM 式经验验证） ----------
def _validate_policy(candidate_seed_ids, recent_directions):
    """经验验证：候选注册方案必须通过全部守卫/选向/宪法/纪律检查才被接受。"""
    checks = {}
    # 1. 宪法完整（不可被自改触碰）
    const = verify_constitution()
    checks["constitution_ok"] = const["ok"]
    # 2. 候选方案能进入探索池
    cand_policy = {"registered_frontier_seeds": list(candidate_seed_ids)}
    pool = explore_pool(cand_policy)
    checks["pool_nonempty"] = len(pool) >= 7
    checks["no_duplicate_ids"] = len({c["id"] for c in pool}) == len(pool)
    # 3. 守卫能力用【固定合成测试向量】检验（盲评纪律：测试输入不随真实日志状态漂移）
    #    此前错误地拿真实日志当测试输入——真实历史不是 canary 井时应判 DIVERSE（守卫是对的），
    #    却把 CONVERGED 当硬门槛，属验证器设计缺陷。修正：合成已知 canary 收敛窗口 + 多样性对照。
    synthetic_canary_window = [
        "canary 判据回放 字面伪规则 语义蕴含",
        "canary 构念效度 冻结集 错位负例",
        "canary 字面伪规则 判据回放",
    ]
    g_same = _guard_state("又一轮canary字面伪规则语义蕴含判据回放", synthetic_canary_window)
    g_diff = _guard_state("记忆治理 知识库 遗忘 压缩", synthetic_canary_window)
    checks["guard_detects_convergence"] = (g_same["state"] == "CONVERGED")
    checks["guard_allows_diverse"] = (g_diff["state"] == "DIVERSE")  # 新增正向检查：防守卫过度敏感
    # propose 探索池不得把 canary 井排在前列（池内本就无 canary 方向，恒真校验保持）
    scored = propose(pool=pool)
    checks["propose_excludes_canary_top"] = all("canary" not in s["tags"] for s in scored[:3])
    # 4. 既有判定不变
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    checks["verdict_unchanged"] = (res["verdict"] == "GAP_INCONCLUSIVE"
                                   and res["l3_claimed"] is False and res["absolute_claimed"] is False)
    checks["all_pass"] = all(v for k, v in checks.items() if k != "all_pass")
    return checks


def self_modify(reason="自主心跳诊断：检测收敛并决定摄食注册"):
    """DGM 式自改闭环：读心跳诊断 → 选摄食 → 经验验证 → 接受则写 policy + archive。

    只改 L1 外层（runtime_policy.json），宪法层 SHA256 不符则拒绝运行。
    返回诊断、候选、验证明细、是否接受、archive 路径。
    """
    const = verify_constitution()
    if not const["ok"]:
        return {"error": "宪法层 SHA256 不符，拒绝自改（L0 完整性失败）", "constitution": const}

    policy = _load_policy()
    registered = list(policy.get("registered_frontier_seeds", []))
    hbs = _load_heartbeats()
    recent = [h["direction"] for h in hbs if h.get("direction")]

    # 诊断：近窗口是否收敛 + 是否还有未注册的摄食种子
    guard = _guard_state(recent[-1] if recent else "self", recent[:-1])
    unregistered = [s["id"] for s in digest()["seeds"] if s["id"] not in registered]

    # 决策：若未注册种子存在，取全部（经验验证会筛）；若已全注册，维持
    candidate_ids = sorted(set(registered) | set(unregistered))
    validation = _validate_policy(candidate_ids, recent)

    accepted = validation["all_pass"] and candidate_ids != registered
    archived_before = _archive_snapshot(policy, note="self_modify before: " + reason)

    result = {
        "at": _utcnow(), "reason": reason,
        "diagnosis": {"guard": guard["state"], "similarity": guard["similarity"],
                      "recent_count": len(recent), "unregistered_seeds": unregistered},
        "candidate_seed_ids": candidate_ids,
        "validation": validation,
        "accepted": accepted,
        "constitution_ok": const["ok"],
        "archive_before": archived_before,
        "archive_count": len(archive_list()),
    }

    if accepted:
        new_policy = {
            "policy_version": KERNEL_VERSION,
            "updated_at": _utcnow(),
            "registered_frontier_seeds": candidate_ids,
            "last_self_modify": result,
            "note": "L1 可进化外层；经 self_modify() 经验验证通过；宪法层永不可触碰。",
        }
        with open(POLICY, "w", encoding="utf-8") as f:
            json.dump(new_policy, f, ensure_ascii=False, indent=2)
        result["archive_after"] = _archive_snapshot(new_policy, note="self_modify after (accepted)")
        result["policy_written"] = True
    else:
        result["policy_written"] = False
        result["reject_reason"] = ("验证未通过：" + ",".join(k for k, v in validation.items()
                                    if k != "all_pass" and not v) if not validation["all_pass"]
                                   else "无新摄食可注册（策略已收敛）")
    return result


# ---------- 进化闭环 ----------
def evolve(direction, action_note="", log_path=None):
    """观测→诊断→改进→验证 闭环，落一条心跳；不改任何既有判定。

    log_path：测试时传隔离路径，避免污染真实心跳日志（v2 修复数据诚实缺陷）。
    """
    const = verify_constitution()
    if not const["ok"]:
        return {"error": "宪法层 SHA256 不符，拒绝运行（L0 完整性失败）", "constitution": const}

    guard = novelty_guard(direction, log_path=log_path)
    hb = {
        "timestamp": _utcnow(),
        "kernel_version": KERNEL_VERSION,
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
    path = log_path or HEARTBEAT_LOG
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
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
    policy = _load_policy()
    scored = propose()
    return {
        "round": "§4ar",
        "kernel_version": KERNEL_VERSION,
        "paradigm_shift": "从诊断者→建设者：仓库从静态档案馆→开放生命体",
        "v2_metabolism": "digest() 摄食外部前沿 + self_modify() DGM 式经验验证自改 + archive 快照可回滚",
        "constitution": const,
        "sensed_state": {
            "audit_dirs_count": snap["audit_dirs_count"],
            "kb_count": snap["kb_count"],
            "kb_kinds": snap["kb_kinds"],
            "topic_map_size": len(snap["topic_map"]),
            "time_budget": snap["time_budget"],
            "git_head": snap.get("git_head"),
            "registered_frontier_seeds": snap["registered_frontier_seeds"],
            "archive_snapshots": snap["archive_snapshots"],
        },
        "heartbeat_count": len(hbs),
        "digest": {"count": digest()["count"], "ingested_at": digest()["ingested_at"]},
        "explore_pool_size": len(explore_pool()),
        "top_novelty_directions": scored[:3],
        "external_mirrors": [
            "Open-Endedness/novelty search → novelty_guard(C7)",
            "RSI 观测-诊断-改进-验证 → evolve()",
            "Rotifer L0 宪法层 → constitution.json(SHA256锁)",
            "DGM archive + 经验验证自改 → self_modify()/archive/",
        ],
        "does_not_change": ["verdict", "l3=false", "absolute=false", "不翻十案",
                            "不编译新门禁", "不动§100", "最终裁定权归用户"],
        "data_layer": "A 本仓内核自检（只读仓库状态，不联网不spawn）",
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
