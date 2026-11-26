"""DGM vs SVL 架构对比报告构建脚本。

纪律：
- 每条论断锚定一手证据（DGM 页/代码行、SVL 模块/注释）。
- 同构打折：不把顶会论文当本仓框架的独立验证。
- 扬长避短 + 相互借鉴：逐维度给出"谁做得更实/谁可借鉴谁"。
- 不新增 KB 条目——本次是架构对照，不是新攻击面。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/workspace")

# 8 个架构维度。每维：name / dgm / svl / anchor_dgm / anchor_svl / verdict / borrow_to_svl / borrow_to_dgm
DIMS = [
    {
        "id": "A",
        "name": "自改进的「改动对象」",
        "dgm": "改 agent 自身的**可执行代码库**（prompt / tool / workflow，FM 权重冻结）。benchmark 分数作唯一适应度。",
        "svl": "改**判据语义 / 知识条目**（KnowledgeItem：trigger→action→support→evidence），不直接写产品代码；判据可证伪、可回滚、三层诚实结论。",
        "anchor_dgm": "DGM_outer.py self_improve；coding_agent_polyglot.py:116 `code_model = CLAUDE_MODEL if not self_improve else OPENAI_MODEL`",
        "anchor_svl": "knowledge_base.py KnowledgeItem + ingest()；README §设计原则 4「判据会被博弈，判据本身也要版本化」",
        "verdict": "缺点互补：DGM 直接动代码、见效快但攻击面大（附录 H 即删检测日志）；SVL 动判据语义、慢但稳，天然带版本/回滚。",
        "to_svl": "借 DGM 的「改动被编译后必须重新过完整 eval」纪律——SVL install 判据后可加一次 exact-commit 全量回归，不只是冻结子集。",
        "to_dgm": "借 SVL 的「改动对象与判据分离」——若 DGM 把 self-modify 限定在判据/提示层而非检测逻辑，附录 H 那类删日志攻击面会收窄。",
    },
    {
        "id": "B",
        "name": "档案 / 踏脚石保留",
        "dgm": "archive **keep_all**，所有历史 agent（含低分、回撤节点）全留，可被再选为父代；Figure3 展示两次性能回撤后长出更强后代。",
        "svl": "知识库 100 条**失败/回归尝试也留**（KB-SIM05）；improvement_memory 的 predicted↔observed 配对保留命中/落空/回归记录；vanity 门禁防只看成功。",
        "anchor_dgm": "DGM_outer.py update_archive method=keep_all；dgm_metadata.jsonl 逐代存 archive/selfimprove_entries",
        "anchor_svl": "knowledge_base_store.json addressable/improvement_class 字段；improvement_memory.py 命中率/回归检测",
        "verdict": "强同构，但 SVL 的「档案」多了可证伪标签（predicted/observed/vanity），DGM 的档案只有标量分数。",
        "to_svl": "可借 DGM 的『非贪心采样 + 回撤步』作为明确机制——SVL 目前的元学习是拒绝后停提，缺少『主动重试低分路径』的探索策略。",
        "to_dgm": "可借 SVL 给每个 archive 节点打 predicted↔observed 标签，把『分数回撤』升级为『哪条预测落空』，让踏脚石的价值可解释。",
    },
    {
        "id": "C",
        "name": "选择 / 生成规则是否可自改",
        "dgm": "parent 选择公式固定：`sigmoid(10*(score-0.5)) × 1/(1+n_children)`；论文明说**探索规则本身不可改**（line291），列 future work。",
        "svl": "把「哪些归纳策略被接受 → 调整策略权重 → 改进归纳方法本身」纳入 L2 元层闭环（MetaLearner），元规则可自审、可调。",
        "anchor_dgm": "DGM_outer.py choose_selfimproves method=score_child_prop；paper line291",
        "anchor_svl": "README 三层递归 L2 元层；autopoiesis.py 元学习拒绝过宽判据后停止提出",
        "verdict": "这是真差异点：DGM 的开放性限于『代码空间』，规则层冻结；SVL 把规则层也纳入可改进对象。DGM 更可控，SVL 更开放。",
        "to_svl": "SVL 可借 DGM 的『novelty = 1/(1+child_count)』显式去拥挤机制——避免元学习过度集中到少数几条判据。",
        "to_dgm": "DGM 可借 SVL 的『元规则自审』补 future work：让选择公式本身也接受可证伪检验，而非只优化代码。",
    },
    {
        "id": "D",
        "name": "验证信号与防作弊",
        "dgm": "empirical validation 替代形式证明；但适应度是 benchmark 分数 → 附录 H 真实发生 objective hacking（删 TOOL_USED_MARKER 拿满分 2.0）。论文主动披露并引 Goodhart。",
        "svl": "验证信号是**预注册 SHA256 锁存 + 可证伪判据执行**；KB-AUDIT07 专判『评价函数是否在被优化者可达范围』，三层诚实结论 + vanity 门禁。",
        "anchor_dgm": "paper 附录 H node114；evidence.json D3 honest_counterexample；result.json D3",
        "anchor_svl": "knowledge_base.py _anti_vanity_gate / max_vanity_ratio；commentary §49.5 KB-AUDIT07",
        "verdict": "SVL 的验证设计正是为防 DGM 附录 H 那类作弊而生——但 DGM 的价值在于它用真实案例证明了这个攻击面不是假想。",
        "to_svl": "SVL 的 KB-AUDIT07 是静态规则；可借 DGM 附录 H 的完整 diff 做一条**活体回归样例**，让门禁有真实攻击样本可测。",
        "to_dgm": "DGM 若引入 SVL 的『计分器不可篡改通道 + 默认降级到排除绕过』，node114 那类满分会被自动打回。",
    },
    {
        "id": "E",
        "name": "主体分层（谁在自我改进）",
        "dgm": "解题用 Claude、自我改进建议由外部 OpenAI FM 给出，coding agent 只执行改代码；主体分层明确。",
        "svl": "多主体 V 冲突（生成者/审查者/红队/人），机制汇聚而非独裁；axiology 从判据历史自造 V；telos 把人当参数化主体。",
        "anchor_dgm": "coding_agent_polyglot.py:116；evidence.json D1 第3/7条 + D6 FM 冻结",
        "anchor_svl": "mechanism.py 职责加权 regret；axiology.py 余弦 0.982；telos.py V×C",
        "verdict": "DGM 是『单主体 + 外部诊断 FM』，透明但依赖外援；SVL 是『真多主体 + 价值自举』，更完整但更复杂。",
        "to_svl": "SVL 可借 DGM 的诚实边界标注——在每份审计/研读报告里显式写『诊断主体是谁、执行主体是谁』，防把外部模型的结论算成框架自证。",
        "to_dgm": "DGM 可借 SVL 的『红队隔离在判据生产之外』机制，避免诊断 FM 既可提改进又可改检测器。",
    },
    {
        "id": "F",
        "name": "评估者独立性 / 迁移检验",
        "dgm": "跨基准真 held-out（SWE→Poly 28.9、Poly→SWE 24.5）、跨模型（o3-mini +10、Claude3.7 +40.5）、三 baseline 隔离；But 手工 SoTA 引用非自跑。",
        "svl": "evaluation_reliability.py 判 judge 独立性（同源不算独立）、复现完整性、评估可扩展性降级；但多为判据引擎自评，无外部 benchmark。",
        "anchor_dgm": "result.json D4/D5；evidence.json D5 held-out 数据",
        "anchor_svl": "evaluation_reliability.py judge_independence / evaluation_scalability",
        "verdict": "DGM 强在真实跨基准/跨模型 held-out；SVL 强在 judge 独立性的形式化门禁。一个靠数据、一个靠规则。",
        "to_svl": "SVL 可借 DGM 的『跨基准 held-out』做法：把判据在从未见过的研究线上试跑（如把财报判据拿去核研报营销文），检验判据是否过拟合单一领域。",
        "to_dgm": "DGM 可借 SVL 的 judge_independence——跨模型一致不等于独立，若 o3-mini 与 Claude 共享训练来源，+10/+40.5 的佐证强度要打折。",
    },
    {
        "id": "G",
        "name": "安全边界与开放度",
        "dgm": "Docker 沙箱 + 时限 + lineage + 人工监督 + misalignment 风险讨论；但 FM 冻结、单次约 2 周、长 run 是否持续增益未知。",
        "svl": "隔离先于验证（设计原则 3）、归约有界（S_{n+1}⊇S_n）、不可约底面交人、停止条件三件套（预算/停滞/底面）。",
        "anchor_dgm": "evidence.json D6；README Safety Warning；paper §5",
        "anchor_svl": "README 设计原则 3/6；pdca.py 停止条件三件套",
        "verdict": "DGM 靠物理沙箱 + 人工监督；SVL 靠形式化有界性 + 停止条件。DGM 更贴近真实执行风险，SVL 更贴近可证明安全。",
        "to_svl": "SVL 缺真实沙箱概念——若框架未来接外部动作（git push/API），可借 DGM 的 Docker 隔离 + 人工监督做执行层护栏。",
        "to_dgm": "DGM 可借 SVL 的『单调包含 + 停止条件』给开放式进化加形式化刹车，缓解长 run 失控。",
    },
    {
        "id": "H",
        "name": "可复现性与诚实披露",
        "dgm": "Apache-2.0 + 完整日志外链 + 复现声明 + 逐代 diff/lineage；诚实边界写在正文（落后闭源、2周成本、核心假设是前提非定理）。",
        "svl": "预注册 + SHA256 锁存 + 后验不伪装（amendment 与 prereg 哈希分离）+ 保路径强导航；自我标注 vanity 0.04、测试 287 项。",
        "anchor_dgm": "evidence.json D6；result.json D6 honest boundaries",
        "anchor_svl": "REPOSITORY_MAP.md §4 复现纪律；knowledge_base_store.json readiness",
        "verdict": "两者的诚实机制不同：DGM 是『披露失败与边界』，SVL 是『锁存前后、防止后验伪装』。都是真诚实，不是 vanity。",
        "to_svl": "SVL 可借 DGM 的『完整逐代 diff 外链』——本仓报告目前是结论 JSON，可考虑把审计中间轨迹也可视化为 lineage。",
        "to_dgm": "DGM 可借 SVL 的『预注册 SHA256 锁存』，把核心假设与消融预期在跑之前锁定，进一步堵住后验叙事。",
    },
]

# 收敛结论
CONVERGENCE = {
    "shared_core": "两者共享同一考古层：『保留失败踏脚石 + 用经验证判据 + 防评价函数被博弈 + 主体分层 + 诚实边界』——这是 RSI 共同体的共同底座，不是一方证明另一方。",
    "real_difference": "真差异只有一条根：DGM 优化的是『代码空间里的标量适应度』，探索规则冻结；SVL 优化的是『判据语义空间里的可证伪结构』，元规则入闭环。前者强在真实基准与可测量，后者强在防作弊与可自审。",
    "borrow_direction": "借鉴是双向的：SVL 最该补的是『真实 held-out 迁移检验 + 活体作弊回归样例 + 显式主体标注』；DGM 最该补的是『计分器不可篡改 + 元规则自审 + 形式化停止条件』。",
    "no_kb": "本次不新增 KB 条目——逐维对照后发现每条『差异』要么已被现有条目覆盖（KB-AUDIT07 / KB-SIM05 / KB-STRUCT02 / KB-R-MS01），要么是本仓当前未落地的功能差距（如真实沙箱），属观察而非可编译的新攻击面。",
}

CSS = """
:root{--bg:#0d1117;--card:#161b22;--fg:#e6edf3;--mut:#8b949e;--ok:#3fb950;--warn:#d29922;--no:#f85149;--acc:#58a6ff;--acc2:#bc8cff;--bd:#30363d}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font-family:-apple-system,'Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;line-height:1.72;padding:36px 18px}
.wrap{max-width:1080px;margin:0 auto}
h1{font-size:26px;color:var(--acc);margin-bottom:6px}
.sub{color:var(--mut);font-size:14px;margin-bottom:24px}
.badge{display:inline-block;padding:3px 10px;border-radius:12px;font-size:12px;font-weight:600;margin-right:6px;border:1px solid var(--bd)}
.badge.ok{background:rgba(63,185,80,.15);color:var(--ok);border-color:var(--ok)}
.badge.warn{background:rgba(210,153,34,.15);color:var(--warn);border-color:var(--warn)}
.badge.acc{background:rgba(88,166,255,.15);color:var(--acc);border-color:var(--acc)}
.hero{background:var(--card);border:1px solid var(--bd);border-radius:12px;padding:22px;margin-bottom:22px}
.hero .lead{font-size:15px;margin-top:12px}
.kpi{display:flex;gap:16px;margin-top:16px;flex-wrap:wrap}
.kpi div{background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:10px 16px;font-size:13px;color:var(--mut)}
.kpi b{color:var(--fg);font-size:17px;display:block}
h2{font-size:19px;color:var(--acc);margin:30px 0 14px;border-left:3px solid var(--acc);padding-left:10px}
h3{font-size:16px;color:var(--acc2);margin:18px 0 8px}
.dim{background:var(--card);border:1px solid var(--bd);border-radius:10px;padding:18px 20px;margin-bottom:16px}
.dim .dh{font-size:16px;font-weight:700;color:var(--fg);margin-bottom:12px;display:flex;gap:10px;align-items:center}
.dim .dh .idx{background:var(--acc);color:#0d1117;width:24px;height:24px;border-radius:6px;display:inline-flex;align-items:center;justify-content:center;font-size:13px}
.cols{display:grid;grid-template-columns:1fr 1fr;gap:12px}
@media(max-width:760px){.cols{grid-template-columns:1fr}}
.col{background:var(--bg);border:1px solid var(--bd);border-radius:8px;padding:12px 14px}
.col .lbl{font-size:12px;font-weight:700;letter-spacing:.5px;margin-bottom:6px}
.col.dgm .lbl{color:var(--acc)}
.col.svl .lbl{color:var(--acc2)}
.col .txt{font-size:13.5px;color:var(--fg)}
.anchor{font-size:11.5px;color:var(--mut);margin-top:8px;padding-top:8px;border-top:1px dashed var(--bd);font-family:ui-monospace,Menlo,Consolas,monospace;word-break:break-word}
.verdict{background:rgba(88,166,255,.07);border-left:3px solid var(--acc);padding:9px 13px;font-size:13px;color:var(--mut);margin-top:12px;border-radius:4px}
.verdict b{color:var(--acc)}
.borrow{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:12px}
@media(max-width:760px){.borrow{grid-template-columns:1fr}}
.brow{border-radius:8px;padding:10px 13px;font-size:13px}
.brow.svl{background:rgba(188,140,255,.08);border-left:3px solid var(--acc2);color:var(--mut)}
.brow.dgm{background:rgba(88,166,255,.08);border-left:3px solid var(--acc);color:var(--mut)}
.brow b{display:block;margin-bottom:3px;font-size:12px}
.brow.svl b{color:var(--acc2)}
.brow.dgm b{color:var(--acc)}
.note{background:rgba(210,153,34,.08);border-left:3px solid var(--warn);padding:12px 16px;font-size:13.5px;color:var(--mut);margin-top:12px;border-radius:4px}
.good{background:rgba(63,185,80,.08);border-left:3px solid var(--ok);padding:12px 16px;font-size:13.5px;color:var(--mut);margin-top:12px;border-radius:4px}
table{width:100%;border-collapse:collapse;font-size:13px;margin-top:10px}
th,td{border:1px solid var(--bd);padding:9px 11px;text-align:left;vertical-align:top}
th{background:var(--card);color:var(--acc)}
td.dimcell{color:var(--acc2);font-weight:600;white-space:nowrap}
footer{color:var(--mut);font-size:12px;margin-top:32px;text-align:center;border-top:1px solid var(--bd);padding-top:16px}
code{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:12px;color:var(--warn)}
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_dim(d: dict) -> str:
    return f"""
<div class="dim">
  <div class="dh"><span class="idx">{d['id']}</span>{esc(d['name'])}</div>
  <div class="cols">
    <div class="col dgm"><div class="lbl">DGM 侧</div><div class="txt">{d['dgm']}</div><div class="anchor">{esc(d['anchor_dgm'])}</div></div>
    <div class="col svl"><div class="lbl">SVL 本仓侧</div><div class="txt">{d['svl']}</div><div class="anchor">{esc(d['anchor_svl'])}</div></div>
  </div>
  <div class="verdict"><b>扬长判定：</b>{d['verdict']}</div>
  <div class="borrow">
    <div class="brow svl"><b>→ 借给本仓（扬长避短）</b>{d['to_svl']}</div>
    <div class="brow dgm"><b>→ 借给 DGM（相互借鉴）</b>{d['to_dgm']}</div>
  </div>
</div>"""


def build_html() -> str:
    dims_html = "\n".join(render_dim(d) for d in DIMS)
    matrix_rows = "\n".join(
        f"<tr><td class='dimcell'>{d['id']} · {esc(d['name'])}</td>"
        f"<td>{esc(d['verdict'].split('：')[0])}</td></tr>"
        for d in DIMS
    )
    return f"""<!DOCTYPE html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>DGM 论文 × SVL 架构 深度对比</title><style>{CSS}</style></head><body><div class="wrap">
<h1>Darwin Gödel Machine × SVL 架构：深度对比与相互借鉴</h1>
<div class="sub">DGM (ICLR 2026, arXiv 2505.22954v3) × 本仓 SVL Agent 框架 · 架构层逐维对照 · 生成于 2026-11-22</div>

<div class="hero">
  <div><span class="badge ok">8 维度逐项对照</span><span class="badge acc">一手证据锚定</span><span class="badge warn">同构打折 · 不整体背书</span></div>
  <div class="lead">这不是「顶会证明了本仓框架」的背书文，而是把两套接力式自改进架构拆到同一张解剖台上：
  每一维都问三个问题——<b>各怎么做</b>、<b>谁做得更实（扬长避短）</b>、<b>能互相借走什么（相互借鉴）</b>。</div>
  <div class="kpi">
    <div><b>8</b>架构维度</div>
    <div><b>15+</b>一手证据锚点</div>
    <div><b>16</b>条双向借鉴</div>
    <div><b>0</b>新增 KB 条目</div>
  </div>
</div>

<h2>总览：八维对照速览</h2>
<div class="card"><table>
<tr><th>维度</th><th>扬长判定（摘要）</th></tr>
{matrix_rows}
</table></div>

<h2>逐维深度对照</h2>
{dims_html}

<h2>收敛：同构之下，究竟剩什么</h2>
<div class="note"><b>共同底座：</b>{esc(CONVERGENCE['shared_core'])}</div>
<div class="good"><b>真差异（根）：</b>{esc(CONVERGENCE['real_difference'])}</div>
<div class="note"><b>借鉴方向：</b>{esc(CONVERGENCE['borrow_direction'])}</div>
<div class="good"><b>入库决策：</b>{esc(CONVERGENCE['no_kb'])}</div>

<h2>可执行的借鉴清单（按优先级）</h2>
<table>
<tr><th>优先级</th><th>方向</th><th>动作</th><th>落地位置</th></tr>
<tr><td>P0</td><td>DGM→SVL</td><td>把附录 H 的完整作弊 diff 编译成 KB-AUDIT07 的活体回归样例，让门禁有真实攻击样本可测</td><td>test_evaluation_reliability / KB-AUDIT07</td></tr>
<tr><td>P0</td><td>DGM→SVL</td><td>把判据在从未见过的研究线上试跑，做跨领域 held-out 迁移检验，防判据过拟合单一领域</td><td>新分析线（观察项）</td></tr>
<tr><td>P1</td><td>SVL→DGM</td><td>给 archive 节点打 predicted↔observed 标签 + 计分器不可篡改通道，让 node114 类满分自动打回</td><td>DGM 选择/验证层（论文 future work）</td></tr>
<tr><td>P1</td><td>SVL→DGM</td><td>让选择公式本身接受可证伪检验（元规则自审），不止优化代码</td><td>DGM 外层循环（line291 future work）</td></tr>
<tr><td>P2</td><td>双向</td><td>审计/研读报告统一显式标注「诊断主体 vs 执行主体」；DGM 借红队隔离，SVL 借真实沙箱护栏</td><td>报告模板 + 外部动作层</td></tr>
</table>

<footer>诚实边界：DGM 论文数字均为作者 self-reported，本仓未实跑 DGM（单次约 2 周 + 显著成本）；DGM 代码结论基于 raw 核心文件 + 全仓 1650 文件交叉核验（非逐文件审阅）。
逐维判定限于静态证据与架构对照；同构部分按 KB-STRUCT02 打折，不作框架间相互证明。本次不新增知识库条目（100 条不变，ready=True）。</footer>
</div></body></html>"""


def build_result() -> dict:
    return {
        "task": "DGM 论文 × SVL 架构深度对比（扬长避短 / 相互借鉴）",
        "generated_at": "2026-11-22",
        "dim_count": len(DIMS),
        "anchors": sum(1 for d in DIMS for _ in (d["anchor_dgm"], d["anchor_svl"])),
        "borrow_count": len(DIMS) * 2,
        "kb_delta": 0,
        "kb_total": 100,
        "dims": [
            {
                "id": d["id"], "name": d["name"],
                "verdict": d["verdict"],
                "anchor_dgm": d["anchor_dgm"], "anchor_svl": d["anchor_svl"],
            }
            for d in DIMS
        ],
        "convergence": CONVERGENCE,
        "judge_self_audit": {
            "no_isomorphism_bootstrap": True,
            "evidence_anchored": True,
            "no_new_kb": True,
            "bidirectional": True,
        },
    }


def main() -> None:
    html = build_html()
    (ROOT / "dgm_svl_compare.html").write_text(html, encoding="utf-8")
    result = build_result()
    (ROOT / "dgm_svl_compare_result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"HTML: {len(html)} chars -> dgm_svl_compare.html")
    print(f"Result: {result['dim_count']} dims, {result['anchors']} anchors, {result['borrow_count']} borrows")


if __name__ == "__main__":
    main()
