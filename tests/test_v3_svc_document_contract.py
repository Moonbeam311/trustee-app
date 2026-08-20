import inspect
import json
import sqlite3

import pytest

import database.db as database_db
import services.services_document_contract as contract
from services.services_document_object_model import build_document_object


def allow_all(_trust_id):
    return True


@pytest.fixture()
def document_db(monkeypatch, tmp_path):
    path = tmp_path / "document-contract.db"
    connection = sqlite3.connect(path)
    connection.execute("""CREATE TABLE trusts (
        trust_id TEXT PRIMARY KEY, trust_name TEXT, short_name TEXT,
        jurisdiction TEXT, effective_date TEXT, trust_type TEXT,
        trust_purpose TEXT, settlor_name TEXT, trustee_name TEXT,
        successor_trustee_name TEXT, beneficiary_name TEXT, status TEXT,
        firm_id TEXT, password TEXT
    )""")
    connection.execute("""CREATE TABLE documents (
        document_id TEXT PRIMARY KEY, trust_id TEXT, property_id TEXT,
        account_id TEXT, document_category TEXT, document_title TEXT,
        notes TEXT, original_filename TEXT, stored_filename TEXT,
        file_path TEXT, firm_id TEXT
    )""")
    connection.executemany("INSERT INTO trusts VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)", [
        ("TR-A", "Trust A", None, "GA", None, "Family", "Preservation", "Settlor", "Trustee", None, None, "Active", "FIRM-A", "must-not-render"),
        ("TR-X", "Trust X", None, None, None, None, None, None, None, None, None, "Active", "FIRM-B", None),
    ])
    connection.executemany("INSERT INTO documents VALUES (?,?,?,?,?,?,?,?,?,?,?)", [
        ("DOC-A", "TR-A", None, None, "trust", "Existing Reference", None, None, None, None, "FIRM-A"),
        ("DOC-X", "TR-A", None, None, "trust", "Other Firm", None, None, None, None, "FIRM-B"),
    ])
    connection.commit()
    connection.close()
    monkeypatch.setattr(database_db, "DB_PATH", path)
    monkeypatch.setattr(database_db, "get_current_firm_id", lambda: "FIRM-A")
    return path


def snapshot(path):
    connection = sqlite3.connect(path)
    try:
        return {
            table: connection.execute(f"SELECT * FROM {table} ORDER BY 1").fetchall()
            for table in ("trusts", "documents")
        }
    finally:
        connection.close()


def test_producer_render_delivery_and_existing_object_builder_compatibility(document_db):
    before = snapshot(document_db)
    context = contract.produce_trust_document_context(
        "TR-A", "Certificate of Trust", authorization_check=allow_all,
        generated_by="contract-test", generated_at="2026-08-20T12:00:00Z",
    )
    assert context["source"] == {
        "object_type": "trust", "object_id": "TR-A", "firm_id": "FIRM-A",
        "authoritative_record": True,
    }
    assert context["source_data"]["trust_name"] == "Trust A"
    assert "password" not in context["source_data"]
    assert "successor_trustee_name" in context["missing_optional_fields"]
    text = contract.render_document(context, "txt")
    assert b"Trust A" in text and b"Source Record Remains Authoritative: Yes" in text
    rendered_json = json.loads(contract.render_document(context, "json"))
    assert rendered_json["output_state"]["persisted"] is False
    delivery = contract.build_delivery_metadata(context, "txt")
    assert delivery["filename"] == "Certificate-of-Trust-TR-A.txt"
    assert delivery["persistence"] == "none"

    existing_object = build_document_object(
        document_id="DOC-CONTEXT-TR-A",
        document_type=context["document_type"],
        source_record_type=context["source"]["object_type"],
        source_record_id=context["source"]["object_id"],
        payload=context,
    )
    assert existing_object["identity"]["source_record_id"] == "TR-A"
    assert snapshot(document_db) == before


def test_missing_cross_firm_references_and_transient_no_persistence(document_db):
    before = snapshot(document_db)
    assert contract.produce_trust_document_context("TR-MISSING", "Trust Output", authorization_check=allow_all) is None
    assert contract.produce_trust_document_context("TR-X", "Trust Output", authorization_check=allow_all) is None
    assert [row["document_id"] for row in contract.list_document_references("TR-A", authorization_check=allow_all)] == ["DOC-A"]
    assert contract.get_document_reference("DOC-A", "TR-A", authorization_check=allow_all)
    assert contract.get_document_reference("DOC-X", "TR-A", authorization_check=allow_all) is None
    context = contract.produce_trust_document_context("TR-A", "Trust Output", authorization_check=allow_all)
    contract.render_document(context, "json")
    assert snapshot(document_db) == before


def test_secret_and_unsupported_rendering_fail_closed(document_db):
    context = contract.produce_trust_document_context("TR-A", "Trust Output", authorization_check=allow_all)
    poisoned = dict(context)
    poisoned["password"] = "secret"
    with pytest.raises(contract.DocumentContractError, match="Secret"):
        contract.render_document(poisoned, "json")
    with pytest.raises(contract.DocumentContractError, match="Unsupported"):
        contract.render_document(context, "pdf")


def test_public_contract_has_no_persistence_or_source_mutation_api():
    public = {
        name for name, value in inspect.getmembers(contract, inspect.isfunction)
        if not name.startswith("_")
    }
    assert public == {
        "produce_trust_document_context", "describe_output_capabilities",
        "render_document", "build_delivery_metadata", "list_document_references",
        "get_document_reference",
    }
    assert not any(token in name for name in public for token in ("persist", "archive", "finalize", "approve", "update", "delete"))
