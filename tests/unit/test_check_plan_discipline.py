"""Unit tests for scripts/quality_gates/check_plan_discipline.py's DEFERRED-token
matching (rule A / rule C false-positive precision fix,
plan_discipline_quoted_deferred_false_positive_2026_07_26.md).
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path


def _load_module() -> types.ModuleType:
    repo_root = Path(__file__).resolve().parents[2]
    path = repo_root / "scripts" / "quality_gates" / "check_plan_discipline.py"
    spec = importlib.util.spec_from_file_location("check_plan_discipline", path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["check_plan_discipline"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


MOD = _load_module()


class TestHasLiveDeferredMarker:
    def test_bold_marker_is_live(self) -> None:
        assert MOD._has_live_deferred_marker("This item is **DEFERRED** pending review.") is True

    def test_bracket_marker_is_live(self) -> None:
        assert MOD._has_live_deferred_marker("- [ ] [DEFERRED] fix the thing later") is True

    def test_bare_dash_marker_is_live(self) -> None:
        assert MOD._has_live_deferred_marker("This work is DEFERRED — see follow-up plan.") is True

    def test_quoted_reference_to_another_docs_annotation_is_not_live(self) -> None:
        text = 'is explicitly annotated in the doc itself as "DEFERRED —...'
        assert MOD._has_live_deferred_marker(text) is False

    def test_quoted_reference_with_closing_quote_is_not_live(self) -> None:
        text = 'quotes another doc\'s own "DEFERRED — ..." annotation of ONE of its items'
        assert MOD._has_live_deferred_marker(text) is False

    def test_quoted_reference_does_not_mask_a_real_marker_elsewhere(self) -> None:
        text = (
            'quotes another doc\'s own "DEFERRED — ..." annotation, and separately '
            "this plan's own item is **DEFERRED** for real."
        )
        assert MOD._has_live_deferred_marker(text) is True

    def test_no_deferred_token_at_all(self) -> None:
        assert MOD._has_live_deferred_marker("Nothing to see here.") is False
