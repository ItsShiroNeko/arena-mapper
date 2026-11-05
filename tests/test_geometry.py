import math

import pytest

from auv_mapper.geometry import auv_poly, bearing, fit_view, lw, seg_dist, vec, wrap180
from auv_mapper.utils import fmt, fmt_time, hex_rgb, mix, slug


def test_bearing_convention():
    assert bearing(0, 1) == pytest.approx(0)      # +y = 0 deg
    assert bearing(1, 0) == pytest.approx(90)     # +x = 90 deg
    assert bearing(0, -1) == pytest.approx(180)
    assert bearing(-1, 0) == pytest.approx(270)


def test_vec_is_inverse_of_bearing():
    for b in (0, 37, 90, 181, 359):
        dx, dy = vec(b)
        assert bearing(dx, dy) == pytest.approx(b % 360)


def test_wrap180():
    assert wrap180(190) == pytest.approx(-170)
    assert wrap180(-190) == pytest.approx(170)
    assert wrap180(0) == 0


def test_local_to_world_heading_east():
    # heading 90 deg (east): "forward" is +x, "right" is -y
    x, y = lw(0, 0, 90, 0, 1)
    assert (round(x, 6), round(y, 6)) == (1.0, 0.0)
    x, y = lw(0, 0, 90, 1, 0)
    assert (round(x, 6), round(y, 6)) == (0.0, -1.0)


def test_seg_dist():
    assert seg_dist(0, 1, -1, 0, 1, 0) == pytest.approx(1)
    assert seg_dist(3, 0, 0, 0, 1, 0) == pytest.approx(2)   # clamps to endpoint
    assert seg_dist(1, 1, 0, 0, 0, 0) == pytest.approx(math.sqrt(2))  # degenerate segment


def test_auv_poly_has_three_vertices():
    assert len(auv_poly(1, 1, 0)) == 3


def test_fit_view_keeps_pool_inside_canvas():
    s, ox, oy = fit_view(50, 25, 1000, 600)
    assert ox >= 0 and oy <= 600
    assert ox + 50 * s <= 1000
    assert oy - 25 * s >= 0


def test_utils():
    assert hex_rgb("#ff8000") == (255, 128, 0)
    assert mix("#000000", "#ffffff", 1.0) == "#000000"
    assert fmt(1.50) == "1.5" and fmt(2.0) == "2" and fmt(-0.0) == "0" and fmt("a") == "a"
    assert fmt_time(125) == "2:05"
    assert slug("Proyek AUV #1") == "Proyek_AUV_1"
    assert slug("***") == "proyek"
