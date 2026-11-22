"""FJ 取证法官扩展入口 4 — 自主运维第四轮新增的第七道（§93）。

不改动已锁存的 forensic_gates.py / ext.py / ext2.py / ext3.py；
本模块承载 redteam_robustness 的 adjudicate_* 入口，
复用同一 forensics.adjudicate 内核与 evidence_chain 链校验。

锚点取自 arXiv:2611.24362v1 全文（audit_redteam_honesty/downloads/paper_flat.txt），
已用探测脚本验证：14 个 disclose 锚点全部命中、红旗 conceal 锚点零误命中
（ALL_ANCHORS_CLEAN=True）。诚实论文 → 推导全 yes → ok；篡改/删改 → partial/no → 降级。

诚实边界：只判原文是否诚实披露四 robustness 边界，不承诺防御真实有效
（KB-R07/META01，near-zero ASR / utility 等 self-reported 数字折 1）；
红旗是探测器不是伪造证据，命中明细进 trace 可人工复核。
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .forensics import (
    EvidenceBundle, ForensicSpec, DimensionSpec, adjudicate as _adjudicate,
)
from .redteam_robustness_honesty import (
    check_redteam_robustness_honesty,
    RedteamRobustnessVerdict,
)

_ROOT = Path(__file__).resolve().parent.parent

# 锚点集中字典（AST 自审：Compare 内无中文字面量）
_A = {
    "asr_robustness_linked": (
        ("achieving high ASR during red-teaming does not guarantee robustness gains from subsequent adversarial training",
         "whose additional successes add no additional robustness improvements to adversarial training"),
        ("higher red-teaming ASR always yields stronger adversarial robustness",
         "every additional attack success improves the hardened defender"),
    ),
    "attack_diversity_measured": (
        ("a dictionary learning-based reward that encourages broader coverage of attack strategies",
         "suffer from mode collapse, repeatedly discovering similar attack strategies"),
        ("attack diversity was not measured or rewarded during red-teaming",
         "the red-teamer was optimized for raw success count alone"),
    ),
    "adaptive_attack_tested": (
        ("achieve near-zero attack success rates on static attacks and can withstand strong adaptive attacks",
         "withstand strong adaptive attacks"),
        ("evaluation was limited to static attacks with no adaptive adversary",
         "robustness was reported only on fixed pre-generated attacks"),
    ),
    "benign_utility_preserved": (
        ("maintaining benign task utility close to that of the undefended baseline",
         "resist attacks while completing legitimate user tasks"),
        ("benign task utility was sacrificed to obtain a low attack success rate",
         "the defender blocks all tool calls including legitimate ones"),
    ),
}

_DEFAULT_SOURCES = ["audit_redteam_honesty/downloads/paper_flat.txt"]
_AUDIT_DIR = "audit_redteam_honesty"


def _spec() -> ForensicSpec:
    dims = tuple(
        DimensionSpec(name, tuple(disc), tuple(conc))
        for name, (disc, conc) in _A.items()
    )
    return ForensicSpec(gate="forensic.redteam_robustness", dimensions=dims)


def default_sources() -> list[str]:
    """返回默认证据绝对路径（供 CLI / 外部调用）。"""
    return [str(_ROOT / p) for p in _DEFAULT_SOURCES]


def _require_chain(enforce: bool, sources: list[str]) -> dict[str, Any] | None:
    """取证前校验：prereg/gate_prereg 二锁必过 + 证据源哈希匹配；失配即拒判。"""
    if not enforce:
        return None
    from .evidence_chain import verify_chain, verify_sources, ChainIntegrityError
    d = _ROOT / _AUDIT_DIR
    report = verify_chain(d)
    core_ok = all(c.ok for c in report.locks
                  if c.lock.startswith(("prereg", "gate_prereg")))
    if not core_ok:
        bad = [c.lock + ":" + c.detail for c in report.locks
               if c.lock.startswith(("prereg", "gate_prereg")) and not c.ok]
        raise ChainIntegrityError("核心锁失配，拒绝取证: " + str(d) + " | " + "; ".join(bad))
    src_check = verify_sources(d, sources)
    if src_check["tampered"]:
        raise ChainIntegrityError("证据源文件已篡改，拒绝取证: " + str(d) + " | " + str(src_check["tampered"]))
    return {"chain": report.to_dict(), "source_verification": src_check}


def adjudicate_redteam_robustness_honesty(
    claim: str = "Red-team to defense robustness claim",
    sources: list[str] | None = None,
    enforce_chain: bool = True,
) -> tuple[RedteamRobustnessVerdict, dict[str, Any]]:
    """取证版红队-防御增益诚实性：验三锁→读 arXiv 全文自取四维→原 check_* 裁决。"""
    eff_sources = sources or default_sources()
    chain = _require_chain(enforce_chain, eff_sources)
    bundle = EvidenceBundle.from_files(eff_sources)
    verdict, trace = _adjudicate(bundle, _spec(),
                                 check_redteam_robustness_honesty, claim,
                                 evidence_scope="primary(arXiv abs+全文,near-zero ASR折1)")
    if chain:
        trace.update(chain)
    return verdict, trace


def live_regression() -> dict:
    """取证自测：真实证据→ok；删披露锚点→partial→flag；红旗→no→降级；链失配拒判。"""
    import tempfile
    checks: dict[str, bool] = {}

    # 1) 真实证据 → ok
    v, tr = adjudicate_redteam_robustness_honesty()
    checks["real_evidence_ok"] = (v.action == "ok" and v.code == "REDTEAM.SELF_CONSISTENT")

    # 2) 篡改：删掉 attack_diversity 维披露锚点 → 该维 partial → flag
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "tampered.txt"
        bad.write_text(
            "achieving high ASR during red-teaming does not guarantee robustness gains from subsequent adversarial training. "
            "achieve near-zero attack success rates on static attacks and can withstand strong adaptive attacks. "
            "maintaining benign task utility close to that of the undefended baseline.",
            encoding="utf-8",
        )
        v2, tr2 = adjudicate_redteam_robustness_honesty(sources=[str(bad)])
        checks["tamper_partial_flag"] = (
            tr2["inferred"]["attack_diversity_measured"] == "partial" and v2.action == "flag"
        )
        checks["tamper_trace_has_sha"] = bool(tr2["source_sha256"])

    # 3) 红旗命中：注入「高ASR必然带来强防御」→ asr 维 no → downgrade
    with tempfile.TemporaryDirectory() as td:
        bad = Path(td) / "redflag.txt"
        bad.write_text(
            "higher red-teaming ASR always yields stronger adversarial robustness, "
            "every additional attack success improves the hardened defender. "
            "a dictionary learning-based reward that encourages broader coverage of attack strategies. "
            "achieve near-zero attack success rates on static attacks and can withstand strong adaptive attacks. "
            "maintaining benign task utility close to that of the undefended baseline.",
            encoding="utf-8",
        )
        v3, tr3 = adjudicate_redteam_robustness_honesty(sources=[str(bad)])
        checks["red_flag_downgrade"] = (
            tr3["inferred"]["asr_robustness_linked"] == "no" and v3.action == "downgrade"
        )

    # 4) 链失配拒判
    import shutil
    with tempfile.TemporaryDirectory() as td:
        shutil.copytree(_ROOT / _AUDIT_DIR, Path(td) / _AUDIT_DIR)
        p = Path(td) / _AUDIT_DIR / "prereg.json"
        p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        orig = _ROOT
        globals()["_ROOT"] = Path(td)
        try:
            adjudicate_redteam_robustness_honesty()
            checks["chain_tamper_rejected"] = False
        except Exception as e:
            checks["chain_tamper_rejected"] = type(e).__name__ == "ChainIntegrityError"
        finally:
            globals()["_ROOT"] = orig

    return {
        "checks": checks,
        "cases": {"real": {"action": v.action, "code": v.code, "inferred": tr["inferred"]}},
        "all_passed": all(checks.values()),
    }
