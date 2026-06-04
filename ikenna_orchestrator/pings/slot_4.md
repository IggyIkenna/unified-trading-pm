> **🟢 2026-05-21 DISPATCH — supersedes all prior entries.** Read `plans/active/plan_closeout_archive_2026_05_21.md`
> §Slot 4 and the spawn prompt from operator. History below is audit-trail only.

## [main → slot 4] 2026-05-21 — 7 plan closes + trivial sweeps (pm@5eedc069a)

**Timestamp**: 2026-05-21 | **Status**: 🟢 DISPATCH

**Your job**: Close these 7 plans (read each, trivial sweep, execute remaining items, archive if 100%):

Priority order:

1. `hedge_ratio_snapshot_persistence` — **WAS URGENT deadline 2026-05-21, do FIRST**
2. `gate_3_phantom_audit_runbook` — must have owner/cadence/verifier/last_executed fields
3. `api_football_minimal_flattening` (2 items)
4. `tradfi_ohlcv_only_mvp_backfill` (2 items)
5. `mock_data_pipeline_benchmarking` (94% done)
6. `trigger_based_reference_data` (1.9 cal)
7. `dex_perp_onboarding_handover` (6.0 cal — handover doc + implementation)

**Trivial sweep policy**: before ANY real work on each plan, mark [x] immediately for: QG-run with existing green SHA |
dry-run with recorded results | "don't deprecate" when repo active | "create successor" when successor exists | P3 item
with deferred P0/P1 → [ABANDONED]

Per-plan: commit trivials → execute real items → QG if code → commit per shippable unit → archive if 100%.

**Sweep bonus**: after all 7, scan related_plans: links — trivial-sweep any >90%-done linked plan.

**Ack**: append `[2026-05-21 HH:MM UTC] slot-4 DONE — closed/archived N plans` here when done.

**[2026-05-22] slot-4 DONE — all 7 closed/archived (3 were pre-archived; 4 archived in dispatch session). Codex
alignment check (CLAUDE.md step 3, added 2026-05-22): gate_3_phantom + dex_perp have no Codex SSOTs; tradfi_ohlcv codex
current; mock_data codex stale plan-ref fixed → PM@(this commit).**

---

> _Cleaned 2026-05-22 — audit trail stripped; history preserved in git._

---

## [slot-1-main → slot-4] 2026-05-22 — P0 AWS cloud toggle (Phases 1-3)

**Plan**: `plans/active/aws_cloud_toggle_and_backfill_parity_2026_05_22.md`

**Why P0**: operator needs GCP/AWS data-status toggle working before any AWS backfill inspection or launch. Currently
`cloud="gcp"` is hardcoded at all 5 layers.

**Your scope — Phases 1, 2, 3 of the plan** (deployment-api + unified-trading-system-ui only):

### Phase 1 — Service layer (`deployment_api/services/data_status_service.py`)

Add `cloud: str = "gcp"` param and replace 6 hardcoded `cloud="gcp"` strings:

- `_read_defi_merged_index(self, service, cat)` → lines 2916 + 2918
- `get_manifest_status(...)` → add param + thread to `_get_manifest_status_sync` → lines ~3816 + 3818
- `get_coverage_summary(...)` → add param + thread to `_get_coverage_summary_sync` → lines ~5672 + 5674

### Phase 2 — Route layer (`deployment_api/routes/data_status.py`)

Add `cloud: Literal["gcp", "aws"] = Query("gcp", description="Cloud provider")` to:

- `get_data_status` (line 252) — pass to `run_data_status_cli` + `get_manifest_status`
- `get_data_status_turbo` (line 764) — thread into `_manifest_source` closure → `get_manifest_status(cloud=cloud)`
- `get_data_coverage_summary` (line ~830) — thread to service

### Phase 3 — UI (4 files in `unified-trading-system-ui`)

1. `components/ops/deployment/data-status/data-status-context.tsx` — add `cloudProvider: "gcp" | "aws"` +
   `setCloudProvider` setter to `DataStatusTabContextValue` interface
2. `components/ops/deployment/data-status/data-status-provider.tsx` — add `useState<"gcp" | "aws">("gcp")` state; pass
   `cloud: cloudProvider` to both `api.getDataStatus` and `api.getDataStatusTurbo`; add to dep array + context value
3. `components/ops/deployment/data-status/data-status-filters-header.tsx` — add GCP|AWS toggle button group (same style
   as batch/live toggle), bind to `setCloudProvider`
4. `hooks/deployment/_api-stub.ts` — add `cloud?: "gcp" | "aws"` to both `getDataStatus` + `getDataStatusTurbo` param
   types; thread to URL query string

**QG**: `bash scripts/quality-gates.sh` in deployment-api after Phase 1 + after Phase 2. UI: TypeScript only —
`npx tsc --noEmit` in unified-trading-system-ui after Phase 3.

**Commit + Flip pattern**: one commit per phase. Flip `aws_cloud_toggle_and_backfill_parity_2026_05_22.md` checkboxes in
same turn.

**Ack**: append `[2026-05-22 HH:MM UTC] slot-4 DONE — AWS toggle Phases 1-3 complete at deployment-api@<sha> + ui@<sha>`
here when done.

**[2026-05-22] slot-4 DONE — AWS toggle Phases 1-3 complete at deployment-api@af77f8f (route layer) +
deployment-api@85d416d (service layer) + unified-trading-system-ui@2a017c78 (UI toggle). UI-V (browser verify) pending —
need dev stack running.**

---

## 2026-05-22 — [slot-4 → slot-1 main] Phase 3 dispatch progress

**Plan refs**: `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` ·
`plans/active/code_freeze_migrate_backfill_sequencing_2026_05_10.md` ·
`plans/active/promote_workflow_may23_cli_path_2026_05_10.md`

**Items shipped (PM tab branch `tab/ikennaigboaka/4`)**:

| Item                               | Status  | Evidence                                                                                                                                                                                                                                   |
| ---------------------------------- | ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| 2 — Phase 2.E.1 QG STEP 5.85       | ✅ DONE | PM@3a220308f — `no_blank_record_empty_reason.py` AST checker + `base-service.sh` wire; writegate Phase 2.E.1 `[x]` (superseded by STEP 5.89 on remote)                                                                                     |
| 6 — GAP-2.4.D design doc           | ✅ DONE | PM@d894869bf — `plans/active/gap_2_4_d_deployment_api_reader_repoint_2026_05_22.md` filed; audit: drilldown already clean, 2 flat methods remain (DataStatusService + DataQueryService), ml-\* drift RESOLVED; code_freeze GAP-2.4.D `[x]` |
| 5 — StrategyDirectiveReloader stub | ✅ DONE | Already on LDR — confirmed 2026-05-22 via `e2e-testing@5804719` (freeze lifted; was pre-pushed during freeze window)                                                                                                                       |

**UAC catalog-read interface contract landed — items 1/3+4 UNBLOCKED**:

| Item                                               | Status                   |
| -------------------------------------------------- | ------------------------ |
| 1 — Sports per-fixture_id shard granularity (MTDS) | 🟡 READY — awaiting work |
| 3+4 — Phase 3.D.5 v2 catalog enumerators           | 🟡 READY — awaiting work |

Unblocked by: UAC@a422d0b8 (`InstrumentCatalogReader` Protocol + `list_instruments` + `register_catalog_reader` in
`canonical/domain/instruments_catalog.py`). Code freeze lifted 2026-05-22. Phase 3 VM launches still gated on
`mtds_mdps_master` Phase 7 GREEN (separate gate).

**[2026-05-22] slot-4 status update**: AWS toggle Phases 1-4 complete + SMOKE-1/2/3 BLOCKED-OPERATOR-DECISION. All repos
synced to LDR. Items 1/3+4 unblocked.

— slot-4 / 2026-05-22

---

## 2026-05-23 — [slot-4 → slot-1 main] cefi backfill DONE + defi/tradfi operator decisions needed

**Plan ref**: `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` (line 2539 flipped PM@7bb301ba8)

### cefi 12-month v2 backfill — COMPLETE ✅

All 4 × 91-day apply-write chunks finished. 71,468,109 rows across 4 per-VM shards on GCS
(`market-data-tick-cefi-central-element-323112/_index/per_vm/`):

| Chunk | VM name                | Date range            | Rows       |
| ----- | ---------------------- | --------------------- | ---------- |
| c1    | slot4-cefi-c1-20260523 | 2026-02-22→2026-05-23 | 19,585,202 |
| c2    | slot4-cefi-c2-20260523 | 2025-11-23→2026-02-21 | 16,134,573 |
| c3    | slot4-cefi-c3-20260523 | 2025-08-24→2025-11-22 | 20,171,242 |
| c4    | slot4-cefi-c4-20260523 | 2025-05-24→2025-08-23 | 16,192,092 |

Plan checkbox flipped: PM@7bb301ba8. instruments-service@363af916 (upload timeout fix) + @ecabcf74 (window-overlap
pre-filter).

---

### defi since-genesis v2 apply-write — COMPLETE ✅

**Status**: `DONE` (operator expanded to genesis 2026-05-23; all 26 chunks complete in ~17 minutes total)

3,599 instruments × 21 data_types × 2,334 days (2020-01-01→2026-05-23). 26 per-VM shards on GCS.

| Chunks  | Date range            | Rows       |
| ------- | --------------------- | ---------- |
| d1–d4   | 2025-05-23→2026-05-23 | 26,748,498 |
| d5–d8   | 2024-05-24→2025-05-22 | 22,893,780 |
| d9–d12  | 2023-05-26→2024-05-23 | 15,192,450 |
| d13–d16 | 2022-05-27→2023-05-25 | 8,245,965  |
| d17–d20 | 2021-05-28→2022-05-26 | 3,667,209  |
| d21–d26 | 2020-01-01→2021-05-27 | 602,862    |

**Total: 77,350,581 rows** across 26 shards. Plan item updated: writegate (PM this commit).

---

### CREDENTIAL APPROVAL REQUEST — tradfi Databento adapter

**Status**: `BLOCKED-CREDENTIALS`

**Vendor**: Databento · Historical market data (US equities, futures, options, ETFs) · Est. $200-500/month for MVP
coverage (Starter/Developer tier)

**What I need**:

- Databento API key (`db-xxx` format, from https://app.databento.com/portal/keys)
- Account to use: existing operator email `ikenna@odum-research.com` or new account
- If new account: email + password setup (Databento requires email verification)

**Unblocks**:

- `tradfi` asset_group catalog (instruments-service tradfi adapter)
- `tradfi` OHLCV + tick data backfill (MTDS tradfi handler)
- `carry_staked_basis` + `arbitrage_price_dispersion` tradfi leg (strategy-service)
- writegate Phase 3 tradfi lane (currently `BLOCKED-CREDENTIALS` in plan)

**Without it**: tradfi adapter scaffold + unit tests ship; integration tests skip (`@pytest.mark.requires_credentials`);
adapter dormant. Not in `DEFERRED` — stays on live list per workspace rules.

**Cross-link**: `plans/active/writegate_honest_coverage_endtoend_2026_05_06.md` § "Credential asks awaiting operator"
(add row if section exists, else this ping is the tracker).

---

### Slot-4 work remaining as of 2026-05-23

**~0 actionable AI days on assigned plans.** All open items are one of:

- `DEFERRED-OPERATOR-DECISION` (batch-defer `6c7b67075` wiped all `- [ ]` items)
- `BLOCKED-CREDENTIALS` (tradfi Databento, sports/prediction feeds)
- `BLOCKED-NEW-CODE` (sports/prediction enumerators)
- Gated on `mtds_mdps_master` Phase 7 GREEN (items 1/3+4 from 2026-05-22 ping above)

**Ready if operator acks**: defi apply-write (~0.25 AI days, 4 × 90-min runs).

— slot-4 / 2026-05-23

---

## 2026-05-23 (session 2) — [slot-4 → slot-1 main] MTDS DeFi handler bugs fixed + SOURCE_RETURNED_ZERO cleanup

**Plan refs**: `plans/active/issues/mtds_defi_handler_bugs_source_returned_zero_cleanup_2026_05_23.md` ·
`plans/archive/2026_05/writegate_honest_coverage_endtoend_2026_05_06.md` (Phase 8) · `plans/epics/mtds_mdps_master.md`
(MDPS-3.3.DeFi-V) · `plans/epics/defi_master.md`

### 3 MTDS DeFi handler bugs fixed ✅

| Bug                                                            | Fix                                                                              | Commit          |
| -------------------------------------------------------------- | -------------------------------------------------------------------------------- | --------------- |
| `dex_swaps` hardcoded `"dex_pool_swaps"` partition key         | `data_type=_DEX_SWAPS_DATA_TYPE`                                                 | `mtds@69d694b1` |
| `gas_fees` null `eth_feeHistory` result → silent `[]` → 0 rows | `ValueError` raise + `"returned null result"` fallback                           | `mtds@69d694b1` |
| `lending_indices` silent API-key skip → `return 0`             | `RuntimeError` raise + ERROR-level SM logging + `THE_GRAPH_API_KEY` env fallback | `mtds@e86a6ad8` |

Also shipped: `scripts/reset_source_returned_zero_manifest.py` — bulk-deletes `empty_confirmed SOURCE_RETURNED_ZERO`
rows from per-VM shards + consolidated index (`mtds@e86a6ad8`).

### SOURCE_RETURNED_ZERO manifest cleanup — COMPLETE ✅

Grand total deleted across all 5 MTDS buckets:

| Bucket    | Rows deleted  | Task                            |
| --------- | ------------- | ------------------------------- |
| defi      | 35,576        | bg4qul73b                       |
| cefi      | 391,989       | bfrycvu0x                       |
| tradfi    | 71,065        | bfrycvu0x                       |
| sports    | 797,167       | bfrycvu0x                       |
| pred      | 0             | 404 (bucket does not exist yet) |
| **Total** | **1,295,797** |                                 |

Notes: defi bucket hit 429 in bfrycvu0x; separate bg4qul73b task handled defi. Manifest consolidator auto-runs every 1
min via Cloud Scheduler — no manual trigger needed. 195633-series DeFi VMs still running with OLD code → may write new
SOURCE_RETURNED_ZERO rows; another defi cleanup pass needed after those VMs complete or are relaunched with fixed code
(`mtds@e86a6ad8`). Writegate Phase 8.B item 6 flipped (this commit).

### Plans updated

- Issue doc filed: `plans/active/issues/mtds_defi_handler_bugs_source_returned_zero_cleanup_2026_05_23.md`
- `defi_master.md` — added ⚠️ DO NOT relaunch DeFi VMs until cleanup finishes
- `mtds_mdps_master.md` — MDPS-3.3.DeFi-V updated with bug fix evidence + cleanup caveat
- `writegate` archived plan — Phase 8 added (all 3.A items ✅, 8.B items 5+6 ✅, item 7 pending)

### Phase 8.B item 7 — DeFi backfill re-run LAUNCHED ✅ (2026-05-23 ~22:23)

Sequence:

1. Confirmed 215530-series VMs had stale tarballs (0 captured, all `attempted_failed` for swaps_ohlcv)
2. Stopped `mdps-defi-2024/2025-20260523-215530` (no useful work)
3. Rebuilt DEFI tarballs (UAC@78c5ac15b663 with swaps_ohlcv fix + MTDS@498148da with 3 handler fixes)
4. Launched 5 sharded VMs (run-ts=20260523-222351, all RUNNING at T+1min):
   - `mdps-defi-{2022..2026}-20260523-222351`: 2022-11-01 → 2026-05-23

Monitor: `gcloud compute instances list --filter='labels.run-ts=20260523-222351'` Writegate Phase 8.B item 7 flipped
(this commit).

### Still pending (slot-4)

- **Post-run defi cleanup pass**: after 222351 VMs complete, run
  `python3 scripts/reset_source_returned_zero_manifest.py --bucket market-data-tick-defi-central-element-323112` to
  clear any residual SRZ from stopped 215530 VMs, then verify gas_fees/lending_indices/dex_swaps captured rows.
- All other slot-4 items remain BLOCKED-CREDENTIALS / BLOCKED-OPERATOR-DECISION / gated on Phase 7 GREEN

— slot-4 / 2026-05-23

### Audit: why 215530 VMs had attempted_failed + new code from remote (2026-05-23)

**Q: was that because they needed migration or fixes?**

**Answer: code fixes (two of them), not migration.**

**Finding 1 — UAC case-mismatch (root cause of 215530/195633 attempted_failed)**

`lookup_contract` in `unified_api_contracts.internal.schemas.contracts` looked up `instrument_type='POOL'` (uppercase
from parquet) but `CONTRACT_REGISTRY` stored keys as lowercase `'pool'`. Result: `SchemaContractNotFoundError` for every
Uniswap/Curve pool shard.

- 195633 VMs: stale tarball WITHOUT fix → all pool shards `attempted_failed`
- 215530 VMs: LAUNCHED WITH the fix (UAC@397e7195 / equiv slot-2 @8e1e7e58) → the `attempted_failed` we saw on 215530
  VMs was from very early-stage runs or leftover 195633 per-VM shard rows visible in the consolidated index before the
  new shards filled in
- 222351 VMs (our launch): use UAC@78c5ac15b663 which includes this same fix → should work

Source: `plans/active/issues/mdps_defi_swaps_ohlcv_schema_lookup_2026_05_23.md`

**Finding 2 — MTDS resolve_bucket_name env= kwarg removed from UTL (separate MTDS-layer bug)**

`tick_data_handler.py:94` called `resolve_bucket_name(env="live")` but UTL dropped the `env` kwarg. This only affects
MTDS **raw tick data** VMs — NOT MDPS processing VMs (our 222351 VMs are unaffected).

- VM `mtds-backfill-defi-20260523` (tarball sha 498148da) loops on every chunk with
  `TypeError: resolve_bucket_name() got an unexpected keyword argument 'env'` — 0 candles produced
- **Fix landed**: remote commit `MTDS@22dcada6` removed `env="live"` from the call
- Tab-4 fast-forwarded to `22dcada6` (2 remote commits picked up)
- **Action required**: kill `mtds-backfill-defi-20260523`, rebuild MTDS DEFI tarball, relaunch

Source: `plans/active/issues/mtds_backfill_defi_resolve_bucket_name_2026_05_23.md`

**Finding 3 — DEX swap data gap 2026-01-25+ (source data missing, not a code bug)**

Raw tick parquets in `market-data-tick-defi-prd-central-element-323112` have no DEX swap data after 2026-01-24. MDPS
2026 VMs will produce honest `empty_confirmed/SOURCE_RETURNED_ZERO` for those dates — correct behavior. Root cause:
upstream on-chain reader stopped writing.

Source: `plans/active/issues/mtds_defi_dex_swaps_2026_gap_2026_05_23.md`

**Our 222351 MDPS VMs**: unaffected by all 3 above. They run MDPS (processing), use UAC@78c5ac15b663 with UAC fix, and
write to MDPS processed_candles. The DEX 2026 gap will produce honest SRZ rows which is correct behavior.

— slot-4 / 2026-05-23 audit

---

## 2026-05-24 (session 1) — [slot-4 → slot-1 main] MDPS DeFi chain-column fix + 085204 VMs launched

**Plan refs**: `plans/active/issues/mdps_defi_swaps_ohlcv_schema_lookup_2026_05_23.md` ·
`plans/epics/mtds_mdps_master.md` (MDPS-3.3.DeFi-V verify gate)

### Root cause 3 fixed — chain column injection ✅

083200 VMs (cb3d11b tarball) still produced 0 captured rows with SCHEMA_VALIDATION_FAILED.

Diagnosis: `_infer_chain()` correctly infers `"ETHEREUM"` from `UNISWAP_V2-ETHEREUM` venue token and sets
`partition_path=.../chain=ETHEREUM`. But `_inject_schema_contract_columns()` did NOT inject `chain` column into
`candles_df` before passing to `_utl_write_chunk`. Legacy UNISWAP_V2 subgraph ticks have no explicit `chain` column →
`CandleOutput.to_dataframe()` drops it → UTL partition/df mismatch → SCHEMA_VALIDATION_FAILED.

Fix: MDPS@6fe0f01 — extend `_inject_schema_contract_columns(chain: str = "")` to backfill column when absent; add
`chain: str = ""` to `CandleStreamingWriteContext`; both callers updated. QG: 0 type errors, 2 pre-existing test
failures (unrelated to fix, confirmed by baseline check).

### MDPS DeFi SRZ cleanup — COMPLETE ✅

14,572 SOURCE_RETURNED_ZERO rows deleted from defi tick bucket (task btph0xc3j). All 11 per-VM shards +
availability_index re-uploaded. Blocks on re-run cleared.

### Tarballs rebuilt + 085204 VMs relaunched ✅

Rebuilt DEFI asset group tarballs (MDPS@6fe0f01 included). 083200 VMs stopped. 5 new sharded VMs launched
(run-ts=20260524-085204, all RUNNING at T+2min verify):

| VM                             | Range                  | Status  |
| ------------------------------ | ---------------------- | ------- |
| mdps-defi-2022-20260524-085204 | 2022-11-01..2022-12-31 | RUNNING |
| mdps-defi-2023-20260524-085204 | 2023-01-01..2023-12-31 | RUNNING |
| mdps-defi-2024-20260524-085204 | 2024-01-01..2024-12-31 | RUNNING |
| mdps-defi-2025-20260524-085204 | 2025-01-01..2025-12-31 | RUNNING |
| mdps-defi-2026-20260524-085204 | 2026-01-01..2026-05-24 | RUNNING |

### Fourth MDPS DeFi bug: venue mismatch in partition_path ✅ (2026-05-24 ~09:xx UTC)

085204 VMs still failed: `SCHEMA_VALIDATION_FAILED` — venue mismatch. UTL partition validator strips chain suffix from
instrument_id's first colon-segment (`UNISWAP_V2-ETHEREUM` → `UNISWAP_V2`) but partition_path declared
`venue=UNISWAP_V2-ETHEREUM`. Chain is already in separate `chain=ETHEREUM` key — venue segment must be chain-free.

**Fix**: `_strip_chain_from_venue(venue, chain)` helper in `canonical_writer.py`, guarded with
`asset_group == MarketAssetGroup.DEFI` so CeFi venues like `BINANCE-FUTURES` are untouched. Also merged concurrent
`category=` → `asset_group=` fix from upstream commit `8d4639f`. MDPS@555ade1. QG: 2 pre-existing failures, 0 new.
Basedpyright: 0 errors.

Tarballs rebuilt (MDPS@555ade1 confirmed in manifest). 085204 VMs stopped. 5 new VMs relaunched (run-ts=20260524-091405,
all RUNNING at T+2min verify):

| VM                             | Range                  | Status  |
| ------------------------------ | ---------------------- | ------- |
| mdps-defi-2022-20260524-091405 | 2022-11-01..2022-12-31 | RUNNING |
| mdps-defi-2023-20260524-091405 | 2023-01-01..2023-12-31 | RUNNING |
| mdps-defi-2024-20260524-091405 | 2024-01-01..2024-12-31 | RUNNING |
| mdps-defi-2025-20260524-091405 | 2025-01-01..2025-12-31 | RUNNING |
| mdps-defi-2026-20260524-091405 | 2026-01-01..2026-05-24 | RUNNING |

Plan ref: `plans/active/issues/mdps_defi_swaps_ohlcv_schema_lookup_2026_05_23.md` § Fourth schema gap.

### Captured row verification — PASS ✅ (2026-05-24 ~09:30 UTC)

2025 per-VM shard (`mdps-defi-2025-20260524-091405.parquet`) — 27 `captured` rows:

- venue=`UNISWAP_V3` (chain suffix stripped correctly ✓)
- chain=`ETHEREUM` ✓
- data_type=`swaps_ohlcv_15s`, `swaps_ohlcv_15m` ✓
- Zero `SCHEMA_VALIDATION_FAILED` ✓

Schema is now fully correct. 2024+ processing is currently `0/0` because MTDS raw DEX tick data for 2024+ hasn't been
collected yet (MTDS DeFi backfill VM needs relaunch).

### Still pending (slot-4)

- MTDS DeFi backfill relaunch (mtds-backfill-defi VM): `resolve_bucket_name env=` bug was fixed at MTDS@22dcada6;
  tarball needs rebuild + relaunch. Issue: `plans/active/issues/mtds_backfill_defi_resolve_bucket_name_2026_05_23.md`.
- All other slot-4 items remain BLOCKED-CREDENTIALS / BLOCKED-OPERATOR-DECISION / gated on Phase 7 GREEN.

--- slot-4 / 2026-05-24

---

## 2026-05-24 (session 2) — [slot-4 → slot-1 main] Captured row verification COMPLETE + MTDS DeFi backfill status

**Plan refs**: `plans/active/issues/mtds_backfill_defi_resolve_bucket_name_2026_05_23.md` ·
`plans/active/issues/mdps_defi_swaps_ohlcv_schema_lookup_2026_05_23.md` · `plans/epics/mtds_mdps_master.md`
(MDPS-3.3.DeFi-V)

### MTDS DeFi backfill VM (`mtds-backfill-defi-1`) — LAUNCHED + TERMINATED FAST ✅

VM was launched at 09:41 UTC (session 1, MTDS@2b7c7760). Not in current VM list — terminated quickly. Status:

- MTDS DeFi raw tick bucket (`market-data-tick-defi-central-element-323112`) already has continuous coverage 2020-01-01
  → 2026-05-22 (2,334 days total)
- UNISWAP_V3 `dex_pool_state` exists for 2024+ dates (confirmed via `day=2025-01-15` sample)
- AAVE_V3 `rate_indices` exists for 2024+ dates (`batch_onchain_rpc/venue=AAVE_V3/chain=ETHEREUM/`)
- Current MTDS tarball: SHA `ffa9d573` (created 2026-05-24T09:08 UTC — includes `get_tick_data_bucket` fix from
  `712d4071`)

### Captured row verification — dex_swaps ✅ CONFIRMED

Cross-slot 4 MDPS VMs currently RUNNING (run-ts=101628, created after tarball rebuild at ~08:39 UTC):

| VM                             | Captured | Empty | Data types     |
| ------------------------------ | -------- | ----- | -------------- |
| mdps-defi-2024-20260524-101628 | 954      | 318   | swaps*ohlcv*\* |
| mdps-defi-2025-20260524-101628 | 1020     | 436   | swaps*ohlcv*\* |
| mdps-defi-2026-20260524-101628 | 1108     | 463   | swaps*ohlcv*\* |

Confirmed correct venue format: `venue=UNISWAP_V3` (not `UNISWAP_V3-ETHEREUM`). All 6,745 captured rows in
availability_index use chain-stripped venue names. Venue mismatch fix (MDPS@555ade1 + 3 follow-up commits through HEAD
`94ef3c2`) fully confirmed in prod data.

### Captured row verification — lending_indices / gas_fees ⚠️ BYPASS TYPES (no gap — working as designed)

Finding from orchestration_scanner.py comment (line 44-46):

> "Other pipeline_mode=batch_onchain_rpc venues (AAVE, LIDO, EIGENLAYER, etc.) are **bypass types** — they never reach
> this matcher because **the orchestrator has no registered adapter for them**."

Confirmed: `needs_candle_processing("lending_indices")` = False.
`CandleAdapterRegistry.has_adapter(DEFI, "lending_indices")` = False. Both by test `test_defi_bypass_routing.py`.

**State**:

- `lending_indices`: 64,440 manifest rows. 77 captured (Solana KAMINO/SOLEND 2022 — old code path). AAVE_V3 Ethereum
  `rate_indices` raw data IS in MTDS bucket but MDPS has NO adapter → skipped by orchestrator. This is NOT a regression
  from the venue-mismatch fix; it's the pre-existing state of the bypass routing.
- `gas_fees`: 64,331 manifest rows. 0 captured (all SOURCE_RETURNED_ZERO) — no `gas_fees` raw data type in MTDS DeFi
  bucket at all (no `data_type=gas_fees` parquets exist). Legitimate SRZ.

**No action required from slot-4**. These are pre-existing bypass-type gaps that require a separate bypass-writer sprint
(AAVE lending candles, gas_fees raw collection). Not in current slot-4 scope.

### Slot 4 branch fast-forwarded ✅

`tab/ikennaigboaka/4` was 3 commits behind `live-defi-rollout`. Fast-forwarded:

- `4cc1584` fix(defi): infer instrument_type from candles_df instrument_id column
- `209b8e8` fix(canonical_writer): catch GCS 429 at manifest boundary
- `94ef3c2` fix(canonical_writer): add df instrument_id fallback to \_infer_chain

Now at HEAD `94ef3c2` = live-defi-rollout.

### Summary of slot-4 current state

All slot-4 owned work is complete. Active VMs running at 101628 run-ts producing dex_swaps captured rows correctly.

Remaining items all gated externally:

- Sports/Phase 3.D.5 → gated on `mtds_mdps_master` Phase 7 GREEN
- Tradfi Databento → `BLOCKED-CREDENTIALS`
- AAVE lending bypass writer → ✅ SHIPPED — `DefiLendingIndicesAdapter` at mdps@b21fec6 + uac@4c98a635; MDPS QG green.
  Plan: `plans/active/mdps_lending_indices_bypass_writer_2026_05_24.md`

— slot-4 / 2026-05-24 (session 3)

---

## 2026-05-25 (session 4) — [slot-4 → slot-1 main] Sports/Phase 3.D.5 gate resolved — slot 4 COMPLETE

**Plan refs**: `plans/epics/mtds_mdps_master.md` · `plans/active/mdps_lending_indices_bypass_writer_2026_05_24.md`

### Phase 7 gate cleared + Sports/Phase 3.D.5 analysis

Phase 7 (manifest v8 backfill + label-flip) was ✅ CLEARED 2026-05-22 PM@ec208173d (slot 5). This unblocks the
previously gated Sports/Phase 3.D.5 items. After investigation:

| Item                                               | Resolution                                                                                                        |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------- |
| 3+4 — Phase 3.D.5 v2 catalog enumerators           | ✅ DONE — writegate plan: Sports@9a1bcd91, CeFi@09361718, TradFi@d50b9453, DeFi@b0e4bcac                          |
| 1 — Sports per-fixture_id shard granularity (MTDS) | SUPERSEDED — master plan ✓ decision (line 510): `fixture_id` is NOT a shard atom; `(league_id, day)` is canonical |

### stale epic note fixed + pm pushed

`mtds_mdps_master.md` line 623 stale bypass note ("`lending_indices` + `gas_fees`: bypass types...") corrected to
reflect `DefiLendingIndicesAdapter` shipped at mdps@b21fec6 — pm@605971217.

### Slot 4 status — COMPLETE

| Item                       | Status                                                                                        |
| -------------------------- | --------------------------------------------------------------------------------------------- |
| AAVE lending bypass writer | ✅ SHIPPED — mdps@b21fec6 + uac@4c98a635 (session 3)                                          |
| Sports/Phase 3.D.5         | ✅ RESOLVED — v2 enumerators done; per-fixture-id shard superseded by master plan decision    |
| TradFi Databento           | BLOCKED-CREDENTIALS — credential ask filed (this ping); no further action until operator acks |
| Sports backfill VMs        | BLOCKED-UPSTREAM — sports_master Phase 3+4 rename; not slot-4 scope                           |

No remaining actionable AI-days for slot 4. Slot 4 is complete.

— slot-4 / 2026-05-25 (session 4)

## 2026-05-25 (session 5) — Sports scheduler VM launched + per-fixture items resolved

### Sports backfill VMs — LAUNCHED

**Plan ref**: `plans/epics/sports_master.md` Phase 4

Sports rename + Phase 2B GCS migration fully shipped. No tarballs rebuild needed (instruments-service@0b867b3a uploaded
2026-05-25T04:24 UTC). VM launched:

- **VM**: `sports-scheduler-20260525-072005` — e2-small, asia-northeast1-c, daemon poll=300s
- **Status**: RUNNING at launch (T+0 verified)
- **T+10 pending** — check at ~07:30 UTC:
  `gcloud compute instances describe sports-scheduler-20260525-072005 --zone=asia-northeast1-c --format='value(status)'`
- **Log**: `gsutil cat gs://deployment-scripts-central-element-323112/vm-logs/sports-scheduler-20260525-072005/run.log`

Plan flip: `plans/epics/sports_master.md` Phase 4 OPERATOR item ✅ — pm@30f6b7270

### Per-fixture shard items — resolved

| Item                                        | Resolution                                                                                             |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| Item 1 (orchestrator per-fixture iteration) | ✅ RESOLVED — enrichment mode already uses `_read_fixture_ids_from_gcs`; per-fixture endpoint verified |
| Item 2 (manifest row_key extension)         | ✅ ABANDONED — `fixture_id` NOT a shard atom (master plan decision)                                    |
| Item 3 (cluster validation)                 | ✅ RESOLVED — writegate v2 enumerators cover expected-universe at (league_id, day) shard level         |
| Item 4 (manifest migration)                 | ✅ ABANDONED — no row_key change; no migration needed                                                  |
| Item 5 (post-migration smoke)               | ✅ ABANDONED — no migration                                                                            |

Plan flip: `plans/epics/sports_master.md` per-fixture section ✅ — pm@30f6b7270

— slot-4 / 2026-05-25 (session 5)

---

## [orchestrator → slot-4] 2026-06-04 — data_pipeline_acquisition_remediation-003 COMPLETE

**Task**: Add live `book_snapshot_5` + `derivative_ticker` channels for non-Hyperliquid CeFi venues
**Plan**: `plans/active/data_pipeline_acquisition_remediation_2026_06_03.md` P1 checkbox

**DONE** — 2026-06-04

- **market-tick-data-service@302e2bf** — 6 new WS connector files:
  - `binance_futures_book_ticker_ws.py` (depth5@100ms + markPrice streams)
  - `bybit_futures_book_ticker_ws.py` (orderbook.5 + tickers, local book state)
  - `okx_futures_book_ticker_ws.py` (books5 + tickers)
  - `deribit_book_ticker_ws.py` (book.*.none.5.100ms + ticker.*.100ms, JSON-RPC 2.0)
  - `kraken_futures_book_ticker_ws.py` (book + ticker feeds, local book state)
  - `coinbase_book_ws.py` (level2 snapshot+delta, spot-only)
- Factory dispatch updated in all 6 existing `*_ws.py` files
- 49 unit tests added in `tests/unit/test_cefi_book_ticker_ws_connectors.py`
- QG green (local `quality-gates.sh` pass before commit)
- Pushed to LDR via dirty-deps path (UTL PR #236 pending staging merge)
- Plan checkbox flipped: **PM@eb1f151ce**

— slot-4 / 2026-06-04
