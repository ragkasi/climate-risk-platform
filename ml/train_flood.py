"""
Training script for flood risk prediction model.
"""

import argparse
import os
import sys
from pathlib import Path
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import mlflow
import mlflow.pytorch
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from ml.models.tft_flood import FloodRiskModel
from ml.utils.mlflow_logger import MLflowLogger


def generate_demo_data(n_samples: int = 1000, sequence_length: int = 48) -> tuple:
    """
    Generate demo data for flood risk prediction.
    
    Args:
        n_samples: Number of samples to generate
        sequence_length: Length of time series
        
    Returns:
        Tuple of (features, targets)
    """
    np.random.seed(42)
    
    # Generate synthetic features
    features = np.random.randn(n_samples, sequence_length, 8)  # 8 features
    
    # Add some temporal patterns
    for i in range(n_samples):
        # Precipitation pattern
        features[i, :, 0] += np.sin(np.linspace(0, 4*np.pi, sequence_length)) * 0.5
        
        # Soil moisture pattern
        features[i, :, 1] += np.cos(np.linspace(0, 2*np.pi, sequence_length)) * 0.3
        
        # Elevation (constant)
        features[i, :, 2] = np.random.normal(0, 1)
        
        # Distance to water (constant)
        features[i, :, 3] = np.random.exponential(1)
        
        # Upstream flow
        features[i, :, 4] += np.random.normal(0, 0.5, sequence_length)
        
        # Temperature
        features[i, :, 5] += np.sin(np.linspace(0, 2*np.pi, sequence_length)) * 0.4
        
        # Humidity
        features[i, :, 6] += np.random.normal(0.7, 0.2, sequence_length)
        
        # Wind speed
        features[i, :, 7] += np.random.exponential(0.5, sequence_length)
    
    # Generate targets based on features
    # Risk increases with precipitation, soil moisture, and decreases with elevation
    risk_scores = []
    for i in range(n_samples):
        # Calculate risk based on features
        precip_avg = np.mean(features[i, :, 0])
        soil_moisture_avg = np.mean(features[i, :, 1])
        elevation = features[i, 0, 2]  # Constant over time
        distance_to_water = features[i, 0, 3]  # Constant over time
        
        # Risk calculation
        risk = (precip_avg * 0.3 + soil_moisture_avg * 0.2 - elevation * 0.1 - distance_to_water * 0.1)
        risk = np.clip(risk, 0, 1)  # Clip to [0, 1]
        
        risk_scores.append(risk)
    
    targets = np.array(risk_scores)
    
    return features, targets


def train_model(
    model: nn.Module,
    train_loader: DataLoader,
    val_loader: DataLoader,
    num_epochs: int = 100,
    learning_rate: float = 0.001,
    device: str = "cpu"
) -> dict:
    """
    Train the flood risk model.
    
    Args:
        model: Model to train
        train_loader: Training data loader
        val_loader: Validation data loader
        num_epochs: Number of training epochs
        learning_rate: Learning rate
        device: Device to train on
        
    Returns:
        Training history
    """
    model.to(device)
    
    # Loss function and optimizer
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)
    scheduler = optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=10, factor=0.5)
    
    # Training history
    history = {
        'train_loss': [],
        'val_loss': [],
        'train_mae': [],
        'val_mae': []
    }
    
    best_val_loss = float('inf')
    
    for epoch in range(num_epochs):
        # Training phase
        model.train()
        train_loss = 0.0
        train_mae = 0.0
        
        for batch_idx, (data, target) in enumerate(train_loader):
            data, target = data.to(device), target.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass
            output = model(data)
            loss = criterion(output['risk_prob'].squeeze(), target)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item()
            train_mae += torch.mean(torch.abs(output['risk_prob'].squeeze() - target)).item()
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        val_mae = 0.0
        
        with torch.no_grad():
            for data, target in val_loader:
                data, target = data.to(device), target.to(device)
                
                output = model(data)
                loss = criterion(output['risk_prob'].squeeze(), target)
                
                val_loss += loss.item()
                val_mae += torch.mean(torch.abs(output['risk_prob'].squeeze() - target)).item()
        
        # Calculate averages
        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        train_mae /= len(train_loader)
        val_mae /= len(val_loader)
        
        # Update history
        history['train_loss'].append(train_loss)
        history['val_loss'].append(val_loss)
        history['train_mae'].append(train_mae)
        history['val_mae'].append(val_mae)
        
        # Learning rate scheduling
        scheduler.step(val_loss)
        
        # Log progress
        if epoch % 10 == 0:
            logger.info(f"Epoch {epoch}: Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save(model.state_dict(), 'best_flood_model.pth')
    
    return history


def main():
    """Main training function."""
    parser = argparse.ArgumentParser(description='Train flood risk prediction model')
    parser.add_argument('--demo', action='store_true', help='Use demo data')
    parser.add_argument('--epochs', type=int, default=100, help='Number of epochs')
    parser.add_argument('--batch-size', type=int, default=32, help='Batch size')
    parser.add_argument('--learning-rate', type=float, default=0.001, help='Learning rate')
    parser.add_argument('--device', type=str, default='cpu', help='Device to use')
    
    args = parser.parse_args()
    
    # Set up logging
    logger.add("flood_training.log", rotation="1 day")
    
    # Set up MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("flood-risk-prediction")
    
    with mlflow.start_run():
        # Log parameters
        mlflow.log_param("epochs", args.epochs)
        mlflow.log_param("batch_size", args.batch_size)
        mlflow.log_param("learning_rate", args.learning_rate)
        mlflow.log_param("device", args.device)
        mlflow.log_param("demo_mode", args.demo)
        
        # Generate or load data
        if args.demo:
            logger.info("Generating demo data...")
            features, targets = generate_demo_data(n_samples=1000, sequence_length=48)
        else:
            # In production, load real data
            logger.error("Real data loading not implemented yet")
            return
        
        # Prepare data
        X_train, X_val, y_train, y_val = train_test_split(
            features, targets, test_size=0.2, random_state=42
        )
        
        # Create data loaders
        train_dataset = TensorDataset(
            torch.FloatTensor(X_train),
            torch.FloatTensor(y_train)
        )
        val_dataset = TensorDataset(
            torch.FloatTensor(X_val),
            torch.FloatTensor(y_val)
        )
        
        train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=False)
        
        # Create model
        model = FloodRiskModel(
            feature_size=8,
            sequence_length=48,
            prediction_horizon=16,
            hidden_size=64,
            num_heads=4,
            num_layers=3,
            dropout=0.1
        )
        
        logger.info(f"Model created with {sum(p.numel() for p in model.parameters())} parameters")
        
        # Train model
        logger.info("Starting training...")
        history = train_model(
            model=model,
            train_loader=train_loader,
            val_loader=val_loader,
            num_epochs=args.epochs,
            learning_rate=args.learning_rate,
            device=args.device
        )
        
        # Log metrics
        mlflow.log_metric("final_train_loss", history['train_loss'][-1])
        mlflow.log_metric("final_val_loss", history['val_loss'][-1])
        mlflow.log_metric("final_train_mae", history['train_mae'][-1])
        mlflow.log_metric("final_val_mae", history['val_mae'][-1])
        mlflow.log_metric("best_val_loss", min(history['val_loss']))
        
        # Log model
        mlflow.pytorch.log_model(model, "model")
        
        # Register model
        model_uri = f"runs:/{mlflow.active_run().info.run_id}/model"
        mlflow.register_model(model_uri, "flood-head")
        
        logger.info("Training completed successfully!")


if __name__ == "__main__":
    main()
