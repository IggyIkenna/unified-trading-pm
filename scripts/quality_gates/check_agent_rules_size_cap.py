#!/usr/bin/env python3
# Epic: agent_operating_framework_master
# Lifecycle: permanent
"""Hard-cap the agent rule files so they cannot regress to bloat.

CLAUDE.md and SUB_AGENT_MANDATORY_RULES.md are a "lean index" by design: each rule is a
1-line directive + a pointer to its codex SSOT, and the *detail* lives in codex — never inline.
They keep silently re-bloating (agents append full incident narratives instead of condensing),
so this gate makes the cap machine-enforced instead of merely "review-blocking".

Caps are in BYTES (the SSOT for the cap). ~4 bytes/token, so the byte cap doubles as a token
budget: 40 KiB ≈ 10k tokens (CLAUDE.md), 10 KiB ≈ 2.5k tokens (SUB_AGENT_MANDATORY_RULES.md).

When this fails: DO NOT raise the cap. Condense a rule to its 1-line directive + codex pointer
and migrate the detail into the named codex SSOT. Growing the cap defeats the gate's purpose.
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


def _repo_root() -> Path:
    # scripts/quality_gates/<this file> -> parents[2] == PM repo root
    return Path(__file__).resolve().parents[2]


def main() -> int:
    repo_root = _repo_root()
    failures: list[str] = []

    print("Agent-rules size cap (CLAUDE.md / SUB_AGENT_MANDATORY_RULES.md):")
    for rel, cap in sorted(CAPS.items()):
        path = repo_root / rel
        if not path.is_file():
            print(f"  [MISSING] {rel}")
            failures.append(f"{rel} is missing — expected an agent-rules file at this path")
            continue
        size = path.stat().st_size
        approx_tokens = size // 4
        over = size > cap
        marker = "OVER" if over else "ok"
        print(
            f"  [{marker:>4}] {rel}: {size:,} B (~{approx_tokens:,} tok) / cap {cap:,} B"
        )
        if over:
            failures.append(
                f"{rel} is {size:,} B (~{approx_tokens:,} tok), OVER the {cap:,} B hard cap by "
                f"{size - cap:,} B. Condense a rule to a 1-line directive + codex pointer and "
                f"migrate the detail into its codex SSOT. Do NOT raise the cap."
            )

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

    print("✅ all agent-rules files within hard cap")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
