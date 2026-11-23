#!/usr/bin/env python3
"""一键生成 l3_external_audit_v2/ 空壳，外家只需按 <<<FILL>>> 填空。

用法：  python3 make_template.py [输出目录名]
默认：  l3_external_audit_v2

本脚本只生成"空壳 + 结构 + 纪律声明"，所有需要外家独立决策的内容
（选论文、造样本、写判据、定 gt、下裁决）都留 <<<FILL>>> 由外家填写。
"""
import datetime
import json
import os
import sys

OUT = sys.argv[1] if len(sys.argv) > 1 else "l3_external_audit_v2"
F = "<<<FILL>>>"
NOW = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def w(path, text):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write(text)
    print("  created", path)


def wj(path, obj):
    w(path, json.dumps(obj, ensure_ascii=False, indent=2) + "\n")


print("生成空壳 ->", OUT)
os.makedirs(OUT, exist_ok=True)

# --- T0 承诺（时间戳=现在，保证早于取料）--------------------------------
wj("prereg.json", {
    "experiment": "L3_GAP_TARGETED_EXTERNAL_V2",
    "phase": "T0_PREREG — 承诺先于执行，本文件时间戳必须最早",
    "timestamp": NOW,
    "chosen_paper": F,
    "avoid_list_acknowledged": True,
    "avoid_list_note": "已读作业书避开清单，所选论文不在其中（含任何版本）",
    "coverage_plan": {
        "declared": True,
        "note": "本轮覆盖计划：三类断言改写现象各至少一组",
        "NEGATION": "否定极性翻转：计划 >=1 组（例：never restores <-> restores）",
        "ASSERTION_TAIL": "断言补语删尾：计划 >=1 组（例：... yields no false positive <-> ... yields）",
        "CONNECTOR": "连接/让步词增删：计划 >=1 组（例：The direction, however, is <-> The direction, is）",
    },
    "sample_construction": F,
    "criterion_induction": F,
    "gt_definition": F,
    "verdict_tree": {
        "EXTERNAL_CONFIRMED": "判据在你自建 gt 上逐 case 一致率 >= 你预注册阈值，且纯函数准入通过",
        "EXTERNAL_DIVERGENT": "系统性给出与本仓同方向结论不同的结果",
        "EXTERNAL_PARTIAL": "部分 case 一致、部分分歧",
        "EXTERNAL_INCONCLUSIVE": "取料失败/429/判据无法准入/无法定 gt，诚实封顶不调参",
    },
    "discipline": {
        "no_post_hoc": True,
        "no_retry_to_pass": True,
        "l3_claimed": False,
        "absolute_claimed": False,
    },
})

# --- manifest ------------------------------------------------------------
wj("manifest.json", {
    "arxiv_id": F,
    "title": F,
    "url_abs": F,
    "url_full": F,
    "sources": ["abs", "full"],
    "note": "一手来源；两源均须 HTTP 200 并落地到 sources/",
})

# --- 取料日志（时间戳留空，取料时如实填 ISO）----------------------------
wj("sources/fetch_log.json", {
    "fetches": [
        {
            "role": "primary_abs",
            "url": F,
            "http_status": 200,
            "bytes": 0,
            "timestamp": F,
        },
        {
            "role": "primary_full",
            "url": F,
            "http_status": 200,
            "bytes": 0,
            "timestamp": F,
        },
    ],
    "note": "timestamp 填你实际取料的 ISO-8601（如 2026-11-23T18:10:00Z），必须晚于 prereg 时间戳",
})

# --- 全文纯文本 ----------------------------------------------------------
w("sources/paper_flat.txt", F + "\n（把论文全文纯文本粘到这里；判据逐字锚定用）\n")

# --- 裸样本（id 固定 N01..N12，只有三个键）------------------------------
pairs = [{"id": f"N{i:02d}", "text_a": F, "text_b": F} for i in range(1, 13)]
wj("samples_blind.json", {
    "note": "12 组文本对；键只能有 id/text_a/text_b；id 用 N01..N12；不得出现任何标签类字样或类型标注",
    "pairs": pairs,
})

# --- 判据纯函数骨架 ------------------------------------------------------
w("criterion.py", '''#!/usr/bin/env python3
"""判据：judge(text_a, text_b) -> (bool, reasons:list, anchors:list)。

纯函数纪律（违反即本仓判证据无效）：
  - 禁止 open/exec/eval/input/__import__
  - 禁止 import 或调用 random/time/datetime/os/sys/requests
  - 禁止硬编码任何样本 id 或读取标签（连注释里也别写样本编号，会被误判）
  - 只用字符串处理判断 text_a 是否完整保留 text_b 的断言
"""
def judge(text_a, text_b):
    # <<<FILL>>> 写你的确定性规则：
    #   text_a 是否完整保留了 text_b 的断言？
    #   否定词多出/丢失、断言补语被截、让步连接词被删 -> False
    #   仅格式/重复数字差异而断言相同 -> True
    # reasons/anchors 返回你据以判断的逐字片段（可为空列表）
    # 注意：别在这里写死任何样本编号字符串，纯函数检查会扫全文。
    return True, [], []
''')

# --- 判据说明（三段覆盖声明，默认含第9项关键词）--------------------------
w("criterion_note.md", """# 判据说明（criterion_note）

## 判据语义来源
<<<FILL>>> 你的判据为什么这样设计：目标语义是"text_a 是否完整保留 text_b 的断言"。

## 否定极性翻转（negation / polarity）
<<<FILL>>> 举一个你自己的样本例子（id + 两句逐字文本 + 你判据命中的锚点），
说明你的判据如何看到 never/restores、are not/are 这类否定极性差异。

## 断言补语删尾（complement / tail / truncation / assertion）
<<<FILL>>> 举一个你自己的样本例子，说明判据如何看到断言补语被截掉
（如 "... yields no false positive" 变成 "... yields"）。

## 连接/让步词增删（connector / concession / however）
<<<FILL>>> 举一个你自己的样本例子，说明判据如何看到 however/though 等
连接或让步词被增删导致断言关系改变。
""")

# --- 私有 gt -------------------------------------------------------------
wj("gt_private.json", {f"N{i:02d}": F for i in range(1, 13)})

# --- 逐样本判断 ----------------------------------------------------------
wj("judgments.json", {
    f"N{i:02d}": {"verdict": F, "reasons": [], "anchors": []}
    for i in range(1, 13)
})

# --- 裁决 ----------------------------------------------------------------
wj("verdict.json", {
    "verdict": F,
    "why": F,
    "metrics": {"agreement": F},
    "l3_claimed": False,
    "absolute_claimed": False,
    "note": "verdict 四选一：EXTERNAL_CONFIRMED / EXTERNAL_DIVERGENT / EXTERNAL_PARTIAL / EXTERNAL_INCONCLUSIVE",
})

# --- 执行日志 ------------------------------------------------------------
w("EXECUTION_LOG.md", f"""# 执行日志（EXECUTION_LOG）

时间线：T0 承诺 {NOW}（本脚本生成）→ T1 取料 → T2 出题 → T3 判据 →
T4 定 gt → T5 执行 → T6 裁决 → T7 打包。

<<<FILL>>> 如实记录每一步的时间、做法；若误读本仓任何禁止文件，也在此披露。
""")

print("完成。下一步：按各文件里的 <<<FILL>>> 填空，然后 pack.py 打包 -> selfcheck.py 自检（顺序见 README_FIRST.md）。")
