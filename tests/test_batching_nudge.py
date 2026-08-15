"""Tests for cursor-configs/hooks/batching-nudge.py.

This hook runs on EVERY matched tool call in every session, local and on the AO VM, so
two properties matter more than the nudge itself: it must never break a tool call, and it
must never fire at an agent that is already batching correctly.

That second one is the whole design risk. Four Reads in ONE message and four Reads across
four turns produce identical PostToolUse event sequences; only the inter-call latency
separates them. If the hook got that backwards it would train agents OUT of the behaviour
it exists to encourage — so the same-message cases below are the point of this file, not
an edge case in it.

Driven through the real stdin/stdout/exit-code contract (subprocess, not an import),
because that contract is what the harness actually depends on.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

HOOK = Path(__file__).resolve().parents[1] / "cursor-configs" / "hooks" / "batching-nudge.py"


def run_hook(
    transcript: Path,
    tool: str,
    session_id: str = "sess-1",
    *,
    event: str = "PostToolUse",
    file_path: str | None = None,
) -> str:
    payload: dict[str, object] = {
        "hook_event_name": event,
        "session_id": session_id,
        "transcript_path": str(transcript),
        "tool_name": tool,
    }
    if file_path is not None:
        payload["tool_input"] = {"file_path": file_path}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, f"hook must never exit non-zero (stderr: {proc.stderr})"
    return proc.stdout


def denied(out: str) -> bool:
    if not out.strip():
        return False
    payload = json.loads(out)
    return payload["hookSpecificOutput"].get("permissionDecision") == "deny"


def nudged(out: str) -> bool:
    if not out.strip():
        return False
    payload = json.loads(out)
    return "BATCHING:" in payload["hookSpecificOutput"]["additionalContext"]


def backdate(transcript: Path, session_id: str = "sess-1", seconds: float = 30.0) -> None:
    """Age the recorded timestamp so the NEXT call reads as a separate turn.

    Cheaper and more deterministic than really sleeping past the same-message window,
    and it exercises the same branch.
    """
    state = transcript.parent / f".batch-nudge-{session_id}.json"
    data = json.loads(state.read_text())
    data["ts"] = time.time() - seconds
    state.write_text(json.dumps(data))


@pytest.fixture
def transcript(tmp_path: Path) -> Path:
    p = tmp_path / "session.jsonl"
    p.write_text("")
    return p


# ---------------------------------------------------------------------------
# The false positive that would make this hook actively harmful
# ---------------------------------------------------------------------------


def test_same_message_batch_is_never_nudged(transcript: Path) -> None:
    """Five Reads issued as five tool_use blocks in ONE message — the CORRECT behaviour.
    Back-to-back in milliseconds, so no round-trip separates them and the chain counter
    must not advance. Nudging here would punish exactly what we want."""
    outs = [run_hook(transcript, "Read") for _ in range(5)]
    assert not any(nudged(o) for o in outs)


def test_round_tripped_chain_is_nudged(transcript: Path) -> None:
    """The same calls, each in its own turn — the anti-pattern. Fires at the 2nd
    round-tripped call (FIRST_NUDGE_AT, lowered 3->2 2026-08-14 per operator measurement)."""
    run_hook(transcript, "Read")  # 1st — below threshold
    backdate(transcript)
    assert nudged(run_hook(transcript, "Read"))  # 2nd — fires


def test_a_fast_batch_inside_a_slow_chain_still_does_not_advance(transcript: Path) -> None:
    """Mixed: two round-tripped calls, then a correctly-batched pair. The batched pair
    must not push the run over the threshold on its own."""
    run_hook(transcript, "Bash")
    backdate(transcript)
    run_hook(transcript, "Bash")  # run == 2
    out = run_hook(transcript, "Bash")  # same-message with the previous — holds at 2
    assert not nudged(out)


# ---------------------------------------------------------------------------
# Chain accounting
# ---------------------------------------------------------------------------


def test_single_call_is_silent(transcript: Path) -> None:
    assert not nudged(run_hook(transcript, "Bash"))


def test_a_different_tool_breaks_the_chain(transcript: Path) -> None:
    """Bash, Bash, Read, Bash is not a 3-chain of Bash — interleaving means the agent was
    doing genuinely different work."""
    run_hook(transcript, "Bash")
    backdate(transcript)
    run_hook(transcript, "Bash")
    backdate(transcript)
    run_hook(transcript, "Read")
    backdate(transcript)
    assert not nudged(run_hook(transcript, "Bash"))


def test_renudges_on_a_long_chain_but_not_every_call(transcript: Path) -> None:
    """A run of 32 was observed live. Firing once would be lost; firing every call is
    noise an agent learns to ignore. Fires at 2 (FIRST_NUDGE_AT), then every 5th."""
    fired: list[int] = []
    for i in range(1, 13):
        if i > 1:
            backdate(transcript)
        if nudged(run_hook(transcript, "Bash")):
            fired.append(i)
    assert fired == [2, 7, 12]


def test_non_chainable_tool_is_ignored(transcript: Path) -> None:
    """Task/Write and friends are not collapsible the same way; sequencing there is
    usually meaningful."""
    outs = [run_hook(transcript, "Task") for _ in range(5)]
    assert not any(nudged(o) for o in outs)


def test_sessions_do_not_interfere(transcript: Path) -> None:
    """Concurrent slots share a machine and, on the AO VM, a transcript directory. One
    slot's chain must never nudge another's."""
    for _ in range(3):
        run_hook(transcript, "Bash", session_id="slot-a")
        backdate(transcript, session_id="slot-a")
    assert not nudged(run_hook(transcript, "Bash", session_id="slot-b"))


# ---------------------------------------------------------------------------
# It must never break a tool call
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    ["", "not json at all", "{}", '{"tool_name": "Bash"}', '{"transcript_path": "/nonexistent/dir/x.jsonl"}'],
)
def test_malformed_input_exits_clean_and_silent(raw: str) -> None:
    proc = subprocess.run([sys.executable, str(HOOK)], input=raw, capture_output=True, text=True, timeout=15)
    assert proc.returncode == 0
    assert not proc.stdout.strip()


def test_unwritable_state_location_is_not_fatal(tmp_path: Path) -> None:
    """A transcript path whose directory does not exist must be a silent no-op, not an
    exception that surfaces as a failed tool call."""
    missing = tmp_path / "no-such-dir" / "session.jsonl"
    payload = {"session_id": "s", "transcript_path": str(missing), "tool_name": "Bash"}
    proc = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, timeout=15
    )
    assert proc.returncode == 0
    assert not proc.stdout.strip()


def test_advice_is_tool_specific_and_names_the_exception(transcript: Path) -> None:
    """Generic advice gets ignored. Bash should be told to use `&&`, Edit to use
    replace_all — and both must carry the do-NOT-batch carve-out so the hook never pushes
    an agent into bundling a check with the destructive act it authorises."""
    run_hook(transcript, "Bash")
    backdate(transcript)
    msg = json.loads(run_hook(transcript, "Bash"))["hookSpecificOutput"]["additionalContext"]
    assert "`&&`" in msg
    assert "destructive" in msg
    assert "/codex/06-coding-standards/tool-call-batching.md" in msg


# ---------------------------------------------------------------------------
# PreToolUse hard block (2026-08-15) — a nudge that was already ignored once
# escalates to an actual denial, with a one-retry grace escape hatch so a
# genuinely sequential (result-dependent) chain can never be permanently
# deadlocked. See the hook's own module docstring for the full design rationale.
# ---------------------------------------------------------------------------


def _round_trip(transcript: Path, tool: str, **kw: object) -> tuple[str, str]:
    """A full Pre+Post pair for one round-tripped call, mirroring how the real harness
    invokes both hooks around a single tool execution. Returns (pre_out, post_out)."""
    pre = run_hook(transcript, tool, event="PreToolUse", **kw)
    post = run_hook(transcript, tool, event="PostToolUse", **kw)
    return pre, post


def test_pretooluse_never_blocks_a_same_message_batch(transcript: Path) -> None:
    """Same false-positive guarantee as the nudge, extended to the block: N calls issued
    back-to-back (no backdate between them) must never be denied, no matter how many."""
    outs = []
    for _ in range(8):
        pre, _post = _round_trip(transcript, "Bash")
        outs.append(pre)
    assert not any(denied(o) for o in outs)


def test_pretooluse_blocks_after_the_nudge_was_already_ignored(transcript: Path) -> None:
    """1st call: below threshold. 2nd: nudge fires (FIRST_NUDGE_AT). 3rd round-tripped
    call of the same tool: the nudge was ignored once already — this is now a hard
    denial (HARD_BLOCK_AT), not another reminder."""
    _round_trip(transcript, "Bash")
    backdate(transcript)
    pre2, post2 = _round_trip(transcript, "Bash")
    assert not denied(pre2)
    assert nudged(post2)
    backdate(transcript)
    pre3 = run_hook(transcript, "Bash", event="PreToolUse")
    assert denied(pre3)


def test_denied_call_gets_exactly_one_grace_retry(transcript: Path) -> None:
    """The escape hatch: immediately retrying the exact call that was just denied is let
    through once — this is what keeps a genuinely sequential chain from deadlocking. A
    THIRD attempt at the same checkpoint (not a retry, a repeat) is denied again."""
    _round_trip(transcript, "Bash")
    backdate(transcript)
    _round_trip(transcript, "Bash")
    backdate(transcript)
    assert denied(run_hook(transcript, "Bash", event="PreToolUse"))  # 3rd, denied
    backdate(transcript)
    retry_pre = run_hook(transcript, "Bash", event="PreToolUse")
    assert not denied(retry_pre)  # grace-exempted retry
    run_hook(transcript, "Bash", event="PostToolUse")  # completes the graced call, run=3


def test_hard_block_has_headroom_after_a_grace_pass_then_rechecks(transcript: Path) -> None:
    """After a graced call lands, the NEXT couple of calls get real headroom
    (HARD_BLOCK_RENUDGE_EVERY) before the next checkpoint — a chain that keeps needing
    grace passes every few calls is still allowed to proceed, just with a periodic
    checkpoint, never a hard permanent stop."""
    for _ in range(2):  # get to run=2 (nudge) then run=3 (denied+grace-retried -> run=3 lands)
        _round_trip(transcript, "Bash")
        backdate(transcript)
    assert denied(run_hook(transcript, "Bash", event="PreToolUse"))
    backdate(transcript)
    run_hook(transcript, "Bash", event="PreToolUse")  # grace retry, run=3 lands
    run_hook(transcript, "Bash", event="PostToolUse")
    backdate(transcript)
    # run=4: headroom (4-3=1 < HARD_BLOCK_RENUDGE_EVERY=3)
    assert not denied(run_hook(transcript, "Bash", event="PreToolUse"))
    run_hook(transcript, "Bash", event="PostToolUse")
    backdate(transcript)
    # run=5: still headroom (5-3=2 < 3)
    assert not denied(run_hook(transcript, "Bash", event="PreToolUse"))
    run_hook(transcript, "Bash", event="PostToolUse")
    backdate(transcript)
    # run=6: checkpoint again (6-3=3 >= 3)
    assert denied(run_hook(transcript, "Bash", event="PreToolUse"))


def test_a_different_tool_is_never_blocked_by_an_unrelated_chain(transcript: Path) -> None:
    """The block, like the nudge, is per-chain — interleaving a different tool must not
    inherit or trip another tool's near-threshold count."""
    _round_trip(transcript, "Bash")
    backdate(transcript)
    _round_trip(transcript, "Bash")  # Bash chain at run=2, nudged
    backdate(transcript)
    assert not denied(run_hook(transcript, "Read", event="PreToolUse"))


def test_same_file_edit_chain_blocks_independently_of_general_edit_chain(transcript: Path) -> None:
    """Same-file Edit repetition is a stronger signal (SAME_FILE_HARD_BLOCK_AT) and is
    tracked separately from the general same-tool chain."""
    _round_trip(transcript, "Edit", file_path="/tmp/foo.py")
    backdate(transcript)
    pre2, post2 = _round_trip(transcript, "Edit", file_path="/tmp/foo.py")
    assert not denied(pre2)
    assert nudged(post2)
    backdate(transcript)
    assert denied(run_hook(transcript, "Edit", event="PreToolUse", file_path="/tmp/foo.py"))


def test_edit_grace_retry_does_not_also_trip_the_general_chain_block(transcript: Path) -> None:
    """Regression test for a real bug caught in self-review before this shipped: every
    Edit call is ALSO a same-tool "Edit" call, so the general and same-file counters
    climb in lockstep. A retry that clears the same-file grace check must not then fall
    through and get independently denied by the general same-tool check for the exact
    same underlying event — same-file is the SOLE block signal once a file_path
    resolves, never evaluated alongside the general check."""
    _round_trip(transcript, "Edit", file_path="/tmp/foo.py")
    backdate(transcript)
    _round_trip(transcript, "Edit", file_path="/tmp/foo.py")
    backdate(transcript)
    assert denied(run_hook(transcript, "Edit", event="PreToolUse", file_path="/tmp/foo.py"))
    backdate(transcript)
    # The retry must be allowed outright — not denied a second time via the general chain.
    assert not denied(run_hook(transcript, "Edit", event="PreToolUse", file_path="/tmp/foo.py"))


def test_editing_a_different_file_does_not_inherit_a_blocked_files_chain(transcript: Path) -> None:
    _round_trip(transcript, "Edit", file_path="/tmp/foo.py")
    backdate(transcript)
    _round_trip(transcript, "Edit", file_path="/tmp/foo.py")
    backdate(transcript)
    run_hook(transcript, "Edit", event="PreToolUse", file_path="/tmp/foo.py")  # denies foo.py's 3rd
    backdate(transcript)
    assert not denied(run_hook(transcript, "Edit", event="PreToolUse", file_path="/tmp/bar.py"))


def test_missing_hook_event_name_defaults_to_post_only_and_never_blocks(transcript: Path) -> None:
    """A caller that omits hook_event_name entirely (older harness variant, or a stubbed
    test payload) must fall back to the original nudge-only contract — never silently
    start denying calls it can't tell are PreToolUse."""
    payload = {"session_id": "sess-1", "transcript_path": str(transcript), "tool_name": "Bash"}
    outs = []
    for i in range(6):
        if i > 0:
            backdate(transcript)
        proc = subprocess.run(
            [sys.executable, str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, timeout=15
        )
        assert proc.returncode == 0
        outs.append(proc.stdout)
    assert not any(denied(o) for o in outs)
    assert any(nudged(o) for o in outs)  # the nudge half of the contract still works
