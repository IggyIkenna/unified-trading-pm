#!/usr/bin/env python3
# Epic: ci_master
# Lifecycle: temporary
# Delete-when: fleet-wide git-tag dynamic-versioning rollout stable + service templates carry the fix
"""Surgically fix the SECOND manifestation of the WS-L/D13 git-tag-versioning regression: the
Dockerfile's `pip install -e .` (editable install) triggers hatch-vcs (setuptools-scm
source = "vcs") version detection INSIDE the Docker build, where `.git` is `.dockerignore`d and
absent → `LookupError: ... unable to detect version` → the cloudbuild `build` (docker) step fails.

(The companion patch_cloudbuild_fetch_tags.py fixes the separate wheel-build step; this fixes the
Docker image build for services that `pip install -e .` in their Dockerfile.)

THE FIX — pass setuptools-scm's official escape-hatch env (the error message itself recommends it):
  1. cloudbuild `build` step: inject `--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$$SCM_VERSION` after
     the existing `--build-arg PROJECT_ID=...` line, where SCM_VERSION is the extract-version
     `/workspace/VERSION` SANITIZED to a PEP-440 X.Y.Z (the $SHORT_SHA fallback is not a valid
     version → setuptools-scm pretend would itself error, so coerce a non-X.Y.Z to 0.0.0).
  2. Dockerfile: declare `ARG SETUPTOOLS_SCM_PRETEND_VERSION` + `ENV ...` immediately BEFORE the
     `RUN ... pip install ... -e .` line so the editable install resolves the version statically.

Surgical + idempotent: each edit is guarded by a sentinel comment and a no-op when already present.
NOT a re-roll. Exit 0 = patched or already-correct / nothing to patch; exit 1 = error.

Usage: patch_dockerfile_scm_version.py <repo_dir>
       (expects <repo_dir>/Dockerfile and <repo_dir>/cloudbuild.yaml)
"""

from __future__ import annotations

import os
import re
import sys

_DF_SENTINEL = "# scm-version-fix: pretend version for editable install (D13 git-tag versioning)"
_CB_SENTINEL = "# scm-version-fix: SETUPTOOLS_SCM_PRETEND_VERSION build-arg (D13 git-tag versioning)"


def _patch_dockerfile(path: str) -> tuple[bool, str]:
    """Insert ARG+ENV SETUPTOOLS_SCM_PRETEND_VERSION before the editable `pip install -e .`."""
    with open(path) as f:
        text = f.read()
    if _DF_SENTINEL in text:
        return False, "Dockerfile already patched"
    # Match the editable-install RUN line (uv/pip, `-e .` in any flag order).
    m = re.search(r"^([ \t]*)RUN .*pip install .*-e \.\S*.*$", text, flags=re.MULTILINE)
    if m is None:
        return False, "Dockerfile has no `pip install -e .` line (nothing to patch)"
    indent = m.group(1)
    block = (
        f"{indent}{_DF_SENTINEL}\n"
        f"{indent}ARG SETUPTOOLS_SCM_PRETEND_VERSION=0.0.0\n"
        f"{indent}ENV SETUPTOOLS_SCM_PRETEND_VERSION=${{SETUPTOOLS_SCM_PRETEND_VERSION}}\n"
    )
    patched = text[: m.start()] + block + text[m.start() :]
    with open(path, "w") as f:
        f.write(patched)
    return True, "Dockerfile: ARG/ENV SETUPTOOLS_SCM_PRETEND_VERSION before editable install"


def _patch_cloudbuild(path: str) -> tuple[bool, str]:
    """Inject the SETUPTOOLS_SCM_PRETEND_VERSION build-arg into the docker `build` step.

    Two surgical insertions, each at a correct shell-statement boundary:
      1. the SCM_VERSION sanitize line right AFTER the existing `VERSION=$(cat /workspace/VERSION..)`
         statement (a real statement boundary — NOT inside the `\\`-continued docker build command);
      2. the `--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$$SCM_VERSION \\` line right AFTER the
         `--build-arg PROJECT_ID=$PROJECT_ID \\` continuation line.
    """
    with open(path) as f:
        text = f.read()
    if _CB_SENTINEL in text:
        return False, "cloudbuild already patched"

    # Insertion 2 anchor: the --build-arg PROJECT_ID continuation line (locates the docker build step).
    marg = re.search(r"^([ \t]*)--build-arg PROJECT_ID=\$PROJECT_ID \\\s*$", text, flags=re.MULTILINE)
    if marg is None:
        return False, "cloudbuild has no `--build-arg PROJECT_ID=$PROJECT_ID` docker-build anchor"

    # Insertion 1: the VERSION=$(cat /workspace/VERSION ..) line in the SAME step — i.e. the LAST such
    # line BEFORE the PROJECT_ID anchor (scopes the SCM_VERSION assignment to the docker build step,
    # robust to other steps that also read /workspace/VERSION).
    ver_pat = re.compile(
        r"^([ \t]*)VERSION=\$\(cat /workspace/VERSION 2>/dev/null \|\| echo \"\$SHORT_SHA\"\)[ \t]*$",
        flags=re.MULTILINE,
    )
    mver = None
    for cand in ver_pat.finditer(text):
        if cand.start() < marg.start():
            mver = cand
        else:
            break
    if mver is None:
        return False, "cloudbuild docker build step has no preceding VERSION=$(cat /workspace/VERSION ..)"

    indent = mver.group(1)
    # Sanitize VERSION → PEP-440 X.Y.Z (extract-version's $SHORT_SHA fallback isn't a valid version).
    sanitize = (
        f"{indent}{_CB_SENTINEL}\n"
        f'{indent}SCM_VERSION=$$(printf "%s" "$$VERSION" | grep -qE '
        f"'^[0-9]+\\.[0-9]+\\.[0-9]+' && printf \"%s\" \"$$VERSION\" || printf '0.0.0')\n"
    )
    arg_indent = marg.group(1)
    inject = f"{arg_indent}--build-arg SETUPTOOLS_SCM_PRETEND_VERSION=$$SCM_VERSION \\\n"

    # Compute both insertion offsets up front (line-ends). The VERSION line precedes the PROJECT_ID
    # anchor, so splice the LATER (anchor) offset first to keep the earlier (VERSION) offset valid.
    ver_nl = text.find("\n", mver.end())
    ver_nl = ver_nl + 1 if ver_nl != -1 else len(text)
    arg_nl = text.find("\n", marg.end())
    arg_nl = arg_nl + 1 if arg_nl != -1 else len(text)

    text = text[:arg_nl] + inject + text[arg_nl:]  # later offset first
    text = text[:ver_nl] + sanitize + text[ver_nl:]  # earlier offset still valid

    with open(path, "w") as f:
        f.write(text)
    return True, "cloudbuild: SETUPTOOLS_SCM_PRETEND_VERSION build-arg in docker build step"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: patch_dockerfile_scm_version.py <repo_dir>", file=sys.stderr)
        return 1
    repo = argv[1].rstrip("/")
    df = os.path.join(repo, "Dockerfile")
    cb = os.path.join(repo, "cloudbuild.yaml")
    if not os.path.isfile(df):
        print(f"OK  {repo}: no Dockerfile (nothing to patch)")
        return 0
    if not os.path.isfile(cb):
        print(f"OK  {repo}: no cloudbuild.yaml (nothing to patch)")
        return 0

    # Only services that pip-install -e . in the Dockerfile are affected.
    with open(df) as f:
        df_text = f.read()
    if not re.search(r"^[ \t]*RUN .*pip install .*-e \.\S*.*$", df_text, flags=re.MULTILINE):
        print(f"OK  {repo}: Dockerfile has no editable install (not affected)")
        return 0

    notes: list[str] = []
    try:
        changed_df, msg_df = _patch_dockerfile(df)
        if changed_df:
            notes.append(msg_df)
        changed_cb, msg_cb = _patch_cloudbuild(cb)
        if changed_cb:
            notes.append(msg_cb)
        elif not changed_df:
            print(f"OK  {repo}: already patched (no-op)")
            return 0
        if changed_df and not changed_cb:
            print(f"FAIL {repo}: patched Dockerfile but cloudbuild anchor not found ({msg_cb})", file=sys.stderr)
            return 1
    except OSError as err:
        print(f"FAIL {repo}: {err}", file=sys.stderr)
        return 1

    print(f"OK  {repo}: applied [{', '.join(notes)}] (surgical)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
