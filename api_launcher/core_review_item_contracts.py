from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ReviewQueueItemContractField:
    """One draft field for a future review queue item.

    This is not a database schema and it does not define resolution statuses.
    It only gives Core a stable item identity shape so review-required evidence
    can be discussed without treating display counters as durable queue rows.
    """

    field_id: str
    category: str
    required: bool
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "field_id": self.field_id,
            "category": self.category,
            "required": self.required,
            "description": self.description,
        }


def review_item_identity_contract_fields() -> tuple[ReviewQueueItemContractField, ...]:
    return (
        ReviewQueueItemContractField(
            "review_item_id",
            "identity",
            True,
            "Stable id derived from source surface, source reference, and review bucket.",
        ),
        ReviewQueueItemContractField(
            "source_surface",
            "identity",
            True,
            "Core surface that produced the review-required item.",
        ),
        ReviewQueueItemContractField(
            "source_reference",
            "identity",
            True,
            "Stable reference inside the source surface, such as plan id, resource url, or registry id.",
        ),
        ReviewQueueItemContractField(
            "review_bucket",
            "classification",
            True,
            "Backend-defined review bucket; UI must not infer it from display text.",
        ),
        ReviewQueueItemContractField(
            "payload_format_hint",
            "classification",
            False,
            "Optional content format hint that explains why review is needed.",
        ),
        ReviewQueueItemContractField(
            "evidence_url",
            "audit",
            False,
            "Source or artifact URL/path that supports the review decision.",
        ),
        ReviewQueueItemContractField(
            "warning_codes",
            "audit",
            False,
            "Machine-readable warning codes carried from crawler, resolver, downloader, or importer.",
        ),
        ReviewQueueItemContractField(
            "next_action",
            "display",
            True,
            "Backend-defined next safe action for Tk/Web/future Qt rendering.",
        ),
    )


def review_item_identity_contract_draft() -> dict[str, Any]:
    fields = review_item_identity_contract_fields()
    return {
        "schema_version": "core_review_item_identity_contract_draft.v1",
        "status": "contract_only",
        "scope": "stable_identity_shape_only",
        "field_count": len(fields),
        "fields": [field.to_dict() for field in fields],
        "identity_fields": [
            field.field_id
            for field in fields
            if field.category == "identity"
        ],
        "safety": {
            "adds_review_queue_schema": False,
            "writes_review_queue_records": False,
            "defines_review_resolution_statuses": False,
            "changes_lifecycle_schema": False,
            "promotes_review_required_to_ready": False,
            "imports_renderer_projects": False,
            "imports_compressor_projects": False,
            "reads_renderer_payloads": False,
            "reads_npz": False,
            "cross_repo_implementation": False,
        },
    }


__all__ = [
    "ReviewQueueItemContractField",
    "review_item_identity_contract_draft",
    "review_item_identity_contract_fields",
]
