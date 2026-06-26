import logging

from app.logging import JsonFormatter, RedactionFilter, mask_ssn


def test_mask_ssn():
    assert mask_ssn("123-45-6789") == "***-**-6789"
    assert mask_ssn("123456789") == "***-**-6789"
    assert mask_ssn(None) is None


def test_redaction_filter_scrubs_ssn_in_message():
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname=__file__, lineno=1,
        msg="owner ssn 123-45-6789 here", args=(), exc_info=None,
    )
    RedactionFilter().filter(record)
    assert "123-45-6789" not in record.getMessage()
    assert "6789" in record.getMessage()


def test_redaction_filter_preserves_dict_args():
    # logging stores a single mapping arg as the dict itself (for %(name)s formatting);
    # the filter must not iterate/corrupt it.
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname=__file__, lineno=1,
        msg="counts %s", args=({"claimants": 12},), exc_info=None,
    )
    RedactionFilter().filter(record)
    assert record.getMessage() == "counts {'claimants': 12}"


def test_json_formatter_outputs_json():
    record = logging.LogRecord(
        name="t", level=logging.INFO, pathname=__file__, lineno=1,
        msg="hello", args=(), exc_info=None,
    )
    out = JsonFormatter().format(record)
    assert '"message": "hello"' in out
    assert '"level": "INFO"' in out
