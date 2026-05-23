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

### defi 12-month v2 apply-write — COMPLETE ✅

**Status**: `DONE` (operator acked 2026-05-23; all 4 chunks ran within ~15 minutes total)

Actual: 3,599 instruments, 21 data_types. Fixed tz-normalization bug in `_enumerate_v2_defi`
(instruments-service@b02943be) — defi catalog `available_from_datetime` is tz-aware (+00:00) while window timestamps
were tz-naive. Runs were blazing fast (~8-10s each vs 90min projected — frozenset at 1.6M not 150M).

| Chunk | VM name                | Date range            | Rows      |
| ----- | ---------------------- | --------------------- | --------- |
| d1    | slot4-defi-d1-20260523 | 2026-02-21→2026-05-23 | 6,953,268 |
| d2    | slot4-defi-d2-20260523 | 2025-11-22→2026-02-20 | 6,747,741 |
| d3    | slot4-defi-d3-20260523 | 2025-08-23→2025-11-21 | 6,617,793 |
| d4    | slot4-defi-d4-20260523 | 2025-05-23→2025-08-22 | 6,429,696 |

**Total: 26,748,498 rows** across 4 per-VM shards on GCS
(`market-data-tick-defi-central-element-323112/_index/per_vm/`). Consolidator merging within ~5min each. Plan item
updated: writegate@2539 (PM this commit).

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
