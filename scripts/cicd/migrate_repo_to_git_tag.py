#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: temporary
# Delete-when: fleet-wide git-tag rollout complete (every version-tracked repo is version_source=git-tag)
"""Migrate ONE repo's ``pyproject.toml`` from a committed ``version =`` line to dynamic
hatch-vcs versioning (Phase-2 / D13, "version out of source").

The transform (idempotent — safe to re-run):
  1. ``[build-system].requires`` gains ``"hatch-vcs"`` (alongside ``hatchling``).
  2. ``[project]`` loses its ``version = "X.Y.Z"`` line and gains ``dynamic = ["version"]``.
  3. A ``[tool.hatch.version]`` table with ``source = "vcs"`` is added (if absent).

Why this is SAFE (audited 2026-06-27): for every fleet repo ``git describe --tags --match 'v*'``
from HEAD resolves to the SAME version the ``version =`` line declares (the release tag already
exists), so hatch-vcs produces the identical version — no jump, no regression. Stray high tags
(e.g. unified-trading-library ``v1.2.0``) are NOT reachable from HEAD, so ``git describe`` ignores
them (it resolves the nearest ANCESTOR tag). This script REFUSES to migrate if it cannot confirm a
reachable ``v*`` tag whose version is >= the declared one, so it can never silently regress a repo
to ``0.0.0``/dev under dynamic versioning (the writer-before-resolvability hazard).

This edits ONLY pyproject.toml. The caller is responsible for: rolling the retargeted
semver-agent + version-registry-notify workflows (``rollout-workflow-templates.sh --repo``), re-rolling
cloudbuild (``rollout-cloudbuild.py --repo``), flipping ``version_source=git-tag`` in
workspace-manifest.json, and committing via quickmerge.

Stdlib only (no tomllib WRITE — tomllib is read-only; we do line-oriented edits to preserve
formatting/comments, the same approach the semver-agent sed uses).

Usage:
    migrate_repo_to_git_tag.py --repo <name> [--workspace <root>] [--check] [--apply]
        --check   report what WOULD change + the version-source audit; exit 0 if safe, 2 if unsafe
        --apply   perform the pyproject edit (implies the safety check first)
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys

_VERSION_LINE_RE = re.compile(r'^version\s*=\s*"(?P<v>[0-9]+\.[0-9]+\.[0-9]+)"\s*$')
_SEMVER_RE = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)")


def _semver_tuple(s: str) -> tuple[int, int, int]:
    m = _SEMVER_RE.match(s or "")
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else (0, 0, 0)


def _git(cwd: str, *args: str) -> str:
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


def _declared_version(text: str) -> str | None:
    """The committed ``[project].version`` value, or None when already dynamic / absent."""
    in_project = False
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("[") and s.endswith("]"):
            in_project = s == "[project]"
            continue
        if in_project:
            m = _VERSION_LINE_RE.match(s)
            if m:
                return m.group("v")
    return None


def _is_already_dynamic(text: str) -> bool:
    has_dynamic = any(re.match(r'^\s*dynamic\s*=\s*\[[^\]]*"version"', line) for line in text.splitlines())
    has_hatch_vcs_table = "[tool.hatch.version]" in text and re.search(
        r'\[tool\.hatch\.version\][^\[]*source\s*=\s*"vcs"', text, re.DOTALL
    )
    return has_dynamic and bool(has_hatch_vcs_table)


def _audit(repo_dir: str, declared: str | None) -> tuple[bool, str]:
    """Confirm a reachable v* tag whose version is >= the declared version (no regression risk).

    Returns (safe, message). When declared is None (already dynamic) the audit still confirms a
    reachable tag exists so a re-run never reports a dynamic-but-untagged repo as safe.
    """
    nearest = _git(repo_dir, "describe", "--tags", "--abbrev=0", "--match", "v*")
    if not nearest:
        return False, (
            "no reachable v* tag from HEAD — dynamic versioning would resolve 0.0.0/dev; mint a baseline tag first"
        )
    nv = _semver_tuple(nearest)
    if declared is not None:
        dv = _semver_tuple(declared)
        if nv < dv:
            return False, (
                f"nearest reachable tag {nearest} ({nv}) is BEHIND the declared version {declared} ({dv}) — "
                "migrating would regress the version under dynamic resolution; mint a v{declared} tag first"
            )
        if nv[0] >= 1 and dv[0] < 1:
            return False, (
                f"nearest reachable tag {nearest} crosses the 1.0.0 graduation boundary vs declared {declared} "
                "— 1.0.0 graduation is human-only (HARD STOP); resolve the stray tag before migrating"
            )
    return True, (
        f"safe: nearest reachable tag {nearest} matches/leads declared"
        f" {declared or '(dynamic)'} (no regression, no 1.0.0 crossing)"
    )


def _transform(text: str) -> str:
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    section: str | None = None
    project_version_removed = False
    project_dynamic_added = False

    def _flush_dynamic_if_needed() -> None:
        nonlocal project_dynamic_added

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            # Leaving [project] without a dynamic line yet → inject it before the next section.
            if section == "[project]" and project_version_removed and not project_dynamic_added:
                out.append('dynamic = ["version"]\n')
                project_dynamic_added = True
            section = stripped
            out.append(line)
            # Inject hatch-vcs requires inside [build-system].requires below (handled separately).
            continue
        if section == "[project]" and _VERSION_LINE_RE.match(stripped):
            # Replace the static version line with the dynamic declaration (in place, preserves order).
            out.append('dynamic = ["version"]\n')
            project_version_removed = True
            project_dynamic_added = True
            continue
        out.append(line)

    # Trailing [project] with no following section.
    if section == "[project]" and project_version_removed and not project_dynamic_added:
        out.append('dynamic = ["version"]\n')

    text2 = "".join(out)

    # 1. hatch-vcs in [build-system].requires (handle inline and multiline arrays).
    if "hatch-vcs" not in text2:
        # inline:  requires = ["hatchling"]  /  requires = ["hatchling", ...]
        text2, n = re.subn(
            r"(requires\s*=\s*\[)([^\]]*?)(\])",
            lambda m: (
                m.group(1)
                + m.group(2)
                + ("" if m.group(2).rstrip().endswith(",") or not m.group(2).strip() else ", ")
                + '"hatch-vcs"'
                + m.group(3)
            ),
            text2,
            count=1,
            flags=re.DOTALL,
        )
        if n == 0:
            # multiline:  requires = [\n  "hatchling",\n]  → add a line before the closing ].
            text2 = re.sub(
                r"(requires\s*=\s*\[\n)((?:[^\]]*\n)*?)(\s*\])",
                lambda m: m.group(1) + m.group(2) + '    "hatch-vcs",\n' + m.group(3),
                text2,
                count=1,
            )

    # 2. [tool.hatch.version] source = "vcs" (append if absent).
    if "[tool.hatch.version]" not in text2:
        sep = "" if text2.endswith("\n") else "\n"
        text2 = text2 + sep + '\n[tool.hatch.version]\nsource = "vcs"\n'

    return text2


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="repo name (directory under the workspace root)")
    ap.add_argument("--workspace", default=None, help="workspace root (default: two levels up from this script)")
    ap.add_argument("--check", action="store_true", help="audit + report; do not write")
    ap.add_argument("--apply", action="store_true", help="apply the pyproject edit")
    args = ap.parse_args(argv)

    here = os.path.dirname(os.path.abspath(__file__))
    workspace = args.workspace or os.path.abspath(os.path.join(here, "..", "..", ".."))
    repo_dir = os.path.join(workspace, args.repo)
    pyproject = os.path.join(repo_dir, "pyproject.toml")
    if not os.path.isfile(pyproject):
        print(f"❌ {args.repo}: no pyproject.toml at {pyproject} (UI/npm repo? excluded from the pyproject migration)")
        return 2

    with open(pyproject) as f:
        text = f.read()

    if _is_already_dynamic(text):
        print(f"✅ {args.repo}: already dynamic (hatch-vcs source=vcs + dynamic=['version']) — idempotent no-op")
        return 0

    declared = _declared_version(text)
    safe, msg = _audit(repo_dir, declared)
    print(f"[{args.repo}] declared={declared or '(none)'} | {msg}")
    if not safe:
        print(f"❌ {args.repo}: UNSAFE to migrate — {msg}")
        return 2

    if args.check and not args.apply:
        print(f"✅ {args.repo}: SAFE to migrate (declared {declared} → dynamic vcs). Re-run with --apply to write.")
        return 0

    if args.apply:
        new_text = _transform(text)
        if new_text == text:
            print(f"⚠️  {args.repo}: transform produced no change (unexpected) — inspect pyproject manually")
            return 2
        with open(pyproject, "w") as f:
            f.write(new_text)
        # Verify the result parses + is dynamic.
        if not _is_already_dynamic(new_text):
            print(f"❌ {args.repo}: post-transform pyproject is NOT dynamic — reverting expected; inspect manually")
            return 2
        print(
            f"✅ {args.repo}: pyproject migrated to dynamic hatch-vcs versioning"
            f" (declared {declared} preserved via tag)"
        )
        return 0

    print(f"✅ {args.repo}: SAFE (dry default). Pass --apply to write.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
