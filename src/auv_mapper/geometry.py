"""2-D geometry helpers.

Conventions: origin at the bottom-left of the pool, +x right, +y up.
Bearing 0 deg = +y (map up), clockwise (90 deg = +x).
"""
import math


def vec(b):
    r = math.radians(b)
    return math.sin(r), math.cos(r)


def bearing(dx, dy):
    return math.degrees(math.atan2(dx, dy)) % 360.0


def wrap180(a):
    return (a + 180.0) % 360.0 - 180.0


def lw(cx, cy, heading, lx, ly):
    """Local coordinates (lx right, ly forward) -> world."""
    fx, fy = vec(heading)
    return cx + fy * lx + fx * ly, cy - fx * lx + fy * ly


def seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    n = dx * dx + dy * dy
    t = 0.0 if n == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / n))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def auv_poly(x, y, h, k=1.0):
    pts = [(0.0, 0.8 * k), (-0.35 * k, -0.5 * k), (0.35 * k, -0.5 * k)]
    return [lw(x, y, h, a, b) for a, b in pts]


def fit_view(W, H, cw, ch, ml=52, mr=48, mt=40, mb=46):
    """Return (scale, origin_x, origin_y) fitting a W x H pool into a cw x ch canvas."""
    aw, ah = max(cw - ml - mr, 40), max(ch - mt - mb, 40)
    s = max(min(aw / W, ah / H), 1.0)
    ox = ml + (aw - W * s) / 2
    oy = ch - mb - (ah - H * s) / 2
    return s, ox, oy
