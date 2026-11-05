"""Top-level application window: screen switching, project lifecycle, global keys."""
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from ..constants import (
    APP_DIR,
    APP_NAME,
    APP_VERSION,
    DEFAULT_PROJECT_DIR,
    EXT,
    HOME,
    IS_MAC,
    IS_WIN,
    MAX_RECENT,
    MOD,
    SETTINGS_FILE,
)
from ..help_text import HELP_TEXT
from ..icons import clear_icons, ico
from ..model import Auv, Project
from ..scaling import sc, set_ui_scale
from ..storage import JsonStore, RecentStore
from ..theme import F, T, pick_fonts, set_theme
from ..utils import slug
from .dialogs import NewProjectDialog
from .editor import Editor
from .home import Home
from .style import setup_style


class App(tk.Tk):
    def __init__(self):
        super().__init__(className="AUVMapper")
        try:
            set_ui_scale(float(self.winfo_fpixels("1i")) / 96.0)
        except tk.TclError:
            set_ui_scale(1.0)
        pick_fonts(self)
        self.settings = JsonStore(SETTINGS_FILE, {"theme": "dark"})
        if not isinstance(self.settings.data, dict):
            self.settings.data = {"theme": "dark"}
        set_theme(self.settings.data.get("theme", "dark"))
        self.title(APP_NAME)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(sc(1440), sw - 60), min(sc(860), sh - 90)
        self.geometry(f"{w}x{h}+{max((sw - w) // 2, 0)}+{max((sh - h) // 3, 0)}")
        self.minsize(min(sc(1100), sw), min(sc(680), sh))
        try:
            self.iconphoto(True, ico("app", 64))
        except tk.TclError:
            pass
        setup_style(self)
        self.recent = RecentStore()
        self.screen = None
        self.fullscreen = False
        self.bind_all("<Key>", self.on_key)
        self.bind_all("<KeyRelease>", self.on_key_release)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.show_home(force=True)

    # ---- screens
    def set_screen(self, frame):
        old = self.screen
        self.screen = frame
        frame.pack(fill="both", expand=True)
        if old is not None:
            old.destroy()

    def home_menu(self):
        m = tk.Menu(self, tearoff=0)
        f = tk.Menu(m, tearoff=0)
        f.add_command(label="Proyek Baru...", accelerator=f"{MOD}+N", command=self.new_dialog)
        f.add_command(label="Buka...", accelerator=f"{MOD}+O", command=self.open_dialog)
        rm = tk.Menu(f, tearoff=0, postcommand=lambda: self.fill_recent_menu(rm))
        f.add_cascade(label="Buka Terbaru", menu=rm)
        f.add_separator()
        f.add_command(label="Keluar", accelerator=f"{MOD}+Q", command=self.on_close)
        m.add_cascade(label="Berkas", menu=f)
        v = tk.Menu(m, tearoff=0)
        v.add_command(label="Ganti tema gelap / terang", command=self.toggle_theme)
        v.add_command(label="Layar penuh", accelerator="F11", command=self.toggle_fullscreen)
        m.add_cascade(label="Tampilan", menu=v)
        h = tk.Menu(m, tearoff=0)
        h.add_command(label="Shortcut & bantuan", accelerator="F1", command=self.show_help)
        h.add_command(label=f"Tentang {APP_NAME}", command=self.show_about)
        m.add_cascade(label="Bantuan", menu=h)
        return m

    def fill_recent_menu(self, menu):
        menu.delete(0, "end")
        items = [i for i in self.recent.items if os.path.isfile(i["path"])]
        if not items:
            menu.add_command(label="(kosong)", state="disabled")
        for it in items[:MAX_RECENT]:
            menu.add_command(label=f"{it.get('name', '')}   -   {it['path']}",
                             command=lambda p=it["path"]: self.open_path(p))

    def show_home(self, force=False):
        if not force and not self.confirm_discard():
            return
        self.title(APP_NAME)
        self.config(menu=self.home_menu())
        self.set_screen(Home(self))

    def show_editor(self, proj, path):
        ed = Editor(self, proj, path)
        self.config(menu=ed.build_menu())
        self.set_screen(ed)
        ed.update_title()
        return ed

    def rebuild(self):
        old = self.screen
        if isinstance(old, Editor):
            old.stop_sim()
            new = Editor(self, old.proj, old.path)
            new.adopt(old)
            self.config(menu=new.build_menu())
            self.set_screen(new)
            new.update_title()
        else:
            self.config(menu=self.home_menu())
            self.set_screen(Home(self))

    def toggle_theme(self):
        name = "light" if self.settings.data.get("theme", "dark") == "dark" else "dark"
        self.settings.data["theme"] = name
        self.settings.save()
        set_theme(name)
        clear_icons()
        setup_style(self)
        self.rebuild()

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        try:
            self.attributes("-fullscreen", self.fullscreen)
        except tk.TclError:
            self.state("zoomed" if self.fullscreen else "normal")

    # ---- projects
    def confirm_discard(self):
        ed = self.screen if isinstance(self.screen, Editor) else None
        if ed is None or not ed.is_dirty():
            return True
        ans = messagebox.askyesnocancel("Simpan perubahan?", f"Proyek '{ed.proj.name}' punya perubahan "
                                        "yang belum disimpan. Simpan sekarang?", parent=self)
        if ans is None:
            return False
        if ans:
            return ed.save()
        ed.clear_autosave()
        return True

    def new_dialog(self):
        if not self.confirm_discard():
            return
        dlg = NewProjectDialog(self)
        self.wait_window(dlg)
        r = dlg.result
        if not r:
            return
        proj = Project(r["name"], r["W"], r["H"], r["D"], r["qual"])
        if r["template"] == 1:
            proj.apply_sauvc_template()
        else:
            proj.auv = Auv(min(1.5, r["W"] / 2), r["H"] / 2, 90.0, min(1.0, r["D"]))
            proj.order = ""
        folder = r["folder"] or DEFAULT_PROJECT_DIR
        try:
            os.makedirs(folder, exist_ok=True)
            base = os.path.join(folder, slug(r["name"]))
            path, n = base + EXT, 2
            while os.path.exists(path):
                path = f"{base}_{n}{EXT}"
                n += 1
            proj.save(path)
        except OSError as ex:
            messagebox.showerror("Gagal membuat proyek", str(ex), parent=self)
            return
        self.recent.add(path, proj.name)
        self.show_editor(proj, path)

    def open_dialog(self):
        if not self.confirm_discard():
            return
        init = DEFAULT_PROJECT_DIR if os.path.isdir(DEFAULT_PROJECT_DIR) else HOME
        path = filedialog.askopenfilename(parent=self, initialdir=init, title="Buka proyek",
                                          filetypes=[("AUV Map project", "*" + EXT), ("JSON", "*.json"),
                                                     ("Semua file", "*.*")])
        if path:
            self.open_path(path, checked=True)

    def open_path(self, path, checked=False):
        if not checked and not self.confirm_discard():
            return
        recovered = False
        try:
            proj = Project.load(path)
            ap = path + ".autosave"
            if os.path.exists(ap) and os.path.getmtime(ap) > os.path.getmtime(path):
                if messagebox.askyesno("Pulihkan autosave?", "Ditemukan salinan autosave yang lebih baru dari "
                                       "file proyek (mungkin aplikasi tertutup tiba-tiba).\n\nPulihkan?",
                                       parent=self):
                    proj, recovered = Project.load(ap), True
                else:
                    os.remove(ap)
        except (OSError, ValueError, KeyError, TypeError) as ex:
            messagebox.showerror("Gagal membuka proyek", f"{path}\n\n{ex}", parent=self)
            return
        self.recent.add(path, proj.name)
        ed = self.show_editor(proj, path)
        if recovered:
            ed.saved_state = ""
            ed.update_title()
            ed.say("Autosave dipulihkan. Simpan untuk menjadikannya permanen.")

    # ---- info dialogs
    def _info_window(self, title, body, mono=True, w=78, h=34):
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=T["panel"])
        win.transient(self)
        t = tk.Text(win, width=w, height=h, bg=T["panel2"], fg=T["text"], relief="flat", padx=16, pady=12,
                    font=F(10, mono=mono), highlightthickness=0, wrap="word")
        t.insert("1.0", body)
        t.config(state="disabled")
        t.pack(fill="both", expand=True, padx=10, pady=(10, 4))
        ttk.Button(win, text="Tutup", command=win.destroy).pack(pady=(0, 10))
        win.bind("<Escape>", lambda e: win.destroy())
        return win

    def show_help(self):
        self._info_window("Shortcut & Bantuan", HELP_TEXT)

    def show_about(self):
        body = (f"{APP_NAME}  v{APP_VERSION}\n\n"
                "Perancang arena kolam AUV dan perencana waypoint.\n"
                "Koordinat: origin di pojok kiri-bawah, +x ke kanan, +y ke atas.\n"
                "Bearing: 0 deg = +y (atas peta), searah jarum jam.\n\n"
                f"Berkas proyek : {EXT} (JSON, bisa diedit manual)\n"
                f"Konfigurasi   : {APP_DIR}\n"
                f"Folder proyek : {DEFAULT_PROJECT_DIR}\n\n"
                f"Python {sys.version.split()[0]}  |  Tk {tk.TkVersion}  |  {sys.platform}")
        self._info_window("Tentang", body, mono=False, w=64, h=13)

    # ---- keyboard
    def on_key(self, e):
        try:
            if e.widget.winfo_toplevel() is not self:
                return
        except (AttributeError, KeyError, tk.TclError):
            return
        st = e.state
        ctrl = bool(st & 0x4) or (IS_MAC and bool(st & 0x8))
        shift = bool(st & 0x1)
        alt = bool(st & (0x20000 if IS_WIN else 0x10 if IS_MAC else 0x8))
        if alt and not ctrl:
            return  # Alt + letter belongs to menus; Windows NumLock (0x8) is no longer misread
        k = e.keysym.lower()
        scr = self.screen
        if k == "f1":
            self.show_help()
            return
        if k == "f11":
            self.toggle_fullscreen()
            return
        if ctrl and k == "q":
            self.on_close()
            return
        if k == "space" and isinstance(scr, Editor) and not ctrl and not scr.in_text_entry():
            scr.space_down()
            return
        if scr is not None and hasattr(scr, "on_key"):
            scr.on_key(e, k, ctrl, shift)

    def on_key_release(self, e):
        if e.keysym.lower() == "space" and isinstance(self.screen, Editor):
            self.screen.space_up()

    def on_close(self):
        if not self.confirm_discard():
            return
        if isinstance(self.screen, Editor):
            self.screen.stop_sim()
        self.destroy()
