# -*- coding: utf-8 -*-
import json
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, r"C:\Users\HP\Desktop\居家管家\home_manager")


def posts(tags, limit=9):
    q = urllib.parse.quote("rating:safe," + tags)
    u = ("https://safebooru.org/index.php?page=dapi&s=post&q=index&json=1"
         "&limit=%d&tags=%s" % (limit, q))
    req = urllib.request.Request(u, headers={"User-Agent": "HomeManager/1.1"})
    d = json.loads(urllib.request.urlopen(req, timeout=20).read())
    return d if isinstance(d, list) else []


def complete(term):
    try:
        raw = urllib.request.urlopen(
            "https://safebooru.org/autocomplete.php?q=%s"
            % urllib.parse.quote(term), timeout=15).read().decode("utf-8", "ignore")
        return raw.replace("\n", " ")[:300]
    except Exception as e:
        return "ERR %s" % str(e)[:60]


for t in ["neko", "catgirl", "foxgirl", "kitsune", "headpat", "cuddle",
          "waving"]:
    print("AUTO", t, "=>", complete(t))

cands = ["1girl,solo,cat_ears", "1girl,solo,nekomimi", "cat_girl,solo",
         "1girl,solo,fox_ears", "1girl,solo,kitsune", "headpat,1girl",
         "cuddling,1girl", "hug,1girl", "waving,1girl",
         "1girl,solo,smile", "1girl,solo,blush", "1boy,solo,male_focus"]
for t in cands:
    ps = posts(t, 5)
    print("\nTAG", t, "n=", len(ps))
    for p in ps[:3]:
        tags = (p.get("tags") or "").split()
        hit = [x for x in tags if any(k in x for k in
              ("cat", "fox", "neko", "kitsune", "pat", "cuddl", "hug",
               "wav", "smile", "blush", "boy", "male"))]
        print("   hits:", hit[:8])
