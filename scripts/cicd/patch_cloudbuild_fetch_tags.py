#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: temporary
# Delete-when: fleet-wide git-tag dynamic-versioning rollout stable + templates carry fetch-tags
"""Surgically insert a `fetch-tags` step into a repo's cloudbuild.yaml so the wheel-build step's
hatch-vcs (setuptools-scm `source = "vcs"`) version detection succeeds in Cloud Build.

ROOT CAUSE (WS-L/D13 regression): the dynamic-versioning migration switched pyproject to
`dynamic = ["version"]` + `[tool.hatch.version] source = "vcs"`. Cloud Build's FETCHSOURCE does a
SHALLOW branch checkout into /workspace/.git with NO tags, so the `python:3.13-slim` wheel-build
step (`python -m build --wheel` / `pip install -e .`) hits:
    LookupError: Error getting the version from source `vcs`: setuptools-scm was unable to
    detect version for /workspace.
→ build red → quality-gates-v2 red → LDR→main promote PRs blocked (fleet promotion lag).

The pre-existing `extract-version` step's `git fetch --tags --force --quiet 2>/dev/null || true`
is UNRELIABLE: the unauthenticated fetch against the FETCHSOURCE-left origin intermittently fails
(swallowed by `|| true` → VERSION falls back to $SHORT_SHA → no tags in /workspace/.git → the
later wheel step fails with the LookupError). Builds passed only when that fetch happened to work.

THE FIX — a dedicated `fetch-tags` step that, BEFORE the wheel-build step:
  1. reads GH_PAT from Secret Manager (the exact pattern the existing clone-pm-scripts step uses),
  2. does an AUTHENTICATED `git fetch --unshallow --tags --force` (fallback to a plain `--tags`
     fetch when the repo is not shallow) against the GitHub remote into /workspace/.git, and
  3. since Cloud Build steps SHARE /workspace, the later wheel-build step (python:3.13-slim) then
     sees the tags + full history and hatch-vcs resolves the version (clean X.Y.Z at a release
     tag, X.Y.Z.devN+gSHA ahead — the intended D13 behaviour; the publish-gate skips dev wheels).

The wheel-build step is only edited to add `fetch-tags` to its `waitFor` (so it runs after the
fetch). NOTHING else in the cloudbuild is touched — this is a surgical patch, NOT a re-roll
(re-rolling clobbered custom steps in 7 repos previously).

Idempotent: a no-op if a `fetch-tags` step already exists. Exit 0 = patched or already-correct;
exit 1 = error (e.g. no wheel-build step found — unexpected for a vcs repo).

Usage: patch_cloudbuild_fetch_tags.py <path/to/cloudbuild.yaml>
"""

from __future__ import annotations

import re
import sys

# The fetch-tags step block. Conventions: $$VAR = shell var (escaped for Cloud Build); $PROJECT_ID
# and $REPO_NAME = Cloud Build builtin substitutions (single dollar). The org is always IggyIkenna
# (matches the hardcoded IggyIkenna/... remotes in the existing notify-deployment / clone steps).
# cloud-sdk:alpine has BOTH gcloud (secret read) and git (the clone-pm-scripts step relies on both).
_FETCH_TAGS_STEP = """  # ── fetch-tags: make hatch-vcs (source = "vcs") resolvable in the wheel-build step ──────────
  # Cloud Build's FETCHSOURCE is a SHALLOW, tag-less /workspace/.git → setuptools-scm cannot detect
  # the version in the later python:3.13-slim wheel step. This step authenticates with GH_PAT and
  # fetches tags + full history into the SHARED /workspace/.git so the wheel step resolves it.
  - name: "gcr.io/google.com/cloudsdktool/cloud-sdk:alpine"
    id: "fetch-tags"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        set -e
        if [ ! -d /workspace/.git ]; then
          echo "fetch-tags: /workspace/.git absent (non-trigger build) — skipping (wheel step reports any real error)"
          exit 0
        fi
        GH_PAT=$$(gcloud secrets versions access latest --secret=GH_PAT --project=$PROJECT_ID 2>/dev/null || echo "")
        REMOTE="https://github.com/IggyIkenna/$REPO_NAME.git"
        [ -n "$$GH_PAT" ] && REMOTE="https://$$GH_PAT@github.com/IggyIkenna/$REPO_NAME.git"
        # Unshallow so tagged commits are reachable for setuptools-scm (a plain tag-ref fetch on a
        # shallow clone leaves git describe unable to compute the version). Fall back to a tags-only
        # fetch when the repo is already complete (--unshallow errors on a non-shallow repo).
        git -C /workspace fetch --unshallow --tags --force "$$REMOTE" "+refs/tags/*:refs/tags/*" 2>/dev/null \\
          || git -C /workspace fetch --tags --force "$$REMOTE" "+refs/tags/*:refs/tags/*"
        echo "fetch-tags: $$(git -C /workspace tag --list 'v*' | wc -l | tr -d ' ') v* tags present"
    waitFor: ["-"]

"""

# Match the wheel-build step's `waitFor:` line (build-wheel in libraries, publish-wheel in services)
# so we can append "fetch-tags" to its dependency list. We locate the step by its id then its
# waitFor; both library and service wheel steps run `python -m build`.


def _find_wheel_step_id(text: str) -> str | None:
    """Return the id of the step that runs `python -m build` (build-wheel | publish-wheel | ...)."""
    # Split into step blocks on the "  - name:" boundary, find the one containing `python -m build`.
    blocks = re.split(r"(?=^  - name:)", text, flags=re.MULTILINE)
    for block in blocks:
        if "python -m build" in block:
            m = re.search(r'^    id:\s*"([^"]+)"', block, flags=re.MULTILINE)
            if m:
                return m.group(1)
    return None


# Sentinel comment so the git-setup injection is idempotent + greppable.
_GIT_SETUP_SENTINEL = "# fetch-tags-fix: git for setuptools-scm"


def _inject_git_setup_before_build(text: str) -> str:
    """Insert `apt-get install git` + `safe.directory` before the `python -m build` line.

    python:3.13-slim has NO git binary; setuptools-scm (hatch-vcs source = "vcs") shells out to
    `git describe` and fails silently with "unable to detect version" even when fetch-tags has put
    the tags in /workspace/.git. So the wheel step must install git AND mark /workspace a safe
    directory (cross-step ownership → git's "dubious ownership" guard otherwise blocks describe).
    """
    if _GIT_SETUP_SENTINEL in text:
        return text

    # Find the `python -m build` line, capture its leading indentation, prepend the git setup
    # (same indentation) so it runs in the same shell just before the build.
    def _repl(m: re.Match[str]) -> str:
        indent = m.group(1)
        build_line = m.group(0)
        setup = (
            f"{indent}{_GIT_SETUP_SENTINEL}\n"
            f"{indent}command -v git >/dev/null 2>&1 || "
            f"{{ apt-get update -qq && apt-get install -y --no-install-recommends git; }}\n"
            f"{indent}git config --global --add safe.directory /workspace || true\n"
        )
        return setup + build_line

    return re.sub(r"^([ \t]*)python -m build\b.*$", _repl, text, count=1, flags=re.MULTILINE)


def _add_fetch_tags_to_waitfor(text: str, wheel_id: str) -> str:
    """Append "fetch-tags" to the wheel step's waitFor list (idempotent)."""
    blocks = re.split(r"(?=^  - name:)", text, flags=re.MULTILINE)
    out: list[str] = []
    for block in blocks:
        if f'id: "{wheel_id}"' in block and "python -m build" in block:
            # Find the waitFor line in this block and append fetch-tags if absent.
            def _repl(m: re.Match[str]) -> str:
                inner = m.group(1)
                if "fetch-tags" in inner:
                    return m.group(0)
                inner = inner.rstrip()
                # inner is like '"quality-gates", "cloud-sdk-isolation-check"' or '"quality-gates"'
                return f'    waitFor: [{inner}, "fetch-tags"]'

            # Match only the same line up to the closing ] + trailing inline spaces — NEVER consume
            # the newline (a greedy \s*$ collapsed the next step's "- name:" onto this line).
            block = re.sub(r"^    waitFor:\s*\[([^\]]*)\][ \t]*$", _repl, block, count=1, flags=re.MULTILINE)
        out.append(block)
    return "".join(out)


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: patch_cloudbuild_fetch_tags.py <cloudbuild.yaml>", file=sys.stderr)
        return 1
    path = argv[1]
    try:
        with open(path) as f:
            text = f.read()
    except OSError as err:
        print(f"FAIL cannot read {path}: {err}", file=sys.stderr)
        return 1

    if "python -m build" not in text:
        print(f"OK  {path}: no `python -m build` wheel step (nothing to patch — preserved as-is)")
        return 0

    wheel_id = _find_wheel_step_id(text)
    if wheel_id is None:
        print(f"FAIL {path}: found `python -m build` but no step id to wire waitFor", file=sys.stderr)
        return 1

    patched = text
    parts: list[str] = []

    # Part 1: insert the fetch-tags step (after the `steps:` line) + wire the wheel step's waitFor.
    if 'id: "fetch-tags"' not in patched:
        m = re.search(r"^steps:\s*\n", patched, flags=re.MULTILINE)
        if m is None:
            print(f"FAIL {path}: no top-level `steps:` key", file=sys.stderr)
            return 1
        insert_at = m.end()
        patched = patched[:insert_at] + _FETCH_TAGS_STEP + patched[insert_at:]
        patched = _add_fetch_tags_to_waitfor(patched, wheel_id)
        parts.append(f"fetch-tags step + '{wheel_id}' waitFor")

    # Part 2: make the wheel step git-capable (install git + safe.directory) so setuptools-scm,
    # which shells out to `git`, actually resolves the version in the slim image.
    before = patched
    patched = _inject_git_setup_before_build(patched)
    if patched != before:
        parts.append("git-setup in wheel step")

    if not parts:
        print(f"OK  {path}: already patched (fetch-tags + git-setup present — no-op)")
        return 0

    with open(path, "w") as f:
        f.write(patched)
    print(f"OK  {path}: applied [{', '.join(parts)}] (surgical)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
