"""initial schema: pgvector extension + all tables.

Table creation is driven from SQLAlchemy metadata to guarantee the migration never drifts
from the models (see docs/adr/0001). The vector extension is created first so the
`vector(EMBED_DIM)` column and its HNSW index can be built.

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-26
"""

from __future__ import annotations

from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    from app.db import models  # noqa: F401  (register tables)
    from app.db.base import Base

    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    from app.db import models  # noqa: F401
    from app.db.base import Base

    Base.metadata.drop_all(bind=op.get_bind())
    op.execute("DROP EXTENSION IF EXISTS vector")
