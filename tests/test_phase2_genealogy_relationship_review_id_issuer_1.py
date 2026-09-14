import re

from services.services_genealogy_relationship_reviews import (
    generate_genealogy_relationship_review_id,
)


def test_genealogy_review_id_issuer_uses_canonical_grr_family():
    review_id = generate_genealogy_relationship_review_id()

    assert re.fullmatch(
        r"GRR-[0-9A-F]{20}",
        review_id,
    )


def test_genealogy_review_id_issuer_is_unique():
    generated = {
        generate_genealogy_relationship_review_id()
        for _ in range(200)
    }

    assert len(generated) == 200
