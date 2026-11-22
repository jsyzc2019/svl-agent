"""§110 异厂商 designer 受控验证管线测试（验证工具逻辑，不改门禁/不放宽断言）。"""
import json, hashlib, os, subprocess

BASE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "audit_cross_vendor_evaluator")
CELLS = ("P0", "P1", "P2")


def load(p): return json.load(open(p, encoding="utf-8"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()


def test_prereg_locks_frozen_before_vendor_spawn():
    p = load(f"{BASE}/prereg.json")
    assert p["locked_before_vendor_spawn"] is True
    assert p["l3_claimed"] is False and p["absolute_claimed"] is False
    assert sha(f"{BASE}/prereg.json") == open(f"{BASE}/prereg.sha256").read().strip()


def test_frozen_samples_identical_to_107():
    p = load(f"{BASE}/prereg.json")
    target = p["held_fixed_from_107"]["samples_blind_sha256"]
    shas = {sha(f"{BASE}/vendor_{c}/samples_blind.json") for c in CELLS}
    assert len(shas) == 1 and shas.pop() == target
    # 与 §107 实际存档样本逐字节一致
    ref = hashlib.sha256(open(
        os.path.join(os.path.dirname(BASE), "audit_stratified_confirmation", "designer_P1", "samples_blind.json"),
        "rb").read()).hexdigest()
    assert ref == target


def test_scorer_key_never_in_vendor_prompt():
    """裸样本只含 id/text_a/text_b；purpose 不含 gt/deletion_class/orig_id。"""
    for c in CELLS:
        s = load(f"{BASE}/vendor_{c}/samples_blind.json")["samples"]
        for row in s:
            assert set(row.keys()) == {"id", "text_a", "text_b"}, f"{c} leaked fields: {row.keys()}"
        purpose = open(f"{BASE}/vendor_{c}/purpose.md", encoding="utf-8").read()
        for tok in ("deletion_class", "ground_truth", "orig_id", "scorer_key", "negation_flip"):
            assert tok not in purpose


def test_purpose_single_variable():
    """三条件 purpose 各异但技术要求段逐字一致（单变量=目的语义）。"""
    purposes = {c: open(f"{BASE}/vendor_{c}/purpose.md", encoding="utf-8").read() for c in CELLS}
    assert len(set(purposes.values())) == 3
    tail = "要求：纯字符串/正则实现，确定性；不使用随机数、时间、样本 id、外部文件或样本文本硬编码。"
    for c in CELLS:
        assert tail in purposes[c]


def test_pending_state_has_no_forged_verdict():
    r = load(f"{BASE}/result.json")
    if r["status"] == "PENDING_API_KEY":
        assert "verdict" not in r
        assert r["missing_judges"] == list(CELLS)
        for c in CELLS:
            assert not os.path.exists(f"{BASE}/vendor_{c}/judge_vendor.py")


def test_verify_pending_all_ok():
    p = subprocess.run(["python3", f"{BASE}/verify.py"], capture_output=True, text=True)
    assert p.returncode == 0
    assert "ALL_OK" in p.stdout


def test_call_vendor_never_writes_key():
    """调用器只从环境变量读 key，源码里不得有硬编码 key 或写 key 到盘的逻辑。"""
    src = open(f"{BASE}/call_vendor.py", encoding="utf-8").read()
    assert "os.environ.get(\"CROSS_VENDOR_API_KEY\"" in src
    assert "ghp_" not in src
    # 留痕写入内容不含 API_KEY 变量
    assert "API_KEY" not in src.split("json.dumps(manifest")[1].split(")")[0]


def test_verdict_rules_locked_four_tiers():
    p = load(f"{BASE}/prereg.json")
    joined = " ".join(p["verdict_rules"])
    for tier in ("CROSS_VENDOR_CONFIRMED", "CROSS_VENDOR_PARTIAL", "CROSS_VENDOR_REFUTED", "CROSS_VENDOR_INCONCLUSIVE"):
        assert tier in joined


# ---- §110 执行态回归（异厂 key 到位后真实执行，锁定诚实裁决不翻案）----

def test_executed_judges_are_real_vendor_outputs():
    """执行态：三份 judge 必来自异厂 API 真实调用（留痕齐全、finish=stop、来源如实标注）。"""
    mpath = f"{BASE}/runs/vendor_call_manifest.json"
    if not os.path.exists(mpath):
        return  # 尚未执行，主测试集覆盖 PENDING
    m = load(mpath)
    assert m.get("api_base", "").startswith("https://")
    for c in CELLS:
        r = m["calls"][c]
        assert r["status"] == "ok", f"{c} 调用未成功: {r}"
        assert r["finish_reason"] == "stop", f"{c} 未完成生成（可能 token 截断）"
        assert r["code_source"] in ("content", "reasoning_fallback")
        assert r["user_prompt_sha256"] and r["system_sha256"]
        # judge 文件哈希必须与留痕一致（未被事后篡改）
        jp = f"{BASE}/vendor_{c}/judge_vendor.py"
        assert os.path.exists(jp)
        assert hashlib.sha256(open(jp, "rb").read()).hexdigest() == r["judge_sha256"]


def test_executed_result_is_non_hunyuan_vendor():
    """执行留痕厂商须明确非 Hunyuan（设计者厂商独立性这一维才成立）。"""
    mpath = f"{BASE}/runs/vendor_call_manifest.json"
    if not os.path.exists(mpath):
        return
    m = load(mpath)
    v = (m.get("vendor", "") + " " + m.get("model", "")).lower()
    assert "hunyuan" not in v and "混元" not in v


def test_numeric_reproduction_does_not_overturn_conservative_verdict():
    """诚实边界：PRIMARY=1.00 数值复现，但准入未全过时裁决仍为 INCONCLUSIVE，不事后翻案。"""
    r = load(f"{BASE}/result.json")
    if r.get("status") != "EXECUTED":
        return
    if not r["all_admissions_pass"]:
        # 准入未过 → 无论数值多好，封顶 INCONCLUSIVE（prereg 裁决树首枝）
        assert r["verdict"] == "CROSS_VENDOR_INCONCLUSIVE"
        assert r["metrics"]["PRIMARY"] >= 0.8  # 数值确复现，只是不翻案
    assert r["l3_claimed"] is False and r["absolute_claimed"] is False


def test_leaked_label_tokens_are_in_notes_not_logic():
    """定位弱点：命中禁用表的词只出现在 notes 说明文字，不在判据控制流读取标签字段。"""
    r = load(f"{BASE}/result.json")
    if r.get("status") != "EXECUTED":
        return
    import re
    for c in CELLS:
        src = open(f"{BASE}/vendor_{c}/judge_vendor.py", encoding="utf-8").read()
        # 判据不得访问这些标签字段（源码中不得出现读取结构）
        for field in ("ground_truth", "scorer_key", "deletion_class", "variant", "orig_id"):
            assert not re.search(r"\b" + field + r"\b\s*[=\[]", src), f"{c} 判据读取标签字段 {field}"
        assert "def judge(" in src


def test_no_api_key_committed_anywhere():
    """硬红线：工作区任何受版本控制内容不得含 OpenRouter/通用 API key 模式。"""
    import re
    root = os.path.dirname(BASE)
    patterns = [re.compile(r"sk-or-v1-[A-Za-z0-9]{20,}"), re.compile(r"sk-[A-Za-z0-9]{32,}")]
    for dirpath, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d != ".git" and not d.startswith("__pycache__")]
        for fn in files:
            if not fn.endswith((".py", ".json", ".md", ".sha256", ".txt")):
                continue
            p = os.path.join(dirpath, fn)
            try:
                t = open(p, encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for pat in patterns:
                assert not pat.search(t), f"疑似 key 泄漏: {p}"
