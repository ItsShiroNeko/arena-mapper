"""Colour themes and font selection."""
from tkinter import font as tkfont

FONTS = {"ui": "Helvetica", "mono": "Courier"}


def pick_fonts(root):
    fams = set(tkfont.families(root))
    ui = ["Segoe UI", "SF Pro Text", "Helvetica Neue", "Ubuntu", "Noto Sans", "Cantarell", "DejaVu Sans",
          "Liberation Sans"]
    mono = ["Consolas", "Menlo", "DejaVu Sans Mono", "Ubuntu Mono", "Liberation Mono", "Courier New"]
    FONTS["ui"] = next((f for f in ui if f in fams), tkfont.nametofont("TkDefaultFont").actual("family"))
    FONTS["mono"] = next((f for f in mono if f in fams), "Courier")


def F(size=10, bold=False, mono=False):
    fam = FONTS["mono" if mono else "ui"]
    return (fam, size, "bold") if bold else (fam, size)


DARK = dict(
    bg="#12141a", panel="#1a1d25", panel2="#232733", border="#2e3342",
    text="#e6e9f0", muted="#8b93a7", accent="#4f8cff", accent_hover="#6ea0ff",
    danger="#ff6b6b", warn="#f5b942", ok="#4cc38a", canvas="#0d0f13",
    pool="#17324e", qual="#1d3f63", grid_minor="#1f4468", grid_major="#34648f",
    border_pool="#8fb8e0", label="#c5d8ec", gate_body="#f2f2f2",
    path="#c792ea", wp_fill="#1a1d25", wp_text="#ffffff", sel="#ffd54a",
    auv="#ffd400", obj_edge="#0b0d12", sim="#ff5d5d", measure="#5de0c2",
)
LIGHT = dict(DARK)
LIGHT.update(
    bg="#e9ecf1", panel="#f6f7f9", panel2="#ffffff", border="#cdd3de", text="#1b2130", muted="#667085",
    accent="#2f6fed", accent_hover="#4f86f5", danger="#d92d20", warn="#b7791f", ok="#1a8f5a",
    canvas="#f3f5f8", pool="#d9eaf9", qual="#c7ddf3", grid_minor="#bcd3ea", grid_major="#8fb0d0",
    border_pool="#1f3b57", label="#1f2d3d", gate_body="#111111", path="#7b2fbf", wp_fill="#ffffff",
    wp_text="#111111", sel="#e6a800", obj_edge="#222222", measure="#0b8f77",
)
T = dict(DARK)  # active theme (mutated in place)


def set_theme(name):
    T.clear()
    T.update(LIGHT if name == "light" else DARK)
