-- Initialize Climate Risk Lens database

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Create MLflow database
CREATE DATABASE mlflow;
GRANT ALL PRIVILEGES ON DATABASE mlflow TO postgres;

-- Create tables for Climate Risk Lens
-- (These will be created by SQLAlchemy migrations in production)

-- Create a simple grid for demo purposes
CREATE TABLE IF NOT EXISTS demo_grid (
    grid_id VARCHAR(50) PRIMARY KEY,
    geom GEOMETRY(POLYGON, 4326),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert some demo grid cells around San Francisco
INSERT INTO demo_grid (grid_id, geom) VALUES
('37_-122', ST_MakeEnvelope(-122.5, 37.5, -122.4, 37.6, 4326)),
('37_-121', ST_MakeEnvelope(-122.4, 37.5, -122.3, 37.6, 4326)),
('37_-123', ST_MakeEnvelope(-122.6, 37.5, -122.5, 37.6, 4326)),
('38_-122', ST_MakeEnvelope(-122.5, 37.6, -122.4, 37.7, 4326)),
('36_-122', ST_MakeEnvelope(-122.5, 37.4, -122.4, 37.5, 4326))
ON CONFLICT (grid_id) DO NOTHING;

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_demo_grid_geom ON demo_grid USING GIST (geom);

-- Create a function to get grid ID from lat/lon
CREATE OR REPLACE FUNCTION get_grid_id(lat FLOAT, lon FLOAT)
RETURNS VARCHAR(50) AS $$
DECLARE
    grid_lat INTEGER;
    grid_lon INTEGER;
BEGIN
    grid_lat := FLOOR(lat);
    grid_lon := FLOOR(lon);
    RETURN grid_lat || '_' || grid_lon;
END;
$$ LANGUAGE plpgsql;
