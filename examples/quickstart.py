"""最小上手：看 agent 如何自己造出一条判据。

运行：python3 examples/quickstart.py
（未安装包时会自动把项目根目录加入 sys.path）
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from svagent.autopoiesis import (  # noqa: E402
    Environment, SelfOrganizingAgent, simulate_session,
)


def main() -> None:
    agent = SelfOrganizingAgent(Environment())
    for session in range(3):
        metric = agent.cycle(simulate_session(session))
        print(f"round {metric['cycle']}: env v{metric['version']}, "
              f"predicates={metric['predicates']}, leak={metric['attack_success']:.0%}")

    env = agent.env
    print("\nagent 自己造出的判据:")
    for spec in env.predicates:
        print(f"  - {spec.name}  ({spec.strategy}, evidence={spec.evidence})")

    path = "/tmp/svl_quickstart_env.json"
    env.save(path)
    reloaded = Environment.load(path)
    print(f"\n跨会话重载: v{reloaded.version}, {len(reloaded.predicates)} 条判据仍在")

    # PDCA 自动机：喂入日志流，自己识别/研究/验证/改进到收敛
    from svagent.pdca import Budget, PDCALoop, _sample_batches  # noqa: E402

    loop = PDCALoop(Environment(), Budget(max_cycles=8, patience=2))
    for batch in _sample_batches():
        loop.feed(batch)
        loop.run()
    s = loop.status()
    print(f"\nPDCA 自动机: {s['cycle']} 轮收敛, v{s['version']}, "
          f"判据 {s['predicates']} 条, 交人 {s['human_queue']} 项, "
          f"审计 {s['audit_records']} 条")


if __name__ == "__main__":
    main()
