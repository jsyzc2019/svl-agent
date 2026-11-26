#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""论证取证工作台 · 机械信号扫描引擎（纯函数，规则来自 signal_rules.json）。
诚实边界：只标可疑信号，不判真假，不替代一手核验。"""
import json, os, re
ROOT = os.path.dirname(os.path.abspath(__file__))

def load_rules():
    return json.load(open(os.path.join(ROOT,"signal_rules.json"),encoding="utf-8"))

def scan(text, rules=None, min_hits=1):
    rules = rules or load_rules()
    hits=[]
    for r in rules["rules"]:
        matched=[]
        for pat in r["patterns"]:
            for m in re.finditer(pat,text):
                matched.append({"pattern":pat,"start":m.start(),"end":m.end(),"snippet":text[max(0,m.start()-12):m.end()+12]})
        if len(matched)>=min_hits:
            hits.append({"id":r["id"],"label":r["label"],"why":r["why"],"how":r["how"],"kb":r["kb"],"count":len(matched),"matches":matched[:8]})
    hits.sort(key=lambda h:-h["count"])
    return {"n_signals":len(hits),"hits":hits,"honest_bound":rules["honest_bound"]}

if __name__=="__main__":
    import sys
    text=sys.stdin.read()
    print(json.dumps(scan(text),ensure_ascii=False,indent=1))
