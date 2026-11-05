"""Widget construction for the editor screen (toolbar, palette, side tabs, status bar)."""
import tkinter as tk
from tkinter import ttk

from ...constants import IS_MAC, MOD
from ...icons import ico, states
from ...kinds import GROUPS, KINDS, TOKEN_CHOICES
from ...scaling import sc
from ...theme import F, T
from ..style import tip


class LayoutMixin:
    def _sep(self, tb):
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=6, pady=3)

    def _btn(self, tb, icon, text, accel, cmd, disabled_icon=False):
        b = ttk.Button(tb, image=states(icon, disabled=disabled_icon), style="Tool.TButton", command=cmd,
                       takefocus=False)
        b.pack(side="left", padx=1)
        return tip(b, text, accel)

    def _radio(self, tb, icon, text, accel, val):
        r = ttk.Radiobutton(tb, image=states(icon, selected=True), value=val, variable=self.tool_var,
                            style="Tool.Toolbutton", takefocus=False)
        r.pack(side="left", padx=1)
        return tip(r, text, accel)

    def _check(self, tb, icon, text, accel, var, cmd):
        c = ttk.Checkbutton(tb, image=states(icon, selected=True), variable=var, style="Tool.Toolbutton",
                            command=cmd, takefocus=False)
        c.pack(side="left", padx=1)
        return tip(c, text, accel)

    def _build_toolbar(self):
        tb = ttk.Frame(self, style="Bar.TFrame", padding=(8, 5))
        tb.grid(row=0, column=0, sticky="ew")
        self._btn(tb, "home", "Beranda", f"{MOD}+W", self.app.show_home)
        self._btn(tb, "new", "Proyek baru", f"{MOD}+N", self.app.new_dialog)
        self._btn(tb, "open", "Buka proyek", f"{MOD}+O", self.app.open_dialog)
        self._btn(tb, "save", "Simpan", f"{MOD}+S", lambda: self.save())
        self._sep(tb)
        self.btn_undo = self._btn(tb, "undo", "Undo", f"{MOD}+Z", self.do_undo, True)
        self.btn_redo = self._btn(tb, "redo", "Redo", f"{MOD}+Y", self.do_redo, True)
        self._btn(tb, "cut", "Potong", f"{MOD}+X", self.cut)
        self._btn(tb, "copy", "Salin", f"{MOD}+C", self.copy_sel)
        self._btn(tb, "paste", "Tempel", f"{MOD}+V", self.paste)
        self._sep(tb)
        self._radio(tb, "select", "Pilih / geser", "V", "select")
        self._radio(tb, "pan", "Tangan (geser tampilan)", "H / tahan Spasi", "pan")
        self._radio(tb, "waypoint", "Tambah waypoint", "W", "waypoint")
        self._radio(tb, "auv", "Posisi awal AUV", "A", "auv")
        self._radio(tb, "measure", "Ukur jarak & bearing", "M", "measure")
        self._sep(tb)
        self._check(tb, "grid", "Tampilkan grid", "G", self.grid_on, self.redraw)
        self._check(tb, "snap", "Snap ke grid", "N", self.snap_on, self.redraw)
        self._check(tb, "label", "Tampilkan label", "L", self.labels_on, self.redraw)
        self._btn(tb, "zoomin", "Perbesar", f"{MOD}++", lambda: self.zoom(1.25))
        self._btn(tb, "zoomout", "Perkecil", f"{MOD}+-", lambda: self.zoom(1 / 1.25))
        self._btn(tb, "fit", "Fit ke kolam", f"{MOD}+0", lambda: self.fit(True))
        self._sep(tb)
        self._btn(tb, "plan", "Generate waypoint dari urutan misi", "P", self.do_plan)
        self._btn(tb, "check", "Validasi misi", "F6", self.run_validate)
        self.btn_play = self._btn(tb, "play", "Simulasi: play / pause", "F5", self.toggle_sim)
        self._btn(tb, "stop", "Hentikan simulasi", "Shift+F5", self.stop_sim)
        ttk.Button(tb, text=" Simpan", style="Accent.TButton", command=lambda: self.save(), takefocus=False,
                   image=ico("save", fg="#ffffff", accent="#ffffff"), compound="left").pack(side="right")
        b = ttk.Button(tb, image=ico("theme"), style="Tool.TButton", command=self.app.toggle_theme, takefocus=False)
        b.pack(side="right", padx=6)
        tip(b, "Ganti tema gelap / terang")
        b = ttk.Button(tb, image=ico("help"), style="Tool.TButton", command=self.app.show_help, takefocus=False)
        b.pack(side="right")
        tip(b, "Bantuan & shortcut", "F1")

    def _build(self):
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_toolbar()
        self.pw = ttk.PanedWindow(self, orient="horizontal")
        self.pw.grid(row=1, column=0, sticky="nsew")
        left = ttk.Frame(self.pw, width=sc(200), padding=(8, 8))
        left.pack_propagate(False)
        self._build_palette(left)
        mid = ttk.Frame(self.pw, style="Bg.TFrame")
        self.canvas = tk.Canvas(mid, bg=T["canvas"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        right = ttk.Frame(self.pw, width=sc(450))
        right.pack_propagate(False)
        self.pw.add(left, weight=0)
        self.pw.add(mid, weight=1)
        self.pw.add(right, weight=0)
        c = self.canvas
        c.bind("<Configure>", self.on_configure)
        c.bind("<ButtonPress-1>", self.on_press)
        c.bind("<B1-Motion>", self.on_drag)
        c.bind("<ButtonRelease-1>", self.on_release)
        c.bind("<Motion>", self.on_motion)
        c.bind("<Leave>", lambda e: c.delete("ghost"))
        mid_btn = "3" if IS_MAC else "2"
        c.bind(f"<ButtonPress-{mid_btn}>", self.on_pan_start)
        c.bind(f"<B{mid_btn}-Motion>", self.on_pan_move)
        c.bind(f"<ButtonRelease-{mid_btn}>", lambda e: self.end_pan())
        c.bind("<ButtonPress-2>" if IS_MAC else "<ButtonPress-3>", self.on_context)
        if IS_MAC:
            c.bind("<Control-ButtonPress-1>", self.on_context)
        c.bind("<MouseWheel>", self.on_wheel)
        c.bind("<Button-4>", self.on_wheel)
        c.bind("<Button-5>", self.on_wheel)
        self.nb = ttk.Notebook(right)
        self.nb.pack(fill="both", expand=True)
        self.tab_props = ttk.Frame(self.nb, padding=12)
        self.tab_mission = ttk.Frame(self.nb, padding=10)
        self.tab_objects = ttk.Frame(self.nb, padding=8)
        self.tab_check = ttk.Frame(self.nb, padding=8)
        self.tab_project = ttk.Frame(self.nb, padding=12)
        self.nb.add(self.tab_props, text="Properti")
        self.nb.add(self.tab_mission, text="Misi")
        self.nb.add(self.tab_objects, text="Objek")
        self.nb.add(self.tab_check, text="Cek")
        self.nb.add(self.tab_project, text="Proyek")
        self.props_body = ttk.Frame(self.tab_props)
        self.props_body.pack(fill="both", expand=True)
        self._build_mission()
        self._build_objects()
        self._build_check()
        self._build_project_tab()
        sb = ttk.Frame(self, style="Bar.TFrame", padding=(10, 4))
        sb.grid(row=2, column=0, sticky="ew")
        self.sv_coord, self.sv_hint, self.sv_info = tk.StringVar(), tk.StringVar(), tk.StringVar()
        ttk.Label(sb, textvariable=self.sv_coord, style="BarB.TLabel", width=24).pack(side="left")
        ttk.Label(sb, textvariable=self.sv_info, style="Bar.TLabel").pack(side="right")
        ttk.Label(sb, textvariable=self.sv_hint, style="Bar.TLabel").pack(side="left", padx=12)
        self.tool_var.trace_add("write", lambda *a: self.on_tool_change())
        self.on_tool_change()
        self.ctx = tk.Menu(self, tearoff=0)

    def _build_palette(self, left):
        ttk.Label(left, text="PALET OBJEK", style="PSec.TLabel").pack(anchor="w")
        self.pal_filter = tk.StringVar()
        e = ttk.Entry(left, textvariable=self.pal_filter)
        e.pack(fill="x", pady=(4, 2))
        tip(e, "Cari objek di palet")
        self.pal_filter.trace_add("write", lambda *a: self.fill_palette())
        self.pal_body = ttk.Frame(left)
        self.pal_body.pack(fill="both", expand=True)
        self.fill_palette()

    def fill_palette(self):
        for w in self.pal_body.winfo_children():
            w.destroy()
        q = self.pal_filter.get().strip().lower()
        for g in GROUPS:
            kinds = [(kind, k) for kind, k in KINDS.items()
                     if k["group"] == g and (not q or q in k["label"].lower() or q in g.lower())]
            if not kinds:
                continue
            ttk.Label(self.pal_body, text=g.upper(), style="PSec.TLabel").pack(anchor="w", pady=(8, 1))
            for kind, k in kinds:
                row = ttk.Frame(self.pal_body)
                row.pack(fill="x", pady=0)
                chip = tk.Canvas(row, width=14, height=14, bg=T["panel"], highlightthickness=0)
                chip.pack(side="left", padx=(2, 6))
                if k["shape"] == "circle":
                    chip.create_oval(2, 2, 13, 13, fill=k["color"], outline="")
                elif k["shape"] == "text":
                    chip.create_text(7, 7, text="T", fill=k["color"], font=F(9, True))
                elif k["shape"] in ("gate", "bar"):
                    chip.create_rectangle(1, 5, 14, 9, fill=k["color"], outline="")
                else:
                    chip.create_rectangle(2, 2, 13, 13, fill=k["color"], outline="")
                ttk.Radiobutton(row, text=k["label"], value="obj:" + kind, variable=self.tool_var,
                                style="Palette.Toolbutton", takefocus=False).pack(side="left", fill="x", expand=True)

    def _build_mission(self):
        f = self.tab_mission
        ttk.Label(f, text="Urutan misi", style="H.TLabel").pack(anchor="w")
        ttk.Label(f, text="Token dipisah spasi. Contoh: orange gate yellow red blue drum_blue surface",
                  style="Muted.TLabel", wraplength=sc(400), justify="left").pack(anchor="w", pady=(2, 6))
        self.order_var = tk.StringVar()
        e = ttk.Entry(f, textvariable=self.order_var)
        e.pack(fill="x")
        e.bind("<Return>", lambda ev: self.apply_order())
        e.bind("<FocusOut>", lambda ev: self.apply_order())
        row = ttk.Frame(f)
        row.pack(fill="x", pady=6)
        self.tok_var = tk.StringVar(value=TOKEN_CHOICES[0])
        ttk.Combobox(row, textvariable=self.tok_var, values=TOKEN_CHOICES, width=14, state="readonly").pack(side="left")
        ttk.Button(row, text=" Tambah", image=ico("plus", sc(14)), compound="left", command=self.add_token,
                   takefocus=False).pack(side="left", padx=4)
        ttk.Button(row, text=" Generate", style="Accent.TButton", image=ico("plan", fg="#ffffff", accent="#ffffff"),
                   compound="left", command=self.do_plan, takefocus=False).pack(side="right")
        row2 = ttk.Frame(f)
        row2.pack(fill="x", pady=(2, 6))
        ttk.Label(row2, text="Kecepatan (m/s)").pack(side="left")
        self.speed_var = tk.StringVar()
        sp = ttk.Spinbox(row2, from_=0.1, to=3.0, increment=0.1, textvariable=self.speed_var, width=5)
        sp.pack(side="left", padx=6)
        sp.bind("<Return>", lambda ev: self.apply_speed())
        sp.bind("<FocusOut>", lambda ev: self.apply_speed())
        sp.bind("<<Increment>>", lambda ev: self.after_idle(self.apply_speed))
        sp.bind("<<Decrement>>", lambda ev: self.after_idle(self.apply_speed))
        self.mult_var = tk.StringVar(value="1x")
        mc = ttk.Combobox(row2, textvariable=self.mult_var, values=["0.5x", "1x", "2x", "4x", "8x"], width=4,
                          state="readonly")
        mc.pack(side="right")
        mc.bind("<<ComboboxSelected>>", lambda ev: setattr(self, "sim_mult", float(self.mult_var.get()[:-1])))
        tip(mc, "Kecepatan simulasi")
        b = ttk.Button(row2, image=ico("stop"), style="Tool.TButton", command=self.stop_sim, takefocus=False)
        b.pack(side="right", padx=2)
        tip(b, "Stop simulasi", "Shift+F5")
        self.btn_play2 = ttk.Button(row2, image=ico("play"), style="Tool.TButton", command=self.toggle_sim,
                                    takefocus=False)
        self.btn_play2.pack(side="right")
        tip(self.btn_play2, "Play / pause simulasi", "F5")
        cols = ("n", "x", "y", "z", "aksi", "brg", "jrk", "blk", "t")
        heads = ("#", "x", "y", "z", "Aksi", "Brg", "Jrk", "Blk", "ETA")
        widths = (26, 42, 42, 32, 92, 40, 40, 42, 40)
        self.tree = ttk.Treeview(f, columns=cols, show="headings", selectmode="browse", height=9)
        for c, h, w in zip(cols, heads, widths):
            self.tree.heading(c, text=h, anchor="w")
            self.tree.column(c, width=w, anchor="w", stretch=(c == "aksi"))
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        row3 = ttk.Frame(f)
        row3.pack(fill="x", pady=(6, 0))
        for icon, tt, cmd in (("up", "Naikkan waypoint", lambda: self.move_wp(-1)),
                              ("down", "Turunkan waypoint", lambda: self.move_wp(1)),
                              ("delete", "Hapus terpilih", self.delete_selected),
                              ("csv", "Ekspor CSV", self.export_csv),
                              ("json", "Ekspor JSON misi", self.export_json),
                              ("copy", "Salin tabel ke clipboard", self.copy_table)):
            b = ttk.Button(row3, image=ico(icon), style="Tool.TButton", command=cmd, takefocus=False)
            b.pack(side="left", padx=1)
            tip(b, tt)
        ttk.Button(row3, text="Kosongkan", command=self.clear_wps, takefocus=False).pack(side="right")
        self.prof = tk.Canvas(f, height=sc(92), bg=T["panel2"], highlightthickness=0)
        self.prof.pack(fill="x", pady=(8, 0))
        self.prof.bind("<Configure>", lambda e: self.draw_profile())
        self.lbl_stats = ttk.Label(f, text="", style="Muted.TLabel", wraplength=sc(400), justify="left")
        self.lbl_stats.pack(anchor="w", pady=(6, 0))

    def _build_objects(self):
        f = self.tab_objects
        cols = ("id", "nama", "x", "y", "vis", "lock")
        heads = ("#", "Nama", "x", "y", "Tampil", "Kunci")
        widths = (32, 140, 46, 46, 52, 46)
        self.otree = ttk.Treeview(f, columns=cols, show="headings", selectmode="extended")
        for c, h, w in zip(cols, heads, widths):
            self.otree.heading(c, text=h, anchor="w")
            self.otree.column(c, width=w, anchor="w", stretch=(c == "nama"))
        self.otree.pack(fill="both", expand=True)
        self.otree.bind("<<TreeviewSelect>>", self.on_otree_select)
        self.otree.bind("<ButtonRelease-1>", self.on_obj_click)
        ttk.Label(f, text="Klik kolom Tampil / Kunci untuk mengubah. Objek terkunci tidak bisa digeser; "
                          "objek tersembunyi tidak ikut tergambar dan terekspor.", style="Muted.TLabel",
                  wraplength=sc(400), justify="left").pack(anchor="w", pady=(6, 0))

    def _build_check(self):
        f = self.tab_check
        self.lbl_check = ttk.Label(f, text="", style="H.TLabel")
        self.lbl_check.pack(anchor="w", pady=(0, 6))
        self.ctree = ttk.Treeview(f, show="tree", selectmode="browse")
        self.ctree.column("#0", width=380, stretch=True)
        self.ctree.pack(fill="both", expand=True)
        self.ctree.bind("<<TreeviewSelect>>", self.on_issue_select)
        ttk.Label(f, text="Klik masalah untuk menyorot objek / waypoint terkait. Pengecekan berjalan otomatis "
                          "setiap ada perubahan.", style="Muted.TLabel", wraplength=sc(400),
                  justify="left").pack(anchor="w", pady=(6, 0))

    def _build_project_tab(self):
        f = self.tab_project
        ttk.Label(f, text="Pengaturan proyek & kolam", style="H.TLabel").grid(row=0, column=0, columnspan=2,
                                                                                sticky="w", pady=(0, 8))
        self.proj_vars = {}
        for i, (lbl, key, _t) in enumerate(self.PROJECT_FIELDS, 1):
            ttk.Label(f, text=lbl).grid(row=i, column=0, sticky="w", pady=3, padx=(0, 10))
            v = tk.StringVar()
            self.proj_vars[key] = v
            e = ttk.Entry(f, textvariable=v, width=18)
            e.grid(row=i, column=1, sticky="ew")
            e.bind("<Return>", lambda ev: self.apply_project())
        f.columnconfigure(1, weight=1)
        n = len(self.PROJECT_FIELDS) + 1
        self.proj_err = ttk.Label(f, text="", style="Err.TLabel", wraplength=sc(400), justify="left")
        self.proj_err.grid(row=n, column=0, columnspan=2, sticky="w", pady=(6, 0))
        ttk.Button(f, text="Terapkan", style="Accent.TButton", command=self.apply_project, takefocus=False).grid(
            row=n + 1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        ttk.Label(f, text="Mengubah ukuran kolam tidak memindahkan objek; objek di luar batas tetap tersimpan "
                          "dan ditandai di tab Cek.", style="Muted.TLabel", wraplength=sc(400),
                  justify="left").grid(row=n + 2, column=0, columnspan=2, sticky="w", pady=(12, 0))
