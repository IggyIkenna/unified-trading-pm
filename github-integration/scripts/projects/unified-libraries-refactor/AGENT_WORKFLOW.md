# Agent Workflow: Unified Libraries Refactor - Local Execution

## Purpose

This document provides instructions for an AI agent to complete a subtask from the Unified Libraries Refactor epic,
matching the batch automation workflow but running locally.

## Prerequisites

- Repository must have quality gates script: `scripts/quality-gates.sh`
- Repository must have quickmerge script: `scripts/quickmerge.sh`
- Agent has access to GitHub via `gh` CLI
- Agent can run bash scripts
- Epic breakdown file available:
  `unified-trading-codex/11-project-management/epic-breakdowns/epic-unified-libraries-refactor.md`

## CRITICAL: Project Context

**Before starting any subtask, read the epic documentation:**

| Document                   | Purpose                           | Location                                                                                          |
| -------------------------- | --------------------------------- | ------------------------------------------------------------------------------------------------- |
| **Epic Overview**          | High-level goals and architecture | `@unified-trading-codex/11-project-management/epics/unified-libraries-refactor-epic.md`           |
| **Epic Breakdown**         | All 51 subtasks with details      | `@unified-trading-codex/11-project-management/epic-breakdowns/epic-unified-libraries-refactor.md` |
| **Infrastructure Updates** | Build/publish/test changes        | `@~/.cursor/plans/infrastructure-updates-for-library-refactor.md`                                 |
| **Quality Gates**          | Core quality gates spec           | `@unified-trading-codex/06-coding-standards/quality-gates.md`                                     |
| **Git Workflow**           | Branch protection, quickmerge     | `@unified-trading-codex/.cursor/rules/git-workflow.mdc`                                           |

## Project Goals (Quick Ref)

**Split unified-trading-services into focused libraries:**

1. **Phase 0 (Infra)**: Artifact Registry Python repo, IAM permissions, docs
2. **Phase 1 (Events)**: PubSub abstraction + unified-trading-library
3. **Phase 2 (Config)**: unified-config-interface with hot-reload
4. **Phase 3 (Market)**: unified-market-interface for market data feeds
5. **Phase 4 (Order)**: unified-order-interface for order execution

**Key Architecture Decisions:**

- **Cloud-agnostic**: Only unified-trading-services touches cloud providers
- **Backward compatibility**: Services work with ZERO code changes (transitive dependencies + re-exports)
- **Python packages**: Published to GCP Artifact Registry (NOT GitHub Packages)
- **Quality gates**: Must pass in Local, GitHub Actions, Cloud Build

## Workflow Steps

### Step 1: Pull Issue Details and Read Epic Breakdown

```bash
# Get issue number and repo from context
REPO_NAME="[REPO_NAME]"  # e.g., "unified-trading-library"
ISSUE_NUMBER="[ISSUE_NUMBER]"  # e.g., "3"

# Fetch issue details
gh issue view $ISSUE_NUMBER --repo "IggyIkenna/$REPO_NAME" --json title,body,labels

# Extract subtask ID from issue (e.g., "Subtask 1.2.1")
```

**Read subtask from epic breakdown:**

```bash
# Open epic breakdown to find your subtask
cat unified-trading-codex/11-project-management/epic-breakdowns/epic-unified-libraries-refactor.md | \
    grep -A 50 "Subtask [0-4]\.[0-9]\+\.[0-9]\+:"
```

**Extract from subtask:**

- **Description**: What needs to be done
- **Complexity**: LOW/MEDIUM/HIGH
- **Priority**: P0-critical, P1-high, P2-medium
- **Risk**: TRIVIAL/MODERATE/HIGH
- **Estimated**: Hours estimate
- **Files to modify**: Which files to create/edit
- **Codex sections**: Standards to follow
- **Tests required**: What tests to add
- **Blocking**: Dependencies on other subtasks
- **Parent**: Epic reference

### Step 2: Understand Subtask Context

**Check which phase:**

- **Phase 0 (Infrastructure)**: 0.x subtasks → Manual GCP commands, no PR
- **Phase 1 (Events)**: 1.x subtasks → PubSub + events interface
- **Phase 2 (Config)**: 2.x subtasks → Config interface
- **Phase 3 (Market)**: 3.x subtasks → Market data interface
- **Phase 4 (Order)**: 4.x subtasks → Order execution interface

**Check repo type:**

- **New library repos**: unified-trading-library, unified-config-interface, unified-market-interface,
  unified-order-interface
  - Start from scratch (no existing code)
  - Create repo structure first (pyproject.toml, README.md, src/, tests/, scripts/)
  - Add quality-gates.sh and quickmerge.sh scripts
- **Existing repo**: unified-trading-services
  - Already has structure
  - Modify existing code
  - Add new abstractions (e.g., PubSub)
  - Add re-exports for backward compatibility

### Step 3: Implement Subtask

#### 3.1: For New Library Repos (First Task)

**If this is the first subtask for a new library (e.g., "Create repo structure"):**

````bash
cd /path/to/$REPO_NAME

# 1. Create directory structure
mkdir -p ${REPO_NAME//-/_}/  # e.g., unified_trading_library.events/
mkdir -p tests/unit tests/integration tests/e2e tests/smoke
mkdir -p scripts

# 2. Create pyproject.toml
cat > pyproject.toml <<'EOF'
[project]
name = "[REPO_NAME]"
version = "0.1.0"
description = "Part of Unified Libraries Refactor - [description]"
readme = "README.md"
requires-python = ">=3.13,<3.14"
dependencies = [
    # Cloud abstractions (ONLY via unified-trading-services)
    # Note: unified-trading-services NOT listed here (installed separately)
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-xdist>=3.3.1",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.0",
    "ruff==0.15.0",
]

[build-system]
requires = ["setuptools>=68.0"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["."]

[tool.ruff]
line-length = 120
target-version = "py313"

[tool.pytest.ini_options]
addopts = "-v --tb=short --strict-markers"
testpaths = ["tests"]
python_files = "test_*.py"
python_classes = "Test*"
python_functions = "test_*"
EOF

# 3. Create README.md
cat > README.md <<'EOF'
# [REPO_NAME]

Part of the Unified Libraries Refactor epic.

## Overview

[Brief description]

## Installation

```bash
# From GCP Artifact Registry (private)
uv pip install [REPO_NAME] \\
    --index-url https://asia-northeast1-python.pkg.dev/test-project/unified-libraries/simple/
````

## Usage

```python
from [package_name] import [key_exports]
```

## Development

```bash
# Install dependencies
uv pip install -e ".[dev]"

# Run quality gates
bash scripts/quality-gates.sh
```

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=[package_name] --cov-report=html
```

## Related Documentation

- **Epic Overview**: `unified-trading-codex/11-project-management/epics/unified-libraries-refactor-epic.md`
- **Epic Breakdown**: `unified-trading-codex/11-project-management/epic-breakdowns/epic-unified-libraries-refactor.md`
- **Coding Standards**: `unified-trading-codex/06-coding-standards/README.md` EOF

# 4. Copy quality-gates.sh and quickmerge.sh from unified-trading-services

cp ../unified-trading-services/scripts/quality-gates.sh ./scripts/ cp ../unified-trading-services/scripts/quickmerge.sh
./scripts/ chmod +x scripts/\*.sh

# 5. Create **init**.py

cat > ${REPO*NAME//-/*}/**init**.py <<'EOF' """[REPO_NAME] - Part of Unified Libraries Refactor."""

**version** = "0.1.0" EOF

# 6. Create initial test

cat > tests/unit/test_version.py <<'EOF' """Test package version.""" from [package_name] import **version**

def test_version(): """Test that version is defined.""" assert **version** == "0.1.0" EOF

# 7. Run uv lock to create lockfile

uv lock

````

#### 3.2: For Existing Repos (unified-trading-services)

**If modifying unified-trading-services:**

```bash
cd /path/to/unified-trading-services

# Pull latest main
git checkout main
git pull origin main

# Create feature branch
git checkout -b subtask-${ISSUE_NUMBER}-[descriptive-name]

# Make changes as specified in epic breakdown
# (e.g., add PubSub abstraction, add re-exports)

# Update uv.lock if dependencies changed
uv lock
````

#### 3.3: Implement Code Changes

**Follow epic breakdown specifications:**

```bash
# Example: Create PubSub abstraction (Subtask 1.1.2)

cat > unified_trading_services/core/pubsub_abstraction.py <<'EOF'
"""Cloud-agnostic PubSub interface (GCP Pub/Sub ↔ AWS SNS/SQS)."""

from abc import ABC, abstractmethod
from typing import Any


class PubSubClient(ABC):
    """Cloud-agnostic PubSub interface."""

    @abstractmethod
    def publish(self, topic: str, message: dict[str, Any]) -> str:
        """Publish message to topic, returns message ID."""
        pass

    @abstractmethod
    def subscribe(self, topic: str, subscription: str, callback: callable) -> None:
        """Subscribe to topic with callback."""
        pass

    @abstractmethod
    def create_topic(self, topic: str) -> None:
        """Create topic if it doesn't exist."""
        pass

    @abstractmethod
    def create_subscription(self, topic: str, subscription: str) -> None:
        """Create subscription to topic."""
        pass


class GCPPubSubClient(PubSubClient):
    """GCP Pub/Sub implementation."""

    def __init__(self, project_id: str):
        from google.cloud import pubsub_v1
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()

    def publish(self, topic: str, message: dict[str, Any]) -> str:
        """Publish message to GCP Pub/Sub topic."""
        import json
        topic_path = self.publisher.topic_path(self.project_id, topic)
        data = json.dumps(message).encode("utf-8")
        future = self.publisher.publish(topic_path, data)
        return future.result()

    # ... other methods


class AWSPubSubClient(PubSubClient):
    """AWS SNS/SQS implementation."""

    def __init__(self, region: str):
        import boto3
        self.sns = boto3.client("sns", region_name=region)
        self.sqs = boto3.client("sqs", region_name=region)

    def publish(self, topic: str, message: dict[str, Any]) -> str:
        """Publish message to AWS SNS topic."""
        import json
        response = self.sns.publish(
            TopicArn=topic,
            Message=json.dumps(message)
        )
        return response["MessageId"]

    # ... other methods
EOF

# Add tests
cat > tests/unit/test_pubsub_abstraction.py <<'EOF'
"""Test PubSub abstraction."""
import pytest
from unittest.mock import Mock, patch
from unified_trading_services.core.pubsub_abstraction import (
    PubSubClient,
    GCPPubSubClient,
    AWSPubSubClient,
)


def test_pubsub_client_is_abstract():
    """Test that PubSubClient is abstract."""
    with pytest.raises(TypeError):
        PubSubClient()


@patch("unified_trading_services.core.pubsub_abstraction.pubsub_v1")
def test_gcp_pubsub_client_publish(mock_pubsub):
    """Test GCP PubSub publish."""
    mock_publisher = Mock()
    mock_pubsub.PublisherClient.return_value = mock_publisher

    client = GCPPubSubClient(project_id="test-project")
    message_id = client.publish("test-topic", {"key": "value"})

    assert mock_publisher.publish.called


# ... more tests
EOF
```

#### 3.4: Add Tests

**Follow testing standards:**

- **Unit tests**: `tests/unit/` - Synthetic fixtures, no real GCS data
- **Integration tests**: `tests/integration/` - Minimal data, <120s
- **E2E tests**: `tests/e2e/` - Single shard, <180s
- **Smoke tests**: `tests/smoke/` - `--max-results 1`

**Coverage target**: Minimum 35% to pass quality gates; 80% for audit readiness

### Step 4: Run Quality Gates

```bash
cd /path/to/$REPO_NAME

# Run with auto-fix first
bash scripts/quality-gates.sh

# Then verify they pass
bash scripts/quality-gates.sh --no-fix
```

**If quality gates FAIL:**

#### 4a: Check for missing dependencies

```bash
# If pytest-xdist missing
pip show pytest-xdist || uv pip install pytest-xdist

# Add to pyproject.toml dev dependencies if missing
# Then: uv lock
```

#### 4b: Fix code issues

**Common issues:**

- Ruff formatting: Run `ruff format .`
- Ruff linting: Run `ruff check --fix .`
- Import errors: Check imports at top of file
- Test failures: Fix root cause (never skip tests)

#### 4c: Ensure three-environment consistency

**Local vs CI vs Cloud Build must match:**

```bash
# Verify GitHub Actions workflow exists
cat .github/workflows/quality-gates.yml

# Should have:
# - python-version-file: 'pyproject.toml'
# - uv pip install --system -e ".[dev]"
# - bash scripts/quality-gates.sh --no-fix
```

### Step 5: Submit PR

```bash
cd /path/to/$REPO_NAME

# List changed files
git status

# Run quickmerge (includes quality gates + creates PR)
bash scripts/quickmerge.sh \
    "Complete subtask #$ISSUE_NUMBER: [subtask title]

[Brief description of changes]

- Created/modified: [files]
- Added tests: [test files]
- Updated dependencies: [if uv.lock changed]

Closes #$ISSUE_NUMBER" \
    --files "[list of changed files including uv.lock if deps changed]"
```

**Expected result:**

- ✅ Quality gates pass
- ✅ PR created with auto-merge enabled
- ✅ Branch pushed to GitHub
- ✅ Issue referenced in PR body (`Closes #$ISSUE_NUMBER`)

### Step 6: Verify PR Passes CI

```bash
# Check PR status
PR_NUMBER=$(gh pr list --repo "IggyIkenna/$REPO_NAME" --head "$(git branch --show-current)" --json number --jq '.[0].number')

# Monitor CI status
gh pr view $PR_NUMBER --repo "IggyIkenna/$REPO_NAME"

# Wait for checks to pass
gh pr checks $PR_NUMBER --repo "IggyIkenna/$REPO_NAME" --watch
```

**If CI fails:**

**STOP! If local quality gates passed, this is an infrastructure mismatch.**

#### 6a: Diagnose Infrastructure Mismatch

```bash
# Pull CI logs
gh run view --repo "IggyIkenna/$REPO_NAME" --log

# Common issues:
# 1. Missing .github/workflows/quality-gates.yml
# 2. Workflow not calling quality-gates.sh
# 3. Dependencies not installed correctly
# 4. Python version mismatch
```

#### 6b: Fix GitHub Actions Workflow

**Create or update `.github/workflows/quality-gates.yml`:**

```yaml
name: Quality Gates

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  quality-gates:
    runs-on: ubuntu-22.04
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version-file: "pyproject.toml"

      - name: Install dependencies
        run: |
          pip install uv
          uv pip install --system -e ".[dev]"

      - name: Run quality gates
        run: bash scripts/quality-gates.sh --no-fix
```

**Commit and push infrastructure fix:**

```bash
git add .github/workflows/quality-gates.yml
git commit -m "Add GitHub Actions quality gates workflow"
git push
```

### Step 7: Infrastructure Tasks (Phase 0)

**For Phase 0 subtasks (infrastructure only):**

These don't require PRs - just execute the command and document in issue.

#### Example: Create Artifact Registry Python repo

```bash
# Run gcloud command
gcloud artifacts repositories create unified-libraries \
    --repository-format=python \
    --location=asia-northeast1 \
    --description="Unified libraries Python packages" \
    --project=test-project

# Verify
gcloud artifacts repositories describe unified-libraries \
    --location=asia-northeast1

# Comment on issue
gh issue comment $ISSUE_NUMBER --repo "IggyIkenna/unified-trading-services" --body \
    "✅ Completed: Created Artifact Registry Python repository

\`\`\`bash
gcloud artifacts repositories describe unified-libraries --location=asia-northeast1
\`\`\`

Repository URL: https://console.cloud.google.com/artifacts/docker/test-project/asia-northeast1/unified-libraries"

# Close issue
gh issue close $ISSUE_NUMBER --repo "IggyIkenna/unified-trading-services"
```

## Success Criteria

- ✅ Subtask requirements met (per epic breakdown)
- ✅ All specified files created/modified
- ✅ Quality gates pass locally
- ✅ PR created with issue number
- ✅ PR passes GitHub Actions quality gates
- ✅ Tests added/updated and passing
- ✅ Auto-merge enabled (PR will merge when checks pass)
- ✅ Issue will be auto-closed when PR merges
- ✅ uv.lock included in PR if dependencies changed

## Example: Full Workflow

```bash
# Context
REPO_NAME="unified-trading-library"
ISSUE_NUMBER="3"

# Step 1: Get issue
cd /Users/ikennaigboaka/Documents/repos/unified-trading-system-repos/unified-trading-library
gh issue view 3 --repo "IggyIkenna/unified-trading-library"

# Read epic breakdown
grep -A 50 "Subtask 1.2.1:" \
    ../unified-trading-codex/11-project-management/epic-breakdowns/epic-unified-libraries-refactor.md

# Step 2: Understand context
# → Phase 1 (Events Interface)
# → New library repo (create structure)
# → Priority: P0-critical

# Step 3: Implement (create repo structure)
mkdir -p unified_trading_library.events/ tests/unit tests/integration scripts
cat > pyproject.toml <<'EOF'
[project]
name = "unified-trading-library"
version = "0.1.0"
...
EOF

cat > README.md <<'EOF'
# unified-trading-library
...
EOF

cp ../unified-trading-services/scripts/quality-gates.sh ./scripts/
cp ../unified-trading-services/scripts/quickmerge.sh ./scripts/
chmod +x scripts/*.sh

cat > unified_trading_library.events/__init__.py <<'EOF'
"""unified-trading-library - Observability + Coordination events."""
__version__ = "0.1.0"
EOF

cat > tests/unit/test_version.py <<'EOF'
from unified_trading_library.events import __version__

def test_version():
    assert __version__ == "0.1.0"
EOF

uv lock

# Step 4: Run quality gates
bash scripts/quality-gates.sh --no-fix

# Step 5: Submit PR
bash scripts/quickmerge.sh \
    "Complete subtask #3: Create unified-trading-library repo structure

- Added pyproject.toml with Python 3.13, ruff==0.15.0
- Added README.md with usage docs
- Added quality-gates.sh and quickmerge.sh scripts
- Added initial __init__.py and version test
- Created directory structure (src/, tests/, scripts/)

Closes #3" \
    --files "pyproject.toml README.md unified_trading_library.events/__init__.py tests/unit/test_version.py scripts/quality-gates.sh scripts/quickmerge.sh uv.lock"

# Step 6: Monitor PR
PR_NUM=$(gh pr list --head "$(git branch --show-current)" --json number --jq '.[0].number')
gh pr checks $PR_NUM --watch

# Done! PR will auto-merge when checks pass.
```

## Notes for Agent

- **Read epic breakdown first**: Every subtask has detailed specs
- **Follow codex standards**: Quality gates enforce this automatically
- **Test thoroughly**: Minimum 35% coverage to pass gates
- **Infrastructure consistency**: Local = GitHub Actions = Cloud Build
- **Don't skip tests**: Fix root cause, never skip
- **Use quickmerge**: Always use quickmerge (never manual git push)
- **Include uv.lock**: If dependencies changed, include in PR
- **Auto-merge**: Let PRs auto-merge (don't merge manually)
- **Cloud-agnostic**: Only unified-trading-services touches cloud providers

## Related Documentation

### Core Documentation (READ FIRST)

- **Epic overview:** `@unified-trading-codex/11-project-management/epics/unified-libraries-refactor-epic.md`
- **Epic breakdown:** `@unified-trading-codex/11-project-management/epic-breakdowns/epic-unified-libraries-refactor.md`
- **Infrastructure updates:** `@~/.cursor/plans/infrastructure-updates-for-library-refactor.md`

### Coding Standards

- **Coding standards:** `@unified-trading-codex/06-coding-standards/README.md`
- **Quality gates:** `@unified-trading-codex/06-coding-standards/quality-gates.md`
- **Testing standards:** `@unified-trading-codex/06-coding-standards/testing.md`
- **Git workflow:** `@unified-trading-codex/.cursor/rules/git-workflow.mdc`
- **Dependency management:** `@unified-trading-codex/06-coding-standards/dependency-management.md`

### Architecture

- **Batch-live symmetry:** `@unified-trading-codex/04-architecture/batch-live-symmetry.md`
- **Cloud-agnostic migration:** `@unified-trading-codex/05-infrastructure/cloud-agnostic-migration.md`
