import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# Configurar matplotlib para estilo académico limpio
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'grid.alpha': 0.3,
    'legend.fontsize': 8
})

from simulador_quad.trajectories.analytic import (
    HoldTrajectory,
    CircleTrajectory,
    LissajousTrajectory,
    LineTrajectory,
)
from simulador_quad.core.contracts import VehicleState

def main():
    fig = plt.figure(figsize=(10, 8), dpi=300)
    
    # ----------------------------------------------------
    # 1. HOLD TRAJECTORY (Mantenimiento de posición)
    # ----------------------------------------------------
    ax1 = fig.add_subplot(2, 2, 1, projection='3d')
    hold_pos = np.array([0.0, 0.0, 1.5])
    traj_hold = HoldTrajectory(hold_pos, yaw_rad=0.0)
    
    # Generar algunos puntos temporales
    times = np.linspace(0, 10, 100)
    ref_points = np.array([traj_hold.get_reference(t).position_W_m for t in times])
    
    ax1.plot(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], 
             label="Referencia Hold", color='blue', linestyle='-', linewidth=2)
    # Dibujar el punto inicial de hold
    ax1.scatter([hold_pos[0]], [hold_pos[1]], [hold_pos[2]], 
                color='red', marker='o', s=40, label="Punto de Hold (0, 0, 1.5)")
    
    # Esfera/Cilindro de tolerancia de posición (esquema)
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    r_tol = 0.20 # Tolerancia de 20cm
    x_tol = hold_pos[0] + r_tol * np.outer(np.cos(u), np.sin(v))
    y_tol = hold_pos[1] + r_tol * np.outer(np.sin(u), np.sin(v))
    z_tol = hold_pos[2] + r_tol * np.outer(np.ones(np.size(u)), np.cos(v))
    ax1.plot_surface(x_tol, y_tol, z_tol, color='red', alpha=0.15, shade=False)
    
    ax1.set_title("a) Familia HOLD\n(Sustentación en Punto Fijo)")
    ax1.set_xlabel("Este (x_W) [m]")
    ax1.set_ylabel("Norte (y_W) [m]")
    ax1.set_zlabel("Arriba (z_W) [m]")
    ax1.set_xlim(-1, 1)
    ax1.set_ylim(-1, 1)
    ax1.set_zlim(0, 3)
    ax1.legend(loc='upper right')
    
    # ----------------------------------------------------
    # 2. CIRCLE TRAJECTORY (Círculo Horizontal)
    # ----------------------------------------------------
    ax2 = fig.add_subplot(2, 2, 2, projection='3d')
    center = np.array([0.0, 0.0, 1.5])
    radius = 1.5
    omega = 0.5
    traj_circle = CircleTrajectory(center, radius_m=radius, omega_rad_s=omega, yaw_mode="forward")
    
    times = np.linspace(0, 2*np.pi / omega, 150)
    ref_points = np.array([traj_circle.get_reference(t).position_W_m for t in times])
    ref_vels = np.array([traj_circle.get_reference(t).velocity_W_m_s for t in times])
    
    ax2.plot(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], 
             label="Referencia Circular", color='green', linestyle='-', linewidth=2)
    # Marcar el centro
    ax2.scatter([center[0]], [center[1]], [center[2]], color='black', marker='x', s=30, label="Centro")
    
    # Dibujar vectores de velocidad en algunos puntos para mostrar avance
    for idx in [0, 37, 75, 112]:
        p = ref_points[idx]
        v = ref_vels[idx]
        v_norm = v / np.linalg.norm(v) * 0.5 # Normalizar longitud de flecha
        ax2.quiver(p[0], p[1], p[2], v_norm[0], v_norm[1], v_norm[2], 
                   color='darkgreen', length=0.6, arrow_length_ratio=0.3, linewidth=1.5)
        
    ax2.set_title("b) Familia CIRCLE\n(Seguimiento de Velocidad Variable)")
    ax2.set_xlabel("Este (x_W) [m]")
    ax2.set_ylabel("Norte (y_W) [m]")
    ax2.set_zlabel("Arriba (z_W) [m]")
    ax2.set_xlim(-2, 2)
    ax2.set_ylim(-2, 2)
    ax2.set_zlim(0, 3)
    ax2.legend(loc='upper right')

    # ----------------------------------------------------
    # 3. LISSAJOUS TRAJECTORY (Espacial 3D)
    # ----------------------------------------------------
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    center_l = np.array([0.0, 0.0, 1.5])
    amps_l = np.array([1.5, 1.2, 0.6])
    omegas_l = np.array([0.4, 0.8, 0.4])
    traj_liss = LissajousTrajectory(center_l, amplitudes=amps_l, omegas=omegas_l)
    
    times = np.linspace(0, 2*np.pi / 0.4, 200) # Un ciclo en x
    ref_points = np.array([traj_liss.get_reference(t).position_W_m for t in times])
    
    ax3.plot(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], 
             label="Referencia Lissajous", color='purple', linestyle='-', linewidth=2)
    
    ax3.set_title("c) Familia LISSAJOUS\n(Aceleración en 3 Ejes)")
    ax3.set_xlabel("Este (x_W) [m]")
    ax3.set_ylabel("Norte (y_W) [m]")
    ax3.set_zlabel("Arriba (z_W) [m]")
    ax3.set_xlim(-2, 2)
    ax3.set_ylim(-2, 2)
    ax3.set_zlim(0.5, 2.5)
    ax3.legend(loc='upper right')

    # ----------------------------------------------------
    # 4. WAYPOINT / LINE TRAJECTORY (Misión discreta segmentada)
    # ----------------------------------------------------
    ax4 = fig.add_subplot(2, 2, 4, projection='3d')
    wps = np.array([
        [0.0, 0.0, 1.0],
        [1.5, 1.5, 1.5],
        [1.5, -1.5, 2.0],
        [-1.5, -1.5, 1.5],
        [0.0, 0.0, 1.0]
    ])
    
    # Instanciar LineTrajectory
    traj_wp = LineTrajectory(
        waypoints=wps,
        max_speed_m_s=0.8,
        max_acceleration_m_s2=0.6,
        waypoint_tolerance_m=0.2,
        waypoint_speed_tolerance_m_s=0.2,
        dwell_time_s=0.5
    )
    
    # Simular avance temporal con un seguidor de estado nominal para muestrear LineTrajectory
    ref_list = []
    dt = 0.02
    t = 0.0
    state = VehicleState(
        position_W_m=wps[0].copy(),
        velocity_W_m_s=np.zeros(3),
        orientation_WB=np.array([1.0, 0, 0, 0]),
        angular_velocity_B_rad_s=np.zeros(3),
        time_s=t
    )
    
    # Ejecutamos hasta completar la trayectoria (o un max_time razonable)
    max_steps = 1500
    step = 0
    while not traj_wp.completed and step < max_steps:
        ref = traj_wp.get_reference_for_state(t, state)
        ref_list.append(ref.position_W_m)
        
        # Mover el "estado" ficticio hacia la referencia nominal de forma ideal
        state.position_W_m = ref.position_W_m.copy()
        state.velocity_W_m_s = ref.velocity_W_m_s.copy()
        state.time_s = t
        
        t += dt
        step += 1
        
    ref_points = np.array(ref_list)
    
    # Dibujar la trayectoria recorrida nominal
    ax4.plot(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], 
             label="Referencia de Perfil Suave", color='darkorange', linestyle='-', linewidth=2)
    # Dibujar waypoints discretos
    ax4.scatter(wps[:, 0], wps[:, 1], wps[:, 2], 
                color='black', marker='d', s=35, label="Waypoints objetivo")
    
    # Conexiones rectilíneas de fondo (líneas finas punteadas)
    ax4.plot(wps[:, 0], wps[:, 1], wps[:, 2], 
             color='gray', linestyle=':', linewidth=1, label="Trazas Rectas Directas")
    
    ax4.set_title("d) Familia WAYPOINT\n(Transición Acotada entre Puntos)")
    ax4.set_xlabel("Este (x_W) [m]")
    ax4.set_ylabel("Norte (y_W) [m]")
    ax4.set_zlabel("Arriba (z_W) [m]")
    ax4.set_xlim(-2, 2)
    ax4.set_ylim(-2, 2)
    ax4.set_zlim(0.5, 2.5)
    ax4.legend(loc='upper right')

    plt.tight_layout()
    
    # Asegurar que el directorio de salida existe
    out_path = "TFG_Memoria/Figuras/diagramas/FIG-009.pdf"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, format='pdf', bbox_inches='tight')
    print(f"Figura FIG-009 guardada exitosamente en {out_path}")

if __name__ == "__main__":
    main()
