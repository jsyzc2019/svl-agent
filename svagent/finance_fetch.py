"""真实财报取数：东方财富公开接口，三家公司最近 5 个年报。

红线（遵循 eastmoney-stock-data skill）：
1. 严格校验返回行 SECUCODE 与目标一致，不一致即丢弃（防止串家公司）。
2. 取不到明确写 None，绝不用行业均值/往年数据填补。
3. reportName 用 ALL 列，不猜列名（猜错列会返回空 data，不是报错）。
4. 标注来源与报告期；审计意见仅年报有效。
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, asdict, field

import requests

API = "https://datacenter.eastmoney.com/securities/api/data/v1/get"
SOURCE = "东方财富公开数据接口 datacenter.eastmoney.com（非官方授权源）"

REPORTS = {
    "income": "RPT_F10_FINANCE_GINCOME",
    "balance": "RPT_F10_FINANCE_GBALANCE",
    "cashflow": "RPT_F10_FINANCE_GCASHFLOW",
    "main": "RPT_F10_FINANCE_MAINFINADATA",
}
# 金融业（银行）在 G 系列无数据，fallback 到简版三大表；口径字段更少，如实标注
REPORTS_SIMPLE = {
    "income": "RPT_DMSK_FN_INCOME",
    "balance": "RPT_DMSK_FN_BALANCE",
    "cashflow": "RPT_DMSK_FN_CASHFLOW",
}

# 随机种子固定抽取的目标（见 commentary 第17节）
TARGETS = [
    ("601166", "兴业银行", "601166.SH", "银行"),
    ("002415", "海康威视", "002415.SZ", "电子制造"),
    ("000725", "京东方A", "000725.SZ", "面板制造"),
]

# 造假对照组：已被监管处罚的真实案例，用于检出测试（非编造数据）。
# 康美药业 600518：2016-2018 虚增收入约300亿，2019 起审计意见转保留/无法表示。
# 乐视网 300104：2016 起资金链问题，2017 起审计意见转无法表示/保留。
FRAUD_CASES = [
    ("600518", "康美药业", "600518.SH", "医药(造假对照)"),
    ("300104", "乐视网", "300104.SZ", "互联网(造假对照)"),
]


@dataclass
class FetchResult:
    code: str
    name: str
    secucode: str
    industry: str
    source: str = SOURCE
    years: list[str] = field(default_factory=list)
    income: dict[str, dict] = field(default_factory=dict)     # year -> row
    balance: dict[str, dict] = field(default_factory=dict)
    cashflow: dict[str, dict] = field(default_factory=dict)
    main: dict[str, dict] = field(default_factory=dict)
    opinion: dict[str, str | None] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    rejected_rows: int = 0  # 因 SECUCODE 不匹配被丢弃的行数

    def to_dict(self) -> dict:
        return asdict(self)


def _fetch(report_name: str, secucode: str, pagesize: int = 60) -> list[dict]:
    p = {
        "reportName": report_name,
        "columns": "ALL",
        "filter": f'(SECUCODE="{secucode}")',
        "pageSize": pagesize,
        "sortColumns": "REPORT_DATE",
        "sortTypes": "-1",
    }
    r = requests.get(API, params=p, timeout=40)
    r.raise_for_status()
    d = r.json()
    if not d.get("success"):
        # 9201 = 报表名有效但该组合无数据；9501 = 表名错
        return [] if d.get("code") == 9201 else []
    return (d.get("result") or {}).get("data") or []


def _annual_years(rows: list[dict], secucode: str, res: FetchResult,
                  simple: bool = False) -> dict[str, dict]:
    """只保留年报，校验 SECUCODE，按年索引。
    G 系列：REPORT_TYPE=='年报'；简版表：无 REPORT_TYPE，用 REPORT_DATE 的 12-31 判年报。
    """
    by_year: dict[str, dict] = {}
    for row in rows:
        if row.get("SECUCODE") != secucode:
            res.rejected_rows += 1
            continue
        date = row.get("REPORT_DATE", "")
        if not date.startswith(tuple(f"{y}-12-" for y in range(2010, 2027))):
            continue
        if not simple and row.get("REPORT_TYPE") != "年报":
            continue
        by_year[date[:4]] = row
    return by_year


def fetch_company(code: str, name: str, secucode: str, industry: str,
                  n_years: int = 5, year_window: tuple[int, int] | None = None) -> FetchResult:
    """year_window: 指定年份闭区间（如造假案 (2016,2020)）；None=取最近 n_years。"""
    res = FetchResult(code=code, name=name, secucode=secucode, industry=industry)
    raw: dict[str, list[dict]] = {}
    for key, rname in REPORTS.items():
        try:
            raw[key] = _fetch(rname, secucode)
            time.sleep(0.3)
        except Exception as e:  # 取不到明确记录，不填补
            res.errors.append(f"{key}: {type(e).__name__}: {e}")
            raw[key] = []

    # G 系列若三表全空（金融业），整家 fallback 到简版表，并标注口径
    use_simple = not raw["balance"] and not raw["cashflow"]
    if use_simple:
        res.errors.append("G系列三表无数据（疑金融业），整家fallback简版RPT_DMSK_FN_*；口径字段更少")
        for key, rname in REPORTS_SIMPLE.items():
            try:
                raw[key] = _fetch(rname, secucode)
                time.sleep(0.3)
            except Exception as e:
                res.errors.append(f"simple.{key}: {type(e).__name__}: {e}")
                raw[key] = []
        raw["main"] = []

    inc = _annual_years(raw["income"], secucode, res, simple=use_simple)
    bal = _annual_years(raw["balance"], secucode, res, simple=use_simple)
    cash = _annual_years(raw["cashflow"], secucode, res, simple=use_simple)
    main = _annual_years(raw["main"], secucode, res)

    all_years = set(inc) | set(bal) | set(cash) | set(main)
    if year_window is not None:
        lo, hi = year_window
        years = sorted(y for y in all_years if lo <= int(y) <= hi)
    else:
        years = sorted(all_years, reverse=True)[:n_years]
    res.years = sorted(years)
    for y in res.years:
        res.income[y] = inc.get(y) or {}
        res.balance[y] = bal.get(y) or {}
        res.cashflow[y] = cash.get(y) or {}
        res.main[y] = main.get(y) or {}
        res.opinion[y] = (inc.get(y) or {}).get("OPINION_TYPE")
        missing = [k for k in ("income", "balance", "cashflow", "main")
                   if not {"income": inc, "balance": bal, "cashflow": cash, "main": main}[k].get(y)]
        if missing:
            res.errors.append(f"{y}: 缺 {','.join(missing)}（未填补）")
    return res


def save_all(path: str = "/workspace/financials.json") -> list[FetchResult]:
    # 对照组：正常公司取最近5年；造假对照取案发窗口 2016-2020
    results = [fetch_company(*t, n_years=5) for t in TARGETS]
    results += [fetch_company(*t, year_window=(2016, 2020)) for t in FRAUD_CASES]
    payload = {
        "source": SOURCE,
        "note": "公开接口非官方授权源；金额单位多为元；合并报表口径；审计意见仅年报有效；"
                "造假对照组年份为案发窗口2016-2020，正常组为最近5年2021-2025",
        "companies": [r.to_dict() for r in results],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    return results


def load_all(path: str = "/workspace/financials.json") -> list[FetchResult]:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    out = []
    for c in d["companies"]:
        r = FetchResult(**c)
        out.append(r)
    return out


if __name__ == "__main__":
    rs = save_all()
    for r in rs:
        print(f"{r.code} {r.name} [{r.industry}] years={r.years} "
              f"rejected={r.rejected_rows} errors={r.errors}")
        for y in r.years:
            inc = r.income.get(y, {})
            print(f"   {y} opinion={r.opinion.get(y)} "
                  f"rev={inc.get('TOTAL_OPERATE_INCOME')} np={inc.get('PARENT_NETPROFIT')}")
