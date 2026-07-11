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

AXIS_LABELS = {
    "xlabel": "East (x_W) [m]",
    "ylabel": "North (y_W) [m]",
    "zlabel": "Up (z_W) [m]",
}


def set_3d_axis_labels(ax):
    ax.set_xlabel(AXIS_LABELS["xlabel"], labelpad=0)
    ax.set_ylabel(AXIS_LABELS["ylabel"], labelpad=4)
    ax.set_zlabel("")
    ax.text2D(
        1.14,
        0.50,
        AXIS_LABELS["zlabel"],
        transform=ax.transAxes,
        rotation=90,
        ha="center",
        va="center",
        clip_on=False,
    )


def main():
    fig = plt.figure(figsize=(10, 8.5), dpi=300)
    
    # ----------------------------------------------------
    # 1. HOLD TRAJECTORY (Mantenimiento de posición)
    # ----------------------------------------------------
    ax1 = fig.add_subplot(2, 2, 1, projection='3d')
    hold_pos = np.array([0.0, 0.0, 1.5])
    traj_hold = HoldTrajectory(hold_pos, yaw_rad=0.0)
    
    times = np.linspace(0, 10, 100)
    ref_points = np.array([traj_hold.get_reference(t).position_W_m for t in times])
    
    ax1.plot(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], 
             label="Reference", color='blue', linestyle='-', linewidth=2)
    ax1.scatter([hold_pos[0]], [hold_pos[1]], [hold_pos[2]], 
                color='red', marker='o', s=40, label="Hold Point (0, 0, 1.5)")
    
    u = np.linspace(0, 2 * np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    r_tol = 0.20
    x_tol = hold_pos[0] + r_tol * np.outer(np.cos(u), np.sin(v))
    y_tol = hold_pos[1] + r_tol * np.outer(np.sin(u), np.sin(v))
    z_tol = hold_pos[2] + r_tol * np.outer(np.ones(np.size(u)), np.cos(v))
    ax1.plot_surface(x_tol, y_tol, z_tol, color='red', alpha=0.15, shade=False)
    
    ax1.set_title("a) HOLD Family\n(Hover at Fixed Point)")
    set_3d_axis_labels(ax1)
    ax1.set_xlim(-1, 1)
    ax1.set_ylim(-1, 1)
    ax1.set_zlim(0, 3)
    ax1.set_xticks([-1, 0, 1])
    ax1.set_yticks([-1, 0, 1])
    ax1.set_zticks([0, 1.5, 3])
    ax1.legend(loc='upper right', numpoints=1, scatterpoints=1)
    
    # ----------------------------------------------------
    # 2. CIRCLE TRAJECTORY (Círculo Horizontal)
    # ----------------------------------------------------
    ax2 = fig.add_subplot(2, 2, 2, projection='3d')
    ax2.dist = 11.5
    center = np.array([0.0, 0.0, 1.5])
    radius = 1.5
    omega = 0.5
    traj_circle = CircleTrajectory(center, radius_m=radius, omega_rad_s=omega, yaw_mode="forward")
    
    times = np.linspace(0, 2*np.pi / omega, 150)
    ref_points = np.array([traj_circle.get_reference(t).position_W_m for t in times])
    ref_vels = np.array([traj_circle.get_reference(t).velocity_W_m_s for t in times])
    
    ax2.plot(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], 
             label="Reference", color='green', linestyle='-', linewidth=2)
    ax2.scatter([center[0]], [center[1]], [center[2]], color='black', marker='x', s=30, label="Center")
    
    for i in range(0, len(times), 18):
        p = ref_points[i]
        v = ref_vels[i]
        v_norm = v / np.linalg.norm(v) if np.linalg.norm(v) > 1e-5 else v
        ax2.quiver(p[0], p[1], p[2], v_norm[0], v_norm[1], v_norm[2], 
                   color='darkgreen', length=0.6, arrow_length_ratio=0.3, linewidth=1.5)
        
    ax2.set_title("b) CIRCLE Family\n(Variable Velocity Tracking)")
    set_3d_axis_labels(ax2)
    ax2.set_xlim(-2, 2)
    ax2.set_ylim(-2, 2)
    ax2.set_zlim(0, 3)
    ax2.set_xticks([-2, 0, 2])
    ax2.set_yticks([-2, 0, 2])
    ax2.set_zticks([0, 1.5, 3])
    ax2.legend(loc='upper right', numpoints=1, scatterpoints=1)

    # ----------------------------------------------------
    # 3. LISSAJOUS TRAJECTORY (Espacial 3D)
    # ----------------------------------------------------
    ax3 = fig.add_subplot(2, 2, 3, projection='3d')
    ax3.dist = 11.5
    center_l = np.array([0.0, 0.0, 1.5])
    amps_l = np.array([1.5, 1.2, 0.6])
    omegas_l = np.array([0.4, 0.8, 0.4])
    traj_liss = LissajousTrajectory(center_l, amplitudes=amps_l, omegas=omegas_l)
    
    times = np.linspace(0, 2*np.pi / 0.4, 200)
    ref_points = np.array([traj_liss.get_reference(t).position_W_m for t in times])
    
    ax3.plot(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], 
             label="Reference", color='purple', linestyle='-', linewidth=2)
    
    ax3.set_title("c) LISSAJOUS Family\n(3D Acceleration)")
    set_3d_axis_labels(ax3)
    ax3.set_xlim(-2, 2)
    ax3.set_ylim(-2, 2)
    ax3.set_zlim(0.5, 2.5)
    ax3.set_xticks([-2, 0, 2])
    ax3.set_yticks([-2, 0, 2])
    ax3.set_zticks([0.5, 1.5, 2.5])
    ax3.legend(loc='upper right', numpoints=1, scatterpoints=1)

    # ----------------------------------------------------
    # 4. WAYPOINT / LINE TRAJECTORY (Misión discreta segmentada)
    # ----------------------------------------------------
    ax4 = fig.add_subplot(2, 2, 4, projection='3d')
    ax4.dist = 11.5
    wps = np.array([
        [0.0, -1.5, 0.8],
        [1.5, -0.7, 1.2],
        [1.5, 0.7, 1.6],
        [0.0, 1.5, 2.0],
        [-1.5, 0.0, 2.4]
    ])
    
    traj_wp = LineTrajectory(
        waypoints=wps,
        max_speed_m_s=0.8,
        max_acceleration_m_s2=0.6,
        waypoint_tolerance_m=0.2,
        waypoint_speed_tolerance_m_s=0.2,
        dwell_time_s=0.5
    )
    
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
    
    max_steps = 1500
    step = 0
    while not traj_wp.completed and step < max_steps:
        ref = traj_wp.get_reference_for_state(t, state)
        ref_list.append(ref.position_W_m)
        
        state.position_W_m = ref.position_W_m.copy()
        state.velocity_W_m_s = ref.velocity_W_m_s.copy()
        state.time_s = t
        
        t += dt
        step += 1
        
    ref_points = np.array(ref_list)
    
    ax4.plot(ref_points[:, 0], ref_points[:, 1], ref_points[:, 2], 
             label="Reference", color='darkorange', linestyle='-', linewidth=2)
    ax4.scatter(wps[:, 0], wps[:, 1], wps[:, 2], 
                color='black', marker='d', s=35, label="Target Waypoints")
    
    ax4.set_title("d) WAYPOINT Family\n(Bounded Inter-point Transition)")
    set_3d_axis_labels(ax4)
    ax4.set_xlim(-2, 2)
    ax4.set_ylim(-2, 2)
    ax4.set_zlim(0.5, 2.5)
    ax4.set_xticks([-2, 0, 2])
    ax4.set_yticks([-2, 0, 2])
    ax4.set_zticks([0.5, 1.5, 2.5])
    ax4.legend(loc='upper right', numpoints=1, scatterpoints=1)

    fig.subplots_adjust(left=0.04, right=0.78, bottom=0.16, top=0.94, hspace=0.30, wspace=0.46)
    
    out_path = "TFG_Memoria/Figuras_en/diagramas/FIG-009.pdf"
    out_png = "TFG_Memoria/Figuras_en/diagramas/FIG-009.png"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, format='pdf', bbox_inches='tight', pad_inches=0.12)
    plt.savefig(out_png, format='png', bbox_inches='tight', pad_inches=0.12, dpi=300)
    print(f"Figura FIG-009 guardada exitosamente en PDF y PNG:")
    print(f"  - PDF: {out_path}")
    print(f"  - PNG: {out_png}")

if __name__ == "__main__":
    main()
