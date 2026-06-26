from app.services.chunking import chunk_markdown


def test_empty():
    assert chunk_markdown("") == []
    assert chunk_markdown("   \n  ") == []


def test_no_headings_is_single_chunk():
    assert chunk_markdown("just a paragraph") == ["just a paragraph"]


def test_splits_on_headings_and_keeps_heading_with_body():
    md = "# Title\nintro\n\n## A\nalpha body\n\n## B\nbeta body"
    chunks = chunk_markdown(md)
    assert any(c.startswith("## A") and "alpha body" in c for c in chunks)
    assert any(c.startswith("## B") and "beta body" in c for c in chunks)


def test_preamble_before_first_heading_is_kept():
    md = "preamble line\n\n## Section\nbody"
    chunks = chunk_markdown(md)
    assert chunks[0].startswith("preamble line")
