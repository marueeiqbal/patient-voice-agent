# Voice AI Patient Registration

A caller dials a US number, talks to an AI intake coordinator ("Sam"), and is registered as a patient. Data is saved to Postgres and exposed through a REST API and a simple dashboard.

## Live demo
- Phone number: <YOUR VAPI NUMBER>
- API base URL: https://web-production-42a33.up.railway.app
- API docs: https://web-production-42a33.up.railway.app/docs
- Dashboard: https://web-production-42a33.up.railway.app/dashboard

## Architecture
Caller -> Vapi (telephony, STT, TTS, LLM) -> POST /vapi/webhook (tool calls) -> CRUD layer -> Postgres
- `app/main.py`: FastAPI app, REST routes, response envelope `{"data":..., "error":...}`
- `app/schemas.py`: Pydantic validation (server-side source of truth)
- `app/models.py`, `app/database.py`: SQLAlchemy model and connection (SQLite locally, Postgres on Railway)
- `app/crud.py`: all database access, shared by the API and the voice webhook
- `app/vapi_webhook.py`: handles the tools check_existing_patient, save_patient, update_patient
- `app/prompts.py`: the documented system prompt
- `app/dashboard.py`: read-only HTML table of patients

## Tech stack and why
- Vapi: handles phone number, STT, TTS and interruptions so time goes into prompt, tools and validation.
- FastAPI + Pydantic: fast to build, strong validation, auto-generated docs.
- Postgres on Railway: survives redeploys (SQLite on ephemeral disk would not). SQLite locally for simplicity.

## Setup
    python -m venv .venv
    .venv\Scripts\activate
    pip install -r requirements.txt
    copy .env.example .env
    uvicorn app.main:app --reload

## Environment variables
- DATABASE_URL: SQLite or Postgres URL (default sqlite:///./patients.db)
- LOG_LEVEL: logging level (default INFO)
- VAPI_WEBHOOK_SECRET: optional shared secret checked on the webhook

## API
GET /patients (filters: last_name, date_of_birth, phone_number), GET /patients/{id}, POST /patients, PUT /patients/{id} (partial), DELETE /patients/{id} (soft delete via deleted_at).

## Prompt design
See `app/prompts.py`: one question at a time, required fields first, optional fields offered as opt-in, mandatory read-back and explicit confirmation before saving, honest error handling, corrections and "start over" supported.

## Edge cases handled
- Invalid DOB, phone, state, ZIP: rejected by the API; the tool returns VALIDATION_ERROR and the agent re-asks only that field.
- Database write fails: tool returns DATABASE_ERROR and the agent tells the caller honestly.
- Call drops mid-call: nothing is saved until the caller confirms, so no partial records.
- Returning caller: lookup by phone offers an update instead of a duplicate.

## Known limitations
- Phone numbers are not unique at the database level.
- No authentication on the REST API or dashboard (assessment only, fake data).
- Webhook secret is optional.
- Single language (English).

## Next steps
Appointment scheduling, Spanish support, API tests, call transcripts linked to patient records.