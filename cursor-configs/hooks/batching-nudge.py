#!/usr/bin/env python3
# Epic: anthropic_per_task_actual_spend_and_account_calibration_2026_08_10
# Lifecycle: permanent (behavioural mechanism, not a one-off)
"""PostToolUse hook: nudge IN-LOOP when an agent is running a chain of
consecutive same-tool calls that could have been a single call.

WHY A HOOK AND NOT A RULE
-------------------------
A written rule has already been tried on exactly this problem. `SUB_AGENT_
MANDATORY_RULES.md` has carried a batching directive since ~2026-08-05, alongside
`/plans/active/issues/ao_worker_unbatched_tool_calls_inflate_turn_count_2026_08_05.md`
which measured only ~11% of fleet turns batching more than one call. Five days later a
controlled measurement found 57.3% of ALL calls still sitting in collapsible same-tool
chains (2026-08-10). Restating the rule a third time is not a plan.

The difference here is TIMING: a rule is read once at session start and competes with
everything else in context, whereas this fires at the moment the behaviour happens, with
the actual count attached. Each collapsed chain saves one full cached-prefix re-read
(405,833 tokens measured, mean) AND one model round-trip (10.5s median gap), so this is
a throughput lever as much as a cost one.

THE FALSE POSITIVE THIS AVOIDS — READ BEFORE CHANGING THE LOGIC
---------------------------------------------------------------
The obvious implementation — count consecutive calls carrying the same tool name — is
WRONG, and wrong in the worst possible direction: it fires hardest at agents that are
already doing the right thing. Four `Read` calls issued as four `tool_use` blocks in ONE
message (correct, one round-trip) produce exactly the same sequence of PostToolUse events
as four `Read` calls across four separate turns (the anti-pattern, four round-trips).
Nudging the first agent would train it out of the behaviour we want.

They are separable by LATENCY. Tool calls inside one message execute back-to-back in
milliseconds; calls in separate turns are separated by a full model round-trip — measured
median 10.5s, and the short tail is still comfortably above a second. So a gap below
``SAME_MESSAGE_WINDOW_SECONDS`` is treated as evidence of correct batching (it does NOT
advance the chain counter), and only calls separated by a real round-trip count toward a
chain. The threshold is deliberately generous: mistaking a slow same-message batch for a
chain is a false nudge, while mistaking a very fast round-trip for a batch merely misses
one — the asymmetry favours silence.

SAFETY
------
This runs on EVERY matched tool call in every session, local and on the AO VM. It must
never break, slow, or block a tool call: every failure path exits 0 silently, no network,
no imports beyond the stdlib, and one small state file per session written next to that
session's transcript.
"""

from __future__ import annotations

import contextlib
import json
import os
import sys
import time
from pathlib import Path

# Tools where a consecutive run is genuinely collapsible into one call. Bash dominates
# (52.8% of all measured calls, 69% of them inside a chain), but serial Reads/Greps and
# repeated Edits on one file are the same waste. Deliberately EXCLUDES tools where
# sequencing is usually meaningful or batching is not expressible.
CHAINABLE_TOOLS = {"Bash", "Read", "Grep", "Glob", "Edit"}

# Below this gap, two calls were almost certainly issued in the SAME message — i.e. the
# agent already batched them. See the module docstring: this is the whole reason the hook
# does not punish correct behaviour.
SAME_MESSAGE_WINDOW_SECONDS = 2.0

# Nudge at the 2nd round-tripped call in a row, then every 5th. Lowered from 3->2
# 2026-08-14 (operator ask, after a real before/after measurement showed the 3-call
# threshold left multi-tool-turn% at 4.3-5.7%, far short of the ~50% target) — catch the
# pattern one call earlier, before it is already locked in. Firing on every call would be
# noise the agent learns to ignore; firing once would be lost in a run of 32 (runs of
# 20/23/26/28/32 were all observed in one 4h25m window).
FIRST_NUDGE_AT = 2
RENUDGE_EVERY = 5

# Same-file repeated Edits are a STRONGER, near-zero-false-positive signal than "same
# tool" alone (operator 2026-08-14: "file edits we can batch pretty much always... still
# see us edit same file 2,3,4,5 times") — unlike Bash/Read/Grep, where a later call
# sometimes genuinely depends on an earlier one's result, a later Edit on the SAME file
# almost never needs the PRIOR edit's tool_result to construct its own old_string/
# new_string (both are known from the file's on-disk content, not from what the edit
# tool returned). So this fires EARLIER than the general chain nudge, and with a more
# specific, harder-to-ignore message naming the actual file.
SAME_FILE_NUDGE_AT = 2

_SSOT = "/codex/06-coding-standards/tool-call-batching.md"


def _state_path(transcript_path: str, session_id: str) -> Path | None:
    """State file next to the session's own transcript — same convention as
    `context-threshold-nudge.sh`'s sentinel, so it is cleaned up with the session and
    never collides between concurrent slots. Returns None when the harness gave us
    nowhere safe to write (in which case the hook simply does nothing)."""
    if not transcript_path:
        return None
    parent = Path(transcript_path).parent
    if not parent.is_dir():
        return None
    safe = "".join(c for c in session_id if c.isalnum() or c in "-_")[:64] or "unknown"
    return parent / f".batch-nudge-{safe}.json"


def _advice(tool: str, run_length: int) -> str:
    how = {
        "Bash": "chain them into ONE call with `&&` (stop on failure) or `;` (run regardless)",
        "Read": "issue them as several `tool_use` blocks in a SINGLE message",
        "Grep": "issue them as several `tool_use` blocks in a SINGLE message",
        "Glob": "issue them as several `tool_use` blocks in a SINGLE message",
        "Edit": "use `replace_all: true`, or one Write, instead of serial Edits",
    }.get(tool, "issue them as several `tool_use` blocks in a SINGLE message")
    return (
        f"BATCHING: that was {run_length} consecutive {tool} calls, each in its own turn. "
        f"Every one re-read the entire cached prompt prefix (~406k tokens, measured) and cost a full model "
        f"round-trip (~10.5s median), so this is throughput as much as cost. "
        f"For the remaining {tool} calls that do NOT depend on each other's results, {how}. "
        f"Calls whose input genuinely depends on a previous result — and any check that authorises a "
        f"destructive action — must stay sequential; this is not a request to guess. SSOT: {_SSOT}"
    )


def _same_file_advice(file_path: str, run_length: int) -> str:
    return (
        f"BATCHING: that was {run_length} consecutive Edit calls on the SAME file ({file_path}), each in its "
        f"own turn. Same-file edits are almost NEVER dependent on each other's tool_result — the next edit's "
        f"old_string/new_string are known from the file's own content, not from what the prior edit returned. "
        f"Combine them into one `replace_all: true` Edit or a single `Write` with the final content. Every "
        f"separate turn re-read the entire cached prompt prefix (~406k tokens, measured) and cost a full model "
        f"round-trip (~10.5s median). SSOT: {_SSOT}"
    )


def _extract_file_path(tool: str, payload: dict[str, object]) -> str | None:
    if tool != "Edit":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    fp = tool_input.get("file_path")
    return fp if isinstance(fp, str) and fp else None


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    tool = payload.get("tool_name") or ""
    if tool not in CHAINABLE_TOOLS:
        # A different tool breaks the chain — record that so the next same-tool call
        # starts a fresh run rather than resuming a stale one.
        _reset(payload, tool)
        return

    path = _state_path(payload.get("transcript_path") or "", payload.get("session_id") or "")
    if path is None:
        return

    now = time.time()
    prev = _load(path)
    same_tool_as_prev = prev.get("tool") == tool
    gap = now - float(prev.get("ts") or 0.0) if same_tool_as_prev else None
    # A gap BELOW the window means the agent issued these in one message — it did the
    # right thing, so HOLD the counter rather than advancing it. Correct behaviour must
    # never be nudged; that is the whole design constraint (see module docstring).
    same_message = gap is not None and gap < SAME_MESSAGE_WINDOW_SECONDS

    run_length = 1
    if same_tool_as_prev:
        run_length = int(prev.get("run") or 1) if same_message else int(prev.get("run") or 0) + 1

    file_path = _extract_file_path(tool, payload)
    same_file_as_prev = tool == "Edit" and file_path is not None and prev.get("file") == file_path
    file_run = 1
    if same_file_as_prev:
        file_run = int(prev.get("file_run") or 1) if same_message else int(prev.get("file_run") or 0) + 1

    fired_at = int(prev.get("fired_at") or 0) if same_tool_as_prev else 0
    should_fire = run_length >= FIRST_NUDGE_AT and (fired_at == 0 or run_length - fired_at >= RENUDGE_EVERY)

    file_fired_at = int(prev.get("file_fired_at") or 0) if same_file_as_prev else 0
    same_file_should_fire = (
        file_path is not None
        and file_run >= SAME_FILE_NUDGE_AT
        and (file_fired_at == 0 or file_run - file_fired_at >= RENUDGE_EVERY)
    )

    _save(
        path,
        {
            "tool": tool,
            "run": run_length,
            "ts": now,
            "fired_at": run_length if should_fire else fired_at,
            "file": file_path,
            "file_run": file_run,
            "file_fired_at": file_run if same_file_should_fire else file_fired_at,
        },
    )

    # Same-file takes priority when both would fire — it's the stronger, more specific
    # signal (see SAME_FILE_NUDGE_AT's own comment); only one additionalContext string
    # can be returned per call, so pick the more actionable one rather than concatenating.
    advice: str | None = None
    if same_file_should_fire and file_path is not None:
        advice = _same_file_advice(file_path, file_run)
    elif should_fire:
        advice = _advice(tool, run_length)

    if advice is not None:
        json.dump(
            {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": advice}},
            sys.stdout,
        )


def _reset(payload: dict[str, object], tool: str) -> None:
    path = _state_path(str(payload.get("transcript_path") or ""), str(payload.get("session_id") or ""))
    if path is not None:
        _save(
            path,
            {"tool": tool, "run": 0, "ts": time.time(), "fired_at": 0, "file": None, "file_run": 0, "file_fired_at": 0},
        )


def _load(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save(path: Path, state: dict[str, object]) -> None:
    """Best-effort, atomic-ish. A lost write costs at most one missed nudge, so it is
    never worth raising into the agent's tool call."""
    try:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state))
        os.replace(tmp, path)
    except Exception:
        pass


if __name__ == "__main__":
    # Never let this hook fail a tool call: swallow everything, always exit 0.
    with contextlib.suppress(Exception):
        main()
    sys.exit(0)
