#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""precompact-watcher.py — personal, single-session analog of agent-orchestrator's
context_lifecycle.py, for a tmux-wrapped `claude` CLI session (launched via
launch-tab-precompact-session.sh). SSOT: codex/05-infrastructure/local-tmux-precompact-watcher.md

Ported directly from agent-orchestrator/server/{tmux_spawn.py,worker_liveness/__init__.py,
context_lifecycle.py} (2026-07-22) so the pane-parsing regexes and the verified-submit
pattern stay identical to the code they were copied from — this is NOT a from-scratch
reimplementation, it is the same signal-and-injection logic scoped to one local session
with no agent-outbox/SlotRow/backlog (nothing here talks to agent-orchestrator's DB).

Two tiers, cooperative-first (mirrors context_lifecycle.py's own docstring):

Tier 1 — proactive nudge at context% >= --guidance-pct: once, when the pane is idle,
  SUBMIT a plain reminder message asking Claude to run /pre-compact at its next
  checkpoint. This is a real turn (costs a little), same tradeoff context_lifecycle.py
  already accepts for its own agent-outbox guidance.

Tier 2 — forced two-phase fallback after --force-after-seconds unacked AND
  --idle-observations consecutive idle polls with no pending input and no child
  processes: force-submit /pre-compact, wait for the pane to go idle AGAIN (proof its
  own work finished), then force-submit /compact. Never forces over a spinner, a
  non-empty input box, or a running child process under the pane shell.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import cast

# -- ported regexes (agent-orchestrator/server/worker_liveness/__init__.py) --------

_SPINNER_RE = re.compile(
    r"esc to interrupt"  # Claude's interrupt hint line — authoritative active-turn marker
    r"|Running \d+ tool"
    r"|Executing"
    r"|\[Thinking\]",
    re.IGNORECASE,
)
_PROMPT_RE = re.compile(r"^\s*❯\s*(.*?)\s*$", re.MULTILINE)  # noqa: RUF001 — U+276F is claude's real prompt glyph
_AUTO_COMPACT_RE = re.compile(r"(\d+)\s*%\s*until\s+auto-compact", re.IGNORECASE)
_TOKEN_USAGE_RE = re.compile(r"[↑↓]\s*([\d.]+)\s*k\s+tokens", re.IGNORECASE)  # up/down arrows
# Operator correction 2026-07-23: the workspace's actual context tier is 1M, not
# 200K -- 200K over-reports pct-used badly enough to trigger the nudge/forced
# path far too often (mirrors the same fix in agent-orchestrator/server/
# worker_liveness/__init__.py::_DEFAULT_CONTEXT_WINDOW_K).
_DEFAULT_CONTEXT_WINDOW_K = 1000

# -- ported regexes (agent-orchestrator/server/tmux_spawn.py) ----------------------

_ACTIVE_TURN_MARKERS = ("esc to interrupt", "esc to cancel")
_INPUT_GHOST_RE = re.compile(r'^Try "[^"]*"$')
_INPUT_DECORATION_RE = re.compile(r"^[─│╭╮╰╯┌┐└┘═║\s·]+$")

_COMPACTION_DROP_PCT = 25


def _exact_pane_target(session: str) -> str:
    """Exact-match pane target — a bare -t prefix-matches (claude-tab1 also matches
    claude-tab10); tmux_spawn.py's exact_pane_target() exists for exactly this."""
    return f"={session}:"


def _exact_session_target(session: str) -> str:
    return f"={session}"


def has_session(session: str) -> bool:
    res = subprocess.run(
        ["tmux", "has-session", "-t", _exact_session_target(session)],
        capture_output=True,
        timeout=2,
    )
    return res.returncode == 0


def capture_pane(session: str, history_lines: int = 300) -> str:
    res = subprocess.run(
        ["tmux", "capture-pane", "-p", "-t", _exact_pane_target(session), "-S", f"-{history_lines}"],
        capture_output=True,
        text=True,
        timeout=5,
        check=True,
    )
    return res.stdout


def _last_nonblank_lines(text: str, n: int) -> list[str]:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    return lines[-n:] if len(lines) > n else lines


def classify_pane(pane_text: str) -> str:
    """ "working" | "frozen" | "idle" — see context_lifecycle.py's docstring for the
    exact same three-way split this ports."""
    tail = "\n".join(_last_nonblank_lines(pane_text, 6))
    if _SPINNER_RE.search(tail):
        return "working"
    m = _PROMPT_RE.search(tail)
    if m:
        pending = m.group(1).strip()
        if pending and not _INPUT_GHOST_RE.match(pending) and not _INPUT_DECORATION_RE.match(pending):
            return "frozen"
    return "idle"


def pane_input_pending(session: str) -> str:
    """Unsubmitted text sitting in the input box, "" when empty/consumed/mid-turn."""
    try:
        pane = capture_pane(session, history_lines=50)
    except (subprocess.SubprocessError, OSError):
        return ""
    tail = "\n".join([ln for ln in pane.splitlines() if ln.strip()][-8:])
    if any(marker in tail for marker in _ACTIVE_TURN_MARKERS):
        return ""
    matches: list[str] = _PROMPT_RE.findall(tail)
    if not matches:
        return ""
    text = matches[-1].strip()
    if _INPUT_GHOST_RE.match(text):
        return ""
    if text and _INPUT_DECORATION_RE.match(text):
        return ""
    return text


def pane_has_child_processes(session: str) -> bool:
    """True when the pane's shell has RUNNING children beyond the claude CLI itself
    (a build, a background QG, a hung curl) — never force-inject over those.
    Conservative: any measurement failure reads as True (not safe to force)."""
    try:
        res = subprocess.run(
            ["tmux", "display-message", "-p", "-t", _exact_pane_target(session), "#{pane_pid}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        pane_pid = res.stdout.strip()
        if res.returncode != 0 or not pane_pid.isdigit():
            return True
        pgrep = subprocess.run(["pgrep", "-P", pane_pid], capture_output=True, text=True, timeout=5)
        children = [ln for ln in pgrep.stdout.splitlines() if ln.strip()]
        return len(children) > 1  # the claude CLI process itself is the idle baseline
    except (subprocess.SubprocessError, OSError):
        return True


def submit_to_pane(session: str, text: str, submit_settle_s: float = 1.0) -> bool:
    """Type text + verify it submitted (send-keys -l, settle, C-m, retry once) —
    the ONE sanctioned pane-injection pattern; a raw fire-and-forget send-keys+C-m
    can leave text stuck in the input box under bracketed-paste (tmux_spawn.py)."""
    try:
        subprocess.run(
            ["tmux", "send-keys", "-t", _exact_pane_target(session), "-l", text],
            capture_output=True,
            timeout=5,
        )
    except (subprocess.SubprocessError, OSError):
        return False
    for _attempt in range(2):
        time.sleep(submit_settle_s)
        subprocess.run(["tmux", "send-keys", "-t", _exact_pane_target(session), "C-m"], capture_output=True, timeout=5)
        time.sleep(submit_settle_s)
        if not pane_input_pending(session):
            return True
    return not pane_input_pending(session)


# -- transcript-measured context (ported from agent-orchestrator/server/context_probe.py,
#    2026-08-08) ------------------------------------------------------------------
#
# The pane readouts above cannot drive a mid-range threshold. Measured on the
# orchestrator VM: "% context used" matched 0/11 live panes and "% until auto-compact"
# 2/11 -- the CLI only renders the countdown in the last few percent. Worse, the
# _TOKEN_USAGE_RE fallback divides by a HARDCODED window, which was 5x too big for
# sonnet-4.6 (a 165,797-token session reading 99% full in its own pane computed as
# 16%). Both are fixed the same way as in AO: read message.usage from the session
# transcript -- present on EVERY assistant turn -- and divide by a window LEARNED per
# model instead of assumed.
#
# This also answers "don't count history from before the last compact" directly. The
# transcript is append-only across every /compact (one real session accumulated 13
# compact_boundary events), so a whole-file byte heuristic runs wildly high --
# measured ~1475% of budget on a session the operator read at ~15%. The LAST
# assistant turn's usage is inherently POST-compact (after a compaction the next
# turn's input is just [summary + new turns]), so it needs no windowing at all; the
# only extra guard required is the stale case below.

_SYNTHETIC_MODEL = "<synthetic>"
_MIN_CALIBRATION_PCT = 25
_WATERMARK_TO_WINDOW = 0.97
_MIN_WATERMARK_TOKENS = 50_000
# A watermark is a WINDOW estimate only once sessions demonstrably SATURATE at it --
# one session reaching N proves the window is at least N, not that it stops there.
# Caught by testing this port against a real session: a fresh registry learned 222,121
# from ONE in-flight claude-opus-5 session and reported 97% full when the truth was
# ~22%, which would force a compaction immediately and forever after. Exceeding the
# watermark RESETS the hit count -- the ceiling just moved, so old evidence is void.
_WATERMARK_CONFIRM_HITS = 3
_WATERMARK_CLUSTER_FRACTION = 0.95
_LEARNED_WINDOWS_PATH = Path.home() / ".claude" / "precompact-learned-windows.json"


def _as_int(value: object) -> int:
    return value if isinstance(value, int) else 0


def _token_total(usage: dict[str, object]) -> int:
    """Live context size for one assistant turn -- the same four fields AO sums."""
    raw_cache = usage.get("cache_creation")
    cache = raw_cache if isinstance(raw_cache, dict) else {}
    return (
        _as_int(usage.get("input_tokens"))
        + _as_int(usage.get("cache_read_input_tokens"))
        + _as_int(cache.get("ephemeral_5m_input_tokens"))
        + _as_int(cache.get("ephemeral_1h_input_tokens"))
    )


def _pane_cwd(session: str) -> str:
    try:
        res = subprocess.run(
            ["tmux", "display-message", "-p", "-t", _exact_pane_target(session), "#{pane_current_path}"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return res.stdout.strip() if res.returncode == 0 else ""
    except (subprocess.SubprocessError, OSError):
        return ""


def _project_dir_for_cwd(cwd: str) -> str:
    """Claude Code's project-dir encoding of a cwd: every non-alphanumeric character
    becomes ``-`` (so ``/Users/x/Code/.tabs/1`` -> ``-Users-x-Code--tabs-1``).
    Verified against a real local transcript directory."""
    return re.sub(r"[^a-zA-Z0-9]", "-", cwd)


def newest_transcript(session: str) -> Path | None:
    """Newest transcript JSONL for the pane's current working directory.

    Scoped to the pane's OWN project dir rather than "newest file anywhere under
    ~/.claude/projects" so a second local Claude session in another repo can never be
    mistaken for this one."""
    cwd = _pane_cwd(session)
    if not cwd:
        return None
    project_dir = Path.home() / ".claude" / "projects" / _project_dir_for_cwd(cwd)
    matches = [Path(p) for p in glob.glob(str(project_dir / "*.jsonl"))]
    if not matches:
        return None
    return max(matches, key=lambda p: p.stat().st_mtime if p.exists() else 0.0)


def read_transcript_snapshot(path: Path) -> tuple[str, int, bool] | None:
    """``(model, tokens, stale_after_compaction)`` from a transcript, or None.

    Two guards, both load-bearing (see context_probe.py for the measured evidence):
    ``<synthetic>`` records carry ZERO-token usage and are often the LAST record, and
    a ``compact_boundary`` after the last usage record means the reading describes
    the PRE-compact session."""
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return None
    model, tokens, last_usage, last_compaction = "", 0, -1, -1
    for index, line in enumerate(text.split("\n")):
        if '"compact_boundary"' in line:
            last_compaction = index
        if '"usage"' not in line:
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(record, dict) or record.get("type") != "assistant":
            continue
        raw_message = record.get("message")
        message = raw_message if isinstance(raw_message, dict) else {}
        record_model = message.get("model")
        if not isinstance(record_model, str) or record_model == _SYNTHETIC_MODEL:
            continue
        raw_usage = message.get("usage")
        if not isinstance(raw_usage, dict):
            continue
        model, tokens, last_usage = record_model, _token_total(raw_usage), index
    if last_usage < 0 or tokens <= 0:
        return None
    return model, tokens, last_compaction > last_usage


def _load_learned() -> dict[str, dict[str, int]]:
    try:
        raw = json.loads(_LEARNED_WINDOWS_PATH.read_text())
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    return {k: v for k, v in raw.items() if isinstance(k, str) and isinstance(v, dict)}


def observe_window(model: str, tokens: int, pane_pct: int | None, fallback_window_k: int) -> int:
    """Record an observation and return the best window estimate for ``model``.

    Precedence: exact calibration from a visible pane pct > a SATURATED high-water
    mark > the caller's ``--context-window-k`` fallback. Monotonic, so a short
    session can never shrink a window learned from a long one. Adapts to any model,
    which is the point -- nothing here knows the name "sonnet" or "deepseek"."""
    data = _load_learned()
    entry = dict(data.get(model, {}))
    watermark = entry.get("watermark_tokens", 0)
    if tokens > watermark:
        entry["watermark_tokens"] = tokens
        entry["watermark_hits"] = 1
    elif tokens >= watermark * _WATERMARK_CLUSTER_FRACTION:
        entry["watermark_hits"] = entry.get("watermark_hits", 0) + 1
    if pane_pct is not None and pane_pct >= _MIN_CALIBRATION_PCT:
        calibrated = int(tokens / (pane_pct / 100))
        if calibrated > entry.get("calibrated_window", 0):
            entry["calibrated_window"] = calibrated
    data[model] = entry
    try:
        _LEARNED_WINDOWS_PATH.parent.mkdir(parents=True, exist_ok=True)
        _LEARNED_WINDOWS_PATH.write_text(json.dumps(data, indent=2, sort_keys=True))
    except OSError:
        pass  # advisory cache only -- a failed write just means re-learning next tick
    if entry.get("calibrated_window", 0) > 0:
        return entry["calibrated_window"]
    watermark = entry.get("watermark_tokens", 0)
    if watermark >= _MIN_WATERMARK_TOKENS and entry.get("watermark_hits", 0) >= _WATERMARK_CONFIRM_HITS:
        return int(watermark / _WATERMARK_TO_WINDOW)
    return fallback_window_k * 1000


def read_pct(session: str, context_window_k: int) -> int | None:
    """Context% for the session -- MEASURED from its transcript, pane as fallback.

    The pane reading is still taken first because when it IS present it is
    authoritative about the window the CLI itself divides by, so it calibrates the
    learned window exactly. Returns None for "unknown" (never 0), including the
    just-compacted case where the last transcript reading is stale-high."""
    pane_pct: int | None = None
    try:
        pane = capture_pane(session)
    except (subprocess.SubprocessError, OSError):
        pane = ""
    if pane:
        m = _AUTO_COMPACT_RE.search(pane)
        if m:
            pane_pct = max(0, min(100, 100 - int(m.group(1))))

    path = newest_transcript(session)
    if path is not None:
        snapshot = read_transcript_snapshot(path)
        if snapshot is not None:
            model, tokens, stale = snapshot
            if stale:
                return None  # just compacted -- the last reading describes the old session
            window = observe_window(model, tokens, pane_pct, context_window_k)
            if window > 0:
                return max(0, min(100, round(tokens * 100 / window)))
    if pane_pct is not None:
        return pane_pct
    toks: list[str] = _TOKEN_USAGE_RE.findall(pane) if pane else []
    if toks:
        try:
            return max(1, min(100, int(float(toks[-1]) * 100 / context_window_k)))
        except (ValueError, ZeroDivisionError):
            return None
    return None


@dataclass
class _State:
    last_pct: int = 0
    guidance_sent_at: float | None = None
    idle_streak: int = 0
    precompact_forced_at: float | None = None
    forced_at: float | None = None
    seen_ticks: int = 0


@dataclass(frozen=True)
class Config:
    """Typed CLI config — built once from argparse.Namespace so the rest of the
    module never touches the untyped (Any-attributed) Namespace directly."""

    session: str
    guidance_pct: int
    force_after_seconds: int
    idle_observations: int
    poll_interval: int
    context_window_k: int


def _log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


GUIDANCE_MESSAGE = (
    "Context is getting high (past your configured threshold). At your next natural "
    "checkpoint: run the /pre-compact skill to checkpoint in-flight work (commit/push, "
    "convert deferred discoveries into plan todos, write the Deferred work table), then "
    "run /compact. (Automated nudge from precompact-watcher.py — not a user message.)"
)


def _run_tier2(session: str, state: _State, idle_observations: int) -> None:
    pane = capture_pane(session, history_lines=40)
    if classify_pane(pane) != "idle":
        state.idle_streak = 0
        return
    state.idle_streak += 1
    if state.idle_streak < idle_observations:
        return
    if pane_input_pending(session):
        state.idle_streak = 0
        return
    if pane_has_child_processes(session):
        state.idle_streak = 0
        return

    if state.precompact_forced_at is None:
        submitted = submit_to_pane(session, "/pre-compact")
        state.precompact_forced_at = time.time()
        state.idle_streak = 0
        _log(f"FORCED /pre-compact (submitted={submitted}) — waiting for idle again before /compact")
        return

    submitted = submit_to_pane(session, "/compact")
    state.forced_at = time.time()
    _log(f"FORCED /compact (submitted={submitted}) — post-precompact")


def watch(cfg: Config) -> int:
    session = cfg.session
    state = _State()
    _log(f"Watching tmux session '{session}' (poll every {cfg.poll_interval}s)")
    while True:
        if not has_session(session):
            _log(f"Session '{session}' is gone — nothing more to watch, exiting.")
            return 0

        pct = read_pct(session, cfg.context_window_k)
        state.seen_ticks += 1
        if pct is None:
            time.sleep(cfg.poll_interval)
            continue

        if state.last_pct - pct >= _COMPACTION_DROP_PCT:
            _log(f"Compaction observed ({state.last_pct}% -> {pct}%) — guidance state reset")
            state.guidance_sent_at = None
            state.precompact_forced_at = None
            state.forced_at = None
            state.idle_streak = 0
        state.last_pct = pct

        if pct >= cfg.guidance_pct and state.guidance_sent_at is None:
            pane = capture_pane(session, history_lines=40)
            if classify_pane(pane) == "idle" and not pane_input_pending(session):
                submitted = submit_to_pane(session, GUIDANCE_MESSAGE)
                state.guidance_sent_at = time.time()
                _log(f"Context at {pct}% — sent guidance nudge (submitted={submitted})")
            # else: mid-turn or frozen — try again next poll, don't mark as sent

        elif (
            state.guidance_sent_at is not None
            and state.forced_at is None
            and (time.time() - state.guidance_sent_at) >= cfg.force_after_seconds
        ):
            _run_tier2(session, state, cfg.idle_observations)

        time.sleep(cfg.poll_interval)


def _parse_args(argv: list[str]) -> Config:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("session", help="tmux session name (as started by launch-tab-precompact-session.sh)")
    parser.add_argument(
        "--guidance-pct", type=int, default=50, help="context%% to trigger the Tier-1 nudge (default 50)"
    )
    parser.add_argument(
        "--force-after-seconds",
        type=int,
        default=2700,
        help="seconds an unacked nudge waits before Tier-2 forcing kicks in (default 2700 = 45min)",
    )
    parser.add_argument(
        "--idle-observations",
        type=int,
        default=3,
        help="consecutive idle polls required before forcing (default 3)",
    )
    parser.add_argument("--poll-interval", type=int, default=15, help="seconds between polls (default 15)")
    parser.add_argument(
        "--context-window-k",
        type=int,
        default=_DEFAULT_CONTEXT_WINDOW_K,
        help="context window in K tokens (default 1000 = 1M)",
    )
    ns = parser.parse_args(argv)
    # argparse.Namespace attributes are dynamically typed (Any) in the stubs even
    # though `type=int`/positional-str guarantee the runtime type — cast documents
    # that guarantee explicitly rather than silently letting Any flow further.
    return Config(
        session=cast(str, ns.session),
        guidance_pct=cast(int, ns.guidance_pct),
        force_after_seconds=cast(int, ns.force_after_seconds),
        idle_observations=cast(int, ns.idle_observations),
        poll_interval=cast(int, ns.poll_interval),
        context_window_k=cast(int, ns.context_window_k),
    )


def main(argv: list[str]) -> int:
    cfg = _parse_args(argv)

    if not has_session(cfg.session):
        print(
            f"No tmux session named '{cfg.session}'. Start it first with launch-tab-precompact-session.sh.",
            file=sys.stderr,
        )
        return 1

    try:
        return watch(cfg)
    except KeyboardInterrupt:
        _log("Stopped.")
        return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
