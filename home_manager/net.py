# -*- coding: utf-8 -*-
"""居家管家 - 联网下载（纯标准库，后台线程 + Tk 主线程回调）

- fetch_json：取 JSON（集市图源列表）
- fetch_wallpapers：取图片列表（进程内短时缓存，切回标签秒开）
- fetch_thumb：缩略图（磁盘缓存 + 后台线程缩放 + 线程池并发）
- download：下载文件到指定目录，带进度回调（原图内存缓存，看过的图秒存）
所有回调都通过 root.after 投递回主线程，UI 可直接刷新。
"""
import hashlib
import io
import json
import os
import random
import shutil
import threading
import time
import urllib.parse
import urllib.request
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

from config import THUMB_CACHE_DIR

UA = "HomeManager/1.1 (Windows; desktop assistant)"

# 免费 SFW 图源：
#  - safebooru.org：自带 15KB 原生缩略图，浏览快（主源）
#  - nekos.best：精选插画/GIF（备用源，缩略图由本地缩放原图生成）
NEKOS_CATEGORIES = ["waifu", "neko", "kitsune", "husbando",
                    "hug", "pat", "cuddle", "wave", "smile", "blush"]
NEKOS_API = "https://nekos.best/api/v2/%s?amount=%d"
SAFEBOORU_API = ("https://safebooru.org/index.php?page=dapi&s=post&q=index"
                 "&json=1&limit=%d&pid=%d&tags=%s")
# 标签之间用空格表示 AND（逗号在 booru 语法里是 OR）；
# 第二项是随机翻页上限，冷门标签池子小，翻太深会空页
SAFEBOORU_TAGS = {
    "waifu":    ("1girl solo looking_at_viewer -anthro", 200),
    "neko":     ("catgirl", 30),
    "kitsune":  ("foxgirl", 20),
    "husbando": ("1boy solo male_focus looking_at_viewer", 100),
    "hug":      ("hug 1girl", 60),
    "pat":      ("headpat", 40),
    "cuddle":   ("cuddle", 3),
    "wave":     ("waving 1girl solo", 100),
    "smile":    ("1girl solo smile", 200),
    "blush":    ("1girl solo blush", 200),
}

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
AUDIO_EXTS = {".mp3", ".wav", ".m4a", ".wma", ".ogg"}

# 缩略图尺寸（卡片约 300px 宽，略放大保证清晰）
THUMB_W, THUMB_H = 320, 200

_LIST_TTL = 1800          # 列表接口内存缓存 30 分钟
_FULL_CACHE_MAX = 8       # 原图内存缓存张数（每张数 MB）
_THUMB_CACHE_MAX = 240    # 磁盘缩略图缓存上限
_THUMB_CACHE_KEEP = 180

_list_cache = OrderedDict()   # category -> (ts, items)
_list_tokens = {}             # category -> 最新请求令牌，丢弃过期响应
_full_cache = OrderedDict()   # url -> 原图字节
_cache_lock = threading.Lock()
_executor = None

try:
    from PIL import Image, ImageOps
except Exception:
    Image = None
    ImageOps = None


def _pool():
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=6, thread_name_prefix="hm-net")
    return _executor


def _ui(root, fn, *args):
    """把回调投递到 Tk 主线程（控件可能已销毁，静默忽略）"""
    def call():
        try:
            fn(*args)
        except Exception:
            pass
    if root is not None:
        try:
            root.after(0, call)
        except Exception:
            pass
    else:
        call()


def _http_open(url, timeout=20, retries=2, data=None):
    """带重试的 HTTP GET（POST 仅在 data 非空时）"""
    last = None
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=data,
                                         headers={"User-Agent": UA})
            return urllib.request.urlopen(req, timeout=timeout)
        except Exception as e:
            last = e
            if i < retries:
                time.sleep(0.8 * (i + 1))
    raise last


def fetch_json(root, url, on_ok, on_err):
    def work():
        try:
            with _http_open(url, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            _ui(root, on_ok, data)
        except Exception as e:
            _ui(root, on_err, str(e))
    threading.Thread(target=work, daemon=True).start()


def fetch_bytes(root, url, on_ok, on_err):
    """下载原始字节（无缓存场景使用）"""
    def work():
        try:
            with _http_open(url, timeout=20) as resp:
                data = resp.read()
            _ui(root, on_ok, data)
        except Exception as e:
            _ui(root, on_err, str(e))
    threading.Thread(target=work, daemon=True).start()


# ---------- 集市图片列表 ----------

def _abs_url(u):
    if not u:
        return ""
    if u.startswith(("http://", "https://")):
        return u
    if u.startswith("//"):
        return "https:" + u
    return "https://safebooru.org/" + u.lstrip("/")


def _fetch_safebooru(category, amount):
    """safebooru 原生缩略图源；返回 items 或抛异常"""
    extra_tags, pid_max = SAFEBOORU_TAGS.get(category, ("1girl solo", 200))
    tags = "rating:safe " + extra_tags
    pid = random.randint(0, pid_max)
    url = SAFEBOORU_API % (max(1, min(20, amount)), pid,
                           urllib.parse.quote(tags))
    with _http_open(url, timeout=15) as resp:
        posts = json.loads(resp.read().decode("utf-8"))
    items = []
    if isinstance(posts, list):
        for p in posts:
            full = _abs_url(p.get("file_url"))
            sample = _abs_url(p.get("sample_url"))
            prev = _abs_url(p.get("preview_url"))
            if not full or not (sample or prev):
                continue
            # 样图通常 70–600KB，缩放成 320px 缩略图既快又清晰；
            # 没有样图时退而用 5–10KB 原生小预览
            if sample:
                items.append({"url": full, "thumb": sample, "title": category,
                              "resize": True, "remember": sample == full})
            else:
                items.append({"url": full, "thumb": prev, "title": category,
                              "resize": False, "remember": False})
    return items


def _fetch_nekos(category, amount):
    """nekos.best 备用源（原图很大，缩略图靠本地缩放）"""
    with _http_open(NEKOS_API % (category, max(1, min(20, amount))),
                    timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    items = []
    for r in data.get("results", []):
        u = r.get("url", "")
        if not u:
            continue
        items.append({"url": u, "thumb": u,
                      "title": r.get("anime_name") or r.get("artist_name") or category,
                      "resize": True, "remember": True})
    return items


def fetch_wallpapers(root, category, amount, on_ok, on_err, force=False):
    """返回 [{url, thumb, title, resize}]；短时间内重复切换分类走内存缓存。

    优先 safebooru（原生小缩略图，秒开），失败再回退 nekos.best。
    """
    def work():
        try:
            cached = _list_cache.get(category)
            if not force and cached and time.time() - cached[0] < _LIST_TTL:
                _ui(root, on_ok, cached[1])
                return
            # 仅真正发起网络请求时占用令牌；纯缓存命中不抢占，
            # 避免“换一批”的新结果被随后一次缓存回切挤掉
            with _cache_lock:
                token = _list_tokens.get(category, 0) + 1
                _list_tokens[category] = token
            try:
                items = _fetch_safebooru(category, amount)
            except Exception:
                items = []
            if len(items) < 6:
                try:
                    items = _fetch_nekos(category, amount)
                except Exception:
                    pass
            if not items:
                raise RuntimeError("no images from any source")
            # 只有最新一次请求可以写缓存/回调，防止快速切换时旧响应污染
            if _list_tokens.get(category) != token:
                return
            _list_cache[category] = (time.time(), items)
            _list_cache.move_to_end(category)
            while len(_list_cache) > 10:
                _list_cache.popitem(last=False)
            _ui(root, on_ok, items)
        except Exception as e:
            if _list_tokens.get(category) == token:
                _ui(root, on_err, str(e))
    threading.Thread(target=work, daemon=True).start()


# ---------- 缩略图（磁盘缓存 + 后台缩放） ----------

def _thumb_path(url):
    h = hashlib.md5(url.encode("utf-8")).hexdigest()
    return os.path.join(THUMB_CACHE_DIR, h + ".jpg")


def _remember_full(url, data):
    if not data or len(data) < 20 * 1024 * 1024:   # 单张 >20MB 不入内存缓存
        with _cache_lock:
            _full_cache[url] = data
            _full_cache.move_to_end(url)
            while len(_full_cache) > _FULL_CACHE_MAX:
                _full_cache.popitem(last=False)


def _make_thumb(data):
    """原图字节 -> 320x200 居中裁剪 JPEG 字节；GIF 取首帧"""
    if Image is None:
        return data
    img = Image.open(io.BytesIO(data))
    img.seek(0)
    img = img.convert("RGB")
    try:
        img = ImageOps.fit(img, (THUMB_W, THUMB_H), method=Image.BICUBIC)
    except Exception:
        img.thumbnail((THUMB_W, THUMB_H), Image.BICUBIC)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=82)
    return out.getvalue()


def _prune_thumbs():
    try:
        files = [os.path.join(THUMB_CACHE_DIR, n)
                 for n in os.listdir(THUMB_CACHE_DIR) if n.endswith(".jpg")]
        if len(files) <= _THUMB_CACHE_MAX:
            return
        files.sort(key=lambda p: os.path.getmtime(p))
        for p in files[:len(files) - _THUMB_CACHE_KEEP]:
            try:
                os.remove(p)
            except OSError:
                pass
    except OSError:
        pass


def fetch_thumb(root, url, on_ok, on_err, resize=False, remember=False):
    """优先读磁盘缩略图；未命中则线程池下载。

    resize=False：url 本身就是小缩略图，直接下载缓存（秒开）；
    resize=True ：url 是大图，下载后在后台线程缩放为 320x200 JPEG；
    remember=True：下载的同时缓存原图字节，供“设为背景/吉祥物”秒存。
    """
    cache_file = _thumb_path(url)
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "rb") as f:
                _ui(root, on_ok, f.read())
            return
        except OSError:
            pass

    def work():
        try:
            # 双重检查（可能其他线程刚写好）
            if os.path.exists(cache_file):
                with open(cache_file, "rb") as f:
                    data = f.read()
            else:
                with _http_open(url, timeout=30, retries=2) as resp:
                    raw = resp.read()
                if resize:
                    if remember:
                        _remember_full(url, raw)
                    data = _make_thumb(raw)
                else:
                    data = raw
                try:
                    os.makedirs(THUMB_CACHE_DIR, exist_ok=True)
                    tmp = cache_file + ".tmp"
                    with open(tmp, "wb") as f:
                        f.write(data)
                    os.replace(tmp, cache_file)
                    _prune_thumbs()
                except OSError:
                    pass
            _ui(root, on_ok, data)
        except Exception as e:
            _ui(root, on_err, str(e))

    _pool().submit(work)


def guess_kind(url, content_type=""):
    path = urllib.parse.urlparse(url).path.lower()
    ext = os.path.splitext(path)[1]
    ct = (content_type or "").lower()
    if ext in IMAGE_EXTS or "image" in ct:
        return "image", ext or ".jpg"
    if ext in AUDIO_EXTS or "audio" in ct:
        return "audio", ext or ".mp3"
    return "other", ext or ".bin"


def unique_path(folder, filename):
    base, ext = os.path.splitext(filename)
    p = os.path.join(folder, filename)
    if not os.path.exists(p):
        return p
    for i in range(1, 999):
        p = os.path.join(folder, "%s_%d%s" % (base, i, ext))
        if not os.path.exists(p):
            return p
    return os.path.join(folder, uuid.uuid4().hex[:8] + ext)


def download(root, url, folder, filename=None, kind_hint="",
             on_progress=None, on_ok=None, on_err=None):
    """下载文件；on_progress(已下载字节, 总字节或0)，on_ok(路径, kind)

    浏览过的原图在内存缓存里时直接落盘，秒存不重复下载。
    """
    def work():
        tmp = None
        try:
            os.makedirs(folder, exist_ok=True)
            ctype = ""
            with _cache_lock:
                cached = _full_cache.get(url)
            if cached is not None:
                ctype = "image/*" if url.lower().split("?")[0].endswith(
                    (".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp")) else ""
                data = cached
            else:
                resp = _http_open(url, timeout=30, retries=1)
                ctype = resp.headers.get("Content-Type", "")
                data = resp.read()
                _remember_full(url, data)
            kind, ext = guess_kind(url, ctype)
            if kind_hint in ("image", "audio"):
                kind = kind_hint
                if kind_hint == "image" and ext not in IMAGE_EXTS:
                    ext = ".jpg"
                if kind_hint == "audio" and ext not in AUDIO_EXTS:
                    ext = ".mp3"
            fname = filename
            if not fname:
                name = os.path.basename(urllib.parse.urlparse(url).path)
                if not name or os.path.splitext(name)[1] == "":
                    name = "hm_%s%s" % (uuid.uuid4().hex[:8], ext)
                fname = urllib.parse.unquote(name)
            elif os.path.splitext(fname)[1] == "":
                fname = fname + ext
            dest = unique_path(folder, os.path.basename(fname))
            tmp = dest + ".part"
            with open(tmp, "wb") as f:
                # 内存缓存场景一次性写入并回报进度；网络场景分块回报
                f.write(data)
                if on_progress:
                    _ui(root, on_progress, len(data), len(data))
            shutil.move(tmp, dest)
            tmp = None
            if on_ok:
                _ui(root, on_ok, dest, kind)
        except Exception as e:
            if tmp:
                try:
                    os.remove(tmp)
                except OSError:
                    pass
            if on_err:
                _ui(root, on_err, str(e))
    threading.Thread(target=work, daemon=True).start()
