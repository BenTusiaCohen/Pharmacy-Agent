# Pharmacy Agent – Agent Engineer Home Assignment

A stateless, streaming AI pharmacy assistant that uses internal tools and a synthetic database to answer pharmacy-related questions in **English and Hebrew**.

### Supported capabilities
- Medication information (tool-based, no hallucinations)
- Stock availability by branch
- Prescription lookup
- Refill request submission (simulated)

---

## High-Level Architecture

### Frontend
- Simple web UI (`/web`)
- Stateless interaction (conversation sent on each request)
- Streaming responses

### Backend
- FastAPI (`app/main.py`)
- Stateless design
- Streaming OpenAI responses
- SQLite-backed deterministic tools

### Agent Design
- Intent-based routing
- Multi-step workflows
- Tool-first factual grounding
- No medical advice or diagnosis

---

## Tools

### `get_medication_by_name`
Lookup a medication by English or Hebrew name.

**Input**
```json
{ "name": "Ibuprofen" }
Output

json
Copy code
{
  "id": 2,
  "name_en": "Ibuprofen",
  "name_he": "נורופן",
  "active_ingredients": "Ibuprofen 200mg",
  "dosage_en": "Take 1 tablet every 6–8 hours with food.",
  "dosage_he": "טבליה אחת כל 6–8 שעות עם אוכל.",
  "prescription_required": false,
  "warnings_en": "Avoid if you have stomach ulcers.",
  "warnings_he": "אין להשתמש במקרה של כיב קיבה."
}
check_inventory
Check stock availability across branches.

Input

json
Copy code
{ "medication_id": 2 }
Output

json
Copy code
[
  {
    "branch_name": "Downtown Pharmacy",
    "city": "Tel Aviv",
    "hours": "08:00–22:00",
    "quantity": 80
  }
]
get_user_by_contact
Find a user by phone number or email.

Input

json
Copy code
{ "contact": "0501234567" }
Output

json
Copy code
{
  "id": 1,
  "full_name": "Ben Cohen"
}
list_user_prescriptions
List prescriptions for a user.

Input

json
Copy code
{ "user_id": 1 }
Output

json
Copy code
[
  {
    "medication_id": 3,
    "status": "active",
    "refills_left": 2
  }
]
Database
SQLite database (data/pharmacy.db)

Generated via data/seed_db.py

Synthetic data includes:

10 users

5 medications

Multiple pharmacy branches

Active and expired prescriptions

Database file is not committed

Multi-Step Agent Flows
Flow 1 – Stock Availability
Trigger: medication availability question
Steps:

Extract medication → get_medication_by_name

Fetch inventory → check_inventory

Stream response

Examples:

Do you have Ibuprofen in stock?

יש נורופן במלאי?

Flow 2 – Prescription Lookup
Trigger: prescription check
Steps:

Identify user → get_user_by_contact

Fetch prescriptions → list_user_prescriptions

Stream results

Flow 3 – Refill Request (Simulated)
Trigger: refill request
Steps:

Identify user

Validate prescription

Confirm refill (simulation)

Safety
No medical advice

No hallucinated facts

Tool-based grounding only

Setup
bash
Copy code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python data/seed_db.py
uvicorn app.main:app --reload
Open: http://127.0.0.1:8000/web/

Security
.env excluded via .gitignore

No secrets committed
