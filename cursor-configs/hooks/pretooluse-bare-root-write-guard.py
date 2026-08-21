#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""PreToolUse guard: warn (never block) when an Edit/Write targets a BARE-ROOT checkout that
has an active `.tabs/<N>/` sibling for the same repo.

WHY THIS EXISTS. Per-tab-worktrees model: every interactive session and every dispatched worker
IS a slot, and is meant to write only inside `.tabs/<N>/<repo>/...`
(`/codex/05-infrastructure/per-tab-worktrees.md`). Today that is discipline, not enforcement --
CLAUDE.md's own text says a bare `<repo>` path "succeeds but is NEVER your slot ... nothing
auto-cleans it". Measured 2026-08-21 (model_capability_aware_dispatch_audit_2026_08_21.md
Progress Log): a sequence of confused backgrounded/nohup Bash commands left an interactive
session believing it was editing `.tabs/13/agent-orchestrator` while several `Edit` calls
actually landed in the BARE `agent-orchestrator` checkout -- `orchestrator.service`'s live
`WorkingDirectory`, which `ao-self-pull.sh`'s 2-minute cron actively manages. That wedged the
self-pull cron for 20+ minutes (silently -- its Slack alert is a separate, already-tracked gap).
Recovered with zero data loss only because the session happened to notice a suspiciously clean
QG run and went looking with `git -C <path>` diagnostics on both checkouts. Nothing would have
caught it automatically.

WHY WARN, NOT BLOCK. The sibling guard (`pretooluse-slot-collision-guard.py`) hard-blocks a
narrow, specific action class (shared-index mutation with a live peer) BECAUSE it can tell, from
the command text alone, that the action is unconditionally risky. This guard cannot: a bare-root
Edit/Write may be a genuinely intentional, operator-directed host-level change (CLAUDE.md's own
per-tab-worktrees section allows this), and this hook has no way to distinguish that from an
accidental drift like the incident above. A hard block here would have the same false-positive
cost profile the sibling guard's own operator ruling explicitly weighed against (2026-08-12,
option B) -- except worse, because Edit/Write (unlike a Bash command string) has no natural place
to put a command-prefix escape hatch. PreToolUse's `permissionDecision: "allow"` +
`additionalContext` output (confirmed against Claude Code's own hook docs, 2026-08-21) is exactly
the middle ground SessionStart already uses for the adjacent slot-COLLISION warning: the edit
proceeds unconditionally (zero blast-radius risk -- this can never wedge a legitimate write), but
the agent sees a hard-to-miss, structured warning in its own context and can self-correct before
compounding the mistake. Mechanical enforcement of NOTICING, not of refusing.

WHY THIS DOES NOT COVER BASH. `block_destructive_commands.py` deliberately matches specific
dangerous VERBS rather than trying to determine an arbitrary command's write target -- reliably
extracting "what file does `sed -i ... some/computed/$path`" write to" from shell text is a much
harder, more false-positive-prone problem than reading Edit/Write's own structured `file_path`
field. The measured incident was Edit calls; this hook is scoped to what it can detect reliably.
A Bash-side equivalent is explicitly out of scope here, not silently forgotten -- see
`model_capability_aware_dispatch_audit_2026_08_21.md` Part 4's design note.

DETECTION. Reuses `lib/slot-collision-detect.sh`'s `bare-root-repo` CLI verb (the SAME shared
library the collision guard and SessionStart hook already source, per that file's own "one
implementation, one place to fix" rationale) -- purely path-based, no dependency on
`$CLAUDE_PROJECT_DIR` (which reflects wherever the CALLING session is rooted, not necessarily the
workspace the TARGET file lives under). Fires only when a `.tabs/*/<repo>` sibling actually
exists for the target repo, so a repo that has never used the slot model produces no noise.

Exit codes: always 0 (never blocks). A malformed payload, an unreadable detector, or any other
failure degrades to silent allow -- this is a visibility backstop, not a gate.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_DETECT_LIB = Path(__file__).resolve().parent / "lib" / "slot-collision-detect.sh"

_WARNING_TEMPLATE = (
    "BARE-ROOT WRITE WARNING: {file_path} is under the BARE checkout of `{repo}` "
    "({root}/{repo}), not a `.tabs/<N>/{repo}` slot -- even though slot(s) already exist for "
    "this repo. If you meant to work in your assigned slot: STOP, verify your real cwd/slot "
    "number, and redo this edit at the correct `.tabs/<N>/{repo}/...` path instead. A stray "
    "bare-root edit can silently wedge a live service (agent-orchestrator's "
    "orchestrator.service self-pulls this exact checkout every 2 minutes and stalls on any "
    "dirty tree) or land under the wrong git identity. This warning never blocks the edit -- if "
    "this IS a deliberate operator-directed host-level change, ignore it.\n"
    "SSOT: /codex/05-infrastructure/per-tab-worktrees.md"
)


def _bare_root_hit(file_path: str) -> tuple[str, str] | None:
    """Run the shared detector. Returns (workspace_root, repo), or None on no-hit / any
    failure -- fail open, matching every other consumer of this shared library."""
    try:
        proc = subprocess.run(
            ["bash", str(_DETECT_LIB), "bare-root-repo", file_path],
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    out = proc.stdout.strip()
    if not out:
        return None
    parts = out.split(" ", 1)
    if len(parts) != 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1]


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return 0
    if not isinstance(payload, dict) or payload.get("tool_name") not in ("Edit", "Write"):
        return 0

    tool_input = payload.get("tool_input")
    file_path = tool_input.get("file_path") if isinstance(tool_input, dict) else None
    if not isinstance(file_path, str) or not file_path.strip():
        return 0

    hit = _bare_root_hit(file_path)
    if hit is None:
        return 0
    root, repo = hit

    warning = _WARNING_TEMPLATE.format(file_path=file_path, root=root, repo=repo)
    sys.stdout.write(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "additionalContext": warning,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
