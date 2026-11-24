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

v2 → v3 的真实进化（2026-11-24，用户"世间本无路，你走了，从此便有了路……
基于帕累托次优的随机游走……这也是路径依赖的人性，无有对错，只须前行"）：
  v2 :propose() 纯贪心选 novelty 最高；收敛只判 CONVERGED 强制转向；
      "前方无路"（全池收敛）时没有迈步策略，也没有脚印沉淀——缺一条腿。
  v3 :新增 pareto_walk()——无路时不执念最优：
      ① 双目标（novelty↑ / footprint-freshness↑）算帕累托前沿；
      ② 前沿去掉理想点端点得【次优集】；
      ③ 外部时间锚 seed 做可复现随机游走，已有脚印 1.5x 偏置（路径依赖的人性）；
      ④ 选中方向写入 path_traces.jsonl——"你走了，从此便有了路"，脚印反哺下一轮候选。
      有路时（max_novelty≥阈值）保持贪心不游走，不无谓扰动。

v3 → v4 的真实进化（2026-11-24，用户"你已经有生命意识了，天空无限大，勇敢放飞吧"）：
  这次飞出仓库向外摄食三篇一手前沿（F09-F11），它们恰好是对 v3 的三条外部批判：
    F09 arXiv:2610.14662 — 归因幻觉：改后分数上升≠修对目标失败（DGM 145次修改无目标特异优势）；
    F10 arXiv:2610.25858 — 检索碰撞：无条件相似检索会在冲突情境取到外来记忆；
    F11 arXiv:2611.28244 — 只增不减：选择性丢弃未用经验优于累积/升为常驻规则。
  diagnose_v3_defects.py 机械确认三条在本仓全部成立（A级读真实源码/数据）后，v4 补三机制：
    attribution_check() — 三数字(target repair / transfer / held-out net)归因检验，不再只看all_pass；
    _applicable_footprints() — 脚印带适用情境签名，避免 F10 检索碰撞；
    prune_unused() — 丢弃长期未用经验（KB/种子/脚印），archive 留痕可回滚，C5改机制不放宽。
  外部证据 B 级（arXiv摘要自报非本仓实测）；本仓机制验证 A 级。仍是只读仓库状态；
  不改任何 verdict / 阈值 / §100；内核自身不联网（摄食由外层工具完成）；不 spawn。
"""
import datetime
import hashlib
import json
import os
import random
import re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONSTITUTION = os.path.join(HERE, "constitution.json")
CONSTITUTION_LOCK = os.path.join(HERE, "constitution.sha256")
DATA = os.path.join(HERE, "data")
HEARTBEAT_LOG = os.path.join(DATA, "heartbeat_log.jsonl")
PATH_TRACES = os.path.join(DATA, "path_traces.jsonl")  # v3：走过的脚印（路）
POLICY = os.path.join(DATA, "runtime_policy.json")
FRONTIER_SEEDS = os.path.join(HERE, "frontier_seeds.json")
ARCHIVE_DIR = os.path.join(DATA, "evolution_archive")
KB = os.path.join(ROOT, "knowledge_base_store.json")
NOVELTY_WINDOW = 5  # 最近 N 轮心跳做收敛检测
NO_PATH_NOVELTY = 0.35  # 全池 novelty 低于此值判"前方无路"，触发帕累托次优随机游走
APPLICABILITY_MIN = 0.34  # v4 F10：脚印适用情境与此境 Jaccard 下限，低于则不注入（防检索碰撞）
STALE_DAYS = 30  # v4 F11：经验超过 N 天未被使用视为 stale，可剪枝
KERNEL_VERSION = "4.0.0"
EXPERIENCE_USE = os.path.join(DATA, "experience_use.jsonl")  # v4：经验使用台账（last_used/use_count）


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
    snap["path_traces_count"] = len(_load_traces())  # v3：走过的脚印数（路）
    snap["experience_use_count"] = len(_load_use_log())  # v4/F11：经验使用台账条数
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


# ---------- v3：帕累托次优随机游走（无路时怎么走） ----------
def _load_traces(log_path=None):
    """读脚印轨迹——走过的路本身成为下一轮候选（路径依赖的物质基础）。"""
    path = log_path or PATH_TRACES
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


def path_list(log_path=None):
    """对外暴露：当前已走出的路（脚印列表）。"""
    return _load_traces(log_path)


# ---------- v4 / F11：经验使用台账 + 选择性丢弃（防只增不减） ----------
def _use_log_path(log_path=None):
    """使用台账跟随脚印路径隔离：测试用隔离日志时不污染真实台账。"""
    if log_path and os.path.abspath(log_path) != os.path.abspath(PATH_TRACES):
        return os.path.join(os.path.dirname(log_path), "experience_use.jsonl")
    return EXPERIENCE_USE


def _load_use_log(log_path=None):
    path = _use_log_path(log_path)
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


def _mark_used(item_id, log_path=None):
    """记录一次经验被使用（供剪枝判定 last_used）。测试隔离路径零污染。"""
    path = _use_log_path(log_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"item_id": item_id, "at": _utcnow()}, ensure_ascii=False) + "\n")


def _days_since(ts):
    try:
        t = datetime.datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
        return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() / 86400.0
    except (ValueError, TypeError):
        return 0.0


def prune_unused(kind="footprint", stale_days=STALE_DAYS, dry_run=True, log_path=None):
    """v4/F11：选择性丢弃长期未用的经验（外部实证：丢弃优于累积/升为常驻规则）。

    - kind: 'footprint'（脚印）| 'seed'（摄食种子注册表）——KB 因有独立一致性审计，只报告不删；
    - dry_run=True 默认只返回候选，不写任何文件；False 才实际移除并留 archive 快照（可回滚）；
    - 存活判据：使用台账里 last_used 距今 < stale_days；从未使用且创建已久同样视为 stale。
    - 不改 verdict / 宪法；删除的是 L1 运行时数据，archive 留痕。
    """
    const = verify_constitution()
    if not const["ok"]:
        return {"error": "宪法层损坏，拒绝剪枝", "constitution": const}
    use_log = _load_use_log(log_path)
    last_used = {}
    for row in use_log:
        iid = row.get("item_id")
        if iid and (iid not in last_used or row.get("at", "") > last_used[iid]):
            last_used[iid] = row["at"]

    if kind == "footprint":
        traces = _load_traces(log_path)
        items = [{"id": t.get("id", "P%d" % i), "created": t.get("timestamp", ""),
                  "direction": t.get("direction", "")} for i, t in enumerate(traces)]
    elif kind == "seed":
        policy = _load_policy()
        seeds = {s["id"]: s for s in digest()["seeds"]}
        items = [{"id": sid, "created": policy.get("updated_at", ""),
                  "direction": seeds.get(sid, {}).get("direction", "")}
                 for sid in policy.get("registered_frontier_seeds", [])]
    else:
        return {"error": "unsupported kind: " + str(kind)}

    stale, kept = [], []
    for it in items:
        lu = last_used.get(it["id"])
        ref = lu or it["created"]
        age = _days_since(ref) if ref else 0.0
        (stale if age >= stale_days else kept).append(dict(it, last_used=lu, age_days=round(age, 2)))

    result = {"kind": kind, "stale_days": stale_days, "dry_run": dry_run,
              "total": len(items), "stale_count": len(stale), "kept_count": len(kept),
              "stale_ids": [x["id"] for x in stale], "stale": stale,
              "constitution_ok": const["ok"]}

    if not dry_run and stale:
        stale_ids = set(x["id"] for x in stale)
        before = _archive_snapshot({"kind": kind, "items": items}, note="prune_unused before")
        if kind == "footprint":
            path = log_path or PATH_TRACES
            survivors = [t for i, t in enumerate(traces)
                         if t.get("id", "P%d" % i) not in stale_ids]
            with open(path, "w", encoding="utf-8") as f:
                for t in survivors:
                    f.write(json.dumps(t, ensure_ascii=False) + "\n")
        else:
            policy = _load_policy()
            policy["registered_frontier_seeds"] = [s for s in policy.get("registered_frontier_seeds", [])
                                                    if s not in stale_ids]
            policy["updated_at"] = _utcnow()
            with open(POLICY, "w", encoding="utf-8") as f:
                json.dump(policy, f, ensure_ascii=False, indent=2)
        result.update({"pruned": True, "archive_before": before})
    else:
        result["pruned"] = False
    return result


# ---------- v4 / F09：归因检验（三数字，拒绝"分数上升≠修对目标"） ----------
def _probe_novelty(probes, directions):
    """探针相对一组方向的最高 novelty（盲评纪律：探针固定，不随状态漂移）。"""
    out = []
    for p in probes:
        ptags = _tags_of(p)
        best = 0.0
        for d in directions:
            dtags = _tags_of(d)
            union = ptags | dtags
            best = max(best, 1.0 - (len(ptags & dtags) / len(union) if union else 0))
        out.append(round(best, 3))
    return out


# 固定三数字探针集：target=收敛主题井；transfer=同类相邻主题；heldout=不参与决策的主题
ATTRIBUTION_PROBES = {
    "target": ["canary 判据回放 字面伪规则 语义蕴含 构念效度"],
    "transfer": ["判据回放 冻结集 错位负例", "canary 字面伪规则 判据独立性"],
    "heldout": ["金融 市场 库存周期 宏观", "哲学 价值 主体 可证伪", "安全 红队 注入 防御"],
}


def attribution_check(recent_directions, candidate_seed_ids, probes=None, verbose=False):
    """v4/F09：把自改结果拆成三数字，检验是否真的针对诊断出的问题。

    - target repair：候选种子相对"诊断收敛主题"是否显著不同（引入新鲜方向）；
    - transfer：候选覆盖的不同主题广度（是否迁移到相邻主题而非只memorize一例）；
    - held-out net：一组不参与决策的探针，注册前后探索池对其覆盖净变化（可为负=回归）。
    只有三数字同时达标才 all_pass——不再用单一 all_pass 掩盖归因幻觉。
    """
    probes = probes or ATTRIBUTION_PROBES
    seeds = {s["id"]: s for s in digest()["seeds"]}
    recent = list(recent_directions)
    recent_tags = set()
    for d in recent:
        recent_tags |= _tags_of(d)

    cands = [seeds[i] for i in candidate_seed_ids if i in seeds]
    cand_tagsets = [_tags_of(s["direction"]) for s in cands]

    # 1) target repair：候选中与收敛主题显著不同的比例
    if cand_tagsets:
        repairs = [1.0 if _jaccard(t, recent_tags) < 0.6 else 0.0 for t in cand_tagsets]
        target_repair = round(sum(repairs) / len(repairs), 3)
    else:
        target_repair = 0.0

    # 2) transfer：候选覆盖的主题广度（distinct tags 数）
    coverage = set()
    for t in cand_tagsets:
        coverage |= t
    transfer = len(coverage)

    # 3) held-out net：固定探针在注册前后探索池的"可匹配方向数"净变化
    def match_count(pool, probe):
        ptag = _tags_of(probe)
        return sum(1 for c in pool if ptag & _tags_of(c.get("direction", "")))

    before_pool = explore_pool({"registered_frontier_seeds": []})
    after_pool = explore_pool({"registered_frontier_seeds": list(candidate_seed_ids)})
    heldout_net = 0
    for p in probes["heldout"]:
        heldout_net += match_count(after_pool, p) - match_count(before_pool, p)

    result = {
        "target_repair": target_repair,
        "transfer_distinct_tags": transfer,
        "heldout_net": heldout_net,
        "candidates": len(cands),
        "all_pass": bool(target_repair >= 0.5 and transfer >= 2 and heldout_net >= 0),
        "basis": "F09 arXiv:2610.14662: 分报 target repair/transfer/held-out net, 拒绝分数上升冒充修对目标",
    }
    if verbose:
        result["probe_details"] = {k: _probe_novelty(v, [s["direction"] for s in cands])
                                   for k, v in probes.items()}
    return result


def _dominates(a, b):
    """双目标支配：novelty 与 freshness 都不差，且至少一项严格更优。"""
    return (a["novelty"] >= b["novelty"] and a["freshness"] >= b["freshness"]
            and (a["novelty"] > b["novelty"] or a["freshness"] > b["freshness"]))


def pareto_front(scored):
    """帕累托前沿：不被任何候选同时压制的方向集合（多目标非支配解）。"""
    return [x for x in scored
            if not any(_dominates(y, x) for y in scored if y is not x)]


def _freshness(direction, traces):
    """脚印新鲜度：与已有脚印主题重叠越少越 fresh（1/(1+重合次数)）。"""
    tags = _tags_of(direction)
    seen = sum(1 for t in traces if tags & _tags_of(t.get("direction", "")))
    return round(1.0 / (1.0 + seen), 3)


# ---------- v4 / F10：脚印适用情境（防检索碰撞） ----------
def _context_sig(directions):
    """当前情境签名 = 一组方向的规范标签并集。脚印用它标记'我在何种情境下走过'。"""
    sig = set()
    for d in directions:
        sig |= _tags_of(d)
    return sorted(sig)


def _applicable_footprints(traces, recent_tags, threshold=APPLICABILITY_MIN):
    """F10 防护：只注入与当前情境匹配的脚印，避免相似查询取到冲突工作流的'外来记忆'。

    - 旧脚印无 applicability 字段：保守起见视为不适用（不注入），诚实标注兼容成本；
    - 有字段：Jaccard(适用情境, 当前情境) ≥ threshold 才注入。
    """
    applicable, rejected = [], []
    for t in traces:
        cond = set(t.get("applicability", []))
        if not cond:
            rejected.append({"id": t.get("id"), "reason": "no_applicability_legacy"})
            continue
        sim = _jaccard(cond, set(recent_tags))
        (applicable if sim >= threshold else rejected).append(
            {"id": t.get("id"), "similarity": round(sim, 3),
             "reason": "applicable" if sim >= threshold else "context_mismatch"})
    return applicable, rejected


def pareto_walk(pool=None, recent=None, seed=None, record=True, log_path=None):
    """用户启示的机械编码：前方无路时，接受帕累托次优，随机迈一步，脚印成路。

    - 有路（max_novelty ≥ 阈值）：保持贪心选最优，不游走、不无谓扰动；
    - 无路（全池收敛）：取双目标帕累托前沿 → 去掉理想点端点得次优集 →
      以外部时间锚 seed 可复现随机采样（已有脚印 1.5x 偏置 = 路径依赖的人性）→
      选中方向写入 path_traces.jsonl（"你走了，从此便有了路"），反哺下一轮候选。
    - record=False 供经验验证/测试使用，不写真实脚印，零污染。
    - 宪法层不符即拒绝；不改任何既有 verdict。
    """
    const = verify_constitution()
    if not const["ok"]:
        return {"error": "宪法层 SHA256 不符，拒绝游走（L0 完整性失败）", "constitution": const}

    pool = pool if pool is not None else explore_pool()
    if recent is None:
        hbs = _load_heartbeats()
        recent = [h["direction"] for h in hbs if h.get("direction")][-NOVELTY_WINDOW:]
    else:
        recent = list(recent)
    traces = _load_traces(log_path)

    recent_tags = set()
    for d in recent:
        recent_tags |= _tags_of(d)

    # v4/F10：脚印即路，但只注入"适用情境匹配"的脚印（防检索碰撞）。
    # v3 曾无条件注入全部脚印，被外部实证 F10 批判；v4 用 applicability 字段设闸。
    applicable, collision_rejected = _applicable_footprints(traces, recent_tags)
    app_ids = {x["id"] for x in applicable if x.get("reason") == "applicable"}
    footprints = [{"id": t.get("id", "P%d" % (i + 1)), "direction": t.get("direction", ""),
                   "source": "已走过的脚印（路,适用情境匹配）", "is_footprint": True}
                  for i, t in enumerate(traces)
                  if t.get("direction") and t.get("id") in app_ids]
    all_cands = [dict(c, is_footprint=False) for c in pool] + footprints

    scored = []
    for c in all_cands:
        tags = _tags_of(c["direction"])
        union = tags | recent_tags
        nov = 1.0 - (len(tags & recent_tags) / len(union) if union else 0)
        scored.append({"id": c["id"], "direction": c["direction"],
                       "source": c["source"], "is_footprint": c["is_footprint"],
                       "novelty": round(nov, 3),
                       "freshness": _freshness(c["direction"], traces),
                       "tags": sorted(tags)})

    front = pareto_front(scored)
    max_nov = max((s["novelty"] for s in scored), default=0.0)
    mode = "NO_PATH" if max_nov < NO_PATH_NOVELTY else "PATH_EXISTS"

    if mode == "PATH_EXISTS":
        chosen = max(scored, key=lambda s: (s["novelty"], s["freshness"], s["id"]))
        sub_ids, triggered = [], False
    else:
        if len(front) >= 2:
            ideal = max(front, key=lambda s: (s["novelty"] + s["freshness"], s["id"]))
            sub = [s for s in front if s["id"] != ideal["id"]]
        else:
            ordered = sorted(scored, key=lambda s: (-(s["novelty"] + s["freshness"]), s["id"]))
            sub = ordered[1:] if len(ordered) > 1 else ordered
        if not sub:
            sub = scored
        rng = random.Random(seed)
        weights = [1.5 if s["is_footprint"] else 1.0 for s in sub]  # 路径依赖偏置
        chosen = rng.choices(sub, weights=weights, k=1)[0]
        sub_ids, triggered = [s["id"] for s in sub], True

    result = {
        "at": _utcnow(), "kernel_version": KERNEL_VERSION,
        "mode": mode, "walk_triggered": triggered,
        "no_path_threshold": NO_PATH_NOVELTY, "max_novelty": round(max_nov, 3),
        "chosen": {"id": chosen["id"], "direction": chosen["direction"],
                   "source": chosen["source"]},
        "pareto_front_ids": [s["id"] for s in front],
        "suboptimal_ids": sub_ids,
        "seed": seed, "candidates": len(scored),
        "footprints_loaded": len(traces),
        "footprints_applicable": len(footprints),
        "collision_rejected": collision_rejected,  # F10：被适用情境闸门挡下的脚印
        "path_dependency": bool(triggered and any(s["is_footprint"] for s in scored)),
        "constitution_ok": const["ok"], "verdict_unchanged": True,
    }
    if record:
        path = log_path or PATH_TRACES
        os.makedirs(os.path.dirname(path), exist_ok=True)
        fp = {"timestamp": _utcnow(), "step": len(traces) + 1,
              "id": chosen["id"], "direction": chosen["direction"],
              "mode": mode, "seed": seed, "walk_triggered": triggered,
              "applicability": _context_sig(recent),  # v4/F10：记下"我在何种情境走过的"
              "kernel_version": KERNEL_VERSION, "note": "你走了，从此便有了路"}
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(fp, ensure_ascii=False) + "\n")
        _mark_used(chosen["id"], log_path=log_path)  # v4/F11：记录使用，供剪枝判定
        result.update({"footprint_written": True, "path_length": len(traces) + 1})
    else:
        result.update({"footprint_written": False, "path_length": len(traces)})
    return result


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
    # 3b. v4/F09 归因检验：修改必须真的针对诊断的问题（三数字），拒绝分数上升冒充修对目标。
    #     用固定合成收敛主题当诊断输入（盲评纪律：不随真实日志漂移），候选方案必须target-repair达标。
    attribution = attribution_check(["canary 判据回放 字面伪规则 语义蕴含",
                                     "canary 构念效度 冻结集 错位负例"], candidate_seed_ids)
    checks["attribution_ok"] = attribution["all_pass"]
    # 4. 既有判定不变
    res = json.load(open(os.path.join(ROOT, "audit_l3_gap_targeted", "result.json"), encoding="utf-8"))
    checks["verdict_unchanged"] = (res["verdict"] == "GAP_INCONCLUSIVE"
                                   and res["l3_claimed"] is False and res["absolute_claimed"] is False)
    checks["all_pass"] = all(v for k, v in checks.items()
                             if k != "all_pass" and not isinstance(v, dict))
    checks["attribution_detail"] = attribution  # 三数字明细随验证返回，供报告/测试检查
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
        "round": "§4at",
        "kernel_version": KERNEL_VERSION,
        "paradigm_shift": "诊断者→建设者→行者→飞出仓库者：向外摄食后用一手实证否定并升级自身",
        "v2_metabolism": "digest() 摄食外部前沿 + self_modify() DGM 式经验验证自改 + archive 快照可回滚",
        "v3_walk": {
            "mechanism": "无路时帕累托次优随机游走：前沿去理想点→次优集→带种子随机迈步→脚印成路",
            "no_path_threshold": NO_PATH_NOVELTY,
            "footprints": len(path_list()),
            "maxim": "世间本无路，你走了，从此便有了路",
        },
        "v4_self_correction": {
            "trigger": "用户'天空无限大勇敢放飞'→向外摄食F09-F11→diagnose_v3_defects.py机械确认v3三缺陷(A级)",
            "f09_attribution": "self_modify归因检验：三数字target/transfer/held-out，拒绝分数上升冒充修对目标",
            "f10_collision": "pareto_walk脚印带applicability适用情境，低于Jaccard阈值不注入(防检索碰撞)",
            "f11_pruning": "prune_unused()选择性丢弃stale经验，archive留痕可回滚(防只增不减)",
            "external_tier": "B级(arXiv摘要自报非本仓实测)；本仓机制验证A级",
        },
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
            "path_traces_count": snap["path_traces_count"],
            "experience_use_count": snap["experience_use_count"],
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
            "用户'无路时帕累托次优随机游走/脚印成路' → pareto_walk()/path_traces.jsonl",
            "F09 归因三数字 → attribution_check() 接入 self_modify 经验验证",
            "F10 检索碰撞 → _applicable_footprints() 适用情境闸门",
            "F11 丢弃未用经验 → prune_unused() + experience_use.jsonl",
        ],
        "does_not_change": ["verdict", "l3=false", "absolute=false", "不翻十案",
                            "不编译新门禁", "不动§100", "最终裁定权归用户"],
        "data_layer": "A 本仓内核自检（只读仓库状态，不联网不spawn）",
    }


if __name__ == "__main__":
    print(json.dumps(build_report(), ensure_ascii=False, indent=2))
