import pytest
from simulador_quad.datasets.classic import pid_candidate_score, passes_hard_filters

def test_hard_filters():
    # Pass case
    metrics_ok = {
        "termination_reason": "Time limit reached",
        "saturation_percentage": 1.0,
        "degradation_percentage": 0.5,
        "position_max_err_m": 0.3,
        "position_rmse_m": 0.1,
        "collective_thrust_mean_N": 9.81,
        "body_moment_norm_mean_Nm": 0.05
    }
    ok, msg = passes_hard_filters(metrics_ok, "hold")
    assert ok
    
    # Fail case: termination
    m_fail = metrics_ok.copy()
    m_fail["termination_reason"] = "Crash"
    ok, msg = passes_hard_filters(m_fail, "hold")
    assert not ok
    assert "termination" in msg.lower()
    
    # Fail case: saturation
    m_fail = metrics_ok.copy()
    m_fail["saturation_percentage"] = 3.0
    ok, msg = passes_hard_filters(m_fail, "hold")
    assert not ok
    assert "saturation" in msg.lower()

    # Fail case: max err
    m_fail = metrics_ok.copy()
    m_fail["position_max_err_m"] = 0.5
    ok, msg = passes_hard_filters(m_fail, "hold")
    assert not ok
    assert "position error" in msg.lower()

def test_pid_score():
    from simulador_quad.core.frames import get_level_quaternion
    class MockState:
        def __init__(self):
            self.orientation_WB = get_level_quaternion(0.0) # Level
    class MockSample:
        def __init__(self):
            self.state = MockState()
            
    telemetry = [MockSample() for _ in range(10)]
    
    metrics = {
        "position_rmse_m": 0.1,
        "position_max_err_m": 0.2,
        "collective_thrust_mean_N": 9.81,  # 1.0 normalized
        "body_moment_norm_mean_Nm": 0.9,   # 9.0 normalized -> Total effort_norm = 10.0
        "saturation_percentage": 1.0,
        "degradation_percentage": 0.0
    }
    
    # Attitude RMS for level is 0
    score = pid_candidate_score(metrics, telemetry, "hold")
    
    # pos_rmse: 1.0 * 0.1 = 0.1
    # pos_max: 0.5 * 0.2 = 0.1
    # att_rms: 0.2 * 0.0 = 0.0
    # effort_norm: 0.1 * 10.0 = 1.0
    # sat: 2.0 * 0.01 = 0.02
    # deg: 2.0 * 0.0 = 0.0
    # Total: 0.1 + 0.1 + 0.0 + 1.0 + 0.02 + 0.0 = 1.22
    assert pytest.approx(score) == 1.22
