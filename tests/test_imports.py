"""Import every module with a stubbed tkinter so the package can be checked headlessly."""
import importlib
import pkgutil
import sys
from unittest import mock

import pytest

import auv_mapper


def test_all_modules_import_with_stub_tk():
    stubs = {n: mock.MagicMock() for n in ("tkinter", "tkinter.ttk", "tkinter.filedialog",
                                           "tkinter.messagebox", "tkinter.colorchooser", "tkinter.font")}
    # class bases must be real classes
    class _Base:
        def __init__(self, *a, **k):
            pass
    for sub in ("ttk", "filedialog", "messagebox", "colorchooser", "font"):
        setattr(stubs["tkinter"], sub, stubs["tkinter." + sub])
    for mod in ("tkinter", "tkinter.ttk"):
        for attr in ("Tk", "Toplevel", "Frame"):
            setattr(stubs[mod], attr, _Base)
    with mock.patch.dict(sys.modules, stubs):
        for name in [m.name for m in pkgutil.walk_packages(auv_mapper.__path__, "auv_mapper.")]:
            sys.modules.pop(name, None)
        for info in pkgutil.walk_packages(auv_mapper.__path__, "auv_mapper."):
            importlib.import_module(info.name)
        from auv_mapper.ui.editor import Editor
        assert hasattr(Editor, "do_undo") and hasattr(Editor, "export_svg") and hasattr(Editor, "sim_tick")
    for name in [m for m in sys.modules if m.startswith("auv_mapper.")]:
        sys.modules.pop(name, None)


def test_icon_rasteriser_outputs_png():
    pytest.importorskip("tkinter")
    from auv_mapper.icons import ICONS, raster_icon
    png = raster_icon(ICONS["save"], 24, ("#000", "#00f", "#f00", "#0f0", "#ff0"))
    assert png.startswith(b"\x89PNG")
