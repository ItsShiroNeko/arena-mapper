"""Modal dialogs."""
import tkinter as tk
from tkinter import filedialog, ttk

from ..constants import DEFAULT_PROJECT_DIR, HOME
from ..theme import F, T

TEMPLATES = ["Kosong (mulai dari nol)", "SAUVC 50 x 25 (dari gambar arena)"]


class NewProjectDialog(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.result = None
        self.title("Proyek Baru")
        self.configure(bg=T["panel"])
        self.transient(app)
        self.resizable(False, False)
        body = ttk.Frame(self, padding=20)
        body.pack(fill="both", expand=True)
        self.v = {k: tk.StringVar(value=val) for k, val in
                  dict(name="Proyek AUV 1", W="50", H="25", D="2", qual="10",
                       folder=DEFAULT_PROJECT_DIR, template=TEMPLATES[1]).items()}
        ttk.Label(body, text="Proyek Baru", style="H.TLabel", font=F(15, True)).grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        rows = [("Nama proyek", "name"), ("Panjang kolam / sumbu x (m)", "W"), ("Lebar kolam / sumbu y (m)", "H"),
                ("Kedalaman (m)", "D"), ("Lebar area kualifikasi (m, 0 = tanpa)", "qual")]
        r = 1
        first = None
        for lbl, key in rows:
            ttk.Label(body, text=lbl).grid(row=r, column=0, sticky="w", pady=4, padx=(0, 14))
            e = ttk.Entry(body, textvariable=self.v[key], width=30)
            e.grid(row=r, column=1, columnspan=2, sticky="ew")
            first = first or e
            r += 1
        ttk.Label(body, text="Template").grid(row=r, column=0, sticky="w", pady=4)
        cb = ttk.Combobox(body, textvariable=self.v["template"], values=TEMPLATES, state="readonly", width=34)
        cb.grid(row=r, column=1, columnspan=2, sticky="ew")
        cb.bind("<<ComboboxSelected>>", self._on_template)
        r += 1
        ttk.Label(body, text="Simpan di folder").grid(row=r, column=0, sticky="w", pady=4)
        ttk.Entry(body, textvariable=self.v["folder"], width=24).grid(row=r, column=1, sticky="ew")
        ttk.Button(body, text="...", width=3, command=self._browse).grid(row=r, column=2, padx=(4, 0))
        r += 1
        self.err = ttk.Label(body, text="", style="Err.TLabel")
        self.err.grid(row=r, column=0, columnspan=3, sticky="w", pady=(8, 0))
        bt = ttk.Frame(body)
        bt.grid(row=r + 1, column=0, columnspan=3, sticky="e", pady=(14, 0))
        ttk.Button(bt, text="Batal", command=self.destroy).pack(side="left", padx=6)
        ttk.Button(bt, text="Buat Proyek", style="Accent.TButton", command=self._ok).pack(side="left")
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self.update_idletasks()
        x = app.winfo_rootx() + (app.winfo_width() - self.winfo_width()) // 2
        y = app.winfo_rooty() + (app.winfo_height() - self.winfo_height()) // 3
        self.geometry(f"{self.winfo_reqwidth()}x{self.winfo_reqheight()}+{max(x, 0)}+{max(y, 0)}")
        try:
            self.wait_visibility()
            self.grab_set()
        except tk.TclError:
            pass
        if first:
            first.focus_set()
            first.select_range(0, "end")

    def _on_template(self, _e=None):
        if self.v["template"].get() == TEMPLATES[1]:
            for k, val in dict(W="50", H="25", D="2", qual="10").items():
                self.v[k].set(val)

    def _browse(self):
        d = filedialog.askdirectory(parent=self, initialdir=self.v["folder"].get() or HOME)
        if d:
            self.v["folder"].set(d)

    def _ok(self):
        try:
            W, H, D = (float(self.v[k].get().replace(",", ".")) for k in ("W", "H", "D"))
            q = float(self.v["qual"].get().replace(",", "."))
            if W < 2 or H < 2 or D <= 0 or W > 500 or H > 500:
                raise ValueError("Ukuran kolam harus 2-500 m dan kedalaman > 0.")
            if q < 0 or q >= W:
                raise ValueError("Lebar area qual harus 0 sampai < panjang kolam.")
            name = self.v["name"].get().strip()
            if not name:
                raise ValueError("Nama proyek tidak boleh kosong.")
        except ValueError as ex:
            msg = str(ex)
            self.err.config(text=msg if "harus" in msg or "kosong" in msg else "Isi angka yang valid.")
            return
        self.result = dict(name=name, W=W, H=H, D=D, qual=q, folder=self.v["folder"].get().strip(),
                           template=TEMPLATES.index(self.v["template"].get()))
        self.destroy()
