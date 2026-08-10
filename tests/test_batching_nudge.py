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


def run_hook(transcript: Path, tool: str, session_id: str = "sess-1") -> str:
    payload = {"session_id": session_id, "transcript_path": str(transcript), "tool_name": tool}
    proc = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert proc.returncode == 0, f"hook must never exit non-zero (stderr: {proc.stderr})"
    return proc.stdout


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
    """The same five calls, each in its own turn — the anti-pattern."""
    run_hook(transcript, "Read")
    backdate(transcript)
    assert not nudged(run_hook(transcript, "Read"))  # 2nd — still below threshold
    backdate(transcript)
    assert nudged(run_hook(transcript, "Read"))  # 3rd — fires


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
    noise an agent learns to ignore. Fires at 3, then every 5th."""
    fired: list[int] = []
    for i in range(1, 13):
        if i > 1:
            backdate(transcript)
        if nudged(run_hook(transcript, "Bash")):
            fired.append(i)
    assert fired == [3, 8]


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
    run_hook(transcript, "Bash")
    backdate(transcript)
    msg = json.loads(run_hook(transcript, "Bash"))["hookSpecificOutput"]["additionalContext"]
    assert "`&&`" in msg
    assert "destructive" in msg
    assert "/codex/06-coding-standards/tool-call-batching.md" in msg
