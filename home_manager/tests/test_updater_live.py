# -*- coding: utf-8 -*-
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import updater

result = {}
updater.check_latest(
    None,
    lambda version, notes, page, zip_url: result.update(
        v=version, page=page, zip=zip_url),
    lambda e: result.update(err=e))
for _ in range(100):
    if result:
        break
    time.sleep(0.1)

if "err" in result:
    print("FAIL", result["err"])
    sys.exit(1)
v = result["v"]
print("latest version:", v)
print("page:", result["page"])
print("zip url:", (result["zip"] or "")[:110])
print("newer than 1.1.0:", updater.is_newer(v, "1.1.0"))
print("newer than 1.1.1:", updater.is_newer(v, "1.1.1"))
assert v == "1.1.2"
assert updater.is_newer(v, "1.1.0") is True
assert updater.is_newer(v, "1.1.1") is True
assert updater.is_newer(v, "1.1.2") is False
assert "HomeManager-v1.1.2-portable.zip" in (result["zip"] or "")
print("OK")
