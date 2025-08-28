"""
MLflow logging utilities for model tracking.
"""

import mlflow
import mlflow.pytorch
from typing import Dict, Any, Optional
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import json


class MLflowLogger:
    """Enhanced MLflow logger for Climate Risk Lens models."""
    
    def __init__(self, experiment_name: str, tracking_uri: str = "http://localhost:5000"):
        """
        Initialize MLflow logger.
        
        Args:
            experiment_name: Name of the MLflow experiment
            tracking_uri: MLflow tracking server URI
        """
        self.experiment_name = experiment_name
        self.tracking_uri = tracking_uri
        
        # Set tracking URI
        mlflow.set_tracking_uri(tracking_uri)
        
        # Set experiment
        mlflow.set_experiment(experiment_name)
    
    def log_model_metrics(
        self,
        metrics: Dict[str, float],
        step: Optional[int] = None
    ):
        """
        Log model metrics to MLflow.
        
        Args:
            metrics: Dictionary of metric names and values
            step: Optional step number
        """
        for metric_name, metric_value in metrics.items():
            if step is not None:
                mlflow.log_metric(metric_name, metric_value, step=step)
            else:
                mlflow.log_metric(metric_name, metric_value)
    
    def log_model_parameters(self, params: Dict[str, Any]):
        """
        Log model parameters to MLflow.
        
        Args:
            params: Dictionary of parameter names and values
        """
        for param_name, param_value in params.items():
            mlflow.log_param(param_name, param_value)
    
    def log_model_artifacts(self, artifacts: Dict[str, str]):
        """
        Log model artifacts to MLflow.
        
        Args:
            artifacts: Dictionary of artifact names and file paths
        """
        for artifact_name, artifact_path in artifacts.items():
            if Path(artifact_path).exists():
                mlflow.log_artifact(artifact_path, artifact_name)
            else:
                print(f"Warning: Artifact {artifact_path} not found")
    
    def log_training_plots(
        self,
        history: Dict[str, list],
        save_dir: str = "plots"
    ):
        """
        Log training plots to MLflow.
        
        Args:
            history: Training history dictionary
            save_dir: Directory to save plots
        """
        Path(save_dir).mkdir(exist_ok=True)
        
        # Loss plot
        plt.figure(figsize=(10, 6))
        plt.plot(history['train_loss'], label='Train Loss')
        plt.plot(history['val_loss'], label='Validation Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.title('Training and Validation Loss')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{save_dir}/loss_plot.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # MAE plot
        plt.figure(figsize=(10, 6))
        plt.plot(history['train_mae'], label='Train MAE')
        plt.plot(history['val_mae'], label='Validation MAE')
        plt.xlabel('Epoch')
        plt.ylabel('MAE')
        plt.title('Training and Validation MAE')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{save_dir}/mae_plot.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Log plots
        mlflow.log_artifacts(save_dir, "training_plots")
    
    def log_calibration_plots(
        self,
        y_true: np.ndarray,
        y_pred: np.ndarray,
        save_dir: str = "plots"
    ):
        """
        Log calibration plots to MLflow.
        
        Args:
            y_true: True labels
            y_pred: Predicted probabilities
            save_dir: Directory to save plots
        """
        Path(save_dir).mkdir(exist_ok=True)
        
        # Reliability diagram
        plt.figure(figsize=(10, 8))
        
        # Bin predictions
        n_bins = 10
        bin_boundaries = np.linspace(0, 1, n_bins + 1)
        bin_lowers = bin_boundaries[:-1]
        bin_uppers = bin_boundaries[1:]
        
        bin_centers = []
        bin_accuracies = []
        bin_confidences = []
        
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (y_pred > bin_lower) & (y_pred <= bin_upper)
            prop_in_bin = in_bin.mean()
            
            if prop_in_bin > 0:
                accuracy_in_bin = y_true[in_bin].mean()
                avg_confidence_in_bin = y_pred[in_bin].mean()
                
                bin_centers.append((bin_lower + bin_upper) / 2)
                bin_accuracies.append(accuracy_in_bin)
                bin_confidences.append(avg_confidence_in_bin)
        
        # Plot reliability diagram
        plt.subplot(2, 2, 1)
        plt.plot([0, 1], [0, 1], 'k--', label='Perfect Calibration')
        plt.plot(bin_confidences, bin_accuracies, 'ro-', label='Model')
        plt.xlabel('Confidence')
        plt.ylabel('Accuracy')
        plt.title('Reliability Diagram')
        plt.legend()
        plt.grid(True)
        
        # Histogram of predictions
        plt.subplot(2, 2, 2)
        plt.hist(y_pred, bins=20, alpha=0.7, edgecolor='black')
        plt.xlabel('Predicted Probability')
        plt.ylabel('Frequency')
        plt.title('Distribution of Predictions')
        plt.grid(True)
        
        # Calibration error
        plt.subplot(2, 2, 3)
        calibration_errors = np.abs(np.array(bin_accuracies) - np.array(bin_confidences))
        plt.bar(range(len(calibration_errors)), calibration_errors)
        plt.xlabel('Bin')
        plt.ylabel('Calibration Error')
        plt.title('Calibration Error by Bin')
        plt.grid(True)
        
        # Brier score
        plt.subplot(2, 2, 4)
        brier_scores = []
        for bin_lower, bin_upper in zip(bin_lowers, bin_uppers):
            in_bin = (y_pred > bin_lower) & (y_pred <= bin_upper)
            if in_bin.sum() > 0:
                brier_score = np.mean((y_pred[in_bin] - y_true[in_bin]) ** 2)
                brier_scores.append(brier_score)
            else:
                brier_scores.append(0)
        
        plt.bar(range(len(brier_scores)), brier_scores)
        plt.xlabel('Bin')
        plt.ylabel('Brier Score')
        plt.title('Brier Score by Bin')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/calibration_plots.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Log plots
        mlflow.log_artifacts(save_dir, "calibration_plots")
    
    def log_shap_plots(
        self,
        shap_values: np.ndarray,
        feature_names: list,
        save_dir: str = "plots"
    ):
        """
        Log SHAP plots to MLflow.
        
        Args:
            shap_values: SHAP values
            feature_names: List of feature names
            save_dir: Directory to save plots
        """
        Path(save_dir).mkdir(exist_ok=True)
        
        # Summary plot
        plt.figure(figsize=(10, 8))
        
        # Calculate mean absolute SHAP values
        mean_shap = np.mean(np.abs(shap_values), axis=0)
        
        # Sort features by importance
        feature_importance = sorted(zip(feature_names, mean_shap), key=lambda x: x[1], reverse=True)
        
        # Plot feature importance
        features, importances = zip(*feature_importance)
        plt.barh(range(len(features)), importances)
        plt.yticks(range(len(features)), features)
        plt.xlabel('Mean |SHAP value|')
        plt.title('Feature Importance (SHAP)')
        plt.grid(True, axis='x')
        
        plt.tight_layout()
        plt.savefig(f"{save_dir}/shap_summary.png", dpi=300, bbox_inches='tight')
        plt.close()
        
        # Log plots
        mlflow.log_artifacts(save_dir, "shap_plots")
    
    def log_model_info(
        self,
        model: Any,
        model_name: str,
        model_version: str = "1.0"
    ):
        """
        Log model information to MLflow.
        
        Args:
            model: Model object
            model_name: Name of the model
            model_version: Version of the model
        """
        # Log model
        mlflow.pytorch.log_model(model, "model")
        
        # Log model info
        model_info = {
            "model_name": model_name,
            "model_version": model_version,
            "model_type": type(model).__name__,
            "num_parameters": sum(p.numel() for p in model.parameters()),
            "trainable_parameters": sum(p.numel() for p in model.parameters() if p.requires_grad)
        }
        
        # Save model info
        with open("model_info.json", "w") as f:
            json.dump(model_info, f, indent=2)
        
        mlflow.log_artifact("model_info.json")
    
    def log_data_info(
        self,
        data_info: Dict[str, Any]
    ):
        """
        Log data information to MLflow.
        
        Args:
            data_info: Dictionary with data information
        """
        for key, value in data_info.items():
            mlflow.log_param(f"data_{key}", value)
    
    def log_environment_info(self):
        """Log environment information to MLflow."""
        import torch
        import sys
        
        env_info = {
            "python_version": sys.version,
            "pytorch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "cuda_version": torch.version.cuda if torch.cuda.is_available() else None,
            "device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0
        }
        
        for key, value in env_info.items():
            mlflow.log_param(f"env_{key}", value)
