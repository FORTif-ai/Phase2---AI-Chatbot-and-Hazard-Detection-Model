"""
CRUD operations for Fortif.ai Memory Dashboard database.
Provides functions for creating, reading, updating, and deleting records.
"""

from typing import Optional, List
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from .models import User, Patient, PatientAssignment, UserRole

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password for storage."""
    return pwd_context.hash(password)


# === User CRUD ===

def get_user(db: Session, user_id: int) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get a user by email address."""
    return db.query(User).filter(User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
    """Get a list of users with pagination."""
    return db.query(User).offset(skip).limit(limit).all()


def create_user(
    db: Session,
    email: str,
    password: str,
    full_name: str,
    role: UserRole = UserRole.CAREGIVER
) -> User:
    """Create a new user with hashed password."""
    hashed_password = get_password_hash(password)
    user = User(
        email=email,
        hashed_password=hashed_password,
        full_name=full_name,
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    if not user.is_active:
        return None
    return user


def update_user(
    db: Session,
    user_id: int,
    full_name: Optional[str] = None,
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None
) -> Optional[User]:
    """Update user fields."""
    user = get_user(db, user_id)
    if not user:
        return None

    if full_name is not None:
        user.full_name = full_name
    if role is not None:
        user.role = role
    if is_active is not None:
        user.is_active = is_active

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """Delete a user by ID."""
    user = get_user(db, user_id)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


# === Patient CRUD ===

def get_patient(db: Session, patient_id: int) -> Optional[Patient]:
    """Get a patient by internal ID."""
    return db.query(Patient).filter(Patient.id == patient_id).first()


def get_patient_by_external_id(db: Session, patient_id: str) -> Optional[Patient]:
    """Get a patient by external patient_id (used in Weaviate)."""
    return db.query(Patient).filter(Patient.patient_id == patient_id).first()


def get_patients(db: Session, skip: int = 0, limit: int = 100) -> List[Patient]:
    """Get a list of patients with pagination."""
    return db.query(Patient).offset(skip).limit(limit).all()


def create_patient(
    db: Session,
    patient_id: str,
    display_name: str,
    notes: Optional[str] = None
) -> Patient:
    """Create a new patient record."""
    patient = Patient(
        patient_id=patient_id,
        display_name=display_name,
        notes=notes
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def get_or_create_patient(
    db: Session,
    patient_id: str,
    display_name: Optional[str] = None
) -> Patient:
    """Get existing patient or create new one."""
    patient = get_patient_by_external_id(db, patient_id)
    if patient:
        return patient
    return create_patient(
        db,
        patient_id=patient_id,
        display_name=display_name or f"Patient {patient_id}"
    )


# === Patient Assignment CRUD ===

def get_user_patients(db: Session, user_id: int) -> List[Patient]:
    """Get all patients assigned to a user."""
    assignments = db.query(PatientAssignment).filter(
        PatientAssignment.user_id == user_id
    ).all()
    return [a.patient for a in assignments]


def get_patient_users(db: Session, patient_id: int) -> List[User]:
    """Get all users assigned to a patient."""
    assignments = db.query(PatientAssignment).filter(
        PatientAssignment.patient_id == patient_id
    ).all()
    return [a.user for a in assignments]


def assign_patient_to_user(
    db: Session,
    user_id: int,
    patient_id: int,
    can_edit: bool = False
) -> PatientAssignment:
    """Assign a patient to a user."""
    # Check if assignment already exists
    existing = db.query(PatientAssignment).filter(
        PatientAssignment.user_id == user_id,
        PatientAssignment.patient_id == patient_id
    ).first()

    if existing:
        existing.can_edit = can_edit
        db.commit()
        db.refresh(existing)
        return existing

    assignment = PatientAssignment(
        user_id=user_id,
        patient_id=patient_id,
        can_edit=can_edit
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def check_user_patient_access(
    db: Session,
    user_id: int,
    patient_external_id: str
) -> Optional[PatientAssignment]:
    """Check if user has access to a patient by external ID."""
    patient = get_patient_by_external_id(db, patient_external_id)
    if not patient:
        return None

    return db.query(PatientAssignment).filter(
        PatientAssignment.user_id == user_id,
        PatientAssignment.patient_id == patient.id
    ).first()


def remove_patient_assignment(
    db: Session,
    user_id: int,
    patient_id: int
) -> bool:
    """Remove a patient assignment from a user."""
    assignment = db.query(PatientAssignment).filter(
        PatientAssignment.user_id == user_id,
        PatientAssignment.patient_id == patient_id
    ).first()

    if not assignment:
        return False

    db.delete(assignment)
    db.commit()
    return True
