---
doc_type: issue
title: >-
  Candle canonical-path migration — operational history, part 1 of 2 (2026-07-21 to 2026-07-22): writer/reader lockstep
  landing, -test- gate proof, P0 census, P5 executor build + adversarial review, prep-risk items — extracted from
  candle_feature_canonical_path_divergence_2026_07_20.md
summary: >-
  Companion history doc (part 1 of 2) to /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md —
  the verbatim Progress Log narrative (2026-07-21 through 2026-07-22, up to the P6 drain) extracted for line-cap
  compliance (plans/active/task_template.md §3 finding J, plans/active/issues/*.md 1000-line hard cap — the combined
  narrative itself exceeded 1000 lines, hence the 2-part split). Covers: the coordinated writer+reader lockstep landing
  across unified-trading-library/market-data-processing-service/features-service/ unified-trading-api; the -test- gate
  proof (2 real regressions found+fixed); todo 6's comparator-staleness fixes; the P0 census (~10.9M candle objects,
  ORPHAN=0 across all 4 asset groups); the P5 migration executor build (adversarial review caught a CRITICAL split-brain
  sharding bug before any prod object was touched); and the prep-risk items (todos 12/14/17/18) shipped ahead of the
  P6→P7→P8 sequence. Continues in part 2 (candle_feature_canonical_path_divergence_history_part2_2026_07_25.md) for P6
  drain onward. Zero open todos of its own — the parent issue doc remains the single live source of truth for every
  still-open todo (2, 3, 7, 9, 13, 15, 16, 19).
status: resolved
nature: record
asset_group: [cefi, defi, tradfi, sports, prediction]
stage: [data]
repos: [market-data-processing-service, features-service, unified-trading-library, unified-api-contracts]
scope: [engineer, admin]
tags:
  [
    data-correctness,
    canonical,
    gcs-paths,
    manifest,
    candles,
    features,
    migration,
    mdps,
    volatility,
    history,
    progress-log,
  ]
related:
  [
    /plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md,
    /plans/archive/issues/candle_feature_canonical_path_divergence_history_part2_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: data
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by: >-
  plan-hygiene line-cap remediation 2026-07-25 (extraction is the resolution — this is a closed, historical Progress Log
  narrative preserved verbatim for context; the parent issue doc remains the live source of truth for any still-open
  todos)
source: >-
  Extracted 2026-07-25 from plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md (1453 lines, over
  the plans/active/issues/*.md 1000-line hard cap, scripts/plan-hygiene/check_line_caps.sh) per the established
  extract-to-archive-bound-history-child pattern (plans/active/issues/plan_line_cap_remediation_2026_07_23.md's FINAL
  RESOLUTION section); split into 2 parts because the combined extracted narrative (1088 lines) itself exceeded the cap.
  Verbatim Progress Log content in original document order; only the todo-11/12/13/14/15 and todo-16/19 checkbox lines
  were excised in place (relocated to the parent's consolidated `## Todos` section, to avoid double-counting in the
  todo-conservation check) — both removals are marked in place below.
---

# Candle canonical-path migration — operational history, part 1 of 2 (2026-07-21 to 2026-07-22)

> **🟢 RESOLVED 2026-07-25 — ACKED-INTO-CODE** — extraction is the resolution (closed, historical Progress Log
> narrative; the parent issue doc remains the live source of truth for any still-open todos); archived per the
> terminal-status backlog sweep.

> **Companion history doc, not the live plan (1 of 2).** This holds the first half of the verbatim Progress Log
> narrative extracted from `/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md` to bring that
> issue doc back under the 1000-line `plans/active/issues/` hard cap (`scripts/plan-hygiene/check_line_caps.sh`) — the
> combined narrative itself was too large for one companion doc, hence this 2-part split. Nothing below was rewritten;
> it remains the verbatim historical record, in original document order, except the todo-11/12/13/14/15 and todo-16/19
> checkbox lines, which were relocated to the parent's `## Todos` section (each removal is marked in place below with a
> pointer). Continues in part 2
> (`/plans/archive/issues/candle_feature_canonical_path_divergence_history_part2_2026_07_25.md`) starting at the P6
> drain. The parent issue doc remains the single live source of truth for the
> Findings/Corrected-Ruling/Decision/LOCKED-shape sections and for every still-open todo (2, 3, 7, 9, 13, 15, 16, 19).

## Progress Log

### 2026-07-21 — coordinated code foundation LANDED (P1 writer + P3 readers), QG-green all 4 repos

The coordinated, held-uncommitted foundation described in the "OPERATOR PRINCIPLE" section above landed dep-ordered.
Every repo was QG-green (fresh sentinel against current HEAD — this host has heavy concurrent agent QG activity, so the
sentinel needed a re-run per repo each time HEAD advanced underneath it) before shipping.

- **`unified-trading-library`** — `build_canonical_candle_path` / `candle_read_prefixes` + `pipeline_mode=` in the
  `processed_candles` registry template. Landed via `quickmerge --agent` (staging-first routing for this repo).
- **`market-data-processing-service@752eaff`** — writer single-derivation (`build_canonical_candle_object_path` /
  `derive_candle_object_path`: adds `instrument_type=` + SOURCE `data_type` + `pipeline_mode=`); manifest records the
  SOURCE key; empty-stem bundled-write fix (todo 8); codex `per-asset-group-bucket-layouts.md:166` amended to the LOCKED
  shape. **Also closed the ONE gap the prior session flagged** (`build_continuous_engine.py`'s per-contract candle
  reader): now dual-probes canonical (`pipeline_mode=batch_databento` default + `instrument_type=FUTURE`) + legacy
  prefixes via `candle_read_prefixes`; the stitched continuous-future OUTPUT is now built through the same
  single-derivation UTL seam (it was missing `pipeline_mode=` entirely). **Bonus find while in that file**:
  `_resolve_tradfi_bucket()` called `resolve_bucket_name(kind="market-data-tick-tradfi")` — not a registered kind — so
  `run_build_continuous` raised on every invocation; the continuous-futures pipeline had never successfully run. Fixed
  to use the same `get_service_config().get_output_bucket_for_asset_group()` seam every other MDPS writer uses (also
  makes it `-test-`-routable, matching the writer's existing test-isolation contract). Shipped via the closed dirty-deps
  carve-out (UAC had live uncommitted venue-registry + quarantine WIP, mtime <120s, blocking quickmerge's pre-flight).
- **`features-service@99d5554e`** — `delta_one` + `volatility` readers dual-read via `candle_read_prefixes` (todo 5);
  `dependency_checker` drops `delimiter="/"` to walk the candle subtree; `continuous_future` slice confirmed intact. P2
  volatility sink-prefix fix (todo 4) landed in the same commit. Shipped via the same dirty-deps carve-out
  (`calendar_orchestrator.py`, a separate peer's live WIP in the same repo, was deliberately excluded from staging).
- **`unified-trading-api@8377c98`** — `batch_candles` chart/UI reader dual-reads via the same `candle_read_prefixes`
  SSOT. Shipped via the dirty-deps carve-out.
- **`deployment-service`** — coverage probe confirmed transparent to the `instrument_type=` insert (no code change
  needed, per the earlier scoping). While QG-ing this batch, found + attempted to fix an UNRELATED pre-existing parity
  gap (`configs/cloud-providers.yaml` missing the `alerting-service` bucket kind UAC's packaged copy already had —
  `test_sibling_copy_matches_packaged_uac_copy[deployment-service]` was failing on it) — a concurrent agent fixed the
  identical gap upstream in the interim, so this repo needed no commit from this session (verified via a clean
  `git diff HEAD` after reconciling the pull).

**Verification note (this host):** `bash scripts/quality-gates.sh --no-fix`'s SHA sentinel is invalidated the moment
`origin/live-defi-rollout` advances underneath it (the per-slot cron fast-forward-pulls every ~5 min, and this session
observed multiple OTHER concurrent `quality-gates.sh` processes for other repos/slots on the same host) — every
`quickmerge`/carve-out commit in this batch needed a **fresh** `quality-gates.sh --no-fix` run immediately before
staging, not the run from a few minutes earlier. Budget for this when landing a multi-repo batch on a busy host.

**NEXT (per the RESUME ORDER in `data_pipeline_check_mdps_features_2026_07_20.md`):** rebuild tarballs
(`refresh_code_tarballs.sh`) → verify the canonical shape on `-test-` via `/data-pipeline-check-mdps` (force+skip+
canonical, both axes) — THE GATE before any prod-data executor → then build the P5 migration+purge executor (todos 2/3/9
— census, tradfi-id quarantine, split-brain dedup) → P0 census + P6 drain/snapshot + P7 per-AG SPOT backward apply + P8
verify/reconcile.

### 2026-07-21 — ✅ THE GATE PASSED: writer proven emitting the LOCKED canonical shape on a real -test- VM (2 real bugs found + fixed along the way)

Ran `/data-pipeline-check-mdps` (force+skip+canonical) against CEFI:DERIBIT:trades on the rebuilt tarball
(`mdps@752eaff`). **First attempt failed with a real regression** (not the expected canonical-leg staleness): every
force-leg write errored `Multi-source manifest write missing required source= kwarg` (VM exit 1, 0 objects). Root cause
— `_resolve_candle_source_from_pipeline_mode`'s `has_source_priority`/`get_source_priority` lookup was keyed on the
AGGREGATED `mdps_data_type_key` (a computed key almost never registered in `SOURCE_PRIORITY`), but `record_captured`'s
own multi-source guard now evaluates `row_key["data_type"]` — the SOURCE type — since the coordinated manifest change.
cefi/trades has 6 registered `SOURCE_PRIORITY` sources (tardis first), so the writer's own guard rejected the write its
own source-resolver had just silently returned `None` for. **Fixed + shipped `mdps@2d720b4`** (dirty-deps carve-out):
re-keyed the lookup on `source_data_type`; moved the resolver to the shared `canonical_writer_shaping.py` and wired the
SAME fix into the streaming write path, which had NEVER passed `source=` at all (a pre-existing, independent gap the
SOURCE-key change made much more likely to bite). Verified directly:
`resolve_candle_source_from_pipeline_mode(CEFI, "trades", BATCH_TARDIS)` now returns `"tardis"` (was `None`).

**Re-ran on the re-rebuilt tarball — THE GATE PASSED.** 29/60 instrument×timeframe cells succeeded (217,679 candles
written); ground-truthed an actual object directly on GCS:

```
gs://market-data-tick-cefi-test-central-element-323112/processed_candles/by_date/day=2026-06-27/
  pipeline_mode=batch_tardis/timeframe=15m/data_type=trades/instrument_type=PERPETUAL/venue=DERIBIT/
  DERIBIT:PERPETUAL:BTC-USD@INV.parquet
```

— exactly the LOCKED shape (`instrument_type=` present, SOURCE `data_type=trades`, `pipeline_mode=` present). Read the
per-VM manifest shard directly via pyarrow for the same shard:
`data_type=trades, instrument_type=PERPETUAL, pipeline_mode=batch_tardis, capture_status=captured, row_count=96, source=tardis`
— **path==manifest holds exactly**, and `source=` resolved correctly (proves the fix). The remaining 31/60 failures are
a SEPARATE, PRE-EXISTING gap (`cefi/trades/FUTURE: ALL FAILED (31/31)` — CEFI has no registered candle SchemaContract
for standalone `instrument_type =future`, unrelated to path/manifest shape) — filed
`issues/cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md`, not blocking this gate. The `canonical`
leg still correctly reports `content_check=non_canonical` (todo 6, re-point the skill's declared-template comparator,
still pending — expected, not a failure of the writer).

**Gate verdict: the writer + manifest are proven correct on real infra. Proceeding to the P5 executor.**

### 2026-07-21 — P5 executor build dispatched (workflow); raw-tick fleet CHECKED — P6/P7 must wait for it

Dispatched a workflow (build agent + 3 parallel adversarial-review lenses — data-loss safety, dedup/shape correctness,
operational safety — + a conditional fix pass) to write
`market-data-processing-service/scripts/ migrate_candle_canonical_2026_07.py`, cloning
`market-tick-data-service/.../migrate_tradfi_canonical_2026_07.py`'s proven safety structure (dry-run default,
mapping-manifest + 0-orphan reconcile before any write, copy→verify→delete with the target==source no-delete guard,
per-object try/except isolation, sharding) while explicitly NOT cloning its `source→aggregated data_type` transform —
the candle migration's `data_type` axis is UNCHANGED (already SOURCE on existing objects, per the -test- gate proof
above); only `instrument_type=`/`pipeline_mode=` are added + the 3 genuine defects (empty-stem, TradFi leaf-id,
split-brain) repaired. Not yet reviewed/shipped — awaiting the workflow.

**Checked the running raw-tick fleet before considering P6/P7 timing**:
`gcloud compute instances list --filter="name~'canonical-migration-cefi'"` → **11 RUNNING / 7 TERMINATED (18 total)**,
so the fleet is well underway but NOT complete. Per the coordination note already in the master catalogue row (sequence
P7 AROUND the raw-tick fleet's completion, disjoint prefix but shared manifest-shard write contention): **P0 census / P6
drain / P7 apply are correctly BLOCKED-pending on this external fleet finishing, not something to force through now.**
This is a "cannot be done yet" deferral (elapsed time / external event), not a gap — re-check fleet status before
starting P6.

### 2026-07-21 — ✅ P5 executor SHIPPED (`mdps@6ce1a25`) — the adversarial workflow caught a real critical bug before it ever touched prod

`market-data-processing-service/scripts/migrate_candle_canonical_2026_07.py` (951 lines) + a 23-test unit suite, cloning
`migrate_tradfi_canonical_2026_07.py`'s proven safety structure (dry-run default, mapping-manifest + 0-orphan reconcile
before any write, copy→verify→delete with the target==source no-delete guard, per-object try/except isolation, sharding)
while deliberately NOT reusing its `data_type` transform (candles keep SOURCE `data_type` unchanged — see the LOCKED
shape above). 8 disposition classes + the ORPHAN loud-failure bucket; genuine defects (empty-stem, TradFi leaf-id,
split-brain dedup) repaired in the same pass per todos 2/3/9.

**Built + reviewed via a workflow (build agent + 3 parallel adversarial lenses — data-loss safety, dedup/shape
correctness, operational safety — + a conditional fix pass), and it earned its keep**: all 3 lenses INDEPENDENTLY
converged on the same **CRITICAL** finding — `PipelineModeSiblingIndex`/`ProvisionalTargetIndex` (the split-brain dedup
indices) were built PER-SHARD using the same `--shard-of`/`--shard-index` filter as the classify/apply pass, but
`_stable_shard()` hashes each object's raw enumeration LINE TEXT, and a split-brain pair's two lines differ (one carries
an extra `pipeline_mode=X/` segment) — so under the script's own documented `--shard-of N` prod usage, a split-brain
pair lands in DIFFERENT shards with overwhelming probability. The sibling backfill would silently never fire, the
pm-less twin would fall back to the blind `BATCH_DATABENTO` default, and BOTH objects would migrate to DISTINCT,
one-mislabeled canonical paths — permanently duplicating the shard with corrupted provenance metadata, with the
reconcile's 0-orphan check never catching it (both twins individually resolve to a valid disposition). This is exactly
the class of silent-corruption-at-scale bug the adversarial-review step exists to catch before a real `--apply` run.

**Fixed in the same pass**: `build_pipeline_mode_sibling_index()` / `build_target_index()` no longer accept shard
parameters at all (the footgun removed at the signature level, not just one call site) — they always scan the full
unsharded enumeration; only the classify/apply passes stay sharded. 4 new regression tests added, including one that
hand-reconstructs the OLD buggy call pattern and asserts it DOES reproduce the bug (documents exactly what the fix
prevents). I additionally fixed 2 issues surfaced but not auto-fixed (medium/low severity, so outside the workflow's
auto-fix threshold): the crc32c verification was OPPORTUNISTIC (`if smeta.crc32c and dmeta.crc32c and ...`) rather than
REQUIRED, so a missing crc32c on either side would silently downgrade to a weaker size-only match — tightened to require
crc32c on both sides, never falling through to size-only; and a genuine `str | None` type-safety gap in the
content-repair path (now explicitly narrowed, never assumed). basedpyright: 0 errors. QG: ALL PASSED.

**Remaining findings NOT fixed (medium/low, tracked as follow-up, not blocking)**:

> _Todos 11, 12, 13, 14, and 15 (originally listed here) were relocated verbatim to the parent's `## Todos` section —
> see `/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`._

**NEXT: P0 census** (Tier-2 spot VM, per the workspace's own census-and-compute-tiers rule — a full ~10-20M-object
enumeration + classification run must happen on sanctioned infra, never in-session) — **blocked on the raw-tick fleet
finishing** (checked above, 11/18 still running).

### 2026-07-22 — ✅ Todo 6 SHIPPED: the check scripts' OWN comparators were still asserting the pre-migration/superseded shape (2 real bugs beyond the known one, proven fixed on real `-test-` infra)

Re-checked the raw-tick fleet before picking up todo 6: down to **1/8 CEFI VMs RUNNING** (`wp21`, actively writing —
confirmed via serial-port gsutil activity every ~60s, not stalled); AWS side fully drained. Not yet fully drained, so P0
census stays blocked; picked up todo 6 as the highest-value unblocked item per the prior session's own recommendation.

**Traced the comparator code** (`market-data-processing-service/scripts/pipeline_e2e_check.py`) rather than assuming the
fix was purely doc-cosmetic, and found it was NOT — offline-probed the exact ground-truthed `-test-` object path from
the 2026-07-21 gate (`.../timeframe=15m/data_type=trades/instrument_type=PERPETUAL/venue=DERIBIT/…parquet`) directly
against `_measured_violations`/`_declared_violations` and confirmed **two real, currently-live bugs**, not one:

1. **Force leg (§3A MEASURED template) would have FALSE-FAILED every genuinely-migrated write.**
   `_MEASURED_CANDLE_SEGMENT_ORDER` didn't include `instrument_type` at all, so `_measured_violations` reported
   `unexpected_segments=instrument_type` on the exact object the writer now correctly produces — the object would land
   in `off_template`, never `matched`, meaning `write_verified=False` and the force leg's own pass predicate would fail
   on real, correct data. (§3A's docstring said "there is NO instrument_type= segment anywhere" — true on 2026-07-20
   when it was measured, stale since `mdps@752eaff`/`2d720b4` landed the writer fix.)
2. **Canonical leg (§3B DECLARED template) — the known one — plus its manifest lookups were ALSO broken.**
   `_declared_violations` compared `data_type` against the AGGREGATED `mdps_data_type_key()` instead of the shard's
   SOURCE data_type, so it reported `data_type=trades!=ohlcv_15m` on the exact LOCKED-shape object (a false
   `non_canonical`). `_manifest_match` and `_canonical_leg_ids` had the SAME bug on the manifest-row filter — since the
   manifest `data_type` column is now overridden to SOURCE right before `record_captured` (operator ruling 2026-07-21),
   filtering on the aggregated key silently matched **zero rows**, making the id-canonicality check vacuous rather than
   a real assertion.

**Fixed both, offline-verified the fix** (same ground-truthed object + a synthetic legacy/pre-migration sibling without
`instrument_type=`): the LOCKED object now passes `_measured_violations`/`_declared_violations` with zero violations;
the legacy object still passes `_measured_violations` (force leg stays green on either shape, by design) but
`_declared_violations` correctly reports exactly `missing_segment=instrument_type` — the P7 migration-worklist signal,
and nothing else (no more false `data_type` mismatch riding along). Added 6 regression tests (MDPS) covering both the
LOCKED-pass and legacy-still-flagged cases.

**Found the same root-cause bug a third time, in a third file, while checking `/data-pipeline-check-features`** (todo 6
named it too): `features-service/scripts/pipeline_e2e_check.py`'s `_is_canonical_input_row` required a candle INPUT
row's `data_type` to start with an aggregated prefix (`ohlcv_`/`book5_`/`deriv_`) to count as canonical — same
superseded assumption, would have flagged every genuinely-canonical candle input row (feeding
delta_one/multi_timeframe/cross_instrument) non-canonical. Dropped the `data_type` axis from that check entirely (the
manifest `data_type` is now SOURCE, permanently, not a migration-transient signal); `timeframe` presence + normalisation
remains the real signal. 3 new regression tests.

**Shipped**: `mdps@25ce29c37` via quickmerge (QG green, 67s, incl. a driver smoke re-import); `features@d58b7760` via
the closed **dirty-deps carve-out** (`unified-api-contracts` had live peer WIP, mtime <120s — protected, not touched; QG
green, 237s fresh sentinel immediately pre-commit). Also updated
`cursor-configs/skills/data-pipeline-check-mdps/SKILL.md`'s documented canonical contract to match (still needs its own
commit — see below).

**Proven on real `-test-` infra, not just offline** — ran `/data-pipeline-check-mdps` force+canonical for
`CEFI:DERIBIT:trades` day=2026-06-27 (same shard as the 2026-07-21 gate):
`plans/audit/results/data_pipeline_e2e_check_mdps_2026_06_27.md`. The force leg's own VM run itself hit a **known,
separately-tracked, unrelated** gap (`cefi_future_instrument_type_no_candle_schema_contract_2026_07_21.md` —
`cefi/trades/FUTURE: ALL FAILED (31/31)` in that shard's sub-dimension breakdown, dragging the overall VM exit code
to 1) — but the VM's own `run.log` shows it genuinely wrote **29/60 succeeded, 217,679 candles** (matching the
2026-07-21 gate's numbers exactly) before that unrelated failure. Critically, the **canonical leg does not depend on the
VM's exit code** (only needs a VM name to scan real `-test-` objects + the per-VM manifest shard), so it directly
exercised the fixed code on real data regardless:

- **7/7 canonical-leg cells PASSED** (`content_check=canonical`), migration worklist **EMPTY** — before the fix, every
  one of these would have shown `data_type=trades!=ohlcv_15m`.
- **6/7 cells' internal `_scan_cell` classification showed `on_measured_template=29, off_template=0`** — i.e.
  `_measured_violations` (the SAME function the force leg's pass predicate uses) found ZERO violations on 29 real,
  `instrument_type`-bearing objects — direct real-infra proof the force-leg fix (item 1 above) is correct too, not just
  offline-probed.
- **29/29 instrument ids checked, 29/29 canonical**, read via `checked per_vm_shard` — direct proof
  `_canonical_leg_ids`'s manifest-frame mask now correctly finds real rows filtered on SOURCE `data_type` (was silently
  vacuous before the fix).

**One minor observed nuance, NOT caused by this fix, not blocking, tracked as todo 16 below**: the `24h` timeframe cell
alone showed `on_measured_template=0, off_template=29` (all 29 objects landed off-template in the MEASURED
classification) while the canonical leg still correctly passed it. Not touched by today's data_type/instrument_type fix
— orthogonal to it — plausibly the object path already normalises `24h`→`1d` (contradicting §3A's own "timeframe is the
RAW token" documentation, which may itself now be stale the same way the data_type docs were). Didn't chase it further
this session; doesn't affect correctness (canonical leg's own `tf_canon` comparison already absorbs it).

> _Todos 16 and 19 (originally listed here) were relocated verbatim to the parent's `## Todos` section — see
> `/plans/active/issues/candle_feature_canonical_path_divergence_2026_07_20.md`._

### 2026-07-22 — ✅ P0 census COMPLETE, all 4 asset_groups, real GCS enumeration — ~10.9M total objects, ORPHAN=0 everywhere

Operator explicitly approved starting the **read-only** P0 census in parallel with the still-running raw-tick fleet
("start the read-only P0 census now in parallel, and hold P6/P7/P8 until wp21 finishes") — census is enumeration +
classification only (no writes/deletes to any AG data bucket), genuinely disjoint from the fleet's write path.

**Launcher wiring** (todo, new): `migrate_candle_canonical_2026_07.py` had no VM-launcher dispatch branch (todo 11's
gap). Built 4 new categories (`{cefi,defi,tradfi,prediction}-candle-census`) in
`deployment-service/scripts/vm/launch-canonical-migration-vm.sh` via a workflow (build agent + 3 parallel adversarial
lenses: no-mutation-safety / service-staging-correctness / bucket-scope-and-registry). The adversarial pass caught 2
real bugs before any VM ever launched: a **CRITICAL** wrong-bucket-name bug (`prediction-candle-census` targeted the
nonexistent `market-data-tick-prediction-*` bucket — real abbreviation is `pred` — would have silently produced zero
census output on every invocation), and a **HIGH** shell-injection path via the unquoted `WORKERS`/`TRADFI_TICK_BUCKET`
env vars in the VM-side `bash -c` execution (**pre-existing in this launcher file, affects every category, not just the
new ones** — closed globally with a positive-integer / bucket-name-shape validation gate). Verified via `bash -n` + a
`DRY_RUN=true` preview of the actual generated command string for both a normal and the previously-broken category.
Shipped `deployment-service@865d0f9`, QG green (97s).

**Launched all 4 as parallel SPOT VMs** (`cefi-candle-census`/`defi-candle-census`/`tradfi-candle-census`/
`prediction-candle-census`, each `--dry-run`-only against `gs://<AG tick bucket>/processed_candles/**`, `2020-01-01`/
`2026-07-22` cosmetic labels). Rebuilt VM-deployment code tarballs first (`refresh_code_tarballs.sh`) since the MDPS
tarball predated today's launcher work — confirmed via `git merge-base --is-ancestor` that the pre-refresh "stale"
tarball SHA already contained everything the census script needs (`6ce1a25`/`752eaff`/`2d720b4`), so the already-running
`defi` VM (launched before the refresh) was left alone rather than killed/relaunched. All 4 VMs completed in 4-25
minutes (`VM_SHUTDOWN_ON_COMPLETION=true`, self-deleted after finishing — **do not expect to find them in
`gcloud compute instances list`**, their evidence lives in GCS logs/staged output only), `exit_code=0` on every one.

**Full results** (source: each VM's `run.log` at
`gs://deployment-scripts-central-element-323112/vm-logs/canonical-migration-{cat}-candle-census-<ts>/run.log`; mapping
TSV + reconcile report staged to
`gs://deployment-scripts-central-element-323112/canonical-migration-candle-census/<ts>/canonical-migration-{cat}-candle-census-<ts>/mappings/`):

| Asset group    |  Total objects |   MIGRATE |   SPLIT_BRAIN_DUPLICATE | QUARANTINE_CORRUPT | EMPTY_STEM (with/without underlying) | NEEDS_CONTENT_INSTRUMENT_TYPE | NEEDS_CONTENT_TRADFI_ID | CANONICAL_NOOP | ORPHAN |
| -------------- | -------------: | --------: | ----------------------: | -----------------: | -----------------------------------: | ----------------------------: | ----------------------: | -------------: | -----: |
| **defi**       |      1,124,849 | 1,123,407 | 0 (folded into MIGRATE) |              1,442 |                                0 / 0 |                             0 |                       0 |              0 |  **0** |
| **prediction** |      1,165,459 |         1 |               1,165,458 |                  0 |                                0 / 0 |                             0 |                       0 |              0 |  **0** |
| **cefi**       |        940,606 |        10 |                 804,670 |            130,906 |                        2,576 / 2,198 |                           238 |                       0 |              8 |  **0** |
| **tradfi**     |      7,646,831 |         0 |                 724,214 |                  0 |                      428,792 / 6,780 |                             0 |               6,487,045 |              0 |  **0** |
| **TOTAL**      | **10,877,745** |         — |                       — |                  — |                                    — |                             — |                       — |              — |  **0** |

(`defi`'s disposition histogram reported `MIGRATE`/no separate split-brain line — its split-brain count folds into the
1,123,407 MIGRATE figure per the script's own histogram, unlike the other 3 AGs which break it out; the executor's own
"MIGRATE (incl. split-brain)" summary line confirms this convention.)

**Reading the numbers** — every AG's `ORPHAN count = 0 (PASS — total map)`, the executor's own hard safety invariant
(every enumerated object gets exactly one disposition or the run aborts loudly): this is the single most important line
in each report, and it held cleanly across ~10.9M real objects. Beyond that:

- **prediction is ~100% split-brain** (1,165,458/1,165,459) — virtually the entire prediction candle corpus exists as
  duplicate pipeline_mode-partitioned + pipeline_mode-less pairs. Dedup is effectively the WHOLE prediction migration.
- **tradfi is dominated by content-repair** (6,487,045/7,646,831 = 84.8% `NEEDS_CONTENT_TRADFI_ID`) — confirms the
  LOCKED plan's own sequencing rationale ("tradfi LAST — ~99% id-canonicalisation"); P7 for tradfi will spend the vast
  majority of its time doing parquet content reads + `_renormalize_legacy_instrument_ids`, not path-only rewrites.
- **cefi's 13.9% QUARANTINE_CORRUPT rate is anomalously high** vs defi's 0.13% — filed as new todo 18, worth sampling
  before quarantining 130,906 objects at scale in case it's a fixable systematic bug rather than true garbage.
- **A genuinely new finding, not previously known**: cefi's `run.log` surfaced live WARNINGs for an **unregistered
  `pipeline_mode=batch_hyperliquid_rest`** value, silently defaulting to `BATCH_DATABENTO` in `canonical_writer.py` —
  filed as new todo 17, should be resolved before P7 backfills those objects' siblings with the wrong mode.
- **defi and cefi both show `CANONICAL_NOOP` near-zero (0 and 8)** — confirms the corpus really is "born non-canonical"
  as the original issue framed it; essentially nothing was already on the LOCKED shape before this migration.

**Raw-tick fleet ALSO fully drained during this work** (checked 2026-07-22, after the census): `wp21` (the last VM, 1/8
running as of the previous check) is gone entirely from `gcloud compute instances list` — self-deleted after completion,
same as the census VMs. **This means the fleet-drain condition that was blocking P6/P7/P8 is now satisfied** — but per
the operator's explicit instruction this session ("hold P6/P7/P8 until wp21 finishes"), P6 (drain/snapshot) and P7 (the
actual destructive backward-migration `--apply`) are NOT started without a fresh operator go-ahead, since P7 is
genuinely destructive (copy→verify→**delete** across ~10.9M objects) and deserves its own explicit authorization
checkpoint even though the technical blocker has lifted.

### 2026-07-22 — ✅ Prep work COMPLETE: todos 12/14/17/18 all shipped — operator authorized P6→P7→P8 pending this prep

Operator gave explicit go-ahead this session for the full P6→P7→P8 sequence, conditioned on resolving the prep risk
items first ("resolve prep risks first, then P6→P7→P8"). All three (four, counting todo 14 as a free side effect of
todo 18) are now shipped, real-infra-test-proven where applicable, and QG-green.

**Todo 12 (resume checkpoint)** — built via a workflow (build agent + 3 parallel adversarial lenses: data-loss safety,
resume correctness, operational safety) before touching production. The review caught real, concrete bugs, not style
nits: (1) HIGH/CRITICAL (found independently by 2 lenses) — the checkpoint frontier advanced past `ERROR:*`/KEPT_SRC
outcomes exactly like a real success, so a transient GCS failure or crc32c mismatch would be checkpointed as "done" and
silently, permanently skipped on every future resumed/re-run invocation — a genuine regression versus the pre-diff
behavior (a plain re-run always retried a straggler from line 0). (2) HIGH — `enumeration_signature` fingerprinted the
local enum file via `(size, mtime_ns)`; a real SPOT preemption relaunches on a FRESH VM that re-stages the same file
with a NEW mtime, so the signature would mismatch and the shard would replay from line 0 on every single preemption —
the checkpoint would work in every synthetic test but never actually help in the one scenario it exists for. (3) MEDIUM
— `ThreadPoolExecutor.map()`'s submission-order result consumption meant the checkpoint's advertised "~500 objects at
risk" cadence bound didn't actually hold under a stalled object. (4) HIGH (operational-safety lens, cross-repo) — the
checkpoint is keyed by `VM_NAME`, but the actual production launcher
(`deployment-service/scripts/vm/launch-canonical-migration-vm.sh`) regenerates a fresh `RUN_TS`-derived name on every
invocation and never calls `lc_write_launch_params`, so a real preemption relaunch (automatic OR manual) could never
find the checkpoint the preempted VM wrote — the whole mechanism would be dead weight for the one launcher family that
matters. All 4 fixed with regression tests (mirroring `launch-mdps-backfill-vm.sh`'s proven `VM_NAME_OVERRIDE` +
launch-param-persistence pattern for finding 4). Shipped `mdps@efa559a` + `deployment-service@0ed7cf5` (both via the
closed dirty-deps carve-out — `unified-api-contracts` had live peer WIP both times), fresh QG green on both repos.

**Todos 14/17/18 (classifier fixes)** — the follow-on workflow to BUILD these fixes hit the account's weekly
agent-dispatch limit (all 3 subagents errored immediately, zero work done, `resets Jul 24 8pm London`) after the
read-only investigation phase had already completed successfully with strong, evidenced findings. Rather than wait ~2
days, did the implementation directly (no subagents) using the same investigation evidence:

- **Todo 17**: confirmed `batch_hyperliquid_rest` is a duplicate/legacy alias of `batch_hyperliquid`, NOT a genuine new
  pipeline_mode (would have resurrected the R4-retired glued-transport antipattern if registered in UAC). Root cause: a
  prior migration (`migrate_hyperliquid_rest_pipeline_mode_2026_06_17.py`) fixed `raw_tick_data/` but was never scoped
  to `processed_candles/`, stranding 31,640 real CEFI HYPERLIQUID candle objects. Fixed
  `resolve_pipeline_mode_from_source` with an explicit legacy-alias table — sufficient on its own (no separate GCS
  rename migration needed) since P7 `--apply` will re-classify + migrate these objects normally anyway.
- **Todos 14 + 18**: confirmed the CEFI `QUARANTINE_CORRUPT` over-classification (128,218 of 130,906, 97.9%) was a
  simple wiring gap — `_renormalize_wire_cefi` already existed, was already imported, was simply never called for CEFI's
  classify branch (only TRADFI was wired). New `NEEDS_CONTENT_CEFI_WIRE_ID` disposition closes it. Separately found +
  fixed a genuinely NEW class (2,688 KRAKEN-SPOT objects, not previously tracked): a literal `/` embedded in the pair
  symbol (e.g. `ADA/USD`) broke Hive-path parsing outright — `_parse_candle_rel` now narrowly rejoins this one confirmed
  shape.
- Both real-object shapes were ground-truthed directly against the P0 census's staged CEFI mapping TSV
  (`gs:// deployment-scripts-central-element-323112/canonical-migration-candle-census/20260722-031920/.../candle_census_ mapping.tsv`)
  before writing any code, and proven via regression tests using those exact shapes. Hit + fixed one self-inflicted lint
  failure along the way (`_resolve_path_only` cyclomatic complexity 16>15 from the added CEFI branch — resolved by
  factoring the TRADFI/CEFI dispatch into a small `_LEAF_STEM_CONTENT_REPAIR_KIND` mapping). Shipped together as
  `mdps@6b9ee49` (dirty-deps carve-out again), fresh QG **fully green** (a concurrent peer fixed the pre-existing
  unrelated `seed_mock_data.py` baseline overage mid-session, so unlike the todo-12 ship this one hit zero pre-existing
  noise).

**Also recovered dangling evidence**: this issue doc's own todo-6 Progress Log entry (2026-07-22, earlier this session)
cited `plans/audit/results/data_pipeline_e2e_check_mdps_2026_06_27.md` as evidence, but that file was never actually
committed — found uncommitted in the working tree during this session's routine `git pull` (autostash-pop surfaced it).
Committed alongside this doc update so the citation isn't dangling for a fresh clone.

**Residual, explicitly non-blocking**: the true post-fix CEFI QUARANTINE_CORRUPT count is unmeasured (a fresh dry-run
census re-run would confirm it quantitatively, but P7's own `--apply` re-derives classification fresh per object rather
than trusting a stale plan, so this doesn't gate starting P7 — just don't assume the residual count is exactly
`130,906 - 128,218 - 2,688`).
