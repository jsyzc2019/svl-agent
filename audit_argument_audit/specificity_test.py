#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""§4gw 异质文本特异度测试。

诚实边界：只统计机械信号命中率，不判文本好坏、不判真假。
目的：检验规则在"训练题材（煽动文）之外"的假阳性/假阴性表现。
阳性对照应高命中；阴性对照（理性/跨语言/文学）应低命中。
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scan as S

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def demo_text():
    """从 HTML 抽取内置 DEMO，保证阳性对照一致。"""
    html = open(os.path.join(ROOT, "argument_audit.html"), encoding="utf-8").read()
    m = re.search(r"const DEMO=`([^`]*)`", html)
    return m.group(1) if m else ""


def load(path, limit=4000):
    p = os.path.join(ROOT, path)
    if not os.path.exists(p):
        return None
    return open(p, encoding="utf-8", errors="replace").read()[:limit]


def profile(text):
    r = S.scan(text)
    by = {h["id"]: h["count"] for h in r["hits"]}
    total = sum(by.values())
    return {
        "len": len(text),
        "n_signals": r["n_signals"],
        "total_hits": total,
        "per_1000": round(total / max(len(text), 1) * 1000, 2),
        "by_signal": by,
    }


def run():
    cases = [
        ("POS-DEMO 内置煽动文", demo_text(), "positive"),
        ("POS-爆款文元信息", load("article_input.txt"), "positive"),
        ("NEG-技术交接文档", load("SESSION_HANDOFF.md"), "negative"),
        ("NEG-网络小说", load("doupo_train.txt"), "negative"),
        ("NEG-DeepMind英文观点文", load("agi_essay_raw.txt"), "negative"),
        ("NEU-大摩文元信息", load("ms_article_input.txt"), "neutral"),
        ("NEU-康波文元信息", load("kondratieff_input.txt"), "neutral"),
    ]
    out = {}
    for name, text, kind in cases:
        if text is None:
            continue
        out[name] = {"kind": kind, **profile(text)}
    return out


if __name__ == "__main__":
    print(json.dumps(run(), ensure_ascii=False, indent=1))
