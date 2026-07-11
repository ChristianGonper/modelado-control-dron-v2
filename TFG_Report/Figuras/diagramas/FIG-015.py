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
    ax.plot(x[:-5], y[:-5], color=color, linewidth=1.0, zorder=8)
    
    ax.annotate('', xy=(x[-1], y[-1]), xytext=(x[-6], y[-6]),
                arrowprops=dict(arrowstyle="-|>", color=color, lw=1.0, patchB=None, shrinkA=0, shrinkB=0, mutation_scale=6),
                zorder=9)

def draw_plant_view(ax, xc, yc, thrust_states, yaw_net_moment=0.0):
    """Dibuja la vista en planta del cuadricóptero centrada en (xc, yc)."""
    d = 0.45  # distancia de brazo en la figura
    
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
    
    # 2. Ejes de cuerpo en el CM
    axis_len = 0.75
    ax.annotate('', xy=(xc, yc + axis_len), xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#0f766e', lw=1.2, mutation_scale=8),
                zorder=3)
    ax.text(xc, yc + axis_len + 0.03, r"$x_B$ (Forward)", color='#0f766e', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
    
    ax.annotate('', xy=(xc + axis_len, yc), xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#be185d', lw=1.2, mutation_scale=8),
                zorder=3)
    ax.text(xc + axis_len + 0.03, yc, r"$y_B$ (Right)", color='#be185d', ha='left', va='center', fontsize=7.5, fontweight='bold')
    
    # Símbolo z_B
    zx, zy = xc - 0.75, yc - 0.75
    z_circle = patches.Circle((zx, zy), 0.05, facecolor='none', edgecolor='#6d28d9', lw=1.0, zorder=3)
    ax.add_patch(z_circle)
    ax.plot([zx - 0.035, zx + 0.035], [zy - 0.035, zy + 0.035], color='#6d28d9', lw=1.0, zorder=3)
    ax.plot([zx - 0.035, zx + 0.035], [zy + 0.035, zy - 0.035], color='#6d28d9', lw=1.0, zorder=3)
    ax.text(zx + 0.08, zy, r"$z_B$ (Down)", color='#6d28d9', ha='left', va='center', fontsize=7)
    
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
        
        ax.text(rx, ry + 0.05, str(i), ha='center', va='center', fontsize=7, color=text_color, fontweight='bold', zorder=7)
        ax.text(rx, ry - 0.04, f"({sign})", ha='center', va='center', fontsize=6.2, color=text_color, fontweight='bold', zorder=7)
        
        spin_color = '#b91c1c' if spin == 'CW' else '#1d4ed8'
        draw_spin_arrow(ax, rx, ry, spin, radius=0.18, color=spin_color)
        
    # 5. Momento neto en CM
    if yaw_net_moment > 0.0:
        arrow = patches.FancyArrowPatch((xc - 0.22, yc + 0.22), (xc + 0.22, yc + 0.22),
                                       connectionstyle="arc3,rad=-0.8",
                                       arrowstyle="->,head_width=3.5,head_length=3.5",
                                       color='#b45309', lw=1.8, zorder=10)
        ax.add_patch(arrow)
        ax.text(xc - 0.1, yc, r"$\tau_z > 0$", color='#b45309', ha='right', va='center', fontsize=8.5, fontweight='bold', zorder=10)
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
    
    ax.plot([xc - d, xc + d], [yc + d, yc - d], color='#e2e8f0', linestyle='--', linewidth=1.5, zorder=1)
    ax.plot([xc + d, xc - d], [yc + d, yc - d], color='#e2e8f0', linestyle='--', linewidth=1.5, zorder=1)
    
    ax.plot([xc, xc], [yc, yc + 0.73], color='#cbd5e1', lw=1.0, linestyle='--', zorder=1)
    ax.annotate('', xy=(xc, yc + 0.75), xytext=(xc, yc + 0.71),
                arrowprops=dict(arrowstyle="->", color='#cbd5e1', lw=1.0, shrinkA=0, shrinkB=0), zorder=1)
    ax.plot([xc, xc + 0.73], [yc, yc], color='#cbd5e1', lw=1.0, linestyle='--', zorder=1)
    ax.annotate('', xy=(xc + 0.75, yc), xytext=(xc + 0.71, yc),
                arrowprops=dict(arrowstyle="->", color='#cbd5e1', lw=1.0, shrinkA=0, shrinkB=0), zorder=1)
    
    def rotate(x, y):
        xr = x * np.cos(psi) + y * np.sin(psi)
        yr = -x * np.sin(psi) + y * np.cos(psi)
        return xc + xr, yc + yr

    r0 = rotate(d, d)
    r1 = rotate(-d, d)
    r2 = rotate(d, -d)
    r3 = rotate(-d, -d)
    
    ax.plot([r1[0], r2[0]], [r1[1], r2[1]], color='#9ca3af', linewidth=3.5, zorder=2)
    ax.plot([r0[0], r3[0]], [r0[1], r3[1]], color='#9ca3af', linewidth=3.5, zorder=2)
    
    axis_len = 0.75
    x_pt = rotate(0, axis_len)
    ax.annotate('', xy=x_pt, xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#0f766e', lw=1.2, mutation_scale=8), zorder=3)
    ax.text(x_pt[0], x_pt[1] + 0.03, r"$x_B$", color='#0f766e', ha='center', va='bottom', fontsize=7.5, fontweight='bold')
    
    y_pt = rotate(axis_len, 0)
    ax.annotate('', xy=y_pt, xytext=(xc, yc),
                arrowprops=dict(arrowstyle="->", color='#be185d', lw=1.2, mutation_scale=8), zorder=3)
    ax.text(y_pt[0] + 0.03, y_pt[1], r"$y_B$", color='#be185d', ha='left', va='center', fontsize=7.5, fontweight='bold')
    
    r_arc = 0.22
    arc_t = np.linspace(np.radians(90), np.radians(90 - psi_deg), 40)
    ax.plot(xc + r_arc * np.cos(arc_t), yc + r_arc * np.sin(arc_t), color='#4b5563', lw=1.0, zorder=4)
    
    ax.text(xc + 0.08, yc + 0.27, r"$\psi$", color='#4b5563', ha='center', va='bottom', fontsize=8)
    
    draw_cm_symbol(ax, xc, yc, radius=0.07)
    
    for i, (rx, ry) in enumerate([r0, r1, r2, r3]):
        rotor = patches.Circle((rx, ry), 0.10, facecolor='#e2e3e5', edgecolor='#6c757d', lw=1.0, zorder=6)
        ax.add_patch(rotor)
        propeller = patches.Ellipse((rx, ry), 0.34, 0.08, angle=45 - psi_deg if i%2==0 else -45 - psi_deg,
                                    facecolor='#9ca3af', edgecolor='#4b5563', alpha=0.20, lw=0.6, zorder=5)
        ax.add_patch(propeller)
        ax.text(rx, ry, str(i), ha='center', va='center', fontsize=6.5, color='#41464b', fontweight='bold', zorder=7)
        
    arrow = patches.FancyArrowPatch((xc - 0.7, yc + 0.6), (xc + 0.7, yc + 0.6),
                                   connectionstyle="arc3,rad=-0.5",
                                   arrowstyle="fancy,head_width=2.5,head_length=2.5",
                                   color='#2563eb', alpha=0.8, lw=1.2, zorder=10)
    ax.add_patch(arrow)
    
    ax.text(xc, yc - 0.85, "Yaw\nRotation", color='#2563eb', ha='center', va='top', fontsize=8, fontweight='bold')

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
        ax.text(xc - 0.5, y_val + 0.38, r"$T_{left}$", ha='center', va='bottom', fontsize=7.5, color='#198754')
        ax.text(xc + 0.5, y_val + 0.38, r"$T_{right}$", ha='center', va='bottom', fontsize=7.5, color='#198754')
        
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
        ax.text(xc + 0.90, y_val - 0.5, "Vertical\nAscent", color='#2563eb', ha='left', va='center', fontsize=8, fontweight='bold')
        
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
        
        dx_f, dy_f = sin_p, cos_p
        
        ax.annotate('', xy=(xl + 0.45 * dx_f, yl + 0.45 * dy_f), xytext=(xl, yl),
                    arrowprops=dict(arrowstyle="->", color='#198754', lw=1.5))
        ax.annotate('', xy=(xr + 0.20 * dx_f, yr + 0.20 * dy_f), xytext=(xr, yr),
                    arrowprops=dict(arrowstyle="->", color='#dc3545', lw=1.2))
        ax.text(xl + 0.5 * dx_f, yl + 0.5 * dy_f, r"$T_{left}$ (+)", ha='center', va='bottom', fontsize=7.5, color='#198754')
        ax.text(xr + 0.25 * dx_f, yr + 0.25 * dy_f, r"$T_{right}$ (-)", ha='center', va='bottom', fontsize=7.5, color='#dc3545')
        
        ax.plot([xc, xc], [yc, yc + 0.9], color='#9ca3af', linestyle='--', linewidth=0.8, zorder=1)
        
        arc = patches.Arc((xc, yc), 0.5, 0.5, theta1=75, theta2=90, color='#4b5563', lw=1.0)
        ax.add_patch(arc)
        ax.text(xc + 0.1, yc + 0.3, r"$\phi$", color='#4b5563', ha='left', va='center', fontsize=8)
        
        tx, ty = xc + 0.7 * dx_f, yc + 0.7 * dy_f
        ax.annotate('', xy=(tx, ty), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#b45309', lw=2.0))
        ax.text(tx + 0.05, ty + 0.05, r"$T$", color='#b45309', ha='left', va='bottom', fontsize=9, fontweight='bold')
        
        ax.plot([xc, xc], [yc, yc + 0.7 * cos_p - 0.02], color='#4b5563', lw=1.0, linestyle=':', zorder=3)
        ax.annotate('', xy=(xc, yc + 0.7 * cos_p), xytext=(xc, yc + 0.7 * cos_p - 0.05),
                    arrowprops=dict(arrowstyle="->", color='#4b5563', lw=1.0, shrinkA=0, shrinkB=0), zorder=3)
        
        ax.annotate('', xy=(xc + 0.7 * dx_f, yc), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#be185d', lw=1.2))
        
        ax.annotate('', xy=(xc, yc - 0.7), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#374151', lw=1.2))
        
        ax.annotate('', xy=(xc + 0.65, yc - 0.85), xytext=(xc + 0.3, yc - 0.85),
                    arrowprops=dict(arrowstyle="fancy,head_width=2.5,head_length=2.5", color='#2563eb', alpha=0.8, lw=1.2))
        ax.text(xc + 0.475, yc - 1.1, "Lateral\nFlight", color='#2563eb', ha='center', va='top', fontsize=8, fontweight='bold')
        
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
        ax.text(xr - 0.08, yr, "Tail\n(A)", ha='right', va='center', fontsize=7, color='#555')
        ax.text(xf + 0.08, yf, "Nose\n(F)", ha='left', va='center', fontsize=7, color='#555')
        
        dx_f, dy_f = -sin_t, cos_t
        ax.annotate('', xy=(xr + 0.45 * dx_f, yr + 0.45 * dy_f), xytext=(xr, yr),
                    arrowprops=dict(arrowstyle="->", color='#198754', lw=1.5))
        ax.annotate('', xy=(xf + 0.20 * dx_f, yf + 0.20 * dy_f), xytext=(xf, yf),
                    arrowprops=dict(arrowstyle="->", color='#dc3545', lw=1.2))
        ax.text(xr + 0.5 * dx_f, yr + 0.5 * dy_f, r"$T_{rear}$ (+)", ha='center', va='bottom', fontsize=7.5, color='#198754')
        ax.text(xf + 0.25 * dx_f, yf + 0.25 * dy_f, r"$T_{front}$ (-)", ha='center', va='bottom', fontsize=7.5, color='#dc3545')
        
        ax.plot([xc, xc], [yc, yc + 0.9], color='#9ca3af', linestyle='--', linewidth=0.8, zorder=1)
        
        arc = patches.Arc((xc, yc), 0.5, 0.5, theta1=75, theta2=90, color='#4b5563', lw=1.0)
        ax.add_patch(arc)
        ax.text(xc + 0.11, yc + 0.28, r"$|\theta|$", color='#4b5563', ha='left', va='center', fontsize=8)
        
        tx, ty = xc + 0.7 * dx_f, yc + 0.7 * dy_f
        ax.annotate('', xy=(tx, ty), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#b45309', lw=2.0))
        ax.text(tx + 0.05, ty + 0.05, r"$T$", color='#b45309', ha='left', va='bottom', fontsize=9, fontweight='bold')
        
        ax.plot([xc, xc], [yc, yc + 0.7 * cos_t - 0.02], color='#4b5563', lw=1.0, linestyle=':', zorder=3)
        ax.annotate('', xy=(xc, yc + 0.7 * cos_t), xytext=(xc, yc + 0.7 * cos_t - 0.05),
                    arrowprops=dict(arrowstyle="->", color='#4b5563', lw=1.0, shrinkA=0, shrinkB=0), zorder=3)
        
        ax.annotate('', xy=(xc + 0.7 * dx_f, yc), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#0f766e', lw=1.2))
        
        ax.annotate('', xy=(xc, yc - 0.7), xytext=(xc, yc),
                    arrowprops=dict(arrowstyle="->", color='#374151', lw=1.2))
        
        ax.annotate('', xy=(xc + 0.65, yc - 0.85), xytext=(xc + 0.3, yc - 0.85),
                    arrowprops=dict(arrowstyle="fancy,head_width=2.5,head_length=2.5", color='#2563eb', alpha=0.8, lw=1.2))
        ax.text(xc + 0.475, yc - 1.1, "Longitudinal\nFlight", color='#2563eb', ha='center', va='top', fontsize=8, fontweight='bold')

def main():
    fig, axs = plt.subplots(2, 2, figsize=(9, 6), dpi=300)
    
    xc_p = -1.35
    xc_l = 1.35
    div_x = 0.4
    
    # Subplot 0,0: Collective Thrust
    ax = axs[0, 0]
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("A. Collective Thrust (Altitude)", fontsize=10, fontweight='bold', pad=10)
    
    draw_plant_view(ax, xc=xc_p, yc=0.0, thrust_states=['base', 'base', 'base', 'base'], yaw_net_moment=0.0)
    draw_lateral_view(ax, xc=xc_l, yc=0.0, mode='colectivo')
    
    ax.plot([div_x, div_x], [-1.2, 1.2], color='#e2e8f0', linestyle='--', linewidth=0.8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.3, 1.3)
    
    # Subplot 0,1: Roll and Lateral Flight
    ax = axs[0, 1]
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("B. Roll and Lateral Flight", fontsize=10, fontweight='bold', pad=10)
    
    draw_plant_view(ax, xc=xc_p, yc=0.0, thrust_states=['-', '+', '-', '+'], yaw_net_moment=0.0)
    draw_lateral_view(ax, xc=xc_l, yc=0.0, mode='alabeo')
    
    ax.plot([div_x, div_x], [-1.2, 1.2], color='#e2e8f0', linestyle='--', linewidth=0.8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.3, 1.3)
    
    # Subplot 1,0: Pitch and Longitudinal Flight
    ax = axs[1, 0]
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("C. Pitch and Longitudinal Flight", fontsize=10, fontweight='bold', pad=10)
    
    draw_plant_view(ax, xc=xc_p, yc=0.0, thrust_states=['-', '-', '+', '+'], yaw_net_moment=0.0)
    draw_lateral_view(ax, xc=xc_l, yc=0.0, mode='cabeceo')
    
    ax.plot([div_x, div_x], [-1.2, 1.2], color='#e2e8f0', linestyle='--', linewidth=0.8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.3, 1.3)
    
    # Subplot 1,1: Yaw
    ax = axs[1, 1]
    ax.set_aspect('equal')
    ax.axis('off')
    ax.set_title("D. Yaw via Reactive Torque", fontsize=10, fontweight='bold', pad=10)
    
    draw_plant_view(ax, xc=xc_p, yc=0.0, thrust_states=['-', '+', '+', '-'], yaw_net_moment=1.0)
    draw_rotated_drone_guiñada(ax, xc=xc_l, yc=0.0, psi_deg=20)
    
    ax.plot([div_x, div_x], [-1.2, 1.2], color='#e2e8f0', linestyle='--', linewidth=0.8)
    ax.set_xlim(-2.4, 2.4)
    ax.set_ylim(-1.3, 1.3)
    
    plt.tight_layout()
    plt.subplots_adjust(wspace=0.12, hspace=0.08)
    
    out_pdf = "TFG_Report/Figuras/diagramas/FIG-015.pdf"
    out_png = "TFG_Report/Figuras/diagramas/FIG-015.png"
    
    os.makedirs(os.path.dirname(out_pdf), exist_ok=True)
    
    plt.savefig(out_pdf, format='pdf', bbox_inches='tight')
    plt.savefig(out_png, format='png', bbox_inches='tight')
    plt.close()
    
    print(f"Figura FIG-015 guardada exitosamente en PDF y PNG:")
    print(f"  - PDF: {out_pdf}")
    print(f"  - PNG: {out_png}")

if __name__ == "__main__":
    main()
