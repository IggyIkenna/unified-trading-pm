---
doc_type: plan
title: CeFi instrument_type casing residual — re-count fresh, then apply
summary: >-
  Operator-ruled 2026-08-16 (na-eligibility-audit follow-up Q&A round 3) — re-verify the
  2,982-row instrument_type casing residual figure from cefi_consolidated_closeout_2026_07_18.md
  line 523 live before applying the canonicalization fix, given how much has landed on this
  branch since that figure was measured.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, canonicalization, casing]
related:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-16"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 1
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A round 3, 2026-08-16"
locked_by:
context_scope: [/plans/active/cefi_consolidated_closeout_2026_07_18.md]
locked_since:
context_scope:
  [
    /plans/active/cefi_consolidated_closeout_2026_07_18.md,
    instruments-service/scripts/canonicalize_cefi_instrument_type_legacy_lowercase_2026_07_16.py,
  ]
resolved_by:
---

# CeFi instrument_type casing residual — re-count fresh, then apply

## Todos

- [ ] [DATA] P2. Re-count the instrument_type casing residual live against the current catalogue (was 2,982
      non-canonical rows as of `cefi_consolidated_closeout_2026_07_18.md` line 523) — do not trust the cited figure
      without a fresh measurement. If the count still shows a real residual, execute the `--apply` casing fix.
      (repo: instruments-service)

## Progress Log

- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries)
- **2026-08-16 (na-eligibility-audit follow-up Q&A round 3, operator ruling)**: extracted from
  `cefi_consolidated_closeout_2026_07_18.md`.
