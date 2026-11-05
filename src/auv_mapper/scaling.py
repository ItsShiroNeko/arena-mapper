"""HiDPI scaling helpers."""
from .constants import IS_WIN

_UI_SCALE = 1.0


def ui_scale():
    """Current UI scale factor (1.0 = 96 dpi)."""
    return _UI_SCALE


def set_ui_scale(value):
    """Set the UI scale factor, clamped to a sane range."""
    global _UI_SCALE
    _UI_SCALE = max(1.0, min(3.0, float(value)))


def sc(n):
    """Scale a pixel value for HiDPI screens."""
    return int(round(n * _UI_SCALE))


def enable_dpi():
    """Opt in to per-monitor DPI awareness on Windows (no-op elsewhere)."""
    if IS_WIN:
        try:
            import ctypes
            try:
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
            except Exception:
                ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass
