# UPA-1B-6B-2 — High-Specificity Workspace Exposure Validation

Generated: 2026-06-13T18:27:57.687671
Status: **PRIOR_ADMIN_MARKER_RESULT_NOT_REPRODUCED_WITH_STRONG_MARKERS**

## Database Safety

- Runtime binding verified: **True**
- Live database unchanged: **True**

## Summary

- Workspace Rows: **7**
- Firm 001 Rows: **6**
- Firm 002 Rows: **1**
- Firm 001 Unique Markers: **26**
- Firm 002 Unique Markers: **6**
- Routes Tested: **2**
- Requests Completed: **4**
- Confirmed Exposure Events: **0**

## Unique Workspace Markers

- `FIRM-001`: `['Explore real-property holding structure and related recordkeeping questions.', 'Organize filing questions, tax form links, and reporting workflow notes.', 'Plan and compare family trust structure options before formal buildout.', 'Explore insurance-related trust planning and documentation questions.', 'Organize filing guides, reporting flow, and amendment considerations.', 'Fiduciary Filing Planning Sandbox', 'Land Holding Structure Sandbox', 'Family Trust Design Sandbox', 'Insurance Planning Sandbox', 'Tax Workflow Sandbox', 'filing_planning', 'trust_design', 'insurance', 'revocable', 'too short', 'admin 01', 'too long', 'too much', 'complex', 'too fat', 'WS-001', 'WS-002', 'WS-010', 'WS-011', 'WS-012', 'other']`
- `FIRM-002`: `['Luna I Mishoe III Revocable Trust', 'Too Create a Trust', 'Trust Creation', 'Beneficiary', 'Luna Mishoe', 'FIRM-002']`

## Route Results

### `/discussions/new`

- `FIRM-001` — status `200` — own hits `[]` — opposite hits `[]`
- `FIRM-002` — status `200` — own hits `[]` — opposite hits `[]`

### `/documents/generate`

- `FIRM-001` — status `200` — own hits `[]` — opposite hits `[]`
- `FIRM-002` — status `200` — own hits `[]` — opposite hits `[]`

## Route Source

### `discussion_new`

- Lines: `10528-10553`
- Contains firm_id: **False**
- Contains active-firm helper: **False**

```python
def discussion_new():
    workspaces = get_all_workspaces()
    if request.method == "POST":
        if not validate_csrf_token():
            return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Invalid or missing CSRF token.")

        thread_id = (request.form.get("thread_id") or "").strip()
        title = (request.form.get("title") or "").strip()
        if not thread_id or not title:
            return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories(), error_message="Thread ID and Title are required.")

        payload = {
            "thread_id": thread_id,
            "workspace_id": request.form.get("workspace_id"),
            "title": title,
            "category": request.form.get("category"),
            "related_trust_type": request.form.get("related_trust_type"),
            "related_form": request.form.get("related_form"),
            "created_by": session.get("username") or "unknown",
            "status": request.form.get("status") or "open",
            "owner_id": get_current_owner(),
        }
        create_discussion_thread(payload)
        return redirect(url_for("discussion_thread", thread_id=thread_id))

    return render_template("discussion_form.html", mode="new", workspaces=workspaces, categories=get_discussion_categories())
```

### `document_generate`

- Lines: `10888-10949`
- Contains firm_id: **False**
- Contains active-firm helper: **False**

```python
def document_generate():
    templates = get_document_templates()
    workspaces = get_all_workspaces()

    if request.method == "POST":
        if not validate_csrf_token():
            return render_template(
                "document_generate_form.html",
                templates=templates,
                workspaces=workspaces,
                error_message="Invalid or missing CSRF token."
            )

        document_id = (request.form.get("document_id") or "").strip()
        template_id = (request.form.get("template_id") or "").strip()
        title = (request.form.get("title") or "").strip()

        if not document_id or not template_id or not title:
            return render_template(
                "document_generate_form.html",
                templates=templates,
                workspaces=workspaces,
                error_message="Document ID, Template, and Title are required."
            )

        template = get_document_template_by_id(template_id)
        if not template:
            return render_template(
                "document_generate_form.html",
                templates=templates,
                workspaces=workspaces,
                error_message="Selected template was not found."
            )

        values = {
            "title": request.form.get("title") or "",
            "purpose": request.form.get("purpose") or "",
            "trust_type_focus": request.form.get("trust_type_focus") or "",
            "notes": request.form.get("notes") or "",
            "trust_name": request.form.get("trust_name") or "",
            "trustee_name": request.form.get("trustee_name") or "",
            "authority_scope": request.form.get("authority_scope") or "",
            "related_forms": request.form.get("related_forms") or "",
            "related_reports": request.form.get("related_reports") or "",
        }
        content = render_document_template(template.get("template_body"), values)

        payload = {
            "document_id": document_id,
            "workspace_id": request.form.get("workspace_id"),
            "trust_id": request.form.get("trust_id"),
            "template_id": template_id,
            "title": title,
            "content": content,
            "status": request.form.get("status") or "draft",
            "created_by": session.get("username") or "unknown",
            "owner_id": get_current_owner(),
        }
        create_generated_document(payload)
        return redirect(url_for("document_detail", document_id=document_id))

    return render_template("document_generate_form.html", templates=templates, workspaces=workspaces)
```

## Classification Rule

The earlier `admin` marker result was not reproduced using workspace values unique to the opposite firm. Treat the earlier finding as a likely false positive unless source tracing proves an unscoped lookup independently.
