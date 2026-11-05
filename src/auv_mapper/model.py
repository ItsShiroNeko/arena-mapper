"""Project data model, (de)serialisation, mission planner and validator.

This module is pure Python (no Tk) so it can be unit-tested and reused headlessly.
"""
import json
import math
import os
from dataclasses import asdict, dataclass

from .constants import CLEARANCE, FORMAT_VERSION, TURN_RATE_DEG_S
from .geometry import bearing, seg_dist, vec, wrap180
from .kinds import KINDS, TOKENS
from .utils import now_iso


@dataclass
class Obj:
    id: int
    kind: str
    x: float
    y: float
    heading: float = 0.0
    size: float = 1.0
    h: float = 1.0
    depth: float = 1.0
    label: str = ""
    color: str = ""
    locked: bool = False
    hidden: bool = False


@dataclass
class Waypoint:
    x: float
    y: float
    depth: float = 1.0
    action: str = "GOTO"
    hold: float = 0.0


@dataclass
class Auv:
    x: float = 1.0
    y: float = 1.0
    heading: float = 0.0
    depth: float = 1.0


class Project:
    def __init__(self, name="Proyek Baru", W=50.0, H=25.0, D=2.0, qual=10.0):
        self.name = name
        self.W, self.H, self.D, self.qual = float(W), float(H), float(D), float(qual)
        self.grid_minor, self.grid_major, self.snap_step = 1.0, 5.0, 0.5
        self.standoff, self.backoff, self.north_offset = 2.0, 1.5, 0.0
        self.speed = 0.5
        self.order = "orange gate yellow red blue drum_blue surface"
        self.objects, self.waypoints = [], []
        self.auv = Auv(1.0, H / 2.0, 90.0, 1.0)
        self.next_id = 1
        self.created = self.modified = now_iso()

    # ---- objects
    def add(self, kind, x, y, heading=None):
        k = KINDS[kind]
        o = Obj(self.next_id, kind, float(x), float(y), float(k["heading"] if heading is None else heading),
                k["size"], k["h"], k["depth"], k["label"])
        self.next_id += 1
        self.objects.append(o)
        return o

    def obj(self, oid):
        for o in self.objects:
            if o.id == oid:
                return o
        return None

    def clamp(self, x, y, m=0.0):
        return min(max(x, m), self.W - m), min(max(y, m), self.H - m)

    # ---- serialisation
    def to_dict(self, meta=True):
        d = {
            "format": "auvmap", "version": FORMAT_VERSION, "name": self.name,
            "pool": {"width": self.W, "height": self.H, "depth": self.D, "qual_width": self.qual},
            "grid": {"minor": self.grid_minor, "major": self.grid_major, "snap": self.snap_step},
            "mission": {"order": self.order, "speed": self.speed, "standoff": self.standoff,
                        "backoff": self.backoff, "north_offset": self.north_offset},
            "auv": asdict(self.auv),
            "objects": [asdict(o) for o in self.objects],
            "waypoints": [asdict(w) for w in self.waypoints],
            "next_id": self.next_id,
        }
        if meta:
            d["meta"] = {"created": self.created, "modified": self.modified}
        return d

    def state(self):
        return json.dumps(self.to_dict(False), sort_keys=True)

    def apply_dict(self, d):
        pool, grid, ms = d.get("pool", {}), d.get("grid", {}), d.get("mission", {})
        self.name = str(d.get("name", self.name))
        self.W = float(pool.get("width", 50.0))
        self.H = float(pool.get("height", 25.0))
        self.D = float(pool.get("depth", 2.0))
        self.qual = float(pool.get("qual_width", 10.0 if "pool" not in d else 0.0))
        self.grid_minor = float(grid.get("minor", 1.0))
        self.grid_major = float(grid.get("major", 5.0))
        self.snap_step = float(grid.get("snap", 0.5))
        self.order = str(ms.get("order", d.get("order", self.order)))
        self.speed = float(ms.get("speed", 0.5))
        self.standoff = float(ms.get("standoff", 2.0))
        self.backoff = float(ms.get("backoff", 1.5))
        self.north_offset = float(ms.get("north_offset", 0.0))
        a = d.get("auv", {})
        self.auv = Auv(float(a.get("x", 1.0)), float(a.get("y", 1.0)),
                       float(a.get("heading", 0.0)), float(a.get("depth", 1.0)))
        nid = int(d.get("next_id", 1))
        objs = []
        for od in d.get("objects", []):
            kind = od.get("kind")
            if kind not in KINDS:
                continue
            k = KINDS[kind]
            oid = int(od.get("id", 0) or 0)
            if oid <= 0:
                oid = nid
                nid += 1
            objs.append(Obj(oid, kind, float(od["x"]), float(od["y"]),
                            float(od.get("heading", k["heading"])), float(od.get("size", k["size"])),
                            float(od.get("h", k["h"])), float(od.get("depth", k["depth"])),
                            str(od.get("label") or k["label"]), str(od.get("color", "")),
                            bool(od.get("locked", False)), bool(od.get("hidden", False))))
        self.objects = objs
        self.next_id = max([nid] + [o.id + 1 for o in objs])
        self.waypoints = [Waypoint(float(w["x"]), float(w["y"]), float(w.get("depth", 1.0)),
                                   str(w.get("action", "GOTO")), float(w.get("hold", 0.0)))
                          for w in d.get("waypoints", [])]
        meta = d.get("meta", {})
        self.created = meta.get("created", self.created)
        self.modified = meta.get("modified", self.modified)

    def load_state(self, s):
        self.apply_dict(json.loads(s))

    @classmethod
    def from_dict(cls, d):
        p = cls()
        p.apply_dict(d)
        return p

    @classmethod
    def load(cls, path):
        with open(path, encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    def save(self, path, touch=True):
        if touch:
            self.modified = now_iso()
        tmp = path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(True), f, indent=2, ensure_ascii=False)
        os.replace(tmp, path)

    # ---- template
    def apply_sauvc_template(self):
        sx, sy = self.W / 50.0, self.H / 25.0

        def A(kind, x, y, h=None):
            return self.add(kind, x * sx, y * sy, h)

        if self.qual > 0:
            for y in (22.4, 11.8, 2.6):
                self.add("qstart", 0.4, y * sy, 90)
                self.add("qual_gate", self.qual, y * sy, 90)
        A("surface", 12.1, 6.9)
        A("start", 31.8, 1.1)
        A("gate", 26.2, 9.6, 0)
        A("target", 26.0, 22.5)
        A("drum_blue", 22.8, 22.5)
        for x in (24.9, 27.1, 29.2):
            A("drum_red", x, 22.5)
        A("flare_orange", 27.7, 5.4)
        A("flare_yellow", 22.6, 16.6)
        A("flare_red", 36.6, 16.9)
        A("flare_blue", 44.2, 14.5)
        self.auv = Auv(31.8 * sx, 1.1 * sy, 0.0, 1.0)

    # ---- strategy
    def plan(self):
        wps, warn = [], []
        cx, cy = self.auv.x, self.auv.y
        for tok in self.order.split():
            if tok.lower().startswith("goto:"):
                try:
                    v = [float(p) for p in tok[5:].split(",")]
                    x, y = self.clamp(v[0], v[1])
                    wps.append(Waypoint(x, y, v[2] if len(v) > 2 else self.auv.depth, "GOTO"))
                    cx, cy = x, y
                except (ValueError, IndexError):
                    warn.append(tok)
                continue
            kind = TOKENS.get(tok.lower())
            cands = [o for o in self.objects if o.kind == kind] if kind else []
            if not cands:
                warn.append(tok)
                continue
            o = min(cands, key=lambda c: math.hypot(c.x - cx, c.y - cy))
            shape = KINDS[kind]["shape"]
            T_ = tok.upper()
            if shape in ("gate", "bar"):
                d = vec(o.heading)
                a = self.clamp(o.x - d[0] * self.standoff, o.y - d[1] * self.standoff, 0.3)
                b = self.clamp(o.x + d[0] * self.standoff, o.y + d[1] * self.standoff, 0.3)
                tag = "GATE" if kind == "gate" else "QUAL"
                wps += [Waypoint(*a, o.depth, f"ALIGN {tag}"), Waypoint(o.x, o.y, o.depth, f"PASS {tag}"),
                        Waypoint(*b, o.depth, f"EXIT {tag}")]
            elif kind.startswith("flare"):
                dx, dy = o.x - cx, o.y - cy
                n = math.hypot(dx, dy) or 1.0
                u = (dx / n, dy / n)
                wps.append(Waypoint(o.x, o.y, o.depth, f"TOUCH {T_}", 1.0))
                wps.append(Waypoint(*self.clamp(o.x - u[0] * self.backoff, o.y - u[1] * self.backoff, 0.3),
                                    o.depth, "BACKOFF"))
            elif kind.startswith("drum"):
                wps.append(Waypoint(o.x, o.y, o.depth, f"DROP {T_}", 2.0))
            elif kind == "surface":
                wps.append(Waypoint(o.x, o.y, 0.0, "SURFACE", 3.0))
            elif kind == "target":
                wps.append(Waypoint(o.x, o.y, o.depth, "TARGET ZONE"))
            else:
                wps.append(Waypoint(o.x, o.y, o.depth, f"VISIT {o.label}"[:24]))
            cx, cy = wps[-1].x, wps[-1].y
        return wps, warn

    def segments(self):
        rows, x, y, h, cum, t = [], self.auv.x, self.auv.y, self.auv.heading, 0.0, 0.0
        for i, w in enumerate(self.waypoints, 1):
            dx, dy = w.x - x, w.y - y
            dist = math.hypot(dx, dy)
            b = bearing(dx, dy) if dist > 1e-6 else h
            turn = wrap180(b - h)
            cum += dist
            t += dist / max(self.speed, 0.01) + abs(turn) / TURN_RATE_DEG_S + w.hold
            rows.append(dict(idx=i, x=w.x, y=w.y, depth=w.depth, action=w.action, hold=w.hold, bearing=b,
                             dist=dist, turn=turn, cum=cum, eta=t))
            x, y, h = w.x, w.y, b
        return rows

    # ---- validation
    def validate(self):
        """List of (level, message, selection) with level in error / warn / info."""
        out = []
        W, H, D = self.W, self.H, self.D

        def inside(x, y):
            return -1e-6 <= x <= W + 1e-6 and -1e-6 <= y <= H + 1e-6

        a = self.auv
        if not inside(a.x, a.y):
            out.append(("error", "Posisi awal AUV di luar kolam.", ("auv",)))
        seen = set()
        for o in self.objects:
            sh = KINDS[o.kind]["shape"]
            if not inside(o.x, o.y):
                out.append(("warn", f"{o.label} (#{o.id}) berada di luar kolam.", ("obj", o.id)))
            if sh != "text" and o.depth > D + 1e-6:
                out.append(("warn", f"{o.label} (#{o.id}) lebih dalam dari kolam ({o.depth:g} > {D:g} m).", ("obj", o.id)))
            key = (o.kind, round(o.x, 2), round(o.y, 2))
            if key in seen:
                out.append(("info", f"{o.label} (#{o.id}) menumpuk dengan objek sejenis.", ("obj", o.id)))
            seen.add(key)
        if not self.waypoints:
            out.append(("info", "Belum ada waypoint. Tekan P untuk generate dari urutan misi.", None))
            return out
        obst = [o for o in self.objects if KINDS[o.kind]["shape"] == "circle" or o.kind == "obstacle"]
        rows = self.segments()
        px, py, pd = a.x, a.y, a.depth
        for i, w in enumerate(self.waypoints):
            sel = ("wp", i)
            n = i + 1
            if not inside(w.x, w.y):
                out.append(("error", f"Waypoint {n} berada di luar kolam.", sel))
            if w.depth > D + 1e-6:
                out.append(("error", f"Waypoint {n}: kedalaman {w.depth:g} m melebihi kolam ({D:g} m).", sel))
            for o in obst:
                rad = (o.size / 2 if KINDS[o.kind]["shape"] == "circle" else max(o.size, o.h) / 2) + CLEARANCE
                if math.hypot(o.x - w.x, o.y - w.y) <= 0.35:
                    continue  # intentional visit
                if math.hypot(o.x - px, o.y - py) <= rad + 0.05:
                    continue  # leaving the object
                if min(abs(pd - o.depth), abs(w.depth - o.depth)) > 0.8 and abs(pd - w.depth) < 0.8:
                    continue  # different depth
                if seg_dist(o.x, o.y, px, py, w.x, w.y) < rad:
                    out.append(("warn", f"Segmen ke waypoint {n} melintas dekat {o.label} (#{o.id}).", sel))
            r = rows[i]
            if i > 0 and abs(r["turn"]) > 135 and r["dist"] > 0.1:
                out.append(("info", f"Waypoint {n}: belok tajam {r['turn']:+.0f} deg.", sel))
            if w.action.startswith("PASS"):
                for o in self.objects:
                    if KINDS[o.kind]["shape"] in ("gate", "bar") and math.hypot(o.x - w.x, o.y - w.y) < 0.05:
                        d = abs(wrap180(r["bearing"] - o.heading))
                        d = min(d, 180 - d)
                        if d > 25:
                            out.append(("warn", f"Waypoint {n}: lewat {o.label} miring {d:.0f} deg dari sumbunya.", sel))
            px, py, pd = w.x, w.y, w.depth
        return out
