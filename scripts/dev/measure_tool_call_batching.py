#!/usr/bin/env python3
# Epic: anthropic_per_task_actual_spend_and_account_calibration_2026_08_10
# Lifecycle: permanent — re-run it; THE NUMBER HAS A DATE ON IT
# Delete-when: NA (the batching baseline needs re-measuring whenever guidance or the hook changes)
"""Measure what share of tool calls sit in COLLAPSIBLE consecutive same-tool chains.

WHY THIS EXISTS
---------------
A written batching rule was shipped ~2026-08-05 and did not move the number (~11% of
fleet turns batching >1 call, measured then; 57.3% of calls still collapsible on
2026-08-10). An in-loop `PostToolUse` hook shipped 2026-08-11
(`cursor-configs/hooks/batching-nudge.py`, unified-trading-pm@19dc43ec69). This script is
how we find out whether the MECHANISM moved what the RULE could not — and a flat result
is the finding, not a failure: it would mean the answer is structural, not a nudge.

BASELINE TO BEAT (2026-08-10, controlled 4h25m window, laptop-only)
-------------------------------------------------------------------
    3,123 API calls | 57.3% collapsible | 405,833 mean cache-read tokens/call
    Bash 52.8% of all calls; 69% of Bash calls inside a chain; runs of 20/23/26/28/32.

TWO MEASUREMENT TRAPS — BOTH ALREADY COST A WRONG ANSWER
--------------------------------------------------------
1. **requestId dedup vs UNION.** Claude Code writes ONE JSONL LINE PER CONTENT BLOCK,
   every line repeating the same `requestId` and the same `usage`. So usage must be
   counted ONCE per requestId, but content blocks must be UNIONED across every line
   sharing it. Keeping only the first line silently drops `tool_use` blocks and produced
   a false "71% of turns are tool-free" reading before it was caught.
2. **Same-message batching looks identical to a chain.** Four Reads issued as four
   `tool_use` blocks in ONE message emit the same sequence as four Reads across four
   turns — the first is CORRECT behaviour, the second is the anti-pattern. They are
   separable only by LATENCY: same-message calls land milliseconds apart, separate turns
   are split by a model round-trip (measured median 10.5s). This script uses the SAME
   threshold the hook uses (`SAME_MESSAGE_WINDOW_SECONDS`), so the metric and the
   intervention agree on what "collapsible" means. Counting raw same-tool adjacency
   instead would score a perfectly-batching agent as 100% collapsible.

Read-only. Scans every slot's transcripts on THIS machine (`~/.claude/projects/`).

Usage:
    python3 scripts/dev/measure_tool_call_batching.py --hours 4
    python3 scripts/dev/measure_tool_call_batching.py --since 2026-08-11T02:00:00
"""

from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import os
from collections import defaultdict

# Must match cursor-configs/hooks/batching-nudge.py — the metric and the intervention
# have to agree on what counts as a separate turn, or one will flatter the other.
SAME_MESSAGE_WINDOW_SECONDS = 2.0
CHAINABLE_TOOLS = {"Bash", "Read", "Grep", "Glob", "Edit"}

BASELINE_COLLAPSIBLE_PCT = 57.3
BASELINE_MEAN_CACHE_READ = 405_833
BASELINE_CALLS = 3123
BASELINE_DATE = "2026-08-10"


def _parse_ts(raw: str) -> _dt.datetime | None:
    try:
        return _dt.datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return None


def collect(since: _dt.datetime) -> dict[str, dict[str, object]]:
    """requestId -> {session, ts, cache_read, tools[]} with usage counted ONCE and
    content blocks UNIONED (see trap 1)."""
    calls: dict[str, dict[str, object]] = {}
    pattern = os.path.expanduser("~/.claude/projects/**/*.jsonl")
    cutoff_mtime = since.timestamp()
    for path in glob.iglob(pattern, recursive=True):
        try:
            if os.path.getmtime(path) < cutoff_mtime:
                continue
        except OSError:
            continue
        try:
            with open(path, encoding="utf-8", errors="replace") as handle:
                lines = handle.readlines()
        except OSError:
            continue
        for line in lines:
            if '"type":"assistant"' not in line:
                continue
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") != "assistant":
                continue
            msg = ev.get("message") or {}
            usage = msg.get("usage")
            rid = ev.get("requestId") or msg.get("id")
            ts = _parse_ts(ev.get("timestamp") or "")
            if not usage or not rid or ts is None or ts < since:
                continue
            call = calls.get(rid)
            if call is None:
                call = calls[rid] = {
                    "session": ev.get("sessionId") or "?",
                    "ts": ts,
                    "cache_read": int(usage.get("cache_read_input_tokens") or 0),
                    "tools": [],
                }
            for block in msg.get("content") or []:
                if isinstance(block, dict) and block.get("type") == "tool_use":
                    tools = call["tools"]
                    assert isinstance(tools, list)
                    tools.append(block.get("name") or "?")
    return calls


def analyse(calls: dict[str, dict[str, object]]) -> tuple[int, int, dict[str, int], dict[int, int]]:
    """Collapsible = consecutive same-single-tool calls SEPARATED BY A REAL ROUND-TRIP
    (see trap 2). Same-message batches never advance a chain."""
    per_session: dict[str, list[dict[str, object]]] = defaultdict(list)
    for call in calls.values():
        per_session[str(call["session"])].append(call)

    collapsible = 0
    by_tool: dict[str, int] = defaultdict(int)
    chain_hist: dict[int, int] = defaultdict(int)

    for sess in per_session.values():
        sess.sort(key=lambda c: c["ts"])  # type: ignore[arg-type,return-value]
        prev_tool: str | None = None
        prev_ts: _dt.datetime | None = None
        run = 0
        for call in sess:
            tools = call["tools"]
            assert isinstance(tools, list)
            tool = tools[0] if len(tools) == 1 and tools[0] in CHAINABLE_TOOLS else None
            ts = call["ts"]
            assert isinstance(ts, _dt.datetime)
            round_tripped = prev_ts is None or (ts - prev_ts).total_seconds() >= SAME_MESSAGE_WINDOW_SECONDS
            if tool is not None and tool == prev_tool and round_tripped:
                run += 1
                collapsible += 1
                by_tool[tool] += 1
            else:
                if run:
                    chain_hist[run + 1] += 1
                run = 0
            prev_tool, prev_ts = tool, ts
        if run:
            chain_hist[run + 1] += 1
    return collapsible, sum(len(v) for v in per_session.values()), dict(by_tool), dict(chain_hist)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hours", type=float, default=4.0, help="Look-back window in hours (default 4).")
    ap.add_argument("--since", help="ISO-8601 start instead of --hours.")
    args = ap.parse_args()

    now = _dt.datetime.now(_dt.UTC)
    since = _parse_ts(args.since) if args.since else now - _dt.timedelta(hours=args.hours)
    if since is None:
        raise SystemExit("could not parse --since")
    if since.tzinfo is None:
        since = since.replace(tzinfo=_dt.UTC)

    calls = collect(since)
    if not calls:
        print(f"No API calls found since {since.isoformat()} — nothing to measure.")
        return
    collapsible, total, by_tool, chain_hist = analyse(calls)
    pct = collapsible / total * 100
    mean_cr = sum(int(c["cache_read"]) for c in calls.values()) / total  # type: ignore[call-overload]

    print(f"Window            : {since.isoformat(timespec='minutes')} -> now ({args.hours}h)")
    print(f"Sessions / calls  : {len({c['session'] for c in calls.values()})} / {total}")
    print(f"COLLAPSIBLE       : {collapsible} ({pct:.1f}%)")
    print(f"Mean cache read   : {mean_cr:,.0f} tokens/call")
    print()
    print(
        f"BASELINE ({BASELINE_DATE}) : {BASELINE_CALLS} calls, {BASELINE_COLLAPSIBLE_PCT}% collapsible, "
        f"{BASELINE_MEAN_CACHE_READ:,} mean cache read"
    )
    delta = pct - BASELINE_COLLAPSIBLE_PCT
    verdict = "IMPROVED" if delta <= -5 else ("FLAT" if abs(delta) < 5 else "WORSE")
    print(f"DELTA             : {delta:+.1f} pp  ->  {verdict}")
    if verdict == "FLAT":
        print("  FLAT is a FINDING, not a failure: a rule was already tried and did not move this,")
        print("  and now an in-loop nudge has not either. The next lever is structural, not advisory.")
    if by_tool:
        print("\nCollapsible by tool:")
        for tool, n in sorted(by_tool.items(), key=lambda kv: -kv[1]):
            print(f"  {tool:<8}{n:>6}  ({n / total * 100:.1f}% of all calls)")
    if chain_hist:
        longest = max(chain_hist)
        print(f"\nLongest chain observed: {longest} consecutive round-tripped calls")


if __name__ == "__main__":
    main()
