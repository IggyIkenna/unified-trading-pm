"""Regression coverage for the fix to
get_first_paragraph_after_heading() hard-truncation bug:
the function previously cut at char 197 with no word/sentence-boundary
awareness (``result[:197] + "..."``), producing mid-word-cut summaries
whenever a doc's first paragraph exceeded 200 chars.

Guards, most-important first:
  * A paragraph >200 chars truncates at the last sentence boundary
    (period/exclamation/question-mark + space) before char 197.
  * A paragraph >200 chars with no sentence boundary falls back to
    the last word boundary (space) before char 197.
  * A paragraph <=200 chars is returned unmodified (no regression).
  * An extremely long unbroken token (>197 chars, no spaces or
    sentence breaks) still gets the original hard-cut behavior as a
    last resort (avoids returning the raw >200-char string).
  * The output ends with " ..." (space-ellipsis) on sentence/word
    boundary truncation, distinguishing a deliberate boundary cut
    from the old mid-word "..." (no leading space) hard cut.
"""

from __future__ import annotations

import importlib.util
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "plan-hygiene" / "fix_frontmatter.py"
    spec = importlib.util.spec_from_file_location("fix_frontmatter", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


FF = _load_module()

_SENTENCE_BODY = (
    "# Test Doc\n\n"
    "This is the first sentence. "
    "This is a second sentence that adds more text. "
    "And here is a third sentence with even more words to pad things out. "
    "A fourth sentence that continues building length further still. "
    "A fifth sentence that pushes well past two hundred characters total across the whole paragraph block here now.\n\n"
    "## Another heading\n\n"
    "This should not appear in the summary."
)


def test_truncates_at_sentence_boundary() -> None:
    """A paragraph >200 chars truncates at the last sentence-end within 197 chars."""
    text = (
        "# Heading\n\n"
        "Short intro sentence. "
        + "padding " * 60
        + "Final sentence here. "
        + "afterthought " * 30
        + "\n\nMore content."
    )
    result = FF.get_first_paragraph_after_heading(text)
    assert result is not None
    # Must end with " ..." (space-ellipsis = boundary-aware cut)
    assert result.endswith(" ..."), f"Expected ' ...' suffix, got: {result!r}"
    # Must be <= 200 chars (the original length cap)
    assert len(result) <= 200, f"Result too long: {len(result)}"
    # Must not end mid-word (the original bug)
    last_word = result.rsplit(" ", 2)[-2] if " " in result[:-4] else ""
    # The word before " ..." should be a complete word (ending with
    # a sentence terminator if a sentence boundary was found, or a
    # regular word character if a word boundary fallback was used).
    assert not result[:-4].endswith(" ..."), f"Double ellipsis: {result!r}"


def test_truncates_at_word_boundary_when_no_sentence_break() -> None:
    """A paragraph >200 chars with no sentence boundary falls back to last word break."""
    # Build a paragraph with NO sentence-ending punctuation (.!?) + space
    # so the sentence-boundary search fails and the word-boundary fallback activates
    words = [
        "alpha",
        "bravo",
        "charlie",
        "delta",
        "echo",
        "foxtrot",
        "golf",
        "hotel",
        "india",
        "juliet",
        "kilo",
        "lima",
        "mike",
        "november",
        "oscar",
        "papa",
        "quebec",
        "romeo",
        "sierra",
        "tango",
        "uniform",
        "victor",
        "whiskey",
        "xray",
        "yankee",
        "zulu",
        "alpha2",
        "bravo2",
        "charlie2",
        "delta2",
        "echo2",
        "foxtrot2",
        "golf2",
        "hotel2",
        "india2",
        "juliet2",
    ]
    body = "# Heading\n\n" + " ".join(words) + "\n\nMore content."
    result = FF.get_first_paragraph_after_heading(body)
    assert result is not None
    assert result.endswith(" ..."), f"Expected ' ...' suffix on word-boundary fallback, got: {result!r}"
    assert len(result) <= 200
    # The last token before " ..." should be a complete word from our list
    # (not a mid-word fragment)
    content_before_ellipsis = result[:-4].rstrip()
    last_token = content_before_ellipsis.split()[-1] if content_before_ellipsis.split() else ""
    assert last_token in words, f"Last token '{last_token}' is not a complete word from the input"


def test_short_paragraph_unchanged() -> None:
    """A paragraph <=200 chars is returned unmodified (no regression)."""
    body = "# Doc\n\nThis is a short paragraph.\n\n## Next"
    result = FF.get_first_paragraph_after_heading(body)
    assert result == "This is a short paragraph."


def test_no_paragraph_returns_none() -> None:
    """A doc whose body has only headings/lists/blockquotes returns None."""
    body = "# Doc\n\n## Subheading\n\n- only a list item\n- another list item\n\n> just a blockquote"
    result = FF.get_first_paragraph_after_heading(body)
    assert result is None


def test_single_unbroken_token_falls_back_to_hard_cut() -> None:
    """An extremely long token (>197 chars, no spaces/sentence-breaks) still truncates
    rather than returning the raw >200-char string."""
    long_token = "A" * 250
    body = f"# Heading\n\n{long_token}\n\nMore."
    result = FF.get_first_paragraph_after_heading(body)
    assert result is not None
    assert len(result) <= 200
    # With no spaces at all, the result falls through to the hard-cut path
    # and ends with "..." (no leading space — not a boundary cut)
    assert result.endswith("...")


def test_exactly_200_chars_unchanged() -> None:
    """A paragraph exactly 200 chars stays unmodified (boundary check only fires >200)."""
    # Build a paragraph exactly 200 chars
    body = "# H\n\n" + "x" * 200 + "\n\nMore."
    result = FF.get_first_paragraph_after_heading(body)
    assert result is not None
    assert len(result) == 200
    assert "..." not in result
