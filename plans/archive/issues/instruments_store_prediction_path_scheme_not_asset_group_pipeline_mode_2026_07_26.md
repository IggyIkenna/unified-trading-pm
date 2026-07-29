---
doc_type: issue
title: >-
  instruments-store prediction bucket's object-path scheme genuinely lacks asset_group=/pipeline_mode= segments (CF-2/
  CF-3 RED) -- architect decision needed, not a mechanical copy like cefi/defi/tradfi got
summary: >-
  Live re-audit (2026-07-26, read-only, `cf_manifest_audit_2026_06_01.py` against all 4 non-sports instruments-store
  prod buckets) for `cross_cutting_satellite_ao_dispatch_batch1-012` found the dispatched todo's premise stale: cefi/
  defi/tradfi are ALL already CF-1/CF-2/CF-3/CF-6/CF-9/CF-13 GREEN (the C0 canonical-form path/partition single-walk
  already landed for those 3 AGs -- their object paths already carry
  `pipeline_mode=batch_instruments_service/asset_group={ag}/` segments). Prediction is the one non-sports AG where this
  did NOT happen: its objects use `instrument_availability/by_date/canonical_question_group={G}/day={D}/venue={V}/...`
  and a second, structurally different `market_lifecycle/by_canonical_group/day={D}/group={G}/...` shape -- neither
  carries an `asset_group=`/`pipeline_mode=` path segment. Unlike cefi/defi/tradfi (where `pipeline_mode` is a SINGLE
  constant value `batch_instruments_service` per bucket -- retrofitting it into the path is redundant-but-harmless
  uniformity), prediction's manifest rows carry FOUR distinct pipeline_mode values in the same bucket
  (`batch_polymarket_gamma_api`, `batch_polymarket_clob`, `batch_instruments_service`, `batch_kalshi`), so a mechanical
  copy-migration is not obviously the right fix -- it needs a design call on whether/how to fold the segment into
  prediction's TWO existing top-level path shapes without breaking the `canonical_question_group=`/`group=` partition
  keys those shapes already use for their own (valid) purposes.
status: resolved
nature: issue
asset_group: [prediction]
stage: [data]
repos: [instruments-service]
scope: [engineer]
tags: [data-correctness, canonicalisation, single-walk, manifest, prediction, architect-decision]
related:
  [
    /plans/active/instruments_store_cf_canonicalization_single_walk_2026_07_24.md,
    /plans/active/cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/02-data/pipeline-mode-partition.md,
  ]
created: 2026-07-26
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: design
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.3
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
source:
  [
    "found 2026-07-26 while executing cross_cutting_satellite_ao_dispatch_batch1-012 (instruments-store CF-1..CF-12
    single-walk) -- live re-audit reconciled the dispatched scope against the actual current bucket state before
    launching any VM/migration",
  ]
resolved_by: instrument_availability_hive_canonicalisation_2026_07_21.md
locked_by:
---

# instruments-store prediction bucket — CF-2/CF-3 path-scheme gap needs an architect call

> **🟢 RESOLVED — resolved_by `instrument_availability_hive_canonicalisation_2026_07_21.md`. Archived.**

## 1. What I found

Ran the read-only `cf_manifest_audit_2026_06_01.py` (no whole-corpus walk -- pulls the single `_index`
`availability_index.parquet` + a handful of shallow, non-recursive `gcloud storage ls` probes) against all 4 non-sports
instruments-store prod buckets on 2026-07-26:

| bucket (prd) | CF-1 schema_v9 | CF-2 rows | CF-3 col | CF-2 paths | CF-3 partition | CF-6  | CF-9  | CF-13 | CF-4 | CF-8 |
| ------------ | -------------- | --------- | -------- | ---------- | -------------- | ----- | ----- | ----- | ---- | ---- |
| cefi         | GREEN          | GREEN     | GREEN    | GREEN      | GREEN          | GREEN | GREEN | GREEN | RED  | RED  |
| defi         | GREEN          | GREEN     | GREEN    | GREEN      | GREEN          | GREEN | GREEN | GREEN | RED  | RED  |
| tradfi       | GREEN          | GREEN     | GREEN    | GREEN      | GREEN          | GREEN | GREEN | GREEN | RED  | RED  |
| pred         | GREEN          | GREEN     | GREEN    | **RED**    | **RED**        | GREEN | GREEN | GREEN | RED  | RED  |

(CF-4/CF-8 reds are a SEPARATE, active writer-bug finding tracked in its own issue doc -- not this one.)

cefi/defi/tradfi object samples all show the retrofitted path shape, e.g.:

```
gs://instruments-store-cefi-prd-.../instrument_availability/by_date/day=2019-03-30/pipeline_mode=batch_instruments_service/asset_group=cefi/venue=DERIBIT/instruments.parquet
```

Prediction's object samples show NEITHER segment, across BOTH of its top-level shapes:

```
gs://instruments-store-pred-prd-.../instrument_availability/by_date/canonical_question_group=AVAX_PRICE_RANGE_DAILY/day=2026-07-13/venue=POLYMARKET/instruments.parquet
gs://instruments-store-pred-prd-.../market_lifecycle/by_canonical_group/day=2025-03-14/group=BTC_PRICE_RANGE_DAILY/market_lifecycle.parquet
```

Row-level `pipeline_mode` IS populated correctly in the manifest for prediction (CF-3 col GREEN, 100% populated), with a
real 4-way split: `batch_polymarket_gamma_api` (11,322), `batch_polymarket_clob` (11,288), `batch_instruments_service`
(2,834), `batch_kalshi` (1,949). This is the key structural difference from cefi/defi/tradfi, where `pipeline_mode` is a
SINGLE constant value (`batch_instruments_service`) for every row in the bucket -- so retrofitting the segment there was
pure uniformity (harmless, no information gain). For prediction, the segment would carry real information (which
producer wrote which object) that the current path scheme doesn't expose at all.

## 2. Why it matters

The parent todo (`instruments_store_cf_canonicalization_single_walk_2026_07_24.md`, folded into
`cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md` todo -012) frames this as ONE bundled, mechanical,
VM-launched single-walk across "every non-sports instruments-store bucket" (`category=`→`asset_group=` +
`pipeline_mode=` partition + v9 re-version + env-split + canonical names + `available_at` preserve + phantom relabel).
That framing is now stale for 3 of the 4 AGs (already done, confirmed GREEN today) -- but for prediction it was never
actually a mechanical copy in the first place. Prediction has TWO existing top-level path shapes
(`instrument_availability/by_date/ canonical_question_group=.../day=.../venue=...` and
`market_lifecycle/by_canonical_group/day=.../group=...`), and both already use a meaningful partition key
(`canonical_question_group=`/`group=`) that a generic `asset_group=`/ `pipeline_mode=` retrofit would need to compose
with, not replace. Blindly inserting `pipeline_mode=batch_instruments_service/ asset_group=prediction/` ahead of the
existing segments (mirroring cefi/defi/tradfi's shape) is _possible_ but a real design decision belongs to whoever owns
the prediction pipeline (does anything read these paths positionally? would adding a segment need a reader-side bridge
like the cefi canonical-migration program used? do BOTH shapes need the same treatment, or does `market_lifecycle/` stay
exempt since it's lifecycle metadata, not availability data?) -- this is exactly the "figure out how X should look"
class of decision the workspace's plan-authoring rule reserves for a human/architect-track plan, not something an
AO-dispatched worker should decide and execute unilaterally in the same session it discovered the gap.

## 3. Recommended decision

Do NOT fold this into a blind copy-migration. Options, for the operator/architect to pick between:

- **A. Retrofit both prediction shapes** to add `pipeline_mode={pm}/asset_group=prediction/` ahead of the existing
  `canonical_question_group=`/`group=` segments (mirrors cefi/defi/tradfi's shape exactly), with a reader-side bridge
  during the mixed window -- full uniformity, real migration cost, benefit is mostly consistency + genuinely correct
  `pipeline_mode` disambiguation in the path (currently only in the manifest row, not the object key). the object key).
- **B. Leave prediction's path scheme as-is** (accept CF-2-paths/CF-3-partition as a documented, permanent exception for
  this AG -- update the codex `KEY FINDING` table + the CF audit script to SKIP those two checks for prediction
  specifically, the way CF-10/CF-14 already have a documented SKIP path) -- zero migration cost, but the audit stays
  permanently RED for this AG unless the script is taught the exception.
- **C. Partial**: retrofit only the `instrument_availability/` shape (the one that actually has per-row `pipeline_mode`
  variance worth exposing) and leave `market_lifecycle/` exempt (it's lifecycle metadata, arguably not "availability"
  data in the CF sense at all).

None of A/B/C should be executed by an AO worker without an explicit pick -- each has a different amount of downstream
reader-migration risk. Whichever is chosen, land it as its own scoped, human-track (`assigned_vm: NA`) plan (not
re-opened as part of -012, which is done for the 3 AGs that actually needed it).

## Todos

> **RE-AUDITED 2026-07-28 — this issue's premise is STALE; the design decision below was already ruled AND shipped.**
> Read-only investigation (`instruments-service` repo, `instruments_service/engine/orchestrator/writers.py`) found the
> operator's 2026-07-21 HARD RULE in `/plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md`
> already answers this exact A/B/C question — and it answers it as **Option A: retrofit BOTH prediction shapes** (not B
> or C), for ALL 4 non-sports asset_groups including prediction, not just cefi/defi/tradfi. That doc's todos 1-6 are
> already `[x]` ✅ SHIPPED (`instruments-service@a9be6ce9`): `_instrument_availability_sink_for()` and
> `_market_lifecycle_sink_for()` (`writers.py:156-207`) both now bake `pipeline_mode=`/`asset_group=prediction` into the
> sink PREFIX (not the partition dict, avoiding the alphabetical-sort trap) ahead of the caller's `venue=`/`group=`
> keys, for EVERY asset_group's writer, prediction included — the docstrings explicitly confirm this ("full canonical
> hive... operator HARD RULE R2, 2026-07-21", "only the missing `pipeline_mode=`/`asset_group=` keys are inserted, in
> canonical order, ahead of the caller's remaining `group=` partition key"). Reader-side bridges were shipped in the
> same commit (todo 6). This resolves the exact open questions this issue's § 2 raised ("does anything read these paths
> positionally" — yes, and it was already made layout-tolerant across the cutover; "does market_lifecycle stay exempt" —
> no, it got the same fix).
>
> **What this issue's own CF audit (2026-07-26) actually caught**: not an undecided design question, but the EXPECTED,
> already-labeled `migration_pending` gap between the (already-fixed) writer and the (not-yet-migrated) HISTORICAL
> objects — the sibling doc's own todo 7b sized this precisely: prediction has 22,637 `instrument_availability` + 12,582
> `market_lifecycle` = **35,219** legacy flat objects still needing copy-up to the full-hive tree. That doc's todos 7c
> (copy+verify, `[DATA]`, not operator-gated — reversible/additive) and 7d (purge, gated on a same-run
> `gcs_bucket_soft_delete_retention_seconds()` check per finding T, not a fresh operator ask) and 8 (register the
> cutover date) are the ALREADY-TRACKED, AO-dispatchable remainder — per the general theme ("full
> backfills/migrations... DO IT" + "no half-built... left lying around"), that migration should run to full completion
> exactly as already scoped there, not be re-litigated here as a fresh design question.
>
> **Disposition**: this issue is SUPERSEDED by
> `/plans/active/issues/instrument_availability_hive_canonicalisation_2026_07_21.md` for its design-choice content. No
> new `[OPERATOR]` decision is needed — retagging the todo below accordingly. This doc's `status`/archival is left to
> the normal plan-completion-and-archival discipline in a follow-up pass (not executed in this session, since
> `instrument_availability_hive_canonicalisation_2026_07_21.md` is outside this session's assigned-file list and
> archival requires touching both docs' cross-references).

- [x] ✅ [REVIEW] P2. **RESOLVED 2026-07-28 — superseded, not a live decision.** The A/B/C pick was already made (Option
      A) and shipped `instruments-service@a9be6ce9` per `instrument_availability_hive_canonicalisation_2026_07_21.md`
      (todos 1-6, all `[x]`). No retrofit/reader-bridge scoping remains to do here — that work is done. The only
      genuinely remaining work (historical migration of prediction's 35,219 legacy flat objects) is already tracked as
      that doc's todos 7c/7d/8; route any further dispatch there, not here.
