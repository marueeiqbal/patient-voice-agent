from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Patient
from app.schemas import PatientCreate, PatientUpdate, clean_phone


def _to_date(value: str):
    """Convert 'MM/DD/YYYY' text into a date object."""
    return datetime.strptime(value, "%m/%d/%Y").date()


def list_patients(
    db: Session,
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
):
    """List patients that are not soft-deleted, with optional filters."""
    query = select(Patient).where(Patient.deleted_at.is_(None))
    if last_name:
        query = query.where(func.lower(Patient.last_name) == last_name.strip().lower())
    if date_of_birth:
        query = query.where(Patient.date_of_birth == _to_date(date_of_birth))
    if phone_number:
        query = query.where(Patient.phone_number == clean_phone(phone_number))
    query = query.order_by(Patient.created_at.desc())
    return list(db.scalars(query).all())


def get_patient(db: Session, patient_id: str) -> Optional[Patient]:
    query = select(Patient).where(
        Patient.patient_id == patient_id, Patient.deleted_at.is_(None)
    )
    return db.scalar(query)


def find_by_phone(db: Session, phone_number: str) -> Optional[Patient]:
    """Used for duplicate detection: find an existing patient by phone."""
    digits = clean_phone(phone_number)
    query = select(Patient).where(
        Patient.phone_number == digits, Patient.deleted_at.is_(None)
    )
    return db.scalars(query).first()


def create_patient(db: Session, data: PatientCreate) -> Patient:
    values = data.model_dump()
    values["date_of_birth"] = _to_date(values["date_of_birth"])
    patient = Patient(**values)
    try:
        db.add(patient)
        db.commit()
        db.refresh(patient)
    except Exception:
        db.rollback()
        raise
    return patient


def update_patient(db: Session, patient: Patient, data: PatientUpdate) -> Patient:
    """Partial update: only fields that were sent (and are not null) change."""
    values = {k: v for k, v in data.model_dump(exclude_unset=True).items() if v is not None}
    if "date_of_birth" in values:
        values["date_of_birth"] = _to_date(values["date_of_birth"])
    for field, value in values.items():
        setattr(patient, field, value)
    try:
        db.commit()
        db.refresh(patient)
    except Exception:
        db.rollback()
        raise
    return patient


def soft_delete_patient(db: Session, patient: Patient) -> Patient:
    """Set deleted_at instead of removing the row."""
    patient.deleted_at = datetime.now(timezone.utc)
    try:
        db.commit()
        db.refresh(patient)
    except Exception:
        db.rollback()
        raise
    return patient