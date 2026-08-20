"""Regression tests for explicit, boundary-aware NA marker compaction."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import na_marker_helper as helper


def test_short_suffix_is_unchanged() -> None:
    suffix = "KEEP-NA, valid — operator decision remains open."
    assert helper.truncate_marker_suffix(suffix) == suffix


def test_truncates_at_sentence_boundary() -> None:
    suffix = "First complete finding. " + "Additional evidence " * 30
    result = helper.truncate_marker_suffix(suffix, max_chars=120)
    assert len(result) <= 120
    assert result.startswith("First complete finding.")
    assert result.endswith(helper.TRUNCATION_NOTICE)


def test_prefers_balanced_clause_boundary() -> None:
    suffix = "Evidence includes (a complete parenthetical clause), then more supporting detail " * 6
    result = helper.truncate_marker_suffix(suffix, max_chars=120)
    content = result.removesuffix(helper.TRUNCATION_NOTICE)
    assert len(result) <= 120
    assert helper._delimiters_balanced(content)
    assert result.endswith(helper.TRUNCATION_NOTICE)


def test_word_fallback_keeps_delimiters_balanced() -> None:
    suffix = "Evidence starts (with an open parenthetical and no clause boundary " + "detail " * 30
    result = helper.truncate_marker_suffix(suffix, max_chars=120)
    content = result.removesuffix(helper.TRUNCATION_NOTICE)
    assert helper._delimiters_balanced(content)
    assert len(result) <= 120


def test_rejects_bare_ellipsis() -> None:
    try:
        helper._validate_marker_suffix("KEEP-NA, valid — rationale...")
    except ValueError as exc:
        assert "complete rationale" in str(exc)
    else:
        raise AssertionError("bare ellipsis must be rejected")
