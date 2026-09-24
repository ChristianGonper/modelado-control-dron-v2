"""
Simulation execution service for NeuroFlight.
Runs the 4 controllers (classic PD, MLP, GRU, LSTM outer-force) concurrently in background,
manages status, stores run artifacts in data/neuroflight_runs/<run_id>/, and isolates results
from historical TFG data.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import threading
from typing import Any, Dict, List, Optional, Tuple
import uuid

import numpy as np
import yaml

from simulador_quad.api.bundle_verifier import BundleVerifier
from simulador_quad.api.models import (
    ControllerProgress,
    ControllerSummary,
    MissionConfigRequest,
    RunResultsResponse,
    RunStatusResponse,
)
from simulador_quad.api.scenario_builder import build_scenario_for_simulation, compute_preview
from simulador_quad.control.classic import ClassicCascadeController
from simulador_quad.control.neural import NeuralOuterForceController
from simulador_quad.metrics.report import compute_metrics
from simulador_quad.runner import SimulationRunner
from simulador_quad.scenarios.loader import instantiate_scenario
from simulador_quad.telemetry.export import export_metrics_json, export_telemetry_json

RUNS_DIR = Path("data/neuroflight_runs")


class SimulationTask:
    def __init__(self, run_id: str, mission: MissionConfigRequest, run_dir: Path):
        self.run_id = run_id
        self.mission = mission
        self.run_dir = run_dir
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.state = "preparing" # preparing, running, completed, partial, interrupted, error
        self.controllers: Dict[str, ControllerProgress] = {
            "classic": ControllerProgress(status="pending"),
            "mlp": ControllerProgress(status="pending"),
            "gru": ControllerProgress(status="pending"),
            "lstm": ControllerProgress(status="pending"),
        }
        self.summaries: Dict[str, ControllerSummary] = {}
        self.telemetry_cache: Dict[str, List[Dict[str, Any]]] = {}
        self.nominal_path: List[List[float]] = []
        self.artifact_identity: Dict[str, Any] = {}
        self.effective_config: Dict[str, Any] = {}
        self.selected_pid: str = ""
        self.selected_pid_explanation: str = ""
        self.cancel_requested: bool = False


class RunnerService:
    def __init__(self, runs_dir: Path = RUNS_DIR):
        self.runs_dir = runs_dir.resolve()
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        self.verifier = BundleVerifier()
        self._tasks: Dict[str, SimulationTask] = {}
        self._lock = threading.Lock()

    def start_simulation(self, mission: MissionConfigRequest) -> str:
        """Lanza la simulación en segundo plano y devuelve el ID de ejecución."""
        run_id = str(uuid.uuid4())[:8]
        run_dir = self.runs_dir / run_id
        run_dir.mkdir(parents=True, exist_ok=True)

        task = SimulationTask(run_id, mission, run_dir)
        with self._lock:
            self._tasks[run_id] = task

        thread = threading.Thread(target=self._run_worker, args=(task,), daemon=True)
        thread.start()
        return run_id

    def cancel_simulation(self, run_id: str) -> bool:
        with self._lock:
            if run_id in self._tasks:
                self._tasks[run_id].cancel_requested = True
                return True
        return False

    def get_status(self, run_id: str) -> Optional[RunStatusResponse]:
        with self._lock:
            task = self._tasks.get(run_id)
            if not task:
                # Intentar cargar desde disco si existe
                manifest_file = self.runs_dir / run_id / "run_manifest.json"
                if manifest_file.exists():
                    return self._status_from_disk(run_id, manifest_file)
                return None

            # Calcular porcentaje global
            completed_count = sum(1 for c in task.controllers.values() if c.status in ("completed", "error", "cancelled"))
            pct = (completed_count / len(task.controllers)) * 100.0

            return RunStatusResponse(
                run_id=task.run_id,
                state=task.state,
                progress_pct=round(pct, 1),
                controllers=task.controllers,
                created_at=task.created_at,
            )

    def get_results(self, run_id: str) -> Optional[RunResultsResponse]:
        with self._lock:
            task = self._tasks.get(run_id)

        if task and task.state in ("completed", "partial", "error", "interrupted"):
            return self._build_results_response(task)

        # Cargar de disco si se reinició el servidor
        manifest_file = self.runs_dir / run_id / "run_manifest.json"
        if manifest_file.exists():
            with open(manifest_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return RunResultsResponse(**data)

        return None

    def _status_from_disk(self, run_id: str, manifest_path: Path) -> RunStatusResponse:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        controllers = {}
        for cid, summ in data.get("summaries", {}).items():
            controllers[cid] = ControllerProgress(
                status=summ.get("status", "completed"),
                progress_pct=100.0,
                termination_reason=summ.get("termination_reason"),
                duration_s=summ.get("duration_s"),
                position_mae_m=summ.get("position_mae_m"),
                position_max_err_m=summ.get("position_max_err_m"),
            )
        return RunStatusResponse(
            run_id=run_id,
            state="completed" if not data.get("is_partial") else "partial",
            progress_pct=100.0,
            controllers=controllers,
            created_at=data.get("timestamp", ""),
        )

    def _build_results_response(self, task: SimulationTask) -> RunResultsResponse:
        runs_trajectory: Dict[str, List[Dict[str, Any]]] = {}

        for cid, telemetry in task.telemetry_cache.items():
            # Muestras simplificadas para reproducción 3D
            traj_samples = []
            for s in telemetry:
                pos = s.get("state", {}).get("position_W_m", [0, 0, 0])
                ref_pos = s.get("reference", {}).get("position_W_m", [0, 0, 0])
                err = float(np.linalg.norm(np.array(pos) - np.array(ref_pos)))
                traj_samples.append({
                    "time_s": round(s.get("time_s", 0.0), 3),
                    "pos": [round(float(c), 3) for c in pos],
                    "yaw": round(float(s.get("reference", {}).get("yaw_rad", 0.0)), 3),
                    "err_m": round(err, 3),
                })
            runs_trajectory[cid] = traj_samples

        is_partial = any(c.status != "completed" for c in task.controllers.values())

        return RunResultsResponse(
            run_id=task.run_id,
            timestamp=task.created_at,
            mission_mode=task.mission.mode,
            mission_family=task.mission.family.value,
            selected_pid=task.selected_pid,
            selected_pid_explanation=task.selected_pid_explanation,
            effective_config=task.effective_config,
            seed=task.mission.seed,
            summaries=task.summaries,
            nominal_path=task.nominal_path,
            runs_trajectory=runs_trajectory,
            is_partial=is_partial,
            artifact_identity=task.artifact_identity,
        )

    def _run_worker(self, task: SimulationTask):
        """Worker en segundo plano que ejecuta la comparativa de los 4 controladores."""
        try:
            # 1. Construir escenario base
            scenario_cfg, pid_fam, pid_exp = build_scenario_for_simulation(
                task.mission, task.run_dir, self.verifier
            )
            task.selected_pid = pid_fam
            task.selected_pid_explanation = pid_exp
            task.effective_config = scenario_cfg
            task.artifact_identity = self.verifier.artifact_identity()
            # Ruta geométrica común, independiente de cuándo llega cada vehículo.
            task.nominal_path = compute_preview(task.mission).points
            task.state = "running"

            # 2. Controladores a ejecutar en orden
            controllers_to_run = [
                ("classic", "PD Clásico (PID Congelado)"),
                ("mlp", "MLP Neuronal (Outer-Force)"),
                ("gru", "GRU Neuronal (Outer-Force)"),
                ("lstm", "LSTM Neuronal (Outer-Force)"),
            ]

            success_count = 0

            for cid, name in controllers_to_run:
                if task.cancel_requested:
                    task.controllers[cid].status = "cancelled"
                    continue

                task.controllers[cid].status = "running"
                task.controllers[cid].progress_pct = 10.0

                try:
                    summary, raw_telemetry = self._simulate_controller(
                        cid, name, scenario_cfg, task.run_dir
                    )
                    task.summaries[cid] = summary
                    task.telemetry_cache[cid] = raw_telemetry
                    task.controllers[cid].status = "completed"
                    task.controllers[cid].progress_pct = 100.0
                    task.controllers[cid].termination_reason = summary.termination_reason
                    task.controllers[cid].duration_s = summary.duration_s
                    task.controllers[cid].position_mae_m = summary.position_mae_m
                    task.controllers[cid].position_max_err_m = summary.position_max_err_m
                    success_count += 1

                except Exception as exc:
                    task.controllers[cid].status = "error"
                    task.controllers[cid].error_message = str(exc)
                    task.summaries[cid] = ControllerSummary(
                        controller_id=cid,
                        name=name,
                        family=cid,
                        status="error",
                        termination_reason=f"Fallo de ejecución: {exc}",
                        duration_s=0.0,
                        is_interrupted=True,
                    )

            if task.cancel_requested:
                task.state = "interrupted"
            elif success_count == len(controllers_to_run):
                task.state = "completed"
            elif success_count > 0:
                task.state = "partial"
            else:
                task.state = "error"

            # Guardar manifiesto de la corrida
            res_obj = self._build_results_response(task)
            manifest_file = task.run_dir / "run_manifest.json"
            with open(manifest_file, "w", encoding="utf-8") as f:
                json.dump(res_obj.model_dump(), f, indent=2)

        except Exception as global_exc:
            task.state = "error"
            for c in task.controllers.values():
                if c.status == "pending":
                    c.status = "error"
                    c.error_message = str(global_exc)

    def _simulate_controller(
        self,
        cid: str,
        name: str,
        base_scenario_cfg: Dict[str, Any],
        run_dir: Path,
    ) -> Tuple[ControllerSummary, List[Dict[str, Any]]]:
        """Ejecuta una corrida aislada para un único controlador con SimulationRunner."""
        # Clonar configuración
        cfg = json.loads(json.dumps(base_scenario_cfg))

        v_params, mixer, actuators, initial_state, trajectory, _, wind, noise = (
            instantiate_scenario(cfg)
        )

        # Instanciar el controlador deseado
        if cid == "classic":
            c_cfg = cfg["controller"]
            controller = ClassicCascadeController(
                v_params.mass_kg,
                v_params.gravity_m_s2,
                v_params.inertia_B_kg_m2,
                Kp_pos=np.array(c_cfg["Kp_pos"], dtype=float),
                Kd_pos=np.array(c_cfg["Kd_pos"], dtype=float),
                Kp_att=np.array(c_cfg["Kp_att"], dtype=float),
                Kd_att=np.array(c_cfg["Kd_att"], dtype=float),
                max_body_moments_Nm=np.array(c_cfg.get("max_body_moments_Nm", [10.0, 10.0, 2.0]), dtype=float),
            )
        else: # mlp, gru, lstm
            ckpt_path, norm_path, _ = self.verifier.get_neural_paths(cid)
            controller = NeuralOuterForceController(
                checkpoint_path=str(ckpt_path),
                normalization_path=str(norm_path),
                architecture=cid,
                feature_version="outer_force_min_v1",
                sequence_length=20,
                clip_to_classic_limits=True,
                mass_kg=v_params.mass_kg,
                gravity_m_s2=v_params.gravity_m_s2,
                inertia_B_kg_m2=v_params.inertia_B_kg_m2,
                Kp_att=np.array([4.0, 4.0, 1.0], dtype=float),
                Kd_att=np.array([1.5, 1.5, 0.5], dtype=float),
                max_body_moments_Nm=np.array([10.0, 10.0, 2.0], dtype=float),
                device="auto",
            )

        # Instanciar Runner idéntico
        timing = cfg["timing"]
        termination = cfg["termination"]
        runner = SimulationRunner(
            physics_dt_s=timing["physics_dt_s"],
            control_dt_s=timing["control_dt_s"],
            telemetry_dt_s=timing["telemetry_dt_s"],
            vehicle_params=v_params,
            mixer=mixer,
            actuators=actuators,
            wind_model=wind,
            observation_noise=noise,
            max_duration_s=termination["max_duration_s"],
            z_min_m=termination["z_min_m"],
            max_attitude_angle_rad=termination["max_attitude_angle_rad"],
            max_saturation_duration_s=termination["max_saturation_duration_s"],
        )

        sim_result = runner.run(initial_state, controller, trajectory)
        telemetry = sim_result["telemetry"]
        reason = sim_result["termination_reason"]

        # Exportar archivos
        telem_file = run_dir / f"telemetry_{cid}.json"
        metrics_file = run_dir / f"metrics_{cid}.json"
        export_telemetry_json(telemetry, str(telem_file))

        metrics = compute_metrics(telemetry, reason, metadata={"controller": cid, "name": name})
        export_metrics_json(metrics, str(metrics_file))

        # Cargar raw telemetry serializada
        with open(telem_file, "r", encoding="utf-8") as f:
            raw_telemetry = json.load(f)

        dur = float(telemetry[-1].time_s) if telemetry else 0.0
        mae = float(metrics.get("position_mae_m", 0.0))
        max_err = float(metrics.get("position_max_err_m", 0.0))

        summary = ControllerSummary(
            controller_id=cid,
            name=name,
            family=cid,
            status="completed",
            termination_reason=reason or "Misión finalizada",
            duration_s=round(dur, 2),
            position_mae_m=round(mae, 4),
            position_max_err_m=round(max_err, 4),
            sample_count=len(telemetry),
            is_interrupted=("Crash" in reason or "exceeded" in reason or "Persistent" in reason),
        )
        return summary, raw_telemetry
