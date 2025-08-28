#!/usr/bin/env python3
"""
Build map tiles for Climate Risk Lens.
"""

import asyncio
import sys
import json
from pathlib import Path
from datetime import datetime
import random

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "backend"))

from app.db.database import AsyncSessionLocal
from app.db.models import HazardPrediction
from app.geo.tiles import vector_tile_builder, tile_system
from sqlalchemy import select


async def build_tiles():
    """Build map tiles from risk predictions."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Get recent hazard predictions
            result = await session.execute(
                select(HazardPrediction)
                .where(HazardPrediction.issued_at >= datetime.utcnow() - timedelta(hours=1))
                .limit(1000)
            )
            predictions = result.scalars().all()
            
            if not predictions:
                print("No recent predictions found, generating demo tiles...")
                await generate_demo_tiles()
                return
            
            # Group predictions by grid
            grid_predictions = {}
            for pred in predictions:
                if pred.grid_id not in grid_predictions:
                    grid_predictions[pred.grid_id] = []
                grid_predictions[pred.grid_id].append(pred)
            
            # Generate tiles for different zoom levels
            zoom_levels = [8, 10, 12, 14]
            tiles_generated = 0
            
            for zoom in zoom_levels:
                # Calculate tile bounds for this zoom level
                # For demo, we'll generate a few tiles around San Francisco
                center_tile = tile_system.deg2num(37.7749, -122.4194, zoom)
                
                # Generate tiles in a 3x3 grid around center
                for x_offset in range(-1, 2):
                    for y_offset in range(-1, 2):
                        tile_x = center_tile[0] + x_offset
                        tile_y = center_tile[1] + y_offset
                        
                        # Get tile bounds
                        tile_bounds = tile_system.num2deg(tile_x, tile_y, zoom)
                        
                        # Filter predictions for this tile
                        tile_predictions = []
                        for grid_id, preds in grid_predictions.items():
                            # Simple check if grid intersects with tile
                            # In production, use proper spatial intersection
                            if is_grid_in_tile(grid_id, tile_bounds):
                                for pred in preds:
                                    tile_predictions.append({
                                        'grid_id': pred.grid_id,
                                        'hazard_type': pred.type,
                                        'p_risk': pred.p_risk,
                                        'q10': pred.q10,
                                        'q50': pred.q50,
                                        'q90': pred.q90,
                                        'model_version': pred.model_version,
                                        'issued_at': pred.issued_at.isoformat(),
                                        'lat': 37.7749 + random.uniform(-0.1, 0.1),
                                        'lon': -122.4194 + random.uniform(-0.1, 0.1)
                                    })
                        
                        # Build vector tile
                        from app.geo.tiles import TileCoord
                        coord = TileCoord(z=zoom, x=tile_x, y=tile_y)
                        tile_data = vector_tile_builder.build_risk_tile(coord, tile_predictions)
                        
                        # Save tile (in production, save to MinIO or file system)
                        tile_path = Path(f"tiles/{zoom}/{tile_x}/{tile_y}.json")
                        tile_path.parent.mkdir(parents=True, exist_ok=True)
                        tile_path.write_text(tile_data.decode('utf-8'))
                        
                        tiles_generated += 1
            
            print(f"✓ Generated {tiles_generated} tiles from {len(predictions)} predictions")
            
        except Exception as e:
            print(f"✗ Error building tiles: {e}")
            raise


def is_grid_in_tile(grid_id: str, tile_bounds: tuple) -> bool:
    """
    Check if a grid cell intersects with a tile.
    
    Args:
        grid_id: Grid ID string
        tile_bounds: Tile bounds (min_lon, min_lat, max_lon, max_lat)
        
    Returns:
        True if grid intersects with tile
    """
    try:
        # Parse grid ID
        grid_lat, grid_lon = map(int, grid_id.split("_"))
        
        # Convert to approximate coordinates
        grid_min_lat = grid_lat
        grid_max_lat = grid_lat + 1
        grid_min_lon = grid_lon
        grid_max_lon = grid_lon + 1
        
        # Check intersection
        min_lon, min_lat, max_lon, max_lat = tile_bounds
        
        return not (grid_max_lon < min_lon or grid_min_lon > max_lon or
                   grid_max_lat < min_lat or grid_min_lat > max_lat)
    except:
        return False


async def generate_demo_tiles():
    """Generate demo tiles with mock data."""
    
    # Generate demo risk data
    demo_predictions = []
    hazards = ["flood", "heat", "smoke", "pm25"]
    
    for i in range(100):
        demo_predictions.append({
            'grid_id': f'37_-122',
            'hazard_type': random.choice(hazards),
            'p_risk': random.uniform(0.1, 0.8),
            'q10': random.uniform(0.05, 0.3),
            'q50': random.uniform(0.2, 0.6),
            'q90': random.uniform(0.4, 0.9),
            'model_version': 'demo-model-v1',
            'issued_at': datetime.utcnow().isoformat(),
            'lat': 37.7749 + random.uniform(-0.5, 0.5),
            'lon': -122.4194 + random.uniform(-0.5, 0.5)
        })
    
    # Generate tiles for zoom level 10
    zoom = 10
    center_tile = tile_system.deg2num(37.7749, -122.4194, zoom)
    
    # Generate a single tile
    from app.geo.tiles import TileCoord
    coord = TileCoord(z=zoom, x=center_tile[0], y=center_tile[1])
    tile_data = vector_tile_builder.build_risk_tile(coord, demo_predictions)
    
    # Save demo tile
    tile_path = Path("tiles/demo.json")
    tile_path.parent.mkdir(parents=True, exist_ok=True)
    tile_path.write_text(tile_data.decode('utf-8'))
    
    print(f"✓ Generated demo tile with {len(demo_predictions)} predictions")


async def main():
    """Main function."""
    print("Building map tiles for Climate Risk Lens...")
    await build_tiles()


if __name__ == "__main__":
    asyncio.run(main())
