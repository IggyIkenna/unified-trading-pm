#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
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
promote PR into `<base_branch>`, identified by its stable `chore(promote)` TITLE prefix
(NOT by `--head` — promote PRs are opened with varying head-ref shapes across bot
variants: literally `live-defi-rollout` for the Tier-C/Option-B auto-drain bots, or the
WS-L Phase-0 per-SHA-ref `promote/<repo>/<sha>` for the fleet direct-promote bot; a
head-branch filter only matches the former and can never advance past a repo's
per-SHA-ref cutover — `promote_provenance_marker_stale_head_query_2026_07_13.md`). For a
merged PR the head SHA is frozen at merge time — i.e. exactly the LDR SHA that was
promoted in the last drain — so it IS the "last-promoted LDR SHA per repo" the contract
calls for, with nothing to maintain (no tag-move step, no state file, no write race). The
provenance check then runs `<marker>..origin/live-defi-rollout` — only commits since the
last drain. An already-drained commit (≤ marker) drops out of range permanently; a
genuine new direct-push (after the marker) is still flagged.

FAIL-SAFE (HARD): if no merged promote PR exists yet (first drain), OR the marker SHA
is empty/unreachable as a commit object in the current git repo, OR the marker SHA — even
though it exists as an object — is NOT a true git ANCESTOR of `ldr_ref`, FALL BACK to the
raw `<base_ref>..<ldr_ref>` range. A stale/missing/non-ancestor marker must WIDEN the range
(over-flag), NEVER narrow it to miss a genuine new bypass. (The pre-push hook range
`origin/live-defi-rollout..HEAD` is already a since-base range and is unaffected — this
helper is only for the promote bots.)

WHY OBJECT-EXISTENCE ALONE IS NOT ENOUGH (the bug this ALSO fixes —
`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`): a marker SHA
can keep resolving as a git object long after it is USELESS as a range start. GitHub serves
any SHA it still has, including one orphaned by a `git filter-repo`-style history rewrite (a
2026-08-05T11:24:53Z security-driven rewrite did exactly this to several repos). A pre-rewrite
marker then sits on a disconnected history line with essentially no useful common ancestor
against the post-rewrite `ldr_ref` — `commit_reachable()` alone still returns true, so the
"marker" mode range balloons to `<marker>..<ldr_ref>` spanning nearly the ENTIRE repo history
(observed: 3,701 commits back to a repo's Nov-2025 initial commit) instead of the real handful
of commits since the last promote, which then false-flags as quickmerge-bypass content and
deadlocks promotion. The fix: verify true ancestry via `git merge-base --is-ancestor <marker>
<ldr_ref>` (exit 0 = true ancestor) in addition to object existence — a marker that fails
ancestry falls through to the SAME safe fallback range as an unreachable one.

SSOT: `plans/active/issues/provenance_gate_squash_perpetual_block_2026_06_17.md`,
`plans/active/issues/provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`,
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
    marker_usable: bool,
) -> tuple[str, str]:
    """Return ``(range, mode)`` for the provenance check.

    A present, USABLE marker → ``"<marker>..<ldr_ref>"`` (``mode="marker"``): only the
    commits added to LDR since the last drain. Otherwise → ``"<base_ref>..<ldr_ref>"``
    (``mode="fallback"``): the FAIL-SAFE raw range — widen (over-flag), never narrow.

    "Usable" is the caller's job to establish and means BOTH the marker SHA exists as a
    commit object AND it is a true git ancestor of ``ldr_ref`` — object existence alone is
    NOT sufficient (see module docstring's "WHY OBJECT-EXISTENCE ALONE IS NOT ENOUGH").
    """
    if marker and marker_usable:
        return f"{marker}..{ldr_ref}", "marker"
    return f"{base_ref}..{ldr_ref}", "fallback"


def _run(cmd: list[str], cwd: str | None = None) -> tuple[int, str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return proc.returncode, proc.stdout


PROMOTE_TITLE_PREFIX = "chore(promote)"


def last_promoted_marker(
    owner: str,
    repo: str,
    base_branch: str,
) -> str | None:
    """``headRefOid`` of the most-recently MERGED promote PR into ``base_branch``.

    Filters by the stable ``chore(promote)`` TITLE prefix (every promote-bot variant sets it:
    `chore(promote): LDR → staging (Tier C auto-drain)`, `... main (Option-B auto-drain)`,
    `... main (Option-B direct)`), NOT by ``--head`` — the WS-L Phase-0 per-SHA-ref cutover
    (`ldr-to-main-promote-fleet.yml`) opens promote PRs with head ``promote/<repo>/<sha>``,
    never literally ``live-defi-rollout``, so a head-branch filter matches zero of those PRs and
    the marker can never advance (`promote_provenance_marker_stale_head_query_2026_07_13.md`).
    Title filtering is head-ref-shape-agnostic and works across every variant unchanged.

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
            "--state",
            "merged",
            "--json",
            "headRefOid,mergedAt,title",
            "--limit",
            "50",
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
    best_merged_at = ""
    best_sha: str | None = None
    for item in items:
        if not isinstance(item, dict):
            continue
        record = cast("dict[str, object]", item)
        title_obj = record.get("title")
        title = title_obj if isinstance(title_obj, str) else ""
        if not title.startswith(PROMOTE_TITLE_PREFIX):
            continue
        merged_at_obj = record.get("mergedAt")
        merged_at = merged_at_obj if isinstance(merged_at_obj, str) else ""
        sha_obj = record.get("headRefOid")
        sha = sha_obj.strip() if isinstance(sha_obj, str) else ""
        if not sha or not merged_at:
            continue
        if merged_at > best_merged_at:
            best_merged_at = merged_at
            best_sha = sha
    return best_sha


def commit_reachable(ref: str, cwd: str | None = None) -> bool:
    """True iff ``ref`` resolves to a commit object in the repo at ``cwd``.

    OBJECT EXISTENCE ONLY — NOT ancestry. A marker can pass this check while sitting on a
    disconnected history line (e.g. after a `git filter-repo`-style history rewrite) if the
    remote still serves the object; see `marker_is_ancestor` for the ancestry check that
    additionally guards against exactly that
    (`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`).
    """
    rc, _ = _run(["git", "cat-file", "-e", f"{ref}^{{commit}}"], cwd=cwd)
    return rc == 0


def marker_is_ancestor(marker: str, ldr_ref: str, cwd: str | None = None) -> bool:
    """True iff ``marker`` is a true git ANCESTOR of ``ldr_ref`` — not merely an existing object.

    THE BUG THIS FIXES (`provenance_marker_broken_by_history_rewrite_blocks_promotion_2026_08_06.md`):
    a history rewrite can leave a pre-rewrite marker SHA still resolvable as a git object (the
    remote keeps serving it) while it sits on a now-disconnected history line with essentially no
    useful common ancestor against the post-rewrite ``ldr_ref``. Object existence alone
    (`commit_reachable`) cannot detect this — only true ancestry can. Uses
    ``git merge-base --is-ancestor`` (exit 0 = true ancestor; exit 1 = not an ancestor; any other
    exit code, e.g. one ref not found locally, is also treated as NOT an ancestor — the safe
    direction, since it forces the caller's fail-safe fallback range rather than trusting an
    unverifiable marker).
    """
    rc, _ = _run(["git", "merge-base", "--is-ancestor", marker, ldr_ref], cwd=cwd)
    return rc == 0


def try_fetch_sha(remote: str, sha: str, cwd: str | None = None) -> None:
    """Best-effort: make a non-local marker reachable (GitHub allows reachable-SHA fetch).

    A no-op on failure — the caller re-checks reachability and falls back if still absent.
    """
    _run(["git", "fetch", "-q", "--no-tags", remote, sha], cwd=cwd)


def marker_usability(
    marker: str,
    *,
    ldr_ref: str,
    cwd: str | None = None,
    fetch_remote: str | None = None,
) -> tuple[bool, bool]:
    """Resolve whether ``marker`` is safe to use as the provenance range start.

    Two independent checks, BOTH required for the marker to be usable: (1) the SHA resolves
    to a commit object locally — best-effort fetched from ``fetch_remote`` first if not
    already present — and (2) the SHA is a true git ancestor of ``ldr_ref``
    (`marker_is_ancestor`). Check (2) only runs once (1) is satisfied, since an absent object
    can never be an ancestor of anything.

    Returns ``(reachable, ancestor)`` as two separate flags (rather than a single bool) so the
    caller can log both for diagnostics — overall usability is ``reachable and ancestor``.
    """
    reachable = commit_reachable(marker, cwd=cwd)
    if not reachable and fetch_remote:
        try_fetch_sha(fetch_remote, marker, cwd=cwd)
        reachable = commit_reachable(marker, cwd=cwd)
    ancestor = marker_is_ancestor(marker, ldr_ref, cwd=cwd) if reachable else False
    return reachable, ancestor


def main() -> int:
    ap = argparse.ArgumentParser(description="Compute the since-last-promote provenance range.")
    ap.add_argument("--owner", default="IggyIkenna")
    ap.add_argument("--repo", required=True)
    ap.add_argument("--base-branch", required=True, choices=["staging", "main"])
    ap.add_argument("--base-ref", default=None, help="fallback base ref (default origin/<base-branch>)")
    ap.add_argument("--ldr-ref", default=f"origin/{LDR}")
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
    cwd = cast("str | None", args.cwd)
    fetch_remote = cast("str | None", args.fetch_remote)

    marker = last_promoted_marker(owner, repo, base_branch)
    reachable = False
    ancestor = False
    if marker:
        reachable, ancestor = marker_usability(marker, ldr_ref=ldr_ref, cwd=cwd, fetch_remote=fetch_remote)

    rng, mode = resolve_range(marker, base_ref=base_ref, ldr_ref=ldr_ref, marker_usable=reachable and ancestor)
    # Range → stdout (the workflow captures it). Diagnostic → stderr (never echoes the
    # token-bearing fetch remote). A stale/missing/non-ancestor marker is the EXPECTED
    # fail-safe, not an error.
    print(rng)
    print(
        f"promote-provenance-range[{repo}→{base_branch}]: mode={mode} "
        f"marker={marker or '∅'} reachable={reachable} ancestor={ancestor} → {rng}",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
