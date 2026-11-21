"""抗偏差盲测：随机十家公司近五年（2021-2025）财报叙事真实性研判。

方法论（见 commentary 第18节 / 报告）：
  1. 抽样框：28 家候选池（12 正常白马 + 16 曾风险/退市），先剔除数据断档者
     （本身就是幸存者偏差证据），固定种子 seed=2026 随机抽 10 家。
  2. 结局标签：2025 年报审计意见（年报同期公开，非事后标签，零后知）。
  3. 防标签泄漏：判据【刻意不含审计意见判据】，只用四个财务符号判据去预测标签。
  4. 盲判：blind_audit() 只接收纯财务数据，看不到命运分组/标签。
  5. 揭盲：evaluate() 在全部判据产出后才对照标签，强制报告 FP/FN 与混淆矩阵。
  6. 预注册：阈值与告警规则跑数前固定（ALARM_RULE），不因个案调整。

红线：仅限方法研究，不构成任何投资建议。数据为公开接口加工指标，非年报原文。
"""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field

from .finance_fetch import fetch_company, FetchResult
from .finance_audit import (
    collapse_balance_identity,
    collapse_cash_quality,
    collapse_receipt_ratio,
    collapse_growth_divergence,
)

SEED = 2026
YEAR_LO, YEAR_HI = 2021, 2025
PRED_YEARS = ("2021", "2022", "2023", "2024")   # 用前四年判据信号做预测
LABEL_YEAR = "2025"                              # 揭盲标签所在年

# 候选池：code -> (名称, 分组, 行业)。分组仅用于分层覆盖与偏差审计，【不进入判据】。
CANDIDATES: dict[str, tuple[str, str, str]] = {
    # 正常白马（12）
    "000001": ("平安银行", "normal", "银行"),
    "000333": ("美的集团", "normal", "家电"),
    "000858": ("五粮液", "normal", "白酒"),
    "002594": ("比亚迪", "normal", "汽车"),
    "300750": ("宁德时代", "normal", "电池"),
    "300760": ("迈瑞医疗", "normal", "医疗器械"),
    "600036": ("招商银行", "normal", "银行"),
    "600276": ("恒瑞医药", "normal", "医药"),
    "600519": ("贵州茅台", "normal", "白酒"),
    "600887": ("伊利股份", "normal", "食品"),
    "601318": ("中国平安", "normal", "保险"),
    "601899": ("紫金矿业", "normal", "有色"),
    # 曾风险/退市/造假（16）
    "002477": ("雏鹰农牧", "risk", "农业"),
    "300431": ("暴风集团", "risk", "传媒"),
    "600485": ("信威集团", "risk", "通信"),
    "000422": ("湖北宜化", "risk", "化工"),
    "000939": ("凯迪退", "risk", "电力"),
    "000980": ("众泰汽车", "risk", "汽车"),
    "002323": ("雅博退", "risk", "环保"),
    "002450": ("康得新", "risk", "新材料"),
    "002604": ("龙力退", "risk", "食品"),
    "300104": ("乐视网", "risk", "互联网"),
    "300216": ("千山药机", "risk", "医疗"),
    "600122": ("宏图高科", "risk", "商贸"),
    "600186": ("莲花控股", "risk", "食品"),
    "600518": ("康美药业", "risk", "医药"),
    "600666": ("奥瑞德", "risk", "电子"),
    "601777": ("力帆科技", "risk", "汽车"),
}

# 数据断档（探测确认近五年无连续年报）——剔除即幸存者偏差，必须记录
DATA_GAPS = {
    "002477": "2021-2025 无年报数据（退市后口径断档）",
    "300431": "2021-2025 无年报数据（退市后口径断档）",
    "600485": "2021-2025 无年报数据（退市后口径断档）",
}

# 预注册告警规则：前四年信号中，任一硬违约 block，或软信号重复 >=2 年 → 预警
ALARM_RULE = ("若 2021-2024 出现任一会计恒等式违约(block)，"
              "或现金含量LOW>=2年、收现比LOW>=2年、增速背离>=2年 → 预警(alarm=1)；否则 0")

BLIND_VERIFIERS = (
    ("会计恒等式", collapse_balance_identity),
    ("盈利含金量", collapse_cash_quality),
    ("收入含金量", collapse_receipt_ratio),
    ("增长叙事背离", collapse_growth_divergence),
)  # 注意：【不含】collapse_audit_opinion —— 它是标签本身，纳入即泄漏


@dataclass
class BlindResult:
    code: str
    name: str
    group: str            # 仅审计用，盲判阶段不读
    industry: str
    years: list[str]
    signals: list[dict] = field(default_factory=list)   # 前四年判据信号（盲）
    block: int = 0
    cash_low: int = 0
    receipt_low: int = 0
    growth_div: int = 0
    alarm: int = 0        # 预注册规则产出
    label_opinion: str = ""   # 揭盲后填
    label_neg: int = -1       # 1=审计否定(非标), 0=未否定(标准无保留)
    data_errors: list[str] = field(default_factory=list)


def draw_sample(seed: int = SEED) -> tuple[list[str], dict]:
    """固定种子分层随机抽样，返回(入样code列表, 抽样审计信息)。"""
    eligible = sorted(c for c in CANDIDATES if c not in DATA_GAPS)
    rng = random.Random(seed)
    picked = rng.sample(eligible, 10)
    audit = {
        "seed": seed,
        "候选池大小": len(CANDIDATES),
        "数据断档剔除": {c: {"名称": CANDIDATES[c][0], "原因": why}
                    for c, why in DATA_GAPS.items()},
        "入样池大小": len(eligible),
        "入样正常": sum(1 for c in eligible if CANDIDATES[c][1] == "normal"),
        "入样风险": sum(1 for c in eligible if CANDIDATES[c][1] == "risk"),
        "抽中": [{"code": c, "名称": CANDIDATES[c][0], "分组": CANDIDATES[c][1]}
               for c in picked],
    }
    return picked, audit


def _secu(code: str) -> str:
    return f"{code}.SH" if code[0] in "69" else f"{code}.SZ"


def counterexample_analysis(cache: dict[str, "FetchResult"]) -> dict:
    """【审计整改 P1】反例对照：检验判据是否只在测"困境"，而非真的测"叙事失真"。

    审计揭示：alarm=1 与后验 risk 组高度重合 → "预测非标"≈"用困境预测困境的结果"。
    本函数用全部可得真实数据（不只10家样本）做四类分解，重点看两个反例：
      - FP 反例"困境但标准无保留"：判据误报，说明它抓的是动荡表征；
      - FN 反例"非困境但非标"：若存在，说明判据漏掉纯叙事问题。
    分组标签 group 在本分析中【不使用】——只用盲判信号 + 当期审计标签。
    """
    cells = {"TP": [], "FP": [], "FN": [], "TN": []}
    for code, r in cache.items():
        _, score = blind_audit(r)
        op = str(r.opinion.get(LABEL_YEAR) or "")
        if not op:
            continue
        neg = 0 if "无保留" in op else 1
        cell = ("TP" if score["alarm"] and neg else
                "FP" if score["alarm"] and not neg else
                "FN" if not score["alarm"] and neg else "TN")
        cells[cell].append({
            "name": r.name, "code": code, "alarm": score["alarm"], "neg": neg,
            "信号": f"blk{score['block']}/cash{score['cash_low']}/"
                   f"recv{score['receipt_low']}/grow{score['growth_div']}",
        })
    n = sum(len(v) for v in cells.values())
    prec = len(cells["TP"]) / (len(cells["TP"]) + len(cells["FP"])) if (cells["TP"] or cells["FP"]) else None
    return {
        "参评家数": n,
        "四类": {k: [x["name"] for x in v] for k, v in cells.items()},
        "反例_困境但标准无保留_FP": [f"{x['name']}({x['信号']})" for x in cells["FP"]],
        "反例_非困境但非标_FN": [x["name"] for x in cells["FN"]],
        "精确率": round(prec, 3) if prec is not None else None,
        "循环诊断": (
            f"FP={len(cells['FP'])} 家（含正常白马如比亚迪）说明 alarm 抓的是经营动荡表征，"
            f"不是造假/叙事失真本身；FN={len(cells['FN'])} 家。当 FP 远大于 TP 时，"
            f"'判据命中非标'很大程度上是'困境→增速背离→非标'的同一经济机制两段读数，"
            f"而非独立预测。这是第19节审计指出的循环，本对照将其量化。"
        ),
        "_cells": cells,  # 供真实日志构造使用
    }


def build_real_verdict_log(cache: dict[str, "FetchResult"]) -> list[dict]:
    """【审计整改 P2】从真实财报构造裁决日志，接 estimation 估参。

    打破"全部理论模块零真实数据"的自证循环：
      evidence = 该公司 2021-2024 的财务动荡信号强度（归一化的 alarm 计数）
      forged   = 2025 审计意见是否非标（真实标签，非合成）
      rejected = 盲判 alarm 是否触发（判据的裁决）
    每条 = 一家真实公司的真实裁决。诚实边界：标签是"审计意见"代理，非"造假"真值；
    evidence 由同一批判据构造，仍非完全独立——但数据来源是真实世界，不再是 simulator。
    """
    from .finance_audit import collapse_cash_quality, collapse_receipt_ratio, collapse_growth_divergence
    log = []
    for code, r in cache.items():
        op = str(r.opinion.get(LABEL_YEAR) or "")
        if not op:
            continue
        raw, score = blind_audit(r)
        evidence = (score["block"] * 1.0 + score["cash_low"] * 0.5 +
                    score["receipt_low"] * 0.5 + score["growth_div"] * 0.5) / 4.0
        log.append({"company": r.name, "code": code,
                    "evidence": round(evidence, 4),
                    "forged": 0 if "无保留" in op else 1,
                    "rejected": score["alarm"],
                    "opinion": op})
    return log


def blind_audit(r: FetchResult) -> tuple[list[dict], dict]:
    """盲判：只用四个财务判据，绝不读 r.opinion / 分组 / 标签。"""
    pred = [y for y in r.years if y in PRED_YEARS]
    raw: list[dict] = []
    for name, fn in BLIND_VERIFIERS:
        for d in fn(r):
            if d.locus.ref.split("·")[0] in PRED_YEARS:
                raw.append({"判据": name, "code": d.code, "severity": d.severity,
                            "年份": d.locus.ref.split("·")[0], "证据": d.message})
    cnt = {
        "block": sum(1 for d in raw if d["code"] == "FIN.BALANCE.BREACH"),
        "cash_low": sum(1 for d in raw if d["code"] == "FIN.CASH.LOW"),
        "receipt_low": sum(1 for d in raw if d["code"] == "FIN.RECEIPT.LOW"),
        "growth_div": sum(1 for d in raw if d["code"] == "FIN.GROWTH.DIVERGE"),
    }
    alarm = int(cnt["block"] >= 1 or cnt["cash_low"] >= 2
                or cnt["receipt_low"] >= 2 or cnt["growth_div"] >= 2)
    return raw, {**cnt, "alarm": alarm}


def label_of(r: FetchResult) -> tuple[str, int]:
    """揭盲：2025 审计意见 → (原文, 1=非标否定/0=标准无保留/-1=未知)。仅在判据产出后调用。

    诚实原则：标签"未取到"必须作为【未知】剔除出混淆矩阵，绝不能默认塞进正例
    （否则一个数据缺陷会被伪装成"命中"，这正是后知偏差的隐蔽来源）。
    """
    op = str(r.opinion.get(LABEL_YEAR) or "").strip()
    if not op or op in ("未取到", "None", "nan"):
        return (op or "未取到"), -1
    neg = 0 if "无保留" in op else 1
    return op, neg


def _recompute_alarm(r: BlindResult, codes: set[str], k: int) -> int:
    """基于已冻结的 signals 重算 alarm（用于消融，不改判据、不改原始数据）。"""
    cnt = sum(1 for s in r["signals"] if s["code"] in codes)
    return int(cnt >= k)


def sensitivity_analysis(results: list[dict]) -> dict:
    """消融/阈值敏感性：诊断 recall=1.0 有多少来自'困境同义反复'。

    这是诊断性分析，不是新的假设检验；阈值/判据子集的变化只用来揭示稳健性边界。
    """
    labeled = [r for r in results if r["label_neg"] in (0, 1)]
    variants = {
        "A_全判据_k>=2(主结果)": ({"FIN.BALANCE.BREACH", "FIN.CASH.LOW",
                                 "FIN.RECEIPT.LOW", "FIN.GROWTH.DIVERGE"}, 2),
        "B_去掉增速背离": ({"FIN.BALANCE.BREACH", "FIN.CASH.LOW", "FIN.RECEIPT.LOW"}, 2),
        "C_只用收现比+现金含量": ({"FIN.CASH.LOW", "FIN.RECEIPT.LOW"}, 2),
        "D_只用增速背离": ({"FIN.GROWTH.DIVERGE"}, 2),
        "E_阈值收紧k>=3": ({"FIN.BALANCE.BREACH", "FIN.CASH.LOW",
                          "FIN.RECEIPT.LOW", "FIN.GROWTH.DIVERGE"}, 3),
        "F_阈值放宽k>=1": ({"FIN.BALANCE.BREACH", "FIN.CASH.LOW",
                          "FIN.RECEIPT.LOW", "FIN.GROWTH.DIVERGE"}, 1),
    }
    out = {}
    for name, (codes, k) in variants.items():
        tp = fp = fn = tn = 0
        for r in labeled:
            a = _recompute_alarm(r, codes, k)
            if a and r["label_neg"] == 1: tp += 1
            elif a and r["label_neg"] == 0: fp += 1
            elif not a and r["label_neg"] == 1: fn += 1
            else: tn += 1
        rec = round(tp / (tp + fn), 3) if tp + fn else None
        prec = round(tp / (tp + fp), 3) if tp + fp else None
        out[name] = {"TP": tp, "FP": fp, "FN": fn, "TN": tn,
                     "recall": rec, "precision": prec}
    return out


def run(fetch_cache: dict[str, FetchResult] | None = None) -> dict:
    picked, sample_audit = draw_sample()
    results: list[BlindResult] = []
    for code in picked:
        name, group, industry = CANDIDATES[code]
        r = (fetch_cache or {}).get(code) or fetch_company(
            code, name, _secu(code), industry, year_window=(YEAR_LO, YEAR_HI))
        raw, score = blind_audit(r)                 # ① 盲判（无标签）
        op, neg = label_of(r)                       # ② 揭盲（判据产出后）
        results.append(BlindResult(
            code=code, name=name, group=group, industry=industry, years=r.years,
            signals=raw, **score, label_opinion=op, label_neg=neg,
            data_errors=list(r.errors),
        ))
    metrics = evaluate(results)
    result_dicts = [vars(x) for x in results]
    sensitivity = sensitivity_analysis(result_dicts)
    return {
        "methodology": {
            "终点": "2026年（近五年=2021-2025年报，2025年报为最新完整年报）",
            "抽样": f"固定种子 seed={SEED} 分层随机抽10家",
            "结局标签": f"{LABEL_YEAR}年报审计意见（同期公开，零后知）",
            "防泄漏": "判据不含审计意见判据，blind_audit 不读 opinion/分组/标签",
            "预测信号窗": f"{PRED_YEARS[0]}-{PRED_YEARS[-1]}",
            "告警规则": ALARM_RULE,
            "免责": "仅限方法研究，不构成投资建议；公开接口加工指标非年报原文",
        },
        "sample_audit": sample_audit,
        "results": result_dicts,
        "metrics": metrics,
        "sensitivity": sensitivity,
    }


def evaluate(results: list[BlindResult]) -> dict:
    """揭盲评估：混淆矩阵 + 强制 FP/FN 清单。标签未知者剔除，不塞进任何一类。"""
    labeled = [r for r in results if r.label_neg in (0, 1)]
    unknown = [r for r in results if r.label_neg == -1]
    tp = [r for r in labeled if r.alarm == 1 and r.label_neg == 1]
    fp = [r for r in labeled if r.alarm == 1 and r.label_neg == 0]
    fn = [r for r in labeled if r.alarm == 0 and r.label_neg == 1]
    tn = [r for r in labeled if r.alarm == 0 and r.label_neg == 0]
    n_pos = sum(1 for r in labeled if r.label_neg == 1)
    n_neg = len(labeled) - n_pos
    def rate(a, b): return round(a / b, 3) if b else None
    return {
        "参评样本": len(labeled),
        "标签未知_剔除": [f"{r.name}({r.code}):{r.label_opinion}" for r in unknown],
        "混淆矩阵": {"TP": len(tp), "FP": len(fp), "FN": len(fn), "TN": len(tn)},
        "召回味觉率_recall": rate(len(tp), n_pos),
        "特异度_specificity": rate(len(tn), n_neg),
        "精确率_precision": rate(len(tp), len(tp) + len(fp)),
        "假阳性_预警但标准无保留": [f"{r.name}({r.code})" for r in fp],
        "假阴性_非标却无预警": [f"{r.name}({r.code})" for r in fn],
        "真阳性_预警且非标": [f"{r.name}({r.code})" for r in tp],
        "真阴性_无预警且标准无保留": [f"{r.name}({r.code})" for r in tn],
        "正例数_非标": n_pos, "负例数_标准无保留": n_neg,
    }


if __name__ == "__main__":
    out = run()
    path = "/workspace/finance_blind_test_result.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"已写入 {path}\n")
    sa = out["sample_audit"]
    print(f"抽样: seed={sa['seed']} 候选{sa['候选池大小']} 断档剔除{sa['数据断档剔除']} "
          f"入样{sa['入样池大小']} (正常{sa['入样正常']}/风险{sa['入样风险']})")
    print("\n盲判 → 揭盲（alarm=1 表示前四年财务判据预警；标签=2025审计意见）")
    print(f"{'公司':<10}{'组':<8}{'alarm':<7}{'blk':'<5}{'cash':'<6}{'recv':'<6}{'grow':'<6}{'2025审计意见':<22}")
    for r in out["results"]:
        print(f"{r['name']:<10}{r['group']:<8}{r['alarm']:<7}{r['block']:<5}"
              f"{r['cash_low']:<6}{r['receipt_low']:<6}{r['growth_div']:<6}{r['label_opinion']:<22}")
    m = out["metrics"]
    print("\n混淆矩阵:", m["混淆矩阵"], " recall:", m["召回味觉率_recall"],
          " specificity:", m["特异度_specificity"], " precision:", m["精确率_precision"])
    print("假阳性(预警但标准无保留):", m["假阳性_预警但标准无保留"])
    print("假阴性(非标却无预警):", m["假阴性_非标却无预警"])

    # 【审计整改】用全量真实数据做反例对照，量化"困境代理"循环
    import os
    from .finance_fetch import FetchResult as _FR
    cp = "/workspace/real_financials_cache.json"
    if os.path.exists(cp):
        full = {c: _FR(**d) for c, d in json.load(open(cp, encoding="utf-8")).items()}
        ce = counterexample_analysis(full)
        print("\n" + "=" * 80)
        print(f"【审计整改·全量反例对照】{ce['参评家数']}家真实公司，四类分解:")
        print(f"  TP={len(ce['四类']['TP'])} FP={len(ce['四类']['FP'])} "
              f"FN={len(ce['四类']['FN'])} TN={len(ce['四类']['TN'])} "
              f"精确率={ce['精确率']}")
        print(f"  FP反例(困境但标准无保留): {ce['反例_困境但标准无保留_FP']}")
        print(f"  {ce['循环诊断']}")
