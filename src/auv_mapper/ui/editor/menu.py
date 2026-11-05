"""Menu bar and context-menu helpers."""
import tkinter as tk

from ...constants import APP_NAME, IS_MAC, IS_WIN, MOD
from ...icons import ico
from ...scaling import sc
from ...theme import T


class MenuMixin:
    def _mi(self, m, label, icon=None, accel="", cmd=None):
        kw = dict(label=label, command=cmd)
        if accel:
            kw["accelerator"] = accel
        if icon and not IS_MAC:
            fg = "#333333" if IS_WIN else T["text"]
            kw.update(image=ico(icon, sc(16), fg=fg, accent=T["accent"]), compound="left")
        m.add_command(**kw)

    def build_menu(self):
        m = tk.Menu(self.app, tearoff=0)
        f = tk.Menu(m, tearoff=0)
        self._mi(f, "Proyek Baru...", "new", f"{MOD}+N", self.app.new_dialog)
        self._mi(f, "Buka...", "open", f"{MOD}+O", self.app.open_dialog)
        rm = tk.Menu(f, tearoff=0, postcommand=lambda: self.app.fill_recent_menu(rm))
        f.add_cascade(label="Buka Terbaru", menu=rm)
        f.add_separator()
        self._mi(f, "Simpan", "save", f"{MOD}+S", self.save)
        self._mi(f, "Simpan Sebagai...", "save", f"{MOD}+Shift+S", lambda: self.save(True))
        f.add_separator()
        self._mi(f, "Ekspor CSV waypoint...", "csv", f"{MOD}+E", self.export_csv)
        self._mi(f, "Ekspor JSON misi...", "json", "", self.export_json)
        self._mi(f, "Ekspor gambar SVG...", "svg", f"{MOD}+Shift+E", self.export_svg)
        f.add_separator()
        self._mi(f, "Tutup ke Beranda", "home", f"{MOD}+W", self.app.show_home)
        self._mi(f, "Keluar", None, f"{MOD}+Q", self.app.on_close)
        m.add_cascade(label="Berkas", menu=f)
        e = tk.Menu(m, tearoff=0)
        self._mi(e, "Undo", "undo", f"{MOD}+Z", self.do_undo)
        self._mi(e, "Redo", "redo", f"{MOD}+Y", self.do_redo)
        e.add_separator()
        self._mi(e, "Potong", "cut", f"{MOD}+X", self.cut)
        self._mi(e, "Salin", "copy", f"{MOD}+C", self.copy_sel)
        self._mi(e, "Tempel", "paste", f"{MOD}+V", self.paste)
        self._mi(e, "Duplikat", "copy", f"{MOD}+D", self.duplicate)
        self._mi(e, "Hapus", "delete", "Del", self.delete_selected)
        e.add_separator()
        self._mi(e, "Pilih semua objek", None, f"{MOD}+A", self.select_all)
        self._mi(e, "Batal pilih", None, "Esc", lambda: self.set_sel([]))
        e.add_separator()
        self._mi(e, "Putar +15 deg", "rotate", "R", lambda: self.rotate(15))
        self._mi(e, "Putar -15 deg", "rotate", "Shift+R", lambda: self.rotate(-15))
        self._mi(e, "Kunci / buka kunci", "lock", f"{MOD}+L", lambda: self.toggle_flag("locked"))
        self._mi(e, "Sembunyikan / tampilkan", "eye", f"{MOD}+H", lambda: self.toggle_flag("hidden"))
        self._mi(e, "Tampilkan semua objek", "eye", "", self.show_all)
        al = tk.Menu(e, tearoff=0)
        for lbl, ic, md in (("Rata kiri", "al_l", "l"), ("Rata tengah horizontal", "al_c", "c"),
                            ("Rata kanan", "al_r", "r"), ("Rata atas", "al_t", "t"),
                            ("Rata tengah vertikal", "al_m", "m"), ("Rata bawah", "al_b", "b"),
                            ("Sebar horizontal", "dist_h", "dh"), ("Sebar vertikal", "dist_v", "dv")):
            self._mi(al, lbl, ic, "", lambda md=md: self.align(md))
        e.add_cascade(label="Ratakan & sebar", menu=al)
        m.add_cascade(label="Edit", menu=e)
        self.edit_menu = e
        v = tk.Menu(m, tearoff=0)
        v.add_checkbutton(label="Grid", accelerator="G", variable=self.grid_on, command=self.redraw)
        v.add_checkbutton(label="Snap", accelerator="N", variable=self.snap_on, command=self.redraw)
        v.add_checkbutton(label="Label", accelerator="L", variable=self.labels_on, command=self.redraw)
        v.add_separator()
        self._mi(v, "Perbesar", "zoomin", f"{MOD}++", lambda: self.zoom(1.25))
        self._mi(v, "Perkecil", "zoomout", f"{MOD}+-", lambda: self.zoom(1 / 1.25))
        self._mi(v, "Fit ke kolam", "fit", f"{MOD}+0", lambda: self.fit(True))
        v.add_separator()
        self._mi(v, "Ganti tema gelap / terang", "theme", "", self.app.toggle_theme)
        self._mi(v, "Layar penuh", "fullscreen", "F11", self.app.toggle_fullscreen)
        m.add_cascade(label="Tampilan", menu=v)
        ms = tk.Menu(m, tearoff=0)
        self._mi(ms, "Generate waypoint", "plan", "P", self.do_plan)
        self._mi(ms, "Validasi misi", "check", "F6", self.run_validate)
        ms.add_separator()
        self._mi(ms, "Simulasi: play / pause", "play", "F5", self.toggle_sim)
        self._mi(ms, "Stop simulasi", "stop", "Shift+F5", self.stop_sim)
        ms.add_separator()
        self._mi(ms, "Kosongkan waypoint", "delete", "", self.clear_wps)
        self._mi(ms, "Salin tabel waypoint", "copy", "", self.copy_table)
        m.add_cascade(label="Misi", menu=ms)
        h = tk.Menu(m, tearoff=0)
        self._mi(h, "Shortcut & bantuan", "help", "F1", self.app.show_help)
        self._mi(h, f"Tentang {APP_NAME}", "info", "", self.app.show_about)
        m.add_cascade(label="Bantuan", menu=h)
        return m
