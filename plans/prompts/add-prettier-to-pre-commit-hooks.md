# Task: Add Prettier to All Pre-Commit Hooks

**Plan location:** `unified-trading-pm/plans/ai/` **Codex reference:**
`unified-trading-/codex/06-coding-standards/formatting-standards.md`

---

## Context

Prettier formats TypeScript, JSON, and Markdown files automatically on every `git commit` via the pre-commit/prek hook.
It is already present in some repos (`instruments-service` is the pilot). This task rolls it out to all remaining repos.

**Prettier version in use:** `3.6.2` (verified via `prettier --version` on the workspace machine).

**SSOT for the Prettier block** (copy verbatim into every target repo):

```yaml
# Prettier - TypeScript/JSON/Markdown formatter
- repo: https://github.com/pre-commit/mirrors-prettier
  rev: v4.0.0-alpha.8
  hooks:
    - id: prettier
      name: Format with Prettier
      types_or: [ts, tsx, javascript, jsx, json, markdown, yaml]
      additional_dependencies:
        - prettier@3.6.2
```

Place this block **after the ruff block and before the basic file checks block** in each `.pre-commit-config.yaml`. See
`instruments-service/.pre-commit-config.yaml` as the reference.

---

## Repos Already Done (skip these)

- `batch-audit-ui`
- `client-reporting-ui`
- `instruments-service` ← pilot
- `logs-dashboard-ui`
- `onboarding-ui`
- `trading-analytics-ui`
- `unified-trading-codex`

---

## Repos Requiring the Change (29 repos)

| #   | Repo                                |
| --- | ----------------------------------- |
| 1   | `execution-algo-library`            |
| 2   | `execution-service`                 |
| 3   | `execution-services`                |
| 4   | `features-calendar-service`         |
| 5   | `features-delta-one-service`        |
| 6   | `features-onchain-service`          |
| 7   | `features-volatility-service`       |
| 8   | `live-health-monitor-ui`            |
| 9   | `market-data-processing-service`    |
| 10  | `market-tick-data-handler`          |
| 11  | `market-tick-data-service`          |
| 12  | `matching-engine-library`           |
| 13  | `ml-inference-service`              |
| 14  | `ml-training-service`               |
| 15  | `position-balance-monitor-service`  |
| 16  | `risk-and-exposure-service`         |
| 17  | `settlement-ui`                     |
| 18  | `strategy-service`                  |
| 19  | `unified-cloud-services`            |
| 20  | `unified-config-interface`          |
| 21  | `unified-domain-client`             |
| 22  | `unified-domain-services`           |
| 23  | `unified-trading-library`           |
| 24  | `unified-market-interface`          |
| 25  | `unified-ml-interface`              |
| 26  | `unified-order-interface`           |
| 27  | `unified-trade-execution-interface` |
| 28  | `unified-trading-deployment-v2`     |
| 29  | `deployment-service`                |
| 30  | `unified-trading-services`          |

---

## Agent Instructions

Follow all workspace cursor rules in .cursorrules. See no-summary-docs.mdc for documentation rules; plans only in
unified-trading-pm or unified-trading-pm/plans/ai/ uv not pip, basedpyright not pyright, quickmerge not git push. Delete
deprecated code; no parallel code paths — see delete-deprecated.mdc. Search unified libraries before implementing
anything new.

### Step 1 — Read the reference file

Read `instruments-service/.pre-commit-config.yaml` to see the canonical result before making any changes.

### Step 2 — Process each repo

For each repo in the list above:

1. Read `<repo>/.pre-commit-config.yaml`.
2. **Skip** if it already contains `mirrors-prettier` (idempotent guard).
3. Locate the insertion point:
   - **If a ruff block exists:** insert the Prettier block immediately after the closing line of the ruff block (before
     any `# Basic file checks` or `pre-commit-hooks` block).
   - **If no ruff block exists (UI-only repos):** insert the Prettier block as the first `repos:` entry (after any
     comments).
4. Insert the SSOT Prettier block verbatim (from the Context section above).
5. Do **not** modify any other part of the file.

### Step 3 — Parallelise

Launch up to 4 parallel sub-agents, each covering a non-overlapping slice of the repo list. Suggested split:

- Agent A: repos 1–8
- Agent B: repos 9–16
- Agent C: repos 17–23
- Agent D: repos 24–30

Each sub-agent edits files directly (StrReplace tool). No commits — the human runs `quickmerge.sh` after review.

### Step 4 — Verify

After all agents complete, run:

```bash
WORKSPACE="/data/Upwork/On Going/Ikenna/unified-trading-system-repos"
for f in "$WORKSPACE"/*/".pre-commit-config.yaml"; do
  repo=$(basename "$(dirname "$f")")
  if grep -q "prettier" "$f" 2>/dev/null; then
    echo "OK:      $repo"
  else
    echo "MISSING: $repo"
  fi
done
```

Expected output: every repo shows `OK`.

### Step 5 — Do NOT commit

Do not run `quickmerge.sh`. The human will review the diffs and commit when ready.

---

## Notes

- `additional_dependencies: [prettier@3.6.2]` installs an isolated copy into the pre-commit cache on first run. It does
  **not** rely on any globally installed Prettier, making it safe and reproducible across all developer machines and CI
  environments.
- The hook only fires on `git commit` (local dev). GitHub Actions and Cloud Build quality gates do not invoke
  prek/pre-commit, so there is zero CI impact.
- If a repo has a `.prettierrc.json` already, the hook picks it up automatically — no extra config needed.
- UI repos (`*-ui`) that already have a Prettier block may have a different `types_or` list or no
  `additional_dependencies` pin. Do **not** overwrite those — they are already done and may have intentional
  differences.
