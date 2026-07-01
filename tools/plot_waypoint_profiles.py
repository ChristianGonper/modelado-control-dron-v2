import os
import numpy as np
import matplotlib.pyplot as plt

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

from simulador_quad.trajectories.analytic import compute_trapezoidal_profile

def main():
    # ----------------------------------------------------
    # Parámetros de los perfiles
    # ----------------------------------------------------
    # 1. Perfil Trapezoidal (alcanza velocidad máxima)
    L_trap = 5.0
    v_max_trap = 1.0
    a_max_trap = 0.5
    
    t_acc_trap = v_max_trap / a_max_trap  # 2.0 s
    t_const_trap = (L_trap - a_max_trap * t_acc_trap**2) / v_max_trap  # 3.0 s
    t_total_trap = 2 * t_acc_trap + t_const_trap  # 7.0 s
    
    # 2. Perfil Triangular (no alcanza velocidad máxima)
    L_tri = 1.5
    v_max_tri = 1.5
    a_max_tri = 0.5
    
    t_acc_tri = np.sqrt(L_tri / a_max_tri)  # 1.732 s
    t_total_tri = 2 * t_acc_tri  # 3.464 s

    # Rango de tiempo para evaluar
    t_eval_trap = np.linspace(-0.5, 7.5, 500)
    t_eval_tri = np.linspace(-0.5, 4.0, 500)

    # Evaluar
    res_trap = np.array([compute_trapezoidal_profile(t, L_trap, v_max_trap, a_max_trap) for t in t_eval_trap])
    res_tri = np.array([compute_trapezoidal_profile(t, L_tri, v_max_tri, a_max_tri) for t in t_eval_tri])

    # Crear figura: 3 filas (s, s_dot, s_ddot), 2 columnas (trapezoidal, triangular)
    fig, axs = plt.subplots(3, 2, figsize=(9, 8), sharex='col', dpi=300)

    # Nombres de fases para sombrear
    colors_phase = {
        'acc': '#d1e7dd',    # verde suave
        'const': '#fff3cd',  # amarillo suave
        'dec': '#f8d7da'     # rojo suave
    }

    # ====================================================
    # COLUMNA 1: PERFIL TRAPEZOIDAL (L = 5.0m)
    # ====================================================
    # Fila 1: Posición s(t)
    axs[0, 0].plot(t_eval_trap, res_trap[:, 0], 'b-', linewidth=2, label=r"$s(t)$")
    axs[0, 0].set_ylabel("Posición $s$ [m]")
    axs[0, 0].set_title(f"Perfil Trapezoidal ($L={L_trap}$ m)")
    
    # Fila 2: Velocidad s_dot(t)
    axs[1, 0].plot(t_eval_trap, res_trap[:, 1], 'g-', linewidth=2, label=r"$\dot{s}(t)$")
    axs[1, 0].set_ylabel(r"Velocidad $\dot{s}$ [m/s]")
    
    # Fila 3: Aceleración s_ddot(t)
    axs[2, 0].plot(t_eval_trap, res_trap[:, 2], 'r-', linewidth=1.8, label=r"$\ddot{s}(t)$")
    axs[2, 0].set_ylabel(r"Aceleración $\ddot{s}$ [m/s$^2$]")
    axs[2, 0].set_xlabel("Tiempo $t$ [s]")

    # Sombrear fases para Columna 1
    for ax in axs[:, 0]:
        ax.grid(True)
        # Fase Aceleración [0, t_acc_trap]
        ax.axvspan(0, t_acc_trap, color=colors_phase['acc'], alpha=0.5, label='Aceleración' if ax == axs[0,0] else "")
        # Fase Crucero [t_acc_trap, t_acc_trap + t_const_trap]
        ax.axvspan(t_acc_trap, t_acc_trap + t_const_trap, color=colors_phase['const'], alpha=0.5, label='Crucero' if ax == axs[0,0] else "")
        # Fase Frenado [t_acc_trap + t_const_trap, t_total_trap]
        ax.axvspan(t_acc_trap + t_const_trap, t_total_trap, color=colors_phase['dec'], alpha=0.5, label='Frenado' if ax == axs[0,0] else "")

    # ====================================================
    # COLUMNA 2: PERFIL TRIANGULAR (L = 1.5m)
    # ====================================================
    # Fila 1: Posición s(t)
    axs[0, 1].plot(t_eval_tri, res_tri[:, 0], 'b-', linewidth=2)
    axs[0, 1].set_title(f"Perfil Triangular ($L={L_tri}$ m)")
    
    # Fila 2: Velocidad s_dot(t)
    axs[1, 1].plot(t_eval_tri, res_tri[:, 1], 'g-', linewidth=2)
    
    # Fila 3: Aceleración s_ddot(t)
    axs[2, 1].plot(t_eval_tri, res_tri[:, 2], 'r-', linewidth=1.8)
    axs[2, 1].set_xlabel("Tiempo $t$ [s]")

    # Sombrear fases para Columna 2
    for ax in axs[:, 1]:
        ax.grid(True)
        # Fase Aceleración [0, t_acc_tri]
        ax.axvspan(0, t_acc_tri, color=colors_phase['acc'], alpha=0.5)
        # Fase Frenado [t_acc_tri, t_total_tri]
        ax.axvspan(t_acc_tri, t_total_tri, color=colors_phase['dec'], alpha=0.5)

    # Añadir leyenda de fases en la parte superior central
    fig.legend(loc='upper center', bbox_to_anchor=(0.5, 0.97), ncol=3, frameon=True)
    
    plt.tight_layout()
    # Ajustar para dejar espacio a la leyenda sin pisar títulos
    plt.subplots_adjust(top=0.86)
    
    # Guardar
    out_path = "TFG_Memoria/Figuras/diagramas/FIG-010.pdf"
    out_png = "TFG_Memoria/Figuras/diagramas/FIG-010.png"
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    plt.savefig(out_path, format='pdf', bbox_inches='tight')
    plt.savefig(out_png, format='png', bbox_inches='tight', dpi=300)
    print(f"Figura FIG-010 guardada exitosamente en PDF y PNG:")
    print(f"  - PDF: {out_path}")
    print(f"  - PNG: {out_png}")

if __name__ == "__main__":
    main()
