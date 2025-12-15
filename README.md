# Pharmacy Agent (Agent Engineer Home Assignment)

A stateless, streaming pharmacy assistant that uses an internal SQLite database via tools to answer:
1) Medication information
2) Stock availability by branch
3) Prescription lookup
4) Refill request submission (simulated)

## Key Design Points
- **Stateless backend**: the browser sends the full conversation each request.
- **Streaming responses**: answers stream token-by-token to the UI.
- **Tool-first behavior**: medication/stock/prescription facts come only from the internal DB (no hallucinated medical details).
- **Bilingual**: if the user writes Hebrew, the assistant replies in Hebrew; otherwise English.

## Project Structure
- `app/main.py` — FastAPI backend + agent logic + flows
- `services/db.py` — deterministic SQLite access layer
- `data/seed_db.py` — creates & seeds `data/pharmacy.db`
- `web/` — simple streaming UI

## Setup

### 1) Create venv and install deps
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt


2) configure env
OPENAI_API_KEY=YOUR_KEY_HERE
OPENAI_MODEL=gpt-5

3) Seed the database
python data/seed_db.py

4) Run the server
uvicorn app.main:app --reload --port 8000

Enter:
http://127.0.0.1:8000/web/

Demo Prompts
Flow 1 — Stock availability

English: Do you have Ibuprofen in stock?

Hebrew: יש נורופן במלאי?

Flow 2 — Prescription lookup

English: Check prescriptions for 0507654321

Hebrew: תבדוק מרשמים עבור 0501234567

Flow 3 — Refill request (simulated)

English: Refill Atorvastatin for 0507654321

Hebrew: אני רוצה חידוש לאמוקסיצילין עבור 0501234567

Notes / Assumptions

Refill submission is simulated (no DB writes). The assistant validates:

prescription exists

status is active

refills_left > 0

The assistant refuses individualized medical advice and directs users to a pharmacist/doctor.

## Notes / Assumptions
- Refill submission is simulated (no DB writes). The assistant validates: prescription exists, status=active, refills_left>0.
- The assistant refuses individualized medical advice and directs users to a pharmacist/doctor.

## Security
- The OpenAI key is read from `.env` and `.env` is excluded from Git history via `.gitignore`.
