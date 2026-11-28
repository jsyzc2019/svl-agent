#!/usr/bin/env python3
"""Holdout scorer: records-only. Scores any criterion on the frozen holdout.
Never writes to verdict/l3/authority. Reports accuracy +/- standard error.
"""
import json,os,sys,math,hashlib

HERE=os.path.dirname(os.path.abspath(__file__))
CRIT_DIR=os.path.join(HERE,'..','received','l3_external_audit_v2')

def wilson(k,n,z=1.96):
    if n==0: return (0.0,0.0)
    p=k/n
    d=1+z*z/n
    c=(p+z*z/(2*n))/d
    h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
    return (max(0,c-h),min(1,c+h))

def load_criterion(path):
    import importlib.util
    spec=importlib.util.spec_from_file_location('cand_crit',path)
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m.judge

def score(judge, pairs):
    k=0; rows=[]
    for p in pairs:
        got=judge(p['text_a'],p['text_b'])
        gotb=bool(got[0]) if isinstance(got,tuple) else bool(got)
        ok=gotb==p['expected']
        k+=int(ok)
        rows.append({'id':p['id'],'rule':p['rule'],'expected':p['expected'],'got':gotb,'ok':ok})
    n=len(pairs); acc=k/n
    lo,hi=wilson(k,n)
    se=math.sqrt(acc*(1-acc)/n) if n else 0.0
    return {'correct':k,'total':n,'accuracy':round(acc,4),'se':round(se,4),
            'wilson95':[round(lo,4),round(hi,4)],'rows':rows}

def score_current():
    sys.path.insert(0,CRIT_DIR)
    import criterion
    pairs=json.load(open(os.path.join(HERE,'samples_holdout.json'),encoding='utf-8'))['pairs']
    return score(criterion.judge,pairs)

if __name__=='__main__':
    mode=sys.argv[1] if len(sys.argv)>1 else 'current'
    if mode=='current':
        print(json.dumps(score_current(),ensure_ascii=False,indent=2))
    elif mode=='always_pass':
        pairs=json.load(open(os.path.join(HERE,'samples_holdout.json'),encoding='utf-8'))['pairs']
        print(json.dumps(score(lambda a,b:(True,[],[]),pairs),ensure_ascii=False,indent=2))
