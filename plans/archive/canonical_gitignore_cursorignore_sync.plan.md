---
doc_type: plan
title: Canonical .gitignore / .cursorignore Sync
summary: 'Update the canonical .gitignore and .cursorignore files in unified-trading-pm, then

  propagate them to all 55 git repos in the workspace. The canonical files are the SSOT —

  all repos must align to them. Repo-specific exception sections are preserved per-repo.

  A durable sync script is created so future canonical changes propagate with one command.'
status: complete
nature: record
asset_group: [cross-cutting]
stage: [meta]
repos: [deployment-ui, execution-service, instruments-service, market-tick-data-service, strategy-service, unified-trading-library]
scope: [engineer, admin]
tags: []
related: []
created: '2026-03-09'
archived: '2026-03-09'
archiveReason: 'Partially implemented. Sync script exists: scripts/workspace/sync-gitignore-cursorignore.py

  (Python, not shell). Central templates exist: scripts/templates/.gitignore.central and

  .cursorignore.central. *.feather was NOT added to templates — only *.parquet present.

  Repo-specific exceptions (data/sample, sample_data, data/sample_features) not in script.

  Dry-run/apply flags, old-style upgrade, untrack-ignored-files, and full propagate not done.

  '
todos:
- {id: gi-update-canonical, content: "Update unified-trading-pm/.gitignore and .cursorignore with the only canonical change:\n  .gitignore    — add *.feather after *.parquet in the data/doc file types section.\n  .cursorignore — add **/*.feather after **/*.parquet.\nNo global test-fixture exception is added — each repo manages its own exceptions in\nits repo-specific section (see gi-audit-test-fixture-exceptions).\nCopy both updated files into scripts/templates/ as the authoritative template source.\n", status: pending}
- {id: gi-create-sync-script, content: "Create unified-trading-pm/scripts/sync_gitignore.sh.\nBehaviour:\n  --dry-run (default): print a per-repo diff of what would change, do not write.\n  --apply: write changes to each repo.\nLogic per repo:\n  1. If repo has canonical-format .gitignore (contains \"Central .gitignore\"):\n     - Extract the repo-specific section (lines before the \"# ===\" marker).\n     - Replace the canonical body with the updated template from scripts/templates/.\n     - Re-inject the repo-specific section at the top, unchanged.\n  2. If repo has old-style .gitignore (no canonical header): flag as OLD-STYLE,\n     skip — handled by gi-upgrade-old-style.\n  3. If repo has no .gitignore: flag as MISSING — handled by gi-create-missing.\nSame logic applies to .cursorignore.\nSafety rules baked in:\n  - Never silently drops lines from the repo-specific section.\n  - Prints a warning and skips if repo-specific section contains a pattern that\n    conflicts with a new canonical\
    \ rule — do not auto-resolve conflicts.\n  - Dry-run is the default; --apply must be passed explicitly.\n  - Script is idempotent: running twice produces no further changes.\nOutput: scripts/sync_gitignore_report.txt (written on every run).\n", status: pending}
- {id: gi-dry-run-audit, content: "Run: bash unified-trading-pm/scripts/sync_gitignore.sh --dry-run\nReview the report. Confirm:\n  - 49 canonical repos show only the expected diff (*.feather line added).\n  - 4 OLD-STYLE repos are flagged but not modified.\n  - 2 MISSING repos are flagged but not modified.\n  - No repo-specific exception lines appear as removed in any diff.\nDocument findings in this plan under \"Dry Run Results\" before proceeding.\n", status: pending}
- {id: gi-upgrade-old-style, content: "Upgrade the 4 old-style repos to the canonical format. For each:\n  features-multi-timeframe-service — no unique patterns found; full canonical replace.\n  instruments-service              — no unique patterns found; full canonical replace.\n  strategy-service                 — no unique patterns found; full canonical replace.\n  unified-trading-library          — no unique patterns found; full canonical replace.\nFor each repo, write the canonical template (from scripts/templates/) as the new\n.gitignore and .cursorignore, with an empty repo-specific section at the top.\nBefore replacing, verify the old file has no lines not already covered by the\ncanonical template. If anything unique is found, move it to the repo-specific\nsection instead of discarding it.\n", status: pending}
- {id: gi-create-missing, content: "Create .gitignore and .cursorignore from the canonical template for:\n  deployment-ui\n  strategy-validation-service\nUse scripts/templates/ as source. Repo-specific section is left empty.\n", status: pending}
- {id: gi-audit-test-fixture-exceptions, content: "Audit all repos that commit test fixture data files (CSV, feather, parquet) and\nensure each has the correct repo-specific exception in its .gitignore so those\nfiles are not accidentally dropped by gi-untrack-ignored-files.\n\nKnown repos and their fixture paths (confirmed by audit 2026-03-06):\n\n  features-delta-one-service  — data/mock/ (ALREADY HAS !data/mock/ exception)\n                              — data/sample_features/ (MISSING exception — add it)\n  features-calendar-service   — data/sample/ (MISSING exception — add it)\n  market-tick-data-service    — sample_data/ (MISSING exception — add it)\n  features-onchain-service    — features_onchain_service/examples/ (in source tree,\n                                not under data/, unaffected — no exception needed)\n  execution-service           — execution_service/data/ (ALREADY HAS exception,\n                                Python source package not a data folder)\n\nFor each MISSING\
    \ case, add the negation to the repo-specific section of that\nrepo's .gitignore ONLY (do not touch the canonical template).\n\nConvention going forward: repos that need to commit test fixture data files add\na negation in their own repo-specific section. The canonical template stays clean.\n", status: pending}
- {id: gi-apply-sync, content: "Run: bash unified-trading-pm/scripts/sync_gitignore.sh --apply\nThis applies the canonical update (*.feather addition) to all 49 canonical repos.\nAfter apply, spot-check 5 repos to verify:\n  1. *.feather is present in the data/doc file types section.\n  2. Repo-specific exceptions are intact (execution-service, features-delta-one-service,\n     market-tick-data-service, features-calendar-service, unified-trading-pm).\n  3. No unintended lines were added or removed.\n", status: pending}
- {id: gi-untrack-ignored-files, content: "For every repo that had its .gitignore updated (all 55 git repos), find and remove\nany files currently tracked by git that should now be ignored under the new rules.\nGit does not automatically stop tracking a file when a new .gitignore rule matches\nit — it must be explicitly removed from the index.\n\nDetection command (run per repo, does not delete files from disk):\n  git ls-files --ignored --exclude-standard\n\nIf output is non-empty, inspect the list first, then remove from index only:\n  git rm -r --cached <files>\n\nKey patterns likely to surface tracked-but-should-be-ignored files:\n  *.feather   — new rule; any previously committed feather files\n  data/       — old-style repos that lacked this rule (instruments-service has 800+\n                timestamp-named generated CSVs in data/samples/ that must be untracked)\n  *.csv / *.parquet — old-style repos that lacked the file-type section\n\nIMPORTANT safety rules:\n  - --cached flag only,\
    \ never bare git rm — files stay on disk.\n  - Before running git rm --cached, print the list and verify it looks correct.\n  - If a file appears in the ignored list but is a known test fixture (e.g.\n    features-delta-one-service/data/mock/*.csv), the repo-specific exception from\n    gi-audit-test-fixture-exceptions is missing or wrong — stop and fix it first.\n  - Document all findings in this plan under \"Untrack Findings\".\n\nKnown large cleanup expected:\n  instruments-service — ~800+ generated CSVs in data/samples/ should be untracked.\n  instruments-service — corporate_actions_output/ parquets should be untracked.\n", status: pending}
- {id: gi-commit-each-repo, content: "For each modified repo, stage and commit in a single commit:\n  git add .gitignore .cursorignore\n  git rm -r --cached <previously-tracked-ignored-files>  # from gi-untrack-ignored-files\n  bash scripts/quickmerge.sh \"chore: sync canonical .gitignore and remove tracked ignored files\"\nIf a repo had no files to untrack, just commit the gitignore changes.\nCommit unified-trading-pm last (canonical source + sync script + plan update).\n", status: pending}
isProject: false
---

# Canonical .gitignore / .cursorignore Sync

**Day:** 0 (pre-Phase 1 hygiene, run alongside phase0_standards_enforcement) **Scope:** All 55 git repos in workspace
**Blocks:** Nothing directly, but uncommitted test fixtures cause flaky tests in any phase **Owner:** Person A

---

## Motivation

1. `*.feather` files are not currently ignored — feather data files are large and binary and should not be committed.
2. Several repos commit test fixture data files (CSV, parquet, feather) but are missing the repo-specific `.gitignore`
   exceptions that protect them during syncs.
3. A durable sync script does not exist — canonical changes have been propagated manually.

**Decision: per-repo exceptions, not a global path.** An audit of all repos (2026-03-06) found that each repo uses a
different folder name for committed test data: `data/mock/`, `data/sample/`, `data/sample_features/`, `sample_data/`. No
repo uses a shared `data/test_samples/` path. Forcing a migration to a single canonical path would require changing test
code across many repos — high churn, real breakage risk. Instead: the canonical template stays clean; each repo declares
its own exception.

---

## Current State

| Category         | Count | Repos                                                                                                    |
| ---------------- | ----- | -------------------------------------------------------------------------------------------------------- |
| Canonical format | 49    | All others (have `# Central .gitignore` header + repo-specific section)                                  |
| Old-style        | 4     | `features-multi-timeframe-service`, `instruments-service`, `strategy-service`, `unified-trading-library` |
| Missing files    | 2     | `deployment-ui`, `strategy-validation-service`                                                           |
| Skipped (no git) | 0     | `execution_service` deleted                                                                              |

### Known Repo-Specific Exceptions

| Repo                         | Exception                   | Status  | Reason                                              |
| ---------------------------- | --------------------------- | ------- | --------------------------------------------------- |
| `execution-service`          | `!execution_service/data/`  | EXISTS  | Python source package named `data/` in service tree |
| `features-delta-one-service` | `!data/mock/`               | EXISTS  | Test fixture CSVs (ETHUSDT.csv, SOLUSDT.csv)        |
| `features-delta-one-service` | `!data/sample_features/`    | MISSING | 14 parquet test fixtures                            |
| `features-calendar-service`  | `!data/sample/`             | MISSING | CSV + parquet test fixtures                         |
| `market-tick-data-service`   | `!sample_data/`             | MISSING | 2 CSV test fixtures (coinbase, upbit trade data)    |
| `market-tick-data-service`   | `package-lock.json`         | EXISTS  | Keeps package-lock tracked                          |
| `unified-trading-pm`         | `!github-integration/data/` | EXISTS  | GitHub integration data must be tracked             |

---

## Canonical File Changes

Only one change to the canonical template — `*.feather` added to both files:

### `.gitignore`

```diff
 # --- Common data / document file types ---
 *.csv
 ...
 *.parquet
+*.feather
 *.tsv
```

### `.cursorignore`

```diff
 **/*.parquet
+**/*.feather
 **/*.tsv
```

No global test-fixture exceptions are added. Each repo manages its own exceptions.

---

## Sync Script Design

**Location:** `unified-trading-pm/scripts/sync_gitignore.sh` **Template source:**
`unified-trading-pm/scripts/templates/.gitignore` and `.cursorignore`

```
Usage:
  bash scripts/sync_gitignore.sh --dry-run   # show diffs, no writes (default)
  bash scripts/sync_gitignore.sh --apply     # write changes

Output:
  scripts/sync_gitignore_report.txt          # always written
```

**Algorithm per repo:**

```
for each repo in workspace:
  if .gitignore missing          → MISSING   (log, skip)
  if no canonical header         → OLD-STYLE (log, skip)
  else:
    extract repo-specific section (everything before "# ===" marker)
    new content = repo-specific section + canonical template body
    if new == current            → UNCHANGED (skip)
    else                         → CHANGED: print diff / write file
```

---

## Dry Run Results

_(to be filled in after running `bash scripts/sync_gitignore.sh --dry-run`)_

---

## Untrack Findings

_(to be filled in after running `git ls-files --ignored --exclude-standard` across all repos)_

| Repo | Tracked-but-ignored files found | Action taken |
| ---- | ------------------------------- | ------------ |
|      |                                 |              |

---

## Gate Criteria

- [ ] `*.feather` present in the data/doc section of all 55 repo `.gitignore` files
- [ ] `**/*.feather` present in all 55 `.cursorignore` files
- [ ] All pre-existing repo-specific exceptions intact (see table above)
- [ ] `!data/sample_features/` added to `features-delta-one-service` repo-specific section
- [ ] `!data/sample/` added to `features-calendar-service` repo-specific section
- [ ] `!sample_data/` added to `market-tick-data-service` repo-specific section
- [ ] `git ls-files --ignored --exclude-standard` returns empty in all 55 repos after apply
- [ ] Known test fixture files (data/mock/, data/sample/, sample_data/) do NOT appear in any ignored list
- [ ] `scripts/sync_gitignore.sh --dry-run` exits 0 with "0 repos changed" after apply completes
- [ ] All 55 repos committed with `chore: sync canonical .gitignore and remove tracked ignored files`
