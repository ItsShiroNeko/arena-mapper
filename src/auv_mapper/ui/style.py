"""ttk styling and tooltips."""
import tkinter as tk
from tkinter import ttk

from ..scaling import sc
from ..theme import F, T


def setup_style(root):
    th = T
    st = ttk.Style(root)
    st.theme_use("clam")
    root.configure(bg=th["bg"])
    root.option_add("*TCombobox*Listbox.background", th["panel2"])
    root.option_add("*TCombobox*Listbox.foreground", th["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", th["accent"])
    root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
    root.option_add("*Menu.background", th["panel2"])
    root.option_add("*Menu.foreground", th["text"])
    root.option_add("*Menu.activeBackground", th["accent"])
    root.option_add("*Menu.activeForeground", "#ffffff")
    root.option_add("*Menu.relief", "flat")
    root.option_add("*Menu.borderWidth", 1)
    f = F(10)
    st.configure(".", background=th["panel"], foreground=th["text"], fieldbackground=th["panel2"],
                 bordercolor=th["border"], lightcolor=th["panel"], darkcolor=th["panel"],
                 troughcolor=th["panel2"], focuscolor=th["panel"], font=f)
    st.configure("TFrame", background=th["panel"])
    st.configure("Bg.TFrame", background=th["bg"])
    st.configure("Bar.TFrame", background=th["panel2"])
    st.configure("Card.TFrame", background=th["panel2"])
    st.configure("TLabel", background=th["panel"], foreground=th["text"])
    st.configure("Muted.TLabel", foreground=th["muted"])
    st.configure("Bar.TLabel", background=th["panel2"], foreground=th["muted"])
    st.configure("BarB.TLabel", background=th["panel2"], foreground=th["text"], font=F(9, True))
    st.configure("Title.TLabel", background=th["bg"], font=F(24, True))
    st.configure("Sub.TLabel", background=th["bg"], foreground=th["muted"], font=F(11))
    st.configure("Sec.TLabel", background=th["bg"], foreground=th["muted"], font=F(9, True))
    st.configure("BgMuted.TLabel", background=th["bg"], foreground=th["muted"])
    st.configure("PSec.TLabel", background=th["panel"], foreground=th["muted"], font=F(8, True))
    st.configure("Card.TLabel", background=th["panel2"], foreground=th["text"])
    st.configure("CardH.TLabel", background=th["panel2"], foreground=th["text"], font=F(14, True))
    st.configure("CardMuted.TLabel", background=th["panel2"], foreground=th["muted"])
    st.configure("H.TLabel", font=F(11, True))
    st.configure("Err.TLabel", foreground=th["danger"])
    st.configure("TButton", background=th["panel2"], foreground=th["text"], padding=(10, 5), borderwidth=1)
    st.map("TButton", background=[("active", th["border"]), ("disabled", th["panel"])],
           foreground=[("disabled", th["muted"])])
    st.configure("Accent.TButton", background=th["accent"], foreground="#ffffff", padding=(14, 7), font=F(10, True))
    st.map("Accent.TButton", background=[("active", th["accent_hover"])])
    st.configure("Tool.TButton", background=th["panel2"], padding=4, borderwidth=0)
    st.map("Tool.TButton", background=[("active", th["border"]), ("disabled", th["panel2"])])
    st.configure("Toolbutton", background=th["panel2"], foreground=th["text"], padding=(9, 4), borderwidth=1)
    st.map("Toolbutton", background=[("selected", th["accent"]), ("active", th["border"])],
           foreground=[("selected", "#ffffff")])
    st.configure("Tool.Toolbutton", background=th["panel2"], padding=4, borderwidth=0)
    st.map("Tool.Toolbutton", background=[("selected", th["accent"]), ("active", th["border"])])
    st.configure("Palette.Toolbutton", anchor="w", padding=(6, 2), background=th["panel"], borderwidth=0)
    st.map("Palette.Toolbutton", background=[("selected", th["accent"]), ("active", th["panel2"])],
           foreground=[("selected", "#ffffff")])
    st.configure("Treeview", background=th["panel2"], fieldbackground=th["panel2"], foreground=th["text"],
                 rowheight=sc(24), borderwidth=0)
    st.map("Treeview", background=[("selected", th["accent"])], foreground=[("selected", "#ffffff")])
    st.configure("Treeview.Heading", background=th["panel"], foreground=th["muted"], relief="flat", font=F(9, True))
    st.configure("TNotebook", background=th["panel"], borderwidth=0)
    st.configure("TNotebook.Tab", padding=(11, 7), background=th["panel"], foreground=th["muted"])
    st.map("TNotebook.Tab", background=[("selected", th["panel2"])], foreground=[("selected", th["text"])])
    st.configure("TEntry", fieldbackground=th["panel2"], foreground=th["text"], insertcolor=th["text"], padding=4)
    st.configure("TCombobox", fieldbackground=th["panel2"], foreground=th["text"], arrowcolor=th["text"], padding=4)
    st.configure("TSpinbox", fieldbackground=th["panel2"], foreground=th["text"], arrowcolor=th["text"], padding=4)
    st.map("TCombobox", fieldbackground=[("readonly", th["panel2"])], foreground=[("readonly", th["text"])],
           selectbackground=[("readonly", th["panel2"])], selectforeground=[("readonly", th["text"])])
    st.configure("TCheckbutton", background=th["panel"], foreground=th["text"])
    st.configure("TRadiobutton", background=th["panel"], foreground=th["text"])
    st.configure("TSeparator", background=th["border"])
    st.configure("TPanedwindow", background=th["border"])
    st.configure("Sash", sashthickness=4, background=th["border"])
    for orient in ("Vertical", "Horizontal"):
        st.configure(orient + ".TScrollbar", background=th["border"], troughcolor=th["panel"],
                     bordercolor=th["panel"], arrowcolor=th["muted"], lightcolor=th["border"],
                     darkcolor=th["border"])
        st.map(orient + ".TScrollbar", background=[("active", th["muted"])])


class Tooltip:
    def __init__(self, widget, text):
        self.w, self.text, self.tip, self.job = widget, text, None, None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _enter(self, _e):
        self._hide()
        self.job = self.w.after(500, self._show)

    def _show(self):
        if self.tip or not self.w.winfo_exists():
            return
        x = self.w.winfo_rootx() + 8
        y = self.w.winfo_rooty() + self.w.winfo_height() + 6
        self.tip = tk.Toplevel(self.w)
        self.tip.wm_overrideredirect(True)
        self.tip.wm_geometry(f"+{x}+{y}")
        tk.Label(self.tip, text=self.text, bg=T["panel2"], fg=T["text"], bd=1, relief="solid",
                 padx=8, pady=3, font=F(9)).pack()

    def _hide(self, _e=None):
        if self.job:
            try:
                self.w.after_cancel(self.job)
            except tk.TclError:
                pass
            self.job = None
        if self.tip:
            self.tip.destroy()
            self.tip = None


def tip(widget, text, accel=""):
    Tooltip(widget, f"{text}  ({accel})" if accel else text)
    return widget
