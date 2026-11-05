# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to
[Semantic Versioning](https://semver.org/).

## [2.0.0] - 2026-11-05

### Changed
- Refactored the single-file script into the installable `auv_mapper` package (`src/` layout):
  pure-Python core (`model`, `geometry`, `kinds`, `utils`), rendering (`render/`), and the Tk UI (`ui/`),
  with the editor split into focused mixins under `ui/editor/`.
- `UI_SCALE` is no longer a mutable module global; use `auv_mapper.scaling.ui_scale()` / `set_ui_scale()`.
- New entry points: `auv-mapper` command and `python -m auv_mapper`.

### Fixed
- `Project.add()` now always stores `heading` as `float`, so a project serialises identically before and
  after a save/load round-trip.

### Added
- Unit tests (geometry, model, planner, validator, headless import check) and GitHub Actions CI.
- Project documentation: README, CONTRIBUTING, file-format reference.
