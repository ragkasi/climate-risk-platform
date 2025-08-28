"""
Sequence-to-sequence model for smoke and PM2.5 prediction.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
from typing import Dict, List, Optional, Tuple
import numpy as np


class SmokeEncoder(nn.Module):
    """Encoder for smoke prediction with wind field integration."""
    
    def __init__(
        self,
        input_size: int,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.input_size = input_size
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        # Input projection
        self.input_projection = nn.Linear(input_size, hidden_size)
        
        # LSTM encoder
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True,
            bidirectional=True
        )
        
        # Output projection
        self.output_projection = nn.Linear(hidden_size * 2, hidden_size)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, Tuple[torch.Tensor, torch.Tensor]]:
        """
        Forward pass through encoder.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, input_size)
            
        Returns:
            Encoded sequence and hidden states
        """
        # Input projection
        x = self.input_projection(x)
        x = self.dropout(x)
        
        # LSTM encoding
        lstm_out, hidden = self.lstm(x)
        
        # Output projection
        encoded = self.output_projection(lstm_out)
        
        return encoded, hidden


class SmokeDecoder(nn.Module):
    """Decoder for smoke prediction with attention mechanism."""
    
    def __init__(
        self,
        hidden_size: int = 128,
        output_size: int = 1,
        num_layers: int = 2,
        dropout: float = 0.1
    ):
        super().__init__()
        
        self.hidden_size = hidden_size
        self.output_size = output_size
        self.num_layers = num_layers
        
        # Attention mechanism
        self.attention = nn.MultiheadAttention(
            embed_dim=hidden_size,
            num_heads=4,
            dropout=dropout,
            batch_first=True
        )
        
        # LSTM decoder
        self.lstm = nn.LSTM(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout if num_layers > 1 else 0,
            batch_first=True
        )
        
        # Output projection
        self.output_projection = nn.Linear(hidden_size, output_size)
        
        # Dropout
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self, 
        encoder_output: torch.Tensor, 
        hidden: Tuple[torch.Tensor, torch.Tensor],
        target_length: int
    ) -> torch.Tensor:
        """
        Forward pass through decoder.
        
        Args:
            encoder_output: Encoded sequence from encoder
            hidden: Hidden states from encoder
            target_length: Length of target sequence
            
        Returns:
            Decoded sequence
        """
        batch_size = encoder_output.size(0)
        
        # Initialize decoder input
        decoder_input = torch.zeros(batch_size, 1, self.hidden_size, device=encoder_output.device)
        
        outputs = []
        
        for _ in range(target_length):
            # Apply attention
            attn_output, _ = self.attention(
                decoder_input, encoder_output, encoder_output
            )
            
            # LSTM decoding
            lstm_out, hidden = self.lstm(attn_output, hidden)
            
            # Output projection
            output = self.output_projection(lstm_out)
            outputs.append(output)
            
            # Use output as next input
            decoder_input = lstm_out
        
        # Concatenate outputs
        decoded = torch.cat(outputs, dim=1)
        
        return decoded


class WindFieldProcessor(nn.Module):
    """Process wind field data for smoke advection."""
    
    def __init__(self, wind_size: int = 4, hidden_size: int = 64):
        super().__init__()
        
        self.wind_size = wind_size  # u, v, speed, direction
        self.hidden_size = hidden_size
        
        # Wind field processing
        self.wind_conv = nn.Conv2d(wind_size, hidden_size, kernel_size=3, padding=1)
        self.wind_norm = nn.BatchNorm2d(hidden_size)
        
        # Advection features
        self.advection_conv = nn.Conv2d(hidden_size, hidden_size, kernel_size=3, padding=1)
        self.advection_norm = nn.BatchNorm2d(hidden_size)
    
    def forward(self, wind_data: torch.Tensor) -> torch.Tensor:
        """
        Process wind field data.
        
        Args:
            wind_data: Wind field tensor of shape (batch, seq_len, height, width, wind_size)
            
        Returns:
            Processed wind features
        """
        batch_size, seq_len, height, width, _ = wind_data.size()
        
        # Reshape for convolution
        wind_reshaped = wind_data.view(batch_size * seq_len, height, width, self.wind_size)
        wind_reshaped = wind_reshaped.permute(0, 3, 1, 2)  # (batch*seq, wind_size, height, width)
        
        # Process wind field
        wind_features = F.relu(self.wind_norm(self.wind_conv(wind_reshaped)))
        
        # Advection features
        advection_features = F.relu(self.advection_norm(self.advection_conv(wind_features)))
        
        # Reshape back
        advection_features = advection_features.permute(0, 2, 3, 1)  # (batch*seq, height, width, hidden)
        advection_features = advection_features.view(batch_size, seq_len, height, width, self.hidden_size)
        
        return advection_features


class FireDetectionProcessor(nn.Module):
    """Process fire detection data from NASA FIRMS."""
    
    def __init__(self, fire_size: int = 3, hidden_size: int = 64):
        super().__init__()
        
        self.fire_size = fire_size  # lat, lon, frp (fire radiative power)
        self.hidden_size = hidden_size
        
        # Fire detection processing
        self.fire_embedding = nn.Linear(fire_size, hidden_size)
        self.fire_norm = nn.LayerNorm(hidden_size)
    
    def forward(self, fire_data: torch.Tensor) -> torch.Tensor:
        """
        Process fire detection data.
        
        Args:
            fire_data: Fire detection tensor of shape (batch, seq_len, num_fires, fire_size)
            
        Returns:
            Processed fire features
        """
        batch_size, seq_len, num_fires, _ = fire_data.size()
        
        # Reshape for processing
        fire_reshaped = fire_data.view(batch_size * seq_len * num_fires, self.fire_size)
        
        # Process fire detections
        fire_features = F.relu(self.fire_norm(self.fire_embedding(fire_reshaped)))
        
        # Reshape back
        fire_features = fire_features.view(batch_size, seq_len, num_fires, self.hidden_size)
        
        return fire_features


class SmokeSeqModel(nn.Module):
    """
    Complete smoke and PM2.5 prediction model.
    
    Combines sequence-to-sequence architecture with wind field processing
    and fire detection integration.
    """
    
    def __init__(
        self,
        pm25_size: int = 1,
        wind_size: int = 4,
        fire_size: int = 3,
        hidden_size: int = 128,
        num_layers: int = 2,
        dropout: float = 0.1,
        prediction_horizon: int = 24
    ):
        super().__init__()
        
        self.pm25_size = pm25_size
        self.wind_size = wind_size
        self.fire_size = fire_size
        self.hidden_size = hidden_size
        self.prediction_horizon = prediction_horizon
        
        # Wind field processor
        self.wind_processor = WindFieldProcessor(wind_size, hidden_size)
        
        # Fire detection processor
        self.fire_processor = FireDetectionProcessor(fire_size, hidden_size)
        
        # Feature fusion
        self.feature_fusion = nn.Linear(hidden_size * 3, hidden_size)  # pm25 + wind + fire
        
        # Encoder
        self.encoder = SmokeEncoder(
            input_size=hidden_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            dropout=dropout
        )
        
        # Decoder
        self.decoder = SmokeDecoder(
            hidden_size=hidden_size,
            output_size=1,
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
    
    def forward(
        self, 
        pm25_data: torch.Tensor,
        wind_data: torch.Tensor,
        fire_data: torch.Tensor
    ) -> Dict[str, torch.Tensor]:
        """
        Forward pass through smoke prediction model.
        
        Args:
            pm25_data: PM2.5 data of shape (batch, seq_len, pm25_size)
            wind_data: Wind field data of shape (batch, seq_len, height, width, wind_size)
            fire_data: Fire detection data of shape (batch, seq_len, num_fires, fire_size)
            
        Returns:
            Dictionary with risk probability and quantiles
        """
        batch_size, seq_len = pm25_data.size(0), pm25_data.size(1)
        
        # Process wind field
        wind_features = self.wind_processor(wind_data)
        # Average over spatial dimensions
        wind_features = wind_features.mean(dim=(2, 3))  # (batch, seq_len, hidden)
        
        # Process fire detections
        fire_features = self.fire_processor(fire_data)
        # Average over fire detections
        fire_features = fire_features.mean(dim=2)  # (batch, seq_len, hidden)
        
        # Fuse features
        fused_features = torch.cat([pm25_data, wind_features, fire_features], dim=-1)
        fused_features = self.feature_fusion(fused_features)
        
        # Encode sequence
        encoded, hidden = self.encoder(fused_features)
        
        # Decode for prediction horizon
        decoded = self.decoder(encoded, hidden, self.prediction_horizon)
        
        # Get quantile predictions
        quantiles = []
        for head in self.quantile_heads:
            quantile = self.quantile_activation(head(decoded))
            quantiles.append(quantile)
        
        # Calculate risk probability from PM2.5 levels
        # Risk increases with PM2.5 concentration
        risk_prob = self.risk_activation(decoded)
        
        return {
            'risk_prob': risk_prob.mean(dim=1),  # Average over prediction horizon
            'q10': quantiles[0].mean(dim=1),
            'q50': quantiles[1].mean(dim=1),
            'q90': quantiles[2].mean(dim=1)
        }
