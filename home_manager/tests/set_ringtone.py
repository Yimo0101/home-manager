# -*- coding: utf-8 -*-
"""把 assets/audio/起床铃声.mp3 设为 07:00 起床闹钟铃声，并验证 MCI 可播放"""
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from media import SoundPlayer  # noqa: E402
from storage import DataStore  # noqa: E402

ring = os.path.join(os.path.dirname(HERE), "assets", "audio", "起床铃声.mp3")
assert os.path.exists(ring), "铃声文件不存在: %s" % ring

store = DataStore()
store.update_settings(language="zh")
target = None
for a in store.alarms:
    if a.get("time") == "07:00":
        target = a
        break
assert target is not None, "未找到 07:00 的起床闹钟"
target["ringtone"] = ring
store.upsert_alarm(target)
print("已设置铃声:", target["name"], "->", ring)

# 验证 MCI 能打开并播放 2.5 秒
p = SoundPlayer()
ok = p.play(ring, loop=False)
print("MCI open/play:", ok)
time.sleep(2.5)
p.stop()
print("验证完成")
