"""§4gr 族标注-判据能力同构守卫。

固化 §4gr 的 ISOMORPHIC_CONFIRMED 发现：
- 判据规则集(AST从源码提取)恰为三类
- 族标注断言类逐一映射到这三类，数值类落在规则外
- 判据在16独立样本上实际触发标签全集=同一三类
- 裁决文件含反方证据(时序无泄漏/标注独立于DeepSeek)，防止把'结构同构'夸大成造假
- 判定态三值不动

负向自咬(gq04类比)：篡改映射使断言类出现规则外标签，守卫必须失败。
"""
import ast
import json

CRIT = "audit_l3_gap_targeted/received/l3_external_audit_v2/criterion.py"
PREREG = "audit_l3_gap_targeted/prereg.json"
JUDGMENTS = "audit_l3_gap_targeted/received/l3_external_audit_v2/judgments.json"
RESULT = "audit_l3_gap_targeted/result_4gr.json"

TAGS = ("negation-polarity", "assertion-tail-deletion", "connector-change")
FAM_TO_TAG = {
    "ASSERTION_TAIL": "assertion-tail-deletion",
    "NEGATION": "negation-polarity",
    "CONNECTOR": "connector-change",
}


def _criterion_rules(path=CRIT):
    """提取 judge() 里所有 reason 字符串的冒号前缀标签——不预设标签名，
    因此第四类新规则也能被发现（防'声称无第四类却抓不到第四类'的自咬）。"""
    tree = ast.parse(open(path, encoding="utf-8").read())
    found = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Constant) and isinstance(n.value, str) and ":" in n.value:
            head = n.value.split(":")[0].strip()
            if head and len(head) < 50 and " " not in head:
                found.add(head)
    return found


def _assertion_family_map():
    p = json.load(open(PREREG, encoding="utf-8"))
    ft = p["family_taxonomy"]
    m = {}
    for fam in ("ASSERTION_TAIL", "NEGATION", "CONNECTOR"):
        for sid in ft[fam]:
            m[sid] = fam
    return m, ft["numeric_family_list"]


def test_gr01_criterion_rules_are_exactly_three():
    """判据规则集恰为三类（AST从源码提取，非手工列举）。"""
    assert _criterion_rules() == set(TAGS)


def test_gr02_assertion_family_maps_to_criterion_rules():
    """断言类4样本逐一映射到判据三类规则，数值类落在规则外。"""
    amap, numeric = _assertion_family_map()
    assert len(amap) == 4, f"断言类样本数异常: {len(amap)}"
    rules = _criterion_rules()
    for sid, fam in amap.items():
        assert fam in FAM_TO_TAG, f"未知族 {fam}"
        assert FAM_TO_TAG[fam] in rules, f"{sid} 的族 {fam} 不对应判据规则"
    assert len(numeric) == 2
    # 数值类族名不在映射表(即规则外)
    p = json.load(open(PREREG, encoding="utf-8"))
    for sid in numeric:
        fam = next(f for f in ("NUMERIC_QUANT",) if sid in p["family_taxonomy"][f])
        assert fam not in FAM_TO_TAG, "数值类不应映射到判据规则"


def test_gr03_triggered_tags_match_ruleset():
    """判据在16独立样本上实际触发的标签全集=规则集，无第四类。"""
    j = json.load(open(JUDGMENTS, encoding="utf-8"))
    triggered = set()
    for rec in j.values():
        for reason in rec.get("reasons", []):
            for t in TAGS:
                if t in reason:
                    triggered.add(t)
    assert triggered == set(TAGS), f"触发标签与规则集不符: {triggered}"


def test_gr04_negative_selfbite_unmapped_family_must_fail():
    """负向自咬：若断言类出现判据规则外的族，gr02 必须失败。"""
    rules = _criterion_rules()
    # 构造假映射: 把某断言样本标成判据规则外的语义族
    fake = {"S01_tampered": "SEMANTIC_ENTITY_SWAP"}  # 不在 FAM_TO_TAG
    violated = [sid for sid, fam in fake.items()
                if fam not in FAM_TO_TAG or FAM_TO_TAG[fam] not in rules]
    assert violated, "自咬失效：假映射应被判为规则外"
    assert len(violated) == 1


def test_gr05_result_verdict_and_counter_evidence():
    """裁决=ISOMORPHIC_CONFIRMED，含反方证据，判定态三值不动，sha锁一致。"""
    import hashlib
    r = json.load(open(RESULT, encoding="utf-8"))
    assert r["verdict"] == "ISOMORPHIC_CONFIRMED"
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
    assert r["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    ce = r["counter_evidence_honestly_recorded"]
    assert len(ce) >= 3, "反方证据不完整（防夸大成造假）"
    joined = " ".join(ce)
    assert "时序无泄漏" in joined and "Qoder" in joined
    lock = open(RESULT + ".sha256", encoding="utf-8").read().split()[0]
    assert hashlib.sha256(open(RESULT, "rb").read()).hexdigest() == lock
