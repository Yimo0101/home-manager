# -*- coding: utf-8 -*-
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import net

items = []
net.fetch_wallpapers(None, "neko", 9, lambda it: items.extend(it),
                     lambda e: print("list err", e), force=True)
for _ in range(100):
    if items:
        break
    time.sleep(0.1)

it = items[0]
print("full url:", it["url"][:110])
res = {}
t0 = time.time()
net.download(None, it["url"], tempfile.mkdtemp(), kind_hint="image",
             on_ok=lambda p, k: res.update(path=p, kind=k,
                                           t=time.time() - t0),
             on_err=lambda e: res.update(err=e))
for _ in range(200):
    if res:
        break
    time.sleep(0.1)

if "err" in res:
    print("DOWNLOAD FAIL:", res["err"])
    sys.exit(1)
print("download result:", res["kind"],
      round(os.path.getsize(res["path"]) / 1024), "KB",
      "%dms" % (res["t"] * 1000))
print("OK")
