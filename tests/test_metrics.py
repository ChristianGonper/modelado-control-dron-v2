import numpy as np
import os
from simulador_quad.metrics.report import compute_metrics
from simulador_quad.telemetry.export import export_telemetry_json, export_metrics_json
from simulador_quad.core.contracts import TelemetrySample, VehicleState, TrajectoryReference, ControlCommand, RotorCommand, RotorAppliedState

def create_sample(time, pos, ref_pos, thrust, omega, body_moments=None, saturated=False, degraded=False):
    if body_moments is None:
        body_moments = np.zeros(3)
    state = VehicleState(pos, np.zeros(3), np.array([1,0,0,0]), np.zeros(3), time)
    ref = TrajectoryReference(ref_pos, np.zeros(3), np.zeros(3), 0.0)
    ctrl = ControlCommand(thrust, np.array(body_moments, dtype=float))
    rcmd = RotorCommand(
        target_thrust_N=np.array([thrust/4.0]*4),
        target_omega_rad_s=np.array([omega]*4),
        degraded_collective_thrust=degraded
    )
    rapp = RotorAppliedState(
        applied_omega_rad_s=np.array([omega]*4),
        applied_thrust_N=np.array([thrust/4.0]*4),
        applied_torque_Nm=np.zeros(4),
        rotor_speed_rpm=np.array([omega * 60 / (2*np.pi)]*4),
        saturation_flags=np.array([saturated, False, False, False], dtype=bool)
    )
    return TelemetrySample(
        time_s=time,
        state=state,
        observation=state,
        reference=ref,
        control_command=ctrl,
        rotor_command=rcmd,
        rotor_applied=rapp
    )

def test_metrics_computation():
    # 2 muestras sintéticas
    s1 = create_sample(
        0.0,
        np.zeros(3),
        np.array([1.0, 0.0, 0.0]),
        10.0,
        10.0,
        body_moments=np.array([3.0, 4.0, 0.0]),
    )
    s2 = create_sample(
        1.0,
        np.array([0.5, 0.0, 0.0]),
        np.array([1.0, 0.0, 0.0]),
        20.0,
        20.0,
        body_moments=np.array([0.0, 0.0, 2.0]),
        saturated=True,
        degraded=True,
    )
    
    telemetry = [s1, s2]
    metrics = compute_metrics(telemetry, "Success")
    
    # Error s1: 1.0, Error s2: 0.5
    # MSE = (1.0^2 + 0.5^2) / 2 = 0.625
    # RMSE = sqrt(0.625) ~ 0.7905
    assert np.isclose(metrics["position_rmse_m"], np.sqrt(0.625))
    assert np.isclose(metrics["position_mae_m"], 0.75)
    assert np.isclose(metrics["position_max_err_m"], 1.0)
    assert np.isclose(metrics["collective_thrust_mean_N"], 15.0)
    assert np.isclose(metrics["collective_thrust_max_N"], 20.0)
    assert np.isclose(metrics["collective_thrust_min_N"], 10.0)
    assert np.isclose(metrics["body_moment_norm_mean_Nm"], 3.5)
    assert np.isclose(metrics["body_moment_norm_max_Nm"], 5.0)
    assert np.isclose(metrics["control_effort_heuristic_mean"], 18.5)
    assert np.isclose(metrics["control_effort_mean"], 18.5)
    assert np.isclose(metrics["max_rotor_speed_rad_s"], 20.0)
    assert np.isclose(metrics["saturation_percentage"], 50.0)
    assert np.isclose(metrics["degradation_percentage"], 50.0)
    assert metrics["duration_s"] == 1.0
    
def test_exports(tmp_path):
    s1 = create_sample(0.0, np.zeros(3), np.array([1.0, 0.0, 0.0]), 10.0, 10.0)
    tel_file = os.path.join(tmp_path, "tel.json")
    met_file = os.path.join(tmp_path, "met.json")
    
    export_telemetry_json([s1], tel_file)
    export_metrics_json({"test": 1.0}, met_file)
    
    assert os.path.exists(tel_file)
    assert os.path.exists(met_file)
