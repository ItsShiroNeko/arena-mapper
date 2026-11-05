"""Mouse interaction: tools, hit-testing, drag, rubber-band, context menu."""
import math

from ...constants import MOD
from ...geometry import seg_dist, vec
from ...kinds import KINDS
from ...model import Waypoint
from ...scaling import ui_scale
from ...theme import T


class InteractionMixin:
    def on_tool_change(self):
        t = self.tool_var.get()
        self.canvas.config(cursor="arrow" if t == "select" else "fleur" if t == "pan" else "crosshair")
        if t.startswith("obj:"):
            self.say(f"Klik di peta untuk menaruh {KINDS[t[4:]]['label']}. Esc untuk selesai.")
        else:
            self.say(self.HINTS.get(t, ""))
        self.canvas.delete("ghost")

    def active_tool(self):
        return "pan" if self.space_pan else self.tool_var.get()

    def pick(self, x, y):
        s = self.view[0]
        tol = 7.0 / s
        best, bk = None, None
        for i, w in enumerate(self.proj.waypoints):
            d = math.hypot(w.x - x, w.y - y)
            if d <= 10.0 * ui_scale() / s and (bk is None or (0, d) < bk):
                best, bk = ("wp", i), (0, d)
        a = self.proj.auv
        d = math.hypot(a.x - x, a.y - y)
        if d <= 0.9 + tol and (bk is None or (1, d) < bk):
            best, bk = ("auv",), (1, d)
        for o in self.proj.objects:
            if o.hidden:
                continue
            sh = KINDS[o.kind]["shape"]
            key = None
            if sh == "circle":
                d = math.hypot(o.x - x, o.y - y)
                if d <= o.size / 2 + tol:
                    key = (2, d)
            elif sh in ("gate", "bar"):
                dv = vec(o.heading)
                r = (dv[1], -dv[0])
                hf = o.size / 2
                d = seg_dist(x, y, o.x - r[0] * hf, o.y - r[1] * hf, o.x + r[0] * hf, o.y + r[1] * hf)
                if d <= tol + 0.15:
                    key = (3, d)
            elif sh == "text":
                d = math.hypot(o.x - x, o.y - y)
                if d <= max(0.8, tol * 3):
                    key = (4, d)
            else:
                dx, dy = x - o.x, y - o.y
                fx, fy = vec(o.heading)
                lx, ly = dx * fy - dy * fx, dx * fx + dy * fy
                if abs(lx) <= o.size / 2 + tol * 0.3 and abs(ly) <= o.h / 2 + tol * 0.3:
                    key = (5, o.size * o.h)
            if key and (bk is None or key <= bk):
                best, bk = ("obj", o.id), key
        return best

    def on_press(self, e):
        self.canvas.focus_set()
        if self.view is None:
            return
        x, y = self.s2w(e.x, e.y)
        tool = self.active_tool()
        shift = bool(e.state & 0x1)
        if tool == "pan":
            self.pan = (e.x, e.y, self.view[1], self.view[2])
            return
        if tool == "measure":
            sx, sy = self.snap_xy(x, y)
            self.measure = [sx, sy, sx, sy]
            self.draw_measure()
            return
        if tool == "select":
            hit = self.pick(x, y)
            if hit:
                if shift:
                    self.set_sel([s for s in self.sel if s != hit] if hit in self.sel else self.sel + [hit])
                elif hit not in self.sel:
                    self.set_sel([hit])
                items = []
                for s in self.sel:
                    t = self.tgt(s)
                    if t is not None and not (s[0] == "obj" and t.locked):
                        items.append((t, t.x, t.y))
                self.drag = dict(before=self.proj.state(), px=x, py=y, sx=e.x, sy=e.y, items=items,
                                 moved=False, hit=hit, shift=shift)
            else:
                base = list(self.sel) if shift else []
                if not shift:
                    self.set_sel([])
                self.band = dict(x0=e.x, y0=e.y, base=base)
            return
        sx, sy = self.snap_xy(x, y)
        if tool == "waypoint":
            with self.edit():
                z = self.proj.waypoints[-1].depth if self.proj.waypoints else self.proj.auv.depth
                self.proj.waypoints.append(Waypoint(sx, sy, z))
            self.select(("wp", len(self.proj.waypoints) - 1))
        elif tool == "auv":
            with self.edit():
                self.proj.auv.x, self.proj.auv.y = sx, sy
            self.select(("auv",))
        elif tool.startswith("obj:"):
            with self.edit():
                o = self.proj.add(tool[4:], sx, sy)
            self.select(("obj", o.id))

    def on_drag(self, e):
        if self.view is None:
            return
        x, y = self.s2w(e.x, e.y)
        self.sv_coord.set(f"x {x:6.2f} m   y {y:6.2f} m")
        tool = self.active_tool()
        if self.pan and tool == "pan":
            x0, y0, ox, oy = self.pan
            self.view = (self.view[0], ox + e.x - x0, oy + e.y - y0)
            self.auto_fit = False
            self.redraw()
            return
        if tool == "measure" and self.measure:
            sx, sy = self.snap_xy(x, y)
            self.measure[2:] = [sx, sy]
            self.draw_measure()
            return
        if self.band:
            b = self.band
            self.canvas.delete("band")
            self.canvas.create_rectangle(b["x0"], b["y0"], e.x, e.y, outline=T["accent"], dash=(4, 3), width=1,
                                         fill="", tags="band")
            return
        d = self.drag
        if d and d["items"]:
            if not d["moved"] and math.hypot(e.x - d["sx"], e.y - d["sy"]) < 4:
                return
            d["moved"] = True
            dx, dy = x - d["px"], y - d["py"]
            if len(d["items"]) == 1:
                t, x0, y0 = d["items"][0]
                t.x, t.y = self.snap_xy(x0 + dx, y0 + dy)
            else:
                if self.snap_on.get():
                    st = max(self.proj.snap_step, 0.01)
                    dx, dy = round(dx / st) * st, round(dy / st) * st
                for t, x0, y0 in d["items"]:
                    t.x, t.y = self.proj.clamp(x0 + dx, y0 + dy)
            self.refresh_props()
            self.redraw()

    def on_release(self, e):
        self.pan = None
        if self.band:
            b, self.band = self.band, None
            self.canvas.delete("band")
            if abs(e.x - b["x0"]) > 3 or abs(e.y - b["y0"]) > 3:
                xa, ya = self.s2w(min(e.x, b["x0"]), max(e.y, b["y0"]))
                xb, yb = self.s2w(max(e.x, b["x0"]), min(e.y, b["y0"]))
                got = [("obj", o.id) for o in self.proj.objects
                       if not o.hidden and xa <= o.x <= xb and ya <= o.y <= yb]
                got += [("wp", i) for i, w in enumerate(self.proj.waypoints) if xa <= w.x <= xb and ya <= w.y <= yb]
                a = self.proj.auv
                if xa <= a.x <= xb and ya <= a.y <= yb:
                    got.append(("auv",))
                self.set_sel(b["base"] + got)
        d, self.drag = self.drag, None
        if d:
            if d["moved"]:
                self.commit(d["before"])
            elif not d["shift"] and len(self.sel) > 1:
                self.set_sel([d["hit"]])

    def on_motion(self, e):
        if self.view is None:
            return
        x, y = self.s2w(e.x, e.y)
        inside = 0 <= x <= self.proj.W and 0 <= y <= self.proj.H
        self.sv_coord.set(f"x {x:6.2f} m   y {y:6.2f} m" if inside else "")
        tool = self.tool_var.get()
        if tool in ("waypoint", "auv") or tool.startswith("obj:"):
            sx, sy = self.snap_xy(x, y)
            self.draw_ghost(sx, sy)
        elif tool == "select" and not self.drag and not self.band:
            hit = self.pick(x, y)
            t = self.tgt(hit) if hit else None
            if t is None:
                self.say(self.HINTS["select"])
            elif hit[0] == "obj":
                self.say(f"{t.label} #{t.id}   ({t.x:.2f}, {t.y:.2f})   kedalaman {t.depth:g} m"
                         f"{'   [terkunci]' if t.locked else ''}")
            elif hit[0] == "wp":
                self.say(f"Waypoint {hit[1] + 1}  {t.action}   ({t.x:.2f}, {t.y:.2f})  z {t.depth:g} m")
            else:
                self.say(f"AUV   ({t.x:.2f}, {t.y:.2f})   heading {t.heading:.0f} deg")

    def seg_near(self, x, y):
        tol = 10.0 * ui_scale() / self.view[0]
        a = self.proj.auv
        pts = [(a.x, a.y)] + [(w.x, w.y) for w in self.proj.waypoints]
        best = None
        for i, (p, q) in enumerate(zip(pts[:-1], pts[1:])):
            d = seg_dist(x, y, p[0], p[1], q[0], q[1])
            if d <= tol and (best is None or d < best[0]):
                best = (d, i)
        return best[1] if best else None

    def on_context(self, e):
        if self.view is None:
            return
        x, y = self.s2w(e.x, e.y)
        hit = self.pick(x, y)
        m = self.ctx
        m.delete(0, "end")
        sx, sy = self.snap_xy(x, y)
        if hit:
            if hit not in self.sel:
                self.set_sel([hit])
            if any(s[0] == "obj" for s in self.sel):
                self._mi(m, "Salin", "copy", f"{MOD}+C", self.copy_sel)
                self._mi(m, "Potong", "cut", f"{MOD}+X", self.cut)
                self._mi(m, "Duplikat", "copy", f"{MOD}+D", self.duplicate)
                m.add_separator()
                self._mi(m, "Putar +90 deg", "rotate", "", lambda: self.rotate(90))
                self._mi(m, "Putar -90 deg", "rotate", "", lambda: self.rotate(-90))
                self._mi(m, "Kunci / buka kunci", "lock", f"{MOD}+L", lambda: self.toggle_flag("locked"))
                self._mi(m, "Sembunyikan", "eye", f"{MOD}+H", lambda: self.toggle_flag("hidden"))
                m.add_separator()
            elif hit[0] == "auv":
                self._mi(m, "Putar +90 deg", "rotate", "", lambda: self.rotate(90))
            if any(s[0] != "auv" for s in self.sel):
                self._mi(m, "Hapus", "delete", "Del", self.delete_selected)
        else:
            self._mi(m, "Tempel di sini", "paste", f"{MOD}+V", lambda: self.paste((sx, sy)))
            m.add_separator()
            self._mi(m, "Taruh AUV di sini", "auv", "", lambda: self._place_auv(sx, sy))
            self._mi(m, "Tambah waypoint di sini", "waypoint", "", lambda: self._add_wp(sx, sy))
            seg = self.seg_near(x, y)
            if seg is not None:
                self._mi(m, "Sisipkan waypoint pada jalur ini", "insert", "", lambda: self.insert_wp(seg, sx, sy))
        try:
            m.tk_popup(e.x_root, e.y_root)
        finally:
            m.grab_release()

    def _place_auv(self, x, y):
        with self.edit():
            self.proj.auv.x, self.proj.auv.y = x, y
        self.select(("auv",))

    def _add_wp(self, x, y):
        with self.edit():
            z = self.proj.waypoints[-1].depth if self.proj.waypoints else self.proj.auv.depth
            self.proj.waypoints.append(Waypoint(x, y, z))
        self.select(("wp", len(self.proj.waypoints) - 1))

    def insert_wp(self, i, x, y):
        with self.edit():
            z = self.proj.waypoints[i - 1].depth if i > 0 else self.proj.auv.depth
            self.proj.waypoints.insert(i, Waypoint(x, y, z))
        self.select(("wp", i))
