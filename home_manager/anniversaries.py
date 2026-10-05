# -*- coding: utf-8 -*-
"""居家管家 - 纪念日 / 倒数日逻辑（支持公历、农历、每年重复）

item = {
  "id": str, "title": str,
  "calendar": "solar" | "lunar",
  "date": "YYYY-MM-DD",   # solar=公历日期；lunar=该农历日期在“基准公历年”对应的农历坐标
  "yearly": bool,
}
农历日期存储说明：date 字段里的年月日即农历坐标（农历年/月/日），
显示与换算时按农历处理；is_leap 一律按非闰月（生日纪念通常不取闰月）。
"""
import datetime

import holidays


def _parts(item):
    y, m, d = (int(x) for x in str(item["date"]).split("-"))
    return y, m, d


def lunar_occurrence(item, year):
    """农历纪念日在公历 year 年的对应公历日期（该年无此闰日则回退月末）"""
    _, lm, ld = _parts(item)
    try:
        return holidays.lunar_to_solar(year, lm, ld, is_leap=False)
    except ValueError:
        # 小月无三十，回退到该月最后一天（廿九）
        return holidays.lunar_to_solar(year, lm, ld - 1, is_leap=False)


def next_occurrence(item, today=None):
    """返回 (公历date, 距今天数)。days=0 即今天；非重复且已过返回负数天数。"""
    today = today or datetime.date.today()
    y, m, d = _parts(item)
    if item.get("calendar") == "lunar":
        if item.get("yearly", True):
            for year in (today.year, today.year + 1):
                occ = lunar_occurrence(item, year)
                days = (occ - today).days
                if days >= 0:
                    return occ, days
            return occ, days
        return holidays.lunar_to_solar(y, m, d), (
            holidays.lunar_to_solar(y, m, d) - today).days
    # 公历
    if item.get("yearly", True):
        for year in (today.year, today.year + 1):
            try:
                occ = datetime.date(year, m, d)
            except ValueError:
                occ = datetime.date(year, m, 28)
            days = (occ - today).days
            if days >= 0:
                return occ, days
        return occ, days
    occ = datetime.date(y, m, d)
    return occ, (occ - today).days


def coord_text(item, lang="zh"):
    """纪念日日期的副标题文本"""
    y, m, d = _parts(item)
    if item.get("calendar") == "lunar":
        return holidays.lunar_coord_label(m, d, lang)
    return "%02d-%02d" % (m, d)


def upcoming(items, today=None, limit=6):
    """按临近程度排序的 [(item, date, days)]，今天的排最前"""
    today = today or datetime.date.today()
    rows = []
    for it in items:
        try:
            occ, days = next_occurrence(it, today)
            rows.append((it, occ, days))
        except Exception:
            continue
    rows.sort(key=lambda r: (r[2] if r[2] >= 0 else 10 ** 6, r[1]))
    return rows[:limit]
