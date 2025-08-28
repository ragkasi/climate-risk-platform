"""
Spatiotemporal Transformer for heat risk prediction.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np


class SpatialAttention(nn.Module):
    """Spatial attention mechanism for geographic features."""
    
    def __init__(self, hidden_size: int, num_heads: int = 4):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_size = hidden_size // num_heads
        
        assert hidden_size % num_heads == 0, "Hidden size must be divisible by num_heads"
        
        # Linear projections
        self.q_linear = nn.Linear(hidden_size, hidden_size)
        self.k_linear = nn.Linear(hidden_size, hidden_size)
        self.v_linear = nn.Linear(hidden_size, hidden_size)
        self.out_linear = nn.Linear(hidden_size, hidden_size)
        
        # Spatial position encoding
        self.spatial_encoding = nn.Parameter(torch.randn(1, 1, hidden_size))
    
    def forward(self, x: torch.Tensor, spatial_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through spatial attention.
        
        Args:
            x: Input tensor of shape (batch_size, num_locations, hidden_size)
            spatial_mask: Optional spatial adjacency mask
            
        Returns:
            Output tensor with spatial attention applied
        """
        batch_size, num_locations, _ = x.size()
        
        # Add spatial encoding
        x = x + self.spatial_encoding
        
        # Linear projections
        Q = self.q_linear(x)
        K = self.k_linear(x)
        V = self.v_linear(x)
        
        # Reshape for multi-head attention
        Q = Q.view(batch_size, num_locations, self.num_heads, self.head_size).transpose(1, 2)
        K = K.view(batch_size, num_locations, self.num_heads, self.head_size).transpose(1, 2)
        V = V.view(batch_size, num_locations, self.num_heads, self.head_size).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.head_size)
        
        # Apply spatial mask if provided
        if spatial_mask is not None:
            scores = scores.masked_fill(spatial_mask == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        
        # Apply attention to values
        context = torch.matmul(attention_weights, V)
        
        # Reshape and project output
        context = context.transpose(1, 2).contiguous().view(
            batch_size, num_locations, self.hidden_size
        )
        output = self.out_linear(context)
        
        return output


class TemporalAttention(nn.Module):
    """Temporal attention mechanism for time series features."""
    
    def __init__(self, hidden_size: int, num_heads: int = 4):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_size = hidden_size // num_heads
        
        # Linear projections
        self.q_linear = nn.Linear(hidden_size, hidden_size)
        self.k_linear = nn.Linear(hidden_size, hidden_size)
        self.v_linear = nn.Linear(hidden_size, hidden_size)
        self.out_linear = nn.Linear(hidden_size, hidden_size)
        
        # Positional encoding
        self.pos_encoding = PositionalEncoding(hidden_size)
    
    def forward(self, x: torch.Tensor, temporal_mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through temporal attention.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, hidden_size)
            temporal_mask: Optional temporal mask
            
        Returns:
            Output tensor with temporal attention applied
        """
        batch_size, seq_len, _ = x.size()
        
        # Add positional encoding
        x = self.pos_encoding(x)
        
        # Linear projections
        Q = self.q_linear(x)
        K = self.k_linear(x)
        V = self.v_linear(x)
        
        # Reshape for multi-head attention
        Q = Q.view(batch_size, seq_len, self.num_heads, self.head_size).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.head_size).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.head_size).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.head_size)
        
        # Apply temporal mask if provided
        if temporal_mask is not None:
            scores = scores.masked_fill(temporal_mask == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        
        # Apply attention to values
        context = torch.matmul(attention_weights, V)
        
        # Reshape and project output
        context = context.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.hidden_size
        )
        output = self.out_linear(context)
        
        return output


class PositionalEncoding(nn.Module):
    """Positional encoding for temporal sequences."""
    
    def __init__(self, hidden_size: int, max_len: int = 5000):
        super().__init__()
        
        pe = torch.zeros(max_len, hidden_size)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        
        div_term = torch.exp(torch.arange(0, hidden_size, 2).float() * 
                           (-np.log(10000.0) / hidden_size))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        pe = pe.unsqueeze(0)
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add positional encoding to input."""
        return x + self.pe[:, :x.size(1), :]


class SpatiotemporalTransformer(nn.Module):
    """
    Spatiotemporal Transformer for heat risk prediction.
    
    Combines spatial and temporal attention mechanisms for
    urban heat island and extreme heat prediction.
    """
    
    def __init__(
        self,
        feature_size: int,
        hidden_size: int = 64,
        num_heads: int = 4,
        num_layers: int = 3,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.feature_size = feature_size
        self.hidden_size = hidden_size
        
        # Input projection
        self.input_projection = nn.Linear(feature_size, hidden_size)
        
        # Spatial attention layers
        self.spatial_attention = nn.ModuleList([
            SpatialAttention(hidden_size, num_heads)
            for _ in range(num_layers)
        ])
        
        # Temporal attention layers
        self.temporal_attention = nn.ModuleList([
            TemporalAttention(hidden_size, num_heads)
            for _ in range(num_layers)
        ])
        
        # Layer normalization
        self.spatial_norms = nn.ModuleList([
            nn.LayerNorm(hidden_size) for _ in range(num_layers)
        ])
        self.temporal_norms = nn.ModuleList([
            nn.LayerNorm(hidden_size) for _ in range(num_layers)
        ])
        
        # Feed-forward networks
        self.feed_forward = nn.ModuleList([
            nn.Sequential(
                nn.Linear(hidden_size, hidden_size * 4),
                nn.ReLU(),
                nn.Dropout(dropout),
                nn.Linear(hidden_size * 4, hidden_size)
            )
            for _ in range(num_layers)
        ])
        
        # Output projection
        self.output_projection = nn.Linear(hidden_size, 1)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self, 
        x: torch.Tensor, 
        spatial_mask: Optional[torch.Tensor] = None,
        temporal_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass through spatiotemporal transformer.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, num_locations, feature_size)
            spatial_mask: Optional spatial adjacency mask
            temporal_mask: Optional temporal mask
            
        Returns:
            Output tensor of shape (batch_size, seq_len, num_locations, 1)
        """
        batch_size, seq_len, num_locations, _ = x.size()
        
        # Reshape for processing
        x = x.view(batch_size * seq_len, num_locations, self.feature_size)
        
        # Input projection
        x = self.input_projection(x)
        
        # Apply spatiotemporal attention layers
        for i in range(len(self.spatial_attention)):
            # Spatial attention
            spatial_out = self.spatial_attention[i](x, spatial_mask)
            x = self.spatial_norms[i](x + self.dropout(spatial_out))
            
            # Temporal attention (reshape for temporal processing)
            x_temp = x.view(batch_size, seq_len, num_locations, self.hidden_size)
            x_temp = x_temp.transpose(1, 2)  # (batch, locations, seq, hidden)
            x_temp = x_temp.contiguous().view(batch_size * num_locations, seq_len, self.hidden_size)
            
            temporal_out = self.temporal_attention[i](x_temp, temporal_mask)
            x_temp = self.temporal_norms[i](x_temp + self.dropout(temporal_out))
            
            # Reshape back
            x_temp = x_temp.view(batch_size, num_locations, seq_len, self.hidden_size)
            x_temp = x_temp.transpose(1, 2)  # (batch, seq, locations, hidden)
            x = x_temp.contiguous().view(batch_size * seq_len, num_locations, self.hidden_size)
            
            # Feed-forward network
            ff_out = self.feed_forward[i](x)
            x = x + self.dropout(ff_out)
        
        # Output projection
        output = self.output_projection(x)
        
        # Reshape to original format
        output = output.view(batch_size, seq_len, num_locations, 1)
        
        return output


class HeatRiskModel(nn.Module):
    """
    Complete heat risk prediction model.
    
    Combines spatiotemporal transformer with heat-specific features.
    """
    
    def __init__(
        self,
        feature_size: int,
        sequence_length: int = 72,  # 72 hours
        hidden_size: int = 64,
        num_heads: int = 4,
        num_layers: int = 3,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.feature_size = feature_size
        self.sequence_length = sequence_length
        
        # Spatiotemporal transformer
        self.st_transformer = SpatiotemporalTransformer(
            feature_size=feature_size,
            hidden_size=hidden_size,
            num_heads=num_heads,
            num_layers=num_layers,
            dropout=dropout
        )
        
        # Output heads for different quantiles
        self.risk_head = nn.Linear(hidden_size, 1)
        self.quantile_heads = nn.ModuleList([
            nn.Linear(hidden_size, 1) for _ in range(3)  # q10, q50, q90
        ])
        
        # Activation functions
        self.risk_activation = nn.Sigmoid()
        self.quantile_activation = nn.ReLU()
    
    def forward(self, x: torch.Tensor) -> Dict[str, torch.Tensor]:
        """
        Forward pass through heat risk model.
        
        Args:
            x: Input features of shape (batch_size, seq_len, num_locations, feature_size)
            
        Returns:
            Dictionary with risk probability and quantiles
        """
        # Get spatiotemporal features
        st_features = self.st_transformer(x)
        
        # Get last timestep for prediction
        last_timestep = st_features[:, -1, :, :]  # (batch, locations, 1)
        
        # Reshape for output heads
        batch_size, num_locations, _ = last_timestep.size()
        features = last_timestep.view(batch_size * num_locations, -1)
        
        # Get predictions
        risk_prob = self.risk_activation(self.risk_head(features))
        
        quantiles = []
        for head in self.quantile_heads:
            quantile = self.quantile_activation(head(features))
            quantiles.append(quantile)
        
        # Reshape back
        risk_prob = risk_prob.view(batch_size, num_locations)
        quantiles = [q.view(batch_size, num_locations) for q in quantiles]
        
        return {
            'risk_prob': risk_prob,
            'q10': quantiles[0],
            'q50': quantiles[1],
            'q90': quantiles[2]
        }
