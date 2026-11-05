"""Command line entry point."""
import os
import sys

from .scaling import enable_dpi
from .ui.app import App


def main(argv=None):
    """Launch the GUI. An optional first argument is a project file to open."""
    argv = sys.argv[1:] if argv is None else list(argv)
    enable_dpi()
    app = App()
    if argv and os.path.isfile(argv[0]):
        app.open_path(os.path.abspath(argv[0]), checked=True)
    app.mainloop()
