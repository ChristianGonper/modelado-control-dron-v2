"""
Bucle de entrenamiento supervisado.
"""

import os
import time
import json
import torch
import torch.nn as nn
from torch.utils.data import DataLoader

def train_model(model, train_loader, val_loader, config):
    """
    Entrena el modelo usando los loaders proporcionados.
    Implementa Early Stopping basado en val_loss.
    """
    device = config.get("device", "cpu")
    model.to(device)
    
    epochs = config.get("epochs", 100)
    lr = config.get("lr", 1e-3)
    patience = config.get("patience", 10)
    out_dir = config.get("out_dir", "results")
    
    os.makedirs(os.path.join(out_dir, "checkpoints"), exist_ok=True)
    os.makedirs(os.path.join(out_dir, "metrics"), exist_ok=True)
    
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    
    best_val_loss = float("inf")
    epochs_no_improve = 0
    
    history = {
        "train_loss": [],
        "val_loss": []
    }
    
    print(f"Starting training for {epochs} epochs on {device}...")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        for x, y in train_loader:
            x, y = x.to(device), y.to(device)
            
            optimizer.zero_grad()
            y_pred = model(x)
            loss = criterion(y_pred, y)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * x.size(0)
        
        train_loss /= len(train_loader.dataset)
        
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for x, y in val_loader:
                x, y = x.to(device), y.to(device)
                y_pred = model(x)
                loss = criterion(y_pred, y)
                val_loss += loss.item() * x.size(0)
        
        val_loss /= len(val_loader.dataset)
        
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        
        print(f"Epoch {epoch+1}/{epochs} - train_loss: {train_loss:.6f} - val_loss: {val_loss:.6f}")
        
        # Early Stopping
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            epochs_no_improve = 0
            # Guardar mejor modelo
            torch.save(model.state_dict(), os.path.join(out_dir, "checkpoints", f"{config['architecture']}_best.pt"))
        else:
            epochs_no_improve += 1
            if epochs_no_improve >= patience:
                print(f"Early stopping at epoch {epoch+1}")
                break
    
    # Guardar metricas
    with open(os.path.join(out_dir, "metrics", "train_metrics.json"), "w") as f:
        json.dump({"train_loss": history["train_loss"]}, f, indent=4)
    with open(os.path.join(out_dir, "metrics", "val_metrics.json"), "w") as f:
        json.dump({"val_loss": history["val_loss"]}, f, indent=4)
    
    return history
