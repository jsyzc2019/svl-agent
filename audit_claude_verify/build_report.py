"""后验报告构建：精研 Claude Code 验证一文 + 审查者评估门禁（§60）。
预注册已在分析前 SHA256 锁存；本脚本只读产物，不回写预注册。
"""
import hashlib
import json
from datetime import datetime, timezone, timedelta

from svagent.reviewer_evaluation import live_regression

TZ = timezone(timedelta(hours=8))
BASE = __import__("os").path.dirname(__import__("os").path.abspath(__file__))


def sha256(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    prereg = json.load(open(f"{BASE}/prereg.json", encoding="utf-8"))
    rev_prereg = json.load(open(f"{BASE}/reviewer_eval_prereg.json", encoding="utf-8"))
    engine = json.load(open(f"{BASE}/result.json", encoding="utf-8"))
    live = live_regression()

    locks = {
        "article_html": engine["source_sha_ok"],
        "prereg": engine["prereg_lock_ok"],
        "reviewer_eval_prereg": (
            open(f"{BASE}/reviewer_eval_prereg.sha256", encoding="utf-8").read().split()[0]
            == sha256(f"{BASE}/reviewer_eval_prereg.json")),
    }
    result = {
        "title": prereg["title"],
        "built_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "locks": locks,
        "V1_V8_all_present": engine["V1_V8_all_present"],
        "V9_grading": engine["V9_honesty_grading"],
        "V10_repo_gap": engine["V10_repo_gap"],
        "compiled_gate": {
            "module": rev_prereg["target_module"],
            "symbol": rev_prereg["target_symbol"],
            "rules": rev_prereg["rules_priority_order"],
            "live_regression": live,
            "kb_anchor": rev_prereg["kb_anchor"],
        },
        "honest_boundaries": prereg["honest_boundaries"] + rev_prereg["honest_boundaries"],
    }
    json.dump(result, open(f"{BASE}/final_result.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    rows = "".join(
        f"<tr><td>{n}</td><td><b>{d['action']}</b></td><td><code>{d['code']}</code></td></tr>"
        for n, d in live["cases"].items()
    )
    gap_rows = "".join(
        f"<tr><td>{t['key']}</td><td>{'✅ 有' if t['repo_has_corresponding_gate'] else '❌ 缺'}</td>"
        f"<td>{t['evidence']}</td></tr>" for t in engine["V10_repo_gap"]["targets"]
    )
    rule_items = "".join(f"<li>{r}</li>" for r in rev_prereg["rules_priority_order"])
    lock_str = " · ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in locks.items())
    pill = "PASS" if (all(locks.values()) and engine["V1_V8_all_present"] and live["all_passed"]) else "FAIL"
    color = "#1a7f37" if pill == "PASS" else "#d1242f"
    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>精研 Claude Code 验证一文 · §60</title>
<style>
body{{font-family:-apple-system,"PingFang SC",sans-serif;max-width:960px;margin:32px auto;padding:0 20px;color:#1f2328;line-height:1.65}}
h1{{font-size:23px;border-bottom:2px solid #0969da;padding-bottom:8px}}
h2{{font-size:18px;margin-top:28px;color:#0969da}}
.pill{{display:inline-block;background:{color};color:#fff;padding:4px 14px;border-radius:20px;font-weight:bold}}
table{{border-collapse:collapse;width:100%;margin-top:12px}}
th,td{{border:1px solid #d0d7de;padding:7px 11px;text-align:left;font-size:13px;vertical-align:top}}
th{{background:#f6f8fa}}
code{{background:#f6f8fa;padding:1px 5px;border-radius:4px;font-size:12px}}
.meta{{color:#57606a;font-size:13px}}
blockquote{{border-left:3px solid #0969da;margin:12px 0;padding:6px 14px;background:#f6f8fa;color:#57606a}}
</style></head><body>
<h1>精研《How the Claude Code team thinks about verification》· 把断言落到代码</h1>
<p class="meta">Addy Osmani · claude.dev · 2026-11-16 · 一手 HTML 106KB/正文 164 行 · 构建于 {result['built_at']}</p>
<p><span class="pill">精研 {pill}</span>　<span class="meta">锁存校验：{lock_str}</span></p>

<h2>三层诚实结论</h2>
<blockquote>
<b>可判</b>：数字内部一致性（~90% / up to 10 points / 39 项 / 3-10 项 / 三轮）、机制一手列出、已实施vs愿景、本仓有无对应门禁。<br>
<b>不可判</b>：系统真实有效性、90%与10points的因果、内部流程可迁移性——均 self-reported（KB-RSI06 折扣）。<br>
<b>同构打折</b>：三类测试/规则不被篡改/漏检变规则 与本仓 scoring_integrity/judgment_robustness/knowledge_base 同谱系，按 KB-STRUCT02 打折，不给本仓独立背书。
</blockquote>

<h2>V10 本仓源码级缺口核验</h2>
<table><tr><th>维度</th><th>本仓对应门禁</th><th>证据</th></tr>{gap_rows}</table>

<h2>编译成的门禁：{rev_prereg['target_symbol']}</h2>
<p>文章 line 123："Any evaluation that treats all these as one end-to-end score won't capture this nuance." 本仓从未判过评估方案本身的分阶段/对照/分离口径，编译成会拦会判的代码：</p>
<ol>{rule_items}</ol>

<h2>活体回归 8 场景（判据自咬：控制流曾漏两处 return，已修正）</h2>
<table><tr><th>场景</th><th>判定</th><th>代号</th></tr>{rows}</table>

<h2>诚实边界</h2>
<ul>{''.join(f'<li>{b}</li>' for b in result['honest_boundaries'])}</ul>
<p class="meta">遵循 §58 用户选 A：新门禁不接入 run_loop，仍是按需显式调用的判据工具库。</p>
</body></html>"""
    open(f"{BASE}/claude_verify_report.html", "w", encoding="utf-8").write(html)
    print(json.dumps({"pill": pill, "locks": locks, "live_all": live["all_passed"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
