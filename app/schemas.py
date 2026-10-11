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