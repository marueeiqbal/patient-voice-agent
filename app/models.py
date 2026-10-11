import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import String, Date, DateTime, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def utc_now():
    return datetime.now(timezone.utc)


class Patient(Base):
    __tablename__ = "patients"

    patient_id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    date_of_birth: Mapped[date] = mapped_column(Date)
    sex: Mapped[str] = mapped_column(String(20))
    phone_number: Mapped[str] = mapped_column(String(10), index=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    address_line_1: Mapped[str] = mapped_column(String(255))
    address_line_2: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(2))
    zip_code: Mapped[str] = mapped_column(String(10))
    insurance_provider: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    insurance_member_id: Mapped[Optional[str]] = mapped_column(String(50), default=None)
    preferred_language: Mapped[str] = mapped_column(String(50), default="English")
    emergency_contact_name: Mapped[Optional[str]] = mapped_column(String(100), default=None)
    emergency_contact_phone: Mapped[Optional[str]] = mapped_column(String(10), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), default=utc_now, onupdate=utc_now
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime(timezone=True), default=None
    )
    __table_args__ = (
    CheckConstraint(
    "sex IN ('Male', 'Female', 'Other', 'Decline to Answer')",
    name="ck_patients_sex",
        ),
    )