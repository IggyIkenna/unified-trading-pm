#!/usr/bin/env python3
"""
add-dockerfile-digest-arg.py

Converts production Dockerfiles to the FROM-digest ratchet pattern (QG STEP 5.79,
plan dependency_promotion_range_pins_and_major_bump_sit_2026_06_09.md Phase 6):
each consumer Dockerfile carries a checked-in `ARG BASE_IMAGE_DIGEST=sha256:<digest>`
default, consumed in the unified-trading-library FROM line:

    ARG PROJECT_ID
    ARG BASE_IMAGE_DIGEST=sha256:<digest>
    FROM --platform=linux/amd64 asia-northeast1-docker.pkg.dev/${PROJECT_ID}/\
unified-trading-library/unified-trading-library@${BASE_IMAGE_DIGEST}

The digest default makes rebuilds byte-deterministic + records exactly which UTL/UAC
build went in (provenance), while `--build-arg BASE_IMAGE_DIGEST=...` lets cloudbuild
inject a fresher digest at build time. Digest freshness rides the dependency-update
fan-out (update-dependency-version.yml rewrites the ARG default on base-image publish).

Handles both consumption shapes found in the fleet:
  - direct FROM:  FROM ...unified-trading-library/unified-trading-library:latest
  - indirect ARG: ARG BASE_IMAGE=...unified-trading-library:latest + FROM ${BASE_IMAGE}
    (instruments-service) -- the ARG default is rewritten; FROM is left untouched.

Idempotent: re-running with the same digest is a no-op; a newer digest refreshes the
ARG default in place. Preserves --platform flags, ${PROJECT_ID}, and stage aliases.

Skips: unified-trading-library (base-image owner), unified-trading-pm, dev/test/ci
Dockerfile variants, and vendored/test directories.

Usage:
    python add-dockerfile-digest-arg.py [--dry-run] [--repo NAME] [--digest sha256:HEX]

Options:
    --dry-run         Print what would change without writing files.
    --repo NAME       Process a single repo only.
    --digest DIGEST   Use this digest (sha256:<64-hex>) instead of resolving via gcloud.
    --project-id ID   GCP project for gcloud digest resolution (default: the active
                      `gcloud config get-value project` — no project id is hardcoded here).
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import cast

SCRIPT_DIR = Path(__file__).resolve().parent
PM_ROOT = SCRIPT_DIR.parent.parent
WORKSPACE_ROOT = PM_ROOT.parent
MANIFEST_PATH = PM_ROOT / "workspace-manifest.json"

REGISTRY_HOST = "asia-northeast1-docker.pkg.dev"
UTL_IMAGE_PATH = "unified-trading-library/unified-trading-library"
DIGEST_ARG_NAME = "BASE_IMAGE_DIGEST"

SKIP_REPOS = {
    "unified-trading-pm",  # not a deployed package
    "unified-trading-library",  # base-image owner -- pins python:slim, not itself
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

DIGEST_RE = re.compile(r"^sha256:[0-9a-f]{64}$")

# A UTL base-image reference with its current pin (mutable :tag, literal digest,
# or the already-converted @${BASE_IMAGE_DIGEST}).
UTL_IMAGE_REF_RE = re.compile(
    r"(?P<base>"
    + re.escape(REGISTRY_HOST)
    + r"/(?:\$\{PROJECT_ID\}|[A-Za-z0-9_.-]+)/"
    + re.escape(UTL_IMAGE_PATH)
    + r")"
    r"(?P<pin>:[A-Za-z0-9_.-]+|@\$\{" + DIGEST_ARG_NAME + r"\}|@sha256:[0-9a-f]{64})"
)

DIGEST_ARG_LINE_RE = re.compile(
    r"^(?P<indent>\s*)ARG\s+" + DIGEST_ARG_NAME + r"=(?P<digest>sha256:[0-9a-f]{64})\s*$",
    re.MULTILINE,
)

DIGEST_ARG_COMMENT = (
    "# Digest-pinned UTL base image (QG STEP 5.79 -- reproducible builds + UTL/UAC provenance).\n"
    "# Refreshed by the dependency-update fan-out (update-dependency-version.yml) on base-image\n"
    "# republish; cloudbuild may override at build time: --build-arg BASE_IMAGE_DIGEST=sha256:...\n"
)


def resolve_digest_via_gcloud(project_id: str) -> str:
    """Resolve the current :latest digest of the UTL base image via gcloud (ADC)."""
    image = f"{REGISTRY_HOST}/{project_id}/{UTL_IMAGE_PATH}:latest"
    cmd = [
        "gcloud",
        "artifacts",
        "docker",
        "images",
        "describe",
        image,
        "--format=value(image_summary.digest)",
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=60)
    except FileNotFoundError:
        raise SystemExit(
            f"gcloud not on PATH -- pass --digest sha256:<64-hex> explicitly (resolve with: {' '.join(cmd)})"
        ) from None
    except subprocess.TimeoutExpired:
        raise SystemExit("gcloud digest resolution timed out -- pass --digest explicitly") from None
    digest = result.stdout.strip()
    if result.returncode != 0 or not DIGEST_RE.match(digest):
        raise SystemExit(
            f"Failed to resolve digest for {image} "
            f"(rc={result.returncode}, stdout={digest!r}, stderr={result.stderr.strip()!r}) "
            "-- pass --digest sha256:<64-hex> explicitly"
        )
    return digest


def load_repo_names() -> list[str]:
    raw = cast(dict[str, object], json.loads(MANIFEST_PATH.read_text()))
    if "repositories" not in raw:
        raise SystemExit("workspace-manifest.json: missing 'repositories' block — refusing to guess")
    repos_obj = raw["repositories"]
    if not isinstance(repos_obj, dict):
        raise SystemExit("workspace-manifest.json: 'repositories' is not an object")
    return sorted(cast(dict[str, object], repos_obj).keys())


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


def insert_digest_arg(content: str, digest: str) -> str:
    """Insert the ARG BASE_IMAGE_DIGEST default directly above its first consumer line."""
    lines = content.split("\n")
    consumer_idx: int | None = None
    for i, line in enumerate(lines):
        if "${" + DIGEST_ARG_NAME + "}" in line:
            consumer_idx = i
            break
    if consumer_idx is None:
        return content  # nothing consumes the ARG -- do not insert dead config
    block = DIGEST_ARG_COMMENT + f"ARG {DIGEST_ARG_NAME}={digest}"
    lines.insert(consumer_idx, block)
    return "\n".join(lines)


def convert_dockerfile(content: str, digest: str) -> tuple[str, str]:
    """Return (new_content, action) -- action in {convert, refresh, ok, skip}."""
    if not UTL_IMAGE_REF_RE.search(content):
        return content, "skip"

    new_content = UTL_IMAGE_REF_RE.sub(lambda m: m.group("base") + "@${" + DIGEST_ARG_NAME + "}", content)

    arg_match = DIGEST_ARG_LINE_RE.search(new_content)
    if arg_match is None:
        new_content = insert_digest_arg(new_content, digest)
        return new_content, "convert"
    if arg_match.group("digest") != digest:
        new_content = DIGEST_ARG_LINE_RE.sub(
            lambda m: f"{m.group('indent')}ARG {DIGEST_ARG_NAME}={digest}", new_content
        )
        return new_content, "refresh"
    return new_content, "convert" if new_content != content else "ok"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Print changes, do not write")
    parser.add_argument("--repo", type=str, default="", help="Limit to single repo")
    parser.add_argument("--digest", type=str, default="", help="Digest override (sha256:<64-hex>)")
    parser.add_argument(
        "--project-id",
        type=str,
        default="",
        help="GCP project for gcloud resolution (default: active `gcloud config get-value project`)",
    )
    args = parser.parse_args()
    dry_run = cast(bool, args.dry_run)
    only_repo = cast(str, args.repo)
    digest = cast(str, args.digest)
    project_id = cast(str, args.project_id)

    if digest:
        if not DIGEST_RE.match(digest):
            print(f"--digest must match sha256:<64-hex>, got: {digest!r}", file=sys.stderr)
            return 1
    else:
        if not project_id:
            # No hardcoded project id (QG codex rule): default to the active gcloud project, loud-fail if unset.
            proc = subprocess.run(
                ["gcloud", "config", "get-value", "project"], capture_output=True, text=True, timeout=30, check=False
            )
            project_id = proc.stdout.strip()
            if proc.returncode != 0 or not project_id or project_id == "(unset)":
                raise SystemExit("No --project-id given and no active gcloud project — pass --project-id or --digest")
        digest = resolve_digest_via_gcloud(project_id)
    print(f"Base-image digest: {digest}")

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
            new_content, action = convert_dockerfile(content, digest)
            if action == "skip":
                continue
            if action == "ok":
                print(f"  OK       {rel} (already pinned to current digest)")
                continue
            changed += 1
            verb = "CONVERT" if action == "convert" else "REFRESH"
            if dry_run:
                print(f"  {verb}  {rel} (dry-run)")
            else:
                dockerfile.write_text(new_content)
                print(f"  {verb}  {rel}")

    print(f"\n{'Would change' if dry_run else 'Changed'} {changed} Dockerfile(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
