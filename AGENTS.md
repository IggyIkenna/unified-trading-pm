# AGENTS.md

## Setup

```bash
uv sync --extra dev
source .venv/bin/activate
```

## Quality Gates

```bash
bash scripts/quality-gates.sh
```

## Key Entry Points

- `scripts/` — workspace management scripts
- `scripts/quickmerge.sh` — push changes (use this, NOT `git push` directly)
- `scripts/repo-management/run-version-alignment.sh` — 4-step alignment pipeline
- `scripts/repo-management/run-all-setup.sh` — runs `setup.sh` in topological order
- `scripts/repo-management/create-staging-branches.sh` — bootstrap staging branches
- `plans/active/` — active plan files (`.plan.md`)
- `plans/active/INDEX.md` — canonical plan registry
- `cursor-rules/` — canonical cursor rules (symlinked to `.cursor/rules/`)
- `workspace-manifest.json` — SSOT for all 59 repos (types, deps, merge order)

## Notes

- Workspace PM repo — tracks plans, scripts, cursor rules, and workspace manifest
- NOT a runnable service; the Python package wraps `scripts/` for importability
- To push changes: `bash scripts/quickmerge.sh "your message"` — NOT `git push`
- `quickmerge.sh` supports `--to-staging` flag for breaking changes
- Staging lock: set when `staging_status.locked=true` in manifest (SIT running)
- Three-tier branch model: `feat/*` → QG only; `staging` → SIT; `main` → stable
- Plans directory has 26b+ active plans as of 2026-03-06
- `[tool.setuptools.packages.find] include = []` in pyproject.toml — prevents multi-package discovery error
