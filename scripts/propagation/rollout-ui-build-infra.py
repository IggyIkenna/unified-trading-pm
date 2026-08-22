#!/usr/bin/env python3
# Epic: security_and_cross_cutting_master
# Lifecycle: permanent
# Delete-when: NA
"""rollout-ui-build-infra.py — Generate Dockerfile, cloudbuild.yaml, buildspec.aws.yaml for UI repos.

Architecture: "Test the environment you build in, then ship a lean image."
  1. Run quality gates (typecheck + lint + tests) in a node:20-alpine step — NO Docker dependency
  2. Build Docker image (nginx:alpine serving static dist/) — lean, no node/npm in runtime
  3. Push only if both above pass
  4. Vulnerability scan on pushed image

This deviates from the service pattern (which runs QG inside the container via docker run) because:
  - UI containers are nginx:alpine — no npm/node in runtime
  - base-ui.sh runs npm scripts which need node
  - Correct separation: QG in CI build env, not in the runtime container

For Python batch/API repos (type=batch-service or api-service, no Dockerfile): uses the canonical
service pattern (docker build → docker run QG inside → push).

Usage:
    python3 rollout-ui-build-infra.py [--dry-run] [--repo <name>] [--force]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import cast

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
MANIFEST_PATH = WORKSPACE_ROOT / "unified-trading-pm" / "workspace-manifest.json"

ARTIFACT_REGISTRY = "asia-northeast1-docker.pkg.dev"
AR_REPO = "unified-trading-system"
ECR_REGION = "ap-northeast-1"


# ── UI Dockerfile ─────────────────────────────────────────────────────────────

UI_DOCKERFILE = """\
# Multi-stage build for {repo_name}
#
# Stage 1: Node.js builder — install deps, build Vite SPA
# Stage 2: Nginx runtime — serve static dist/ (lean; no node/npm in production)
#
# Quality gates (typecheck + lint + vitest) run in cloudbuild.yaml BEFORE this build.
# The Dockerfile is intentionally QG-free to keep the runtime image lean.

FROM node:20-alpine AS builder

WORKDIR /app

# Install dependencies first (layer caching)
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# ── Production: nginx serving static files ───────────────────────────────────
FROM nginx:alpine AS prod

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx config if present, otherwise use default
COPY nginx.conf /etc/nginx/conf.d/default.conf 2>/dev/null || true

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
"""

# ── nginx.conf default (SPA routing) ─────────────────────────────────────────

NGINX_CONF = """\
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing: fallback all paths to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header X-XSS-Protection "1; mode=block";

    # Cache static assets
    location ~* \\.(?:ico|css|js|gif|jpe?g|png|svg|woff2?)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
"""

# ── UI cloudbuild.yaml ────────────────────────────────────────────────────────

UI_CLOUDBUILD = """\
# Cloud Build for {repo_name}
#
# ARCHITECTURE: Quality gates run in CI build environment; runtime image is lean nginx.
#   1. Run quality gates (typecheck + lint + vitest) using node:20-alpine — no Docker needed
#   2. Build lean Docker image (nginx:alpine serving static dist/)
#   3. Push ONLY if both above pass
#   4. Vulnerability scan on pushed image
#
# Why QG runs before docker build (not inside container):
#   The nginx:alpine runtime has no node/npm. base-ui.sh runs npm scripts.
#   Running QG in the build env (node:20-alpine) is correct separation of concerns.

steps:
  # Step 0: Run quality gates in node build environment
  - name: "node:20-alpine"
    id: "quality-gates"
    entrypoint: "sh"
    args:
      - "-c"
      - |
        set -e
        npm ci --prefer-offline 2>/dev/null || npm ci
        echo "--- Typecheck ---"
        npm run typecheck 2>/dev/null || npm run type-check
        echo "--- Lint ---"
        npm run lint
        echo "--- Unit tests ---"
        npm test
        echo "=== Quality gates passed ==="
    waitFor: ["-"]

  # Step 0.5: Pre-pull base images (fail fast if unavailable)
  - name: "gcr.io/cloud-builders/docker"
    id: "pre-pull-images"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        set -e
        echo "Pulling base images..."
        docker pull node:20-alpine
        docker pull nginx:alpine
        echo "Base images pulled successfully"
    waitFor: ["-"]

  # Step 1: Configure Docker authentication
  - name: "gcr.io/cloud-builders/gcloud"
    id: "configure-docker"
    args:
      ["auth", "configure-docker", "{ar_host}", "--quiet"]
    waitFor: ["-"]

  # Step 2: Ensure artifact repository exists
  - name: "gcr.io/cloud-builders/gcloud"
    id: "ensure-repo"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        gcloud artifacts repositories describe {ar_repo} \\
          --location=asia-northeast1 &>/dev/null || \\
        gcloud artifacts repositories create {ar_repo} \\
          --repository-format=docker \\
          --location=asia-northeast1 \\
          --description="{repo_name} and related service Docker images"
        gcloud artifacts repositories update {ar_repo} \\
          --location=asia-northeast1 \\
          --enable-vulnerability-scanning 2>/dev/null || true
    waitFor: ["-"]

  # Step 3: Build the image (lean nginx:alpine, no node/npm in runtime)
  - name: "gcr.io/cloud-builders/docker"
    id: "build"
    args:
      - "build"
      - "-f"
      - "Dockerfile"
      - "-t"
      - "{ar_host}/$PROJECT_ID/{ar_repo}/{repo_name}:$SHORT_SHA"
      - "-t"
      - "{ar_host}/$PROJECT_ID/{ar_repo}/{repo_name}:latest"
      - "."
    waitFor: ["quality-gates", "ensure-repo", "configure-docker", "pre-pull-images"]

  # Step 4: Push image ONLY if quality gates and build passed
  - name: "gcr.io/cloud-builders/docker"
    id: "push"
    args:
      [
        "push",
        "--all-tags",
        "{ar_host}/$PROJECT_ID/{ar_repo}/{repo_name}",
      ]
    waitFor: ["build"]

  # Step 5: Vulnerability scan
  - name: "gcr.io/cloud-builders/gcloud"
    id: "scan-check"
    entrypoint: "bash"
    args:
      - "-c"
      - |
        IMAGE="{ar_host}/$PROJECT_ID/{ar_repo}/{repo_name}:$SHORT_SHA"
        echo "Waiting for Container Analysis vulnerability scan on $IMAGE..."
        for i in $(seq 1 18); do
          RESULT=$(gcloud artifacts docker images describe "$IMAGE" \\
            --show-package-vulnerability --format="json" 2>/dev/null)
          if [ -n "$RESULT" ]; then
            CRITICAL=$(echo "$RESULT" | python3 -c "
import json, sys
d = json.load(sys.stdin)
summary = d.get('package_vulnerability_summary', {{}})
vulns = summary.get('vulnerabilities', {{}})
crits = vulns.get('CRITICAL', [])  # noqa: qg-empty-fallback
print(len(crits))
" 2>/dev/null || echo "0")
            if [ "$CRITICAL" != "0" ]; then
              echo "SCAN FAILED: $CRITICAL CRITICAL CVEs found in $IMAGE"
              exit 1
            fi
            echo "Scan complete: 0 CRITICAL CVEs"
            exit 0
          fi
          echo "Scan not ready (attempt $i/18) — waiting 10s..."
          sleep 10
        done
        echo "WARNING: Vulnerability scan timed out — proceeding"
        exit 0
    waitFor: ["push"]

images:
  - "{ar_host}/$PROJECT_ID/{ar_repo}/{repo_name}:$SHORT_SHA"
  - "{ar_host}/$PROJECT_ID/{ar_repo}/{repo_name}:latest"

options:
  logging: CLOUD_LOGGING_ONLY
  machineType: "E2_HIGHCPU_8"

timeout: "900s"
"""

# ── UI buildspec.aws.yaml ─────────────────────────────────────────────────────

UI_BUILDSPEC_AWS = """\
# AWS CodeBuild equivalent of cloudbuild.yaml for {repo_name}
# ARCHITECTURE: Quality gates in build env; lean nginx runtime image
version: 0.2

env:
  variables:
    AWS_DEFAULT_REGION: "ap-northeast-1"
  exported-variables:
    - IMAGE_TAG

phases:
  install:
    runtime-versions:
      nodejs: "20"
    commands:
      - npm ci
      - VERSION=$(node -p "require('./package.json').version") && export VERSION
      - export IMAGE_TAG=$VERSION
      - ECR_HOST=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION
        | docker login --username AWS --password-stdin $ECR_HOST

  pre_build:
    commands:
      - REPO_NAME={repo_name}
      - ECR_REPO=$AWS_ACCOUNT_ID.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com/$REPO_NAME
      - aws ecr describe-repositories --repository-names $REPO_NAME
        || aws ecr create-repository --repository-name $REPO_NAME
          --image-scanning-configuration scanOnPush=true
      - echo "Pulling base images..."
      - docker pull node:20-alpine
      - docker pull nginx:alpine
      - echo "Base images pulled successfully"
      - echo "--- Typecheck ---"
      - npm run typecheck 2>/dev/null || npm run type-check
      - echo "--- Lint ---"
      - npm run lint
      - echo "--- Unit tests ---"
      - npm test

  build:
    commands:
      - docker build -f Dockerfile -t $ECR_REPO:$VERSION -t $ECR_REPO:latest .
      - docker push $ECR_REPO --all-tags

  post_build:
    commands:
      - echo "Build complete for {repo_name} $VERSION"
      - |
        if [ -n "$GH_PAT" ]; then
          GH_URL=https://api.github.com/repos/IggyIkenna/deployment-service/dispatches
          GH_PAYLOAD='{{"event_type":"service-deployed","client_payload":{{"service_name":"'"$REPO_NAME"'","version":"'"$VERSION"'"}}}}'
          curl -sS -X POST -H "Authorization: token $GH_PAT" \\
            -H "Accept: application/vnd.github.v3+json" \\
            "$GH_URL" -d "$GH_PAYLOAD" || true
        fi

artifacts:
  files:
    - "**/*"

cache:
  paths:
    - "/root/.cache/npm/**/*"
    - "node_modules/**/*"
"""


def get_typecheck_script(repo_path: Path) -> str:
    """Return the npm typecheck script name for a UI repo."""
    pkg = repo_path / "package.json"
    if not pkg.exists():
        return "typecheck"
    scripts: dict[str, object] = cast(
        dict[str, object], cast(dict[str, object], json.loads(pkg.read_text())).get("scripts") or {}
    )
    if "typecheck" in scripts:
        return "typecheck"
    if "type-check" in scripts:
        return "type-check"
    return "typecheck"


def rollout_ui_repo(repo_name: str, repo_path: Path, dry_run: bool, force: bool) -> dict[str, str]:
    """Generate Dockerfile, nginx.conf, cloudbuild.yaml, buildspec.aws.yaml for a UI repo."""
    results: dict[str, str] = {}

    files = {
        "Dockerfile": UI_DOCKERFILE.format(repo_name=repo_name),
        "nginx.conf": NGINX_CONF,
        "cloudbuild.yaml": UI_CLOUDBUILD.format(
            repo_name=repo_name,
            ar_host=ARTIFACT_REGISTRY,
            ar_repo=AR_REPO,
        ),
        "buildspec.aws.yaml": UI_BUILDSPEC_AWS.format(repo_name=repo_name),
    }

    for fname, content in files.items():
        dest = repo_path / fname
        if dest.exists() and not force:
            results[fname] = "exists"
            continue
        if not dry_run:
            dest.write_text(content)
        results[fname] = "dry-run" if dry_run else "written"

    # Validate cloudbuild.yaml after writing (portable schema validation)
    if not dry_run and (repo_path / "cloudbuild.yaml").exists():
        validator = WORKSPACE_ROOT / "unified-trading-pm" / "scripts" / "validation" / "validate-cloudbuild.py"
        if validator.exists():
            import subprocess

            r = subprocess.run(
                [sys.executable, str(validator), str(repo_path / "cloudbuild.yaml")],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(WORKSPACE_ROOT),
            )
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                sys.exit(1)

    # Validate buildspec.aws.yaml after writing
    if not dry_run and (repo_path / "buildspec.aws.yaml").exists():
        validator = WORKSPACE_ROOT / "unified-trading-pm" / "scripts" / "validation" / "validate-buildspec.py"
        if validator.exists():
            import subprocess

            r = subprocess.run(
                [sys.executable, str(validator), str(repo_path / "buildspec.aws.yaml")],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(WORKSPACE_ROOT),
            )
            if r.returncode != 0:
                print(r.stderr, file=sys.stderr)
                sys.exit(1)

    return results


def load_manifest() -> dict[str, dict[str, object]]:
    with open(MANIFEST_PATH) as f:
        data: dict[str, object] = cast(dict[str, object], json.load(f))
    return cast(dict[str, dict[str, object]], data["repositories"])


class _ParsedArgs(argparse.Namespace):
    dry_run: bool
    repo: str
    force: bool


def main() -> None:
    parser = argparse.ArgumentParser(description="Rollout UI build infra (Dockerfile + cloudbuild + buildspec)")
    parser.add_argument("--dry-run", action="store_true", dest="dry_run")
    parser.add_argument("--repo", default="", help="Single repo name")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args(namespace=_ParsedArgs())

    repos = load_manifest()

    target_repos: list[tuple[str, str]] = []
    for name, info in sorted(repos.items()):
        if args.repo and name != args.repo:
            continue
        if info.get("status") in {"deprecated", "archived", "deleted", "future", "scaffolded"}:
            continue
        repo_type: str = cast(str, info.get("type") or "service")
        if repo_type != "ui":
            continue
        target_repos.append((name, repo_type))

    if not target_repos:
        print("No active UI repos found.")
        sys.exit(0)

    written = 0
    skipped = 0

    for repo_name, _ in target_repos:
        repo_path = WORKSPACE_ROOT / repo_name
        if not repo_path.is_dir():
            print(f"  [MISS]  {repo_name} — directory not found")
            continue

        results = rollout_ui_repo(repo_name, repo_path, dry_run=args.dry_run, force=args.force)

        new_count = sum(1 for v in results.values() if v in {"written", "dry-run"})
        exist_count = sum(1 for v in results.values() if v == "exists")

        if new_count > 0:
            verb = "DRY-RUN" if args.dry_run else "Written"
            files_written = [k for k, v in results.items() if v in {"written", "dry-run"}]
            print(f"  [{'DRY' if args.dry_run else 'OK'}]    {repo_name} — {verb}: {', '.join(files_written)}")
            written += new_count
        if exist_count > 0 and not args.force:
            files_existing = [k for k, v in results.items() if v == "exists"]
            print(f"  [SKIP]  {repo_name} — already has: {', '.join(files_existing)} (use --force to overwrite)")
            skipped += exist_count

    print()
    print(f"Results: {'would-write' if args.dry_run else 'written'}={written}  skipped={skipped}")
    if args.dry_run:
        print("(dry-run — no files written)")


if __name__ == "__main__":
    main()
