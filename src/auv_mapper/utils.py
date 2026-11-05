"""Small pure helpers (colours, formatting, time)."""
import re
import time


def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(c1, c2, t):
    a, b = hex_rgb(c1), hex_rgb(c2)
    return "#%02x%02x%02x" % tuple(int(a[i] * t + b[i] * (1 - t)) for i in range(3))


def fmt(v):
    if isinstance(v, float):
        s = f"{v:.3f}".rstrip("0").rstrip(".")
        return "0" if s in ("", "-0") else s
    return str(v)


def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def slug(name):
    return re.sub(r"[^\w\-]+", "_", name, flags=re.UNICODE).strip("_") or "proyek"


def fmt_time(sec):
    sec = int(round(sec))
    return f"{sec // 60}:{sec % 60:02d}"
