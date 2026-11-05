"""Vector icon set rasterised to anti-aliased PNG at runtime (no PIL needed)."""
import base64
import math
import struct
import tkinter as tk
import zlib

from .geometry import seg_dist
from .scaling import sc
from .theme import T
from .utils import hex_rgb


def _png(w, h, px):
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw += px[y * w * 4:(y + 1) * w * 4]

    def ch(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)

    return (b"\x89PNG\r\n\x1a\n" + ch(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
            + ch(b"IDAT", zlib.compress(bytes(raw), 6)) + ch(b"IEND", b""))


def L(p, w=1.8, c=0):
    return ("L", p, w, c)


def S(p, w=1.8, c=0):
    return ("S", p, w, c)


def Pf(p, c=0):
    return ("P", p, 0, c)


def Cf(x, y, r, c=0):
    return ("CF", (x, y, r), 0, c)


def Cs(x, y, r, w=1.8, c=0):
    return ("CS", (x, y, r), w, c)


def arc(cx, cy, r, a0, a1, n=16):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def xf(prims, fn):
    out = []
    for k, d, w, c in prims:
        if k in ("CF", "CS"):
            x, y = fn(d[0], d[1])
            d = (x, y, d[2])
        else:
            d = [fn(*p) for p in d]
        out.append((k, d, w, c))
    return out


MX = lambda x, y: (24 - x, y)  # noqa: E731
MY = lambda x, y: (x, 24 - y)  # noqa: E731
SW = lambda x, y: (y, x)  # noqa: E731

_undo = [L([(10, 6), (5, 11), (10, 16)], 1.9), L([(5.5, 11), (14, 11), (19, 13.5), (19, 19)], 1.9)]
_alL = [L([(5, 3), (5, 21)], 1.8), Pf([(8, 6), (19, 6), (19, 10), (8, 10)]), Pf([(8, 14), (14, 14), (14, 18), (8, 18)])]
_alC = [L([(12, 3), (12, 21)], 1.6), Pf([(5, 6), (19, 6), (19, 10), (5, 10)]), Pf([(8, 14), (16, 14), (16, 18), (8, 18)])]
_dist = [L([(4, 4), (4, 20)], 1.8), L([(12, 7), (12, 17)], 1.8, 1), L([(20, 4), (20, 20)], 1.8)]
_eye = [L([(2, 12), (7, 7), (12, 6), (17, 7), (22, 12), (17, 17), (12, 18), (7, 17), (2, 12)], 1.7), Cf(12, 12, 3, 1)]

ICONS = {
    "new": [S([(6, 3), (14, 3), (19, 8), (19, 21), (6, 21)]), L([(14, 3), (14, 8), (19, 8)], 1.5),
            L([(12.5, 12.5), (12.5, 18)], 1.8, 1), L([(9.7, 15.2), (15.3, 15.2)], 1.8, 1)],
    "open": [S([(3, 6), (9, 6), (11.5, 8.5), (21, 8.5), (21, 19), (3, 19)]), L([(3, 12), (21, 12)], 1.4)],
    "save": [S([(4, 4), (17.5, 4), (20, 6.5), (20, 20), (4, 20)]), L([(8, 4), (8, 9), (16, 9), (16, 4)], 1.5),
             L([(8, 20), (8, 14), (16, 14), (16, 20)], 1.5)],
    "undo": _undo, "redo": xf(_undo, MX),
    "cut": [L([(8, 3.5), (16.5, 15.5)]), L([(16, 3.5), (7.5, 15.5)]), Cs(7, 18.2, 2.7, 1.7), Cs(17, 18.2, 2.7, 1.7)],
    "copy": [S([(9, 8), (20, 8), (20, 21), (9, 21)]), L([(5.5, 16), (5.5, 3.5), (15.5, 3.5)], 1.7)],
    "paste": [S([(5, 6), (19, 6), (19, 21), (5, 21)]), Pf([(9, 3), (15, 3), (15, 8), (9, 8)], 1)],
    "select": [Pf([(6, 3), (6, 19.5), (10.2, 15.6), (13, 21.5), (15.8, 20.2), (13.2, 14.5), (18.8, 14.5)])],
    "pan": [L([(12, 3), (12, 21)], 1.6), L([(3, 12), (21, 12)], 1.6), L([(9, 6), (12, 3), (15, 6)], 1.6),
            L([(9, 18), (12, 21), (15, 18)], 1.6), L([(6, 9), (3, 12), (6, 15)], 1.6),
            L([(18, 9), (21, 12), (18, 15)], 1.6)],
    "waypoint": [L([(7, 21), (7, 4)], 2), Pf([(7, 4.5), (19, 8.5), (7, 13)], 1)],
    "auv": [Pf([(12, 3), (18.5, 20), (12, 16), (5.5, 20)], 1)],
    "measure": [S([(3, 16), (16, 3), (21, 8), (8, 21)], 1.7), L([(7, 14), (9, 16)], 1.3, 1),
                L([(10, 11), (12, 13)], 1.3, 1), L([(13, 8), (15, 10)], 1.3, 1)],
    "grid": [S([(4, 4), (20, 4), (20, 20), (4, 20)], 1.6), L([(4, 9.3), (20, 9.3)], 1.3), L([(4, 14.7), (20, 14.7)], 1.3),
             L([(9.3, 4), (9.3, 20)], 1.3), L([(14.7, 4), (14.7, 20)], 1.3)],
    "snap": [L([(6, 3.5), (6, 12.5), (8, 17), (12, 19), (16, 17), (18, 12.5), (18, 3.5)], 3.4),
             L([(6, 3.5), (6, 7)], 3.4, 1), L([(18, 3.5), (18, 7)], 3.4, 1)],
    "label": [L([(5, 5.5), (19, 5.5)], 2.2), L([(12, 5.5), (12, 19.5)], 2.2)],
    "fit": [L([(4, 9), (4, 4), (9, 4)]), L([(15, 4), (20, 4), (20, 9)]), L([(20, 15), (20, 20), (15, 20)]),
            L([(9, 20), (4, 20), (4, 15)]), Cf(12, 12, 2.2, 1)],
    "zoomin": [Cs(10.5, 10.5, 6.5), L([(15.5, 15.5), (21, 21)], 2.4), L([(7.5, 10.5), (13.5, 10.5)], 1.6, 1),
               L([(10.5, 7.5), (10.5, 13.5)], 1.6, 1)],
    "zoomout": [Cs(10.5, 10.5, 6.5), L([(15.5, 15.5), (21, 21)], 2.4), L([(7.5, 10.5), (13.5, 10.5)], 1.6, 1)],
    "plan": [L([(6, 17), (6, 11), (18, 13), (18, 7)], 1.8), Cf(6, 18.5, 2.6, 1), Cf(18, 5.5, 2.6, 1)],
    "play": [Pf([(7, 4), (20, 12), (7, 20)], 1)],
    "pause": [Pf([(6.5, 4.5), (10.5, 4.5), (10.5, 19.5), (6.5, 19.5)], 1), Pf([(13.5, 4.5), (17.5, 4.5), (17.5, 19.5), (13.5, 19.5)], 1)],
    "stop": [Pf([(6, 6), (18, 6), (18, 18), (6, 18)], 2)],
    "check": [L([(4.5, 12.5), (10, 18), (19.5, 6.5)], 2.4, 3)],
    "warn": [S([(12, 4), (21.5, 20), (2.5, 20)], 1.8, 4), L([(12, 10), (12, 14.5)], 2, 4), Cf(12, 17.3, 1.1, 4)],
    "error": [Cs(12, 12, 9, 1.8, 2), L([(8.5, 8.5), (15.5, 15.5)], 1.9, 2), L([(15.5, 8.5), (8.5, 15.5)], 1.9, 2)],
    "info": [Cs(12, 12, 9, 1.8, 1), L([(12, 11), (12, 17)], 2, 1), Cf(12, 7.5, 1.2, 1)],
    "csv": [S([(4, 5), (20, 5), (20, 19), (4, 19)], 1.6), L([(4, 10), (20, 10)], 1.3), L([(4, 14.5), (20, 14.5)], 1.3),
            L([(10, 5), (10, 19)], 1.3)],
    "svg": [S([(3, 5), (21, 5), (21, 19), (3, 19)], 1.6), Cf(8, 10, 2),
            Pf([(4.5, 18), (10, 12.5), (14, 16), (17, 13), (19.5, 18)], 1)],
    "json": [L([(9, 4), (7, 4), (6, 6), (6, 10), (4, 12), (6, 14), (6, 18), (7, 20), (9, 20)], 1.6),
             L([(15, 4), (17, 4), (18, 6), (18, 10), (20, 12), (18, 14), (18, 18), (17, 20), (15, 20)], 1.6)],
    "delete": [L([(5, 7), (19, 7)]), S([(7, 7), (8, 20), (16, 20), (17, 7)], 1.7), L([(10, 4), (14, 4)]),
               L([(10, 11), (10, 17)], 1.4), L([(14, 11), (14, 17)], 1.4)],
    "rotate": [L(arc(12, 12, 7, -40, 250, 18), 1.9), L([(14.5, 2.5), (18.5, 6), (13.5, 8.5)], 1.9, 1)],
    "lock": [S([(6, 11), (18, 11), (18, 21), (6, 21)], 1.8), L([(8.5, 11), (8.5, 8), (10, 5.5), (14, 5.5), (15.5, 8), (15.5, 11)], 1.8),
             Cf(12, 16, 1.4, 1)],
    "eye": _eye,
    "al_l": _alL, "al_r": xf(_alL, MX), "al_t": xf(_alL, SW), "al_b": xf(xf(_alL, SW), MY),
    "al_c": _alC, "al_m": xf(_alC, SW),
    "dist_h": _dist, "dist_v": xf(_dist, SW),
    "help": [Cs(12, 12, 9, 1.8), L([(9, 9.5), (9.5, 7.5), (11, 6.5), (13.5, 6.8), (15, 8.5), (14.5, 10.5), (12, 12.3), (12, 14)], 1.7),
             Cf(12, 17.4, 1.2, 1)],
    "theme": [Cs(12, 12, 8, 1.8), Pf(arc(12, 12, 8, -90, 90, 14) + [(12, 12)], 1)],
    "home": [L([(3.5, 11.5), (12, 4), (20.5, 11.5)], 2), S([(6, 10), (6, 20), (18, 20), (18, 10)], 1.7),
             L([(10, 20), (10, 14), (14, 14), (14, 20)], 1.5, 1)],
    "plus": [L([(12, 5), (12, 19)], 2.2), L([(5, 12), (19, 12)], 2.2)],
    "up": [L([(6, 15), (12, 8), (18, 15)], 2.2)],
    "down": [L([(6, 9), (12, 16), (18, 9)], 2.2)],
    "insert": [L([(4, 18), (20, 6)], 1.8), Cf(12, 12, 3, 1)],
    "fullscreen": [L([(4, 9), (4, 4), (9, 4)]), L([(15, 4), (20, 4), (20, 9)]), L([(20, 15), (20, 20), (15, 20)]),
                   L([(9, 20), (4, 20), (4, 15)])],
}
APP_ICON = [
    Pf([(0, 0), (24, 0), (24, 24), (0, 24)], "#17324e"),
    L([(0, 8), (24, 8)], 0.5, "#34648f"), L([(0, 16), (24, 16)], 0.5, "#34648f"),
    L([(8, 0), (8, 24)], 0.5, "#34648f"), L([(16, 0), (16, 24)], 0.5, "#34648f"),
    L([(5, 19), (5, 12), (14, 12), (14, 6), (19, 5)], 1.5, "#c792ea"), Cf(19, 5, 2.2, "#c792ea"),
    Pf([(5, 21.5), (8, 15.5), (5, 16.5), (2, 15.5)], "#ffd400"),
    S([(0.4, 0.4), (23.6, 0.4), (23.6, 23.6), (0.4, 23.6)], 0.9, "#8fb8e0"),
]


def raster_icon(prims, size, pal, grid=24.0, ss=3):
    """Anti-aliased rasterisation of vector icon primitives -> PNG bytes."""
    k = grid / size
    buf = [[0.0, 0.0, 0.0, 0.0] for _ in range(size * size)]

    def colour(c):
        h = c if isinstance(c, str) else pal[c]
        return hex_rgb(h)

    for kind, d, w, c in prims:
        r, g, b = colour(c)
        if kind in ("CF", "CS"):
            cx, cy, rad = d
            pad = rad + w / 2
            bb = (cx - pad, cy - pad, cx + pad, cy + pad)
            if kind == "CF":
                def hit(x, y, cx=cx, cy=cy, rad=rad):
                    return (x - cx) ** 2 + (y - cy) ** 2 <= rad * rad
            else:
                def hit(x, y, cx=cx, cy=cy, rad=rad, w=w):
                    return abs(math.hypot(x - cx, y - cy) - rad) <= w / 2
        else:
            pts = d
            xs, ys = [p[0] for p in pts], [p[1] for p in pts]
            pad = w / 2 + 0.01
            bb = (min(xs) - pad, min(ys) - pad, max(xs) + pad, max(ys) + pad)
            if kind == "P":
                def hit(x, y, pts=pts):
                    inside, j = False, len(pts) - 1
                    for i in range(len(pts)):
                        xi, yi = pts[i]
                        xj, yj = pts[j]
                        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
                            inside = not inside
                        j = i
                    return inside
            else:
                segs = list(zip(pts[:-1], pts[1:]))
                if kind == "S":
                    segs.append((pts[-1], pts[0]))

                def hit(x, y, segs=segs, w=w):
                    for (ax, ay), (bx, by) in segs:
                        if seg_dist(x, y, ax, ay, bx, by) <= w / 2:
                            return True
                    return False
        i0, i1 = max(int(bb[0] / k), 0), min(int(bb[2] / k) + 1, size - 1)
        j0, j1 = max(int(bb[1] / k), 0), min(int(bb[3] / k) + 1, size - 1)
        for j in range(j0, j1 + 1):
            for i in range(i0, i1 + 1):
                n = 0
                for sb in range(ss):
                    for sa in range(ss):
                        if hit((i + (sa + .5) / ss) * k, (j + (sb + .5) / ss) * k):
                            n += 1
                if not n:
                    continue
                cov = n / (ss * ss)
                px = buf[j * size + i]
                oa = cov + px[3] * (1 - cov)
                px[0] = (r * cov + px[0] * px[3] * (1 - cov)) / oa
                px[1] = (g * cov + px[1] * px[3] * (1 - cov)) / oa
                px[2] = (b * cov + px[2] * px[3] * (1 - cov)) / oa
                px[3] = oa
    out = bytearray()
    for r, g, b, a in buf:
        out += bytes((int(r), int(g), int(b), int(a * 255)))
    return _png(size, size, out)


_ICON_CACHE = {}


def ico(name, size=None, fg=None, accent=None):
    """Cached PhotoImage icon. Must be called after the Tk root exists."""
    size = size or sc(20)
    fg = fg or T["text"]
    accent = accent or T["accent"]
    key = (name, size, fg, accent)
    img = _ICON_CACHE.get(key)
    if img is None:
        prims = APP_ICON if name == "app" else ICONS[name]
        png = raster_icon(prims, size, (fg, accent, T["danger"], T["ok"], T["warn"]))
        img = tk.PhotoImage(data=base64.b64encode(png).decode("ascii"))
        _ICON_CACHE[key] = img
    return img


def ico_sel(name, size=None):
    return ico(name, size, fg="#ffffff", accent="#ffffff")


def ico_dis(name, size=None):
    return ico(name, size, fg=T["muted"], accent=T["muted"])


def clear_icons():
    _ICON_CACHE.clear()


def states(name, selected=False, disabled=False):
    """ttk ``image=`` option value with state variants (selected / disabled)."""
    parts = [str(ico(name))]
    if selected:
        parts += ["selected", str(ico_sel(name))]
    if disabled:
        parts += ["disabled", str(ico_dis(name))]
    return tuple(parts)
