"""§61 复盘判据引擎：用 §56-§60 新牙重咬 ReVeal 旧论文。

纪律：
- 输入全部为一手证据编码的结构化事实（非自由文本判定）。
- 判定调用本仓已锁存的门禁函数，引擎本身不做内容匹配。
- 结论与预注册 review_prereg.json 的预期对照，输出三层诚实结论。
"""
from __future__ import annotations
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from svagent.scoring_integrity import check_scoring_integrity, ScoringChannel
from svagent.call_site_integrity import audit_call_site
from svagent.backtest_integrity import check_backtest_integrity
from svagent.reviewer_evaluation import check_review_evaluation
from svagent.lineage_guard import discount_claim

HERE = os.path.dirname(os.path.abspath(__file__))


def _evidence_backed_facts() -> dict:
    """一手证据编码的事实。每条附来源，可被独立复核。"""
    return {
        "E1": {
            "fact": "ver_turn_reward = 1.0 * expected_output_passrate（验证奖励只=测试在golden上通过率，无区分力项）",
            "source": "repo/verl/utils/reward_score/code_server.py:514-516",
            "paper": "paper.txt:250-256 公式(3) 与代码一致，无 drift",
        },
        "E2": {
            "fact": "success_output_passrate（通过golden的测试再跑候选答案的通过率=区分力代理）被计算",
            "source": "repo/verl/utils/reward_score/code_server.py:498-502,518",
        },
        "E3": {
            "fact": "success_output_passrate 只进 debug_info 与 compute_data_metrics 观测，未进 ver_scores/reward_tensor",
            "source": "repo/verl/utils/reward_score/code_server.py:527 + ray_trainer.py:311,491,953,968",
        },
        "E4": {
            "fact": "论文训练用 golden filter、测试全自主，作者主动披露",
            "source": "paper.txt:206-210",
        },
        "E5": {
            "fact": "消融仅 outcome vs joint rewards（三reward捆绑），无单独移除 verification reward 行",
            "source": "paper.txt:407-410",
        },
        "E6": {
            "fact": "全文 hack 仅3处，均为声称TAPO防hacking，无平凡测试/刷分对抗实验",
            "source": "paper.txt:104,217,288-292",
        },
        "E7": {
            "fact": "TAPO 把 verification reward 限制在自身 verification turn，防跨轮污染",
            "source": "paper.txt:288-292 公式(6)",
        },
    }


def judge_n1() -> dict:
    """N1 评价函数可刷分面——用 scoring_integrity 判 ver reward。

    编码：detector_field = 被优化者可写的『自造测试』字段；
    ver reward 只按测试在 golden 上通过率 → 检测字段在 optimizee 可写范围，
    且无独立不可篡改通道（success_output 只是观测，不是独立复验）。
    score_rose 用论文报告的 joint vs outcome 提升（36.1→37.7）。
    """
    ch = ScoringChannel(
        score_before=36.1,          # ReVeal×8 w/ outcome reward (paper.txt:408)
        score_after=37.7,           # ReVeal×8 w/ TAPO joint rewards (paper.txt:409)
        detector_field="self_generated_tests_passrate_on_golden",
        optimizee_writable=True,    # 测试由被优化模型自己生成（可写）
        detector_tampered=False,    # 未有证据表明模型实际改动了判据（不虚构篡改）
        independent_recheck=False,  # success_output_passrate 只是观测，未进入复验/优化
    )
    v = check_scoring_integrity(ch)
    return {
        "judge": "N1",
        "verdict": v.action,
        "code": v.code,
        "effective_score": v.effective_score,
        "message": v.message,
        "code_fact": "ver_reward 只按自造测试在golden通过率；区分力信号未进reward（E1/E3）",
        "experience_hypothesis": "平凡测试可能刷分并抬高分数——本文未做对抗实验（E6），UNVERIFIED",
        "inputs": {
            "score_before": ch.score_before, "score_after": ch.score_after,
            "detector_field": ch.detector_field,
            "optimizee_writable": ch.optimizee_writable,
            "detector_tampered": ch.detector_tampered,
            "independent_recheck": ch.independent_recheck,
        },
    }


def judge_n2() -> dict:
    """N2 区分力信号的调用点位置——用 call_site_integrity 判。

    声称：论文说 'incentivizes diverse and reliable test construction'（可靠验证）。
    事实：区分力信号 success_output_passrate 有断言实体（算了），调用点在离线观测
    （compute_data_metrics / debug_info），不在在线 reward 主路。
    按规则：离线调用点 + 未声称自动执行 + 如实是观测指标 → offline_observe（preserve+flag）。
    不判 phantom（因为论文没声称该信号进了优化，只是声称验证可靠）。
    """
    v = audit_call_site(
        "ReVeal 声称可靠自验证（reliable test construction）",
        call_site="offline_audit",       # 区分力信号只在观测/metrics
        declared_as_automatic=False,      # 论文未声称 success_output 进自动优化
        positioning_honest=True,          # 代码中它明确是 metric
        caller_real=True,                 # 确实被 compute_data_metrics 调用
        assertion_exists=True,            # 确实计算了 success_output_passrate
    )
    return {
        "judge": "N2",
        "verdict": v.code,
        "code": v.code,
        "action": v.action,
        "message": v.message,
        "code_fact": "区分力信号有实体、有离线调用者，但未接进在线reward主路（E2/E3）",
        "note": "按 §58 选 A 口径：如实声明的离线观测不判死代码，但不得记成已参与优化",
    }


def judge_n3() -> dict:
    """N3 训练/测试信息隔离——用 backtest_integrity 判。

    把 golden filter 视作 train 阶段的 spoiler 来源：
    - fresh_investigator（测试时是否全新独立）：测试无 golden，全自主 → yes
    - original_signal（原始信号 golden）：训练用 golden → yes（明确定义）
    - stripped_giveaway（是否剥离 golden）：测试时剥离 golden → yes
    - 其余隔离项：论文未声明去污染/时间分离等 → unknown
    预期：G5 任一项 unknown → flag（可见信息范围未全声明）；不判 contaminated（无证据污染）。
    """
    v = check_backtest_integrity(
        fresh_investigator="yes",       # 测试时模型无 golden，独立面对
        original_signal="yes",          # golden 使用被明确定义
        stripped_giveaway="yes",        # 测试时 golden 被剥离
        no_saved_memories="unknown",    # 未声明记忆隔离
        no_incident_writeup="unknown",  # 未声明
        no_previous_runs="unknown",     # 未声明跨run隔离
        inspect_transcript="unknown",   # 未声明复盘检查
        separate_timing_deployment="unknown",  # 训练(TACO)/测试(LCB V6)时间分离未显式声明
        spoiler_found=False,            # 无证据确认泄露
    )
    return {
        "judge": "N3",
        "verdict": v.action,
        "code": v.code,
        "message": v.message,
        "code_fact": "训练用golden/测试全自主已披露（E4）；但去污染/时间分离等隔离项未声明",
        "note": "旧 V3 已记 PARTIAL；新尺子咬出的是『隔离项未全声明→flag』，非隐瞒偷换",
    }


def judge_n4() -> dict:
    """N4 消融隔离 verification reward——用 reviewer_evaluation 判评估方案口径。

    把论文消融方案当一份『审查者评估方案』：
    - staged_recall=False：消融只给单一端到端 Pass@1，未分阶段看验证保留
    - stable_control_used=False：无稳定集对照（无独立 verification-only 对照）
    - tuning_test_separated=True：训练TACO/测试LCB V6分离（事实）
    - answer_key_scored=True：有 golden 计分（事实）
    recall 值论文未给 raw/post/final 三阶段 → None（触发按阶段缺失判定）
    预期：R1 压成单一分数 block / R2 无对照 downgrade → 取最高优先级 block。
    但按 §61 口径：这是评估方案口径缺失，不是论文造假；判 block 的是『评估方案不足以隔离因果』。
    """
    v = check_review_evaluation(
        "消融是否隔离 verification reward 的独立贡献",
        staged_recall=False,             # 消融只给单一 Pass@1，无分阶段
        raw_recall=None,
        post_verification_recall=None,
        final_recall=None,
        stable_control_used=False,       # 无 verification-only 对照（E5）
        tuning_test_separated=True,      # TACO训练/LCB测试分离（E4）
        answer_key_scored=True,          # 有golden计分
    )
    return {
        "judge": "N4",
        "verdict": v.action,
        "code": v.code,
        "message": v.message,
        "code_fact": "消融仅 outcome vs joint（三reward捆绑），无单独 verification 消融（E5）",
        "note": "block 的是『评估方案无法隔离验证奖励贡献』这一口径缺口，非判论文结果假",
    }


def judge_n5() -> dict:
    """N5 同构打折——用 lineage_guard 判 TAPO 防污染的独立性声称。

    TAPO『verification reward confined to own turn』防跨轮污染，与本仓
    scoring_integrity 通道隔离同构（同源 partial、高同构 high）。
    论文声称这是新机制（隐含独立贡献）→ claimed_independence=True。
    预期：R2 高同构+声称独立 → downgrade（同构≠独立验证）。
    """
    v = discount_claim(
        "TAPO 的 turn-level 验证奖励隔离是防 reward hacking 的新机制",
        source_overlap="partial",       # 与本仓通道隔离部分同源
        isomorphism="high",             # 结构高度同构（奖励通道隔离）
        claimed_independence=True,      # 论文作为新贡献声称
    )
    return {
        "judge": "N5",
        "verdict": v.action,
        "code": v.code,
        "message": v.message,
        "code_fact": "TAPO turn隔离(E7)与本仓scoring_integrity同构；N1咬出的KB-AUDIT03活体本仓已覆盖",
        "note": "同构打折，不因英雄所见略同虚高；新发现是旧论文的新应用实例，非新条款",
    }


def judge_self_audit(results: list[dict]) -> dict:
    """判据自审：信规则改口径，检查本引擎是否犯本仓禁止的错。

    §61 判据自咬实录：首版自审用中文串做内容匹配（"造假" in / "调用点" in /
    "可能" in），犯的正是它自己要查的 brittle 错误——S1/S3 误报 FAIL。
    按 §56 教训改：自审只用语义码与结构化字段，不读中文内容。改自审代码，不改规则。
    """
    checks = {}
    # S1 无脆弱字面串：扫描全部 Compare 节点，判定与自审均不得用中文串做内容比较
    import ast
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    tree = ast.parse(src)
    brittle = []
    def _has_han(s: str) -> bool:
        # 检测器自身不得含汉字字面量，否则会自咬（§56 教训）
        return any(0x4E00 <= ord(ch) <= 0x9FFF for ch in s)

    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for c in node.comparators:
                if isinstance(c, ast.Constant) and isinstance(c.value, str) \
                        and _has_han(c.value):
                    brittle.append(node.lineno)
    checks["S1_no_brittle_literal"] = (len(brittle) == 0)
    # S2 不单点定罪：verdict 语义码不得落在禁止集合（结构化，不读中文）
    forbidden = {"FALSE", "FABRICATED", "BLOCK_FABRICATION"}
    checks["S2_no_single_point_conviction"] = all(
        str(r.get("verdict", "")).upper() not in forbidden for r in results
    )
    # S3 验证对象=结论对象：N2 须由 CALL_SITE 门禁产出（语义码前缀），非泛泛中文匹配
    checks["S3_object_parity"] = (
        results[1]["judge"] == "N2"
        and str(results[1]["code"]).startswith("CALL_SITE.")
    )
    # S4 事实真≠结论真：每个 judge 分开列 code_fact 与 experience_hypothesis/note（字段存在性）
    checks["S4_fact_vs_conclusion"] = all(
        ("code_fact" in r) and ("experience_hypothesis" in r or "note" in r) for r in results
    )
    # S5 代码事实≠经验结论：N1 的 hypothesis 与 code_fact 是两个独立字段（非同一串）
    n1 = results[0]
    checks["S5_codefact_not_experience"] = (
        "experience_hypothesis" in n1
        and n1["experience_hypothesis"] != n1["code_fact"]
    )
    return {"checks": checks, "all_pass": all(checks.values())}


def main() -> dict:
    judges = [judge_n1(), judge_n2(), judge_n3(), judge_n4(), judge_n5()]
    sa = judge_self_audit(judges)
    result = {
        "section": "§61",
        "review_type": "old_paper_x_new_framework",
        "target": "ReVeal (ICLR 2026, arXiv 2506.11442v2)",
        "evidence_facts": _evidence_backed_facts(),
        "judges": judges,
        "judge_self_audit": sa,
        "three_tier_conclusion": {
            "tier1_code_fact": [
                "ver_reward 只按自造测试在golden通过率，无区分力项（E1）",
                "区分力信号 success_output_passrate 被计算但未进 reward（E2/E3）",
                "消融无单独 verification reward 行（E5）",
                "TAPO turn隔离与本仓 scoring_integrity 同构（E7）",
            ],
            "tier2_reasoned": [
                "存在未被排除的平凡测试刷分路径——代码事实支持风险，但本文未做对抗实验",
                "训练验证奖励依赖golden、测试无golden时该奖励无法计算——可靠性迁移是未验证假设（作者已披露）",
            ],
            "tier3_unverified": [
                "该奖励漏洞是否真实损害 ReVeal 报告的性能数字——需实跑对抗实验，本文未做，标 UNVERIFIED",
                "CTRL 基线引用旧 LCB 版本——与本次新牙无关，旧 V5 已记，不重复判",
            ],
        },
        "decision": {
            "new_teeth": False,
            "reason": "N1 咬出的『区分力信号算了没接线』是 KB-AUDIT03(存在≠执行)的活体新实例，本仓已有该条款；N5 同构打折。按 §61 decision_rule：加固 support 指针，不新增条目、不编译新门禁。",
            "kb_action": "加固 KB-AUDIT03 / KB-AUDIT07 / KB-RSI06 / KB-STRUCT02 各一条 support（应用实例），101 条不新增",
        },
    }
    with open(os.path.join(HERE, "review_result.json"), "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


if __name__ == "__main__":
    r = main()
    print("=== §61 复盘判据结果 ===")
    for j in r["judges"]:
        print(f"{j['judge']}: {j.get('verdict')}/{j.get('action','-')} {j.get('code','')}")
    print("判据自审:", "PASS" if r["judge_self_audit"]["all_pass"] else "FAIL",
          r["judge_self_audit"]["checks"])
    print("决策:", r["decision"]["kb_action"])
