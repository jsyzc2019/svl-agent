"""后验报告构建：调用点完整性门禁（§59）。
预注册 call_site_prereg.json 已在实现前 SHA256 锁存；本脚本只读运行产物，
不回写预注册，不伪装后验为预注册。
"""
import hashlib
import json
from datetime import datetime, timezone, timedelta

from svagent.call_site_integrity import live_regression

TZ = timezone(timedelta(hours=8))


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    prereg = json.load(open("call_site_prereg.json", encoding="utf-8"))
    stored = open("call_site_prereg.sha256", encoding="utf-8").read().split()[0]
    actual = sha256("call_site_prereg.json")
    lock_ok = (stored == actual)

    live = live_regression()
    result = {
        "prereg_id": prereg["prereg_id"],
        "built_at": datetime.now(TZ).isoformat(timespec="seconds"),
        "prereg_sha256_stored": stored,
        "prereg_sha256_actual": actual,
        "prereg_lock_ok": lock_ok,
        "rules": prereg["rules_priority_order"],
        "live_regression": live,
        "verdict": {
            "all_live_passed": live["all_passed"],
            "rule_count": len(prereg["rules_priority_order"]),
            "case_count": len(live["cases"]),
        },
        "honest_boundaries": prereg["honest_boundaries"],
    }
    json.dump(result, open("call_site_result.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    # HTML 报告
    rows = "".join(
        f"<tr><td>{name}</td><td><b>{d['action']}</b></td><td><code>{d['code']}</code></td></tr>"
        for name, d in live["cases"].items()
    )
    rule_items = "".join(f"<li>{r}</li>" for r in prereg["rules_priority_order"])
    bnd_items = "".join(f"<li>{b}</li>" for b in prereg["honest_boundaries"])
    check_pill = "PASS" if live["all_passed"] and lock_ok else "FAIL"
    pill_color = "#1a7f37" if check_pill == "PASS" else "#d1242f"
    html = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<title>调用点完整性门禁 · §59</title>
<style>
body{{font-family:-apple-system,"PingFang SC",sans-serif;max-width:900px;margin:32px auto;padding:0 20px;color:#1f2328;line-height:1.65}}
h1{{font-size:24px;border-bottom:2px solid #0969da;padding-bottom:8px}}
h2{{font-size:18px;margin-top:28px;color:#0969da}}
.pill{{display:inline-block;background:{pill_color};color:#fff;padding:4px 14px;border-radius:20px;font-weight:bold}}
table{{border-collapse:collapse;width:100%;margin-top:12px}}
th,td{{border:1px solid #d0d7de;padding:8px 12px;text-align:left;font-size:14px}}
th{{background:#f6f8fa}}
code{{background:#f6f8fa;padding:1px 5px;border-radius:4px;font-size:13px}}
.meta{{color:#57606a;font-size:13px}}
blockquote{{border-left:3px solid #0969da;margin:12px 0;padding:6px 14px;background:#f6f8fa;color:#57606a}}
</style></head><body>
<h1>调用点完整性门禁 · 把认知变成能力，把断言落到代码</h1>
<p class="meta">预注册 {prereg['prereg_id']} · 构建于 {result['built_at']} ·
SHA256 锁存校验 <b>{'OK' if lock_ok else 'FAIL'}</b></p>
<p><span class="pill">活体回归 {check_pill}</span></p>

<h2>这条断言从哪来</h2>
<blockquote>{prereg['cognitive_source']}</blockquote>

<h2>会拦会判的规则（按优先级写死）</h2>
<ol>{rule_items}</ol>

<h2>活体回归 8 场景</h2>
<table><tr><th>场景</th><th>判定</th><th>代号</th></tr>{rows}</table>

<h2>诚实边界</h2>
<ul>{bnd_items}</ul>

<p class="meta">预注册 SHA256（存储）：<code>{stored}</code><br>
本门禁由 §58 本仓自审的认知增量编译，按 KB-STRUCT02 不构成独立验证；
遵循 §58 用户选 A，不接入 run_loop。</p>
</body></html>"""
    open("call_site_report.html", "w", encoding="utf-8").write(html)
    print(json.dumps({"lock_ok": lock_ok, "all_live_passed": live["all_passed"],
                      "case_count": len(live["cases"])}, ensure_ascii=False))


if __name__ == "__main__":
    main()
