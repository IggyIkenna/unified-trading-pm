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
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, market-tick-data-service, deployment-service, instruments-service, unified-api-contracts]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-6, satellite-docs, conflict-checked]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch5_2026_07_29_finalize.md,
    /plans/active/instruments_tradfi_g1_g5_gate_execution_2026_07_24.md,
    /plans/active/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md,
    /plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-01"
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
---

# TradFi satellite AO batch 6 — fresh audit extraction

> **Status: draft — NOT approved, NOT dispatched.** Per the ag-closeout-audit skill's autonomous-mode contract, a
> freshly-drafted batch always ships `status: draft` regardless of how clean the conflict-check came back; flipping to
> `active` to actually dispatch it is an operator decision, never autonomous.
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

## Codex SSOTs

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/05-infrastructure/vm-launcher-runbook.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.
