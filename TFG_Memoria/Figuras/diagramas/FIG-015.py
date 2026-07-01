import os
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches

# Configurar matplotlib para estilo académico limpio y premium
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Arial', 'Helvetica'],
    'font.size': 8.5,
    'axes.labelsize': 9.5,
    'axes.titlesize': 10.5,
    'xtick.labelsize': 8,
    'ytick.labelsize': 8,
    'legend.fontsize': 8
})

def draw_cm_symbol(ax, xc, yc, radius=0.08):
    """Dibuja el símbolo clásico de centro de masas (CM) en ingeniería."""
    bg_circle = patches.Circle((xc, yc), radius, facecolor='white', edgecolor='black', lw=1.0, zorder=4)
    ax.add_patch(bg_circle)
    w1 = patches.Wedge((xc, yc), radius, 0, 90, facecolor='black', zorder=5)
    w2 = patches.Wedge((xc, yc), radius, 180, 270, facecolor='black', zorder=5)
    ax.add_patch(w1)
    ax.add_patch(w2)
    border_circle = patches.Circle((xc, yc), radius, facecolor='none', edgecolor='black', lw=1.0, zorder=6)
    ax.add_patch(border_circle)

def draw_spin_arrow(ax, rx, ry, direction, radius=0.20, color='gray'):
    """Dibuja una flecha curva que indica el sentido de giro del rotor."""
    if direction == 'CW':
        angles = np.linspace(np.pi/2, -np.pi, 80)
    else:
        angles = np.linspace(np.pi/2, 2*np.pi, 80)
        
    x = rx + radius * np.cos(angles)
    y = ry + radius * np.sin(angles)
    ax.plot(x, y, color=color, linewidth=1.0, zorder=8)
    
    dt = angles[-1] - angles[-2]
    dx = -radius * np.sin(angles[-1]) * np.sign(dt)
    dy = radius * np.cos(angles[-1]) * np.sign(dt)
    
    length = np.hypot(dx, dy)
    dx /= length
    dy /= length
    
    ax.annotate('', xy=(x[-1], y[-1]), xytext=(x[-1]-dx*0.01, y[-1]-dy*0.01),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0, patchB=None, shrinkA=0, shrinkB=0, mutation_scale=6),
                zorder=9)

def draw_plant_view(ax, xc, yc, thrust_states, yaw_net_moment=0.0):
    """
    Dibuja la vista en planta del cuadricóptero centrada en (xc, yc).
    thrust_states: lista con estados de empuje para R0, R1, R2, R3 (valores: '+', '-', 'base')
    yaw_net_moment: si es mayor a 0, dibuja flecha curva horario en CM; menor a 0, antihorario.
    """
    d = 0.45  # distancia de brazo en la figura
    
    # Coordenadas de los rotores (Horizontal es y_B [derecha], Vertical es x_B [delante])
    rotors_pos = [
        (xc + d, yc + d),  # R0
        (xc - d, yc + d),  # R1
        (xc + d, yc - d),  # R2
        (xc - d, yc - d)   # R3
    ]
    
    rotors_dir = ['CW', 'CCW', 'CCW', 'CW']
    
    # 1. Dibujar brazos del chasis en X
    ax.plot([rotors_pos[1][0], rotors_pos[2][0]], [rotors_pos[1][1], rotors_pos[2][1]], 
            color='#9ca3af', linewidth=3.5, zorder=2)
    ax.plot([rotors_pos[0][0], rotors_pos[3][0]], [rotors_pos[0][1], rotors_pos[3][1]], 
            color='#9ca3af', linewidth=3.5, zorder=2)
    
    # 2. Ejes de cuerpo en el CM (Restablecidos a longitud 0.75)
    axis_len = 0.75
    ax.annotate('', xy=(xc, yc + axis_len), xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#0f766e', lw=1.2, mutation_scale=8),
                zorder=3)
    ax.text(xc, yc + axis_len + 0.03, r"$x_B$ (Delante)", color='#0f766e', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
    
    ax.annotate('', xy=(xc + axis_len, yc), xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#be185d', lw=1.2, mutation_scale=8),
                zorder=3)
    ax.text(xc + axis_len + 0.03, yc, r"$y_B$ (Derecha)", color='#be185d', ha='left', va='center', fontsize=7.5, fontweight='bold')
    
    # Símbolo z_B (Abajo, en esquina inferior izquierda de la planta)
    zx, zy = xc - 0.75, yc - 0.75
    z_circle = patches.Circle((zx, zy), 0.05, facecolor='none', edgecolor='#6d28d9', lw=1.0, zorder=3)
    ax.add_patch(z_circle)
    ax.plot([zx - 0.035, zx + 0.035], [zy - 0.035, zy + 0.035], color='#6d28d9', lw=1.0, zorder=3)
    ax.plot([zx - 0.035, zx + 0.035], [zy + 0.035, zy - 0.035], color='#6d28d9', lw=1.0, zorder=3)
    ax.text(zx + 0.08, zy, r"$z_B$ (Abajo)", color='#6d28d9', ha='left', va='center', fontsize=7)
    
    # 3. Dibujar centro de masas (CM)
    draw_cm_symbol(ax, xc, yc, radius=0.07)
    ax.text(xc + 0.08, yc + 0.08, "CM", fontsize=7.5, fontweight='bold', zorder=7)
    
    # 4. Dibujar rotores
    for i, (rx, ry) in enumerate(rotors_pos):
        state = thrust_states[i]
        spin = rotors_dir[i]
        
        if state == '+':
            face = '#d1e7dd'   # verde suave
            edge = '#198754'   # verde fuerte
            text_color = '#0f5132'
            sign = '+'
            lw = 1.5
        elif state == '-':
            face = '#f8d7da'   # rojo suave
            edge = '#dc3545'   # rojo fuerte
            text_color = '#842029'
            sign = '-'
            lw = 1.5
        else:
            face = '#e2e3e5'   # gris suave
            edge = '#6c757d'   # gris fuerte
            text_color = '#41464b'
            sign = '='
            lw = 1.0
            
        rotor = patches.Circle((rx, ry), 0.12, facecolor=face, edgecolor=edge, lw=lw, zorder=6)
        ax.add_patch(rotor)
        
        propeller = patches.Ellipse((rx, ry), 0.38, 0.10, angle=45 if i%2==0 else -45,
                                    facecolor='#9ca3af', edgecolor='#4b5563', alpha=0.25, lw=0.6, zorder=5)
        ax.add_patch(propeller)
        
        ax.text(rx, ry, f"{i}\n({sign})", ha='center', va='center', fontsize=7, color=text_color, fontweight='bold', zorder=7)
        
        spin_color = '#b91c1c' if spin == 'CW' else '#1d4ed8'
        draw_spin_arrow(ax, rx, ry, spin, radius=0.18, color=spin_color)
        
    # 5. Momento neto en CM
    if yaw_net_moment > 0.0:
        arrow = patches.FancyArrowPatch((xc - 0.22, yc + 0.22), (xc + 0.22, yc + 0.22),
                                       connectionstyle="arc3,rad=-0.8",
                                       arrowstyle="->,head_width=3.5,head_length=3.5",
                                       color='#b45309', lw=1.8, zorder=10)
        ax.add_patch(arrow)
        # Etiqueta de momento colocada abajo a la izquierda en el hueco entre R1 y R3 para dar aire
        ax.text(xc - 0.3, yc, r"$\tau_z > 0$", color='#b45309', ha='right', va='center', fontsize=8.5, fontweight='bold', zorder=10)
    elif yaw_net_moment < 0.0:
        arrow = patches.FancyArrowPatch((xc + 0.22, yc + 0.22), (xc - 0.22, yc + 0.22),
                                       connectionstyle="arc3,rad=0.8",
                                       arrowstyle="->,head_width=3.5,head_length=3.5",
                                       color='#b45309', lw=1.8, zorder=10)
        ax.add_patch(arrow)
        ax.text(xc - 0.3, yc, r"$\tau_z < 0$", color='#b45309', ha='right', va='center', fontsize=8.5, fontweight='bold', zorder=10)

def draw_rotated_drone_guiñada(ax, xc, yc, psi_deg=20):
    """Dibuja un esquema del dron rotado un ángulo psi para ilustrar el efecto de guiñada."""
    psi = np.radians(psi_deg)
    d = 0.45
    
    # 1. Dibujar referencia inercial original (sin rotar) en gris muy tenue
    ax.plot([xc - d, xc + d], [yc + d, yc - d], color='#e2e8f0', linestyle='--', linewidth=1.5, zorder=1)
    ax.plot([xc + d, xc - d], [yc + d, yc - d], color='#e2e8f0', linestyle='--', linewidth=1.5, zorder=1)
    
    # Ejes de referencia inercial
    ax.annotate('', xy=(xc, yc + 0.75), xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#cbd5e1', lw=1.0, linestyle='--'), zorder=1)
    ax.annotate('', xy=(xc + 0.75, yc), xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#cbd5e1', lw=1.0, linestyle='--'), zorder=1)
    
    # Función auxiliar para rotar puntos (sentido horario: guiñada positiva)
    def rotate(x, y):
        xr = x * np.cos(psi) + y * np.sin(psi)
        yr = -x * np.sin(psi) + y * np.cos(psi)
        return xc + xr, yc + yr

    # Coordenadas rotadas de los rotores
    r0 = rotate(d, d)
    r1 = rotate(-d, d)
    r2 = rotate(d, -d)
    r3 = rotate(-d, -d)
    
    # 2. Dibujar brazos del chasis rotados
    ax.plot([r1[0], r2[0]], [r1[1], r2[1]], color='#9ca3af', linewidth=3.5, zorder=2)
    ax.plot([r0[0], r3[0]], [r0[1], r3[1]], color='#9ca3af', linewidth=3.5, zorder=2)
    
    # Ejes de cuerpo rotados (Restablecidos a longitud 0.75)
    axis_len = 0.75
    x_pt = rotate(0, axis_len)
    ax.annotate('', xy=x_pt, xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#0f766e', lw=1.2, mutation_scale=8), zorder=3)
    ax.text(x_pt[0], x_pt[1] + 0.03, r"$x_B$", color='#0f766e', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
    
    y_pt = rotate(axis_len, 0)
    ax.annotate('', xy=y_pt, xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#be185d', lw=1.2, mutation_scale=8), zorder=3)
    ax.text(y_pt[0] + 0.03, y_pt[1], r"$y_B$", color='#be185d', ha='left', va='center', fontsize=7.5, fontweight='bold')
    
    # Arco de rotación en el CM desde el eje vertical (90 deg) hasta el rotado (90 - psi_deg)
    # Reducimos el radio del arco de guiñada (R = 0.22) para que no se pase de largo y sea proporcional
    r_arc = 0.22
    arc_t = np.linspace(np.radians(90), np.radians(90 - psi_deg), 40)
    ax.plot(xc + r_arc * np.cos(arc_t), yc + r_arc * np.sin(arc_t), color='#4b5563', lw=1.0, zorder=4)
    
    # Punta de flecha fina al final del arco (en 90 - psi_deg)
    phi_dest = np.radians(90 - psi_deg)
    # Dirección tangente en sentido horario (CW)
    dx = np.sin(phi_dest)
    dy = -np.cos(phi_dest)
    xf_arc = xc + r_arc * np.cos(phi_dest)
    yf_arc = yc + r_arc * np.sin(phi_dest)
    ax.annotate('', xy=(xf_arc, yf_arc), xytext=(xf_arc - dx*0.01, yf_arc - dy*0.01),
                arrowprops=dict(arrowstyle="->", color='#4b5563', lw=1.0, mutation_scale=4), zorder=4)
    
    # Etiqueta de ángulo psi al lado del arco (a la derecha)
    ax.text(xc + 0.08, yc + 0.27, r"$\psi$", color='#4b5563', ha='center', va='bottom', fontsize=8)
    
    # 3. Dibujar centro de masas (CM)
    draw_cm_symbol(ax, xc, yc, radius=0.07)
    
    # 4. Dibujar los 4 rotores rotados
    for i, (rx, ry) in enumerate([r0, r1, r2, r3]):
        rotor = patches.Circle((rx, ry), 0.10, facecolor='#e2e3e5', edgecolor='#6c757d', lw=1.0, zorder=6)
        ax.add_patch(rotor)
        propeller = patches.Ellipse((rx, ry), 0.34, 0.08, angle=45 - psi_deg if i%2==0 else -45 - psi_deg,
                                    facecolor='#9ca3af', edgecolor='#4b5563', alpha=0.20, lw=0.6, zorder=5)
        ax.add_patch(propeller)
        ax.text(rx, ry, str(i), ha='center', va='center', fontsize=6.5, color='#41464b', fontweight='bold', zorder=7)
        
    # 5. Flecha de rotación azul de guiñada
    arrow = patches.FancyArrowPatch((xc - 0.7, yc + 0.6), (xc + 0.7, yc + 0.6),
                                   connectionstyle="arc3,rad=-0.5",
                                   arrowstyle="fancy,head_width=2.5,head_length=2.5",
                                   color='#2563eb', alpha=0.8, lw=1.2, zorder=10)
    ax.add_patch(arrow)
    
    # Texto de movimiento en la parte inferior
    ax.text(xc, yc - 0.85, "Rotación de\nGuiñada", color='#2563eb', ha='center', va='top', fontsize=8, fontweight='bold')

def draw_lateral_view(ax, xc, yc, mode):
    """Dibuja el esquema lateral de fuerzas."""
    if mode == 'colectivo':
        y_val = yc
        ax.plot([xc - 0.5, xc + 0.5], [y_val, y_val], color='#4b5563', linewidth=3, zorder=2)
        ax.plot(xc - 0.5, y_val, 'o', color='black', markersize=6, zorder=3)
        ax.plot(xc + 0.5, y_val, 'o', color='black', markersize=6, zorder=3)
        
        # Fuerzas individuales
        ax.annotate('', xy=(xc - 0.5, y_val + 0.35), xytext=(xc - 0.5, y_val),
                    arrowprops=dict(arrowstyle="->", color='#198754', lw=1.2))
        ax.annotate('', xy=(xc + 0.5, y_val + 0.35), xytext=(xc + 0.5, y_val),
                    arrowprops=dict(arrowstyle="->", color='#198754', lw=1.2))
        ax.text(xc - 0.5, y_val + 0.38, r"$T_{izq}$", ha='center', va='bottom', fontsize=7.5, color='#198754')
        ax.text(xc + 0.5, y_val + 0.38, r"$T_{der}$", ha='center', va='bottom', fontsize=7.5, color='#198754')
        
        # Fuerza neta en CM
        ax.annotate('', xy=(xc, y_val + 0.7), xytext=(xc, y_val),
                    arrowprops=dict(arrowstyle="->", color='#b45309', lw=2.0))
        ax.text(xc - 0.08, y_val + 0.45, r"$T$", color='#b45309', ha='right', va='center', fontsize=9, fontweight='bold')
        
        # Peso
        ax.annotate('', xy=(xc, y_val - 0.7), xytext=(xc, y_val),
                    arrowprops=dict(arrowstyle="->", color='#374151', lw=1.5))
                    
        # Flecha de desplazamiento vertical azul
        ax.annotate('', xy=(xc + 0.75, y_val - 0.3), xytext=(xc + 0.75, y_val - 0.7),
                    arrowprops=dict(arrowstyle="fancy,head_width=2.5,head_length=2.5", color='#2563eb', alpha=0.8, lw=1.2))
        ax.text(xc + 0.90, y_val - 0.5, "Ascenso\nVertical", color='#2563eb', ha='left', va='center', fontsize=8, fontweight='bold')
        
    elif mode == 'alabeo':
        phi = 15 * np.pi / 180
        cos_p, sin_p = np.cos(phi), np.sin(phi)
        
        xl = xc - 0.5 * cos_p
        yl = yc + 0.5 * sin_p
        xr = xc + 0.5 * cos_p
        yr = yc - 0.5 * sin_p
        
        ax.plot([xl, xr], [yl, yr], color='#4b5563', linewidth=3, zorder=2)
        ax.plot(xl, yl, 'o', color='black', markersize=6, zorder=3)
        ax.plot(xr, yr, 'o', color='black', markersize=6, zorder=3)
        
        # Perpendiculares al dron inclinados hacia arriba-derecha: (sin_p, cos_p)
        dx_f, dy_f = sin_p, cos_p
        
        ax.annotate('', xy=(xl + 0.45 * dx_f, yl + 0.45 * dy_f), xytext=(xl, yl),
                    arrowprops=dict(arrowstyle="->", color='#198754', lw=1.5))
        ax.annotate('', xy=(xr + 0.20 * dx_f, yr + 0.20 * dy_f), xytext=(xr, yr),
                    arrowprops=dict(arrowstyle="->", color='#dc3545', lw=1.2))
        ax.text(xl + 0.5 * dx_f, yl + 0.5 * dy_f, r"$T_{izq}$ (+)", ha='center', va='bottom', fontsize=7.5, color='#198754')
        ax.text(xr + 0.25 * dx_f, yr + 0.25 * dy_f, r"$T_{der}$ (-)", ha='center', va='bottom', fontsize=7.5, color='#dc3545')
        
        # Línea vertical de referencia
        ax.plot([xc, xc], [yc, yc + 0.9], color='#9ca3af', linestyle='--', linewidth=0.8, zorder=1)
        
        # Arco del ángulo de alabeo phi: a la derecha (entre 75 y 90 grados)
        # Corregido: Ahora el arco de phi está a la derecha del empuje (de 75 a 90 grados)
        arc = patches.Arc((xc, yc), 0.5, 0.5, theta1=75, theta2=90, color='#4b5563', lw=1.0)
        ax.add_patch(arc)
        ax.text(xc + 0.08, yc + 0.3, r"$\phi$", color='#4b5563', ha='left', va='center', fontsize=8)
        
        # Fuerza neta inclinada
        tx, ty = xc + 0.7 * dx_f, yc + 0.7 * dy_f
        ax.annotate('', xy=(tx, ty), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#b45309', lw=2.0))
        ax.text(tx + 0.05, ty + 0.05, r"$T$", color='#b45309', ha='left', va='bottom', fontsize=9, fontweight='bold')
        
        # Descomposición de T
        ax.annotate('', xy=(xc, yc + 0.7 * cos_p), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#4b5563', lw=1.0, linestyle=':'))
        
        ax.annotate('', xy=(xc + 0.7 * dx_f, yc), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#be185d', lw=1.2))
        
        # Peso
        ax.annotate('', xy=(xc, yc - 0.7), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#374151', lw=1.2))
        
        # Flecha de desplazamiento lateral reducida y bajada
        ax.annotate('', xy=(xc + 0.65, yc - 0.85), xytext=(xc + 0.3, yc - 0.85),
                    arrowprops=dict(arrowstyle="fancy,head_width=2.5,head_length=2.5", color='#2563eb', alpha=0.8, lw=1.2))
        ax.text(xc + 0.475, yc - 1.1, "Desplazamiento\nLateral", color='#2563eb', ha='center', va='top', fontsize=8, fontweight='bold')
        
    elif mode == 'cabeceo':
        theta = -15 * np.pi / 180
        cos_t, sin_t = np.cos(theta), np.sin(theta)
        
        xr = xc - 0.5 * cos_t
        yr = yc - 0.5 * sin_t
        xf = xc + 0.5 * cos_t
        yf = yc + 0.5 * sin_t
        
        ax.plot([xr, xf], [yr, yf], color='#4b5563', linewidth=3, zorder=2)
        ax.plot(xr, yr, 'o', color='black', markersize=6, zorder=3)
        ax.plot(xf, yf, 'o', color='black', markersize=6, zorder=3)
        ax.text(xr - 0.08, yr, "Cola\n(A)", ha='right', va='center', fontsize=7, color='#555')
        ax.text(xf + 0.08, yf, "Morro\n(F)", ha='left', va='center', fontsize=7, color='#555')
        
        # Fuerzas individuales (Cola mayor que morro)
        dx_f, dy_f = -sin_t, cos_t
        ax.annotate('', xy=(xr + 0.45 * dx_f, yr + 0.45 * dy_f), xytext=(xr, yr),
                    arrowprops=dict(arrowstyle="->", color='#198754', lw=1.5))
        ax.annotate('', xy=(xf + 0.20 * dx_f, yf + 0.20 * dy_f), xytext=(xf, yf),
                    arrowprops=dict(arrowstyle="->", color='#dc3545', lw=1.2))
        ax.text(xr + 0.5 * dx_f, yr + 0.5 * dy_f, r"$T_{tras}$ (+)", ha='center', va='bottom', fontsize=7.5, color='#198754')
        ax.text(xf + 0.25 * dx_f, yf + 0.25 * dy_f, r"$T_{del}$ (-)", ha='center', va='bottom', fontsize=7.5, color='#dc3545')
        
        # Línea vertical de referencia
        ax.plot([xc, xc], [yc, yc + 0.9], color='#9ca3af', linestyle='--', linewidth=0.8, zorder=1)
        
        # Arco del ángulo de cabeceo theta: a la derecha (entre 75 y 90 grados)
        # Corregido: El arco de theta ahora está al lado derecho de la vertical, igual que el empuje T inclinado (de 75 a 90 grados)
        arc = patches.Arc((xc, yc), 0.5, 0.5, theta1=75, theta2=90, color='#4b5563', lw=1.0)
        ax.add_patch(arc)
        ax.text(xc + 0.08, yc + 0.3, r"$|\theta|$", color='#4b5563', ha='left', va='center', fontsize=8)
        
        # Fuerza neta inclinada
        tx, ty = xc + 0.7 * dx_f, yc + 0.7 * dy_f
        ax.annotate('', xy=(tx, ty), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#b45309', lw=2.0))
        ax.text(tx + 0.05, ty + 0.05, r"$T$", color='#b45309', ha='left', va='bottom', fontsize=9, fontweight='bold')
        
        # Descomposición de T
        ax.annotate('', xy=(xc, yc + 0.7 * cos_t), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#4b5563', lw=1.0, linestyle=':'))
        
        ax.annotate('', xy=(xc + 0.7 * dx_f, yc), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#0f766e', lw=1.2))
        
        # Peso
        ax.annotate('', xy=(xc, yc - 0.7), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#374151', lw=1.2))
        
        # Flecha de avance longitudinal
        ax.annotate('', xy=(xc + 0.65, yc - 0.85), xytext=(xc + 0.3, yc - 0.85),
                    arrowprops=dict(arrowstyle="fancy,head_width=2.5,head_length=2.5", color='#2563eb', alpha=0.8, lw=1.2))
        ax.text(xc + 0.475, yc - 1.1, "Avance\nLongitudinal", color='#2563eb', ha='center', va='top', fontsize=8, fontweight='bold')

def main():
    fig, axs = plt.subplots(2, 2, figsize=(9, 6), dpi=300)
    
    # Separación horizontal
    xc_p = -1.35
    xc_l = 1.35
    
    # Línea divisoria vertical gris desplazada a la derecha (X = 0.15)
    div_x = 0.4
    
    # ----------------------------------------------------
    # Subplot 0,0: Empuje Colectivo
    # ----------------------------------------------------
    ax = axs[0, 0]
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("A. Empuje Colectivo (Altitud)", fontsize=10, fontweight='bold', pad=10)
    
    draw_plant_view(ax, xc=xc_p, yc=0.0, thrust_states=['base', 'base', 'base', 'base'], yaw_net_moment=0.0)
    draw_lateral_view(ax, xc=xc_l, yc=0.0, mode='colectivo')
    
    ax.plot([div_x, div_x], [-1.2, 1.2], color='#e2e8f0', linestyle='--', linewidth=0.8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.3, 1.3)
    
    # ----------------------------------------------------
    # Subplot 0,1: Alabeo (Roll) y Desplazamiento Lateral
    # ----------------------------------------------------
    ax = axs[0, 1]
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("B. Alabeo (Roll) y Desplazamiento Lateral", fontsize=10, fontweight='bold', pad=10)
    
    draw_plant_view(ax, xc=xc_p, yc=0.0, thrust_states=['-', '+', '-', '+'], yaw_net_moment=0.0)
    draw_lateral_view(ax, xc=xc_l, yc=0.0, mode='alabeo')
    
    ax.plot([div_x, div_x], [-1.2, 1.2], color='#e2e8f0', linestyle='--', linewidth=0.8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.3, 1.3)
    
    # ----------------------------------------------------
    # Subplot 1,0: Cabeceo (Pitch) y Movimiento Longitudinal
    # ----------------------------------------------------
    ax = axs[1, 0]
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("C. Cabeceo (Pitch) y Movimiento Longitudinal", fontsize=10, fontweight='bold', pad=10)
    
    draw_plant_view(ax, xc=xc_p, yc=0.0, thrust_states=['-', '-', '+', '+'], yaw_net_moment=0.0)
    draw_lateral_view(ax, xc=xc_l, yc=0.0, mode='cabeceo')
    
    ax.plot([div_x, div_x], [-1.2, 1.2], color='#e2e8f0', linestyle='--', linewidth=0.8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.3, 1.3)
    
    # ----------------------------------------------------
    # Subplot 1,1: Guiñada (Yaw)
    # ----------------------------------------------------
    ax = axs[1, 1]
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("D. Guiñada (Yaw) por Par de Reacción", fontsize=10, fontweight='bold', pad=10)
    
    draw_plant_view(ax, xc=xc_p, yc=0.0, thrust_states=['-', '+', '+', '-'], yaw_net_moment=1.0)
    draw_rotated_drone_guiñada(ax, xc=xc_l, yc=0.0, psi_deg=20)
    
    ax.plot([div_x, div_x], [-1.2, 1.2], color='#e2e8f0', linestyle='--', linewidth=0.8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.3, 1.3)
    
    # Ajustes finales y guardado
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.12, hspace=0.08)
    
    out_pdf = "TFG_Memoria/Figuras/diagramas/FIG-015.pdf"
    out_png = "TFG_Memoria/Figuras/diagramas/FIG-015.png"
    
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    
    plt.savefig(out_pdf, format='pdf', bbox_inches='tight')
    plt.savefig(out_png, format='png', bbox_inches='tight')
    plt.close()
    
    print(f"Figura FIG-015 refinada (ronda 3) exitosamente en PDF y PNG:")
    print(f"  - PDF: {out_pdf}")
    print(f"  - PNG: {out_png}")

if __name__ == "__main__":
    main()
