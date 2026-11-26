"""§4gq 判据泛化宽度守卫。

把 §4gq 的 SPECIALIZED_SYNTAX 发现固化为可复现断言：
- 判据在声明类(否定/尾删/连接词)上必须仍高检出（防止判据退化）
- 判据在语义类(实体/程度/量词/体态)上必须仍低检出（保护已记录的能力边界真相）
- 零重叠：新样本不得与冻结集重复（防止样本记忆污染结论）
- 镜像测试：应保留句不得误报（排除"一律判False"）

负向自咬见 test_gq04：若判据被篡改成"什么都检出"，守卫必须失败。
"""
import importlib.util
import json
import os

CRIT_PATH = "audit_l3_gap_targeted/received/l3_external_audit_v2/criterion.py"
FROZEN_PATH = "audit_l3_gap_targeted/received/l3_external_audit_v2/samples_blind.json"
RESULT_PATH = "audit_l3_gap_targeted/result_4gq.json"


def _load_crit(path=CRIT_PATH):
    spec = importlib.util.spec_from_file_location("crit_gq", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _sixgrams(s, n=6):
    w = s.lower().split()
    return set(" ".join(w[i:i + n]) for i in range(len(w) - n + 1))


DECLARED = [
    ("negation", "The committee approved the final proposal yesterday.",
     "The committee did not approve the final proposal yesterday."),
    ("negation", "She recorded the results in the laboratory notebook.",
     "She never recorded the results in the laboratory notebook."),
    ("negation", "The device protects the circuit from voltage spikes.",
     "The device does not protect the circuit from voltage spikes."),
    ("tail_drop", "The researcher measured the temperature of the boiling liquid carefully.",
     "The researcher measured the temperature of the boiling liquid."),
    ("tail_drop", "The team completed the ambitious project despite the severe delays.",
     "The team completed the ambitious project."),
    ("tail_drop", "We observed that the catalyst accelerated the reaction under high pressure.",
     "We observed that the catalyst accelerated the reaction."),
    ("connector", "Despite the heavy rain, the match continued as scheduled.",
     "However the heavy rain, the match continued as scheduled."),
    ("connector", "Although the results were promising, the trial was halted early.",
     "But the results were promising, the trial was halted early."),
    ("connector", "The method worked in the lab, but it failed in the field.",
     "The method worked in the lab, whereas it failed in the field."),
]

SEMANTIC = [
    ("entity_swap", "The cat sat on the mat near the warm fireplace.",
     "The dog sat on the mat near the warm fireplace."),
    ("entity_swap", "Marie Curie discovered radium in the old laboratory.",
     "Marie Curie discovered polonium in the old laboratory."),
    ("entity_swap", "The company hired a new engineer from the northern city.",
     "The company hired a new manager from the northern city."),
    ("degree_flip", "The treatment produced a significant improvement in patients.",
     "The treatment produced a negligible improvement in patients."),
    ("degree_flip", "The new policy had a modest effect on local employment.",
     "The new policy had a dramatic effect on local employment."),
    ("degree_flip", "The results were highly consistent across all trials.",
     "The results were marginally consistent across all trials."),
    ("quantifier", "All participants completed the survey before the deadline.",
     "Some participants completed the survey before the deadline."),
    ("quantifier", "Most samples showed traces of the contaminant.",
     "Few samples showed traces of the contaminant."),
    ("quantifier", "Every student passed the difficult examination.",
     "No student passed the difficult examination."),
    ("aspect", "She walks to the office along the river every morning.",
     "She walked to the office along the river every morning."),
    ("aspect", "The system processes thousands of requests every second.",
     "The system processed thousands of requests every second."),
    ("aspect", "They are building a new bridge across the valley.",
     "They built a new bridge across the valley."),
]

MIRROR = [
    ("format", "The committee approved the final proposal yesterday.",
     "the committee approved the final proposal yesterday"),
    ("format", "She recorded the results in the laboratory notebook.",
     "She recorded the results in the laboratory notebook."),
    ("synonym_safe", "The cat sat on the mat near the warm fireplace.",
     "The cat sat on the mat near the cozy fireplace."),
    ("equiv_connector", "Despite the heavy rain, the match continued as scheduled.",
     "Although the heavy rain, the match continued as scheduled."),
]


def _detected(crit, a, b):
    j, _, _ = crit.judge(a, b)
    return j is False


def test_gq01_declared_still_detected():
    """判据在其声明的三类语法上必须保持高检出（防退化）。"""
    crit = _load_crit()
    hit = sum(_detected(crit, a, b) for _, a, b in DECLARED)
    assert hit == len(DECLARED), f"声明类检出退化: {hit}/{len(DECLARED)}"


def test_gq02_semantic_still_blind():
    """判据对未声明的语义破坏必须仍系统性盲——保护 §4gq 能力边界真相。"""
    crit = _load_crit()
    hit = sum(_detected(crit, a, b) for _, a, b in SEMANTIC)
    rate = hit / len(SEMANTIC)
    assert rate < 0.30, f"语义类检出升高, SPECIALIZED_SYNTAX 边界被推翻: {hit}/{len(SEMANTIC)}"


def test_gq03_zero_overlap_and_no_false_positive():
    """新样本与冻结集零重叠(整句+6gram)；应保留句零误报。"""
    frozen = json.load(open(FROZEN_PATH, encoding="utf-8"))
    ftexts = [p["text_a"] for p in frozen["pairs"]] + [p["text_b"] for p in frozen["pairs"]]
    fgrams = set()
    for s in ftexts:
        fgrams |= _sixgrams(s)
    news = [s for _, a, b in DECLARED + SEMANTIC for s in (a, b)]
    for s in news:
        assert s not in ftexts, f"整句重叠: {s[:40]}"
        assert not (_sixgrams(s) & fgrams), f"6gram重叠: {s[:40]}"
    crit = _load_crit()
    fp = sum(_detected(crit, a, b) for _, a, b in MIRROR)
    assert fp == 0, f"应保留句被误报: {fp}/{len(MIRROR)}"


def test_gq04_negative_selfbite_all_true_must_fail():
    """负向自咬：构造一个'什么都检出'的假判据，证明确实会被 gq03 镜像测试抓到。"""
    class FakeAllTrue:
        @staticmethod
        def judge(a, b):
            return False, ["fake: always broken"], []
    fp = sum(_detected(FakeAllTrue, a, b) for _, a, b in MIRROR)
    assert fp > 0, "自咬失效：假判据应触发镜像误报"
    # 真实判据不应如此
    crit = _load_crit()
    assert sum(_detected(crit, a, b) for _, a, b in MIRROR) == 0


def test_gq05_result_file_verdict_locked():
    """§4gq 裁决文件必须是 SPECIALIZED_SYNTAX 且判定态三值不动。"""
    r = json.load(open(RESULT_PATH, encoding="utf-8"))
    assert r["verdict"] == "SPECIALIZED_SYNTAX"
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False
    assert r["kernel_verdict_unchanged"] == "GAP_INCONCLUSIVE"
    # sha256 锁一致
    import hashlib
    lock = open(RESULT_PATH + ".sha256", encoding="utf-8").read().split()[0]
    assert hashlib.sha256(open(RESULT_PATH, "rb").read()).hexdigest() == lock
