"""L3 主线机械证据台账：从各轮真实 result.json 提取裁决，数据驱动不手抄。

纪律：
- 只读已提交冻结的 result.json，不改任何裁决、不翻案、不放宽。
- 每份 result.json 记 SHA256，台账可复现、可核。
- 台账只做"陈述归纳"，不产生新判定；l3/absolute 恒 false 由真实数据断言。
"""
import json, os, hashlib, datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # /workspace

# (轮次, 目录, 主题, 外移/消融维度, 尺子四维或None, verdict取值器)
# verdict 取值器: (path, key)  path 用 . 分隔；key=None 取整值
ROUNDS = [
    ("§97",  "audit_l3_evidence_rubric",      "成熟度尺子编译+首次自审",   "（无，首次对准本仓）",
     dict(level_definition_traced="yes", process_product_split="yes", shared_start_controlled="no", independent_tests="no"),
     "self_audit.verdict.code"),
    ("§98",  "audit_shared_start_controlled", "shared-start 受控对照",     "出题起点/预算受控",
     dict(level_definition_traced="yes", process_product_split="yes", shared_start_controlled="yes", independent_tests="partial"),
     "l3_reassessment.verdict.code"),
    ("§99",  "audit_evaluator_independence",  "评估器独立性自审",          "judge 降级/确定性门禁",
     None, "self_audit.verdict.code"),
    ("§100", "audit_frozen_holdout",           "冻结 held-out 独立性验证",  "出题权外移到外部论文一手全文",
     None, "verdict.independence_grade"),
    ("§101", "audit_meta_canary",              "元 canary 投毒检测",        "检验者递归（Trusting Trust）",
     None, "verdict.meta_detection_capability_demonstrated"),
    ("§102", "audit_criterion_portability",    "判据设计权外移",            "判据设计权（本 Agent 最后一环）",
     None, "verdict.code"),
    ("§103", "audit_designer_desteering",      "设计者约束消融 de-steering","prompt 规则词+id 语义引导",
     None, "verdict.code"),
    ("§104", "audit_field_neutral",            "字段名语义消融",            "字段名语义",
     None, "verdict.code"),
    ("§105", "audit_cross_domain_field",       "跨数据域字段名消融 2×2",     "字段名×数据域",
     None, "verdict"),
    ("§106", "audit_task_purpose_injection",   "任务目的语义注入",          "任务目的叙事（加法受控）",
     None, "verdict"),
    ("§107", "audit_stratified_confirmation",  "预注册分层确认性实验",      "分层主指标+能力对照",
     None, "verdict"),
    ("§108", "audit_cross_domain_confirm2",    "跨集复现+外部时间锚",       "第三独立确认集",
     None, "verdict"),
    ("§109", "audit_external_orchestrator",    "外部 orchestrator 执行者",  "执行权外移到 Azure runner",
     None, "verdict"),
    ("§110", "audit_cross_vendor_evaluator",   "异厂商 designer",           "设计者→异厂 LLM",
     None, "verdict"),
    ("§111", "audit_admission_ast_audit",      "准入规则粒度修订 AST v2",   "准入规则粒度（修工具不放宽）",
     None, "verdict"),
    ("§112", "audit_cross_vendor_designer2",   "真正跨厂商 designer 交叉",  "厂商（修正 nvidia→真异厂）",
     None, "verdict"),
    ("§113", "audit_cross_set_vendor2",        "跨集×跨厂商 2×2 闭合",      "集×厂商交互",
     None, "verdict"),
    ("§114", "audit_interpreter_independence", "解释者独立性",              "解释权→异厂 LLM 盲评",
     None, "verdict"),
    ("§115", "audit_interpreter_cross_vendor", "解释者跨厂商交叉",          "解释者×厂商交叉",
     None, "verdict"),
    ("L3",   "audit_l3_fullchain_external",    "Operation L3 五权力全外置", "出题/gt/判据/执行/裁决 同时外置",
     None, "verdict"),
    ("L3-R2", "audit_l3_gap_targeted",         "缺口定向第二家回放",         "断言类覆盖下限定向",
     None, "verdict"),
]


def dig(d, path):
    cur = d
    for p in path.split('.'):
        if isinstance(cur, dict) and p in cur:
            cur = cur[p]
        else:
            return None
    return cur


def find_flag(r, names):
    """递归找 l3/absolute 标志，返回 (found, value)."""
    stack = [r]
    while stack:
        cur = stack.pop()
        if isinstance(cur, dict):
            for k, v in cur.items():
                lk = k.lower()
                if any(n in lk for n in names) and isinstance(v, bool):
                    return True, v
                stack.append(v)
        elif isinstance(cur, list):
            stack.extend(cur)
    return False, None


def sha256_file(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def build():
    rows = []
    for sec, dr, topic, axis, dims, vpath in ROUNDS:
        rp = os.path.join(ROOT, dr, 'result.json')
        if not os.path.exists(rp):
            rows.append(dict(section=sec, dir=dr, topic=topic, axis=axis, missing=True))
            continue
        r = json.load(open(rp, encoding='utf-8'))
        v = dig(r, vpath)
        if isinstance(v, dict):
            v = v.get('code') or v.get('action') or json.dumps(v, ensure_ascii=False)[:80]
        l3_found, l3_val = find_flag(r, ['l3_claimed'])
        # absolute 有多个字段名，分别识别
        abs_found = False; abs_val = None
        for nm in ['absolute_claimed', 'absolute_independence_claimed', 'absolute_no_backdoor_claimed']:
            f, val = find_flag(r, [nm])
            if f:
                abs_found, abs_val = True, val; break
        rows.append(dict(
            section=sec, dir=dr, topic=topic, axis=axis,
            four_dims=dims, verdict=str(v) if v is not None else None,
            l3_claimed=(l3_val if l3_found else None),
            l3_flag_present=l3_found,
            absolute_claimed=(abs_val if abs_found else None),
            abs_flag_present=abs_found,
            result_sha256=sha256_file(rp),
            missing=False,
        ))
    # 统计：所有显式 l3_claimed 必须为 false
    explicit = [x for x in rows if not x.get('missing') and x.get('l3_flag_present')]
    bad = [x['section'] for x in explicit if x['l3_claimed'] is not False]
    # 裁决分布（按 verdict 后缀归类）
    from collections import Counter
    dist = Counter()
    for x in rows:
        v = (x.get('verdict') or '').upper()
        if 'CONFIRMED' in v: dist['CONFIRMED'] += 1
        elif 'INCONCLUSIVE' in v: dist['INCONCLUSIVE'] += 1
        elif 'PARTIAL' in v or 'WEAKENED' in v or 'DEPENDENT' in v: dist['PARTIAL/受依赖'] += 1
        else: dist['其他/能力演示'] += 1
    ledger = dict(
        generated_at=datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        generator='audit_l3_gap_targeted/build_evidence_ledger.py',
        purpose='L3 主线 21 轮裁决机械提取，陈述归纳不产生新判定；不翻案不放宽',
        n_rounds=len(rows),
        rounds=rows,
        stats=dict(
            explicit_l3_flags=len(explicit),
            all_l3_false=(len(bad) == 0),
            violating_sections=bad,
            verdict_distribution=dict(dist),
        ),
    )
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'L3_EVIDENCE_LEDGER.json')
    json.dump(ledger, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    print(f"台账已生成: {out}")
    print(f"轮数: {len(rows)}  显式l3标志: {len(explicit)}  全部false: {len(bad)==0}")
    print("裁决分布:", dict(dist))
    if bad:
        print("警告: l3 非 false 的轮次:", bad)
    return ledger


if __name__ == '__main__':
    build()
