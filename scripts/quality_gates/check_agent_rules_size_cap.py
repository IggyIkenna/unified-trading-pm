#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
# Delete-when: NA
"""Hard-cap the agent rule files so they cannot regress to bloat.

CLAUDE.md and SUB_AGENT_MANDATORY_RULES.md are a "lean index" by design: each rule is a
1-line directive + a pointer to its codex SSOT, and the *detail* lives in codex — never inline.
They keep silently re-bloating (agents append full incident narratives instead of condensing),
so this gate makes the cap machine-enforced instead of merely "review-blocking".

Caps are in BYTES (the SSOT for the cap). ~4 bytes/token, so the byte cap doubles as a token
budget: 40 KiB ≈ 10k tokens (CLAUDE.md), 10 KiB ≈ 2.5k tokens (SUB_AGENT_MANDATORY_RULES.md).

When this fails: DO NOT raise the cap. Condense a rule to its 1-line directive + codex pointer
and migrate the detail into the named codex SSOT. Growing the cap defeats the gate's purpose.

Soft WARN threshold (2026-08-07, incident: CLAUDE.md sat at 40,929/40,960 B — 31 B of headroom —
before anyone noticed, forcing an emergency same-session trim instead of a routine one): at
WARN_RATIO of the cap (38 KiB / 40 KiB = 95%), print a non-blocking warning so size creep is
visible many commits before it re-accelerates into another hard-cap emergency. Exit code is
UNAFFECTED by a WARN — only OVER-cap fails the gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

KIB = 1024

# Byte caps per agent-rules file (path is repo-root-relative). These ARE the hard cap.
CAPS: dict[str, int] = {
    "cursor-configs/CLAUDE.md": 40 * KIB,
    "cursor-configs/SUB_AGENT_MANDATORY_RULES.md": 10 * KIB,
}

# Soft warn threshold as a fraction of each file's hard cap — 0.95 == 38 KiB for the 40 KiB
# CLAUDE.md cap. Advisory only: crossing this prints a WARN line but never fails the gate.
WARN_RATIO = 0.95


def _repo_root() -> Path:
    # scripts/quality_gates/<this file> -> parents[2] == PM repo root
    return Path(__file__).resolve().parents[2]


def main() -> int:
    repo_root = _repo_root()
    failures: list[str] = []
    warnings: list[str] = []

    print("Agent-rules size cap (CLAUDE.md / SUB_AGENT_MANDATORY_RULES.md):")
    for rel, cap in sorted(CAPS.items()):
        path = repo_root / rel
        if not path.is_file():
            print(f"  [MISSING] {rel}")
            failures.append(f"{rel} is missing — expected an agent-rules file at this path")
            continue
        size = path.stat().st_size
        approx_tokens = size // 4
        warn_at = int(cap * WARN_RATIO)
        over = size > cap
        nearing = size > warn_at and not over
        marker = "OVER" if over else "WARN" if nearing else "ok"
        print(f"  [{marker:>4}] {rel}: {size:,} B (~{approx_tokens:,} tok) / cap {cap:,} B")
        if over:
            failures.append(
                f"{rel} is {size:,} B (~{approx_tokens:,} tok), OVER the {cap:,} B hard cap by "
                f"{size - cap:,} B. Condense a rule to a 1-line directive + codex pointer and "
                f"migrate the detail into its codex SSOT. Do NOT raise the cap."
            )
        elif nearing:
            warnings.append(
                f"{rel} is {size:,} B — past the {warn_at:,} B ({WARN_RATIO:.0%}) warn threshold, "
                f"only {cap - size:,} B of headroom left before the {cap:,} B hard cap. Condense a "
                f"rule now, routinely, before it becomes an emergency trim."
            )

    if warnings:
        print("\n⚠️  agent-rules size approaching cap:")
        for w in warnings:
            print(f"  - {w}")

    if failures:
        print("\n❌ agent-rules size cap violation:", file=sys.stderr)
        for f in failures:
            print(f"  - {f}", file=sys.stderr)
        print(
            "\n   SSOT for this rule: CLAUDE.md header § 'Size budget' "
            "(lean index = directive + codex pointer; detail lives in codex).",
            file=sys.stderr,
        )
        return 1

    print("✅ all agent-rules files within hard cap" + (" (with warnings above)" if warnings else ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
