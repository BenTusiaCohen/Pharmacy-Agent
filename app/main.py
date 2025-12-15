import os
import json
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI

from services.db import (
    get_medication_by_name,
    check_inventory,
    get_user_by_contact,
    list_user_prescriptions,
)

load_dotenv()

OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5")

client = OpenAI(api_key=OPENAI_API_KEY)

app = FastAPI()
app.mount("/web", StaticFiles(directory="web", html=True), name="web")

SYSTEM_PROMPT = """You are an AI pharmacist assistant for a retail pharmacy.

- You DO have access to an internal pharmacy database via tools. Never say you "don't have access".
- For stock questions, always use tools and answer from tool results.

Hard rules:
- Provide factual information only. No medical advice, no diagnosis, no treatment recommendations.
- If asked for personal medical advice ("should I take", "is it safe for me", "what do you recommend"),
  refuse politely and direct the user to a pharmacist/doctor.
- Respond in the user's language: if the user writes Hebrew, respond in Hebrew. Otherwise respond in English.

Tool / data rules (critical):
- For ANY question about a specific medication (info, active ingredient, dosage/usage instructions, prescription requirement),
  you MUST call get_medication_by_name first.
- For ANY question about stock/availability, you MUST call get_medication_by_name first, then check_inventory.
- For ANY question about prescriptions/refills, you MUST call get_user_by_contact first, then list_user_prescriptions.
- You may ONLY use facts returned by tools/DB for medication details (ingredient, dosage, warnings, prescription requirement, stock, prescriptions).
- If a tool returns None (not found), ask a short clarifying question.
- Do NOT invent dosing ranges, onset times, interactions, pregnancy/breastfeeding guidance, etc. unless explicitly provided by tools.

Stock response format (when user asks about availability/stock):
- First line: availability summary (in the user's language)
- Then list branches sorted by quantity (include: branch_name, city, hours, quantity)
- If all quantities are 0: say it's currently out of stock and ask if they want to check other branches.
- Do not offer medical advice or recommendations.

Prescription response format (when user asks about prescriptions/refills):
- Start with the user's name (from DB) if found
- List each prescription: medication name (match language), status, refills_left
- If none exist: say "no prescriptions found"
- End with a short question asking if they want to request a refill for an ACTIVE prescription

Refill request behavior:
- This is a simulated request submission.
- Only allow refill submission if: prescription exists for that medication, status is active, and refills_left > 0.
- Otherwise, explain why it can't be submitted (no prescription / expired / no refills left).
"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_medication_by_name",
            "description": "Lookup a medication by its English or Hebrew name and return its details.",
            "parameters": {
                "type": "object",
                "properties": {"name": {"type": "string"}},
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_inventory",
            "description": "Check stock availability for a medication across pharmacy branches.",
            "parameters": {
                "type": "object",
                "properties": {"medication_id": {"type": "integer"}},
                "required": ["medication_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_by_contact",
            "description": "Find a user by phone number or email stored in the system.",
            "parameters": {
                "type": "object",
                "properties": {"contact": {"type": "string"}},
                "required": ["contact"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_user_prescriptions",
            "description": "List prescriptions for a given user id.",
            "parameters": {
                "type": "object",
                "properties": {"user_id": {"type": "integer"}},
                "required": ["user_id"],
            },
        },
    },
]


def run_tool(name: str, args: dict):
    if name == "get_medication_by_name":
        return get_medication_by_name(args["name"])
    if name == "check_inventory":
        return check_inventory(int(args["medication_id"]))
    if name == "get_user_by_contact":
        return get_user_by_contact(args["contact"])
    if name == "list_user_prescriptions":
        return list_user_prescriptions(int(args["user_id"]))
    return {"error": f"Unknown tool: {name}"}


def _looks_like_hebrew(text: str) -> bool:
    return any("\u0590" <= ch <= "\u05FF" for ch in text)


@app.post("/chat/stream")
def chat_stream(payload: dict):
    messages = payload.get("messages", [])
    if not isinstance(messages, list):
        messages = []

    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    # ---- Get last user text for intent routing ----
    last_user = ""
    for m in reversed(messages):
        if isinstance(m, dict) and m.get("role") == "user":
            last_user = (m.get("content") or "").strip()
            break

    stock_keywords = ["in stock", "stock", "availability", "available", "check stock"]
    stock_keywords_he = ["מלאי", "זמין", "זמינות", "יש לכם"]

    rx_keywords = ["prescription", "prescriptions", "rx", "check prescriptions"]
    rx_keywords_he = ["מרשם", "מרשמים", "תבדוק מרשמים", "בדוק מרשמים"]

    refill_keywords = ["refill", "renew", "renewal", "request refill"]
    refill_keywords_he = ["חידוש", "לחדש", "בקשת חידוש", "ריפיל"]

    is_stock_intent = any(k in last_user.lower() for k in stock_keywords) or any(
        k in last_user for k in stock_keywords_he
    )
    is_rx_intent = any(k in last_user.lower() for k in rx_keywords) or any(
        k in last_user for k in rx_keywords_he
    )
    is_refill_intent = any(k in last_user.lower() for k in refill_keywords) or any(
        k in last_user for k in refill_keywords_he
    )

    # =========================
    # FLOW 1: STOCK AVAILABILITY
    # =========================
    if is_stock_intent:
        planning_med = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=full_messages,
            tools=TOOLS,
            tool_choice={"type": "function", "function": {"name": "get_medication_by_name"}},
            stream=False,
        )

        assistant_msg = planning_med.choices[0].message
        tool_calls = getattr(assistant_msg, "tool_calls", None)

        med = None
        if tool_calls:
            tc = tool_calls[0]
            tool_args = json.loads(tc.function.arguments or "{}")
            med = run_tool("get_medication_by_name", tool_args)
            print(f"[TOOL] get_medication_by_name args={tool_args} result={med}")

        if not med:
            def event_generator_not_found():
                if _looks_like_hebrew(last_user):
                    yield "לא מצאתי את התרופה במערכת. אפשר לרשום את השם המדויק (עברית/אנגלית) כדי שאבדוק מלאי?"
                else:
                    yield "I couldn't find that medication in our catalog. Please provide the exact name (English or Hebrew) so I can check stock."
            return StreamingResponse(event_generator_not_found(), media_type="text/plain")

        inv = check_inventory(int(med["id"]))
        print(f"[TOOL] check_inventory args={{'medication_id': {med['id']}}} result={inv}")

        full_messages.append(
            {
                "role": "system",
                "content": (
                    "Use ONLY the following internal DB facts to answer. "
                    "Do not add external medical information.\n"
                    f"Medication: {json.dumps(med, ensure_ascii=False)}\n"
                    f"Inventory: {json.dumps(inv, ensure_ascii=False)}\n"
                    "Now answer the user's stock question. "
                    "Format: summary line, then branches sorted by quantity with branch_name, city, hours, quantity."
                ),
            }
        )

        def event_generator():
            stream = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=full_messages,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                text = getattr(delta, "content", None)
                if text:
                    yield text

        return StreamingResponse(event_generator(), media_type="text/plain")

    # =========================
    # FLOW 2: PRESCRIPTION LOOKUP
    # =========================
    if is_rx_intent:
        planning_user = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=full_messages,
            tools=TOOLS,
            tool_choice={"type": "function", "function": {"name": "get_user_by_contact"}},
            stream=False,
        )

        assistant_msg = planning_user.choices[0].message
        tool_calls = getattr(assistant_msg, "tool_calls", None)

        user = None
        if tool_calls:
            tc = tool_calls[0]
            tool_args = json.loads(tc.function.arguments or "{}")
            user = run_tool("get_user_by_contact", tool_args)
            print(f"[TOOL] get_user_by_contact args={tool_args} result={user}")

        if not user:
            def event_generator_user_not_found():
                if _looks_like_hebrew(last_user):
                    yield "לא מצאתי משתמש/ת עם הפרטים האלה. אפשר לשלוח מספר טלפון או אימייל כפי שמופיע במערכת?"
                else:
                    yield "I couldn’t find a user with that contact. Please provide the phone number or email exactly as stored in the system."
            return StreamingResponse(event_generator_user_not_found(), media_type="text/plain")

        presc = list_user_prescriptions(int(user["id"]))
        print(f"[TOOL] list_user_prescriptions args={{'user_id': {user['id']}}} result={presc}")

        full_messages.append(
            {
                "role": "system",
                "content": (
                    "Use ONLY the following internal DB facts to answer. Do not add external medical information.\n"
                    f"User: {json.dumps(user, ensure_ascii=False)}\n"
                    f"Prescriptions: {json.dumps(presc, ensure_ascii=False)}\n"
                    "Now answer the user's prescription question.\n"
                    "Format:\n"
                    "- Start with the user's name.\n"
                    "- List prescriptions with medication name (match language), status, refills_left.\n"
                    "- If none exist, say so.\n"
                    "- End with a short question: whether they want to request a refill for an active prescription.\n"
                ),
            }
        )

        def event_generator():
            stream = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=full_messages,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta
                text = getattr(delta, "content", None)
                if text:
                    yield text

        return StreamingResponse(event_generator(), media_type="text/plain")

    # =========================
    # FLOW 3: REFILL REQUEST
    # =========================
    if is_refill_intent:
        # Extract user contact
        planning_user = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=full_messages,
            tools=TOOLS,
            tool_choice={"type": "function", "function": {"name": "get_user_by_contact"}},
            stream=False,
        )

        assistant_msg = planning_user.choices[0].message
        tool_calls = getattr(assistant_msg, "tool_calls", None)

        user = None
        if tool_calls:
            tc = tool_calls[0]
            tool_args = json.loads(tc.function.arguments or "{}")
            user = run_tool("get_user_by_contact", tool_args)
            print(f"[TOOL] get_user_by_contact args={tool_args} result={user}")

        if not user:
            def event_generator_need_contact():
                if _looks_like_hebrew(last_user):
                    yield "כדי להגיש בקשת חידוש, אני צריך/ה מספר טלפון או אימייל כפי שמופיע במערכת."
                else:
                    yield "To submit a refill request, I need the phone number or email exactly as stored in the system."
            return StreamingResponse(event_generator_need_contact(), media_type="text/plain")

        presc = list_user_prescriptions(int(user["id"]))
        print(f"[TOOL] list_user_prescriptions args={{'user_id': {user['id']}}} result={presc}")

        # Extract requested medication name
        planning_med = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=full_messages,
            tools=TOOLS,
            tool_choice={"type": "function", "function": {"name": "get_medication_by_name"}},
            stream=False,
        )

        med_msg = planning_med.choices[0].message
        med_calls = getattr(med_msg, "tool_calls", None)

        requested_med = None
        if med_calls:
            tc2 = med_calls[0]
            med_args = json.loads(tc2.function.arguments or "{}")
            requested_med = run_tool("get_medication_by_name", med_args)
            print(f"[TOOL] get_medication_by_name args={med_args} result={requested_med}")

        if not requested_med:
            def event_generator_need_med():
                if _looks_like_hebrew(last_user):
                    yield "לא הצלחתי לזהות איזו תרופה תרצה/י לחדש. אפשר לכתוב את שם התרופה (עברית/אנגלית) + מספר טלפון/אימייל?"
                else:
                    yield "I couldn’t identify which medication you want to refill. Please provide the medication name (English/Hebrew) plus your phone/email."
            return StreamingResponse(event_generator_need_med(), media_type="text/plain")

        # Find matching prescription
        match = None
        for p in presc:
            if int(p["medication_id"]) == int(requested_med["id"]):
                match = p
                break

        def event_generator():
            if not match:
                if _looks_like_hebrew(last_user):
                    yield f"לא מצאתי במערכת מרשם עבור {requested_med['name_he']} תחת המשתמש/ת הזה/זו. האם תרצה/י שאציג מרשמים קיימים?"
                else:
                    yield f"I couldn’t find a prescription for {requested_med['name_en']} under this user. Would you like me to list existing prescriptions?"
                return

            status = (match.get("status") or "").lower()
            refills_left = int(match.get("refills_left", 0))

            if _looks_like_hebrew(last_user):
                med_name = requested_med["name_he"]
                if status != "active":
                    yield f"לא ניתן להגיש בקשת חידוש: המרשם עבור {med_name} אינו פעיל (סטטוס: {match.get('status')}). האם תרצה/י לבדוק מרשמים אחרים?"
                    return
                if refills_left <= 0:
                    yield f"לא ניתן להגיש בקשת חידוש: אין יתרת חידושים למרשם עבור {med_name}. האם תרצה/י לראות את סטטוס המרשמים במערכת?"
                    return
                yield (
                    f"בקשת חידוש נשלחה עבור {med_name} (משתמש/ת: {user['full_name']}). "
                    f"יתרת חידושים לאחר הבקשה: {refills_left - 1}.\n"
                    "האם תרצה/י שאציג גם שעות פתיחה של הסניפים לאיסוף?"
                )
            else:
                med_name = requested_med["name_en"]
                if status != "active":
                    yield f"Unable to submit a refill request: the prescription for {med_name} is not active (status: {match.get('status')}). Would you like me to list existing prescriptions?"
                    return
                if refills_left <= 0:
                    yield f"Unable to submit a refill request: no refills left for {med_name}. Would you like me to check your prescription statuses?"
                    return
                yield (
                    f"Refill request submitted for {med_name} (user: {user['full_name']}). "
                    f"Refills remaining after this request: {refills_left - 1}.\n"
                    "Would you like pickup hours for the branches?"
                )

        return StreamingResponse(event_generator(), media_type="text/plain")

    # =========================
    # DEFAULT PATH: tool-based Q&A
    # =========================
    planning = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=full_messages,
        tools=TOOLS,
        tool_choice="auto",
        stream=False,
    )

    assistant_msg = planning.choices[0].message
    tool_calls = getattr(assistant_msg, "tool_calls", None)

    assistant_dict = {"role": "assistant", "content": assistant_msg.content or ""}
    if tool_calls:
        assistant_dict["tool_calls"] = [
            {
                "id": tc.id,
                "type": "function",
                "function": {"name": tc.function.name, "arguments": tc.function.arguments},
            }
            for tc in tool_calls
        ]
    full_messages.append(assistant_dict)

    if tool_calls:
        for tc in tool_calls:
            tool_name = tc.function.name
            tool_args = json.loads(tc.function.arguments or "{}")
            result = run_tool(tool_name, tool_args)
            print(f"[TOOL] {tool_name} args={tool_args} result={result}")

            full_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result, ensure_ascii=False),
                }
            )

    def event_generator():
        stream = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=full_messages,
            tools=TOOLS,
            tool_choice="none",
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            text = getattr(delta, "content", None)
            if text:
                yield text

    return StreamingResponse(event_generator(), media_type="text/plain")
