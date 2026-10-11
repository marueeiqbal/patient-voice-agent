"""Vapi webhook: receives tool calls from the voice assistant and runs them
against the same CRUD layer the REST API uses."""
import json
import logging
import os

from fastapi import APIRouter, Depends, Request
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud
from app.database import get_db
from app.schemas import PatientCreate, PatientUpdate

router = APIRouter()
logger = logging.getLogger("vapi-webhook")


def _args(raw) -> dict:
    """Vapi sends arguments as a dict or as a JSON string."""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return {}
    return raw or {}


def _clean(args: dict) -> dict:
    """Drop empty values so optional fields the caller skipped are ignored."""
    return {k: v for k, v in args.items() if v not in (None, "", "null")}


def _validation_text(e: ValidationError) -> str:
    parts = []
    for err in e.errors():
        field = ".".join(str(p) for p in err["loc"])
        msg = err["msg"].replace("Value error, ", "")
        parts.append(f"{field}: {msg}")
    return "; ".join(parts)


# ---------- Tools (each returns a plain string the LLM reads) ----------

def check_existing_patient(db: Session, args: dict) -> str:
    try:
        patient = crud.find_by_phone(db, args.get("phone_number", ""))
    except ValueError as e:
        return f"VALIDATION_ERROR: phone_number: {e}. Ask the caller to repeat the phone number."
    if patient is None:
        return "NO_EXISTING_PATIENT"
    return (
        f"EXISTING_PATIENT patient_id={patient.patient_id} "
        f"first_name={patient.first_name} last_name={patient.last_name}"
    )


def save_patient(db: Session, args: dict) -> str:
    try:
        data = PatientCreate(**_clean(args))
    except ValidationError as e:
        return f"VALIDATION_ERROR: {_validation_text(e)}. Ask the caller to correct only those fields."
    try:
        patient = crud.create_patient(db, data)
    except Exception:
        logger.exception("Database write failed")
        return "DATABASE_ERROR: the record could not be saved."
    logger.info("FINAL PAYLOAD SAVED: %s", data.model_dump())
    return f"SAVED patient_id={patient.patient_id} first_name={patient.first_name}"


def update_patient(db: Session, args: dict) -> str:
    args = _clean(args)
    patient_id = args.pop("patient_id", None)
    patient = crud.get_patient(db, patient_id) if patient_id else None
    if patient is None:
        return "NOT_FOUND: no patient with that id."
    try:
        data = PatientUpdate(**args)
    except ValidationError as e:
        return f"VALIDATION_ERROR: {_validation_text(e)}. Ask the caller to correct only those fields."
    try:
        crud.update_patient(db, patient, data)
    except Exception:
        logger.exception("Database update failed")
        return "DATABASE_ERROR: the record could not be updated."
    logger.info("FINAL PAYLOAD UPDATED: %s %s", patient_id, args)
    return f"UPDATED patient_id={patient_id} first_name={patient.first_name}"


TOOLS = {
    "check_existing_patient": check_existing_patient,
    "save_patient": save_patient,
    "update_patient": update_patient,
}


# ---------- Webhook endpoint ----------

@router.post("/vapi/webhook")
async def vapi_webhook(request: Request, db: Session = Depends(get_db)):
    secret = os.getenv("VAPI_WEBHOOK_SECRET")
    if secret and request.headers.get("x-vapi-secret") != secret:
        return {"error": "unauthorized"}

    body = await request.json()
    message = body.get("message", {})
    msg_type = message.get("type")

    # Log a summary/transcript when the call ends (observability).
    if msg_type == "end-of-call-report":
        logger.info("CALL ENDED. summary=%s", message.get("summary"))
        logger.info("TRANSCRIPT: %s", message.get("transcript"))
        return {}

    if msg_type != "tool-calls":
        return {}

    results = []
    for call in message.get("toolCallList") or message.get("toolCalls") or []:
        function = call.get("function", {})
        name = function.get("name")
        handler = TOOLS.get(name)
        if handler is None:
            result = f"ERROR: unknown tool {name}"
        else:
            try:
                result = handler(db, _args(function.get("arguments")))
            except Exception:
                logger.exception("Tool %s crashed", name)
                result = "DATABASE_ERROR: unexpected failure."
        logger.info("Tool %s -> %s", name, result)
        results.append({"toolCallId": call.get("id"), "result": result})

    return {"results": results}