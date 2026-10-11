import logging
import os

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional

from app import crud, models  # noqa: F401  (models import registers the table)
from app.database import Base, engine, get_db
from app.schemas import PatientCreate, PatientOut, PatientUpdate
from app.vapi_webhook import router as vapi_router

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("patient-api")

# Create tables on startup if they don't exist yet.
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Patient Registration API")
app.include_router(vapi_router)


# ---------- Response envelope: {"data": ..., "error": null} ----------

def ok(data, status_code: int = 200) -> JSONResponse:
    return JSONResponse(status_code=status_code, content={"data": data, "error": None})


def fail(status_code: int, message: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"data": None, "error": {"code": status_code, "message": message}},
    )


def serialize(patient) -> dict:
    return PatientOut.model_validate(patient).model_dump(mode="json")


# ---------- Error handlers (so every error uses the same envelope) ----------

@app.exception_handler(StarletteHTTPException)
async def http_error_handler(request: Request, exc: StarletteHTTPException):
    return fail(exc.status_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    messages = []
    for err in exc.errors():
        field = ".".join(str(p) for p in err["loc"] if p != "body")
        msg = err["msg"].replace("Value error, ", "")
        messages.append(f"{field}: {msg}" if field else msg)
    return fail(422, "; ".join(messages))


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error")
    return fail(500, "Internal server error")


# ---------- Routes ----------

@app.get("/")
def health():
    return ok({"status": "running"})


@app.get("/patients")
def list_patients(
    last_name: Optional[str] = None,
    date_of_birth: Optional[str] = None,
    phone_number: Optional[str] = None,
    db: Session = Depends(get_db),
):
    try:
        patients = crud.list_patients(db, last_name, date_of_birth, phone_number)
    except ValueError as e:
        # bad filter value, e.g. a 3-digit phone or a wrong date format
        raise HTTPException(status_code=400, detail=str(e))
    return ok([serialize(p) for p in patients])


@app.get("/patients/{patient_id}")
def get_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    return ok(serialize(patient))


@app.post("/patients")
def create_patient(data: PatientCreate, db: Session = Depends(get_db)):
    patient = crud.create_patient(db, data)
    payload = serialize(patient)
    logger.info("Patient created: %s", payload)
    return ok(payload, status_code=201)


@app.put("/patients/{patient_id}")
def update_patient(patient_id: str, data: PatientUpdate, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    if not data.model_dump(exclude_unset=True):
        raise HTTPException(status_code=400, detail="No fields provided to update")
    patient = crud.update_patient(db, patient, data)
    payload = serialize(patient)
    logger.info("Patient updated: %s", payload)
    return ok(payload)


@app.delete("/patients/{patient_id}")
def delete_patient(patient_id: str, db: Session = Depends(get_db)):
    patient = crud.get_patient(db, patient_id)
    if patient is None:
        raise HTTPException(status_code=404, detail="Patient not found")
    crud.soft_delete_patient(db, patient)
    logger.info("Patient soft-deleted: %s", patient_id)
    return ok({"patient_id": patient_id, "deleted": True})