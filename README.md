<div align="center">

# AUV Arena Mapper

**Design AUV competition pools, place objects, and plan waypoint missions - in a single, dependency-free desktop app.**

[![CI](https://github.com/ItsShiroNeko/auv-arena-mapper/actions/workflows/ci.yml/badge.svg)](https://github.com/ItsShiroNeko/auv-arena-mapper/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/python-3.8%2B-3776AB?logo=python&logoColor=white)
![Platforms](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

</div>

AUV Arena Mapper is a Tkinter desktop application for autonomous underwater vehicle (AUV) teams. Lay out the arena
(gates, flares, drums, zones, ...), describe the mission as a sequence of tokens, and the app generates an editable
waypoint plan with bearings, distances, ETA and a depth profile - then validates it, simulates it, and exports it.
It ships with a template based on the **SAUVC** arena (50 x 25 m pool).

> **Note:** the user interface is currently in Indonesian (Bahasa Indonesia). Localisation is on the roadmap.

## Features

- **Arena editor** - palette of 16 object kinds, drag & drop, rotate, resize, per-object depth and colour
- **Multi-select** with rubber-band, group move, align & distribute, lock / hide, object outline list
- **Undo / redo** (300 steps), copy / cut / paste (also between windows via the system clipboard), duplicate
- **Mission planner** - generate waypoints from a token sequence (`gate`, `orange`, `drum_blue`, `goto:x,y,z`, ...),
  hold times, insert waypoints on a path segment, live depth profile
- **Validation** - out-of-pool objects/waypoints, depth limits, path/obstacle clearance, oblique gate crossings, sharp turns
- **AUV simulation** - play / pause / stop at 0.5x-8x with turn-rate limited kinematics
- **Measurement tool** (distance + bearing), scale bar, north arrow, grid + snap
- **Export** - CSV, mission JSON, SVG drawing, or copy the waypoint table straight into Excel / Sheets
- **Quality of life** - autosave + crash recovery, recent projects with preview, dark / light theme, HiDPI aware,
  standard keyboard shortcuts (press `F1` in the app)
- **Zero dependencies** - Python standard library only

## Installation

**Requirements:** Python 3.8+ with Tkinter.

| OS | Tkinter |
|----|---------|
| Windows / macOS | included with the python.org installers |
| Debian / Ubuntu | `sudo apt install python3-tk` |
| Fedora | `sudo dnf install python3-tkinter` |

```bash
# from source
git clone https://github.com/ItsShiroNeko/auv-arena-mapper.git
cd auv-arena-mapper
pip install .
```

## Usage

```bash
auv-mapper                      # start the app
auv-mapper my_project.auvmap    # open a project directly
python -m auv_mapper            # equivalent, without installing the entry point
```

Quick start:

1. **New project** -> choose the *SAUVC 50 x 25* template (or start empty).
2. Drag objects into place, or pick one in the palette and click on the map.
3. Open the **Misi** tab, edit the mission order (e.g. `orange gate yellow red blue drum_blue surface`) and press **Generate** (`P`).
4. Check the **Cek** tab for warnings, press `F5` to simulate, then export CSV / JSON for your vehicle's controller.

### Keyboard shortcuts (excerpt)

| Action | Shortcut | | Action | Shortcut |
|--------|----------|-|--------|----------|
| New / Open / Save | `Ctrl+N` / `O` / `S` | | Select / Hand / Waypoint / AUV / Measure | `V` `H` `W` `A` `M` |
| Undo / Redo | `Ctrl+Z` / `Ctrl+Y` | | Generate waypoints | `P` |
| Copy / Cut / Paste | `Ctrl+C` / `X` / `V` | | Simulate (play/pause, stop) | `F5`, `Shift+F5` |
| Duplicate / Select all | `Ctrl+D` / `Ctrl+A` | | Validate | `F6` |
| Rotate +/- 15 deg | `R` / `Shift+R` | | Fit to pool | `F` / `Ctrl+0` |
| Lock / Hide | `Ctrl+L` / `Ctrl+H` | | Help / Fullscreen | `F1` / `F11` |

(`Cmd` replaces `Ctrl` on macOS.) The full list is available in-app under **Bantuan > Shortcut & bantuan**.

### Coordinate conventions

Origin `(0, 0)` is the pool's bottom-left corner, `+x` right, `+y` up (metres).
Headings and bearings are in degrees: `0` = `+y` (top of the map), clockwise (`90` = `+x`).
An optional *IMU compass offset* is added to bearings in CSV / JSON exports.

## Project file format

Projects are human-readable JSON (`.auvmap`). See [docs/file-format.md](docs/file-format.md) for the schema,
object kinds and mission tokens.

## Repository layout

```
auv-arena-mapper/
├── src/auv_mapper/
│   ├── model.py          # Project, Obj, Waypoint, planner, validator (pure Python)
│   ├── geometry.py       # vectors, bearings, view fitting
│   ├── kinds.py          # object catalogue + mission tokens
│   ├── constants.py      # paths, tuning constants, platform detection
│   ├── storage.py        # settings + recent-projects stores
│   ├── theme.py icons.py scaling.py help_text.py utils.py
│   ├── render/           # drawing sinks (Tk canvas / SVG) and the scene renderer
│   └── ui/
│       ├── app.py        # main window, screen switching, global keys
│       ├── home.py       # start screen
│       ├── dialogs.py    # new-project dialog
│       ├── style.py      # ttk styling, tooltips
│       └── editor/       # Editor = layout + menu + history + selection + properties
│                         #          + refresh + view + interaction + actions
│                         #          + simulation + files + keys (mixins)
├── tests/                # pytest suite (runs headless, no display needed)
├── docs/file-format.md
└── .github/workflows/ci.yml
```

The core (`model`, `geometry`, `kinds`, `utils`) has no GUI dependency, so planning and validation can be
reused from scripts:

```python
from auv_mapper.model import Project

p = Project("demo", 50, 25, 2, 10)
p.apply_sauvc_template()
p.waypoints, warnings = p.plan()
for row in p.segments():
    print(row["idx"], row["action"], f"{row['dist']:.1f} m", f"brg {row['bearing']:.0f}")
print(p.validate())
```

## Development

```bash
pip install -e ".[dev]"
ruff check .
pytest
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for architecture rules and the pull-request workflow.

## Roadmap

- [ ] Localisation (English UI) via a string catalogue
- [ ] Packaged binaries (PyInstaller) for Windows / macOS / Linux
- [ ] Additional arena templates
- [ ] Import waypoints from CSV

## License

Released under the [MIT License](LICENSE).
