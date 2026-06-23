# Epic: observability_master
# Lifecycle: campaign
# Delete-when: build caching rolled out + committed to all repos (detect via grep --cache-from across fleet)
"""Add BuildKit inline layer caching to a repo's cloudbuild.yaml (operator ask 2026-06-23).

Most service/library cloudbuilds use the bash-heredoc build shape:

    id: "build"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        VERSION=$(cat /workspace/VERSION ...)
        docker build -f Dockerfile \
          --build-arg PROJECT_ID=$PROJECT_ID \
          -t .../${_SERVICE_NAME}:$SHORT_SHA \
          ...
          .

This patcher (idempotent) turns that into a cached build by:
  1. pull-base-image: after `docker pull "$${BASE}:latest" || true`, also pull the
     repo's OWN `:latest` so its layers seed the cache.
  2. build: `docker build` -> `DOCKER_BUILDKIT=1 docker build`, and inject
     `--build-arg BUILDKIT_INLINE_CACHE=1` + `--cache-from <repo>:latest`.

A first build (or cache miss) is unaffected — `docker pull … || true` is best-effort
and `--cache-from` silently ignores an absent image. Subsequent builds reuse the
unchanged deps/UI layers (~10min -> ~2-3min for a small source change). The inline
cache metadata (`BUILDKIT_INLINE_CACHE=1`) is what the NEXT build's --cache-from reads.

Shapes it does NOT touch (reports SKIP, never mangles):
  - already-cached files (`--cache-from` present)
  - the args-list shape (deployment-api) — already cached by hand
  - a file with no recognizable `docker build` invocation

Usage:  python add-cloudbuild-cache.py <path/to/cloudbuild.yaml> [--apply]
        (default is a dry-run diff; --apply writes the file)
"""

from __future__ import annotations

import argparse
import difflib
import sys
from pathlib import Path

_IMG = "asia-northeast1-docker.pkg.dev/$PROJECT_ID/${_REGISTRY_REPO}/${_SERVICE_NAME}:latest"
_BASE_PULL = 'docker pull "$${BASE}:latest" || true'
_CACHE_PULL = f'docker pull "{_IMG}" || true'


def patch_text(text: str) -> tuple[str, str]:
    """Return (new_text, status). status in {patched, already_cached, no_build_step, unhandled}."""
    if "--cache-from" in text or "BUILDKIT_INLINE_CACHE" in text:
        return text, "already_cached"
    if "docker build -f Dockerfile" not in text:
        return text, "no_build_step"

    lines = text.splitlines(keepends=True)
    out: list[str] = []
    did_pull = did_build = did_args = False
    for line in lines:
        stripped = line.rstrip("\n")
        # 1) seed the repo's own :latest right after the base-image pull
        if not did_pull and stripped.strip() == _BASE_PULL:
            out.append(line)
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}# layer-cache seed: pull our own previous :latest so --cache-from reuses layers\n")
            out.append(f"{indent}{_CACHE_PULL}\n")
            did_pull = True
            continue
        # 2) enable BuildKit on the docker build line
        if not did_build and stripped.strip().startswith("docker build -f Dockerfile"):
            out.append(line.replace("docker build -f Dockerfile", "DOCKER_BUILDKIT=1 docker build -f Dockerfile", 1))
            did_build = True
            continue
        # 3) inject the cache build-args right after the PROJECT_ID build-arg line
        if did_build and not did_args and "--build-arg PROJECT_ID=$PROJECT_ID" in stripped:
            out.append(line)
            indent = line[: len(line) - len(line.lstrip())]
            out.append(f"{indent}--build-arg BUILDKIT_INLINE_CACHE=1 \\\n")
            out.append(f"{indent}--cache-from {_IMG} \\\n")
            did_args = True
            continue
        out.append(line)

    if not (did_pull and did_build and did_args):
        return text, "unhandled"
    return "".join(out), "patched"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path", type=Path)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not args.path.is_file():
        print(f"SKIP (not a file): {args.path}")
        return 0
    original = args.path.read_text()
    new, status = patch_text(original)
    repo = args.path.parent.name
    if status != "patched":
        print(f"SKIP[{status}]: {repo}")
        return 0
    if args.apply:
        args.path.write_text(new)
        print(f"PATCHED: {repo}")
    else:
        diff = "".join(
            difflib.unified_diff(original.splitlines(True), new.splitlines(True), f"{repo}/cloudbuild.yaml", "patched")
        )
        print(diff)
        print(f"DRY-RUN PATCHED (would write): {repo}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
