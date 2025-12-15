# Pharmacy Agent – Agent Engineer Home Assignment

A stateless, streaming AI pharmacy assistant backed by internal tools and a synthetic database.  
Supports **English and Hebrew**.

## Capabilities
- Medication information (tool-based, no hallucinations)
- Stock availability by branch
- Prescription lookup
- Refill request submission (simulated)

## Architecture
- **Frontend:** simple streaming web UI (`/web`)
- **Backend:** stateless FastAPI service
- **Agent:** intent-based routing + multi-step flows
- **Data:** SQLite DB accessed only via deterministic tools

## Tools (DB-backed)
- `get_medication_by_name`
- `check_inventory`
- `get_user_by_contact`
- `list_user_prescriptions`

(All factual answers are sourced strictly from these tools.)

## Agent Flows
**Flow 1 – Stock**
- Medication → inventory → streamed response

**Flow 2 – Prescriptions**
- User identification → prescription list → refill prompt

**Flow 3 – Refill (Simulated)**
- Validate prescription exists, is active, and has refills remaining

## Safety
- No medical advice or diagnosis
- No hallucinated medication facts
- Clear refusal for personalized medical questions

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python data/seed_db.py
uvicorn app.main:app --reload
Open: http://127.0.0.1:8000/web/