# -*- coding: utf-8 -*-
"""居家管家 - 数据存储（JSON 原子读写 + 线程锁）"""
import json
import os
import threading
import uuid

from config import DATA_FILE, default_settings


def new_id():
    return uuid.uuid4().hex[:10]


def sample_data():
    """首次启动时的示例数据（可自行编辑/删除）"""
    return {
        "settings": default_settings(),
        "alarms": [
            {
                "id": new_id(),
                "name": "起床闹钟",
                "time": "07:00",
                "days": [0, 1, 2, 3, 4],   # 周一到周五
                "enabled": True,
                "ringtone": "",
                "image": "",
            },
        ],
        "tasks": [
            {
                "id": new_id(),
                "name": "吃药提醒",
                "type": "reminder",
                "time": "12:30",
                "days": [0, 1, 2, 3, 4, 5, 6],
                "date": "",               # 一次性任务时使用 YYYY-MM-DD
                "enabled": True,
                "message": "午饭后该吃药啦，记得喝温水。",
                "ringtone": "",
                "image": "",
            },
        ],
        "events": [],
        "anniversaries": [],
        "focus": {},
    }


class DataStore:
    def __init__(self, path=DATA_FILE):
        self.path = path
        self.lock = threading.RLock()
        self.data = self._load()

    def _default(self):
        return {"settings": default_settings(), "alarms": [], "tasks": [],
                "events": [], "anniversaries": [], "focus": {}}

    def _load(self):
        if os.path.exists(self.path):
            try:
                with open(self.path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # 兼容缺字段
                base = self._default()
                base.update(data)
                st = default_settings()
                st.update(base.get("settings", {}))
                base["settings"] = st
                for key in ("alarms", "tasks", "events", "anniversaries"):
                    base.setdefault(key, [])
                base.setdefault("focus", {})
                return base
            except Exception:
                # 损坏文件自动备份
                bak = self.path + ".bad"
                try:
                    os.replace(self.path, bak)
                except OSError:
                    pass
        data = sample_data()
        self._write(data)
        return data

    def _write(self, data):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.path)

    def save(self):
        with self.lock:
            self._write(self.data)

    # ---- 设置 ----
    @property
    def settings(self):
        return self.data["settings"]

    def update_settings(self, **kw):
        with self.lock:
            self.data["settings"].update(kw)
            self.save()

    # ---- 闹钟 ----
    @property
    def alarms(self):
        return self.data["alarms"]

    def upsert_alarm(self, item):
        with self.lock:
            item.setdefault("id", new_id())
            for i, old in enumerate(self.data["alarms"]):
                if old.get("id") == item["id"]:
                    self.data["alarms"][i] = item
                    break
            else:
                self.data["alarms"].append(item)
            self.save()
        return item

    def delete_alarm(self, item_id):
        with self.lock:
            self.data["alarms"] = [a for a in self.data["alarms"] if a.get("id") != item_id]
            self.save()

    # ---- 定时任务 ----
    @property
    def tasks(self):
        return self.data["tasks"]

    def upsert_task(self, item):
        with self.lock:
            item.setdefault("id", new_id())
            for i, old in enumerate(self.data["tasks"]):
                if old.get("id") == item["id"]:
                    self.data["tasks"][i] = item
                    break
            else:
                self.data["tasks"].append(item)
            self.save()
        return item

    def delete_task(self, item_id):
        with self.lock:
            self.data["tasks"] = [t for t in self.data["tasks"] if t.get("id") != item_id]
            self.save()

    # ---- 日历日程 ----
    @property
    def events(self):
        return self.data["events"]

    def upsert_event(self, item):
        with self.lock:
            item.setdefault("id", new_id())
            for i, old in enumerate(self.data["events"]):
                if old.get("id") == item["id"]:
                    self.data["events"][i] = item
                    break
            else:
                self.data["events"].append(item)
            self.save()
        return item

    def delete_event(self, item_id):
        with self.lock:
            self.data["events"] = [e for e in self.data["events"] if e.get("id") != item_id]
            self.save()

    # ---- 纪念日 / 倒数日 ----
    @property
    def anniversaries(self):
        return self.data["anniversaries"]

    def upsert_anniversary(self, item):
        with self.lock:
            item.setdefault("id", new_id())
            for i, old in enumerate(self.data["anniversaries"]):
                if old.get("id") == item["id"]:
                    self.data["anniversaries"][i] = item
                    break
            else:
                self.data["anniversaries"].append(item)
            self.save()
        return item

    def delete_anniversary(self, item_id):
        with self.lock:
            self.data["anniversaries"] = [
                a for a in self.data["anniversaries"] if a.get("id") != item_id]
            self.save()

    # ---- 番茄钟专注统计（focus: {"YYYY-MM-DD": {"minutes": n, "rounds": n}}）----
    def add_focus_minutes(self, day_key, minutes, rounds=0):
        with self.lock:
            focus = self.data.setdefault("focus", {})
            rec = focus.get(day_key)
            if not isinstance(rec, dict):
                rec = {"minutes": int(rec or 0), "rounds": 0}
            rec["minutes"] = int(rec.get("minutes", 0)) + int(minutes)
            rec["rounds"] = int(rec.get("rounds", 0)) + int(rounds)
            focus[day_key] = rec
            self.save()

    def focus_stat(self, day_key):
        rec = self.data.get("focus", {}).get(day_key, {"minutes": 0, "rounds": 0})
        if not isinstance(rec, dict):
            rec = {"minutes": int(rec or 0), "rounds": 0}
        return int(rec.get("minutes", 0)), int(rec.get("rounds", 0))
