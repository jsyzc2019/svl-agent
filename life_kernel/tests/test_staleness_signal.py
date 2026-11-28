"""§4S67 守卫测试：证据年龄标注 + 一行信号日志（只读判据）。

预注册 prereg_staleness_signal_20261128.json SHA b15efc02… 锁死口径。
纪律：G2 真实数据不伪造 STALE；G3 负向注入真通过/真失败；零副作用。
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone, timedelta

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import kernel as K

NOW = "2026-11-28T07:00:00Z"


def _write(path, rows):
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def _tmp_paths():
    d = tempfile.mkdtemp(prefix="staleness_test_")
    hb = os.path.join(d, "heartbeat_log.jsonl")
    ib = os.path.join(d, "inbound_inbox.jsonl")
    return d, hb, ib


# ---------------- G2: 真实数据不伪造 STALE ----------------

def test_real_data_all_fresh_no_fabrication():
    """真实台账最早11-24距今4天,30天阈值下全FRESH,不得凭空造STALE。"""
    r = K.staleness_probe()
    assert r["counts"]["STALE"] == 0
    assert r["counts"]["UNDATED"] == 0
    assert r["total"] == r["counts"]["FRESH"]
    assert r["total"] > 0
    assert r["verdict_unchanged"] is True and r["consumed"] is False
    assert r["is_gate_verdict"] is False


def test_signal_log_one_line_numbers_match_fields():
    """one_line 里每个数字都等于真实聚合字段,不硬编码。"""
    s = K.signal_log_probe()
    assert s["inbound_unread"] == 2
    assert s["heartbeats"] == 11
    line = s["one_line"]
    assert ("H=%d" % s["heartbeats"]) in line
    assert ("inbound=%d" % s["inbound_unread"]) in line
    assert ("echo=%s" % s["echo_verdict"]) in line
    assert ("birth_auth=%d" % s["birth_authentic"]) in line
    assert ("backfill=%d" % s["birth_backfilled"]) in line
    assert ("stale=%d" % s["staleness_counts"]["STALE"]) in line
    assert s["verdict_unchanged"] is True and s["consumed"] is False
    assert s["is_gate_verdict"] is False


# ---------------- G3: 负向注入——非恒真 ----------------

def test_stale_injection_40_days_old():
    """造40天前的timestamp→该条STALE,不是恒FRESH。"""
    d, hb, ib = _tmp_paths()
    old = (datetime.now(timezone.utc) - timedelta(days=40)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(hb, [{"direction": "old thing", "timestamp": old}])
    _write(ib, [])
    r = K.staleness_probe(now=NOW, heartbeat_log=hb, inbox_log=ib)
    assert r["counts"]["STALE"] == 1
    assert r["per_item"][0]["state"] == "STALE"
    assert r["per_item"][0]["age_days"] >= 30


def test_undated_not_counted_as_fresh():
    """无timestamp/坏timestamp→UNDATED,绝不当FRESH(沉默≠覆盖)。"""
    d, hb, ib = _tmp_paths()
    _write(hb, [
        {"direction": "no ts"},
        {"direction": "bad ts", "timestamp": "not-a-date"},
        {"direction": "empty ts", "timestamp": ""},
    ])
    _write(ib, [])
    r = K.staleness_probe(now=NOW, heartbeat_log=hb, inbox_log=ib)
    assert r["counts"]["UNDATED"] == 3
    assert r["counts"]["FRESH"] == 0
    # 纪律：UNDATED 不并入 FRESH
    assert r["stale_rate"] == 0.0
    assert r["undated_rate"] == 1.0
    assert all(it["state"] == "UNDATED" for it in r["per_item"])


def test_stale_days_boundary():
    """stale_days=1 + 2天前条目→STALE;边界可注入,证明非硬编码30。"""
    d, hb, ib = _tmp_paths()
    two_days_ago = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(hb, [{"direction": "x", "timestamp": two_days_ago}])
    _write(ib, [])
    r30 = K.staleness_probe(now=NOW, heartbeat_log=hb, inbox_log=ib, stale_days=30)
    r1 = K.staleness_probe(now=NOW, heartbeat_log=hb, inbox_log=ib, stale_days=1)
    assert r30["counts"]["FRESH"] == 1  # 2天<30
    assert r1["counts"]["STALE"] == 1   # 2天>=1


def test_no_item_silently_dropped():
    """每条都出现在per_item,STALE/UNDATED也在named_missing,不静默丢弃。"""
    d, hb, ib = _tmp_paths()
    old = (datetime.now(timezone.utc) - timedelta(days=99)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write(hb, [
        {"direction": "fresh", "timestamp": NOW},
        {"direction": "stale", "timestamp": old},
        {"direction": "undated"},
    ])
    _write(ib, [{"at": NOW, "message": "hi"}])
    r = K.staleness_probe(now=NOW, heartbeat_log=hb, inbox_log=ib)
    assert len(r["per_item"]) == 4  # 3心跳+1收件箱,一条不少
    assert len(r["named_missing_sections"]) == 2  # stale+undated 显式列名
    assert {x["state"] for x in r["per_item"]} == {"FRESH", "STALE", "UNDATED"}
    assert sum(r["counts"].values()) == r["total"] == 4


def test_signal_log_injection_changes_unread():
    """注入隔离收件箱→inbound_unread随注入变化,证明不是恒值2。"""
    d, hb, ib = _tmp_paths()
    _write(hb, [])
    _write(ib, [
        {"at": NOW, "message": "a", "consumed": False},
        {"at": NOW, "message": "b", "consumed": False},
        {"at": NOW, "message": "c", "consumed": False},
    ])
    s = K.signal_log_probe(log_path=hb, inbox_log=ib, now=NOW)
    assert s["inbound_unread"] == 3
    assert ("inbound=3" in s["one_line"])
