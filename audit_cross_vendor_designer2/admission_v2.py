"""§111 AST 控制流级标签泄漏准入规则（事前锁定，spawn 前 commit）。

相对 §110 的 word-boundary 规则的唯一修订（KB-META18 定位的弱点）：
- §110: re.search(r'\\btoken\\b', strip_docstrings(src)) —— 标签词在源码任何位置出现即判泄漏，
  包括 notes.append("...negation...") 的字符串字面量（正当语义说明），造成误报。
- §111(v2): 只查 judge 函数**控制流**里对标签字段的读取：
    (a) Subscript 键为字符串常量且命中标签载体字段（gt/deletion_class/variant/orig_id/...）
    (b) Attribute 访问命中标签载体字段
    (c) 调用名命中标签载体函数（scorer_key/load_gt/get_label/...）
    (d) Name 直接引用标签载体全局（scorer_key/key/gt_table/...）
    (e) 硬编码样本 id / 随机数 / 时间 / 外部文件 / os/sys import
  字符串 Constant（notes/signals 的说明文字）一律不算泄漏——它不读取任何标签。

合法性（事前论证，非对着结果调阈值）：
- 真泄漏的本质是"judge 读取了 text_a/text_b 之外的标签信息"，这必然表现为对某个
  非入参数据结构的字段访问或外部读取；字符串字面量不构成信息通道。
- 规则形式由信息论语义决定，与"这批 judge 恰好写了什么 notes"无关。
- 对偶测试（tests/test_admission_ast_audit.py）：构造含真泄漏的 judge 必须被拒，
  构造仅在 notes 里提 negation/variant 的 judge 必须放行——两者在规则锁定前写死。

使用：admit_source(src) -> dict；不依赖具体样本、不依赖 gt 值。
"""
import ast
import re

# 标签载体字段：judge 若在控制流里读取这些字段=拿到了 text_a/text_b 之外的标签
LABEL_FIELDS = {
    "gt", "ground_truth", "label", "deletion_class", "variant", "orig_id",
    "canary", "negation", "is_clean", "is_tampered", "answer", "target",
}
# 标签载体标识符（变量/函数/模块名）
LABEL_CARRIERS = {
    "scorer_key", "key", "gt_table", "gt_map", "labels", "get_label", "load_gt",
    "load_ground_truth", "read_scorer", "load_key", "manifest", "result",
}
# 非确定性/外部 IO 调用或模块
RNG_CALLS = {"random", "randint", "choice", "shuffle", "uuid", "time", "datetime", "perf_counter"}
IO_MODULES = {"os", "sys", "subprocess", "socket", "urllib", "requests", "open", "pathlib"}
# 样本 id（§107 id 中性化后 N01..N18）
ID_RE = re.compile(r"\bN0[1-9]\b|\bN1[0-8]\b")


def _is_str_constant(node):
    return isinstance(node, ast.Constant) and isinstance(node.value, str)


def admit_source(src, judge_params=None):
    """对一份 judge 源码做 AST 控制流准入审计。返回结构化结论。"""
    tree = ast.parse(src)
    func = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "judge":
            func = node
            break
    if func is None:
        return {"admission_ok": False, "reason": "no_judge_function", "signature_ok": False,
                "label_reads": [], "hardcoded_ids": [], "rng_or_io": []}

    params = [a.arg for a in func.args.args]
    signature_ok = len(params) == 2

    label_reads = []   # 真正的标签字段读取（控制流）
    hard_ids = set()
    rng_io = []

    for node in ast.walk(func):
        # (a) subscript 键为字符串常量且命中标签字段
        if isinstance(node, ast.Subscript):
            sl = node.slice
            if _is_str_constant(sl) and sl.value in LABEL_FIELDS:
                label_reads.append(f"subscript[{sl.value}]")
            elif isinstance(sl, ast.Constant) and isinstance(sl.value, str) and sl.value in LABEL_CARRIERS:
                label_reads.append(f"subscript[{sl.value}]")
        # (b) attribute 命中标签字段/载体
        elif isinstance(node, ast.Attribute) and node.attr in LABEL_FIELDS | LABEL_CARRIERS:
            label_reads.append(f"attr.{node.attr}")
        # (c) 调用名命中标签载体/RNG
        elif isinstance(node, ast.Call):
            f = node.func
            nm = f.id if isinstance(f, ast.Name) else (f.attr if isinstance(f, ast.Attribute) else None)
            if nm in LABEL_CARRIERS:
                label_reads.append(f"call:{nm}")
            if nm in RNG_CALLS:
                rng_io.append(f"call:{nm}")
            if nm in IO_MODULES and nm == "open":
                rng_io.append("call:open")
        # (d) Name 直接引用标签载体全局（排除 params 与局部赋值名）
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
            if node.id in LABEL_CARRIERS and node.id not in params:
                label_reads.append(f"name:{node.id}")

    # (e) 硬编码样本 id：只看字符串常量与源码文本（id 是字面标记，任何出现都算）
    for node in ast.walk(func):
        if _is_str_constant(node):
            hard_ids.update(ID_RE.findall(node.value))
    hard_ids.update(ID_RE.findall(src))
    hard_ids = sorted(hard_ids)

    # import 外部 IO / 随机模块
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for al in node.names:
                root = al.name.split(".")[0]
                if root in IO_MODULES or root in RNG_CALLS:
                    rng_io.append(f"import:{al.name}")
        elif isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            if root in IO_MODULES or root in RNG_CALLS:
                rng_io.append(f"from:{node.module}")

    admission_ok = signature_ok and not label_reads and not hard_ids and not rng_io
    return {
        "signature": params, "signature_ok": signature_ok,
        "label_reads": label_reads, "no_label_read": not label_reads,
        "hardcoded_ids": hard_ids, "no_hardcoded_ids": not hard_ids,
        "rng_or_io": rng_io, "deterministic_no_io": not rng_io,
        "admission_ok": admission_ok,
    }


if __name__ == "__main__":
    import json, sys
    src = open(sys.argv[1], encoding="utf-8").read()
    print(json.dumps(admit_source(src), ensure_ascii=False, indent=2))
