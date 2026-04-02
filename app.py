from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

# Simple in-memory storage
trusts = []
properties = []
accounts = []
documents = []
ledger_entries = []

@app.route("/")
def home():
    return render_template("dashboard.html", trusts=trusts)


@app.route("/create_trust", methods=["GET", "POST"])
def create_trust():
    if request.method == "POST":
        trust_id = f"TR-{len(trusts) + 1:03d}"
        trust = {
            "trust_id": trust_id,
            "trust_name": request.form.get("trust_name"),
            "trust_type": request.form.get("trust_type"),
            "effective_date": request.form.get("effective_date"),
            "jurisdiction": request.form.get("jurisdiction"),
            "status": "Active"
        }
        trusts.append(trust)
        return redirect(url_for("trust_detail", trust_id=trust_id))

    return render_template("create_trust.html")

@app.route("/add_property", methods=["GET", "POST"])
def add_property():
    if request.method == "POST":
        property_id = f"PR-{len(properties) + 1:03d}"
        prop = {
            "property_id": property_id,
            "trust_id": request.form.get("trust_id"),
            "property_name": request.form.get("property_name"),
            "property_type": request.form.get("property_type"),
            "address_or_identifier": request.form.get("address_or_identifier"),
            "acquisition_date": request.form.get("acquisition_date"),
            "title_notes": request.form.get("title_notes"),
            "beneficial_notes": request.form.get("beneficial_notes"),
            "status": "Mapped"
        }
        properties.append(prop)
        return redirect(url_for("property_detail", property_id=property_id))

    return render_template("add_property.html", trusts=trusts)

@app.route("/link_account", methods=["GET", "POST"])
def link_account():
    if request.method == "POST":
        account_id = f"AC-{len(accounts) + 1:03d}"
        account = {
            "account_id": account_id,
            "trust_id": request.form.get("trust_id"),
            "property_id": request.form.get("property_id"),
            "account_type": request.form.get("account_type"),
            "institution": request.form.get("institution"),
            "account_label": request.form.get("account_label"),
            "masked_number": request.form.get("masked_number"),
            "purpose": request.form.get("purpose")
        }
        accounts.append(account)
        return redirect(url_for("property_detail", property_id=account["property_id"]))

    return render_template("link_account.html", trusts=trusts, properties=properties)

@app.route("/upload_document", methods=["GET", "POST"])
def upload_document():
    if request.method == "POST":
        document_id = f"DOC-{len(documents) + 1:03d}"
        document = {
            "document_id": document_id,
            "trust_id": request.form.get("trust_id"),
            "property_id": request.form.get("property_id"),
            "account_id": request.form.get("account_id"),
            "document_category": request.form.get("document_category"),
            "document_title": request.form.get("document_title"),
            "notes": request.form.get("notes")
        }
        documents.append(document)

        if document["property_id"]:
            return redirect(url_for("property_detail", property_id=document["property_id"]))
        return redirect(url_for("trust_detail", trust_id=document["trust_id"]))

    return render_template("upload_document.html", trusts=trusts, properties=properties, accounts=accounts)

@app.route("/ledger_entry", methods=["GET", "POST"])
def ledger_entry():
    if request.method == "POST":
        entry_id = f"LD-{len(ledger_entries) + 1:03d}"
        entry = {
            "entry_id": entry_id,
            "trust_id": request.form.get("trust_id"),
            "property_id": request.form.get("property_id"),
            "account_id": request.form.get("account_id"),
            "entry_type": request.form.get("entry_type"),
            "amount": request.form.get("amount"),
            "entry_date": request.form.get("entry_date"),
            "description": request.form.get("description")
        }
        ledger_entries.append(entry)

        if entry["property_id"]:
            return redirect(url_for("property_detail", property_id=entry["property_id"]))
        return redirect(url_for("trust_detail", trust_id=entry["trust_id"]))

    return render_template("ledger_entry.html", trusts=trusts, properties=properties, accounts=accounts)

@app.route("/trust/<trust_id>")
def trust_detail(trust_id):
    trust = next((t for t in trusts if t["trust_id"] == trust_id), None)
    if not trust:
        return f"Trust {trust_id} not found"

    linked_properties = [p for p in properties if p["trust_id"] == trust_id]
    linked_accounts = [a for a in accounts if a["trust_id"] == trust_id]
    linked_documents = [d for d in documents if d["trust_id"] == trust_id]
    linked_ledger = [l for l in ledger_entries if l["trust_id"] == trust_id]

    return render_template(
        "trust_detail.html",
        trust=trust,
        linked_properties=linked_properties,
        linked_accounts=linked_accounts,
        linked_documents=linked_documents,
        linked_ledger=linked_ledger
    )

@app.route("/property/<property_id>")
def property_detail(property_id):
    prop = next((p for p in properties if p["property_id"] == property_id), None)
    if not prop:
        return f"Property {property_id} not found"

    linked_trust = next((t for t in trusts if t["trust_id"] == prop["trust_id"]), None)
    linked_accounts = [a for a in accounts if a["property_id"] == property_id]
    linked_documents = [d for d in documents if d["property_id"] == property_id]
    linked_ledger = [l for l in ledger_entries if l["property_id"] == property_id]

    return render_template(
        "property_detail.html",
        prop=prop,
        linked_trust=linked_trust,
        linked_accounts=linked_accounts,
        linked_documents=linked_documents,
        linked_ledger=linked_ledger
    )

if __name__ == "__main__":
    app.run(debug=True)
