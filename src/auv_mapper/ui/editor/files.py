"""File operations: save / autosave and CSV / JSON / SVG / clipboard export."""
import csv
import json
import os
from dataclasses import asdict
from tkinter import filedialog, messagebox

from ...constants import AUTOSAVE_MS, DEFAULT_PROJECT_DIR, EXT
from ...render.scene import draw_hud, draw_scene
from ...render.sinks import SvgSink
from ...theme import LIGHT
from ...utils import slug


class FileMixin:
    def autosave_path(self):
        return (self.path or os.path.join(DEFAULT_PROJECT_DIR, slug(self.proj.name) + EXT)) + ".autosave"

    def autosave(self):
        self._auto_job = self.after(AUTOSAVE_MS, self.autosave)
        if not self.is_dirty():
            return
        try:
            p = self.autosave_path()
            os.makedirs(os.path.dirname(p), exist_ok=True)
            self.proj.save(p, touch=False)
        except OSError:
            pass

    def clear_autosave(self):
        try:
            os.remove(self.autosave_path())
        except OSError:
            pass

    def save(self, as_new=False):
        path = self.path
        if as_new or not path:
            path = filedialog.asksaveasfilename(
                parent=self.app, defaultextension=EXT, filetypes=[("AUV Map project", "*" + EXT)],
                initialdir=os.path.dirname(self.path) if self.path else DEFAULT_PROJECT_DIR,
                initialfile=os.path.basename(self.path) if self.path else slug(self.proj.name) + EXT)
            if not path:
                return False
        try:
            self.proj.save(path)
        except OSError as ex:
            messagebox.showerror("Gagal menyimpan", str(ex), parent=self.app)
            return False
        self.clear_autosave()
        self.path = path
        self.saved_state = self.proj.state()
        self.app.recent.add(path, self.proj.name)
        self.update_title()
        self.say(f"Tersimpan: {path}")
        return True

    def _ask_out(self, ext, label, suffix):
        base = os.path.splitext(self.path or slug(self.proj.name))[0] + suffix + ext
        return filedialog.asksaveasfilename(parent=self.app, defaultextension=ext, initialfile=os.path.basename(base),
                                            initialdir=os.path.dirname(base) or None, filetypes=[(label, "*" + ext)])

    def export_csv(self):
        rows = self.proj.segments()
        if not rows:
            self.say("Belum ada waypoint untuk diekspor.")
            return
        out = self._ask_out(".csv", "CSV", "_waypoints")
        if not out:
            return
        try:
            with open(out, "w", newline="", encoding="utf-8") as f:
                wr = csv.writer(f)
                wr.writerow(["idx", "x_m", "y_m", "depth_m", "action", "hold_s", "bearing_map_deg",
                             "bearing_compass_deg", "dist_m", "turn_deg", "cum_dist_m", "eta_s"])
                for r in rows:
                    wr.writerow([r["idx"], f"{r['x']:.3f}", f"{r['y']:.3f}", f"{r['depth']:.2f}", r["action"],
                                 f"{r['hold']:.1f}", f"{r['bearing']:.1f}",
                                 f"{(r['bearing'] + self.proj.north_offset) % 360:.1f}", f"{r['dist']:.3f}",
                                 f"{r['turn']:.1f}", f"{r['cum']:.3f}", f"{r['eta']:.1f}"])
        except OSError as ex:
            messagebox.showerror("Gagal ekspor", str(ex), parent=self.app)
            return
        self.say(f"CSV diekspor: {out}")

    def export_json(self):
        rows = self.proj.segments()
        if not rows:
            self.say("Belum ada waypoint untuk diekspor.")
            return
        out = self._ask_out(".json", "JSON", "_mission")
        if not out:
            return
        p = self.proj
        data = {"project": p.name, "pool": {"width": p.W, "height": p.H, "depth": p.D},
                "start": asdict(p.auv), "speed_mps": p.speed, "north_offset_deg": p.north_offset,
                "total_distance_m": round(rows[-1]["cum"], 3), "estimated_time_s": round(rows[-1]["eta"], 1),
                "waypoints": [dict(idx=r["idx"], x=round(r["x"], 3), y=round(r["y"], 3), depth=r["depth"],
                                   action=r["action"], hold_s=r["hold"], bearing_map_deg=round(r["bearing"], 1),
                                   bearing_compass_deg=round((r["bearing"] + p.north_offset) % 360, 1),
                                   dist_m=round(r["dist"], 3), turn_deg=round(r["turn"], 1)) for r in rows]}
        try:
            with open(out, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except OSError as ex:
            messagebox.showerror("Gagal ekspor", str(ex), parent=self.app)
            return
        self.say(f"JSON misi diekspor: {out}")

    def copy_table(self):
        rows = self.proj.segments()
        if not rows:
            self.say("Belum ada waypoint.")
            return
        lines = ["idx\tx\ty\tdepth\taction\thold\tbearing\tdist\tturn"]
        for r in rows:
            lines.append(f"{r['idx']}\t{r['x']:.2f}\t{r['y']:.2f}\t{r['depth']:.2f}\t{r['action']}\t"
                         f"{r['hold']:.1f}\t{r['bearing']:.0f}\t{r['dist']:.2f}\t{r['turn']:+.0f}")
        self.app.clipboard_clear()
        self.app.clipboard_append("\n".join(lines))
        self.say("Tabel waypoint disalin ke clipboard (tempel ke Excel / Sheets).")

    def export_svg(self):
        out = self._ask_out(".svg", "SVG", "")
        if not out:
            return
        s = 24.0
        w, h = self.proj.W * s + 130, self.proj.H * s + 120
        sink = SvgSink(w, h, "#ffffff")
        light = dict(LIGHT, canvas="#ffffff")
        draw_scene(sink, self.proj, (s, 62.0, 66.0 + self.proj.H * s), light, grid=True, labels=True, axis=True,
                   selected=())
        draw_hud(sink, w, h, s, light)
        try:
            with open(out, "w", encoding="utf-8") as f:
                f.write(sink.render())
        except OSError as ex:
            messagebox.showerror("Gagal ekspor", str(ex), parent=self.app)
            return
        self.say(f"SVG diekspor: {out}")
