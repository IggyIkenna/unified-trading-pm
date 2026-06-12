#!/usr/bin/env python3
"""Credential-ask orphan QG check.

Per CLAUDE.md "External Data Is Always Available — Never Silently Defer Adapters" (HARD RULE):
every `BLOCKED-CREDENTIALS` plan item MUST cite an operator credential-ask ping
(filed in `<side>_orchestrator/pings/slot_<N>.md` or `_agent_pings.md`) so the
operator can action it. Orphan `BLOCKED-CREDENTIALS` items — items lacking any
ping reference, `CREDENTIAL APPROVAL REQUEST`, secret-name, or `[ack]` token
in their immediate context — block dispatch silently.

This check walks `plans/active/*.md`, finds every `BLOCKED-CREDENTIALS` line,
and reports any without a recognisable ping-reference token in ±5 lines of
context.

Baseline-ratchet semantics (matching codex_doc_freshness + plan_discipline):
  --baseline-write writes current orphan count to
    `scripts/quality_gates/credential_ask_orphans_baseline.yaml`.
  Default mode fails if orphan count exceeds baseline.

Exit codes:
  0 — at-or-below baseline (clean)
  1 — regression (more orphans than baseline)
  2 — argument / IO error

SSOT: CLAUDE.md § "External Data Is Always Available" (2026-05-14 codification).
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_BASELINE_PATH = Path(__file__).parent / "credential_ask_orphans_baseline.yaml"

# Active plans where BLOCKED-CREDENTIALS items aggregate / track but don't originate.
# These reference other plans; their occurrences are NOT orphans by design.
SUMMARY_PLAN_NAMES = {
    "master_to_live_defi_2026_05_23.md",
    "human_work_backlog_2026_05_20.md",
    "_agent_pings.md",
}

# Tokens accepted as evidence that an operator ask has been filed.
PING_PATH_RE = re.compile(r"(ikenna|harsh)_orchestrator/(?:pings/slot_\d+|_agent_pings)\.md")
ACK_TOKENS = (
    "CREDENTIAL APPROVAL REQUEST",
    "[ack]",
    "[ACK]",
    "[ack-pending]",
    "CONFIRMED-STATUS",
    "DEFERRED-OPERATOR-DECISION",  # operator has explicitly articulated descope
)
# Common secret-name patterns (operator has named the SM key needed)
SECRET_NAME_RE = re.compile(r"\b[a-z][a-z0-9-]+-(api-key|api-secret|secret-key|private-key|passphrase|pem)\b")

BLOCKED_RE = re.compile(r"BLOCKED-CREDENTIALS")

# A line that enumerates MULTIPLE distinct BLOCKED-* status tokens is DEFINING the status
# taxonomy / restating the rule (e.g. "set (BLOCKED-CREDENTIALS / BLOCKED-OPERATOR-DECISION / …)"
# or "BLOCKED-CREDENTIALS/BLOCKED-UPSTREAM ping (do not descope)") — it is documentation, not a
# credential ASK, so it can never cite a ping and must NOT count as an orphan (added 2026-06-09 to
# de-false-positive the ratchet). A genuine ask names exactly one blocked status for one cell.
BLOCKED_STATUS_TOKEN_RE = re.compile(r"BLOCKED-[A-Z][A-Z-]+")

# The ping rule binds "BLOCKED-CREDENTIALS plan ITEMS" (CLAUDE.md) — and an ORPHAN is an OPEN ask
# lacking a ping. A plan item is a checkbox todo (PLAN_FORMAT), but only an OPEN `- [ ]` item is a
# live, actionable ask: a COMPLETED `- [x] ✅` credential item is resolved (the credential was
# obtained / the ask was acked or descoped), so it can never be an orphan — its ping may legitimately
# have aged out / been archived. Counting `[x]` items inflated the orphan count by 10 grandfathered
# completed asks (residual, 2026-06-12 — dependency_promotion plan Phase 3). Bare prose that merely
# MENTIONS the token — narrative ("the two BLOCKED-CREDENTIALS items below"), results-line
# parentheticals ("Kalshi 0 records (BLOCKED-CREDENTIALS — expected)"), findings, or backtick-quoted
# token references (`BLOCKED-CREDENTIALS`) — is NOT a plan item, can never cite a ping, and must not
# count (the prose-mention false-positive class, 2026-06-11). This is a PRECISION fix: every real
# orphan ASK is still an OPEN checkbox item, so no real orphan is missed.
CHECKBOX_ITEM_RE = re.compile(r"^\s*[-*]\s*\[ \]")
BACKTICKED_BLOCKED_RE = re.compile(r"`[^`]*BLOCKED-CREDENTIALS[^`]*`")

CONTEXT_LINES = 5


def _is_status_taxonomy_line(line: str) -> bool:
    """True if the line enumerates ≥2 distinct BLOCKED-* status tokens (a rule/taxonomy doc line)."""
    return len(set(BLOCKED_STATUS_TOKEN_RE.findall(line))) >= 2


def _is_credential_ask_item(line: str) -> bool:
    """True iff the line is an OPEN (`- [ ]`) checkbox plan ITEM declaring a (non-backtick-quoted)
    BLOCKED-CREDENTIALS status — i.e. a live, actionable ask the ping rule governs, not a prose
    mention/finding/token ref and not a COMPLETED (`- [x]`) item (a resolved ask is never an orphan)."""
    if not CHECKBOX_ITEM_RE.match(line):
        return False  # prose / results note / finding / COMPLETED `[x]` item — not a live open ask
    # the occurrence must be a STATUS, not a backtick-quoted reference to the concept
    return "BLOCKED-CREDENTIALS" in BACKTICKED_BLOCKED_RE.sub("", line)


def _has_ask_evidence(lines: list[str], lineno: int) -> bool:
    """Check ±CONTEXT_LINES around lineno for any ask-evidence token."""
    start = max(0, lineno - CONTEXT_LINES)
    end = min(len(lines), lineno + CONTEXT_LINES + 1)
    blob = "\n".join(lines[start:end])
    if PING_PATH_RE.search(blob):
        return True
    if SECRET_NAME_RE.search(blob):
        return True
    return any(tok in blob for tok in ACK_TOKENS)


def _scan_plan(path: Path) -> list[tuple[int, str]]:
    """Return [(lineno, line_text), ...] for orphan BLOCKED-CREDENTIALS lines."""
    lines = path.read_text(encoding="utf-8").splitlines()
    orphans: list[tuple[int, str]] = []
    for i, line in enumerate(lines):
        if not BLOCKED_RE.search(line):
            continue
        if not _is_credential_ask_item(line):
            continue  # prose mention / results note / finding / backtick token ref — not a plan item
        if _is_status_taxonomy_line(line):
            continue  # rule/taxonomy doc line, not a credential ask
        if _has_ask_evidence(lines, i):
            continue
        orphans.append((i + 1, line.strip()))
    return orphans


def _scan_workspace() -> dict[str, list[tuple[int, str]]]:
    """Return {plan_rel_path: [orphan_tuples, ...]}."""
    active_dir = REPO_ROOT / "plans" / "active"
    results: dict[str, list[tuple[int, str]]] = {}
    for p in sorted(active_dir.glob("*.md")):
        if p.name in SUMMARY_PLAN_NAMES:
            continue
        orphans = _scan_plan(p)
        if orphans:
            results[str(p.relative_to(REPO_ROOT))] = orphans
    return results


def _load_baseline(path: Path) -> int:
    if not path.is_file():
        return 0
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return int(data.get("orphan_count", 0))


def _write_baseline(path: Path, count: int) -> None:
    path.write_text(
        yaml.dump({"orphan_count": count}, default_flow_style=False, sort_keys=False),
        encoding="utf-8",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--baseline-path",
        type=Path,
        default=DEFAULT_BASELINE_PATH,
        help="Path to baseline YAML (default: scripts/quality_gates/credential_ask_orphans_baseline.yaml)",
    )
    parser.add_argument(
        "--baseline-write",
        action="store_true",
        help="Write current orphan count to baseline path (use after intentional debt)",
    )
    parser.add_argument(
        "--show-orphans",
        action="store_true",
        help="Print every orphan line (default: just the count)",
    )
    args = parser.parse_args()

    results = _scan_workspace()
    total_orphans = sum(len(v) for v in results.values())

    if args.baseline_write:
        _write_baseline(args.baseline_path, total_orphans)
        print(f"Wrote baseline: {total_orphans} orphan BLOCKED-CREDENTIALS lines across {len(results)} plans")
        return 0

    baseline = _load_baseline(args.baseline_path)

    if args.show_orphans or total_orphans > baseline:
        for plan, items in results.items():
            print(f"\n  {plan}")
            for lineno, text in items:
                snippet = text[:120] + ("..." if len(text) > 120 else "")
                print(f"    L{lineno}: {snippet}")

    if total_orphans > baseline:
        print(
            f"\nERROR: {total_orphans} orphan BLOCKED-CREDENTIALS lines (baseline {baseline}). "
            f"Each must cite a ping (e.g. ikenna_orchestrator/pings/slot_N.md) or filed CREDENTIAL APPROVAL REQUEST.",
            file=sys.stderr,
        )
        print(
            "  Either: (a) file the ping + reference it in the plan line, or "
            "(b) if intentional debt, re-baseline with --baseline-write.",
            file=sys.stderr,
        )
        return 1

    print(f"OK — {total_orphans} orphan BLOCKED-CREDENTIALS (at-or-below baseline {baseline})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
