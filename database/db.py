import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "trustee_app.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS trusts (
        trust_id TEXT PRIMARY KEY,
        trust_name TEXT,
        short_name TEXT,
        jurisdiction TEXT,
        effective_date TEXT,
        trust_type TEXT,
        trust_purpose TEXT,
        accounting_method TEXT,
        workflow_mode TEXT,
        settlor_name TEXT,
        trustee_name TEXT,
        successor_trustee_name TEXT,
        beneficiary_name TEXT,
        record_visibility TEXT,
        workflow_mode_confirmed TEXT,
        ai_explanations TEXT,
        recommended_guidance TEXT,
        initial_corpus_description TEXT,
        property_mapping_timing TEXT,
        asset_categories TEXT,
        generate_schedule_recommendations TEXT,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS properties (
        property_id TEXT PRIMARY KEY,
        trust_id TEXT,
        property_name TEXT,
        property_type TEXT,
        address_or_identifier TEXT,
        acquisition_date TEXT,
        title_notes TEXT,
        beneficial_notes TEXT,
        status TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS accounts (
        account_id TEXT PRIMARY KEY,
        trust_id TEXT,
        property_id TEXT,
        account_type TEXT,
        institution TEXT,
        account_label TEXT,
        masked_number TEXT,
        purpose TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        document_id TEXT PRIMARY KEY,
        trust_id TEXT,
        property_id TEXT,
        account_id TEXT,
        document_category TEXT,
        document_title TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS ledger_entries (
        entry_id TEXT PRIMARY KEY,
        trust_id TEXT,
        property_id TEXT,
        account_id TEXT,
        entry_type TEXT,
        amount TEXT,
        entry_date TEXT,
        description TEXT
    )
    """)

    conn.commit()
    conn.close()
