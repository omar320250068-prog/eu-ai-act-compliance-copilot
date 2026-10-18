"""
models.py
SQLAlchemy ORM models — mirror of PostgreSQL schema.
Shared contract between Omar Hendawy (DB) and Ahmed El-Desouky (Backend).
"""
import uuid
import enum
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Enum, Numeric, Boolean,
    DateTime, Date, ForeignKey, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import DeclarativeBase, relationship

class Base(DeclarativeBase):
    pass

class RiskTier(str, enum.Enum):
    UNACCEPTABLE = "UNACCEPTABLE"
    HIGH = "HIGH"
    LIMITED = "LIMITED"
    MINIMAL = "MINIMAL"

class Project(Base):
    __tablename__ = "projects"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    submitter_email = Column(String(320), nullable=False)
    deployment_context = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    assessments = relationship("Assessment", back_populates="project", cascade="all, delete-orphan")

class Assessment(Base):
    __tablename__ = "assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    risk_tier = Column(Enum(RiskTier), nullable=False)
    confidence_score = Column(Numeric(5, 4))
    reasoning = Column(Text)
    raw_model_output = Column(JSONB)
    assessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    model_version = Column(String(100))

    project = relationship("Project", back_populates="assessments")

class ComplianceRule(Base):
    __tablename__ = "compliance_rules"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    rule_code = Column(String(20), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    risk_tier = Column(Enum(RiskTier), nullable=False)
    source_ref = Column(String(200))
    annex_ref = Column(String(100), nullable=True)
    rule_tree = Column(JSONB, nullable=False)
    blocks_deployment = Column(Boolean, default=False)
    requires_documentation = Column(Boolean, default=False)
    remediation_text = Column(Text, nullable=True)
    effective_date = Column(Date)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
