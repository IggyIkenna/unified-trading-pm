#!/usr/bin/env python3
# Epic: anthropic_per_task_actual_spend_and_account_calibration_2026_08_10
# Lifecycle: permanent (behavioural mechanism, not a one-off)
"""PostToolUse nudge + PreToolUse hard-block for a chain of consecutive same-tool
calls that could have been a single call.

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

WHY A HARD BLOCK TOO (2026-08-15, operator escalation)
--------------------------------------------------------
The PostToolUse-only nudge is advisory by construction — it fires AFTER the call has
already executed, so it can shape the NEXT decision at best. Measured result: a
compressed-context agent (or a sub-agent that never saw the earlier reminders) can and
does run the anti-pattern for 20-32+ calls in a row despite repeated nudges (see
FIRST_NUDGE_AT's own comment). The operator's direction: after the nudge has already
fired once and been ignored, this needs to become a hard rule, not another reminder —
"I don't like that it's advisory... it should be hard."

A PreToolUse hook CAN block — it runs before the call executes and can return
`permissionDecision: "deny"`. Registered under the SAME matcher as the PostToolUse nudge
below, reading the SAME per-session state file that already tracks same-message vs
round-tripped chains (see THE FALSE POSITIVE THIS AVOIDS, unchanged).

THE DEADLOCK THIS DESIGN AVOIDS — READ BEFORE CHANGING THE LOGIC
------------------------------------------------------------------
A blind "deny every call past N in a row" is actively harmful, not just imperfect: this
hook has NO semantic visibility into whether call N+1 genuinely depends on call N's
result (a real, common, LEGITIMATE pattern — e.g. polling a long-running job's status,
then querying based on what it reports). A hard denial with no escape hatch would
deadlock exactly that work: the agent has no way to "confirm this is really sequential"
to a stateless script, and can't synthesize a batch out of calls it hasn't decided on
yet. Blocking this class of call is a WORSE failure than the thing this hook exists to
prevent.

The escape hatch: a denial is a CHECKPOINT, not a wall. The very next attempt of the
same call is let through once (`GRACE_RETRIES_ALLOWED`) — the cost of a genuinely
sequential chain is one extra round-trip per checkpoint, not an unrecoverable stop. A
chain that keeps needing grace passes is charged one deny+retry every
`HARD_BLOCK_RENUDGE_EVERY` calls thereafter — annoying enough to be a real deterrent
against the anti-pattern (which the nudge alone wasn't), but never a dead end for
genuinely dependent work. This mirrors the same latency-based same-message detection
the nudge already uses — no new false-positive surface, just a stricter consequence for
the same, already-validated signal.

SAFETY
------
This runs on EVERY matched tool call in every session, local and on the AO VM. The
PostToolUse half must never break, slow, or block a tool call (it can't — the call has
already happened by then): every failure path exits 0 silently. The PreToolUse half is a
deliberate, narrow exception to "hooks never block" — see the escape-hatch design above
for why this one is safe to fail toward `allow`, not `deny`, on any internal error (a
missed block costs a re-explained rule; a wrongly-fired block that can't be recovered
from costs the agent's whole task). No network, no imports beyond the stdlib, one small
state file per session written next to that session's transcript.
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
# does not punish correct behaviour. Reused for both the nudge and the block: the block
# decision needs to make the identical same-message-vs-round-trip distinction the nudge's
# counter already makes.
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

# Hard-block thresholds (2026-08-15). Set to fire right after the FIRST re-nudge would —
# i.e. the agent has already been told once (at FIRST_NUDGE_AT) and kept going anyway.
# Same-file gets the same near-zero-false-positive treatment as its nudge counterpart:
# no grace headroom beyond the standard one retry, since a same-file Edit chain is the
# strongest signal this hook tracks.
HARD_BLOCK_AT = 3
HARD_BLOCK_RENUDGE_EVERY = 3
SAME_FILE_HARD_BLOCK_AT = 3
SAME_FILE_HARD_BLOCK_RENUDGE_EVERY = 3
# Exactly one free pass per checkpoint — see the deadlock-avoidance section above. This
# is not a tunable "how lenient" knob; it is the minimum needed to keep a denial from
# ever becoming an unrecoverable dead end for genuinely sequential work.
GRACE_RETRIES_ALLOWED = 1

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


def _block_reason(tool: str, run_length: int, *, same_file: str | None) -> str:
    scope = f"on the SAME file ({same_file})" if same_file else ""
    how = {
        "Bash": "chain them into ONE call with `&&`/`;`",
        "Read": "issue them as several `tool_use` blocks in a SINGLE message",
        "Grep": "issue them as several `tool_use` blocks in a SINGLE message",
        "Glob": "issue them as several `tool_use` blocks in a SINGLE message",
        "Edit": "use `replace_all: true`, or one Write, instead of serial Edits",
    }.get(tool, "issue them as several `tool_use` blocks in a SINGLE message")
    return (
        f"BATCHING HARD RULE: this would be the {run_length}th consecutive {tool} call {scope}, each in its own "
        f"turn, after you already got a nudge about this pattern. This is now BLOCKED, not advisory. "
        f"If the REMAINING calls in this chain do not depend on each other's results, {how} instead. "
        f"If this exact call genuinely depends on the immediately-prior call's result (a real, legitimate "
        f"pattern — e.g. polling a job's status then acting on what it reports), retry this SAME call once — "
        f"it will go through. A chain that keeps needing that retry every few calls is itself a signal to step "
        f"back and batch what you've learned so far into a plan instead of continuing to poll one call at a "
        f"time. SSOT: {_SSOT}"
    )


def _extract_file_path(tool: str, payload: dict[str, object]) -> str | None:
    if tool != "Edit":
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    fp = tool_input.get("file_path")
    return fp if isinstance(fp, str) and fp else None


def _chain_state(payload: dict[str, object], tool: str, now: float, prev: dict[str, object]) -> dict[str, object]:
    """Shared same-message-vs-round-trip accounting, used identically by both the
    PreToolUse block decision and the PostToolUse nudge/state-write — a block and a
    nudge must never disagree about what counts as a chain."""
    same_tool_as_prev = prev.get("tool") == tool
    gap = now - float(prev.get("ts") or 0.0) if same_tool_as_prev else None
    # A gap BELOW the window means the agent issued these in one message — it did the
    # right thing, so HOLD the counter rather than advancing it. Correct behaviour must
    # never be nudged or blocked; that is the whole design constraint (see module
    # docstring).
    same_message = gap is not None and gap < SAME_MESSAGE_WINDOW_SECONDS

    run_length = 1
    if same_tool_as_prev:
        run_length = int(prev.get("run") or 1) if same_message else int(prev.get("run") or 0) + 1

    file_path = _extract_file_path(tool, payload)
    same_file_as_prev = tool == "Edit" and file_path is not None and prev.get("file") == file_path
    file_run = 1
    if same_file_as_prev:
        file_run = int(prev.get("file_run") or 1) if same_message else int(prev.get("file_run") or 0) + 1

    return {
        "same_tool_as_prev": same_tool_as_prev,
        "same_message": same_message,
        "run_length": run_length,
        "file_path": file_path,
        "same_file_as_prev": same_file_as_prev,
        "file_run": file_run,
    }


def _should_block(
    *,
    prospective_run: int,
    threshold: int,
    renudge_every: int,
    prev_blocked_at: int,
    prev_grace_used_at: int,
    prev_run_for_grace_check: int,
) -> bool:
    """True iff this call should be DENIED. `prev_grace_used_at`/`prev_run_for_grace_check`
    implement the one-retry escape hatch: a call is exempted iff a grace pass was already
    offered at the CURRENT (unchanged, since a denied call never advances `run`) prior
    run count — i.e. this is recognizably the retry of the call that was just denied."""
    if prospective_run < threshold:
        return False
    if prev_grace_used_at == prev_run_for_grace_check:
        return False  # this is the one free retry — let it through
    # already blocked+graced recently; give real headroom before the next checkpoint
    return not (prev_blocked_at != 0 and prospective_run - prev_blocked_at < renudge_every)


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return

    # Default missing hook_event_name to PostToolUse — this hook's sole event before the
    # 2026-08-15 PreToolUse block was added, and the settings.json-registered contract a
    # caller with no explicit event field (older test payloads, any harness variant that
    # omits it) should still get the nudge-only, never-block behavior it always had.
    event = payload.get("hook_event_name") or "PostToolUse"
    tool = payload.get("tool_name") or ""
    if tool not in CHAINABLE_TOOLS:
        # A different tool breaks the chain — record that so the next same-tool call
        # starts a fresh run rather than resuming a stale one. Only PostToolUse owns
        # writes (see module docstring: PreToolUse is read-mostly).
        if event == "PostToolUse":
            _reset(payload, tool)
        return

    path = _state_path(str(payload.get("transcript_path") or ""), str(payload.get("session_id") or ""))
    if path is None:
        return

    now = time.time()
    prev = _load(path)
    chain = _chain_state(payload, tool, now, prev)

    if event == "PreToolUse":
        _handle_pre(prev, chain, path, tool)
        return
    if event == "PostToolUse":
        _handle_post(prev, chain, path, tool, now)
        return
    # Unknown event — do nothing rather than guess (fail toward inaction, per SAFETY).


def _handle_pre(prev: dict[str, object], chain: dict[str, object], path: Path, tool: str) -> None:
    """Read-mostly: decides allow/deny for the call about to run. Writes ONLY a grace
    marker when it denies, so the retry can be recognized (see _should_block's
    docstring) — never touches run/file_run/fired_at, which stay PostToolUse's alone."""
    prospective_run = int(chain["run_length"])  # type: ignore[arg-type]
    same_tool_as_prev = bool(chain["same_tool_as_prev"])
    same_message = bool(chain["same_message"])
    file_path = chain["file_path"]
    same_file_as_prev = bool(chain["same_file_as_prev"])
    prospective_file_run = int(chain["file_run"])  # type: ignore[arg-type]

    prev_run = int(prev.get("run") or 0)

    # Same-file is the SOLE block signal for an Edit call with a resolvable path — never
    # evaluated alongside the general same-tool check. A same-file Edit chain is always
    # ALSO a same-tool chain (every Edit shares tool="Edit"), so without this exclusivity
    # a call that clears the file-specific grace check would immediately fall through and
    # get independently blocked by the general check on the very next line — the agent
    # would see two unrelated-looking denials for one underlying pattern. This is the
    # block-decision analog of the nudge's own "only one message, same-file wins"
    # priority rule; the nudge tolerates dual bookkeeping because it never double-fires
    # user-visible consequences, a block cannot afford the same looseness.
    if tool == "Edit" and file_path is not None:
        if not (same_file_as_prev and not same_message):
            return  # fresh file, or same-message batch — never blocked
        blocked = _should_block(
            prospective_run=prospective_file_run,
            threshold=SAME_FILE_HARD_BLOCK_AT,
            renudge_every=SAME_FILE_HARD_BLOCK_RENUDGE_EVERY,
            prev_blocked_at=int(prev.get("file_blocked_at") or 0),
            prev_grace_used_at=int(prev.get("file_grace_used_at") or -1),
            prev_run_for_grace_check=int(prev.get("file_run") or 0),
        )
        if blocked:
            _save_grace_marker(path, prev, file_grace_used_at=int(prev.get("file_run") or 0))
            _deny(_block_reason(tool, prospective_file_run, same_file=str(file_path)))
        return

    if same_tool_as_prev and not same_message:
        blocked = _should_block(
            prospective_run=prospective_run,
            threshold=HARD_BLOCK_AT,
            renudge_every=HARD_BLOCK_RENUDGE_EVERY,
            prev_blocked_at=int(prev.get("blocked_at") or 0),
            prev_grace_used_at=int(prev.get("grace_used_at") or -1),
            prev_run_for_grace_check=prev_run,
        )
        if blocked:
            _save_grace_marker(path, prev, grace_used_at=prev_run)
            _deny(_block_reason(tool, prospective_run, same_file=None))
            return


def _handle_post(prev: dict[str, object], chain: dict[str, object], path: Path, tool: str, now: float) -> None:
    run_length = int(chain["run_length"])  # type: ignore[arg-type]
    same_tool_as_prev = bool(chain["same_tool_as_prev"])
    file_path = chain["file_path"]
    same_file_as_prev = bool(chain["same_file_as_prev"])
    file_run = int(chain["file_run"])  # type: ignore[arg-type]

    fired_at = int(prev.get("fired_at") or 0) if same_tool_as_prev else 0
    should_fire = run_length >= FIRST_NUDGE_AT and (fired_at == 0 or run_length - fired_at >= RENUDGE_EVERY)

    file_fired_at = int(prev.get("file_fired_at") or 0) if same_file_as_prev else 0
    same_file_should_fire = (
        file_path is not None
        and file_run >= SAME_FILE_NUDGE_AT
        and (file_fired_at == 0 or file_run - file_fired_at >= RENUDGE_EVERY)
    )

    # A call that actually reached PostToolUse was, by definition, allowed through —
    # either it never crossed the block threshold, or it just consumed its one grace
    # retry. Record `blocked_at`/`file_blocked_at` whenever this run_length is at/past
    # the hard-block threshold so the NEXT PreToolUse checkpoint knows how much
    # headroom remains, mirroring `fired_at`'s own renudge bookkeeping.
    blocked_at = int(prev.get("blocked_at") or 0) if same_tool_as_prev else 0
    if run_length >= HARD_BLOCK_AT and (blocked_at == 0 or run_length - blocked_at >= HARD_BLOCK_RENUDGE_EVERY):
        blocked_at = run_length
    file_blocked_at = int(prev.get("file_blocked_at") or 0) if same_file_as_prev else 0
    if (
        file_path is not None
        and file_run >= SAME_FILE_HARD_BLOCK_AT
        and (file_blocked_at == 0 or file_run - file_blocked_at >= SAME_FILE_HARD_BLOCK_RENUDGE_EVERY)
    ):
        file_blocked_at = file_run

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
            "blocked_at": blocked_at,
            "file_blocked_at": file_blocked_at,
            # Grace markers are consumed by a successful PostToolUse — clear them so a
            # LATER, unrelated call at the same run count can't spuriously inherit a
            # stale grace pass.
            "grace_used_at": -1,
            "file_grace_used_at": -1,
        },
    )

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


def _deny(reason: str) -> None:
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )


def _save_grace_marker(
    path: Path, prev: dict[str, object], *, grace_used_at: int | None = None, file_grace_used_at: int | None = None
) -> None:
    """Denial-time write: ONLY the grace marker, nothing else — run/file_run/fired_at
    stay exactly as PostToolUse last left them, since the call being denied never
    executed and must not appear to have advanced the chain."""
    merged = dict(prev)
    if grace_used_at is not None:
        merged["grace_used_at"] = grace_used_at
    if file_grace_used_at is not None:
        merged["file_grace_used_at"] = file_grace_used_at
    _save(path, merged)


def _reset(payload: dict[str, object], tool: str) -> None:
    path = _state_path(str(payload.get("transcript_path") or ""), str(payload.get("session_id") or ""))
    if path is not None:
        _save(
            path,
            {
                "tool": tool,
                "run": 0,
                "ts": time.time(),
                "fired_at": 0,
                "file": None,
                "file_run": 0,
                "file_fired_at": 0,
                "blocked_at": 0,
                "file_blocked_at": 0,
                "grace_used_at": -1,
                "file_grace_used_at": -1,
            },
        )


def _load(path: Path) -> dict[str, object]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _save(path: Path, state: dict[str, object]) -> None:
    """Best-effort, atomic-ish. A lost write costs at most one missed nudge/block, so it
    is never worth raising into the agent's tool call."""
    try:
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(state))
        os.replace(tmp, path)
    except Exception:
        pass


if __name__ == "__main__":
    # PreToolUse is the one deliberate exception to "never affect the call" — see the
    # module docstring's SAFETY section for why it still fails toward allow, not deny,
    # on any internal error (contextlib.suppress means an exception mid-_handle_pre
    # simply skips emitting a deny decision, which defaults to allow).
    with contextlib.suppress(Exception):
        main()
    sys.exit(0)
