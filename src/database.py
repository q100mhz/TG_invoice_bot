import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")

def init_db():
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS company_profiles (
        user_id INTEGER PRIMARY KEY,
        company_name TEXT NOT NULL,
        inn TEXT NOT NULL,
        bank_name TEXT NOT NULL,
        bik TEXT NOT NULL,
        rs TEXT NOT NULL,
        ks TEXT NOT NULL
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_profile(user_id: int, company_name: str, inn: str, bank_name: str, bik: str, rs: str, ks: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT OR REPLACE INTO company_profiles (user_id, company_name, inn, bank_name, bik, rs, ks)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, company_name, inn, bank_name, bik, rs, ks))
    conn.commit()
    conn.close()

def get_profile(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT company_name, inn, bank_name, bik, rs, ks FROM company_profiles WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return {
            "company_name": row[0],
            "inn": row[1],
            "bank_name": row[2],
            "bik": row[3],
            "rs": row[4],
            "ks": row[5]
        }
    return None

def create_invoice_entry(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO invoices (user_id) VALUES (?)", (user_id,))
    conn.commit()
    invoice_id = cursor.lastrowid
    conn.close()
    return invoice_id