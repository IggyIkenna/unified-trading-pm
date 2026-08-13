---
doc_type: plan
title: >-
  DeFi Track 0-1 — "Open items recovered from the pre-2026-07-24 historical Progress Log" subsection, extracted +
  archived (line-cap remediation)
summary: >-
  Line-cap remediation extraction from `defi_track01_per_instrument_and_canon_id_2026_07_24.md` (was 1007-1022L, over
  the 1000L hard cap) — moved verbatim, nothing rewritten or summarized. All 4 items in this subsection were already
  `[x]` done as of the extraction; this doc exists purely so the content isn't lost, not because any of it needed
  further work. See the parent doc for a short pointer in its place.
status: complete
nature: process
asset_group: [defi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [defi, canonicalisation, line-cap-remediation, archive, extraction]
related:
  [
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
    /codex/11-project-management/cross-reference-path-convention.md,
  ]
created: "2026-08-13"
last_updated: "2026-08-13"
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  Extracted 2026-08-13 (finalize-reconciliation slot 14) while appending a closing note to
  `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s R3 section per
  `/plans/archive/2026_08/defi_pool_rate_indices_dex_pool_fees_retirement_finalize_2026_08_10.md` todo 1 — the append
  pushed the parent doc from 1007L to 1022L, over the 1000L hard cap (`check_line_caps.sh`, no exceptions). This
  subsection was the parent's own best extraction candidate: fully closed (all 4 items `[x]`), self-contained, and
  already explicitly framed there as "carried forward... rather than archived silently" back when it still had open
  items — now that all 4 are done, silent archival is no longer the concern the parent's own header note warned against.
---

# DeFi Track 0-1 — "Open items recovered" subsection (archived, line-cap remediation)

> Verbatim move from `defi_track01_per_instrument_and_canon_id_2026_07_24.md`'s "### Open items recovered from the
> pre-2026-07-24 historical Progress Log's deferred-work tables" section. Nothing rewritten or summarized.

### Open items recovered from the pre-2026-07-24 historical Progress Log's deferred-work tables

> The chronological Progress Log narrative was moved verbatim to the archive doc (pointer below); these 4 items were
> genuinely still-open (not "done"/duplicate-of-above) as of the last tick and are carried forward here rather than
> archived silently.

- [x] ✅ [DATA] P1. **Ship the `delete_migrated_defi_markers_2026_07_23.py` script — DONE (cited sha `952618d1` was
      stale/pre-rebase; actual shipped sha `market-tick-data-service@a65117eb`, confirmed ancestor of
      `origin/live-defi-rollout`).** The named blocker
      (`mtds_deployment_env_monkeypatch_leak_blocks_quickmerge_2026_07_23.md`) was worked around via the serial-pytest
      mitigation (`bc5d1490`, `PYTEST_WORKERS=1` — reduces but does not eliminate exposure per that issue doc's reopened
      findings) and the script landed. **Remaining: only the `--apply` run itself, [OPERATOR]-tagged at the parent plan
      (line 708) — prod-bucket delete, human-only hard stop, not an agent action.** The 12-liquidations-bundle question
      is ANSWERED (writer half): the daily-cron timestamp-glued-empty-marker defect across 6 handlers that produced them
      is root-caused + fixed this session (`market-tick-data-service@f2e3ad41`) — no FUTURE liquidations glued rows will
      be written. The 12 EXISTING glued rows already in the manifest from before the fix still need a targeted
      re-verify/reclassify pass — tracked at Track 1's line 712-equivalent item below, not a distinct gap. (repo:
      market-tick-data-service)

      **RE-VERIFIED 2026-07-24 (this pass) — the `--apply` handoff is still NOT unblocked; NOT 0 glued ids.** The 9
                  ORCA `dex_pool_state` cells (2025-12-23..12-31) finished migrating clean this session (all 9 confirmed
                  `errors=0` across a retry chain: `leafparallel`+`lpar5`+`lpar7` VMs, cumulative `cells=1+3+5=9`) and a scoped
                  manifest rebuild ran after — but a fresh `verify_defi_glued_ids_2026_07_24.py` run still shows **21 glued-id
                  rows** (unchanged: the same 9 ORCA + the same 12 liquidations). Root cause (code-read, not inferred): neither
                  the migration, the scoped rebuild, nor this delete-marker script (GCS-objects-only, confirmed via its own
                  docstring) ever **retracts** a pre-existing manifest row once its source object is renamed to `_migrated_*` —
                  the old glued-id row and the new per-instrument rows have different `instrument_id`s, so upsert never
                  supersedes the old one. Full findings + recommended next step (a manifest-row-level purge, not yet built):
                  `plans/archive/issues/mtds_defi_migration_cell_stall_untimed_gcs_read_2026_07_22.md` addendum "tick 3"
                  (2026-07-24). **The `--apply` operator handoff at the parent plan (line 708) stays gated — do not consider it
                  unblocked by the 9 ORCA cells finishing; a separate manifest-side fix is still required first.**

- [x] ✅ [DATA] P1. **Verify the fake-history relabel-forward migration to actual completion** (todo 3,
      `/plans/archive/issues/defi_solana_dex_pools_fake_history_recurrence_prd_bucket_2026_07_23.md`) — **VERIFIED
      COMPLETE 2026-07-24 ~12:09 UTC**: all 4 ON_DEMAND VMs (`d01to05v3`/`d06to09v3`/`d10to13v3`/`d14to17v3`) terminated
      cleanly, `run.log` ends `done. objects processed = N (apply=True)` + `exit_code=0` for each, sum = 241,281 exactly
      matching the measured source population (no shard under-ran). **Re-confirmed independently in this session** via a
      fresh `gcloud storage ls` count against the live `-prd-` bucket: `day=2026-05-04` = 14,104 ORCA + 119 RAYDIUM,
      `day=2026-05-05` = 14,099 ORCA + 113 RAYDIUM, sum = 28,435 distinct canonical `dex_pool_state` objects, exactly
      matching the issue doc's cited final count. Pending-delete audit report
      (`_index/audit/dex_pools_fake_history_pending_delete.parquet`) confirmed present in GCS for the later human
      delete-review step. (repo: market-tick-data-service)
- [x] ✅ [DATA] P2. **CLOSED 2026-08-07 (na-eligibility-audit, stale-item citation-fix).** File + fix the
      `staking_yields_handler.py` / `lst_rates_handler.py` gap found during the 2026-07-22 C2–C12 scoping pass —
      verbatim-extracted into `issues/defi_staking_yields_lst_rates_handler_gaps_2026_07_24.md` (status: open,
      `assigned_vm: planning`), which re-verified both claims live: the `lst_rates_handler.py` "non-canonical path" half
      is FALSE (docstring-only drift, already fixed there — the handler does write to the canonical hive path); the
      `staking_yields`-dead-in-production half IS real and stays tracked in that doc's own open §6. Do not re-open this
      checkbox; real remaining work lives at the cited doc. (repo: market-tick-data-service)
- [x] ✅ [BACKEND] P2. **Cherry-pick the unshipped `is_defi_force_include_pool` wiring — SHIPPED 2026-07-24
      `instruments-service@4e97a82e`** ("wire is_defi_force_include_pool into DEX relevance filter + catalogue
      force_include"), confirmed ancestor of `origin/live-defi-rollout`. The UAC-side predicate is now wired into
      `filter_defi_instruments_by_relevance` + `_add_force_include`, covering the high-TVL Raydium pool force-include
      behavior R5 flagged (32 legacy-only pools incl. XMR/USDC $47M, BNB/USDC $18M). (repo: instruments-service)

- [x] ✅ [DOC] P1. **RESOLVED by concurrent work, verified 2026-07-24 (autonomous session) —
      `defi_consolidated_closeout_2026_07_18.md` is back UNDER the 1000L hard cap.** Live re-check via the actual gate
      (`bash scripts/plan-hygiene/check_line_caps.sh`): the file is now **996L**, badged `SOFT` (over the 500L soft
      threshold, but no longer over the 1000L hard one) — not in `check_line_caps.sh`'s hard-violator output at all.
      Other concurrent sessions' own split/trim passes on this same shared branch (this todo cites its own extraction
      precedent) already did the ~550-line trim this todo called for between when it was filed (1546L) and now — no
      further extraction needed to clear the hard gate. The scoped prek hook that originally blocked edits to this file
      no longer blocks a staged touch to it (verified via the same live gate script run above, not by testing an actual
      commit against it in this pass). Note the file is still over the 500L SOFT threshold (996L) — the "Aggregated
      source docs" / "Contradiction resolution" extraction candidates named below remain a reasonable FUTURE hygiene
      improvement, just no longer a hard blocker on anyone editing the file. (repo: unified-trading-pm)
