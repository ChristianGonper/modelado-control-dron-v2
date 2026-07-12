import os
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.patches as patches

# Configurar matplotlib para estilo académico limpio y premium
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 9,
    'axes.labelsize': 10,
    'axes.titlesize': 11
})

def main():
    fig = plt.figure(figsize=(8, 7.5), dpi=300)
    ax = fig.add_subplot(111, projection='3d')
    ax.set_proj_type('persp') # Perspectiva real
    
    # ----------------------------------------------------
    # Definición de la Actitud y Matrices de Rotación
    # ----------------------------------------------------
    # Ángulos de actitud del dron en radianes
    psi = np.radians(35)    # guiñada: rotado a la derecha desde el Norte (eje Y inercial)
    theta = np.radians(-12) # cabeceo: morro hacia abajo
    phi = np.radians(15)    # alabeo: inclinado a la derecha
    
    # Matrices de rotación intrínsecas (orden ZYX)
    R_z = np.array([
        [np.cos(psi), -np.sin(psi), 0],
        [np.sin(psi), np.cos(psi), 0],
        [0, 0, 1]
    ])
    R_y = np.array([
        [np.cos(theta), 0, np.sin(theta)],
        [0, 1, 0],
        [-np.sin(theta), 0, np.cos(theta)]
    ])
    R_x = np.array([
        [1, 0, 0],
        [0, np.cos(phi), -np.sin(phi)],
        [0, np.sin(phi), np.cos(phi)]
    ])
    R_att = R_z @ R_y @ R_x
    
    # Relación de nivel inicial cuerpo-inercial (cero actitud):
    # En ENU: x_W es Este, y_W es Norte, z_W es Arriba.
    # En nivel: x_B (Delante) apunta al Norte (+y_W), y_B (Derecha) al Este (+x_W), z_B (Abajo) a -z_W.
    R_0 = np.array([
        [0, 1, 0],
        [1, 0, 0],
        [0, 0, -1]
    ])
    R_WB = R_att @ R_0
    
    # ----------------------------------------------------
    # Orígenes de Coordenadas
    # ----------------------------------------------------
    OW = np.array([0.0, 0.0, 0.0]) # Origen del Mundo
    OB = np.array([2.0, 3.8, 2.5]) # Origen del Cuerpo (CM del Dron)
    
    # ----------------------------------------------------
    # DIBUJO DEL SISTEMA DE REFERENCIA MUNDO W (ENU)
    # ----------------------------------------------------
    # Ejes ENU en origen OW
    len_W = 2.5
    # Eje x_W (Este): verde oscuro
    ax.quiver(OW[0], OW[1], OW[2], len_W, 0, 0, color='#15803d', arrow_length_ratio=0.12, lw=1.8, pivot='tail', zorder=3)
    ax.text(len_W + 0.15, 0.0, 0.0, r"$x_W$ (Este)", color='#15803d', fontsize=8.5, ha='left', va='center', fontweight='bold')
    
    # Eje y_W (Norte): azul
    ax.quiver(OW[0], OW[1], OW[2], 0, len_W, 0, color='#1d4ed8', arrow_length_ratio=0.12, lw=1.8, pivot='tail', zorder=3)
    ax.text(0.0, len_W + 0.15, 0.0, r"$y_W$ (Norte)", color='#1d4ed8', fontsize=8.5, ha='left', va='center', fontweight='bold')
    
    # Eje z_W (Arriba): rojo
    ax.quiver(OW[0], OW[1], OW[2], 0, 0, len_W, color='#b91c1c', arrow_length_ratio=0.12, lw=1.8, pivot='tail', zorder=3)
    ax.text(0.0, 0.0, len_W + 0.15, r"$z_W$ (Arriba)", color='#b91c1c', fontsize=8.5, ha='center', va='bottom', fontweight='bold')
    
    # Origen del Mundo
    ax.scatter([OW[0]], [OW[1]], [OW[2]], color='black', s=18, zorder=5)
    ax.text(OW[0] - 0.25, OW[1] - 0.25, OW[2] - 0.1, r"$\mathcal{O}_W$", fontsize=10, fontweight='bold', ha='right')
    ax.text(OW[0] + 0.2, OW[1] - 1.2, OW[2], r"Sistema de referencia" "\n" r"mundo $\mathcal{W}$ (ENU)", color='black', fontsize=8.5, fontstyle='italic', ha='center')
    
    # ----------------------------------------------------
    # TRAYECTORIA Y VECTOR DE POSICIÓN
    # ----------------------------------------------------
    # Vector de posición r_WB (trazado discontinuo que llega hasta el origen del cuerpo)
    # Se establece un zorder=1 y color gris azulado para que pase por detrás del chasis y los rotores
    ax.plot([OW[0], OB[0]], [OW[1], OB[1]], [OW[2], OB[2]], color='#64748b', linestyle='--', lw=1.1, zorder=1)
    
    # Flecha indicadora de dirección en la mitad del vector de posición (desplazada del cuerpo)
    arrow_start = OW + 0.42 * (OB - OW)
    dx_arrow, dy_arrow, dz_arrow = 0.08 * (OB - OW)
    ax.quiver(arrow_start[0], arrow_start[1], arrow_start[2], dx_arrow, dy_arrow, dz_arrow, 
              color='#64748b', arrow_length_ratio=0.45, lw=1.3, pivot='tail', zorder=1)
    
    # Etiqueta en el punto medio
    mid = (OW + OB) / 2.0
    ax.text(mid[0] - 0.1, mid[1] + 0.15, mid[2] + 0.1, r"$\mathbf{r}_{WB}$ (Posición)", color='#4b5563', fontsize=8, ha='right', va='center')
    
    # ----------------------------------------------------
    # DIBUJO DEL SISTEMA DE REFERENCIA CUERPO B (FRD)
    # ----------------------------------------------------
    # Ejes de cuerpo en origen OB
    len_B = 1.3
    # Vectores unitarios de cuerpo en coordenadas inerciales
    uxB = R_WB[:, 0]  # Delante
    uyB = R_WB[:, 1]  # Derecha
    uzB = R_WB[:, 2]  # Abajo
    
    # Eje x_B (Delante): cian
    ax.quiver(OB[0], OB[1], OB[2], len_B*uxB[0], len_B*uxB[1], len_B*uxB[2], color='#0891b2', arrow_length_ratio=0.18, lw=1.8, pivot='tail', zorder=4)
    ax.text(OB[0] + (len_B + 0.12)*uxB[0], OB[1] + (len_B + 0.12)*uxB[1], OB[2] + (len_B + 0.12)*uxB[2], 
            r"$x_B$ (Delante)", color='#0891b2', fontsize=8.5, ha='left', va='center', fontweight='bold')
            
    # Eje y_B (Derecha): magenta
    ax.quiver(OB[0], OB[1], OB[2], len_B*uyB[0], len_B*uyB[1], len_B*uyB[2], color='#db2777', arrow_length_ratio=0.18, lw=1.8, pivot='tail', zorder=4)
    ax.text(OB[0] + (len_B + 0.12)*uyB[0], OB[1] + (len_B + 0.12)*uyB[1], OB[2] + (len_B + 0.12)*uyB[2], 
            r"$y_B$ (Derecha)", color='#db2777', fontsize=8.5, ha='left', va='center', fontweight='bold')
            
    # Eje z_B (Abajo): violeta
    ax.quiver(OB[0], OB[1], OB[2], len_B*uzB[0], len_B*uzB[1], len_B*uzB[2], color='#7c3aed', arrow_length_ratio=0.18, lw=1.8, pivot='tail', zorder=4)
    ax.text(OB[0] + (len_B + 0.12)*uzB[0], OB[1] + (len_B + 0.12)*uzB[1], OB[2] + (len_B + 0.12)*uzB[2], 
            r"$z_B$ (Abajo)", color='#7c3aed', fontsize=8.5, ha='center', va='top', fontweight='bold')
            
    # Origen del Cuerpo
    ax.scatter([OB[0]], [OB[1]], [OB[2]], color='black', s=18, zorder=5)
    ax.text(OB[0] - 0.25, OB[1] - 0.25, OB[2] + 0.45, r"$\mathcal{O}_B$ (CM)", fontsize=9.5, fontweight='bold', ha='right', va='center')
    ax.text(OB[0] + 0.3, OB[1] + 1.2, OB[2] + 1.2, r"Sistema de referencia" "\n" r"cuerpo $\mathcal{B}$ (FRD)", color='black', fontsize=8.5, fontstyle='italic', ha='center')
    
    # ----------------------------------------------------
    # DIBUJO DEL CUADRICÓPTERO (Estructura en X y Hélices)
    # ----------------------------------------------------
    d = 0.35  # Distancia de los brazos en cuerpo
    # Posiciones de los 4 rotores en cuerpo
    r_rotors_B = [
        np.array([d, d, 0.0]),   # R0
        np.array([d, -d, 0.0]),  # R1
        np.array([-d, d, 0.0]),  # R2
        np.array([-d, -d, 0.0])  # R3
    ]
    # Posiciones inerciales de los rotores
    r_rotors_W = [OB + R_WB @ r_B for r_B in r_rotors_B]
    
    # Brazos del chasis
    # Se dibujan individualmente desde el centro de masa (OB) hasta el 95% de la longitud 
    # del brazo, asegurando que las líneas grises no solapen ni tapen el punto negro central
    # de los motores en ninguna de las proyecciones 3D.
    for i in range(4):
        r_arm_end_W = OB + 0.86 * (r_rotors_W[i] - OB)
        ax.plot([OB[0], r_arm_end_W[0]], [OB[1], r_arm_end_W[1]], [OB[2], r_arm_end_W[2]],
                color='#9ca3af', linewidth=3.0, zorder=3)
            
    # Dibujar rotores y hélices
    r_prop = 0.18  # Radio de la hélice
    beta = np.linspace(0, 2*np.pi, 50)
    for i, r_rot_W in enumerate(r_rotors_W):
        # Punto del motor (tamaño aumentado para evitar oclusiones y mejorar visibilidad)
        ax.scatter([r_rot_W[0]], [r_rot_W[1]], [r_rot_W[2]], color='black', s=25, zorder=5)
        
        # Puntos del círculo de la hélice en cuerpo
        prop_circle_B = np.array([r_prop * np.cos(beta), r_prop * np.sin(beta), np.zeros_like(beta)])
        # Transformar a inercial
        prop_circle_W = r_rot_W[:, np.newaxis] + R_WB @ prop_circle_B
        
        # Dibujar hélice
        ax.plot(prop_circle_W[0], prop_circle_W[1], prop_circle_W[2], color='#4b5563', alpha=0.35, linewidth=0.8, zorder=3)
        
    # ----------------------------------------------------
    # VECTOR DE EMPUJE EN -z_B (Dirección opuesta a z_B)
    # ----------------------------------------------------
    len_F = 1.6
    # Dirección opuesta a uzB (-uzB)
    u_thrust = -uzB
    ax.quiver(OB[0], OB[1], OB[2], len_F*u_thrust[0], len_F*u_thrust[1], len_F*u_thrust[2], 
              color='#d97706', arrow_length_ratio=0.18, lw=2.4, pivot='tail', zorder=4)
    ax.text(OB[0] + (len_F + 0.1)*u_thrust[0], OB[1] + (len_F + 0.1)*u_thrust[1], OB[2] + (len_F + 0.1)*u_thrust[2], 
            r"$\mathbf{T}$" "\n" r"(Empuje)", color='#d97706', fontsize=9.5, fontweight='bold', ha='center', va='bottom', zorder=10)
            
    # ----------------------------------------------------
    # CONFIGURACIÓN Y LIMPIEZA DE EJES 3D
    # ----------------------------------------------------
    # Ocultar completamente el marco de ejes y rejillas de Matplotlib
    ax.set_axis_off()
    
    # Límites del dibujo
    ax.set_xlim(-0.8, 3.5)
    ax.set_ylim(-0.8, 5.0)
    ax.set_zlim(-0.2, 4.2)
    
    # Ocultar ticks y etiquetas numéricas
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])
    
    # Ajustar vista
    ax.view_init(elev=20, azim=-55)
    
    plt.tight_layout()

    # Guardar (PDF/PNG para la memoria; SVG opcional para la presentación)
    out_pdf = "TFG_Memoria/Figuras/diagramas/FIG-002.pdf"
    out_png = "TFG_Memoria/Figuras/diagramas/FIG-002.png"
    out_svg = os.environ.get("FIG002_SVG_OUT", "").strip() or None

    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    plt.savefig(out_pdf, format="pdf", bbox_inches="tight", transparent=True)
    plt.savefig(out_png, format="png", bbox_inches="tight", dpi=300)
    if out_svg:
        os.makedirs(os.path.dirname(out_svg) or ".", exist_ok=True)
        plt.savefig(out_svg, format="svg", bbox_inches="tight", transparent=True)
    plt.close()

    print("Figura FIG-002 guardada exitosamente:")
    print(f"  - PDF: {out_pdf}")
    print(f"  - PNG: {out_png}")
    if out_svg:
        print(f"  - SVG: {out_svg}")


if __name__ == "__main__":
    main()
