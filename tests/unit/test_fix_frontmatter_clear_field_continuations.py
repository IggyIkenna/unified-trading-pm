"""Unit tests for `_clear_field_continuations()` / `is_field_empty()` / `fix_active_plan()` in
scripts/plan-hygiene/fix_frontmatter.py.

Regression coverage for
plans/active/issues/fix_frontmatter_clear_field_continuations_deletes_valid_trailing_comment_2026_08_03.md:
the function's only guard against deleting a deliberate value was "does the first continuation
line start with a quote?" — it did not recognize a real single-line value immediately followed by
a `#`-prefixed comment (possibly wrapped across further indented comment-only lines), and deleted
the value along with the comment, silently reverting a dated operator ruling.

The todo-1 fix to `_clear_field_continuations()` alone was NECESSARY BUT NOT SUFFICIENT: the
todo-2 corpus audit found `is_field_empty()` — called immediately afterward at both call sites
(`execution_scope`, unconditional; `last_updated`, gated on `status: active`) — only inspects the
field's OWN line for a value, never the continuation `_clear_field_continuations()` just decided
to preserve. So even after the todo-1 fix, a bare `field:` line with a legitimate preserved
continuation still read as "empty" and got overwritten with the derived default on its own line,
leaving the real value dangling underneath as orphaned YAML-fold garbage — re-corrupting the field
on the very same fixer run that was supposed to have fixed it. This file also covers that fix.

Guards, most-important first:
  * `is_field_empty()` does not treat a bare field with a preserved continuation as empty.
  * End-to-end `fix_active_plan()` leaves the exact live-corpus shape untouched (both bugs closed).
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


def test_is_field_empty_false_when_continuation_carries_the_value() -> None:
    """Regression: a bare `field:` line is NOT empty when a value+comment continuation follows.

    Callers run `is_field_empty()` AFTER `_clear_field_continuations()` has already decided to
    preserve this exact continuation (it survived the guard), so the field's real value lives on
    the continuation line, not the bare own-line.
    """
    fm = _lines(
        [
            "execution_scope:",
            "  local-only # corrected 2026-08-02 (operator ruling on ...)",
            "priority: P1",
        ]
    )
    assert FF.is_field_empty(fm, "execution_scope") is False


def test_is_field_empty_false_for_quoted_multiline_scalar() -> None:
    fm = _lines(
        [
            "last_updated:",
            "  '2026-07-10 (was: 2026-06-27 -- corrected per operator ruling on X)'",
            "priority: P1",
        ]
    )
    assert FF.is_field_empty(fm, "last_updated") is False


def test_is_field_empty_true_for_genuinely_bare_field() -> None:
    """No continuation at all — still correctly reported as empty (defaults must still populate)."""
    fm = _lines(["execution_scope:", "priority: P1"])
    assert FF.is_field_empty(fm, "execution_scope") is True


def test_is_field_empty_true_when_own_line_blank() -> None:
    fm = _lines(["execution_scope: ", "priority: P1"])
    assert FF.is_field_empty(fm, "execution_scope") is True


def test_end_to_end_fix_active_plan_preserves_live_corpus_shape(tmp_path: Path) -> None:
    """Full `fix_active_plan()` pass on the exact
    worker_session_teardown_kills_long_running_pipeline_check_2026_07_27.md shape must be a no-op —
    proving `_clear_field_continuations()` + `is_field_empty()` no longer fight each other and
    re-corrupt the field within the same fixer run.
    """
    doc = tmp_path / "sample_issue_2026_08_03.md"
    doc.write_text(
        "---\n"
        "doc_type: issue\n"
        "title: sample\n"
        "summary: sample\n"
        "status: open\n"
        "nature: issue\n"
        "asset_group: [meta]\n"
        "stage: [meta]\n"
        "repos: []\n"
        "scope: [engineer]\n"
        "tags: []\n"
        "related: []\n"
        "created: 2026-08-03\n"
        "parent_epic: infrastructure_master\n"
        "assigned_vm: NA\n"
        "execution_scope:\n"
        "  local-only # corrected 2026-08-02 (operator ruling on\n"
        "  # some_decision_doc.md item 20, option A): was\n"
        "  # orchestrator-agent, contradicting assigned_vm: NA.\n"
        "priority: P1\n"
        "drift_direction: advance-code\n"
        "depends_on: []\n"
        "locked_by:\n"
        "locked_since:\n"
        "---\n"
        "\nbody\n"
    )
    before = doc.read_text()
    changed = FF.fix_active_plan(doc)
    after = doc.read_text()
    assert changed is False
    assert after == before
    assert "execution_scope:\n  local-only # corrected 2026-08-02" in after
