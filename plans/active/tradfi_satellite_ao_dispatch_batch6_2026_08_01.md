---
doc_type: plan
title: TradFi satellite AO batch 6 — fresh /ag-closeout-audit extraction (4 clean orphans)
summary: >-
  Sixth AO-dispatch batch for tradfi, produced by a fresh `/ag-closeout-audit tradfi` pass on 2026-08-01 (autonomous
  mode, scheduled daily worker). Phase 0 rediscovered the covering set as 13 docs (up from the 11 a stale
  `generate_ag_closeout_audit_candidates.py` would have found — fixed same-session, see that script's own commit) and
  enumerated 65 real tradfi-primary candidates (not 67 — the 2 extra were line-cap forks of the consolidated closeout
  now correctly recognized as covering apparatus, not member docs). Phase 1 ran a 65-agent Workflow classifying every
  candidate against the 13-doc covering set: 31 excluded (genuinely multi-AG/cross-cutting content, confirmed by reading
  each doc's body, not just its tag), 3 archivable now, 19 archivable-after-planned-work (already self-dispatched or
  genuinely covered), and 12 orphaned (5 partial-coverage, 7 never-touched). Of those 12, 4 cleared the Phase-3
  conflict-check as bounded, conflict-free, AO-eligible work and are drafted below. The other 8 stay deferred: 4
  too-large-or-risky (2 unchanged from batch1-5's own precedent — `data_completion_tradfi_2026_07_15.md`,
  `issues/tradfi_canonical_path_migration_design_2026_07_19.md` — plus a newly-scoped 3rd,
  `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s CME instrument-definitions full re-fetch, and
  `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`, re-confirmed still conflict-gated on batch5's own todo 2
  which has NOT yet shipped), 3 operator-gated (unchanged from prior batches, not re-asked:
  `issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md`,
  `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`,
  `canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`), and 1 whose blocking precondition changed since
  batch5 in a way that needs a fresh look, not a naive re-run (`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`
  — the dry-run batch5 was waiting on has since landed, but its RESULT measured 0% twin-coverage, not the 100% the
  delete needs, so this is not yet a clean delete candidate). One further genuine orphan finding
  (`mtds_is_full_adapter_smoketest_findings_2026_07_07.md` carries 4 TradFi-specific bugs never promoted to checkboxes)
  is flagged but NOT drafted here — that doc's `parent_epic` is `instruments_master` and its `asset_group` is genuinely
  5-way ([cefi, defi, tradfi, sports, prediction]), so per the primary-owner rule a shared doc's write belongs to
  whichever tranche actually owns it, not to tradfi reaching in.
status: active
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, deployment-service, instruments-service, unified-api-contracts]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-6, satellite-docs, conflict-checked]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md,
    /plans/archive/2026_07/tradfi_satellite_ao_dispatch_batch5_2026_07_29_finalize.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md,
    /plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-06"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.5
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit tradfi run 2026-08-01 (autonomous / AO-dispatched mode, scheduled daily `ag_closeout_auditor`
  worker, dispatch agt-d7b683, slot 2, operator away). Phase 0 discovered the covering set via both documented paths
  (filename-pattern + dependency-graph); the dependency-graph path required a same-session fix to
  `generate_ag_closeout_audit_candidates.py` (it only resolved `depends_on:` for `*_finalize*` docs, missing 2
  finalize-less forks named only in the closeout's own `depends_on:` — one of which,
  `tradfi_phase_d_terminal_gate_2026_07_24.md`, was not even listed there until this same pass corrected it). Phase 1
  classified all 65 real tradfi-primary candidates via a `Workflow` (65 agents, 0 errors, 613 tool calls, ~1.27M ms
  wall-clock). Phase 3 ran the conflict-check against the full 13-doc covering family before drafting any todo below;
  every prior batch's own Deferred section was re-checked first per the skill's iterative-drain methodology (batch5's
  todo 2 status was live-verified still open via that doc's own text; the ES_OPT singleton-lock precondition was
  live-verified CLEAR via `gcloud compute instances list` — 0 `tradfi-bf-*`/`fred-full-*` instances running as of
  2026-08-01).
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
context_scope:
  [
    /codex/02-data/tradfi-databento-sourcing-ssot.md,
    /codex/02-data/availability-manifest-and-data-status.md,
    /codex/05-infrastructure/vm-launcher-runbook.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh,
    instruments-service/instruments_service/engine/urdi_reference_provider.py,
  ]
---

# TradFi satellite AO batch 6 — fresh audit extraction

> **Status: active — operator-approved 2026-08-06, dispatching.** Todo 2 (ES_OPT launch) will re-check the shared
> Databento singleton lock at execution time and safely wait/retry if a legitimate concurrent backfill (e.g. the
> in-flight NYSE/NASDAQ OHLCV fleet) holds it — the operator explicitly approved dispatching as-is rather than deferring
> todo 2. Per the ag-closeout-audit skill's autonomous-mode contract, a freshly-drafted batch always ships
> `status: draft` regardless of how clean the conflict-check came back; flipping to `active` to actually dispatch it is
> an operator decision, never autonomous.
>
> All 4 todos below are same-priority-independent and were checked for file collisions (see the matrix near the bottom)
> — all 4 touch distinct repos/scripts, no overlap.

## Why this batch exists

This is the first fresh `/ag-closeout-audit tradfi` pass since batch5 (2026-07-29), and the corpus moved in 3 days:

1. **A same-session Phase-0 tooling fix corrected the covering-plan count** (11 → 13), which in turn corrected the real
   candidate-member count (67 → 65) — `generate_ag_closeout_audit_candidates.py` was not resolving the consolidated
   closeout doc's own `depends_on:` for forks with no paired `*_finalize*` doc. This didn't change today's orphan count
   in practice (the 2 previously-miscounted docs were both actively-maintained covering plans, not orphans either way),
   but it makes every future `/ag-closeout-audit tradfi` run's Phase 0 accurate without needing manual correction.
2. **The ES_OPT backfill's blocking precondition cleared.** `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s
   ES_OPT launch was blocked 2026-07-30 by a live concurrent `tradfi-bf-fred-full-*` job holding the account-wide
   Databento singleton lock. Live-verified 2026-08-01 (`gcloud compute instances list --filter='name~"tradfi-bf"'` and
   `--filter='name~"fred-full"'`, both zero results): that job has since completed and self-deleted, and no other
   `tradfi-bf-*` instance is running. This todo is now genuinely ready, not just theoretically unblocked.
3. **A 2026-07-31 post-drain re-measurement on `tradfi_manifest_writer_legacy_id_regression_2026_07_21.md` split out a
   brand-new, previously-nonexistent todo** (historical manifest repair for a one-time 2026-07-27 registration-burst's
   null-id rows) — this postdates batch5 (2026-07-29) entirely, so no prior batch's conflict-check could have seen it.
4. **2 more docs came back genuinely orphaned with clean, conflict-free, bounded residual work** — one investigate-first
   item on `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (2 anomalous Sundays) and one on
   `tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` (BASE_ASSET/underlying naming-drift
   reconciliation). Neither is referenced by any doc in the 13-doc covering family (verified by grep + read, not just
   grep, per the skill's Phase 1 discipline).

## Todos

- [ ] [DATA] P2. **Historical manifest repair for the 2026-07-27T16:46:40-48Z registration burst's null-id rows.** 3,612
      NASDAQ/NYSE equity/ETF rows (`ohlcv_1m`/`trades`) + 100 CBOE INDEX rows (`ohlcv_15m`) carry canonical UPPERCASE
      `instrument_type` but `instrument_id=None`; content `date` spans dozens of historical dates 2024-2026 sharing one
      8-second write burst — the signature of a one-time metadata registration/recovery script, NOT a live writer bug
      (the resolver is already proven correct for these exact venue/itype shapes via 6 regression tests shipped
      2026-07-31, `market-tick-data-service`, `tests/unit/engine/test_tradfi_manifest_shard.py`). Identify the exact
      registration/recovery script that ran at that timestamp (candidates in `market_tick_data_service/scripts/`
      matching `recover_tradfi_*`/`register_tradfi_*` — none read so far matched by content, per the source doc's own
      note) to confirm what original identifying information is recoverable per row, then either (a) re-derive +
      CAS-write (`if_generation_match`) a canonical id for each of the 3,712 rows by cross-referencing the actual GCS
      object each row corresponds to (bounded — dozens of distinct dates, not a corpus walk), or (b) if genuinely
      unrecoverable from the GCS object itself, document that explicitly rather than guessing. Repo:
      market-tick-data-service. **Done when**: every one of the 3,712 rows carries a verified canonical id or a recorded
      non-recoverability reason, with a before/after manifest census, and `quality-gates.sh` is green. Source:
      `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`.

- [ ] [DATA] P0. **Launch the ES_OPT backfill, then wire its post-launch manifest-verify into Phase-D gate tracking
      (combined into ONE todo — the second step only makes sense once the first lands).** (1) Re-verify the singleton
      lock is still clear immediately before launch (`gcloud compute instances list --filter='name~"^tradfi-bf-"'`) —
      live-verified clear 2026-08-01, but re-check at execution time per the async-wait-and-poll-discipline norm, then
      run `bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh --root-symbol ES_OPT` (defaults: SPOT
      provisioning per the backfill-VM-defaults-to-SPOT HARD RULE; year-shards 2022-2026 per `cme-expiry-calendars.sh`'s
      `default_years_for_root`; `data_types=ohlcv_1m` only). This is a standard, idempotent, SPOT-default backfill-VM
      launch — no delete, no `--apply`, no `[OPERATOR]` tag needed (safe-idempotent justification per `task_template.md`
      finding O: shards simply re-run on preemption). Done when: the VM(s) are STARTED (<60s) + confirmed RUNNING at
      T+10min, per async-wait-and-poll-discipline (no fire-and-forget). (2) Once launched and complete, run the same
      manifest-count-only check used for ES futures (mirrors the NASDAQ/NYSE precedent,
      `data_completion_tradfi_2026_07_15.md`) scoped to venue=CME × root∈{ES,EW,EW1,EW2,EW4,E1A,E2A,E3A,E4A, E5A,EOM} ×
      data_type=ohlcv_1m, and record the result as a line item in
      `plans/active/tradfi_consolidated_closeout_2026_07_18.md`'s MVP-cell table, "S&P index options" row. Repos:
      deployment-service, unified-trading-pm. **Done when**: the VM(s) ran to completion, the manifest-count check
      result is recorded with real query + counts, and the MVP-cell table row is updated. Source:
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`.

- [ ] [DATA] P3. **Investigate the 2 anomalous Sundays in the CME instrument-definitions manifest.** `2024-06-02` and
      `2024-10-06` hard-fail with `RuntimeError: URDI returned zero records` instead of writing an honest
      `empty_confirmed` row like the other 363 weekends in the corpus (99.92% floor coverage otherwise) — a minor
      adapter-level inconsistency, not yet root-caused. Determine why these 2 specific dates diverge from the other 363
      (a URDI-side outage, a malformed request, a genuine zero-instrument-universe day) and either fix the adapter to
      write `empty_confirmed` correctly for this case, or document why these 2 dates are a legitimate exception. Repo:
      instruments-service. **Done when**: the root cause is identified and either fixed (with a regression test) or
      explicitly documented as a non-bug exception. Source: `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`
      (Deferred work after 2026-07-26, row 2).

- [ ] [DATA] P2. **Reconcile the `BASE_ASSET`/manifest `underlying` string-naming drift found incidentally during the
      2026-07-28 within-bounds-source-zero cross-check.** `HEATING-OIL`/`HEATINGOIL`/`HO`,
      `NAT-GAS`/`NAT-GAS-HH`/`NATGAS`, and similar variants disagree between `BASE_ASSET` and the manifest's actual
      stored `underlying` string. Determine whether this drift causes any real denominator/accounting issue (per the
      source doc's own conditional framing — "if it is found to cause its own... issues"); if yes, propose and apply the
      reconciliation; if no, close this item with the negative evidence recorded rather than leaving it open
      indefinitely. Repos: market-tick-data-service, unified-api-contracts. **Done when**: either the drift is fixed
      with regression coverage, or it is confirmed harmless with the specific check that proved it (e.g. a
      denominator/count comparison before vs. after normalizing the strings). Source:
      `issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` (todo 3).

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`data_completion_tradfi_2026_07_15.md`** — unchanged from batch1-5. Phase 0 layout audit, ~133K-cell NASDAQ/NYSE
  backfill, G1 `--apply-write` denominator-seed execution (gate-b still frozen), and the catalogue-scheduler terraform
  wiring are all real but too large/interdependent for a batch todo. (One of its 14 open items — the Massive→Databento
  reference-capture replacement path — IS covered, via `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`'s
  2026-07-29 re-feed todo; the rest stay deferred as a whole per this doc's own established batch1-5 treatment, not
  cherry-picked.)
- **`issues/tradfi_canonical_path_migration_design_2026_07_19.md`** — unchanged from batch1-5. Steps 5-6 are explicit
  `[GATE]` operator-go items over a 2.73M-object corpus (copy→verify→delete + a 140,138-object REBUNDLE second pass);
  the whole sequencing (steps 4-8) stays deferred as one unit.
- **NEW (2026-08-01) — `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s full CME instrument-definitions
  re-fetch** (2020-01-01→2026-06-18, ~2,368 days; sample-verified 2 dates both confirm a real gap, instrument_count
  jumps ~15-18K/day pre-lockdown → ~74-95K/day post). The finding's own text explicitly scopes this as "a real backfill
  campaign, not a small sample task — needs its own dedicated plan/VM launch, not attempted here" — same class as the
  ES-futures/ES_OPT backfills that got dedicated planning attention across multiple batches, not a single todo. Flag for
  a dedicated design pass, not a future batch6+N extraction.
- **`tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`** — re-confirmed still `orphaned_never_touched` and still
  conflict-gated. All 7 remaining items (down from 8 — the CME/`coverage_starts.py` mismatch already resolved) are gated
  on the MDPS `continuous_future` hit-rate mismatch batch5's own todo 2 is re-testing. **Live-verified 2026-08-01**:
  that todo is still `[ ]` open, explicitly marked "NOT YET DISPATCHABLE (2026-07-31, slot-2) ... still mid-backfill,
  gated on that fleet finishing before build-continuous + the re-measure can run" — so the blocker has NOT cleared since
  batch5. This doc remains a strong batch7+ candidate the moment that todo ships; not drafted speculatively here, per
  batch5's own explicit prediction.

## Deferred — operator-gated (a ruling, not a re-triage, unblocks these; unchanged, NOT re-asked)

`issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (which `EXCHANGE_CODE_TO_NAME` registry is
authoritative — `tradfi_instrument_universe.py` 96 keys vs `tradfi_symbology.py` 61 keys, 17 value-mismatches, now
confirmed to hit BOTH CME and CBOE);
`issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s sole remaining
`[DESIGN] P2` on whether real aggregated `ohlcv_15m`/`ohlcv_24h` TradFi bars are wanted (a scope/product judgment call,
not a worker-determinable fact — reconfirmed KEEP-NA by the 2026-07-30 na-eligibility-audit);
`canonical_id_p1_tradfi_combo_leg_canonicalization_2026_07_08.md`'s residual catalogue-script `--apply` reapplication
for 91 CBOE + 312 DBEQ rows (the doc's own text calls it "pending operator confirmation"); and the entirety of
`issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md` (a pure `assigned_vm: NA` human-decision queue by
design — item 3's `EXCHANGE_CODE_TO_NAME` SSOT contradiction is the same still-open gate as the chain-bundle-sampler
item above, and both of its own PM todos stay blocked on that).

## Deferred — precondition changed since batch5, needs a fresh look (not a naive re-run)

- **`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md`'s todo 3 (the actual legacy-twin bucket DELETE)** — batch5
  deferred this waiting on batch1's dry-run to land. **That dry-run HAS since landed (closed 2026-07-30)**, but its
  measured RESULT is 0% twin-coverage (900 class-B legacy twins loaded → 0 deletable, 900 blocked because "canonical
  twin NOT captured in manifest") — not the 100% coverage the delete's own safety gate requires. This is a NEW,
  different blocker than the one batch5 was tracking (not "the dry-run hasn't run yet" but "the dry-run ran and says the
  delete can't proceed"). Not drafted here: root-causing WHY twin-coverage measures 0% instead of 100% (a manifest
  registration gap, most likely) needs its own investigation before any todo — including a delete-adjacent investigation
  todo — touches this doc again, given the whole doc exists specifically to gate a real prod-bucket delete with maximum
  caution. **Recommend**: a dedicated investigation pass into the 0%-coverage measurement, separate from this batch,
  before either a batch7 todo or a direct operator ask.

## Flagged, not batched — cross-tranche ownership

- **`mtds_is_full_adapter_smoketest_findings_2026_07_07.md`** carries 4 TradFi-specific bugs that were never promoted to
  checkboxes at all (a real violation of the "every follow-up is a todo, never prose" HARD RULE): (1)
  `databento_adapter.py`'s CME event-contract `instrument_class` handling — **live-checked 2026-08-01: this specific
  code pattern (`instrument_class="BAG"`) no longer greps anywhere in the tradfi databento adapter family post the
  2026-07-?? Wave-3 size-debt file split (`databento_adapter.py` was broken into `databento_fetch.py` /
  `databento_cme_converter.py` / `databento_equity.py` / etc.) — this finding may already be moot, or may have relocated
  under different logic; needs re-verification, not a blind "still broken" assumption.** (2) `umi_tick_provider.py`'s
  ICE/CBOE INDEX routing — partially re-checked: the file now carries explicit 2026-06-25 design commentary about CBOE
  VIX routing through Databento deliberately (VX futures, not a Yahoo INDEX symbol), so at least the VIX case may
  already be intentional, not a bug; the "every other CBOE data_type" claim is unverified. (3) stale TradFi catalogue
  vs. fixed adapter code (ICE/CBOE/NASDAQ/NYSE row counts) — a data-state claim, not independently re-verified this
  pass. (4) `_umi_yahoo.py`'s `fetch_yahoo_equities`/`fetch_yahoo_fx` ignoring an `instrument_ids` filter —
  **live-confirmed 2026-08-01: `fetch_yahoo_equities` genuinely has no `instrument_ids` parameter at all,
  unconditionally iterating the full `KRX_EQUITIES` registry — this one is real, still-open.** This doc's `parent_epic`
  is `instruments_master` and its `asset_group` is genuinely `[cefi, defi, tradfi, sports, prediction]` (5-way) — per
  the primary-owner rule for multi-tranche docs, a WRITE to a shared doc (promoting these to real checkboxes, fixing
  them) belongs to whichever tranche actually owns `instruments_master`-epic content, not to tradfi drafting into
  someone else's file. Flagging here so it isn't lost, not batching it.

## File-collision matrix (verified before finalizing — same-priority todos run concurrently by default)

| Todo | Primary file(s) touched                                                                                                                                         |
| ---- | --------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | `market-tick-data-service` manifest-repair script (historical CAS rewrite of 3,712 rows; exact script TBD by the worker per the todo's own investigation step)  |
| 2    | `deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh` (execution only, no code edit) + `tradfi_consolidated_closeout_2026_07_18.md` (MVP-cell table row) |
| 3    | `instruments-service` URDI CME instrument-definitions capture path                                                                                              |
| 4    | `market-tick-data-service` / `unified-api-contracts` `BASE_ASSET`/underlying naming registries                                                                  |

No file appears twice — all 4 todos touch distinct repos/scripts.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch6_2026_08_01_finalize.md` (`depends_on` on this plan plus `gate_on_depends: true`),
mirroring the batch1-5 finalize pattern.

## Progress Log

### 2026-08-06 — slot 2, task `tradfi_satellite_ao_dispatch_batch6-002` (todo #2, ES_OPT launch) — pre-compact checkpoint

**Status: IN FLIGHT — todo #2 still `[ ]`. Blocked on the Databento singleton lock (expected; operator-approved wait, no
`--force`).** Nothing shipped this session; no checkbox flipped (the task's done-when is not yet met).

**Phase 1 — launch (NOT yet executed):**

- Singleton lock re-verified 2026-08-06T~15:45Z: HELD by a live concurrent `tradfi-bf-*` fleet in `asia-northeast1-c`
  (32 VMs at first check, draining to 28 by ~16:20Z — NASDAQ/NYSE OHLCV shards, CBOE VX 2026, CME g01 roots
  ES/CL/MET/MBT/BTC; all created 2026-08-06T08:00-08:12Z, all verified actively progressing via run.log + monotonic
  `PROGRESS.json` — NOT stale, do NOT force/delete).
- Dry-run confirmed the launch plan:
  `bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh --root-symbol ES_OPT` → 5 VMs
  `tradfi-bf-es-opt-light-{2022..2026}-<ts>`, `e2-standard-4`, SPOT, `data_types=ohlcv_1m`, `asia-northeast1-c`.
- **NEXT ACTION (fresh session):** re-check
  `gcloud compute instances list --filter='name~"^tradfi-bf-" AND status=RUNNING' --zones=asia-northeast1-c`. When count
  == 0, run the launch command; confirm VM(s) STARTED (<60s) + RUNNING at T+10min per async-wait-and-poll-discipline (no
  fire-and-forget).

**Phase 2 — post-launch manifest-count check (NOT yet run; query vocabulary LOCKED via baseline probe 2026-08-06):**

- Baseline census of `gs://market-data-tick-tradfi-prd-central-element-323112/_index/availability_index.parquet`
  (6,831,204 rows, 2026-08-06T15:50Z snapshot): venue=CME × data_type=ohlcv_1m × instrument_type=`options_chain` =
  68,604 rows, of which 68,203 carry EMPTY instrument_id (the legacy null-id population — tracked by todo #1 of this
  batch) and 401 carry `CME:OPTION:SP500` (pre-existing SPX index-option data). **ZERO rows carry the ES_OPT roots'
  canonical ids pre-launch.**
- **WRITER VOCABULARY (probed, do not assume):** options rows are `instrument_type=options_chain` (NOT
  `option`/`OPTION`); row-key atom is canonical `CME:OPTION:<ROOT>` for roots ∈ {ES,EW,EW1,EW2,EW4,E1A,E2A,E3A,E4A,
  E5A,EOM}.
- **POST-LAUNCH QUERY** (mirrors ES-futures precedent `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`,
  manifest-count-only, single manifest read, no bucket walk): venue=CME × data_type=ohlcv_1m ×
  instrument_type=options_chain × instrument_id ∈ {CME:OPTION:ES, CME:OPTION:EW, CME:OPTION:EW1, CME:OPTION:EW2,
  CME:OPTION:EW4, CME:OPTION:E1A, CME:OPTION:E2A, CME:OPTION:E3A, CME:OPTION:E4A, CME:OPTION:E5A, CME:OPTION:EOM};
  report capture_status distribution + `row_count>0` counts + date span. Record the result in
  `tradfi_consolidated_closeout_2026_07_18.md` MVP-cell table "S&P index options" row (line ~259). Baseline to compare
  against: 0 scoped rows pre-launch (all 11 roots absent).

**Observation (not this task's scope — flagged for the NASDAQ/NYSE OHLCV fleet owner):** sampled run.log for
`tradfi-bf-nyse-ohlcv-1m-2024-d02-*` shows repeated
`ERROR Schema validation FAILED: venue=NYSE data_type=ohlcv_1m missing columns=['timestamp']` while still emitting rows
(`rows_emitted` rising) — ambiguous (validation log that does not block writes, or a real schema gap). Belongs to the
fleet's own plan, not this batch; verify before filing.

### 2026-08-06T~16:10Z — slot 2, same task — post-compact resume + operator decision (keep waiting, twice)

**Status unchanged: IN FLIGHT — todo #2 still `[ ]`. Lock still held.** Fleet re-verified 2026-08-06T16:05Z: **21
`tradfi-bf-*` RUNNING** (drain 32→28→24→23→22→21), every VM monotonic + fresh PROGRESS.json/run.log heartbeats — live,
not stale.

**Operator decision (2026-08-06, twice-confirmed via direct question, incl. with ETA numbers on the table): KEEP
WAITING, no `--force`.** Three session-level "proceed now" nudges do NOT override this — they are idle nudges, not a
force-launch instruction. **Do NOT launch with `--force` on a nudge alone.**

**Drain ETA (extrapolated from per-VM progress vs ~8h elapsed, all monotonic): the lock is realistically held ~15–46h
more.** ~6 VMs finish in ~1–3h (nasdaq-2024-d05 @2024-11-30, nyse-2024-d05 @11-16, nasdaq-2025-d04 @09-18, nyse-2023-d03
@09-08, nyse-2024-d04 @09-18, nyse-2025-d04 @09-18); ~5 in ~10–19h; the long pole (~20–46h) is the year-shard CME g01 +
nyse-2025-d01 set (cme es-2020 @2020-03-24 ~28h, met-2023 @02-25 ~46h, met-2025 @03-18 ~30h, btc-2026 @02-25 ~23h,
cl-2026 @03-04 ~19h, nyse-2025-d01 @03-04 ~38h, cboe-vx-2026 @03-04 ~19h, mbt-2024 @05-26 ~12h, nasdaq-2023-d01 @06-02
~11h, met-2024 @05-12 ~14h, nasdaq/nyse-2025-d02 @04-25 ~17h, nyse-2024-d02 @04-25 ~17h, nasdaq-2024-d02 @05-02 ~16h,
nyse-2023-d01 @05-12 ~14h). Re-extrapolate from `PROGRESS.json` rather than trusting these exact hours — the point is it
is a **multi-day hold**, not minutes.

**CORRECTION (2026-08-06T~16:25Z) — the 15–46h estimate was pessimistic.** The early-run average was inflated by VM
spin-up; a two-snapshot delta (16:05Z vs 16:25Z) shows marginal rates ~4–8× faster. Corrected lock-clear ETA: **~6–12h
worst case**, and most VMs finish in 1–4h (nasdaq-2024-d05 @2024-12-14 and nyse-2024-d05 @11-30 are ~20–60 min out;
cboe-vx/btc-2026 @03-25, mbt-2024 @07-21, met-2024 @06-16 ≈ 1–2h; cl-2026 @03-18, es-2020 @04-21, met-2025 @04-08,
nasdaq-2024-d02 @05-23 ≈ 2–4h; worst case ~5–12h: met-2023 @03-11, nasdaq-2025-d02 @05-09, nyse-2023-d01 @05-26,
nyse-2024-d02 @05-09, nyse-2025-d02 @05-02). Still a multi-hour wait — keep-waiting decision unchanged.

**MATERIAL EVENT (2026-08-06T~18:05Z) — new backfill wave RESET the lock.** At ~18:00Z a fresh `tradfi-bf-*` wave
launched (13 VMs: NYSE 2023 d01–d05, NASDAQ 2023 d01–d05, CME g01 es-es-2020 / met-met-2023 / mbt-mbt-2024 /
met-met-2024), on top of the 6 original long-pole VMs still running → **19 RUNNING**. The drain to 0 is no longer near:
the new year-shard wave realistically adds **+8–12h** (same ~8–10h runtime as the 08:00Z wave). New VMs were <5 min old
(no PROGRESS.json yet, booting normally) at first sighting. Owner/launcher of the new wave NOT identified from within
this slot — assumed another dispatch of the same batch or a sibling task. Keep-waiting decision UNCHANGED (legitimate
concurrent backfills; no `--force`), but the horizon is now indeterminate — re-check the fleet before assuming a clear
ETA.

**EXPANSION + OPERATOR RE-CONFIRMATION (2026-08-06T~18:10Z).** By 18:10Z the fleet grew to **28 RUNNING and still
climbing** — an orchestrated multi-year NYSE/NASDAQ + CME backfill campaign launching successive waves (2023 d01–d05 →
2024 d01–d03+, 2025 likely next): 2×2020, 11×2023, 11×2024, 1×2025, 3×2026. The Databento singleton is now held
CONTINUOUSLY; a genuine count==0 window may not occur for days. **Operator asked directly with these facts (2026-08-06,
3rd confirmation, explicit): KEEP WAITING (status quo).** This overrides the "draining to 0" premise of the earlier
confirmations — the wait is now open-ended by explicit operator choice. **Do NOT `--force`; do NOT delete campaign
VMs.** A fresh session should re-check the fleet and, if still >0, continue waiting per this decision. If the task is
later re-scoped or the campaign ends, launch ES_OPT per the phase-1 command below.

**Watcher hardening (learned):** a `gcloud ... | wc -l` watcher false-fires `count==0` on a transient gcloud error
(empty stdout). Use an error-aware loop: only fire CLEAR when the gcloud call rc==0 AND the result is empty; on rc!=0
hold the wait. Current armed watcher (this session) is error-aware; a fresh session should re-arm the same shape.

**THIRD WAVE — CONTINUOUS-LAUNCH PATTERN CONFIRMED (2026-08-06T~21:00Z).** A 3rd wave launched at 21:00Z (14:01 PDT):
es-es-2020, met-met-2023, nasdaq-2023-d01, alongside the still-running originals → **6 RUNNING**. Waves so far: 08:00Z,
18:00Z, 21:00Z — the campaign **replenishes year-shards as slots free**. The Databento singleton is held INDEFINITELY;
there is no count==0 window in sight by construction, not just by estimate. This is exactly the scenario of the 18:10Z
operator decision (keep-waiting, no `--force`), so no re-ask is needed — the decision stands. A fresh session should
treat "count >0" as the permanent expected state and NOT expect the lock to clear on its own; launch ES_OPT only if a
real count==0 window appears or the operator re-scopes/overrides.

**Phase 2 toolchain verified intact post-compaction:** `_scratch/availability_index.parquet` (119 MiB snapshot) + the
market-tick-data-service `.venv` python (pyarrow 23.0.1) still present; baseline re-run clean (0 canonical ES_OPT rows
pre-launch). Post-launch = re-download a FRESH manifest + run the phase-2 query above.

**SLOT-11 SESSION 3 (2026-08-07T04:46Z) — Watcher armed and running.** Fleet at session start: 7 VMs (2 completing
imminently). At 04:55:52Z: watcher launched (harness task `bff5b50zn`), PID 957114. Poll 1 (04:55:52Z): 4 VMs. Poll 2
(05:00:53Z): 4 VMs. Watcher is error-aware; will autonomously launch ES_OPT when count==0, verify T+30s/T+10min,
download fresh manifest, run pyarrow count query (venue=CME × ohlcv_1m × options_chain × 11 roots), flip checkbox,
commit `docs(plans):` push, call `/done`. Script at:
`/home/ubuntu/.claude-configs/orch-slot-11/cc-tmpdir/claude-1000/-home-ubuntu-unified-trading-system-repos--tabs-11/10b8b22e-b2b7-4746-a864-3fec64b52969/scratchpad/es_opt_watcher.sh`
(and promoted to `deployment-service/scripts/vm/es-opt-backfill-watcher.sh`). Log: `…/scratchpad/es_opt_watcher.log`.
**Compaction safety:** bash process (PID 957114) and harness task survive compaction.

- **NEXT ACTION (fresh session):** First check if watcher is still alive:
  `kill -0 957114 2>/dev/null && echo ALIVE || echo DEAD`. If ALIVE: wait for harness notification (`bff5b50zn`) — the
  watcher will complete autonomously. If DEAD: check if todo #2 checkbox is already flipped (done). If not done, re-arm:
  update SCRATCHPAD var in `deployment-service/scripts/vm/es-opt-backfill-watcher.sh` and re-launch with the Bash
  run_in_background tool. Do NOT re-run if watcher is alive — singleton lock race risk.

- **context-scout 2026-08-07**: populated context_scope (6 entries) — the 4 codex docs already named in this doc's own
  "Codex SSOTs" section, plus the 2 highest-value per-todo source paths from the File-collision matrix
  (`launch-tradfi-backfill-vm.sh` for the P0 ES_OPT todo, `urdi_reference_provider.py` for the CME
  instrument-definitions todo).

**SLOT-11 SESSION 4 (2026-08-07T05:58Z) — Watcher re-armed after session-3 instance died.** Original watcher (PID
957114, harness task `bff5b50zn`) went silent after poll 10 (05:41:01Z, 3 VMs); confirmed DEAD via `kill -0` at 05:57Z
(~17min gap, no poll 11 despite 300s cadence — process died, root cause not investigated, not needed). Todo #2 checkbox
confirmed still `[ ]` (not a stale-DEAD false alarm). Live re-check at re-arm time: 2 tradfi-bf-* VMs running (down from
3 — fleet still draining). Re-armed from the promoted script `deployment-service/scripts/vm/es-opt-backfill-watcher.sh`
into the SAME scratchpad dir (prior log renamed to `es_opt_watcher.log.run1` to avoid poll-number confusion with the new
run). New instance: **PID 2186673**, PPID=1 (confirmed fully detached from the launching harness task — nohup + `&`
reparented it to init, so it will NOT die when the launching Bash tool call's own background-task wrapper exits). Poll 1
(05:58:35Z): 2 VMs. Same 6-phase autonomous script (poll → launch ES_OPT → verify T+30s/T+10min → poll completion →
manifest query → flip+commit+push+`/done`).

**SLOT-11 SESSION 5 (2026-08-07T06:07Z) — Watcher re-armed AGAIN; root-caused the death and fixed detachment.** PID
2186673 (session 4) also died silently — between poll 2 (06:03:36Z, 10 VMs) and 06:05:53Z, mid-`sleep 300`, with **zero
FATAL log entry**. A mid-sleep death with no error output rules out an internal script bug (nothing executes during
`sleep`) — it means an external signal killed it. Diagnosis: `nohup cmd &` reparents the child to init on parent exit
(confirmed PPID=1 both times) but does **NOT** put it in a new process group — under `bash -c "..."` (no job control /
`set -m`), a `&`-backgrounded job stays in the **same PGID** as the invoking shell. If the launching Bash tool's
tracked-task cleanup kills by process group (common sandbox pattern) rather than by direct-child tracking, a `nohup`'d
grandchild with PPID=1 is still reachable via that shared PGID and dies anyway — PPID=1 alone is NOT sufficient proof of
immunity. **Fix: `setsid nohup bash script.sh > log 2>&1 < /dev/null &` + `disown`** — `setsid` makes the process both
session leader AND process-group leader of a brand-new group, genuinely unreachable via the launching shell's PGID/SID.
**Gotcha hit while re-arming:** util-linux `setsid` without `-f` forks internally when it can't `setsid()` in-place, so
`$!` in the launching shell captures the WRONG pid (the forked wrapper, which exits immediately) — the real long-lived
process gets a **different** PID. Always resolve the real PID via
`ps -ef | grep '<scratchpad>/es_opt_watcher.sh' | grep -v grep` after launch, never trust `$!` with plain (non-`-f`)
`setsid`. New instance: **PID 2367038**, confirmed `PGID=SID=2367038` (own session AND own process group — the actual
isolation bar, not just PPID=1). Poll 1 (06:07:21Z): 22 VMs (fleet is now large — NASDAQ/NYSE 2023 wave in full swing;
does not change watcher behavior, still just waits for count==0).

- **NEXT ACTION (fresh session, supersedes both PID-957114 and PID-2186673 instructions above):** First check if watcher
  is still alive: `kill -0 2367038 2>/dev/null && echo ALIVE || echo DEAD`. If ALIVE: wait for autonomous completion —
  poll the log at `<scratchpad>/es_opt_watcher.log` or check `plans/active/` for the checkbox flip (no harness task ID
  tracks this instance; it was launched fully detached). If DEAD: check if todo #2 checkbox is already flipped (done).
  If not done, re-arm AGAIN from `deployment-service/scripts/vm/es-opt-backfill-watcher.sh`: (1) update `SCRATCHPAD` to
  a fresh writable dir, (2) launch with `setsid nohup bash script.sh > log 2>&1 < /dev/null & disown` — NOT plain
  `nohup ... &` (insufficient — see above), (3) find the REAL pid via `ps -ef | grep script.sh | grep -v grep` (NOT `$!`
  — `setsid` without `-f` forks, so `$!` is wrong), (4) verify with `ps -o pid,ppid,pgid,sid -p <pid>` that **PGID and
  SID both equal the process's own PID** before trusting it survives — PPID=1 alone is insufficient. Do NOT re-run if
  watcher is alive — singleton lock race risk.

### 2026-08-07T~04:46Z — slot 11, task `tradfi_satellite_ao_dispatch_batch6-002` (todo #2) — fresh session

**Status: IN FLIGHT — todo #2 still `[ ]`. Fleet draining (6 VMs remain from 03:00Z wave; operator decision to keep
waiting unchanged).** Background watcher armed.

**Fleet snapshot at ~04:46Z (slot 11 fresh session):**

- `tradfi-bf-nyse-ohlcv-1m-2023-d01-20260807-030305` — COMPLETED (exit_code=0, self-deleting; verified via run.log)
- `tradfi-bf-cme-ohlcv-1m-g01-es-es-2020-20260807-030050` — RUNNING at chunk 19/53 (2020-05-18), ~3h remaining
- `tradfi-bf-cme-ohlcv-1m-g01-mbt-mbt-2024-20260807-030438` — RUNNING at 2024-09-03, progressing
- `tradfi-bf-cme-ohlcv-1m-g01-met-met-2023-20260807-030119` — RUNNING, just (re)initialized DatabentoAdapter
- `tradfi-bf-nyse-ohlcv-1m-2024-d04-20260807-030741` — RUNNING, 2024 date range active
- `tradfi-bf-nyse-ohlcv-1m-2024-d05-20260807-030801` — RUNNING at 2024-12-09 (near end), ~60min
- `tradfi-bf-nyse-ohlcv-1m-2025-d04-20260807-031131` — RUNNING at 2025-10-10

Count dropped from 28 (2026-08-06T18:10Z) → 6 (2026-08-07T04:46Z). Drain is progressing. ETA: es-es-2020 is the long
pole (~3h from check time); if no new wave launches, count==0 likely ~07:00-09:00Z 2026-08-07.

**Watcher armed:** background script `es_opt_watcher.sh` will:

1. Poll every 300s for tradfi-bf-* count==0 (error-aware: rc!=0 = hold)
2. Launch ES_OPT per phase-1 command when clear
3. Verify T+30s started + T+10min RUNNING
4. Poll for tradfi-bf-es-opt-* completion
5. Download fresh manifest, run count query, update closeout plan, flip checkbox, commit+push, call /done

### 2026-08-07T~05:51Z — slot 11, session 4 — watcher re-armed

**Status: IN FLIGHT — todo #2 still `[ ]`. Watcher re-armed (harness task `bcumi0sad`).** Prior watcher (PID 957114,
task `bff5b50zn`) died between sessions; checkbox NOT yet flipped. Fleet at re-arm: 2 VMs remaining
(`tradfi-bf-cme-ohlcv-1m-g01-es-es-2020` at 2020-07-14, `tradfi-bf-cme-ohlcv-1m-g01-met-met-2023` at 2023-05-06 — both
live/monotonic-progressing, not stale). Long pole: met-met-2023 (~6h remaining). Watcher polls every 300s; progress
updates to server every 3rd poll. When count==0: launches ES_OPT → verifies → waits completion → downloads fresh
manifest → runs count query → updates both plan files → commits + pushes → calls `/done`. Log at:
`…/8e0e0b20-3e7a-42f5-a2dd-ef603f9b296e/scratchpad/es_opt_watcher.log`.

### 2026-08-07T~06:14Z — slot 11, session 6 — watcher re-armed (run_in_background: true, per RULES.md)

**Status: IN FLIGHT — todo #2 still `[ ]`. Watcher PID 2367038 (session 5, setsid) DEAD at boot check.** Fleet at
session-6 boot: **33 VMs** — new NASDAQ/NYSE 2023-2025 + CME wave launched ~06:00Z; lock held continuously per the
operator-approved keep-waiting decision.

**Root-cause diagnosis (sessions 3–5):** All three watcher approaches (harness task / nohup+& / setsid) died mid-sleep
with zero FATAL log entries. Working hypothesis: the harness sandbox kills by process group on tracked-task teardown
when the launching tool-call wrapper exits; `setsid` creates a new PGID but the sandbox may also send SIGKILL via PID
directly (not just PGID) to children of exited tracked tasks. Confirmed solution: **use `run_in_background: true`** per
RULES.md HARD RULE ("the harness's own backgrounding keeps the process correctly parented … and its exit is the tracked
wake") — this registers the background job with the harness as an OWNED task, not an orphan-reapable process.

**Session 6 re-arm: `run_in_background: true` (Bash tool, no `nohup`/`&` wrapper).** Watcher script:
`deployment-service/scripts/vm/es-opt-backfill-watcher.sh` (committed `deployment-service@cab7f2d`). Scratchpad:
`/home/ubuntu/.claude-configs/orch-slot-11/cc-tmpdir/claude-1000/-home-ubuntu-unified-trading-system-repos--tabs-11/de9e9cdd-eaf0-4210-a43e-575c4fe333fd/scratchpad`.

**Harness task**: `b9iintlzz` (started 06:32:40Z, poll 1 = 33 VMs). Output file:
`…/de9e9cdd-eaf0-4210-a43e-575c4fe333fd/tasks/b9iintlzz.output`. Watcher log:
`…/de9e9cdd-eaf0-4210-a43e-575c4fe333fd/scratchpad/es_opt_watcher.log`.

- **NEXT ACTION (post-compact or fresh session):** (1) Check if todo #2 checkbox is `[x]` already (watcher may have
  auto-completed). (2) If `[ ]`, check `b9iintlzz.output` file for completion status. (3) If watcher still running
  (harness will notify on completion): wait for notification, then verify checkbox flip in git log. (4) If watcher
  failed or no harness notification arrives: re-arm with `run_in_background: true` (Bash tool, no `nohup`/`&`) from
  `deployment-service/scripts/vm/es-opt-backfill-watcher.sh` — set `SCRATCHPAD` to a fresh writable dir first. (5) Do
  NOT re-arm if watcher is running — singleton lock race risk.

### 2026-08-07T06:57Z — slot 8, session 7 — watcher re-armed

**Status: IN FLIGHT — todo #2 still `[ ]`. Watcher b9iintlzz (session 6, slot 11, `run_in_background:true`) died after
poll 3 at 06:42Z** — confirmed dead (output file ends at poll 3; session-6 task output ends there). Root cause: when the
slot-11 session ended, the harness killed its owned background task (b9iintlzz). This confirms `run_in_background:true`
keeps the task alive only for the duration of the OWNING Claude Code session; it does NOT survive inter-session
handoffs.

**Pattern (sessions 3–7): watcher always dies when the Claude Code session ends.** Each fresh session re-arms. This is
expected — the AO re-dispatches this task to a new slot each time, and the new session re-arms as NEXT ACTION.

**Fleet at slot-8 boot (2026-08-07T06:57Z): 23 VMs running** (down from 27 at session-6 poll 3 → 23 at slot-8 boot).
Fleet is still draining. Operator keep-waiting decision unchanged.

**Session 7 re-arm:** Modified watcher copy for slot 8:
`…/e72382bd-a3d1-416a-ae84-85656714dec1/scratchpad/watcher/es_opt_watcher_slot8.sh` (SLOT_ID=8, SLOT_TABS=.tabs/8,
PYTHON=.tabs/8/market-tick-data-service/.venv/bin/python). Launched with `run_in_background:true`. Harness task:
**`baz81km0n`** (started 06:57:36Z, poll 1 = 23 VMs at 06:57:37Z).

- **NEXT ACTION (fresh session):** (1) Check if todo #2 checkbox is `[x]` (watcher auto-completed). (2) If `[ ]`, check
  harness task output: `…/e72382bd-a3d1-416a-ae84-85656714dec1/tasks/baz81km0n.output`. (3) If watcher still running,
  wait for harness notification. (4) If watcher dead and task not done: re-arm from
  `deployment-service/scripts/vm/es-opt-backfill-watcher.sh` — create modified copy with SLOT_ID=<new-slot>,
  SLOT_TABS=.tabs/<new-slot>, PYTHON=.tabs/<new-slot>/market-tick-data-service/.venv/bin/python — and launch with
  `run_in_background:true`. Verify poll 1 in output before updating progress log. Do NOT re-arm if watcher running.

## Codex SSOTs

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/05-infrastructure/vm-launcher-runbook.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.
