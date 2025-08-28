"""
Ensemble meta-learner for combining multiple hazard models.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np


class MetaLearner(nn.Module):
    """
    Meta-learner for combining predictions from multiple hazard models.
    
    Uses a neural network to learn optimal weights for combining
    predictions from different models and hazards.
    """
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        
        # Input projection
        self.input_projection = nn.Linear(input_size, hidden_size)
        
        # Hidden layers
        self.hidden_layers = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size),
                nn.ReLU(),
                nn.Dropout(dropout)
            )
            for _ in range(num_layers - 1)
        ])
        
        # Output projection
        self.output_projection = nn.Linear(hidden_size, 1)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Forward pass through meta-learner.
        
        Args:
            x: Input features of shape (batch_size, input_size)
            
        Returns:
            Meta-learner output
        """
        # Input projection
        x = self.input_projection(x)
        x = F.relu(x)
        x = self.dropout(x)
        
        # Hidden layers
        for layer in self.hidden_layers:
            x = layer(x)
        
        # Output projection
        output = self.output_projection(x)
        
        return output


class EnsembleModel(nn.Module):
    """
    Ensemble model that combines multiple hazard predictions.
    
    Uses meta-learning to optimally combine predictions from
    different models and hazards.
    """
    
    def __init__(
        self,
        hazard_models: Dict[str, nn.Module],
        feature_size: int = 32,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.hazard_models = nn.ModuleDict(hazard_models)
        self.feature_size = feature_size
        
        # Meta-learner for each hazard
        self.meta_learners = nn.ModuleDict({
            hazard: MetaLearner(
                input_size=feature_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                dropout=dropout
            )
            for hazard in hazard_models.keys()
        })
        
        # Global meta-learner for cross-hazard interactions
        self.global_meta_learner = MetaLearner(
            input_size=feature_size * len(hazard_models),
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout
        )
        
        # Output heads for different quantiles
        self.quantile_heads = nn.ModuleList([
            nn.Linear(hidden_size, 1) for _ in range(3)  # q10, q50, q90
        ])
        
        # Activation functions
        self.risk_activation = nn.Sigmoid()
        self.quantile_activation = nn.ReLU()
    
    def forward(self, x: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Forward pass through ensemble model.
        
        Args:
            x: Dictionary of input features for each hazard
            
        Returns:
            Dictionary with ensemble predictions
        """
        batch_size = next(iter(x.values())).size(0)
        device = next(iter(x.values())).device
        
        # Get predictions from individual hazard models
        hazard_predictions = {}
        for hazard, model in self.hazard_models.items():
            if hazard in x:
                pred = model(x[hazard])
                hazard_predictions[hazard] = pred
        
        # Extract features for meta-learning
        meta_features = []
        for hazard, pred in hazard_predictions.items():
            # Use risk probability as feature
            risk_feat = pred['risk_prob'].unsqueeze(-1)
            meta_features.append(risk_feat)
        
        # Concatenate features
        if meta_features:
            combined_features = torch.cat(meta_features, dim=-1)
        else:
            # Fallback if no predictions
            combined_features = torch.zeros(batch_size, self.feature_size, device=device)
        
        # Apply meta-learners
        meta_outputs = {}
        for hazard, meta_learner in self.meta_learners.items():
            if hazard in hazard_predictions:
                # Use individual hazard features
                hazard_feat = hazard_predictions[hazard]['risk_prob'].unsqueeze(-1)
                meta_output = meta_learner(hazard_feat)
                meta_outputs[hazard] = meta_output
        
        # Global meta-learner for cross-hazard interactions
        global_output = self.global_meta_learner(combined_features)
        
        # Combine meta-learner outputs
        if meta_outputs:
            meta_combined = torch.cat(list(meta_outputs.values()), dim=-1)
            final_output = (meta_combined.mean(dim=-1, keepdim=True) + global_output) / 2
        else:
            final_output = global_output
        
        # Get quantile predictions
        quantiles = []
        for head in self.quantile_heads:
            quantile = self.quantile_activation(head(final_output))
            quantiles.append(quantile)
        
        # Calculate ensemble risk probability
        ensemble_risk = self.risk_activation(final_output)
        
        return {
            'risk_prob': ensemble_risk.squeeze(-1),
            'q10': quantiles[0].squeeze(-1),
            'q50': quantiles[1].squeeze(-1),
            'q90': quantiles[2].squeeze(-1),
            'hazard_predictions': hazard_predictions,
            'meta_outputs': meta_outputs
        }


class CalibrationLayer(nn.Module):
    """
    Calibration layer for improving prediction reliability.
    
    Uses isotonic regression to calibrate model outputs.
    """
    
    def __init__(self, num_bins: int = 100):
        super().__init__()
        
        self.num_bins = num_bins
        self.bin_edges = nn.Parameter(torch.linspace(0, 1, num_bins + 1))
        self.bin_values = nn.Parameter(torch.linspace(0, 1, num_bins))
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Apply calibration to predictions.
        
        Args:
            x: Input predictions
            
        Returns:
            Calibrated predictions
        """
        # Find bin indices
        bin_indices = torch.bucketize(x, self.bin_edges[1:-1])
        
        # Get calibrated values
        calibrated = self.bin_values[bin_indices]
        
        return calibrated


class CalibratedEnsembleModel(nn.Module):
    """
    Calibrated ensemble model with reliability improvements.
    """
    
    def __init__(
        self,
        hazard_models: Dict[str, nn.Module],
        feature_size: int = 32,
        hidden_size: int = 64,
        num_layers: int = 2,
        dropout: float = 0.1,
        num_bins: int = 100
    ):
        super().__init__()
        
        # Base ensemble model
        self.ensemble = EnsembleModel(
            hazard_models=hazard_models,
            feature_size=feature_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout
        )
        
        # Calibration layers
        self.risk_calibration = CalibrationLayer(num_bins)
        self.quantile_calibrations = nn.ModuleList([
            CalibrationLayer(num_bins) for _ in range(3)
        ])
    
    def forward(self, x: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]:
        """
        Forward pass through calibrated ensemble model.
        
        Args:
            x: Dictionary of input features for each hazard
            
        Returns:
            Dictionary with calibrated ensemble predictions
        """
        # Get ensemble predictions
        predictions = self.ensemble(x)
        
        # Apply calibration
        calibrated_risk = self.risk_calibration(predictions['risk_prob'])
        
        calibrated_quantiles = []
        for i, calibration in enumerate(self.quantile_calibrations):
            quantile = calibration(predictions[f'q{10 + i * 40}'])  # q10, q50, q90
            calibrated_quantiles.append(quantile)
        
        return {
            'risk_prob': calibrated_risk,
            'q10': calibrated_quantiles[0],
            'q50': calibrated_quantiles[1],
            'q90': calibrated_quantiles[2],
            'hazard_predictions': predictions['hazard_predictions'],
            'meta_outputs': predictions['meta_outputs']
        }
