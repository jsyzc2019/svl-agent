"""svl-audit CLI — 一条命令完成「校验证据链 → 取证法官裁决 → 落证据」（审计 F7）。

暴露本仓核心能力给外部：给一段证据，出裁决，落可复核的取证痕迹。
原 28 道 check_* 是被动库、无生产调用点；本 CLI 是 FJ 取证入口的对外门面。

用法：
  python3 -m svagent.cli adjudicate            # 三道试点取证裁决（含链校验）
  python3 -m svagent.cli chain                 # 批量链审（32 目录完整度/锁状态）
  python3 -m svagent.cli bridge                # KB+取证缺口 → PDCA 消费痕迹
  svl-audit adjudicate                         # 安装后通过 console_scripts
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parent.parent


def cmd_adjudicate(args: argparse.Namespace) -> dict[str, Any]:
    from .forensic_gates import adjudicate_all
    result = adjudicate_all()
    out = {
        "adjudications": result,
        "all_ok": all(v["action"] == "ok" for v in result.values()),
        "mode": "forensic",
    }
    if args.out:
        Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return out


def cmd_chain(args: argparse.Namespace) -> dict[str, Any]:
    from .evidence_chain import audit_all
    result = audit_all(str(_ROOT))
    summary = {k: v for k, v in result.items() if k != "reports"}
    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return summary


def cmd_bridge(args: argparse.Namespace) -> dict[str, Any]:
    from .growth_bridge import bridge_into_pdca, save_consumption
    from .knowledge_base import KnowledgeBase
    from .pdca import PDCALoop, Budget
    from .forensic_gates import adjudicate_all
    kb = KnowledgeBase.load(_ROOT / "knowledge_base_store.json")
    adj = adjudicate_all()
    loop = PDCALoop(budget=Budget(max_cycles=2, patience=1, max_attempts=1))
    rep = bridge_into_pdca(loop, kb=kb, adjudications=adj)
    out = rep.to_dict()
    out["pdca_injected"] = len(loop._injected_opps)
    if args.out:
        save_consumption(rep, args.out)
    return out


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="svl-audit",
        description="svagent FJ 取证法官：证据链校验 → 取证裁决 → 落证据",
    )
    sub = p.add_subparsers(dest="command", required=True)
    for name, fn, helptext in (
        ("adjudicate", cmd_adjudicate, "三道试点取证裁决（含链校验）"),
        ("chain", cmd_chain, "批量证据链审（32 目录）"),
        ("bridge", cmd_bridge, "KB+取证缺口注入 PDCA 并落消费痕迹"),
    ):
        sp = sub.add_parser(name, help=helptext)
        sp.add_argument("--out", help="结果落盘路径（JSON）")
        sp.set_defaults(func=fn)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        result = args.func(args)
    except Exception as e:
        print(json.dumps({"error": type(e).__name__, "message": str(e)},
                         ensure_ascii=False), file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
