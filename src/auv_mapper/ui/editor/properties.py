"""Properties tab, mission-order entry and project settings."""
import tkinter as tk
from tkinter import colorchooser, ttk

from ...icons import ico
from ...kinds import KINDS
from ...scaling import sc
from ...theme import T
from ...utils import fmt
from ..style import tip


class PropertiesMixin:
    def prop_spec(self):
        s = self.selected
        if not s:
            return "", []
        if s[0] == "obj":
            o = self.proj.obj(s[1])
            k = KINDS[o.kind]
            sh = k["shape"]
            f = [("label", "Label", "s"), ("x", "X (m)", "n"), ("y", "Y (m)", "n")]
            if sh in ("gate", "bar", "rect"):
                f.append(("heading", "Heading (deg)", "n"))
            if sh != "text":
                f.append(("size", "Diameter (m)" if sh == "circle" else "Lebar (m)", "n"))
            if sh == "rect":
                f.append(("h", "Tinggi (m)", "n"))
            if sh != "text":
                f.append(("depth", "Kedalaman (m)", "n"))
            f += [("locked", "Terkunci (tidak bisa digeser)", "b"), ("hidden", "Disembunyikan", "b")]
            return f"{k['label']}  (#{o.id})", f
        if s[0] == "wp":
            return f"Waypoint {s[1] + 1}", [("x", "X (m)", "n"), ("y", "Y (m)", "n"),
                                              ("depth", "Kedalaman (m)", "n"), ("hold", "Tahan di titik (s)", "n"),
                                              ("action", "Aksi", "s")]
        return "Posisi awal AUV", [("x", "X (m)", "n"), ("y", "Y (m)", "n"),
                                    ("heading", "Heading (deg)", "n"), ("depth", "Kedalaman (m)", "n")]

    def _pbtn(self, parent, text, icon, cmd, **kw):
        b = ttk.Button(parent, text=" " + text if text else "", image=ico(icon, sc(16)), compound="left",
                       command=cmd, takefocus=False, **kw)
        return b

    def refresh_props(self):
        sig = tuple(self.sel)
        if sig == self.prop_sig and (self.prop_vars or len(sig) != 1):
            t = self.target()
            if t is not None:
                for key, (var, typ) in self.prop_vars.items():
                    val = bool(getattr(t, key)) if typ == "b" else fmt(getattr(t, key))
                    if var.get() != val:
                        var.set(val)
            return
        self.prop_sig = sig
        self._building = True
        for w in self.props_body.winfo_children():
            w.destroy()
        self.prop_vars = {}
        n = len(self.sel)
        pb = self.props_body
        if n == 0:
            ttk.Label(pb, text="Belum ada yang dipilih.\n\nKlik objek, waypoint, atau AUV di peta; seret area "
                               "kosong untuk memilih banyak sekaligus; atau pilih objek dari palet kiri lalu "
                               "klik di peta untuk menaruhnya.", style="Muted.TLabel", wraplength=sc(400),
                      justify="left").pack(anchor="w")
        elif n == 1:
            self._build_single(pb)
        else:
            self._build_multi(pb, n)
        self._building = False

    def _build_single(self, pb):
        t = self.target()
        title, fields = self.prop_spec()
        ttk.Label(pb, text=title, style="H.TLabel").pack(anchor="w", pady=(0, 8))
        grid = ttk.Frame(pb)
        grid.pack(fill="x")
        grid.columnconfigure(1, weight=1)
        r = 0
        for key, lbl, typ in fields:
            if typ == "b":
                var = tk.BooleanVar(value=bool(getattr(t, key)))
                self.prop_vars[key] = (var, typ)
                ttk.Checkbutton(grid, text=lbl, variable=var,
                                command=lambda k=key, v=var: self.apply_prop(k, v, "b")).grid(
                    row=r, column=0, columnspan=2, sticky="w", pady=2)
            else:
                ttk.Label(grid, text=lbl).grid(row=r, column=0, sticky="w", pady=3, padx=(0, 10))
                var = tk.StringVar(value=fmt(getattr(t, key)))
                self.prop_vars[key] = (var, typ)
                e = ttk.Entry(grid, textvariable=var)
                e.grid(row=r, column=1, sticky="ew")
                e.bind("<Return>", lambda ev, k=key, v=var: self.apply_prop(k, v))
                e.bind("<FocusOut>", lambda ev, k=key, v=var: self.apply_prop(k, v))
            r += 1
        s = self.selected
        if s[0] == "obj" and KINDS[t.kind]["shape"] != "gate":
            ttk.Label(grid, text="Warna").grid(row=r, column=0, sticky="w", pady=3)
            cf = ttk.Frame(grid)
            cf.grid(row=r, column=1, sticky="w")
            chip = tk.Canvas(cf, width=18, height=18, highlightthickness=0, bg=T["panel"])
            chip.create_rectangle(1, 1, 17, 17, fill=t.color or KINDS[t.kind]["color"], outline=T["border"])
            chip.pack(side="left")
            ttk.Button(cf, text="Pilih...", command=self.pick_color, takefocus=False).pack(side="left", padx=6)
            ttk.Button(cf, text="Reset", command=lambda: self.set_color(""), takefocus=False).pack(side="left")
        bt = ttk.Frame(pb)
        bt.pack(fill="x", pady=(14, 0))
        if s[0] == "obj":
            self._pbtn(bt, "Duplikat", "copy", self.duplicate).pack(side="left")
        if s[0] in ("obj", "auv"):
            self._pbtn(bt, "Putar 90", "rotate", lambda: self.rotate(90)).pack(side="left", padx=6)
        if s[0] != "auv":
            self._pbtn(bt, "Hapus", "delete", self.delete_selected).pack(side="left")

    def _build_multi(self, pb, n):
        ttk.Label(pb, text=f"{n} item terpilih", style="H.TLabel").pack(anchor="w", pady=(0, 8))
        objs = self.sel_objs()
        if len(objs) >= 2:
            ttk.Label(pb, text="RATAKAN & SEBAR", style="PSec.TLabel").pack(anchor="w", pady=(2, 4))
            row = ttk.Frame(pb)
            row.pack(anchor="w")
            for ic, md, tt in (("al_l", "l", "Rata kiri"), ("al_c", "c", "Rata tengah horizontal"),
                               ("al_r", "r", "Rata kanan"), ("al_t", "t", "Rata atas"),
                               ("al_m", "m", "Rata tengah vertikal"), ("al_b", "b", "Rata bawah"),
                               ("dist_h", "dh", "Sebar horizontal (min. 3 objek)"),
                               ("dist_v", "dv", "Sebar vertikal (min. 3 objek)")):
                b = ttk.Button(row, image=ico(ic), style="Tool.TButton", takefocus=False,
                               command=lambda m=md: self.align(m))
                b.pack(side="left", padx=1)
                tip(b, tt)
        bt = ttk.Frame(pb)
        bt.pack(fill="x", pady=(14, 0))
        if objs:
            self._pbtn(bt, "Duplikat", "copy", self.duplicate).pack(side="left")
            self._pbtn(bt, "Kunci", "lock", lambda: self.toggle_flag("locked")).pack(side="left", padx=6)
            self._pbtn(bt, "Sembunyikan", "eye", lambda: self.toggle_flag("hidden")).pack(side="left")
        bt2 = ttk.Frame(pb)
        bt2.pack(fill="x", pady=(6, 0))
        self._pbtn(bt2, "Hapus", "delete", self.delete_selected).pack(side="left")
        ttk.Label(pb, text="Seret salah satu item untuk menggeser semuanya. Shift+klik menambah / mengurangi "
                           "pilihan.", style="Muted.TLabel", wraplength=sc(400), justify="left").pack(
            anchor="w", pady=(14, 0))

    def apply_prop(self, key, var, typ="n"):
        if self._building:
            return
        t = self.target()
        if t is None or not hasattr(t, key):
            return
        cur = getattr(t, key)
        if typ == "b":
            val = bool(var.get())
        else:
            raw = var.get().strip()
            try:
                if isinstance(cur, str):
                    val = raw
                else:
                    val = float(raw.replace(",", "."))
                    if key == "x":
                        val = min(max(val, 0.0), self.proj.W)
                    elif key == "y":
                        val = min(max(val, 0.0), self.proj.H)
                    elif key == "depth":
                        val = min(max(val, 0.0), self.proj.D)
                    elif key == "heading":
                        val %= 360.0
                    elif key in ("size", "h"):
                        val = max(val, 0.05)
                    elif key == "hold":
                        val = max(val, 0.0)
            except ValueError:
                var.set(fmt(cur))
                return
        if val == cur:
            if typ != "b":
                var.set(fmt(cur))
            return
        with self.edit():
            setattr(t, key, val)

    def pick_color(self):
        t = self.target()
        if t is None:
            return
        res = colorchooser.askcolor(color=t.color or KINDS[t.kind]["color"], parent=self.app)
        if res and res[1]:
            self.set_color(res[1])

    def set_color(self, c):
        t = self.target()
        if t is not None and self.selected[0] == "obj":
            self.prop_sig = None
            with self.edit():
                t.color = c

    def apply_order(self):
        txt = self.order_var.get().strip()
        if txt != self.proj.order:
            with self.edit():
                self.proj.order = txt

    def apply_speed(self):
        try:
            v = min(max(float(self.speed_var.get().replace(",", ".")), 0.05), 10.0)
        except ValueError:
            self.speed_var.set(fmt(self.proj.speed))
            return
        if v != self.proj.speed:
            with self.edit():
                self.proj.speed = v

    def add_token(self):
        tok = self.tok_var.get()
        cur = self.order_var.get().strip()
        self.order_var.set((cur + " " + tok).strip())
        self.apply_order()

    def apply_project(self):
        try:
            vals = {}
            for _l, key, typ in self.PROJECT_FIELDS:
                raw = self.proj_vars[key].get().strip()
                vals[key] = raw if typ == "s" else float(raw.replace(",", "."))
            if not vals["name"]:
                raise ValueError("Nama tidak boleh kosong.")
            if not (2 <= vals["W"] <= 500 and 2 <= vals["H"] <= 500):
                raise ValueError("Ukuran kolam harus 2-500 m.")
            if vals["D"] <= 0:
                raise ValueError("Kedalaman harus > 0.")
            if not (0 <= vals["qual"] < vals["W"]):
                raise ValueError("Lebar area qual harus 0 sampai < panjang kolam.")
            if vals["grid_minor"] <= 0 or vals["grid_major"] < vals["grid_minor"] or vals["snap_step"] <= 0:
                raise ValueError("Grid minor/snap harus > 0 dan grid major >= grid minor.")
        except ValueError as ex:
            msg = str(ex)
            self.proj_err.config(text=msg if msg.endswith(".") else "Isi angka yang valid.")
            return
        self.proj_err.config(text="")
        with self.edit():
            for key, v in vals.items():
                setattr(self.proj, key, v)
        self.fit(True)
        self.say("Pengaturan proyek diterapkan")
