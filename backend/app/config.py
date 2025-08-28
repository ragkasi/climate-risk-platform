"""
Application configuration using Pydantic settings.
"""

from typing import List, Optional
from pydantic import Field, validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = Field(..., env="DATABASE_URL")
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="climate_risk", env="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", env="POSTGRES_PASSWORD")
    
    # Redis
    redis_url: str = Field(..., env="REDIS_URL")
    celery_broker_url: str = Field(..., env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(..., env="CELERY_RESULT_BACKEND")
    
    # MinIO
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    minio_bucket: str = Field(default="climate-risk", env="MINIO_BUCKET")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")
    
    # MLflow
    mlflow_tracking_uri: str = Field(default="http://localhost:5000", env="MLFLOW_TRACKING_URI")
    mlflow_artifact_root: str = Field(default="s3://mlflow/", env="MLFLOW_ARTIFACT_ROOT")
    
    # API Keys
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    airnow_api_key: Optional[str] = Field(default=None, env="AIRNOW_API_KEY")
    purpleair_api_key: Optional[str] = Field(default=None, env="PURPLEAIR_API_KEY")
    noaa_token: Optional[str] = Field(default=None, env="NOAA_TOKEN")
    
    # Map
    maptiles_url: str = Field(default="http://localhost:8080/tiles", env="MAPTILES_URL")
    
    # Security
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # CORS
    cors_origins: List[str] = Field(default=["http://localhost:3000"], env="CORS_ORIGINS")
    
    # Application
    debug: bool = Field(default=False, env="DEBUG")
    demo_mode: bool = Field(default=True, env="DEMO_MODE")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    # Feature Flags
    enable_a_b_testing: bool = Field(default=True, env="ENABLE_A_B_TESTING")
    enable_feedback: bool = Field(default=True, env="ENABLE_FEEDBACK")
    enable_advanced_analytics: bool = Field(default=True, env="ENABLE_ADVANCED_ANALYTICS")
    
    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=60, env="RATE_LIMIT_REQUESTS_PER_MINUTE")
    rate_limit_burst: int = Field(default=10, env="RATE_LIMIT_BURST")
    
    # Monitoring
    prometheus_port: int = Field(default=9090, env="PROMETHEUS_PORT")
    grafana_port: int = Field(default=3001, env="GRAFANA_PORT")
    otel_exporter_otlp_endpoint: str = Field(default="http://localhost:4317", env="OTEL_EXPORTER_OTLP_ENDPOINT")
    
    # Email
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_user: Optional[str] = Field(default=None, env="SMTP_USER")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from: str = Field(default="alerts@climaterisklens.com", env="SMTP_FROM")
    
    # Webhooks
    webhook_timeout_seconds: int = Field(default=30, env="WEBHOOK_TIMEOUT_SECONDS")
    webhook_retry_attempts: int = Field(default=3, env="WEBHOOK_RETRY_ATTEMPTS")
    
    # Model Configuration
    model_cache_ttl_seconds: int = Field(default=3600, env="MODEL_CACHE_TTL_SECONDS")
    prediction_cache_ttl_seconds: int = Field(default=900, env="PREDICTION_CACHE_TTL_SECONDS")
    tile_cache_ttl_seconds: int = Field(default=1800, env="TILE_CACHE_TTL_SECONDS")
    
    # Grid Configuration
    grid_size_km: float = Field(default=1.0, env="GRID_SIZE_KM")
    grid_epsg: int = Field(default=4326, env="GRID_EPSG")
    prediction_horizon_hours: int = Field(default=72, env="PREDICTION_HORIZON_HOURS")
    
    # Alert Thresholds
    flood_risk_threshold: float = Field(default=0.3, env="FLOOD_RISK_THRESHOLD")
    heat_risk_threshold: float = Field(default=0.4, env="HEAT_RISK_THRESHOLD")
    smoke_risk_threshold: float = Field(default=0.5, env="SMOKE_RISK_THRESHOLD")
    pm25_risk_threshold: float = Field(default=0.6, env="PM25_RISK_THRESHOLD")
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [v]
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
