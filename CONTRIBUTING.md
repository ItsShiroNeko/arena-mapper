# Contributing

Thanks for your interest in AUV Arena Mapper! Bug reports, feature ideas and pull requests are welcome.

## Development setup

```bash
git clone https://github.com/ItsShiroNeko/auv-arena-mapper.git
cd auv-arena-mapper
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

Tkinter ships with Python on Windows/macOS. On Debian/Ubuntu install it with `sudo apt install python3-tk`.

## Checks

```bash
ruff check .        # lint (line length 130)
pytest              # tests (no display required)
python -m auv_mapper   # run the app
```

## Architecture rules

| Layer | Packages | May import |
|-------|----------|------------|
| Core (no GUI) | `model`, `geometry`, `kinds`, `utils`, `constants` | stdlib only |
| Rendering | `render/`, `icons`, `theme`, `scaling` | core, Tkinter |
| UI | `ui/` | everything above |

- Keep business logic (planning, validation, serialisation) in the core layer so it stays unit-testable.
- A new editor feature goes into the mixin that owns that concern (see `ui/editor/`), not into `Editor.__init__`.
- New object kinds are added in `kinds.py` only; the palette, planner tokens and renderer pick them up.
- Any change to the project file format must bump `FORMAT_VERSION` and stay backward compatible in
  `Project.apply_dict`.

## Pull requests

1. Fork and create a topic branch (`feature/...`, `fix/...`).
2. Add or update tests for behaviour changes.
3. Update `CHANGELOG.md` under *Unreleased*.
4. Make sure `ruff check .` and `pytest` pass, then open the PR with a clear description.

Commit messages follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:` ...).
