"""修复环：生成 → 判据 → 定位 → 定向修复 → 重试，直到 block 清零。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from .core import Draft, GroundTruth, Diagnostic

Verifier = Callable[[Draft, GroundTruth], list[Diagnostic]]
Reviser = Callable[[Draft, list[Diagnostic], GroundTruth], Draft]


@dataclass
class VerificationResult:
    draft: Draft
    diagnostics: list[Diagnostic]
    converged: bool
    iterations: int
    history: list[list[Diagnostic]] = field(default_factory=list)


def check(draft: Draft, spec: GroundTruth, verifiers: list[Verifier]) -> list[Diagnostic]:
    diags: list[Diagnostic] = []
    for verifier in verifiers:
        diags.extend(verifier(draft, spec))
    return diags


def run_loop(
    draft: Draft,
    spec: GroundTruth,
    verifiers: list[Verifier],
    reviser: Reviser,
    max_iters: int = 5,
) -> VerificationResult:
    history: list[list[Diagnostic]] = []
    for _ in range(max_iters):
        diags = check(draft, spec, verifiers)
        history.append(diags)
        blocks = [d for d in diags if d.severity == "block"]
        if not blocks:
            return VerificationResult(draft, diags, True, len(history), history)
        draft = reviser(draft, blocks, spec)

    final = check(draft, spec, verifiers)
    history.append(final)
    converged = not any(d.severity == "block" for d in final)
    return VerificationResult(draft, final, converged, max_iters, history)
