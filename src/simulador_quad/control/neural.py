"""
Controlador neuronal para integracion en el simulador.
"""

import torch
import numpy as np
import yaml
from pathlib import Path
from collections import deque
from simulador_quad.control.contract import Controller
from simulador_quad.core.contracts import ControlCommand, VehicleState, TrajectoryReference
from simulador_quad.ml.models import build_model
from simulador_quad.ml.normalization import Normalizer
from simulador_quad.ml.dataset import (
    build_feature_vector,
    build_outer_force_min_features_from_observation,
    build_outer_force_full_features_from_observation,
    OUTER_FORCE_MIN_V1_NAMES,
    OUTER_FORCE_FULL_V1_NAMES,
    TARGET_FORCE_NAMES,
)
from simulador_quad.control.classic import ClassicCascadeController


def _resolve_torch_device(device: str = "auto") -> str:
    if device == "auto":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cuda" and not torch.cuda.is_available():
        raise RuntimeError("CUDA requested, but torch.cuda.is_available() is False")
    return device


class NeuralController(Controller):
    """
    Implementa el contrato de Controller usando una red neuronal entrenada.
    """
    def __init__(self, 
                 checkpoint_path: str, 
                 normalization_path: str, 
                 architecture: str = "mlp", 
                 sequence_length: int = 20,
                 clip_to_classic_limits: bool = True,
                 mass_kg: float = 1.0,
                 gravity_m_s2: float = 9.81,
                 max_moments_Nm: np.ndarray = np.array([10.0, 10.0, 2.0]),
                 device: str = "auto"):
        self.architecture = architecture
        self.sequence_length = sequence_length
        self.clip_to_classic_limits = clip_to_classic_limits
        self.mass = mass_kg
        self.g = gravity_m_s2
        self.max_moments = max_moments_Nm
        self.device = _resolve_torch_device(device)
        
        # Cargar normalizador
        self.normalizer = Normalizer.load(normalization_path).to(self.device)
        
        # Cargar modelo
        # Deducir input_dim del normalizador cargado
        input_dim = len(self.normalizer.mean_x)
        output_dim = 4
        
        # Podriamos intentar cargar hidden_dim del config.yaml si esta al lado del checkpoint
        config_path = Path(checkpoint_path).parent.parent / "config.yaml"
        config = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)
        
        # Validacion de consistencia
        if "input_dim" in config and config["input_dim"] != input_dim:
            raise ValueError(f"Input dim mismatch: model config has {config['input_dim']}, but normalizer has {input_dim}")

        self.model = build_model(architecture, input_dim, output_dim, config).to(self.device)
        self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        self.model.eval()
        
        # Estado recurrente para GRU/LSTM
        self.window = deque(maxlen=sequence_length)
        self.reset()
    
    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        """Ejecuta inferencia y devuelve comando de control."""
        # 1. Construir features
        x = build_feature_vector(
            obs_state.position_W_m,
            obs_state.velocity_W_m_s,
            obs_state.orientation_WB,
            obs_state.angular_velocity_B_rad_s,
            reference.position_W_m,
            reference.velocity_W_m_s,
            reference.acceleration_W_m_s2,
            reference.yaw_rad
        )
        
        # 2. Normalizar
        x_norm = self.normalizer.normalize_x(torch.tensor(x, dtype=torch.float32, device=self.device))
        
        # 3. Preparar entrada segun arquitectura
        if self.architecture == "mlp":
            model_input = x_norm.unsqueeze(0) # [1, input_dim]
        else:
            self.window.append(x_norm)
            # Si no tenemos suficiente historia, rellenamos con la primera muestra
            while len(self.window) < self.sequence_length:
                self.window.appendleft(x_norm)
            
            model_input = torch.stack(list(self.window)).unsqueeze(0) # [1, seq_len, input_dim]
        
        # 4. Inferencia
        with torch.no_grad():
            y_norm = self.model(model_input).squeeze(0) # [4]
        
        # 5. Desnormalizar
        y = self.normalizer.denormalize_y(y_norm).cpu().numpy()
        
        thrust = float(y[0])
        moments = y[1:4]
        
        # 6. Clipping (opcional)
        if self.clip_to_classic_limits:
            # Limites compatibles con el controlador clasico efectivo
            max_thrust = self.mass * self.g * 2.5
            thrust = np.clip(thrust, 0.0, max_thrust)
            moments = np.clip(moments, -self.max_moments, self.max_moments)
            
        return ControlCommand(thrust, moments)

    def reset(self):
        """Limpia estado interno (importante para GRU/LSTM)."""
        self.window.clear()


class NeuralPositionController(Controller):
    """
    Controlador hibrido: la red programa ganancias del lazo externo de posicion
    y el lazo interno de actitud permanece como el clasico.
    """
    def __init__(
        self,
        checkpoint_path: str,
        normalization_path: str,
        architecture: str = "mlp",
        sequence_length: int = 20,
        mass_kg: float = 1.0,
        gravity_m_s2: float = 9.81,
        inertia_B_kg_m2: np.ndarray | None = None,
        base_Kp_pos: np.ndarray | None = None,
        base_Kd_pos: np.ndarray | None = None,
        Kp_att: np.ndarray | None = None,
        Kd_att: np.ndarray | None = None,
        max_body_moments_Nm: np.ndarray | None = None,
        multiplier_clip: np.ndarray | None = None,
        device: str = "auto",
    ):
        self.architecture = architecture
        self.sequence_length = sequence_length
        self.device = _resolve_torch_device(device)
        self.base_Kp_pos = np.array(base_Kp_pos if base_Kp_pos is not None else [2.0, 2.0, 5.0], dtype=float)
        self.base_Kd_pos = np.array(base_Kd_pos if base_Kd_pos is not None else [1.0, 1.0, 2.0], dtype=float)
        self.multiplier_clip = np.array(multiplier_clip if multiplier_clip is not None else [0.25, 4.0], dtype=float)
        if self.multiplier_clip.shape != (2,) or self.multiplier_clip[0] <= 0.0 or self.multiplier_clip[1] < self.multiplier_clip[0]:
            raise ValueError("multiplier_clip must be [min_positive, max] with max >= min")

        inertia = np.eye(3) if inertia_B_kg_m2 is None else inertia_B_kg_m2
        self.classic_inner = ClassicCascadeController(
            mass_kg,
            gravity_m_s2,
            inertia,
            Kp_pos=self.base_Kp_pos,
            Kd_pos=self.base_Kd_pos,
            Kp_att=Kp_att,
            Kd_att=Kd_att,
            max_body_moments_Nm=max_body_moments_Nm,
        )

        self.normalizer = Normalizer.load(normalization_path).to(self.device)
        input_dim = len(self.normalizer.mean_x)
        output_dim = 6

        config_path = Path(checkpoint_path).parent.parent / "config.yaml"
        config = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f)

        if "input_dim" in config and config["input_dim"] != input_dim:
            raise ValueError(f"Input dim mismatch: model config has {config['input_dim']}, but normalizer has {input_dim}")
        if "output_dim" in config and config["output_dim"] != output_dim:
            raise ValueError(f"Output dim mismatch: model config has {config['output_dim']}, expected {output_dim}")

        self.model = build_model(architecture, input_dim, output_dim, config).to(self.device)
        self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        self.model.eval()

        self.window = deque(maxlen=sequence_length)
        self.last_gain_multipliers = np.ones(6)
        self.last_Kp_pos = self.base_Kp_pos.copy()
        self.last_Kd_pos = self.base_Kd_pos.copy()
        self.reset()

    def _predict_gain_multipliers(self, obs_state: VehicleState, reference: TrajectoryReference) -> np.ndarray:
        x = build_feature_vector(
            obs_state.position_W_m,
            obs_state.velocity_W_m_s,
            obs_state.orientation_WB,
            obs_state.angular_velocity_B_rad_s,
            reference.position_W_m,
            reference.velocity_W_m_s,
            reference.acceleration_W_m_s2,
            reference.yaw_rad,
        )
        x_norm = self.normalizer.normalize_x(torch.tensor(x, dtype=torch.float32, device=self.device))

        if self.architecture == "mlp":
            model_input = x_norm.unsqueeze(0)
        else:
            self.window.append(x_norm)
            while len(self.window) < self.sequence_length:
                self.window.appendleft(x_norm)
            model_input = torch.stack(list(self.window)).unsqueeze(0)

        with torch.no_grad():
            y_norm = self.model(model_input).squeeze(0)

        log_multipliers = self.normalizer.denormalize_y(y_norm).cpu().numpy()
        multipliers = np.exp(log_multipliers)
        return np.clip(multipliers, self.multiplier_clip[0], self.multiplier_clip[1])

    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        multipliers = self._predict_gain_multipliers(obs_state, reference)
        kp_pos = self.base_Kp_pos * multipliers[:3]
        kd_pos = self.base_Kd_pos * multipliers[3:6]

        self.last_gain_multipliers = multipliers
        self.last_Kp_pos = kp_pos
        self.last_Kd_pos = kd_pos

        return self.classic_inner.compute_control_with_position_gains(obs_state, reference, kp_pos, kd_pos)

    def reset(self):
        self.window.clear()
        self.last_gain_multipliers = np.ones(6)
        self.last_Kp_pos = self.base_Kp_pos.copy()
        self.last_Kd_pos = self.base_Kd_pos.copy()


class NeuralOuterForceController(Controller):
    """
    Controlador hibrido (nuevo significado de type:"neural"):
    - La red predice desired_force_W_N[3] (lazo externo) desde observation.
    - Aplica clipping de norma (thrust max) preservando direccion y de tilt (angulo max)
      manteniendo Fz y limitando componente horizontal (cuando clip_to_classic_limits=True).
    - Delega conversion fuerza->actitud + PID actitud + saturacion momentos al ClassicCascadeController
      via compute_control_from_desired_force_W (sin duplicar ecuaciones).
    - Rechaza explicitamente checkpoints legacy 4-output (thrust+moments) y 6-output (neural_position).
    - feature_version: outer_force_min_v1 (9) o outer_force_full_v1 (31), siempre desde observation.
    Note: clip_to_classic_limits (default True) gates the outer force norm+tilt safety limits.
    The max_desired_tilt_rad / max_thrust are always used as the physical bounds when clipping is enabled.
    """

    def __init__(
        self,
        checkpoint_path: str,
        normalization_path: str,
        architecture: str = "mlp",
        feature_version: str = "outer_force_min_v1",
        sequence_length: int = 20,
        clip_to_classic_limits: bool = True,
        max_desired_tilt_rad: float = 0.52,
        mass_kg: float = 1.0,
        gravity_m_s2: float = 9.81,
        inertia_B_kg_m2: np.ndarray | None = None,
        Kp_att: np.ndarray | None = None,
        Kd_att: np.ndarray | None = None,
        max_body_moments_Nm: np.ndarray | None = None,
        device: str = "auto",
    ):
        self.architecture = architecture
        self.feature_version = feature_version
        self.sequence_length = sequence_length
        self.clip_to_classic_limits = clip_to_classic_limits
        self.mass = mass_kg
        self.g = gravity_m_s2
        self.device = _resolve_torch_device(device)

        if not (0.0 < max_desired_tilt_rad < np.pi / 2):
            raise ValueError("max_desired_tilt_rad must be in (0, pi/2)")
        self.max_desired_tilt_rad = float(max_desired_tilt_rad)
        self.max_thrust = mass_kg * gravity_m_s2 * 2.5

        inertia = np.eye(3) if inertia_B_kg_m2 is None else np.asarray(inertia_B_kg_m2, dtype=float)
        self.classic_inner = ClassicCascadeController(
            mass_kg,
            gravity_m_s2,
            inertia,
            Kp_pos=np.array([1.0, 1.0, 1.0]),  # dummy, not used for outer-force path
            Kd_pos=np.array([1.0, 1.0, 1.0]),
            Kp_att=Kp_att,
            Kd_att=Kd_att,
            max_body_moments_Nm=max_body_moments_Nm,
        )

        # Normalizer + model + early rejection of legacy checkpoints
        self.normalizer = Normalizer.load(normalization_path).to(self.device)
        input_dim = len(self.normalizer.mean_x)
        expected_out = 3

        config_path = Path(checkpoint_path).parent.parent / "config.yaml"
        config = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config = yaml.safe_load(f) or {}

        cfg_out_dim = config.get("output_dim")
        cfg_mode = config.get("controller_mode")
        cfg_target_ver = config.get("target_version")
        cfg_target_names = config.get("target_names", [])

        def _infer_output_dim_from_state_dict(sd: dict) -> int | None:
            """Robustly find the output dimension even for bare GRU/LSTM/ML P checkpoints."""
            # Prefer the explicit final projection layer that all our models have
            for k in sd:
                if k.endswith("fc.weight") or k.endswith(".fc.weight"):
                    if hasattr(sd[k], "shape") and len(sd[k].shape) == 2:
                        return int(sd[k].shape[0])
            # MLP sequential case
            for k in sd:
                if "net.4.weight" in k or k.endswith("net.4.weight"):
                    if hasattr(sd[k], "shape") and len(sd[k].shape) == 2:
                        return int(sd[k].shape[0])
            # Last resort: largest plausible output dim among 2D weights that look like projections
            candidates = []
            for k, v in sd.items():
                if "weight" in k and hasattr(v, "shape") and len(v.shape) == 2:
                    out = int(v.shape[0])
                    if out in (3, 4, 6):
                        candidates.append((out, k))
            if candidates:
                # Prefer 3/4/6; if multiple, take the one that is not an internal recurrent weight
                for out, k in sorted(candidates, key=lambda x: -x[0]):
                    if "fc" in k or "out" in k or "proj" in k or "net" in k:
                        return out
                return candidates[0][0]
            return None

        inferred_out = None
        if cfg_out_dim is None:
            try:
                sd = torch.load(checkpoint_path, map_location="cpu")
                inferred_out = _infer_output_dim_from_state_dict(sd)
            except Exception:
                inferred_out = None  # best effort only

        # Now raise clear, explicit rejections (these must never be swallowed)
        if inferred_out == 4 or cfg_out_dim == 4:
            raise ValueError(
                "Legacy 4-output neural checkpoint (thrust + body moments) loaded under type 'neural'. "
                "The 'neural' type now exclusively predicts desired_force_W_N[3]. "
                "Legacy 4-output checkpoints are not supported or migrated; "
                "retrain under the outer-force contract or use type='neural_position'."
            )
        if inferred_out == 6 or cfg_out_dim == 6 or cfg_mode == "neural_position" or "neural_position" in str(checkpoint_path).lower():
            raise ValueError(
                "Neural position-gain (6-output) checkpoint loaded as type 'neural' (outer-force). "
                "Use controller.type='neural_position' for models that output gain multipliers."
            )
        if cfg_out_dim is not None and cfg_out_dim != 3:
            raise ValueError(f"Checkpoint output_dim={cfg_out_dim} incompatible with neural outer-force (requires 3).")
        if cfg_mode and cfg_mode != "neural_outer_force":
            raise ValueError(f"Checkpoint controller_mode={cfg_mode} != 'neural_outer_force'. Incompatible with type='neural'.")

        # Normalizer sanity for force targets (best effort)
        tnames = getattr(self.normalizer, "target_names", None) or cfg_target_names
        if tnames:
            tnames_l = [str(t).lower() for t in tnames]
            if any("thrust" in t or "moment" in t for t in tnames_l):
                raise ValueError("Normalizer target names are inconsistent with desired_force_W_N targets.")

        self.model = build_model(architecture, input_dim, expected_out, config).to(self.device)
        self.model.load_state_dict(torch.load(checkpoint_path, map_location=self.device))
        self.model.eval()

        self.window = deque(maxlen=sequence_length)
        self._clip_norm_count = 0
        self._clip_tilt_count = 0
        self._total_steps = 0
        self.last_desired_force_W_N = np.zeros(3, dtype=float)
        self.last_clipped_force_W_N = np.zeros(3, dtype=float)
        self.reset()

    def _predict_desired_force_W_N(self, obs_state: VehicleState, reference: TrajectoryReference) -> np.ndarray:
        if self.feature_version.startswith("outer_force_min"):
            obs_d = {
                "position_W_m": list(np.asarray(obs_state.position_W_m, dtype=float)),
                "velocity_W_m_s": list(np.asarray(obs_state.velocity_W_m_s, dtype=float)),
                "orientation_WB": list(np.asarray(obs_state.orientation_WB, dtype=float)),
                "angular_velocity_B_rad_s": list(np.asarray(obs_state.angular_velocity_B_rad_s, dtype=float)),
            }
            ref_d = {
                "position_W_m": list(np.asarray(reference.position_W_m, dtype=float)),
                "velocity_W_m_s": list(np.asarray(reference.velocity_W_m_s, dtype=float)),
                "acceleration_W_m_s2": list(np.asarray(reference.acceleration_W_m_s2, dtype=float)),
                "yaw_rad": float(reference.yaw_rad),
            }
            x = build_outer_force_min_features_from_observation(obs_d, ref_d)
        else:
            # full: reuse existing builder from arrays (same values as observation)
            x = build_feature_vector(
                obs_state.position_W_m,
                obs_state.velocity_W_m_s,
                obs_state.orientation_WB,
                obs_state.angular_velocity_B_rad_s,
                reference.position_W_m,
                reference.velocity_W_m_s,
                reference.acceleration_W_m_s2,
                reference.yaw_rad,
            )

        x_t = torch.tensor(np.asarray(x, dtype=np.float32), device=self.device)
        x_norm = self.normalizer.normalize_x(x_t)

        if self.architecture == "mlp":
            model_input = x_norm.unsqueeze(0)
        else:
            self.window.append(x_norm)
            while len(self.window) < self.sequence_length:
                self.window.appendleft(x_norm)
            model_input = torch.stack(list(self.window)).unsqueeze(0)

        with torch.no_grad():
            y_norm = self.model(model_input).squeeze(0)

        y = self.normalizer.denormalize_y(y_norm).cpu().numpy()
        return np.asarray(y, dtype=float)[:3]

    def _limit_desired_force_W_N(self, f_W: np.ndarray) -> tuple[np.ndarray, bool, bool]:
        """Norm clip (scale dir preserved) then tilt clip (preserve Fz, reduce horiz).

        Final hard guarantee: the returned force always has Fz >= 0.20 * mass * g
        (positive upward lift). Non-positive vertical requests are projected to this
        minimum before being passed to the classic attitude converter. This
        prevents inverted or zero-lift desired attitudes in the simulator.
        """
        f = np.asarray(f_W, dtype=float).copy()
        clipped_norm = False
        clipped_tilt = False

        # 1. Thrust/norm limit (direction preserving)
        n = np.linalg.norm(f)
        if n > self.max_thrust + 1e-12:
            f *= (self.max_thrust / n)
            clipped_norm = True

        # 2. Tilt limit (Fz preserved)
        n = np.linalg.norm(f)
        if n > 1e-12:
            uz = float(np.clip(f[2] / n, -1.0, 1.0))
            tilt = float(np.arccos(uz))
            if tilt > self.max_desired_tilt_rad + 1e-12:
                clipped_tilt = True
                fz = f[2]
                fh = f[:2].copy()
                hnorm = np.linalg.norm(fh)
                if hnorm > 1e-12:
                    if abs(fz) > 1e-9:
                        max_h = abs(fz) * float(np.tan(self.max_desired_tilt_rad))
                        fh *= (max_h / hnorm)
                    else:
                        # fz ~ 0 edge: enforce tilt limit by zeroing horizontal (pure vertical request, tilt=0)
                        fh = np.zeros(2, dtype=float)
                    f[:2] = fh
                    # Fz unchanged (or 0) by design; tilt now guaranteed <= max

        # Final hard safety guard: never emit Fz <= 0 (or very small positive) to the
        # classic attitude converter. A non-positive vertical force produces an
        # inverted or zero-lift desired attitude.
        min_safe_fz = self.mass * self.g * 0.20  # at least 20% of hover thrust upward
        if f[2] <= min_safe_fz:
            clipped_tilt = True
            f[2] = min_safe_fz
            # Re-apply horizontal limiting so the final direction still respects max tilt
            n2 = np.linalg.norm(f)
            if n2 > 1e-12:
                uz2 = float(np.clip(f[2] / n2, -1.0, 1.0))
                tilt2 = float(np.arccos(uz2))
                if tilt2 > self.max_desired_tilt_rad + 1e-12:
                    fh2 = f[:2].copy()
                    hnorm2 = np.linalg.norm(fh2)
                    if hnorm2 > 1e-12:
                        max_h2 = abs(f[2]) * float(np.tan(self.max_desired_tilt_rad))
                        fh2 *= (max_h2 / hnorm2)
                        f[:2] = fh2

        return f, clipped_norm, clipped_tilt

    def compute_control(self, time_s: float, obs_state: VehicleState, reference: TrajectoryReference) -> ControlCommand:
        f_pred = self._predict_desired_force_W_N(obs_state, reference)
        if self.clip_to_classic_limits:
            f_limited, c_norm, c_tilt = self._limit_desired_force_W_N(f_pred)
        else:
            f_limited = f_pred.copy()
            c_norm = c_tilt = False

        self._clip_norm_count += int(bool(c_norm))
        self._clip_tilt_count += int(bool(c_tilt))
        self._total_steps += 1

        self.last_desired_force_W_N = f_pred.copy()
        self.last_clipped_force_W_N = f_limited.copy()

        return self.classic_inner.compute_control_from_desired_force_W(
            obs_state, reference.yaw_rad, f_limited
        )

    def reset(self):
        """Clear recurrent state and clip counters (call at start of each episode)."""
        self.window.clear()
        self._clip_norm_count = 0
        self._clip_tilt_count = 0
        self._total_steps = 0
        self.last_desired_force_W_N = np.zeros(3, dtype=float)
        self.last_clipped_force_W_N = np.zeros(3, dtype=float)

    def get_clip_stats(self) -> dict:
        """Porcentajes de clipping para logging/evaluacion (0 si total_steps=0)."""
        total = max(self._total_steps, 1)
        return {
            "force_norm_clip_count": self._clip_norm_count,
            "force_tilt_clip_count": self._clip_tilt_count,
            "force_norm_clip_percentage": 100.0 * self._clip_norm_count / total,
            "force_tilt_clip_percentage": 100.0 * self._clip_tilt_count / total,
            "total_steps": self._total_steps,
        }
