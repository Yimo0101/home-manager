# -*- coding: utf-8 -*-
"""新功能逻辑冒烟：白噪音生成、纪念日（公历/农历）、日语词、专注统计、版本比较"""
import datetime
import os
import sys
import wave

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ambient
import anniversaries as ann
import holidays
import nihongo
from storage import DataStore
import updater

fail = []


def check(name, cond):
    print(("PASS " if cond else "FAIL ") + name)
    if not cond:
        fail.append(name)


# 1. 白噪音
paths = ambient.ensure_all()
for key, p in paths.items():
    ok = os.path.exists(p) and os.path.getsize(p) > 100000
    with wave.open(p, "rb") as wf:
        frames = wf.getnframes()
        dur = frames / wf.getframerate()
    check("ambient %s exists & ~30s (%.1fs)" % (key, dur), ok and 25 < dur < 35)

# 2. 农历换算：2026 重阳节（九月初九）应为 2026-10-18
chongyang = {"title": "重阳节", "date": "2026-09-09", "calendar": "lunar",
             "yearly": True}
occ, days = ann.next_occurrence(chongyang, datetime.date(2026, 10, 5))
check("lunar chongyang 2026 -> 2026-10-18, days=13",
      (occ == datetime.date(2026, 10, 18) and days == 13))
# 2025 春节 正月初一 = 2025-01-29
spring = {"title": "春节", "date": "2025-01-01", "calendar": "lunar",
          "yearly": True}
occ2, days2 = ann.next_occurrence(spring, datetime.date(2025, 1, 1))
check("lunar spring festival 2025 -> 2025-01-29",
      occ2 == datetime.date(2025, 1, 29) and days2 == 28)
# 2026 春节 = 2026-02-17
occ3, _ = ann.next_occurrence(spring, datetime.date(2026, 1, 1))
check("lunar spring festival 2026 -> 2026-02-17",
      occ3 == datetime.date(2026, 2, 17))
# 公历每年重复：10-01，从 2026-10-05 看应为 2027-10-01
nat = {"title": "国庆", "date": "2026-10-01", "calendar": "solar", "yearly": True}
occ4, days4 = ann.next_occurrence(nat, datetime.date(2026, 10, 5))
check("solar yearly wraps to next year", occ4 == datetime.date(2027, 10, 1))
# 当天 days=0
occ5, days5 = ann.next_occurrence(chongyang, datetime.date(2026, 10, 18))
check("anniversary today days=0", days5 == 0)

# 3. 日语单词稳定轮换
w1 = nihongo.word_of_day(datetime.date(2026, 10, 5))
w2 = nihongo.word_of_day(datetime.date(2026, 10, 5))
w3 = nihongo.word_of_day(datetime.date(2026, 10, 6))
check("word_of_day stable & changes", w1["word"] == w2["word"] and w1["word"] != w3["word"])
check("word bank >= 70", len(nihongo.WORDS) >= 70)

# 4. 存储：纪念日 CRUD + 专注统计
import tempfile
tmp = os.path.join(tempfile.gettempdir(), "hm_test_data.json")
if os.path.exists(tmp):
    os.remove(tmp)
store = DataStore(tmp)
item = store.upsert_anniversary({"title": "测试生日", "date": "2000-01-01",
                                 "calendar": "solar", "yearly": True})
check("anniversary upsert/get", len(store.anniversaries) == 1)
store.delete_anniversary(item["id"])
check("anniversary delete", len(store.anniversaries) == 0)
store.add_focus_minutes("2026-10-05", 25, 1)
store.add_focus_minutes("2026-10-05", 25, 1)
m, r = store.focus_stat("2026-10-05")
check("focus stat 50min 2 rounds", m == 50 and r == 2)
# 旧版 int 数据兼容
store.data["focus"]["2026-10-06"] = 40
store.save()
store2 = DataStore(tmp)
m2, r2 = store2.focus_stat("2026-10-06")
check("legacy int focus compat", m2 == 40 and r2 == 0)
os.remove(tmp)

# 5. 版本比较
check("version compare 1.2.0 > 1.1.0", updater.is_newer("1.2.0", "1.1.0"))
check("version compare same == false", not updater.is_newer("1.1.0", "1.1.0"))
check("version compare v-prefix", updater.is_newer("v1.1.1", "1.1.0"))

print()
if fail:
    print("FAILED:", fail)
    sys.exit(1)
print("ALL NEW-FEATURE TESTS PASSED")
