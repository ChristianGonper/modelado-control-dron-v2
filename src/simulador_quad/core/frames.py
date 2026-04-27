import numpy as np

# Constantes para la conversión entre ENU (mundo) y FRD (cuerpo)
# Si el dron está "nivelado" apuntando al Norte (Y_W)
# ENU: X=Este, Y=Norte, Z=Arriba
# FRD: X=Front(Norte), Y=Right(Este), Z=Down(Abajo)
# Entonces, para estar nivelado apuntando al Norte:
# X_B = Y_W
# Y_B = X_W
# Z_B = -Z_W
# La rotación que lleva de B a W sería:
# R * X_B = Y_W
# R * Y_B = X_W
# R * Z_B = -Z_W

def get_level_quaternion(yaw_rad: float = 0.0) -> np.ndarray:
    """
    Devuelve el cuaternión q_WB para un dron nivelado apuntando con un yaw específico.
    Yaw = 0 significa Front = Norte (Y_W).
    """
    # Rotación base de FRD a ENU (yaw=0 -> Front=Norte, Right=Este, Down=Abajo)
    # R_base = [[0, 1, 0],
    #           [1, 0, 0],
    #           [0, 0, -1]]
    # Como cuaternión [w, x, y, z]:
    # Representa una rotación de 180 grados (pi) alrededor del eje [1/sqrt(2), 1/sqrt(2), 0]
    # q_base = [0, 1/sqrt(2), 1/sqrt(2), 0]
    
    q_base = np.array([0.0, np.sqrt(2)/2, np.sqrt(2)/2, 0.0])
    
    # Rotación adicional por yaw alrededor de Z_W (Arriba)
    q_yaw = np.array([np.cos(yaw_rad/2), 0.0, 0.0, np.sin(yaw_rad/2)])
    
    # q_WB = q_yaw * q_base
    w1, x1, y1, z1 = q_yaw
    w2, x2, y2, z2 = q_base
    q_WB = np.array([
        w1*w2 - x1*x2 - y1*y2 - z1*z2,
        w1*x2 + x1*w2 + y1*z2 - z1*y2,
        w1*y2 - x1*z2 + y1*w2 + z1*x2,
        w1*z2 + x1*y2 - y1*x2 + z1*w2
    ])
    return q_WB
