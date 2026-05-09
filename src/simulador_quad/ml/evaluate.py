"""
Evaluacion supervisada de modelos entrenados.
"""

import torch
import numpy as np

def evaluate_model(model, loader, normalizer, device="cpu", 
                   mass_kg=1.0, gravity_m_s2=9.81, max_moments_Nm=np.array([10.0, 10.0, 2.0])):
    """
    Evalua el modelo en un dataset supervisado.
    Calcula MSE normalizado, MAE/RMSE en unidades fisicas y porcentaje de saturacion.
    """
    model.eval()
    model.to(device)
    
    total_mse = 0.0
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for x, y in loader:
            x, y = x.to(device), y.to(device)
            y_pred = model(x)
            
            # MSE sobre normalizado
            loss = torch.nn.functional.mse_loss(y_pred, y)
            total_mse += loss.item() * x.size(0)
            
            all_preds.append(y_pred.cpu())
            all_targets.append(y.cpu())
    
    total_mse /= len(loader.dataset)
    
    # Concatenar para metricas fisicas
    Y_pred_norm = torch.cat(all_preds)
    Y_target_norm = torch.cat(all_targets)
    
    # Desnormalizar
    Y_pred = normalizer.denormalize_y(Y_pred_norm)
    Y_target = normalizer.denormalize_y(Y_target_norm)
    
    # Errores en unidades fisicas
    errors = Y_pred - Y_target
    mae = torch.abs(errors).mean(dim=0)
    rmse = torch.sqrt((errors**2).mean(dim=0))
    
    # Calcular saturacion (predicciones fuera de limites fisicos)
    max_thrust = mass_kg * gravity_m_s2 * 2.5
    
    thrust_pred = Y_pred[:, 0]
    moments_pred = Y_pred[:, 1:4]
    
    sat_thrust = (thrust_pred < 0) | (thrust_pred > max_thrust)
    sat_moments = torch.any((moments_pred < -torch.tensor(max_moments_Nm)) | 
                            (moments_pred > torch.tensor(max_moments_Nm)), dim=1)
    
    sat_total = torch.any(sat_thrust.unsqueeze(1) | (moments_pred < -torch.tensor(max_moments_Nm)) | 
                          (moments_pred > torch.tensor(max_moments_Nm)), dim=1)
    
    metrics = {
        "mse_normalized": float(total_mse),
        "mae_thrust_N": float(mae[0]),
        "mae_moments_Nm": mae[1:4].tolist(),
        "rmse_thrust_N": float(rmse[0]),
        "rmse_moments_Nm": rmse[1:4].tolist(),
        "saturation_percentage": {
            "thrust": float(sat_thrust.float().mean() * 100),
            "moments": float(sat_moments.float().mean() * 100),
            "total": float(sat_total.float().mean() * 100)
        }
    }
    
    return metrics
