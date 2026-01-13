"""
SQLAlchemy ORM models for Fortif.ai Memory Dashboard.
Defines User, Patient, and PatientAssignment models.
"""

import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime,
    ForeignKey, Enum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from .connection import Base


class UserRole(enum.Enum):
    """User role enumeration for access control."""
    CAREGIVER = "caregiver"
    FAMILY = "family"
    ADMIN = "admin"


class User(Base):
    """User accounts for dashboard access."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.CAREGIVER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    patient_assignments = relationship(
        "PatientAssignment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role={self.role.value})>"


class Patient(Base):
    """
    Patient records for the dashboard.
    The patient_id field matches the patient_id used in Weaviate memories.
    """
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    date_of_birth = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    assignments = relationship(
        "PatientAssignment",
        back_populates="patient",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Patient(id={self.id}, patient_id='{self.patient_id}', name='{self.display_name}')>"


class PatientAssignment(Base):
    """
    Links users to patients they can access.
    Implements many-to-many relationship with additional permissions.
    """
    __tablename__ = "patient_assignments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    can_edit = Column(Boolean, default=False)  # Caregivers can edit, family read-only
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Unique constraint to prevent duplicate assignments
    __table_args__ = (
        UniqueConstraint('user_id', 'patient_id', name='unique_user_patient'),
    )

    # Relationships
    user = relationship("User", back_populates="patient_assignments")
    patient = relationship("Patient", back_populates="assignments")

    def __repr__(self):
        return f"<PatientAssignment(user_id={self.user_id}, patient_id={self.patient_id}, can_edit={self.can_edit})>"
