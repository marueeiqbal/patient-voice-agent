import re
from datetime import date, datetime
from typing import Optional, Literal

from pydantic import BaseModel, EmailStr, field_validator, ConfigDict

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","DC",
}

NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z '\-]{0,49}$")
ZIP_PATTERN = re.compile(r"^\d{5}(-\d{4})?$")

SexType = Literal["Male", "Female", "Other", "Decline to Answer"]


# ---------- Helper validators (shared by Create and Update) ----------

def clean_phone(value: str) -> str:
    """Strip everything except digits; accept a leading US '1'."""
    digits = re.sub(r"\D", "", value)
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        raise ValueError("Phone number must be exactly 10 digits")
    return digits


def clean_name(value: str) -> str:
    value = value.strip()
    if not NAME_PATTERN.match(value):
        raise ValueError("Name must be 1-50 letters, hyphens or apostrophes")
    return value


def clean_dob(value: str) -> date:
    try:
        dob = datetime.strptime(value, "%m/%d/%Y").date()
    except ValueError:
        raise ValueError("Date of birth must be MM/DD/YYYY")
    if dob > date.today():
        raise ValueError("Date of birth cannot be in the future")
    return dob


def clean_state(value: str) -> str:
    value = value.strip().upper()
    if value not in US_STATES:
        raise ValueError("State must be a valid 2-letter US abbreviation")
    return value


def clean_zip(value: str) -> str:
    value = value.strip()
    if not ZIP_PATTERN.match(value):
        raise ValueError("ZIP code must be 5 digits or ZIP+4 format")
    return value


# ---------- Request schemas ----------

class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: str  # MM/DD/YYYY text
    sex: SexType
    phone_number: str
    email: Optional[EmailStr] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: str = "English"
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def v_name(cls, v):
        return clean_name(v)

    @field_validator("date_of_birth")
    @classmethod
    def v_dob(cls, v):
        return clean_dob(v).strftime("%m/%d/%Y")

    @field_validator("phone_number")
    @classmethod
    def v_phone(cls, v):
        return clean_phone(v)

    @field_validator("emergency_contact_phone")
    @classmethod
    def v_ec_phone(cls, v):
        return clean_phone(v) if v else v

    @field_validator("state")
    @classmethod
    def v_state(cls, v):
        return clean_state(v)

    @field_validator("zip_code")
    @classmethod
    def v_zip(cls, v):
        return clean_zip(v)


class PatientUpdate(BaseModel):
    """All fields optional so partial updates work."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    sex: Optional[SexType] = None
    phone_number: Optional[str] = None
    email: Optional[EmailStr] = None
    address_line_1: Optional[str] = None
    address_line_2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: Optional[str] = None
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def v_name(cls, v):
        return clean_name(v) if v is not None else v

    @field_validator("date_of_birth")
    @classmethod
    def v_dob(cls, v):
        return clean_dob(v).strftime("%m/%d/%Y") if v is not None else v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def v_phone(cls, v):
        return clean_phone(v) if v else v

    @field_validator("state")
    @classmethod
    def v_state(cls, v):
        return clean_state(v) if v is not None else v

    @field_validator("zip_code")
    @classmethod
    def v_zip(cls, v):
        return clean_zip(v) if v is not None else v


# ---------- Response schema ----------

class PatientOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    sex: str
    phone_number: str
    email: Optional[str] = None
    address_line_1: str
    address_line_2: Optional[str] = None
    city: str
    state: str
    zip_code: str
    insurance_provider: Optional[str] = None
    insurance_member_id: Optional[str] = None
    preferred_language: str
    emergency_contact_name: Optional[str] = None
    emergency_contact_phone: Optional[str] = None
    created_at: datetime
    updated_at: datetime