# 贡献指南

欢迎补充新的失败模式、判据归纳策略、元学习规则或线上日志适配器。

## 开发环境

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
python3 -m pytest -q
```

## 提交前检查

1. `python3 -m pytest -q` 全绿；
2. 五个 smoke demo 都能跑完：`demo` / `experiment` / `evolution` / `self_evolving` / `autopoiesis`；
3. 新增判据必须带回归样本，并证明它不会误杀「边界守卫」里的合法表达；
4. 任何改动不得破坏单调包含 `S_{n+1} ⊇ S_n`——归档员的回归门禁是最后防线。

## 设计约束

- 判据必须是纯函数，输出带位置的 `Diagnostic`；
- 不允许引入「需要理解语义才能判断」的判据；
- flag 与 block 分开，流畅只改变路由，不改变通过状态；
- 模糊句永远保持「不挡，只交人」，这条边界被回归测试锁住。

## 结构

新模块放在 `svagent/`，测试放在 `tests/`，示例放在 `examples/`，设计推导放在 `commentary.md`。
