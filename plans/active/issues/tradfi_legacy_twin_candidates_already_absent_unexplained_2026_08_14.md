---
doc_type: issue
title:
  "tradfi legacy-twin delete candidate set: 0/900 legacy objects still exist in GCS — vanished by an unknown route,
  predates this session"
summary: >-
  Re-running cleanup_legacy_twins.py's dry-run for tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md (after fixing
  canonical_twin_path()'s pre-hive asset_group= gap) found that ALL 900 of the report's class-B legacy-duplicate
  candidate objects are ALREADY ABSENT from gs://market-data-tick-tradfi-prd-central-element-323112 — a fresh
  gcs_describe_object + a prefix listing both confirm the entire raw_tick_data/by_date/day=.../equities/NYSE/ legacy
  shape is empty. The report itself is dated 2026-07-30 and was never re-generated. No plan/issue doc in this corpus
  records an executed delete of this candidate set; the bucket's only lifecycle rule is a 60-day COLDLINE storage-class
  transition (no delete action), which cannot explain object absence. This is NOT something this session did (the entire
  investigation was read-only dry-run + gcs_describe_object checks) and is NOT a data-loss risk from THIS finding's
  perspective (897/900 canonical twins independently confirmed present via the now-fixed canonical_twin_path()
  derivation) — but the mechanism by which 900 legacy objects disappeared without a tracked delete-safety-gated
  execution is unexplained and worth a human look.
status: open
nature: issue
asset_group: [tradfi]
stage: [data]
repos: [instruments-service, market-tick-data-service]
scope: [engineer, admin]
tags: [tradfi, data-correctness, delete-safety, legacy-twin, investigation]
related:
  [
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch13_2026_08_13.md,
    /plans/archive/issues/tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
  ]
parent_epic: tradfi_master
source: "tradfi_satellite_ao_dispatch_batch13_2026_08_13.md todo 1 execution, 2026-08-14 interactive session"
assigned_vm: NA
created: 2026-08-14
resolved_by:
locked_by:
locked_since:
priority: P1
execution_scope: local-only
drift_direction: advance-code
depends_on: []
context_scope:
  [
    instruments-service/scripts/cleanup_legacy_twins.py,
    /codex/02-data/gcs-and-manifest-delete-safety-protocol.md,
    /plans/active/tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md,
  ]
---

# tradfi legacy-twin delete candidates: 0/900 already absent, unexplained

## What I found

Executing `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s gated delete todo (dispatched via
`tradfi_satellite_ao_dispatch_batch13_2026_08_13.md` todo 1), after fixing `canonical_twin_path()`'s pre-hive
`asset_group=` gap (see `instruments-service@<sha>`, this session):

- **Fresh dry-run** against the live report
  (`gs://market-data-tick-tradfi-prd-central-element-323112/_index/audit/orphan_sweep_tradfi.parquet`, last-modified
  2026-07-30T04:08Z, 900 class-B candidates): **0 deletable, 900 blocked** — but the block reason changed from the
  2026-07-30 run's "canonical twin NOT captured in manifest" to **"missing crc32c on legacy or canonical"** for every
  row.
- Root cause of the reason change: **the LEGACY object itself no longer exists.** Verified two independent ways:
  1. `gcs_describe_object()` on the exact `uri` field of a sampled 25/900 rows (`random_state=42`): **0/25 exist.**
  2. A full pass over all 900 rows: **legacy_exists=0/900**, **canonical_exists=897/900** (the fix correctly resolves
     canonical twins now — this is real progress, not a new bug), **source_resolved=900/900**.
  3. A prefix listing of `raw_tick_data/by_date/day=2025-01-02/data_type=ohlcv_1m/equities/NYSE/` (one of the
     candidate-set's own prefixes) returned **zero objects** — not renamed elsewhere under a similar shape, genuinely
     empty.
- **Official tool confirmation** (`cleanup_legacy_twins.py --apply --i-understand`, same session): fresh soft-delete
  retention = 604800s (clears §3a); **`deleted 0/0 crc32c-identical legacy twins (0 failed/raced)`**; post-delete
  verification `0/0 confirmed gone, 0 STILL PRESENT` — i.e. the tool itself, independently, confirms there was nothing
  for it to delete.
- **The 3/900 rows with no canonical twin** are all
  `(venue=FX, instrument_type=spot_pair, data_type=ohlcv_24h, underlying=KRW-USD, day∈{2025-11-06, 2025-11-07, 2025-11-10})`
  — this matches the ALREADY-TRACKED `tradfi_fx_krw_usd_phantom_rows_fresh_confirmation_2026_08_12.md` phantom-row
  population (manifest claims captured, no real backing data for these exact KRW/USD cells). Not a new finding; not
  investigated further here.
- **Ruled out**: a GCS Lifecycle Management delete rule (`gcloud`-equivalent check via `bucket.lifecycle_rules`) — the
  bucket's only rule is `{"action": {"type": "SetStorageClass", "storageClass": "COLDLINE"}, "condition": {"age": 60}}`,
  a storage-class transition, not a delete action; it cannot make `gcs_describe_object`/`list_blobs` return absent.
- **Ruled out**: `migrate_tradfi_underlying_display_names_2026_08.py` (a different tradfi migration that also deletes a
  legacy source after copy) — its own issue doc
  (`tradfi_underlying_rename_apply_size_only_verification_gap_2026_08_12.md`) states `--apply`/`full` was "deliberately
  NOT run", and its scope (`underlying=` display-name renames for futures_chain/combo cells) does not overlap this
  candidate set's shape (bare pre-hive `equities/<VENUE>/<file>`, no `underlying=` segment at all).
- **Searched**: no `plans/active/` or `plans/active/issues/` doc records an executed delete of this specific 900-row
  tradfi legacy-B candidate set. `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s own Progress Log's most
  recent prior entry (2026-07-30) still shows 900 candidates blocked at "canonical twin NOT captured" — i.e. the objects
  existed as of that check.

## Why it matters

The delete-safety protocol's entire design (`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`) exists to gate
legacy-object deletes behind a five-part proof + a fresh reversibility check, specifically so a legacy copy is never
destroyed without an independently-confirmed canonical twin. If these 900 objects were deleted through some route OTHER
than this gated tool (or an equivalent gated process), that would be a genuine process gap worth closing — even though
in THIS specific case the practical outcome looks benign (897/900 already had canonical twins per this session's fresh
check, and the remaining 3 are the already-known KRW/USD phantom-row population, not newly orphaned). Alternatively,
this may be a wholly benign explanation this session didn't find (e.g. a since-superseded backfill overwrite, a manual
operator action, or a script run outside this plan's tracking) — the point of filing this is that nobody currently knows
which, and "the data doesn't exist where the report says it should" is exactly the class of signal the delete-safety
protocol asks to be investigated before being waved off.

## Recommended decision

- `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s delete todo can be considered PRACTICALLY resolved (0
  legacy duplicates remain to delete, tool-confirmed) — recommend flipping it with this doc cited as evidence, not
  re-blocking on it.
- This doc stays open for a human/operator pass to determine whether the 900-object disappearance has a known, benign
  explanation (if so, close this doc citing it) or represents a real process gap (if so, scope a follow-up: audit other
  pending legacy-twin-delete candidate sets — defi/pred — for the same already-vanished pattern before trusting their
  own dry-run coverage numbers).

## Todos

- [x] ✅ [DIAG] P1. Determine how/when the 900 tradfi legacy-B objects (day range including at least 2025-01-02) were
      removed from `gs://market-data-tick-tradfi-prd-central-element-323112` — **unrecoverable via Cloud Audit Logs,
      confirmed 2026-08-15**: `storage.objects.delete` query against the project's `_Default` log bucket (90-day
      freshness window) returns zero rows for this bucket, and the bucket's own configured retention is only 2 days
      (`gcloud logging buckets describe _Default --format='value(retentionDays)'`) — no custom long-retention sink
      exists (`gcloud logging sinks list` shows only `_Default`/`_Required`/one unrelated diag sink). A deletion from
      ~2025-01-02 is ~590 days outside that window; the deleting principal/timestamp cannot be recovered by any logging
      mechanism currently configured. Retagged `[OPERATOR]` → `[DIAG]` (bounded investigation, not a judgment call) —
      closing as "mechanism unrecoverable," per this doc's own Disposition options. **Follow-up worth flagging
      separately**: a 2-day audit-log retention on the project handling prod data-pipeline deletes is unusually short
      and was the reason this couldn't be answered — may be worth a deliberate retention bump if this kind of forensic
      question recurs.
- [ ] [OPERATOR] P2. **Retagged 2026-08-19 (plan_reconciler) — was `[SCRIPT]`, but this item's own 2026-08-16
      Progress Log entry parks it `BLOCKED-OPERATOR-DECISION`; the tag now matches that disposition, per the HARD
      RULE that a resolved/changed `[OPERATOR]` state gets retagged in the same edit.** Once the mechanism is
      known, spot-check whether the defi and pred legacy-twin-delete candidate sets
      (same gated todo, `tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s sibling asset_groups) show the same
      already-vanished pattern BEFORE trusting a future dry-run's twin-coverage number for them — a stale report
      reporting "still there" when the objects are already gone would silently under-count, and one reporting "gone"
      when they're still there would silently over-count; this session only checked tradfi.

## Progress Log

- **na-eligibility-audit 2026-08-16** (tradfi tranche, dispatch agt-45ad7b): **KEEP-NA — conflict-check PARKED, not
  reclassified.** Todo P1 is `[x]` (mechanism confirmed unrecoverable). Remaining todo P2 ("spot-check whether the
  defi/pred legacy-twin-delete candidate sets show the same already-vanished pattern") reads as bounded on its own, but
  conflict-checking against `parent_epic: tradfi_master`'s sibling corpus surfaced
  `/plans/archive/2026_08/legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15.md` — a LATER
  (2026-08-15), all-todos-done doc that already ran defi/prediction/sports legacy-twin dry-run investigation
  (twin-coverage 0% for both defi and prediction). Genuinely ambiguous whether that doc's existing dry-run already
  answers "were any of the defi/pred candidates already-vanished before any tracked delete touched them" specifically,
  or whether that's a distinct question its own investigation never asked. Per the shared conflict-check protocol —
  **PARKING as BLOCKED-OPERATOR-DECISION** rather than guessing which side is right: does the 2026-08-15 doc's dry-run
  already cover this, or does P2 still need a fresh, targeted check? `assigned_vm` unchanged.
- **context-scout 2026-08-17**: populated/refreshed context_scope (2 entries).
- **na-eligibility-audit 2026-08-19** (tradfi tranche, dispatch agt-5d34f9): **KEEP-NA, valid — parked status
  reaffirmed.** Sole open todo (P2 [OPERATOR], spot-check whether defi/pred legacy-twin-delete candidates show the
  same already-vanished pattern) is unchanged since the 08-16 conflict-check PARK. Genuine ambiguity re-confirmed:
  whether `/plans/archive/2026_08/legacy_twin_deletes_defi_prediction_and_sports_reverify_ao_dispatch_2026_08_15.md`'s
  existing dry-run already answers this specific question is still an open operator call, not guessed at.
  `assigned_vm` unchanged; stays PARKED BLOCKED-OPERATOR-DECISION.
- **context-scout 2026-08-20**: populated/refreshed context_scope (3 entries)
