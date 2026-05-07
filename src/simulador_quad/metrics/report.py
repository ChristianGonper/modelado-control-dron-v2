import numpy as np
from typing import List, Dict, Any
from simulador_quad.core.contracts import TelemetrySample


def compute_metrics(telemetry: List[TelemetrySample], termination_reason: str, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
    if not telemetry:
        return {}
        
    pos_errors = []
    collective_thrusts_N = []
    body_moment_norms_Nm = []
    control_efforts = []
    max_omegas = []
    max_rpms = []
    sat_samples = 0
    degraded_samples = 0
    
    dt_telemetry = 0.1 # Valor por defecto si no se puede calcular
    if len(telemetry) > 1:
        dt_telemetry = telemetry[1].time_s - telemetry[0].time_s
    
    for sample in telemetry:
        # Error de posición
        p_err = np.linalg.norm(sample.reference.position_W_m - sample.state.position_W_m)
        pos_errors.append(p_err)
        
        # Magnitudes de control separadas por unidad física.
        collective_thrust_N = float(sample.control_command.collective_thrust_N)
        body_moment_norm_Nm = float(np.linalg.norm(sample.control_command.body_moments_Nm))
        collective_thrusts_N.append(collective_thrust_N)
        body_moment_norms_Nm.append(body_moment_norm_Nm)

        # Índice heurístico heredado: mezcla N y Nm, por tanto no debe usarse
        # como argumento físico principal.
        c_eff = np.abs(collective_thrust_N) + body_moment_norm_Nm
        control_efforts.append(c_eff)
        
        # Max omega y RPM
        max_omega_step = np.max(sample.rotor_applied.applied_omega_rad_s)
        max_omegas.append(max_omega_step)
        max_rpms.append(np.max(sample.rotor_applied.rotor_speed_rpm))
        
        # Saturación y degradación
        if np.any(sample.rotor_applied.saturation_flags):
            sat_samples += 1
        if sample.rotor_command.degraded_collective_thrust:
            degraded_samples += 1
            
    pos_errors = np.array(pos_errors)
    collective_thrusts_N = np.array(collective_thrusts_N)
    body_moment_norms_Nm = np.array(body_moment_norms_Nm)
    control_efforts = np.array(control_efforts)
    
    metrics = {
        "position_rmse_m": float(np.sqrt(np.mean(pos_errors**2))),
        "position_mae_m": float(np.mean(pos_errors)),
        "position_max_err_m": float(np.max(pos_errors)),
        "position_std_err_m": float(np.std(pos_errors)),
        "collective_thrust_mean_N": float(np.mean(collective_thrusts_N)),
        "collective_thrust_max_N": float(np.max(collective_thrusts_N)),
        "collective_thrust_min_N": float(np.min(collective_thrusts_N)),
        "collective_thrust_std_N": float(np.std(collective_thrusts_N)),
        "body_moment_norm_mean_Nm": float(np.mean(body_moment_norms_Nm)),
        "body_moment_norm_max_Nm": float(np.max(body_moment_norms_Nm)),
        "body_moment_norm_std_Nm": float(np.std(body_moment_norms_Nm)),
        "control_effort_heuristic_mean": float(np.mean(control_efforts)),
        "control_effort_heuristic_max": float(np.max(control_efforts)),
        "control_effort_heuristic_std": float(np.std(control_efforts)),
        "control_effort_mean": float(np.mean(control_efforts)),
        "control_effort_max": float(np.max(control_efforts)),
        "control_effort_std": float(np.std(control_efforts)),
        "max_rotor_speed_rad_s": float(np.max(max_omegas)),
        "max_rotor_speed_rpm": float(np.max(max_rpms)),
        "saturation_duration_s": float(sat_samples * dt_telemetry),
        "saturation_percentage": float(sat_samples / len(telemetry) * 100.0),
        "degradation_duration_s": float(degraded_samples * dt_telemetry),
        "degradation_percentage": float(degraded_samples / len(telemetry) * 100.0),
        "termination_reason": termination_reason,
        "duration_s": float(telemetry[-1].time_s - telemetry[0].time_s),
    }
    
    if metadata:
        metrics["metadata"] = metadata
        
    return metrics
