#!/usr/bin/env python3
"""Guard 2 — structural 3-way reconcile of ``workspace-manifest.json`` for the
``main → live-defi-rollout`` back-merge.

WHY (cicd_contract_hardening_2026_06_01 § "Guard 2"): ``ci_status`` (and its
sibling CI-automation fields) is written by the bot on **main** only — main is
the single authoritative home. LDR carries a *non-authoritative* copy that goes
stale (tab branches fork an older snapshot, then FF-mirror it back to LDR). When
``main-backmerge-to-ldr`` runs ``git merge origin/main``, both sides have touched
the same ``"ci_status": "..."`` lines since their merge-base → a textual conflict
that blocks the back-merge AND, transitively, the LDR→main promotion (the "dam").

This reconciler resolves that **deterministically without ever blocking on a
CI-automation field**: it does a field-level 3-way merge where the
main-authoritative CI fields always take ``theirs`` (= main, in the back-merge
direction), everything else takes the normal 3-way result, and a *genuine*
divergence on a NON-CI field is left as an explicit conflict (exit 2) so the
existing human-PR + orchestrator escalation still fires. It never silently drops
an LDR-side manifest edit.

Direction contract: ``--ours`` is the LDR side (HEAD during the back-merge),
``--theirs`` is the main side (MERGE_HEAD). CI fields resolve to ``theirs``.

Exit codes: 0 = clean reconcile written to ``--out``; 2 = genuine non-CI conflict
(caller must abort the merge and escalate); 1 = usage / parse error.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path

# Fields written by CI automation on main (single authoritative home). On the
# back-merge these always resolve to main (``theirs``); LDR's copy is
# non-authoritative (Guard 2(a): all readers read ci_status from main).
# Per-repo CI-automation fields (under repositories.<name>.<field>):
_REPO_CI_FIELDS: frozenset[str] = frozenset({"ci_status", "coverage_pct", "ci_failure_reason"})
# Top-level CI / promotion-state blocks (semver-agent + promoter + ci-status bot):
_TOPLEVEL_CI_FIELDS: frozenset[str] = frozenset(
    {
        "staging_status",
        "staging_commits",
        "main_commits",
        "staging_versions",
        "deployed_versions",
        "lastUpdated",
    }
)

ConflictPath = tuple[str, ...]


def _load(path: str) -> object:
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def _merge_value(base: object, ours: object, theirs: object, path: ConflictPath) -> tuple[object, list[ConflictPath]]:
    """Standard 3-way merge of a single value. Returns (merged, conflicts)."""
    if ours == theirs:
        return ours, []
    if base == ours:
        # only theirs changed → take theirs
        return theirs, []
    if base == theirs:
        # only ours changed → take ours
        return ours, []
    # both sides changed differently relative to base
    if isinstance(ours, Mapping) and isinstance(theirs, Mapping):
        base_map = base if isinstance(base, Mapping) else {}
        return _merge_dict(base_map, ours, theirs, path)
    # scalar/list both-changed → genuine conflict
    return ours, [path]


def _merge_dict(
    base: Mapping[str, object],
    ours: Mapping[str, object],
    theirs: Mapping[str, object],
    path: ConflictPath,
) -> tuple[dict[str, object], list[ConflictPath]]:
    merged: dict[str, object] = {}
    conflicts: list[ConflictPath] = []
    for key in dict.fromkeys([*ours.keys(), *theirs.keys()]):
        child = (*path, key)
        in_ours = key in ours
        in_theirs = key in theirs
        # CI-automation field → always take main (theirs) when present, never conflict.
        if _is_ci_field(child):
            if in_theirs:
                merged[key] = theirs[key]
            elif in_ours:
                merged[key] = ours[key]
            continue
        if in_ours and in_theirs:
            value, sub = _merge_value(
                base.get(key) if isinstance(base, Mapping) else None,
                ours[key],
                theirs[key],
                child,
            )
            merged[key] = value
            conflicts.extend(sub)
        elif in_ours:
            # key only on ours: keep unless main deleted a base key → take ours add
            merged[key] = ours[key]
        else:
            merged[key] = theirs[key]
    return merged, conflicts


def _is_ci_field(path: ConflictPath) -> bool:
    if len(path) == 1 and path[0] in _TOPLEVEL_CI_FIELDS:
        return True
    # repositories.<name>.<ci_field>
    return len(path) == 3 and path[0] == "repositories" and path[2] in _REPO_CI_FIELDS


def reconcile(base: object, ours: object, theirs: object) -> tuple[object, list[ConflictPath]]:
    if not (isinstance(ours, Mapping) and isinstance(theirs, Mapping)):
        raise ValueError("manifest root must be a JSON object")
    base_map = base if isinstance(base, Mapping) else {}
    return _merge_dict(base_map, ours, theirs, ())


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="merge-base manifest")
    parser.add_argument("--ours", required=True, help="LDR-side manifest (HEAD)")
    parser.add_argument("--theirs", required=True, help="main-side manifest (MERGE_HEAD)")
    parser.add_argument("--out", required=True, help="path to write the reconciled manifest")
    args = parser.parse_args(argv)

    merged, conflicts = reconcile(_load(args.base), _load(args.ours), _load(args.theirs))

    if conflicts:
        sys.stderr.write("GENUINE NON-CI CONFLICT — cannot auto-resolve; escalate to human PR:\n")
        for path in conflicts:
            sys.stderr.write(f"  - {'.'.join(path)}\n")
        return 2

    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as handle:
        json.dump(merged, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    sys.stdout.write(
        f"reconciled {args.out}: CI-automation fields resolved to main (theirs); "
        "all other fields 3-way merged with no conflict\n"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
