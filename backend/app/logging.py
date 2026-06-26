"""Structured JSON logging with PII redaction.

Guardrail (see docs/adr/0003): we never log full SSNs or other raw PII. A logging filter
redacts anything that looks like an SSN before records are emitted, and `mask_ssn` is the
canonical helper for reducing an SSN to its last 4 digits everywhere else.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from app.config import settings

# 9 consecutive digits, or 3-2-4 grouped with - or spaces.
_SSN_RE = re.compile(r"\b(\d{3}[-\s]?\d{2}[-\s]?\d{4})\b")


def mask_ssn(ssn: str | None) -> str | None:
    """Reduce an SSN to ``***-**-1234``. Returns None for falsy input."""
    if not ssn:
        return None
    digits = re.sub(r"\D", "", ssn)
    if len(digits) < 4:
        return "***"
    return f"***-**-{digits[-4:]}"


def _redact(text: str) -> str:
    return _SSN_RE.sub(lambda m: mask_ssn(m.group(1)) or "***", text)


class RedactionFilter(logging.Filter):
    """Redact SSN-like substrings from the formatted message and string args."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _redact(record.msg)
        # Only positional tuple args are scrubbed. A single mapping arg (used for
        # %(name)s formatting) is left untouched — iterating it would corrupt the record.
        if isinstance(record.args, tuple):
            record.args = tuple(
                _redact(a) if isinstance(a, str) else a for a in record.args
            )
        return True


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        for key, value in getattr(record, "extra_fields", {}).items():
            payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    handler.addFilter(RedactionFilter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(settings.log_level.upper())


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
