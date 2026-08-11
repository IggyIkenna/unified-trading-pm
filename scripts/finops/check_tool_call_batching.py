#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: DURABLE — re-run whenever agent tool-call efficiency needs re-measuring
# Delete-when: never (the answer has a date on it; re-run, do not trust an old number)
#
# Warns when an agent session DEVIATES from the tool-call batching rule.
#
# WHY THIS EXISTS: `/codex/06-coding-standards/tool-call-batching.md` established the
# rule (independent calls belong in ONE call) and the 2026-08-10 baseline (3,123 calls,
# 57.3% collapsible, 405,833 mean cache-read tokens/call), and the directive was
# propagated to all four agent-prompt surfaces — but nothing MEASURED whether the
# guidance actually changed behaviour. A rule with no meter is a rule nobody can tell
# is working. This is the meter.
#
# WHAT "COLLAPSIBLE" MEANS HERE. A turn that issues exactly one tool_use block, whose
# tool is the SAME as the immediately preceding turn's single tool, could have been sent
# as two blocks in one message. Those are the calls the SSOT counts. This is deliberately
# a LOWER BOUND on waste:
#   * it cannot see independence — two consecutive Reads are counted, but a Read whose
#     path came from the previous Grep is genuinely sequential and is counted too, so
#     the true collapsible share is somewhat lower than the raw chain share;
#   * a multi-block turn is already batched, so it never counts against you.
# Read the number as a TREND against the baseline, not as an absolute defect count.
#
# TRAPS HIT BUILDING THIS (the SSOT calls out the first one explicitly — it produced a
# false "71% of turns are tool-free" reading before it was caught):
#   * ONE logical assistant turn streams as SEVERAL JSONL lines sharing one `requestId`.
#     Deduplicate on `requestId` and UNION the content blocks across every line — keeping
#     only the first line silently drops `tool_use` blocks and understates tool activity.
#   * `usage` lives under record['message']['usage'], not at the top level.
#   * Filter on each record's OWN `timestamp`, not file mtime: a long-lived session file
#     contains records outside the window.
#   * Sidechain records (`isSidechain: true`) are SUB-AGENT turns. They are real calls and
#     are included, but reported separately — a parent that fans work out to sub-agents has
#     a genuinely different call profile from one doing the work inline.
#
# Usage:
#   python3 scripts/finops/check_tool_call_batching.py                # last 24h, all sessions
#   python3 scripts/finops/check_tool_call_batching.py --days 7
#   python3 scripts/finops/check_tool_call_batching.py --session <id> # one session
#   python3 scripts/finops/check_tool_call_batching.py --strict       # exit 1 when over baseline
# Exit codes: 0 = at or better than baseline (or --strict not set), 1 = worse under --strict.
from __future__ import annotations

import argparse
import collections
import datetime
import glob
import json
import os
import sys

# The 2026-08-10 measurement every later run should BEAT. Source of truth for these
# numbers is the codex SSOT; they are duplicated here only so the script can print a
# comparison without reading markdown.
BASELINE_COLLAPSIBLE_PCT = 57.3
BASELINE_MEAN_CACHE_READ = 405_833
BASELINE_DATE = "2026-08-10"

ROOT = os.path.expanduser("~/.claude/projects")


def _iter_records(paths: list[str], cutoff: datetime.datetime):
    """Yield (record, is_sidechain) for records inside the window."""
    for path in paths:
        try:
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except (ValueError, TypeError):
                        continue
                    ts = rec.get("timestamp")
                    if not isinstance(ts, str):
                        continue
                    try:
                        when = datetime.datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except ValueError:
                        continue
                    if when.tzinfo is None:
                        when = when.replace(tzinfo=datetime.UTC)
                    if when < cutoff:
                        continue
                    yield rec
        except OSError:
            continue


def _collect_turns(records) -> dict[str, dict[str, object]]:
    """Fold streamed lines into ONE entry per `requestId`, unioning content blocks.

    Keyed by requestId because a single logical assistant turn arrives as several
    lines. Anything without a requestId is not a completed model turn.
    """
    turns: dict[str, dict[str, object]] = {}
    for rec in records:
        if rec.get("type") != "assistant":
            continue
        rid = rec.get("requestId")
        if not isinstance(rid, str) or not rid:
            continue
        message = rec.get("message")
        if not isinstance(message, dict):
            continue
        entry = turns.setdefault(
            rid,
            {
                "tools": [],
                "sidechain": bool(rec.get("isSidechain")),
                "cache_read": 0,
                "timestamp": rec.get("timestamp"),
            },
        )
        usage = message.get("usage")
        if isinstance(usage, dict):
            # Usage repeats across the streamed lines of one turn — take the max
            # rather than summing, or a 3-line turn triples its own cache read.
            read = usage.get("cache_read_input_tokens") or 0
            if isinstance(read, int):
                entry["cache_read"] = max(int(entry["cache_read"]), read)
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = block.get("name")
                if isinstance(name, str):
                    tools = entry["tools"]
                    assert isinstance(tools, list)
                    tools.append(name)
    return turns


def _analyse(turns: dict[str, dict[str, object]]) -> dict[str, object]:
    ordered = sorted(turns.values(), key=lambda e: str(e.get("timestamp") or ""))
    total_calls = 0
    collapsible = 0
    multi_block_turns = 0
    single_block_turns = 0
    tool_free_turns = 0
    chains: collections.Counter[str] = collections.Counter()
    cache_reads: list[int] = []
    prev_single: str | None = None

    for entry in ordered:
        tools = entry["tools"]
        assert isinstance(tools, list)
        total_calls += len(tools)
        read = entry["cache_read"]
        if isinstance(read, int) and read > 0:
            cache_reads.append(read)
        if not tools:
            tool_free_turns += 1
            prev_single = None
            continue
        if len(tools) > 1:
            multi_block_turns += 1
            prev_single = None
            continue
        single_block_turns += 1
        only = str(tools[0])
        if prev_single is not None and prev_single == only:
            collapsible += 1
            chains[only] += 1
        prev_single = only

    pct = (collapsible / total_calls * 100.0) if total_calls else 0.0
    mean_read = int(sum(cache_reads) / len(cache_reads)) if cache_reads else 0
    return {
        "turns": len(ordered),
        "total_calls": total_calls,
        "collapsible": collapsible,
        "collapsible_pct": pct,
        "multi_block_turns": multi_block_turns,
        "single_block_turns": single_block_turns,
        "tool_free_turns": tool_free_turns,
        "mean_cache_read": mean_read,
        "worst_tools": chains.most_common(8),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=float, default=1.0, help="trailing window in days (default 1)")
    parser.add_argument("--session", default="", help="restrict to one sessionId (transcript file stem)")
    parser.add_argument("--strict", action="store_true", help="exit 1 when worse than the baseline")
    parser.add_argument("--include-sidechains", action="store_true", help="fold sub-agent turns into the main figure")
    args = parser.parse_args()

    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=args.days)
    pattern = f"{ROOT}/**/{args.session}*.jsonl" if args.session else f"{ROOT}/**/*.jsonl"
    paths = glob.glob(pattern, recursive=True)
    if not paths:
        print(f"no transcripts under {ROOT} (looked for {pattern})", file=sys.stderr)
        return 0

    turns = _collect_turns(_iter_records(paths, cutoff))
    if not args.include_sidechains:
        main_turns = {k: v for k, v in turns.items() if not v.get("sidechain")}
        side_turns = {k: v for k, v in turns.items() if v.get("sidechain")}
    else:
        main_turns, side_turns = turns, {}

    stats = _analyse(main_turns)
    window = f"last {args.days:g}d"
    print(f"tool-call batching — {window}, {len(paths)} transcript file(s)")
    print(f"  turns with a model response : {stats['turns']}")
    print(f"  tool calls                  : {stats['total_calls']}")
    print(f"  batched turns (>1 block)    : {stats['multi_block_turns']}")
    print(f"  single-call turns           : {stats['single_block_turns']}")
    print(f"  collapsible (same-tool run) : {stats['collapsible']}  = {stats['collapsible_pct']:.1f}%")
    print(f"  mean cache-read tokens/call : {stats['mean_cache_read']:,}")
    if side_turns:
        side = _analyse(side_turns)
        print(
            f"  [sub-agent turns, reported separately: {side['total_calls']} calls, "
            f"{side['collapsible_pct']:.1f}% collapsible]"
        )
    if stats["worst_tools"]:
        worst = ", ".join(f"{name} x{count}" for name, count in stats["worst_tools"])
        print(f"  chains by tool              : {worst}")

    pct = float(stats["collapsible_pct"])
    print(
        f"\nbaseline ({BASELINE_DATE}): {BASELINE_COLLAPSIBLE_PCT}% collapsible, "
        f"{BASELINE_MEAN_CACHE_READ:,} mean cache read"
    )
    if stats["total_calls"] == 0:
        print("VERDICT: no tool calls in window — nothing to judge.")
        return 0
    if pct > BASELINE_COLLAPSIBLE_PCT:
        print(f"VERDICT: ⚠️  WORSE than baseline by {pct - BASELINE_COLLAPSIBLE_PCT:.1f}pp — batch independent calls.")
        print("         See /codex/06-coding-standards/tool-call-batching.md § 'Do this'.")
        return 1 if args.strict else 0
    print(f"VERDICT: ✅ better than baseline by {BASELINE_COLLAPSIBLE_PCT - pct:.1f}pp.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
