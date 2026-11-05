"""Start screen: recent projects list with live preview."""
import os
import time
import tkinter as tk
from tkinter import ttk

from ..constants import APP_NAME, APP_VERSION, IS_MAC, MOD
from ..geometry import fit_view
from ..icons import ico
from ..model import Project
from ..render.scene import draw_scene
from ..render.sinks import TkSink
from ..scaling import sc
from ..theme import F, T


class Home(ttk.Frame):
    def __init__(self, app):
        super().__init__(app, style="Bg.TFrame")
        self.app = app
        self.cache = {}
        left = ttk.Frame(self, style="Bg.TFrame")
        left.pack(side="left", fill="both", expand=True, padx=(44, 20), pady=34)
        head = ttk.Frame(left, style="Bg.TFrame")
        head.pack(anchor="w", fill="x")
        self.logo = ico("app", sc(52))
        tk.Label(head, image=self.logo, bg=T["bg"], bd=0).pack(side="left", padx=(0, 14))
        tb = ttk.Frame(head, style="Bg.TFrame")
        tb.pack(side="left")
        ttk.Label(tb, text=APP_NAME, style="Title.TLabel").pack(anchor="w")
        ttk.Label(tb, text="Rancang arena kolam, taruh objek, dan susun strategi waypoint AUV.",
                  style="Sub.TLabel").pack(anchor="w")
        row = ttk.Frame(left, style="Bg.TFrame")
        row.pack(anchor="w", pady=(22, 0))
        ttk.Button(row, text=" Proyek Baru", style="Accent.TButton", command=app.new_dialog, takefocus=False,
                   image=ico("new", fg="#ffffff", accent="#ffffff"), compound="left").pack(side="left")
        ttk.Button(row, text=" Buka Proyek...", command=app.open_dialog, takefocus=False,
                   image=ico("open"), compound="left").pack(side="left", padx=8)
        ttk.Label(left, text="PROYEK TERAKHIR", style="Sec.TLabel").pack(anchor="w", pady=(28, 6))
        box = ttk.Frame(left, style="Bg.TFrame")
        box.pack(fill="both", expand=True)
        cols = ("name", "pool", "mod")
        self.tree = ttk.Treeview(box, columns=cols, show="headings", selectmode="browse")
        for c, t, w in (("name", "Nama", 230), ("pool", "Kolam", 110), ("mod", "Diubah", 140)):
            self.tree.heading(c, text=t, anchor="w")
            self.tree.column(c, width=w, anchor="w")
        sb = ttk.Scrollbar(box, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", lambda e: self.show_preview())
        self.tree.bind("<Double-1>", lambda e: self.open_selected())
        self.tree.bind("<Button-3>", self.on_menu)
        if IS_MAC:
            self.tree.bind("<Button-2>", self.on_menu)
        foot = ttk.Frame(left, style="Bg.TFrame")
        foot.pack(fill="x", pady=(14, 0))
        ttk.Label(foot, text=f"{MOD}+N proyek baru   {MOD}+O buka   F1 bantuan   |   v{APP_VERSION}",
                  style="BgMuted.TLabel").pack(side="left")
        ttk.Button(foot, text=" Tema", command=app.toggle_theme, takefocus=False, image=ico("theme"),
                   compound="left").pack(side="right")

        right = ttk.Frame(self, style="Card.TFrame", width=sc(480))
        right.pack(side="right", fill="y", padx=(0, 44), pady=34)
        right.pack_propagate(False)
        self.pv = tk.Canvas(right, bg=T["canvas"], highlightthickness=0, height=sc(290))
        self.pv.pack(fill="x", padx=14, pady=(14, 10))
        self.pv.bind("<Configure>", lambda e: self.show_preview())
        self.l_name = ttk.Label(right, text="", style="CardH.TLabel")
        self.l_name.pack(anchor="w", padx=16)
        self.l_info = ttk.Label(right, text="", style="Card.TLabel", justify="left")
        self.l_info.pack(anchor="w", padx=16, pady=(6, 0))
        self.l_path = ttk.Label(right, text="", style="CardMuted.TLabel", wraplength=sc(440), justify="left")
        self.l_path.pack(anchor="w", padx=16, pady=(6, 0))
        self.btn_open = ttk.Button(right, text="Buka Proyek", style="Accent.TButton", command=self.open_selected,
                                   takefocus=False)
        self.btn_open.pack(anchor="w", padx=16, pady=(14, 4))
        self.btn_rm = ttk.Button(right, text="Hapus dari daftar", command=self.remove_selected, takefocus=False)
        self.btn_rm.pack(anchor="w", padx=16)
        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Buka", command=self.open_selected)
        self.menu.add_command(label="Hapus dari daftar", command=self.remove_selected)
        self.refresh()

    def _info(self, path):
        if path in self.cache:
            return self.cache[path]
        try:
            proj = Project.load(path)
            info = dict(proj=proj, mtime=os.path.getmtime(path))
        except (OSError, ValueError, KeyError, TypeError):
            info = dict(proj=None, mtime=None)
        self.cache[path] = info
        return info

    def refresh(self):
        self.cache.clear()
        self.tree.delete(*self.tree.get_children())
        for i, it in enumerate(self.app.recent.items):
            info = self._info(it["path"])
            p = info["proj"]
            if p is None:
                vals = (it.get("name", os.path.basename(it["path"])) + "  (file hilang)", "-", "-")
            else:
                vals = (p.name, f"{p.W:g} x {p.H:g} m",
                        time.strftime("%d %b %Y %H:%M", time.localtime(info["mtime"])))
            self.tree.insert("", "end", iid=str(i), values=vals)
        kids = self.tree.get_children()
        if kids:
            self.tree.selection_set(kids[0])
        self.show_preview()

    def selected_item(self):
        sel = self.tree.selection()
        if not sel:
            return None
        return self.app.recent.items[int(sel[0])]

    def show_preview(self):
        c = self.pv
        c.delete("all")
        it = self.selected_item()
        w, h = max(c.winfo_width(), 50), max(c.winfo_height(), 50)
        if it is None:
            c.create_text(w / 2, h / 2, text="Belum ada proyek.\nBuat proyek baru untuk memulai.",
                          fill=T["muted"], font=F(11), justify="center")
            self.l_name.config(text="")
            self.l_info.config(text="")
            self.l_path.config(text="")
            self.btn_open.state(["disabled"])
            self.btn_rm.state(["disabled"])
            return
        self.btn_rm.state(["!disabled"])
        info = self._info(it["path"])
        p = info["proj"]
        self.l_path.config(text=it["path"])
        if p is None:
            c.create_text(w / 2, h / 2, text="File proyek tidak ditemukan\natau rusak.", fill=T["danger"],
                          font=F(11), justify="center")
            self.l_name.config(text=it.get("name", ""))
            self.l_info.config(text="")
            self.btn_open.state(["disabled"])
            return
        self.btn_open.state(["!disabled"])
        v = fit_view(p.W, p.H, w, h, 14, 14, 14, 14)
        draw_scene(TkSink(c, "pv"), p, v, T, grid=True, labels=False, axis=False, preview=True)
        self.l_name.config(text=p.name)
        self.l_info.config(text=f"Kolam {p.W:g} x {p.H:g} m, kedalaman {p.D:g} m\n"
                                f"{len(p.objects)} objek  |  {len(p.waypoints)} waypoint")

    def open_selected(self):
        it = self.selected_item()
        if it and self._info(it["path"])["proj"] is not None:
            self.app.open_path(it["path"])

    def remove_selected(self):
        it = self.selected_item()
        if it:
            self.app.recent.remove(it["path"])
            self.refresh()

    def on_menu(self, e):
        iid = self.tree.identify_row(e.y)
        if iid:
            self.tree.selection_set(iid)
            self.menu.tk_popup(e.x_root, e.y_root)

    def on_key(self, e, k, ctrl, shift):
        if ctrl and k == "n":
            self.app.new_dialog()
        elif ctrl and k == "o":
            self.app.open_dialog()
        elif k in ("return", "kp_enter"):
            self.open_selected()
        elif k == "delete":
            self.remove_selected()
