from pathlib import Path

path = Path("app.py")
text = path.read_text(encoding="utf-8")

old = '''        transfer.current_capacity = request.form.get("current_capacity", transfer.current_capacity)

        if not validate_capacity_for_step("trustee_acceptance", transfer.current_capacity):
            flash("Trustee acceptance requires trustee capacity.", "warning")
        else:
            transfer.trustee_name = request.form.get("trustee_name", "")
            transfer.trustee_decision = request.form.get("trustee_decision", "")
            transfer.trustee_notes = request.form.get("trustee_notes", "")

            add_transfer_action(
                transfer=transfer,
                action_type="saved_trustee_acceptance",
                performed_by=session.get("username") or "unknown",
                capacity_used=transfer.current_capacity,
                notes=f"Trustee decision: {transfer.trustee_decision}",
                commit=False,
            )

            ext_db.session.commit()
            flash("Trustee acceptance saved.", "success")
            return redirect(url_for("transfer_control_evidence", transfer_id=transfer.transfer_id))
'''

new = '''        transfer.current_capacity = "trustee"
        transfer.trustee_name = request.form.get("trustee_name", "")
        transfer.trustee_decision = request.form.get("trustee_decision", "")
        transfer.trustee_notes = request.form.get("trustee_notes", "")

        add_transfer_action(
            transfer=transfer,
            action_type="saved_trustee_acceptance",
            performed_by=session.get("username") or "unknown",
            capacity_used=transfer.current_capacity,
            notes=f"Trustee decision: {transfer.trustee_decision}",
            commit=False,
        )

        ext_db.session.commit()
        flash("Trustee acceptance saved.", "success")
        return redirect(url_for("transfer_control_evidence", transfer_id=transfer.transfer_id))
'''

if old not in text:
    raise SystemExit("Target block not found. Restore app.py clean before running this helper.")

text = text.replace(old, new, 1)
path.write_text(text, encoding="utf-8")
print("Trustee acceptance block patched cleanly.")
