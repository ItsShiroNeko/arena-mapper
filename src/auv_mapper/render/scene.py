"""Scene renderer shared by the editor, the home-screen preview and exports."""
import math

from ..geometry import auv_poly, lw, vec
from ..kinds import KINDS, SHAPE_Z
from ..scaling import ui_scale
from ..utils import mix


def arrow_head(sink, p0, p1, color, size=8):
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    n = math.hypot(dx, dy) or 1.0
    ux, uy = dx / n, dy / n
    bx, by = p1[0] - ux * size, p1[1] - uy * size
    sink.polygon([p1, (bx - uy * size * 0.5, by + ux * size * 0.5),
                  (bx + uy * size * 0.5, by - ux * size * 0.5)], fill=color, outline=color, width=1)


def draw_obj(sink, o, v, th, sel=False, labels=True, ghost=False):
    k = KINDS[o.kind]
    shape = k["shape"]
    s, ox, oy = v

    def P(x, y):
        return ox + x * s, oy - y * s

    color = o.color or k["color"]
    edge = th["sel"] if (sel or ghost) else th["obj_edge"]
    ew = 3 if sel else (2 if ghost else 1)
    dash = (4, 3) if ghost else None
    cx, cy = P(o.x, o.y)
    ly, anchor = cy, "n"

    if shape == "circle":
        r = max(3.0, o.size / 2 * s)
        sink.oval(cx, cy, r, fill="" if ghost else color, outline=edge, width=ew, dash=dash)
        ly = cy + r + 3
    elif shape == "rect":
        w, h = o.size, o.h
        pts = [P(*lw(o.x, o.y, o.heading, a, b)) for a, b in
               ((-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2))]
        fill = "" if ghost else mix(color, th["pool"], k.get("alpha", 0.6))
        sink.polygon(pts, fill=fill, outline=edge if (sel or ghost) else color, width=ew if sel else 2, dash=dash)
        tx, ty = P(*lw(o.x, o.y, o.heading, 0, h / 2))
        ly, cx, anchor = ty - 3, tx, "s"
    elif shape in ("gate", "bar"):
        d = vec(o.heading)
        r = (d[1], -d[0])
        half = o.size / 2
        a = P(o.x - r[0] * half, o.y - r[1] * half)
        b = P(o.x + r[0] * half, o.y + r[1] * half)
        bw = max(4.0, 0.14 * s)
        if sel:
            sink.line([a, b], fill=th["sel"], width=bw + 5)
        body = th["sel"] if ghost else (th["gate_body"] if shape == "gate" else color)
        sink.line([a, b], fill=body, width=bw, dash=dash)
        if shape == "gate" and not ghost:
            kk = 0.18
            ra = (a[0] + (b[0] - a[0]) * kk, a[1] + (b[1] - a[1]) * kk)
            rb = (b[0] - (b[0] - a[0]) * kk, b[1] - (b[1] - a[1]) * kk)
            sink.line([a, ra], fill="#ff3030", width=bw + 1)
            sink.line([b, rb], fill="#30e060", width=bw + 1)
        tip = P(o.x + d[0] * 1.0, o.y + d[1] * 1.0)
        sink.line([(cx, cy), tip], fill=th["label"], width=1)
        arrow_head(sink, (cx, cy), tip, th["label"], 6)
        ly = cy + max(bw, 8) + 4
    elif shape == "text":
        sink.text(cx, cy, o.label, size=11, fill=th["sel"] if sel else color, bold=True)
        return
    if labels and not ghost:
        sink.text(cx, ly, o.label, size=8, fill=th["label"], anchor=anchor)


def nice_len(s, maxpx=140):
    for v in (100, 50, 20, 10, 5, 2, 1, 0.5, 0.2, 0.1):
        if v * s <= maxpx:
            return v
    return 0.1


def draw_hud(sink, cw, ch, s, th):
    """Scale bar (bottom-right) and north arrow (top-right)."""
    n = nice_len(s)
    x1, y = cw - 18, ch - 12
    x0 = x1 - n * s
    sink.line([(x0, y), (x1, y)], fill=th["label"], width=2)
    sink.line([(x0, y - 4), (x0, y + 4)], fill=th["label"], width=2)
    sink.line([(x1, y - 4), (x1, y + 4)], fill=th["label"], width=2)
    sink.text((x0 + x1) / 2, y - 6, f"{n:g} m", size=8, fill=th["label"], anchor="s")
    cx, cy = cw - 26, 44
    sink.line([(cx, cy + 14), (cx, cy - 6)], fill=th["label"], width=2)
    arrow_head(sink, (cx, cy + 2), (cx, cy - 12), th["label"], 9)
    sink.text(cx, cy - 15, "N", size=9, fill=th["label"], anchor="s", bold=True)


def draw_scene(sink, proj, v, th, *, grid=True, labels=True, axis=True, selected=(),
               show_path=True, preview=False):
    s, ox, oy = v

    def P(x, y):
        return ox + x * s, oy - y * s

    W, H = proj.W, proj.H
    sink.polygon([P(0, 0), P(W, 0), P(W, H), P(0, H)], fill=th["pool"], outline="")
    if proj.qual > 0:
        sink.polygon([P(0, 0), P(proj.qual, 0), P(proj.qual, H), P(0, H)], fill=th["qual"], outline="")
    if grid:
        gm, gM = max(proj.grid_minor, 0.05), max(proj.grid_major, 0.05)
        if gm * s >= 7:
            for i in range(int(W / gm + 1e-9) + 1):
                sink.line([P(i * gm, 0), P(i * gm, H)], fill=th["grid_minor"], width=1)
            for i in range(int(H / gm + 1e-9) + 1):
                sink.line([P(0, i * gm), P(W, i * gm)], fill=th["grid_minor"], width=1)
        if gM * s >= 18:
            for i in range(int(W / gM + 1e-9) + 1):
                sink.line([P(i * gM, 0), P(i * gM, H)], fill=th["grid_major"], width=1)
            for i in range(int(H / gM + 1e-9) + 1):
                sink.line([P(0, i * gM), P(W, i * gM)], fill=th["grid_major"], width=1)
    sink.polygon([P(0, 0), P(W, 0), P(W, H), P(0, H)], fill="", outline=th["border_pool"], width=2)
    if proj.qual > 0:
        sink.line([P(proj.qual, 0), P(proj.qual, H)], fill=th["border_pool"], width=2)
    if axis and not preview:
        gM = max(proj.grid_major, 0.05)
        for i in range(int(W / gM + 1e-9) + 1):
            sink.text(P(i * gM, 0)[0], P(0, 0)[1] + 6, f"{i * gM:g}", size=8, fill=th["label"], anchor="n")
        for i in range(int(H / gM + 1e-9) + 1):
            sink.text(P(0, 0)[0] - 6, P(0, i * gM)[1], f"{i * gM:g}", size=8, fill=th["label"], anchor="e")
        sink.text((P(0, 0)[0] + P(W, 0)[0]) / 2, P(0, H)[1] - 8,
                  f"{W:g} m x {H:g} m   |   kedalaman {proj.D:g} m", size=9, fill=th["label"], anchor="s", bold=True)
        if proj.qual > 0:
            sink.text(P(0.3, H - 0.3)[0], P(0.3, H - 0.3)[1], "Area Kualifikasi", size=9,
                      fill=th["label"], anchor="nw")
    for o in sorted(proj.objects, key=lambda o: SHAPE_Z[KINDS[o.kind]["shape"]]):
        if o.hidden:
            continue
        draw_obj(sink, o, v, th, sel=("obj", o.id) in selected, labels=labels and not preview)
    if show_path and proj.waypoints:
        pts = [P(proj.auv.x, proj.auv.y)] + [P(w.x, w.y) for w in proj.waypoints]
        sink.line(pts, fill=th["path"], width=2)
        for a, b in zip(pts[:-1], pts[1:]):
            n = math.hypot(b[0] - a[0], b[1] - a[1])
            if n > 40:
                ux, uy = (b[0] - a[0]) / n, (b[1] - a[1]) / n
                m = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
                arrow_head(sink, (m[0] - ux * 5, m[1] - uy * 5), (m[0] + ux * 6, m[1] + uy * 6), th["path"], 9)
        rr = 4 if preview else 9 * ui_scale()
        for i, w in enumerate(proj.waypoints):
            x, y = P(w.x, w.y)
            is_sel = ("wp", i) in selected
            sink.oval(x, y, rr, fill=th["sel"] if is_sel else th["wp_fill"],
                      outline=th["sel"] if is_sel else th["path"], width=2)
            if not preview:
                sink.text(x, y, str(i + 1), size=8, fill="#000" if is_sel else th["wp_text"], bold=True)
                if labels and w.action != "GOTO":
                    sink.text(x + rr + 2, y - rr, w.action, size=7, fill=th["path"], anchor="sw")
    a = proj.auv
    is_sel = ("auv",) in selected
    sink.polygon([P(*p) for p in auv_poly(a.x, a.y, a.heading)], fill=th["auv"],
                 outline=th["sel"] if is_sel else th["obj_edge"], width=3 if is_sel else 1)
    if labels and not preview:
        sink.text(*P(a.x, a.y - 0.9), "AUV", size=8, fill=th["label"], anchor="n", bold=True)
