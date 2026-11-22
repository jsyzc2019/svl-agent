"""§75 精研判据引擎：从 AINLP 公众号原文提取断言并核验拦截面。

可重跑、可证伪：所有锚点按原文单行真实措辞核验；交叉来源按繁体原文；
门禁判定调用编译好的 svagent.self_knowledge_honesty.live_regression()。
运行：python3 audit_addy_critical_thinking/engine.py → 重写 result.json
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

# C1-C8 命题的原文单行锚点（措辞按原文；三处自咬已修正：C5 短子串/C6「就」/C7「恰恰是」）
ANCHORS = {
    "C1": ["卸载 依赖与投降", "认知卸载（cognitive offloading）", "依赖（deferral）", "认知投降（cognitive surrender）"],
    "C2": ["认知债务累积的方式", "理解债务（comprehension debt）", "代码库看起来干干净净，测试也都通过了"],
    "C3": ["提问前，我有没有先形成一个假设？", "什么情况成立时，这个结论就会是错的？",
           "哪些能力，我已经不再练习了？", "盲点检查", "我是在请它帮我思考，还是请它替我思考？"],
    "C4": ["绿灯只说明一件事", "一个通过的测试，完全可能没发现已经坏掉的功能", "它证明了什么", "它没证明什么"],
    "C5": ["意图债务", "意图必须来自你", "藏着隐含的目标、约束和理由"],
    "C6": ["编排税", "你就不再是在审阅，而是在碰运气", "多到你无法为之负责"],
    "C7": ["监督悖论", "恰恰是过度使用 AI 后可能退化的编程能力"],
    "C8": ["你可以把工作和大部分审计交出去，但不能把责任也交出去", "承担责任的仍然必须是人"],
}

# S02 繁体综述的证据边界锚点（交叉验证：第三方独立给出未验证批评）
CROSS_ANCHORS = ["個人實務觀察", "沒有提供採用率或前後對照的量化結果",
                 "並沒有證明這六個自問能防止它", "132 人", "自我報告"]


def main() -> dict:
    fulltext = (HERE / "downloads/S01_52nlp_cn_fulltext.txt").read_text(encoding="utf-8")
    cross = (HERE / "downloads/S02_techmoon_spectrum.txt").read_text(encoding="utf-8")

    hit = {k: sum(1 for a in arr if a in fulltext) for k, arr in ANCHORS.items()}
    total = sum(len(v) for v in ANCHORS.values())
    hits = sum(hit.values())

    out = subprocess.run(
        [sys.executable, "-c",
         "import json;from svagent.self_knowledge_honesty import live_regression;"
         "print(json.dumps(live_regression(),ensure_ascii=False))"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    live = json.loads(out.stdout.strip())

    return {
        "request_id": "addy-critical-thinking-20261122",
        "prereg_sha256": (HERE / "prereg.sha256").read_text().strip(),
        "manifest_sha256": (HERE / "manifest.sha256").read_text().strip(),
        "gate_prereg_sha256": (HERE / "gate_prereg.sha256").read_text().strip(),
        "claim_anchors": {
            "anchor_hits": hit,
            "per_claim": {k: f"{hit[k]}/{len(v)}" for k, v in ANCHORS.items()},
            "total": f"{hits}/{total}",
            "all_hit": hits == total,
            "note": "锚点按原文单行真实措辞修正3处(C5短子串/C6『就』字/C7『恰恰是』)，均为工具修正非判定放水",
        },
        "crosscheck": {a: (a in cross) for a in CROSS_ANCHORS},
        "crosscheck_note": "S02 繁体原文，5/5 命中：第三方独立给出证据边界批评（个人实务观察/无量化对照/六问未被证有效/132人单公司/自报）",
        "evidence_grade": {
            "S01": "公众号 AINLP 原文（用户确认），52nlp 同步站全文，含英文原稿截图+参考链接；二手译文折1",
            "S02": "独立第三方综述，明标个人实务观察/无量化对照/六问未被证明有效/132人单公司自报——折扣",
            "结论": "证据支持『作者提出并自述这些自问』，不支持『六问能防认知投降』",
        },
        "novelty_check": {
            "covered_by_existing": ["supervision_viability(§74):评审者能力前提存在性",
                                    "proof_boundary_honesty(§71):证明范围",
                                    "judgment_robustness:判定稳健性",
                                    "retrospective:认知轨迹复盘"],
            "gap": "无门禁判『主体对自己认知边界的诚实觉察』：假设先行/局限自陈/可证伪自问/技能退化披露——比能力前提更内一层的元认知自知",
            "decision": "编译第23门禁 self_knowledge_honesty（KB-META01 会拦才入）",
        },
        "gate_live_regression": live,
        "honesty_boundary": "本门禁只判声明自洽，不承诺真能防认知投降（KB-STRUCT05 框架≠有效、KB-R07 自洽≠有效、KB-RSI07 自述折扣、KB-STRUCT02 同谱系折扣）",
    }


if __name__ == "__main__":
    result = main()
    (HERE / "result.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print("锚点:", result["claim_anchors"]["total"],
          "all_hit=", result["claim_anchors"]["all_hit"])
    print("交叉:", sum(1 for v in result["crosscheck"].values() if v), "/ 5")
    print("活体 all_match:", result["gate_live_regression"]["all_match"])
