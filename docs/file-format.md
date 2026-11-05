# Project file format (`.auvmap`)

A project is a UTF-8 JSON document (current `version`: **2**). It can be edited by hand.

**Coordinates:** origin `(0, 0)` is the bottom-left corner of the pool, `+x` points right, `+y` points up (metres).
**Heading / bearing:** degrees, `0` = `+y` (top of the map), increasing clockwise (`90` = `+x`).

```jsonc
{
  "format": "auvmap",
  "version": 2,
  "name": "My project",
  "pool":  { "width": 50.0, "height": 25.0, "depth": 2.0, "qual_width": 10.0 },
  "grid":  { "minor": 1.0, "major": 5.0, "snap": 0.5 },
  "mission": {
    "order": "orange gate yellow red blue drum_blue surface",
    "speed": 0.5,            // m/s, used for ETA and simulation
    "standoff": 2.0,         // distance before/after a gate for ALIGN / EXIT waypoints
    "backoff": 1.5,          // retreat distance after touching a flare
    "north_offset": 0.0      // IMU compass offset added to bearings on export
  },
  "auv": { "x": 31.8, "y": 1.1, "heading": 0.0, "depth": 1.0 },
  "objects": [
    { "id": 1, "kind": "gate", "x": 26.2, "y": 9.6, "heading": 0.0, "size": 3.0, "h": 0.0,
      "depth": 1.0, "label": "Gate Utama", "color": "", "locked": false, "hidden": false }
  ],
  "waypoints": [
    { "x": 26.2, "y": 7.6, "depth": 1.0, "action": "ALIGN GATE", "hold": 0.0 }
  ],
  "next_id": 2,
  "meta": { "created": "2026-01-01T10:00:00", "modified": "2026-01-01T10:05:00" }
}
```

## Object kinds

`qual_gate`, `gate`, `qstart`, `flare_orange`, `flare_yellow`, `flare_red`, `flare_blue`, `drum_red`,
`drum_blue`, `surface`, `start`, `target`, `zone`, `obstacle`, `marker`, `text`.
Unknown kinds are ignored on load. Missing fields fall back to the defaults in `kinds.py`.

## Mission order tokens

| Token | Generates |
|-------|-----------|
| `gate`, `qual` | `ALIGN` -> `PASS` -> `EXIT` along the object's heading |
| `orange` `yellow` `red` `blue` | `TOUCH <colour>` (1 s hold) then `BACKOFF` |
| `drum_red`, `drum_blue` | `DROP` (2 s hold) |
| `surface` | `SURFACE` at depth 0 (3 s hold) |
| `target`, `marker`, `zone` | visit waypoint |
| `goto:x,y[,z]` | explicit waypoint |

For each token the object of that kind nearest to the previous waypoint is used.

## Exports

- **CSV / JSON** - waypoint table with map bearing, compass bearing (`north_offset` applied), distance,
  turn angle, cumulative distance and ETA.
- **SVG** - light-themed vector drawing of the arena and path.
