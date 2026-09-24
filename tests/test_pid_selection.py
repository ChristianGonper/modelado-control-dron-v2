import pytest
from simulador_quad.api.pid_selection import select_pid_for_mission


def test_simple_mission_pids():
    assert select_pid_for_mission("simple", "hold", {})[0] == "hold"
    assert select_pid_for_mission("simple", "circle", {})[0] == "circle"
    assert select_pid_for_mission("simple", "lissajous", {})[0] == "lissajous"
    assert select_pid_for_mission("simple", "waypoint", {})[0] == "waypoint"
    assert select_pid_for_mission("simple", "lemniscate", {})[0] == "lissajous"


def test_composite_all_hold():
    segments = [
        {"type": "hold", "duration": 5.0, "params": {"position_W_m": [0, 0, 1.5]}},
        {"type": "hold", "duration": 4.0, "params": {"position_W_m": [1, 0, 1.5]}},
    ]
    pid, exp, lengths = select_pid_for_mission("composite", "composite", {}, segments)
    assert pid == "hold"
    assert "estacionaria" in exp.lower()


def test_composite_dominant_family():
    # Circle has 10s at R=1.5, w=0.6 -> length = 9.0 m
    # Waypoint has 3.0 m
    segments = [
        {"type": "waypoint", "duration": 4.0, "params": {"waypoints": [[0, 0, 2], [3, 0, 2]]}},
        {"type": "circle", "duration": 10.0, "params": {"radius_m": 1.5, "omega_rad_s": 0.6}},
    ]
    pid, exp, lengths = select_pid_for_mission("composite", "composite", {}, segments)
    assert pid == "circle"
    assert "Circle" in exp
    assert lengths["circle"] > lengths["waypoint"]


def test_composite_tie_resolution():
    # Segment 1: waypoint length = 4.0 m
    # Segment 2: waypoint length = 0 m (dummy)
    # Let's create exact tie between circle and waypoint
    # Circle: R=2.0, w=0.5, dur=4.0 -> length = 4.0 m
    # Waypoint: [[0,0,2], [4,0,2]] -> length = 4.0 m
    segments_wp_first = [
        {"type": "waypoint", "duration": 5.0, "params": {"waypoints": [[0, 0, 2], [4, 0, 2]]}},
        {"type": "circle", "duration": 4.0, "params": {"radius_m": 2.0, "omega_rad_s": 0.5}},
    ]
    pid1, exp1, _ = select_pid_for_mission("composite", "composite", {}, segments_wp_first)
    assert pid1 == "waypoint"
    assert "desempate" in exp1.lower()

    segments_circle_first = [
        {"type": "circle", "duration": 4.0, "params": {"radius_m": 2.0, "omega_rad_s": 0.5}},
        {"type": "waypoint", "duration": 5.0, "params": {"waypoints": [[0, 0, 2], [4, 0, 2]]}},
    ]
    pid2, exp2, _ = select_pid_for_mission("composite", "composite", {}, segments_circle_first)
    assert pid2 == "circle"
    assert "desempate" in exp2.lower()


def test_composite_lemniscate_maps_to_lissajous():
    segments = [
        {"type": "hold", "duration": 2.0, "params": {"position_W_m": [0, 0, 2]}},
        {"type": "lemniscate", "duration": 15.0, "params": {"a": 2.5, "b": 1.25, "omega_rad_s": 0.5}},
    ]
    pid, exp, lengths = select_pid_for_mission("composite", "composite", {}, segments)
    assert pid == "lissajous"
    assert "Lemniscata" in exp
