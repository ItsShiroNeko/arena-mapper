"""Editor screen, composed from focused mixins.

Each mixin owns one concern; they share state through ``self`` (set up in ``Editor.__init__``).
"""
import tkinter as tk
from tkinter import ttk

from ...constants import AUTOSAVE_MS
from .actions import ActionsMixin
from .files import FileMixin
from .history import HistoryMixin
from .interaction import InteractionMixin
from .keys import KeyboardMixin
from .layout import LayoutMixin
from .menu import MenuMixin
from .properties import PropertiesMixin
from .refresh import RefreshMixin
from .selection import SelectionMixin
from .simulation import SimulationMixin
from .view import ViewMixin

__all__ = ["Editor"]


class Editor(LayoutMixin, MenuMixin, HistoryMixin, SelectionMixin, PropertiesMixin, RefreshMixin,
             ViewMixin, InteractionMixin, ActionsMixin, SimulationMixin, FileMixin, KeyboardMixin,
             ttk.Frame):
    HINTS = {"select": "Klik untuk memilih, seret untuk memindah, seret area kosong untuk kotak pilih. "
                       "Shift+klik menambah pilihan. Klik kanan: menu.",
             "pan": "Seret untuk menggeser tampilan.",
             "waypoint": "Klik untuk menambah waypoint. Esc untuk selesai.",
             "auv": "Klik untuk menetapkan posisi awal AUV. R memutar heading.",
             "measure": "Seret untuk mengukur jarak dan bearing. Esc menghapus pengukuran."}

    PROJECT_FIELDS = [
        ("Nama proyek", "name", "s"), ("Panjang kolam x (m)", "W", "n"), ("Lebar kolam y (m)", "H", "n"),
        ("Kedalaman (m)", "D", "n"), ("Lebar area qual (m)", "qual", "n"), ("Grid minor (m)", "grid_minor", "n"),
        ("Grid major (m)", "grid_major", "n"), ("Langkah snap (m)", "snap_step", "n"),
        ("Jarak align gate (m)", "standoff", "n"), ("Mundur setelah flare (m)", "backoff", "n"),
        ("Offset kompas IMU (deg)", "north_offset", "n"),
    ]

    def __init__(self, app, proj, path):
        super().__init__(app)
        self.app, self.proj, self.path = app, proj, path
        self.undo, self.redo = [], []
        self.saved_state = proj.state()
        self.sel = []
        self.tool_var = tk.StringVar(value="select")
        self.snap_on = tk.BooleanVar(value=True)
        self.grid_on = tk.BooleanVar(value=True)
        self.labels_on = tk.BooleanVar(value=True)
        self.view = None
        self.auto_fit = True
        self.drag = self.pan = self.band = self.measure = None
        self.sim = self.sim_job = None
        self.sim_paused = False
        self.sim_mult = 1.0
        self.space_pan = False
        self._space_job = None
        self.clip, self.paste_n = [], 0
        self.issues = []
        self.prop_sig, self.prop_vars = None, {}
        self._building = False
        self._sync_until = 0.0
        self._auto_job = None
        self._build()
        self.refresh_all()
        self._auto_job = self.after(AUTOSAVE_MS, self.autosave)

    def destroy(self):
        for j in (self._auto_job, self._space_job):
            if j:
                try:
                    self.after_cancel(j)
                except tk.TclError:
                    pass
        self.stop_sim()
        super().destroy()
