---
doc_type: plan
title:
  Instruments Foundation — Phase 0 cross-cutting foundations (observability, honest-coverage v2, canonical-form
  single-SoT)
summary:
  Split out of instruments_foundation_completeness_2026_06_24.md (2026-07-24 line-cap remediation, 4-way split,
  operator- approved). Owns the cross-cutting Phase-0 prerequisites — observability wiring, Honest-Coverage v2,
  cumulative-drawdown metric, expected-universe oracle design, consolidation reconcile, drilldown-correctness guard,
  verification discipline, silent-cap audit, depth-aware re-fetch, cost/entitlement reason class, and the canonical-form
  single-SoT GCS migration — that GATE 0 requires before any per-AG G1→G5 gate work (cefi/tradfi children) can cross G2.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos:
  [
    deployment-api,
    deployment-service,
    instruments-service,
    market-data-processing-service,
    market-tick-data-service,
    unified-api-contracts,
  ]
scope: [engineer, admin]
tags:
  [instruments, catalogue, honest-coverage, data-correctness, observability, canonical-form, foundation, cross-cutting]
related:
  [
    instruments_foundation_completeness_2026_06_24,
    instruments_cefi_g1_g5_gate_execution_2026_07_24,
    instruments_tradfi_g1_g5_gate_execution_2026_07_24,
    /codex/02-data/instruments-foundation-and-catalogue-completeness.md,
  ]
created: "2026-07-24"
last_updated: "2026-08-17"
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: design
estimate_baseline_ai_days: 8
estimate_calibrated_ai_days: 5
assigned_role: data_engineering
drift_direction: advance-code
locked_by:
locked_since:
context_scope: [/plans/active/instruments_foundation_completeness_2026_06_24.md, /codex/02-data/honest-coverage-model.md, /codex/05-infrastructure/deployment-observability.md, instruments-service/scripts/measure_honest_coverage.py, unified-api-contracts/unified_api_contracts/canonical/crosscutting/honest_coverage.py, unified-api-contracts/unified_api_contracts/canonical/coverage_exclusions.py]
supersedes:
superseded_by:
depends_on: []
source:
  [
    "plan-hygiene split of instruments_foundation_completeness_2026_06_24.md, 2026-07-24 (operator-approved, see
    plans/active/issues/plan_line_cap_remediation_2026_07_23.md row #14)",
  ]
---

# Instruments Foundation — Phase 0 cross-cutting foundations

**Split provenance (2026-07-24):** this plan was extracted from
[`instruments_foundation_completeness_2026_06_24.md`](instruments_foundation_completeness_2026_06_24.md) (the umbrella)
as part of the operator-approved plan-line-cap remediation
(`plans/active/issues/plan_line_cap_remediation_2026_07_23.md`, row #14 — 4-way split). This plan owns the
**cross-cutting Phase 0 prerequisites** — build once, reused by every asset group. GATE 0 (below) must sign off before
the per-AG children ([cefi](instruments_cefi_g1_g5_gate_execution_2026_07_24.md) /
[tradfi](instruments_tradfi_g1_g5_gate_execution_2026_07_24.md)) can cross their own G2. The umbrella
(`instruments_foundation_completeness_2026_06_24.md`) stays the process SSOT + rolling status index across all 4
children.

**Codex SSOT (the standard this plan executes):** `/codex/02-data/instruments-foundation-and-catalogue-completeness.md`.

---

## Phase 0 — cross-cutting foundations (block G2; build once, reused by every AG)

- [x] ✅ [INFRA] P0. **DONE 2026-08-09/16 (batch2 reconciliation)** — Observability wiring (§0.5) for every
  instruments/MTDS backfill VM + roll-up job. Root cause: TradFi backfill VMs never survived long enough to be
  observable (`VM_TASK=cefi-backfill` matched no dispatch branch, self-deleted in 2-4min). Fixed —
  `deployment-service@acf965d96` (+ peer `deployment-service@c99ab99b`) extends `launch-tradfi-backfill-vm.sh` +
  `launch-targeted-options-chain-backfill.sh`'s CME-OPTIONS/CBOE-VIX-OPTIONS shards with `VM_TASK=mtds-backfill`.
  Sports/prediction needed no fix (already correctly routed). Was: EXTRACTED 2026-08-09 →
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (archived).
- [x] ✅ [SCRIPT] P0. **DONE 2026-08-09/16 (batch2 reconciliation)** — Layered coverage via the Honest-Coverage v2 SSOT
  surfaced through API + UI — `deployment-api@5a345de22` (byte-for-byte passthrough of the 3 named fields, proven by 2
  new unit tests), `deployment-ui@c55ed8256` (Layer-2 headline+badge gated on Layer-1; Vitest synthetic-gap fixture;
  `pw:L2` regression spec `data_status_coverage_labels.spec.ts`, 5/5 specs green). Was: EXTRACTED 2026-08-09 →
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (archived).
- [ ] [SCRIPT] P0. **Cumulative-drawdown health metric (§1.2)** — per venue, the cumulative-instruments-ever-seen
      series; any negative day-over-day delta = a hard defect (flag + block). Active-count drops must net to a typed
      reason (cefi/tradfi delisting; DeFi delisting OR `NOT_ENOUGH_TVL`). DoD: drawdown count per venue surfaced; target
      zero. **Reconciled 2026-07-28 — STILL OPEN (2 of 5 AGs have a per-AG script; not generalised, not write-time
      wired).** `instruments-service/scripts/` carries `defi_cumulative_drawdown_guard_2026_06_25.py` and
      `cefi_cumulative_drawdown_guard_2026_06_27.py` (the latter "generalising the defi one" per its own plan text); the
      cefi one is PROD-RUN VERIFIED to surface the canonical BINANCE-FUTURES 678→47 thin-day drop (cefi child plan
      G1.2). But no tradfi/sports/prediction equivalent exists (0 grep hits), the two existing scripts are separate
      per-AG copies rather than one cross-cutting metric, and cefi's own G1.2 status is `[~]` PARTIAL — the thin-day
      verdict is not yet wired into the capture-time write path (a partial venue day still risks writing as `captured`
      rather than routing to `attempted_failed` at write time). Leaving `[ ]` open.
- [ ] [DESIGN] P1. **Expected-universe ORACLE design (§2.1)** — the `depth_coverage` denominator: (a) per-instrument
      true genesis from **venue truth** (not circular first-seen); (b) **time-varying futures expiry/listing rules** per
      venue, versioned by effective-date, in UAC. Ship **Tier-A proxy** first (labelled), **Tier-B truth** is the
      completion bar. DoD: design doc + the UAC rule-registry shape; sourcing decision for venue-truth genesis.
      **Reconciled 2026-07-28 — STILL OPEN, unbuilt.** No design doc found under `codex/02-data/` or in any child plan
      naming an expected-universe/depth oracle design; the cefi child plan's own 2026-06-25 build-sequence explicitly
      lists "IS expected-universe DAY seeding (venue-day) + depth-expected" as a still-to-build step, not a completed
      one. Leaving `[ ]` open.
- [ ] [SCRIPT] P0. **Consolidation reconcile (§2.2)** — incremental for steady-state + **scoped `--force`/reconcile**
      after any backfill + periodic, reconciling **actual shards vs the materialised expected-universe** to _discover_
      unexpected-missing shards (→ 0% in day_coverage + re-fetch queue). Never a blind whole-corpus `--force` (clip the
      window; purge discipline vs the 32Gi OOM). DoD: a deleted/absent expected shard is surfaced as a gap, not silently
      merged-around. **Reconciled 2026-07-28 — STILL OPEN, unbuilt.** No `--force`/reconcile-vs-expected-universe script
      or mechanism found in `instruments-service/scripts/`; the cefi child plan's own build-sequence lists
      "consolidation reconcile-vs-expected" as item (5) of an as-yet-undriven sequence, not shipped. Leaving `[ ]` open.
- [ ] [SCRIPT] P0. **Drilldown-correctness guard (§2.3)** — (1) UI renders the SSOT value, never recomputes; (2)
      **reconciliation guard**: independent raw-GCS recompute == manifest/SSOT/UI (ε=0), wired as a QG step + watchdog →
      `#data-pipeline-alerts` on drift; (3) manifest-freshness watchdog + per-cell click→GCS traceability. DoD: a seeded
      manifest/raw divergence trips the guard; cockpit number is proven == ground-truth. **Reconciled 2026-07-28 — STILL
      OPEN, unbuilt.** No ε=0 reconciliation-guard QG step or watchdog found; the cefi child plan's own canonical- form
      audit (2026-06-25) explicitly lists "the §2.3 ε=0 reconciliation guard wiring" among the still-remaining
      canonical-form work, and a separate cefi finding (G1.3 follow-up) notes the guard "must treat split↔glued as
      equivalent" for on-chain-perp venues **until** it is aligned — i.e. describes a future state, not a live guard.
      Leaving `[ ]` open.
- [x] ✅ [SCRIPT] P0. **DONE 2026-08-09/16 (batch2 reconciliation)** — Verification discipline: captured∩expected
  KEY-OVERLAP gate, not raw count (§6.1/§6.3) — `instruments-service@ef635e32`
  (`scripts/backfill_completion_key_overlap_gate_2026_08_09.py`: `evaluate_backfill_completion()` requires both
  `run.log EXIT_STATUS==0` AND ≥1 previously-pending expected key now `captured`; reproduces + fails on the DeFi
  silent-stall signature; 8/8 unit tests green). Was: EXTRACTED 2026-08-09 →
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (archived).
- [x] ✅ [SCRIPT] P0. **DONE 2026-08-09/16 (batch2 reconciliation)** — Silent-cap source audit + `FetchEvidence`
  paging sweep across every data source, done independently twice (converging on the same candidate set) —
  `instruments-service@b8668094` (Betfair `listMarketCatalogue` top-1000 cap: event-type-scoped pagination +
  `ADAPTER_PAGE_CAP_HIT` observability), alongside 2 CRITICAL RPC-error-swallow bugs, a Lighter pagination defect, 5
  Graph skip-cursor additions, 3 cap-exhaustion warnings, and the Polymarket top-2000 cap fix shipped the same session
  (full set: `/plans/archive/issues/silent_cap_source_audit_remaining_findings_2026_08_09.md`, remaining lower-priority
  items tracked there). Was: EXTRACTED 2026-08-09 → `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`
  (archived).
- [ ] [SCRIPT] P0. **Depth-aware re-fetch trigger (§7.5) — NOT blanket `--force`, NOT just unexpected-missing** —
      re-fetch ONLY `{missing/EU, attempted_failed, captured-but-instrument_count < expected_depth}` (the
      shallow-capture a plain skip-if-exists misses); needs the §2.1 depth oracle for `expected_depth`; the §2.2
      reconcile-vs-expected pass _discovers_ the set. DoD: a synthetic shallow `captured` cell is re-queued, a good full
      cell skipped, no blind whole-corpus `--force`. **Reconciled 2026-07-28 — STILL OPEN, unbuilt.** Zero grep hits for
      `expected_depth` across `instruments-service`, `market-tick-data-service`, or `unified-api-contracts` — this item
      is correctly blocked on the still-unbuilt §2.1 depth oracle (item 4 above) and the still-unbuilt §2.2 reconcile
      pass (item 5 above), matching its own stated dependency. Leaving `[ ]` open.
- [x] ✅ [DESIGN] P1. **DONE 2026-08-09/16 (batch2 reconciliation)** — Cost/entitlement-boundary reason class (§6.4):
  registered the TradFi Databento cost-boundary case in `COVERAGE_EXCLUSIONS` — `unified-api-contracts@c839a47d`. CME
  `trades`+`tbbo` entries, `reason=SUBSCRIPTION_GAP`, `start=2020-01-01`/`end=2025-08-06`; live-verified via
  `expected_coverage()` returning `EXPECTED_UPSTREAM_OUT_OF_BOUNDS` in-window. Was: EXTRACTED 2026-08-09 →
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (archived).
- [ ] [DATA] P0. **Canonical-form single-SoT GCS migration (IS + MTDS, every AG) — NO two sources of truth (operator
      2026-06-24).** Any GCS data in a non-canonical **schema** (`schema_version` < v9 / drifted fields), **path**
      (missing `pipeline_mode={mode}_{source}/`/`asset_group=` keys, legacy sibling trees, glued `PROTOCOL-CHAIN`), or
      **naming** (asset_group not in `{cefi,defi,tradfi,sports,prediction}` lowercase · venue/chain not canonical — defi
      `venue=PROTOCOL`+`chain=X` · instrument_id not canonical) is **MIGRATED to the one canonical form** — never a
      dual-write / legacy tree left beside the canonical one. The **manifest (`_index/availability_index`) must line up
      with the coverage SSOT ↔ `/data-status` ↔ deployment-UI** (the §2.3 reconciliation guard proves it ε=0).
      **Single-walk discipline** — bundle schema/path/rename into ONE corpus walk per AG (a new whole-corpus walk is
      review-blocking otherwise). **defi is the DONE exemplar** (this session: glued→canonical `_index` reconcile +
      legacy `dex_pools/`/`lending_indices/` sweep + the catalogue-filter cell-key alignment). Generalise to cefi ·
      tradfi · sports + instruments-service. Reconcile with the existing canonicalisation cluster (don't fork):
      `pipeline_mode_partition_migration` · `*_manifest_canonicalisation_2026_06_01` ·
      `master_data_canonicalisation_migration_catalogue_2026_06_07` · `migration_verification_orphan_safety_2026_06_10`.
      DoD per AG: schema_version distribution == v9 (measured, not the constant) · a path-prober finds **0**
      legacy-shape objects · asset_group/ venue/chain/instrument_id canonical · 0 dual-SoT sibling trees ·
      manifest↔index↔data-status↔UI ε=0 (§2.3 guard green). **Runs per-AG inside G1→G3** (the manifest must be
      canonical + aligned BEFORE its coverage number means anything) — this is foundation-correctness, not cleanup.

🚦 **GATE 0 — NOT RECORDED SIGNED OFF** (operator sign-off on Phase 0 before any backfill launches; all ten Phase 0
items above remain `- [ ]` and no "GATE 0 SIGNED OFF" line exists anywhere in this doc — only recurring "Awaiting GATE 0
sign-off"). **(was: unannotated — corrected 2026-07-14, doc-reconciliation vr2#119: the Progress Log nonetheless records
the freeze-gap backfill VMs launched under the narrower operator 2026-06-26 near-term-target directive, plus the much
larger G2-G4 backfills below reconciled as SIGNED OFF 2026-07-06 — i.e. downstream gates crossed while this prerequisite
gate was never recorded satisfied. Flagging the sequencing gap for an operator ruling rather than asserting a GATE 0
sign-off that isn't evidenced.)**

**Reconciliation pass 2026-07-28** (`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` AUDIT todo): re-checked
every one of the 10 items above plus the 2 folded-in checkboxes below against the cefi/tradfi child plans' Progress Logs
and live code (grep-verified file/symbol existence, not assumed). **Verdict unchanged — GATE 0 correctly stays NOT
SIGNED OFF, and all 10 items correctly stay `- [ ]`.** But "stale checkbox, work already done elsewhere" is NOT what's
happening here: real, substantial per-AG progress exists (cefi's own layered-coverage SSOT, cumulative-drawdown guards,
and cost/entitlement reason-class _mechanism_ have genuinely shipped), it just doesn't clear any single item's full DoD
— each remaining item is missing either (a) fleet-wide/cross-AG breadth (built for cefi+defi only, not
tradfi/sports/prediction), (b) UI/API surfacing on top of an already-shipped backend SSOT, or (c) is simply unbuilt. See
each item's own "**Reconciled 2026-07-28**" annotation above for the specific evidence and citation. No item was
re-implemented here — this is reconciliation only, per this todo's own scope.

---

## Kickoff + cross-AG canonical-form migration history (moved verbatim from the umbrella, 2026-07-24)

- 2026-06-24 — Reset to foundation-first (operator). cefi MTDS paused. cefi + tradfi instruments ground-truth audits
  done (read-only). Codex standard drafted + heavily enriched (gated order · observability precondition · layered
  coverage · expected-universe oracle · cumulative-drawdown · DeFi-TVL · §6 cross-AG borrows · §7 tradfi/cefi-dated
  nuances · §8 retirement · §9 tradfi baseline). This plan filed + completed to match the standard (Phase-0
  §6/§7.5/cost-boundary items; cefi G3b dated-instruments; expanded defi/tradfi/sports + retirement; tradfi+defi
  starting state). **Awaiting GATE 0 sign-off.**

- 2026-06-24 — defi: catalogue/manifest correctness-clean + the skip-cap cursor fix shipped (mtds@08b45468); G4
  catalogue-as-filter implementation IN FLIGHT (overlap-flat until it lands) — tracked in the DeFi plan, the G4 exemplar
  for this standard.

- 2026-06-25 — **DeFi foundation migration STARTED (opus autonomous, full operator authority; DeFi drained — verified 0
  running defi backfill VMs, only cefi-live/tradfi/prediction/watchdog run, none write the defi buckets).** Ground-truth
  re-audit (read-only) corrected several stated-start figures: the IS PRD `_index` is **187,850 rows** (NOT 7,362 — that
  was the catalogue), with TWO populations — `data_type=instrument-catalog` (145,467 venue-day rows) + blank-data_type
  (42,383 per-instrument-type rows, stale-stops 2025-02-01, incl. **119 cefi `EXTENDED-STARKNET` contaminants**). The
  ENVLESS dual bucket (145,467) is exactly PRD's instrument-catalog subset (stale projection). **Canonical-form conflict
  RESOLVED** (Findings-Triage big): UAC `ALL_DEFI_VENUES` is glued-only, but the deployment-api drilldown
  (`data_status/defi.py`) splits each registry entry into `(PROTOCOL,CHAIN)` and matches the manifest's **bare
  `venue=PROTOCOL`+`chain=X`** (its `_is_legacy_defi_venue_row` drops glued+blank-chain as legacy) → **bare+chain is
  unambiguously canonical**; the registry does NOT need flipping; `canonicalize_defi_manifest_venue_2026_06_14.py`
  (canonicalizes to GLUED) is SUPERSEDED by this collapse.
  - **Step 1 SNAPSHOT ✅** — IS PRD/ENVLESS `_index` + catalogue + MTDS defi `_index` →
    `_index/snapshots/ pre_migration_2026_06_25.parquet` (+ `prod/snapshots/catalog.pre_migration_2026_06_25.parquet`).
    Regression baseline fingerprints (per venue×data_type captured counts) recorded. KEY INVARIANT: IS PRD captured
    **cells** = 174,926.
  - **Step 2 COLLAPSE ALL drift → bare canonical ✅ APPLIED**
    (`instruments-service/scripts/ collapse_defi_drift_to_canonical_2026_06_25.py`, ruff-green; per-blob
    `.driftcanon.bak`). before→after, live prod: `_index` 187,850→176,186 rows, **glued 76,904→0, ghost 0→0**, chain
    100% populated, captured **cells** 174,926→174,926 (ε=0; 11,664 dropped rows were glued+bare twins of the SAME
    canonical cell, merged captured-wins); `prod/catalog.parquet` glued 1,001→0, ghost 197→0, chain 100% populated;
    `_index/per_vm/_legacy_seed` glued/ghost→0. Caught+fixed a dedup bug mid-build (first version kept BOTH captured
    twins → duplicate canonical cells; fixed to one-row-per-cell, status-priority captured>empty>failed>EU, richest
    instrument_count; ε=0 asserted on captured CELLS).
  - **EMITTER ROOT-FIX SHIPPED** (IS@92084d5c3, QG-green 95s, quickmerged): the glued treadmill is the by_date snapshot
    — the daily writer writes the parquet `venue` column GLUED (`AAVE_V3-ARBITRUM`) with NO `chain` column for non-pool
    rows, and the GCS path is `venue=AAVE_V3-ARBITRUM/` (no chain= segment). The MANIFEST column split
    (`writers.py::_write_venue` parse_defi_venue → bare+chain) is ALREADY correct in current code (so the live glued
    manifest rows were LEGACY accumulation, cleaned by Step 2). The CATALOGUE was re-drifting because
    `build_instrument_catalogue.py` only split venue for POOL rows; non-pool DeFi (lending/lst/staking/perp) passed the
    glued parquet venue through. **Fix**: `_canonical_bare_venue_chain` (ghost-fix + known-chain-suffix split) on the
    non-pool fallthrough — no-op for bare-canonical + non-DeFi (BINANCE-FUTURES/API_FOOTBALL untouched, verified).
    **VERIFIED (coordinator #3):** a bounded catalogue regen from the actual glued by_date snapshots → **0 glued / 0
    ghost, chain 100% populated**. Treadmill broken on the catalogue side.
  - **NO-REGRESSION PROVEN (coordinator #1):** the "+30,719" was a wrong-baseline compare (vs stale ENVLESS 145,467, not
    true PRD 187,850). Against the snapshot: 187,850→176,186 (DECREASE of 11,664 = glued+bare twins merged); snapshot
    CAPTURED rows collapsed to canonical keys = **174,926 distinct canonical captured cells == live 174,926** (ε=0); 0
    live captured cells absent from snapshot; 0 snapshot canonical captured cells lost; 0 duplicate canonical-cell rows
    post-apply. attempted_failed 1,260 preserved exactly.
  - **STILL TODO** (remaining sequence): junk `1970-01-01` genesis = **15 RAYDIUM POOL rows** (epoch-zero from a missing
    on-chain creation ts) → Step 4 venue-truth genesis (don't mask with a hasty proxy). `available_from` already uniform
    ISO-string (no mixed-type defect; the sort-crash was `available_to` str+None). Step 3 one-bucket: ENVLESS `_index`
    is a stale SUBSET of `-prd-` (no env-less-only data) BUT retiring needs every reader confirmed on `-prd-` first (the
    DURABLE gotcha #1 + MTDS `check_reader_writer_bucket_parity` gate) — code-verify before delete. Then: venue-truth
    genesis · recency 06-22→today · 6 uncovered-venue subgraphs · GCS by_date path-split (Step 5, writers.py:113) · cefi
    `EXTENDED-STARKNET` (119) purge (retirement) · clean backfill.

- 2026-06-25 — **SESSION HANDOFF (clean boundary, NO destructive op half-applied; snapshots intact). Banked + verified
  this session; next session resumes from this + the prober ground-truth.**
  - **Step 3 reader-parity VERIFIED (code, read-only):** every defi instruments READER resolves env-short `-prd-` via
    `resolve_bucket_name(kind="instruments-store", asset_group="defi")` — `_defi_manifest.py` (via
    `assert_reader_writer_bucket_parity`, the gotcha-#1 fix is LIVE), `_instruments_metadata.py` (3 sites),
    `_catalogue_filter.py`, `defi_catalog_reader.py`. **0 readers on env-less.** So the ENVLESS bucket DELETE is
    unblocked BUT NOT YET DONE (left for the fresh session per handoff — it's a destructive 70,151-by_date-obj delete;
    must first prove those objs are redundant-vs-`-prd-`, then snapshot-then-delete). ENVLESS `_index` (145,467 rows /
    75,649 glued) is moot once deleted.
  - **MTDS `_index` glued FIXED ✅** (`--target market-data` venue-only-no-dedup; 6 `UNISWAP_V4-ETHEREUM`→`UNISWAP_V4`
    +chain=ETHEREUM, rows UNCHANGED 7,390,534, captured 1,971,546 preserved, per-blob `.driftcanon.bak`). **CRITICAL
    SAFETY CATCH:** the generic IS-tuned `collapse_frame` dedup applied to MTDS would have dropped **345,219 rows** —
    the MTDS `_index` natural key is WIDER (pipeline_mode varies in 27,116 dup-groups, capture_status in 345,015) → a
    venue-ONLY rewrite (no dedup) is the only safe op there. Never run the IS dedup on the MTDS manifest.
  - **ZERO-GLUED PROBER baseline (record — run `scripts/audit_defi_zero_glued_2026_06_25.py` to refresh):** | surface |
    glued | ghost | state | |---|---|---|---| | IS-PRD `_index` | 0 | 0 | ✅ Step 2 | | IS-PRD catalogue | 0 | 0 | ✅
    Step 2 | | IS-PRD per_vm seed | 0 | 0 | ✅ Step 2 | | MTDS defi `_index` | 0 | 0 | ✅ this session | | MTDS
    raw_tick_data PATH | 0 | 0 | ✅ already canonical (MTDS writer fixed earlier) | | IS-ENVLESS `_index` | 75,649 | 0 |
    → Step 3 DELETE (stale bucket) | | **IS by_date PATH** (`venue=AAVE_V3-ARBITRUM/`) | 56/day (ALL) | 0 | **REMAINING
    — Step 5 path-migration** | | **IS by_date COLUMN** (in-file `venue`, no chain col on non-pool) |
    2,620/15-file-sample | 0 | **REMAINING — Step 5** | | **UAC `ALL_DEFI_VENUES`** | 156 | 0 | **REMAINING — glued-form
    registry; flip-or-document decision** |
  - **REMAINING for the fresh session** (NONE started; no half-applied destructive op): (a) **Step 3** ENVLESS bucket
    delete (readers verified `-prd-`; snapshot-then-delete after redundancy proof). (b) **Step 4** venue-truth genesis
    (15 RAYDIUM `1970-01-01` + scan for other epoch-zero). (c) **Step 5** the by_date PATH+COLUMN migration (the big
    one: 2,345 days × ~56 venues, glued path→`venue=PROTOCOL/chain=X/` + in-file venue→bare + add chain col) AND the
    `writers.py:113` path-split EMITTER fix (the catalogue-read-side fix shipped IS@1e97931; the writer path-split is
    NOT done — by_date still WRITES glued). (d) **UAC registry** flip-to-bare-or-document (operator bar = no glued
    vocabulary; the drilldown splits it to `(PROTOCOL,CHAIN)` pairs so it's an internal join key, not a path/manifest/UI
    surface — decision pending). (e) recency 06-22→today · 6 uncovered subgraphs · `EXTENDED-STARKNET` 119 cefi purge ·
    clean backfill. **Snapshots intact** (`_index/snapshots/pre_migration_2026_06_25.parquet` in all 3 buckets +
    per-blob `.driftcanon.bak`). Banked this session: IS@1e97931 (Step-2 collapse + catalogue emitter fix), IS HEAD
    (MTDS venue-only collapse + prober).

- 2026-06-25 — **Reversible drivable work remaining (no operator gate): G1.g MVP tags; G1.a.2 massive.py §7.1 (the
  actual OPRA/I:VIX pollution source); G1.a.3 router.py dead non-billable config. Operator-gated: retirement GCS purge ·
  G2 fleet · G1.f DXY key-migration. cefi-coordinated: G1.h §7.3 `available_to`/per-venue-`latest_day` (still the cefi
  agent's unstarted item-4; AG-agnostic, blocks G3 for both AGs). CI-verified: IS#629 merged-staging-green; UAC + MTDS
  Tier-C-draining.**

---

## Folded-in cross-cutting items (I-1 consolidation 2026-06-26 — cross-cutting portion; tradfi portion moved to the tradfi child)

### From `proper_instrument_catalogue_lifecycle_rollup_2026_06_04` (archived)

- [x] ✅ [INFRA] P0. **DONE 2026-08-09/16 (batch2 reconciliation)** — Rebuild the IS daily-definition producer for
  TradFi/sports/prediction. **Finding**: sports and prediction already had live, prod-verified daily producers (stale
  premise); only TradFi was broken — `uts-prod-instruments-service-tradfi-t1-recon` crashed on
  `UndeclaredTradfiVenueError('FRED')` daily for ≥5 days. Fixed — `instruments-service@cad1d322` declares FRED as a
  24/7 venue alongside FX. Live-verified via manual rebuild + execution:
  `Evidence: cloudbuild=00f77c23-2ce0-4371-b203-8cedbede3404` (SUCCESS), execution
  `uts-prod-instruments-service-tradfi-t1-recon-kfkzj` completed exit 0. Was: EXTRACTED 2026-08-09 →
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (archived).
- [x] [INFRA] P1. ✅ **Wire the lifecycle roll-up to trigger on every IS instruments update (per-AG).** TF authored
      (deployment@98bee4b, `lifecycle_catalogue_scheduler.tf`); REMAINING = `terraform apply` + T+10min per-AG execution
      verify. (MIGRATED FROM: `proper_instrument_catalogue_lifecycle_rollup_2026_06_04`.) — deployment-service@c1d2e3e6
      (weekly self-heal + terraform apply landed, reachable on origin/live-defi-rollout); per-AG apply verified per
      `instruments_catalogue_incremental_rollup_2026_06_29.md`.
- [x] [INFRA] P1. ✅ **Make the cloud lifecycle-catalogue-regen job log, then fix the real error** — add
      `print(..., flush=True)` bisection markers per `run_rollup` phase (or bootstrap stdout logging), localize the
      job-only failure (suspect grpc/pyarrow/GCS native init or a job-env gap), fix it. Until fixed the catalogue
      refreshes via the local-run path. Repo: instruments-service + deployment-service (job env). (MIGRATED FROM: same —
      supersedes the earlier "diagnose fast-fail" bullet.) — RESOLVED: root cause was full-history-walk timeout, not a
      grpc/pyarrow init bug; fixed by instruments-service@b0596d0c incremental engine (reachable on
      origin/live-defi-rollout).
- [x] ✅ [CODE] P1. **DONE 2026-08-09/16 (batch2 reconciliation) — stale premise, no code change needed.** All 5
  asset groups already adopt the granularity-aware catalogue producer: the cited pre-history-rewrite commit
  (live-defi-rollout equivalent `instruments-service@8c1875e0`) introduced the shared shape-aware `_row_data_types()`
  filter into all 5 `_enumerate_v2_*` functions in the same commit, sports (per-league) and prediction (per-cqg-bundle)
  included — the todo's own "cefi/tradfi/defi only" claim did not survive contact with the code. Live-verified against
  real prod catalogues/manifests for all 5 AGs 2026-08-09 (scan-only, no full-corpus walk). Was: EXTRACTED 2026-08-09 →
  `cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md` (archived).

---

## Autonomous run results — 2026-06-26 (5-AG instrument foundation)

**Shipped:** EU-seeding `instruments-service@f739a41` · Yahoo G10 FX `UAC@526f3c83`/`IS@97cdf92` (Treasuries+DXY already
existed) · all-AG producer crash fix `IS@d279615` · Databento concurrency-cap (singleton→cap 20) `deployment@96be3dc` ·
catalogue PYTHONUNBUFFERED `deployment@c90cf97` · tradfi cleanup batch (`UAC@4ad54282`, `deployment@62a6645`,
`MDPS@91192b9`, `MTDS@dd313086`).

**Producers (daily):** cefi 06:00 de-hardcoded ✅; defi 00:00 (`uts-prod-instruments-service-t1-recon`→DEFI) ✅. The
all-AG crash is fixed in `d279615` but the cloud image is STALE (06-23) and the IMAGE BUILD is IAM-BLOCKED for the agent
identity (`gcloud builds submit` forbidden from `central-element-323112_cloudbuild`). So restoring the 00:00 job to
all-AG (→ tradfi/sports/prediction daily producers) + EU-seeding on daily cloud runs are BLOCKED on an operator/CI image
rebuild. Interim daily capture covered by today's backfills.

**Per-AG (instrument DEFINITIONS + CATALOGUE):**

- **cefi** ✅ DONE — backfill gap-free (0 absent June days) + catalogue regenerated `prod/catalog.parquet` 345,920 rows
  (MVP 271,673), monotonic ACCEPT, promoted 13:34Z.
- **defi** — backfill gap-free ✅; catalogue regen RUNNING (`bztf6gn3r`).
- **tradfi** — 9-shard def fleet + CME ohlcv ES 2020-2026 (futures+options 1s+1m) + CL/GC/HG/NG/NQ/SI + FX/NASDAQ/NYSE
  running under the cap; catalogue regen pending def-backfill (`--asset-group tradfi`).
- **sports** ✅ IS defs current to 06-26 (+3,097; historical 2014-2020 VMs ETA 06-27). Catalogue needs the
  granularity-aware producer (`--by-date-prefix`). MTDS odds BLOCKED-SCHEMA (manifest missing v9 `available_at` →
  `sports_manifest_canonicalisation_2026_06_01`).
- **prediction** ✅ IS defs current to 06-26 (+300; PM 1269 + Kalshi 262); MTDS Polymarket → 06-25 ✅. Catalogue needs
  per-cqg producer. Kalshi MTDS historical BLOCKED-STRUCTURAL (Kalshi IS writes `canonical_question_group` paths, not
  `day/venue=KALSHI`). PREDICTION excluded from producer `cleanup()` flush_groups (pre-existing — track).

**NEXT:** verify defi catalogue → cefi+defi DONE (priority); tradfi catalogue when def-backfill finishes;
sports/prediction catalogues need granularity-aware producers; operator/CI image rebuild to unblock all-AG daily
producer + cloud EU-seeding.

### Catalogues — ALL 5 AG regenerated + promoted (2026-06-26, monotonic ACCEPT)

cefi 345,920 · defi 7,416 (100% MVP-tagged via defi tag-all `instruments-service@665966b`) · tradfi 814,012 · sports
1,608 · prediction 1,204,816. Sports/prediction need NO special flag (builder auto-handles league/cqg grain). FLAGS:
prediction MVP=0 (UAC `is_mvp` gates on a `market_group` column the catalogue doesn't carry — UAC gap); tradfi MVP 895 /
sports MVP 2 (narrow screens).

### Rigorous cefi/defi SILENT-GAP audit (per venue×day / venue×chain×day, inception→present)

cefi: 486 absent cells — REAL gap 2026-03-01→05-20 (BYBIT-SPOT/COINBASE-FUTURES/DERIBIT-COMBO, backfill
`cefi-instr-all-20260626-161800` launched) + COINBASE/OKX bare-alias artifacts (116d ea) + small
(LIGHTER/EXTENDED-STARKNET/PACIFICA). defi: 2293 absent — mostly stray-genesis artifacts (SUSHISWAP_V3-BASE genesis-2021
vs Base-2023; TRADER_JOE_V2 genesis-2020) + subgraph-blocked stragglers (EXTENDED/CAMELOT_V3/UNISWAP_V3-BASE → should be
attempted_failed). Agent af6f764 driving genuine-gap→0 + reconciling artifacts; "gap-free" bar = every shard×day
represented (captured or correctly-typed empty), NOT just recent-month.

### Standing requirements (operator 2026-06-26)

- Images MUST auto-build on main + auto-deploy (today: manual → stale; CI-build agent a9cd863 wiring main-trigger
  build→push :latest→update Cloud Run jobs, failures→#data-pipeline-alerts). IMAGE REBUILD IAM-blocked for agent
  identity → CI is the fix + bypass.
- All batch data-pipeline deployments (instruments catalogue jobs, instruments data-grabbing, MTDS) must be ALERT-FREE
  (deadman coverage CONFIRMED complete; stale-image alert being added by a118550) AND running LATEST code.
- Daily scheduler: T+1 producer (00:00) slightly before catalogue aggregation (01:00), monotonic guard — terraform
  exists; gated on image so cloud jobs run latest code. ALL AG.

### Daily scheduler COMPLETE + robust (2026-06-26) — per-AG split (deployment-service@9d0e457)

all-AG 00:00 job OOM'd (signal 9) even at 8cpu/32Gi → SPLIT into per-AG t1-recon jobs (verified no-OOM, all ran
SUCCEEDED today): cefi 06:00 (existing) · defi 00:00 · tradfi 00:10 · prediction 00:20 · sports via sports-fixtures.
Retired the all-AG `instruments` scheduler entry. ORDERING confirmed: per-AG T+1 producers 00:00-00:20 → MTDS FAST 00:30
→ lifecycle-catalogue-regen 01:00 (monotonic guard, 35-min buffer). This is the operator's "daily T+1 backfill slightly
before aggregation, monotonicity, all AG" design — DONE.

### Session net-state (2026-06-26 autonomous run)

DONE: all 5 catalogues regenerated+promoted · daily scheduler (per-AG producers→aggregation, monotonic, all AG) ·
auto-build on main + auto-deploy + build-fail→#data-pipeline-alerts (a9cd863, fixed the missing instruments-service-prod
trigger) · alert coverage complete (deadman multi-layer + stale-image DP-VM-007 + CI-fail) · writer honest-absence
9e6dab5 (pre-genesis/no-activity/weekend/failed→typed empty_confirmed/attempted_failed) · Yahoo FX(G10)/Treasuries/DXY
universe · defi MVP tag-all · sports MTDS available_at fix · cefi+defi backfill gap-free + catalogues. RUNNING
(multi-hour): full-history honest-coverage backfills all 5 AGs since inception (empty_confirmed climbing: cefi 0→20k+,
defi →37k+, pred 0→480; fleet draining 57→~30) → drives every shard×day to represented (zero silent-absent).
OPERATOR-BLOCKED: ~~tradfi ICE/FX (Databento allowlist), KRX (adapter)~~ [SUPERSEDED 2026-06-27: KRX=Yahoo KOSPI +
ICE-DXY=Yahoo, both SHIPPED `uac@5480f5d5`+`is@dc0d99a` — NOT blocked; only ICE _commodity_ futures remain a Databento
ask], KALSHI historical IS (API), 9e6dab5 cloud-image catch-up (auto on next main promotion → re-resolve cloud jobs).

### CULMINATION — all 5 AGs honest-coverage (2026-06-26)

Writer honest-absence applied across full history: cefi/defi/prediction full-history backfills (empty_confirmed 0→20,580
/ →~40k / 0→600) + tradfi reconciliation `instruments-service@104607f` (flipped 2,445 lookback-artifact non-trading-day
cells captured→empty_confirmed; tradfi empty_confirmed 406→2,851; EXPECTED_WEEKEND/HOLIDAY, calendar-driven, snapshot
`_index/snapshots/pre_nontrade_flip_2026_06_26.parquet`). Every shard×day now represented as one of the 4 states by the
correct reason. Writer code: 9e6dab5 (pre-genesis/no-activity/weekend) + d3908c3 (tradfi weekend unreachable-guard +
DBEQ-lookback) + 104607f (historical reconcile). REMAINING (wall-clock/auto/operator): tradfi 9-shard full-history VMs
still capturing 2010-2026 trading days (long); cloud image auto-catch-up of 9e6dab5/d3908c3/104607f on next main
promotion → re-resolve t1-recon + catalogue-regen jobs; OPERATOR-BLOCKED: ~~tradfi ICE/FX (Databento allowlist), KRX
(adapter)~~ [SUPERSEDED 2026-06-27: KRX=Yahoo KOSPI + ICE-DXY=Yahoo, both SHIPPED — NOT blocked; only ICE _commodity_
futures (IFEU/IFUS Brent/Gasoil) remain a Databento subscription ask], KALSHI historical IS (API access).

### FINAL — instruments foundation honest-complete (2026-06-27)

tradfi silent-absent fully classified + filled (`scripts/fill_tradfi_silent_absent_cells_2026_06_27.py @9571361`): 878
weekend/holiday cells → empty_confirmed (snapshot `_index/snapshots/pre_silent_absent_fill_2026_06_27.parquet`). All 5
AGs now represent every REPRESENTABLE shard×day (captured / empty_confirmed-typed / attempted_failed / EU). CLOUD now on
latest honest-absence code: main caught up (promotion drain unstuck after the GH-billing/Actions outage), image rebuilt
from 104607f (`sha256:15a28711`), all 10 prod jobs (5 t1-recon + 5 catalogue-regen) re-resolved. Per-AG daily
scheduler + auto-build + full alert coverage live. REMAINING = OPERATOR-GATED ONLY:

- tradfi residual silent-absent = 1,836 GENUINE-GAPs: KRX 1,795 + ICE 32 + ~11 today/yesterday transient. **[SUPERSEDED
  2026-06-27 — see "CORRECTION + closeout" below]:** this was MIS-FRAMED as needing a "KRX-capable adapter" / "Databento
  subscription allowlist". Reality: KRX = daily KOSPI via **Yahoo Finance** (`^KS11`/`^KS200`) and ICE = DXY via **Yahoo
  Finance** (DX-Y.NYB) — both SHIPPED (`uac@5480f5d5` + `is@dc0d99a`), NOT operator-blocked. The only genuine remaining
  ICE ask is the ICE _commodity_ futures (Brent/Gasoil, IFEU/IFUS) which DO need a Databento subscription — but that is
  NOT the DXY/index data this residual refers to.
- Auto-build self-sufficiency: grant `github-cloudbuild-trigger@` `roles/cloudbuild.builds.editor` (unconditional) —
  agent identity is IAM-forbidden; operator running it.

### CORRECTION + closeout — KRX/ICE were MIS-SOURCING (not operator-gated) (2026-06-27)

Operator corrected the prior "OPERATOR-BLOCKED tradfi ICE/FX/KRX" framing: KRX = daily KOSPI from **Yahoo Finance** (not
a special adapter); ICE is **not** a Databento dataset we subscribe to — ICE data we want comes from Yahoo. So the 1,795
KRX + 32 ICE residual silent-absent cells were a **sourcing/config bug**, not a credential block. FIXED + shipped:

- `unified-api-contracts@5480f5d5`: KOSPI (`^KS11`) + KOSPI200 (`^KS200`) added to `YAHOO_INDICES` (venue=KRX,
  first_available 2019-01-02); `get_krx_index_daily_source()` resolver; ICE removed from `venue_to_databento`, added
  `venue_to_data_provider["ICE"]="yahoo_finance"`. 11 unit tests. QG-green, runtime-verified
  (`_create_yahoo_index_records(venue_filter='KRX')` → KRX:INDEX:KOSPI-USD/^KS11; ICE no longer in venue_to_databento).
- `instruments-service@dc0d99a`: KRX KOSPI Yahoo-enumeration + ICE-not-in-databento regression guards (4 tests).

Manifest VERIFICATION (market-data-tick-tradfi `_index`): CME OHLCV is honest-complete for the EXPECTED window —
expected universe floor = **2020-01-01** (not 2010; 2018-2019 = empty_confirmed EXPECTED_INSTRUMENT_NOT_LISTED), both
1s+1m captured every year 2020-2026, futures+options present (ES.FUT/ES.OPT/MES.FUT/MES.OPT). No silent absence.
2025/2026 expected_unattempted (853/1341) draining via ~13 running tradfi-bf VMs.

DISPATCHED (2 sonnet agents, in-flight):

- KRX/ICE instruments-history re-run — apply the shipped fix to the instruments manifest (close 1,795 KRX + 32 ICE
  absent instrument-def cells → captured/honest empty_confirmed). KRX single-stock breadth = BLOCKED-OPERATOR-DECISION
  (operator wanted the index, which this closes).
- CME ohlcv_1m 2020-Q1 writer fix — 3,355 attempted_failed (venue=CME, 2020-01..03) are a real writer bug:
  StreamingParquetWriter pre-write validation rejects space-containing CME option symbols (`CME:E1AG0 C3240`,
  `CME:ESM0`) landing in instrument_type=UNKNOWN → SCHEMA_VALIDATION_FAILED. Root-cause fix (normalize→canonical
  InstrumentKey + classify OPTION/FUTURE) + re-run 2020 Q1. NOT a transient retry (attempted_at 06-22..06-24, running VM
  keeps failing).

### Manifest audit — stale-row cruft + within-window gaps (2026-06-27)

Post KRX/ICE rebuild, audited canonical tradfi instruments index (`instruments-store-tradfi` `_index`). Found: 16,556
valid schema_v9 rows (all 4-state, 0 invalid) + **15,781 STALE rows** (schema_version 4 [10,396] or '' [5,385]; blank
capture_status + blank data_type; written_at ≤ 2026-04-15) co-residing. Per-venue v9 genesis floors confirmed correct vs
UAC: CME/FX/ICE/CBOE 2020-01-01, NASDAQ/NYSE 2023-04-15 (DBEQ discovery API empty before — NOT a gap), KRX 2019-01-02.
Of stale-only (date,venue) cells, **907 are ≥ genesis = genuine within-window instrument-def gaps** (CME 332, FX 244,
ICE 167, CBOE 160, NASDAQ/NYSE 2 ea); the rest (~14.9k) are pre-genesis cruft. RESUMED agent to: (1) re-enumerate the
907 via genesis+calendar-aware v9 producer → captured/empty_confirmed; (2) prune all 15,781 stale rows (snapshot
`pre_stale_v4_prune_2026_06_27.parquet`); (3) harden UTL manifest_consolidator to DROP sub-canonical-schema/blank-status
rows at UNION ALL (root cause: old per_vm shards carried forward). UTL column-order consolidator fix already shipped
(UTL@6b0520a6). KRX/ICE history closed: KRX 1,796→0 absent (3,187 captured + 876 holiday EC), ICE 33→0.

### CME ohlcv_1m 2020-Q1 writer fix — shipped + corrective re-run (2026-06-27)

Root cause of the 3,355 attempted_failed (CME ohlcv_1m, 2020-01..03): MTDS used `stype_out="raw_symbol"` on the
Databento GLBX.MDP3 fetch (stype_in=parent) → HTTP 422 → empty iid→raw map → fell back to a `symbol` column carrying
malformed option symbols (`CME:ESM0`, `CME:E1AG0 C3240`) → classified instrument_type=UNKNOWN → StreamingParquetWriter
partition_mismatch/SCHEMA_VALIDATION_FAILED. FIX (MTDS): `dc8075da` revert stype_out→instrument_id + post-fetch
`_build_iid_to_raw_symbol_map()`; `b35ecb74` paginate symbology.resolve in 2000-symbol batches (ES.FUT+ES.OPT ~2075/7d
window exceeds the 422 cap). 16 unit tests. Corrective VM `…es-2020-20260627-090849` (dc8075da) verified 0-failed
(2020-01-02 36,335 / 01-03 52,329 / 01-06 42,664 records). Tarball rebuilt @b35ecb74 for future launches. Cleanup:
deleted broken VM `…083324` + old-code DUPLICATE `…090019` (MTDS d8778cee, pre-fix — would have re-stamped
attempted_failed and raced the consolidator). PENDING: full-2020-Q1 manifest verify (0 attempted_failed) at VM
completion (~1-2h); if dc8075da's no-pagination 422-fallback leaves residue, relaunch on b35ecb74.

### Auto-build deploy fix — IS image was silently stale (2026-06-27)

Operator flagged images must auto-build on main. Found instruments-service prod image STALE at 01:33 (sha256:15a28711,
missing today's KRX/ICE dc0d99a) while MTDS/UTL auto-rebuilt 10:28-30. Root cause (4-link): IS `-build` trigger's
push:main removed 06-26 (switch to router-invoked `-prod`); `-prod` was a manual sourceToBuild (no push event); GHA SA
`github-actions-deploy@` lacks `roles/cloudbuild.builds.editor` → router `gcloud builds triggers run` got
PERMISSION_DENIED; router error-classification only handled quota/region/503 → misclassified PERMISSION_DENIED as
"not-configured" + SILENTLY dropped (build_triggered=false, no alert). FIX: (1) `instruments-service-prod` trigger →
`repositoryEventConfig push:branch=^main$` (auto-fires on main, no router/IAM dependency — matches MTDS pattern); (2)
router `cloud-build-router.yml@c3a113e94` PERMISSION_DENIED→exit 3 + new `notify-permission-denied` CRITICAL Slack job
(IAM gaps always surface). VERIFIED: build 4be77e5b SUCCESS 11:02; `instruments-service:latest` now sha256:d9418e6e
(10:58, tag 0.87.0); Cloud Run t1-recon + lifecycle-catalogue-regen reference :latest → fresh image next run; next main
push auto-builds without manual intervention. MTDS image 5126ab57 (10:30, CME writer fix), UTL 10:28 (consolidator
hardening) both already fresh.

### cefi/defi honest-coverage audit + cefi remediation (2026-06-27)

Ran the same masked-gap lens (stale rows hiding within-window gaps) on cefi+defi instruments manifests + catalogues:

- **defi: CLEAN / 100%** — 215,916 rows, 100% schema_v9, 0 stale, 0 masked gaps; chains continuous (BASE/BSC/LINEA
  "gaps" are genesis-explained pre-launch). Catalogue CURRENT `prod/catalog.parquet` 2026-06-26 (7,416 instr / 6,469
  active). Cosmetic only: 74 ZKSYNC/LIGHTER rows mis-filed into defi catalogue (belong to cefi); 15 epoch-zero RAYDIUM
  delisted rows.
- **cefi: catalogue CURRENT** `prod/catalog.parquet` 2026-06-27 (349,156 instr / 4,410 active), **but manifest NOT
  clean** — 250 stale/blank rows (incl. legacy writer bug leaking chain names SOLANA/ZKSYNC into schema_version field);
  22 masked (date,venue) cells across 8 venues (Dec-2023 + Mar-2025 clusters); 8 venues with large NO-ROW gaps from
  2023-12-17 (BINANCE-DELIVERY 721d, DERIBIT-COMBO 475, PACIFICA 448, BITGET-SPOT/FUT 327, COINBASE-FUTURES 319,
  EXTENDED-STARKNET 289, LIGHTER 236) — mix of genuine gaps + un-seeded pre-launch venues.
- NOTE: the tiny `_catalogue/instruments-service/day=*/manifest.json` pointers (mtime 2026-05-12) are SUPERSEDED legacy
  artifacts; the real catalogue is `{env}/catalog.parquet` (per build_instrument_catalogue.py).

DISPATCHED cefi remediation agent (mirrors tradfi a71): per-venue genesis-vs-genuine split for the 8 gaps; fix the
schema_version-holds-chain writer bug (+test); re-enumerate genuine gaps via calendar/genesis-aware CEFI producer ON A
VM (host memory-constrained by the tradfi backfill); seed pre-launch stretches as empty_confirmed(PRE_VENUE_LAUNCH);
prune the 250 stale rows (or rely on consolidator dd17ce23 auto-drop). Verify continuity genesis→today.

### cefi G1 catalogue-correctness VERIFICATION (2026-06-27, opus cefi agent) — operator asked "is cefi instruments 100%?"

**VERDICT: NOT done.** The day-axis IS fixed (✅ 2,646/2,646 days genesis→06-26, 0 missing; ✅ 20,580 `empty_confirmed`
materialised, was 0; ✅ MVP + schema_v9), but 4 live G1-correctness defects remain — now todos **G1.1–G1.4** under the
Phase-1 cefi G1 item above. **Crucially, the 06-27 audit just above treated the catalogue as "CURRENT / 4,410 active"
and did NOT flag that 4,410-active is the BUG** — so the catalogue defects are NEW/uncovered:

- **G1.1 (NEW, uncovered, P0-urgent): catalogue `available_to` mass FALSE-DELISTING (§7.3).** `prod/catalog.parquet`
  (06-27 01:23) stamps **8,520 instruments `available_to=2026-06-25`** across every venue; active collapsed to **4,410
  of 349,156** (BINANCE-FUTURES ≈47 active vs ~600+ real). Root cause confirmed: **06-26 was a PARTIAL capture**
  (BINANCE-FUTURES instrument*count 678@06-25→47@06-26; BINANCE-SPOT 767→67; OKX-FUT 81→32; BYBIT 652→652 stable;
  parquet 47KB→30KB) × the last-seen/global-`latest_day` bug. 06-27 recovered to full but the bad catalogue is live →
  **MTDS-G4 would filter against a catalogue that thinks Binance lists ~47 instruments.** Shared
  `build_instrument* catalogue.py` fix with slot-3 tradfi G1.h.
- **G1.2 (NEW): capture-stability** — a thin/partial venue day must `record_failed`, never overwrite a full prior day
  (the 06-26 partial is what drove G1.1). Canonical test for the §1.2 drawdown metric (678→47).
- **G1.3 (OVERLAPS the dispatched cefi remediation agent above): canonical-form pollution** — 320 `asset_group=defi`
  (LIGHTER 202 + PACIFICA 118, the "74 ZKSYNC/LIGHTER mis-filed" finding but it's a single-SoT violation not "cosmetic")
  · 1,108 blank-asset_group (2019 OKX/Coinbase) · ~234 schema-misaligned (the 250-stale / schema_version-holds-chain
  writer bug the remediation agent owns). COORDINATE — don't double-fix the schema-bug/stale-prune (theirs); the cefi
  agent owns the defi-mistag re-stamp + the 2019 blanks if they don't.
- **G1.4 (NEW): junk-symbol rejection NOT implemented** — 9 CJK/meme test symbols live (`龙虾`/`币安人生`/`我踏马来了`
  on BINANCE/BITGET/ASTER). Reject at the venue adapter + surgical purge.

Evidence is read-only duckdb on the live parquets (numbers reproduce). G1.1 is the priority (catalogue is actively
wrong).

## Progress Log

- **na-eligibility-audit 2026-08-02** (re-confirms 2026-07-30; only change since = context-scout `context_scope`
  frontmatter, body byte-identical): KEEP-NA, valid — all 10 items sit behind GATE 0, explicitly NOT RECORDED SIGNED
  OFF, and were re-reconciled 2026-07-28 with per-item evidence confirming each stays open.
- **context-scout 2026-08-03**: re-scouted; refreshed context_scope (6 entries) — swapped the 2 sibling AG
  gate-execution plans for 3 real source paths (the honest-coverage v2 producer script + the 2 UAC crosscutting modules
  the still-open items 2/3/8/10 all cite live-grep evidence against).
- **na-eligibility-audit 2026-08-07**: KEEP-NA, valid — reaffirms 2026-08-02/08-06 (unchanged): all 13 open items sit
  behind GATE 0 (NOT RECORDED SIGNED OFF); the set mixes unbuilt SCRIPT infra with genuine DESIGN-judgment items
  (expected-universe oracle venue-truth sourcing decision, canonical-form single-SoT whole-corpus migration sequencing)
  that aren't cleanly bounded-outcome — consistent with the prior two passes' verdict, doc stays NA as a mixed set.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-07 (unchanged): all
  open Phase-0 items sit behind GATE 0 (still NOT RECORDED SIGNED OFF); the set mixes unbuilt SCRIPT infra with genuine
  DESIGN-judgment items (expected-universe oracle venue-truth sourcing decision) that aren't cleanly bounded-outcome. No
  cheat-sheet precedent (IAM/reversible-delete/recurring-finding-job) applies to any open item here.
- **context-scout 2026-08-17**: populated/refreshed context_scope (6 entries)
- **na-eligibility-audit 2026-08-17** [body-hash:78413ace047add14]: KEEP-NA, valid -- All 10 Phase-0 cross-cutting foundation items sit behind an explicit, self-documented GATE 0 that is 'NOT RECORDED SIGNED OFF' — 6 of them remain open. Four are unbuilt, cross-AG infra scripts requiring real engineering judgment on safe design (a bounded --force reconcile that avoids a 32Gi OOM; a wiring change into the live capture-time write path across every AG; a QG/watchdog-wired ε=0 reconciliation guard). One is explicitly tagged [DESIGN] and needs a genuine sourcing decision (expected-universe oracle venue-truth genesis). One (depth-aware re-fetch trigger) is explicitly self-described as correctly blocked on the other two still-unbuilt items. One (canonical-form single-SoT GCS migration) is a large multi-AG whole-corpus migration under an explicit operator single-walk-discipline mandate. Three prior na-eligibility-audit passes (2026-08-02, 08-07, 08-08) all independently confirmed KEEP-NA with matching reasoning.
