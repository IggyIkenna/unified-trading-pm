#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: temporary
# Delete-when: fleet-wide git-tag rollout complete
"""Surgically patch a cloudbuild.yaml's version-extraction from the pyproject grep to git-describe
(Phase-2/D13), PRESERVING every other step (stage-siblings, pm-configs, custom build args, …).

The fleet migration's mistake was re-rolling the WHOLE cloudbuild from the generic template, which
clobbered per-repo customizations (e.g. execution/strategy's `stage-siblings` step that clones the
sibling repos into the GCP build context for the Dockerfile COPY). This patches ONLY the one
extract-version line, so customizations survive.

Idempotent: a no-op if the cloudbuild already uses git describe, or has no pyproject-grep line.

Usage: patch_cloudbuild_version.py <path/to/cloudbuild.yaml>
       exit 0 = patched or already-correct (no-op); exit 1 = error.
"""

from __future__ import annotations

import sys

# The exact static-version extraction line the old service template emitted.
_OLD_LINE = """        VERSION=$(grep '^version' pyproject.toml | head -1 | sed 's/version = "//;s/"//')"""

# The git-describe resolution block (git tag SSOT > highest v-tag ref > pyproject > short-sha).
# $$VERSION / $SHORT_SHA conventions match the cloudbuild template (double-dollar = shell var;
# single-dollar SHORT_SHA = Cloud Build builtin).
_NEW_BLOCK = """        git fetch --tags --force --quiet 2>/dev/null || true
        VERSION=$(git describe --tags --abbrev=0 --match 'v*' 2>/dev/null | sed 's/^v//')
        if [ -z "$$VERSION" ]; then
          VERSION=$(git tag --list 'v[0-9]*' --sort=-v:refname 2>/dev/null | head -1 | sed 's/^v//')
        fi
        if [ -z "$$VERSION" ]; then
          VERSION=$(grep '^version' pyproject.toml 2>/dev/null | head -1 | sed 's/version = "//;s/"//')
        fi
        if [ -z "$$VERSION" ]; then
          VERSION="$SHORT_SHA"
        fi"""


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: patch_cloudbuild_version.py <cloudbuild.yaml>", file=sys.stderr)
        return 1
    path = argv[1]
    try:
        with open(path) as f:
            text = f.read()
    except OSError as err:
        print(f"❌ cannot read {path}: {err}", file=sys.stderr)
        return 1

    if "git describe --tags --abbrev=0 --match 'v*'" in text:
        print(f"✅ {path}: already git-describe (no-op)")
        return 0
    if _OLD_LINE not in text:
        # No pyproject-grep extract-version (api-type / custom) — nothing to patch.
        print(f"✅ {path}: no pyproject-grep extract-version line (nothing to patch — preserved as-is)")
        return 0

    patched = text.replace(_OLD_LINE, _NEW_BLOCK, 1)
    if patched == text:
        print(f"⚠️  {path}: replacement produced no change (unexpected)")
        return 1
    with open(path, "w") as f:
        f.write(patched)
    print(f"✅ {path}: extract-version patched to git-describe (customizations preserved)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
