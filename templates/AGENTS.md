# AGENTS.md — {REPO_NAME}

> Per-repo guide for AI agents and developers working in fresh or isolated environments.
> Copy this template to the repo root and fill in repo-specific details.
> See: unified-trading-codex/06-coding-standards/setup-standards.md

## Quick Start

```bash
# Full workspace setup (has all sibling repos):
bash scripts/setup.sh

# Isolated setup (standalone clone, no workspace):
bash scripts/setup.sh --isolated

# Verify environment:
bash scripts/setup.sh --check
```

## Tier & Dependencies

| Field          | Value                   |
| -------------- | ----------------------- |
| Tier           | T{N} ({tier_name})      |
| Package name   | `{package_name}`        |
| Python version | 3.13                    |
| Key deps       | {list_key_dependencies} |

### Workspace Dependencies

<!-- List repos this package depends on (from workspace-manifest.json (SSOT)) -->
<!-- In isolated mode, these are skipped — install from Artifact Registry if needed -->

- `{dep_repo_1}` — {what_it_provides}
- `{dep_repo_2}` — {what_it_provides}

## Key Commands

```bash
# Import smoke test
python -c "import {package_name}"

# Run linting only (fastest feedback)
bash scripts/quickmerge.sh "msg" --lint-only

# Run unit tests only
bash scripts/quickmerge.sh "msg" --unit-only

# Full quality gate
bash scripts/quickmerge.sh "msg" --qg-only

# Full pipeline (the only gate that counts)
bash scripts/quickmerge.sh "msg"
```

## Known Caveats

<!-- Document non-obvious issues that agents or new developers will encounter -->
<!-- setup.sh reads this section and prints it during setup -->

### Tests

- {description_of_known_test_failure_or_quirk}
- {e.g., "alignment tests require unified-internal-contracts to be installed from workspace"}

### Type Checking

- {description_of_known_basedpyright_issues}
- {e.g., "3 pre-existing basedpyright errors in legacy_adapter.py — tracked in #123"}

### Dependencies

- {description_of_dependency_quirks}
- {e.g., "VCR cassette tests require httpx>=0.27 — included in dev deps"}

## Isolation Notes

<!-- What works and what doesn't when this repo is cloned standalone -->

**Works in isolation:**

- {e.g., "Unit tests (tests/unit/)"}
- {e.g., "Import smoke test"}
- {e.g., "Linting and formatting"}

**Requires workspace:**

- {e.g., "Integration tests (tests/integration/) — need sibling repos installed"}
- {e.g., "Cross-repo alignment tests (test_ac_uic_alignment.py)"}

**Requires GCP credentials:**

- {e.g., "E2E tests, Secret Manager access, GCS operations"}

## Architecture Notes

<!-- Brief description of internal architecture for agent context -->

{2-3 sentences about the repo's internal structure, key modules, and patterns}

### Key Files

| Path                             | Purpose                           |
| -------------------------------- | --------------------------------- |
| `{src_dir}/`                     | Main package source               |
| `tests/`                         | Test suite (unit + integration)   |
| `scripts/`                       | Setup, quality gates, quickmerge  |
| `pyproject.toml`                 | Project metadata and dependencies |
| `workspace-manifest.json (SSOT)` | Workspace dependency declarations |

## Troubleshooting

| Symptom                               | Likely Cause                     | Fix                                                              |
| ------------------------------------- | -------------------------------- | ---------------------------------------------------------------- |
| `ModuleNotFoundError: {package_name}` | Package not installed            | `bash scripts/setup.sh`                                          |
| Import fails for workspace dep        | Isolated mode, dep not installed | `uv pip install -e ../dep-repo` or `--isolated` flag             |
| basedpyright timeout                  | Large codebase, slow machine     | `run_timeout 120 basedpyright {src_dir}/`                        |
| Tests fail with credential error      | No GCP credentials configured    | Set `GOOGLE_APPLICATION_CREDENTIALS` or skip with `-m "not e2e"` |
