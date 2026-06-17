#!/usr/bin/env python3
"""Compute the SINCE-LAST-PROMOTE range for the strict-quickmerge provenance gate.

The promote bots (`ldr-to-staging-promote.yml` / `ldr-to-main-promote.yml`) must run
`check_strict_quickmerge.py` over the commits added to `live-defi-rollout` SINCE the
LAST drain to the target branch — NOT the raw `<target>..LDR` range.

WHY (the bug this fixes — `provenance_gate_squash_perpetual_block_2026_06_17.md`):
promotes are SQUASH merges, so an already-promoted commit's SHA never lands on the
target branch AND its individual patch-id ≠ the squash's combined patch-id. So
`git rev-list`/`git cherry`/`merge-base` over `<target>..LDR` cannot tell that an
already-drained commit was promoted → the historical hardcoded
`--range origin/staging..origin/live-defi-rollout` (resp. `origin/main..…`) re-flags a
one-time trailer-less commit on EVERY subsequent drain, forever (the `14b11e2` /
`06a83fb6` recurring "Provenance gate BLOCKED"; each drain needed a manual admin merge).

THE MARKER (no new persistent state): the head SHA (`headRefOid`) of the LAST MERGED
`<head_branch>`→`<base_branch>` promote PR. For a merged PR the head SHA is frozen at
merge time — i.e. exactly the LDR SHA that was promoted in the last drain — so it IS
the "last-promoted LDR SHA per repo" the contract calls for, with nothing to maintain
(no tag-move step, no state file, no write race). The provenance check then runs
`<marker>..origin/live-defi-rollout` — only commits since the last drain. An
already-drained commit (≤ marker) drops out of range permanently; a genuine new
direct-push (after the marker) is still flagged.

FAIL-SAFE (HARD): if no merged promote PR exists yet (first drain), OR the marker SHA
is empty/unreachable as a commit object in the current git repo, FALL BACK to the raw
`<base_ref>..<ldr_ref>` range. A stale/missing marker must WIDEN the range (over-flag),
NEVER narrow it to miss a genuine new bypass. (The pre-push hook range
`origin/live-defi-rollout..HEAD` is already a since-base range and is unaffected — this
helper is only for the promote bots.)

SSOT: `plans/active/issues/provenance_gate_squash_perpetual_block_2026_06_17.md`,
`codex/08-workflows/ci-cd-flow.md` § "The promote bot promotes only quickmerge-provenanced
content (D1)".

Usage (prints the resolved range to stdout, a one-line diagnostic to stderr):
    promote_provenance_range.py --repo unified-trading-library --base-branch staging \
        --cwd "$PROV_TMP" --fetch-remote "https://x-access-token:$TOK@github.com/IggyIkenna/<repo>"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from typing import cast

LDR = "live-defi-rollout"


def resolve_range(
    marker: str | None,
    *,
    base_ref: str,
    ldr_ref: str,
    marker_reachable: bool,
) -> tuple[str, str]:
    """Return ``(range, mode)`` for the provenance check.

    A present, reachable marker → ``"<marker>..<ldr_ref>"`` (``mode="marker"``): only the
    commits added to LDR since the last drain. Otherwise → ``"<base_ref>..<ldr_ref>"``
    (``mode="fallback"``): the FAIL-SAFE raw range — widen (over-flag), never narrow.
    """
    if marker and marker_reachable:
        return f"{marker}..{ldr_ref}", "marker"
    return f"{base_ref}..{ldr_ref}", "fallback"


def _run(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return proc.returncode, proc.stdout


def last_promoted_marker(
    owner: str,
    repo: str,
    base_branch: str,
    head_branch: str = LDR,
) -> str | None:
    """``headRefOid`` of the most-recently MERGED ``head_branch``→``base_branch`` promote PR.

    Returns ``None`` when there is no merged promote PR yet, the ``gh`` query fails, or the
    payload is malformed — every such case triggers the fail-safe fallback in the caller.
    """
    rc, out = _run(
        [
            "gh",
            "pr",
            "list",
            "--repo",
            f"{owner}/{repo}",
            "--base",
            base_branch,
            "--head",
            head_branch,
            "--state",
            "merged",
            "--json",
            "headRefOid,mergedAt",
            "--limit",
            "1",
        ]
    )
    if rc != 0 or not out.strip():
        return None
    try:
        raw = cast(object, json.loads(out))
    except json.JSONDecodeError:
        return None
    if not isinstance(raw, list):
        return None
    items = cast("list[object]", raw)
    if not items:
        return None
    first = items[0]
    if not isinstance(first, dict):
        return None
    record = cast("dict[str, object]", first)
    sha_obj = record.get("headRefOid")
    sha = sha_obj.strip() if isinstance(sha_obj, str) else ""
    return sha or None


def commit_reachable(ref: str, cwd: str | None = None) -> bool:
    """True iff ``ref`` resolves to a commit object in the repo at ``cwd``."""
    rc, _ = _run(["git", "cat-file", "-e", f"{ref}^{{commit}}"], cwd=cwd)
    return rc == 0


def try_fetch_sha(remote: str, sha: str, cwd: str | None = None) -> None:
    """Best-effort: make a non-ancestor marker reachable (GitHub allows reachable-SHA fetch).

    A no-op on failure — the caller re-checks reachability and falls back if still absent.
    """
    _run(["git", "fetch", "-q", "--no-tags", remote, sha], cwd=cwd)


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute the since-last-promote provenance range.")
    ap.add_argument("--owner", default="IggyIkenna")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base-branch", required=True, choices=["staging", "main"])
    ap.add_argument("--base-ref", default=None, help="fallback base ref (default origin/<base-branch>)")
    ap.add_argument("--ldr-ref", default=f"origin/{LDR}")
    ap.add_argument("--head-branch", default=LDR)
    ap.add_argument("--cwd", default=None, help="git repo dir in which to resolve refs (default: cwd)")
    ap.add_argument(
        "--fetch-remote",
        default=None,
        help="remote URL to best-effort fetch an unreachable marker SHA before falling back",
    )
    args = ap.parse_args()

    owner = cast(str, args.owner)
    repo = cast(str, args.repo)
    base_branch = cast(str, args.base_branch)
    base_ref = cast("str | None", args.base_ref) or f"origin/{base_branch}"
    ldr_ref = cast(str, args.ldr_ref)
    head_branch = cast(str, args.head_branch)
    cwd = cast("str | None", args.cwd)
    fetch_remote = cast("str | None", args.fetch_remote)

    marker = last_promoted_marker(owner, repo, base_branch, head_branch)
    reachable = False
    if marker:
        reachable = commit_reachable(marker, cwd=cwd)
        if not reachable and fetch_remote:
            try_fetch_sha(fetch_remote, marker, cwd=cwd)
            reachable = commit_reachable(marker, cwd=cwd)

    rng, mode = resolve_range(marker, base_ref=base_ref, ldr_ref=ldr_ref, marker_reachable=reachable)
    # Range → stdout (the workflow captures it). Diagnostic → stderr (never echoes the
    # token-bearing fetch remote). A stale/missing marker is the EXPECTED fail-safe, not an error.
    print(rng)
    print(
        f"promote-provenance-range[{repo}→{base_branch}]: mode={mode} "
        f"marker={marker or '∅'} reachable={reachable} → {rng}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
