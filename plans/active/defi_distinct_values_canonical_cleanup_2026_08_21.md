---
doc_type: plan
title: DeFi distinct-values canonical cleanup — purge legacy/phantom manifest rows, fix live writers, execute canon-swap, verify UI/API clean
summary: >-
  Client-facing deliverable — the deployment UI/API distinct-values panel for DeFi must show ONE canonical value set
  per axis (venue/chain/instrument_type/data_type). Live census 2026-08-21 found 22 EVM chain-glued venue rows that are
  pure manifest phantoms (zero backing GCS objects, 100% fake "captured"), 4 Solana glued venues written by a
  still-LIVE writer bug, legacy data_types (dex_pools/dex_swaps/rate_indices), POOL casing regrowth, and blanket
  perp_funding/derivative_ticker honest-absence stamps on non-perp venues. This plan purges/migrates them, root-fixes
  the writers/seeders so they don't regrow, executes the already-shipped N5r/N6r manifest canon-swap on a VM, and
  regenerates the coverage rollup so the panel verifies clean. Operator rulings 2026-08-21 — physical merge now; full
  autonomy incl. proof-gated deletes; human plan.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos:
  [
    market-tick-data-service,
    instruments-service,
    deployment-service,
    unified-api-contracts,
    deployment-api,
  ]
scope: [engineer]
tags: [defi, canonicalisation, manifest, distinct-values, migration, data-correctness]
related:
  [
    /plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md,
    /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md,
    /plans/active/issues/b21_distinct_values_noncanonical_live_2026_08_18.md,
    /plans/active/issues/b21_defi_venue_5_unregistered_perp_dex_2026_08_19.md,
    /plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md,
    /plans/active/data_pipeline_completion_2026_08_21.md,
    /plans/active/defi_track01_per_instrument_and_canon_id_2026_07_24.md,
  ]
created: 2026-08-21
last_updated: 2026-08-21
parent_epic: defi_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
assigned_role: data_engineering
effort: max
context_scope:
  [
    /codex/02-data/defi-canonical-naming-ssot.md,
    /codex/02-data/four-surface-reconciliation-procedure.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /codex/02-data/honest-coverage-model.md,
    market-tick-data-service/market_tick_data_service/scripts/defi_manifest_venue_itype_canon_swap.py,
    market-tick-data-service/market_tick_data_service/scripts/defi_manifest_drain_gate.py,
    deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh,
    deployment-api/deployment_api/routes/data_status/_distinct_values.py,
    instruments-service/scripts/measure_honest_coverage.py,
  ]
drift_direction: advance-code
---

# DeFi distinct-values canonical cleanup (2026-08-21)

> **Codex SSOTs**: /codex/02-data/defi-canonical-naming-ssot.md (bare venue + separate chain= is canonical; combined
> PROTOCOL-CHAIN is legacy) · /codex/02-data/four-surface-reconciliation-procedure.md ·
> /codex/02-data/gcs-and-manifest-delete-safety-protocol.md · /codex/02-data/honest-coverage-model.md.
>
> **Operator rulings (2026-08-21, this session)**: (1) physical merge NOW, not read-path cosmetics; (2) FULL autonomy
> incl. deletes where the five-part proof / phantom-verification passes (overrides the human-only default for this
> cleanup); (3) this is a human (NA) plan; (4) zero-content rows (empty_confirmed / phantom "captured" with no object)
> under NON-canonical venue spellings are purge targets too — the manifest must only carry canonical venues, because
> legacy rows pollute the distinct-values panel and the coverage denominator.
>
> **Explicit NON-goals**: perp_funding vs derivative_ticker are NOT duplicates — ruled 2026-07-15/2026-08-08 and
> code-verified 2026-08-21 (independent fetches; only 60.7% match for HYPERLIQUID; features-service is hardwired
> venue-by-venue to one or the other with no fallback). Do NOT merge them. The 6-venue CARRY_BASIS_PERP defi-bucket
> home (BINANCE-FUTURES etc.) is operator-ACCEPTED (2026-08-20) and live-read by CanonicalPerpFundingProvider — do NOT
> purge; disposition is todo 13.

## Evidence base (live census 2026-08-21, slot-3 session)

- Defi `_index`: 161,763,515 defi rows. Census artifacts (the
  verbatim distinct-values BEFORE payload `defi_distinct_values_result.json`, per-venue purge counts, retirement + rekey verdicts) are committed under
  `/plans/audit/results/defi_distinct_values_census_2026_08_21/`.
- **Class A — 22 EVM glued phantom venues** (`UNISWAP_V3-{ETHEREUM,ARBITRUM,BASE,OPTIMISM,POLYGON}`,
  `BALANCER-{6 chains}`, `CURVE-{AVALANCHE,ETHEREUM}`, `SUSHISWAP_V3-{BASE,AVALANCHE,ETHEREUM}`, `SUSHISWAP-ARBITRUM`,
  `CAMELOT_V3-ARBITRUM`, `PANCAKESWAP_V3-{BASE,ETHEREUM,BSC}`, `AERODROME_V3-BASE`): all `data_type=dex_pool_swaps`,
  `chain=""`, `instrument_id=NULL`, 100% capture_status=captured, `written_at` clustered 2026-08-03/04T07:2x (single
  bulk registration), **zero backing GCS objects** (prefix probes found no `venue={GLUED}/` prefix at all). Purge.
- **Class B — 4 Solana glued venues, LIVE writer bug**: `KAMINO-SOLANA`/`MARGINFI-SOLANA`/`SOLEND-SOLANA` (risk_params,
  real objects, e.g. `venue=KAMINO-SOLANA/chain=SOLANA/instrument_type=solana_lending/data_type=risk_params/`
  `KAMINO-SOLANA-SOLANA:SOLANA_LENDING:BONK.parquet`, last written 2026-08-14) + `SOLBLAZE-SOLANA` (lst_rates, 1,330
  rows, backing objects not found under expected defillama pipeline_mode — verify then purge-or-migrate). Fix writer,
  migrate objects, re-key manifest.
- **Class C — legacy axis values**: `dex_pools` 454,014 rows (re-retire; recurs via rebuild rescans of live legacy
  objects — needs a scan guard), `dex_swaps` 3,460,714 rows (REAL legacy-only content in 22/24 venue-chain pairs — NOT
  a blanket rename; content migration is gated), `rate_indices` 25,478, `POOL` uppercase 10,204,983 rows (canon-swap
  re-keys; MDPS root fix shipped @94215e9cd9 — confirm landed), blank instrument_type 5,620,899 rows + Python-None
  3,296 rows, blanket perp_funding/derivative_ticker stamps across ~90 non-perp defi venue-chain combos.
- **Distinct-values surface**: `GET /data-status/distinct-values/defi` reads the nightly honest-coverage rollup
  (`coverage.json`) raw-by-design (drift detector); the panel only reflects cleanup after the rollup regenerates.

## Todos

- [x] [SCRIPT] P0. 1. ✅ **MTDS writer fix — Solana glued-venue double-glue.** — market-tick-data-service@36e4c830:
      root cause `_lending_grain.py:141-145` `_PROTOCOL_TO_CANONICAL_VENUE` glued values (feeds
      risk_params/lending_indices handlers; `write_defi_rows` glues AGAIN) → bare KAMINO/SOLEND/MARGINFI;
      `solana_lst_archival.py:737,757` → bare SOLBLAZE; `_normalize_venue` false docstring corrected. 18 tests.
      Content-verified on origin/live-defi-rollout.
- [x] [SCRIPT] P1. 2. ✅ **Rebuild-scan legacy-path guard.** — market-tick-data-service@36e4c830:
      `_rebuild_defi_retired_guard.py` wired into `scan_and_rebuild` (retired `dex_pools` + double-glued-id detector
      via UAC `split_glued_venue_chain`; `dex_swaps` deliberately EXCLUDED — real un-migrated content). 12 tests.
      Content-verified on origin.
- [x] [DATA] P0. 3. ✅ **Purge Class-A 22 glued phantom venues.** — APPLIED 2026-08-21 20:02 London: deleted exactly
      4,834 rows (pass-1 count == live-measured expectation, per-venue counts in session log task3_apply_kleene8.log);
      pre-write server-side snapshot `_index/snapshots/pre_evm_glued_phantom_venue_purge_*.parquet` + `.bak`; CAS
      generation-match write, new generation 1787338958360429; consolidator paused for the write + re-enabled after.
      Kleene-mask fix was required (NULL chain + non-Kleene or_/and_ nulled the mask). Authorized by the operator
      ruling recorded in this plan's banner (§ Operator rulings 2026-08-21,
      /plans/active/defi_distinct_values_canonical_cleanup_2026_08_21.md). Original scope text: Safe-idempotent + self-justified per the banner ruling (/plans/active/defi_distinct_values_canonical_cleanup_2026_08_21.md § Operator rulings)
      (2): rows are phantom `captured` with verified-zero backing objects; per-venue prefix re-verification runs
      IMMEDIATELY before each delete inside the same tool run (delete-safety §phantom path; prefix_tpls must cover the
      glued shape). Use the existing IS/MTDS reconcile tooling — never a hand-rolled index rewrite. Evidence: per-venue
      before/after row counts. (repos: instruments-service, market-tick-data-service)
- [x] [DATA] P0. 4. ✅ **Re-retire `dex_pools` legacy rows** — retirement tool re-run to a terminal measured verdict
      2026-08-21 ~20:33 London (task4_retire_apply2.log): **retired=0 — the corpus was ALREADY fully retired** (the
      2026-08-16 re-retirement held; the census's 454,014 counted rows of any status, not captured rows). Exactly 29
      captured rows remain, ALL twinless ORCA/RAYDIUM address-keyed Solana pools dated 2025-01-17 (full list in the
      log) — these keep `dex_pools` alive in the distinct-values panel; follow-up todo 16. Scan-guard
      (todo 2, market-tick-data-service@36e4c830) now prevents regrowth.
- [x] [DATA] P1. 16. ✅ **Last captured `dex_pools` rows purged (nothing to migrate).** The mid-state census
      DISPROVED the migrate premise: all 29 remaining captured rows (RAYDIUM/SOLANA, 2025-01-17, address-keyed) carry
      **`row_count=0`** — zero-row placeholder captures under the retired data_type, and the canonical
      `data_type=dex_pool_state` twins for that day already exist (92 symbol-keyed objects). Executed 2026-08-22
      16:21Z per the banner ruling (4): rows deleted on VM `mtds-defi-blanket-perp-stamp-purge` via
      `purge_zero_row_dex_pools_rows_2026_08_22.py --apply --expect-delete 29` (pass-1 == 29, snapshot
      `_index/snapshots/pre_zero_row_dex_pools_purge_*` + `.bak`, CAS → **generation 1787415711357543**, rc=0), then
      all 99 legacy `data_type=dex_pools/` objects under day=2025-01-17 deleted (retention re-checked 604800s, twin
      dir verified non-empty, 0 legacy objects remain). `dex_pools` is now 0-captured → drops from the panel at the
      next rollup. NOTE: attempt 1 hard-aborted rc=3 exactly as designed — a stale-blob monitor false-SUCCESS had
      resumed the consolidator early and the one-off's PAUSED assert refused to write. (repo: market-tick-data-service)
- [x] [DATA] P0. 5. ✅ **Migrate Class-B Solana glued objects to canonical** — objects: 213 copied to the canonical
      `venue={BARE}/chain=SOLANA/` path + single-glue filename, pass-2 re-verified (213 present+verified, 0 mismatched,
      0 failed; plan CSV 293 entries). Manifest re-key APPLIED 2026-08-22 01:33 London
      (`rekey_solana_glued_venue_defi_rows_2026_08_21.py --apply`): 1,575 rows — KAMINO-SOLANA 80, MARGINFI-SOLANA 84,
      SOLEND-SOLANA 81, SOLBLAZE-SOLANA 1,330 (SOLBLAZE re-keyed rather than purged — its rows fold onto bare SOLBLAZE);
      server-side snapshot + CAS write, new generation 1787358781949362; consolidator re-enabled. Legacy glued OBJECT
      deletes deliberately NOT yet done → todo 17. Original scope text:
- [x] [DATA] P1. 17. ✅ **Delete the legacy glued Solana objects** — APPLIED 2026-08-22 09:30 London via
      `market-tick-data-service/scripts/one_offs/delete_legacy_glued_solana_defi_objects_2026_08_22.py --apply`
      (untracked until the dep-clean ship; lessons embedded): retention re-checked fresh = 604800s; ALL 293 copy-plan
      rows (not 213 — the copy plan enumerated 293 legacy objects, 80 of which already had matching twins before the
      copy pass) verified `deletable` (twin exists, size+crc32c equal) → `Deleted 293 legacy glued-venue object(s);
      skipped {}`; 0 twin_missing / 0 twin_mismatch. Evidence: session `task17_dryrun.log` + `task17_apply.log`.
      Authorized by the banner ruling (/plans/active/defi_distinct_values_canonical_cleanup_2026_08_21.md § Operator
      rulings). (repo: market-tick-data-service)
- [ ] [DATA] P0. 5-original. **Migrate Class-B Solana glued objects to canonical.** Bounded (hundreds of objects): UTL
      `gcs_copy_object` to `venue={BARE}/chain=SOLANA/...` + canonical filename, re-key the manifest rows, then delete
      legacy objects (reversibility-qualified: verify `gcs_bucket_soft_delete_retention_seconds() >= 604800` first;
      content-equality proof per copied object). SOLBLAZE-SOLANA rows: verify backing objects under the vocabulary the
      writer actually emits before verdict — purge-as-phantom only on a confirmed-absent probe. (repos:
      instruments-service, market-tick-data-service)
- [x] [DATA] P1. 6. ✅ **Purge blanket perp_funding/derivative_ticker honest-absence stamps on non-perp defi venues**
      AND root-fix the seeder/capability declaration. Root-fix SHIPPED both layers: unified-api-contracts@4b06013aea
      (defi-scoped union-fallback exclusion) + instruments-service@0020df5f (`_defi_perp_capable_protocols()` gate).
      Purge APPLIED 2026-08-22 08:50:51Z on in-region VM `mtds-defi-blanket-perp-stamp-purge` (e2-standard-4, Pattern A
      launcher `deployment-service/scripts/vm/launch-defi-blanket-perp-stamp-purge-vm.sh --apply --expect-delete
      441402`, one-off `purge_blanket_perp_stamps_nonperp_defi_venues_2026_08_22.py`): pass-1 census = 441,402 rows
      (0 `captured`), pass-2 `kept=161317283 deleted=441402`, server-side snapshot
      `_index/snapshots/pre_blanket_perp_stamp_purge_*` + `.bak`, CAS write → **new generation 1787388651853992**
      (`Purge applied. Deleted 441402 rows`, rc=0, run.log `vm-logs/mtds-defi-blanket-perp-stamp-purge/`). KEEP-set
      untouched by construction: ASTER/EXTENDED/HYPERLIQUID/LIGHTER + `*-FUTURES`/`*-PERP`. Consolidator cron paused
      for the write, resumed after. (repos: unified-api-contracts, instruments-service, market-tick-data-service,
      deployment-service)
- [ ] [INFRA] P0. 7. **Launch the N5r/N6r projection VM** (`deployment-service/scripts/vm/
      launch-defi-manifest-projection-vm.sh`, shipped @99b46b9f2d) — no defi rebuild VM is running (verified 2026-08-21,
      GCE list), so the 2026-08-10 blocker is clear. Verify STARTED + progress + terminal state; record the swap
      plan-mode ADD/REMOVE delta here and in the owning issue doc. (repo: deployment-service)
- [ ] [SCRIPT] P0. 8. **Drain-gate + apply + post-verify the canon-swap** (`--drain-gate` → snapshot →
      `--apply-prod --confirm-prod-write` on the VM) per
      /plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md todo (e) — same safety
      construction (snapshot rollback path, stale_remaining=0, canon_missing=0, no captured→failed mass flip). Sequence
      AFTER todos 3-5 manifest mutations complete (drain requires quiet index). Flip the issue doc's checkbox with the
      same evidence. (repo: market-tick-data-service)
- [ ] [SCRIPT] P0. 9. **Regenerate the honest-coverage rollup + verify the panel clean.** Re-run
      `measure_honest_coverage.py` (or trigger its nightly job) post-mutations; re-derive
      `/data-status/distinct-values/defi` via the production functions; verify: zero glued `PROTOCOL-CHAIN` venue
      values, zero `dex_pools`, single-cased instrument_types, no phantom venues. Record the before/after distinct
      counts (108 venues → target ≤ ~70 canonical). (repos: instruments-service, deployment-api)
- [ ] [SCRIPT] P1. 10. **Blank/None instrument_type diagnosis** (5,620,899 blank across 71 venues + 3,296 None across
      16): classify by (venue, data_type) writer, decide per-class backfill-or-accept, execute the clear cases. (repos:
      market-tick-data-service, instruments-service)
- [ ] [SCRIPT] P2. 11. **Consumer alignment residuals**: MDPS `_DEFI_DEX_VENUE_SEGMENTS` hand-maintained legacy
      combined-form literals (orchestration_scanner.py:88-113) — remove once GCS carries no combined-form objects;
      MTDS preflight combined-form vocabulary (preflight.py:292-296) — verify against post-swap manifest;
      optional defensive fold in measure_honest_coverage. (repos: market-data-processing-service,
      market-tick-data-service, instruments-service)
- [ ] [SCRIPT] P2. 12. **`rate_indices` (25,478 rows) migration to `lending_indices`** — same treatment class as
      dex_pools; verify content vs canonical twin first. (repo: market-tick-data-service)
- [ ] [OPERATOR] P2. 13. **Boundary disposition**: HYPERLIQUID/ASTER/EXTENDED/LIGHTER perp rows + the 4 `*-FUTURES`
      carry-basis venues remain visible in the DeFi distinct values. SSOT classes on-chain perp CLOBs as cefi, but the
      defi-bucket carry-basis home is operator-accepted and live-read. Decide: accept + register as expected exceptions
      (badge canonical, document) vs re-home the corpus to the cefi bucket (large migration). Until ruled, they stay.
- [ ] [SCRIPT] P2. 14. **`dex_swaps` → `dex_pool_swaps` content migration** (3.46M rows, real legacy-only content) —
      execute per /plans/active/issues/defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md under its
      five-part proof gating; not a blanket rename. (repo: market-tick-data-service)
- [ ] [SCRIPT] P2. 18. **`check_plan_commit_sha_evidence.py` false-fails every sibling citation when the commit runs
      inside a git WORKTREE** — measured 2026-08-22 (this plan's doc push from a temp worktree at origin): git exports
      an ABSOLUTE `GIT_DIR` (`.git/worktrees/<name>`) to hooks, so the checker's `git -C <sibling-repo> cat-file -t
      <sha>` resolves against the PM worktree's object store and reports real, on-origin citations as unresolvable;
      the same checker run by hand from the worktree (`--workspace-root <ws> --only …`) is clean. Fix: strip
      `GIT_DIR`/`GIT_WORK_TREE`/`GIT_INDEX_FILE` from the sibling-repo subprocess env (or `env -u` in
      `run_hygiene_sweep.sh`'s invocation). safe-doc-push's isolated mode may hit this too — verify. (repo:
      unified-trading-pm; `scripts/quality_gates/check_plan_commit_sha_evidence.py`)
- [ ] [DATA] P1. 19. **KAMINO-SOLANA residual 339 captured rows (2026-08-09..13) + KAMINO_LENDING 80 rows
      (2026-06-01..08-05) + BLAZESTAKE 1 row (2026-08-06)** — measured in the 2026-08-22 mid-state census: the todo-5
      copy plan only covered KAMINO-SOLANA 2026-06-01..08-05; rows written between then and the writer fix (last
      legacy write 2026-08-14) were out of scope, and the KAMINO_LENDING third spelling was never in scope. Expect the
      N5r/N6r canon-swap to re-key them (spelling-legacy class, twins from the projection); VERIFY post-swap they are
      0, else extend the todo-5 migration to the residual window. (repo: market-tick-data-service)
- [ ] [SCRIPT] P2. 20. **Walkthrough doc uses glued venue names in client-facing prose** — operator-flagged
      2026-08-22: `codex/14-customer-journeys/commercial-model/platform-external-api-walkthrough.html` hand-writes
      `KAMINO-SOLANA`, `ORCA-SOLANA`, `PACIFICA-SOLANA` (×4), `JITO-SOLANA`, `MARGINFI-SOLANA`, `MARINADE-SOLANA`,
      `NATIVE-SOLANA`, `JUPITER-SOLANA`, `PYTH-SOLANA`, `JITORESTAKING-SOLANA` — hand-authored (not API-generated),
      and a slot-2 session is actively editing it under /plans/active/walkthrough_feedback_remediation_2026_08_21.md
      (PROTECTed — do not edit concurrently from this slot). Fold canonical bare-venue + `chain=SOLANA` naming into
      that remediation pass, or apply here once it lands. (repo: unified-trading-pm)
- [ ] [SCRIPT] P2. 15. **Post-phase codex audit**: update defi-canonical-naming-ssot (phantom-registration class,
      Solana double-glue gotcha), update/flip the owned checkboxes in the related issue docs, fix any doc that misled
      during this work. (repo: unified-trading-pm)

## Deferred work after 2026-08-22 (pre-compact checkpoint, ~01:40 London)

| item | state / why deferred | blocked-on |
| --- | --- | --- |
| Todo 8 canon-swap apply (`--drain-gate` → snapshot → `--apply-prod --confirm-prod-write` on the VM) | **Cannot be done yet** — needs the projection to finish. VM `…-20260821-195038` was NOT preempted: its in-guest stall watchdog killed a HEALTHY run (rc=137, 39 parts, last part 53s before the kill) because the launcher's `STALL_PROGRESS_REGEX=progress:` matched 0 lines of run.log. Launcher regex + `BACKFILL_CMD` module-form both re-fixed (local, ship pending dep-clean) → relaunched `defi-manifest-projection-20260822-074226` (e2-standard-8 per measured 175% CPU / 3.3 GB RSS; UAC tarball one unrelated commit stale, warn-mode) with ONE sized monitor (`monitor_vm_072651.py <run-ts>`, 14h cap, stall = parts flat 3h) | projection completion |
| Todo 6 purge-half (existing blanket perp_funding/derivative_ticker rows on non-perp venues) | **Not done (apply pending)** — forward seeding stopped (unified-api-contracts@4b06013aea + instruments-service@0020df5f); one-off `purge_blanket_perp_stamps_nonperp_defi_venues_2026_08_22.py` authored + dry-run MEASURED 441,402 rows / 0 captured (local, 22 min); apply runs on an in-region VM via `deployment-service/scripts/vm/launch-defi-blanket-perp-stamp-purge-vm.sh --apply --expect-delete 441402` (needs `create-code-tarballs.sh --include market-tick-data-service --force` so the untracked one-off rides the tarball, consolidator re-paused immediately before launch, resumed after the terminal verdict); serialize with every other index write | nothing |
| Todo 9 rollup regen + panel verification | **Not done** — run `measure_honest_coverage.py` (or its nightly job) AFTER the index rewrites settle, then re-derive `/data-status/distinct-values/defi` via the production functions (`dump_defi_distinct.py` pattern in the census artifacts) and record before/after distinct counts (before: 108 venues / 32 data_types / 16 instrument_types / 23 chains) | todos 6-half, 8 |
| Todo 16 (29 twinless dex_pools → dex_pool_state), todo 17 (213 legacy glued object deletes), todo 10 (blank itype), 11, 12 (`retire_rate_indices_legacy_captured_rows_2026_08_12.py` already exists), 14, 15 | **Not done** — bounded, tooling mostly exists | nothing (serialize index writes) |
| Todo 13 boundary disposition (HYPERLIQUID/ASTER/EXTENDED/LIGHTER + `*-FUTURES` carry-basis in DeFi distinct values) | **Operator-owned** | operator |
| MTDS one-off scripts commit (purge + rekey + NEW todo-6 purge script, lessons embedded) + deployment-service launcher regex fix | **Not done** — quickmerge attempts 1 (type-check timeout under host load ~200) and 2 (Stage-1 dep gate: foreign WIP in UAC 9 files + UTL 10 files) FAILED; scripts intact + untracked locally; a dep-clean watcher is armed → re-ship `--isolated` the moment UAC+UTL are clean, verify by `git show origin:<file> \| grep <symbol>` | peer WIP in UAC/UTL |

**Recommended NEXT**: verify the projection VM (preempted? → relaunch), then run the todo-6 purge-half while the
projection runs (independent: purge = index write, projection = GCS scan + read-only plan), then todo 8 apply after
drain, then todo 9. Serialize EVERY index rewrite (CAS makes a race a wasted hour, not corruption).

## Progress Log

- **2026-08-22 ~17:30 London (todo 16 DONE; operator re-affirmed complete-work mode)** — Operator (interactive):
  "keep going … complete work even if you fill others' work — the plans and docs are all there." Todo 16 executed
  end-to-end on a VM (details in the todo). Two more monitor lessons hardened into `monitor_vm_generic.py`: (1)
  same-name relaunches inherit the prior run's `vm-logs/` blobs — the monitor now takes a launch-epoch and treats
  older `EXIT_STATUS`/`run.log` as absent (a stale-blob false-SUCCESS had resumed the cron mid-run and correctly
  tripped the one-off's PAUSED hard-abort — attempt 2 with the epoch gate ran clean); (2) harness bash background
  tasks die at a 600s cap — monitors are now sized ≤520s and CHAINED via task notifications, and 4h dep-watcher
  loops are dead (dep state is checked inline each tick instead). MTDS QG for the carve-out ship: KILLED by the
  resource governor after a 3600s queue wait (host saturated by peer QGs, exit 75) — the 5 one-offs remain
  untracked-local; ship retries when the host quiets or UTL/DS clean up for normal quickmerge. Projection VM:
  62/~81 parts at 16:3xZ. PM checkout: peers rebased their 2 parked commits onto newer origin (behind 82→7,
  ahead=2 unchanged).
- **2026-08-22 ~12:30 London (mid-state census + operator Q&A)** — Read-only DuckDB census of the live index
  (scratchpad `midstate_*.csv`, generation 1787388651853992): distinct ANY-status = 83 venues / 34 data_types / 17
  itypes / 23 chains (BEFORE: 108/32/16/23); CAPTURED-view = 67 venues, 23 data_types. Remaining captured legacy:
  `POOL`/`PERPETUAL` itypes (canon-swap), KAMINO-SOLANA 339 + KAMINO_LENDING 80 + BLAZESTAKE 1 (todo 19),
  dex_pools 29 (todo 16), dex_swaps 189,061 real content (todo 14); `rate_indices` is 0-captured (fully retired —
  drops from the panel at the next rollup regen). Blank-itype (todo 10) quantified: overwhelmingly
  `empty_confirmed`/`expected_unattempted` blanket absence stamps cross-joined per venue×data_type (e.g. AAVE_V3 ×
  19,453 rows EACH for dex_pool_state/eigenlayer_rewards/perp_daily_ctx/staking_yields/… — capabilities the protocol
  does not have): the same expected-universe cross-join disease as todo 6 but for NON-perp data_types; the IS fix
  gated only `_DEFI_PERP_ONLY_DATA_TYPES`, so full capability-gating + purge is the todo-10 execution shape
  (denominator correctness, post-swap). Operator (interactive): 82-behind PM = the co-occupant's 2 ungated local
  commits (their issue doc: PM quickmerge blocked by two pre-existing gates); two `pull --rebase --autostash`
  attempts aborted (`could not detach HEAD`, live peer edits mid-tree) — not forced; my pushes go via the
  origin-based worktree. Walkthrough HTML glued venues = hand-authored prose, slot-2 actively editing (todo 20).
  UAC tree is now CLEAN (peer landed); UTL + deployment-service still dirty — one-off/launcher ship still gated.
- **2026-08-22 ~10:00 London (todo 6 DONE on VM; stale-EXIT_STATUS monitor trap; doc-push path)** — Purge VM
  attempt 2 (with `VM_ASSET_GROUP=DEFI`) ran end-to-end in 13 min in-region: download + census 4 min, pass 2 7 min,
  7.15 GB CAS upload 81 s → generation 1787388651853992 (vs ~1h+ per attempt over the laptop uplink yesterday —
  the VM route is the only sane one for this index). LESSON: a relaunched VM with the SAME name inherits the previous
  attempt's `vm-logs/<vm>/EXIT_STATUS` blob until the new boot overwrites it with `RUNNING` (~2 min after create) —
  my monitor read the stale `78` and declared TERMINAL while attempt 2 was healthy; monitors must ignore an
  EXIT_STATUS older than the launch, or the launcher should delete the previous run's blobs. Doc push: isolated mode
  keeps abandoning ("plan changed on origin since last sync" — false alarm, only my own re-wrapped content) and the
  shared-index fallback correctly REFUSES (exit 16) because the co-occupant's 2 local-only CODE commits sit ahead of
  origin in this PM checkout — `SDP_ALLOW_UNRELATED_AHEAD=1` would ship their ungated code, so NOT used; pushing
  docs from a temp worktree at `origin/live-defi-rollout` (hygiene sweep run there) instead. Next: verify the first
  post-purge defi consolidator cycle (marker-strip self-heal = one full merge), todo 8 after the projection VM
  finishes, todo 9 rollup.
- **2026-08-22 ~09:40 London (todo 17 DONE; todo 6 VM apply attempt 1 rc=78 → relaunch; cefi finding)** — (1) Todo
  17 applied: 293 legacy glued Solana objects deleted after per-object twin re-verify (size+crc32c) and a fresh
  retention check (604800s) — see the todo's evidence line. (2) Todo 6 apply VM `mtds-defi-blanket-perp-stamp-purge`
  (Pattern A launcher `launch-defi-blanket-perp-stamp-purge-vm.sh`, one-off rides the force-republished mtds tarball
  @7facfa43 — verified by `tar -tzf`) died rc=78 BEFORE Python: `setup-data-pipeline-vm.sh` §5b OOM-preflight
  defaulted the asset group to CEFI and found the **CEFI consolidated `_index` 133134s stale** (last_modified
  2026-08-20T19:29Z, cron `…-cefi-cron` ENABLED, last attempt 08:00Z today) → exited 78. Fix: launcher now sets
  `VM_ASSET_GROUP=DEFI` (defi index last_modified 2026-08-22T00:33Z = my rekey, fresh). Relaunched with the defi
  consolidator cron re-verified PAUSED. The cefi staleness is a real, unrelated data-pipeline finding → issue doc
  `/plans/active/issues/cefi_manifest_consolidated_index_stale_37h_2026_08_22.md` (outside this plan's scope;
  operator notified in the session report). (3) Gotcha journaled: `create-code-tarballs.sh` upload step imports
  deployment_service → needs `GCP_PROJECT_ID` in env or it tracebacks AFTER building the tarball (first publish
  attempt lost 1 min that way); `.tmp/` IS tarball-excluded, and this session's 88 GB of local index copies under
  MTDS `.tmp/` were unlinked.
- **2026-08-22 ~09:10 London (todo 7 SECOND CORRECTION + relaunch #4; todo 6 dry-run measured)** — ⛔ VM
  `defi-manifest-projection-20260822-072651` died rc=2 in 10s on the OLD file-path command (`can't open
  …/workspace/mtds/scripts/rebuild_defi_manifest.py`). The launcher's module-style `BACKFILL_CMD` fix had NEVER
  landed on origin (`git log origin -- <launcher>` = only 99b46b9f + the fleet-wide `python -u` commit; the swept
  copy still sits in deployment-service `stash@{0}: quickmerge-8919`), and the local file had been reverted to origin
  content. My 2026-08-21 "verified 2 hits for `-m market_tick_data_service.scripts`" check matched the launcher's
  HEADER COMMENT, which always showed the module form. LESSON (third ahead=0-class miss): verify the FUNCTIONAL line
  (`git show origin:<file> | grep -n 'BACKFILL_CMD='`), never a symbol that also appears in prose. Re-applied the
  `-m` form with an inline "measured twice" comment; relaunched `defi-manifest-projection-20260822-074226`
  (e2-standard-8 SPOT, warn-mode tarball) — RUNNING, 19 parts by 07:58Z (2021 chunks ~30s each; the 2025-26 tail
  measured 23 min/chunk last night). Monitor re-armed with the fix that `EXIT_STATUS` reads literal `RUNNING` while
  alive (numeric = terminal). Todo 6 dry-run (read-only, local, 22 min): **441,402 rows** would be deleted —
  exactly the census prediction; 0 `captured` rows in the delete set; keep-set resolved to
  {ASTER, EXTENDED, HYPERLIQUID, LIGHTER} + `*-FUTURES`/`*-PERP`. Apply goes to an in-region VM (restamp-launcher
  pattern, `VM_TASK=canonical-migration`), serialized after nothing (the projection VM only READS the index at its
  swap-plan step; a CAS race costs a re-run, not corruption).
- **2026-08-22 ~08:30 London (todo 7 ROOT CAUSE + relaunch; todo 6 purge script authored)** — (1) VM
  `defi-manifest-projection-20260821-195038` was NOT SPOT-preempted: `EXIT_STATUS=137`, run.log tail =
  `WORKER_STALLED (no-progress-marker): no progress in 7206s (threshold=7200s)` — the in-guest watchdog killed it
  exactly 7200s after start while it was HEALTHY (part0039 written 22:03:08, kill 22:04:01; chunk cadence 3-23 min).
  Root cause: the launcher set `STALL_PROGRESS_REGEX=progress:` and its comment claimed the script logs
  "progress: chunk N/M done" — FALSE; `rebuild_defi_manifest.py` logs `chunk N complete: …` and deliberately
  suppresses the `[[VM_PROGRESS]]` marker in `--dry-run`. Measured: 0 matches in the whole 8.4MB run.log. Fix:
  regex `chunk.[0-9]+.complete` (metadata-safe) + corrected comment in
  `deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh` (local; ship blocked on dep dirt, see
  Deferred). Relaunched `defi-manifest-projection-20260822-072651` (`--end-date 2026-08-22`, `MACHINE_TYPE=
  e2-standard-8` — rightsizing from the measured profile 175% CPU / 3.3 GB RSS on 16 vCPU; `LC_TARBALL_FRESHNESS=
  warn` because the UAC tarball @72af5a19 is stale only by `venue_granularity.py` NASDAQ/NYSE commits — irrelevant
  to DeFi naming — and UAC's tree carries live peer WIP so it cannot be republished). Monitor armed (scratchpad
  `monitor_vm_072651.py`: parts count = progress metric, EXIT_STATUS = terminal, 14h cap). (2) Host load 138-211
  (76 foreign QG/pytest processes, slots 2/4/6): a bare UTL import takes 70s, `gcloud` 60s+; every local probe
  >100s — size timeouts accordingly, never conclude "hung" under 5 min. (3) Todo 6 purge-half script authored:
  `market-tick-data-service/scripts/one_offs/purge_blanket_perp_stamps_nonperp_defi_venues_2026_08_22.py` — keep-set
  derived at runtime from UAC `PROTOCOL_CAPABILITIES` (+ HYPERLIQUID/ASTER/EXTENDED/LIGHTER, `*-FUTURES`, `*-PERP`),
  hard-aborts on any `captured` row in the delete set, `--apply` requires `--expect-delete N` from the dry-run;
  census CSV predicts ~441k rows (475,649 non-captured perp-dt rows − EXTENDED 14,460 − LIGHTER 17,352 − ASTER 2,435;
  BINANCE/COINBASE bare rows are LST-protocol cross-join stamps, in scope). Read-only dry-run running locally.
- **2026-08-22 ~01:40 London (pre-compact checkpoint — lessons, not just state)** — (1) **Uplink is the bottleneck**
  for local index rewrites: each attempt moves ~7.5GB down + 7.5GB up; 3 attempts died on 600s read-timeouts /
  connection resets during peak host load; the final successful purge upload took ~1h. Server-side `copy_blob`
  snapshots (zero egress) are now in both one-offs. Any further rewrite of this size should run on an in-region VM.
  (2) **Kleene logic is load-bearing** in pyarrow masks over this index: `chain` is NULL (not `""`) on legacy rows;
  non-Kleene `or_`/`and_` propagate null → 0 matches → the script's count guard hard-aborts (good) but the rows stay.
  (3) **ahead=0 + zero-diff ≠ landed — twice this session** (IS seeder fix, deployment-service launcher): a failed
  quickmerge SWEEPS the change into `stash@{N}` and restores origin content; verify by `git show origin:<file> | grep
  <symbol>`, never by diff-vs-local. (4) **Chained-bash cwd drift**: three wasted runs came from prod-script paths
  resolved against the wrong repo after a `cd` earlier in the same chain — use absolute paths for every prod invocation.
  (5) The consolidator cron gets re-ENABLED by something external (it was ENABLED again ~1h after my pause without my
  resume) — always re-pause immediately before an index write, never assume an earlier pause holds. (6) The dex_pools
  corpus was already retired; the distinct-values panel is driven by the rollup's per-value retirement-drop, so a
  value disappears only when 0 captured rows remain — 29 twinless rows keep `dex_pools` visible (todo 16).
  (7) State: todos 1-5 ✅; 6 half ✅; 7 VM launched with verified progress (39 parts) but instance gone at checkpoint
  (SPOT preemption suspected, UNVERIFIED); PM local shows ahead=2 from a CO-OCCUPANT session's local-only commits
  (not mine — their issue doc names it) — my doc pushes land via isolated worktree regardless.
- **2026-08-21 ~21:0x London (todo 7 CORRECTION + recovery)** — ⛔ the earlier claim "deployment-service launcher fix
  landed on origin" was WRONG: the exit-128 quickmerge attempt had SWEPT the fix into `stash@{0}` and restored the OLD
  launcher; my "HEAD on origin + zero diff" check then verified equality against the OLD content (ahead=0 trap,
  second occurrence this session — same class as the IS sweep). Proof: VM `defi-manifest-projection-20260821-191035`
  (launched 19:10, self-deleted) died rc=2 on the exact old-path bug (`can't open .../workspace/mtds/scripts/
  rebuild_defi_manifest.py`), 0 projection objects. Recovered the fix from `stash@{0}` (6 module-style refs
  verified), reshipping `--isolated` + relaunching. LESSON journaled: after ANY quickmerge, verify the SYMBOL exists
  in `git show origin:<file>` — never diff-vs-local alone.
- **2026-08-21 ~17:2x London (todo 6 root-fix FULLY SHIPPED both layers)** — instruments-service@0020df5f
  (`capability-gated expected-universe seeding for perp data_types`, landed on LDR, content-verified on origin: the
  `_defi_perp_capable_protocols()` gate is present) + unified-api-contracts@4b06013aea (earlier). NOTE the recovery
  detail: the first IS quickmerge exited 12 having SWEPT the fix into `stash@{0}` (ahead=0 trap) — recovered via
  `git checkout 'stash@{0}' -- <files>` then re-shipped `--isolated` successfully. Remaining half of todo 6: purge the
  EXISTING blanket perp-stamp rows (forward seeding now stops; historical rows still in the index).
- **2026-08-21 ~17:2x London (todo 7 ship leg done; todo 3 purge in flight)** — deployment-service launcher fix landed
  on origin (module-style `-m market_tick_data_service.scripts.*` invocation; old tarball file path 404'd on the VM).
  VM launch attempt 2 was aborted by the stale-UAC-tarball freshness gate (co-occupant WIP, since cleared) — relaunch
  pending after the current uplink-heavy purge completes. Todo 3 purge: Kleene-mask fix VERIFIED (pass 1 matched
  EXACTLY the expected 4,834 phantom rows); attempts 2/3 died on 600s GCS read-timeouts (saturated uplink), attempt 5
  got through download+delete but died re-UPLOADING the 7.5GB snapshot — script patched to SERVER-SIDE
  `copy_blob` snapshots (zero egress, generation-pinned); attempt 7 running with a pause→apply→resume consolidator
  bracket. MTDS ship (todos 1+2): size-gate fix applied (`scan_and_rebuild` 213L→~196L via `_log_retired_skip` +
  `_covered_key` extraction); quickmerge attempt 4 mid-re-gate (pytest ~80%).
- **2026-08-21 ~15:15 London (todos 1+2 CODE-COMPLETE, ship pending)** — a LOCAL market-tick-data-service commit (superseded on LDR by market-tick-data-service@36e4c830; 10 files
  +557/-29; NOT yet on LDR — quickmerge dirty-deps-blocked, see choke point below). Root causes: (1)
  `_lending_grain.py:141-145` `_PROTOCOL_TO_CANONICAL_VENUE` mapped kamino_lending/solend/marginfi to GLUED
  `X-SOLANA` venues — feeds risk_params/lending_indices handlers; `write_defi_rows`'s `build_canonical_instrument_id`
  glues AGAIN → double-glued path+id; fixed to bare. (2) `solana_lst_archival.py:737,757` SOLBLAZE-SOLANA → bare
  SOLBLAZE. (3) `canonical_write.py:85` `_normalize_venue` docstring falsely claimed glue-stripping — corrected. (4)
  NEW `_rebuild_defi_retired_guard.py` wired into `rebuild_defi_manifest.py` scan: skips RETIRED
  `dex_pools` (dex_swaps deliberately EXCLUDED — real content) + double-glued-id detector via UAC
  `split_glued_venue_chain`. 18 new/updated tests. QG: own tests green; 1 fail + 1 collection error from unrelated
  same-day peer commit f7cdd18b (sports registry / pipeline_e2e_check) — peer sessions are actively shipping
  fixes/skip-marks for exactly those.
- **2026-08-21 ~15:15 London (execution state)** — Todo 3 purge apply RUNNING (Kleene-mask fix applied to
  `purge_evm_glued_phantom_venue_defi_rows_2026_08_21.py` — non-Kleene or_/and_ nulled the whole mask on NULL-chain
  rows; consolidator cron PAUSED for the write, resume after terminal verdict). Todo 7 projection VM launch attempt 2
  ABORTED at the tarball-freshness gate (dirty UAC checkout). **Single choke point: co-occupant sessions' uncommitted
  WIP in slot-3 UAC (`venue_instrument_type_axis.py`, actively being QG'd by its owner) + UTL (`ledger/run_writer.py`)
  blocks ALL of: MTDS ship (the local pre-36e4c830 commit), IS seeder-fix ship, deployment-service launcher ship, and the VM tarball
  publish.** Dep-clean watcher armed (60s poll, 45min cap) → on fire: relaunch VM + retry all three quickmerges.
  Purge agent also left `scripts/one_offs/rekey_solana_glued_venue_defi_rows_2026_08_21.py` (task-5 manifest re-key,
  untracked) — run after task-3 completes + copies verified.

- **2026-08-21 (slot 3, interactive + /autonomous)** — Plan created from a 4-agent live census (manifest census /
  distinct-values trace / plans census / UAC+consumer audit). Key numbers in § Evidence base. Census artifacts in the
  session scratchpad (`venue_census.csv`, `datatype_census.csv`, `instrumenttype_census.csv`, `chain_census.csv`,
  `perp_census.csv`, `defi_distinct_values_result.json`). VM fleet check: no defi rebuild VM running; canon-swap
  unblocked. Operator rulings recorded in the banner. perp_funding vs derivative_ticker settled as NOT-duplicates
  (code-verified; see banner).
- **2026-08-21 ~14:00Z (todo 6 root-fix half)** — Root cause of the blanket perp stamps FOUND + half-shipped. (1)
  Primary: `instruments-service/scripts/enumerate_expected_universe.py::_yield_v2_defi_pre_launch_rows` Class-2 loop
  cross-joined every `PROTOCOL_LAUNCH_DATES` entry (126 chain-protocol tuples) × ALL defi data_types incl.
  perp_funding/derivative_ticker with ZERO capability check. (2) Secondary: UAC
  `market_data_categories.py::valid_data_types_for_venue_instrument_type` unmapped-protocol fallback returned the
  cross-protocol UNION, leaking perp_funding via the `spot_pair` union — **fix SHIPPED
  unified-api-contracts@4b06013aea** (defi-scoped exclusion + 2 tests; QG 13445 passed, 2 pre-existing unrelated
  fails). IS seeder fix (capability-derived `_defi_perp_capable_protocols()` gate + 2 tests) is code-complete,
  QG-passed locally, but quickmerge Stage-1 dep validation is HARD BLOCKED: two unrelated peer sessions hold
  uncommitted WIP in this slot's UAC (`venue_instrument_type_axis.py` DERIBIT fix) + UTL (`ledger/run_writer.py`)
  checkouts — PROTECTed per liveness rule; re-attempt the IS quickmerge once peers land. Stops-seeding population: 71
  of 72 protocols × chains × {perp_funding, derivative_ticker} (ASTER kept — capability-declared; HYPERLIQUID /
  EXTENDED / LIGHTER untouched by construction). Reverse finding (report-only): `DATA_TYPES_BY_ASSET_GROUP["defi"]`
  declares perp_funding/derivative_ticker but no defi-axis venue capability produces them — inert axis declarations,
  belongs to the b21/orthogonality thread.
- **2026-08-21 ~14:00Z (in-flight)** — Todo 3 phantom purge forward-apply RUNNING + todo 5 Solana migration copy pass
  2 RUNNING (purge worker, background jobs with wake-loops). Todo 1 writer fix code-complete, QG queued behind the
  saturated host-wide QG governor (Monitor armed). Todo 7 projection VM: first launch attempt FAILED, launcher fix in
  QG, relaunch pending (worker driving).
- **2026-08-21 ~14:40 London — SESSION-LIMIT interruption (resets 16:40 London). RESUME STATE (lossless):** the purge
  and VM sub-agents were API-terminated mid-flight; verified NO orphaned process is mutating the manifest (ps clean;
  the only heavy host processes are a slot-2 peer quickmerge shipping adjacent DeFi handler fixes — it also skip-marks
  `test_defi_prefix_parser_handles_multi_hyphen_protocol_keys`, a pre-existing UAC `parse_defi_venue` multi-hyphen
  failure directly adjacent to this plan's glued-venue scope; see
  `/plans/archive/issues/mtds_defi_prefix_parser_multi_hyphen_solana_native_2026_08_21.md`). Per-todo resume state,
  scratch evidence in the session scratchpad: **Todo 3** — dry-run + full-reverify done (`task3_purge_dryrun.log`,
  `task3_full_reverify.log`); forward-apply NOT completed (216-byte `task3_forward_apply.log`): the worker found a
  REAL bug in its pyarrow mask before applying — `pc.equal(chain, "")` on a NULL chain yields null and non-Kleene
  `pc.or_`/`pc.and_` propagate it through the mask; the fix was unverified at termination. Re-verify the mask
  (null-safe: use `pc.is_null` OR Kleene logic) against the dry-run counts BEFORE any apply. **Todo 4** — no evidence
  of execution; not started. **Todo 5** — SOLBLAZE-SOLANA confirmed PHANTOM (absence re-verified across writer
  vocabularies, `task5_solblaze_reverify.log`/`task5_solblaze_absent.csv` → purge rows with todo 3); copy pass 1 done
  (`task5_copy.log`, plan `task5_copy_plan.csv` 142KB), pass 2 started (`task5_copy_pass2.log` 313B) — re-verify copy
  completeness against the plan CSV, then manifest re-key, then retention-qualified legacy deletes. **Todo 1** —
  writer-fix worker ALIVE at interruption: QG queued ~57min behind the saturated host governor (host cap 7, peer-slot
  runs), Monitor armed on the QG log terminal marker; ship + report pending. **Todo 6** — UAC half SHIPPED
  (@4b06013aea); IS half code-complete in the IS working tree, quickmerge dep-gate blocked on peer WIP in UAC
  (`venue_instrument_type_axis.py` et al.) + UTL (`ledger/run_writer.py`) — re-attempt when peers land. **Todo 7** —
  VM NOT launched; launcher fix was in QG at ~98% when the worker was terminated; deployment-service working tree
  holds the fix — verify QG, quickmerge, launch, then todo 8 sequencing (apply only after todos 3-5 mutations land +
  drain gate green).
