"""
Database models for Climate Risk Lens.
"""

import uuid
from datetime import datetime
from typing import Optional, List
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Text, JSON, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

Base = declarative_base()


class User(Base):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OTP-only auth
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    role = Column(String(50), default="anon")  # anon, org_user, analyst, admin
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    feedback = relationship("Feedback", back_populates="user")


class Organization(Base):
    """Organization model for multi-tenancy."""
    
    __tablename__ = "organizations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    api_key = Column(String(255), unique=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    sites = relationship("Site", back_populates="organization")
    alerts = relationship("Alert", back_populates="organization")


class Site(Base):
    """Site model for asset management."""
    
    __tablename__ = "sites"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    name = Column(String(255), nullable=False)
    geom = Column(Geometry("POINT", srid=4326), nullable=False)
    metadata = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="sites")
    alerts = relationship("Alert", back_populates="site")
    
    # Indexes
    __table_args__ = (
        Index("idx_sites_geom", "geom", postgresql_using="gist"),
        Index("idx_sites_org_id", "org_id"),
    )


class HazardPrediction(Base):
    """Hazard prediction model for risk forecasts."""
    
    __tablename__ = "hazards"
    
    hazard_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(String(50), nullable=False)  # flood, heat, smoke, pm25
    issued_at = Column(DateTime, nullable=False, index=True)
    horizon_minutes = Column(Integer, nullable=False)  # Prediction horizon in minutes
    grid_id = Column(String(50), nullable=False, index=True)
    p_risk = Column(Float, nullable=False)  # Risk probability
    q10 = Column(Float, nullable=True)  # 10th percentile
    q50 = Column(Float, nullable=True)  # 50th percentile (median)
    q90 = Column(Float, nullable=True)  # 90th percentile
    model_version = Column(String(100), nullable=False)
    data_time = Column(DateTime, nullable=False)  # Time of input data
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_hazards_type_issued", "type", "issued_at"),
        Index("idx_hazards_grid_id", "grid_id"),
        Index("idx_hazards_type_grid_issued", "type", "grid_id", "issued_at"),
    )


class Alert(Base):
    """Alert model for notifications."""
    
    __tablename__ = "alerts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    site_id = Column(UUID(as_uuid=True), ForeignKey("sites.id"), nullable=True)
    hazard_type = Column(String(50), nullable=False)
    status = Column(String(50), default="pending")  # pending, sent, failed
    p_risk = Column(Float, nullable=False)
    threshold = Column(Float, nullable=False)
    sent_at = Column(DateTime, nullable=True)
    channel = Column(String(50), nullable=False)  # email, webhook
    webhook_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="alerts")
    site = relationship("Site", back_populates="alerts")
    
    # Indexes
    __table_args__ = (
        Index("idx_alerts_org_id", "org_id"),
        Index("idx_alerts_site_id", "site_id"),
        Index("idx_alerts_status", "status"),
    )


class Telemetry(Base):
    """Telemetry model for data ingestion tracking."""
    
    __tablename__ = "telemetry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source = Column(String(100), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    geom = Column(Geometry("POINT", srid=4326), nullable=True)
    payload_json = Column(JSON, nullable=True)
    data_latency_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_telemetry_source_ts", "source", "ts"),
        Index("idx_telemetry_geom", "geom", postgresql_using="gist"),
    )


class Experiment(Base):
    """A/B testing experiment model."""
    
    __tablename__ = "experiments"
    
    exp_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    variant = Column(String(50), nullable=False)  # A, B, control
    start_at = Column(DateTime, nullable=False)
    stop_at = Column(DateTime, nullable=True)
    config_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_experiments_name", "name"),
        Index("idx_experiments_variant", "variant"),
        Index("idx_experiments_active", "is_active"),
    )


class Feedback(Base):
    """User feedback model for model improvement."""
    
    __tablename__ = "feedback"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    hazard_id = Column(UUID(as_uuid=True), ForeignKey("hazards.hazard_id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    label = Column(String(10), nullable=False)  # TP, FP, FN, TN
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    hazard = relationship("HazardPrediction")
    user = relationship("User", back_populates="feedback")
    
    # Indexes
    __table_args__ = (
        Index("idx_feedback_hazard_id", "hazard_id"),
        Index("idx_feedback_user_id", "user_id"),
        Index("idx_feedback_label", "label"),
    )


class ModelRegistry(Base):
    """Model registry for MLflow integration."""
    
    __tablename__ = "model_registry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    model_name = Column(String(255), nullable=False, index=True)
    model_version = Column(String(100), nullable=False)
    mlflow_run_id = Column(String(100), nullable=False)
    mlflow_model_uri = Column(String(500), nullable=False)
    stage = Column(String(50), default="None")  # None, Staging, Production
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes
    __table_args__ = (
        Index("idx_model_registry_name_version", "model_name", "model_version"),
        Index("idx_model_registry_stage", "stage"),
    )
