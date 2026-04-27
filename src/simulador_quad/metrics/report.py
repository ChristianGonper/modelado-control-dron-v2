import numpy as np
from typing import List, Dict, Any
from simulador_quad.core.contracts import TelemetrySample

def compute_metrics(telemetry: List[TelemetrySample], termination_reason: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    if not telemetry:
        return {}
        
    pos_errors = []
    control_efforts = []
    max_omegas = []
    sat_steps = 0
    
    # Supongamos que la velocidad máxima del rotor está en el primer rotor.
    # No tenemos acceso directo a omega_max en TelemetrySample, 
    # pero podemos contar como saturación si alguna omega_cmd > omega_applied.
    # O si omega_applied coincide con un valor límite (que asumimos constante).
    
    for sample in telemetry:
        # Error de posición
        p_err = np.linalg.norm(sample.reference.position_W_m - sample.state.position_W_m)
        pos_errors.append(p_err)
        
        # Esfuerzo de control (norma del comando)
        c_eff = np.abs(sample.control_command.collective_thrust_N) + np.linalg.norm(sample.control_command.body_moments_Nm)
        control_efforts.append(c_eff)
        
        # Max omega
        max_omega_step = np.max(sample.rotor_applied.applied_omega_rad_s)
        max_omegas.append(max_omega_step)
        
        # Saturación aproximada: si el comando objetivo es diferente del aplicado
        if not np.allclose(sample.rotor_command.target_omega_rad_s, sample.rotor_applied.applied_omega_rad_s, atol=1e-3):
            # El filtro de lag también hace que sean diferentes.
            # Una mejor métrica de saturación requeriría saber omega_max.
            # Lo dejamos simple por ahora.
            pass
            
    pos_errors = np.array(pos_errors)
    
    metrics = {
        "position_rmse_m": float(np.sqrt(np.mean(pos_errors**2))),
        "position_mae_m": float(np.mean(pos_errors)),
        "position_max_err_m": float(np.max(pos_errors)),
        "control_effort_mean": float(np.mean(control_efforts)),
        "max_rotor_speed_rad_s": float(np.max(max_omegas)),
        "termination_reason": termination_reason,
        "duration_s": float(telemetry[-1].time_s - telemetry[0].time_s),
    }
    
    if metadata:
        metrics["metadata"] = metadata
        
    return metrics
