#!/usr/bin/env python3
"""Git merge driver: semantic 3-way merge of ``workspace-manifest.json``.

Concurrent manifest writers (``update-repo-version``, ``reconcile-staging-versions``, the
staging->main drain, the backmerge bot) all commit ``versions`` / ``staging_versions`` mutations to
``main``. A plain line-based ``git rebase`` conflicts whenever two of them touch adjacent JSON lines
even when the *semantic* change is non-overlapping (different repo keys) or deterministically
resolvable (both bumped the same key — higher semver wins). Before this driver the
five-attempt rebase-retry loop in those workflows died FATAL on the first content conflict, silently
losing a version bump (incident 2026-06-26: deployment-service 0.95.0 manifest write lost, fired 3x
:x: update-repo-version CRITICAL).

Resolution rules (applied recursively):
  * ``versions`` / ``staging_versions`` (and any X.Y.Z value): both bumped -> MAX semver wins.
  * lists (e.g. ``staging_status.breaking_pending``): UNION, sorted, de-duped.
  * dicts: recurse key-by-key.
  * one side unchanged vs base: take the changed side (incl. honoring a deletion).
  * a genuine non-version scalar divergence: leave it to OURS and exit 1 so the rebase pauses and
    the caller escalates (FAIL SAFE — never silently pick a side for non-version state).

Git invokes a merge driver as ``driver %O %A %B`` (base, ours, theirs); the merged result MUST be
written back to the ``ours`` (%A) path. Exit 0 = fully resolved, 1 = conflict markers remain.

Wire-up (runner-local, NOT committed git config — only the ``merge=manifestmerge`` attribute is):
    git config merge.manifestmerge.driver "python3 .../manifest_merge_driver.py %O %A %B"
See scripts/cicd/setup_manifest_merge_drivers.sh for the canonical wiring used by the workflows.

SSOT: plans/active/cicd_consolidated_remaining_2026_06_24.md (manifest-merge-driver).
"""

# Epic: ci_master
# Lifecycle: permanent
# Delete-when: NA
from __future__ import annotations

import json
import re
import sys

_VER_RE = re.compile(r"^\d+\.\d+\.\d+([.\-+].*)?$")
_MISSING = object()


def _semver_key(version: str) -> list[tuple[int, object]]:
    """Sort key that orders 0.9.0 < 0.10.0 numerically (not lexically)."""
    key: list[tuple[int, object]] = []
    for part in re.split(r"[.\-+]", version):
        key.append((0, int(part)) if part.isdigit() else (1, part))
    return key


def _is_version(value: object) -> bool:
    return isinstance(value, str) and bool(_VER_RE.match(value))


def _merge_list(ours: list[object], theirs: list[object]) -> list[object]:
    """Union two lists, de-duped and sorted when the elements are comparable scalars.

    Used for append-style sets like ``staging_status.breaking_pending``. Falls back to a stable
    order-preserving union for non-scalar / mixed-type elements.
    """
    seen: list[object] = []
    for item in [*ours, *theirs]:
        if item not in seen:
            seen.append(item)
    # key=str gives a deterministic order for the scalar string sets we union (e.g.
    # breaking_pending repo names) without requiring the elements be mutually comparable.
    return sorted(seen, key=str)


def merge3(base: object, ours: object, theirs: object) -> tuple[object, bool]:
    """Return ``(merged_value, has_conflict)`` for a 3-way merge of one JSON node."""
    if ours == theirs:
        return ours, False
    if ours == base:  # only theirs changed (incl. deletion handled by caller)
        return theirs, False
    if theirs == base:  # only ours changed
        return ours, False

    # Both sides diverged from base.
    if isinstance(ours, dict) and isinstance(theirs, dict):
        base_d = base if isinstance(base, dict) else {}
        out: dict[str, object] = {}
        conflict = False
        # Preserve ours' key order; append keys only theirs has at the end (minimise merge churn).
        ordered_keys = list(ours) + [k for k in theirs if k not in ours]
        for k in ordered_keys:
            in_o, in_t = k in ours, k in theirs
            if in_o and in_t:
                v, c = merge3(base_d.get(k, _MISSING), ours[k], theirs[k])
                out[k] = v
                conflict = conflict or c
            elif in_o:  # theirs lacks k
                # Unchanged-by-ours + deleted-by-theirs => honor the deletion (drop the key).
                if k in base_d and ours[k] == base_d[k]:
                    continue
                out[k] = ours[k]
            else:  # ours lacks k
                if k in base_d and theirs[k] == base_d[k]:
                    continue
                out[k] = theirs[k]
        return out, conflict

    if isinstance(ours, list) and isinstance(theirs, list):
        return _merge_list(ours, theirs), False

    if _is_version(ours) and _is_version(theirs) and isinstance(ours, str) and isinstance(theirs, str):
        return max(ours, theirs, key=_semver_key), False

    # Genuine non-version scalar divergence — FAIL SAFE: keep ours, signal conflict.
    return ours, True


def main() -> int:
    if len(sys.argv) < 4:
        sys.stderr.write("usage: manifest_merge_driver.py %O %A %B\n")
        return 2
    base_path, ours_path, theirs_path = sys.argv[1], sys.argv[2], sys.argv[3]

    def _load(path: str) -> object:
        try:
            with open(path) as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            sys.stderr.write(f"manifest_merge_driver: cannot parse {path}: {exc}\n")
            return _MISSING

    base, ours, theirs = _load(base_path), _load(ours_path), _load(theirs_path)
    if _MISSING in (ours, theirs):
        # Cannot semantically merge unparseable JSON — leave it to git (conflict).
        return 1
    if base is _MISSING:
        base = {}

    merged, conflict = merge3(base, ours, theirs)
    if conflict:
        # Non-version divergence we will not guess at — leave ours in place, let git mark conflict.
        sys.stderr.write("manifest_merge_driver: genuine non-version conflict — escalating\n")
        return 1

    with open(ours_path, "w") as handle:
        json.dump(merged, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
