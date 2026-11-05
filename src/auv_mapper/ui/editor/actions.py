"""Editing commands: clipboard, transforms, alignment, waypoints, planning."""
import json
import tkinter as tk
from dataclasses import asdict

from ...kinds import KINDS


class ActionsMixin:
    def delete_selected(self):
        if not self.sel:
            return
        objs = [o for o in self.sel_objs() if not o.locked]
        wps = sorted({s[1] for s in self.sel if s[0] == "wp"}, reverse=True)
        if not objs and not wps:
            if any(o.locked for o in self.sel_objs()):
                self.say("Objek terkunci tidak bisa dihapus. Buka kunci dulu (Ctrl+L).")
            return
        with self.edit():
            for o in objs:
                self.proj.objects.remove(o)
            for i in wps:
                if i < len(self.proj.waypoints):
                    del self.proj.waypoints[i]
        self.set_sel([])

    def _paste_objs(self, data, dx, dy):
        new = []
        with self.edit():
            for od in data:
                kind = od.get("kind")
                if kind not in KINDS:
                    continue
                k = KINDS[kind]
                n = self.proj.add(kind, *self.proj.clamp(od["x"] + dx, od["y"] + dy), od.get("heading", k["heading"]))
                n.size, n.h, n.depth = od.get("size", k["size"]), od.get("h", k["h"]), od.get("depth", k["depth"])
                n.label, n.color = od.get("label", k["label"]), od.get("color", "")
                n.locked, n.hidden = bool(od.get("locked", False)), False
                new.append(("obj", n.id))
        if new:
            self.set_sel(new)

    def duplicate(self):
        data = [asdict(o) for o in self.sel_objs()]
        if data:
            self._paste_objs(data, 1.0, 1.0)

    def copy_sel(self):
        objs = self.sel_objs()
        if not objs:
            self.say("Pilih objek dulu untuk disalin.")
            return False
        self.clip = [asdict(o) for o in objs]
        self.paste_n = 0
        try:
            self.app.clipboard_clear()
            self.app.clipboard_append("AUVMAP-CLIP:" + json.dumps(self.clip))
        except tk.TclError:
            pass
        self.say(f"{len(objs)} objek disalin.")
        return True

    def cut(self):
        if self.copy_sel():
            self.delete_selected()

    def paste(self, at=None):
        data = None
        try:
            txt = self.app.clipboard_get()
            if txt.startswith("AUVMAP-CLIP:"):
                data = json.loads(txt[len("AUVMAP-CLIP:"):])
        except (tk.TclError, ValueError):
            pass
        data = data or self.clip
        if not data:
            self.say("Clipboard kosong.")
            return
        self.paste_n += 1
        if at:
            cx = sum(od["x"] for od in data) / len(data)
            cy = sum(od["y"] for od in data) / len(data)
            dx, dy = at[0] - cx, at[1] - cy
        else:
            dx = dy = 1.0 * self.paste_n
        self._paste_objs(data, dx, dy)

    def rotate(self, deg):
        targets = []
        for s in self.sel:
            t = self.tgt(s)
            if t is not None and hasattr(t, "heading") and not (s[0] == "obj" and t.locked):
                targets.append(t)
        if not targets:
            return
        with self.edit():
            for t in targets:
                t.heading = (t.heading + deg) % 360.0

    def nudge(self, dx, dy, mult=1):
        st = max(self.proj.snap_step, 0.01) * mult
        items = [self.tgt(s) for s in self.sel if not (s[0] == "obj" and self.tgt(s) and self.tgt(s).locked)]
        items = [t for t in items if t is not None]
        if not items:
            return
        with self.edit():
            for t in items:
                t.x, t.y = self.proj.clamp(t.x + dx * st, t.y + dy * st)

    def adjust(self, attr, delta, lo, hi):
        targets = [t for t in (self.tgt(s) for s in self.sel) if t is not None and hasattr(t, attr)]
        if not targets:
            return
        with self.edit():
            for t in targets:
                setattr(t, attr, round(min(max(getattr(t, attr) + delta, lo), hi), 3))

    def toggle_flag(self, key):
        objs = self.sel_objs()
        if not objs:
            return
        val = not all(getattr(o, key) for o in objs)
        with self.edit():
            for o in objs:
                setattr(o, key, val)
        self.say(("Terkunci" if key == "locked" else "Disembunyikan") if val else
                 ("Kunci dibuka" if key == "locked" else "Ditampilkan"))

    def show_all(self):
        if any(o.hidden for o in self.proj.objects):
            with self.edit():
                for o in self.proj.objects:
                    o.hidden = False

    def align(self, mode):
        objs = [o for o in self.sel_objs() if not o.locked]
        if len(objs) < 2 or (mode in ("dh", "dv") and len(objs) < 3):
            self.say("Pilih minimal 2 objek (3 untuk sebar).")
            return
        xs, ys = [o.x for o in objs], [o.y for o in objs]
        with self.edit():
            if mode == "l":
                for o in objs:
                    o.x = min(xs)
            elif mode == "r":
                for o in objs:
                    o.x = max(xs)
            elif mode == "c":
                for o in objs:
                    o.x = (min(xs) + max(xs)) / 2
            elif mode == "t":
                for o in objs:
                    o.y = max(ys)
            elif mode == "b":
                for o in objs:
                    o.y = min(ys)
            elif mode == "m":
                for o in objs:
                    o.y = (min(ys) + max(ys)) / 2
            elif mode in ("dh", "dv"):
                attr = "x" if mode == "dh" else "y"
                objs.sort(key=lambda o: getattr(o, attr))
                a, b = getattr(objs[0], attr), getattr(objs[-1], attr)
                for i, o in enumerate(objs):
                    setattr(o, attr, a + (b - a) * i / (len(objs) - 1))

    def move_wp(self, d):
        s = self.selected
        if not s or s[0] != "wp":
            return
        i, j = s[1], s[1] + d
        if not (0 <= j < len(self.proj.waypoints)):
            return
        with self.edit():
            w = self.proj.waypoints
            w[i], w[j] = w[j], w[i]
        self.select(("wp", j))

    def clear_wps(self):
        if self.proj.waypoints:
            with self.edit():
                self.proj.waypoints.clear()

    # ---- mission planning
    def do_plan(self):
        self.apply_order()
        wps, warn = self.proj.plan()
        with self.edit():
            self.proj.waypoints = wps
        self.set_sel([])
        if warn:
            self.say("Token tidak dikenal / objek tidak ada: " + ", ".join(warn))
        else:
            self.say(f"{len(wps)} waypoint dibuat dari urutan misi.")
        self.nb.select(self.tab_mission)

    def run_validate(self):
        self.refresh_issues()
        self.nb.select(self.tab_check)
        bad = sum(1 for l, _m, _s in self.issues if l != "info")
        self.say("Validasi: tidak ada masalah." if not self.issues else f"Validasi: {bad} peringatan/error.")
