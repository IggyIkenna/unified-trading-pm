---
doc_type: plan
title: >-
  Retire legacy POOL / rate_indices / dex_pool_fees manifest rows post-rebuild, trigger a fresh honest-coverage rollup,
  and re-check the Distinct Values panel
summary: >-
  Extracted from `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s Todos section — every judgment call
  this work depended on is now resolved (POOL/rate_indices/dex_pool_fees scope confirmed, the retirement pattern already
  proven twice on dex_pools/dex_swaps, the blocking rebuild VM's OOM root-caused and fixed) so the remaining steps are
  bounded, determinable, mechanical. `status: draft` until the rebuild VM (currently
  `canonical-migration-defi-rebuild-20260810-093118` or its latest successor) reaches genuine terminal SUCCESS — flip to
  `active` only then; a draft plan is not ingested, so this avoids an AO worker claiming a todo whose precondition isn't
  met yet.
status: draft
nature: process
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, instruments-service, unified-trading-pm]
scope: [engineer, admin]
tags: [defi, manifest, retirement, pool-casing, rate-indices, dex-pool-fees, honest-coverage, distinct-values]
related:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: data_engineering
effort: medium
drift_direction: advance-code
depends_on: []
context_scope:
  [
    /plans/active/defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /plans/active/issues/defi_rebuild_vm_oom_root_cause_and_relaunch_carveout_2026_08_10.md,
    /codex/02-data/canonical-cutover-register.md,
    /codex/02-data/defi-canonical-naming-ssot.md,
  ]
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
sequential: true
source: >-
  Interactive `/autonomous` session 2026-08-10, operator asked to flip the remaining well-scoped todos to an AO plan
  ("can we flip this to ao plan and tasks since the rest of the todos are clearly known").
---

# Retire legacy POOL / rate_indices / dex_pool_fees rows, refresh honest coverage, re-verify the panel

## Why `status: draft`

Every todo below reads live state before acting and is genuinely mechanical — but the retirement steps (todos 2-4) are
UNSAFE against a still-moving-target manifest: the `canonical-migration-defi-rebuild-*` VM chain has already OOM'd twice
on this exact prefix (see the related OOM issue doc), and a direct-CAS full-index-rewrite retirement racing an
actively-merging consolidator risks retiring an incomplete/stale snapshot. Flip `status: draft` → `active` only once
`canonical-migration-defi-rebuild-20260810-093118` (or whatever superseded it) has reached a genuine terminal
**SUCCESS**, not just any terminal state — todo 1 below re-verifies this itself as its own first action, since a worker
picking this plan up cold should never trust the flip-time state without a fresh check.

## Todos

- [ ] [DATA] P1. **Verify the rebuild VM reached terminal SUCCESS + confirm POOL/rate_indices/dex_pool_fees counts are
      STABLE.** Check
      `gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-defi-rebuild-20260810-093118/run.log`
      (or its latest successor, per `gcloud compute instances list --filter=name~canonical-migration-defi-rebuild` +
      the deployments registry)
      for a clean exit (no `rc=137`/ `Killed`, a `Rebuild complete:` line for the FINAL chunk reaching
      `--end-date 2026-12-31`). Then run 2 live queries ~5min apart against `read_availability_index()` for
      `instrument_type=POOL` (uppercase, `dex_pool_swaps`) and `data_type=rate_indices`/`dex_pool_fees`
      `capture_status=captured` counts — done-when: VM terminal SUCCESS confirmed AND all 3 counts identical across both
      queries (not still growing). If the VM instead failed again, STOP — do not proceed to todo 2; file a fresh issue
      doc citing this plan and the failure evidence, do not blind-retry a 3rd/4th time without new root-cause
      information (RB-INFRA-RELAUNCH's stop clause, `/codex/15-runbooks/incidents/rb_infra_relaunch.md`). (repo:
      market-tick-data-service)
- [ ] [DATA] P1. **Pause the DeFi manifest consolidator cron, retire POOL (uppercase `instrument_type`) legacy
      `captured` rows in `dex_pool_swaps` via the proven reversible `capture_status: captured→attempted_failed`
      pattern.** Mirror `retire_dex_pools_legacy_captured_rows_2026_08_05.py` /
      `retire_dex_swaps_legacy_captured_rows_2026_08_09.py` (both `market-tick-data-service/scripts/one_offs/`). Pause
      `uts-prod-manifest-consolidator-market-data-defi-cron` (`asia-northeast1`) before writing, resume after.
      Done-when: a fresh `read_availability_index()` query shows 0 remaining `captured` rows with
      `instrument_type=POOL`. (repo: market-tick-data-service)
- [ ] [DATA] P1. **Retire `rate_indices` legacy `captured` rows** (fold already GENUINELY 100% COMPLETE 2026-08-07 per
      `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 4 — this is the retirement half only, never
      done). Same reversible pattern + consolidator pause/resume as the prior todo (share the pause window if run
      back-to-back). Done-when: 0 remaining `captured` legacy `rate_indices` rows. (repo: market-tick-data-service)
- [ ] [DATA] P2. **Verify + retire `dex_pool_fees` legacy `captured` rows if any remain** (tiny scope — a prior read
      noted ~21 rows on the axis-census panel before that panel's `attempted_failed` filter fix; the corpus itself was 0
      real objects for its whole lifetime, phantom manifest rows only). Confirm the count live first — if 0, mark this
      todo done-with-nothing-to-retire and move on; if >0, same reversible pattern as above. (repo:
      market-tick-data-service)
- [ ] [DATA] P1. **Resume the consolidator (if not already), trigger a fresh `measure_honest_coverage.py` rollup run**,
      and confirm it completes cleanly (the enumeration-key fix shipped `instruments-service@8b59e8ba2` this session
      must be live in whatever image/VM runs the rollup — verify before trusting output). Launcher:
      `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` or the existing scheduled job, whichever this
      workspace currently uses for on-demand triggers — check the launcher registry rather than guessing. Done-when: a
      new `coverage.json` is written with a timestamp after this todo's retirements. (repo: instruments-service)
- [ ] [DATA] P1. **Re-check the Distinct Values panel post-rollup.** Confirm: `dex_pools`/`dex_swaps`/`rate_indices`/
      `dex_pool_fees` no longer appear as non-canonical `data_type`s; `POOL` (uppercase) no longer appears as a
      non-canonical `instrument_type`; venues drop to the genuinely-unresolved set (ASTER/GMX/HYPERLIQUID/EXTENDED/
      LIGHTER + the 24 composite `VENUE-CHAIN` venues, which are CORRECTLY flagged-but-accepted per this epic's prior
      false-alarm investigation, not a bug); `instrument_types` clean modulo the small genuine `<blank>` gap (~58
      `captured` rows, not the ~5.3M raw count — that count is a KNOWN, separately-tracked panel over-report, see
      `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s Todos). Record the live counts in this plan's
      Progress Log. (repo: unified-trading-pm)
