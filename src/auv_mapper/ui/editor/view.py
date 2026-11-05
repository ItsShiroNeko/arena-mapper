"""Viewport: coordinate transforms, zoom / pan, canvas rendering."""
import math

from ...geometry import auv_poly, bearing, fit_view
from ...kinds import KINDS
from ...model import Obj
from ...render.scene import draw_hud, draw_obj, draw_scene
from ...render.sinks import TkSink
from ...scaling import ui_scale
from ...theme import F, T


class ViewMixin:
    def fit(self, force=False):
        if force:
            self.auto_fit = True
        cw, ch = self.canvas.winfo_width(), self.canvas.winfo_height()
        if cw < 20 or ch < 20:
            return
        self.view = fit_view(self.proj.W, self.proj.H, cw, ch)
        self.redraw()
        self.update_status()

    def on_configure(self, _e):
        if self.auto_fit or self.view is None:
            self.fit()
        else:
            self.redraw()

    def w2s(self, x, y):
        s, ox, oy = self.view
        return ox + x * s, oy - y * s

    def s2w(self, px, py):
        s, ox, oy = self.view
        return (px - ox) / s, (oy - py) / s

    def snap_xy(self, x, y):
        if self.snap_on.get():
            st = max(self.proj.snap_step, 0.01)
            x, y = round(x / st) * st, round(y / st) * st
        return self.proj.clamp(x, y)

    def zoom(self, factor, px=None, py=None):
        if self.view is None:
            return
        s, ox, oy = self.view
        px = self.canvas.winfo_width() / 2 if px is None else px
        py = self.canvas.winfo_height() / 2 if py is None else py
        wx, wy = self.s2w(px, py)
        ns = min(max(s * factor, 2.0), 600.0)
        self.view = (ns, px - wx * ns, py + wy * ns)
        self.auto_fit = False
        self.redraw()
        self.update_status()

    def on_wheel(self, e):
        up = getattr(e, "delta", 0) > 0 or getattr(e, "num", 0) == 4
        if self.view is None:
            return
        if e.state & 0x1:  # Shift + scroll = horizontal pan
            s, ox, oy = self.view
            self.view = (s, ox + (60 if up else -60), oy)
            self.auto_fit = False
            self.redraw()
            return
        self.zoom(1.15 if up else 1 / 1.15, e.x, e.y)

    def on_pan_start(self, e):
        if self.view:
            self.pan = (e.x, e.y, self.view[1], self.view[2])
            self.canvas.config(cursor="fleur")

    def on_pan_move(self, e):
        if self.pan and self.view:
            x0, y0, ox, oy = self.pan
            self.view = (self.view[0], ox + e.x - x0, oy + e.y - y0)
            self.auto_fit = False
            self.redraw()

    def end_pan(self):
        self.pan = None
        self.on_tool_change()

    def space_down(self):
        if self._space_job:
            self.after_cancel(self._space_job)
            self._space_job = None
        if not self.space_pan:
            self.space_pan = True
            self.canvas.config(cursor="fleur")

    def space_up(self):
        if self._space_job:
            self.after_cancel(self._space_job)
        self._space_job = self.after(40, self._space_release)  # ignore X11 auto-repeat

    def _space_release(self):
        self._space_job = None
        self.space_pan = False
        self.on_tool_change()

    # ---- rendering
    def redraw(self):
        if self.view is None:
            return
        c = self.canvas
        c.delete("scene")
        c.delete("hud")
        draw_scene(TkSink(c, "scene"), self.proj, self.view, T, grid=self.grid_on.get(),
                   labels=self.labels_on.get(), selected=set(self.sel))
        c.tag_lower("scene")
        draw_hud(TkSink(c, "hud"), c.winfo_width(), c.winfo_height(), self.view[0], T)
        self.draw_sim()
        self.draw_measure()
        self.draw_profile()

    def draw_ghost(self, x, y):
        c = self.canvas
        c.delete("ghost")
        tool = self.tool_var.get()
        px, py = self.w2s(x, y)
        sink = TkSink(c, "ghost")
        if tool.startswith("obj:"):
            kind = tool[4:]
            k = KINDS[kind]
            g = Obj(-1, kind, x, y, k["heading"], k["size"], k["h"], k["depth"], k["label"])
            draw_obj(sink, g, self.view, T, ghost=True, labels=False)
        elif tool == "waypoint":
            sink.oval(px, py, 9 * ui_scale(), fill="", outline=T["path"], width=2, dash=(4, 3))
        elif tool == "auv":
            sink.polygon([self.w2s(*p) for p in auv_poly(x, y, self.proj.auv.heading)], fill="",
                         outline=T["auv"], width=2, dash=(4, 3))
        sink.line([(px - 7, py), (px + 7, py)], fill=T["sel"], width=1)
        sink.line([(px, py - 7), (px, py + 7)], fill=T["sel"], width=1)

    def draw_measure(self):
        c = self.canvas
        c.delete("measure")
        m = self.measure
        if not m or self.view is None:
            return
        x0, y0, x1, y1 = m
        a, b = self.w2s(x0, y0), self.w2s(x1, y1)
        sink = TkSink(c, "measure")
        sink.line([a, b], fill=T["measure"], width=2, dash=(6, 3))
        sink.oval(*a, 4, fill=T["measure"], outline="")
        sink.oval(*b, 4, fill=T["measure"], outline="")
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy)
        txt = f"{d:.2f} m   brg {bearing(dx, dy):.0f} deg   dx {dx:+.2f}  dy {dy:+.2f}" if d > 1e-6 else "0 m"
        mx, my = (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 12
        tid = c.create_text(mx, my, text=txt, fill=T["measure"], font=F(9, True), tags="measure")
        bb = c.bbox(tid)
        if bb:
            r = c.create_rectangle(bb[0] - 4, bb[1] - 2, bb[2] + 4, bb[3] + 2, fill=T["canvas"], outline=T["measure"],
                                   tags="measure")
            c.tag_lower(r, tid)
