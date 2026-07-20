---
doc_type: codex-ssot
title: Reconciliation finding taxonomy (closed set · severities · delete-eligibility · accepted-exception list)
summary: >-
  The CLOSED, named set of finding types the four-surface reconciliation emits — phantom, missing_row, orphan_real,
  true_gap, divergent_empty, missing_expected, non_canonical_path, legacy_duplicate, junk, manifest_infra, non_data,
  shard_pillar_fail, catalogue_gap, manifest_only, masked_empty_row, drift_axis_false_positive — each defined in terms
  of the four canonical surfaces, with its detection method, default severity, safe remediation, and whether it can EVER
  justify a delete. Carries the OPERATOR-ACCEPTED EXCEPTION LIST (suppression is mandatory, not optional) and the two
  axes the reconciliation skill must currently REFUSE to report on pending operator rulings. Without a closed set,
  consecutive runs emit prose that cannot be diffed and the delete-suggestion feature has nothing to key off.
status: current
nature: ssot
asset_group: [meta]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    unified-trading-library,
    e2e-testing,
  ]
scope: [engineer, admin]
tags:
  [
    reconciliation,
    finding-taxonomy,
    phantom,
    orphan,
    delete-safety,
    accepted-exceptions,
    manifest,
    canonicalisation,
    ssot,
  ]
related:
  [
    four-surface-reconciliation-procedure.md,
    cross-asset-canonical-target-ssot.md,
    availability-manifest-and-data-status.md,
    defi-canonical-naming-ssot.md,
    pipeline-mode-partition.md,
    tradfi-databento-sourcing-ssot.md,
    honest-coverage-model.md,
    cross-asset-rescan-protocol.md,
    ../../plans/active/data_pipeline_reconciliation_skill_2026_07_20.md,
    ../../plans/active/issues/canonical_closeout_open_questions_2026_07_18.md,
  ]
created: 2026-07-20
authoritative_for:
  [
    reconciliation finding type names,
    finding severity defaults,
    finding delete-eligibility,
    operator-accepted reconciliation exception list,
    axes the reconciliation skill must refuse to report on,
  ]
referenced_by:
  [
    codex/02-data/four-surface-reconciliation-procedure.md,
    codex/02-data/orphan-object-detection.md,
    codex/02-data/non-canonical-path-inventory.md,
    codex/02-data/cross-asset-canonical-target-ssot.md,
  ]
owner:
last_reviewed: 2026-07-20
code_refs:
  [
    instruments-service/scripts/reconcile_phantom_manifest_rows_all.py,
    instruments-service/scripts/migration_orphan_sweep.py,
    market-tick-data-service/scripts/reconcile_market_tick_manifest.py,
    market-tick-data-service/scripts/validate_manifest_coverage.py,
    unified-trading-library/scripts/detect_manifest_divergence.py,
    e2e-testing/scripts/validation/validate_shards_4pillar.py,
    e2e-testing/scripts/audit/manifest_hygiene_daily.py,
  ]
---

# Reconciliation finding taxonomy

> **What this doc is for.** Before this doc, the finding vocabulary lived in individual script docstrings and in plans:
> `phantom` in one script, `true_gap`/`missing_row` in another, `class A/B/C/D/E` in a third,
> `DIVERGENT_EMPTY`/`MISSING_EXPECTED` in a fourth. Nothing declared the SET. Two consequences, both measured: (1)
> consecutive reconciliation runs emitted prose that could not be diffed, so "did it get better?" was unanswerable; (2)
> the delete-suggestion feature had no safe/unsafe classification to key off.
>
> **This doc is the closed set.** A reconciliation report MUST type every finding as exactly one name below. A
> disagreement that fits no type is itself a finding — of a taxonomy gap — and gets escalated, never silently narrated.
>
> **Scope boundary.** The four surfaces and the per-shard comparison procedure are defined in
> `four-surface-reconciliation-procedure.md`; this doc names and grades the DISAGREEMENTS that procedure produces. The
> five-part delete proof is defined in `gcs-and-manifest-delete-safety-protocol.md`; this doc declares only which types
> are delete-ELIGIBLE (i.e. permitted to enter that proof at all). The living register of concrete non-canonical
> locations is `non-canonical-path-inventory.md`. This doc REFERENCES all three rather than duplicating them.

---

## 1. The four surfaces (names only — definitions live in the procedure doc)

| #   | Surface       | Concretely                                                                       |
| --- | ------------- | -------------------------------------------------------------------------------- |
| S1  | **GCS path**  | the object's hive path + leaf filename                                           |
| S2  | **Content**   | the parquet's rows + columns (`instrument_id`, defi `canonical_instrument_id`)   |
| S3  | **Manifest**  | the `_index/availability_index.parquet` shard-atom row and its `capture_status`  |
| S4  | **Catalogue** | the instruments/features/ml/strategy catalogue + the data-status render it feeds |

Every finding below is a statement about a DISAGREEMENT between a named pair (or the absence of one member).

---

## 2. The closed set

Fifteen estate types plus one tool-defect type. Names are lowercase snake_case and are the literal strings a report
emits.

### 2.1 Manifest ↔ GCS (S3 ↔ S1)

#### `phantom`

- **Definition** — an S3 row claims `capture_status=captured`, and NO parquet exists at any candidate canonical S1 path
  for that shard atom.
- **Why it is dangerous** — it is not cosmetic. The orchestrator's `_should_skip_shard` pre-flight TRUSTS the manifest,
  so a phantom row permanently skips the shard: "every backfill VM exits doing nothing"
  (`instruments-service/scripts/reconcile_phantom_manifest_rows_all.py:6-11`).
- **Detection** — `reconcile_phantom_manifest_rows_all.py --asset-group <AG> --dry-run`. Prefer READING the published
  `_index/phantom_audit_latest.json` over re-running (the run is a bulk multi-worker GCS listing costing minutes).
- **Severity default** — **HIGH**. RED for the asset_group if the count is non-zero and rising.
- **Safe remediation** — flip `captured → attempted_failed` so the shard becomes re-fetchable. Write-back MUST re-merge
  via `merge_canonical_with_outstanding_shards` immediately before the write (the staleness guard codified 2026-07-12,
  `…rows_all.py:36-50`) — never a raw `pd.read_parquet` of a point-in-time snapshot.
- **Delete-eligible** — **NO.** A phantom is a row, not an object; there is nothing on disk to delete.
- **False-positive hazard** — see `drift_axis_false_positive` (§2.6). A phantom count is only trustworthy from a tool
  whose prefix set is DERIVED from `canonical_path_templates(ag)`.
- **HARD RULE** — never run the phantom reconciler against `prediction`: its CQG bundle grain is mis-keyed by this tool.

#### `missing_row`

- **Definition** — a parquet EXISTS at a canonical S1 path, and NO S3 row points at it.
- **Detection** — `market-tick-data-service/scripts/reconcile_market_tick_manifest.py --asset-group <AG> --dry-run`,
  which emits exactly this category (`:22-24`). The instruments-side inverse is
  `instruments-service/scripts/enumerate_expected_universe.py` (scan-only by default).
- **Severity default** — **HIGH**. Real data invisible to every downstream reader is a coverage understatement, i.e. it
  silently depresses honest coverage.
- **Safe remediation** — add `captured` rows via a per-VM shard, consumed by the consolidator (~60s latency). No vendor
  credits are spent (`:26-28`).
- **Delete-eligible** — **NO.** The correct action is to ADD a row, never to remove the data.

#### `true_gap`

- **Definition** — NEITHER S3 nor S1 has data for a shard atom the expectation oracle says should exist.
- **Detection** — same script, category `true_gaps` (`:20`).
- **Severity default** — **MEDIUM**. It is honest absence, correctly represented; it is a backfill backlog item, not a
  correctness defect.
- **Safe remediation** — schedule a real backfill. This is the ONLY finding type whose fix costs vendor credits, which
  is precisely why it must be told apart from `phantom` before anyone re-fetches (`:33-38`).
- **Delete-eligible** — **NO.**

#### `orphan_real`

- **Definition** — an object on S1 with a VALID shard shape and `rows > 0`, with NO S3 row, **and outside the oracle's
  expected set** — i.e. it is not merely an unrecorded canonical cell (that is `missing_row`) but data nobody knew to
  look for. Class **E** in the sweep's forced classification
  (`instruments-service/scripts/migration_orphan_sweep.py:25-27, :101, :363`).
- **Why it matters** — it is the silent-write / manifest-completeness bug. The sweep's own comment: "**WE NEED IT**:
  `record_captured` backfill, NEVER delete" (`:25-27`).
- **Detection** — `migration_orphan_sweep.py --asset-group <AG> --dry-run` (plus the `_sports` variant). This is the
  ONLY whole-corpus GCS enumerator and therefore the ONLY sanctioned orphan route; it is also the reconciliation's
  SINGLE WALK — bundle every pass onto its one snapshot.
- **Severity default** — **HIGH**. Acceptance bar is `orphan_class_E == 0` per asset_group (CF-17, `:36-38`).
- **Safe remediation** — `record_captured` backfill of the missing rows.
- **Delete-eligible** — **NO. Never.** Explicit in the defining script.
- **Caveat to carry** — `migration_orphan_sweep.py` is marked `# Lifecycle: oneoff` (`:3`) while UAC treats it as a
  durable SSOT consumer. Resolve the lifecycle marker before depending on it as a standing detector.

#### `legacy_duplicate`

- **Definition** — an object at a LEGACY-shape S1 path whose canonical cell IS manifested. Class **B**
  (`migration_orphan_sweep.py:20, :97, :356`).
- **Detection** — the sweep (class B), plus `e2e-testing/scripts/defi/audit_legacy_gcs_dup_delete_list.py`, which
  derives each legacy object's canonical `pipeline_mode` twin and classifies SAFE-TO-DELETE vs MIGRATE-FIRST.
- **Severity default** — **LOW** as a correctness matter (the data IS represented canonically); **MEDIUM** as a cost
  matter at scale.
- **Safe remediation** — copy-first, never move. `migrate_legacy_twins_from_audit.py` is COPY-ONLY by construction.
- **Delete-eligible** — **YES, and it is the ONLY delete-eligible type carrying real data.** Eligible means "may enter
  the five-part proof", not "may be deleted". Path-existence of a twin is explicitly INSUFFICIENT — the R5 precedent
  measured a PARTIAL overlap (66-of-98 intersection) behind an existence check that read as full duplication. A CONTENT
  verify is mandatory. See `gcs-and-manifest-delete-safety-protocol.md`.

#### `junk`

- **Definition** — class **D**: an unparseable hive key, a shard shape outside the valid could-exist space, or a
  zero-row object with no manifest row (`migration_orphan_sweep.py:24, :100, :325, :346, :362`, plus the footer-read
  refinement at `:570-573`).
- **Severity default** — **LOW**.
- **Delete-eligible** — **YES**, and it is the least contentious case: an unparseable or zero-row object carries no
  recoverable data. Still routes through the five-part proof; still a human-only hard stop on a prod bucket.

#### `manifest_infra`

- **Definition** — class **C**: `_index/`, `*.tmp`, `*.partial`, `_SUCCESS` (`:21, :98`).
- **Severity default** — **INFO**. Reported for completeness only, so the taxonomy can claim "every byte accounted for"
  (the sweep's 0-`unknown` acceptance bar, `:29-31`).
- **Delete-eligible** — **NO** (except `*.tmp`/`*.partial` under an explicit, separately-ruled janitor policy — not this
  reconciliation's business).

#### `non_data`

- **Definition** — class **C2**: VM logs, run artifacts, terraform state, tarballs (`:22-23, :99`).
- **Severity default** — **INFO**.
- **Delete-eligible** — **NO. Never.** The defining script states these are "kept, labelled, NEVER deleted — operator
  2026-06-10" (`:22-23`). A reconciliation that proposes deleting a class-C2 object is malfunctioning.

### 2.2 Path canonicality (S1 vs the machine oracle)

#### `non_canonical_path`

- **Definition** — an object exists at an S1 path that the UAC machine oracle
  (`unified_api_contracts.canonical_path_violations` / `is_canonical`) rejects.
- **Detection** — `e2e-testing/scripts/audit/manifest_hygiene_daily.py`, which emits `DP_NONCANONICAL_PATH_ON_DISK` and
  computes it index-only (no corpus walk) by running the oracle over the manifest's IMPLIED paths (`:14-19, :57-60`).
- **Severity default** — **MEDIUM**, and **date-conditional**: pre-cutover data is legitimately historical, not
  non-canonical. Grade against the per-AG effective-from dates in `canonical-cutover-register.md`. Without that gating
  the finding either floods false positives on old data or silently passes post-cutover regressions.
- **Known weakness to state in every report** — the oracle's `require_pipeline_mode` defaults **False**, so the machine
  gate is currently WEAKER than the codex declaration. A report must name which setting it used.
- **Second known weakness — the oracle does NOT validate the filename instrument-id.** It drops the last path segment
  before validating; only `asset_group=tradfi` single-instrument shards have a stem rule. So a wire-named or
  double-wrapped CeFi object (`ADAF0:USTF0.parquet`, `BITFINEX-FUTURES:PERPETUAL:ADAF0:USTF0.parquet`) **can never raise
  this finding** — ~811,200 such objects read as canonical. Path STRUCTURE and instrument-id FORM are orthogonal; a
  report must either run the canonical-id check separately or state plainly that id-form was not machine-checked. SSOT:
  `plans/active/issues/canonical_path_oracle_blind_to_filename_stem_2026_07_20.md`.
- **Safe remediation** — migrate (copy) to the canonical path. Never in this reconciliation's own process.
- **Delete-eligible** — **NO, not on this finding alone.** Non-canonical location is not evidence of duplication. It
  becomes delete-eligible only if it independently classifies as `legacy_duplicate` with a CONTENT-verified twin.

### 2.3 Expectation oracle ↔ manifest (oracle ↔ S3)

Both types below come from `unified-trading-library/scripts/detect_manifest_divergence.py`, whose classifier is at
`:204-224`.

#### `divergent_empty`

- **Definition** — oracle says `SHOULD_HAVE_DATA`; the manifest has an `empty_confirmed` row and no captured row
  (`:211-215`).
- **Severity default** — **HIGH**. This is the shape of a real fetch failure wearing an honest-absence costume.
- **Safe remediation** — re-attempt the shard; if it stays empty, the ORACLE is wrong and the expectation needs
  correcting — one of the two must move.
- **Delete-eligible** — **NO.**

#### `missing_expected`

- **Definition** — oracle says `SHOULD_HAVE_DATA`; there is NO manifest row of any status (`:211, :219`).
- **Severity default** — **MEDIUM**. Distinguished from `divergent_empty` by the absence of any claim at all.
- **Delete-eligible** — **NO.**

> The same classifier also emits `UNEXPECTED_CAPTURED` (oracle `EXPECTED_EMPTY`, data present) and
> `UNEXPECTED_PRE_LAUNCH_CAPTURED` (oracle `NOT_YET_LIVE`, data present) at `:221-224`. Both are **oracle defects, not
> estate defects** — report them as severity **MEDIUM** under the name `oracle_contradiction`, and never resolve them by
> deleting the data.

### 2.4 Catalogue leg (S4 ↔ S3)

From `market-tick-data-service/scripts/validate_manifest_coverage.py:15-23`.

#### `catalogue_gap`

- **Definition** — the catalogue has the shard, the manifest does not (the script's `gap`, a.k.a. false-missing).
- **Severity default** — **HIGH**. The gate metric is `false_missing_rate = gap / (agree + gap)`, and the declared bar
  is **0%** (`:22-23`) — this is the natural per-AG PASS/FAIL bar for the catalogue surface.
- **Delete-eligible** — **NO.**

#### `manifest_only`

- **Definition** — the manifest has a row for an instrument no longer in the catalogue: a stale entry, or an orphan
  (`:20-21`).
- **Severity default** — **LOW**. Very often legitimate history — a delisted instrument's past data is still real.
- **Delete-eligible** — **NO.** Delisting is not a reason to destroy captured history.

### 2.5 Content leg (S2)

#### `shard_pillar_fail`

- **Definition** — a sampled parquet fails one of the four pillars: `row_count > 0`; NaN ratio under threshold (default
  1%); schema matches the UAC contract; cluster coverage meets expectation for bundled data_types
  (`e2e-testing/scripts/validation/validate_shards_4pillar.py:13-34`).
- **Detection** — `validate_shards_4pillar.py`, read-only by construction ("never writes GCS, never mutates the manifest
  index", `:36`).
- **Severity default** — **HIGH** for a pillar-1 or pillar-3 failure; **MEDIUM** for pillar 2 or 4.
- **Critical qualifier a report MUST print** — this check is **SAMPLED**, so it is a spot-check, NOT a proof. A green
  content surface means "no defect found in the sample", never "the corpus is clean".
- **Cross-link** — pillar 1 is the content-side detector of `phantom`: a 0-row parquet masquerading as `captured` is a
  phantom, and a `captured` manifest row with `row_count = 0` is a phantom signal (`:16-20`).
- **Delete-eligible** — **NO.** A zero-row parquet reaches delete-eligibility only via `junk` (class D), i.e. only when
  it ALSO has no manifest row.

#### `masked_empty_row`

- **Definition** — an `empty_confirmed` manifest row carrying a BLANK `error_reason`, which silently masks a real fetch
  failure as honest absence.
- **Provenance** — the 2026-05-07 RED ALERT: 5 CeFi VMs at 96-100% empty with all blank reasons
  (`unified-api-contracts/unified_api_contracts/canonical/crosscutting/_honest_coverage_logic.py:543-556`). The writer
  now raises `LegacyBlankErrorReasonError` on `record_empty(reason="")`, so this type is HISTORICAL-ONLY going forward.
- **Severity default** — **HIGH** if any post-guard row appears (that would mean the guard is bypassed); **MEDIUM** for
  historical rows.
- **Safe remediation** — `reconcile_blank_error_reason_rows.py`: catalogue-says-alive rows reclassify to
  `attempted_failed`; catalogue-says-not-alive rows get a proper typed `EXPECTED_*` reason (`:552-556`).
- **Delete-eligible** — **NO.**
- **Naming note (UNVERIFIED as a pre-existing name)** — the plan corpus refers to this class as "masked-stale-row". No
  script or codex doc defines that literal string; the underlying defect above IS defined in code, at the citation
  given. `masked_empty_row` is therefore this doc's NORMALISATION of an informal label onto a verified defect, not the
  adoption of an existing term. Any report using the old label should be read as this type.

### 2.6 Tool-defect type (not an estate finding)

#### `drift_axis_false_positive`

- **Definition** — a finding produced by a detector whose expected-path set has drifted out of sync with what writers
  actually emit. It is a statement about the TOOL, not the estate, and it MUST NOT be counted in estate severity
  rollups.
- **Why it earns a name** — every axis is a measured incident, not a hypothetical. From
  `reconcile_phantom_manifest_rows_all.py`: the 2026-05-01 CeFi incident produced **181k false phantoms** from probing
  only the new key (`:100-102`); Axis-10 (hardcoded `prefix_tpls`) false-flagged real captured rows as phantom — cefi
  130k on 2026-05-03, AAVE_V3 29,782 on 2026-05-07, EIGENLAYER 597 on 2026-05-04 (`:118-127`); the DeFi
  protocol-underscore drift alone false-positived 29,782 AAVE_V3 rows (`:140-150`); Axis-7 Databento paired schemas
  produced identical 1,017-count false phantoms on both `trades` and `tbbo` (`:152-161`); Axis-8 `venue=UNKNOWN`
  produced ~565 TradFi + ~2k cross-asset false positives (`:164-170`); Axis-9 clips sports pre-coverage rows
  (`:339-347`).
- **Structural defence, not a checklist** — derive every prefix from
  `unified_api_contracts.canonical_path_templates(ag)` (`:114-133`). A hand-maintained prefix list IS the Axis-10 bug.
- **Severity default** — **HIGH against the tool**; the affected estate findings are SUPPRESSED, not downgraded.
- **Delete-eligible** — **NO.** A delete suggestion derived from a suspected drift-axis finding is the single most
  dangerous output this system can produce.

---

## 3. Delete-eligibility, consolidated

Exactly **two** of the sixteen types can ever justify a delete:

| Type               | Delete-eligible | Because                                                        |
| ------------------ | --------------- | -------------------------------------------------------------- |
| `legacy_duplicate` | **YES**         | a canonical twin may hold the same content — must be PROVEN    |
| `junk`             | **YES**         | unparseable / zero-row / no manifest row — no recoverable data |
| all fourteen other | **NO**          | each is either real data, a missing claim, or a tool defect    |

Three standing qualifiers:

1. **Eligible ≠ approved.** Eligibility only admits a candidate to the five-part proof in
   `gcs-and-manifest-delete-safety-protocol.md`. Any failed part ⇒ `no-migrate-first`.
2. **Deletes are SUGGESTIONS.** The reconciliation never deletes. Prod-bucket deletes, legacy-after-copy deletes, the
   tradfi `batch_massive` purge, and anything touching `instrument_type` casing are **human-only hard stops**.
3. **`non_data` (class C2) is a permanent NEVER**, independent of any proof.

---

## 4. Operator-accepted exception list (suppression is MANDATORY)

> Re-reporting an accepted exception as a fresh finding destroys the report's signal. The sports entry below has already
> cost twenty-plus audit dispatches. Each entry names the condition under which it STOPS being an exception — an
> exception with no exit condition is a permanent blind spot, which is a different failure.

### AE-1 — 19,274 sports IS rows with blank `pipeline_mode` + `source`

- **What** — 19,274 rows (0.3–0.4% of the corpus) in `instruments-store-sports-prd` carry a blank `pipeline_mode` AND a
  blank `source`.
- **Why accepted** — all predate 2026-07-08; confirmed unreachable by the real v9-migrator `--apply` run; no
  deterministic `pipeline_mode`/`source` is derivable from any existing column, and no raw-provider-payload trail was
  retrievable to reconstruct them (`codex/02-data/availability-manifest-and-data-status.md:637-645`;
  `instruments-service/scripts/restamp_is_sports_blank_source_2026_07_13.py:11-22`).
- **Ruled by / when** — operator, **BLK-d48acae4, answered 2026-07-13, decision A**.
- **Suppression rule** — any "0 blank `pipeline_mode`/`source` over full history" gate treats this residual as accepted.
  Report it as a named, counted, SUPPRESSED line, never as a finding.
- **Stops being an exception when** — the count EXCEEDS 19,274, or any blank-typed row appears with
  `attempted_at >= 2026-07-08`. Either means the live write-path gap has reopened; that is a fresh HIGH finding.

### AE-2 — tradfi `combo` bare-underlying carve-out

- **What** — tradfi `combo` shards keep the bare `underlying=…/ticks.parquet` fan-in and sit OUTSIDE the full-canonical-
  id filename guard that governs every other tradfi single type.
- **Why accepted** — the leg-aware combo id format is deliberately unsettled, so no full-id filename can be required
  yet. `combo` is explicitly excluded in the UAC path builder itself:
  `unified-api-contracts/unified_api_contracts/canonical/partition_paths.py:271-273` ("`combo` is deliberately EXCLUDED
  (its leg-aware id format is unsettled — combo chains keep the bare `underlying=.../ticks.parquet`") and again at
  `:278-280` and `:812`.
- **Ruled by / when** — carried in shipped code as a documented carve-out; the leg-aware spec is tracked at
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`
  (`codex/02-data/cross-asset-canonical-target-ssot.md:132-133`).
- **Suppression rule** — never flag a `combo` shard's bare `underlying=` tail as `non_canonical_path`.
- **Stops being an exception when** — the leg-aware combo id format is ruled and the filename guard is extended to
  `combo`.
- **⚠ ADJACENT DEFECT — NOT covered by this exception, and NOT suppressed.** The writer and the reader disagree about
  whether `combo` is underlying-partitioned:
  `market-tick-data-service/market_tick_data_service/engine/orchestrator/symbol_rules.py:258` has
  `frozenset({"options_chain", "futures_chain", "combo"})` (WRITES combo partitioned by `underlying=`), while
  `market-tick-data-service/market_tick_data_service/reader.py:62` has `frozenset({"options_chain", "futures_chain"})`
  (PROBES a combo shard as a single-instrument shard). Read as written, a combo shard is written to a path the reader
  will never find. This is a live cross-repo finding and must be reported at severity **HIGH**, not absorbed into AE-2.

### AE-3 — defi two-id POOL divergence (Option A, intentional)

- **What** — every address-identified defi row carries TWO ids, and the POOL-keyed rows show a deliberate divergence
  between them rather than a single rewritten id.
- **Why accepted** — the two-id model is the ruled design, chosen to avoid a mass historical rewrite: "**Two-id model
  (defi, Option A — intentional, NOT a gap)**" (`codex/02-data/cross-asset-canonical-target-ssot.md:202`), restated in
  the operator log at `:256` ("defi two-id model kept (Option A, no mass rewrite)"). POOL rows are additionally
  protected by the pool-address `agg_key` collapse (`codex/02-data/defi-canonical-naming-ssot.md:212`).
- **Ruled by / when** — operator, 2026-07-18 close-out.
- **Suppression rule** — an `instrument_id` ≠ `canonical_instrument_id` divergence on a defi POOL row is NOT a content
  finding.
- **Stops being an exception when** — the operator reverses Option A and authorises a mass re-key.

### AE-4 — `batch_massive` read-recognition, kept until the gated purge

- **What** — `batch_massive` remains a recognised `PipelineMode` and `possible_manifest` entry, and ~1.47M historical
  objects live under `pipeline_mode=batch_massive/`, even though Massive (formerly Polygon.io) was REMOVED as a tradfi
  SOURCE on 2026-07-19.
- **Why accepted** — recognition is DELIBERATELY KEPT so historical data stays readable until the gated GCS purge
  completes: `codex/02-data/tradfi-databento-sourcing-ssot.md:49-59` ("`batch_massive` `PipelineMode` +
  `possible_manifest` recognition are DELIBERATELY KEPT until the ~1.47M historical … purge"; the same passage notes the
  residual exposure is a re-consolidation/backfill that tries to RE-STAMP legacy rows).
- **Ruled by / when** — operator ruling 2026-07-19 (source removal), with recognition explicitly narrowed, not revoked.
- **Suppression rule** — `pipeline_mode=batch_massive` is NOT `non_canonical_path` and NOT delete-eligible on the
  strength of source-removal alone. **Removal is a separate, human-only, operator-gated purge** — the reconciliation
  never suggests it.
- **Stops being an exception when** — the gated purge completes; recognition is then removed and any surviving
  `batch_massive` object becomes a genuine finding.

### AE-5 — defi interim flat `LENDING` for market/event data_types

- **What** — the market/event lending data_types (`lending_indices`, `liquidation_events`, `flash_loan_events`,
  `position_data`) key to the market-level `LENDING` (EVM) / `SOLANA_LENDING` (Solana) `instrument_type`, NOT to the
  holdings-level `A_TOKEN`/`DEBT_TOKEN` split.
- **Why accepted** — the Wave-B flat-`LENDING`-retire OVER-REACHED and was **REVERSED** (`wn12e7itc`). Retiring it made
  `build_instrument_id(...LENDING...)` raise, which broke 5+ MTDS writers into `attempted_failed`/zero-data via their
  shard-level `except ValueError`, and the partial A_TOKEN work-around created a shard-atom desync (GCS
  `instrument_type=a_token` vs manifest `lending`). Sources: `codex/02-data/defi-canonical-naming-ssot.md:82` and
  `:117-118`; `plans/active/issues/canonical_closeout_open_questions_2026_07_18.md:158-171`.
- **Ruled by / when** — reversal is shipped in code; the FORWARD decision is PARKED for the operator (decision D, parked
  2026-07-19). Holdings are unaffected and stay `A_TOKEN`/`DEBT_TOKEN`.
- **Suppression rule** — never flag `lending` / `solana_lending` on a market/event lending data_type as non-canonical.
- **⚠ Codex contradiction to state, not resolve** — `cross-asset-canonical-target-ssot.md:182` still asserts "Legacy
  flat `LENDING` is **RETIRED**". That doc currently asserts a state the code DELIBERATELY does not implement. Until a
  correction banner lands there, a reconciliation citing either doc must cite BOTH.
- **Stops being an exception when** — operator rules decision D (see §5).

---

## 5. Axes the reconciliation MUST REFUSE to report on

Two axes are genuinely UNRULED. The reconciliation must emit a `REFUSED — awaiting operator ruling` line naming each,
must NOT emit a finding on either, and must NOT propose a migration on either. Refusing is the correct output; picking a
side silently is the failure mode this section exists to prevent. **Neither side below is adjudicated here.**

### 5.1 [C2a] Manifest `instrument_type` COLUMN casing — UPPER vs lowercase

- **Side A — lowercase.** `codex/02-data/cross-asset-canonical-target-ssot.md:210-212`, § "instrument_type case + venue
  spelling": "**case**: LOWERCASE in the GCS path segment + the manifest `instrument_type` column (writer grain);
  **UPPER** only in [the id]". Restated in the operator log at `:257` and in the defi plan.
- **Side B — UPPERCASE, catalogue is SSOT.** `plans/active/tradfi_consolidated_closeout_2026_07_18.md:375` — "UPPERCASE
  enum, CATALOGUE is the SSOT — `{FUTURE, OPTION, EQUITY, ETF, INDEX, COMBO, SPOT_PAIR}`" — with the converge-the-
  writers todo at `:384-387` and an executed migration reporting **3,300,155 UPPERCASE case re-stamps** at `:698` and
  `:761`.
- **Why it is undecidable from documents** — both sides cite the SAME operator on the SAME date (2026-07-18); the
  scripts that UPPERCASE the column have ALREADY SHIPPED on both cefi and tradfi. The issue register records this as a
  self-caught inconsistency in the freshly-shipped SSOT
  (`plans/active/issues/canonical_closeout_open_questions_2026_07_18.md:111-115`, which carries a REC toward UPPERCASE —
  a recommendation, **not a ruling**).
- **Stakes** — the direction determines >12M row rewrites.
- **Required behaviour** — do NOT report `instrument_type` column casing as a finding; do NOT propose a casing
  migration; keep the two DRAIN-GATED `--apply` runs frozen. The GCS path SEGMENT being lowercase and the id middle
  segment being UPPER are NOT in dispute and remain reportable.

### 5.2 [decision D] DeFi market/event lending data_type canonical keying

- **Side A — keep `LENDING` as a market-level `instrument_type`** (the current interim). Different grain from the
  holdings duplication the operator's ruling targeted; simplest; no re-key; historical rows unchanged. Carried as
  `[WORKER REC]` — "least-bad, reversible" (`canonical_closeout_open_questions_2026_07_18.md:175-177`).
- **Side B — key each to the reserve's `A_TOKEN`.** Uniform with "A_TOKEN/DEBT_TOKEN only", but coarse: loses the debt
  side for `liquidation_events`/`position_data`/`flash_loan_events`, and forces a historical re-key plus a manifest
  shard-atom migration (`:178-180`).
- **Side C — split per side** (supply-index/collateral → `A_TOKEN`; borrow-index/debt/flash-loan → `DEBT_TOKEN`). Most
  semantically precise, biggest change: row-shape change, doubling for indices, historical re-key (`:181-183`).
- **Consequence recorded in the register** — B or C re-activates the UTL consumer todo, a full migration of all 5+ MTDS
  writers (not the partial 3), a Wave-D historical re-key, and a shard-atom fix on both axes (`:185-`).
- **Required behaviour** — do NOT report the interim `LENDING` keying as a finding (this is AE-5's suppression), and do
  NOT propose any re-key. Report only that the axis is REFUSED pending decision D.

---

## 6. Report contract (what a typed finding must carry)

Every finding line in a reconciliation report carries, at minimum:

`type` (from §2, verbatim) · `severity` (§2 default, or an explicitly-justified override) · `asset_group` · `shard_atom`
· `surfaces_disagreeing` (which of S1–S4) · `detector` (script + flags that produced it) · `delete_eligible` (from §3) ·
`suppressed_by` (an AE-n from §4, when applicable).

Two consequences this contract is designed to produce, both currently missing:

1. **Diffability** — two runs over the same asset_group differ by a set-difference over typed findings, not by reading
   prose.
2. **A keyable delete feature** — the delete-suggestion pass filters on `delete_eligible == true`, and can therefore
   never be talked into a delete by narrative.

Any number a report prints must name its formula (see `honest-coverage-model.md` for the live, CK3-certified coverage
definition and for why every printed `coverage_pct` is a LOWER BOUND).
