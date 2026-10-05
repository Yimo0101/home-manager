# -*- coding: utf-8 -*-
"""居家管家 - 一键早安：今日简报内容构建 + 依次启动程序"""
import datetime
import os
import threading
import time

import holidays
import i18n
import nihongo


def today_events(store, day):
    return sorted(
        [e for e in store.events if e.get("date") == day.strftime("%Y-%m-%d")],
        key=lambda e: (e.get("all_day"), e.get("time", "")))


def build_brief(store, now=None, lang=None):
    """返回 [(小标题, [行...]), ...]，供简报窗口渲染"""
    now = now or datetime.datetime.now()
    day = now.date()
    lang = lang or i18n.get_lang()
    blocks = []

    blocks.append(("", [i18n.popup_date(now)]))

    marks = holidays.panel_lines(day, lang)
    if marks:
        blocks.append(("", ["  ".join(text for text, _ in marks)]))

    events = today_events(store, day)
    lines = []
    if events:
        for e in events:
            when = i18n.t("all_day") if e.get("all_day") else e.get("time", "")
            lines.append(("%s  %s" % (when, e.get("title", ""))).strip())
    else:
        lines.append(i18n.t("morning_no_events"))
    blocks.append((i18n.t("morning_today_events"), lines))

    w = nihongo.word_of_day()
    word_line = "%s（%s）%s" % (w["word"], w["kana"], w["zh"])
    blocks.append((i18n.t("nihongo_title"), [word_line, w["ex_ja"], w["ex_zh"]]))
    return blocks


def launch_apps(paths, on_each=None, delay=2.5):
    """依次启动程序（后台线程，互不阻塞）"""
    def work():
        for p in paths:
            p = p.strip().strip('"')
            if not p or not os.path.exists(p):
                continue
            try:
                if on_each:
                    on_each(os.path.basename(p))
                os.startfile(p)
            except Exception:
                continue
            time.sleep(delay)

    threading.Thread(target=work, daemon=True).start()
