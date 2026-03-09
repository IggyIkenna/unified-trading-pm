# Workspace SSOT templates

Canonical templates for files that should be consistent across all 56 repos (Python services, Python libraries,
React/TypeScript UIs).

## Files

| Template                | Copy to repo as | Purpose                                                                 |
| ----------------------- | --------------- | ----------------------------------------------------------------------- |
| `.gitignore.central`    | `.gitignore`    | Single gitignore for Python + Node + security; never commit credentials |
| `.cursorignore.central` | `.cursorignore` | Keep Cursor from indexing venvs, node_modules, build, data              |

## Usage

### One-time sync to a repo

```bash
# From repo root (e.g. instruments-service)
PM="path/to/unified-trading-pm"
cp "$PM/scripts/templates/.gitignore.central" .gitignore
cp "$PM/scripts/templates/.cursorignore.central" .cursorignore
```

### Repo-specific additions

Append repo-specific patterns **after** the copied content (e.g. `coverage.xml`, `logs/`, or Terraform block). Do not
remove security or credential patterns.

**CSV / data fixtures:** The central template ignores `*.csv` and other data/doc types (xlsx, ppt, doc, pdf, parquet,
tsv, etc.). If a repo commits small CSV fixtures under `tests/fixtures/`, add after the central content:

```gitignore
!tests/fixtures/*.csv
```

### Security (quality gates)

- **DO** use `*credentials*.json` in `.gitignore` (blocks credential JSON).
- **NEVER** use `!central-element-*.json` or whitelist any credential pattern.
- Tests must use `test-project`, not `central-element-323112`.

See: `.cursor/rules/quality-gates/quality-gates-audit-factors.mdc`

## Sync all repos

From workspace root:

```bash
python3 unified-trading-pm/scripts/sync-gitignore-cursorignore.py
```

This writes `.gitignore` and `.cursorignore` at each **repo root** only. Subdirectory ignore files (e.g.
`ui/.gitignore`, `frontend/.gitignore`) are left unchanged. Repo-specific exceptions (e.g. `!tests/fixtures/*.csv` for
unified-trading-library, `!.env.example` and Terraform for unified-trading-deployment-v3) are applied automatically.

Each repo’s `.gitignore` ends with a **preserved block**:
`# --- Repo-specific exceptions (add below; sync preserves this section) ---`. Anything you add under that line (e.g.
`!some/path/*.csv`) is kept on the next sync; the script only overwrites content above that block.

## Propagation (manual alternative)

To roll out to all repos, use a script that copies from `unified-trading-pm/scripts/templates/` into each repo root,
then commit with:

```bash
# Human (full QG including tests + act)
bash scripts/quickmerge.sh "chore: sync .gitignore and .cursorignore from PM SSOT"

# Agent/automated rollout script (skip tests + act; tests ran in Pass 1 QG)
bash scripts/quickmerge.sh "chore: sync .gitignore and .cursorignore from PM SSOT" --agent
```

**Two-pass model for rollout scripts:** run `bash scripts/quality-gates.sh` in each repo first (Pass 1 — full
validation), then call `quickmerge --agent` (Pass 2 — lint/format/typecheck/codex verify only). This avoids re-running
slow test suites in quickmerge when they already passed.

Per-repo overrides (e.g. Terraform, `data/`) can be uncommented or appended in each repo after sync.
