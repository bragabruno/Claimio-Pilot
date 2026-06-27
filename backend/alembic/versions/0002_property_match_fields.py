"""property reconciliation fields for Phase 2 matching.

Adds normalized + blocking + corroboration columns to `property`.

Statements are idempotent (IF NOT EXISTS): on a fresh database the metadata-driven 0001
already creates these columns from the current models, while an existing database upgraded
before Phase 2 gets them added here. Either path converges to the same schema.

Revision ID: 0002_property_match_fields
Revises: 0001_initial
Create Date: 2026-06-27
"""

from __future__ import annotations

from alembic import op

revision = "0002_property_match_fields"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

_COLUMNS = (
    "ADD COLUMN IF NOT EXISTS normalized_owner_name TEXT",
    "ADD COLUMN IF NOT EXISTS normalized_owner_address TEXT",
    "ADD COLUMN IF NOT EXISTS owner_name_tokens TEXT[] NOT NULL DEFAULT '{}'",
    "ADD COLUMN IF NOT EXISTS owner_zip VARCHAR(10)",
    "ADD COLUMN IF NOT EXISTS owner_ssn_last4 VARCHAR(4)",
    "ADD COLUMN IF NOT EXISTS owner_dob DATE",
    "ADD COLUMN IF NOT EXISTS owner_is_business BOOLEAN NOT NULL DEFAULT false",
)


def upgrade() -> None:
    for clause in _COLUMNS:
        op.execute(f"ALTER TABLE property {clause}")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_property_owner_name_tokens_gin "
        "ON property USING gin (owner_name_tokens)"
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_property_owner_zip ON property (owner_zip)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_property_owner_zip")
    op.execute("DROP INDEX IF EXISTS ix_property_owner_name_tokens_gin")
    for column in (
        "normalized_owner_name",
        "normalized_owner_address",
        "owner_name_tokens",
        "owner_zip",
        "owner_ssn_last4",
        "owner_dob",
        "owner_is_business",
    ):
        op.execute(f"ALTER TABLE property DROP COLUMN IF EXISTS {column}")
