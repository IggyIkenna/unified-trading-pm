# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Unit tests for check_ao_dispatch_gap.py.

Covers the four known trigger shapes from
plans/active/issues/ao_silently_non_dispatchable_todos_have_no_visibility_gate_2026_08_08.md via
the pure `classify()` function against synthetic (block, dispatchable_descs) pairs -- no live
agent-orchestrator .venv needed (that dependency is exercised separately by the live-corpus smoke
test below, which auto-skips when the sibling repo/.venv isn't present).
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_HERE = Path(__file__).parent
sys.path.insert(0, str(_HERE))

from check_ao_dispatch_gap import _iter_disk_open_todos, classify  # type: ignore[import-not-found]

_PM_ROOT = _HERE.parents[1]
_WORKSPACE_ROOT = _PM_ROOT.parent


def test_dispatchable_todo_is_never_flagged() -> None:
    """A todo present in the dispatchable set is not a gap, regardless of its text."""
    desc = "**Some todo.** BLOCKED-CREDENTIALS mentioned in passing."
    assert classify(desc, f"- [ ] {desc}", {desc}) is None


def test_shape1_resolved_retag_is_not_misclassified_once_fixed() -> None:
    """ao_non_dispatchable_regex_swallows_resolved_retags_2026_07_29: 'was BLOCKED-X' resolution
    language. Once regen's own stale-prefix fix includes it in the dispatchable set, this gate
    must not re-flag it as a gap at all."""
    desc = "**Do the thing.** Prior BLOCKED-CREDENTIALS framing was retired 2026-07-29."
    block = f"- [ ] {desc}\n      resolved, no longer gated."
    assert classify(desc, block, {desc}) is None


def test_shape2_unrecognized_token_variant_still_reads_as_declared() -> None:
    """blocked_prerequisites_marker_not_in_non_dispatchable_regex_2026_07_28: BLOCKED-PREREQUISITES
    isn't in regen's own hardcoded alternation, so regen may dispatch it when it shouldn't. If this
    gate ever sees it excluded (a different path), it must still recognise the generic BLOCKED-<TOKEN>
    shape rather than needing its own per-token allow-list widened the same way regen's did."""
    desc = "**Fix the odds-api credential.**"
    block = f"- [ ] {desc}\n      BLOCKED-PREREQUISITES: waiting on the upstream secret rotation."
    assert classify(desc, block, set()) == "declared"


def test_shape3_marker_then_resolution_word_order_is_not_misclassified_once_fixed() -> None:
    """defi_batch8_finalize_gate_bypass_missing_upstream_task_2026_08_02: 'BLOCKED-CREDENTIALS ...
    was retired' (marker BEFORE the resolution keyword, not after). Once regen's suffix-lookback
    fix includes it, this gate must not re-flag it."""
    desc = "**Wire the gate.** Original BLOCKED-CREDENTIALS framing was retired 2026-07-29."
    block = f"- [ ] {desc}"
    assert classify(desc, block, {desc}) is None


def test_shape4_negated_marker_mention_is_accidental_not_declared() -> None:
    """The 2026-08-08 sports-Betfair trigger: the todo's own text contains the marker string only
    to DISCLAIM it ('Do NOT mark this BLOCKED-CREDENTIALS'). A naive substring match on
    BLOCKED-<TOKEN> would misclassify this as a deliberate hold -- the exact false-positive this
    gate exists to catch. If excluded, it must classify as accidental, not declared."""
    desc = "**Scaffold the Betfair Exchange consumer, credential-free.**"
    block = (
        f"- [ ] {desc}\n"
        "      Fully AO-completable with no operator step. Do NOT mark this BLOCKED-CREDENTIALS --\n"
        "      the credential ask is a separate, already-tracked item and must not gate the scaffold."
    )
    assert classify(desc, block, set()) == "accidental"


def test_iter_disk_open_todos_matches_regen_description_extraction() -> None:
    """The disk-side description text must line up character-for-character with what regen's own
    _UNCHECKED_RE captures (both strip the same way) -- otherwise every live-corpus comparison
    would false-positive as a gap purely from text-normalisation drift."""
    text = (
        "---\nstatus: active\n---\n\n- [ ] [SCRIPT] P1. **Do a thing.** More text.\n      continuation.\n- [x] done\n"
    )
    todos = _iter_disk_open_todos(text)
    assert len(todos) == 1
    desc, block = todos[0]
    assert desc == "[SCRIPT] P1. **Do a thing.** More text."
    assert "continuation." in block


def test_live_corpus_gate_runs_clean_or_skips() -> None:
    """The gate must exit 0 against the live corpus right now (baseline absorbs any pre-existing
    debt) -- or skip cleanly when the agent-orchestrator sibling/.venv isn't present (e.g. CI)."""
    result = subprocess.run(
        [sys.executable, str(_HERE / "check_ao_dispatch_gap.py"), "--workspace-root", str(_WORKSPACE_ROOT), "--quiet"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
