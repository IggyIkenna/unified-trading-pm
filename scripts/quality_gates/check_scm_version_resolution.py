#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""QG recurrence-prevention gate: a dynamic-versioned (hatch-vcs ``source = "vcs"``) repo whose
build runs setuptools-scm on a SHALLOW / TAG-LESS tree MUST resolve the version deterministically,
else hatch-vcs raises ``LookupError: setuptools-scm was unable to detect version`` → red wheel/image
build → blocked promote → fleet promotion lag.

WHY (D13 git-tag dynamic-versioning regression — plans/active/issues/
fleet_promote_schedule_yaml_break_2026_06_29.md § P3): repos migrated pyproject to
``dynamic = ["version"]`` + ``[tool.hatch.version] source = "vcs"``. Cloud Build's FETCHSOURCE is a
SHALLOW, tag-less ``/workspace/.git`` and the Docker build ``.dockerignore``s ``.git`` →
setuptools-scm cannot detect a version. Repos fixed this two equally-valid ways:
  (a) cloudbuild: a dedicated ``fetch-tags`` step OR an inline authenticated
      ``git fetch --unshallow --tags --force`` in ``extract-version``, with a ``0.0.0.dev0`` PEP-440
      sentinel fallback (so even a total fetch failure yields a valid version, never a LookupError);
  (b) Dockerfile: ``SETUPTOOLS_SCM_PRETEND_VERSION`` (ARG/ENV) so the editable install resolves the
      version statically.
There is NO cloudbuild/Dockerfile template SSOT, so a NEW or re-rolled repo can silently regress this
fix. This gate runs in each repo's own QG and FAILS LOUD when a hazardous build step is present WITHOUT
any of the accepted escapes.

Surfaces (checked ONLY when pyproject is dynamic + source="vcs" — otherwise hatch-vcs never runs):
  1. ``cloudbuild*.yaml`` with a ``python -m build`` wheel step → require, in that SAME file, a
     ``git fetch ... --tags`` / a ``fetch-tags`` step / ``SETUPTOOLS_SCM_PRETEND_VERSION`` /
     a ``0.0.0.dev0`` sentinel.
  2. ``Dockerfile``/``Dockerfile.*`` with a RUN editable ``pip install ... -e .`` (a comment does NOT
     count) → require ``SETUPTOOLS_SCM_PRETEND_VERSION`` in that Dockerfile.

PASS (exit 0): not dynamic+vcs, or no hazardous step, or an escape is present.
FAIL (exit 1): a hazardous step present with NO escape. ``SCM_VERSION_GATE_WARN=1`` downgrades to a
non-blocking warning (escape valve, mirrors FROZEN_FLOOR_GATE_WARN).

Fix tooling (surgical, idempotent): scripts/cicd/patch_cloudbuild_fetch_tags.py,
scripts/cicd/patch_dockerfile_scm_version.py.

Usage: check_scm_version_resolution.py --repo <repo_dir>
"""

from __future__ import annotations

import argparse
import glob
import os
import re
import sys


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


# `python -m build`, robust to BOTH the shell form (`bash -c "... python -m build ..."`) and the
# Cloud Build YAML args-list form (`args: ["python", "-m", "build"]`) — only quotes/commas/spaces may
# separate the tokens, and `build` is boundary-anchored so `buildx`/`build_x` don't match.
_WHEEL_BUILD_RE = re.compile(r"""python['",\s]+-m['",\s]+build\b""")


def _cloudbuild_escape(text: str) -> bool:
    """True if a cloudbuild text resolves the hatch-vcs version on a shallow/tagless tree."""
    return (
        re.search(r"git\s+fetch[^\n]*--tags", text) is not None
        or "fetch-tags" in text
        or "SETUPTOOLS_SCM_PRETEND_VERSION" in text
        or "0.0.0.dev0" in text
    )


def check_repo(repo: str) -> list[str]:
    """Return a list of problem strings ([] = clean / N/A)."""
    pyproject = _read(os.path.join(repo, "pyproject.toml"))
    is_dynamic = re.search(r"""dynamic\s*=\s*\[[^\]]*["']version["']""", pyproject) is not None
    is_vcs = re.search(r"""source\s*=\s*["']vcs["']""", pyproject) is not None
    if not (is_dynamic and is_vcs):
        return []  # hatch-vcs not in play → setuptools-scm never runs at build time

    problems: list[str] = []

    # Surface 1: cloudbuild wheel-build step (`python -m build`). Each cloudbuild file is its own
    # build (Cloud Build steps share /workspace only within ONE build), so each is checked alone.
    cloudbuilds = sorted(
        glob.glob(os.path.join(repo, "cloudbuild*.yaml")) + glob.glob(os.path.join(repo, "cloudbuild*.yml"))
    )
    for cb in cloudbuilds:
        text = _read(cb)
        if _WHEEL_BUILD_RE.search(text) is None:
            continue
        if not _cloudbuild_escape(text):
            problems.append(
                f"{os.path.relpath(cb, repo)}: `python -m build` wheel step with NO "
                "git-tag fetch / fetch-tags step / SETUPTOOLS_SCM_PRETEND_VERSION / 0.0.0.dev0 sentinel"
            )

    # Surface 2: Dockerfile editable install (`RUN ... pip install ... -e .`). A comment line does
    # NOT match (anchored RUN), so a "no editable install needed" comment is not a false positive.
    # Two accepted escapes: (a) the Dockerfile sets its OWN SETUPTOOLS_SCM_PRETEND_VERSION; (b) it
    # derives `FROM` the unified-trading-library base image, which declares
    # `ENV SETUPTOOLS_SCM_PRETEND_VERSION` (unified-trading-library/Dockerfile:94-95) — a PERSISTED env
    # inherited by every `FROM base` stage (the standard service-image pattern, e.g. deployment-api
    # Dockerfile.dashboard). Without one of these AND with `.git` absent from the build context,
    # hatch-vcs raises LookupError.
    dockerfiles = sorted(glob.glob(os.path.join(repo, "Dockerfile")) + glob.glob(os.path.join(repo, "Dockerfile.*")))
    for df in dockerfiles:
        text = _read(df)
        if re.search(r"^[ \t]*RUN\s+.*pip install\s+.*-e\s+\.", text, flags=re.MULTILINE) is None:
            continue
        if "SETUPTOOLS_SCM_PRETEND_VERSION" in text:
            continue  # escape (a): declares its own pretend-version
        if re.search(r"^\s*FROM\s+.*unified-trading-library", text, flags=re.MULTILINE):
            continue  # escape (b): inherits ENV SETUPTOOLS_SCM_PRETEND_VERSION from the UTL base image
            # (the FROM line may carry flags, e.g. `FROM --platform=linux/amd64 .../unified-trading-library@...`)
        problems.append(
            f"{os.path.relpath(df, repo)}: editable `pip install -e .` with NO SETUPTOOLS_SCM_PRETEND_VERSION "
            "and no `FROM unified-trading-library` base (hatch-vcs cannot resolve a version with .git absent)"
        )

    return problems


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="D13 hatch-vcs version-resolution regression gate")
    ap.add_argument("--repo", required=True, help="repo dir to check")
    args = ap.parse_args(argv)
    repo = args.repo.rstrip("/")
    name = os.path.basename(repo) or repo
    warn = os.environ.get("SCM_VERSION_GATE_WARN", "0") == "1"

    problems = check_repo(repo)
    if not problems:
        print(f"✅ scm-version-gate: {name} — hatch-vcs version resolution present on all build surfaces")
        return 0

    print(
        f"{'⚠️ ' if warn else '❌ '}scm-version-gate: {name} — D13 version-resolution MISSING "
        "(hatch-vcs LookupError risk on shallow/tagless build):"
    )
    for problem in problems:
        print(f"   {problem}")
    print(
        "   FIX: cloudbuild → add a `--tags` fetch / fetch-tags step + a 0.0.0.dev0 sentinel "
        "(scripts/cicd/patch_cloudbuild_fetch_tags.py); Dockerfile → add SETUPTOOLS_SCM_PRETEND_VERSION "
        "(scripts/cicd/patch_dockerfile_scm_version.py). SCM_VERSION_GATE_WARN=1 downgrades to a warning."
    )
    return 0 if warn else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
