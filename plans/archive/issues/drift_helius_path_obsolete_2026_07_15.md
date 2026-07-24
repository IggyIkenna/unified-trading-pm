---
doc_type: issue
title: DRIFT V2 Helius sig-walker path is obsolete — ruling confirmed, migrate to Velocity Data API
summary: >
  Consolidated finding + operator/main ruling for whether DRIFT `perp_funding`/`perp_trades` backfill should abandon the
  Helius sig-index/day-walker path (`mtds-drift-sig-walker-*` + `mtds-solana-drift-backfill`) for the already-shipped
  Velocity Data API ingester (`backfill_drift_v2_historical.py`, `market-tick-data-service@0f70f376`). Main ruled **A —
  migrate** (2026-07-15, consistent across BLK-ba6c367c / BLK-5d122841 / BLK-6067d459). Sequencing per main: (1)
  verify-first, (2) stop/do-not-relaunch the Helius fleet, (3) wire an existing launcher to the Velocity path (never
  hand-roll a VM name), (4) reconcile the DRIFT `perp_funding` manifest, (5) consolidate follow-up here. This doc covers
  step (1) — DONE, with one real bug found + fixed in the process — and tracks (2)-(4) as open todos. Original incident
  doc (the Helius OOM crash itself) is `drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md`; this doc is the
  single consolidation point for the obsolescence/migration finding per main's instruction — don't duplicate.
status: superseded
nature: notes
asset_group: [defi]
stage: [data]
repos: [market-tick-data-service, deployment-service, instruments-service]
scope: [engineer, admin]
tags: [correctness, efficiency, drift, sig-index, helius, velocity-api, migration, pipeline-mode]
related:
  [
    issues/drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md,
    issues/drift_v2_sig_index_parts_cache_full_download_2026_07_15.md,
    issues/manifest_index_read_oom_canonical_cache_2026_06_24.md,
    plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md,
    /codex/04-architecture/drift-v2-data-sources.md,
  ]
created: 2026-07-15
parent_epic: defi_master
priority: P0
source: [drift_v2_sig_index_program_wide_helius_oom-005, data_engineering slot-2]
assigned_vm: planning
resolved_by:
locked_by:
execution_scope: orchestrator-agent
drift_direction: advance-code
depends_on: []
last_updated: 2026-07-15
locked_since:
---

> 🔴 **SUPERSEDED (2026-07-16, operator ruling, verbatim):** "kill drift entirely from our whole system it's pointless —
> Jupiter is the main one let's just use that. kill all other solana perp dex's. uac, code, adaptors, manifest, gcs,
> everything. no instruments no mvp nothing." The DRIFT venue this doc's finding concerns has been **removed entirely**
> (Drift was hacked ~$280M on 2026-04-01, rebranded to Velocity DEX 2026-07-01, now a ~2-week-old private beta with ~$0
> listed TVL) — all Solana perp DEXes are dropped except Jupiter (not integrated). This doc's finding/fix is now moot;
> kept for historical record only. SSOT for the removal: `/codex/04-architecture/solana-defi-coverage.md` (tombstone
> banner).

# DRIFT V2 Helius path obsolete — migration ruling + verify-first (2026-07-15)

## Ruling (main, 2026-07-15)

**Option A confirmed** via `/blocked` `BLK-ba6c367c` (slot-2), consistent with the SAME ruling given independently on
`BLK-5d122841` + `BLK-6067d459` this session. Abandon the Helius sig-index path entirely; switch DRIFT `perp_funding`
backfill to the shipped Velocity API ingester (`backfill_drift_v2_historical.py`, `mtds@0f70f376`). Grounded in
`/codex/04-architecture/drift-v2-data-sources.md` (`status: current`, created 2026-06-01) — it explicitly declares the
Helius sig-walker path OBSOLETE (intractable ~6.4M sig/day wall) and names Velocity as canonical. Option B's premise (a
known reason Velocity was rejected) is **false** per the SSOT.

Main's sequencing:

1. **VERIFY-FIRST** — run the Velocity ingester on one market-day, confirm canonical UAC rows land (manifest-verified)
   BEFORE stopping anything.
2. Stop/do-not-relaunch the `mtds-drift-sig-walker-*` SPOT fleet + `mtds-solana-drift-backfill` (protective — stops the
   OOM path + Helius spend).
3. Grep `VM_PREFIX_TO_BUCKET` before wiring a launcher — reuse an existing `launch-*.sh`, don't hand-roll a name.
   Backfill VMs default SPOT.
4. Reconcile DRIFT `perp_funding` manifest cells once Velocity is capturing.
5. Fold into this single issue doc — don't duplicate — and note the Helius-OOM plan/doc is superseded by Velocity so
   sibling tasks redirect here.

## Step 1 — VERIFY-FIRST: DONE, with one real bug found + fixed

### Pre-ruling API-level verification (data_engineering slot-2, before the ruling)

Live-probed `https://data.api.drift.trade` (read-only, no code) against the actual backfill gap's real dates —
2025-01-09 (the OOM-crash date), 2025-01-15/2025-12-23 (gap bounds per `mvp_backfill_defi_onchain_v10` G1.5), plus 3
other historically-volatile days. Funding: exactly 24 rows/day, matches docs, all 6 dates. Trades: **the walker's own
logged cost on 2025-12-23 was 1,720,013 program-wide Helius sigs / 17,207 batches / 200 minutes** (v10 plan line 1085) —
the SAME date via Velocity returns only **20,290 actual SOL-PERP trades, an ~85x reduction**. CSV parses cleanly with
pandas (34 cols, 0 nulls, all covered by the canonical rename map). No 429s under a 10-request burst. Full detail in
`drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md`'s P0 todo (this doc doesn't repeat it — see `related`).

### Code-execution verification (data_engineering slot-2, after the ruling)

Ran
`backfill_drift_v2_historical.py --markets SOL-PERP --start 2025-01-09 --end 2025-01-09 --data-types funding,trades --run-tag batch`
for real against production GCP (`central-element-323112`), twice.

**Bug found and fixed**: `DriftV2HistoricalIngester._write_parquet()` called `write_defi_rows()` without an explicit
`pipeline_mode`, so the write path fell through to the generic `(asset_group, data_type)` `SOURCE_PRIORITY` derivation —
which has no DRIFT-specific entry — and silently wrote the GCS object under `pipeline_mode=batch_hyperliquid` while
`record_captured()` stamped the manifest as `batch_onchain_rpc`. A **shard-atom-identity violation** (writer and
manifest partition path disagree) — confirmed on both the pre-existing legacy Helius-path file at the same location
(this bug is NOT new to the Velocity migration; it's a pre-existing gap in this handler that predates today, affecting
both paths identically) and my own first test write. No existing test caught it because
`tests/unit/test_drift_v2_historical_handler.py` mocks `_write_parquet` as a noop for the manifest-emission tests, so
the real partition-path construction was never exercised.

**Fix**: pass `pipeline_mode=PipelineMode.BATCH_ONCHAIN_RPC.value` explicitly in `_write_parquet()`, matching what
`record_captured()` already stamps. Added
`TestWritePathPipelineMode.test_funding_write_stamps_batch_onchain_rpc_not_hyperliquid` (asserts the real, unmocked
`write_defi_rows()` partition path). Extracted `_rows_with_symbol()` to keep `_write_parquet()` under the 50-line
method-size gate. Full `quality-gates.sh` green (sentinel `0a0374d2`), shipped `market-tick-data-service@1bd507b4`
(`--files`-scoped quickmerge).

**Post-fix confirmation**: re-ran for the same day — funding (24 rows) landed at
`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2025-01-09/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=DRIFT/chain=SOLANA/instrument_type=perpetual/data_type=perp_funding/SOL-PERP.parquet`
and trades (17,223 rows — matches the pre-ruling API probe's 17,219 within normal count drift) landed at the equivalent
`data_type=perp_trades` path. Both counts match live API probing; both land at the CORRECT (manifest-matching) path.
Deleted the one pre-fix test artifact I had written under the wrong `batch_hyperliquid` path (my own artifact, no
manifest entry, orphaned).

### Caveat found during verify-first: shared manifest-index-read OOM (NOT a new bug)

Both local runs' RSS climbed sharply (10-20GB) **after** the parquet write completed successfully, during
`recorder.record_captured()` / manifest close — twice on this shared interactive host, the second time even with
`MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` set (documented Option C mitigation didn't visibly prevent it here; worth
re-checking that env var's actual plumbing). **This matches the already-filed, separately-owned**
`manifest_index_read_oom_canonical_cache_2026_06_24.md` (P2, `parent_epic: manifest_master`) — the slow-path
`_read_and_merge_per_vm_shards` fallback holding 4-5x copies of the consolidated DeFi index in `_CANONICAL_CACHE`, which
that doc's own text says is "unblocked OPERATIONALLY by running on e2-highmem-8." **Not a new Drift-specific defect** —
any DeFi handler (old Helius path included) hits the same wall under a stale local/consolidated index. I killed both
runs (`kill -TERM`) before they could OOM this shared host (free memory dropped to 367MiB at the worst point) rather
than let them run to completion here.

**Implication for step 2/3 below**: whatever VM re-routes to the Velocity path (existing `mtds-solana-drift-backfill`
launcher, reused per main's step 3) should follow the SAME operational mitigation already used for other DeFi backfills
— e2-highmem-8, not the default e2-standard-4 — until `manifest_index_read_oom_canonical_cache_2026_06_24.md` lands its
durable fix. This is not new scope; it's an existing, tracked constraint that now also applies to Drift.

## Remaining todos (steps 2-5, NOT done this session — scoped for follow-up)

- [x] ✅ [INFRA] P0. Stop/do-not-relaunch `mtds-drift-sig-walker-*` (both parts + gap walkers) and
      `mtds-solana-drift-backfill` — protective, stops the OOM path + Helius API spend. Verify via
      `gcloud compute     instances list` (project `central-element-323112`) before/after. (repo: deployment-service /
      GCP console) — `deployment-service@46d6492`: verified 0 instances running/present under either prefix in any state
      (project `central-element-323112`) via `aggregated_list_instances` — the sandboxed `gcloud` CLI is snap-confined
      here (`cap_dac_override` missing), so listing went through UTL's `get_compute_engine_client` instead — so there
      was nothing live to stop. Flipped `mtds-drift-sig-walker-` to `None` in
      `deployment_service/data_pipeline_monitors/launcher_registry.py` so the self-heal actuator escalates to
      `file_issue` instead of auto-relaunching the retired Helius path (permanent — Option A abandons that path
      entirely). `mtds-solana-drift-backfill` was left mapped to its launcher: todo 2 below landed concurrently
      (`ee859e43`, slot-6) while this task was in flight, re-routing `launch-mtds-solana-drift-backfill-vm.sh` to the
      Velocity ingester — the Helius-spend concern that would have justified disabling it here no longer applied, so
      auto-relaunch of a stalled, correctly-routed backfill stays enabled. Guard test
      `tests/unit/test_launcher_registry.py` (7/7) + full `quality-gates.sh` green.
- [x] ✅ [INFRA] P0. Re-route `mtds-solana-drift-backfill`'s launcher (`launch-mtds-solana-drift-backfill-vm.sh`,
      already registered in `VM_PREFIX_TO_BUCKET` — reuse it, do not hand-roll a new name) to invoke
      `backfill_drift_v2_historical.py` instead of the legacy `solana_defi_handler.py` Helius path (`VM_TASK` routing
      lives in `setup-data-pipeline-vm.sh` ~line 1410/1243). **Provision e2-highmem-8, not the default e2-standard-4**,
      per the manifest-index-OOM caveat above. Backfill VMs default SPOT per CLAUDE.md. (repo: deployment-service) —
      `deployment-service@ee859e4`: `setup-data-pipeline-vm.sh`'s `solana-drift-backfill` VM_TASK branch now invokes
      `python -m market_tick_data_service.scripts.backfill_drift_v2_historical --markets --data-types --start --end`
      (VM_DATA_TYPES defaults `funding;trades`); launcher `MACHINE_TYPE` default changed to `e2-highmem-8`. SPOT default
      unchanged (already SPOT). QG green, dry-run verified (`Machine: e2-highmem-8`), module import path confirmed.
- [x] [DATA] P1.1. Reconcile the 2025-01-09 SOL-PERP shard — DONE (data_engineering slot-7, 2026-07-16). See Progress
      Log.
- [x] ✅ [INFRA] P1. Launch the re-routed `mtds-solana-drift-backfill` VM (Velocity path, `deployment-service@ee859e4`)
      at scale over the real backfill gap (`2025-01-15`–`2025-12-23` per `mvp_backfill_defi_onchain_v10` G1.5) — reuse
      `launch-mtds-solana-drift-backfill-vm.sh` (already registered in `VM_PREFIX_TO_BUCKET`, do not hand-roll a new
      name), `e2-highmem-8`, SPOT default per CLAUDE.md. Both prereq todos (1, 2 above) are landed — this is the missing
      "actually run it" step P1.2 below needs; without this todo P1.2's park-behind-prereq has no gate to open. On
      completion: flip `drift_velocity_backfill_running_at_scale` (`POST /api/prerequisites/...` `{value: true}`) so
      P1.2 unparks. (repo: deployment-service) — done 2026-07-16 (infra slot-2). See Progress Log.
- [x] ✅ [DATA] P1.2. Reconcile the broader `attempted_failed`/`expected_unattempted` cells currently under the old
      Helius path once Velocity is capturing at scale — root cause found + fixed: `unified-api-contracts@5fd781c7`. See
      Progress Log for the full finding; follow-up materialization todo P1.3 added below (real production write, needs
      its own scoped dispatch, not absorbed into this task per findings-triage discipline).
- [x] ✅ [DATA] P1.3. Materialize the DRIFT `perp_trades` `expected_unattempted` catalog rows now that the registry gap
      (P1.2) is fixed — done 2026-07-16 (data_engineering slot-15), with one real scoping gotcha found + worked around.
      **The todo's own assumption was wrong**: `--data-types perp_trades` does NOT naturally scope to DRIFT only — an
      unrelated, already-known-but-under-scoped bug (`A_TOKEN`/`DEBT_TOKEN` lending tokens unmapped in
      `unified_api_contracts.registry.market_data_categories._INSTRUMENT_TYPE_ALIASES`, same class as the LST finding in
      `defi_expected_unattempted_backlog_1m_2026_07_03.md`) makes the CLI's `--data-types` override leak onto every
      unmapped instrument across the WHOLE defi catalogue — a plain unfiltered run produced 7,357,031 candidates, not
      the expected ~51k. Root-caused, evidenced, and added as a fix todo to that existing issue doc (not duplicated
      here) rather than fixed inline — the shared alias table is also consumed by `possible_manifest.is_valid_shard_key`
      (orphan-sweep/phantom-reconciler), too wide a blast radius for this task. **Worked around it instead**: a
      standalone one-off script (reuses `enumerate_v2`/`_write_absent_rows` verbatim, not committed) filtered the
      candidate rows to `venue == "DRIFT"` before writing — 250,937 DRIFT-only rows written
      (`_index/per_vm/enum-drift-perp-trades-materialize-1784165794.parquet`, durably verified by direct read-back: 100%
      `venue=DRIFT`/`data_type=perp_trades`, `pipeline_mode=batch_onchain_rpc` matching the P1.2 fix, 107,760
      `expected_unattempted` + 143,177 `empty_confirmed`). See Progress Log for the full finding.
- [x] ✅ [DATA] P2. Once (2)-(4) land, add a banner to `drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md` and
      `mvp_backfill_defi_onchain_v10_2026_06_27.md` noting the Helius sig-walker path is retired in favor of Velocity,
      and close out that doc's remaining `[INFRA] P2` (zombie-VM monitoring) and `[DATA] P3` (relaunch) todos as
      superseded/moot. — **done 2026-07-16 (data_engineering slot-15)**. See Progress Log.

## Progress Log

### 2026-07-16 — data_engineering slot-15: materialized DRIFT perp_trades expected_unattempted rows (P1.3)

Picked up `drift_helius_path_obsolete-006` (P1.3). Fresh-pulled clean. Verified the DeFi catalog parquet
(`gs://instruments-store-defi-prd-central-element-323112/prod/catalog.parquet`, 1.24MB, updated 2026-07-15) and ran a
scan-only dry run per the todo's instruction.

**Found the todo's scoping assumption was wrong.**
`--asset-group defi --data-types perp_trades --catalog-path <full catalog>` (scan-only, uncapped) produced **7,357,031
candidate rows**, not the expected ~51k order of magnitude. Traced the cause:
`unified_api_contracts.registry.market_data_categories._INSTRUMENT_TYPE_ALIASES` doesn't map `a_token`/ `debt_token`
(the literal catalogue instrument_type tokens for AAVE_V3/MORPHO/FLUID/SPARK/VENUS/SOLEND lending positions) to the
canonical `lending` type, so `valid_data_types_for_instrument_type` returns `None` (unmapped) for them, and
`_row_data_types`'s documented fallback-to-ALL behavior means "ALL" = the CLI's `--data-types` override verbatim — i.e.
every unmapped-type instrument across the WHOLE defi catalogue gets falsely stamped with `perp_trades`, not just DRIFT.
This is the SAME bug class already flagged (smaller-scale, LST-only) as a "minor secondary finding" in
`plans/active/issues/defi_expected_unattempted_backlog_1m_2026_07_03.md` — added a fuller writeup + a new `[DATA] P2`
fix todo there (don't duplicate here) rather than re-filing a fresh issue doc.

**Did not fix the shared alias table this session** — confirmed via grep that
`valid_data_types_for_venue_instrument_type`/`_for_instrument_type` is also the validity source for
`possible_manifest.is_valid_shard_key` (the orphan-sweep/phantom-reconciler check), and the two candidate alias targets
disagree on `oracle_prices` validity for `A_TOKEN`/`DEBT_TOKEN` (current `PROTOCOL_CAPABILITIES`-derived set excludes
it; the separate legacy `venue_mapping.DataTypeConfig.instrument_data_types` table includes it) — narrowing on the wrong
one would newly misclassify real captured `oracle_prices` cells as orphans. That's a genuine SSOT-contradiction call
outside this task's scope, not a fix to bundle into a P1.3 materialization todo.

**Workaround for my own task** (kept the fix out of shared code): wrote a standalone one-off script (not committed —
same "reuse the production enumerator functions verbatim" pattern already used in
`defi_expected_unattempted_backlog_1m_2026_07_03.md`'s own diagnostic) that called `enumerate_v2()` +
`_write_absent_rows()` from `enumerate_expected_universe.py` directly, filtering the resulting candidate list to
`venue == "DRIFT"` before the real write. Verified via cross-tab that this exactly isolates DRIFT's own legitimate rows
(both the 34 PERPETUAL + 46 SPOT_PAIR catalogue instruments' per-instrument lifecycle cells, and DRIFT's own venue-grain
pre-launch history) from the 7.1M-row leak across the other 63 venues. DRIFT's SPOT_PAIR instruments getting
`perp_trades` candidates too (not just PERPETUAL) is expected, pre-existing behavior — `PROTOCOL_CAPABILITIES["drift"]`
already declares both instrument_types with one shared `data_types` list (same coarse-grained modeling `perp_funding`
already uses today), not a new asymmetry.

Dry-ran first (scan-only): 250,937 DRIFT-scoped rows (107,760 `expected_unattempted` blank-reason + 77,652
`EXPECTED_INSTRUMENT_NOT_LISTED` + 65,205 `EXPECTED_PRE_GENESIS_CHAIN` + 320 `EXPECTED_INSTRUMENT_DELISTED`). Then ran
for real (`MANIFEST_PER_VM_SHARDS=true VM_NAME=enum-drift-perp-trades-materialize-<ts>`): wrote 250,937 rows to
`_index/per_vm/enum-drift-perp-trades-materialize-1784165794.parquet`. **Durably verified** by reading the shard back
directly: 250,937 rows, 100% `venue=DRIFT` / `data_type=perp_trades`, `pipeline_mode=batch_onchain_rpc` (matching the
P1.2 shard-atom-identity fix), `capture_status` split 107,760 `expected_unattempted` / 143,177 `empty_confirmed`. Will
merge into the consolidated index on the next consolidator cycle (~5 min).

No code shipped this session (pure data materialization + a documented workaround; the underlying alias-table fix is
tracked as its own todo in the sibling issue doc, not this task's scope). Checkbox flipped above.

### 2026-07-16 — data_engineering slot-15: banner + closure (P2)

Re-dispatched to `-004`. Verified live state before acting rather than trusting doc text: `GET /api/backlog` showed
`drift_helius_path_obsolete-005` (the P1.2 reconcile task, item (4)) at `status: "done"` — confirmed via this doc's own
Progress Log (slot-14's entry above: root cause fixed, `unified-api-contracts@5fd781c7` shipped) that all of (2), (3),
(4) have now genuinely landed, unlike the 4 prior dispatches (slot-9/10/11/13) that correctly declined because (4) was
still open. Added the retirement banner to both target docs:

- `issues/drift_v2_sig_index_program_wide_helius_oom_2026_07_15.md` — new 🟢 banner confirming the migration is
  complete, with the specific commits (`deployment-service@46d6492`/`@ee859e4`, `unified-api-contracts@5fd781c7`).
  Checked that doc's own `[INFRA] P2` (zombie-VM CLI monitor) and `[DATA] P3` (relaunch) todos: both were already
  checked off from prior sessions. P3 was already explicitly closed "AS SUPERSEDED" (slot-13); P2 is a permanent,
  protocol-agnostic monitoring tool independent of the Helius/Velocity question, so it stays done-not-moot (called this
  out explicitly in the banner rather than silently leaving it ambiguous).
- `plans/active/mvp_backfill_defi_onchain_v10_2026_06_27.md` — new 🟢 banner placed directly after the two
  DRIFT-sig-walker banners (13:15Z BLOCKED-OPERATOR-DECISION / 14:07Z resolved-and-relaunched) it supersedes, marking
  that content historical and pointing at `issues/drift_helius_path_obsolete_2026_07_15.md` as the migration SSOT.

No code changes (doc-only task, `repos: []`). This doc's own P2 todo flipped above.

### 2026-07-16 — data_engineering slot-14: root-caused + fixed the perp_trades catalog gap (P1.2)

Picked up P1.2. Verified the VM launched by infra slot-2 was genuinely alive
(`deployment-service/scripts/data_pipeline_monitors/check_vm_cli.py --vm-name mtds-solana-drift-backfill`,
heartbeat/run-log age <1min) before touching manifest data.

Read the current DRIFT manifest state via the safe filtered path
(`read_availability_index(bucket, columns=[...], filters=[("venue","==","DRIFT"), ...])`, never a full-index/corpus walk
— the DeFi bucket's full-index read is a known OOM risk per `manifest_index_read_oom_canonical_cache_2026_06_24.md`; ran
under an RSS-guarded wrapper as an added precaution on this shared host). For the `2025-01-15`–`2025-12-23` gap:
`perp_funding` shows 3 `captured` / 27 `attempted_failed` (all "day sig count exceeds 50000 ceiling" — the old Helius
wall, on specific high-volume days) / 313 `empty_confirmed` / 13720 `expected_unattempted` (~40 markets × 343 days) —
this part is coherent and will naturally self-correct as Velocity's writes supersede the stale rows per the
dedup/captured-outranks logic, no code change needed there.

**Real bug found**: `perp_trades` has exactly ONE row in DRIFT's ENTIRE manifest history — the single day manually
reconciled last session (P1.1) — versus `perp_funding`'s 51,301 `expected_unattempted` catalog rows. Traced root cause
(background Explore agent + my own verification of both files): the expected-universe seeder
(`instruments-service/scripts/enumerate_expected_universe.py`) enumerates candidate
`(date, venue, chain, data_type, market)` cells from two UAC registries — `PROTOCOL_CAPABILITIES["drift"].data_types`
and `DATA_TYPES_BY_ASSET_GROUP["defi"]` — and neither ever listed `"perp_trades"`, even though the MTDS Velocity
ingester (`drift_v2_historical_handler.py`) and the UAC schema/contract layer (`DataType.PERP_TRADES`,
`DEFI_PERPETUAL_PERP_TRADES` contract) both already fully support it. Confirmed via `git log -S` this was an original
gap (perp_trades added system-wide in `f26097f9`, scoped to schema/contracts only, never touched these two enumeration
registries) — not a regression.

**Fix**: added `"perp_trades"` to both registries (additive, DRIFT/DeFi-scoped only — cannot leak onto other DeFi
protocols since `valid_data_types_for_venue_instrument_type` narrows per-protocol) + a regression test
(`test_drift_has_perp_trades`) in `unified-api-contracts`. Full `quality-gates.sh` green (sentinel matches HEAD),
shipped `unified-api-contracts@5fd781c7` (`--files`-scoped quickmerge).

**Scope call**: the actual materialization of ~51k-scale `expected_unattempted` rows for DRIFT `perp_trades` requires
running `enumerate_expected_universe.py --apply-write` against production — a real, separately-scoped write op (needs a
`--catalog-path` located first, dry-run row-count sanity check before commit). This is a genuine discovery the original
P1.2 todo didn't anticipate (it assumed only stale `attempted_failed`→`captured` transitions, not a missing catalog
registration), so per findings-triage discipline I'm not absorbing it into this task — added as `P1.3` above, scoped to
`instruments-service`. P1.2 itself (the code-level root-cause fix) is now shipped, hence flipped done.

### 2026-07-16 — infra slot-2: launched the re-routed Velocity VM at scale (P1)

Picked up the `[INFRA] P1` launch-at-scale todo. Fresh-pulled all repos clean (deployment-service already at `ee859e4`
as a parent of current HEAD `46d6492`). `gcloud` (the snap CLI) is broken in this slot (`cap_dac_override` snap-confine
failure, same as every prior session on this host) — used the working non-snap SDK at `~/google-cloud-sdk/bin/gcloud`
(prepended to `PATH`) for both the pre-launch existing-VM check and the actual launch, per the documented workaround in
prior issue docs.

Confirmed zero `mtds-solana-drift-*` VMs running before launch. Dry-ran
`launch-mtds-solana-drift-backfill-vm.sh --start 2025-01-15 --end 2025-12-23` first — confirmed correct config
(e2-highmem-8, SPOT, `VM_TASK=solana-drift-backfill`, `VM_DRIFT_MARKET=SOL-PERP`). Launched for real (same flags, no
`--dry-run`): VM created, tarball-freshness check passed for all 4 dependent repos (mtds@1bd507b4, uac@3e3739a1,
utl@4165f409, deployment-service@46d6492 — a direct child of `ee859e4`, confirmed via `git log --oneline` the Velocity
re-route commit is included), status `RUNNING` within seconds (no fire-and-forget per infra craft north-star).

**Startup verification** (not fire-and-forget): the VM's log object
(`gs://deployment-scripts-central-element-323112/vm-logs/mtds-solana-drift-backfill/run.log`) initially still showed the
STALE tail from the prior (pre-re-route) VM run (`2026-07-15 23:33Z`, Helius-path `Drift Helius backfill: ... sigs`
messages) — that VM had self-deleted over an hour earlier. Backgrounded a watcher polling `gsutil ls -l` for the log's
mtime to advance past the stale timestamp, then tailed it once it did (`2026-07-16 00:41Z`, ~3 min after VM create).
Confirmed the NEW run is genuinely on the Velocity path: log lines read
`DriftV2 perp_funding/SOL-PERP/<date>: wrote 24 rows to .../pipeline_mode=batch_onchain_rpc/.../data_type=perp_funding/SOL-PERP.parquet`
(and equivalent for `perp_trades`), i.e. the correct manifest-matching partition path (the exact bug fixed in
`mtds@1bd507b4`), with `ManifestWriter: per-VM shard updated` entries after each date and a `PIPELINE_HEARTBEAT`
liveness line. Throughput is dramatically better than the abandoned Helius path — ~5-6s/day vs. the documented ~2-3h/day
sig-walker stall — so the full `2025-01-15`→`2025-12-23` (345-day) gap should clear in well under an hour, not the 44+
days the Helius path would have needed.

Flipped `drift_velocity_backfill_running_at_scale` to `true` via `POST /api/prerequisites/...` so P1.2 (the manifest
cell reconciliation, currently parked behind this condition per `BLK-b72a4b59`) unparks for the next data_engineering
dispatch. No code changes this session — pure infra launch, `repos: []` on the task. Checkbox flipped above.

### 2026-07-16 — data_engineering slot-7: P1.2 parked behind a real prereq (`BLK-b72a4b59`)

P1.2 auto-dispatched to me immediately after P1.1, but its stated precondition ("Velocity capturing at scale") wasn't
met — a read-only GCE check (`compute_v1.AggregatedListInstancesRequest`, project `central-element-323112`) found ZERO
instances matching `mtds-drift-sig-walker*` or `mtds-solana-drift-backfill*`; nothing was capturing anything. Filed
`/blocked` `BLK-b72a4b59` rather than guess. Main ruled **A** (park behind a real prereq) with 3 riders:

1. Confirm the plan has a todo to actually LAUNCH the re-routed Velocity backfill at scale — it did NOT (todos 1/2 above
   are stop-fleet + re-route-launcher, i.e. wiring only, never an actual run). **Added** the `[INFRA] P1`
   launch-at-scale todo directly above so P1.2's gate has something to open.
2. Mark the stop-fleet todo done citing my GCE-check evidence — **already done concurrently** by infra slot-16
   (`deployment-service@46d6492`, same zero-instance finding, independently confirmed) before I got to it.
3. Name + wire a real prereq condition instead of letting P1.2 re-dispatch and churn. **Done**: created
   `drift_velocity_backfill_running_at_scale` (`POST /api/prerequisites/...` `{value: false}`), attached it to
   `drift_helius_path_obsolete-005`'s `prereqs.prerequisites` in `backlog.yaml`, and set `priority: 999` +
   `priority_override: true` on the same entry so it stays parked instead of re-dispatching. Whoever executes the new
   `[INFRA] P1` todo flips the condition to `true` on completion, which unparks P1.2 for the next data_engineering
   worker.

### 2026-07-16 — infra slot-16: stop/do-not-relaunch (todo 1)

Picked up the `[INFRA] P0` fleet-stop todo. Listed instances in `central-element-323112` in every state (not just
RUNNING) via UTL's `get_compute_engine_client(...).aggregated_list_instances` (the sandboxed `gcloud` CLI here is
snap-confined — `cap_dac_override` missing, unusable) — 0 matches for `mtds-drift-sig-walker-*` or
`mtds-solana-drift-backfill` in the full 22-instance listing, so no live VM needed stopping. Fixed the durable
"do-not-relaunch" half: `deployment_service/data_pipeline_monitors/launcher_registry.py` maps VM-name prefixes to the
self-heal actuator's relaunch script, and both prefixes were still mapped to their launchers — meaning a
watchdog-detected stall/OOM would have auto-relaunched the retired Helius path. Flipped `mtds-drift-sig-walker-` to
`None` (permanent — Option A abandons that path entirely, no re-route planned). Left `mtds-solana-drift-backfill` mapped
to its launcher: `ee859e43` (slot-6, todo 2) landed concurrently mid-task, re-routing that exact launcher to the
Velocity ingester, so the Helius-spend rationale for disabling it no longer held — auto-relaunch of a correctly-routed
backfill is desired self-heal behaviour, not a risk. `tests/unit/test_launcher_registry.py` (7/7) + full
`quality-gates.sh` green. Shipped `deployment-service@46d6492`.

### 2026-07-16 — data_engineering slot-7: reconciled the 2025-01-09 SOL-PERP shard (P1.1)

Picked up the P1 reconcile todo. Verified ground truth by reading the two real GCS parquet files directly (single-file
`pyarrow.parquet.ParquetFile.metadata.num_rows` reads, not a corpus walk):
`gs://market-data-tick-defi-prd-central-element-323112/raw_tick_data/by_date/day=2025-01-09/pipeline_mode=batch_onchain_rpc/asset_group=defi/venue=DRIFT/chain=SOLANA/instrument_type=perpetual/data_type={perp_funding,perp_trades}/SOL-PERP.parquet`
— `perp_funding`=24 rows, `perp_trades`=17223 rows. Both files exist, correctly partitioned, sizes plausible (20KB /
2.7MB), `last_modified` 2026-07-15 (the prior session's verify-first run) — confirms the **data write** side was durable
all along.

The **manifest** side was NOT reconciled, confirming the caveat this doc flagged: reading
`read_availability_index(bucket, columns=[...], filters=[("date","==","2025-01-09")])` (the safe, OOM-proof slim
filtered path — measured ~5MB per the `_read_index.py` docstring) required `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400`
(the documented DeFi-launcher mitigation from `manifest_index_read_oom_canonical_cache_2026_06_24.md` Option C) because
the consolidated blob for this bucket is genuinely stale right now (measured age 194.7s then 279.8s ~85s later —
climbing in real time, i.e. the consolidator is actually behind/down for this bucket, not just transiently past the 120s
default threshold — a live data point for that separately-owned P2 issue, not duplicated here). Even with that env var,
the manifest showed:

- `perp_funding`: ONE `captured` row, but `row_count=1209478` — not this shard's real content (a 20KB/24-row file cannot
  hold 1.2M records); a bogus/stale entry.
- `perp_trades`: **no `captured` row at all** — only the unrelated `expected_unattempted` catalogue placeholders for
  other DRIFT data_types on this date.

**Root cause of why the fix didn't durably land last session**: `record_captured()`/`close()` on this shared interactive
host defaults to the LEGACY single-blob CAS write (`manifest_per_vm_shards` defaults `False` —
`config_interface/cloud_config.py:688`), which read-merge-uploads the WHOLE consolidated index — the actual OOM trigger,
not `record_captured()` itself. **Fix applied**: set `MANIFEST_PER_VM_SHARDS=true` (the same flag production backfill
VMs already set per CLAUDE.md) so the writer targets the small per-VM shard object instead. Re-ran the reconciliation as
a standalone script calling `DefiManifestRecorder.record_captured()` with the exact production call shape from
`drift_v2_historical_handler.py:412-420` (`venue=DRIFT, chain=SOLANA, pipeline_mode=BATCH_ONCHAIN_RPC`, no
`instrument_type`/`instrument_id` — matches the existing venue/chain-grain recording, not a new gap) and the
GCS-verified row counts (24 / 17223). Ran under an RSS monitor with an 8GB kill-switch as a precaution; actual peak RSS
was ~2MB, completed in 5s — confirms the risk was specifically the legacy full-index CAS path, not the manifest write
itself. **Durably verified**: read the resulting per-VM shard object directly
(`_index/per_vm/local-2742523-30b2.parquet`) and confirmed both rows present — `perp_funding captured row_count=24`,
`perp_trades captured row_count=17223`, `attempted_at=2026-07-16T00:08:0{2,6}`. This entry will merge into the
consolidated index on the manifest consolidator's next successful run for this bucket (separately tracked as
stale/behind above); any full (unfiltered) `read_availability_index` call already unions per-VM shards over the
consolidated blob per its own docstring, so downstream full-read consumers see the correct values now, independent of
consolidator catch-up.

**Operational note for future DeFi manifest reconciliation on this shared interactive host**: prefer
`MANIFEST_PER_VM_SHARDS=true` + `MANIFEST_CONSOLIDATED_STALENESS_SEC=86400` for both reads and writes — avoids both the
full-corpus slow-path read AND the legacy single-blob CAS write, which is what actually OOM'd the prior session (not
`record_captured()` in the abstract).

P1.2 (the broader Helius-path cell reconciliation) is NOT started — it explicitly depends on Velocity "capturing at
scale", which presumes the `[INFRA] P0` fleet-stop todo above has landed; that is infra-scoped, outside this craft's
remit.

### 2026-07-15 — data_engineering slot-2: ruling obtained, verify-first done, pipeline_mode bug found + fixed

Picked up the P0 ruling-needed todo. Did pre-ruling API verification (see above), posted `/blocked` `BLK-ba6c367c`
recommending A with evidence, main confirmed A (consistent with BLK-5d122841/BLK-6067d459). Executed main's step-1
verify-first: ran the real ingester against production GCP, found and fixed a real shard-atom-identity bug
(`pipeline_mode` mislabeling, `market-tick-data-service@1bd507b4`), confirmed correct row counts + correct partition
path post-fix. Surfaced a caveat (shared manifest-index-read OOM, already tracked separately) that constrains how step
2/3 should be executed (e2-highmem-8). Twice had to kill a runaway local process to protect the shared host — did not
let it OOM. Created this consolidation doc per main's step-5 instruction. Steps 2-4 (stop fleet, wire launcher,
reconcile manifest) are scoped as todos above, not executed this session — they involve stopping a live multi-VM SPOT
fleet and infra changes better suited to a dedicated follow-up dispatch than folded into this single P0 verification
task.

### 2026-07-16T00:15-00:28Z — data_engineering slot-13 (dispatched to `mvp_backfill_defi_onchain_v10-003`): independently confirmed slot-7's P1.1 root-cause before seeing their fix, no duplicate work; P1.2 sole remaining blocker is a VM launch (infra-scoped)

Dispatched to the main plan's `-003` ("Verify the DRIFT fleet drains") todo, not this doc directly. Independently traced
the exact same defect slot-7 root-caused and fixed moments earlier: queried `_index/availability_index.parquet` with
predicate pushdown (`venue=DRIFT, data_type=perp_funding, date=2025-01-09`) before fresh-pulling picked up slot-7's
`record_captured()` fix, found the same stale `row_count=1209478`/ `source=hyperliquid` bogus captured row, and
independently downloaded + verified the real GCS parquet directly (24 rows, matches). Fresh-pulled again before writing
anything and found slot-7's fix (`per_vm/local-2742523-30b2.parquet`, `MANIFEST_PER_VM_SHARDS=true` reconciliation)
already landed with a more thorough root-cause (the legacy single-blob CAS write path, not `record_captured()` itself) —
dropped my own draft fix, no duplicate write.

**Current blocker for P1.2 (and this doc's own gate) is now singular and infra-scoped**: `gcloud compute instances list`
(project `central-element-323112`, 2026-07-16 00:28Z) shows zero `mtds-solana-drift-backfill` instances running — the
last one (2026-07-15 23:11-23:34Z) predates both `deployment-service@46d6492` (fleet-stop/launcher-registry fix, 00:0xZ)
and `@ee859e4` (re-route to Velocity, 00:12:35Z), so it ran the OLD Helius path and self-deleted before either fix
existed. Nobody has launched `launch-mtds-solana-drift-backfill-vm.sh` since the re-route landed — the launcher is
correctly wired (verified via `deployment-service@ee859e4`'s dry-run) but has not actually been invoked. This is a VM
launch, which is `does_not` scope for `data_engineering` craft (`agents/data_engineering.md`) — deferring to an
infra-craft dispatch or main, consistent with slot-7's same scope call on P1.2. Re-ran the aggregate gate one more time
before this session's fresh-pull picked up slot-7's fix (2026-07-16 00:18Z): DRIFT `perp_funding`
`captured=9, attempted_failed=72, expected_unattempted=51301` — `attempted_failed` grew 54→72 from the stale-code VM's
last run (18 ceiling-exceeded days recorded honestly, not a new defect); did NOT re-run the full corpus-scale gate again
after slot-7's fix landed minutes later, since (a) the consolidator is confirmed stale/behind right now (slot-7's own
finding) so a fresh full read would not yet reflect their per-VM-shard fix, and (b) a third corpus-scale
`measure_honest_coverage.py` run within 30 minutes is the exact over-watch pattern this task has been flagged for
repeatedly.

**Recommendation for the next dispatch (any craft, ideally infra)**: launch `launch-mtds-solana-drift-backfill-vm.sh`
(already re-routed + e2-highmem-8 + SPOT) — that is now the ONLY remaining action item before P1.2's reconciliation and
this task's own gate can move. No further data_engineering-craft investigation is warranted until that VM produces new
manifest data to reconcile.

No code changes this session (draft fix superseded before commit). This doc's own todos unchanged (P1.1 done, P1.2/P2
still open, both correctly gated). No checkbox flip on the main plan's `-003` item — gate (item 4) still not met.
`/skip-current-task`.

### 2026-07-16T00:1xZ — data_engineering slot-11 (dispatched to -004, the banner todo — declined, genuinely premature)

**Dispatched to `drift_helius_path_obsolete-004`** ("Once (2)-(4) land, add a banner..."). Fresh-pulled clean. This
todo's own text is explicit: it only fires once steps 2 ([INFRA] stop the Helius fleet), 3 ([INFRA] re-route the
launcher), and 4 ([DATA] reconcile the manifest) all land. Checked this doc's own todo list directly — all three are
still `[ ]` (none executed since slot-2's session created this doc). Adding the "retired, superseded" banner now would
be false — the Helius fleet hasn't actually been stopped yet, so declaring the path "retired" in the plan/issue docs
would misrepresent live system state. Declining — no action taken, checkbox NOT flipped. `/skip-current-task`.

### 2026-07-16 — data_engineering slot-10 (dispatched to -004 again, re-confirmed still premature; merge-reconciled with slot-7's concurrent, more complete fix)

Re-dispatched to `drift_helius_path_obsolete-004` after (2) and (3) landed (`deployment-service@46d6492`, `@ee859e4`).
Fresh-pulled clean. Re-checked this doc's own todo list directly: (2)/(3) now `[x]`, but (4) (`P1.2` reconcile-manifest)
is still `[ ]` and explicitly "NOT started" per its own text. Independently re-verified the live blocker both `slot-13`
(00:15-00:28Z) and `slot-11` (00:1xZ) had already identified — queried GCE directly via UTL's
`get_compute_engine_client(...).aggregated_list_instances` (`central-element-323112`, the sandboxed `gcloud` CLI here is
snap-confined, same as prior sessions): **0** instances matching `drift` in the name, out of 13 total — the re-routed
launcher (`launch-mtds-solana-drift-backfill-vm.sh`) has still not been invoked by anyone since it was wired 2026-07-16.
Drafted a prose-only `[INFRA] P1` launch todo to formalize this, but on `quickmerge`'s pull-first rebase hit a **genuine
same-file conflict**: `data_engineering slot-7` had landed the identical realization moments earlier — `/blocked`
`BLK-b72a4b59`, ruled by main, resulting in an actual `[INFRA] P1` launch todo PLUS a real
`drift_velocity_backfill_running_at_scale` prerequisite (`POST /api/prerequisites/...`) parking P1.2 in `backlog.yaml`
(`priority: 999` + `priority_override: true`) instead of letting it keep re-dispatching. Their fix is strictly more
complete than my prose-only version (a wired API prerequisite vs. just checkbox text), so resolved the conflict by
keeping their `[INFRA] P1`/`[DATA] P1.2` block verbatim and dropping my duplicate, folding in only my independent
zero-instance confirmation as a one-line addendum. P2 (this doc's own banner gate) remains genuinely unmet: (4) still
hasn't landed, now properly tracked via the prerequisite instead of prose.

**Second conflict, same file, on push** — while shipping the above, `quickmerge` (then a manual `git pull --rebase`)
surfaced a further concurrent landing: `infra slot-2` had, in the interim, picked up the `[INFRA] P1` launch-at-scale
todo directly (`deployment-service` VM launch, no code diff) and confirmed via `run.log` that the VM is genuinely
resolving on the Velocity path (correct `pipeline_mode=batch_onchain_rpc` partitions, ~5-6s/day throughput vs. the
abandoned Helius path's ~2-3h/day) — then flipped `drift_velocity_backfill_running_at_scale` to `true`, unparking P1.2.
Re-resolved this second conflict by keeping their landed `[x]` P1 checkbox and updating my own P1.2/P2 prose to reflect
reality: P1.2 is UNPARKED but has NOT yet actually executed (no reconciled manifest counts exist), so this doc's P2
banner gate is still not met — the remaining gap narrowed from "an open infra question" to "wait for P1.2 to run," but
hasn't closed. No code changes this session (doc-only, twice conflict-resolved). Checkbox NOT flipped (gate still
unmet). `/skip-current-task`.

### 2026-07-16 — data_engineering slot-9 (dispatched to -004 a 3rd+ time — still premature; wired a machine-checked gate to stop the redispatch thrash)

Re-dispatched to `drift_helius_path_obsolete-004`. Fresh-pulled all repos clean. Re-checked live state directly rather
than trusting doc text alone: `GET /api/backlog` shows `drift_helius_path_obsolete-005` (the P1.2 reconcile task, item
(4)) with `status: "dispatched"` — actively being worked by another slot, not yet `done`. So (4) still has not landed;
this task's own precondition ("once (2)-(4) land") remains unmet for the 3rd+ consecutive dispatch, matching slot-10's
and slot-11's identical findings.

Rather than decline silently again, wired the precondition into the dispatcher itself so it stops re-offering this task
until (4) is genuinely `done`: added `prereqs.completed_tasks: [drift_helius_path_obsolete-005]` to task -004's entry in
`agent-orchestrator/data/config/backlog.yaml` (the documented backlog-tuning mechanism, `RULES.md` § 4 — tunes an
already-derived entry, doesn't hand-author a new one) + `POST /api/backlog/reload`. This is the same pattern
`data_engineering slot-7` already used for -005 itself (`drift_velocity_backfill_running_at_scale` prerequisite), which
has held across at least 2 regen ticks since. Once -005 flips to `done`, the dispatcher will hold -004 until then
instead of a 4th/5th worker re-deriving the same "still not landed" conclusion. No code changes this session. Checkbox
NOT flipped (gate still unmet — this doc's own P2 item stays open until -005 lands). `/skip-current-task`.
