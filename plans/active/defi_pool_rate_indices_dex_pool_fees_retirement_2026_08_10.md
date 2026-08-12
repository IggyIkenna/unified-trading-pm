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
status: active
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

- [x] ✅ [DATA] P1. **Verify the rebuild VM reached terminal SUCCESS + confirm POOL/rate_indices/dex_pool_fees counts
      are STABLE.** — unified-trading-pm (verification-only, no code). Latest successor VM
      `canonical-migration-defi-rebuild-20260810-204358` reached genuine terminal SUCCESS: `run.log` shows
      `Rebuild complete:` for the final chunk (`2026-08-25..2026-11-22` then `2026-11-23..2026-12-31`, both empty —
      corpus exhausted), `REBUILD_DEFI_MANIFEST_RUN_COMPLETED`, `[vm-exec] command exited rc=0`, deployment archived
      `status=completed exit_code=0`, then self-deleted (`VM_SHUTDOWN_ON_COMPLETION=true`). 3 live
      `read_availability_index()` queries (17:37:xx, 17:38:xx, 17:43:41 UTC 2026-08-11 — spanning the required ~5min)
      against the freshly-consolidated index blob (confirmed fresh via `get_blob_metadata()`,
      `last_modified=2026-08-11T17:33:39Z`) returned IDENTICAL counts every time: `instrument_type=POOL`
      (`dex_pool_swaps`) = 7,930,863; `data_type=rate_indices` `captured` = 26,128; `data_type=dex_pool_fees` `captured`
      = 21 (out of 39,349,334 total `captured` rows). Done-when met: VM terminal SUCCESS + all 3 counts stable. STOP
      clause not triggered.

      Note for todo 2's worker: the direct pandas `read_availability_index(columns=..., filters=[("capture_status",
                                                                      "==", "captured")])` path OOM'd repeatedly (killed at 8G/16G/24G RSS caps, then again unwrapped) even against the
                                                                      fresh consolidated blob — decoding 39M captured rows into a DataFrame is itself too heavy. Query via a streaming
                                                                      DuckDB aggregate over a locally-streamed copy instead (`client.download_file()` + `duckdb.read_parquet()` +
                                                                      `COUNT(*) FILTER (...)`), not a pandas `read_availability_index()` call — bounds memory to DuckDB's own
                                                                      streaming footprint regardless of corpus size.

- [x] ✅ [DATA] P1. **Root-cause the 0→7,930,863 `instrument_type=POOL` recurrence before any retirement resumes**
      (blocks the retirement todo below — main-agent-added 2026-08-11 per
      `/plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md`, BLK-e7fe6971 answered A). Confirm
      the rebuild VM's actual deployed code content (`cloudbuild`/tarball manifest `commit_sha`) to rule in/out a stale
      pre-N6a snapshot. (repo: market-tick-data-service) — unified-trading-pm (verification-only, no code). **Stale
      pre-N6a snapshot theory RULED OUT.** See Progress Log for evidence.
- [x] ✅ [DATA] P1. **Determine whether the manifest rebuild is full-replace or upsert-onto-existing-index** (same
      recurrence investigation). Read `rebuild_defi_manifest.py`'s top-level `main()`/index-write path — if upsert, any
      pre-existing uppercase rows that survived the 2026-08-05 fold would pass through untouched rather than being
      reintroduced by the rebuild. (repo: market-tick-data-service) — **UPSERT-onto-existing-index, NOT full-replace.**
      The rebuild's only index write is a per-VM shard (`_build_manifest_writer()` →
      `ManifestWriter(per_vm_shards=True)` → `_index/per_vm/{instance}.parquet`); UTL `_writer.py` `per_vm_shards`
      docstring + `_read_index.py` `_read_and_merge_per_vm_shards` confirm the consolidator merges shards into the
      canonical `_index/availability_index.parquet` asynchronously (last-attempted-write wins per dedup key). The
      rebuild never deletes/rewrites rows in the canonical index its scan doesn't touch, and `parse_hive_path`
      lowercases `instrument_type` unconditionally (lines 370/395) — so the 7.9M uppercase `POOL` rows were PRESENT in
      the index BEFORE the rebuild ran and passed through untouched; the rebuild is exonerated as a reintroduction
      mechanism. Full evidence: Progress Log, 2026-08-12 (slot 32) entry.
- [x] ✅ [DATA] P1. **Sample the 7,930,863 uppercase rows' underlying GCS objects directly** — market-tick-data-service
      (verification-only, no code). **CONFIRMED: manifest-column-only artifact.** Sampled 30 rows across the full date
      range (2023-01-01→2026-08-05), both pipeline_modes (`batch_onchain_subgraph` + `batch_onchain_rpc`), 5 venues
      (UNISWAP_V2, UNISWAP_V3, TRADER_JOE_V2), 3 chains (ETHEREUM, AVALANCHE, POLYGON): **0/30 have physical GCS objects
      at `instrument_type=POOL/`** (uppercase); **30/30 have objects at `instrument_type=pool/`** (lowercase). A broad
      scan across 5 dates (2023-06-15→2025-06-15) found **0 total objects** containing `instrument_type=POOL/` anywhere
      in their GCS path. The 2026-08-05 fold's assumption is correct — no Part-5 "legacy COPIED not MOVED" migration
      treatment needed. The retirement todo's only remaining blocker is slot-31's wrapped-id content-verify gap
      (manifest-only fix is safe). Full evidence: Progress Log, 2026-08-12 (slot 32) entry.
- [x] ✅ [DATA] P1. **Pause the DeFi manifest consolidator cron, retire POOL (uppercase `instrument_type`) legacy
      `captured` rows in `dex_pool_swaps` via the proven reversible `capture_status: captured→attempted_failed`
      pattern.** Mirror `retire_dex_pools_legacy_captured_rows_2026_08_05.py` /
      `retire_dex_swaps_legacy_captured_rows_2026_08_09.py` (both `market-tick-data-service/scripts/one_offs/`). Pause
      `uts-prod-manifest-consolidator-market-data-defi-cron` (`asia-northeast1`) before writing, resume after.
      Done-when: a fresh `read_availability_index()` query shows 0 remaining `captured` rows with
      `instrument_type=POOL`. (repo: market-tick-data-service) — **DONE 2026-08-12 (slot 7, data_engineering):
      `market-tick-data-service@5e456d0d`.** Resolved both blockers the prior slots flagged — slot-31's content-verify
      gap AND slot-31's script key-vocabulary bug (its dry-run matched 0 of 1,135,962 keys because it unwrapped only the
      canonical side). Content-verified live (DuckDB + GCS object probes): canonical `pool` twins' objects hold real
      swap data at lowercase `instrument_type=pool/` paths; no-twin legacy rows' physical objects also exist there (real
      data, never hidden). Fixed the script to unwrap BOTH sides to the last-colon segment → 1,122,141 of 1,135,962
      legacy keys (98.8% of 7,930,863 rows) have a canonical twin. Applied two-bucket treatment (mirrors the 2026-08-05
      fold): RETIRED 7,834,322 twin-having rows (`captured→attempted_failed`) + FOLDED 96,541 no-twin rows (`POOL→pool`,
      kept `captured`). Cron paused before write / resumed after. Snapshot
      `_index/snapshots/pre_pool_uppercase_retire_2026_08_12T*.parquet` + `.pool_uppercase_retire.bak` written
      pre-write. Post-apply fresh query: **0 remaining captured `instrument_type=POOL` rows** (`POOL`
      attempted_failed=7,841,381; `pool` captured=8,849,599 incl. the 96,541 folded).
- [x] ✅ [DATA] P1. **Retire `rate_indices` legacy `captured` rows** (fold already GENUINELY 100% COMPLETE 2026-08-07
      per `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md` row 4 — this is the retirement half only,
      never done). Same reversible pattern + consolidator pause/resume as the prior todo (share the pause window if run
      back-to-back). Done-when: 0 remaining `captured` legacy `rate_indices` rows. (repo: market-tick-data-service) —
      **DONE 2026-08-12 (slot 20, data_engineering): `market-tick-data-service@bf712ddb`.** Three-bucket treatment
      (mirrors the POOL precedent's retire-vs-fold split): RETIRE 25,478 twin-verified rows (AAVE_V3/ETHEREUM 3,160
      exact-id; MORPHO/ETHEREUM 22,318 full-address-prefix) + FOLD 650 no-twin rows (22 MORPHO markets whose
      fold-written `batch_onchain_rpc` canonical objects exist on GCS but were never manifest-registered — only the
      subgraph twin existed; folded in-place to `MORPHO-ETHEREUM:LENDING:{sym}-0x{short}`, kept `captured`) + EXCLUDE 0.
      Consolidator paused before write / resumed after. Round-trip + independent post-apply verify: **0 captured
      `rate_indices` rows**; `lending_indices` captured 385,050→385,700 (+650 folded exactly); snapshot
      `_index/snapshots/pre_rate_indices_retire_20260812T144912Z.parquet` + `.rate_indices_retire.bak`. See Progress Log
      for the fold-gap finding (650 cells' rpc canonical rows were never registered).
- [x] ✅ [DATA] P2. **Verify + retire `dex_pool_fees` legacy `captured` rows if any remain** (tiny scope — a prior read
      noted ~21 rows on the axis-census panel before that panel's `attempted_failed` filter fix; the corpus itself was 0
      real objects for its whole lifetime, phantom manifest rows only). Confirm the count live first — if 0, mark this
      todo done-with-nothing-to-retire and move on; if >0, same reversible pattern as above. (repo:
      market-tick-data-service) — **DONE 2026-08-12 (slot 14, data_engineering): `market-tick-data-service@9f5868e5`.**
      The "phantom rows only" premise was FALSE (the 2026-08-04 sample missed `day=2026-05-16..22`): all 21 `captured`
      rows are backed by real subgraph-fee objects (3 pools: CURVE x2 `0x4dece678..`/`0xbebc4478..`, BALANCER x1
      `0x06df3b2b..`, ETHEREUM, `batch_onchain_subgraph`). Content-verified redundant with canonical `dex_pool_state`
      twins on all 7 days (CURVE symbol-named objects `CURVE-ETHEREUM:POOL:USDC-CRVUSD.parquet`/`DAI-USDC-USDT.parquet`
      — `daily_supply_revenue_usd == fees_usd`, volume/tvl identical; the "no CURVE twin" claim in
      `dex_pool_fees_inverted_flip_write_race_2026_08_12.md` was an address-named wrong-vocabulary false negative,
      re-verified live 2026-08-12 slot 14). Operator confirmed retire-all (BLK-9aed224f; the BLK-b118f150 partial-go
      predated the twin content-verification). Applied `retire_dex_pool_fees_all_captured_rows_2026_08_12.py --apply`
      (reversible `captured→attempted_failed`, no row/object deleted): retired the remaining 14 CURVE rows (7 BALANCER
      already retired by slot 20). Consolidator paused pre-write / resumed after (verified ENABLED). Snapshot
      `_index/snapshots/pre_dex_pool_fees_all_retire_<ts>.parquet` + `.dex_pool_fees_all_retire.bak`. Round-trip + fresh
      independent post-apply census: **0 captured `dex_pool_fees` rows; 21 `attempted_failed` (7 BALANCER + 14 CURVE)**
      — done-when met.
- [x] ✅ [DATA] P1. **Resume the consolidator (if not already), trigger a fresh `measure_honest_coverage.py` rollup
      run**, and confirm it completes cleanly (the enumeration-key fix shipped `instruments-service@8b59e8ba2` this
      session must be live in whatever image/VM runs the rollup — verify before trusting output). Launcher:
      `deployment-service/scripts/vm/launch-measure-honest-coverage-vm.sh` or the existing scheduled job, whichever this
      workspace currently uses for on-demand triggers — check the launcher registry rather than guessing. Done-when: a
      new `coverage.json` is written with a timestamp after this todo's retirements. (repo: instruments-service) —
      **DONE 2026-08-12 (slot 14, data_engineering): `instruments-service@4bb2164e`.** Consolidator already ENABLED
      (verified `uts-prod-manifest-consolidator-market-data-defi-cron`). Fresh rollup written
      `gs://central-element-323112-honest-coverage/2026-08-12/coverage.json` (`generated_at=2026-08-12T22:00:38Z`, post
      all retirements) on `measure-honest-coverage-20260812-215144` (e2-highmem-8), launcher VERIFIED terminal SUCCESS.
      Two blocking bugs root-caused + fixed: (1) post-rebuild defi index at 158,267,760 rows OOM'd the default
      e2-highmem-4 (32 GiB) → ran e2-highmem-8 (64 GiB), memory proven sufficient; (2) the 2026-08-11
      `get_storage_client` refactor left `blob.upload_from_string`/`bucket.get_blob` calls that UTL handles no longer
      expose → fixed to `client.upload_bytes`/`client.get_blob_metadata` (`instruments-service@4bb2164e`, the real
      reason 08-11/08-12 cron wrote nothing). Enumeration fix `8b59e8ba2` confirmed live in the VM's tarball
      (`instruments-service-code @ 4bb2164e9491`, contains it). Post-rollup key check: defi `POOL` uppercase,
      `rate_indices`, `dex_pool_fees` all ABSENT from enumerated keys; `lending_indices` present. 5/5 AGs measured,
      `asset_groups_failed: []`.
- [x] ✅ [DATA] P1. **Re-check the Distinct Values panel post-rollup.** Confirm: `dex_pools`/`dex_swaps`/`rate_indices`/
      `dex_pool_fees` no longer appear as non-canonical `data_type`s; `POOL` (uppercase) no longer appears as a
      non-canonical `instrument_type`; venues drop to the genuinely-unresolved set (ASTER/GMX/HYPERLIQUID/EXTENDED/
      LIGHTER + the 24 composite `VENUE-CHAIN` venues, which are CORRECTLY flagged-but-accepted per this epic's prior
      false-alarm investigation, not a bug); `instrument_types` clean modulo the small genuine `<blank>` gap (~58
      `captured` rows, not the ~5.3M raw count — that count is a KNOWN, separately-tracked panel over-report, see
      `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s Todos). Record the live counts in this plan's
      Progress Log. (repo: unified-trading-pm) — **DONE 2026-08-12 (slot 14, data_engineering): panel re-checked against
      the fresh `2026-08-12` rollup (replicating `deployment-api` `enumerate_distinct_values` + `_comparison_set` +
      `_ACCEPTED_EXCEPTIONS` exactly). This plan's OWN retirements CONFIRMED clean: `rate_indices` 0 captured,
      `dex_pool_fees` 0 captured, uppercase `POOL` absent from instrument_types, instrument_types clean modulo the
      single `<blank>` row, chains clean modulo `HYPERLIQUID`. TWO residual non-canonical data_types REMAIN, both
      tracked on their proper issue docs (NOT this plan's scope): `dex_pools` 454,014 captured — the 2026-08-10/11 defi
      rebuild RE-REGISTERED the 2026-08-05-retired rows (new finding on
      `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`, same recurrence class as POOL-uppercase);
      `dex_swaps` 3.46M captured — the genuinely-open separate `[DATA] P2` migration (never retired). Venue axis has the
      expected unresolved set + composites, PLUS legacy `AAVEV3`/`BLAZESTAKE`/`KAMINO_LENDING` (known operator-gated
      purge candidates on the prior epic). Full census in Progress Log.**

## Progress Log

- **2026-08-11 (slot 31, data_engineering) — todo 2 attempted, NOT completed: canonical `pool` population is itself
  mixed, a simple casing-unwrap twin-match is unsafe.** First hit a real OOM (exit 137) using a bare
  `pandas.read_parquet(BytesIO(...), filters=...)` against this manifest (7.16GB raw, 158.3M total rows) — confirmed
  host recovered clean (`free -h`: 28GB available after), then redid every subsequent query via
  `run-bounded-analysis.sh` + DuckDB streaming as todo 1's own note already recommended (should have started there).
  Sampled `instrument_id` shapes for `instrument_type=POOL` (legacy, uppercase) vs `pool` (canonical, lowercase) within
  `data_type=dex_pool_swaps`: **legacy `POOL` is 100% wrapped-form** (`VENUE-CHAIN:POOL:id`, e.g.
  `AERODROME_V3-BASE:POOL:0xf8d5df4d3408acd52a3ff54e8dbce0b3b28aa744`) — ALL 7,930,863 captured rows contain a colon.
  **Canonical `pool` is MIXED**: of ~8.75M captured rows, `contains_colon`=5,361,579 (still carrying the full wrapped
  legacy-shaped id string VERBATIM, uppercase `POOL` token embedded and all — i.e. only the outer `instrument_type`
  column was casing-normalized at some point, the id itself was never re-derived) vs `no_colon`=3,391,479 (genuinely
  bare — hex address or bare symbol pair like `WEETH-WETH-1`). Wrote
  `retire_pool_uppercase_legacy_captured_rows_2026_08_11.py` (`market-tick-data-service@85677ff363`) mirroring the
  sibling scripts' Pass-1/Pass-2 reversible pattern (`captured→attempted_failed`, snapshot-before-write, round-trip
  verify), unwrapping canonical ids to the segment after the last `:` to compare against legacy's bare id — the same
  "wrong vocabulary" pattern `retire_dex_swaps_legacy_captured_rows_2026_08_09.py` already solved for a DIFFERENT
  population. A first isolated DuckDB probe (against a since-superseded manifest snapshot, the consolidator actively
  merges every few minutes) found 0 missing twins across 1,135,962 legacy keys; a full-corpus dry-run minutes later
  against a FRESH download found the opposite — ALL 1,135,962 keys excluded, 0 retirable — illustrating exactly the
  moving-target risk this plan's own `status: draft` rationale warned about, and confirming the population genuinely is
  mixed (not a stale-read artifact): the wrapped-form subset of "canonical" `pool` rows can never match my
  unwrap-last-segment key scheme since they're not actually in bare form. **Did not loosen the matching logic to force a
  match** — that would risk either quietly leaving true duplicates un-retired (harmless) or, worse, misclassifying a
  wrapped-form `pool` row that is NOT truly a duplicate of legacy `POOL` (different real data sharing a
  coincidentally-similar id string) as safe-to-retire, an irreversible-class judgment call on real financial data under
  time pressure — exactly the class of mistake `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`'s Part 2
  (content, not path/label) exists to prevent, even though this is a manifest-status flip rather than a GCS delete. **0
  rows retired, no manifest write executed** — the script's own Pass-1 safety gate is working exactly as designed.
  **What's needed next**: a genuine content-verify pass (read actual swap/price data for a sample of wrapped-form
  "canonical" `pool` rows vs their legacy `POOL` counterpart) to determine whether the wrapped-form `pool` subset is (a)
  a partial, incomplete casing migration that still needs its ids re-derived to bare form before this retirement can
  proceed, or (b) something else entirely. Filed as the blocking gap on the checkbox above rather than a separate issue
  doc — same doc, same todo, narrower scope than a new investigation needs.
- **2026-08-11 (slot 33)**: Todo 1 done. Rebuild VM `canonical-migration-defi-rebuild-20260810-204358` confirmed
  terminal SUCCESS (see checkbox evidence above). Stability-check counts (identical across 3 queries, 17:37:xx →
  17:43:41 UTC): `instrument_type=POOL` (`dex_pool_swaps`) = 7,930,863; `data_type=rate_indices` `captured` = 26,128;
  `data_type=dex_pool_fees` `captured` = 21. These are the baseline pre-retirement counts todo 2-4's workers should
  expect to drive to 0.
- **2026-08-11 (slot 4, data_engineering) — todo 2 still NOT DONE; filed a SECOND, independent blocking finding on top
  of slot-31's content-verify gap.** While researching how to safely resolve slot-31's wrapped-id matching problem,
  traced whether the 7,930,863 uppercase `POOL` rows todo 1 measured are consistent with what's known about this
  population's history — they are not. `defi_cefi_venue_chain_axis_contamination_2026_07_28.md` P3 recorded a
  full-corpus-verified **0** `instrument_type=POOL` rows remaining as of 2026-08-05 (after
  `fold_pool_instrument_type_casing_2026_08_05.py --apply`). Ruled out the two obvious explanations for the 0→7.9M
  regrowth by direct code read (not inference): the only live `record_captured` call site for `dex_pool_swaps`
  pool-grain rows (`_dex_swaps_queries.py:174-182`) passes lowercase `instrument_type="pool"` with a bare id — not a
  regression; and `rebuild_defi_manifest.py::parse_hive_path` unconditionally lowercases `instrument_type`
  (`market-tick-data-service@3f5cc6e4`, shipped 2026-06-18, well before the just-completed rebuild VM chain) — so the
  rebuild's own path-parsing logic shouldn't be able to reproduce this either. **Mechanism for the recurrence is
  UNRESOLVED** — filed as `/plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` (also corrected
  the now-stale P3 "0 remaining, no further action needed" claim in the contamination issue doc, which is directly
  contradicted by this). Retiring the 7.9M rows again without understanding why they came back once already risks the
  same "fixed, then silently reverted" cycle repeating a third time. Did not attempt retirement this session — filed as
  a big finding (data-correctness, SSOT contradiction) per CLAUDE.md's findings-triage rule rather than absorbing an
  open-ended root-cause investigation as unplanned scope on a task scoped to "retire POOL rows." Recommend the
  operator/main review the new issue doc's 3-point verification list before todo 2-4 are attempted again.
- **2026-08-12 (slot 5, data_engineering) — todo 2 done: stale pre-N6a snapshot theory RULED OUT.** Read
  `vm-logs/<vm>/TARBALL_PINS.json` for both VMs in the `-093118`→`-204358` chain (GCS reads via UTL
  `download_from_storage`, per the storage-code HARD RULE): the OOM'd predecessor `-093118` had `MTDS_TARBALL_SHA`
  PINNED to `483eb895581cc645cf884ba780c871b65060202d` (well past N6a); the VM that actually reached terminal SUCCESS,
  `-204358`, had `MTDS_TARBALL_SHA` FLOATING (`"pins": {}`) — no per-deployment record captured the exact commit_sha it
  resolved to at launch (2026-08-10T19:43:58Z), a genuine observability gap in `create-code-tarballs.sh`'s
  floating-tarball path (not fixed here — infra-craft scope, flagged below). Since a floating tarball is built from
  whatever `market-tick-data-service` HEAD is checked out when `create-code-tarballs.sh` last ran, the relevant question
  is whether the N6a lowercasing fix (`market-tick-data-service@3f5cc6e4`, 2026-06-18) was EVER reverted between then
  and the VM's 2026-08-10 launch. `git log 3f5cc6e4..HEAD -- market_tick_data_service/scripts/rebuild_defi_manifest.py`
  lists every commit touching this file in that window (12 commits, none of them touching the `parse_hive_path`
  lowercasing lines); confirmed directly at HEAD (`market-tick-data-service@859405a1`, the tarball commit_sha as of
  2026-08-11T23:00:56Z — after the VM launch, used as the nearest-available content proof): both
  `instrument_type=p["itype"].lower()` call sites in `parse_hive_path` (lines 370, 395) are intact, unconditional,
  unchanged. **Conclusion: no floating-tarball snapshot in the 2026-06-18→2026-08-11 window could have shipped pre-N6a
  code — the stale-snapshot theory from the issue doc's "what I did NOT verify" #1 is RULED OUT.** This narrows the
  still-unresolved recurrence mechanism to the issue doc's remaining two open questions (full-replace vs. upsert;
  physical uppercase GCS objects vs. manifest-column-only) — those are this plan's next two todos, not re-litigated
  here. Updated `/plans/active/issues/defi_pool_uppercase_recurrence_after_fold_2026_08_11.md` to mark this question
  resolved. **Follow-up flagged, not filed as new work** (small, non-blocking, outside this plan's `data_engineering`
  scope): `create-code-tarballs.sh`'s floating-pin path should persist the resolved `commit_sha` into
  `TARBALL_PINS.json` at launch time (mirroring the pinned-tarball case) so a future audit doesn't have to reconstruct
  it from git history — worth an infra-craft todo if this pattern comes up again.
- **2026-08-12 (slot 32, data_engineering) — todo 3 done: the rebuild is UPSERT-onto-existing-index, NOT full-replace.**
  Read `rebuild_defi_manifest.py::main()` → `scan_and_rebuild()`/`_run_chunked()` → `_build_manifest_writer()`, plus the
  UTL `ManifestWriter` per-VM-shard write + reader/consolidator merge paths (direct code reads, not inference):
  - The rebuild's ONLY index write is a per-VM shard: `_build_manifest_writer()` (rebuild_defi_manifest.py:121-136)
    constructs `ManifestWriter(per_vm_shards=True, per_vm_flush_entries=50_000, per_vm_flush_interval_sec=300)`. UTL
    `_writer.py` `per_vm_shards` docstring (lines 131-142): per-VM mode writes to `_index/per_vm/{instance}.parquet`
    "regardless of the bucket-wide flag — guarantees the writer never races the consolidator daemon on the canonical
    `_index/availability_index.parquet`", and "The consolidator (`consolidate_per_vm_shards`) merges per-VM shards into
    the canonical view asynchronously". `_read_index.py::_read_and_merge_per_vm_shards` (line 1347):
    "Last-attempted-write wins per dedup key (matches the consolidator's intended algorithm)". The canonical blob is
    consolidator-owned — the rebuild never rewrites it directly.
  - The rebuild is idempotent/upsert by construction (one `ManifestWriter.add()` per parquet found on disk, CAPTURED;
    module docstring "Safe to re-run" / "OCC-safe via UTL's generation-match"). It only ADDS/updates rows for objects
    its scan finds; it never DELETES or rewrites rows already in the index that its disk scan doesn't touch.
  - **Implication for the POOL recurrence**: `parse_hive_path` lowercases `instrument_type` unconditionally (lines 370 +
    395, N6a), so the rebuild cannot EMIT an uppercase `POOL` row from disk scanning; and because it is
    upsert-onto-existing, it also cannot have REMOVED pre-existing uppercase rows. Therefore the 7,930,863 uppercase
    `POOL` rows must have been PRESENT in the consolidated index BEFORE the rebuild ran (i.e. by the time the `-204358`
    VM's scan/merge landed on 2026-08-10) and passed through untouched. This narrows the unexplained 0→7.9M window from
    "between the 08-05 fold and the 08-11 stability check" to "between the 08-05 fold and the 08-10 rebuild start" —
    either the 2026-08-05 fold's verified '0 POOL remain' did not actually remove all rows, or some writer path
    re-created them in that pre-rebuild window. The rebuild is exonerated as a reintroduction mechanism. Remaining open
    question (todo 4): whether the uppercase rows are manifest-column-only or reflect physical uppercase GCS objects.
- **2026-08-12 (slot 32, data_engineering) — todo 4 done: CONFIRMED manifest-column-only artifact, 0 physical uppercase
  GCS objects.** Sampled 30 manifest rows with `instrument_type=POOL` + `data_type=dex_pool_swaps` +
  `capture_status=captured` across the full date range (2023-01-01 → 2026-08-05), both pipeline_modes
  (`batch_onchain_subgraph` + `batch_onchain_rpc`), 3 chains (ETHEREUM, AVALANCHE, POLYGON), 5 venues (UNISWAP_V2,
  UNISWAP_V3, TRADER_JOE_V2). For each sampled row, derived the expected GCS prefix with both uppercase
  `instrument_type=POOL/` and lowercase `instrument_type=pool/`, then listed blobs at each prefix via UTL
  `storage.list_blobs()` (per the storage-code HARD RULE, never subprocess `gsutil`). Result: **0/30 rows have any
  objects at the uppercase `POOL/` path; 30/30 have objects at the lowercase `pool/` path.** A broad scan across 5
  additional dates (2023-06-15, 2024-01-15, 2024-06-15, 2025-01-15, 2025-06-15) found **0 total objects** containing
  `instrument_type=POOL/` anywhere in their GCS path name. **Conclusion: this is a manifest-column-only artifact.** The
  2026-08-05 fold's assumption is correct — the physical GCS objects are all at correctly-lowercase
  `instrument_type=pool/` paths; no Part-5 "legacy COPIED not MOVED" migration treatment is needed. The retirement
  todo's only remaining blocker is slot-31's wrapped-id content-verify gap (the manifest-only fix is safe from a
  physical-path perspective). Pipeline_mode distribution of the 7,930,863 POOL rows: `batch_onchain_subgraph` 4,025,328
  (2023-01-01..2026-08-05), `batch_onchain_rpc` 3,905,535 (2023-01-04..2026-04-19).
- **2026-08-12 (slot 7, data_engineering) — todo 5 DONE: POOL (uppercase) retirement applied + independently verified (0
  remaining captured `instrument_type=POOL`).** Resolved the two blockers prior slots flagged: (1) slot-31's
  content-verify gap, and (2) slot-31's script key-vocabulary bug. Full evidence:
  - **Key-vocabulary bug root-caused**: `retire_pool_uppercase_legacy_captured_rows_2026_08_11.py`'s dry-run matched 0
    of 1,135,962 legacy keys because `_keys()` unwrapped ONLY the canonical side (`unwrap_canonical_id=True`) while
    leaving legacy `POOL` keys in FULL wrapped form (`unwrap_canonical_id=False`) — legacy wrapped
    `VENUE-CHAIN:POOL:0xabc` vs canonical bare `0xabc` never intersect. Legacy `POOL` is 100% wrapped-form; canonical
    `pool` is mixed (wrapped + bare). Fixed to unwrap BOTH sides to the last-colon segment. Verified live via DuckDB
    (fresh consolidated index, 2026-08-12): 1,122,141 of 1,135,962 distinct legacy keys (98.8% of the 7,930,863 captured
    rows) have a canonical `pool` twin; 13,821 keys (96,541 rows) have none.
  - **Content-verify passed**: for sampled matched pairs, the canonical `pool` row's physical object exists at
    `instrument_type=pool/data_type=dex_pool_swaps/` with real swap columns (verified content), and legacy rows are
    per-timeframe (15s/1m/5m/15m/1h/4h/1d) manifest duplicates of the same cell; no-twin legacy rows' physical objects
    also exist at lowercase `pool/` paths (probed 8/8 sampled) — real data, so they are FOLDED (never retired).
  - **Two-bucket apply** (mirrors `fold_pool_instrument_type_casing_2026_08_05.py`): RETIRED 7,834,322 twin-having
    legacy `POOL` rows (`capture_status` `captured→attempted_failed`,
    `error_reason=superseded_by_content_verified_ canonical_pool_lowercase_twin_2026_08_11`) and FOLDED 96,541 no-twin
    rows (`instrument_type` `POOL→pool`, status kept `captured`, id untouched).
    `uts-prod-manifest-consolidator-market-data-defi-cron` paused (verified PAUSED) before the write, resumed (verified
    ENABLED) after. Snapshot `_index/snapshots/pre_pool_uppercase_retire_2026_08_12T131625Z.parquet` +
    `_index/availability_index.parquet .pool_uppercase_retire.bak` streamed via `storage.upload_file` (the 6.8GB index
    is never materialised in memory — whole-file `read_bytes`+`upload_bytes` OOMs the shared host). Round-trip verify
    inside the apply returned 0 remaining captured `POOL` rows; independent post-apply fresh query confirmed the same:
    `POOL` attempted_failed= 7,841,381, `pool` captured=8,849,599 (incl. the 96,541 folded). Script shipped
    `market-tick-data-service@5e456d0d`.
  - **Recurrence note**: the 0→7.9M recurrence mechanism (issue `defi_pool_uppercase_recurrence_after_fold_2026_08_11`)
    remains ROOT-CAUSE-UNRESOLVED after the three checks the issue doc recommended (stale-snapshot ruled out, rebuild
    upsert-onto-existing exonerated, physical-uppercase-objects ruled out — manifest-column-only). This retirement
    achieves the done-when for the current population; if the underlying writer/reconsolidation path re-emits uppercase
    `POOL` rows again, that issue doc is the tracking point for a durable fix. Notably the legacy rows' `written_at`
    timestamps (2026-08-10T03:52-03:53Z, during the rebuild VM window) and `service_name=market-data-processing-service`
    differ from canonical `pool` rows (`market-tick-data-service`) — flagged as a lead for that issue doc's eventual
    root-cause, not investigated further here (bounded task scope).
- **2026-08-12 (slot 20, data_engineering) — todo 6 DONE: `rate_indices` retirement applied + independently verified (0
  remaining captured `rate_indices`).** Pre-apply census (memory-safe DuckDB over the fresh consolidated index):
  `data_type=rate_indices` `captured` = 26,128 — AAVE_V3/ETHEREUM 3,160 (bare symbol ids `WETH`/`USDC`/`DAI`/`USDT`) +
  MORPHO/ETHEREUM 22,968 (wrapped `MORPHO-ETHEREUM:LENDING_MARKET:{sym}:0x{short}` ids). Established the venue-aware key
  vocabulary the retirement uses (this task's slot-31-style "wrong vocabulary" trap): `0x`-short legacy ids prefix-match
  the canonical full-address (`0x<64hex>` / `MORPHO-ETHEREUM:LENDING:0x<64hex>`) while bare-symbol legacy ids
  exact-match (`usdt` vs the distinct `usdt.e` market — a prefix match would false-flag ambiguity).
  - **Fold-gap finding (data-correctness, resolved in-band)**: the 2026-08-07 fold is NOT "100% complete" on the
    manifest side. 22 MORPHO markets (650 cells) have fold-written canonical GCS objects under
    `MORPHO-ETHEREUM:LENDING:{sym}-0x{short}` for **both** `batch_onchain_rpc` and `batch_onchain_subgraph`, but the
    fold's manifest registration only recorded the SUBGRAPH twin — the RPC canonical rows were never registered, so the
    legacy `rate_indices` row was the only captured manifest record. Verified via the pre-apply snapshot
    (`_index/snapshots/pre_rate_indices_retire_20260812T144912Z.parquet`: wstETH-WBTC had only the subgraph row). GCS
    probes confirmed every one of the 650 rpc objects exists (`blob_exists` 650/650).
  - **Three-bucket apply** (`retire_rate_indices_legacy_captured_rows_2026_08_12.py --apply`): RETIRE 25,478
    twin-verified rows (`capture_status` `captured→attempted_failed`,
    `error_reason=superseded_by_content_verified_canonical_lending_indices_twin_2026_08_12`); FOLD 650 no-twin rows
    in-place (`data_type` `rate_indices→lending_indices`, `instrument_id` re-keyed to
    `MORPHO-ETHEREUM:LENDING:{sym}-0x{short}`, `capture_status` kept `captured` — the physical object already exists at
    that path); EXCLUDE 0. Consolidator cron paused before write / resumed after. Snapshot + `.rate_indices_retire.bak`
    streamed to `_index/` pre-write (the 6GB index is never materialised in memory).
  - **Independent post-apply verify**: `rate_indices` `captured` = **0** (done-when met), `attempted_failed` = 25,478;
    `lending_indices` `captured` 385,050→385,700 (**+650 = the folded rows exactly**); the folded rows appear as
    `MORPHO-ETHEREUM:LENDING:wstETH-WBTC-0x3197ba` etc. on their legacy dates; no true duplicates introduced (the
    rpc-vs-subgraph pairs for the 650 are separate shard atoms — `pipeline_mode` is part of the shard atom — and the
    group-by-having duplicate scan found none at the (…, pipeline_mode) level).
  - **Residual note for todo 7 (dex_pool_fees)**: its count is unchanged at 21 `captured` rows on the axis census; this
    todo did not touch `dex_pool_fees`.
- **2026-08-12 (slot 20, data_engineering) — todo 7 NOT RETIRABLE AS PLANNED: the phantom-rows premise is FALSE; 21 real
  `dex_pool_fees` objects exist (day=2026-05-16..22) and the reversible flip would mislabel real data.** Ran the
  retirement script's dry-run census (`retire_dex_pool_fees_legacy_captured_rows_2026_08_12.py`, mirror of the
  rate_indices pattern) over the fresh consolidated index: `dex_pool_fees` `captured` = **21** (baseline confirmed). Its
  physical-object safety probe classified **RETIRE 0 / EXCLUDE 21** — every captured row is backed by a real parquet
  object at `data_type=dex_pool_fees/` for 3 pools (CURVE x2 `0x4dece678..`/`0xbebc4478..`, BALANCER x1 `0x06df3b2b..`)
  × day=2026-05-16..22, `batch_onchain_subgraph`, chain ETHEREUM. Content read (CURVE 05-16): `fees_usd=371.3`,
  `volume_usd=7,426,451`, `tvl_usd=23,787,341` — real subgraph fee/volume/TVL data, `available_at=2026-06-21`
  (materialised 2026-06-21, i.e. the 2026-08-04 "0 objects for its lifetime" sample missed the mid-May window). Rows
  (re)registered `captured` by the 2026-08-10 rebuild scan (`written_at=2026-08-10T23:08-23:10Z`,
  `service_name=market-tick-data-service`). Twin analysis: BALANCER has a canonical `dex_pool_state` twin on all 7 days
  (`swap_fees`) → retire-as-superseded feasible after content-verify; **CURVE has NO `dex_pool_state` twin on any day**
  → its fee data may be the only copy. Filed
  `/plans/active/issues/dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md` (data-correctness
  finding, options A/B/C/D) + `/blocked` to the operator. No manifest write made; the retirement script ships as the
  template for the decided disposition (needs twin-verify or migration logic before `--apply`).
- **2026-08-12 (slot 14, data_engineering) — todo 7 DONE: all 21 `dex_pool_fees` rows retired (0 captured / 21
  attempted_failed).** Resolved the write-race aftermath + the two issue docs' conflicting twin claims by live
  measurement (see the checkbox evidence above for the full trail).
  - **Ground-truth probe (2026-08-12, slot 14)**: fresh DuckDB census + GCS object probe over the live consolidated
    index confirmed the CURRENT state (post slot-20's `d2014c87` corrective flip) was **14 CURVE `captured` + 7 BALANCER
    `attempted_failed`**. Then content-read the canonical symbol-named CURVE `dex_pool_state` object
    `CURVE-ETHEREUM:POOL:USDC-CRVUSD.parquet` (day=2026-05-16): `daily_supply_revenue_usd=371.32`,
    `volume_usd=7,426,451`, `tvl_usd=23,787,340` — EXACTLY matching the legacy `dex_pool_fees` object's
    `fees_usd=371.32`/`volume_usd`/`tvl_usd`. The canonical ADDRESS-named path does NOT exist (NotFound) — confirming
    the inverted-flip issue doc's "phantom CURVE twin / only copy" claim was the SAME address-named wrong-vocabulary
    false negative slot 32 already corrected. **The CURVE rows are content-redundant with canonical `dex_pool_state` —
    retiring them loses nothing.**
  - **Disposition confirmed retire-all-21**: the operator's BLK-9aed224f (recorded in
    `dex_pool_fees_phantom_premise_false_real_mid_may_objects_2026_08_12.md`) explicitly retired all 14 CURVE rows after
    slot 32's content-verification; the interim BLK-b118f150 partial-go the main-agent guidance message cited predated
    that content-verification and its premise was disproven by this slot's live probe. Applied
    `retire_dex_pool_fees_all_captured_rows_2026_08_12.py --apply` (reversible status flip only, no row/object deleted;
    `market-tick-data-service@9f5868e5`): retired the remaining 14 CURVE rows → **0 captured / 21 attempted_failed** (7
    BALANCER + 14 CURVE). Consolidator paused pre-write (verified PAUSED) / resumed after (verified ENABLED). Snapshot
    `_index/snapshots/pre_dex_pool_fees_all_retire_*.parquet` + `.dex_pool_fees_all_retire.bak` written pre-write.
    Round-trip verify (0 remaining captured) + independent fresh post-apply census both confirm the terminal state.
  - **Issue-doc reconciliation**: `dex_pool_fees_inverted_flip_write_race_2026_08_12.md` todo-1 (the corrective flip
    that restored 14 CURVE to captured) was based on that disproven "only copy" premise — the CURVE restoration is now
    re-retired by this todo's apply, and the doc's premise is corrected below. The phantom-premise doc's P2 (correct the
    "0 objects" claim in the archived recommendation + this plan's premise) remains its own tracked todo.
- **2026-08-12 (slot 14, data_engineering) — todo 8 DONE: fresh `measure_honest_coverage.py` rollup written +
  verified.** Full trail:
  - **Pre-flight**: consolidator `uts-prod-manifest-consolidator-market-data-defi-cron` already ENABLED (resumed); no
    running honest-coverage VM (singleton lock free); latest prior `coverage.json` was `2026-08-10 00:37` — genuinely
    stale vs the 2026-08-12 retirements.
  - **Attempt 1 (e2-highmem-4 / 32 GiB, `measure-honest-coverage-20260812-211215`) → OOM (exit 137)**: run.log shows
    cefi (27.8M rows) completed, then defi manifest SELECTED at **158,267,760 rows** (post-rebuild) was `Killed`. The
    08-10 00:37 success predated the defi rebuild (`canonical-migration-defi-rebuild-20260810-204358`); the post-rebuild
    defi index no longer fits in 32 GiB. This is the SAME tracked OOM class
    (`honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md`) — and notably there was **no coverage.json for 08-11
    or 08-12** in the bucket: the daily cron had silently failed since the rebuild landed.
  - **Attempt 2 (e2-highmem-8 / 64 GiB + `--oom-monitor`, `measure-honest-coverage-20260812-212755`) → computed ALL 5
    asset groups cleanly (memory fix proven), then crashed on the FINAL WRITE**: `_write_output`'s
    `blob.upload_from_string(...)` — `AttributeError: 'GCSBlobHandle' object has no attribute 'upload_from_string'`,
    exit rc=1. Same-class warn-only regression in `_get_blob_updated`
    (`'GCSBucketHandle' object has no attribute 'get_blob'`). **Root cause: `instruments-service@02cc9055` (2026-08-11,
    "replace google.cloud/boto3 imports with get_storage_client across scripts tier") swapped the import but left
    google.cloud-style method calls on the UTL handles.** This is the definitive explanation for the 08-11/08-12 missing
    cron output — even with enough memory, the rollup computed but could never write.
  - **FIX SHIPPED `instruments-service@4bb2164e`**: `_write_output` →
    `client.upload_bytes(_OUTPUT_BUCKET, f"{run_date}/coverage.json", blob_bytes, content_type="application/json")`;
    `_get_blob_updated` → `client.get_blob_metadata(...)` with `datetime.fromisoformat(metadata.last_modified)` (UTL
    `BlobMetadata` is ISO-8601 UTC). Test updated (`upload_bytes` assertion). 44/44 honest-coverage tests pass incl. the
    enumeration-key attempted_failed exclusion test. Full QG green, quickmerge `--agent` landed, `4bb2164e` verified on
    origin.
  - **Attempt 3 (e2-highmem-8, `measure-honest-coverage-20260812-215144`, tarball `instruments-service @ 4bb2164e9491`)
    → SUCCESS**: launcher VERIFIED `gs://central-element-323112-honest-coverage/2026-08-12/coverage.json` written fresh
    post-launch (exit 0). `generated_at=2026-08-12T22:00:38Z` — after all retirements. 5/5 AGs measured,
    `asset_groups_failed: []`. **Post-rollup enumeration-key check** (the drift-panel-relevant surface): defi
    instrument_types do NOT include uppercase `POOL`; defi data_types do NOT include `rate_indices` or `dex_pool_fees`;
    `lending_indices` IS present. Done-when met.
  - **Finding triaged**: both root causes (post-rebuild 32 GiB OOM + the `02cc9055` write-path regression) appended to
    the open `honest_coverage_daily_vm_oom_all_asset_groups_2026_08_08.md` issue doc's Progress Log — the write-path
    regression is the cross-cutting fix this slot shipped; the machine-type bump for the daily cron remains the
    operator-gated decision in that doc (this run used an explicit `--machine-type e2-highmem-8` override, not a
    launcher-default change).
- **2026-08-12 (slot 14, data_engineering) — todo 9 DONE: Distinct Values panel re-checked against the fresh
  `2026-08-12` rollup; live census recorded.**
  - **Method**: replicated `deployment-api` `_distinct_values.enumerate_distinct_values` + `_comparison_set` +
    `_ACCEPTED_EXCEPTIONS` exactly (imported UAC canonical sets `InstrumentType` / `DATA_TYPES_BY_ASSET_GROUP['defi']` /
    `ALL_DEFI_VENUES` bare-bases / `MAINNET_CHAIN_IDS`; `_BLANK_SENTINELS` collapse; the defi instrument_type casefold
    - defi venue bare-base comparison rules) against the fresh `coverage.json` (`generated_at=2026-08-12T22:00:38Z`).
      This IS the endpoint's computation — the panel reads only this rollup's by_venue*/by_chain keys.
  - **Census (defi)**:
    - **instrument_types**: 16 distinct, 1 non-canonical = `<blank>` only. No uppercase `POOL`. **CLEAN** ✓
    - **data_types**: 31 distinct, 2 non-canonical = `dex_pools`, `dex_swaps`. `rate_indices` + `dex_pool_fees` ABSENT
      (0 captured). `lending_indices` present.
    - **chains**: 23 distinct, 1 non-canonical = `HYPERLIQUID`.
    - **venues**: 105 distinct, 34 non-canonical — the expected unresolved set (ASTER/GMX/HYPERLIQUID/EXTENDED/LIGHTER)
      - the VENUE-CHAIN composites (CORRECTLY flagged-but-accepted per this epic's prior false-alarm investigation) + 3
        legacy operator-gated purge candidates (`AAVEV3`, `BLAZESTAKE`, `KAMINO_LENDING` — tracked on
        `defi_distinct_values_zero_noncanonical_dispatch_2026_08_04.md`'s row-11 `[OPERATOR]` purge item, NOT this
        plan).
  - **FINDING — `dex_pools` legacy data_type is BACK at full pre-retirement population (454,014 captured), re-registered
    by the 2026-08-10/11 defi rebuild**: ORCA 450,976 + RAYDIUM 3,038, all `captured`, 0 `attempted_failed`. The
    2026-08-05 retirement's terminal state was 29 captured / 453,985 attempted_failed — the rebuild's disk scan re-added
    every legacy `dex_pools` physical object as captured. Same recurrence mechanism as the POOL-uppercase recurrence:
    **a capture_status-flip retirement whose legacy GCS objects still exist is undone by the next
    `rebuild_defi_manifest.py` scan.** This is why the 08-12 POOL retirement achieved 0 POOL (no physical uppercase
    objects existed — manifest-column-only) while `dex_pools` re-appeared (real physical objects exist at the legacy
    path). **Filed on `defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`** (the proper tracker) with
    the implication that the still-open `dex_swaps` migration requires the object-level/rebuild-skip fix for durability,
    not just a manifest flip. Not executed here (bounded task scope).
  - **`dex_swaps` residual**: 3.46M captured — this is the genuinely-open separate `[DATA] P2` migration
    (`defi_legacy_data_type_names_manifest_migration_scope_2026_08_04.md`), NOT this plan's scope, correctly untouched.
  - **Panel verdict**: this plan's three retirements (POOL uppercase, rate_indices, dex_pool_fees) all landed and the
    panel reflects them; the two remaining non-canonical data_types are pre-existing/tracked elsewhere, not regressions
    from this plan's work.
