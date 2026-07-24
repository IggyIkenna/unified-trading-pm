---
doc_type: issue
title: TradFi docs↔reality contradictions (35 verified) — pending application
summary:
  35 adversarially-verified doc contradictions vs the migration/backfill/purge reality, from workflow wf_40c3b4fe, to
  APPLY after the content-migration lands (so migration-complete claims reflect post-apply reality). Plus 4 stale codex
  docs (Massive-purge-pending) + non-canonical-path-inventory register patch from the tradfi reconciliation.
status: open
nature: record
asset_group: tradfi
created: 2026-07-21
tags: [tradfi, docs-reconciliation, canonical, massive, mvp]
related: [tradfi_consolidated_closeout_2026_07_18, data_pipeline_reconciliation_tradfi_2026_07_21]
stage: [data]
repos: [unified-trading-pm]
scope: [engineer, admin]
parent_epic: tradfi_master
assigned_vm: NA
execution_scope: local-only
priority: P2
drift_direction: advance-code
depends_on: []
source: docs-reconciliation workflow wf_40c3b4fe (2026-07-21)
locked_by:
resolved_by:
---

# TradFi docs↔reality contradictions — 35 verified, pending application

**Full machine-readable detail: `tradfi_docs_reconciliation_findings_2026_07_21.json`** (doc/line/claim/reality/fix per
finding).

Source: docs-reconciliation workflow `wf_40c3b4fe` (7 find agents + adversarial verify, 2026-07-21). Each finding was
adversarially verified against live state. **Apply AFTER the content-migration** so "migration complete" edits reflect
the post-`--apply` id-form reality (nuance: paths/catalogue canonical since this session; historical content id-form was
30.8% → being migrated). Massive-purged premise VERIFIED (0 objects everywhere). Storage
`_migration_backup`/`_quarantine`/`_needs_attribution` now DELETED (register patch below reflects that).

> **✅ 32/34 checkboxes applied 2026-07-21 (`unified-trading-pm@935de9424` + `unified-trading-pm@1dd1a22fd`)** — the
> SAFE subset (no content-migration-complete claims). **3 remain `- [ ]` and are DEFERRED on purpose**: L97 + L460 in
> `tradfi_consolidated_closeout_2026_07_18.md` and L237 in `canonical-cutover-register.md` — each would assert the
> manifest/raw-tick-parquet `instrument_id` CONTENT column is canonical/migrated, which is still false (content id-form
> measured 30.8% canonical; only GCS paths + the catalogue are genuinely canonical so far). Apply those 3 once the
> content-migration lands.

## Findings by document (apply the `fix` field from the JSON)

### `plans/active/tradfi_consolidated_closeout_2026_07_18.md` — 5 (P1,P1,P1,P2,P2)

- [ ] **[P1 L97]** Ground-truth verdict header: 'the id-canonicalisation is barely started on the derivative id columns
      (manifest + catalogue)... tradfi is done on filenames only' → FIX: Insert a supersede banner immediately under the
      '## Ground-truth verdict' header (line 97) and relabel the table as a dated baseline. Suggested: '> **SUPERSEDED
      2026-07-21 — this 2026-07-18 baseline verdict is historical.** The canonicalisa
- [ ] **[P1 L460]** Phase B migration items still unchecked: '- [ ] [DATA] P0. Migrate the catalogue (Surface A)'
      (L460), '- [ ] [DATA] P0. Migrate the live manifest (Surface B)' ( → FIX: Flip the four false-negative boxes to
      checked with the evidence already in the Progress Log, and leave L507 open. Specifically: L460 -> "- [x] ✅ [DATA]
      P0. Migrate the catalogue (Surface A) — DONE/verified live (Progress Log ticks 5 + 11):
- [x] **[P1 L124]** MVP universe: '**CME BTC + ETH futures + options** (crypto index products on the TradFi venue)'. →
      FIX: Change L124 from "CME BTC + ETH futures + options (crypto index products on the TradFi venue)" to "CME
      BTC/ETH/MBT/MET futures — FUTURES ONLY, no crypto options (operator 2026-07-21 'no CME option for BTC and ETH';
      option_underliers={ES})". — applied unified-trading-pm@935de9424
- [x] **[P2 L297]** Open todo '- [ ] [BACKEND] P1. Massive dual-source shape parity + consolidator dedup-key omits
      source (tradfi_massive_dual_source_2026_05_28.md Phase 4b — a sil → FIX: Strike both Massive dual-source items as
      MOOT. At L297-299 remove the open '- [ ] [BACKEND] P1 Massive dual-source shape parity + consolidator dedup-key
      omits source' todo (or mark it ~~struck~~ MOOT), and at L977-982 remove/strike the 'Rou — applied
      unified-trading-pm@935de9424
- [x] **[P2 L278]** Open '- [ ] [BACKEND] P0. The ENTIRE tradfi availability index has schema_version typed as STRING —
      every un-forced MTDS tradfi run dies with TypeError', and op → FIX: Flip both boxes and cite the Progress Log
      evidence. L271: `- [x] ✅ [INFRA] P1. yfinance missing from the MTDS image — RESOLVED mtds@d8dc04e1 (Dockerfile
      pinned yfinance==0.2.66 install after -e . --no-deps + image-import-smoke extended to i — applied
      unified-trading-pm@935de9424

### `plans/active/tradfi_massive_dual_source_2026_05_28.md` — 4 (P1,P1,P1,P2)

- [x] **[P1 L7]** status: active — an entire plan whose reason for existing is to add Massive (formerly Polygon.io) as a
      live second TradFi OHLCV source alongside Databento, co-m → FIX: Add a top-of-doc SUPERSEDED banner immediately
      after the frontmatter (line 38): '🔴 SUPERSEDED 2026-07-19/07-21 — Massive REMOVED as a TradFi source (operator
      2026-07-19: Databento = batch SoT, Yahoo = daily; dropped from SOURCE_PRIORITY, ru — applied
      unified-trading-pm@935de9424
- [x] **[P1 L281]** 'Priority downgraded P0→P2 2026-07-12 … Databento is PRIMARY … Massive remains a documented fallback
      — no rebuild urgency.' (Phase 4b framing: Massive is a live → FIX: Replace the 2026-07-12 P0->P2 downgrade note
      (lines 278-281) with a SUPERSEDED note: "Massive (formerly Polygon.io) was fully REMOVED as a tradfi source
      2026-07-19 (operator ruling: Databento = batch SoT, Yahoo = daily) — deleted from SOURC — applied
      unified-trading-pm@935de9424
- [x] **[P1 L283]** Open `- [ ]` todos to (Phase 4b) rebuild MassiveTradfiRestConnector to emit canonical columns, wire
      it into the TradFi adapter orchestrator/factory so it is rea → FIX: In
      plans/active/tradfi_massive_dual_source_2026_05_28.md, mark the four open Phase 4b Massive-integration todos
      (lines 283, 287, 289, 292 — rebuild MassiveTradfiRestConnector, wire it into the orchestrator/factory,
      cross-source parity test, — applied unified-trading-pm@935de9424
- [x] **[P2 L359]** Open `- [ ]` todos to build the S3 flat-files bulk-backfill ingester writing
      record_captured(source='massive'), fix backfill_tradfi_source_column.py to stamp ma → FIX: Add a top-of-plan
      banner marking the dual-source-Massive premise OBSOLETE and retire the affected todos rather than leaving them
      open/active. Specifically: (1) Line 359-367 [SCRIPT] S3 flat-files ingester writing `record_captured(source="ma —
      applied unified-trading-pm@935de9424

### `plans/active/data_completion_tradfi_2026_07_15.md` — 4 (P1,P1,P1,P2)

- [x] **[P1 L316]** - [ ] [DATA] P1. NEXT — run Massive tradfi reference capture → regenerate catalogue → unblock gate-b
      (VM, requires live MASSIVE_API_KEY). ... run IS instrument → FIX: Mark the line-316 todo obsolete rather than
      silently deleting (plan hygiene): convert to `- [x]` or a struck note reading: "SUPERSEDED 2026-07-21 — Massive
      removed as a tradfi source (operator ruling 2026-07-19, uac@a2beed46) and subscripti — applied
      unified-trading-pm@935de9424
- [x] **[P1 L86]** All migration todos are unchecked `- [ ]`: 'C0 ONE bundled walk on the tradfi _index + objects'
      (re-version to v9, category=->asset_group=), 'E4 Dry-VM → full-V → FIX: Reconcile
      data_completion_tradfi_2026_07_15.md against the plan that actually executed the scope
      (tradfi_v9_stage1_finish_2026_07_06.md): (1) Add a DONE/SUPERSEDE banner at the top and set `superseded_by:
      tradfi_v9_stage1_finish_2026_07_06. — applied unified-trading-pm@935de9424
- [x] **[P1 L166]** COVERAGE GAP ... tradfi equities/ETF (NYSE/NASDAQ) were NEVER genuinely ingested — only the 0-row
      Massive dry-run placeholders exist; the real day= hive corpus → FIX: Reframe this todo from a never-ingested gap
      to in-progress ingestion: note the Databento equity/ETF backfill is running (2026-07-21, SPOT) — NASDAQ g01-g05 +
      NYSE g01-g05, ohlcv_1m + ohlcv_1s, window 2023-2026 (XNAS/XNYS Databento discovery — applied
      unified-trading-pm@935de9424
- [x] **[P2 L99]** multi-source cells (the 6 databento+massive/yahoo/barchart cells) emit two rows ... Notify
      tradfi_massive_dual_source to flip its Task -031 ... Stamp source via → FIX: Rewrite the three
      massive/barchart-bearing items to Databento+Yahoo only and mark the dead dual-source cross-links: — applied
      unified-trading-pm@935de9424

1. Line 97-101 (C-source RIDER): drop "the 6 databento+massive/yahoo/barchart cells" — state that every tradfi `_index`
   row

### `plans/epics/tradfi_master.md` — 4 (P1,P1,P2,P2)

- [x] **[P1 L174]** Sourcing = DATABENTO-FIRST (`SOURCE_PRIORITY[("tradfi", *)] = ["databento", "massive"]`; Massive is
      the secondary co-source per `tradfi_massive_dual_source`). → FIX: Rewrite the line-174 Scope sourcing clause to
      reflect databento-only TradFi sourcing. Replace:\n\n\"**Sourcing = DATABENTO-FIRST**
      (`SOURCE_PRIORITY[(\"tradfi\", *)] = [\"databento\", \"massive\"]`; Massive is the secondary co-source per `t —
      applied unified-trading-pm@1dd1a22fd
- [x] **[P1 L797]** P1 — important; post-current-gate: [`tradfi_massive_dual_source_2026_05_28`] status: active ·
      estimate: 7 cal AI-days · title: TradFi dual-source — Massive alon → FIX: Flip
      plans/active/tradfi_massive_dual_source_2026_05_28.md to `status: superseded`, add a SUPERSEDE banner at the top
      citing the 2026-07-19 Massive-as-TradFi-source removal + 2026-07-21 purge (SSOT
      codex/02-data/tradfi-databento-sourcing-ss — applied unified-trading-pm@1dd1a22fd
- [x] **[P2 L88]** Workstream-routing table routes manifest/pipeline_mode canonicalisation + phantom-audit residual to
      [`tradfi_manifest_canonicalisation_2026_06_01`] '(pre-existi → FIX: In the workstream-routing table (line 88),
      update the "Home" cell to point to the archived, superseded path and relabel it. Change the link from
      `[tradfi_manifest_canonicalisation_2026_06_01](../active/tradfi_manifest_canonicalisation_2026_ — applied
      unified-trading-pm@1dd1a22fd
- [x] **[P2 L195]** MVP backtest scope: S&P 500 (CME ES + ES.OPT + SPY) + BTC/ETH ETFs (NASDAQ IBIT, NASDAQ ETHA) +
      crypto futures (CME MBT, CME MET) + CBOE BTC options on IBIT + V → FIX: Edit tradfi_master.md line 195 (the "MVP
      backtest scope" paragraph). Drop "+ CBOE BTC options on IBIT" (option_underliers={ES} ONLY per
      /codex/02-data/mvp-scope-canonical.md:88 — no crypto/non-ES options in MVP). Change "VIX 15m" to "VIX FUT —
      applied unified-trading-pm@1dd1a22fd

### `/codex/02-data/availability-manifest-and-data-status.md` — 4 (P1,P1,P2,P3)

- [x] **[P1 L2059]** tradfi source-wiring row: "✅ WIRED | databento, massive | Multi-source; SOURCE_PRIORITY[("tradfi",
      data_type)] = ["databento", "massive"]; select_primary_availa → FIX: Rewrite the tradfi row (line 2059) to: Status
      ✅ WIRED; Source values wired = `databento` (batch source-of-truth) + `yahoo` (daily/rolling: ohlcv_1m/15m/24h,
      KRX Korean underliers + FX/treasury indices); Notes = Live SOURCE_PRIORITY per _sou — applied
      unified-trading-pm@1dd1a22fd
- [x] **[P1 L692]** Two full subsections present a live "TradFi dual-source (Databento + Massive)" capture model —
      §"Per-source capture_status semantics (v9 TradFi dual-source)" (l → FIX: Add a SUPERSEDED banner atop both
      §"Per-source capture_status semantics (v9 TradFi dual-source)" (line 692) and §"Per-source capture_status
      semantics in a dual-source cell" (line 2071): "SUPERSEDED 2026-07-21 — Massive removed as a TradFi s — applied
      unified-trading-pm@1dd1a22fd
- [x] **[P2 L365]** Temporary-state table + line 734: v9 source-column backfill for TradFi parquets is "pending operator
      drain per tradfi_massive_dual_source_2026_05_28.md Phase 5 → FIX: Re-scope the pending-drain assertions, not the
      historical citations. (1) Line 365 temporary-state table: remove/close this row — the TradFi v9 source column is
      no longer a pending Massive dual-source drain. Replace with a RESOLVED note: "Tr — applied
      unified-trading-pm@1dd1a22fd
- [x] **[P3 L552]** AvailabilityRecord.source comment (line 552) enumerates current values "databento | massive | yahoo
      | barchart | tardis"; §Universal source column (line 634) re → FIX: At line 552, annotate the closed-set so
      massive/barchart read as legacy-only: `source: str = "" # current tradfi: "databento" | "yahoo" | "tardis";
      "massive" (removed 2026-07-19) / "barchart" (retired 2026-06-24) appear ONLY on legacy rows — applied
      unified-trading-pm@1dd1a22fd

### `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` — 2 (P1,P2)

- [x] **[P1 L79]** G5 governing sequence / WAVE 5 / G5 sub-plan registry frame the remaining post-migration work as
      'Resume BACKFILLS -> 100% honest coverage ... + massive/polygon → FIX: Strike the "massive/polygon cost-swap vs
      databento" clause from all four locations, leaving the backfills→100%-honest-coverage work intact: line 79 → "G5
      Resume BACKFILLS → 100% honest coverage (UI drilldowns shrink to minor)"; line 216 → — applied
      unified-trading-pm@935de9424
- [x] **[P2 L763]** R5-fix-6 (open todo): 'wire or retire the mtds MassiveTradfiRestConnector ... either wire it into
      the tradfi dispatch behind the source axis or delete it ... (I → FIX: Mark R5-fix-6 (lines 763-766) DONE, not
      merely reworded — the connector and all Massive runtime routing are already deleted. Replace with: "- [x] ✅
      [DATA] P2. R5-fix-6 — MassiveTradfiRestConnector RETIRED. Massive removed as a tradfi source — applied
      unified-trading-pm@935de9424

### `plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` — 2 (P2,P3)

- [x] **[P2 L57]** Instrument / MTDS / MDPS data-clean ... is owned by tradfi_manifest_canonicalisation_2026_06_01
      (manifest v9 + pipeline_mode + honest-absence) and tradfi_massiv → FIX: In
      plans/active/tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md: (1) Repoint the data-clean owner in the
      pointer block (lines 55-60) and in related: frontmatter (lines 17-18) from
      ./tradfi_manifest_canonicalisation_2026_06_01.md (n — applied unified-trading-pm@935de9424
- [x] **[P3 L117]** VIX features (compute_vix_features()) require VIX OHLCV from Barchart/Yahoo; those are not in the
      IS-driven features pipeline (CLAUDE.md: 'VIX 15m: Barchart pre → FIX: In line 117-118, drop the stale
      VIX-cash-index sourcing sub-claim and the nonexistent CLAUDE.md quote. Keep the real, still-standing MDPS-gap
      blocker (futures_chain/options_chain data_types absent from the TRADFI MTDS bucket), but replace t — applied
      unified-trading-pm@935de9424

### `/codex/02-data/non-canonical-path-inventory.md` — 2 (P1,P2)

- [x] **[P1 L198]** Row 10: "market-data-tick-tradfi-prd-{pid}/ — all objects under pipeline_mode=batch_massive …
      1,696,166 objects. HUMAN-ONLY HARD STOP. Removing read-recognition → FIX: Move row 10 out of the
      `no-migrate-first` delete-candidate table into the "Entry retired 2026-07-20 (kept for audit trail)" section
      (alongside row 29), recording the disproof per the maintenance contract's rule 4. Retirement text: audit cla —
      applied unified-trading-pm@1dd1a22fd
- [x] **[P2 L199]** Row 11 (no-migrate-first): tradfi legacy path shapes — MIGRATE_HYPHEN 100,698, MIGRATE_NONHIVE_EQ
      920, MIGRATE_CHAIN_ADDQM 528,961, MIGRATE_SINGLE_RENAME 389,70 → FIX: Retire Row 11 from the `no-migrate-first`
      (pending) section and move it to a retired/audit-trail entry (or annotate in place) with post-migration evidence:
      migration run `20260720-120911`, 20/20 shards ORPHAN=0, MIGRATE 848,886 objects → ca — applied
      unified-trading-pm@1dd1a22fd

### `/codex/02-data/canonical-cutover-register.md` — 2 (P1,P2)

- [ ] **[P1 L237]** §4: "The tradfi corpus is canonical on filenames only — the manifest measured 0 canonical rows
      across all years, and the physical migration --apply is operator- → FIX: Rewrite §4's closing paragraph
      (canonical-cutover-register.md:237-239) to reflect migration COMPLETE. Replace "canonical on filenames only /
      manifest measured 0 canonical rows / --apply operator-gated / expected non-canonical wholesale" wit
- [x] **[P2 L232]** §4 carve-out: "batch_massive — Massive was removed as a tradfi source 2026-07-19, but batch_massive
      PipelineMode + possible_manifest read-recognition is KEPT un → FIX: Update §4
      (canonical-cutover-register.md:232-235): change the batch_massive carve-out from an active "read-recognition is
      KEPT until the gated GCS purge completes / suppressing is not optional" mandate to a historical note — "Massive
      GCS pu — applied unified-trading-pm@1dd1a22fd

### `plans/active/issues/canonical_closeout_open_questions_2026_07_18.md` — 1 (P2)

- [x] **[P2 L125]** C2a parked as an OPERATOR-RULING-NEEDED open question: 'instrument_type COLUMN case — UPPER vs
      lowercase ... REC: confirm UPPERCASE column (it shipped) -> then → FIX: Add a resolution banner to C2a mirroring
      the Section D pattern already in this same doc. Replace the C2a bullet (lines 126-130) with a "✅ RULED 2026-07-20
      (operator ruling D1): UPPERCASE column, catalogue wins" header, strike the old "REC: — applied
      unified-trading-pm@935de9424

### `plans/active/tradfi_multisource_backfill_2026_06_22.md` — 1 (P3)

- [x] **[P3 L257]** 'VIX cash-index DELETE + Databento floor-clip landed 2026-06-23 (instruments-service@814b14a);
      GCS-object delete `--apply` running.' → FIX: Update line 256-257 to reflect completion, matching the resolved
      todos above it: "VIX cash-index DELETE + Databento floor-clip landed 2026-06-23 (instruments-service@814b14a);
      GCS-object delete `--apply` completed 2026-06-23 (1,621 objects — applied unified-trading-pm@935de9424

### `plans/active/canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md` — 1 (P2)

- [x] **[P2 L157]** Open todo: 'TradFi single-leg @LIN/@INV-YYYYMMDD extension - NOT implemented, needs its own
      dedicated fix plan ... TradFi single-leg dated derivatives (FUTURE/O → FIX: Flip line 157's todo from open to
      done/superseded: "- [x] [SCRIPT] P1 (filed 2026-07-09, DONE 2026-07-18 — superseded by the TradFi canonical path
      migration). TradFi single-leg @LIN/@INV-YYYYMMDD extension for FUTURE/OPTION — IMPLEMENTED vi — applied
      unified-trading-pm@935de9424

### `plans/archive/2026_07/tradfi_v9_stage1_finish_2026_07_06.md` — 1 (P2)

- [x] **[P2 L439]** - [ ] [DATA] P0. BLOCKED-PREREQUISITES (2026-07-13, slot-5). E7 verify — cf_manifest_audit ...
      CF-1..CF-12 all GREEN ... 2 genuine REDs remain (CF-1 v4 tail + C → FIX: Line 439 (E7-verify todo): reconcile the
      stale BLOCKED-PREREQUISITES marker. Its named blocker — task 10's fleet-drain + v4-tail re-stamp — CLOSED
      2026-07-16 (corpus now 100% schema_version=9, blank pipeline_mode=0, blank source=0, per task — applied
      unified-trading-pm@935de9424

### `/codex/02-data/pipeline-mode-partition.md` — 1 (P3)

- [x] **[P3 L136]** Closed-set values table lists "batch_barchart — VIX 15m historical preload (2020-01-02 →
      2025-11-12)" as a live PipelineMode value. → FIX: In the closed-set values table, drop the `batch_barchart` row
      (or replace it with a retirement note): "`batch_barchart` — RETIRED 2026-06-24; Barchart removed as a source. VIX
      15m now aggregates from VX futures via Databento (XCBF.PITCH → ` — applied unified-trading-pm@1dd1a22fd

### `/codex/02-data/four-surface-reconciliation-procedure.md` — 1 (P3)

- [x] **[P3 L369]** §6 tradfi bullet: "batch_massive read-recognition is retained until the gated GCS purge, so a
      batch_massive path found on READ is an accepted exception, not a f → FIX: Update the §6 tradfi bullet (lines
      369-370) to reflect that the gated GCS purge is COMPLETE (executed 2026-07-20 RUN_TS=20260720-193849, 1,701,422
      batch_massive objects removed, 0 collateral — see resolved issue massive_purge_blocked_databe — applied
      unified-trading-pm@1dd1a22fd

## Plus, from the tradfi reconciliation (data_pipeline_reconciliation_tradfi_2026_07_21):

- [x] **[P0 DOCS]** 4 codex docs still call the Massive purge PENDING/human-only — it EXECUTED (0 objects everywhere):
      `non-canonical-path-inventory.md` row 10, `reconciliation-finding-taxonomy.md` AE-4,
      `gcs-and-manifest-delete-safety-protocol.md` §3.3, `tradfi-databento-sourcing-ssot.md`. — applied
      unified-trading-pm@1dd1a22fd
- [x] **[P1 DOCS]** `non-canonical-path-inventory.md` register patch: row 10 RETIRE (massive purged); row 11 counts
      (hyphen→2); row 22 `_quarantine` (was ~15,813 → now DELETED 2026-07-21); row 24 `_needs_attribution` (DELETED);
      `_migration_backup_2026_07_09` (DELETED, was 158,808 obj/35.91GB). — applied unified-trading-pm@1dd1a22fd
