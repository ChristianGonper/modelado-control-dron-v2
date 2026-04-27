import json
import numpy as np
from typing import List, Dict, Any
from simulador_quad.core.contracts import TelemetrySample

class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.integer):
            return int(obj)
        return super(NumpyEncoder, self).default(obj)

def export_telemetry_json(telemetry: List[TelemetrySample], filepath: str):
    data = []
    for s in telemetry:
        data.append({
            "time_s": s.time_s,
            "state": {
                "position_W_m": s.state.position_W_m,
                "velocity_W_m_s": s.state.velocity_W_m_s,
                "orientation_WB": s.state.orientation_WB,
                "angular_velocity_B_rad_s": s.state.angular_velocity_B_rad_s,
            },
            "reference": {
                "position_W_m": s.reference.position_W_m,
                "velocity_W_m_s": s.reference.velocity_W_m_s,
                "acceleration_W_m_s2": s.reference.acceleration_W_m_s2,
                "yaw_rad": s.reference.yaw_rad,
            },
            "control": {
                "collective_thrust_N": s.control_command.collective_thrust_N,
                "body_moments_Nm": s.control_command.body_moments_Nm,
            },
            "rotors": {
                "target_omega_rad_s": s.rotor_command.target_omega_rad_s,
                "applied_omega_rad_s": s.rotor_applied.applied_omega_rad_s,
            }
        })
        
    with open(filepath, 'w') as f:
        json.dump(data, f, cls=NumpyEncoder, indent=2)

def export_metrics_json(metrics: Dict[str, Any], filepath: str):
    with open(filepath, 'w') as f:
        json.dump(metrics, f, cls=NumpyEncoder, indent=2)
