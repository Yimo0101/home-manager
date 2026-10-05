# -*- coding: utf-8 -*-
"""居家管家 - 后台调度器

每秒检查一次：
- 闹钟：按星期重复，到分触发
- 定时任务：提醒类（按星期重复 / 一次性日期）、程序类（打开程序+点击）
- 日历日程：指定日期的定时日程，按“提前提醒分钟”触发
- 贪睡：临时的一次性提醒
并负责计算下一个事件时间，交给 WakeManager 唤醒睡眠中的电脑。
"""
import datetime
import logging
import threading
import time

import i18n
from actions import launch_task
from media import resolve_image, resolve_ringtone

log = logging.getLogger("home_manager")

GRACE_SECONDS = 120  # 程序刚启动时，错过 2 分钟内的闹钟仍补提醒


def parse_hm(s):
    try:
        h, m = str(s).split(":")
        h, m = int(h), int(m)
        if 0 <= h <= 23 and 0 <= m <= 59:
            return datetime.time(h, m)
    except Exception:
        return None
    return None


def parse_date(s):
    try:
        return datetime.datetime.strptime(str(s), "%Y-%m-%d").date()
    except Exception:
        return None


class Scheduler(threading.Thread):
    def __init__(self, store, dispatch, wake_manager=None):
        """dispatch(payload)：由界面层注入，需线程安全（内部会投递到主线程）"""
        super().__init__(daemon=True)
        self.store = store
        self.dispatch = dispatch
        self.wake = wake_manager
        self._stop = threading.Event()
        self._fired = set()          # 已触发去重键
        self._snoozes = []           # [{"at": datetime, "payload": dict}]
        self._snooze_lock = threading.Lock()
        self._wake_due = None

    # ---------- 对外 ----------
    def stop(self):
        self._stop.set()

    def add_snooze(self, payload, minutes):
        at = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        with self._snooze_lock:
            self._snoozes.append({"at": at, "payload": payload})
        self._refresh_wake()

    def _alarm_payload(self, title, line2, item=None, kind="alarm"):
        s = self.store.settings
        item = item or {}
        return {
            "kind": kind,
            "title": title,
            "line2": line2,
            "ringtone": resolve_ringtone(s, item.get("ringtone", "")),
            "image": resolve_image(s, item.get("image", "")),
        }

    # ---------- 主循环 ----------
    def run(self):
        startup = True
        while not self._stop.is_set():
            try:
                now = datetime.datetime.now()
                self._check_alarms(now, startup)
                self._check_tasks(now, startup)
                self._check_events(now, startup)
                self._check_anniversaries(now)
                self._check_snoozes(now)
                self._refresh_wake(now)
            except Exception:
                log.exception("调度循环异常")
            startup = False
            self._stop.wait(1.0)

    # ---------- 闹钟 ----------
    def _check_alarms(self, now, startup):
        for a in list(self.store.alarms):
            if not a.get("enabled", True):
                continue
            t = parse_hm(a.get("time"))
            days = a.get("days", [])
            if t is None or not days:
                continue
            due_today = datetime.datetime.combine(now.date(), t)
            if now.weekday() not in days:
                continue
            key = "alarm:%s:%s" % (a.get("id"), due_today.strftime("%Y%m%d%H%M"))
            if key in self._fired:
                continue
            delta = (now - due_today).total_seconds()
            if (now.hour == t.hour and now.minute == t.minute) or (
                startup and 0 < delta <= GRACE_SECONDS
            ):
                self._fired.add(key)
                payload = self._alarm_payload(
                    a.get("name") or i18n.t("alarms_title"),
                    "%s %s" % (a.get("time", ""), i18n.day_text(days)),
                    a, kind="alarm",
                )
                self.dispatch(payload)

    # ---------- 定时任务 ----------
    def _check_tasks(self, now, startup):
        for task in list(self.store.tasks):
            if not task.get("enabled", True):
                continue
            t = parse_hm(task.get("time"))
            if t is None:
                continue
            days = task.get("days", [])
            date_s = task.get("date", "")
            if days:
                due_today = datetime.datetime.combine(now.date(), t)
                if now.weekday() not in days:
                    continue
                key = "task:%s:%s" % (task.get("id"), due_today.strftime("%Y%m%d%H%M"))
                if key in self._fired:
                    continue
                delta = (now - due_today).total_seconds()
                if (now.hour == t.hour and now.minute == t.minute) or (
                    startup and 0 < delta <= GRACE_SECONDS
                ):
                    self._fired.add(key)
                    self._fire_task(task)
            elif date_s:
                d = parse_date(date_s)
                if d is None:
                    continue
                due = datetime.datetime.combine(d, t)
                if now >= due:
                    delta = (now - due).total_seconds()
                    if delta <= GRACE_SECONDS:
                        key = "taskonce:%s" % task.get("id")
                        if key not in self._fired:
                            self._fired.add(key)
                            self._fire_task(task)
                    # 一次性任务过期后自动停用
                    if task.get("enabled"):
                        task["enabled"] = False
                        self.store.save()

    def _fire_task(self, task):
        if task.get("type") == "program":
            def work():
                try:
                    launch_task(task)
                    log.info("已执行打开程序任务：%s", task.get("name"))
                except Exception as e:
                    log.exception("打开程序失败")
                    self.dispatch(self._alarm_payload(
                        i18n.t("task_fail_title"),
                        "%s：%s" % (task.get("name", ""), e),
                        task, kind="reminder"))
            threading.Thread(target=work, daemon=True).start()
        else:
            self.dispatch(self._alarm_payload(
                task.get("name") or i18n.t("tag_reminder"),
                task.get("message") or i18n.t("default_msg"),
                task, kind="reminder"))

    # ---------- 日历日程 ----------
    def _check_events(self, now, startup):
        changed = False
        for ev in list(self.store.events):
            if ev.get("all_day") or ev.get("reminded"):
                continue
            t = parse_hm(ev.get("time"))
            d = parse_date(ev.get("date"))
            if t is None or d is None:
                continue
            remind = int(ev.get("remind_minutes", 10))
            if remind < 0:
                ev["reminded"] = True
                changed = True
                continue
            due = datetime.datetime.combine(d, t) - datetime.timedelta(minutes=remind)
            if now >= due:
                delta = (now - due).total_seconds()
                if delta <= GRACE_SECONDS:
                    key = "event:%s" % ev.get("id")
                    if key not in self._fired:
                        self._fired.add(key)
                        prefix = (i18n.t("event_now") if remind == 0
                                  else i18n.t("event_min", remind))
                        line2 = "%s：%s" % (ev.get("date", ""), ev.get("title", ""))
                        note = ev.get("note", "")
                        payload = self._alarm_payload(
                            i18n.t("event_reminder_title", prefix),
                            ev.get("title", "日程") + (("\n" + note) if note else ""),
                            ev, kind="reminder")
                        payload["line2"] = line2 if not note else line2 + "\n" + note
                        self.dispatch(payload)
                ev["reminded"] = True
                changed = True
        if changed:
            self.store.save()

    # ---------- 纪念日 ----------
    def _check_anniversaries(self, now):
        import anniversaries as ann_mod
        today = now.date()
        for item in list(self.store.anniversaries):
            try:
                occ, days = ann_mod.next_occurrence(item, today)
            except Exception:
                continue
            if days != 0:
                continue
            key = "ann:%s:%s" % (item.get("id"), today.strftime("%Y%m%d"))
            if key in self._fired:
                continue
            self._fired.add(key)
            self.dispatch(self._alarm_payload(
                i18n.t("ann_reminder"),
                "%s ♡\n%s" % (item.get("title", ""), i18n.t("ann_today")),
                item, kind="reminder"))

    # ---------- 贪睡 ----------
    def _check_snoozes(self, now):
        with self._snooze_lock:
            due_items = [s for s in self._snoozes if now >= s["at"]]
            self._snoozes = [s for s in self._snoozes if now < s["at"]]
        for item in due_items:
            payload = dict(item["payload"])
            payload["snoozed"] = True
            self.dispatch(payload)

    # ---------- 下一个事件 / 唤醒 ----------
    def next_event(self, now=None):
        now = now or datetime.datetime.now()
        candidates = []

        def add_repeating(t_str, days):
            t = parse_hm(t_str)
            if t is None or not days:
                return
            for i in range(8):
                day = now.date() + datetime.timedelta(days=i)
                cand = datetime.datetime.combine(day, t)
                if day.weekday() in days and cand > now:
                    candidates.append(cand)
                    return

        for a in self.store.alarms:
            if a.get("enabled", True):
                add_repeating(a.get("time"), a.get("days", []))
        for task in self.store.tasks:
            if not task.get("enabled", True):
                continue
            if task.get("days"):
                add_repeating(task.get("time"), task.get("days", []))
            else:
                d = parse_date(task.get("date", ""))
                t = parse_hm(task.get("time"))
                if d and t:
                    cand = datetime.datetime.combine(d, t)
                    if cand > now:
                        candidates.append(cand)
        for ev in self.store.events:
            if ev.get("all_day") or ev.get("reminded"):
                continue
            d = parse_date(ev.get("date"))
            t = parse_hm(ev.get("time"))
            if d and t:
                remind = int(ev.get("remind_minutes", 10))
                if remind < 0:
                    continue
                cand = datetime.datetime.combine(d, t) - datetime.timedelta(minutes=remind)
                if cand > now:
                    candidates.append(cand)
        with self._snooze_lock:
            candidates.extend(s["at"] for s in self._snoozes if s["at"] > now)
        return min(candidates) if candidates else None

    def _refresh_wake(self, now=None):
        if not self.wake or not self.store.settings.get("wake_enabled", True):
            return
        nxt = self.next_event(now)
        if not nxt:
            return
        ahead = int(self.store.settings.get("wake_ahead_seconds", 20))
        wake_at = nxt - datetime.timedelta(seconds=ahead)
        if wake_at <= datetime.datetime.now():
            return
        if self._wake_due and abs((wake_at - self._wake_due).total_seconds()) < 20:
            return
        if self.wake.schedule(wake_at):
            self._wake_due = wake_at
            log.info("已设置唤醒时间：%s（事件 %s）", wake_at.strftime("%Y-%m-%d %H:%M"),
                     nxt.strftime("%Y-%m-%d %H:%M"))


def _day_text(days):
    """兼容旧引用，统一走 i18n.day_text"""
    return i18n.day_text(days)
