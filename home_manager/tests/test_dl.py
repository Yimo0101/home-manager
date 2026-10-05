# -*- coding: utf-8 -*-
import sys, time, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import net
from config import WALLPAPER_DIR
out = {}
net.fetch_wallpapers(None, "neko", 1,
                     on_ok=lambda items: out.setdefault("items", items),
                     on_err=lambda e: out.setdefault("err", e))
for _ in range(30):
    if out:
        break
    time.sleep(0.5)
print("list:", list(out.keys()))
url = out["items"][0]["url"]
res = {}
net.download(None, url, WALLPAPER_DIR, kind_hint="image",
             on_ok=lambda p, k: res.setdefault("ok", (p, k)),
             on_err=lambda e: res.setdefault("err", e))
for _ in range(60):
    if res:
        break
    time.sleep(0.5)
print("dl:", res)
if "ok" in res:
    p, k = res["ok"]
    print("size", os.path.getsize(p), "kind", k)
    os.remove(p)
    print("cleaned")
