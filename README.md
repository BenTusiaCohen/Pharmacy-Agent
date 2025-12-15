# Pharmacy Agent – Agent Engineer Home Assignment

A stateless, streaming AI pharmacy assistant backed by internal tools and a synthetic database.  
Supports **English and Hebrew**.

---

## Capabilities
- Medication information (tool-based, no hallucinations)
- Stock availability by branch
- Prescription lookup
- Refill request submission (simulated)

---

## Architecture
- **Frontend:** streaming web UI (`/web`)
- **Backend:** stateless FastAPI service
- **Agent:** intent-based routing with multi-step flows
- **Data:** SQLite database accessed only via deterministic tools

---

## Tools (DB-backed)

### `get_medication_by_name`
**Purpose:** Lookup medication details by English or Hebrew name.  
**Input:** `{ name: string }`  
**Output:** medication details (active ingredient, dosage, warnings, prescription requirement)  
**Error handling:** If not found, the agent asks the user to clarify the medication name.

### `check_inventory`
**Purpose:** Check availability across pharmacy branches.  
**Input:** `{ medication_id: number }`  
**Output:** list of branches with quantities.  
**Fallback:** If all quantities are zero, the agent reports out-of-stock.

### `get_user_by_contact`
**Purpose:** Identify a user by phone number or email.  
**Input:** `{ contact: string }`  
**Output:** user identity.  
**Error handling:** If not found, the agent asks for correct contact details.

### `list_user_prescriptions`
**Purpose:** Retrieve prescriptions for a user.  
**Input:** `{ user_id: number }`  
**Output:** list of prescriptions with status and remaining refills.

All factual responses are sourced strictly from these tools.

---

## Multi-Step Agent Flows

### Flow 1 – Stock Availability
**Trigger:** User asks about medication availability.

**Steps:**
1. Extract medication name → `get_medication_by_name`
2. Fetch inventory → `check_inventory`
3. Stream formatted response

**Examples:**
- Do you have Ibuprofen in stock?
- יש נורופן במלאי?

---

### Flow 2 – Prescription Lookup
**Trigger:** User asks to check prescriptions.

**Steps:**
1. Identify user → `get_user_by_contact`
2. Fetch prescriptions → `list_user_prescriptions`
3. Stream results and ask about refill

**Examples:**
- Check prescriptions for 0507654321
- תבדוק מרשמים עבור 0501234567

---

### Flow 3 – Refill Request (Simulated)
**Trigger:** User requests a refill.

**Steps:**
1. Identify user
2. Validate prescription exists and is active
3. Ensure refills are available
4. Confirm refill submission (simulation only)

**Examples:**
- Refill Atorvastatin for 0507654321
- אני רוצה חידוש לאמוקסיצילין עבור 0501234567

---

## Safety
- No medical advice, diagnosis, or treatment recommendations
- No hallucinated medication facts
- Personalized medical questions are politely refused

---

## Evaluation Plan
The agent is evaluated using:
- **Functional correctness:** correct tool usage and flow routing
- **Safety:** no medical advice or hallucinated facts
- **Multi-step handling:** correct sequencing of tool calls
- **Multilingual behavior:** Hebrew and English inputs
- **Streaming quality:** incremental responses
- **Edge cases:** unknown medication/user, out-of-stock, expired prescriptions, no refills

---

## Setup
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python data/seed_db.py
uvicorn app.main:app --reload

Open:
http://127.0.0.1:8000/web/

Docker:
 Build:
    docker build -t pharmacy-agent .

Run:
    docker run -p 8000:8000 -e OPENAI_API_KEY=YOUR_API_KEY pharmacy-agent

Open:
    http://127.0.0.1:8000/web/
    
Notes:

Refill requests are simulated (no DB writes)

Database is synthetic and recreated via seed script

.env is excluded via .gitignore