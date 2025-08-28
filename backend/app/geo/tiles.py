"""
Map tile utilities for vector tile generation.
"""

import json
import math
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import pyproj
from functools import partial


@dataclass
class TileCoord:
    """Tile coordinate representation."""
    z: int  # Zoom level
    x: int  # X coordinate
    y: int  # Y coordinate


class TileSystem:
    """Map tile system utilities."""
    
    def __init__(self, tile_size: int = 256):
        self.tile_size = tile_size
    
    def deg2num(self, lat_deg: float, lon_deg: float, zoom: int) -> Tuple[int, int]:
        """
        Convert lat/lon to tile coordinates.
        
        Args:
            lat_deg: Latitude in degrees
            lon_deg: Longitude in degrees
            zoom: Zoom level
            
        Returns:
            (x, y) tile coordinates
        """
        lat_rad = math.radians(lat_deg)
        n = 2.0 ** zoom
        x = int((lon_deg + 180.0) / 360.0 * n)
        y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
        return (x, y)
    
    def num2deg(self, x: int, y: int, zoom: int) -> Tuple[float, float, float, float]:
        """
        Convert tile coordinates to lat/lon bounds.
        
        Args:
            x: X tile coordinate
            y: Y tile coordinate
            zoom: Zoom level
            
        Returns:
            (min_lon, min_lat, max_lon, max_lat)
        """
        n = 2.0 ** zoom
        min_lon = x / n * 360.0 - 180.0
        max_lon = (x + 1) / n * 360.0 - 180.0
        min_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        max_lat = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
        return (min_lon, min_lat, max_lon, max_lat)
    
    def get_tile_bounds(self, coord: TileCoord) -> Tuple[float, float, float, float]:
        """Get lat/lon bounds for tile coordinate."""
        return self.num2deg(coord.x, coord.y, coord.z)
    
    def get_tile_polygon(self, coord: TileCoord) -> Polygon:
        """Get Shapely polygon for tile bounds."""
        min_lon, min_lat, max_lon, max_lat = self.get_tile_bounds(coord)
        return Polygon([
            (min_lon, min_lat),
            (max_lon, min_lat),
            (max_lon, max_lat),
            (min_lon, max_lat),
            (min_lon, min_lat)
        ])


class VectorTileBuilder:
    """Builder for vector tiles with risk data."""
    
    def __init__(self, tile_system: TileSystem):
        self.tile_system = tile_system
    
    def build_risk_tile(self, coord: TileCoord, risk_data: List[Dict[str, Any]]) -> bytes:
        """
        Build vector tile with risk data.
        
        Args:
            coord: Tile coordinate
            risk_data: List of risk predictions for this tile
            
        Returns:
            Vector tile as bytes (simplified JSON for demo)
        """
        tile_bounds = self.tile_system.get_tile_bounds(coord)
        min_lon, min_lat, max_lon, max_lat = tile_bounds
        
        # Filter risk data to tile bounds
        tile_risk_data = []
        for risk in risk_data:
            # Simple bounds check (in production, use proper spatial indexing)
            if (min_lon <= risk.get('lon', 0) <= max_lon and 
                min_lat <= risk.get('lat', 0) <= max_lat):
                tile_risk_data.append(risk)
        
        # Build simplified vector tile structure
        vector_tile = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for risk in tile_risk_data:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [risk.get('lon', 0), risk.get('lat', 0)]
                },
                "properties": {
                    "grid_id": risk.get('grid_id', ''),
                    "hazard_type": risk.get('hazard_type', ''),
                    "p_risk": risk.get('p_risk', 0.0),
                    "q10": risk.get('q10', 0.0),
                    "q50": risk.get('q50', 0.0),
                    "q90": risk.get('q90', 0.0),
                    "model_version": risk.get('model_version', ''),
                    "issued_at": risk.get('issued_at', ''),
                }
            }
            vector_tile["features"].append(feature)
        
        return json.dumps(vector_tile, ensure_ascii=True).encode('utf-8')
    
    def build_uncertainty_tile(self, coord: TileCoord, uncertainty_data: List[Dict[str, Any]]) -> bytes:
        """
        Build vector tile with uncertainty data.
        
        Args:
            coord: Tile coordinate
            uncertainty_data: List of uncertainty predictions
            
        Returns:
            Vector tile as bytes
        """
        tile_bounds = self.tile_system.get_tile_bounds(coord)
        min_lon, min_lat, max_lon, max_lat = tile_bounds
        
        # Filter uncertainty data to tile bounds
        tile_uncertainty_data = []
        for unc in uncertainty_data:
            if (min_lon <= unc.get('lon', 0) <= max_lon and 
                min_lat <= unc.get('lat', 0) <= max_lat):
                tile_uncertainty_data.append(unc)
        
        vector_tile = {
            "type": "FeatureCollection",
            "features": []
        }
        
        for unc in tile_uncertainty_data:
            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [unc.get('lon', 0), unc.get('lat', 0)]
                },
                "properties": {
                    "grid_id": unc.get('grid_id', ''),
                    "hazard_type": unc.get('hazard_type', ''),
                    "uncertainty": unc.get('uncertainty', 0.0),
                    "confidence_interval": unc.get('confidence_interval', 0.0),
                    "model_version": unc.get('model_version', ''),
                }
            }
            vector_tile["features"].append(feature)
        
        return json.dumps(vector_tile, ensure_ascii=True).encode('utf-8')


# Global tile system instance
tile_system = TileSystem()
vector_tile_builder = VectorTileBuilder(tile_system)
