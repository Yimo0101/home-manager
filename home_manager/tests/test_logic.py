# -*- coding: utf-8 -*-
"""居家管家 - 调度逻辑测试（不依赖界面）"""
import datetime
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from scheduler import Scheduler, parse_hm  # noqa: E402
from storage import DataStore, new_id  # noqa: E402


class Recorder:
    def __init__(self):
        self.items = []

    def __call__(self, payload):
        self.items.append(payload)


def make_store():
    tmp = tempfile.mkdtemp(prefix="hm_test_")
    return DataStore(os.path.join(tmp, "data.json")), tmp


def test_parse():
    assert parse_hm("07:00") == datetime.time(7, 0)
    assert parse_hm("23:59") == datetime.time(23, 59)
    assert parse_hm("24:00") is None
    assert parse_hm("abc") is None
    print("[OK] 时间解析")


def test_alarm_fires_and_dedup():
    store, tmp = make_store()
    store.data["alarms"] = [{
        "id": new_id(), "name": "起床", "time": "07:00",
        "days": [0, 1, 2, 3, 4], "enabled": True,
        "ringtone": "", "image": ""}]
    rec = Recorder()
    sch = Scheduler(store, rec, None)
    wed_7 = datetime.datetime(2026, 10, 7, 7, 0, 15)  # 周三
    sch._check_alarms(wed_7, False)
    assert len(rec.items) == 1 and rec.items[0]["kind"] == "alarm"
    sch._check_alarms(wed_7, False)  # 同分钟不重复
    assert len(rec.items) == 1
    sat = datetime.datetime(2026, 10, 10, 7, 0, 15)  # 周六不响
    sch._check_alarms(sat, False)
    assert len(rec.items) == 1
    # 启动宽限：错过 1 分半仍补响
    rec.items.clear()
    sch2 = Scheduler(store, Recorder(), None)
    sch2.dispatch = rec
    wed_701 = datetime.datetime(2026, 10, 7, 7, 1, 20)
    sch2._check_alarms(wed_701, True)
    assert len(rec.items) == 1
    shutil.rmtree(tmp, ignore_errors=True)
    print("[OK] 闹钟触发 / 去重 / 星期过滤 / 启动补响")


def test_next_event():
    store, tmp = make_store()
    store.data["tasks"] = []
    store.data["events"] = []
    store.data["alarms"] = [{
        "id": "a1", "name": "x", "time": "07:00",
        "days": [0, 1, 2, 3, 4], "enabled": True}]
    sch = Scheduler(store, lambda p: None, None)
    nxt = sch.next_event(datetime.datetime(2026, 10, 7, 6, 0))  # 周三 06:00
    assert nxt == datetime.datetime(2026, 10, 7, 7, 0)
    nxt = sch.next_event(datetime.datetime(2026, 10, 7, 8, 0))  # 周三 08:00 -> 周四
    assert nxt == datetime.datetime(2026, 10, 8, 7, 0)
    nxt = sch.next_event(datetime.datetime(2026, 10, 9, 8, 0))  # 周五 08:00 -> 周一
    assert nxt == datetime.datetime(2026, 10, 12, 7, 0)
    shutil.rmtree(tmp, ignore_errors=True)
    print("[OK] 下一事件计算（工作日 / 跨周末）")


def test_event_remind():
    store, tmp = make_store()
    store.data["events"] = [{
        "id": "e1", "title": "看牙", "date": "2026-10-08",
        "all_day": False, "time": "09:00", "end_time": "",
        "remind_minutes": 10, "note": "带医保卡", "reminded": False}]
    rec = Recorder()
    sch = Scheduler(store, rec, None)
    # 提前 10 分钟即 08:50 触发
    sch._check_events(datetime.datetime(2026, 10, 8, 8, 50, 5), False)
    assert len(rec.items) == 1
    assert store.events[0]["reminded"] is True
    # 再次检查不重复
    sch._check_events(datetime.datetime(2026, 10, 8, 9, 0, 5), False)
    assert len(rec.items) == 1
    shutil.rmtree(tmp, ignore_errors=True)
    print("[OK] 日历日程提前提醒且只提醒一次")


def test_onetime_task():
    store, tmp = make_store()
    store.data["tasks"] = [{
        "id": "t1", "name": "一次性", "type": "reminder",
        "time": "18:00", "days": [], "date": "2026-10-07",
        "enabled": True, "message": "x", "ringtone": "", "image": ""}]
    rec = Recorder()
    sch = Scheduler(store, rec, None)
    sch._check_tasks(datetime.datetime(2026, 10, 7, 18, 0, 20), False)
    assert len(rec.items) == 1
    assert store.tasks[0]["enabled"] is False  # 触发后自动停用
    # 过期很久的一次性任务不补响，直接停用
    store2, tmp2 = make_store()
    store2.data["tasks"] = [{
        "id": "t2", "name": "过期", "type": "reminder",
        "time": "08:00", "days": [], "date": "2026-10-01",
        "enabled": True, "message": "x"}]
    rec2 = Recorder()
    sch2 = Scheduler(store2, rec2, None)
    sch2._check_tasks(datetime.datetime(2026, 10, 7, 18, 0, 0), False)
    assert len(rec2.items) == 0
    assert store2.tasks[0]["enabled"] is False
    shutil.rmtree(tmp, ignore_errors=True)
    shutil.rmtree(tmp2, ignore_errors=True)
    print("[OK] 一次性任务触发后停用 / 过期不补响")


def test_snooze():
    store, tmp = make_store()
    sch = Scheduler(store, Recorder(), None)
    rec = Recorder()
    sch.dispatch = rec
    now = datetime.datetime(2026, 10, 7, 7, 0, 0)
    with sch._snooze_lock:
        sch._snoozes.append({"at": now + datetime.timedelta(minutes=5),
                             "payload": {"kind": "alarm", "title": "x"}})
    sch._check_snoozes(now)
    assert len(rec.items) == 0
    sch._check_snoozes(now + datetime.timedelta(minutes=5, seconds=1))
    assert len(rec.items) == 1 and rec.items[0].get("snoozed")
    shutil.rmtree(tmp, ignore_errors=True)
    print("[OK] 贪睡 5 分钟后再次提醒")


def test_storage_roundtrip():
    store, tmp = make_store()
    store.upsert_alarm({"id": "z1", "name": "保存测试", "time": "06:30",
                        "days": [0], "enabled": True})
    store.update_settings(snooze_minutes=15)
    again = DataStore(store.path)
    assert any(a["id"] == "z1" for a in again.alarms)
    assert again.settings["snooze_minutes"] == 15
    shutil.rmtree(tmp, ignore_errors=True)
    print("[OK] 数据持久化与重载")


if __name__ == "__main__":
    test_parse()
    test_alarm_fires_and_dedup()
    test_next_event()
    test_event_remind()
    test_onetime_task()
    test_snooze()
    test_storage_roundtrip()
    print("\n全部逻辑测试通过 ✅")
