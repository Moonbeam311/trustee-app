import os
import sqlite3
from pathlib import Path
from datetime import date, timedelta, datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BASE_DIR / "trustee_app.db"
DB_PATH = Path(os.getenv("DB_PATH", str(DEFAULT_DB_PATH))).resolve()

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

    trust_cols = [row["name"] for row in cur.execute("PRAGMA table_info(trusts)").fetchall()]
    for col in [
        ("grantor_name", "TEXT"),
        ("grantor_type", "TEXT"),
        ("grantor_contact", "TEXT"),
    ]:
        if col[0] not in trust_cols:
            cur.execute(f"ALTER TABLE trusts ADD COLUMN {col[0]} {col[1]}")

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
        status TEXT,
        asset_class TEXT,
        asset_subtype TEXT,
        established_date TEXT,
        effective_date TEXT,
        review_date TEXT,
        expiration_date TEXT,
        responsible_party TEXT,
        custodian TEXT
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
        notes TEXT,
        original_filename TEXT,
        stored_filename TEXT,
        file_path TEXT
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
        description TEXT,
        entry_category TEXT,
        accounting_method TEXT,
        recognition_date TEXT,
        due_date TEXT,
        paid_date TEXT,
        chart_account TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS chart_of_accounts (
        coa_id TEXT PRIMARY KEY,
        trust_id TEXT,
        account_code TEXT,
        account_name TEXT,
        account_group TEXT,
        normal_balance TEXT,
        is_active TEXT
    )
    """)

    existing_cols = [row["name"] for row in cur.execute("PRAGMA table_info(documents)").fetchall()]
    if "original_filename" not in existing_cols:
        cur.execute("ALTER TABLE documents ADD COLUMN original_filename TEXT")
    if "stored_filename" not in existing_cols:
        cur.execute("ALTER TABLE documents ADD COLUMN stored_filename TEXT")
    if "file_path" not in existing_cols:
        cur.execute("ALTER TABLE documents ADD COLUMN file_path TEXT")

    prop_cols = [row["name"] for row in cur.execute("PRAGMA table_info(properties)").fetchall()]
    for col in [
        ("asset_class", "TEXT"),
        ("asset_subtype", "TEXT"),
        ("established_date", "TEXT"),
        ("effective_date", "TEXT"),
        ("review_date", "TEXT"),
        ("expiration_date", "TEXT"),
        ("responsible_party", "TEXT"),
        ("custodian", "TEXT"),
    ]:
        if col[0] not in prop_cols:
            cur.execute(f"ALTER TABLE properties ADD COLUMN {col[0]} {col[1]}")

    ledger_cols = [row["name"] for row in cur.execute("PRAGMA table_info(ledger_entries)").fetchall()]
    for col in [
        ("entry_category", "TEXT"),
        ("accounting_method", "TEXT"),
        ("recognition_date", "TEXT"),
        ("due_date", "TEXT"),
        ("paid_date", "TEXT"),
        ("chart_account", "TEXT"),
    ]:
        if col[0] not in ledger_cols:
            cur.execute(f"ALTER TABLE ledger_entries ADD COLUMN {col[0]} {col[1]}")

    for table_name in ["properties", "accounts", "documents", "ledger_entries", "trusts"]:
        cols = [row["name"] for row in cur.execute(f"PRAGMA table_info({table_name})").fetchall()]
        if "owner_id" not in cols:
            cur.execute(f"ALTER TABLE {table_name} ADD COLUMN owner_id TEXT")

    conn.commit()
    conn.close()

def get_next_trust_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM trusts")
    count = cur.fetchone()["count"]
    conn.close()
    return f"TR-{count + 1:03d}"

def create_trust_record(trust_data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO trusts (
            trust_id, trust_name, short_name, jurisdiction, effective_date,
            trust_type, trust_purpose, accounting_method, workflow_mode,
            settlor_name, trustee_name, successor_trustee_name, beneficiary_name,
            record_visibility, workflow_mode_confirmed, ai_explanations,
            recommended_guidance, initial_corpus_description, property_mapping_timing,
            asset_categories, generate_schedule_recommendations, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        trust_data["trust_id"], trust_data["trust_name"], trust_data["short_name"],
        trust_data["jurisdiction"], trust_data["effective_date"], trust_data["trust_type"],
        trust_data["trust_purpose"], trust_data["accounting_method"], trust_data["workflow_mode"],
        trust_data["settlor_name"], trust_data["trustee_name"], trust_data["successor_trustee_name"],
        trust_data["beneficiary_name"], trust_data["record_visibility"], trust_data["workflow_mode_confirmed"],
        trust_data["ai_explanations"], trust_data["recommended_guidance"], trust_data["initial_corpus_description"],
        trust_data["property_mapping_timing"], trust_data["asset_categories"],
        trust_data["generate_schedule_recommendations"], trust_data["status"],
    ))
    conn.commit()
    conn.close()

def get_all_trusts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trusts ORDER BY trust_id")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_trust_by_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM trusts WHERE trust_id = ?", (trust_id,))
    row = cur.fetchone()
    conn.close()
    return row

def update_trust_fields(trust_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [trust_id]
    cur.execute(f"UPDATE trusts SET {fields} WHERE trust_id = ?", values)
    conn.commit()
    conn.close()

def get_next_property_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM properties")
    count = cur.fetchone()["count"]
    conn.close()
    return f"PR-{count + 1:03d}"

def create_property_record(prop_data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO properties (
            property_id, trust_id, property_name, property_type,
            address_or_identifier, acquisition_date, title_notes,
            beneficial_notes, status, asset_class, asset_subtype,
            established_date, effective_date, review_date,
            expiration_date, responsible_party, custodian
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        prop_data["property_id"], prop_data["trust_id"], prop_data["property_name"],
        prop_data["property_type"], prop_data["address_or_identifier"], prop_data["acquisition_date"],
        prop_data["title_notes"], prop_data["beneficial_notes"], prop_data["status"],
        prop_data.get("asset_class"), prop_data.get("asset_subtype"), prop_data.get("established_date"),
        prop_data.get("effective_date"), prop_data.get("review_date"), prop_data.get("expiration_date"),
        prop_data.get("responsible_party"), prop_data.get("custodian"),
    ))
    conn.commit()
    conn.close()

def get_property_by_id(property_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM properties WHERE property_id = ?", (property_id,))
    row = cur.fetchone()
    conn.close()
    return row

def get_properties_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM properties WHERE trust_id = ? AND owner_id = ? ORDER BY property_id",
        (trust_id, "ADMIN_OWNER_001")
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_assets():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT p.*, t.trust_name
        FROM properties p
        LEFT JOIN trusts t ON p.trust_id = t.trust_id
        ORDER BY p.property_id
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_asset_class_counts():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT COALESCE(asset_class, property_type, 'unclassified') AS asset_class, COUNT(*) AS count
        FROM properties
        GROUP BY COALESCE(asset_class, property_type, 'unclassified')
        ORDER BY asset_class
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

def get_next_account_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM accounts")
    count = cur.fetchone()["count"]
    conn.close()
    return f"AC-{count + 1:03d}"

def create_account_record(account_data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO accounts (
            account_id, trust_id, property_id, account_type,
            institution, account_label, masked_number, purpose
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        account_data["account_id"], account_data["trust_id"], account_data["property_id"],
        account_data["account_type"], account_data["institution"], account_data["account_label"],
        account_data["masked_number"], account_data["purpose"],
    ))
    conn.commit()
    conn.close()

def get_accounts_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM accounts WHERE trust_id = ? AND owner_id = ? ORDER BY account_id",
        (trust_id, "ADMIN_OWNER_001")
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_accounts_by_property_id(property_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM accounts WHERE property_id = ? AND owner_id = ? ORDER BY account_id",
        (property_id, "ADMIN_OWNER_001")
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_next_document_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM documents")
    count = cur.fetchone()["count"]
    conn.close()
    return f"DOC-{count + 1:03d}"

def create_document_record(doc_data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO documents (
            document_id, trust_id, property_id, account_id,
            document_category, document_title, notes,
            original_filename, stored_filename, file_path
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        doc_data["document_id"], doc_data["trust_id"], doc_data["property_id"], doc_data["account_id"],
        doc_data["document_category"], doc_data["document_title"], doc_data["notes"],
        doc_data["original_filename"], doc_data["stored_filename"], doc_data["file_path"],
    ))
    conn.commit()
    conn.close()

def get_documents_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents WHERE trust_id = ? AND owner_id = ? ORDER BY document_id",
        (trust_id, "ADMIN_OWNER_001")
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_documents_by_property_id(property_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM documents WHERE property_id = ? AND owner_id = ? ORDER BY document_id",
        (property_id, "ADMIN_OWNER_001")
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_next_entry_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM ledger_entries")
    count = cur.fetchone()["count"]
    conn.close()
    return f"LD-{count + 1:03d}"

def create_ledger_entry(entry_data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ledger_entries (
            entry_id, trust_id, property_id, account_id,
            entry_type, amount, entry_date, description,
            entry_category, accounting_method, recognition_date,
            due_date, paid_date, chart_account
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        entry_data["entry_id"], entry_data["trust_id"], entry_data["property_id"], entry_data["account_id"],
        entry_data["entry_type"], entry_data["amount"], entry_data["entry_date"], entry_data["description"],
        entry_data.get("entry_category"), entry_data.get("accounting_method"), entry_data.get("recognition_date"),
        entry_data.get("due_date"), entry_data.get("paid_date"), entry_data.get("chart_account"),
    ))
    conn.commit()
    conn.close()

def get_ledger_by_trust(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM ledger_entries WHERE trust_id = ? AND owner_id = ? ORDER BY entry_id",
        (trust_id, "ADMIN_OWNER_001")
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def get_ledger_by_property(property_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM ledger_entries WHERE property_id = ? AND owner_id = ? ORDER BY entry_id",
        (property_id, "ADMIN_OWNER_001")
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def seed_chart_of_accounts_for_trust(trust_id):
    defaults = [
        ("1000", "Cash", "asset", "debit"),
        ("1100", "Accounts Receivable", "asset", "debit"),
        ("1200", "Prepaid Expense", "asset", "debit"),
        ("2000", "Accounts Payable", "liability", "credit"),
        ("2100", "Deferred Revenue", "liability", "credit"),
        ("4000", "Trust Income", "income", "credit"),
        ("5000", "Trust Expense", "expense", "debit"),
    ]
    conn = get_connection()
    cur = conn.cursor()
    for code, name, grp, normal in defaults:
        coa_id = f"{trust_id}-{code}"
        cur.execute("""
            INSERT OR IGNORE INTO chart_of_accounts (
                coa_id, trust_id, account_code, account_name,
                account_group, normal_balance, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (coa_id, trust_id, code, name, grp, normal, "yes"))
    conn.commit()
    conn.close()

def get_chart_of_accounts(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM chart_of_accounts WHERE trust_id = ? ORDER BY account_code", (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def _safe_amount(v):
    try:
        return float(v or 0)
    except Exception:
        return 0.0

def get_trust_financial_summary(trust_id):
    rows = get_ledger_by_trust(trust_id)
    cash_income = cash_expense = accrual_income = accrual_expense = receivables = payables = 0.0

    for row in rows:
        amt = _safe_amount(row["amount"])
        category = row["entry_category"] or ""
        paid_date = row["paid_date"]
        due_date = row["due_date"]
        recognition_date = row["recognition_date"]

        if category == "income":
            if paid_date:
                cash_income += amt
            if recognition_date:
                accrual_income += amt
            if recognition_date and not paid_date:
                receivables += amt
        elif category == "expense":
            if paid_date:
                cash_expense += amt
            if recognition_date or due_date:
                accrual_expense += amt
            if (recognition_date or due_date) and not paid_date:
                payables += amt

    return {
        "cash_income": round(cash_income, 2),
        "cash_expense": round(cash_expense, 2),
        "cash_net": round(cash_income - cash_expense, 2),
        "accrual_income": round(accrual_income, 2),
        "accrual_expense": round(accrual_expense, 2),
        "accrual_net": round(accrual_income - accrual_expense, 2),
        "receivables": round(receivables, 2),
        "payables": round(payables, 2),
    }

def get_assets_missing_custodian():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM properties WHERE custodian IS NULL OR custodian = '' ORDER BY property_id")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_assets_missing_review_date():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM properties WHERE review_date IS NULL OR review_date = '' ORDER BY property_id")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_assets_with_expiration():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM properties WHERE expiration_date IS NOT NULL AND expiration_date != '' ORDER BY expiration_date")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_orphaned_assets():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM properties WHERE trust_id IS NULL OR trust_id = '' ORDER BY property_id")
    rows = cur.fetchall()
    conn.close()
    return rows

def _parse_iso_date(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except Exception:
        return None

def _assets_within_days(field_name, days):
    today = date.today()
    cutoff = today + timedelta(days=days)
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM properties WHERE {field_name} IS NOT NULL AND {field_name} != ''")
    rows = cur.fetchall()
    conn.close()
    return [row for row in rows if (d := _parse_iso_date(row[field_name])) and today <= d <= cutoff]

def _assets_past_due(field_name):
    today = date.today()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM properties WHERE {field_name} IS NOT NULL AND {field_name} != ''")
    rows = cur.fetchall()
    conn.close()
    return [row for row in rows if (d := _parse_iso_date(row[field_name])) and d < today]

def get_assets_expiring_within(days):
    return _assets_within_days("expiration_date", days)

def get_assets_review_due_within(days):
    return _assets_within_days("review_date", days)

def get_assets_expired():
    return _assets_past_due("expiration_date")

def get_assets_review_overdue():
    return _assets_past_due("review_date")

def get_asset_severity_summary():
    assets = get_all_assets()
    today = date.today()
    results = []
    for asset in assets:
        severity = "LOW"
        reasons = []
        expiration = _parse_iso_date(asset["expiration_date"])
        review = _parse_iso_date(asset["review_date"])
        custodian = asset["custodian"]
        trust_id = asset["trust_id"]

        if not trust_id:
            severity = "HIGH"
            reasons.append("orphaned")
        if not custodian:
            if severity == "LOW":
                severity = "MEDIUM"
            reasons.append("missing custodian")
        if review and review < today:
            severity = "HIGH"
            reasons.append("review overdue")
        if expiration and expiration < today:
            severity = "CRITICAL"
            reasons.append("expired")

        results.append({
            "property_id": asset["property_id"],
            "property_name": asset["property_name"],
            "asset_class": asset["asset_class"] or asset["property_type"],
            "severity": severity,
            "reasons": ", ".join(reasons) if reasons else "no immediate flags",
        })
    return results

def get_command_snapshot():
    severity = get_asset_severity_summary()
    assets = get_all_assets()
    trusts = get_all_trusts()
    critical = [a for a in severity if a["severity"] == "CRITICAL"]
    high = [a for a in severity if a["severity"] == "HIGH"]
    return {
        "total_assets": len(assets),
        "total_trusts": len(trusts),
        "critical_count": len(critical),
        "high_count": len(high),
        "missing_custodian_count": len(get_assets_missing_custodian()),
        "overdue_count": len(get_assets_review_overdue()) + len(get_assets_expired()),
        "critical_assets": critical,
        "high_assets": high,
    }

def get_tax_profile(trust_id):
    trust = get_trust_by_id(trust_id)
    ledger = get_ledger_by_trust(trust_id)
    has_income = any(e["entry_category"] == "income" for e in ledger)
    has_expense = any(e["entry_category"] == "expense" for e in ledger)
    return {
        "trust_id": trust_id,
        "trust_name": trust["trust_name"] if trust else "",
        "accounting_method": trust["accounting_method"] if trust else "",
        "has_income": has_income,
        "has_expense": has_expense,
        "entry_count": len(ledger),
        "has_ein": "yes" if trust and trust["jurisdiction"] else "unknown"
    }

def get_tax_form_applicability(trust_id):
    profile = get_tax_profile(trust_id)
    forms = []
    if profile["has_income"] or profile["has_expense"]:
        forms.append("Form 1041")
    forms.append("Schedule K-1")
    if profile["has_income"]:
        forms.append("Form 1041-ES")
    forms.append("Form 56")
    return forms

def get_tax_readiness(trust_id):
    trust = get_trust_by_id(trust_id)
    ledger = get_ledger_by_trust(trust_id)
    issues = []
    if not trust:
        issues.append("Trust not found")
        return issues
    if not trust["accounting_method"] or trust["accounting_method"] == "Not Yet Selected":
        issues.append("Missing accounting method")
    if len(ledger) == 0:
        issues.append("No financial activity recorded")
    if not trust["beneficiary_name"]:
        issues.append("Missing beneficiary")
    return issues

# ===============================
# FORM 1041 SAFE MODE ENGINE
# ===============================

def get_1041_summary(trust_id):
    ledger = get_ledger_by_trust(trust_id)

    interest_income = 0.0
    business_income = 0.0
    other_income = 0.0

    admin_expense = 0.0
    tax_expense = 0.0
    other_expense = 0.0

    def safe(v):
        try:
            return float(v or 0)
        except:
            return 0.0

    for row in ledger:
        amt = safe(row["amount"])
        category = row["entry_category"] or ""
        desc = (row["description"] or "").lower()

        if category == "income":
            if "interest" in desc:
                interest_income += amt
            elif "business" in desc:
                business_income += amt
            else:
                other_income += amt

        elif category == "expense":
            if "tax" in desc:
                tax_expense += amt
            elif "admin" in desc or "fee" in desc:
                admin_expense += amt
            else:
                other_expense += amt

    total_income = interest_income + business_income + other_income
    total_deductions = admin_expense + tax_expense + other_expense
    net_income = total_income - total_deductions

    return {
        "interest_income": round(interest_income, 2),
        "business_income": round(business_income, 2),
        "other_income": round(other_income, 2),
        "total_income": round(total_income, 2),

        "admin_expense": round(admin_expense, 2),
        "tax_expense": round(tax_expense, 2),
        "other_expense": round(other_expense, 2),
        "total_deductions": round(total_deductions, 2),

        "net_income": round(net_income, 2)
    }


def ensure_k1_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS beneficiaries (
        beneficiary_id TEXT PRIMARY KEY,
        trust_id TEXT,
        full_name TEXT,
        tax_id TEXT,
        beneficiary_type TEXT,
        email TEXT,
        address TEXT,
        allocation_method TEXT,
        fixed_percentage TEXT,
        is_active TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS distributions (
        distribution_id TEXT PRIMARY KEY,
        trust_id TEXT,
        beneficiary_id TEXT,
        tax_year TEXT,
        distribution_date TEXT,
        distribution_type TEXT,
        description TEXT,
        gross_amount TEXT,
        taxable_amount TEXT,
        principal_amount TEXT,
        source_reference TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_next_beneficiary_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM beneficiaries")
    count = cur.fetchone()["count"]
    conn.close()
    return f"BEN-{count + 1:03d}"


def get_next_distribution_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM distributions")
    count = cur.fetchone()["count"]
    conn.close()
    return f"DST-{count + 1:03d}"


def create_beneficiary_record(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO beneficiaries (
            beneficiary_id, trust_id, full_name, tax_id, beneficiary_type,
            email, address, allocation_method, fixed_percentage, is_active, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["beneficiary_id"], data["trust_id"], data["full_name"], data.get("tax_id"),
        data.get("beneficiary_type"), data.get("email"), data.get("address"),
        data.get("allocation_method"), data.get("fixed_percentage"),
        data.get("is_active", "Yes"), data.get("notes")
    ))
    conn.commit()
    conn.close()


def update_beneficiary_record(beneficiary_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [beneficiary_id]
    cur.execute(f"UPDATE beneficiaries SET {fields} WHERE beneficiary_id = ?", values)
    conn.commit()
    conn.close()


def get_beneficiary_by_id(beneficiary_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM beneficiaries WHERE beneficiary_id = ?", (beneficiary_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_beneficiaries_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM beneficiaries WHERE trust_id = ? ORDER BY full_name", (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def create_distribution_record(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO distributions (
            distribution_id, trust_id, beneficiary_id, tax_year, distribution_date,
            distribution_type, description, gross_amount, taxable_amount,
            principal_amount, source_reference, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["distribution_id"], data["trust_id"], data["beneficiary_id"], data["tax_year"],
        data["distribution_date"], data.get("distribution_type"), data.get("description"),
        data.get("gross_amount"), data.get("taxable_amount"), data.get("principal_amount"),
        data.get("source_reference"), data.get("status", "recorded")
    ))
    conn.commit()
    conn.close()


def update_distribution_record(distribution_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [distribution_id]
    cur.execute(f"UPDATE distributions SET {fields} WHERE distribution_id = ?", values)
    conn.commit()
    conn.close()


def get_distribution_by_id(distribution_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM distributions WHERE distribution_id = ?", (distribution_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_distributions_by_trust_id(trust_id, tax_year=None):
    conn = get_connection()
    cur = conn.cursor()
    if tax_year:
        cur.execute("""
            SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id
            FROM distributions d
            LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id
            WHERE d.trust_id = ? AND d.tax_year = ?
            ORDER BY d.distribution_date DESC, d.distribution_id DESC
        """, (trust_id, str(tax_year)))
    else:
        cur.execute("""
            SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id
            FROM distributions d
            LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id
            WHERE d.trust_id = ?
            ORDER BY d.distribution_date DESC, d.distribution_id DESC
        """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_k1_summary(trust_id, tax_year):
    beneficiaries = get_beneficiaries_by_trust_id(trust_id)
    distributions = get_distributions_by_trust_id(trust_id, tax_year)

    total_gross = sum(float(r["gross_amount"] or 0) for r in distributions)
    total_taxable = sum(float(r["taxable_amount"] or 0) for r in distributions)
    total_principal = sum(float(r["principal_amount"] or 0) for r in distributions)

    by_beneficiary = {}
    missing_tax_ids = []

    for b in beneficiaries:
        by_beneficiary[b["beneficiary_id"]] = {
            "beneficiary_name": b["full_name"],
            "tax_id": b["tax_id"] or "",
            "active": b["is_active"],
            "count": 0,
            "gross": 0.0,
            "taxable": 0.0,
            "principal": 0.0,
        }
        if (b["is_active"] or "") == "Yes" and not b["tax_id"]:
            missing_tax_ids.append(b["full_name"])

    for d in distributions:
        bid = d["beneficiary_id"]
        if bid not in by_beneficiary:
            by_beneficiary[bid] = {
                "beneficiary_name": d["beneficiary_name"] or "Unknown",
                "tax_id": d["beneficiary_tax_id"] or "",
                "active": "Yes",
                "count": 0,
                "gross": 0.0,
                "taxable": 0.0,
                "principal": 0.0,
            }
        by_beneficiary[bid]["count"] += 1
        by_beneficiary[bid]["gross"] += float(d["gross_amount"] or 0)
        by_beneficiary[bid]["taxable"] += float(d["taxable_amount"] or 0)
        by_beneficiary[bid]["principal"] += float(d["principal_amount"] or 0)

    warnings = []
    if len(beneficiaries) == 0:
        warnings.append("No beneficiaries exist for this trust.")
    if len(distributions) == 0:
        warnings.append("No distributions were recorded for the selected tax year.")
    if missing_tax_ids:
        warnings.append("One or more active beneficiaries are missing tax identification data.")

    likely_k1_required = len(beneficiaries) > 0 and len(distributions) > 0

    return {
        "total_beneficiaries": len(beneficiaries),
        "total_distributions": len(distributions),
        "total_gross": total_gross,
        "total_taxable": total_taxable,
        "total_principal": total_principal,
        "by_beneficiary": by_beneficiary,
        "missing_tax_ids": missing_tax_ids,
        "warnings": warnings,
        "likely_k1_required": likely_k1_required,
    }

def get_beneficiary_by_id_and_trust(beneficiary_id, trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM beneficiaries WHERE beneficiary_id = ? AND trust_id = ?",
        (beneficiary_id, trust_id)
    )
    row = cur.fetchone()
    conn.close()
    return row


def toggle_beneficiary_active(beneficiary_id, trust_id):
    row = get_beneficiary_by_id_and_trust(beneficiary_id, trust_id)
    if not row:
        return None
    new_value = "No" if (row["is_active"] or "Yes") == "Yes" else "Yes"
    update_beneficiary_record(beneficiary_id, {"is_active": new_value})
    return new_value


def get_distribution_by_id_and_trust(distribution_id, trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT d.*, b.full_name AS beneficiary_name, b.tax_id AS beneficiary_tax_id
        FROM distributions d
        LEFT JOIN beneficiaries b ON d.beneficiary_id = b.beneficiary_id
        WHERE d.distribution_id = ? AND d.trust_id = ?
        """,
        (distribution_id, trust_id)
    )
    row = cur.fetchone()
    conn.close()
    return row


def export_k1_csv_text(trust_id, tax_year):
    trust = get_trust_by_id(trust_id)
    rows = get_distributions_by_trust_id(trust_id, tax_year)

    import csv
    import io

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        "trust_id",
        "trust_name",
        "beneficiary_id",
        "beneficiary_name",
        "beneficiary_tax_id",
        "tax_year",
        "distribution_date",
        "distribution_type",
        "gross_amount",
        "taxable_amount",
        "principal_amount",
        "status",
        "source_reference",
        "description",
    ])

    for row in rows:
        writer.writerow([
            trust["trust_id"] if trust else "",
            trust["trust_name"] if trust else "",
            row["beneficiary_id"],
            row["beneficiary_name"] or "",
            row["beneficiary_tax_id"] or "",
            row["tax_year"],
            row["distribution_date"],
            row["distribution_type"],
            row["gross_amount"],
            row["taxable_amount"],
            row["principal_amount"],
            row["status"],
            row["source_reference"] or "",
            row["description"] or "",
        ])

    return output.getvalue()

def get_ledger_entries_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM ledger_entries
        WHERE trust_id = ?
        ORDER BY entry_date DESC, entry_id DESC
    """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_1041_dataset(trust_id, tax_year):
    trust = get_trust_by_id(trust_id)
    ledger_rows = get_ledger_entries_by_trust_id(trust_id)
    k1 = get_k1_summary(trust_id, tax_year)

    gross_income = 0.0
    deductions = 0.0

    for row in ledger_rows:
        entry_year = ""
        if row["entry_date"]:
            entry_year = str(row["entry_date"])[:4]

        if entry_year != str(tax_year):
            continue

        amount = float(row["amount"] or 0)

        entry_type = (row["entry_type"] or "").lower()
        entry_category = (row["entry_category"] or "").lower()
        chart_account = (row["chart_account"] or "").lower()

        if entry_type == "income":
            gross_income += amount
        elif entry_type == "expense":
            deductions += amount
        elif "income" in entry_category or "income" in chart_account:
            gross_income += amount
        elif "expense" in entry_category or "expense" in chart_account:
            deductions += amount

    net_income = gross_income - deductions
    distributed_taxable_income = float(k1["total_taxable"] or 0)
    retained_income = net_income - distributed_taxable_income

    warnings = []
    if not trust:
        warnings.append("Trust record not found.")
    if gross_income == 0 and deductions == 0:
        warnings.append("No ledger activity detected for the selected tax year.")
    if k1["total_beneficiaries"] == 0:
        warnings.append("No beneficiaries recorded.")
    if k1["total_distributions"] == 0:
        warnings.append("No K-1 distributions recorded.")
    if k1["missing_tax_ids"]:
        warnings.append("One or more active beneficiaries are missing tax identification data.")

    line_mapping = [
        {"label": "Gross Income", "value": round(gross_income, 2), "note": "Derived from ledger income-classified entries"},
        {"label": "Deductions", "value": round(deductions, 2), "note": "Derived from ledger expense-classified entries"},
        {"label": "Net Income", "value": round(net_income, 2), "note": "Gross Income minus Deductions"},
        {"label": "Distributed Taxable Income", "value": round(distributed_taxable_income, 2), "note": "Derived from K-1 taxable distributions"},
        {"label": "Retained Income", "value": round(retained_income, 2), "note": "Net Income minus Distributed Taxable Income"},
    ]

    readiness_flags = {
        "has_income": gross_income > 0,
        "has_deductions": deductions > 0,
        "has_beneficiaries": k1["total_beneficiaries"] > 0,
        "has_distributions": k1["total_distributions"] > 0,
        "missing_tax_ids": len(k1["missing_tax_ids"]) > 0,
    }

    return {
        "trust": trust,
        "tax_year": str(tax_year),
        "gross_income": round(gross_income, 2),
        "deductions": round(deductions, 2),
        "net_income": round(net_income, 2),
        "distributed_taxable_income": round(distributed_taxable_income, 2),
        "retained_income": round(retained_income, 2),
        "k1_summary": k1,
        "warnings": warnings,
        "line_mapping": line_mapping,
        "readiness_flags": readiness_flags,
    }

def get_ledger_entries_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM ledger_entries
        WHERE trust_id = ?
        ORDER BY entry_date DESC, entry_id DESC
    """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_1041_dataset(trust_id, tax_year):
    trust = get_trust_by_id(trust_id)
    ledger_rows = get_ledger_entries_by_trust_id(trust_id)
    k1 = get_k1_summary(trust_id, tax_year)

    gross_income = 0.0
    deductions = 0.0

    for row in ledger_rows:
        entry_year = ""
        if row["entry_date"]:
            entry_year = str(row["entry_date"])[:4]

        if entry_year != str(tax_year):
            continue

        amount = float(row["amount"] or 0)

        entry_type = (row["entry_type"] or "").lower()
        entry_category = (row["entry_category"] or "").lower()
        chart_account = (row["chart_account"] or "").lower()

        if entry_type == "income":
            gross_income += amount
        elif entry_type == "expense":
            deductions += amount
        elif "income" in entry_category or "income" in chart_account:
            gross_income += amount
        elif "expense" in entry_category or "expense" in chart_account:
            deductions += amount

    net_income = gross_income - deductions
    distributed_taxable_income = float(k1["total_taxable"] or 0)
    retained_income = net_income - distributed_taxable_income

    warnings = []
    if not trust:
        warnings.append("Trust record not found.")
    if gross_income == 0 and deductions == 0:
        warnings.append("No ledger activity detected for the selected tax year.")
    if k1["total_beneficiaries"] == 0:
        warnings.append("No beneficiaries recorded.")
    if k1["total_distributions"] == 0:
        warnings.append("No K-1 distributions recorded.")
    if k1["missing_tax_ids"]:
        warnings.append("One or more active beneficiaries are missing tax identification data.")

    line_mapping = [
        {"label": "Gross Income", "value": round(gross_income, 2), "note": "Derived from ledger income-classified entries"},
        {"label": "Deductions", "value": round(deductions, 2), "note": "Derived from ledger expense-classified entries"},
        {"label": "Net Income", "value": round(net_income, 2), "note": "Gross Income minus Deductions"},
        {"label": "Distributed Taxable Income", "value": round(distributed_taxable_income, 2), "note": "Derived from K-1 taxable distributions"},
        {"label": "Retained Income", "value": round(retained_income, 2), "note": "Net Income minus Distributed Taxable Income"},
    ]

    readiness_flags = {
        "has_income": gross_income > 0,
        "has_deductions": deductions > 0,
        "has_beneficiaries": k1["total_beneficiaries"] > 0,
        "has_distributions": k1["total_distributions"] > 0,
        "missing_tax_ids": len(k1["missing_tax_ids"]) > 0,
    }

    return {
        "trust": trust,
        "tax_year": str(tax_year),
        "gross_income": round(gross_income, 2),
        "deductions": round(deductions, 2),
        "net_income": round(net_income, 2),
        "distributed_taxable_income": round(distributed_taxable_income, 2),
        "retained_income": round(retained_income, 2),
        "k1_summary": k1,
        "warnings": warnings,
        "line_mapping": line_mapping,
        "readiness_flags": readiness_flags,
    }

def ensure_instrument_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS instruments (
        instrument_id TEXT PRIMARY KEY,
        trust_id TEXT,
        instrument_number TEXT,
        instrument_type TEXT,
        issue_date TEXT,
        maturity_date TEXT,
        face_value TEXT,
        backing_type TEXT,
        backing_reference TEXT,
        status TEXT,
        affidavit_reference TEXT,
        custody_reference TEXT,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_next_instrument_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM instruments")
    count = cur.fetchone()["count"]
    conn.close()
    return f"INS-{count + 1:03d}"


def create_instrument_record(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO instruments (
            instrument_id, trust_id, instrument_number, instrument_type,
            issue_date, maturity_date, face_value, backing_type,
            backing_reference, status, affidavit_reference,
            custody_reference, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["instrument_id"], data["trust_id"], data["instrument_number"],
        data["instrument_type"], data.get("issue_date"), data.get("maturity_date"),
        data.get("face_value"), data.get("backing_type"), data.get("backing_reference"),
        data.get("status"), data.get("affidavit_reference"),
        data.get("custody_reference"), data.get("notes")
    ))
    conn.commit()
    conn.close()


def update_instrument_record(instrument_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [instrument_id]
    cur.execute(f"UPDATE instruments SET {fields} WHERE instrument_id = ?", values)
    conn.commit()
    conn.close()


def get_instrument_by_id(instrument_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM instruments WHERE instrument_id = ?", (instrument_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_instruments_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM instruments
        WHERE trust_id = ?
        ORDER BY issue_date DESC, instrument_id DESC
    """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_instruments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM instruments
        ORDER BY issue_date DESC, instrument_id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_instrument_creation_guide():
    return [
        "Choose the issuing trust and confirm authority.",
        "Assign a unique instrument number before issue.",
        "Select the instrument type and intended purpose.",
        "Record issue date, maturity date, and face value.",
        "Document the backing type and backing reference.",
        "Link supporting affidavit and custody references if available.",
        "Keep instruments separate from tax calculations unless explicitly posted to the ledger.",
    ]

def ensure_instrument_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS instruments (
        instrument_id TEXT PRIMARY KEY,
        trust_id TEXT,
        instrument_number TEXT,
        instrument_type TEXT,
        issue_date TEXT,
        maturity_date TEXT,
        face_value TEXT,
        backing_type TEXT,
        backing_reference TEXT,
        status TEXT,
        affidavit_reference TEXT,
        custody_reference TEXT,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_next_instrument_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM instruments")
    count = cur.fetchone()["count"]
    conn.close()
    return f"INS-{count + 1:03d}"


def create_instrument_record(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO instruments (
            instrument_id, trust_id, instrument_number, instrument_type,
            issue_date, maturity_date, face_value, backing_type,
            backing_reference, status, affidavit_reference,
            custody_reference, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["instrument_id"], data["trust_id"], data["instrument_number"],
        data["instrument_type"], data.get("issue_date"), data.get("maturity_date"),
        data.get("face_value"), data.get("backing_type"), data.get("backing_reference"),
        data.get("status"), data.get("affidavit_reference"),
        data.get("custody_reference"), data.get("notes")
    ))
    conn.commit()
    conn.close()


def update_instrument_record(instrument_id, updates):
    conn = get_connection()
    cur = conn.cursor()
    fields = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [instrument_id]
    cur.execute(f"UPDATE instruments SET {fields} WHERE instrument_id = ?", values)
    conn.commit()
    conn.close()


def get_instrument_by_id(instrument_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM instruments WHERE instrument_id = ?", (instrument_id,))
    row = cur.fetchone()
    conn.close()
    return row


def get_instruments_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM instruments
        WHERE trust_id = ?
        ORDER BY issue_date DESC, instrument_id DESC
    """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_all_instruments():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM instruments
        ORDER BY issue_date DESC, instrument_id DESC
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_instrument_creation_guide():
    return [
        "Choose the issuing trust and confirm authority.",
        "Assign a unique instrument number before issue.",
        "Select the instrument type and intended purpose.",
        "Record issue date, maturity date, and face value.",
        "Document the backing type and backing reference.",
        "Link supporting affidavit and custody references if available.",
        "Keep instruments separate from tax calculations unless explicitly posted to the ledger.",
    ]


def get_instrument_status_counts(trust_id=None):
    conn = get_connection()
    cur = conn.cursor()

    if trust_id:
        cur.execute("""
            SELECT status, COUNT(*) AS count
            FROM instruments
            WHERE trust_id = ?
            GROUP BY status
        """, (trust_id,))
    else:
        cur.execute("""
            SELECT status, COUNT(*) AS count
            FROM instruments
            GROUP BY status
        """)

    rows = cur.fetchall()
    conn.close()

    counts = {}
    for row in rows:
        key = row["status"] or "unclassified"
        counts[key] = row["count"]
    return counts


def get_trust_count():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM trusts")
    row = cur.fetchone()
    conn.close()
    return row["count"] if row else 0


def get_beneficiary_count():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM beneficiaries")
    row = cur.fetchone()
    conn.close()
    return row["count"] if row else 0


def get_distribution_count():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM distributions")
    row = cur.fetchone()
    conn.close()
    return row["count"] if row else 0


def get_instrument_count():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM instruments")
    row = cur.fetchone()
    conn.close()
    return row["count"] if row else 0

def init_audit_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entity_type TEXT,
            entity_id TEXT,
            action TEXT,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            previous_hash TEXT,
            entry_hash TEXT,
            hash_algorithm TEXT
        )
    """)

    cur.execute("PRAGMA table_info(audit_log)")
    existing_columns = {row["name"] for row in cur.fetchall()}

    migrations = {
        "previous_hash": "ALTER TABLE audit_log ADD COLUMN previous_hash TEXT",
        "entry_hash": "ALTER TABLE audit_log ADD COLUMN entry_hash TEXT",
        "hash_algorithm": "ALTER TABLE audit_log ADD COLUMN hash_algorithm TEXT",
    }

    for column_name, ddl in migrations.items():
        if column_name not in existing_columns:
            cur.execute(ddl)

    conn.commit()
    conn.close()


def log_change(entity_type, entity_id, action, note=""):
    import hashlib, json

    try:
        from flask import has_request_context, session
        firm_id = session.get("firm_id", "FIRM-001") if has_request_context() else "FIRM-001"
    except Exception:
        firm_id = "FIRM-001"

    conn = get_connection()
    cur = conn.cursor()

    # 1. Get previous hash
    cur.execute("SELECT entry_hash FROM audit_log ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    previous_hash = row["entry_hash"] if row and row["entry_hash"] else None

    # 2. Insert base record WITH firm_id
    cur.execute("""
        INSERT INTO audit_log (entity_type, entity_id, action, note, firm_id)
        VALUES (?, ?, ?, ?, ?)
    """, (entity_type, entity_id, action, note, firm_id))

    entry_id = cur.lastrowid

    # 3. Get created_at timestamp
    cur.execute("SELECT created_at FROM audit_log WHERE id = ?", (entry_id,))
    created_at = cur.fetchone()["created_at"]

    # 4. Build canonical payload
    payload = {
        "id": entry_id,
        "firm_id": firm_id,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "action": action,
        "note": note,
        "created_at": created_at,
        "previous_hash": previous_hash
    }

    payload_str = json.dumps(payload, sort_keys=True)

    # 5. Generate hash
    entry_hash = hashlib.sha256(payload_str.encode()).hexdigest()

    # 6. Update record with hash values
    cur.execute("""
        UPDATE audit_log
        SET previous_hash = ?, entry_hash = ?, hash_algorithm = ?
        WHERE id = ?
    """, (previous_hash, entry_hash, "sha256", entry_id))

    conn.commit()
    conn.close()

def get_audit_log(limit=100):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM audit_log
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_audit_log_by_entity(entity_type=None, entity_id=None, limit=100):
    conn = get_connection()
    cur = conn.cursor()

    if entity_type and entity_id:
        cur.execute("""
            SELECT * FROM audit_log
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (entity_type, entity_id, limit))
    elif entity_type:
        cur.execute("""
            SELECT * FROM audit_log
            WHERE entity_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (entity_type, limit))
    else:
        cur.execute("""
            SELECT * FROM audit_log
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows

def get_audit_log_by_entity(entity_type=None, entity_id=None, limit=100):
    conn = get_connection()
    cur = conn.cursor()

    if entity_type and entity_id:
        cur.execute("""
            SELECT * FROM audit_log
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (entity_type, entity_id, limit))
    elif entity_type:
        cur.execute("""
            SELECT * FROM audit_log
            WHERE entity_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (entity_type, limit))
    else:
        cur.execute("""
            SELECT * FROM audit_log
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))

    rows = cur.fetchall()
    conn.close()
    return rows


def verify_audit_log_chain(limit=None):
    import hashlib, json

    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM audit_log ORDER BY id ASC"
    if limit:
        query += f" LIMIT {limit}"

    cur.execute(query)
    rows = cur.fetchall()

    conn.close()

    previous_hash = None
    checked = 0
    broken = 0
    legacy = 0
    first_broken_id = None

    for row in rows:
        row = dict(row)

        # Skip legacy rows (before hash system)
        if not row["entry_hash"]:
            legacy += 1
            continue

        payload = {
            "id": row["id"],
            "entity_type": row["entity_type"],
            "entity_id": row["entity_id"],
            "action": row["action"],
            "note": row["note"],
            "created_at": row["created_at"],
            "previous_hash": row["previous_hash"]
        }

        payload_str = json.dumps(payload, sort_keys=True)
        expected_hash = hashlib.sha256(payload_str.encode()).hexdigest()

        # Check hash integrity
        if expected_hash != row["entry_hash"]:
            broken += 1
            if not first_broken_id:
                first_broken_id = row["id"]

        # Check chain linkage
        if row["previous_hash"] != previous_hash:
            if previous_hash is not None:
                broken += 1
                if not first_broken_id:
                    first_broken_id = row["id"]

        previous_hash = row["entry_hash"]
        checked += 1

    status = "VERIFIED" if broken == 0 else "BROKEN"

    return {
        "status": status,
        "checked": checked,
        "broken": broken,
        "legacy": legacy,
        "first_broken_id": first_broken_id
    }


def normalize_text(value):
    return (value or "").strip()


def is_locked_status(status):
    return normalize_text(status).lower() in {"issued", "retired"}


def validate_instrument_payload(data):
    errors = []

    if not normalize_text(data.get("trust_id")):
        errors.append("Trust is required.")

    if not normalize_text(data.get("instrument_number")):
        errors.append("Instrument number is required.")

    if not normalize_text(data.get("instrument_type")):
        errors.append("Instrument type is required.")

    if not normalize_text(data.get("status")):
        errors.append("Status is required.")

    return errors


def validate_beneficiary_payload(data):
    errors = []

    if not normalize_text(data.get("full_name")):
        errors.append("Beneficiary full name is required.")

    if not normalize_text(data.get("beneficiary_type")):
        errors.append("Beneficiary type is required.")

    return errors


def validate_distribution_payload(data):
    errors = []

    if not normalize_text(data.get("beneficiary_id")):
        errors.append("Beneficiary is required.")

    if not normalize_text(data.get("tax_year")):
        errors.append("Tax year is required.")

    if not normalize_text(data.get("distribution_type")):
        errors.append("Distribution type is required.")

    return errors

def to_float(value):
    try:
        return float(value or 0)
    except:
        return 0.0


def get_distribution_totals_by_trust(trust_id, tax_year=None):
    distributions = get_distributions_by_trust_id(trust_id, tax_year)

    totals = {
        "gross_total": 0.0,
        "taxable_total": 0.0,
        "principal_total": 0.0,
        "count": len(distributions),
    }

    for row in distributions:
        totals["gross_total"] += to_float(row.get("gross_amount"))
        totals["taxable_total"] += to_float(row.get("taxable_amount"))
        totals["principal_total"] += to_float(row.get("principal_amount"))

    return totals


def get_distribution_totals_by_beneficiary(trust_id, tax_year=None):
    distributions = get_distributions_by_trust_id(trust_id, tax_year)
    beneficiaries = get_beneficiaries_by_trust_id(trust_id)

    lookup = {b["beneficiary_id"]: b for b in beneficiaries}
    results = {}

    for row in distributions:
        bid = row["beneficiary_id"]
        if bid not in results:
            name = lookup.get(bid, {}).get("full_name", bid)
            results[bid] = {
                "beneficiary_id": bid,
                "full_name": name,
                "gross_total": 0.0,
                "taxable_total": 0.0,
                "principal_total": 0.0,
                "count": 0,
            }

        results[bid]["gross_total"] += to_float(row.get("gross_amount"))
        results[bid]["taxable_total"] += to_float(row.get("taxable_amount"))
        results[bid]["principal_total"] += to_float(row.get("principal_amount"))
        results[bid]["count"] += 1

    return list(results.values())

def money(value):
    try:
        return f"{float(value or 0):,.2f}"
    except:
        return "0.00"

def compute_dni_components(trust_id, tax_year=None):
    totals = get_distribution_totals_by_trust(trust_id, tax_year)

    gross_income = totals["gross_total"]
    taxable_distributed = totals["taxable_total"]
    principal_distributed = totals["principal_total"]

    distributable_net_income = taxable_distributed
    retained_income = gross_income - taxable_distributed

    if retained_income < 0:
        retained_income = 0.0

    return {
        "gross_income": gross_income,
        "taxable_distributed": taxable_distributed,
        "principal_distributed": principal_distributed,
        "dni": distributable_net_income,
        "retained_income": retained_income,
    }


def compute_beneficiary_tax_shares(trust_id, tax_year=None):
    rows = get_distribution_totals_by_beneficiary(trust_id, tax_year)
    results = []

    for row in rows:
        gross = to_float(row["gross_total"])
        taxable = to_float(row["taxable_total"])
        principal = to_float(row["principal_total"])

        taxable_ratio = 0.0
        if gross > 0:
            taxable_ratio = taxable / gross

        results.append({
            "beneficiary_id": row["beneficiary_id"],
            "full_name": row["full_name"],
            "gross_total": gross,
            "taxable_total": taxable,
            "principal_total": principal,
            "taxable_ratio": taxable_ratio,
        })

    return results

def get_portfolio_summary():
    trusts = get_all_trusts()
    portfolio = []

    grand_totals = {
        "gross_total": 0.0,
        "taxable_total": 0.0,
        "principal_total": 0.0,
        "trust_count": len(trusts),
    }

    for t in trusts:
        trust_id = t["trust_id"]
        totals = get_distribution_totals_by_trust(trust_id)

        grand_totals["gross_total"] += totals["gross_total"]
        grand_totals["taxable_total"] += totals["taxable_total"]
        grand_totals["principal_total"] += totals["principal_total"]

        portfolio.append({
            "trust_id": trust_id,
            "trust_name": t["trust_name"],
            "gross_total": totals["gross_total"],
            "taxable_total": totals["taxable_total"],
            "principal_total": totals["principal_total"],
            "count": totals["count"],
        })

    return portfolio, grand_totals

def ensure_fiduciary_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS fiduciaries (
        fiduciary_id TEXT PRIMARY KEY,
        full_name TEXT,
        role_title TEXT,
        authority_scope TEXT,
        trust_id TEXT,
        appointment_date TEXT,
        effective_date TEXT,
        status TEXT,
        notes TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_next_fiduciary_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM fiduciaries")
    row = cur.fetchone()
    conn.close()
    return f"FID-{row['count'] + 1:03d}"


def create_fiduciary_record(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO fiduciaries (
            fiduciary_id, full_name, role_title, authority_scope,
            trust_id, appointment_date, effective_date, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["fiduciary_id"],
        data.get("full_name"),
        data.get("role_title"),
        data.get("authority_scope"),
        data.get("trust_id"),
        data.get("appointment_date"),
        data.get("effective_date"),
        data.get("status"),
        data.get("notes"),
    ))
    conn.commit()
    conn.close()


def get_all_fiduciaries():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM fiduciaries
        ORDER BY full_name
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_fiduciaries_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM fiduciaries
        WHERE trust_id = ?
        ORDER BY full_name
    """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def ensure_genealogy_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS genealogy_records (
        genealogy_id TEXT PRIMARY KEY,
        trust_id TEXT,
        full_name TEXT,
        lineage_role TEXT,
        birth_date TEXT,
        death_date TEXT,
        parent_1 TEXT,
        parent_2 TEXT,
        spouse TEXT,
        notes TEXT,
        evidence_notes TEXT,
        source_platform TEXT,
        source_title TEXT,
        source_reference TEXT,
        archive_date TEXT,
        verification_status TEXT,
        trace_summary TEXT,
        guidance_prompt TEXT
    )
    """)

    existing_cols = [row["name"] for row in cur.execute("PRAGMA table_info(genealogy_records)").fetchall()]
    for col in [
        ("source_platform", "TEXT"),
        ("source_title", "TEXT"),
        ("source_reference", "TEXT"),
        ("archive_date", "TEXT"),
        ("verification_status", "TEXT"),
        ("trace_summary", "TEXT"),
        ("guidance_prompt", "TEXT"),
    ]:
        if col[0] not in existing_cols:
            cur.execute(f"ALTER TABLE genealogy_records ADD COLUMN {col[0]} {col[1]}")

    conn.commit()
    conn.close()


def get_next_genealogy_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM genealogy_records")
    row = cur.fetchone()
    conn.close()
    return f"GEN-{row['count'] + 1:03d}"


def create_genealogy_record(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO genealogy_records (
            genealogy_id, trust_id, full_name, lineage_role,
            birth_date, death_date, parent_1, parent_2,
            spouse, notes, evidence_notes,
            source_platform, source_title, source_reference,
            archive_date, verification_status, trace_summary, guidance_prompt
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["genealogy_id"],
        data.get("trust_id"),
        data.get("full_name"),
        data.get("lineage_role"),
        data.get("birth_date"),
        data.get("death_date"),
        data.get("parent_1"),
        data.get("parent_2"),
        data.get("spouse"),
        data.get("notes"),
        data.get("evidence_notes"),
        data.get("source_platform"),
        data.get("source_title"),
        data.get("source_reference"),
        data.get("archive_date"),
        data.get("verification_status"),
        data.get("trace_summary"),
        data.get("guidance_prompt"),
    ))
    conn.commit()
    conn.close()


def get_all_genealogy_records():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM genealogy_records
        ORDER BY full_name
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def get_genealogy_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM genealogy_records
        WHERE trust_id = ?
        ORDER BY full_name
    """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def ensure_media_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS media_records (
        media_id TEXT PRIMARY KEY,
        trust_id TEXT,
        related_entity_type TEXT,
        related_entity_id TEXT,
        media_type TEXT,
        file_path TEXT,
        category TEXT,
        description TEXT,
        created_at TEXT
    )
    """)

    conn.commit()
    conn.close()


def get_next_media_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM media_records")
    row = cur.fetchone()
    conn.close()
    return f"MED-{row['count'] + 1:03d}"


def create_media_record(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO media_records (
            media_id, trust_id, related_entity_type,
            related_entity_id, media_type, file_path,
            category, description, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["media_id"],
        data.get("trust_id"),
        data.get("related_entity_type"),
        data.get("related_entity_id"),
        data.get("media_type"),
        data.get("file_path"),
        data.get("category"),
        data.get("description"),
        data.get("created_at"),
    ))
    conn.commit()
    conn.close()


def get_all_media():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM media_records ORDER BY created_at DESC")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_media_by_entity(entity_type, entity_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM media_records
        WHERE related_entity_type = ? AND related_entity_id = ?
        ORDER BY created_at DESC
    """, (entity_type, entity_id))
    rows = cur.fetchall()
    conn.close()
    return rows

def get_media_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM media_records
        WHERE trust_id = ?
        ORDER BY created_at DESC
    """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows

def ensure_role_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_roles (
        role_id TEXT PRIMARY KEY,
        full_name TEXT,
        role_name TEXT,
        trust_id TEXT,
        status TEXT,
        notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        permission_id TEXT PRIMARY KEY,
        permission_name TEXT UNIQUE,
        description TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS role_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT,
        permission_name TEXT,
        UNIQUE(role_name, permission_name)
    )
    """)

    default_permissions = [
        ("PERM-001", "view_dashboard", "View dashboards and core system pages"),
        ("PERM-002", "create_trust", "Create new trust records"),
        ("PERM-003", "edit_trust", "Edit trust records"),
        ("PERM-004", "view_documents", "View trust documents"),
        ("PERM-005", "generate_documents", "Generate trust documents and packets"),
        ("PERM-006", "export_documents", "Export documents, packets, and snapshots"),
        ("PERM-007", "manage_users", "Create, edit, and reset app users"),
        ("PERM-008", "manage_roles", "Create and manage fiduciary role records"),
        ("PERM-009", "view_audit", "View audit and evidence logs"),
        ("PERM-010", "manage_permissions", "View and manage permission matrix"),
        ("PERM-011", "view_security", "View security dashboard and audit integrity"),
        ("PERM-012", "manage_tax_reports", "Create, view, print, and export K-1 / 1041 reports"),
    ]

    cur.executemany("""
        INSERT OR IGNORE INTO permissions (permission_id, permission_name, description)
        VALUES (?, ?, ?)
    """, default_permissions)

    default_role_permissions = {
        "Admin": [
            "view_dashboard", "create_trust", "edit_trust", "view_documents",
            "generate_documents", "export_documents", "manage_users",
            "manage_roles", "view_audit", "manage_permissions",
            "view_security", "manage_tax_reports"
        ],
        "Trustee": [
            "view_dashboard", "create_trust", "edit_trust", "view_documents",
            "generate_documents", "export_documents", "view_audit",
            "manage_tax_reports"
        ],
        "Viewer": [
            "view_dashboard", "view_documents"
        ],
    }

    for role_name, permission_names in default_role_permissions.items():
        for permission_name in permission_names:
            cur.execute("""
                INSERT OR IGNORE INTO role_permissions (role_name, permission_name)
                VALUES (?, ?)
            """, (role_name, permission_name))

    conn.commit()
    conn.close()


def get_next_role_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM user_roles")
    row = cur.fetchone()
    conn.close()
    return f"ROL-{row['count'] + 1:03d}"


def create_role_record(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_roles (
            role_id, full_name, role_name, trust_id, status, notes
        ) VALUES (?, ?, ?, ?, ?, ?)
    """, (
        data["role_id"],
        data.get("full_name"),
        data.get("role_name"),
        data.get("trust_id"),
        data.get("status"),
        data.get("notes"),
    ))
    conn.commit()
    conn.close()


def get_all_roles():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_roles ORDER BY full_name")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_roles_by_trust_id(trust_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM user_roles
        WHERE trust_id = ?
        ORDER BY full_name
    """, (trust_id,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_role_summary_by_trust(trust_id):
    rows = get_roles_by_trust_id(trust_id)
    summary = {
        "Admin": 0,
        "Trustee": 0,
        "Viewer": 0,
    }
    for row in rows:
        role = row["role_name"] or ""
        if role in summary:
            summary[role] += 1
    return summary

def get_role_names_by_trust(trust_id):
    rows = get_roles_by_trust_id(trust_id)
    return [row["role_name"] for row in rows if row.get("role_name")]


def has_required_role(trust_id, allowed_roles):
    roles = get_role_names_by_trust(trust_id)
    for role in roles:
        if role in allowed_roles:
            return True
    return False

def ensure_user_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS app_users (
        user_id TEXT PRIMARY KEY,
        username TEXT UNIQUE,
        password_hash TEXT,
        role_name TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM app_users
        WHERE username = ?
        LIMIT 1
    """, (username,))
    row = cur.fetchone()
    conn.close()
    return row


def create_app_user(data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO app_users (
            user_id, username, password_hash, role_name, status
        ) VALUES (?, ?, ?, ?, ?)
    """, (
        data["user_id"],
        data["username"],
        data["password_hash"],
        data["role_name"],
        data["status"],
    ))
    conn.commit()
    conn.close()

def get_next_user_id():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) AS count FROM app_users")
    row = cur.fetchone()
    conn.close()
    return f"USR-{row['count'] + 1:03d}"


def get_all_app_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM app_users
        ORDER BY username
    """)
    rows = cur.fetchall()
    conn.close()
    return rows


def update_app_user(username, data):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE app_users
        SET role_name = ?, status = ?
        WHERE username = ?
    """, (
        data["role_name"],
        data["status"],
        username,
    ))
    conn.commit()
    conn.close()


def update_app_user_password(username, password_hash):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        UPDATE app_users
        SET password_hash = ?
        WHERE username = ?
    """, (
        password_hash,
        username,
    ))
    conn.commit()
    conn.close()



# =========================
# PERMISSION MATRIX ENGINE
# =========================

def get_permissions_by_role(role_name):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT permission_name
        FROM role_permissions
        WHERE role_name = ?
    """, (role_name,))
    rows = cur.fetchall()
    conn.close()
    return {row["permission_name"] for row in rows}


def role_has_permission(role_name, permission_name):
    perms = get_permissions_by_role(role_name)
    return permission_name in perms

def replace_role_permissions(role_name, permission_names):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM role_permissions WHERE role_name = ?", (role_name,))

    for permission_name in permission_names:
        cur.execute("""
            INSERT INTO role_permissions (role_name, permission_name)
            VALUES (?, ?)
        """, (role_name, permission_name))

    conn.commit()
    conn.close()

def ensure_user_permission_override_tables():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_permission_overrides (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        permission_name TEXT,
        effect TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def get_user_permission_overrides(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM user_permission_overrides
        WHERE username = ?
        ORDER BY permission_name
    """, (username,))
    rows = cur.fetchall()
    conn.close()
    return rows


def replace_user_permission_overrides(username, allow_permissions, deny_permissions):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM user_permission_overrides WHERE username = ?", (username,))

    for permission_name in allow_permissions:
        cur.execute("""
            INSERT INTO user_permission_overrides (username, permission_name, effect)
            VALUES (?, ?, 'allow')
        """, (username, permission_name))

    for permission_name in deny_permissions:
        cur.execute("""
            INSERT INTO user_permission_overrides (username, permission_name, effect)
            VALUES (?, ?, 'deny')
        """, (username, permission_name))

    conn.commit()
    conn.close()

def get_effective_permissions_for_user(username):
    user = None
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM app_users WHERE username = ? LIMIT 1", (username,))
    user = cur.fetchone()
    conn.close()

    if not user:
        return set()

    base_permissions = get_permissions_by_role(user["role_name"])
    overrides = get_user_permission_overrides(username)

    allow = {row["permission_name"] for row in overrides if row["effect"] == "allow"}
    deny = {row["permission_name"] for row in overrides if row["effect"] == "deny"}

    return (base_permissions | allow) - deny


def user_has_effective_permission(username, permission_name):
    return permission_name in get_effective_permissions_for_user(username)

def get_all_permissions():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM permissions
        ORDER BY permission_name
    """)
    rows = cur.fetchall()
    conn.close()
    return rows

# =========================
# SYSTEM HEALTH / DIAGNOSTICS
# =========================

def get_table_columns(table_name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"PRAGMA table_info({table_name})")
        rows = cur.fetchall()
        return [row["name"] for row in rows]
    finally:
        conn.close()


def table_exists(table_name):
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name = ?
            LIMIT 1
        """, (table_name,))
        return cur.fetchone() is not None
    finally:
        conn.close()


def build_system_health_report():
    required_tables = {
        "audit_log": ["id", "entity_type", "entity_id", "action", "note", "created_at", "previous_hash", "entry_hash", "hash_algorithm"],
        "permissions": ["permission_id", "permission_name", "description"],
        "role_permissions": ["id", "role_name", "permission_name"],
        "app_users": ["user_id", "username", "password_hash", "role_name", "status"],
        "user_permission_overrides": ["id", "username", "permission_name", "effect", "created_at"],
    }

    table_reports = []
    overall_ok = True

    for table_name, required_columns in required_tables.items():
        exists = table_exists(table_name)
        columns = get_table_columns(table_name) if exists else []
        missing_columns = [col for col in required_columns if col not in columns]

        ok = exists and not missing_columns
        if not ok:
            overall_ok = False

        table_reports.append({
            "table_name": table_name,
            "exists": exists,
            "columns": columns,
            "missing_columns": missing_columns,
            "ok": ok,
        })

    return {
        "overall_status": "OK" if overall_ok else "ATTENTION",
        "tables": table_reports,
    }

def run_safe_recovery_migrations():
    """
    Re-runs safe startup migration/initialization routines.
    This is intentionally non-destructive:
    - creates missing tables
    - adds missing columns where coded
    - seeds missing default permissions
    - does not delete user data
    """
    results = []

    try:
        init_audit_table()
        results.append({"name": "audit_log", "status": "OK", "note": "Audit table and hash columns verified."})
    except Exception as exc:
        results.append({"name": "audit_log", "status": "ERROR", "note": str(exc)})

    try:
        ensure_role_tables()
        results.append({"name": "permissions", "status": "OK", "note": "Permission matrix tables and defaults verified."})
    except Exception as exc:
        results.append({"name": "permissions", "status": "ERROR", "note": str(exc)})

    try:
        ensure_user_tables()
        results.append({"name": "app_users", "status": "OK", "note": "User table verified."})
    except Exception as exc:
        results.append({"name": "app_users", "status": "ERROR", "note": str(exc)})

    try:
        ensure_user_permission_override_tables()
        results.append({"name": "user_permission_overrides", "status": "OK", "note": "User override table verified."})
    except Exception as exc:
        results.append({"name": "user_permission_overrides", "status": "ERROR", "note": str(exc)})

    return {
        "overall_status": "OK" if all(item["status"] == "OK" for item in results) else "ATTENTION",
        "results": results,
    }

def reseed_default_role_permissions():
    """
    Rebuilds the default role_permissions matrix.
    This does not modify app_users or user_permission_overrides.
    """
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS permissions (
        permission_id TEXT PRIMARY KEY,
        permission_name TEXT UNIQUE,
        description TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS role_permissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        role_name TEXT,
        permission_name TEXT,
        UNIQUE(role_name, permission_name)
    )
    """)

    default_permissions = [
        ("PERM-001", "view_dashboard", "View dashboards and core system pages"),
        ("PERM-002", "create_trust", "Create new trust records"),
        ("PERM-003", "edit_trust", "Edit trust records"),
        ("PERM-004", "view_documents", "View trust documents"),
        ("PERM-005", "generate_documents", "Generate trust documents and packets"),
        ("PERM-006", "export_documents", "Export documents, packets, and snapshots"),
        ("PERM-007", "manage_users", "Create, edit, and reset app users"),
        ("PERM-008", "manage_roles", "Create and manage fiduciary role records"),
        ("PERM-009", "view_audit", "View audit and evidence logs"),
        ("PERM-010", "manage_permissions", "View and manage permission matrix"),
        ("PERM-011", "view_security", "View security dashboard and audit integrity"),
        ("PERM-012", "manage_tax_reports", "Create, view, print, and export K-1 / 1041 reports"),
    ]

    default_role_permissions = {
        "Admin": [
            "view_dashboard", "create_trust", "edit_trust", "view_documents",
            "generate_documents", "export_documents", "manage_users",
            "manage_roles", "view_audit", "manage_permissions",
            "view_security", "manage_tax_reports"
        ],
        "Trustee": [
            "view_dashboard", "create_trust", "edit_trust", "view_documents",
            "generate_documents", "export_documents", "view_audit",
            "manage_tax_reports"
        ],
        "Viewer": [
            "view_dashboard", "view_documents"
        ],
    }

    cur.executemany("""
        INSERT OR IGNORE INTO permissions (permission_id, permission_name, description)
        VALUES (?, ?, ?)
    """, default_permissions)

    for role_name in default_role_permissions:
        cur.execute("DELETE FROM role_permissions WHERE role_name = ?", (role_name,))

    inserted = 0
    for role_name, permission_names in default_role_permissions.items():
        for permission_name in permission_names:
            cur.execute("""
                INSERT OR IGNORE INTO role_permissions (role_name, permission_name)
                VALUES (?, ?)
            """, (role_name, permission_name))
            inserted += 1

    conn.commit()
    conn.close()

    return {
        "overall_status": "OK",
        "roles_seeded": sorted(default_role_permissions.keys()),
        "permissions_inserted_or_verified": len(default_permissions),
        "role_permission_rows_written": inserted,
        "note": "Default role permission matrix restored. User-specific overrides preserved.",
    }


def ensure_firm_columns():
    conn = get_connection()
    cur = conn.cursor()

    def add_column(table, column_def):
        try:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column_def}")
        except Exception as e:
            if "duplicate column" not in str(e).lower():
                print(f"⚠️ {table}: {e}")

    add_column("app_users", "firm_id TEXT")
    add_column("audit_log", "firm_id TEXT")

    conn.commit()
    conn.close()
