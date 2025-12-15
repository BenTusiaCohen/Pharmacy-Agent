# Pharmacy Agent – Agent Engineer Home Assignment

A stateless, streaming AI pharmacy assistant that uses internal tools and a synthetic database to answer pharmacy-related questions in **English and Hebrew**.

## Supported Capabilities
- Medication information (tool-based, no hallucinations)
- Stock availability by branch
- Prescription lookup
- Refill request submission (simulated)

---

## High-Level Architecture

### Frontend
- Simple web UI (`/web`)
- Stateless interaction (full conversation sent on each request)
- Streaming responses rendered in real time

### Backend
- FastAPI application (`app/main.py`)
- Stateless design
- Streaming OpenAI responses
- SQLite-backed deterministic tools

### Agent Design
- Intent-based routing
- Multi-step workflows implemented in code
- Tool-first factual grounding
- No medical advice or diagnosis

---

## Tools

### get_medication_by_name
Lookup a medication by English or Hebrew name.

**Input**
```json
{
  "name": "Ibuprofen"
}
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
Check stock availability across pharmacy branches.

Input

json
Copy code
{
  "medication_id": 2
}
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
{
  "contact": "0501234567"
}
Output

json
Copy code
{
  "id": 1,
  "full_name": "Ben Cohen"
}
list_user_prescriptions
List prescriptions for a given user.

Input

json
Copy code
{
  "user_id": 1
}
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

Database file is not committed (recreated from seed script)

Multi-Step Agent Flows
Flow 1 – Stock Availability
Trigger
User asks about medication availability.

Steps

Extract medication name → get_medication_by_name

Fetch inventory → check_inventory

Stream formatted response

Examples

Do you have Ibuprofen in stock?

יש נורופן במלאי?

Flow 2 – Prescription Lookup
Trigger
User asks to check prescriptions.

Steps

Identify user → get_user_by_contact

Fetch prescriptions → list_user_prescriptions

Stream results and ask about refill

Examples

Check prescriptions for 0507654321

תבדוק מרשמים עבור 0501234567

Flow 3 – Refill Request (Simulated)
Trigger
User requests a medication refill.

Steps

Identify user

Validate prescription exists and is active

Ensure refills are available

Confirm refill submission (simulation only)

Examples

Refill Atorvastatin for 0507654321

אני רוצה חידוש לאמוקסיצילין עבור 0501234567

Safety
No medical advice, diagnosis, or treatment recommendations

No hallucinated facts

All medication, stock, and prescription data is sourced strictly from tools

Setup
bash
Copy code
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python data/seed_db.py
uvicorn app.main:app --reload
Open the UI:

arduino
Copy code
http://127.0.0.1:8000/web/
Security
.env excluded via .gitignore

No API keys or secrets committed