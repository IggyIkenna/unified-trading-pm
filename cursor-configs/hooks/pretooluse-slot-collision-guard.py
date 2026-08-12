#!/usr/bin/env python3
# Epic: infrastructure_master
# Lifecycle: permanent
# Delete-when: NA
"""PreToolUse guard: refuse a shared-index mutation while a live peer session occupies this slot.

Operator ruling 2026-08-12 (option B in
``plans/active/issues/pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md``):
re-check occupancy **at the moment of mutation** rather than only at session start.

WHY A SESSION-START WARNING WAS NOT ENOUGH. ``session-start-collision-check.sh`` fires once, when
the session opens. The measured incident had the peer session arrive *later* and destroy
uncommitted work twice inside 30 minutes -- long after any start-time warning had scrolled away.
A guard that evaluates when the risky command actually runs is the only one that can see the
collision that matters. Under ``bypassPermissions`` the ``permissions.deny`` list is discarded
entirely, so hooks are the only surviving guardrail
(``plans/active/issues/claude_settings_symlink_writeback_drops_hooks_2026_08_11.md``).

WHAT IT BLOCKS -- deliberately narrow, because a mid-task block is far more expensive per false
positive than a skippable warning (the operator flagged exactly this cost when choosing B):

  * a bare ``git commit`` -- mutates the SHARED index, which is the surface that gets contaminated
    by a peer's staged files and mis-attributed by a shared ``.git/config``;
  * ``quickmerge.sh --no-isolated`` and ``safe-doc-push.sh`` under ``SDP_ISOLATED=0`` -- the
    explicitly de-isolated variants, which commit from the shared index too.

WHAT IT DOES **NOT** BLOCK, and why that is the point. A default ``quickmerge.sh`` or
``safe-doc-push.sh`` commits from a private worktree and is therefore the REMEDY for this hazard,
not an instance of it. Blocking those would push an agent toward a bare ``git commit`` -- strictly
worse. Anything already running inside a linked worktree is likewise exempt: the mutation targets
a private index that no peer reconcile can reach.

FAIL-OPEN, ALWAYS. Every error path allows the command. A guard that blocks because it could not
parse its own input, or because ``pgrep`` is missing, would wedge a worker on every commit -- and
this is a backstop, not the sole control.

Escape hatch: prefix the command with ``SLOT_COLLISION_GUARD=0``, printed in the block message.
It is matched in the COMMAND STRING, not read from this process's environment -- the hook runs as
a child of the CLI, not of the user's command, so an ``os.environ`` read could never see a
``VAR=0 cmd`` prefix. Reading the environment here would have produced an escape hatch that
silently did nothing (caught by the env-canon gate, 2026-08-12, before it shipped).
"""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from pathlib import Path

_ALLOW = 0
_BLOCK = 2

# `git`'s own options that consume the FOLLOWING token, so the subcommand scan skips their values
# rather than mistaking one for the subcommand (`git -C /path commit` must still be seen).
_GIT_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--exec-path"}

_DETECT_LIB = Path(__file__).resolve().parent / "lib" / "slot-collision-detect.sh"


def _git_subcommand(tokens: list[str]) -> str | None:
    """First non-option token after `git`, or None. Value-taking options are skipped."""
    try:
        idx = next(i for i, t in enumerate(tokens) if t == "git" or t.endswith("/git"))
    except StopIteration:
        return None
    i = idx + 1
    while i < len(tokens):
        tok = tokens[i]
        if tok in _GIT_OPTS_WITH_VALUE:
            i += 2
            continue
        if tok.startswith("-"):
            i += 1
            continue
        return tok
    return None


def risky_reason(command: str) -> str | None:
    """Why this command mutates the SHARED index, or None if it is safe/irrelevant.

    Split on shell separators so a compound `cd x && git commit` is still seen; `shlex` keeps
    quoted strings intact so `git commit -m "fix commit bug"` cannot self-match on its message.
    """
    try:
        tokens = shlex.split(command)
    except ValueError:
        return None  # unbalanced quotes -- not parseable, fail open

    segments: list[list[str]] = [[]]
    for tok in tokens:
        if tok in ("&&", "||", ";", "|"):
            segments.append([])
        else:
            segments[-1].append(tok)

    for seg in segments:
        if not seg:
            continue
        joined = " ".join(seg)
        if _git_subcommand(seg) == "commit":
            return "a bare `git commit` writes the SHARED index of this slot's checkout"
        if any(t.endswith("quickmerge.sh") for t in seg) and "--no-isolated" in seg:
            return "`quickmerge.sh --no-isolated` commits from the shared index, not a private worktree"
        if any(t.endswith("safe-doc-push.sh") for t in seg) and "SDP_ISOLATED=0" in joined:
            return "`safe-doc-push.sh` with SDP_ISOLATED=0 commits from the shared index"
    return None


def _detect(subcmd: str, arg: str) -> tuple[int, str]:
    """Run the shared detector. Returns (returncode, stdout); (1, "") on any failure."""
    try:
        # Fixed argv, no shell: the only interpolated values are a subcommand literal and a
        # path this process derived itself.
        proc = subprocess.run(
            ["bash", str(_DETECT_LIB), subcmd, arg],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return (1, "")
    return (proc.returncode, proc.stdout.strip())


def main() -> int:
    raw = sys.stdin.read()
    try:
        payload = json.loads(raw) if raw.strip() else {}
    except json.JSONDecodeError:
        return _ALLOW
    if not isinstance(payload, dict) or payload.get("tool_name") != "Bash":
        return _ALLOW

    tool_input = payload.get("tool_input")
    command = tool_input.get("command", "") if isinstance(tool_input, dict) else ""
    if not isinstance(command, str) or not command.strip():
        return _ALLOW

    # Escape hatch, matched as a command prefix (see the module docstring for why not env).
    if "SLOT_COLLISION_GUARD=0" in command:
        return _ALLOW

    reason = risky_reason(command)
    if reason is None:
        return _ALLOW

    cwd = payload.get("cwd")
    if not isinstance(cwd, str) or not cwd:
        cwd = str(Path.cwd())

    # Already committing against a private index -- exactly what we want people doing.
    if _DETECT_LIB.is_file() and _detect("is-linked-worktree", cwd)[0] == 0:
        return _ALLOW

    slot_dir = _detect("slot-dir", cwd)[1]
    if not slot_dir:
        return _ALLOW  # not in a .tabs/<N> slot -- no shared-checkout hazard this guard models

    pids_out = _detect("foreign-pids", slot_dir)[1]
    pids = [p for p in pids_out.split() if p.isdigit()]
    if not pids:
        return _ALLOW

    sys.stderr.write(
        f"BLOCKED — another live Claude session is working in this slot right now.\n"
        f"\n"
        f"  slot:    {slot_dir}\n"
        f"  peer(s): {len(pids)} live process(es) — PID {', '.join(pids)}\n"
        f"  why:     {reason}\n"
        f"\n"
        f"Two sessions sharing one checkout is how uncommitted work gets destroyed here: a peer's\n"
        f"reconcile reverts your tracked files with no error and a clean `git status`, and a shared\n"
        f".git/config can land your commit under their identity. Measured twice in 30 minutes on\n"
        f"2026-08-11 (pm_repo_commit_rate_exceeds_precommit_hook_duration_2026_08_10.md).\n"
        f"\n"
        f"Do this instead — commit from a private worktree that no peer reconcile can reach:\n"
        f"  bash scripts/dev/ship-from-worktree.sh setup\n"
        f"  cd <printed path> && <your command>\n"
        f"Default `quickmerge.sh` / `safe-doc-push.sh` already isolate and are NOT blocked.\n"
        f"\n"
        f"If you are certain (e.g. the peer is idle, or you are deliberately sharing the slot),\n"
        f"prefix the command — this is matched in the command text, not the environment:\n"
        f"  SLOT_COLLISION_GUARD=0 <your command>\n"
    )
    return _BLOCK


if __name__ == "__main__":
    sys.exit(main())
