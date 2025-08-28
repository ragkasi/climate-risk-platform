"""
Temporal Fusion Transformer for flood risk prediction.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np


class TemporalFusionTransformer(nn.Module):
    """
    Temporal Fusion Transformer for flood risk prediction.
    
    Based on the TFT architecture for time series forecasting with
    attention mechanisms and variable selection.
    """
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 64,
        num_heads: int = 4,
        num_layers: int = 3,
        dropout: float = 0.1,
        output_size: int = 1
    ):
        super().__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.dropout = dropout
        self.output_size = output_size
        
        # Input projection
        self.input_projection = nn.Linear(input_size, hidden_size)
        
        # Positional encoding
        self.pos_encoding = PositionalEncoding(hidden_size, dropout)
        
        # Multi-head attention layers
        self.attention_layers = nn.ModuleList([
            MultiHeadAttention(hidden_size, num_heads, dropout)
            for _ in range(num_layers)
        ])
        
        # Feed-forward networks
        self.feed_forward = nn.ModuleList([
            FeedForward(hidden_size, hidden_size * 4, dropout)
            for _ in range(num_layers)
        ])
        
        # Layer normalization
        self.layer_norms1 = nn.ModuleList([
            nn.LayerNorm(hidden_size) for _ in range(num_layers)
        ])
        self.layer_norms2 = nn.ModuleList([
            nn.LayerNorm(hidden_size) for _ in range(num_layers)
        ])
        
        # Output projection
        self.output_projection = nn.Linear(hidden_size, output_size)
        
        # Dropout
        self.dropout_layer = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor, mask: Optional[torch.Tensor] = None) -> torch.Tensor:
        """
        Forward pass through TFT.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_size)
            mask: Optional attention mask
            
        Returns:
            Output tensor of shape (batch_size, seq_len, output_size)
        """
        # Input projection
        x = self.input_projection(x)
        
        # Add positional encoding
        x = self.pos_encoding(x)
        
        # Apply transformer layers
        for i in range(self.num_layers):
            # Multi-head attention
            attn_output, _ = self.attention_layers[i](x, x, x, mask)
            x = self.layer_norms1[i](x + self.dropout_layer(attn_output))
            
            # Feed-forward network
            ff_output = self.feed_forward[i](x)
            x = self.layer_norms2[i](x + self.dropout_layer(ff_output))
        
        # Output projection
        output = self.output_projection(x)
        
        return output


class MultiHeadAttention(nn.Module):
    """Multi-head attention mechanism."""
    
    def __init__(self, hidden_size: int, num_heads: int, dropout: float = 0.1):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.num_heads = num_heads
        self.head_size = hidden_size // num_heads
        
        assert hidden_size % num_heads == 0, "Hidden size must be divisible by num_heads"
        
        # Linear projections for Q, K, V
        self.q_linear = nn.Linear(hidden_size, hidden_size)
        self.k_linear = nn.Linear(hidden_size, hidden_size)
        self.v_linear = nn.Linear(hidden_size, hidden_size)
        
        # Output projection
        self.out_linear = nn.Linear(hidden_size, hidden_size)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self, 
        query: torch.Tensor, 
        key: torch.Tensor, 
        value: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Forward pass through multi-head attention.
        
        Args:
            query: Query tensor
            key: Key tensor
            value: Value tensor
            mask: Optional attention mask
            
        Returns:
            Output tensor and attention weights
        """
        batch_size, seq_len, _ = query.size()
        
        # Linear projections
        Q = self.q_linear(query)
        K = self.k_linear(key)
        V = self.v_linear(value)
        
        # Reshape for multi-head attention
        Q = Q.view(batch_size, seq_len, self.num_heads, self.head_size).transpose(1, 2)
        K = K.view(batch_size, seq_len, self.num_heads, self.head_size).transpose(1, 2)
        V = V.view(batch_size, seq_len, self.num_heads, self.head_size).transpose(1, 2)
        
        # Scaled dot-product attention
        scores = torch.matmul(Q, K.transpose(-2, -1)) / np.sqrt(self.head_size)
        
        if mask is not None:
            scores = scores.masked_fill(mask == 0, -1e9)
        
        attention_weights = F.softmax(scores, dim=-1)
        attention_weights = self.dropout(attention_weights)
        
        # Apply attention to values
        context = torch.matmul(attention_weights, V)
        
        # Reshape and project output
        context = context.transpose(1, 2).contiguous().view(
            batch_size, seq_len, self.hidden_size
        )
        output = self.out_linear(context)
        
        return output, attention_weights


class FeedForward(nn.Module):
    """Feed-forward network."""
    
    def __init__(self, input_size: int, hidden_size: int, dropout: float = 0.1):
        super().__init__()
        
        self.linear1 = nn.Linear(input_size, hidden_size)
        self.linear2 = nn.Linear(hidden_size, input_size)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through feed-forward network."""
        return self.linear2(self.dropout(F.relu(self.linear1(x))))


class PositionalEncoding(nn.Module):
    """Positional encoding for transformer."""
    
    def __init__(self, hidden_size: int, dropout: float = 0.1, max_len: int = 5000):
        super().__init__()
        
        self.dropout = nn.Dropout(dropout)
        
        # Create positional encoding matrix
        pe = torch.zeros(max_len, hidden_size)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        
        div_term = torch.exp(torch.arange(0, hidden_size, 2).float() * 
                           (-np.log(10000.0) / hidden_size))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer('pe', pe)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Add positional encoding to input."""
        x = x + self.pe[:x.size(0), :]
        return self.dropout(x)


class FloodRiskModel(nn.Module):
    """
    Complete flood risk prediction model.
    
    Combines TFT with additional components for flood-specific features.
    """
    
    def __init__(
        self,
        feature_size: int,
        sequence_length: int = 48,
        prediction_horizon: int = 16,
        hidden_size: int = 64,
        num_heads: int = 4,
        num_layers: int = 3,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.feature_size = feature_size
        self.sequence_length = sequence_length
        self.prediction_horizon = prediction_horizon
        
        # TFT encoder
        self.tft_encoder = TemporalFusionTransformer(
            input_size=feature_size,
            hidden_size=hidden_size,
            num_heads=num_heads,
            num_layers=num_layers,
            dropout=dropout,
            output_size=hidden_size
        )
        
        # Decoder for prediction horizon
        self.decoder = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=2,
            dropout=dropout,
            batch_first=True
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
        Forward pass through flood risk model.
        
        Args:
            x: Input features of shape (batch_size, sequence_length, feature_size)
            
        Returns:
            Dictionary with risk probability and quantiles
        """
        # Encode sequence
        encoded = self.tft_encoder(x)
        
        # Get last timestep for prediction
        last_timestep = encoded[:, -1:, :]
        
        # Decode for prediction horizon
        decoder_output, _ = self.decoder(
            last_timestep.repeat(1, self.prediction_horizon, 1)
        )
        
        # Get predictions
        risk_prob = self.risk_activation(self.risk_head(decoder_output))
        
        quantiles = []
        for head in self.quantile_heads:
            quantile = self.quantile_activation(head(decoder_output))
            quantiles.append(quantile)
        
        return {
            'risk_prob': risk_prob.mean(dim=1),  # Average over prediction horizon
            'q10': quantiles[0].mean(dim=1),
            'q50': quantiles[1].mean(dim=1),
            'q90': quantiles[2].mean(dim=1)
        }
