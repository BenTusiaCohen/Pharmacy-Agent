import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "pharmacy.db"

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

# Recreate tables (start clean every time)
c.executescript("""
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS medications;
DROP TABLE IF EXISTS branches;
DROP TABLE IF EXISTS inventory;
DROP TABLE IF EXISTS prescriptions;

CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    full_name TEXT NOT NULL,
    contact TEXT NOT NULL,
    preferred_language TEXT NOT NULL
);

CREATE TABLE medications (
    id INTEGER PRIMARY KEY,
    name_en TEXT NOT NULL,
    name_he TEXT NOT NULL,
    active_ingredients TEXT NOT NULL,
    dosage_en TEXT NOT NULL,
    dosage_he TEXT NOT NULL,
    prescription_required INTEGER NOT NULL,
    warnings_en TEXT NOT NULL,
    warnings_he TEXT NOT NULL
);

CREATE TABLE branches (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    hours TEXT NOT NULL
);

CREATE TABLE inventory (
    branch_id INTEGER NOT NULL,
    medication_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    PRIMARY KEY (branch_id, medication_id)
);

CREATE TABLE prescriptions (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    medication_id INTEGER NOT NULL,
    status TEXT NOT NULL,
    refills_left INTEGER NOT NULL
);
""")

# 10 synthetic users
users = [
    (1, "Ben Cohen", "0501234567", "en"),
    (2, "Nikol Levi", "0507654321", "en"),
    (3, "David Katz", "david@gmail.com", "en"),
    (4, "Yael Amir", "yael@gmail.com", "he"),
    (5, "Noam Bar", "0501111111", "he"),
    (6, "Dana Rosen", "dana@gmail.com", "en"),
    (7, "Itai Shalev", "itai@gmail.com", "he"),
    (8, "Maya Gold", "0502222222", "en"),
    (9, "Omer Ben-Ami", "omer@gmail.com", "he"),
    (10, "Lior Tal", "0503333333", "en"),
]

# 5 synthetic medications
medications = [
    (1, "Paracetamol", "אקמול", "Paracetamol 500mg",
     "Take 1 tablet every 4–6 hours. Max 4g/day.",
     "טבליה אחת כל 4–6 שעות. עד 4 גרם ביום.",
     0,
     "Do not exceed maximum daily dose.",
     "אין לעבור את המינון היומי המרבי."
    ),
    (2, "Ibuprofen", "נורופן", "Ibuprofen 200mg",
     "Take 1 tablet every 6–8 hours with food.",
     "טבליה אחת כל 6–8 שעות עם אוכל.",
     0,
     "Avoid if you have stomach ulcers.",
     "אין להשתמש במקרה של כיב קיבה."
    ),
    (3, "Amoxicillin", "אמוקסיצילין", "Amoxicillin 500mg",
     "As prescribed by your doctor.",
     "בהתאם להנחיות הרופא.",
     1,
     "Complete the full course.",
     "יש להשלים את כל הטיפול."
    ),
    (4, "Atorvastatin", "ליפיטור", "Atorvastatin 10mg",
     "Once daily, as prescribed.",
     "פעם ביום, לפי מרשם.",
     1,
     "Monitor liver function.",
     "יש לעקוב אחר תפקודי כבד."
    ),
    (5, "Cetirizine", "זירטק", "Cetirizine 10mg",
     "Once daily.",
     "פעם ביום.",
     0,
     "May cause drowsiness.",
     "עלול לגרום לנמנום."
    ),
]

branches = [
    (1, "Downtown Pharmacy", "Tel Aviv", "08:00–22:00"),
    (2, "Mall Pharmacy", "Ramat Gan", "09:00–21:00"),
]

inventory = [
    (1, 1, 120), (1, 2, 80), (1, 3, 15), (1, 4, 10), (1, 5, 60),
    (2, 1, 50),  (2, 2, 40), (2, 3, 0),  (2, 4, 5),  (2, 5, 30),
]

prescriptions = [
    (1, 1, 3, "active", 2),   # Ben has active Amoxicillin Rx
    (2, 2, 4, "active", 1),   # Nikol has active Atorvastatin Rx
    (3, 3, 3, "expired", 0),  # David has expired Amoxicillin Rx
]

c.executemany("INSERT INTO users VALUES (?, ?, ?, ?)", users)
c.executemany("INSERT INTO medications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", medications)
c.executemany("INSERT INTO branches VALUES (?, ?, ?, ?)", branches)
c.executemany("INSERT INTO inventory VALUES (?, ?, ?)", inventory)
c.executemany("INSERT INTO prescriptions VALUES (?, ?, ?, ?, ?)", prescriptions)

conn.commit()
conn.close()

print("✅ Database seeded successfully:", DB_PATH)
