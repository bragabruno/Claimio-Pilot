from app.config import settings
from app.db.base import Base
from app.db.models import RuleChunk


def test_all_tables_registered():
    expected = {
        "claimant",
        "property",
        "state_rule_doc",
        "rule_chunk",
        "claim",
        "run_trace",
        "audit_event",
    }
    assert expected <= set(Base.metadata.tables.keys())


def test_embedding_column_uses_configured_dim():
    col = RuleChunk.__table__.c.embedding
    assert col.type.dim == settings.embed_dim
