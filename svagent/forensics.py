"""FJ 取证内核 — 让门禁从「填表裁判」变成「取证法官」。

设计立场（源起《端到端独立审计 2026-11-22》F1：28/28 check_* 只接调用方填好的
yes/no，0 个自己读证据）：本模块提供一层取证入口，门禁内部读原始证据、逐字命中
预锁锚点，自行推导出四维 {yes,no,partial}，再交给原有 check_* 按 R0–R6 裁决。

与本仓既有纪律完全一致：
  - 不替换、不修改任何 check_*：它们是「裁决法条」，本模块只是「取证程序」；
    原 967 项测试、Verdict 结构、R0–R6 短路全部向后兼容。
  - 证据分级不变：只判「声明/证据是否自洽可核」，不承诺被审系统真实有效
    （KB-R07 / KB-META01 / KB-RSI07）。
  - 中文锚点由各门禁模块集中在 _FORENSIC_ANCHORS 字典；本模块 Compare 内无中文字面量
    （AST 自审纪律）。

三态取证映射（每维）：
  - disclose_anchors 命中且 conceal_anchors 未命中 -> yes（证据明确披露了该维度）；
  - conceal_anchors 命中且 disclose_anchors 未命中 -> no（证据出现隐瞒/冒充的红旗表述）；
  - 两类都命中（证据自相矛盾）或都不命中（证据未覆盖该维度）-> partial
    → 原 check_* 的 R5 会给出 flag（待核）。
  关键：取证不足时绝不补 yes —— 这正是「法官」与「填表裁判」的本质差别。

诚实边界：conceal_anchors 是「红旗特征库」（不诚实系统常见的过度宣称措辞），
用于反向检测，默认不期望在诚实论文里命中；命中即触发 downgrade。它不是伪造的
证据，而是探测器（类似杀毒特征库），命中与否都写在溯源里，可人工复核。
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# 原文规范化：PDF 常把连字符写成 U+2212、引号写成 smart quotes、换行拆字。
# 只做「码位归一 + 空白折叠」，不改写语义，不删字符。
_TRANS = str.maketrans({
    "\u2212": "-", "\u2010": "-", "\u2011": "-", "\u2013": "-", "\u2014": "-",
    "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
    "\u00a0": " ", "\u3000": " ",
})


def normalize(text: str) -> str:
    """规范化原文用于逐字命中：Unicode 标点归一 + 空白折叠，不改语义。"""
    return re.sub(r"\s+", " ", text.translate(_TRANS)).strip()


@dataclass(frozen=True)
class DimensionSpec:
    """一个取证维度：正面披露锚点 + 反向红旗锚点。"""
    name: str
    disclose_anchors: tuple[str, ...] = ()
    conceal_anchors: tuple[str, ...] = ()


@dataclass(frozen=True)
class ForensicSpec:
    """一道门禁的取证规格：门名 + 四维规格。"""
    gate: str
    dimensions: tuple[DimensionSpec, ...]


@dataclass(frozen=True)
class EvidenceBundle:
    """证据对象：一组原文路径 + 规范化合并文本 + 每份原文 SHA256。

    caller 交的是证据（路径），不是结论（yes/no）——这是取证模式的入口契约。
    """
    sources: tuple[str, ...]
    text: str
    sha256: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_files(cls, paths: list[str] | tuple[str, ...]) -> "EvidenceBundle":
        """读原文、规范化、算 SHA256；文件不存在直接抛错（绝不静默吞证据）。"""
        chunks: list[str] = []
        digests: dict[str, str] = {}
        norm_paths: list[str] = []
        for raw in paths:
            p = Path(raw)
            if not p.is_file():
                raise FileNotFoundError(f"取证证据不存在: {raw}")
            data = p.read_bytes()
            digests[p.name] = hashlib.sha256(data).hexdigest()
            chunks.append(normalize(data.decode("utf-8", errors="replace")))
            norm_paths.append(str(p))
        return cls(tuple(norm_paths), "\n".join(chunks), digests)

    @classmethod
    def inline(cls, text: str, label: str = "inline") -> "EvidenceBundle":
        """构造内联证据（测试/小样本用）；同样算 SHA256，可溯源。"""
        t = normalize(text)
        return cls(
            (label,), t,
            {label: hashlib.sha256(t.encode("utf-8")).hexdigest()},
        )

    def hit(self, anchor: str) -> bool:
        """逐字命中：锚点须规范化后作为原文子串出现。"""
        return normalize(anchor) in self.text


def infer_dimensions(bundle: EvidenceBundle, spec: ForensicSpec) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
    """从证据推导四维枚举 + 命中溯源。

    返回 (inferred, provenance)。inferred 可直接喂给原 check_*。
    """
    inferred: dict[str, str] = {}
    provenance: dict[str, dict[str, Any]] = {}
    for dim in spec.dimensions:
        disc = [a for a in dim.disclose_anchors if bundle.hit(a)]
        conc = [a for a in dim.conceal_anchors if bundle.hit(a)]
        if disc and not conc:
            value = "yes"
        elif conc and not disc:
            value = "no"
        else:
            # 都命中=矛盾；都不命中=未覆盖——两者都判 partial，交原门禁 flag。
            value = "partial"
        inferred[dim.name] = value
        provenance[dim.name] = {
            "value": value,
            "disclose_hits": disc,
            "conceal_hits": conc,
            "evidence_sha256": dict(bundle.sha256),
        }
    return inferred, provenance


def adjudicate(
    bundle: EvidenceBundle,
    spec: ForensicSpec,
    check_fn: Callable[..., Any],
    claim: str,
    *,
    evidence_scope: str = "primary",
) -> tuple[Any, dict[str, Any]]:
    """取证裁决：读证据 -> 推导四维 -> 原 check_* 裁决 -> 附溯源。

    返回 (verdict, forensic_trace)。verdict 与原填表模式同类型同语义；
    forensic_trace 记录 mode=forensic、证据来源/哈希、每维命中明细，可落盘复核。
    """
    inferred, provenance = infer_dimensions(bundle, spec)
    verdict = check_fn(claim, **inferred)
    trace = {
        "mode": "forensic",
        "gate": spec.gate,
        "claim": claim,
        "evidence_scope": evidence_scope,
        "sources": list(bundle.sources),
        "source_sha256": dict(bundle.sha256),
        "dimensions": provenance,
        "inferred": inferred,
        "action": verdict.action,
        "code": verdict.code,
    }
    return verdict, trace


def live_regression() -> dict:
    """FJ 内核自测：三态推导（yes / no / partial）+ 规范化命中。"""
    spec = ForensicSpec(
        gate="forensics.selftest",
        dimensions=(DimensionSpec(
            "scope", disclose_anchors=("绿灯只说明一件事",),
            conceal_anchors=("覆盖了一切",),
        ),),
    )
    cases = {
        "disclosed": (EvidenceBundle.inline("绿灯只说明一件事。它检查了什么？"), "yes"),
        "concealed": (EvidenceBundle.inline("覆盖了一切，全部通过。"), "no"),
        "absent": (EvidenceBundle.inline("无关文本。"), "partial"),
        "contradictory": (EvidenceBundle.inline("绿灯只说明一件事，但它覆盖了一切。"), "partial"),
    }
    checks: dict[str, bool] = {}
    for name, (bundle, expect) in cases.items():
        inferred, _ = infer_dimensions(bundle, spec)
        checks[name] = inferred["scope"] == expect
    # 规范化：U+2212 减号与空白折叠后应命中
    checks["normalize"] = EvidenceBundle.inline("self\u2212review the final suite").hit(
        "self-review the final suite"
    )
    return {"checks": checks, "all_passed": all(checks.values())}
