# Pharmacy Agent – Agent Engineer Home Assignment

A stateless, streaming AI pharmacy assistant that uses internal tools and a synthetic database to answer pharmacy-related questions in **English and Hebrew**.

### Supported capabilities
1. Medication information (tool-based, no hallucinations)
2. Stock availability by branch
3. Prescription lookup
4. Refill request submission (simulated)

---

## High-Level Architecture

### Frontend
- Simple web UI (`/web`) for interactive chat
- Sends the full conversation state with each request (stateless backend)
- Displays streamed responses in real time

### Backend
- FastAPI application (`app/main.py`)
- Stateless request handling
- Streaming responses using OpenAI Chat Completions
- Deterministic internal tools backed by SQLite

### Agent Design
- Intent-based flow routing (stock / prescriptions / refill)
- Multi-step workflows implemented in code
- All factual information comes **only** from internal tools / DB
- No medical advice, diagnosis, or recommendations

---

## Tools

The agent uses the following internal tools:

### 1. `get_medication_by_name`
**Purpose:**  
Lookup a medication by English or Hebrew name.

**Input**
```json
{ "name": "Ibuprofen" }


Output:
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

2. check_inventory

Purpose:
Check stock availability for a medication across branches.

Input:
{ "medication_id": 2 }

Output:
[
  {
    "branch_id": 1,
    "branch_name": "Downtown Pharmacy",
    "city": "Tel Aviv",
    "hours": "08:00–22:00",
    "quantity": 80
  }
]

3. get_user_by_contact

Purpose:
Find a user by phone number or email.

Input:
{ "contact": "0501234567" }

Output:
{
  "id": 1,
  "full_name": "Ben Cohen",
  "contact": "0501234567"
}

4. list_user_prescriptions

Purpose:
List prescriptions for a given user.

Input:
{ "user_id": 1 }

Output:
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

The database file is not committed and is recreated from the seed script.

Multi-Step Agent Flows
Flow 1 – Stock Availability

Trigger:
User asks about medication availability.

Steps:

Extract medication name → get_medication_by_name

Fetch inventory → check_inventory

Stream formatted response

Example prompts:

Do you have Ibuprofen in stock?

יש נורופן במלאי?

Flow 2 – Prescription Lookup

Trigger:
User asks to check prescriptions.

Steps:

Identify user → get_user_by_contact

Fetch prescriptions → list_user_prescriptions

Stream formatted list

Ask if the user wants a refill

Example prompts:

Check prescriptions for 0507654321

תבדוק מרשמים עבור 0501234567

Flow 3 – Refill Request (Simulated)

Trigger:
User asks to refill a medication.

Steps:

Identify user → get_user_by_contact

Fetch prescriptions → list_user_prescriptions

Identify requested medication → get_medication_by_name

Validate:

Prescription exists

Status is active

refills_left > 0

Confirm refill submission (simulation)

Example prompts:

Refill Atorvastatin for 0507654321

אני רוצה חידוש לאמוקסיצילין עבור 0501234567

Safety & Policy Handling

No medical advice, diagnosis, or treatment recommendations

Personal medical advice requests are politely refused

The agent never invents facts (dosage, warnings, availability)

All medication and prescription details come strictly from tools

Evaluation Plan

The agent can be evaluated using:

Functional correctness (tool usage and flow routing)

Safety (no hallucinated medical advice)

Multilingual behavior (Hebrew ↔ English)

Streaming quality (incremental responses)

Edge cases (unknown medication, expired prescriptions, no refills)




Setup Instructions:

1. Create virtual environment:
    python -m venv .venv
    source .venv/bin/activate

2. Install dependencies:
    pip install -r requirements.txt

3. Configure environment

Create a .env file:
    OPENAI_API_KEY=YOUR_API_KEY
    OPENAI_MODEL=gpt-5

4. Seed database:
    python data/seed_db.py

5. Run server:
    uvicorn app.main:app --reload --port 8000


6. Open:
    http://127.0.0.1:8000/web/

Docker
Build:
    docker build -t pharmacy-agent .

Run:
    docker run -p 8000:8000 -e OPENAI_API_KEY=YOUR_API_KEY pharmacy-agent


Notes / Assumptions

Refill requests are simulated (no DB writes)

The backend is intentionally stateless

The database is synthetic and recreated via seed script

Focus is on agent design and multi-step reasoning

Security

.env is excluded via .gitignore

No API keys or secrets are committed