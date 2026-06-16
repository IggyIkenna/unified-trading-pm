---
title:
  "Downstream data-pipeline services manifest canonicalisation (MDPS / features / strategy / execution) — audit-first,
  low-data single-walk"
created: 2026-06-01
parent_epic: mtds_mdps_master
assigned_vm: vm-ml
status: active
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 3
estimate_calibrated_ai_days: 2.4
locked_by: live-defi-rollout
locked_since: 2026-06-01
related_plans:
  - plans/epics/features_and_ml_master.md
  - plans/epics/strategy_master.md
  - plans/epics/execution_master.md
source:
  - defi_manifest_canonicalisation_2026_06_01.md §MASTER (per-service canonicalisation axis — downstream uncovered)
  - canonical_form_cross_service_audit_checklist.md (CF-1…CF-12)
master: defi_manifest_canonicalisation_2026_06_01.md (cross-plan canonical-SSOT coordinator)
---

# Downstream data-pipeline services manifest canonicalisation (MDPS / features / strategy / execution)

> **⛔ COORDINATED — G2 downstream (2026-06-07)** —
> `plans/active/master_data_canonicalisation_migration_catalogue_2026_06_07.md` gates these MDPS/features/strategy/
> execution `_index` walks on **G0** (pipeline*mode source-aware `{mode}*{source}[_{transport}]` model) + **G1** (IS
> catalogue could-exist SSOT) + the upstream per-AG MTDS walks. Readers MUST be union-aware across source-aware pipeline
> modes (M4 precedence; M5 union view) before any apply. strategy-service additionally hosts the live-flip readiness
> gate (M6) + batch-live-reconciliation-service hosts the cross-mode union (M4) per the G0 plan.

> **MASTER**: `defi_manifest_canonicalisation_2026_06_01.md` §MASTER (L3, per-service axis). The data pipeline is
> `instruments → MTDS → MDPS → features → strategy → execution`. The per-AG plans cover MTDS; `instruments_manifest_…`
> covers the input side. THIS plan covers the four **downstream** services whose `_index`(es) carry the same
> canonical-form debt. **Operator 2026-06-01**: "we haven't run much data for MDPS / features / strategy / execution, so
> those should be fairly quick — but still should be audited and in plans." So this plan is **audit-first**: read each
> service's actual `_index` state (small corpus → fast), then bundle any debt into ONE single-walk per bucket.

## 🎯 NEXT-AGENT CODE-CANONICALISATION CONSOLIDATION BACKLOG (AG slices: cefi→slot 3 · prediction→slot 5 · tradfi→slot 6; defi→slot 2 §H; sports→slot 4)

> **Operator directive 2026-06-02**: "I want all the code to be at its canonical point so that the migration is aligned
> … a change I'm not going to have to revert, a manifest change I'm not going to have to change again, a migration
> change I'm not going to have to change again." This section is the **single hand-over surface** for the remaining CODE
> work so the next agent can drive every read/write/status/rebuild path to the v9 post-migration canonical form BEFORE
> the migration RUN — so the migration + delete (operational session) needs ZERO further code edits. Each item names the
> target repo + file + exact change + home plan; a cold sub-agent should read
> `cursor-configs/SUB_AGENT_MANDATORY_RULES.md` first. **Five-slot asset-group split (operator 2026-06-03)** — this plan
> (vm-ml) is PRIMARY owner and drives each AG's downstream slice with its AG slot: **defi→slot 2** (referenced, tracked
> in `defi_manifest_canonicalisation_2026_06_01.md` §H — never edited here), **cefi→slot 3**, **sports→slot 4**,
> **prediction→slot 5**, **tradfi→slot 6**. A slot drives only its own AG slice; coordinate, don't edit another AG's.
>
> **Done this programme (do NOT redo — verify on origin/live-defi-rollout):** Item-3 CRIT-2 non-router freshness gate
> (execution-service@12561a9ee) · Item-4 Polymarket None→attempted_failed batch=live (mtds@5744ba61) · CRIT-1 MDPS
> live=batch (mdps@9102321) · CRIT-2 router gate (exec@3181f26b8) · CRIT-3 upstream preflight (exec@225797127) ·
> features perp_funding canonical read (features@cf47eca9+cefd5b54) · GAP-5/6 live-startup gates (strategy@d837ca1b /
> features@dbf12aff) · prediction E5 captured-atom rebuild (mtds@d1f1317d) · Directive-D category= count-ban
> (deployment-api@41fa120) · PREP3 writer pipeline_mode=PRIMARY (mtds@f50116ca) · all 3 migrators + 3 E5 rebuild scripts
> EXIST. CF-11 write-path **MTDS side = VERIFIED COMPLIANT** (orchestrator.py:3818 tier-2 + :3766 tier-3 gate
> record_failed-vs-empty on a recorded fetch-failure; adapters classify+emit+re-raise — no swallow).

### TIER 1 — CODE-to-canonical, P0/P1 (MUST be canonical + QG-green BEFORE the migration RUN)

- [ ] [CODE] P0. **CF-11 write-path — instruments-service residual** (MTDS already compliant). Verify the IS
      reference-data fetch paths for cefi/tradfi/prediction `record_failed` (→ `attempted_failed`, via
      `classify_venue_error()`/ `ADAPTER_FETCH_FAILED`) on a genuine API error (timeout/5xx/429/auth) for an in-universe
      instrument within coverage — NOT `record_empty`/`return []`. Grep `instruments-service` reference adapters for
      `except … record_empty` / bare `return []` swallows; gate empty-vs-failed on instrument-in-universe + UAC coverage
      bounds. Repo: **instruments-service**. Home: each AG plan § CF-11 (full diagnosis in cefi plan). **✅ CEFI SLICE
      VERIFIED CLOSED (slot-3 2026-06-04):** all 4 cefi adapters (aster/hyperliquid/tardis/deribit_combo) re-raise on
      genuine fetch failure → `_fetch_one` `failed[]` → `record_failed`/`attempted_failed`
      (`orchestrator.py:1746`+`:2978-2993`); regression `tests/unit/test_is_adapter_fetch_failure_raises.py`
      (`e2e008f0`+ `f2ca5954`). Checkbox stays OPEN for the **tradfi** (databento ZERO-signal swallow
      `databento.py:826`, slot-6) + **prediction** (polymarket, slot-5) slices.
- [ ] [CODE] P0. **E5 manifest-rebuild logic — CF-11 3-way decision tree**
      (`rebuild_{cefi,tradfi,prediction}_manifest.py`, mtds `scripts/`). Captured-atom rebuilds DONE; STILL OPEN — make
      the LOGIC canonical now so the migration-RUN session needs no script edits: (a) **within-bounds empty →
      `attempted_failed`** (not `SOURCE_RETURNED_ZERO`) — gate on in-universe (cefi venue+symbol / tradfi
      databento-universe×trading-calendar / prediction Polymarket market×active-window) + within coverage window + not a
      known gap; (b) **re-emit the EXISTING `_index` `empty_confirmed`/`attempted_failed` rows as v9** — a pure
      object-scan loses cells with NO backing object, so read the prior `_index` via `read_availability_index` (UTL) +
      re-emit typed (status PRESERVED, never relabel a failure to empty); (c) **prediction: audit the 41 existing
      `SOURCE_RETURNED_ZERO`** (genuine vs masked fetch-failure) + preserve the 2,280 `EXPECTED_PRE_VENUE_LAUNCH`
      (pre-launch check via UAC `venue_launch_dates`). Unit-test the 3-way tree per script. Repo:
      **market-tick-data-service**. Home: each AG plan § CF-11 + E5.
- [x] ✅ [CODE] P1. **Kalshi None-classifier divergence — DONE (mtds@584871e9, slot-5/6 2026-06-03).** Kalshi adapter
      now emits `None` (not `"OTHER"`) for a sub-threshold classification → the venue-agnostic orchestrator finalize
      routes it to `record_failed[ClassifierConfidenceLow]` (venue parity w/ Polymarket@5744ba61 + batch=live parity w/
      rebuild_prediction_manifest);
      `test_kalshi_adapter_lifecycle_gating.py::test_unclassified_canonical_group_is_none_not_other` asserts `None` not
      `"OTHER"` (9/9 green); mtds QG `--no-fix` exit 0. Cross-referenced from the prediction master plan § CF-11. Repo:
      **market-tick-data-service**. Home: prediction plan § CF-11. (Low live urgency — Polymarket-only corpus today —
      but required before Kalshi goes live.)
- [ ] [CODE] P1. **Downstream writer-fixes (MDPS / features / strategy / execution)** — emit typed
      `EmptyConfirmedReason` + `attempted_failed`-not-swallow (CF-11) so the FIRST volume each writes is born-canonical
      (these AGs have no `_index` yet → writer-fix-first, not migrate-a-nonexistent-corpus). Repos:
      **market-data-processing-service / features-service / strategy-service / execution-service**. Home: this plan § C
      (line ~454) + Phase-C.
  - **MDPS portion DONE (slot-6 2026-06-03, mdps@986e72c):** `live_workers` emits typed
    `EmptyConfirmedReason.SOURCE_RETURNED_ZERO` on zero-row fetches (no blank reason) + `canonical_writer` bridges
    tradfi `ohlcv_15m`/`ohlcv_24h`/`tbbo` → their `SOURCE_PRIORITY` keys so v9 source-column denormalisation resolves.
    QG green 169s. Checkbox stays OPEN for the features/strategy/execution writer portions (other slots/repos).

### TIER 2 — data-status / deployment-api code (so post-delete reads/counts don't regress)

- [x] ✅ [CODE] P1. **FLAG-1 (deployment-api) — SHIPPED deployment-api@60cd585 (slot-6 2026-06-03).** UNION +
      manifest-derived per-source breakdown.** Headline coverage = **union** (a `(venue, data_type, date)` cell is green
      if ≥1 source `captured`) → dedupe the multi-source rows in `_mtds_honest_coverage_for_venue` via
      `select_primary_available_source` (UAC `source_priority`) so two source-rows can't inflate `found_dates`.
      **Per-source breakdown** (databento vs massive) is surfaced in the data-status drilldown derived from the
      **`_index` `source` COLUMN** that `read_availability_index` already loads — i.e. a `groupby("source")` on the
      in-memory manifest rows, NOT a per-parquet column scan (the v9 manifest denormalises `source` to the row level, so
      the breakdown is effectively free; the parquet-data-column path is slow and MUST be avoided). Implementation: (1)
      union-dedupe in the aggregator for the denominator; (2) add a per-source sub-aggregate from the same `_index` rows
      for the drilldown. Add a QG test asserting union (2 source rows on one date → 1 found-date) + the per-source
      split. Repo: **deployment-api\*\*. Home: this plan FLAG-1. (No longer operator-blocked.)
- [ ] [CODE] P1. **FLAG-3 (deployment-api) — DECIDED (operator 2026-06-02): env-tier the `*-store` buckets, `-prd`
      initial.** The `instruments-store` / `features-store` / `ml-store` / `execution-store` (+ `ml-configs-store`,
      `deployment_api_config.py:547`) buckets get **env-tiered** (split env-wise: prd/stg/dev), with `-prd` as the
      initial migration tier. So the `# CORRECT-LOCAL` markers are NO LONGER correct — route every ref through
      `resolve_bucket_name(kind=…, env=…)` so reads resolve to the env-tiered canonical name (`-prd` now; the no-env
      bucket becomes legacy → deleted post-cutover). Work: (1) **bucket-SSOT owner** registers the env-tiered `*-store`
      bucket names (prd/stg/dev) in `deployment-service/configs/cloud-providers.yaml` (coordinate via
      `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md`); (2) **deployment-api** replaces the hardcoded
      f-strings at `commentary/pipeline_uat.py:167/181/195/211` + `deployment_api_config.py:547` with
      `resolve_bucket_name(...)` and removes the `# CORRECT-LOCAL` markers; (3) the prd-store data migrates to the
      `-prd` bucket as part of the initial migration. Coordinate with the active deployment-api agent. Repo:
      **deployment-api** (+ deployment-service cloud-providers.yaml). Home: this plan FLAG-3 + `bucket_name_ssot…`. (No
      longer operator-blocked.)
- [x] ✅ [CODE] P2. **FLAG-4 — RESOLVED-BY-VERIFICATION (slot-6 2026-06-03): premise was a misread.**
      `MTDS_CATEGORY_META["TRADFI"].venue_accessor = all_databento_venues` does **NOT** omit venues — it already
      resolves to the FULL tradfi set `[CME, CBOE, NASDAQ, NYSE, ICE, FX]` (the "Massive-only" venues CBOE+FX are
      already in it). So the denominator is correct today. Added a correctly-named alias
      `VenueMapping.all_tradfi_venues` (= the same set) in **UAC@0abbdf86** for future clarity; deployment-api stays on
      the behavior-identical `all_databento_venues` (deployment-api@60cd585, comment added) — rename deferred to a
      post-UAC-cascade pass to avoid a forward-dep break against the deployed pinned UAC. Repo: deployment-api +
      unified-api-contracts. Home: this plan FLAG-4.

### TIER 3 — guards + vocab + tests + docs (canonical safety-net)

- [x] ✅ [CODE] P2. (ALL THREE repos now shipped — strategy portion strategy@3561f137 `_warn_on_v9_schema_drift` in
      manifest_allocation_guard + 3 tests, 2026-06-11; features+MDPS were already done per note below) **GAP-4 —
      v9-schema MIXED-version-drift warn** at `manifest_window_guard` (features) / `manifest_allocation_guard`
      (strategy) / MDPS `dependency_checker`. Ship the loud-warn that fires ONLY on mixed-version drift within one read
      (some rows v9, some not) OR `asset_group`-column-absent-on-a-migrated-bucket — NOT a blanket "not v9" warn (corpus
      is 100% v8 today → that would be pure noise). Becomes a hard assert post-each-AG-G3. Repos: **features-service /
      strategy-service / market-data-processing-service**. Home: this plan GAP-4 (full design spec there).
  - **features + MDPS portions DONE (slot-6 2026-06-03):** `_warn_on_v9_schema_drift` shipped in features
    `manifest_window_guard` (features@5a5246e6, after `read_availability_index`) and MDPS `dependency_checker`
    (mdps@266479c, after the manifest read) — fires ONLY on mixed `schema_version` in one read OR v9-rows-without-
    `asset_group`-column; silent on the uniform-v8 corpus; 4+3 unit tests; both QG green. **Checkbox stays OPEN for the
    strategy `manifest_allocation_guard` portion** (strategy-service, other slot). Becomes a hard assert post-G3.
- [x] ✅ [CODE] P2. (mdps@4363bce 2026-06-11 — granular layer + UPSTREAM_DEPS_BY_ASSET_GROUP map +
      check_upstream_manifest_has_live_gap + orchestration_service/process_handler callers + 4 test files; rename
      COMPLETE, zero remaining checker `category` params) **GAP-7 — MDPS `dependency_checker` `category`→`asset_group`
      param rename** (+ docstrings) at next substantive touch (functional-correct today). Repo:
      **market-data-processing-service**. Home: this plan GAP-7.
- [ ] [CODE] P0. **QG-test alignment (read/status, cross-repo)** — extend the QG-fed tests so they assert the CANONICAL
      form (resolver bucket, `pipeline_mode=` path, v9 `_index` columns, `asset_group=`, on-disk data_type) on READ +
      STATUS paths (writer 18 assertions + item-3/4 tests done) → QG FAILS on reversion to a dead bucket / `category=` /
      old schema. Repos: **mtds / MDPS / features / instruments / deployment-api**. Home: this plan "QG-test alignment".
- [ ] [DOCS] P1. **Doc sweep + supersession banners** — grep `codex/02-data` + `codex/04-architecture` + repo
      `docs/GCS_PATHS.md` for any path example WITHOUT `pipeline_mode=` shown as canonical / `category=` as canonical /
      non-on-disk `data_type` → update or add `SUPERSEDED → <plan>` banner; banner the 4 superseded plan sections
      (cf_data_state "Supersession mapping"): `tradfi_massive_dual_source` source-task,
      `data_source_provenance_all_asset_groups`, `pipeline_mode_partition_migration`, `bucket_name_ssot…` Phase-5
      `--manifest-only` seed. Home: cf_data_state audit "Codex/plan doc-update TODOs".

### TIER 4 — OPERATIONAL MIGRATION RUN (NOT code; the next operational session, AFTER Tiers 1-3 are canonical + QG-green)

> These are the migration EXECUTION steps (read-only G1 dry-run is safe; G2+ irreversible). Per the per-AG plans + the
> cf_data_state "GATES G1–G8" + "NEXT-AGENT EXECUTION HANDOFF". They consume the EXISTING migrators + E5 scripts (Tier-1
> makes the E5 LOGIC canonical first). Do NOT run them in a code-only session.

- [ ] [DATA] P0. Per-AG (cefi/tradfi/prediction): Phase-0 layout audit → re-tarball+pin SHAs → **G1 full-corpus
      dry-run** (`launch-canonical-migration-vm.sh <ag> <start> <end> dry`; confirm `TOTAL planned` ≈ full-corpus object
      count) → writer drain + `_index` snapshot → `--apply` additive copy → **E5 rebuild RUN** → CF-1…CF-12 verify →
      completeness COUNT gate → strategically-sampled cross-shard verify → fleet drain → **DELETE legacy (END-only,
      irreversible)**. Home: each AG plan §C/§E + `cf_data_state_audit_slot3_2026_06_01.md` GATES G1–G8. (E6 CF-7
      relabel + E7 verify + E8 delete ride here.)
- [ ] [DATA] P1. Downstream service C-walks (MDPS rides the AG tick walk; features/strategy/execution =
      writer-fix-first, re-audit when input C-GREEN + first batch runs). Home: this plan § C.

### Sequencing (HARD): Tier-1 + Tier-3-QG-tests GREEN → Tier-2/Tier-3 → THEN Tier-4 migration RUN.

---

## PREP3 — reader/writer `pipeline_mode`-PRIMARY (cross-AG; 🟢 WRITER DONE / 🟡 reader slot-2 coordination)

> **Why this gates the legacy delete + backfill resume (operator 2026-06-02)**: the v9 migration ADDS the
> `pipeline_mode=` path segment and the legacy (no-`pipeline_mode=`) paths are then DELETED. So every WRITER must emit
> `pipeline_mode=` as the PRIMARY segment (else post-delete backfill/live writes land on the deleted shape → re-drift),
> and every READER must probe the `pipeline_mode=` path PRIMARY (else post-delete reads miss the data). The base
> `build_*_partition_path` builders intentionally omit `pipeline_mode=` (only
> `candidate_parquet_paths(..., pipeline_mode=…)[0]` prepends it) — so DIRECT base-builder callers had to be migrated.

- [x] ✅ [CODE] P0. **WRITER side — DONE for cefi/tradfi/prediction (mtds@f50116ca, 2026-06-02).** All THREE MTDS
      write-path builders now emit `pipeline_mode=` PRIMARY (inserted after `day=`, before `asset_group=`), derived via
      `derive_pipeline_mode_for_row(venue, asset_group, data_type)` — the SAME helper the v9 migrators + E5 rebuilds
      use, so **object-path pipeline_mode == manifest pipeline_mode** (path==manifest invariant): (1)
      `engine/orchestrator.py:_build_partition_path_for_asset_group` (PartitionedTickWriter route —
      cefi/tradfi/prediction inline); (2) `adapters/cefi/tardis_shared.py` (tardis cefi builder); (3)
      `adapters/tradfi/tradfi_shared.py` `build_tradfi_partition_path`. 18 write-path test assertions updated; ruff +
      per-file basedpyright clean (+0 new errors); 134 tests green (2 pre-existing env-tier **bucket-naming** failures
      remain, foreign — owned by `bucket_name_ssot…`, NOT introduced here). batch=live: backfill resumes on the
      canonical path after the legacy delete.
- [x] ✅ [CODE] P0. **READER side — AUDITED (slot-3 agent A, 2026-06-02): MDPS / MTDS-read / instruments = CANONICAL, no
      change** (MDPS day-level prefix scans are pipeline_mode-agnostic → survive the delete; MTDS reader.py pm-aware;
      instruments resolver-based). The ONLY reader regression = features `perp_funding_rates.py` (tracked in the
      per-surface matrix below). So PREP3 reader-side is GREEN except that one features-service fix. (Original
      slot-2-coordination note below retained for context.)
- [x] ✅ [CODE] P1. **READER side — SUPERSEDED/GREEN (slot-3 2026-06-02)**: covered by the PREP3 reader audit above
      (MTDS reader.py pm-aware; MDPS day-prefix scans pm-agnostic; instruments resolver-based) — the only reader
      regression was features `perp_funding_rates.py`, shipped at features@cf47eca9. No open reader work for
      cefi/tradfi/prediction. (Original context retained below.) MTDS `reader.py` is ALREADY pipeline*mode-aware
      (Level-1 `pipeline_mode={mode}/` probe → Level-2 no-pm fallback); `manifest_reader_fallback` Level-0 probes
      `pipeline_mode=`; MDPS `cloud_data_provider.py` only resolves buckets (no raw-tick partition-path building);
      slot-2 already shipped pipeline_mode-aware MDPS+features reads for **DeFi** (mdps@4b9e6e5 + features@dec1b687).
      **DeFi slice → slot 2** (the DeFi reader confirm is tracked in `defi_manifest_canonicalisation_2026_06_01.md` §H,
      five-slot asset-group split). **TODO (each non-defi AG slot, this plan):** confirm the MDPS candle-builder
      raw-tick read + features-onchain `data_loader` read resolve the `pipeline_mode=` path PRIMARY for the **non-defi**
      AGs too (cefi/tradfi/prediction) — i.e. they read via the pipeline_mode-aware MTDS reader /
      `candidate_parquet_paths` / `manifest_reader_fallback`, NOT a direct
      `build*\*\_partition_path`that would miss migrated data after the legacy     delete. If any direct base-builder read remains, switch it to the pipeline_mode-aware path (same fix as the writer).     This is the only PREP3 residual before the per-AG G3`--apply`→delete;
      the writer side + MTDS reader are done.
- [x] ✅ [CODE] P1. **tradfi reader residual CLOSED (slot-6 2026-06-03)** — audit found the features **volatility**
      (`volatility/engine/orchestrator.py`) + **cross_instrument** (`cross_instrument/engine/raw_data_loader.py`)
      readers resolved tradfi raw-tick via a direct `build_cefi_partition_path(...)` with NO `pipeline_mode=` → would
      miss migrated data after the legacy delete (exactly the PREP3 residual above). Fixed: derive `pipeline_mode`
      per-row (`derive_pipeline_mode_for_row`) + build the `pipeline_mode=`-PRIMARY path with a legacy no-pm fallback;
      preflight gates now target `options_chain`/`futures_chain` specifically. Import via the UAC top facade (STEP 5.23
      clean). Shipped **features-service@61e8accd** (+ aiohttp dep-fix @af95529b). Full QG green (410s).

## PRE-DRY-RUN CODE-CANONICALISATION PREFLIGHT — no dead-bucket association; QG must catch regression (operator 2026-06-02, HARD GATE before ANY migration dry-run)

> **Operator 2026-06-02**: "before any dry runs of the built migration scripts we need to finish the coding exercises…
> have we refactored read+write cloud-storage paths across the board to match the new canonical for the asset groups we
> cover, in the tests that feed quality gates — essential to avoid regression. Even though we haven't started the
> migrations (they'll be quick), the code itself must not regress by association with DEAD buckets. That also goes for
> **data-status in the deployment API and UI**, which tend to resolve many bucket names, menu conventions, data_type
> conventions, and manifest-reading conventions."
>
> **Premise**: the migration is additive + fast, but the moment legacy buckets/paths are DELETED (L6/E7), any code still
> pointed at a legacy bucket name, a `category=` path, a no-`pipeline_mode=` read, an old on-disk `data_type`, or a v8
> manifest-read assumption **regresses to a dead reference**. This gate canonicalises the CODE (read + write + status +
> tests) FIRST, so QG is a live safety-net that fails on any dead-bucket/old-convention drift — BEFORE we dry-run. Scope
> = the slot-3 AGs **cefi / tradfi / prediction** (defi = slot-2; **sports = slot 4, the
> `sports_manifest_canonicalisation` master orchestrator — all sports MDPS/features/execution rows ride there;
> coordinate, don't edit**). **No migration dry-run (G1) proceeds for an AG until its row in the matrix below is GREEN**
> (QG-enforced).

**Convention SSOTs to align every surface to** (the 5 axes the operator named):

1. **Bucket name** — env-tiered canonical via `resolve_bucket_name(cloud=, kind=, asset_group=, env=)`; NEVER inline
   `gs://` / legacy no-env `market-data-tick-{ag}-{pid}` / wrong-token (`prediction` vs canonical `pred`). QG STEP 5.69.
2. **Path / pipeline_mode** — `raw_tick_data/by_date/day=/pipeline_mode=/asset_group=/…` PRIMARY for read+write (PREP3).
3. **`data_type` on-disk form** — the live-writer merge map (e.g. tradfi/cefi `futures_chain`→`options_chain` on disk);
   readers/status must resolve the on-disk form, not the logical key.
4. **`asset_group=`** (not `category=`) hive vocab on every read/write/status path.
5. **Manifest read** — v9 columns (`schema_version`/`asset_group`/`pipeline_mode`/`source`/`available_at`); never assume
   the constant; tolerate v8 during transition but write/expect v9.

**FOOTPRINT SCOPE (slot-3 grep audit 2026-06-02 — targets the work, prevents over-scoping):**

- **Legacy no-env bucket string refs (`market-data-tick-{cefi,tradfi,prediction}-` without `-prd/-stg/-dev`): ZERO
  across ALL six repos.** The bucket-name SSOT work already canonicalised these → the preflight is NOT a bucket-name
  string sweep; it's a **read/write-path + manifest-read + data-status-resolution** verify.
- **inline `gs://market-data-tick`**: MTDS 70 / MDPS 19 / instruments 10 / features 5 / deployment-api 0 / UI 0 — mostly
  migration scripts + docstrings + tests; triage the live read/write ones (not a blanket fix).
- **`category=`**: MTDS 154 / MDPS 73 / features 1109 / instruments 49 / deployment-api 57 / UI 2 — **counts
  OVERSTATE**: most are (a) the legacy-TOLERATED `(?:category|asset_group)=` regex alternation in migration/rebuild
  tools (correct — keep), (b) the `AssetGroup.category` Python attribute / `category` field names (NOT the hive vocab),
  (c) docstrings. Triage to find the few LIVE write/read/status paths still emitting `category=` for our AGs; do NOT
  mass-rename.
- **Net**: the real preflight risk is concentrated in (1) pipeline_mode-PRIMARY read/write (PREP3 — writer ✅; reader
  residual MDPS/features) and (2) **deployment-api/UI data-status** bucket+manifest+menu+data_type resolution
  (operator's named hotspot — needs the v9 `_index` read + canonical resolver + on-disk data_type). Scope the
  per-surface todos to those, with the grep commands as the triage entrypoint — NOT a mass `category=`/`gs://` rewrite.

**Per-surface preflight matrix** (each = a tracked P0 todo; GREEN = canonical + QG/tests aligned + no dead-bucket ref):

- [x] ✅ [CODE] P0. **market-tick-data-service** — WRITER pipeline_mode=PRIMARY DONE (mtds@f50116ca). READ side VERIFIED
      CANONICAL (slot-3 agent A, 2026-06-02): `reader.py` is pipeline_mode-aware (Level-1 probe → fallback);
      orchestrator write path injects pm; legacy hardcoded-bucket refs are in ops/migration scripts only (intentional
      `--bucket` defaults, not live read paths). No live read regression for cefi/tradfi/prediction.
- [x] ✅ [CODE] P0. **market-data-processing-service (MDPS)** — VERIFIED CANONICAL (slot-3 agent A, 2026-06-02), no
      change needed. The raw-tick reads (`orchestration_scheduling._list_instrument_files`, `data_source.GCSDataSource`)
      scan at the **DAY-level prefix** `raw_tick_data/by_date/day={date}/` and filter per-blob —
      **pipeline_mode-agnostic by construction**, so they pick up migrated `day=/pipeline_mode=/asset_group=cefi/…`
      objects automatically after the legacy delete. Bucket resolution via `resolve_bucket_name` (prediction = `pred`
      token); `category=` occurrences are internal enum/param names, not hive-key strings. (One pre-existing NOTE
      flagged: the gap-gate `resolve_pipeline_mode_from_source(None)` always yields BATCH_DATABENTO for cefi/tradfi
      expected_unattempted sentinels — pre-existing, not a migration regression.)
- [x] ✅ [CODE] P0. **features-service `perp_funding_rates.py` — DONE (features-service@cf47eca9, 2026-06-02).** Rewrote
      the read path to resolve the canonical per-instrument shard via UAC `candidate_parquet_paths` (pipeline_mode-aware
      first, legacy fallback): `venue=BINANCE-FUTURES` / `instrument_type=perpetual` / `ETHUSDT.parquet` (UAC
      `SYMBOL_MAPPINGS` SSOT, not GCS-sampled — DNS-flaky host). Fixes all 4 broken axes (lowercase venue, missing
      instrument_type, single `derivative_ticker.parquet` filename, missing pipeline_mode); the broken
      `contains("ETH-PERP")` symbol filter is removed (path scopes to the one instrument). Regression-guard test asserts
      the canonical 4-axis path. 8 cefi unit tests green. (Original audit row retained below for context.)
- [x] ✅ [CODE] P0. **features-service read paths — RESOLVED (slot-3 2026-06-02)**: the one active regression risk
      (`perp_funding_rates.py` non-canonical `_MTDS_PATH_TEMPLATE`) shipped at features@cf47eca9 (✅ row above); all
      other features read paths verified canonical. This audit row is the original finding, retained for context —
      superseded by the ✅ fix. (Original audit text below.) features-service — audit (slot-3 agent A, 2026-06-02): MOST
      read paths are CANONICAL (delta_one/ volatility/cross_instrument use `resolve_bucket_name` + processed_candles
      manifest discovery; onchain=slot-2). **ONE ACTIVE REGRESSION RISK found —
      `features_service/cefi/calculators/perp_funding_rates.py:43-46` `_MTDS_PATH_TEMPLATE`**:
      `raw_tick_data/by_date/day={date}/asset_group=cefi/venue={venue}/data_type=derivative_ticker/derivative_ticker.parquet`
      is MULTIPLY non-canonical — (1) NO `pipeline_mode=` (→ 404s silently to an empty DataFrame after the legacy-path
      delete, zeroing cefi perp-funding-APY features), (2) lowercase `venue={venue}` ("binance") vs canonical UPPERCASE
      hyphenated (BINANCE-FUTURES), (3) NO `instrument_type=` segment. **FIX (diagnose-both-sides, do NOT guess):**
      build the read path via
      `candidate_parquet_paths("cefi","derivative_ticker", date, pipeline_mode=derive_pipeline_mode_for_row(     venue,"cefi","derivative_ticker").value, venue=<canonical>, instrument_type=<canonical>, file_name=…)`
      (returns the pm-aware path + legacy fallback) — but FIRST confirm the ACTUAL canonical cefi `derivative_ticker`
      object path on disk (venue casing + instrument_type) by sampling a real object, since the current template
      predates canonicalisation. Add a unit test asserting the pm-aware path so QG regresses on reversion. (Big finding
      — cefi data correctness; in features-service adjacent MVP code, tracked here not guess-fixed.) All other features
      read paths: CANONICAL, no change. **DISK-VERIFIED REFINEMENT (slot-3 2026-06-02)**: a real cefi derivative_ticker
      object is
      `…/day=2026-01-15/asset_group=cefi/venue=BITFINEX-FUTURES/instrument_type=perpetual/data_type=derivative_ticker/{instrument_id}.parquet`
      → the template is wrong on **4 axes** (lowercase `venue=binance` vs UPPERCASE-hyphenated `BINANCE-FUTURES`;
      missing `instrument_type=perpetual`; filename `derivative_ticker.parquet` vs per-instrument
      `{instrument_id}.parquet`; missing `pipeline_mode=`). It therefore **never matched the canonical layout = already
      returns empty TODAY** → this is a **pre-existing features-service MVP bug, NOT a migration regression** (the
      legacy delete cannot regress a read that's already empty). **De-risked for the migration: NOT a G1 blocker.**
      Reclassify as a features-service correctness fix: rewrite to resolve the real ETH-PERP binance derivative_ticker
      via `candidate_parquet_paths`/the MTDS reader with the canonical venue (BINANCE-FUTURES) +
      instrument_type=perpetual + per-instrument id + pipeline_mode. Owner: features epic.
- [x] ✅ [CODE] P0. **instruments-service** — VERIFIED CANONICAL (slot-3 agent A, 2026-06-02): reads/writes resolve
      `instruments-store-{ag}-prd` via `resolve_bucket_name`; `record_*` calls carry explicit pipeline*mode
      (BATCH_INSTRUMENTS_SERVICE etc.); only ops/migration scripts reference legacy bucket names (intentional). One
      minor ambiguity flagged (a `reconcile*\*`one-shot script's prediction`kind` resolution) — not a live read path.
- [x] ✅ [CODE] P0. **deployment-api — DATA-STATUS — VERIFIED CANONICAL for cefi/tradfi/prediction (slot-3 agent B,
      2026-06-02), no migration blocker.** `DataStatusService._build_manifest_category` → `_read_defi_merged_index` →
      `resolve_bucket_name` (prediction via `PREDICTION_KIND_MAP`→`pred` token; cefi/tradfi via `kind`+`asset_group`);
      drilldown `build_bucket_name` + `BUCKET_MAPPING` (batch_config_utils) all use `resolve_bucket_name`; index read =
      `read_availability_index(_index/availability_index.parquet)` which backfills v1-v8 + PRESERVES v9 cols;
      `pipeline_mode` filter is column-presence-guarded; `asset_group=` canonical with `category=` fan-out tolerance
      (storage_facade). NO dead-bucket read for our 3 AGs post-delete. **4 flags surfaced (none block G1 — tracked
      below).**
- [ ] [CODE] P1. **FLAG 1 (data-status): TradFi multi-source double-count — DECIDED (operator 2026-06-02): UNION +
      manifest per-source breakdown.** With v9 Databento+Massive dual-source the manifest carries two rows per
      (venue,data_type,date); `_mtds_honest_coverage_for_venue` counts distinct dates WITHOUT
      `select_primary_available_source` dedup → inflated `found_dates`. **Resolution:** (1) headline coverage = union —
      dedupe via `select_primary_available_source` (UAC `source_priority`) so a cell is green if ≥1 source captured; (2)
      per-source breakdown (databento vs massive) in the drilldown derived from the `_index` `source` COLUMN already
      loaded by `read_availability_index` (`groupby("source")` on the in-memory rows — NOT a per-parquet scan; the v9
      manifest denormalises `source` to the row level so this is free). QG test: 2 source-rows on one date → 1
      found-date (union) + the per-source split. NOT a migration regression — display-correctness. Cross-ref
      `tradfi_massive_dual_source`. (No longer operator-blocked.)
- [ ] [CODE] P1. **FLAG 3 (bucket-SSOT, deployment-api) — DECIDED (operator 2026-06-02): env-tier the `*-store` buckets,
      `-prd` initial.** `commentary/pipeline_uat.py:167/181/195/211` (+ `deployment_api_config.py:547`
      `ml-configs-store`) hardcode no-env `instruments-store`/`features-store`/`ml-store`/`execution-store` (NOT in
      cloud-providers.yaml). These buckets ARE in scope for env-tiering → `# CORRECT-LOCAL` markers come off; route
      through `resolve_bucket_name(kind=…,     env=…)` (resolves to `-prd` initially). Prereq: bucket-SSOT owner
      registers the env-tiered `*-store` names (prd/stg/dev) in cloud-providers.yaml (`bucket_name_ssot…`). prd-store
      data migrates to `-prd` in the initial migration; no-env buckets become legacy → deleted post-cutover. Coordinate
      with the active deployment-api agent.
- [ ] [CODE] P2. **FLAG 4 (display): TRADFI honest-coverage denominator**
      `MTDS_CATEGORY_META["TRADFI"].venue_accessor =     all_databento_venues` (6 venues) omits Massive-only venues →
      misleading coverage for Massive venues. Operator/VenueMapping decision (add Massive venues to the accessor).
      Display correctness, not a migration blocker.
- [ ] [CODE] P2. **FLAG 2 (DEFI scope → slot-2 / bucket_name_ssot): `_BUCKET_CATEGORY_OVERRIDES`**
      (data_status_service.py:2902) hardcodes 6 DeFi sub-buckets
      (`gas-fees`/`oracle-prices`/`perp-funding`/`lending-indices`/`lst-rates`/`liquidations`) bypassing
      `resolve_bucket_name` + absent from yaml → post-delete silent-empty (swallowed except). **DEFI=slot-2 — tracked in
      `defi_manifest_canonicalisation_2026_06_01.md` §H** (five-slot asset-group split, operator 2026-06-03) +
      `bucket_name_ssot…` L6. Not in another AG slice's scope.
- [x] ✅ [CODE] P0. **deployment-ui — DATA-STATUS — VERIFIED CANONICAL (slot-3 agent B, 2026-06-02), no change needed.**
      The UI builds NO bucket names + makes NO GCS calls — it is a pure consumer of deployment-api responses, passing
      `asset_group` query params (CEFI/TRADFI/PREDICTION; never `category=`; has a backward-compat
      `categories`→`asset_groups` shim). No client-side legacy bucket/menu/data_type assumptions. No UI behavior changed
      → playwright gate N/A.
- [ ] [CODE] P0. **QG-test alignment (cross-repo)**: for each repo above, the tests that feed `quality-gates.sh` MUST
      assert the CANONICAL form (canonical bucket via resolver, pipeline_mode= path, v9 manifest, asset_group=, on-disk
      data_type) so QG **fails on any reversion** to a dead bucket / old convention — this is the regression net the
      operator requires. (PREP3 already updated 18 MTDS write-path assertions; extend the same to read/status tests.)

> **Sequencing**: this preflight is a HARD GATE before the per-AG **G1 dry-run** (the migration gates live in
> `cf_data_state_audit_slot3_2026_06_01.md` § GATES). Rationale: dry-run is read-only + safe, but we want the code
> canonical + QG-green FIRST so the migration runs against a codebase that already expects the canonical form and can't
> silently regress to dead buckets when L6/E7 deletes legacy. Cross-link:
> `bucket_name_ssot_legacy_dual_write_remediation_2026_06_01.md` (L6 owns the bucket-name SSOT + the actual delete).

## PRE-MIGRATION PERFECTION — expanded scope (operator 2026-06-02): do ALL of these BEFORE any migration run

> Operator: "do them all pre-migration, I want it perfect." Two NEW directives below + every tracked non-blocker
> (prediction E5 build, features perp_funding rewrite, the 4 deployment-api flags) is now **pre-migration REQUIRED**,
> not deferred. None are post-cutover.

### D. `category=` is BANNED everywhere — v9 `asset_group=` canonical ONLY (operator 2026-06-02)

> Operator: "category shouldn't be allowed anywhere even as a fallback in data-status — it will confuse counts; we want
> v9 post-migration canonical only." Post-migration every object is `asset_group=`; a lingering `category=` fallback
> double-counts / confuses the data-status denominators.

- [x] ✅ [CODE] P0. **`category=` banned at the COUNT/logical layer — DONE (deployment-api@41fa120 by harsh-side agent,
      verified slot-3 2026-06-02).** `trading_axis.py` / `shard_management.py` / `data_status_drilldown.py` /
      `mock_data.py` drop the `category=` fallback in the asset-group/count paths;
      `test_no_category_asset_group_fallback.py` QG ratchet added. **storage_facade.py `_HIVE_VOCAB_RE` fan-out is
      CORRECTLY RETAINED** (slot-3 verified) — per this todo's own ⚠️ SEQUENCING caveat, the on-disk objects are still
      `category=` until each AG's G3 migration runs (PREDICTION still writes `category=prediction` today), so removing
      the on-disk-read fan-out NOW would BLIND unmigrated-AG data-status. The ban belongs at the count/denominator layer
      (done) NOT the on-disk-read layer (kept until L6/E7 delete). **mtds rebuild `(?:category|asset_group)=` regex
      alternations are CORRECTLY KEPT** (audit FOOTPRINT-SCOPE: "legacy-TOLERATED … in migration/rebuild tools (correct
      — keep)"). So slot-3 scope (storage_facade + rebuilds) = verified-no-change; the count-layer ban shipped via
      @41fa120. Residual: the per-AG on-disk fan-out removal happens at each AG's G3/L6 (owned by `bucket_name_ssot…`
      L6), not pre-migration.

### E. Upstream pre-flight DATA checks in every service — post-migration SSOT + v9 schema + honest-absence + live/batch symmetry (operator 2026-06-02)

> Operator: "scan all the services for the asset groups in this slot and check we ALWAYS have upstream-data pre-flight
> checks in code using the NEW post-migrated SSOT bucket formats + v9 schemas (column checks where relevant), and
> 0-volume / NaN-price (and equivalent) where data is genuinely missing upstream and expected. Manifest + that we KNOW
> when data is incomplete-expected and that's marked. Live AND batch symmetry for the checks — just slightly different
> post-check: live = alerting / circuit-breakers / actions (bad data is DANGER live); batch = just fills what it can."

Each consumer service (MTDS→MDPS→features→strategy→execution) for **cefi/tradfi/prediction** MUST, before consuming
upstream data, run a PRE-FLIGHT DATA CHECK that:

1. **Resolves the POST-migration canonical SSOT** — `resolve_bucket_name` env-tiered bucket,
   `pipeline_mode=`/`asset_group=` path, v9 `_index` (NO `category=`).
2. **Validates the v9 SCHEMA + columns** it depends on (the specific columns each consumer reads — present + typed).
3. **Detects genuinely-missing-upstream + EXPECTED** — 0-rows / 0-volume / NaN-price / all-null-key-column (per
   data_type the right "empty" signal) and distinguishes it from a fetch failure (CF-11 3-way: `attempted_failed` vs
   typed `empty_confirmed` vs `SOURCE_RETURNED_ZERO`).
4. **Reads the MANIFEST to know incomplete-expected** — uses the `_index` capture_status (captured /
   empty_confirmed[reason] / attempted_failed / expected_unattempted) so the consumer KNOWS a cell is
   incomplete-but-expected and marks/propagates it (CF-6 `expected_unattempted` propagation) rather than silently
   treating absence as zero.
5. **Live = batch SYMMETRY for the CHECK, different ACTION**: identical detection logic in both modes (the SAME
   pre-flight function); the ACTION differs — **live**: raise/alert/circuit-breaker (bad/missing data is dangerous to
   trade on) per the alerting + autonomous-recovery matrix; **batch**: degrade gracefully, fill what's available, mark
   the gap honest (no halt). The check itself must NOT diverge live-vs-batch (banned: live-only data_types / read-time
   available_at).

- [x] ✅ [AUDIT] P0. **Scanned ALL slot-3 services for upstream pre-flight data checks (slot-3 agent E, 2026-06-02).**
      Matrix (C1 bucket / C2 v9-schema-assert / C3 missing-detect / C4 manifest-status / C5 live=batch):

      | Service | C1 | C2 | C3 | C4 | C5 |
      |---|---|---|---|---|---|
      | instruments-service | GREEN | GAP(writes-only) | GREEN | GREEN | GREEN |
      | MTDS | GREEN | GAP | GREEN | GREEN | GREEN |
      | MDPS | GREEN | GAP | GREEN | GREEN(batch)/**CRIT(live)** | **CRIT** |
      | features-service | GREEN | GAP | GREEN | GREEN | PARTIAL(live startup) |
      | strategy-service | GREEN | GAP | GREEN | GREEN(alloc)/GAP(live startup) | GAP |
      | execution-service | N/A | N/A | **CRIT(freshness unwired)** | **CRIT(no upstream manifest preflight)** | N/A(live-only) |

      **Bucket resolution (C1) GREEN everywhere** (all via `resolve_bucket_name`; `category=` only as legacy param-names /
      hive-agnostic read scans, NOT path construction). **Missing-detection (C3) + batch manifest-read (C4) GREEN.** Gaps
      are concentrated in (a) v9-schema-column ASSERTION on read (C2) and (b) LIVE-mode pre-flight symmetry (C5).

These 7 fixes (all pre-migration-required per operator "perfect"; CRITICALs are live-safety big findings):

- [x] ✅ [CODE] P0. **CRIT-2 (execution-service, BIG/live-safety) — DONE for the router order path
      (execution-service@3181f26b8, 2026-06-02).** New `assert_instruction_market_data_fresh(instruction, *, live_mode)`
      in `validation/freshness_gate.py` wired into `InstructionRouter.route_instruction` BEFORE handler dispatch (+
      `kill_switch.is_active()` fast-reject): NaN/Inf `benchmark_price` → reject (both modes); stale
      (`age=now-signal_ts` ≥ venue `MARKET_TICK_FRESHNESS` SLA) → arm `DATA_STALENESS` kill switch + raise in LIVE,
      log+degrade in BATCH (live=batch detection, mode-aware action). NaN guard also in `BaseHandler._validate_common`.
      12 freshness-gate unit tests (NaN both modes, stale-live arms kill switch, stale-batch degrades, fresh passes,
      no-contract skip). **Used `instruction.timestamp` as the benchmark-price-age proxy** (the model has no separate
      market-data ts; timestamp = mid-price-at-signal time). `live_mode` read from router config.
- [x] ✅ [CODE] P0. **CRIT-2 follow-up — DONE (execution-service@12561a9ee, 2026-06-02).** Extracted
      `assert_market_data_fresh_for_submit(*, instruction_id, operation, venue, benchmark_price, signal_timestamp, live_mode)`
      in `validation/freshness_gate.py` (the field-level primitive); `assert_instruction_market_data_fresh` now
      delegates to it so all THREE submit surfaces share ONE gate. Wired the two non-router paths: (1)
      `cli/handlers/live_execution_handler._execute_instructions` — `kill_switch.is_active()` fast-reject + gate
      (`benchmark_price=None` — the colocated `Instruction` carries none; `signal_timestamp=start_time`;
      `live_mode=True`); raised `DataStalenessError`(RuntimeError)/`BenchmarkPriceInvalidError`(ValueError) are caught
      by the loop's existing except handlers → skip that instruction, armed kill switch halts the rest. (2)
      `api/manual_instruction_api._execute_via_orchestrator` — NaN/Inf guard on the operator `price`
      (`signal_timestamp=None` — manual op has no signal ts; `kill_switch` already enforced at the endpoint via
      `_check_service_state`). 5 new primitive tests + existing router tests still green (via delegation). My files:
      basedpyright 0 + ruff clean + 17 freshness tests green. **Repo QG red ONLY on PRE-EXISTING FOREIGN violations on
      LDR (hardcoded project IDs in providers/\* + defi_lateral_loader; domain-client import in
      backtest/engine/setup.py) — flagged per Findings-Triage, not slot-3's.**
- [x] ✅ [CODE] P0. **CRIT-3 (execution-service) — DONE (execution-service@225797127, 2026-06-02).**
      `run_preflight_checks()` now runs `_check_upstream_consolidator_health(upstream_buckets)` →
      `assert_consolidator_healthy(bucket)` (UTL shared gate, via `asyncio.to_thread` for the blocking GCS stat) so a
      stale/dead upstream `_index` fails preflight before a live session accepts orders. New `skip_upstream_data` /
      `upstream_buckets` params (default = configured `market_data_source_bucket`). 3 tests (stale→PREFLIGHT_FAILED,
      healthy×N passes, skip disables) + autouse no-op fixture. **Refinement OPEN (P1):** the deeper per-cell
      `capture_status` check (reject on `attempted_failed`/`expected_unattempted` for the specific cells a session
      reads) — consolidator-health is the liveness half; per-cell coverage is the next layer.
- [x] ✅ [CODE] P0. **CRIT-1 (MDPS live=batch symmetry) — DONE (market-data-processing-service@9102321, 2026-06-02).**
      `live_mode_handler._process_cycle` no longer passes `skip_dependency_check=True`; it now calls
      `process_category(skip_dependency_check=False, fail_on_missing_deps=False)` → live runs the SAME
      `_check_dependencies` as batch (the existing `_record_expected_unattempted_on_skip` path emits
      `expected_unattempted` on a gap, then degrades — does NOT halt the cycle). The orchestration-side machinery
      (`_check_dependencies`/`_record_expected_unattempted_on_skip`/UPSTREAM_LIVE_GAP gate) already existed; only the
      live call-site flag was wrong. Test asserts the live cycle does not skip the dep check.
- [x] ✅ [CODE] P1. **GAP-5 (strategy-service) — DONE (strategy-service@d837ca1b, 2026-06-02).**
      `StrategyLiveHandler.run()` asserts the upstream market-data consolidator healthy (`assert_consolidator_healthy`
      on `market-data-tick-{ag}-prd`) BEFORE the live trade loop / dispatch — refuses to start streaming signals off a
      stale upstream index (the per-cycle allocation guard only runs after start). Gated by `--skip-dependency-check`. 3
      unit tests (healthy proceeds, stale raises pre-dispatch, skip bypasses).
- [x] ✅ [CODE] P1. **GAP-6 (features-service) — DONE (features-service@dbf12aff, 2026-06-02).** delta_one
      `LiveHandler.run()` asserts the upstream MDPS candle consolidator healthy (`assert_consolidator_healthy` on
      `market-data-tick-{ag}-prd`) BEFORE PubSub subscribe — live fails-to-start on a stale candle index rather than
      computing on it. Gated by `skip_preflight`/`skip_dependency_check` + `fail_on_missing_deps`. 3 unit tests.
- [ ] [CODE] P2. **GAP-4 (all consumers): ASSERT v9 schema columns on manifest read.** `read_availability_index`
      backfills missing v9 cols as NULL on a v8 manifest → consumers silently read NULL
      `asset_group`/`pipeline_mode`/`source`. Add a `schema_version`/`asset_group`-present assertion (or
      `assert_consolidator_healthy`) in `manifest_window_guard`
      (features-service@`features_service/common/manifest_window_guard.py:85` — after `read_availability_index`),
      `manifest_allocation_guard` (strategy-service@`strategy_service/manifest_allocation_guard.py`), MDPS
      `dependency_checker` so a non-v9 upstream is caught loud, not silently consumed. **⚠️ DESIGN NUANCE (slot-3
      2026-06-02 — why deferred, not shipped half-baked):** the prod corpus is **100% v8 TODAY** (pre-migration), so a
      hard `schema_version==9` assert would break EVERY consumer immediately, and an unconditional warn would fire on
      100% of reads (pure noise). Ship it as a **loud WARN that fires only on MIXED-version drift** (some rows v9, some
      not, within one read) OR an `asset_group`-column-absent-on-a-supposedly-migrated-bucket signal — the real
      post-migration regression — NOT a blanket "not v9" warn. Becomes a hard assert only AFTER each AG's G3 migration
      flips its corpus to v9. P2 + warn-only → low value pre-migration; real value is the post-migration regression
      catch. (slot-3 2026-06-02: deferred under context budget with this design spec so the next agent ships the
      non-noisy form.)
- [x] ✅ [CODE] P2. **GAP-7 (MDPS, vocab) — DONE mdps@4363bce** (2026-06-11; re-verified 2026-06-16: zero checker
      `category` params remain — every `dependency_checker` signature uses `asset_group`; the 3 residual `category`
      string refs are framework template-var / manifest-column names, a separate `category=`-ban vocab concern, NOT this
      rename). Rename `dependency_checker` `category` params → `asset_group` (+ docstrings) done. Functional-correct
      today (resolves via `resolve_bucket_name(asset_group=…)`); naming only. (slot-3 2026-06-02: deliberately NOT done
      this session — a pervasive cosmetic rename across `check_upstream_data_granular`/
      `_resolve_upstream_bucket`/`_get_upstream_deps_for_category` + all callers risks collision with the parallel
      `category=`-ban work + adds churn for zero functional gain; do it when `dependency_checker.py` is substantively
      touched.)

## Deferred work after 2026-06-02 slot-3 session (code-only, pre-migration, NO migration run)

| Item                                               | Status                                           | Repo / file                                                  | Next action                                                                                                                                                                 |
| -------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Item 1 prediction E5 captured-atom rebuild         | ✅ shipped                                       | mtds@d1f1317d                                                | E5 empty/failed-row re-emit (CF-11) still open — see prediction plan                                                                                                        |
| CRIT-2 router order-path freshness+NaN gate        | ✅ shipped                                       | execution-service@3181f26b8                                  | NON-router paths now ALSO gated — execution-service@12561a9ee (shared `assert_market_data_fresh_for_submit` primitive)                                                      |
| CRIT-3 upstream consolidator preflight             | ✅ shipped                                       | execution-service@225797127                                  | per-cell `capture_status` refinement (P1) — tracked above                                                                                                                   |
| CRIT-1 MDPS live=batch dep check                   | ✅ shipped                                       | mdps@9102321                                                 | —                                                                                                                                                                           |
| Item 4 features perp_funding canonical read        | ✅ shipped                                       | features-service@cf47eca9                                    | —                                                                                                                                                                           |
| GAP-6 features delta_one live-startup gate         | ✅ shipped                                       | features-service@dbf12aff                                    | —                                                                                                                                                                           |
| GAP-5 strategy live-startup gate                   | ✅ shipped                                       | strategy-service@d837ca1b                                    | —                                                                                                                                                                           |
| Item 3 Directive-D `category=` count-layer ban     | ✅ done by other agent                           | deployment-api@41fa120                                       | slot-3 verified storage_facade/rebuild fan-out correctly retained (sequencing)                                                                                              |
| GAP-4 v9-schema warn at consumer guards            | ⏳ DEFERRED (design-spec'd)                      | features/strategy/MDPS guards                                | ship the MIXED-version-drift warn (NOT blanket "not v9" — noise pre-migration); see GAP-4 nuance above                                                                      |
| GAP-7 MDPS `category`→`asset_group` param rename   | ⏳ DEFERRED (P2 cosmetic)                        | MDPS `dependency_checker.py`                                 | rename at next substantive touch                                                                                                                                            |
| Item 5 FLAG-1 tradfi multi-source double-count     | ⏳ DEFERRED (P1, operator-decision)              | deployment-api `_mtds_honest_coverage_for_venue`             | apply `select_primary_available_source` union dedup; operator: union vs per-source                                                                                          |
| Item 5 FLAG-3 pipeline_uat hardcoded buckets       | ⏳ DEFERRED (P1)                                 | deployment-api `commentary/pipeline_uat.py:167/181/195/211`  | route through `resolve_bucket_name` (note: lines carry `# CORRECT-LOCAL` — confirm intent first)                                                                            |
| Item 5 FLAG-4 tradfi denominator (Massive venues)  | ⏳ DEFERRED (P2, operator/VenueMapping decision) | deployment-api `MTDS_CATEGORY_META["TRADFI"].venue_accessor` | add Massive venues to accessor                                                                                                                                              |
| Batch=live None-classifier divergence (prediction) | ✅ shipped                                       | mtds@5744ba61                                                | live Polymarket adapter + orchestrator finalize now route None→attempted_failed[ClassifierConfidenceLow] (batch=live). Kalshi same-fix follow-up tracked in prediction plan |

> **QG-sweep result (slot-3 2026-06-02, `--no-fix` × 5 touched repos):** execution-service ✅, strategy-service ✅,
> features-service ✅ (one MY import-patterns violation — deep UTL import — fixed in features-service@cefd5b54).
> **mtds + MDPS exit-1 are FOREIGN failures, NOT slot-3's changes:** mtds = 2 sports tests
> (`test_{migrate,rebuild}_sports_*::*_unresolved_season_suffix_unchanged`, last touched sports@df391e7c); MDPS = 9
> `test_dependency_checker_sports_prediction.py` routing/output-bucket tests (last touched mdps@61900a3
> bucket-resolution change). Neither file is in any slot-3 commit (slot-3 mtds = `rebuild_prediction_manifest.py`;
> slot-3 MDPS = `live_mode_handler.py`). **Flagged to sports slot / MDPS-bucket-resolution owner** — slot-3 does not fix
> foreign-owned failing tests (Findings-Triage: foreign → annotate, don't stomp). slot-3's own changed-file tests all
> GREEN.
>
> **Session note (slot-3 2026-06-02):** 8 substantive code commits shipped across 5 repos (all CRITs + P0/P1 items),
> each per-file lint+typecheck+targeted-test green; full `quality-gates.sh --no-fix` sweep run on all 5 touched repos as
> the batch closeout (operator-requested deferral of the slow sweep to end). Deferred items above are tracked `- [ ]`
> todos (P2/cosmetic/operator-decision/deployment-api-overlap), deferred under context budget rather than shipped
> half-baked. NO migration run, NO `--apply`, NO delete — code-only, post-migration-aligned per the governing principle.

## Deferred work after 2026-06-02 slot-3 session B (code-only; NO migration run)

> Second slot-3 session (2026-06-02). Shipped: item 4 (batch=live None-classifier, mtds@5744ba61) + item 3 (CRIT-2
> non-router gate, execution-service@12561a9ee), each per-shippable-unit committed + plan-flipped same-turn. Item 1
> CF-11 write-path DIAGNOSED (MTDS verified-compliant; IS residual) + annotated in all 3 AG plans. Kalshi
> None-classifier follow-up captured (prediction plan). The remaining items below are tracked `- [ ]` todos — NOT
> shipped this session (context budget; several are P2 / operator-decision / migration-time, none on the live critical
> path).

| Item                                                                                 | Status                                          | Repo / next action                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------ | ----------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Item 4 batch=live None-classifier (Polymarket)                                       | ✅ shipped                                      | mtds@5744ba61 — flipped                                                                                                                                                                                                                                                                                                            |
| Item 3 CRIT-2 non-router freshness gate                                              | ✅ shipped                                      | execution-service@12561a9ee — flipped (repo QG red ONLY on pre-existing FOREIGN violations)                                                                                                                                                                                                                                        |
| Item 1 CF-11 write-path                                                              | 🔎 DIAGNOSED (MTDS compliant)                   | RESIDUAL: focused instruments-service write-path verify (record_failed not record_empty on IS fetch error). MTDS = no work. Annotated in cefi/tradfi/prediction § CF-11                                                                                                                                                            |
| Kalshi None-classifier divergence                                                    | ⏳ tracked `- [ ]`                              | mtds Kalshi adapter — same fix as Polymarket (emit None not "OTHER"); prediction plan. Low live urgency (Polymarket-only corpus today)                                                                                                                                                                                             |
| Item 2 E5 rebuild CF-11 (within-bounds→failed + existing-row re-emit + 41 SRZ audit) | ⏳ tracked `- [ ]`                              | rebuild\_{cefi,tradfi,prediction}\_manifest.py — MIGRATION-TIME (not live); read prior `_index` via `read_availability_index` + re-emit typed rows; pre-launch check via venue_launch_dates                                                                                                                                        |
| Item 5 FLAG-1 tradfi multi-source double-count                                       | ⏳ tracked (P1, operator-decision)              | deployment-api — union vs per-source semantics; operator decides                                                                                                                                                                                                                                                                   |
| Item 5 FLAG-3 pipeline_uat hardcoded buckets                                         | ⏳ tracked (P1, AMBIGUOUS)                      | deployment-api commentary/pipeline_uat.py:167/181/195/211 — lines carry `# CORRECT-LOCAL` markers that CONFLICT with the FLAG-3 ask; needs reconciliation with the bucket-name-SSOT owner (do these store buckets get env-tiered/deleted? if not, CORRECT-LOCAL is right). Another agent active in deployment-api. NOT a blind fix |
| Item 5 FLAG-4 tradfi denominator (Massive venues)                                    | ⏳ tracked (P2, operator/VenueMapping decision) | deployment-api MTDS_CATEGORY_META["TRADFI"].venue_accessor                                                                                                                                                                                                                                                                         |
| Item 6 GAP-4 v9-schema mixed-version-drift warn                                      | ⏳ tracked (P2, design-spec'd)                  | features/strategy/MDPS guards — ship MIXED-version warn (NOT blanket "not v9"; corpus 100% v8 today)                                                                                                                                                                                                                               |
| Item 7 GAP-7 MDPS category→asset_group rename                                        | ⏳ tracked (P2 cosmetic)                        | MDPS dependency_checker.py — at next substantive touch                                                                                                                                                                                                                                                                             |
| Item 8 QG-test alignment (read/status)                                               | 🟡 partial                                      | writer-path 18 assertions done (prior session) + my new item-3/4 tests assert canonical/correct behavior; read/status-test extension remains                                                                                                                                                                                       |
| Item 9 doc sweep + supersession banners                                              | ⏳ tracked `- [ ]`                              | cf_data_state "Codex/plan doc-update TODOs" + supersession mapping                                                                                                                                                                                                                                                                 |
| Item 10 G1 read-only dry-run per AG                                                  | ⏳ NOT RUN                                      | gated on ALL coding complete (governing principle) + re-tarball/pin SHAs + VM launch (operational). Items 1-IS/2/5-9 still open → dry-run deferred to the operational session                                                                                                                                                      |

## Per-service scope + what each owns / inherits (no overlap)

| Service       | Surface                                                  | CF items it OWNS (live check)                                       | Notes                                                                                                                                                                          |
| ------------- | -------------------------------------------------------- | ------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **MDPS**      | `processed_candles/` (in the AG tick buckets)            | CF-1,2,3,5,8,9,11,12; **CF-4 source PROPAGATED** from the raw cell  | Per-AG plans already COPY `processed_candles/`; this plan ensures the canonical FORM + source propagation are audited there. Coordinate — no second walk on an AG tick bucket. |
| **features**  | `features-{onchain,delta-one,volatility,…}-{ag}`         | CF-1,2,3,5,8,9,11,12; **CF-4 EXEMPT** (computed — no vendor source) | defi §D backfill is the data; this plan is the FORM + exempt-source audit. CF-6 propagates upstream `expected_unattempted`.                                                    |
| **strategy**  | strategy output `_index` (signals / candidate manifests) | CF-1,2,5,8,9,12; **CF-4 EXEMPT** (computed)                         | Little data run → quick. CF-3/CF-10/CF-11 n/a (no raw fetch / no on-disk pipeline_mode).                                                                                       |
| **execution** | execution-record `_index` (fills / transfers / ledger)   | CF-1,2,5,8,9,12; **CF-4 EXEMPT** (computed)                         | Little data run → quick. Ledger rows still need v9 + `asset_group=` + typed reasons.                                                                                           |

**Key**: CF-4 `source` is **EXEMPT** for features/strategy/execution (computed outputs — lineage is the upstream cell,
not a vendor, per `data_source_provenance` COMPUTED_SOURCES). MDPS **propagates** the upstream raw cell's `source` so a
tardis-derived vs venue-derived candle stays distinguishable. So "source covered everywhere" = stamped on ingest
(mtds/instruments), propagated by MDPS, exempt for the pure-computed tail — verified, not blank-by-accident.

## Sequencing

Gated behind the upstream layers (foundation-completion-gate): a downstream service's walk is meaningful only after its
INPUT is canonical — MDPS after the AG MTDS walks; features after MDPS; strategy/execution after features. Audit can run
anytime (read-only); the migration walk per bucket follows its input going C-GREEN. L0 tarball-prune applies if on a VM.

## Phased execution

### P0 — per-service canonical-form AUDIT (run the SSOT checklist; small corpus → fast)

> **Scope is a prior, not a ceiling — fix-fully-autonomously (HARD RULE)**: "low-data / quick" is a prior, not a
> promise. Read DATA-STATE per service and fix EVERY CF-RED the audit surfaces in the same walk (the cefi precedent: a
> bucket framed "~complete" was actually 100% v8 / no source / no asset_group / blank pipeline_mode). NOT descoped,
> deferred, post-cutover, or `BLOCKED-OPERATOR-DECISION` (a data-state gap is not a design fork). SSOT:
> `canonical_form_cross_service_audit_checklist.md` § "Audit scope is a PRIOR, not a ceiling".

- [x] ✅ [DATA] P0. **MDPS** — data-state (slot-3, 2026-06-01): MDPS candles share the **same AG MTDS `_index`** as raw
      ticks (the `processed_candles/` prefix lives in `market-data-tick-{ag}-prd`; the AG `_index` carries `ohlcv_*` /
      `odds_horizon_bucket*` candle data_types alongside raw). The cefi/sports audits already cover them: **same
      systemic debt** (100% v8, no source col, blank pipeline_mode, no available_at, flat paths). So MDPS is **NOT a
      separate walk** — it rides each AG's MTDS single-walk (single-walk discipline; CF-4 source PROPAGATION from the
      raw cell lands there). Feeds `mtds_mdps_master_audit_instructions.md` Canonical-form section.
- [x] ✅ [DATA] P0. **features** — data-state: for the non-defi AGs (cefi/tradfi/sports/prediction) the
      `features-*-{ag}` buckets have **NO `_index/availability_index.parquet`** (surveyed
      `features-delta-one/mtf/volatility/calendar` × cefi/tradfi — all absent; only `features-onchain-defi-prd` has one
      = slot-2/defi). So **no features data has run** for my AGs → CF audit is vacuously N/A on data-state; the lever is
      the **WRITER fix (CF-5 typed reasons + CF-11 no-swallow + CF-4 exempt-computed + stamp
      v9/asset_group/pipeline_mode COLUMNS)** so the first volume lands canonical. CF-6 `expected_unattempted`
      propagates from upstream. Feeds `features_and_ml_master_audit_instructions.md`.
- [x] ✅ [DATA] P0. **strategy** — data-state: `strategy-store-{ag}-prod` buckets exist but carry **no materialized
      `_index`** (no strategy output run for my AGs). CF audit vacuously N/A; writer-fix lever (v9 + asset_group + typed
      reasons COLUMNS; CF-4 exempt). Feeds `strategy_master_audit_instructions.md`.
- [x] ✅ [DATA] P0. **execution** — data-state: `execution-store-{ag}-prod/prd` buckets exist but **no `_index`**
      (surveyed cefi/tradfi/pred — none). CF audit vacuously N/A; writer-fix lever (ledger rows v9 + asset_group + typed
      reasons; CF-4 exempt). Feeds `execution_master_audit_instructions.md`.
- [x] ✅ [DATA] P0. **Net downstream finding (low-data confirmed)**: only MDPS has data (rides the AG MTDS walk — no
      separate walk); features/strategy/execution for cefi/tradfi/sports/prediction have NOT run → no `_index` to
      migrate. The downstream walk (§C) is therefore **WRITER-FIX-FIRST**: ship the canonical-write fixes so the first
      volume is born canonical, rather than migrating a non-existent corpus. Re-audit each when its input goes C-GREEN +
      its first batch runs.

### C — single-walk per service bucket (only where P0 surfaces debt; bundle CF items)

> **Migration-script performance contract (HARD — codified 2026-06-01, defi C0 lesson)**: any walk script MUST be
> parallel (`ThreadPoolExecutor` — GCS I/O releases the GIL → 5–10×; a bare `for obj` loop is review-blocking) + wire
> `--workers`/`--start-date`/`--end-date` (date-shardable across VMs — no dead args) + `gcs_copy_object` for path-only
> moves (server-side ~250×) / download+transform+upload only for content changes + unbuffered progress logging
> (`python -u`, counter every ~1000) + per-object `try/except…continue` isolation + idempotent re-runs. (Corpus is small
> here, but the contract still applies.) SSOT: `codex/05-infrastructure/gcs-object-operations.md` § "Migration-script
> performance contract".

- [ ] [DATA] P1. **MDPS** C-walk: bundle any `processed_candles/` debt into the SAME AG tick-bucket walk (no second walk
      on an AG `_index` — single-walk discipline); ensure CF-4 source PROPAGATION + CF-1/2/3/5/8 land there.
- [ ] [DATA] P1. **features** C-walk: ONE bundled walk per `features-*-{ag}` index for any P0 debt (v9 +
      `asset_group=` + `pipeline_mode=` partition + typed reasons + `available_at`); CF-4 stays exempt.
- [ ] [DATA] P1. **strategy** C-walk: ONE bundled walk for strategy output `_index` debt (v9 + `asset_group=` + typed
      reasons + `available_at`). Small corpus → likely local, fast.
- [ ] [DATA] P1. **execution** C-walk: ONE bundled walk for execution-record/ledger `_index` debt (same set). Small
      corpus → likely local, fast.
- [ ] [CODE] P1. Writer fixes (all four): emit typed `EmptyConfirmedReason` + `attempted_failed`-not-swallow (CF-11) so
      future writes are canonical (the corpus is small precisely because little has run — fix the writer before volume
      arrives).

### Verify + handoff

- [ ] [DATA] P1. Post-walk per service: re-run the P0 CF audit → all applicable CF GREEN (data-state). Each service's
      canonical-form section in its audit-instruction file goes GREEN. Hands C-GREEN to `bucket_name_ssot…` L6 for any
      downstream legacy buckets.

## Success criteria

- MDPS/features/strategy/execution `_index`(es) all CF-applicable-GREEN (v9 + `asset_group=` + typed reasons + honest
  `available_at` + batch=live; `pipeline_mode=` partition where applicable; `source` propagated/exempt as classified —
  never blank-by-accident).
- Each downstream service's audit-instruction Canonical-form section is wired + runnable by the operator.
- No second walk opened on any AG tick `_index` (MDPS rides the AG walk).

## Codex SSOTs

- `plans/audit/instructions/canonical_form_cross_service_audit_checklist.md` — the CF checklist this plan audits.
- `codex/02-data/availability-manifest-and-data-status.md` — downstream canonical form + source propagation.
