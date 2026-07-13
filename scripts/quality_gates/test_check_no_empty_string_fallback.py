# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_no_empty_string_fallback.py (QG STEP 5.101).

Covers `_has_empty_fallback_noqa()`'s three documented noqa shapes: a
single-code comment, a multi-code comment packed into ONE cluster, and two
SEPARATE `# noqa: ...` clusters on the same line
(qg_empty_string_fallback_checker_misses_stacked_noqa_2026_07_13.md).
"""

from __future__ import annotations

from check_no_empty_string_fallback import _has_empty_fallback_noqa  # type: ignore[import-not-found]


def test_single_code_cluster() -> None:
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-empty-fallback')


def test_multi_code_one_cluster_space_separated() -> None:
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-environ qg-empty-fallback')


def test_multi_code_one_cluster_comma_separated() -> None:
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-environ, qg-empty-fallback')


def test_two_separate_clusters_second_cluster_carries_the_code() -> None:
    """Regression: dev_paths.py:27's exact shape — two independent `# noqa: ...`
    clusters on one line, with `qg-empty-fallback` in the SECOND, not the first.
    """
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-env  # noqa: qg-empty-fallback')


def test_two_separate_clusters_first_cluster_carries_the_code() -> None:
    assert _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-empty-fallback  # noqa: qg-os-env')


def test_no_noqa_comment() -> None:
    assert not _has_empty_fallback_noqa('x = d.get("k", "")')


def test_noqa_present_but_wrong_code() -> None:
    assert not _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-environ')


def test_two_separate_clusters_neither_carries_the_code() -> None:
    assert not _has_empty_fallback_noqa('x = d.get("k", "")  # noqa: qg-os-env  # noqa: qg-empty-string')
