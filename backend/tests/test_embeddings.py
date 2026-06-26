import pytest

from app.services.embeddings import EmbeddingsClient

DIM = 8


class _Item:
    def __init__(self, embedding):
        self.embedding = embedding


class _Resp:
    def __init__(self, data):
        self.data = data


def _make_client(dim_returned: int) -> EmbeddingsClient:
    client = EmbeddingsClient(dim=DIM)

    async def fake_create(model, input):  # noqa: A002 — mirrors OpenAI signature
        return _Resp([_Item([0.1] * dim_returned) for _ in input])

    client._client.embeddings.create = fake_create  # type: ignore[assignment]
    return client


async def test_embed_texts_returns_vectors():
    client = _make_client(DIM)
    vectors = await client.embed_texts(["a", "b", "c"])
    assert len(vectors) == 3
    assert all(len(v) == DIM for v in vectors)


async def test_empty_input_short_circuits():
    client = _make_client(DIM)
    assert await client.embed_texts([]) == []


async def test_dimension_mismatch_fails_fast():
    client = _make_client(DIM + 1)
    with pytest.raises(ValueError, match="dimension mismatch"):
        await client.embed_texts(["a"])
