#!/usr/bin/env python3
"""
Seed demo data for Climate Risk Lens.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
import random
import uuid

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "backend"))

from app.db.database import AsyncSessionLocal
from app.db.models import User, Organization, Site, HazardPrediction, Telemetry
from app.geo.grid import grid_system
from sqlalchemy import text


async def seed_demo_data():
    """Seed the database with demo data."""
    
    async with AsyncSessionLocal() as session:
        try:
            # Create demo organization
            org = Organization(
                id=uuid.uuid4(),
                name="Demo Organization",
                api_key="demo_api_key_123",
                is_active=True
            )
            session.add(org)
            await session.flush()
            
            # Create demo user
            user = User(
                id=uuid.uuid4(),
                email="demo@climaterisklens.com",
                is_active=True,
                is_verified=True,
                role="admin",
                org_id=org.id
            )
            session.add(user)
            await session.flush()
            
            # Create demo sites around San Francisco
            demo_sites = [
                {"name": "Downtown SF", "lat": 37.7749, "lon": -122.4194},
                {"name": "Golden Gate Park", "lat": 37.7694, "lon": -122.4862},
                {"name": "Mission District", "lat": 37.7599, "lon": -122.4148},
                {"name": "SOMA", "lat": 37.7749, "lon": -122.4194},
                {"name": "Marina District", "lat": 37.8024, "lon": -122.4358},
            ]
            
            sites = []
            for site_data in demo_sites:
                site = Site(
                    id=uuid.uuid4(),
                    org_id=org.id,
                    name=site_data["name"],
                    geom=f"POINT({site_data['lon']} {site_data['lat']})",
                    metadata={"demo": True, "city": "San Francisco"}
                )
                session.add(site)
                sites.append(site)
            
            await session.flush()
            
            # Create demo hazard predictions
            hazards = ["flood", "heat", "smoke", "pm25"]
            grid_ids = ["37_-122", "37_-121", "37_-123", "38_-122", "36_-122"]
            
            for grid_id in grid_ids:
                for hazard in hazards:
                    for hours_ahead in [6, 12, 24, 48, 72]:
                        prediction = HazardPrediction(
                            hazard_id=uuid.uuid4(),
                            type=hazard,
                            issued_at=datetime.utcnow(),
                            horizon_minutes=hours_ahead * 60,
                            grid_id=grid_id,
                            p_risk=random.uniform(0.1, 0.8),
                            q10=random.uniform(0.05, 0.3),
                            q50=random.uniform(0.2, 0.6),
                            q90=random.uniform(0.4, 0.9),
                            model_version="demo-model-v1",
                            data_time=datetime.utcnow() - timedelta(minutes=15)
                        )
                        session.add(prediction)
            
            # Create demo telemetry data
            sources = ["NOAA", "USGS", "EPA AirNow", "NASA FIRMS"]
            
            for source in sources:
                for i in range(10):
                    telemetry = Telemetry(
                        id=uuid.uuid4(),
                        source=source,
                        ts=datetime.utcnow() - timedelta(minutes=i*5),
                        geom=f"POINT({-122.4194 + random.uniform(-0.1, 0.1)} {37.7749 + random.uniform(-0.1, 0.1)})",
                        payload_json={
                            "temperature": random.uniform(15, 25),
                            "humidity": random.uniform(0.4, 0.8),
                            "pressure": random.uniform(1010, 1020),
                            "demo": True
                        },
                        data_latency_ms=random.randint(100, 1000)
                    )
                    session.add(telemetry)
            
            # Commit all changes
            await session.commit()
            
            print("✓ Demo data seeded successfully!")
            print(f"  - Organization: {org.name}")
            print(f"  - User: {user.email}")
            print(f"  - Sites: {len(sites)}")
            print(f"  - Hazard predictions: {len(grid_ids) * len(hazards) * 5}")
            print(f"  - Telemetry records: {len(sources) * 10}")
            
        except Exception as e:
            await session.rollback()
            print(f"✗ Error seeding demo data: {e}")
            raise


async def main():
    """Main function."""
    print("Seeding demo data for Climate Risk Lens...")
    await seed_demo_data()


if __name__ == "__main__":
    asyncio.run(main())
