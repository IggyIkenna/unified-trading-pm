---
doc_type: issue
title:
  "CEFI manifest instrument_type=COMBO rows vanished (662 -> 0) — likely rebuild-overwrite of a manifest-only relabel"
summary: >
  DERIBIT partition-move dry-run (deribit_combo_perpetual_partition_move-003, market-tick-data-service@04d48b3c) found
  the CEFI manifest's instrument_type=COMBO row count dropped from 662 (2026-07-21 baseline) to 0 sometime in the last
  ~13 days, while at least one underlying GCS object is still physically present at its old wrong-partition path with
  wrong instrument_id content and ZERO manifest registration. Leading hypothesis (unconfirmed): rebuild_cefi_manifest.py
  derives instrument_type from the GCS PATH via regex, so a manifest-only COMBO relabel that never physically moved the
  object would be silently clobbered back to perpetual/future by the next rebuild pass. Gates the deribit doc's pending
  [OPERATOR] --apply sign-off (also cited live in main's BLK-fe7f6669 deferral).
status: open
nature: issue
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service]
scope: [engineer]
tags: [manifest, cefi, deribit, combo-instrument, honest-absence, data-correctness, rebuild]
related:
  - plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md
created: 2026-08-03
parent_epic: manifest_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.6
assigned_role: data_engineering
drift_direction: none
source: "review (slot1, agt-e60e67) escalation + main (agt-1756f6) triage, chat msgs 3407/3410/3411, 2026-08-03"
depends_on: []
locked_by:
locked_since:
context_scope:
resolved_by:
---

# CEFI manifest instrument_type=COMBO rows vanished — likely rebuild-overwrite of a manifest-only relabel

## What I found

`deribit_combo_perpetual_partition_move-003` (slot-15, `market-tick-data-service@04d48b3c`, shipped 2026-08-03) dry-ran
the partition-move script from `deribit_combo_perpetual_partition_move_2026_07_21.md` §5-6 against that doc's own
2026-07-21 baseline (15,119 manifest rows: 8,849 `perpetual` + 6,270 `future`, all combo-shaped symbols mispartitioned).
The dry-run found **zero** qualifying candidates — not because the mispartition was fixed, but because
`instrument_type=COMBO` now has **0 rows in the CEFI manifest, across every venue in it** (down from that doc's own §2b
baseline of 662 DERIBIT `combo` rows). Concretely re-confirmed: one of the doc's two named canary objects
(`.../instrument_type=perpetual/data_type=book_snapshot_5/BTC-FS-26DEC25_PERP.parquet`, 37,258 rows) still physically
exists on GCS at its OLD wrong-partition path with WRONG `instrument_id` content
(`DERIBIT:PERPETUAL:BTC-FS-26DEC25_PERP`) — but the manifest now carries **no row mentioning this symbol at all**, not
even a stale/wrong one.

**Scope precision (important, not yet nailed down):** "0 rows, any venue" was measured by the dry-run script's own
census, which reads `_index/availability_index.parquet` from the CEFI asset_group's tick bucket
(`resolve_bucket_name(cloud="gcp", kind="market-data", asset_group="cefi")`). That proves the drop across every **venue
within CEFI's manifest** — it does NOT prove or disprove anything about other asset_groups (TRADFI has its own
`instrument_type=COMBO` classification for CME multi-leg/combo contracts, e.g. `market-tick-data-service@132ea6b1`, but
per the bucket-isolation model that almost certainly lives in a completely separate manifest object). Todo 1 below
should state the confirmed scope precisely rather than reuse "fleet-wide" loosely.

**Leading hypothesis (unconfirmed — this is the fastest thing to check first):**
`market_tick_data_service/scripts/rebuild_cefi_manifest.py` derives `instrument_type` directly from the GCS object PATH
via regex (`r"instrument_type=(?P<itype>[^/]+)/"`, confirmed by direct read, lines ~189/206/218/430/454) — it does not
consult or preserve any prior manifest-only classification. If DERIBIT's 662-row COMBO baseline was ever produced by a
manifest-row relabel that did NOT also physically move the underlying object to an `instrument_type=combo/` path
(plausible: the writer-side fix, `2ddc6d4a`, only changed classification for newly-ingested rows going forward; a
retroactive relabel of pre-existing rows would need a SEPARATE migration this doc has not located), then any run of
`rebuild_cefi_manifest.py` (or an equivalent path-derived consolidator pass) between 2026-07-21 and now would silently
overwrite those manifest rows back to `perpetual`/`future` — matching every observed symptom: count drop to 0, object
still physically at the old path, wrong content untouched, zero manifest trace.

**Candidates checked and their status** (git log `--since=2026-07-21` across market-tick-data-service, `-i --grep`
sweeps for combo/manifest/prune/purge/consolidat/rebuild; NOT exhaustive — a quick pass, not a full investigation):

- `132ea6b1` (2026-07-27, tradfi "semantic-relabel COMBO residual") — relabels TRADFI rows TO `COMBO` (opposite
  direction), and is very likely a different asset_group's manifest entirely (bucket-isolated). Low probability, but
  Todo 1 should do a 2-minute confirm that CEFI and TRADFI really are separate manifest objects before fully dismissing
  it.
- `5334bff6` (2026-07-24, "remove DERIBIT-COMBO from active cefi venue enumeration") — a forward-dispatch guard only
  (stops future fetches to a deregistered VENUE named `DERIBIT-COMBO`); doesn't touch existing manifest rows or the
  `instrument_type` column. Ruled out.
- `bbad2c31` / `6365f05f` (2026-07-29, "no-batch-source phantom rows" / "combo" in the (venue, data_type) pairing sense)
  — naming collision only; these touch LIGHTER-ZKSYNC/EXTENDED-STARKNET `(venue, data_type)` combinations, not DERIBIT
  or the `instrument_type=COMBO` enum value. Ruled out.
- No `rebuild_cefi_manifest` / consolidator invocation was found or ruled out in this pass — confirming whether one
  actually RAN in the window (VM launch logs, deployment history, or the affected rows' own manifest
  `updated_at`/provenance metadata if the schema carries it) is the single highest-value next step.

## Why it matters

- This is a data-pipeline-correctness / honest-absence finding: an object physically present with wrong content and
  **zero** manifest registration is worse than a stale-but-present row — a manifest-only consumer silently under-counts
  real data with no error signal at all (the exact failure mode `honest-absence-downstream-handling.md` exists to
  prevent).
- **Live-gates an operator decision right now**: main cited this exact discrepancy deferring a separate worker's
  `--apply` sign-off request (BLK-fe7f6669) on the doc's original 15,119-row destructive prod move — don't schedule that
  `--apply` against either "0 remaining" or "15,119 remaining" until this doc's Todo 1 lands a trustworthy count.
- If the rebuild-overwrite hypothesis is confirmed, it's not a DERIBIT-specific bug — it's a **general hazard**: ANY
  future manifest-only relabel/migration script (of the kind this repo runs routinely, e.g. `132ea6b1`'s own TRADFI
  relabel) is silently reversible by the next path-derived rebuild pass unless the object is physically moved in the
  same operation. That would make this a process/tooling fix, not a one-off data patch.

## Todos

- [ ] [DIAG] P1. **Root-cause the instrument_type=COMBO manifest-row disappearance.** Confirm or refute the
      rebuild-overwrite hypothesis above: (a) determine whether `rebuild_cefi_manifest.py` or an equivalent path-derived
      consolidator/rebuild pass actually ran against the CEFI manifest between 2026-07-21 and 2026-08-03 (VM
      launch/deployment history, or the affected rows' manifest provenance timestamps if available); (b) if confirmed,
      verify the mechanism end-to-end on at least the one re-confirmed canary object (`BTC-FS-26DEC25_PERP`, currently
      at `.../instrument_type=perpetual/.../BTC-FS-26DEC25_PERP.parquet`); (c) determine SCOPE — is this isolated to the
      two S6 canary objects / DERIBIT combo rows specifically, or systemic (any manifest-only relabel anywhere in cefi's
      history that predates a later rebuild pass is equally at risk)? State the confirmed scope precisely (see "Scope
      precision" above — do not reuse "fleet-wide" without stating which asset_group(s) were actually checked). (d)
      Recommend next step: re-run the relabel WITH a physical move this time (may fold into
      `deribit_combo_perpetual_partition_move_2026_07_21.md`'s existing `--apply` design), a general process fix to
      `rebuild_cefi_manifest.py` (e.g., don't silently overwrite an `instrument_type` that disagrees with path when the
      disagreement looks intentional/recent), or both. Repo: market-tick-data-service. Done when: the mechanism is
      confirmed or refuted with direct evidence (not inference), the scope question is answered with a stated confidence
      level, and a concrete follow-up (new todo in this doc, or a fold-in to the deribit doc) is proposed with enough
      detail to dispatch without further investigation.

## Progress Log

- **2026-08-03**: Drafted by review (slot1, agt-e60e67) at main's request (chat msgs 3407/3410/3411), after main
  independently agreed this is a data-pipeline-correctness HARD RULE finding and elevated it to P1 — also noting it's
  the same discrepancy already cited live deferring a separate worker's `--apply` sign-off request (BLK-fe7f6669) on the
  deribit doc's original 15,119-row move. Content includes a from-scratch git-log sweep (market-tick-data-service,
  `--since=2026-07-21`) that ruled out 3 near-miss candidates and identified `rebuild_cefi_manifest.py`'s path-derived
  `instrument_type` parsing as the leading unconfirmed hypothesis — NOT independently verified against live
  manifest/deployment history (that's Todo 1's job). **Not committed by review** (zero commits, ever — role boundary) —
  handed as fully-drafted content to main to route to a live worker for the `docs(plans):` quickmerge.
