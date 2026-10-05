# -*- coding: utf-8 -*-
"""居家管家 - 农历 / 二十四节气 / 中外节日（离线内置，无需联网）

- 二十四节气：太阳视黄经天文计算（Meeus 低精度公式，误差远小于 1 小时），
  按北京时间取日期，覆盖任意年份。
- 农历：1900-2100 标准农历表 + 公历换算。
- 节日：农历传统节日、公历节日、日期浮动的母亲节/父亲节/感恩节，三语名称。
"""
import datetime
import math

# ---------------- 二十四节气（黄经顺序：春分=0°） ----------------
# key: (黄经, 中文名, 日本語名, English)
TERMS = [
    (0,   "春分", "春分", "Spring Equinox"),
    (15,  "清明", "清明", "Pure Brightness"),
    (30,  "谷雨", "穀雨", "Grain Rain"),
    (45,  "立夏", "立夏", "Beginning of Summer"),
    (60,  "小满", "小満", "Lesser Fullness"),
    (75,  "芒种", "芒種", "Grain in Ear"),
    (90,  "夏至", "夏至", "Summer Solstice"),
    (105, "小暑", "小暑", "Lesser Heat"),
    (120, "大暑", "大暑", "Great Heat"),
    (135, "立秋", "立秋", "Beginning of Autumn"),
    (150, "处暑", "処暑", "End of Heat"),
    (165, "白露", "白露", "White Dew"),
    (180, "秋分", "秋分", "Autumn Equinox"),
    (195, "寒露", "寒露", "Cold Dew"),
    (210, "霜降", "霜降", "Frost's Descent"),
    (225, "立冬", "立冬", "Beginning of Winter"),
    (240, "小雪", "小雪", "Lesser Snow"),
    (255, "大雪", "大雪", "Greater Snow"),
    (270, "冬至", "冬至", "Winter Solstice"),
    (285, "小寒", "小寒", "Slight Cold"),
    (300, "大寒", "大寒", "Great Cold"),
    (315, "立春", "立春", "Beginning of Spring"),
    (330, "雨水", "雨水", "Rain Water"),
    (345, "惊蛰", "啓蟄", "Awakening of Insects"),
]
TERM_KEYS_ZH = {zh: (zh, ja, en) for lon, zh, ja, en in TERMS}
_TERM_BY_LON = {lon: (zh, ja, en) for lon, zh, ja, en in TERMS}

# ---------------- 农历表 1900-2100 ----------------
_LUNAR_INFO = [
    0x04bd8, 0x04ae0, 0x0a570, 0x054d5, 0x0d260, 0x0d950, 0x16554, 0x056a0,
    0x09ad0, 0x055d2, 0x04ae0, 0x0a5b6, 0x0a4d0, 0x0d250, 0x1d255, 0x0b540,
    0x0d6a0, 0x0ada2, 0x095b0, 0x14977, 0x04970, 0x0a4b0, 0x0b4b5, 0x06a50,
    0x06d40, 0x1ab54, 0x02b60, 0x09570, 0x052f2, 0x04970, 0x06566, 0x0d4a0,
    0x0ea50, 0x06e95, 0x05ad0, 0x02b60, 0x186e3, 0x092e0, 0x1c8d7, 0x0c950,
    0x0d4a0, 0x1d8a6, 0x0b550, 0x056a0, 0x1a5b4, 0x025d0, 0x092d0, 0x0d2b2,
    0x0a950, 0x0b557, 0x06ca0, 0x0b550, 0x15355, 0x04da0, 0x0a5b0, 0x14573,
    0x052b0, 0x0a9a8, 0x0e950, 0x06aa0, 0x0aea6, 0x0ab50, 0x04b60, 0x0aae4,
    0x0a570, 0x05260, 0x0f263, 0x0d950, 0x05b57, 0x056a0, 0x096d0, 0x04dd5,
    0x04ad0, 0x0a4d0, 0x0d4d4, 0x0d250, 0x0d558, 0x0b540, 0x0b6a0, 0x195a6,
    0x095b0, 0x049b0, 0x0a974, 0x0a4b0, 0x0b27a, 0x06a50, 0x06d40, 0x0af46,
    0x0ab60, 0x09570, 0x04af5, 0x04970, 0x064b0, 0x074a3, 0x0ea50, 0x06b58,
    0x055c0, 0x0ab60, 0x096d5, 0x092e0, 0x0c960, 0x0d954, 0x0d4a0, 0x0da50,
    0x07552, 0x056a0, 0x0abb7, 0x025d0, 0x092d0, 0x0cab5, 0x0a950, 0x0b4a0,
    0x0baa4, 0x0ad50, 0x055d9, 0x04ba0, 0x0a5b0, 0x15176, 0x052b0, 0x0a930,
    0x07954, 0x06aa0, 0x0ad50, 0x05b52, 0x04b60, 0x0a6e6, 0x0a4e0, 0x0d260,
    0x0ea65, 0x0d530, 0x05aa0, 0x076a3, 0x096d0, 0x04afb, 0x04ad0, 0x0a4d0,
    0x1d0b6, 0x0d250, 0x0d520, 0x0dd45, 0x0b5a0, 0x056d0, 0x055b2, 0x049b0,
    0x0a577, 0x0a4b0, 0x0aa50, 0x1b255, 0x06d20, 0x0ada0, 0x14b63, 0x09370,
    0x049f8, 0x04970, 0x064b0, 0x168a6, 0x0ea50, 0x06b20, 0x1a6c4, 0x0aae0,
    0x0a2e0, 0x0d2e3, 0x0c960, 0x0d557, 0x0d4a0, 0x0da50, 0x05d55, 0x056a0,
    0x0a6d0, 0x055d4, 0x052d0, 0x0a9b8, 0x0a950, 0x0b4a0, 0x0b6a6, 0x0ad50,
    0x055a0, 0x0aba4, 0x0a5b0, 0x052b0, 0x0b273, 0x06930, 0x07337, 0x06aa0,
    0x0ad50, 0x14b55, 0x04b60, 0x0a570, 0x054e4, 0x0d160, 0x0e968, 0x0d520,
    0x0daa0, 0x16aa6, 0x056d0, 0x04ae0, 0x0a9d4, 0x0a2d0, 0x0d150, 0x0f252,
    0x0d520]

_LUNAR_MONTH_ZH = ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月",
                   "九月", "十月", "冬月", "腊月"]
_LUNAR_MONTH_JA = ["正月", "二月", "三月", "四月", "五月", "六月", "七月", "八月",
                   "九月", "十月", "十一月", "十二月"]
_LUNAR_DAY_ZH = [
    "初一", "初二", "初三", "初四", "初五", "初六", "初七", "初八", "初九", "初十",
    "十一", "十二", "十三", "十四", "十五", "十六", "十七", "十八", "十九", "二十",
    "廿一", "廿二", "廿三", "廿四", "廿五", "廿六", "廿七", "廿八", "廿九", "三十"]


def _leap_month(y):
    return _LUNAR_INFO[y - 1900] & 0xf


def _leap_days(y):
    if _leap_month(y):
        return 30 if (_LUNAR_INFO[y - 1900] & 0x10000) else 29
    return 0


def _month_days(y, m):
    return 30 if (_LUNAR_INFO[y - 1900] & (0x10000 >> m)) else 29


def _year_days(y):
    total = 348
    i = 0x8000
    while i > 0x8:
        if _LUNAR_INFO[y - 1900] & i:
            total += 1
        i >>= 1
    return total + _leap_days(y)


def solar_to_lunar(y, m, d):
    """公历 -> (农历年, 月, 日, 是否闰月)"""
    offset = (datetime.date(y, m, d) - datetime.date(1900, 1, 31)).days
    ly = 1900
    while ly < 2101:
        yd = _year_days(ly)
        if offset < yd:
            break
        offset -= yd
        ly += 1
    leap = _leap_month(ly)  # 0 或闰月月份（闰月插在该正常月之后）
    lm = 1
    is_leap = False
    while True:
        md = _leap_days(ly) if is_leap else _month_days(ly, lm)
        if offset < md:
            return ly, lm, offset + 1, is_leap
        offset -= md
        if is_leap:
            is_leap = False
            lm += 1
        elif leap and lm == leap:
            is_leap = True
        else:
            lm += 1


def lunar_to_solar(ly, lm, ld, is_leap=False):
    """农历(年,月,日[,闰]) -> 公历 date。范围 1900~2100。"""
    if not (1900 <= ly <= 2100 and 1 <= lm <= 12 and 1 <= ld <= 30):
        raise ValueError("农历日期超出范围")
    offset = 0
    for y in range(1900, ly):
        offset += _year_days(y)
    leap = _leap_month(ly)
    m = 1
    while m < lm:
        offset += _month_days(ly, m)
        if leap == m:
            offset += _leap_days(ly)
        m += 1
    if is_leap and leap == lm:
        offset += _month_days(ly, lm)   # 先过正常月才到闰月
    offset += ld - 1
    return datetime.date(1900, 1, 31) + datetime.timedelta(days=offset)


def lunar_coord_label(lm, ld, lang="zh"):
    """农历月日的可读文本"""
    if lang == "zh":
        return _LUNAR_MONTH_ZH[lm - 1] + _LUNAR_DAY_ZH[ld - 1]
    if lang == "ja":
        return _LUNAR_MONTH_JA[lm - 1] + _LUNAR_DAY_ZH[ld - 1]
    return "Lunar %d/%d" % (lm, ld)


# ---------------- 节气天文计算 ----------------
def _julian_day(dt_ut):
    y, m = dt_ut.year, dt_ut.month
    d = dt_ut.day + (dt_ut.hour + dt_ut.minute / 60) / 24
    if m <= 2:
        y -= 1
        m += 12
    a = y // 100
    b = 2 - a + a // 4
    return (int(365.25 * (y + 4716)) + int(30.6001 * (m + 1))
            + d + b - 1524.5)


def _sun_longitude(jd):
    """太阳视黄经（度），Meeus 低精度"""
    t = (jd - 2451545.0) / 36525.0
    l0 = (280.46646 + 36000.76983 * t + 0.0003032 * t * t) % 360
    mr = math.radians((357.52911 + 35999.05029 * t - 0.0001537 * t * t) % 360)
    c = ((1.914602 - 0.004817 * t - 0.000014 * t * t) * math.sin(mr)
         + (0.019993 - 0.00101 * t) * math.sin(2 * mr)
         + 0.000289 * math.sin(3 * mr))
    omega = math.radians(125.04 - 1934.136 * t)
    return (l0 + c - 0.00569 - 0.00478 * math.sin(omega)) % 360


_terms_cache = {}


def terms_of_year(year):
    """{datetime.date: 节气中文名}，按北京时间定日期"""
    if year in _terms_cache:
        return _terms_cache[year]
    # 每天北京时间 12:00（UT 4:00）采样一次太阳黄经
    days = []
    jds = []
    d0 = datetime.date(year, 1, 1)
    for i in range(366):
        d = d0 + datetime.timedelta(days=i)
        dt_ut = datetime.datetime(d.year, d.month, d.day, 4, 0)
        days.append(d)
        jds.append(_julian_day(dt_ut))
    lons = [_sun_longitude(j) for j in jds]
    # 展开成单调递增序列
    unwrap = [lons[0]]
    add = 0.0
    for i in range(1, len(lons)):
        v = lons[i] + add
        if v < unwrap[-1] - 180:
            add += 360
            v += 360
        unwrap.append(v)
    # 黄经目标按年内时间顺序（小寒 285° 在 1 月；春分 0° 展开为 360°，
    # 其后节气在展开坐标中依次为 375°、390°……）
    targets = [285, 300, 315, 330, 345, 360] + list(range(375, 631, 15))
    result = {}
    for target in targets:
        for i in range(1, len(unwrap)):
            if unwrap[i - 1] < target <= unwrap[i]:
                # 在两天之间二分求精确时刻（UT）
                lo, hi = jds[i - 1], jds[i]
                for _ in range(12):
                    mid = (lo + hi) / 2
                    v = _sun_longitude(mid)
                    while v < target - 180:  # 展开到与目标同一圈
                        v += 360
                    if v < target:
                        lo = mid
                    else:
                        hi = mid
                bj = datetime.datetime.utcfromtimestamp(
                    ((lo + hi) / 2 - 2440587.5) * 86400) + datetime.timedelta(hours=8)
                key_lon = target % 360
                result[bj.date()] = _TERM_BY_LON[key_lon][0]
                break
    _terms_cache[year] = result
    return result


# ---------------- 节日 ----------------
# (月, 日, key, 中文, 日本語, English)
_GREG_FESTIVALS = [
    (1, 1, "new_year", "元旦", "元旦", "New Year's Day"),
    (2, 14, "valentine", "情人节", "バレンタインデー", "Valentine's Day"),
    (3, 8, "womens_day", "妇女节", "国際女性デー", "Women's Day"),
    (3, 12, "arbor_day", "植树节", "植樹デー", "Arbor Day"),
    (4, 1, "fools_day", "愚人节", "エイプリルフール", "April Fools' Day"),
    (5, 1, "labour_day", "劳动节", "メーデー", "Labour Day"),
    (5, 4, "youth_day", "青年节", "青年節", "Youth Day"),
    (6, 1, "childrens_day", "儿童节", "子供の日", "Children's Day"),
    (7, 1, "party_day", "建党节", "建党記念日", "CPC Founding Day"),
    (8, 1, "army_day", "建军节", "建軍記念日", "Army Day"),
    (9, 10, "teachers_day", "教师节", "教師の日", "Teachers' Day"),
    (10, 1, "national_day", "国庆节", "国慶節", "National Day"),
    (12, 25, "christmas", "圣诞节", "クリスマス", "Christmas"),
]
# (农历月, 农历日, key, 中文, 日本語, English)
_LUNAR_FESTIVALS = [
    (1, 1, "spring_festival", "春节", "春節", "Spring Festival"),
    (1, 15, "lantern", "元宵节", "元宵節", "Lantern Festival"),
    (2, 2, "longtaitou", "龙抬头", "龍抬头", "Longtaitou Festival"),
    (5, 5, "dragon_boat", "端午节", "端午節", "Dragon Boat Festival"),
    (7, 7, "qixi", "七夕节", "七夕", "Qixi Festival"),
    (7, 15, "zhongyuan", "中元节", "中元節", "Ghost Festival"),
    (8, 15, "mid_autumn", "中秋节", "中秋節", "Mid-Autumn Festival"),
    (9, 9, "chongyang", "重阳节", "重陽節", "Double Ninth Festival"),
    (12, 8, "laba", "腊八节", "臘八節", "Laba Festival"),
    (12, 23, "xiaonian", "小年", "小年", "Little New Year"),
]
_FEST_NAMES = {key: (zh, ja, en)
               for m, d, key, zh, ja, en in _GREG_FESTIVALS + _LUNAR_FESTIVALS}
_FEST_NAMES["new_year_eve"] = ("除夕", "大晦日", "New Year's Eve")
_FEST_NAMES["mothers_day"] = ("母亲节", "母の日", "Mother's Day")
_FEST_NAMES["fathers_day"] = ("父亲节", "父の日", "Father's Day")
_FEST_NAMES["thanksgiving"] = ("感恩节", "感謝祭", "Thanksgiving")
_FEST_NAMES["qingming"] = ("清明节", "清明祭", "Tomb-Sweeping Day")

_lunar_year_cache = {}


def _lunar_festival_map(year):
    """计算某公历年里农历节日对应的公历日期（含上年腊月与除夕落在本年的情况）"""
    if year in _lunar_year_cache:
        return _lunar_year_cache[year]
    m = {}
    # 扫描全年每一天的农历日期
    d = datetime.date(year, 1, 1)
    end = datetime.date(year, 12, 31)
    while d <= end:
        _, lm, ld, is_leap = solar_to_lunar(d.year, d.month, d.day)
        if not is_leap:
            for fmonth, fday, key, *_ in _LUNAR_FESTIVALS:
                if lm == fmonth and ld == fday:
                    m[d] = key
        d += datetime.timedelta(days=1)
    # 除夕：本年春节前一天（春节恒在 1-2 月，故除夕也在本公历年）
    spring = next((d for d, k in m.items() if k == "spring_festival"), None)
    if spring:
        m[spring - datetime.timedelta(days=1)] = "new_year_eve"
    _lunar_year_cache[year] = m
    return m


def _nth_weekday(year, month, weekday, n):
    """第 n 个星期几（weekday: 周一=0）"""
    d = datetime.date(year, month, 1)
    offset = (weekday - d.weekday()) % 7
    return d + datetime.timedelta(days=offset + 7 * (n - 1))


def _moving_festivals(year):
    out = {}
    out[_nth_weekday(year, 5, 6, 2)] = "mothers_day"   # 5 月第 2 个周日
    out[_nth_weekday(year, 6, 6, 3)] = "fathers_day"   # 6 月第 3 个周日
    out[_nth_weekday(year, 11, 3, 4)] = "thanksgiving"  # 11 月第 4 个周四
    return out


# ---------------- 对外 API ----------------
def _name(triple, lang):
    zh, ja, en = triple
    return {"zh": zh, "ja": ja, "en": en}[lang]


def term_on(d, lang="zh"):
    """当天节气名（无则 None）"""
    zh = terms_of_year(d.year).get(d)
    if not zh:
        return None
    triple = TERM_KEYS_ZH[zh]
    return _name(triple, lang)


def festivals_on(d, lang="zh"):
    """当天节日名列表"""
    keys = []
    for m, day, key, *_ in _GREG_FESTIVALS:
        if d.month == m and d.day == day:
            keys.append(key)
    key = _lunar_festival_map(d.year).get(d)
    if key:
        keys.append(key)
    key = _moving_festivals(d.year).get(d)
    if key:
        keys.append(key)
    # 清明节气同时是节日
    zh_term = terms_of_year(d.year).get(d)
    if zh_term == "清明":
        keys.append("qingming")
    return [_name(_FEST_NAMES[k], lang) for k in keys]


def lunar_label(d, lang="zh"):
    """农历日期文字（完整）"""
    _, lm, ld, is_leap = solar_to_lunar(d.year, d.month, d.day)
    if lang == "zh":
        mon = ("闰" if is_leap else "") + _LUNAR_MONTH_ZH[lm - 1]
        return "农历" + mon + _LUNAR_DAY_ZH[ld - 1]
    if lang == "ja":
        mon = ("閏" if is_leap else "") + _LUNAR_MONTH_JA[lm - 1]
        return "旧暦" + mon + _LUNAR_DAY_ZH[ld - 1]
    return "Lunar %d/%d" % (lm, ld)


def cell_label(d, lang="zh"):
    """月历小格子里显示的一行：(文字, 类型 festival/term/lunar)"""
    fests = festivals_on(d, lang)
    if fests:
        return fests[0], "festival"
    term = term_on(d, lang)
    if term:
        return term, "term"
    _, lm, ld, is_leap = solar_to_lunar(d.year, d.month, d.day)
    if lang == "en":
        return (("M%d" % lm) if ld == 1 else str(ld)), "lunar"
    months = _LUNAR_MONTH_JA if lang == "ja" else _LUNAR_MONTH_ZH
    if ld == 1:
        return (("閏" if lang == "ja" and is_leap else "闰" if is_leap else "")
                + months[lm - 1]), "lunar"
    return _LUNAR_DAY_ZH[ld - 1], "lunar"


def panel_lines(d, lang="zh"):
    """当日面板上的标记行：[(文字, 类型)]，节日在前、节气其次、农历日期兜底"""
    lines = [(name, "festival") for name in festivals_on(d, lang)]
    term = term_on(d, lang)
    # 清明节日已在 festivals 里，节气行不重复
    if term and not (lang == "zh" and term == "清明"):
        lines.append((term, "term"))
    lines.append((lunar_label(d, lang), "lunar"))
    return lines
