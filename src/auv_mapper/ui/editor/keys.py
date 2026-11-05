"""Keyboard shortcuts for the editor screen."""
import tkinter as tk
from tkinter import ttk


class KeyboardMixin:
    def in_text_entry(self):
        try:
            w = self.app.focus_get()
        except (KeyError, tk.TclError):
            return False
        return isinstance(w, (tk.Entry, ttk.Entry, ttk.Combobox, ttk.Spinbox, tk.Text))

    def on_key(self, e, k, ctrl, shift):
        typing = self.in_text_entry()
        if k == "f5":
            self.stop_sim() if shift else self.toggle_sim()
            return
        if k == "f6":
            self.run_validate()
            return
        if ctrl:
            if typing and k in ("a", "c", "v", "x", "z", "y", "d", "e", "l", "h"):
                return
            acts = {"z": self.do_redo if shift else self.do_undo, "y": self.do_redo, "x": self.cut,
                    "c": self.copy_sel, "v": self.paste, "a": self.select_all, "d": self.duplicate,
                    "s": (lambda: self.save(as_new=shift)), "o": self.app.open_dialog, "n": self.app.new_dialog,
                    "w": self.app.show_home, "e": (self.export_svg if shift else self.export_csv),
                    "l": (lambda: self.toggle_flag("locked")), "h": (lambda: self.toggle_flag("hidden")),
                    "0": (lambda: self.fit(True)), "q": self.app.on_close,
                    "return": self.do_plan, "kp_enter": self.do_plan}
            if k in acts:
                acts[k]()
            elif k in ("plus", "equal", "kp_add"):
                self.zoom(1.25)
            elif k in ("minus", "kp_subtract", "underscore"):
                self.zoom(1 / 1.25)
            return
        if typing:
            return
        tools = {"v": "select", "h": "pan", "w": "waypoint", "a": "auv", "m": "measure"}
        if k in tools:
            self.tool_var.set(tools[k])
        elif k == "escape":
            if self.measure:
                self.measure = None
                self.draw_measure()
            elif self.tool_var.get() != "select":
                self.tool_var.set("select")
            else:
                self.set_sel([])
        elif k in ("delete", "backspace"):
            self.delete_selected()
        elif k == "r":
            self.rotate(-15 if shift else 15)
        elif k in ("plus", "equal", "kp_add"):
            self.adjust("size", 0.1, 0.05, 500)
        elif k in ("minus", "kp_subtract"):
            self.adjust("size", -0.1, 0.05, 500)
        elif k == "bracketright":
            self.adjust("depth", 0.1, 0.0, self.proj.D)
        elif k == "bracketleft":
            self.adjust("depth", -0.1, 0.0, self.proj.D)
        elif k in ("left", "right", "up", "down"):
            dx, dy = {"left": (-1, 0), "right": (1, 0), "up": (0, 1), "down": (0, -1)}[k]
            self.nudge(dx, dy, 5 if shift else 1)
        elif k == "g":
            self.grid_on.set(not self.grid_on.get())
            self.redraw()
        elif k == "n":
            self.snap_on.set(not self.snap_on.get())
            self.redraw()
            self.update_status()
        elif k == "l":
            self.labels_on.set(not self.labels_on.get())
            self.redraw()
        elif k == "f":
            self.fit(True)
        elif k == "p":
            self.do_plan()
