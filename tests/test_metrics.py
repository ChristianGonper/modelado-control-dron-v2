import numpy as np
import os
from simulador_quad.metrics.report import compute_metrics
from simulador_quad.telemetry.export import export_telemetry_json, export_metrics_json
from simulador_quad.core.contracts import TelemetrySample, VehicleState, TrajectoryReference, ControlCommand, RotorCommand, RotorAppliedState

def test_metrics_computation():
    telemetry = []
    
    # 2 muestras sintéticas
    s1 = TelemetrySample(
        time_s=0.0,
        state=VehicleState(np.zeros(3), np.zeros(3), np.array([1,0,0,0]), np.zeros(3), 0.0),
        reference=TrajectoryReference(np.array([1.0, 0.0, 0.0]), np.zeros(3), np.zeros(3), 0.0),
        control_command=ControlCommand(10.0, np.zeros(3)),
        rotor_command=RotorCommand(np.array([10.0]*4)),
        rotor_applied=RotorAppliedState(np.array([10.0]*4), np.zeros(4), np.zeros(4))
    )
    
    s2 = TelemetrySample(
        time_s=1.0,
        state=VehicleState(np.array([0.5, 0.0, 0.0]), np.zeros(3), np.array([1,0,0,0]), np.zeros(3), 1.0),
        reference=TrajectoryReference(np.array([1.0, 0.0, 0.0]), np.zeros(3), np.zeros(3), 0.0),
        control_command=ControlCommand(20.0, np.zeros(3)),
        rotor_command=RotorCommand(np.array([20.0]*4)),
        rotor_applied=RotorAppliedState(np.array([20.0]*4), np.zeros(4), np.zeros(4))
    )
    
    telemetry = [s1, s2]
    
    metrics = compute_metrics(telemetry, "Success")
    
    # Error s1: 1.0, Error s2: 0.5
    # MSE = (1.0^2 + 0.5^2) / 2 = 1.25 / 2 = 0.625
    # RMSE = sqrt(0.625) ~ 0.7905
    assert np.isclose(metrics["position_rmse_m"], np.sqrt(0.625))
    assert np.isclose(metrics["position_mae_m"], 0.75)
    assert np.isclose(metrics["position_max_err_m"], 1.0)
    assert np.isclose(metrics["control_effort_mean"], 15.0)
    assert np.isclose(metrics["max_rotor_speed_rad_s"], 20.0)
    assert metrics["duration_s"] == 1.0
    
def test_exports(tmp_path):
    s1 = TelemetrySample(
        time_s=0.0,
        state=VehicleState(np.zeros(3), np.zeros(3), np.array([1,0,0,0]), np.zeros(3), 0.0),
        reference=TrajectoryReference(np.array([1.0, 0.0, 0.0]), np.zeros(3), np.zeros(3), 0.0),
        control_command=ControlCommand(10.0, np.zeros(3)),
        rotor_command=RotorCommand(np.array([10.0]*4)),
        rotor_applied=RotorAppliedState(np.array([10.0]*4), np.zeros(4), np.zeros(4))
    )
    tel_file = os.path.join(tmp_path, "tel.json")
    met_file = os.path.join(tmp_path, "met.json")
    
    export_telemetry_json([s1], tel_file)
    export_metrics_json({"test": 1.0}, met_file)
    
    assert os.path.exists(tel_file)
    assert os.path.exists(met_file)
