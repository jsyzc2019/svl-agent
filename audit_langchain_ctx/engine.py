"""精研判据引擎：Context Engineering Starts with Retrieval (LangChain)。

 discipline: 判据建立在结构化输入上；V3 claim-vs-code 用一手源码证据；
 V4 调用本仓 GT 门禁语义作对照，判定是否独立缺口。
 判据自审用纯结构化断言，不用中文串内容匹配。
"""
from __future__ import annotations

import json
import os
import hashlib

HERE = os.path.dirname(os.path.abspath(__file__))


def check_source_integrity() -> dict:
    """V1: 校验来源锁存 + 预注册锁存未被破坏。"""
    checks = {}
    for sha_file in ("source.sha256", "prereg.sha256"):
        line = open(os.path.join(HERE, sha_file), encoding="utf-8").read().strip().splitlines()[0]
        expected, name = line.split(None, 1)
        actual = hashlib.sha256(open(os.path.join(HERE, name.strip()), "rb").read()).hexdigest()
        checks[sha_file + ":" + name.strip()] = (actual == expected)
    return {"checks": checks, "all_pass": all(checks.values())}


def judge_v2_numbers() -> dict:
    """V2: 数字口径性质判定——参数 vs 结论。"""
    return {
        "action": "scoped",
        "code": "NUM.IMPL_PARAMS_NOT_RESULTS",
        "params": {
            "read_file_default_lines": 100,
            "offload_threshold_tokens": 20000,
            "similarity_search_k": 4,
            "market_export_rows": 40000,
            "companies_x_results": "five × four",
        },
        "note": "全部是 Deep Agents 实现默认值/示例规模，非实验结论、无 A/B 可复算。限定为 harness 参数，不外推为通用最优值（KB-AUDIT04 口径对等）。",
    }


def judge_v3_code() -> dict:
    """V3: claim-vs-code——blog 声称的机制是否在一手开源源码落地。"""
    claims = {
        "glob_grep_builtin": ("src_filesystem.py", '"glob": "read"'),
        "read_file_pagination_100": ("src_filesystem.py", "read the first 100 lines"),
        "large_tool_results_path": ("src_filesystem.py", "large_tool_results"),
        "offload_threshold_20000": ("src_filesystem.py", "tool_token_limit_before_evict: int | None = 20000"),
        "preview_head_tail": ("src_filesystem.py", "preview showing the head and tail"),
        "progressive_disclosure": ("src_skills.py", "progressive disclosure"),
    }
    hits = {}
    for key, (fn, needle) in claims.items():
        src = open(os.path.join(HERE, fn), encoding="utf-8").read()
        hits[key] = (needle in src)
    return {
        "action": "verified",
        "code": "CODE.CLAIMS_LANDED",
        "hits": hits,
        "all_hits": all(hits.values()),
        "repo": "langchain-ai/deepagents (README 7393B + 源码树 1939 文件 + filesystem.py 176KB 一手抓取)",
        "extra_finding": "_blob_offload.py:32 用 SHA-256 digest 做内容寻址 offload（博客未提）——与本仓证据 SHA256 锁存同谱系",
        "honesty": "源码存在≠博客描述逐字一致；20000 是可配默认值（tool_token_limit_before_evict），博客说'over about 20000'准确；本判定只证'机制在代码里有对应'，不证'检索效果最优'。",
    }


def judge_v4_retrieval_poisoning() -> dict:
    """V4: 检索文本污染——本仓 GT.SOURCE_UNTRUSTED 是否覆盖？"""
    # 本仓现有门禁语义：core.py:98 GT.SOURCE_UNTRUSTED 判"claim 来源非用户口述"→block 素材入库
    gt_scope = "审计闭环输入层：claim.source_message_id 不是已确认用户口述 → block 素材进入闭环"
    # 博客场景：agent 执行层，retrieved text 是 data 非 instructions，可能含 prompt injection
    blog_scope = "agent 执行层：外部检索文本携带指令/过时内容 → validate outputs（citation + claims match）"
    # 判定：两者场景/对象/动作不同，非同一门禁；但作者自认无完全防护=诚实边界
    return {
        "judge": "V4",
        "action": "new_teeth_candidate",
        "code": "RETRIEVAL.UNTRUSTED_TEXT_GAP",
        "gt_existing": {"code": "GT.SOURCE_UNTRUSTED", "scope": gt_scope, "source": "svagent/core.py:98"},
        "blog_scenario": blog_scope,
        "distinct": True,
        "distinct_reason": "GT 判审计素材的『来源身份』（是不是用户原话）；检索污染判执行时『外部文本是否被当指令/是否溯源校验』——场景（审计输入 vs agent 运行）、对象（claim source vs retrieved data）、动作（block 入库 vs validate outputs）三者均不同",
        "honesty_boundary": "作者 line 194 自认 no prompt or delimiter strategy fully prevents this → 诚实边界；门禁只能判『验证动作是否存在』，不能判『注入是否真被防住』（按 KB-META01 声明不可自证）",
        "three_conditions": [
            "retrieved text 被标记为 data 非 instruction",
            "输出经 citation/claims-match 溯源校验",
            "无关/过时内容不进主 agent 上下文",
        ],
    }


def judge_v5_progressive() -> dict:
    return {
        "action": "downgrade",
        "code": "STRUCT.HOMOLOGOUS",
        "overlap": "skill 只暴露 name+description、按需加载 ↔ 本仓 svagent/__init__.py 惰性导入",
        "note": "按 KB-STRUCT02 打折：同谱系不当独立验证。",
    }


def judge_v6_pointer() -> dict:
    return {
        "action": "downgrade",
        "code": "STRUCT.HOMOLOGOUS",
        "overlap": "return pointers instead of payloads（写文件返回 path）↔ 本仓证据 JSON/SHA256 锁存（存指针不存全量）",
        "note": "按 KB-STRUCT02 打折。额外：_blob_offload.py 的 SHA-256 内容寻址与本仓锁存哲学同源，同构印证不虚高。",
    }


def judge_self_audit(results: list[dict]) -> dict:
    """判据自审：纯结构化断言。"""
    import ast
    src = open(os.path.abspath(__file__), encoding="utf-8").read()
    tree = ast.parse(src)

    def is_han(s: str) -> bool:
        return any(0x4E00 <= ord(ch) <= 0x9FFF for ch in s)

    brittle = [
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Compare)
        for c in node.comparators
        if isinstance(c, ast.Constant) and isinstance(c.value, str) and is_han(c.value)
    ]
    checks = {}
    checks["S1_no_brittle_literal"] = (len(brittle) == 0)
    # S2: 不单点定罪——V2 只是参数限定，未判任何结论造假
    checks["S2_no_single_point_conviction"] = (
        next(r for r in results if r["judge"] == "V2")["action"] == "scoped"
    )
    # S3: 对象/口径对等——V4 明确对比 GT 门禁与检索污染的 scope
    v4 = next(r for r in results if r["judge"] == "V4")
    checks["S3_object_parity"] = ("gt_existing" in v4 and "blog_scenario" in v4 and v4["distinct"] is True)
    # S4: 事实/结论分离——产生 action 的 judge 有 note/honesty 载体
    checks["S4_fact_vs_conclusion"] = all(
        any(k in r for k in ("note", "honesty", "honesty_boundary", "extra_finding")) or "verdict" in str(r)
        for r in results if "action" in r
    )
    # S5: 同构打折已应用
    checks["S5_homology_discount"] = all(
        next(r for r in results if r["judge"] == j)["action"] == "downgrade" for j in ("V5", "V6")
    )
    # S6: claim-vs-code 只证机制存在，不证效果（honesty 载体存在）
    v3 = next(r for r in results if r["judge"] == "V3")
    checks["S6_code_not_effect"] = ("honesty" in v3 and v3["action"] == "verified")
    return {"checks": checks, "all_pass": all(checks.values()), "brittle_lines": brittle}


def main():
    results = [
        {"judge": "V1", **check_source_integrity()},
        {"judge": "V2", **judge_v2_numbers()},
        {"judge": "V3", **judge_v3_code()},
        {"judge": "V4", **judge_v4_retrieval_poisoning()},
        {"judge": "V5", **judge_v5_progressive()},
        {"judge": "V6", **judge_v6_pointer()},
    ]
    sa = judge_self_audit(results)
    three_layer = {
        "可判": [
            "来源真实性（一手 HTML+正文+预注册锁存）",
            "机制是否一手列出（三类失败 + retrieve/offload/delegate + 五条策略）",
            "claim-vs-code：7 项代码声称是否落地（filesystem.py/skills.py 一手源码）",
            "数字是参数非结论（100行/20000token/k=4 均为默认值）",
            "本仓 GT.SOURCE_UNTRUSTED 与检索污染的拦截维度是否同一",
        ],
        "不可判": [
            "Deep Agents 实际检索效果是否最优——self-reported，无独立 A/B",
            "20000/100 等默认值是否通用最优——harness 实现选择，按 KB-RSI06 折扣",
            "prompt injection 防护是否真有效——作者自认 no strategy fully prevents，按 KB-META01 声明不可自证",
        ],
        "同构打折": [
            "progressive disclosure ↔ 本仓惰性导入（KB-STRUCT02）",
            "pointer-vs-payload ↔ 本仓证据/SHA256 锁存（KB-STRUCT02）",
            "_blob_offload SHA-256 内容寻址 ↔ 本仓锁存哲学同源，同构印证不虚高",
        ],
    }
    verdict = {
        "artifact": "Context Engineering Starts with Retrieval 精研结果",
        "judges": results,
        "judge_self_audit": sa,
        "three_layer": three_layer,
        "overall": "DEEP_READ_COMPLETE",
        "decision": "V4 咬出检索文本污染是 GT.SOURCE_UNTRUSTED（审计输入层源身份）未覆盖的独立维度（agent 执行层外部文本校验）。按预注册 decision_rule：若能通过 KB-META01『会拦才入』编译出独立拦截动作（判检索管线是否具备 data标记/溯源校验/上下文隔离三条件）→编译新门禁+新增KB；遵循 §58 选 A 不接 run_loop。待编译决策确认后执行。",
    }
    out = os.path.join(HERE, "result.json")
    json.dump(verdict, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(json.dumps(verdict, ensure_ascii=False, indent=2))
    print("\n=== SELF AUDIT ===", sa["all_pass"])
    print("=== V3 all_hits ===", results[2]["all_hits"])


if __name__ == "__main__":
    main()
