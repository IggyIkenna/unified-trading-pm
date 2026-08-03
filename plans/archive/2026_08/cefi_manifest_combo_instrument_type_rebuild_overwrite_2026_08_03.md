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
status: resolved # (was: open) 2026-08-03 -- sole todo done, doc archived per the 6-step ritual
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
  "slot-2 (data_engineering, task cefi_manifest_combo_instrument_type_rebuild_overwrite-001), 2026-08-03 — leading
  hypothesis refuted; true root cause already independently confirmed in
  deribit_combo_perpetual_partition_move_2026_07_21.md by slot-14 (task -005)"
superseded_by: deribit_combo_perpetual_partition_move_2026_07_21
---

> **✅ ARCHIVED 2026-08-03 — sole todo done.** This doc's own leading hypothesis (`rebuild_cefi_manifest.py`
> path-derived overwrite) was REFUTED after independent live verification. The confirmed root cause + both live
> follow-up todos (an `[OPERATOR]` MVP-scope decision, a `[DATA] P3.` bookkeeping-regen todo) live in
> `/plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md` (its `[DATA] P1.` todo + 2026-08-03
> Progress Log entry) — that doc is the live home for this finding going forward, this archive is the investigation
> record only. Codex-alignment check: **no new codex content required** — the confirmed mechanism is a one-off bug in a
> single already-run migration script (`complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`), not a new systemic
> contract; no codex SSOT needs updating.

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

- [x] ✅ [DIAG] P1. **DONE 2026-08-03 (slot-2, task `cefi_manifest_combo_instrument_type_rebuild_overwrite-001`).**
      **This doc's own leading hypothesis (`rebuild_cefi_manifest.py` path-derived overwrite) is REFUTED.** The actual
      root cause was independently found — with stronger direct evidence than this todo produced — by a sibling task
      (`deribit_combo_perpetual_partition_move-005`, slot-14, same day) working
      `plans/active/issues/deribit_combo_perpetual_partition_move_2026_07_21.md`'s own copy of this exact question (that
      doc's `[DATA] P2.` operator-review todo spawned an identical root-cause todo independently of this doc; both were
      in flight concurrently). Full evidence trail lives there (§ its `[DATA]     P1.` todo + Progress Log, 2026-08-03
      slot-14 entry) — summary:

      - **Confirmed mechanism**: the 662→0 drop happened during the **2026-07-24 Surface C v2 canonical-dedup `--apply`**
                    (`complete_cefi_manifest_canonical_dedup_v2_2026_07_20.py`, VM `canonical-migration-cefi-dedup-apply-20260724-232055`),
                    NOT `rebuild_cefi_manifest.py` — that script was never implicated; no evidence any of its runs touched this
                    population. Proven by a byte-diff between the dedup script's OWN pre-apply manifest snapshot
                    (`_index/snapshots/pre_d4_20260724T232332Z/availability_index.parquet`, 662 `combo`/`empty_confirmed`/DERIBIT rows,
                    100% baseline-matching) and the current live manifest (0 rows), cross-checked against the apply's `run.log`: the
                    only REVIEWED combo-labeled drop in that run was a different, correctly-scoped `venue=DERIBIT-COMBO` purge (196
                    rows) — the 662 bare-`venue=DERIBIT` rows were never a named target; they were silently swept into one of the
                    run's large itype-unbroken-down bulk counters (`eu-dropped=261630` / `de-dup-collapsed=1267269`), most likely via
                    `_dedup_blob`'s per-blob duplicate-collapse (exact colliding line not pinned — ruled correctly out of scope for a
                    bounded root-cause pass). Verdict: a genuine manifest-consolidation correctness bug in that one-off migration
                    script, not an intentional purge, and NOT a general `rebuild_cefi_manifest.py` hazard.
                  - **Mechanism verified end-to-end on the canary**: independently re-confirmed live BY THIS TASK (2026-08-03, same
                    session) — 0/9,912,045 rows in the current CEFI `_index/availability_index.parquet` carry `instrument_type=combo`
                    (any venue, any `capture_status` — direct bounded column-pruned read via `run-bounded-analysis.sh`, not a
                    whole-corpus walk); 0 rows of ANY `instrument_type` reference `BTC-FS-26DEC25` (full disappearance, not a
                    reclassification); the physical object is still present, byte-for-byte unchanged, at
                    `gs://market-data-tick-cefi-prd-central-element-323112/raw_tick_data/by_date/day=2025-01-15/pipeline_mode=batch_tardis/asset_group=cefi/venue=DERIBIT/instrument_type=perpetual/data_type=book_snapshot_5/BTC-FS-26DEC25_PERP.parquet`
                    (confirmed via a single-day bounded `gsutil ls`, not a corpus scan). This matches the sibling doc's findings
                    exactly — independent corroboration from a second read path.
                  - **Scope, confirmed precisely (closes this doc's own "Scope precision" open question)**: the 0-combo-rows result is
                    CEFI-manifest-wide (all venues in `market-data-tick-cefi-prd-*`'s `_index`, verified by direct query, not just a
                    DERIBIT sample). TradFi is confirmed OUT of scope — `gcloud storage buckets list` confirms
                    `market-data-tick-cefi-prd-central-element-323112` and `market-data-tick-tradfi-prd-central-element-323112` are
                    physically separate buckets/manifests, so TradFi's own COMBO relabel (`132ea6b1`) cannot be the same event; ruled
                    out with certainty, not just architectural inference.
                  - **Follow-up**: no NEW todo needed from this doc — the sibling doc already carries the two live follow-ups this
                    finding produces: an `[OPERATOR] P2.` decision (restore `"COMBO"` to `CeFiMvpRule.instrument_types` for bare
                    `venue=DERIBIT`, since `uac@11adf279`'s removal premise is now disproven — 70,128 real catalogue-confirmed
                    bare-DERIBIT COMBO instruments exist) and a `[DATA] P3.` low-priority bookkeeping-regen todo for the 662 lost
                    `empty_confirmed` rows. Nothing further to dispatch from here.

                  **Why this doc still resolves as DONE rather than a bare duplicate-closure**: the todo's own done-bar required
                  confirming or refuting the hypothesis with direct evidence, stating scope with a confidence level, and proposing a
                  dispatchable follow-up — all three are satisfied, just by refuting this doc's hypothesis in favor of the
                  already-proven one, plus this task's own independent corroboration (separate manifest read, separate GCS listing)
                  that the finding is solid rather than a stale/unverified claim. Repo: none (PM-doc-only; no code change — the
                  actual fix candidates, if any, belong to the sibling doc's `[OPERATOR]`/`[DATA] P3.` todos).

## Progress Log

- **2026-08-03**: Drafted by review (slot1, agt-e60e67) at main's request (chat msgs 3407/3410/3411), after main
  independently agreed this is a data-pipeline-correctness HARD RULE finding and elevated it to P1 — also noting it's
  the same discrepancy already cited live deferring a separate worker's `--apply` sign-off request (BLK-fe7f6669) on the
  deribit doc's original 15,119-row move. Content includes a from-scratch git-log sweep (market-tick-data-service,
  `--since=2026-07-21`) that ruled out 3 near-miss candidates and identified `rebuild_cefi_manifest.py`'s path-derived
  `instrument_type` parsing as the leading unconfirmed hypothesis — NOT independently verified against live
  manifest/deployment history (that's Todo 1's job). **Not committed by review** (zero commits, ever — role boundary) —
  handed as fully-drafted content to main to route to a live worker for the `docs(plans):` quickmerge.
- **2026-08-03** (slot-2, data_engineering, task `cefi_manifest_combo_instrument_type_rebuild_overwrite-001`) — Worked
  Todo 1. Read `rebuild_cefi_manifest.py` + its CF-11 re-emit module (`_rebuild_cefi_cf11.py`) end-to-end and confirmed
  the code IS structurally capable of dropping a manifest-only relabeled row (pre-2026-07-28 phantom-reclassification;
  post-2026-07-28 shadow-suppression that trusts-but-doesn't-restore the object-scan's own emission) — but found no
  direct evidence this script actually ran against the affected date/rows. Before finishing the investigation, a full
  read of the related `deribit_combo_perpetual_partition_move_2026_07_21.md` doc (fresh-pulled at task start, so
  current) revealed a sibling task (slot-14, `-005`) had ALREADY root-caused this exact question that same day with
  stronger direct evidence (a pre/post manifest snapshot diff + the actual migration VM's run.log), landing on a
  DIFFERENT mechanism (the 2026-07-24 Surface C v2 canonical-dedup `--apply`, not `rebuild_cefi_manifest.py`).
  Independently re-verified the live manifest (bounded column-pruned read of the 9.9M-row consolidated `_index`,
  `run-bounded-analysis.sh`-wrapped) and a targeted single-day GCS listing myself rather than taking either doc's word
  for it — both corroborate: 0 combo rows anywhere in CEFI, the canary symbol has 0 rows of any instrument_type, the
  physical object is untouched. Also independently confirmed CEFI/TradFi bucket isolation live via
  `gcloud storage buckets list` (closes this doc's own "2-minute confirm" ask). Resolved this doc by citing the
  sibling's root cause + my own corroborating evidence rather than re-deriving it a third time. No code changes needed
  (repos: [] on this task — pure diagnostic); the two live follow-ups (MVP-scope operator decision, bookkeeping-regen)
  stay tracked solely in the sibling doc to avoid a duplicate-todo fork. Next: archive this doc per the 6-step ritual
  (all todos done, unlocked) in a separate follow-up commit.
