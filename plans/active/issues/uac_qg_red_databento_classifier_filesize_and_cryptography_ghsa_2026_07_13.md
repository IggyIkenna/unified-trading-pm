---
doc_type: issue
title:
  unified-api-contracts QG RED — databento_classifier.py exceeds 900 lines + cryptography 47.0.0 GHSA-537c-gmf6-5ccf
summary: >
  bash scripts/quality-gates.sh --no-fix fails repo-wide on unified-api-contracts (STEP "Files exceed 900 lines" +
  "pip-audit vulnerabilities" + "Codex compliance FAILED: 3 violations, max allowed: 2") because (a)
  unified_api_contracts/external/databento/databento_classifier.py is 906 lines, and (b) cryptography 47.0.0 (pinned in
  this repo's uv.lock) carries GHSA-537c-gmf6-5ccf. Both verified pre-existing at HEAD, unrelated to my task (a
  registry-only change to data_type_capability.py / SOURCE_PRIORITY / pipeline_mode.py for
  vol_dvol_backtestable_engines_2026_07_13.md Todo 1) — I never touched either file/dependency. The cryptography CVE was
  already fixed in market-tick-data-service (fleet_hygiene_crypto_ghsa_mtds_baseline_2026_07_13.md) but that plan's
  `repos:` scope did not include unified-api-contracts, so this repo was missed.
status: open
nature: notes
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-api-contracts]
scope: [engineer]
tags: [qg-red, file-size, repo-blocker, codex-compliance, dependency-hygiene, cve]
related:
  [
    plans/active/vol_dvol_backtestable_engines_2026_07_13.md,
    plans/active/fleet_hygiene_crypto_ghsa_mtds_baseline_2026_07_13.md,
  ]
created: 2026-07-13
parent_epic: infrastructure_master
priority: P1
source:
  vol_dvol_backtestable_engines-001 dispatch (Todo 1, "register volatility_index data_type capability"), slot 9,
  2026-07-13
assigned_vm: planning
execution_scope: orchestrator-agent
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-13
locked_by:
resolved_by:
---

# unified-api-contracts QG RED — file-size + cryptography CVE

## What I found

`bash scripts/quality-gates.sh --no-fix` on `unified-api-contracts` at HEAD (`061d8faca`-era, before my own uncommitted
registry changes) fails with:

```
❌ Files exceed 900 lines:
  ./unified_api_contracts/external/databento/databento_classifier.py: 906 L
❌ pip-audit vulnerabilities
  cryptography 47.0.0: GHSA-537c-gmf6-5ccf — pyca/cryptography's wheels include a statically linked copy of OpenSSL...
❌ Codex compliance FAILED: 3 violations (max allowed: 2)
```

Verified both are genuinely pre-existing, not caused by my commit — my only changes are to `data_type_capability.py` /
`_source_priority_data.py` / `availability_semantics.py` / `pipeline_mode.py` + 2 test files (registering
`(cefi, volatility_index)` per `vol_dvol_backtestable_engines_2026_07_13.md` Todo 1):

```
$ git diff --stat HEAD -- unified_api_contracts/external/databento/databento_classifier.py
(empty — I never touched this file)
$ git show HEAD:unified_api_contracts/external/databento/databento_classifier.py | wc -l
906
$ git diff --stat HEAD -- pyproject.toml uv.lock
(empty — I never touched dependency files)
$ grep cryptography uv.lock
name = "cryptography" ... cryptography-47.0.0 ...
```

The cryptography GHSA was already root-caused + fixed elsewhere this session
(`fleet_hygiene_crypto_ghsa_mtds_baseline_2026_07_13.md`, scoped to `market-tick-data-service` + `unified-trading-pm`) —
that plan's `repos:` list did not include `unified-api-contracts`, so the same vulnerable `cryptography` floor is still
pinned here. The 3rd "Codex compliance" violation (tally says 3, only 2 explicit ❌ lines print) was not further
decomposed — out of scope to chase here; likely the same ratchet counting the file-size and pip-audit findings plus one
additional accounting line not surfaced with a ❌ prefix in this run's output.

## Why it matters

- Blocks EVERY subsequent commit to `unified-api-contracts` from any slot until fixed — the repo-wide green-tree rule
  means no one can ship via `quickmerge --agent` while `quality-gates.sh` is red, regardless of how unrelated their
  change is.
- I hit this while trying to ship the `(cefi, volatility_index)` capability registration
  (`vol_dvol_backtestable_engines_2026_07_13.md` Todo 1) — that work is DONE and verified via a full targeted-test sweep
  (718 tests green: `test_source_mode_capability.py` / `test_source_priority.py` /
  `test_source_priority_pipeline_mode.py` / `test_pipeline_mode.py` / `test_availability_semantics.py` /
  `test_validity_matrix_completeness.py` + broader keyword sweep) but cannot land until this repo-wide gate clears.

## Recommended decision

Two independent fixes, same pattern already proven elsewhere in this session:

- **(a) cryptography GHSA bump** — mirror the exact fix already shipped for `market-tick-data-service`
  (`fix(deps): bump cryptography floor off GHSA-537c-gmf6-5ccf`): bump the `cryptography` floor in
  `unified-api-contracts/pyproject.toml`, `uv lock`, re-run QG. Low-risk, same pattern proven minutes earlier in this
  session on a sibling repo.
- **(b) databento_classifier.py file-size split** — extract a cohesive helper (the classifier's split should follow
  whatever natural seam exists, e.g. rule tables vs. dispatch logic) rather than an arbitrary line-count trim. Needs
  domain understanding of what's safe to extract — did not attempt myself, out of my task's scope per findings-triage.

## Todos

- [ ] [BACKEND] P1. Bump the `cryptography` floor in `unified-api-contracts/pyproject.toml` off GHSA-537c-gmf6-5ccf
      (mirror `market-tick-data-service`'s already-shipped fix this session), `uv lock`, verify `pip-audit` clears.
      (repo: unified-api-contracts)
- [ ] [REFACTOR] P1. Split `unified_api_contracts/external/databento/databento_classifier.py` (906 lines) back under the
      900-line ceiling — extract a cohesive helper module rather than an arbitrary line-count trim. Verify
      `bash scripts/quality-gates.sh` is green afterward. (repo: unified-api-contracts)
