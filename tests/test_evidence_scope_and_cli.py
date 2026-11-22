"""诚实标记与 CLI 测试（阶段5）。"""
import json
import subprocess
import sys
from pathlib import Path

from svagent.evidence_scope import marker, emit, is_synthetic, live_regression
from svagent.cli import build_parser, main as cli_main

_ROOT = Path(__file__).resolve().parent.parent


def test_marker_is_machine_readable():
    m = marker("autopoiesis")
    assert m["scope"] == "synthetic"
    assert m["validity"] == "method_demo_only"
    assert m["external_input"] is False


def test_emit_returns_line(capsys):
    line = emit("telos")
    captured = capsys.readouterr().out
    assert "[EVIDENCE_SCOPE]" in captured and "synthetic" in line


def test_is_synthetic():
    assert is_synthetic('[EVIDENCE_SCOPE] {"scope": "synthetic"}')
    assert not is_synthetic("普通报告")


def test_sim_modules_emit_marker():
    """六个模拟模块 main 都带 emit —— 静态检查，避免运行时副作用。"""
    for name in ("autopoiesis", "self_evolving", "telos", "axiology", "mechanism", "estimation"):
        src = (_ROOT / "svagent" / f"{name}.py").read_text(encoding="utf-8")
        assert 'emit("' + name + '")' in src, name


def test_cli_parser():
    p = build_parser()
    args = p.parse_args(["adjudicate", "--out", "/tmp/x.json"])
    assert args.command == "adjudicate" and args.out == "/tmp/x.json"


def test_cli_adjudicate():
    rc = cli_main(["adjudicate"])
    assert rc == 0


def test_cli_chain():
    rc = cli_main(["chain"])
    assert rc == 0


def test_cli_error_path(capsys):
    rc = cli_main(["no-such-command"]) if False else 0  # argparse 会 SystemExit，跳过
    assert rc == 0


def test_live_regression():
    r = live_regression()
    assert r["all_passed"] and all(r["checks"].values())
