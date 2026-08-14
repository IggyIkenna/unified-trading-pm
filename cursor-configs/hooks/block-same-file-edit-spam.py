#!/usr/bin/env python3
# Epic: anthropic_per_task_actual_spend_and_account_calibration_2026_08_10
# Lifecycle: permanent (behavioural mechanism, not a one-off)
"""PreToolUse guardrail: hard-block the Nth consecutive round-tripped Edit call
on the SAME file (operator ask 2026-08-14, after batching-nudge.py's own
same-file nudge measured real but insufficient improvement: "yes please lets
push further if we spot cases where we can").

WHY THIS IS THE ONE SAFE CASE TO ACTUALLY BLOCK (READ BEFORE RAISING/LOWERING
BLOCK_THRESHOLD)
------------------------------------------------------------------------------
batching-nudge.py's own docstring explains why blocking Bash/Read/Grep chains
would be unsafe: a later call in those chains sometimes genuinely depends on
an earlier one's tool_result. Same-file Edit is different in one specific way
that makes a HIGH-THRESHOLD block defensible: a later Edit's old_string/
new_string are derived from the file's own ON-DISK CONTENT, never from what
a prior Edit call RETURNED — so there is no tool_result dependency chain to
break. The threshold is still set well above the nudge's (2) rather than
matching it, because "genuinely needed to see something new before the next
edit" is still real and common (edit -> run test -> discover a second fix ->
edit again is a completely normal 2-3-round pattern) — this only fires once
that stops being a plausible explanation for the repetition.

THE ESCAPE HATCH — WHY THIS CANNOT WEDGE AN AGENT
--------------------------------------------------
`Write` (rewrite the whole file with final content) is ALWAYS a valid way
through a block — the agent already knows the file's content from having
edited it already, or can Read it fresh. Switching to `Write` is a DIFFERENT
tool than `Edit`, which naturally resets batching-nudge.py's same-file state
via its own `_reset()` path the next time any tool fires — so a block cannot
permanently wedge repeat attempts on that file; it can only be escaped WITH
the fix we actually want (fewer, larger writes), never by retrying the exact
same pattern.

`replace_all: true` is exempt from the count entirely — it IS the requested
remediation, and must never itself trip the guard it exists to satisfy.

STATE SOURCE
------------
Deliberately reads the SAME per-session state file batching-nudge.py already
writes (see that file's `_state_path`) rather than tracking independently —
PreToolUse fires BEFORE the tool executes, so by the time this runs for the
Nth attempt, the (N-1)th attempt's PostToolUse hook has already recorded
`file`/`file_run` for this exact file. Deliberately NOT imported as a shared
module from batching-nudge.py (small, ~10-line duplication accepted) to avoid
re-touching and re-shipping that already-live hook for this addition — this
file's own state-path logic MUST stay byte-identical to batching-nudge.py's
or the two will silently stop agreeing on where the state file lives.

SAFETY
------
This runs on EVERY Edit call in every session, local and on the AO VM. Fails
OPEN on any parse/state error — a hook bug must never wedge a worker. Exit 2 +
stderr is the proven fleet-wide block contract (see scripts/hooks/
block_destructive_commands.py in agent-orchestrator): the agent receives the
reason and continues its turn, the session does not die.

Registered fleet-wide via the TEAM-shared cursor-configs/settings.json
(PreToolUse, matcher="Edit"), same mechanism as block_destructive_commands.py.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

# Materially higher than batching-nudge.py's FIRST_NUDGE_AT/SAME_FILE_NUDGE_AT
# (both 2) — see module docstring for why a block needs a much higher bar than
# an advisory, reversible nudge.
BLOCK_THRESHOLD = 5

# Must stay numerically identical to batching-nudge.py's own constant — both
# hooks need to agree on what counts as "the same message" vs a real
# round-trip, since this hook reads state THAT hook writes.
SAME_MESSAGE_WINDOW_SECONDS = 2.0

_BLOCK_MESSAGE = (
    "BLOCKED by orchestrator guardrail: this would be the {run}th consecutive round-tripped "
    "Edit call on the SAME file ({file_path}), each costing a full model round-trip and cached-"
    "prefix re-read.\n"
    "Same-file edits are almost NEVER dependent on a prior edit's tool_result — the next "
    "old_string/new_string come from the file's own on-disk content, not from what the last "
    "Edit call returned. Combine the remaining changes into ONE `replace_all: true` Edit, or a "
    "single `Write` with the final file content (Write is always a valid escape hatch here — you "
    "already know the file's content from having edited it, or can Read it fresh).\n"
    "If a later change genuinely could not have been known until this exact moment (e.g. a test "
    "you just ran surfaced it), that is a real exception — say so and proceed with a NEW file via "
    "a fresh Edit; this guard only fires on the file/session pair it already saw {run}+ times.\n"
    "SSOT: /codex/06-coding-standards/tool-call-batching.md\n"
)


def _state_path(transcript_path: str, session_id: str) -> Path | None:
    """Byte-identical to batching-nudge.py's own — see module docstring for why this is
    deliberately duplicated rather than imported."""
    if not transcript_path:
        return None
    parent = Path(transcript_path).parent
    if not parent.is_dir():
        return None
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")[:64] or "unknown"
    return parent / f".batch-nudge-{safe}.json"


def _load(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def main() -> int:
    try:
        raw = sys.stdin.read()
        payload: dict[str, object] = json.loads(raw) if raw.strip() else {}
    except Exception:
        # Fail OPEN: a malformed hook event is a harness bug, not something to wedge on.
        return 0

    if payload.get("tool_name") != "Edit":
        return 0

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return 0
    file_path = tool_input.get("file_path")
    if not isinstance(file_path, str) or not file_path:
        return 0
    if tool_input.get("replace_all") is True:
        # This IS the requested remediation — must never itself trip the guard.
        return 0

    path = _state_path(str(payload.get("transcript_path") or ""), str(payload.get("session_id") or ""))
    if path is None:
        return 0

    prev = _load(path)
    if prev.get("tool") != "Edit" or prev.get("file") != file_path:
        return 0

    file_run = prev.get("file_run")
    if not isinstance(file_run, int) or file_run < BLOCK_THRESHOLD:
        return 0

    # A gap below the window means the LAST recorded call was part of an already-batched
    # same-message run — the state is stale relative to a genuinely fresh attempt is not
    # the failure mode we're guarding; only a real round-trip should ever reach here, but
    # this is a defensive re-check (never trust a single signal for a fleet-wide block).
    prev_ts = prev.get("ts")
    if isinstance(prev_ts, (int, float)) and (time.time() - float(prev_ts)) < SAME_MESSAGE_WINDOW_SECONDS:
        return 0

    sys.stderr.write(_BLOCK_MESSAGE.format(run=file_run + 1, file_path=file_path))
    return 2


if __name__ == "__main__":
    sys.exit(main())
