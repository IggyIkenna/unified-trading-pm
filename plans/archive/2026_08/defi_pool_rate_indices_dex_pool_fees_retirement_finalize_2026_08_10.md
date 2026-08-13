---
doc_type: plan
title: >-
  Finalize — reconcile `defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md`'s evidence back into its source
  docs and archive
summary: >-
  Gated finalize companion (operator ruling 2026-07-24) for the POOL/rate_indices/dex_pool_fees retirement plan. This is
  a batch-style extraction from `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s Todos section —
  reconciles evidence back into that doc's corresponding checkbox (and `defi_track01_...`'s R3 tracking, which this work
  also gates on), checks whether either source doc is now fully done, and archives this plan + its parent once complete.
status: archived
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [defi, finalize, archival, retirement]
related:
  [
    /plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.15
estimate_calibrated_ai_days: 0.12
assigned_role: data_engineering
effort: low
drift_direction: advance-code
depends_on: [defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_2026_08_10.md,
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source: >-
  Required companion per task_template.md §4 "Every AO-dispatched plan needs a gated finalize plan" — authored alongside
  the retirement plan in the same session. `status: active` (not draft — `gate_on_depends: true` already holds this
  plan's tasks until the retirement plan's are done, so a matching draft status is redundant per task_template.md §4);
  the retirement plan itself stays `status: draft` until the rebuild VM reaches terminal SUCCESS.
---

# Finalize the POOL/rate_indices/dex_pool_fees retirement plan

> **ARCHIVED 2026-08-13** — all 2 todos done: re-verified the retirement plan's evidence live, reconciled it into both
> source docs, and ran the 6-step archival ritual on the retirement plan + self-archived this finalize plan. Archived by
> slot 14 (data_engineering).

## Todos

- [x] ✅ [REVIEW] P1. **DONE 2026-08-13.** Re-verified live (not trusted from the plan's own copy): all 4 cited commits
      confirmed on `origin/live-defi-rollout` (`market-tick-data-service@5e456d0d`/`@bf712ddb`/`@9f5868e5`,
      `instruments-service@4bb2164e`); the cited `coverage.json` (`generated_at=2026-08-12T22:00:38Z`) confirmed still
      the latest rollup (no fresher regen since, checked via a fresh bucket listing); and the 3 retirement counts
      independently re-derived RIGHT NOW via each retirement script's own read-only dry-run census against the live,
      current 158,267,760-row consolidated index (bounded via `run-bounded-analysis.sh`, not a full unbounded load): **0
      legacy POOL keys**, **0 legacy `rate_indices` keys**, **0 remaining captured `dex_pool_fees` rows** — all match
      the plan's claims. Updated both source docs: (1) `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s
      `## Todos` retirement item flipped `[x]` with the re-verified commits/counts; (2)
      `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R3 section got an appended closing note (checkbox left
      `[~]` — R3 itself, the per-instrument historical migration, is still genuinely open; this only closes the
      retirement plan's aftermath of R3's rebuild step). **Archival-candidate check**: neither source doc reaches zero
      remaining open todos — `defi_distinct_values...` has 2 open (`spot_pair` cross-check, `<blank>` panel fix);
      `defi_track01...` has 4 open (R3 residual C2-C12 walk, R4 coverage, the TVL-fallback item, R3-run itself) —
      confirmed via `grep -c '^\s*- \[ \]'`, not assumed. Neither flagged as an archival candidate.
- [x] ✅ [DOC] P2. **DONE 2026-08-13.** Ran the standard 6-step archival ritual on the retirement plan (all 9 todos
      done, unlocked): `git mv` → `plans/archive/2026_08/`, archived-banner added, `status: archived`, corpus-wide
      referrer paths repointed (6 docs citing the active path → archive path; verified zero remaining active-path refs),
      no codex/CLAUDE contract changes needed (all data findings already tracked on their own issue docs). Then
      self-archived this finalize plan the same way (both plans now `status: archived` under `plans/archive/2026_08/`).
      INDEX regenerated.
