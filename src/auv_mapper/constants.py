"""Application-wide constants, platform detection and filesystem locations."""
import os
import sys

from . import __version__

APP_NAME = "AUV Arena Mapper"
APP_VERSION = __version__

# ---- platform
IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
MOD = "Cmd" if IS_MAC else "Ctrl"
HOME = os.path.expanduser("~")


def _config_dir():
    if IS_WIN:
        return os.path.join(os.environ.get("APPDATA", HOME), "AUVMapper")
    if IS_MAC:
        return os.path.join(HOME, "Library", "Application Support", "AUVMapper")
    return os.path.join(os.environ.get("XDG_CONFIG_HOME", os.path.join(HOME, ".config")), "auv_mapper")


def _project_dir():
    docs = os.path.join(HOME, "Documents")
    return os.path.join(docs if os.path.isdir(docs) else HOME, "AUVMapper")


APP_DIR = _config_dir()
RECENT_FILE = os.path.join(APP_DIR, "recent.json")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
LEGACY_RECENT = os.path.join(HOME, ".auv_mapper", "recent.json")
DEFAULT_PROJECT_DIR = _project_dir()

# ---- project file format
EXT = ".auvmap"
FORMAT_VERSION = 2

# ---- editor / simulation tuning
MAX_UNDO = 300
MAX_RECENT = 12
ACCEPT_RADIUS = 0.35
TURN_RATE_DEG_S = 30.0
SIM_DT = 0.05
SIM_STEPS_PER_TICK = 4
AUTOSAVE_MS = 60000
CLEARANCE = 0.4
