"""Keeps side panels (tables, trees, issues, profile) in sync with the project."""
import time

from ...constants import APP_NAME
from ...icons import ico
from ...scaling import sc
from ...theme import F, T
from ...utils import fmt, fmt_time


class RefreshMixin:
    def valid(self, s):
        if s[0] == "obj":
            return self.proj.obj(s[1]) is not None
        if s[0] == "wp":
            return s[1] < len(self.proj.waypoints)
        return s[0] == "auv"

    def refresh_all(self):
        self.sel = [s for s in self.sel if self.valid(s)]
        self.refresh_props()
        self.refresh_table()
        self.refresh_objects()
        self.refresh_issues()
        self.refresh_side_vars()
        self.update_title()
        self.btn_undo.state(["!disabled"] if self.undo else ["disabled"])
        self.btn_redo.state(["!disabled"] if self.redo else ["disabled"])
        self.redraw()
        self.update_status()

    def update_title(self):
        self.app.title(f"{'*' if self.is_dirty() else ''}{self.proj.name} - {APP_NAME}")

    def update_status(self):
        n = len(self.sel)
        sel = f"{n} dipilih   |   " if n else ""
        zoom = f"zoom {self.view[0]:.0f} px/m" if self.view else ""
        self.sv_info.set(f"{sel}{zoom}   snap {'ON' if self.snap_on.get() else 'off'}")

    def refresh_side_vars(self):
        if self.order_var.get() != self.proj.order:
            self.order_var.set(self.proj.order)
        self.speed_var.set(fmt(self.proj.speed))
        for _l, key, t in self.PROJECT_FIELDS:
            self.proj_vars[key].set(fmt(getattr(self.proj, key)))

    def refresh_table(self):
        rows = self.proj.segments()
        self.tree.delete(*self.tree.get_children())
        for r in rows:
            self.tree.insert("", "end", iid=str(r["idx"] - 1),
                             values=(r["idx"], f"{r['x']:.1f}", f"{r['y']:.1f}", f"{r['depth']:.1f}", r["action"],
                                     f"{r['bearing']:.0f}", f"{r['dist']:.1f}", f"{r['turn']:+.0f}",
                                     fmt_time(r["eta"])))
        self.sync_trees()
        length = rows[-1]["cum"] if rows else 0.0
        total = rows[-1]["eta"] if rows else 0.0
        self.lbl_stats.config(text=f"{len(rows)} waypoint  |  jalur {length:.1f} m  |  estimasi {fmt_time(total)} "
                                   f"(mm:ss) @ {self.proj.speed:g} m/s")
        self.draw_profile()

    def refresh_objects(self):
        self.otree.delete(*self.otree.get_children())
        for o in self.proj.objects:
            self.otree.insert("", "end", iid=str(o.id),
                              values=(o.id, o.label, f"{o.x:.1f}", f"{o.y:.1f}",
                                      "\u25CB" if o.hidden else "\u25CF", "\u2713" if o.locked else ""))
        self.sync_trees()

    def refresh_issues(self):
        self.issues = self.proj.validate()
        self.ctree.delete(*self.ctree.get_children())
        icons = {"error": "error", "warn": "warn", "info": "info"}
        for i, (lvl, msg, _sel) in enumerate(self.issues):
            self.ctree.insert("", "end", iid=str(i), text="  " + msg, image=ico(icons[lvl], sc(16)))
        bad = sum(1 for l, _m, _s in self.issues if l != "info")
        if not self.issues:
            self.lbl_check.config(text="Tidak ada masalah ditemukan")
        else:
            self.lbl_check.config(text=f"{bad} peringatan/error, {len(self.issues) - bad} info")
        self.nb.tab(self.tab_check, text=f"Cek ({bad})" if bad else "Cek")

    def on_issue_select(self, _e):
        if self._syncing():
            return
        sel = self.ctree.selection()
        if sel:
            s = self.issues[int(sel[0])][2]
            if s:
                self.set_sel([s], src="issue")

    def draw_profile(self):
        c = self.prof
        c.delete("all")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 60:
            return
        rows = self.proj.segments()
        D = max(self.proj.D, 0.1)
        ml, mr, mt, mb = 38, 10, 10, 18
        c.create_rectangle(ml, mt, w - mr, h - mb, outline=T["border"], fill=T["panel2"])
        c.create_text(ml - 4, mt, text="0 m", anchor="e", fill=T["muted"], font=F(7))
        c.create_text(ml - 4, h - mb, text=f"{D:g} m", anchor="e", fill=T["muted"], font=F(7))
        c.create_text(ml, h - 3, text="Profil kedalaman", anchor="sw", fill=T["muted"], font=F(7))
        if not rows:
            return
        total = max(rows[-1]["cum"], 1e-6)

        def X(d):
            return ml + (w - ml - mr) * d / total

        def Y(z):
            return mt + (h - mt - mb) * min(max(z / D, 0.0), 1.0)

        pts = [(X(0), Y(self.proj.auv.depth))] + [(X(r["cum"]), Y(r["depth"])) for r in rows]
        c.create_line(*[v for p in pts for v in p], fill=T["path"], width=2)
        for i, (x, y) in enumerate(pts[1:]):
            on = ("wp", i) in self.sel
            c.create_oval(x - 3, y - 3, x + 3, y + 3, fill=T["sel"] if on else T["path"], outline="")
        c.create_text(w - mr, h - 3, text=f"{total:.1f} m", anchor="se", fill=T["muted"], font=F(7))

    # ---- tree synchronisation
    def _syncing(self):
        return time.monotonic() < self._sync_until

    def sync_trees(self, src=None):
        self._sync_until = time.monotonic() + 0.12
        wp = [s[1] for s in self.sel if s[0] == "wp"]
        kids = self.tree.get_children()
        if len(self.sel) == 1 and wp and str(wp[0]) in kids:
            self.tree.selection_set(str(wp[0]))
            self.tree.see(str(wp[0]))
        elif self.tree.selection():
            self.tree.selection_remove(*self.tree.selection())
        if src != "obj":
            ids = [str(s[1]) for s in self.sel if s[0] == "obj" and str(s[1]) in self.otree.get_children()]
            if ids:
                self.otree.selection_set(*ids)
                self.otree.see(ids[0])
            elif self.otree.selection():
                self.otree.selection_remove(*self.otree.selection())

    def on_tree_select(self, _e):
        if self._syncing():
            return
        sel = self.tree.selection()
        if sel:
            self.set_sel([("wp", int(sel[0]))], src="wp")

    def on_otree_select(self, _e):
        if self._syncing():
            return
        ids = [("obj", int(i)) for i in self.otree.selection()]
        if ids != [s for s in self.sel if s[0] == "obj"]:
            self.set_sel(ids, src="obj")

    def on_obj_click(self, e):
        if self.otree.identify_region(e.x, e.y) != "cell":
            return
        iid, col = self.otree.identify_row(e.y), self.otree.identify_column(e.x)
        if not iid or col not in ("#5", "#6"):
            return
        o = self.proj.obj(int(iid))
        if o is None:
            return
        key = "hidden" if col == "#5" else "locked"
        with self.edit():
            setattr(o, key, not getattr(o, key))
