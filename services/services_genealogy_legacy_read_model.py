"""Read-only Genealogy & Legacy aggregate.

This service composes already-governed canonical records for the OS
Genealogy & Legacy workspace.

It does not:
- create or modify Person identity;
- infer identity from names;
- read or convert legacy parent_1, parent_2, or spouse text;
- mutate genealogy relationship assertions;
- create or modify Media Evidence;
- create or modify genealogy review history;
- change assertion status;
- reuse P09;
- establish genealogical truth, inheritance, ownership, citizenship,
  legal status, authority, or entitlement.

Legacy genealogy_records remain a separate compatibility surface until
an explicitly governed migration/linkage policy is authorized.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from services.services_person_identity import (
    list_person_identities,
)
from services.services_person_role_links import (
    list_person_role_links,
)
from services.services_genealogy_relationships import (
    list_genealogy_relationship_assertions_for_person,
)
from services.services_genealogy_relationship_evidence import (
    list_genealogy_relationship_media_evidence,
)
from services.services_genealogy_relationship_reviews import (
    list_genealogy_relationship_reviews,
)


class GenealogyLegacyReadModelError(RuntimeError):
    pass


def _required(value: Any, label: str) -> str:
    text = str(value or "").strip()

    if not text:
        raise GenealogyLegacyReadModelError(
            f"{label} is required."
        )

    return text


def _as_dict(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)

    try:
        return dict(value)
    except Exception as exc:
        raise GenealogyLegacyReadModelError(
            "Canonical service returned an unsupported record."
        ) from exc


def build_genealogy_legacy_read_model(
    db_path: str | Path,
    owner_id: str,
    firm_id: str,
) -> dict[str, Any]:
    """Build one scoped, read-only canonical Genealogy & Legacy view."""

    owner = _required(
        owner_id,
        "Owner scope",
    )
    firm = _required(
        firm_id,
        "Firm scope",
    )

    people_raw = list_person_identities(
        db_path,
        owner,
        firm,
    )

    people = [
        _as_dict(row)
        for row in people_raw
    ]

    person_index = {
        row["person_id"]: row
        for row in people
    }

    assertion_cache: dict[str, dict[str, Any]] = {}
    evidence_cache: dict[str, list[dict[str, Any]]] = {}
    review_cache: dict[str, list[dict[str, Any]]] = {}
    role_cache: dict[str, list[dict[str, Any]]] = {}

    for person in people:
        person_id = person["person_id"]

        role_cache[person_id] = [
            _as_dict(row)
            for row in list_person_role_links(
                db_path,
                person_id,
                owner,
                firm,
            )
        ]

        assertions = (
            list_genealogy_relationship_assertions_for_person(
                db_path,
                person_id,
                owner,
                firm,
            )
        )

        for raw in assertions:
            assertion = _as_dict(raw)
            assertion_id = assertion["assertion_id"]

            assertion_cache.setdefault(
                assertion_id,
                assertion,
            )

    for assertion_id, assertion in assertion_cache.items():
        evidence_cache[assertion_id] = [
            _as_dict(row)
            for row in list_genealogy_relationship_media_evidence(
                db_path,
                assertion_id,
                owner,
                firm,
            )
        ]

        review_cache[assertion_id] = [
            _as_dict(row)
            for row in list_genealogy_relationship_reviews(
                db_path,
                assertion_id,
                owner,
                firm,
            )
        ]

    person_views: list[dict[str, Any]] = []

    for person in people:
        person_id = person["person_id"]
        relationships: list[dict[str, Any]] = []

        for assertion in assertion_cache.values():
            subject_id = assertion["subject_person_id"]
            related_id = assertion["related_person_id"]

            if person_id not in {
                subject_id,
                related_id,
            }:
                continue

            if person_id == subject_id:
                direction = "SUBJECT"
                counterparty_id = related_id
            else:
                direction = "RELATED"
                counterparty_id = subject_id

            assertion_id = assertion["assertion_id"]
            evidence = evidence_cache[assertion_id]
            reviews = review_cache[assertion_id]

            relationships.append(
                {
                    "assertion": dict(assertion),
                    "direction": direction,
                    "counterparty_person": (
                        dict(person_index[counterparty_id])
                        if counterparty_id in person_index
                        else None
                    ),
                    "evidence": [
                        dict(row)
                        for row in evidence
                    ],
                    "reviews": [
                        dict(row)
                        for row in reviews
                    ],
                    "source_connected": bool(evidence),
                    "assertion_status": assertion[
                        "assertion_status"
                    ],
                }
            )

        relationships.sort(
            key=lambda row: (
                str(
                    row["assertion"].get(
                        "relationship_type"
                    )
                    or ""
                ),
                str(
                    row["assertion"].get(
                        "assertion_id"
                    )
                    or ""
                ),
            )
        )

        person_views.append(
            {
                "person": dict(person),
                "role_links": [
                    dict(row)
                    for row in role_cache[person_id]
                ],
                "relationships": relationships,
            }
        )

    status_counts: dict[str, int] = {}

    for assertion in assertion_cache.values():
        status = str(
            assertion.get("assertion_status")
            or "UNKNOWN"
        )

        status_counts[status] = (
            status_counts.get(status, 0) + 1
        )

    source_connected_count = sum(
        1
        for assertion_id in assertion_cache
        if evidence_cache[assertion_id]
    )

    reviewed_assertion_count = sum(
        1
        for assertion_id in assertion_cache
        if review_cache[assertion_id]
    )

    return {
        "workspace": "Genealogy & Legacy",
        "read_only": True,
        "owner_id": owner,
        "firm_id": firm,
        "persons": person_views,
        "summary": {
            "person_count": len(people),
            "relationship_assertion_count": len(
                assertion_cache
            ),
            "source_connected_count": (
                source_connected_count
            ),
            "reviewed_assertion_count": (
                reviewed_assertion_count
            ),
            "status_counts": status_counts,
        },
        "legacy_compatibility": {
            "mode": (
                "SEPARATE_LEGACY_COMPATIBILITY_SURFACE"
            ),
            "legacy_rows_included": False,
            "automatic_identity_inference": False,
            "automatic_parent_spouse_conversion": False,
            "reason": (
                "Legacy genealogy_records remain separate. "
                "Their name-based parent/spouse fields are not "
                "merged into canonical Person relationships."
            ),
        },
        "governance": {
            "source_connected_is_status": False,
            "automatic_status_advancement": False,
            "machine_truth_determination": False,
            "p09_reused": False,
        },
    }
