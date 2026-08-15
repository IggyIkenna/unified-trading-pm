---
doc_type: plan
title: CeFi 586-row margin-marker decompose + 4.5M-file instrument_id backfill
summary: >-
  Operator-ruled 2026-08-15 (na-eligibility-audit follow-up Q&A) — (1) check whether the 2026-07-17 operator decision #4
  already covers the 586 marker-less catalogue rows before force-decomposing them, and (2) proceed with the ~4.5M-file
  corpus-wide parquet CONTENT instrument_id backfill via --apply, re-authorized despite its true scope having grown ~2
  orders of magnitude past the original estimate.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [cefi, canonicalization, instrument_id, backfill]
related: [/plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md]
created: "2026-08-15"
last_updated: "2026-08-15"
parent_epic: cefi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
assigned_role: data_engineering
effort: max
drift_direction: advance-code
depends_on: []
supersedes:
superseded_by:
source: "na-eligibility-audit follow-up Q&A, 2026-08-15"
locked_by:
context_scope:
  [
    /plans/active/issues/cefi_residual_followups_after_honest_done_2026_07_17.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
locked_since:
resolved_by:
---

# CeFi 586-row marker decompose + 4.5M-file instrument_id backfill

## Why this exists

`cefi_residual_followups_after_honest_done_2026_07_17.md` carried two open items the na-eligibility-audit flagged as
canonical-naming/`--apply`-scale questions: the 586 marker-less `VENUE:PERPETUAL:BASE-QUOTE` catalogue rows (blueprint
open-q #19), and the corpus-wide parquet CONTENT instrument_id backfill whose true scope (~4.5M files) is roughly 2
orders of magnitude past its original estimate. Operator ruling 2026-08-15: check decision #4's scope before deciding
the 586-row item; proceed with the 4.5M backfill as originally authorized (scope growth does not require
re-authorization).

## Todos

- [ ] [DATA] P2. Read the 2026-07-17 operator decisions section
      (`cefi_residual_followups_after_honest_done_2026_07_17.md` § "Operator decisions (2026-07-17, AskUserQuestion)",
      decision #4) and determine whether it already authorizes force-decomposing the 586 marker-less
      `VENUE:PERPETUAL:BASE-QUOTE` rows (BITGET-FUTURES 275 / BINANCE-FUTURES 153 / COINBASE-FUTURES 107 /
      BINANCE-DELIVERY 27 / BITFINEX-FUTURES 16 / OKX-SWAP 5 / BYBIT 3) to add the `@LIN`/`@INV` margin marker. If yes:
      execute the decompose. If no: file as a fresh, narrower operator question rather than guessing. (repo:
      instruments-service)
- [ ] [SCRIPT] P1. Execute the corpus-wide parquet CONTENT instrument_id backfill via `--apply` (~4.5M files,
      canonicalizing the 3 non-canonical classes already identified: historical margin-marker undecomposed, non-margin
      venues wrapped-wire, on-chain historical raw-content). Operator re-authorized 2026-08-15 despite the ~100x scope
      growth from the original estimate — proceed under the existing authorization, no new sign-off needed. Given the
      scale, this is a VM-launch-class job — follow the VM-launcher runbook (spot default, progress-checkpointed,
      right-sized). (repo: instruments-service)

## Progress Log

- **2026-08-15 (na-eligibility-audit follow-up, operator ruling)**: extracted from
  `cefi_residual_followups_after_honest_done_2026_07_17.md`. Operator explicitly rejected the "pause for a fresh
  cost/time estimate" recommendation for the 4.5M-file backfill and chose to proceed as originally authorized.
