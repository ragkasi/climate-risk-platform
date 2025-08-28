"""
Geospatial grid utilities for 1km grid system.
"""

import math
from typing import Tuple, List, Optional
from shapely.geometry import Point, Polygon
from shapely.ops import transform
import pyproj
from functools import partial


class GridSystem:
    """1km grid system in EPSG 4326."""
    
    def __init__(self, grid_size_km: float = 1.0, epsg: int = 4326):
        self.grid_size_km = grid_size_km
        self.epsg = epsg
        
        # Convert grid size to degrees (approximate)
        # 1 degree latitude ≈ 111 km
        # 1 degree longitude varies by latitude, use average
        self.grid_size_deg_lat = grid_size_km / 111.0
        self.grid_size_deg_lon = grid_size_km / 111.0  # Simplified for demo
    
    def point_to_grid_id(self, lat: float, lon: float) -> str:
        """
        Convert lat/lon point to grid ID.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            
        Returns:
            Grid ID string
        """
        # Calculate grid indices
        grid_lat = math.floor(lat / self.grid_size_deg_lat)
        grid_lon = math.floor(lon / self.grid_size_deg_lon)
        
        return f"{grid_lat}_{grid_lon}"
    
    def grid_id_to_bounds(self, grid_id: str) -> Tuple[float, float, float, float]:
        """
        Convert grid ID to bounding box (min_lon, min_lat, max_lon, max_lat).
        
        Args:
            grid_id: Grid ID string
            
        Returns:
            Bounding box tuple
        """
        try:
            grid_lat, grid_lon = map(int, grid_id.split("_"))
        except ValueError:
            raise ValueError(f"Invalid grid ID format: {grid_id}")
        
        min_lat = grid_lat * self.grid_size_deg_lat
        min_lon = grid_lon * self.grid_size_deg_lon
        max_lat = min_lat + self.grid_size_deg_lat
        max_lon = min_lon + self.grid_size_deg_lon
        
        return (min_lon, min_lat, max_lon, max_lat)
    
    def grid_id_to_polygon(self, grid_id: str) -> Polygon:
        """
        Convert grid ID to Shapely polygon.
        
        Args:
            grid_id: Grid ID string
            
        Returns:
            Shapely polygon
        """
        min_lon, min_lat, max_lon, max_lat = self.grid_id_to_bounds(grid_id)
        
        return Polygon([
            (min_lon, min_lat),
            (max_lon, min_lat),
            (max_lon, max_lat),
            (min_lon, max_lat),
            (min_lon, min_lat)
        ])
    
    def get_neighboring_grids(self, grid_id: str, radius: int = 1) -> List[str]:
        """
        Get neighboring grid IDs within radius.
        
        Args:
            grid_id: Center grid ID
            radius: Number of grid cells in each direction
            
        Returns:
            List of neighboring grid IDs
        """
        try:
            center_lat, center_lon = map(int, grid_id.split("_"))
        except ValueError:
            raise ValueError(f"Invalid grid ID format: {grid_id}")
        
        neighbors = []
        for lat_offset in range(-radius, radius + 1):
            for lon_offset in range(-radius, radius + 1):
                if lat_offset == 0 and lon_offset == 0:
                    continue
                
                neighbor_lat = center_lat + lat_offset
                neighbor_lon = center_lon + lon_offset
                neighbors.append(f"{neighbor_lat}_{neighbor_lon}")
        
        return neighbors
    
    def point_in_grid(self, lat: float, lon: float, grid_id: str) -> bool:
        """
        Check if point is within grid cell.
        
        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            grid_id: Grid ID to check
            
        Returns:
            True if point is in grid
        """
        polygon = self.grid_id_to_polygon(grid_id)
        point = Point(lon, lat)
        return polygon.contains(point)
    
    def get_grids_for_bounds(self, min_lon: float, min_lat: float, 
                           max_lon: float, max_lat: float) -> List[str]:
        """
        Get all grid IDs that intersect with bounding box.
        
        Args:
            min_lon: Minimum longitude
            min_lat: Minimum latitude
            max_lon: Maximum longitude
            max_lat: Maximum latitude
            
        Returns:
            List of intersecting grid IDs
        """
        grids = []
        
        # Calculate grid indices for bounds
        min_grid_lat = math.floor(min_lat / self.grid_size_deg_lat)
        max_grid_lat = math.ceil(max_lat / self.grid_size_deg_lat)
        min_grid_lon = math.floor(min_lon / self.grid_size_deg_lon)
        max_grid_lon = math.ceil(max_lon / self.grid_size_deg_lon)
        
        for grid_lat in range(min_grid_lat, max_grid_lat + 1):
            for grid_lon in range(min_grid_lon, max_grid_lon + 1):
                grids.append(f"{grid_lat}_{grid_lon}")
        
        return grids
    
    def distance_between_grids(self, grid_id1: str, grid_id2: str) -> float:
        """
        Calculate distance between two grid centers in km.
        
        Args:
            grid_id1: First grid ID
            grid_id2: Second grid ID
            
        Returns:
            Distance in kilometers
        """
        try:
            lat1, lon1 = map(int, grid_id1.split("_"))
            lat2, lon2 = map(int, grid_id2.split("_"))
        except ValueError:
            raise ValueError(f"Invalid grid ID format: {grid_id1} or {grid_id2}")
        
        # Convert to center coordinates
        center_lat1 = (lat1 + 0.5) * self.grid_size_deg_lat
        center_lon1 = (lon1 + 0.5) * self.grid_size_deg_lon
        center_lat2 = (lat2 + 0.5) * self.grid_size_deg_lat
        center_lon2 = (lon2 + 0.5) * self.grid_size_deg_lon
        
        # Haversine formula for distance
        R = 6371  # Earth's radius in km
        
        dlat = math.radians(center_lat2 - center_lat1)
        dlon = math.radians(center_lon2 - center_lon1)
        
        a = (math.sin(dlat/2) * math.sin(dlat/2) + 
             math.cos(math.radians(center_lat1)) * math.cos(math.radians(center_lat2)) * 
             math.sin(dlon/2) * math.sin(dlon/2))
        
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        distance = R * c
        
        return distance


# Global grid system instance
grid_system = GridSystem()
