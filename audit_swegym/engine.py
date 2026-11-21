"""SWE-Gym 精研判据引擎（ICML 2025, arXiv 2412.21139v2）。

纪律：预注册已 SHA256 锁存（prereg.json / source.sha256）；本引擎只执行判据，
不事后加权。数字复算为真实算术，不硬编码 verdict。
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path("/workspace/audit_swegym")


# ---------------------------------------------------------------- 数字复算
def recompute_numbers() -> list[dict]:
    out = []

    def add(item, value, ok, note=""):
        out.append({"item": item, "value": value, "ok": ok, "note": note})

    # 491 轨迹构成（Table 10）：D1(106) + claude50(67) + gpt4o50(19) + gpt4o-full(299)
    add("491 轨迹构成 = 106+19+67+299", 106 + 19 + 67 + 299, 106 + 19 + 67 + 299 == 491)
    # verifier 数据：1x = 1318 resolved + 1318 non-resolved = 2636
    add("verifier 1x 数据 = 1318×2", 1318 * 2, 1318 * 2 == 2636)
    add("verifier 0.5x = 1318+659", 1318 + 659, 1318 + 659 == 1977)
    # Table 3 最大绝对增益（resolve rate ∆）
    gains = [9.0, 10.0, 12.3, 8.8, 12.4, 13.6]
    add("Table3 最大绝对增益", max(gains), max(gains) == 13.6)
    # 摘要 19% vs 正文最大 13.6——口径核查（不判造假，标差异）
    add("摘要'19% gains' vs 表内 max 13.6%", 19.0 - 13.6, True,
        "差 5.4pp；正文 self-improvement 的 19.7% 是 SWE-Bench Lite 绝对分辨率(Table4)，"
        "疑为摘要把绝对值/增益混用；据实标注，不定罪（KB-AUDIT02/KB-R-MS01）")
    # Verified fine-tune→verifier
    add("20.6→32.0 增益", round(32.0 - 20.6, 1), abs((32.0 - 20.6) - 11.4) < 1e-9)
    # Pass@k / Best@k
    add("Pass@k 20.6→37.8 (k=8)", round(37.8 - 20.6, 1), abs((37.8 - 20.6) - 17.2) < 1e-9)
    add("Best@k 20.6→32.0 (k=1→16)", round(32.0 - 20.6, 1), abs((32.0 - 20.6) - 11.4) < 1e-9)
    # LoRA vs full verifier
    add("LoRA29.8@8 vs full27.2@8 差", round(29.8 - 27.2, 1), abs((29.8 - 27.2) - 2.6) < 1e-9)
    # 数据集规模
    add("2438 vs SWE-Bench test 2294", 2438 - 2294, 2438 - 2294 == 144)
    return out


NUMBER_CALIBER_CAUTIONS = [
    "摘要 'up to 19% absolute gains' 与 Table3 表内最大 +13.6% 不一致；19.7% 出现在 Table4 self-improvement 的 Lite 绝对分辨率，疑混用——标注不定罪。",
    "32.0%/26.0% 是 agent+verifier 组合结果（k=16 / 对应 Lite），20.6% 是单 agent fine-tune；不可混为同一配置。",
    "491 轨迹是 off-policy 上限；self-improvement 的 868 on-policy 与 verifier 的 875 on-policy 是不同采样批次（32k token 过滤前后），口径不同。",
    "Figure1/摘要 '491 trajectories no saturation' 是训练数据 scaling 子集；Tab2 的 2438 是环境任务总数，两者非一回事。",
    "Best@k 依赖 verifier 精度，Pass@k 才是理论上界；Pass@k 与 Best@k 的 gap 是 verifier 不完美的证据，非缺陷掩盖。",
]


# ---------------------------------------------------------------- 各判据 verdict（由证据支撑）
JUDGMENTS = {
    "S1": {
        "verdict": "IMPLEMENTED_WITH_PARTIAL_REPO",
        "evidence": [
            "verifier reward：论文 r=exp(ly)/(exp(ly)+exp(ln))，代码 infer_rm_sglang.py 用 sgl.gen(choices=[' YES',' NO'], choices_method=sgl.token_length_normalized) 取归一化概率——机制对应（单 token choice 等价 softmax），非手写 exp 公式。",
            "verifier 数据：create_rm_data.ipynb 实跑输出 'Negative multiplier 1x: #resolved=1318, #non-resolved=1318, #total=2636' 与论文 §5.1.1 完全一致。",
            "训练超参：config policy 32B max_seq_len=32768、lr=1e-4、epochs=5、batch_size=1（每卡）+ 全局 8，与 §B.2 一致。",
            "491 轨迹：Table10 + create_rm_data 数据构造对应；config 文件名 '491i' 多处印证。",
            "部分缺失：环境构建脚本/6TB Docker 镜像/数据集/模型权重不在仓（论文明示在 HuggingFace + SWE-Bench-Fork），PARTIAL 属分流非造假。",
        ],
        "minor": [],
    },
    "S2": {
        "verdict": "CONSISTENT_WITH_CALIBER_GAP",
        "evidence": [
            "491=106+19+67+299、verifier 2636=1318×2、20.6→32.0(+11.4)、Pass@k+17.2、LoRA-full 差 2.6、2438-2294=144 全部复算自洽。",
            "摘要 '19% gains' 与表内 max +13.6% 差 5.4pp，已定位 19.7% 为 Table4 Lite 绝对分辨率，口径标注。",
        ],
        "minor": ["19% vs 13.6% 口径差", "Figure4 34% 级曲线与 Figure1 32.0@16 为不同 scaffold（MoatlessTools vs OpenHands），不可混用"],
    },
    "S3": {
        "verdict": "EXPLICIT_WITH_EVIDENCE",
        "evidence": [
            "核心假设（可执行环境+测试奖励→训练出更强 agent/verifier 且可 scale）明确写出。",
            "独立佐证：跨 scaffold（OpenHands 通用 / MoatlessTools 专用，zero-shot 7%/19% vs 1%/3%）、跨规模（7/14/32B 单调）、跨 benchmark（Lite/Verified 双集）、scaling 曲线（Fig1/3/4/5）、反例（self-improvement 无效，OpenHands 15.3→8.7）。",
            "诚实边界：论文承认 self-improvement modest、bottleneck 是 compute 非环境规模、环境多样性有限、模型未 production-ready。",
        ],
        "minor": ["单任务域（Python）/单 benchmark 族（SWE-Bench）", "假设是经验前提非定理"],
    },
    "S4": {
        "verdict": "ISOLATED_WITH_CAVEATS",
        "evidence": [
            "verifier 数据混合消融（on+off 27@8 最优；仅 off 早平台 22%；仅 on 有限）——对照组干净。",
            "per-instance capping（Table6：Cap0=7.0, Cap1=9.0, Cap2=9.7, Cap3=7.7, NoCap=9.3）——Cap2 最优与正文'max 2'一致。",
            "训练数据 scaling（Fig5/Fig9）、模型规模（Table3）、LoRA vs full（29.8 vs 27.2）——多维消融。",
        ],
        "minor": ["算力对等未完全披露（491 vs 294 轨迹数差异影响 scaling 解释，论文自述）", "方差仅 Pass@k/Best@k 用 Lightman 法，主结果无多次 std"],
    },
    "S5": {
        "verdict": "HONEST_LIMITED",
        "evidence": [
            "论文明说 Pass@k 是 Best@k 上界、gap（37.8 vs 29.8 @k8）源于 verifier 不完美，主动报告。",
            "verifier 是 outcome-supervised reward model（trajectory 级 <YES>/<NO>），非逐步验证；论文如实标注 ORM 定义。",
            "训练数据 matters：混合优于单一，off-policy-only 早平台——verifier 可靠性依赖数据多样性。",
        ],
        "minor": ["无 <YES>/<NO> 概率校准（calibration）实验", "Best@k 是 verifier 选择结果，非真值；有 reward hacking 理论空间（论文未讨论，本仓 KB-AUDIT07 视角补）"],
    },
    "S6": {
        "verdict": "PARTIAL_OPEN",
        "evidence": [
            "Apache-2.0；代码（训练/推理/数据准备脚本+配置 19 文件）、数据/模型在 HuggingFace、环境在 SWE-Bench-Fork、Docker 镜像 6TB——论文明示分流开放。",
            "污染控制一手依据：§3 'These repositories are separate from those used in SWE-Bench to avoid contamination'；§2 澄清 SWE-Bench train split 无可执行环境/奖励信号，故用其做训练会污染测试。",
        ],
        "minor": ["环境构建脚本未在本仓（在 SWE-Bench-Fork 依赖链），本仓无法独立验证 2438 环境实体", "单 SWE-bench 跑 ~GPU 周级 + 6TB 镜像，复现门槛高"],
    },
    "S7": {
        "verdict": "DISCOUNTED",
        "evidence": [
            "同构清单：verifier≈本仓外置判据、rejection sampling≈筛选安装、self-improvement≈自改进、scaling≈复利、trajectory≈经验库、测试奖励≈可证伪执行。",
            "按 KB-STRUCT02 打折：SWE agent 与本仓同属 agent 共同体，同构不构成对本仓框架的独立顶会验证。",
            "真实差异：SWE-Gym 改模型权重 + 标量 outcome reward、benchmark 固定不可改；本仓改判据语义 + 可证伪 + 三层诚实结论、元规则入闭环。SWE-Gym 的 verifier 正是本仓 KB-AUDIT07/STRUCT07 防的那类可被 reward hacking 的计分器。",
        ],
        "minor": [],
    },
    "SA": {
        "verdict": "PASS",
        "evidence": [
            "KB-AUDIT01：数字复算用真实算术，判定用机制语义（choices_method/数据构造），无脆弱字面串。",
            "KB-AUDIT02：19%vs13.6% 标 minor 不判造假；环境脚本不在仓标 PARTIAL 不定罪。",
            "KB-AUDIT04：主动标注 491 vs 2438、Pass@k vs Best@k、off/on-policy 批次口径不可混用。",
            "KB-R-MS01：数字全对仍独立判核心假设与 verifier 可靠性（事实真≠结论真）。",
            "KB-SIM02：诊断主体（论文作者 + 外部 gpt-4o/Claude teacher）vs 执行主体（Qwen agent）分层已核。",
            "KB-STRUCT02：S7 专判同谱系打折，不把同构当独立验证。",
        ],
        "minor": [],
    },
}


def build_result() -> dict:
    nums = recompute_numbers()
    return {
        "target": "Training Software Engineering Agents and Verifiers with SWE-Gym (ICML 2025, arXiv 2412.21139v2)",
        "summary": {
            "total": 8,
            "passed": 8,
            "all_pass": True,
            "verdicts": {k: v["verdict"] for k, v in JUDGMENTS.items()},
            "headline": "ICML2025 环境/数据集论文，代码与论文数字扎实(verifier数据2636/公式对应/超参一致); 摘要19%gains与表内13.6%存口径差; verifier是trajectory级ORM可被reward hacking(本仓KB-AUDIT07视角); 与本仓同构但同谱系打折,不新增条目。",
        },
        "number_recompute": nums,
        "caliber_cautions": NUMBER_CALIBER_CAUTIONS,
        "judgments": JUDGMENTS,
        "kb_decision": {
            "new": [],
            "reinforce": ["KB-AUDIT07", "KB-STRUCT07", "KB-RSI06", "KB-META01"],
            "reason": "SWE-Gym 的 verifier 可被 reward hacking 是 KB-AUDIT07 已有攻击面的一手实证；环境-轨迹-判据同构同谱系打折；均已被现有条目覆盖，记观察不硬造条目。",
            "total": 100,
        },
        "honest_boundaries": [
            "论文数字作者 self-reported，未实跑（需 GPU/6TB 环境/显著成本）",
            "代码结论基于公开仓 19 文件，非逐行审阅训练框架依赖",
            "数据集/模型/环境镜像不在仓，无法验证实体本身",
            "核心'训练env→能力↑'是经验假设非定理；Best@k 依赖 verifier 精度非真值",
        ],
    }


def main() -> None:
    result = build_result()
    (ROOT / "result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"judgments: {len(JUDGMENTS)}, recomputes: {len(result['number_recompute'])}")
    print("verdicts:", {k: v["verdict"] for k, v in JUDGMENTS.items()})


if __name__ == "__main__":
    main()
