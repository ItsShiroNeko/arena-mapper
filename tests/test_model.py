import json

import pytest

from auv_mapper.model import Auv, Project, Waypoint


@pytest.fixture
def sauvc():
    p = Project("t", 50, 25, 2, 10)
    p.apply_sauvc_template()
    return p


def test_template_populates_arena(sauvc):
    kinds = {o.kind for o in sauvc.objects}
    assert {"gate", "target", "surface", "flare_orange", "drum_blue"} <= kinds
    assert sum(1 for o in sauvc.objects if o.kind == "drum_red") == 3
    ids = [o.id for o in sauvc.objects]
    assert len(ids) == len(set(ids))


def test_roundtrip_dict(sauvc):
    sauvc.waypoints = sauvc.plan()[0]
    clone = Project.from_dict(json.loads(json.dumps(sauvc.to_dict())))
    assert clone.state() == sauvc.state()


def test_save_and_load(tmp_path, sauvc):
    path = tmp_path / "p.auvmap"
    sauvc.save(str(path))
    assert Project.load(str(path)).state() == sauvc.state()
    assert not (tmp_path / "p.auvmap.tmp").exists()


def test_load_ignores_unknown_kinds():
    p = Project.from_dict({"objects": [{"kind": "nope", "x": 1, "y": 1},
                                        {"kind": "gate", "x": 2, "y": 3}]})
    assert [o.kind for o in p.objects] == ["gate"]
    assert p.objects[0].id >= 1


def test_plan_full_mission(sauvc):
    wps, warn = sauvc.plan()
    assert warn == []
    actions = [w.action for w in wps]
    assert "PASS GATE" in actions and "SURFACE" in actions
    assert wps[-1].action == "SURFACE" and wps[-1].depth == 0.0


def test_plan_reports_unknown_tokens(sauvc):
    sauvc.order = "gate bogus goto:1,2,3 goto:bad"
    wps, warn = sauvc.plan()
    assert warn == ["bogus", "goto:bad"]
    assert any(w.action == "GOTO" and (w.x, w.y, w.depth) == (1, 2, 3) for w in wps)


def test_plan_gate_is_aligned_along_heading(sauvc):
    sauvc.order = "gate"
    wps, _ = sauvc.plan()
    align, passing, exit_ = wps
    assert passing.action == "PASS GATE"
    assert align.y < passing.y < exit_.y        # gate heading 0 deg = +y
    assert align.x == pytest.approx(passing.x)


def test_segments_cumulative_and_eta():
    p = Project("t", 20, 20, 2, 0)
    p.auv = Auv(0, 0, 0, 1)
    p.speed = 1.0
    p.waypoints = [Waypoint(0, 10, 1, "GOTO", 2.0), Waypoint(10, 10, 1)]
    rows = p.segments()
    assert rows[0]["dist"] == pytest.approx(10) and rows[0]["turn"] == pytest.approx(0)
    assert rows[1]["turn"] == pytest.approx(90)
    assert rows[1]["cum"] == pytest.approx(20)
    assert rows[1]["eta"] == pytest.approx(10 + 2 + 10 + 90 / 30)


def test_validate_flags_out_of_pool_and_depth():
    p = Project("t", 10, 10, 2, 0)
    p.auv = Auv(1, 1, 0, 1)
    p.waypoints = [Waypoint(11, 5, 1), Waypoint(5, 5, 3.0)]
    levels = {(lvl, sel) for lvl, _m, sel in p.validate()}
    assert ("error", ("wp", 0)) in levels
    assert ("error", ("wp", 1)) in levels


def test_validate_no_waypoints_is_info():
    p = Project("t", 10, 10, 2, 0)
    out = p.validate()
    assert out and out[-1][0] == "info"


def test_validate_flags_path_through_obstacle():
    p = Project("t", 20, 20, 2, 0)
    p.auv = Auv(1, 10, 90, 1)
    p.add("obstacle", 10, 10)
    p.waypoints = [Waypoint(19, 10, 1)]
    assert any(lvl == "warn" and "melintas" in msg for lvl, msg, _s in p.validate())


def test_validate_flags_oblique_gate_pass():
    p = Project("t", 30, 30, 2, 0)
    p.auv = Auv(5, 5, 0, 1)
    g = p.add("gate", 20, 20, 0)
    p.waypoints = [Waypoint(g.x, g.y, 1, "PASS GATE")]
    assert any("miring" in msg for _l, msg, _s in p.validate())
