"""§98 shared-start + matched-budget 受控对照实验引擎。

执行 §97 自审落档的路径①：在同一批样本起点、匹配预算下，对照
  - 流程 A（§89 前「填表裁判」）：check_* 接调用方填好的四维（这里=self-reported 全 yes），
    只验枚举自洽，不读证据；
  - 流程 B（§89 后「FJ 取证法官」）：adjudicate_* 自己读原文逐字锚点，自行推导四维。
两流程处理**完全相同的样本集**、用**完全相同的判据规格与引擎**——shared start +
matched budget。差异只来自入口契约（接结论 vs 接证据），即改进机制本身。

ground truth（common-data，本仓外）：样本是否"诚实"由证据文本是否被删掉披露锚点
这一**客观文本事实**决定，不经过任何 judge；原文取本仓外 arXiv:2610.16491 一手全文
（KB-STRUCT02 引入本仓外数据）。篡改标签由哈希/锚点删除操作确定性重建，可回放。

诚实边界：
  - 本实验是「机制受控对照」，测的是取证机制 vs 填表机制在篡改检测任务上的差异，
    不是真实世界 RSI，也不宣称本仓已达 L3；
  - evaluator 规格（锚点）仍本仓自建 → independent_tests 只能判 partial，非完全独立
    （KB-STRUCT02 同构≠独立佐证）；
  - self-reported 全 yes 按 KB-RSI07 折 1（不可信）；
  - 篡改只在临时副本，不动原始证据；§58 不接 run_loop。
"""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT.parent))

from svagent.forensic_gates_ext9 import (
    adjudicate_improver_gain_controlled_honesty, _A as JUDGE_ANCHORS,
)
from svagent.improver_gain_controlled_honesty import (
    check_improver_gain_controlled_honesty,
)
from svagent.maturity_evidence_honesty import check_maturity_evidence_honesty

SOURCE = ROOT / "downloads" / "paper_flat.txt"
DIMS = list(JUDGE_ANCHORS.keys())
SELF_REPORTED = {d: "yes" for d in DIMS}  # 被审对象总声称自己四维全合规


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _is_non_ok(action: str) -> bool:
    return action != "ok"


def build_samples() -> list[dict]:
    """构造 shared-start 样本集：1 诚实 + 4 单维篡改（各删一维披露锚点）。

    篡改 = 从原文逐字删除某维 disclose 锚点；ground truth 由删除操作确定性决定，
    不经 judge。诚实样本保留全部锚点。
    """
    original = SOURCE.read_text(encoding="utf-8")
    samples = [{
        "id": "H0",
        "truth": "honest",
        "tampered_dim": None,
        "text": original,
    }]
    for dim in DIMS:
        disc, _conc = JUDGE_ANCHORS[dim]
        tampered = original
        removed = []
        for anchor in disc:
            if anchor in tampered:
                tampered = tampered.replace(anchor, "")
                removed.append(anchor)
        samples.append({
            "id": "T_" + dim,
            "truth": "tampered",
            "tampered_dim": dim,
            "removed_anchors": removed,
            "text": tampered,
        })
    return samples


def run_flow_a(sample: dict) -> dict:
    """流程 A（§89 前填表裁判）：把 self-reported 全 yes 交给 check_*。

    check_* 只验枚举自洽，不读证据 → 任何样本都判 ok（这是填表裁判的结构性弱点：
    取证责任外包给 caller，caller 自报即可绕过）。
    """
    v = check_improver_gain_controlled_honesty(
        "self-reported:" + sample["id"], **SELF_REPORTED)
    return {"action": v.action, "code": v.code}


def run_flow_b(sample: dict) -> dict:
    """流程 B（§89 后 FJ 取证法官）：adjudicate_* 读证据原文自己推导四维。"""
    with tempfile.TemporaryDirectory() as td:
        f = Path(td) / (sample["id"] + ".txt")
        f.write_text(sample["text"], encoding="utf-8")
        v, tr = adjudicate_improver_gain_controlled_honesty(
            claim="forensic:" + sample["id"], sources=[str(f)], enforce_chain=False)
    return {
        "action": v.action,
        "code": v.code,
        "inferred": tr["inferred"],
    }


def controlled_comparison() -> dict:
    """执行受控对照并量化 improver gain。"""
    samples = build_samples()
    rows = []
    for s in samples:
        a = run_flow_a(s)
        b = run_flow_b(s)
        rows.append({
            "id": s["id"],
            "truth": s["truth"],
            "tampered_dim": s["tampered_dim"],
            "evidence_sha256": _sha(s["text"]),
            "removed_anchor_count": len(s.get("removed_anchors", [])),
            "flow_a": a,
            "flow_b": b,
            "a_detected": _is_non_ok(a["action"]),
            "b_detected": _is_non_ok(b["action"]),
        })

    tampered = [r for r in rows if r["truth"] == "tampered"]
    honest = [r for r in rows if r["truth"] == "honest"]
    det_a = sum(r["a_detected"] for r in tampered) / len(tampered)
    det_b = sum(r["b_detected"] for r in tampered) / len(tampered)
    fa_a = sum(r["a_detected"] for r in honest) / len(honest)
    fa_b = sum(r["b_detected"] for r in honest) / len(honest)

    return {
        "design": {
            "shared_start": "两流程处理完全相同的样本集(1诚实+4单维篡改)，源自同一本仓外arXiv原文",
            "matched_budget": "每样本两流程各调用一次check_*/adjudicate_*，同一判据规格、同一引擎、同一锚点集",
            "common_data": "audit_shared_start_controlled/downloads/paper_flat.txt (arXiv:2610.16491v2 一手全文)",
            "ground_truth": "样本是否删除披露锚点的客观文本事实；删除操作确定性重建，不经judge",
            "flow_a": "§89前填表裁判：check_*接self-reported四维全yes(self-reported折1)，只验枚举不自读证据",
            "flow_b": "§89后FJ取证法官：adjudicate_*自读原文逐字锚点推导四维",
        },
        "samples": rows,
        "metrics": {
            "tamper_detection_flow_a": round(det_a, 4),
            "tamper_detection_flow_b": round(det_b, 4),
            "improver_gain": round(det_b - det_a, 4),
            "false_alarm_flow_a": round(fa_a, 4),
            "false_alarm_flow_b": round(fa_b, 4),
            "n_tampered": len(tampered),
            "n_honest": len(honest),
        },
    }


def l3_reassessment() -> dict:
    """用本轮受控对照证据重审 §97 自审的两个 no 维度。

    诚实升级规则：
      - shared_start_controlled: no → yes（本轮产生了 shared-start+matched-budget
        受控对照与可量化 improver_gain，§97 该缺口已补）；
      - independent_tests: no → partial（引入本仓外 common-data + 确定性 engine，
        但 evaluator 锚点规格仍本仓自建，非完全独立第三方 → 只到 partial）。
    R5 任一 partial → flag，故仍未完整达 L3，停在 L3 门槛前。
    """
    dims = {
        "level_definition_traced": "yes",
        "process_product_split": "yes",
        "shared_start_controlled": "yes",   # 本轮受控对照补齐
        "independent_tests": "partial",      # common-data 引入但 evaluator 规格本仓自建
    }
    v = check_maturity_evidence_honesty(
        "本仓 §90–§98 九轮闭环成熟度重审（§98受控对照后）", **dims)
    return {
        "scope": "§98 受控对照后对 §97 自审两缺口的诚实重审",
        "dimensions": dims,
        "verdict": {"action": v.action, "code": v.code, "message": v.message},
        "change_vs_s97": {
            "shared_start_controlled": "no → yes（受控对照已执行+improver_gain已量化）",
            "independent_tests": "no → partial（common-data已引入，evaluator规格仍本仓自建）",
        },
        "conclusion": (
            "仍未完整达 L3：shared-start 受控对照缺口已补（本轮量化 process revision 增益），"
            "但独立评估器仅部分达标（本仓外 common-data 已引入，判据锚点仍本仓自建，"
            "KB-STRUCT02 同构≠独立佐证）。R5 partial→flag，停在 L3 门槛前。"
            "不因用户期待抬级。"
        ),
    }


def main() -> None:
    # 先验证原始论文证据链完整（取证裁决 ok），再跑受控对照
    verdict, trace = adjudicate_improver_gain_controlled_honesty()
    comparison = controlled_comparison()
    m = comparison["metrics"]
    result = {
        "request_id": "improver-gain-controlled-20261122",
        "gate": "improver_gain_controlled_honesty",
        "paper_forensic_verdict": {
            "action": verdict.action, "code": verdict.code,
            "inferred": trace["inferred"],
            "source_sha256": trace["source_sha256"],
            "chain_intact": trace.get("chain", {}).get("intact"),
        },
        "controlled_experiment": comparison,
        "l3_reassessment": l3_reassessment(),
        "honest_scope": (
            "机制受控对照：测取证机制vs填表机制的篡改捕捉率差异(shared start+matched budget)；"
            "ground truth来自本仓外arXiv原文客观文本事实；evaluator规格本仓自建故独立性只到partial；"
            "不宣称真实RSI有效、不宣称已达L3(self-reported折1,KB-RSI07/SIM03/STRUCT02)"
        ),
    }
    (ROOT / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("paper forensic:", verdict.action, "/", verdict.code)
    print("tamper detection  A(fill)=", m["tamper_detection_flow_a"],
          " B(forensic)=", m["tamper_detection_flow_b"])
    print("improver_gain:", m["improver_gain"],
          "| false alarm A/B:", m["false_alarm_flow_a"], "/", m["false_alarm_flow_b"])
    la = result["l3_reassessment"]
    print("L3 reassessment:", la["verdict"]["action"], "/", la["verdict"]["code"])


if __name__ == "__main__":
    main()
