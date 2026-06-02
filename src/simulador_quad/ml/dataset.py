"""
Carga de datos y construccion de features para entrenamiento neuronal.
"""

import os
import json
import numpy as np
import pandas as pd
import torch
import yaml
from torch.utils.data import Dataset
from pathlib import Path

# Constantes de versionado de features
FEATURE_VERSION = "v1"
FEATURE_NAMES = [
    "pos_x", "pos_y", "pos_z",
    "vel_x", "vel_y", "vel_z",
    "quat_w", "quat_x", "quat_y", "quat_z",
    "omega_x", "omega_y", "omega_z",
    "ref_pos_x", "ref_pos_y", "ref_pos_z",
    "ref_vel_x", "ref_vel_y", "ref_vel_z",
    "ref_acc_x", "ref_acc_y", "ref_acc_z",
    "ref_yaw",
    "error_pos_x", "error_pos_y", "error_pos_z",
    "error_vel_x", "error_vel_y", "error_vel_z",
    "sin_yaw", "cos_yaw"
]
TARGET_NAMES = [
    "thrust", "moment_x", "moment_y", "moment_z"
]
POSITION_GAIN_TARGET_NAMES = [
    "log_kp_x_multiplier", "log_kp_y_multiplier", "log_kp_z_multiplier",
    "log_kd_x_multiplier", "log_kd_y_multiplier", "log_kd_z_multiplier",
]
DEFAULT_BASE_KP_POS = np.array([2.0, 2.0, 5.0], dtype=float)
DEFAULT_BASE_KD_POS = np.array([1.0, 1.0, 2.0], dtype=float)

# --- Outer force (neural outer-force controller) feature and target versioning ---
# All new outer-force datasets use *observation* (not state) to avoid leakage under sensor noise.
OUTER_FORCE_MIN_V1_NAMES = [
    "error_pos_x", "error_pos_y", "error_pos_z",
    "error_vel_x", "error_vel_y", "error_vel_z",
    "ref_acc_x", "ref_acc_y", "ref_acc_z",
]
OUTER_FORCE_FULL_V1_NAMES = FEATURE_NAMES[:]  # 31 features, built from observation fields
TARGET_FORCE_NAMES = ["force_x_W_N", "force_y_W_N", "force_z_W_N"]
TARGET_FORCE_VERSION = "desired_force_W_v1"


class ImitationDataset(Dataset):
    """
    Dataset para carga de telemetria y construccion de muestras supervisadas.
    """
    def __init__(self, dataset_path: str, split: str = "train", transform=None, target_transform=None):
        self.dataset_path = Path(dataset_path)
        manifest_path = self.dataset_path / "manifest.csv"
        self.manifest = pd.read_csv(manifest_path)
        self.split_data = self.manifest[self.manifest["split"] == split]
        self.transform = transform
        self.target_transform = target_transform
        
        self.samples = []
        self._load_telemetry()
    
    def _load_telemetry(self):
        """Carga todos los episodios validos del split."""
        for _, row in self.split_data.iterrows():
            result_dir = self.dataset_path / row["result_dir"]
            telemetry_path = result_dir / "telemetry.json"
            
            if not telemetry_path.exists():
                continue
                
            with open(telemetry_path, "r") as f:
                telemetry = json.load(f)
            
            for entry in telemetry:
                sample_x, sample_y = self._extract_features(entry)
                
                # Filtrar no finitos
                if np.isfinite(sample_x).all() and np.isfinite(sample_y).all():
                    self.samples.append((
                        torch.tensor(sample_x, dtype=torch.float32),
                        torch.tensor(sample_y, dtype=torch.float32)
                    ))

    def _extract_features(self, entry: dict):
        """Convierte una entrada de telemetria en arrays de entrada y salida."""
        return _extract_features_from_entry(entry)
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        x, y = self.samples[idx]
        if self.transform:
            x = self.transform(x)
        if self.target_transform:
            y = self.target_transform(y)
        return x, y

class SequentialImitationDataset(Dataset):
    """
    Dataset para arquitecturas recurrentes (GRU/LSTM).
    Entrega ventanas temporales fijas.
    """
    def __init__(self, dataset_path: str, split: str = "train", sequence_length: int = 20, transform=None, target_transform=None):
        self.dataset_path = Path(dataset_path)
        manifest_path = self.dataset_path / "manifest.csv"
        self.manifest = pd.read_csv(manifest_path)
        self.split_data = self.manifest[self.manifest["split"] == split]
        self.sequence_length = sequence_length
        self.transform = transform
        self.target_transform = target_transform
        
        self.windows = []
        self._load_telemetry()
    
    def _load_telemetry(self):
        """Carga episodios y crea ventanas deslizantes sin cruzar fronteras."""
        for _, row in self.split_data.iterrows():
            result_dir = self.dataset_path / row["result_dir"]
            telemetry_path = result_dir / "telemetry.json"
            
            if not telemetry_path.exists():
                continue
                
            with open(telemetry_path, "r") as f:
                telemetry = json.load(f)
            
            episode_samples = []
            for entry in telemetry:
                sample_x, sample_y = self._extract_features(entry)
                
                if np.isfinite(sample_x).all() and np.isfinite(sample_y).all():
                    episode_samples.append((
                        torch.tensor(sample_x, dtype=torch.float32),
                        torch.tensor(sample_y, dtype=torch.float32)
                    ))
            
            # Crear ventanas
            if len(episode_samples) >= self.sequence_length:
                for i in range(len(episode_samples) - self.sequence_length + 1):
                    window = episode_samples[i : i + self.sequence_length]
                    
                    # Entradas de la ventana
                    x_seq = torch.stack([w[0] for w in window])
                    # Target es el comando de la ultima muestra de la ventana
                    y_last = window[-1][1]
                    
                    self.windows.append((x_seq, y_last))

    def _extract_features(self, entry: dict):
        """Reutilizamos la logica de extraccion de la clase base si fuera necesario, 
        pero aqui la repetimos o la movemos a una funcion helper. 
        Para simplificar, usamos una funcion externa o la repetimos."""
        # TODO: Refactorizar para evitar duplicacion
        # Por ahora, usamos el metodo de ImitationDataset estaticamente si fuera posible, 
        # pero como es un metodo de instancia, lo repetimos aqui o lo sacamos.
        return _extract_features_from_entry(entry)

    def __len__(self):
        return len(self.windows)
    
    def __getitem__(self, idx):
        x_seq, y = self.windows[idx]
        if self.transform:
            # Aplicar transformacion al bloque completo (broadcasting)
            # x_seq shape: [seq_len, input_dim]
            x_seq = self.transform(x_seq)
        if self.target_transform:
            y = self.target_transform(y)
        return x_seq, y


class PositionGainDataset(Dataset):
    """
    Dataset supervisado para programacion neuronal de ganancias del lazo externo.

    Cada muestra usa las mismas features de imitacion, pero el target es constante
    por episodio: log(Kp_pos/base_Kp_pos) y log(Kd_pos/base_Kd_pos).
    """
    def __init__(
        self,
        dataset_path: str,
        split: str = "train",
        base_Kp_pos=None,
        base_Kd_pos=None,
        transform=None,
        target_transform=None,
    ):
        self.dataset_path = Path(dataset_path)
        self.manifest = pd.read_csv(self.dataset_path / "manifest.csv")
        self.split_data = self.manifest[self.manifest["split"] == split]
        self.base_Kp_pos = np.array(base_Kp_pos if base_Kp_pos is not None else DEFAULT_BASE_KP_POS, dtype=float)
        self.base_Kd_pos = np.array(base_Kd_pos if base_Kd_pos is not None else DEFAULT_BASE_KD_POS, dtype=float)
        self.transform = transform
        self.target_transform = target_transform
        self.samples = []
        self._load_telemetry()

    def _load_telemetry(self):
        for _, row in self.split_data.iterrows():
            result_dir = self.dataset_path / row["result_dir"]
            telemetry_path = result_dir / "telemetry.json"
            if not telemetry_path.exists():
                continue

            target = _build_position_gain_target(self.dataset_path, row, self.base_Kp_pos, self.base_Kd_pos)

            with open(telemetry_path, "r") as f:
                telemetry = json.load(f)

            for entry in telemetry:
                sample_x, _ = _extract_features_from_entry(entry, prefer_observation=True)
                if np.isfinite(sample_x).all() and np.isfinite(target).all():
                    self.samples.append((
                        torch.tensor(sample_x, dtype=torch.float32),
                        torch.tensor(target, dtype=torch.float32),
                    ))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x, y = self.samples[idx]
        if self.transform:
            x = self.transform(x)
        if self.target_transform:
            y = self.target_transform(y)
        return x, y


class SequentialPositionGainDataset(Dataset):
    """Ventanas temporales para GRU/LSTM con targets de ganancias externas."""
    def __init__(
        self,
        dataset_path: str,
        split: str = "train",
        sequence_length: int = 20,
        base_Kp_pos=None,
        base_Kd_pos=None,
        transform=None,
        target_transform=None,
    ):
        self.dataset_path = Path(dataset_path)
        self.manifest = pd.read_csv(self.dataset_path / "manifest.csv")
        self.split_data = self.manifest[self.manifest["split"] == split]
        self.sequence_length = sequence_length
        self.base_Kp_pos = np.array(base_Kp_pos if base_Kp_pos is not None else DEFAULT_BASE_KP_POS, dtype=float)
        self.base_Kd_pos = np.array(base_Kd_pos if base_Kd_pos is not None else DEFAULT_BASE_KD_POS, dtype=float)
        self.transform = transform
        self.target_transform = target_transform
        self.windows = []
        self._load_telemetry()

    def _load_telemetry(self):
        for _, row in self.split_data.iterrows():
            result_dir = self.dataset_path / row["result_dir"]
            telemetry_path = result_dir / "telemetry.json"
            if not telemetry_path.exists():
                continue

            target = _build_position_gain_target(self.dataset_path, row, self.base_Kp_pos, self.base_Kd_pos)
            with open(telemetry_path, "r") as f:
                telemetry = json.load(f)

            episode_samples = []
            for entry in telemetry:
                sample_x, _ = _extract_features_from_entry(entry, prefer_observation=True)
                if np.isfinite(sample_x).all() and np.isfinite(target).all():
                    episode_samples.append((
                        torch.tensor(sample_x, dtype=torch.float32),
                        torch.tensor(target, dtype=torch.float32),
                    ))

            if len(episode_samples) >= self.sequence_length:
                for i in range(len(episode_samples) - self.sequence_length + 1):
                    window = episode_samples[i : i + self.sequence_length]
                    x_seq = torch.stack([w[0] for w in window])
                    y_last = window[-1][1]
                    self.windows.append((x_seq, y_last))

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, idx):
        x_seq, y = self.windows[idx]
        if self.transform:
            x_seq = self.transform(x_seq)
        if self.target_transform:
            y = self.target_transform(y)
        return x_seq, y

def _extract_features_from_entry(entry: dict, prefer_observation: bool = False):
    """Convierte una entrada de telemetria en arrays de entrada y salida."""
    if prefer_observation and "observation" in entry:
        state = entry["observation"]
    else:
        state = entry["state"]
    ref = entry["reference"]
    ctrl = entry.get("control") # Control puede no estar presente en inferencia
    
    pos = np.array(state["position_W_m"])
    vel = np.array(state["velocity_W_m_s"])
    quat = np.array(state["orientation_WB"])
    omega = np.array(state["angular_velocity_B_rad_s"])
    
    ref_pos = np.array(ref["position_W_m"])
    ref_vel = np.array(ref["velocity_W_m_s"])
    ref_acc = np.array(ref["acceleration_W_m_s2"])
    ref_yaw = ref["yaw_rad"]
    
    return build_feature_vector(pos, vel, quat, omega, ref_pos, ref_vel, ref_acc, ref_yaw), \
           build_target_vector(ctrl) if ctrl else None

def build_feature_vector(pos, vel, quat, omega, ref_pos, ref_vel, ref_acc, ref_yaw):
    """Construye el vector de entrada para la red neuronal."""
    # Errores
    err_pos = ref_pos - pos
    err_vel = ref_vel - vel
    
    # Features
    x = np.concatenate([
        pos, vel, quat, omega,
        ref_pos, ref_vel, ref_acc, [ref_yaw], # ref_yaw is no a vector
        err_pos, err_vel,
        [np.sin(ref_yaw), np.cos(ref_yaw)]
    ])
    return x

def build_target_vector(ctrl):
    """Construye el vector de salida para la red neuronal."""
    y = np.concatenate([
        [ctrl["collective_thrust_N"]],
        ctrl["body_moments_Nm"]
    ])
    return y


def _build_position_gain_target(dataset_path: Path, manifest_row, base_Kp_pos: np.ndarray, base_Kd_pos: np.ndarray) -> np.ndarray:
    if "scenario_path" not in manifest_row or pd.isna(manifest_row["scenario_path"]):
        raise ValueError("PositionGainDataset requires manifest.csv to include scenario_path")

    scenario_path = dataset_path / manifest_row["scenario_path"]
    with open(scenario_path, "r") as f:
        scenario = yaml.safe_load(f)

    controller = scenario.get("controller", {})
    kp_pos = np.array(controller.get("Kp_pos", DEFAULT_BASE_KP_POS), dtype=float)
    kd_pos = np.array(controller.get("Kd_pos", DEFAULT_BASE_KD_POS), dtype=float)

    if np.any(kp_pos <= 0.0) or np.any(kd_pos <= 0.0):
        raise ValueError(f"Position gain targets must be positive in {scenario_path}")

    return np.log(np.concatenate([kp_pos / base_Kp_pos, kd_pos / base_Kd_pos]))


# =============================================================================
# Outer-force feature builders (always from "observation" to prevent leakage)
# =============================================================================

def build_outer_force_min_features_from_observation(observation: dict, reference: dict) -> np.ndarray:
    """Construye features minimas (9) para outer-force: errores pos/vel + ref_acc (ENU)."""
    pos = np.asarray(observation["position_W_m"], dtype=float)
    vel = np.asarray(observation["velocity_W_m_s"], dtype=float)
    ref_pos = np.asarray(reference["position_W_m"], dtype=float)
    ref_vel = np.asarray(reference["velocity_W_m_s"], dtype=float)
    ref_acc = np.asarray(reference["acceleration_W_m_s2"], dtype=float)

    err_pos = ref_pos - pos
    err_vel = ref_vel - vel
    x = np.concatenate([err_pos, err_vel, ref_acc])
    if x.shape != (9,):
        raise ValueError(f"outer_force_min_v1 expected 9 features, got {x.shape}")
    return x


def build_outer_force_full_features_from_observation(observation: dict, reference: dict) -> np.ndarray:
    """Construye features completas (31) desde observation (no state). Reutiliza build_feature_vector."""
    pos = np.asarray(observation["position_W_m"], dtype=float)
    vel = np.asarray(observation["velocity_W_m_s"], dtype=float)
    quat = np.asarray(observation["orientation_WB"], dtype=float)
    omega = np.asarray(observation["angular_velocity_B_rad_s"], dtype=float)
    ref_pos = np.asarray(reference["position_W_m"], dtype=float)
    ref_vel = np.asarray(reference["velocity_W_m_s"], dtype=float)
    ref_acc = np.asarray(reference["acceleration_W_m_s2"], dtype=float)
    ref_yaw = float(reference["yaw_rad"])
    return build_feature_vector(pos, vel, quat, omega, ref_pos, ref_vel, ref_acc, ref_yaw)


def _build_desired_force_target_for_entry(
    entry: dict,
    kp_pos: np.ndarray,
    kd_pos: np.ndarray,
    mass_kg: float,
    g_m_s2: float,
) -> np.ndarray:
    """Calcula target desired_force_W_N[3] usando *observation* + reference + PID experto.
    Delega estrictamente en ClassicCascadeController.compute_desired_force_W para equivalencia.
    inertia dummy (no usada para calculo de fuerza).
    """
    from simulador_quad.control.classic import ClassicCascadeController
    from simulador_quad.core.contracts import VehicleState, TrajectoryReference

    obs_d = entry["observation"]
    ref_d = entry["reference"]

    obs_state = VehicleState(
        position_W_m=np.asarray(obs_d["position_W_m"], dtype=float),
        velocity_W_m_s=np.asarray(obs_d["velocity_W_m_s"], dtype=float),
        orientation_WB=np.asarray(obs_d["orientation_WB"], dtype=float),
        angular_velocity_B_rad_s=np.asarray(obs_d["angular_velocity_B_rad_s"], dtype=float),
        time_s=float(obs_d.get("time_s", 0.0)),
    )
    reference = TrajectoryReference(
        position_W_m=np.asarray(ref_d["position_W_m"], dtype=float),
        velocity_W_m_s=np.asarray(ref_d["velocity_W_m_s"], dtype=float),
        acceleration_W_m_s2=np.asarray(ref_d["acceleration_W_m_s2"], dtype=float),
        yaw_rad=float(ref_d["yaw_rad"]),
    )

    tmp = ClassicCascadeController(
        mass_kg,
        g_m_s2,
        np.eye(3),
        Kp_pos=np.asarray(kp_pos, dtype=float),
        Kd_pos=np.asarray(kd_pos, dtype=float),
    )
    f = tmp.compute_desired_force_W(obs_state, reference)
    return np.asarray(f, dtype=float)


# =============================================================================
# OuterForce datasets (targets por-muestra, features versionables, observation source)
# =============================================================================

class OuterForceDataset(Dataset):
    """Dataset para el controlador neural de fuerza externa deseada (desired_force_W_N[3]).
    Targets calculados con el PID experto (Kp/Kd_pos) sobre la observation del experto.
    Soporta outer_force_min_v1 (9) y outer_force_full_v1 (31).
    """

    def __init__(
        self,
        dataset_path: str,
        split: str = "train",
        feature_version: str = "outer_force_min_v1",
        transform=None,
        target_transform=None,
    ):
        self.dataset_path = Path(dataset_path)
        self.manifest = pd.read_csv(self.dataset_path / "manifest.csv")
        self.split_data = self.manifest[self.manifest["split"] == split]
        self.transform = transform
        self.target_transform = target_transform
        self.feature_version = feature_version

        if feature_version == "outer_force_min_v1":
            self.feature_names = OUTER_FORCE_MIN_V1_NAMES
            self._build_x = build_outer_force_min_features_from_observation
        elif feature_version == "outer_force_full_v1":
            self.feature_names = OUTER_FORCE_FULL_V1_NAMES
            self._build_x = build_outer_force_full_features_from_observation
        else:
            raise ValueError(f"Unsupported feature_version for outer force: {feature_version}. "
                             "Use 'outer_force_min_v1' or 'outer_force_full_v1'.")

        self.target_names = TARGET_FORCE_NAMES[:]
        self.target_version = TARGET_FORCE_VERSION
        self.samples = []
        self._load_telemetry()

    def _load_telemetry(self):
        for _, row in self.split_data.iterrows():
            result_dir = self.dataset_path / row["result_dir"]
            telemetry_path = result_dir / "telemetry.json"
            if not telemetry_path.exists():
                continue

            # Cargar gains del experto y params fisicos desde el scenario yaml del experto (trazable)
            if "scenario_path" not in row or pd.isna(row["scenario_path"]):
                # Fallback conservador (1kg, 9.81) solo si no hay scenario (no recomendado)
                kp_pos = DEFAULT_BASE_KP_POS.copy()
                kd_pos = DEFAULT_BASE_KD_POS.copy()
                mass = 1.0
                g = 9.81
            else:
                scenario_path = self.dataset_path / row["scenario_path"]
                with open(scenario_path, "r") as f:
                    scenario = yaml.safe_load(f)
                c = scenario.get("controller", {})
                kp_pos = np.array(c.get("Kp_pos", DEFAULT_BASE_KP_POS), dtype=float)
                kd_pos = np.array(c.get("Kd_pos", DEFAULT_BASE_KD_POS), dtype=float)
                v = scenario.get("vehicle", {})
                mass = float(v.get("mass_kg", 1.0))
                g = float(v.get("gravity_m_s2", 9.81))

            with open(telemetry_path, "r") as f:
                telemetry = json.load(f)

            for entry in telemetry:
                try:
                    x = self._build_x(entry["observation"], entry["reference"])
                    y = _build_desired_force_target_for_entry(entry, kp_pos, kd_pos, mass, g)
                except (KeyError, ValueError, TypeError, IndexError):
                    continue  # malformed telemetry entry; see legacy ImitationDataset for similar pattern

                if np.isfinite(x).all() and np.isfinite(y).all():
                    self.samples.append((
                        torch.tensor(x, dtype=torch.float32),
                        torch.tensor(y, dtype=torch.float32),
                    ))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        x, y = self.samples[idx]
        if self.transform:
            x = self.transform(x)
        if self.target_transform:
            y = self.target_transform(y)
        return x, y


class SequentialOuterForceDataset(Dataset):
    """Ventanas temporales para GRU/LSTM outer-force (targets de fuerza por-muestra)."""

    def __init__(
        self,
        dataset_path: str,
        split: str = "train",
        sequence_length: int = 20,
        feature_version: str = "outer_force_min_v1",
        transform=None,
        target_transform=None,
    ):
        self.dataset_path = Path(dataset_path)
        self.manifest = pd.read_csv(self.dataset_path / "manifest.csv")
        self.split_data = self.manifest[self.manifest["split"] == split]
        self.sequence_length = sequence_length
        self.feature_version = feature_version
        self.transform = transform
        self.target_transform = target_transform

        if feature_version == "outer_force_min_v1":
            self.feature_names = OUTER_FORCE_MIN_V1_NAMES
            self._build_x = build_outer_force_min_features_from_observation
        elif feature_version == "outer_force_full_v1":
            self.feature_names = OUTER_FORCE_FULL_V1_NAMES
            self._build_x = build_outer_force_full_features_from_observation
        else:
            raise ValueError(f"Unsupported feature_version: {feature_version}")

        self.target_names = TARGET_FORCE_NAMES[:]
        self.target_version = TARGET_FORCE_VERSION
        self.windows = []
        self._load_telemetry()

    def _load_telemetry(self):
        for _, row in self.split_data.iterrows():
            result_dir = self.dataset_path / row["result_dir"]
            telemetry_path = result_dir / "telemetry.json"
            if not telemetry_path.exists():
                continue

            if "scenario_path" not in row or pd.isna(row["scenario_path"]):
                kp_pos = DEFAULT_BASE_KP_POS.copy()
                kd_pos = DEFAULT_BASE_KD_POS.copy()
                mass = 1.0
                g = 9.81
            else:
                scenario_path = self.dataset_path / row["scenario_path"]
                with open(scenario_path, "r") as f:
                    scenario = yaml.safe_load(f)
                c = scenario.get("controller", {})
                kp_pos = np.array(c.get("Kp_pos", DEFAULT_BASE_KP_POS), dtype=float)
                kd_pos = np.array(c.get("Kd_pos", DEFAULT_BASE_KD_POS), dtype=float)
                v = scenario.get("vehicle", {})
                mass = float(v.get("mass_kg", 1.0))
                g = float(v.get("gravity_m_s2", 9.81))

            with open(telemetry_path, "r") as f:
                telemetry = json.load(f)

            episode_samples = []
            for entry in telemetry:
                try:
                    x = self._build_x(entry["observation"], entry["reference"])
                    y = _build_desired_force_target_for_entry(entry, kp_pos, kd_pos, mass, g)
                except (KeyError, ValueError, TypeError, IndexError):
                    continue  # malformed telemetry entry; see legacy ImitationDataset for similar pattern
                if np.isfinite(x).all() and np.isfinite(y).all():
                    episode_samples.append((
                        torch.tensor(x, dtype=torch.float32),
                        torch.tensor(y, dtype=torch.float32),
                    ))

            if len(episode_samples) >= self.sequence_length:
                for i in range(len(episode_samples) - self.sequence_length + 1):
                    window = episode_samples[i : i + self.sequence_length]
                    x_seq = torch.stack([w[0] for w in window])
                    y_last = window[-1][1]
                    self.windows.append((x_seq, y_last))

    def __len__(self):
        return len(self.windows)

    def __getitem__(self, idx):
        x_seq, y = self.windows[idx]
        if self.transform:
            x_seq = self.transform(x_seq)
        if self.target_transform:
            y = self.target_transform(y)
        return x_seq, y
