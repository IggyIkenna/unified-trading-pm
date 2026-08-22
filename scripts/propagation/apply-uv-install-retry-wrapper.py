#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""
apply-uv-install-retry-wrapper.py

Applies the canonical ``uv pip install`` retry-wrapper pattern (codex/06-coding-standards/
dockerfile-standards.md § "uv pip install Retry Wrapper (BuildKit-secret GAR auth)",
plans/active/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md)
to a repo's production Dockerfile(s):

    RUN --mount=type=secret,id=gar_token \\
        UV_EXTRA_INDEX_URL="https://oauth2accesstoken:$(cat /run/secrets/gar_token)@..." \\
        sh -c 'i=1; until uv pip install --system --no-sources -e .; do [ "$i" -ge 3 ] && \\
        { echo "uv pip install failed after 3 attempts" >&2; exit 1; }; w=$((15 * i)); \\
        echo "uv pip install failed (attempt $i/3) -- retrying in ${w}s"; sleep "$w"; \\
        i=$((i + 1)); done'

Finds any ``RUN --mount=type=secret,id=gar_token`` layer whose ``uv pip install ... --no-sources``
call is a bare (un-wrapped) invocation and wraps ONLY that command line in the 3-attempt retry loop
with exponential backoff, preserving every other line in the layer (the ``UV_EXTRA_INDEX_URL``
assignment, indentation, and any other flags/extras the repo's own install command already carries)
verbatim -- this mirrors the ``BASE_IMAGE_DIGEST`` propagation precedent
(``scripts/propagation/add-dockerfile-digest-arg.py``) of a surgical, idempotent, per-line edit
rather than a full-block rewrite.

Idempotent: a layer that already contains ``until uv pip install`` is left untouched (already
wrapped). Skips ``market-tick-data-service`` (vendored-local installs, never resolves from the live
GAR index) and ``unified-trading-system-ui`` (no Cloud Build trigger) -- same exclusions as the
drift checker (``scripts/quality_gates/check_uv_install_retry_wrapper_drift.py``) and the SSOT.

Usage:
    python apply-uv-install-retry-wrapper.py [--dry-run] [--repo NAME]

Options:
    --dry-run     Print what would change without writing files.
    --repo NAME   Process a single repo only.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"

GAR_TOKEN_MOUNT = "--mount=type=secret,id=gar_token"
UV_INSTALL_MARKER = "uv pip install"
NO_SOURCES_FLAG = "--no-sources"
RETRY_WRAP_RE = re.compile(r"\buntil\s+uv\s+pip\s+install\b")

RUN_INSTRUCTION_RE = re.compile(r"^\s*RUN\b", re.IGNORECASE)
LEADING_WS_RE = re.compile(r"^(\s*)")

# Same exclusions as the drift checker + the SSOT (market-tick-data-service: vendored-local
# installs never resolve from the live GAR index; unified-trading-system-ui: no Cloud Build
# trigger).
SKIP_REPOS = {
    "market-tick-data-service",
    "unified-trading-system-ui",
    "unified-trading-pm",  # not a deployed package
}

# Dockerfile name suffixes that are NOT production builds.
SKIP_SUFFIXES = {"dev", "test", "ci", "local"}

# Directory names never holding production Dockerfiles.
SKIP_DIR_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "build",
    "dist",
    "tests",
    "test",
    "fixtures",
    "__pycache__",
}


def _retry_wrap(cmd: str) -> str:
    """Wrap ``cmd`` (a bare ``uv pip install ...`` invocation) in the canonical 3-attempt
    exponential-backoff retry loop."""
    return (
        "sh -c 'i=1; until " + cmd + '; do [ "$i" -ge 3 ] && { echo "uv pip install failed after 3 attempts" >&2;'
        ' exit 1; }; w=$((15 * i)); echo "uv pip install failed (attempt $i/3) -- retrying in'
        ' ${w}s"; sleep "$w"; i=$((i + 1)); done\''
    )


def is_production_dockerfile(path: Path) -> bool:
    """Production Dockerfile filter: skip dev/test/ci variants + vendored/test dirs."""
    for part in path.parts[:-1]:
        if part in SKIP_DIR_PARTS or part.startswith(".venv"):
            return False
    name = path.name
    if name == "Dockerfile":
        return True
    suffix = name.removeprefix("Dockerfile.").lower()
    return not (suffix in SKIP_SUFFIXES or "test" in suffix)


def find_dockerfiles(repo_dir: Path) -> list[Path]:
    candidates: list[Path] = []
    for pattern in ("Dockerfile", "Dockerfile.*"):
        candidates.extend(repo_dir.rglob(pattern))
    return sorted(p for p in set(candidates) if p.is_file() and is_production_dockerfile(p))


def find_run_spans(lines: list[str]) -> list[tuple[int, int]]:
    """Return ``[(start_idx, end_idx), ...]`` (0-indexed, inclusive) for every ``RUN``
    instruction, joining backslash-continuation lines into one logical instruction."""
    spans: list[tuple[int, int]] = []
    i = 0
    n = len(lines)
    while i < n:
        if RUN_INSTRUCTION_RE.match(lines[i]):
            start = i
            j = i
            while lines[j].rstrip("\n").rstrip().endswith("\\"):
                j += 1
                if j >= n:
                    j = n - 1
                    break
            spans.append((start, j))
            i = j + 1
        else:
            i += 1
    return spans


def convert_dockerfile(content: str) -> tuple[str, str]:
    """Return ``(new_content, action)`` -- action in {"convert", "ok", "skip"}."""
    lines = content.splitlines(keepends=True)
    if not lines:
        return content, "skip"

    changed = False
    for start, end in find_run_spans(lines):
        joined = "".join(lines[start : end + 1])
        if GAR_TOKEN_MOUNT not in joined:
            continue
        if UV_INSTALL_MARKER not in joined or NO_SOURCES_FLAG not in joined:
            continue
        if RETRY_WRAP_RE.search(joined):
            continue  # already wrapped -- idempotent no-op

        target_idx: int | None = None
        for idx in range(start, end + 1):
            if UV_INSTALL_MARKER in lines[idx]:
                target_idx = idx
                break
        if target_idx is None:
            continue  # defensive -- UV_INSTALL_MARKER matched the join but no single line has it

        raw_line = lines[target_idx]
        line_no_nl = raw_line[:-1] if raw_line.endswith("\n") else raw_line
        has_continuation = line_no_nl.rstrip().endswith("\\")
        body = line_no_nl.rstrip()
        if has_continuation:
            body = body[:-1].rstrip()
        indent = LEADING_WS_RE.match(line_no_nl).group(1)  # type: ignore[union-attr]
        cmd = body.strip()

        new_body = indent + _retry_wrap(cmd)
        if has_continuation:
            new_body += " \\"
        new_line = new_body + ("\n" if raw_line.endswith("\n") else "")
        lines[target_idx] = new_line
        changed = True

    if not changed:
        return content, "ok" if GAR_TOKEN_MOUNT in content else "skip"
    return "".join(lines), "convert"


def load_repo_names() -> list[str]:
    raw = cast(dict[str, object], json.loads(MANIFEST_PATH.read_text()))
    if "repositories" not in raw:
        raise SystemExit("workspace-manifest.json: missing 'repositories' block — refusing to guess")
    repos_obj = raw["repositories"]
    if not isinstance(repos_obj, dict):
        raise SystemExit("workspace-manifest.json: 'repositories' is not an object")
    return sorted(cast(dict[str, object], repos_obj).keys())


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Print changes, do not write")
    parser.add_argument("--repo", type=str, default="", help="Limit to single repo")
    args = parser.parse_args(argv)
    dry_run = cast(bool, args.dry_run)
    only_repo = cast(str, args.repo)

    repo_names = load_repo_names()
    if only_repo:
        if only_repo not in repo_names:
            print(f"Repo '{only_repo}' not in manifest", file=sys.stderr)
            return 1
        repo_names = [only_repo]

    changed = 0
    for repo_name in repo_names:
        if repo_name in SKIP_REPOS:
            continue
        repo_dir = WORKSPACE_ROOT / repo_name
        if not repo_dir.is_dir():
            print(f"  {repo_name}: not on disk -- skipping", file=sys.stderr)
            continue
        for dockerfile in find_dockerfiles(repo_dir):
            rel = dockerfile.relative_to(WORKSPACE_ROOT)
            content = dockerfile.read_text()
            new_content, action = convert_dockerfile(content)
            if action == "skip":
                continue
            if action == "ok":
                print(f"  OK       {rel} (already wrapped)")
                continue
            changed += 1
            if dry_run:
                print(f"  CONVERT  {rel} (dry-run)")
            else:
                dockerfile.write_text(new_content)
                print(f"  CONVERT  {rel}")

    print(f"\n{'Would change' if dry_run else 'Changed'} {changed} Dockerfile(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
