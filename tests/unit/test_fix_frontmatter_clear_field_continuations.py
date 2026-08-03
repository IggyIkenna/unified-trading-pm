"""Unit tests for `_clear_field_continuations()` in scripts/plan-hygiene/fix_frontmatter.py.

Regression coverage for
plans/active/issues/fix_frontmatter_clear_field_continuations_deletes_valid_trailing_comment_2026_08_03.md:
the function's only guard against deleting a deliberate value was "does the first continuation
line start with a quote?" — it did not recognize a real single-line value immediately followed by
a `#`-prefixed comment (possibly wrapped across further indented comment-only lines), and deleted
the value along with the comment, silently reverting a dated operator ruling.

Guards, most-important first:
  * The exact live-corpus shape (value + wrapped trailing comment) is preserved, not deleted.
  * The pre-existing quoted-multiline-scalar guard still works (no regression).
  * The pre-existing accidental-fold-garbage strip still works (no regression).
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


def _lines(fm_fields: list[str]) -> list[str]:
    return [f"{line}\n" for line in fm_fields]


def test_value_plus_wrapped_trailing_comment_is_preserved() -> None:
    """The exact worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md shape."""
    fm = _lines(
        [
            "execution_scope:",
            "  local-only # corrected 2026-08-02 (operator ruling on",
            "  # plan_reconcile_parked_operator_decisions_2026_08_02.md na-eligibility-audit item 20, option A): was",
            "  # orchestrator-agent, contradicting assigned_vm: NA. Stays NA until the shared-host RAM "
            "exhaustion mechanism",
            "  # (condition mdps-e2e-shared-host-teardown-fixed) is also closed, not just the partial "
            "root-cause on todo 1.",
            "priority: P1",
        ]
    )
    result = FF._clear_field_continuations(fm, "execution_scope")
    joined = "".join(result)
    assert "  local-only # corrected 2026-08-02 (operator ruling on\n" in joined
    assert "orchestrator-agent, contradicting assigned_vm: NA" in joined
    assert result[-1] == "priority: P1\n"


def test_quoted_multiline_scalar_still_preserved() -> None:
    """Pre-existing guard: an intentional quoted multiline scalar must still survive untouched."""
    fm = _lines(
        [
            "last_updated:",
            "  '2026-07-10 (was: 2026-06-27 -- corrected per operator ruling on X)'",
            "priority: P1",
        ]
    )
    result = FF._clear_field_continuations(fm, "last_updated")
    joined = "".join(result)
    assert "'2026-07-10 (was: 2026-06-27 -- corrected per operator ruling on X)'" in joined
    assert result[-1] == "priority: P1\n"


def test_accidental_fold_garbage_still_stripped() -> None:
    """Pre-existing behavior: plain-scalar YAML-fold garbage with no quote and no comment strips clean."""
    fm = _lines(
        [
            "last_updated:",
            "  2026-07-18 changelog: did X, then Y, then Z, a runaway multi-line",
            "  prose blob accidentally folded into this field by an earlier bug",
            "priority: P1",
        ]
    )
    result = FF._clear_field_continuations(fm, "last_updated")
    assert result == ["last_updated:\n", "priority: P1\n"]


def test_bare_field_with_no_continuation_is_untouched() -> None:
    """A field with an inline value and no continuation lines at all passes through unchanged."""
    fm = _lines(["execution_scope: orchestrator-agent", "priority: P1"])
    result = FF._clear_field_continuations(fm, "execution_scope")
    assert result == fm
