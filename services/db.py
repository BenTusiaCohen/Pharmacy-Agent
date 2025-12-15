import sqlite3
from pathlib import Path

# points to: pharmacy-agent/data/pharmacy.db
DB_PATH = Path(__file__).parent.parent / "data" / "pharmacy.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def get_medication_by_name(name: str):
    """
    Search medication by English or Hebrew name (case-insensitive exact match).
    Returns a dict or None.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        SELECT id, name_en, name_he, active_ingredients,
               dosage_en, dosage_he, prescription_required,
               warnings_en, warnings_he
        FROM medications
        WHERE LOWER(name_en) = LOWER(?)
           OR LOWER(name_he) = LOWER(?)
        """,
        (name, name),
    )

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "name_en": row[1],
        "name_he": row[2],
        "active_ingredients": row[3],
        "dosage_en": row[4],
        "dosage_he": row[5],
        "prescription_required": bool(row[6]),
        "warnings_en": row[7],
        "warnings_he": row[8],
    }


def check_inventory(medication_id: int):
    """
    Returns inventory across all branches for a medication_id.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        SELECT b.id, b.name, b.city, b.hours, i.quantity
        FROM inventory i
        JOIN branches b ON b.id = i.branch_id
        WHERE i.medication_id = ?
        ORDER BY i.quantity DESC
        """,
        (medication_id,),
    )

    rows = c.fetchall()
    conn.close()

    return [
        {
            "branch_id": r[0],
            "branch_name": r[1],
            "city": r[2],
            "hours": r[3],
            "quantity": r[4],
        }
        for r in rows
    ]


def get_user_by_contact(contact: str):
    """
    Lookup a user by contact (phone or email). Returns dict or None.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        SELECT id, full_name, contact, preferred_language
        FROM users
        WHERE contact = ?
        """,
        (contact,),
    )

    row = c.fetchone()
    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "full_name": row[1],
        "contact": row[2],
        "preferred_language": row[3],
    }


def list_user_prescriptions(user_id: int):
    """
    List prescriptions for a user, joined with medication details.
    """
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        SELECT p.id, p.status, p.refills_left,
               m.id, m.name_en, m.name_he, m.prescription_required
        FROM prescriptions p
        JOIN medications m ON m.id = p.medication_id
        WHERE p.user_id = ?
        """,
        (user_id,),
    )

    rows = c.fetchall()
    conn.close()

    return [
        {
            "prescription_id": r[0],
            "status": r[1],
            "refills_left": r[2],
            "medication_id": r[3],
            "med_name_en": r[4],
            "med_name_he": r[5],
            "prescription_required": bool(r[6]),
        }
        for r in rows
    ]
