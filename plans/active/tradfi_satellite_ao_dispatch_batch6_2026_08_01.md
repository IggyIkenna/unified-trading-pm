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
    /plans/archive/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md,
    /plans/active/issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
last_updated: "2026-08-08"
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
effort: max
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

- [x] [DATA] P2. **Historical manifest repair for the 2026-07-27T16:46:40-48Z registration burst's null-id rows.** 3,612
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

- [ ] [DATA] P0. **UNBLOCKED 2026-08-09** — S&P options are explicit in-scope work per the MVP-of-MVP ruling
      (/plans/active/issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md); Databento live-verified reachable
      the same day. If a watcher session for this launch is still alive, confirm it's actually making progress (not
      stuck behind the unrelated FX/commodity fleet's rate-limit contention — see the scope-ruling doc's "known relaunch
      gotchas") before assuming it's fine. **Launch the ES_OPT backfill, then wire its post-launch manifest-verify into
      Phase-D gate tracking (combined into ONE todo — the second step only makes sense once the first lands).** (1)
      Re-verify the singleton lock is still clear immediately before launch
      (`gcloud compute instances list --filter='name~"^tradfi-bf-"'`) — live-verified clear 2026-08-01, but re-check at
      execution time per the async-wait-and-poll-discipline norm, then run
      `bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh --root-symbol ES_OPT` (defaults: SPOT
      provisioning per the backfill-VM-defaults-to-SPOT HARD RULE; year-shards 2022-2026 per `cme-expiry-calendars.sh`'s
      `default_years_for_root`; `data_types=ohlcv_1m` only). This is a standard, idempotent, SPOT-default backfill-VM
      launch — no delete, no `--apply`, no `[OPERATOR]` tag needed (safe-idempotent justification per `task_template.md`
      finding O: shards simply re-run on preemption). Done when: the VM(s) are STARTED (<60s) + confirmed RUNNING at
      T+10min, per async-wait-and-poll-discipline (no fire-and-forget). (2) Once launched and complete, run the same
      manifest-count-only check used for ES futures (mirrors the NASDAQ/NYSE precedent,
      `data_completion_tradfi_2026_07_15.md`) scoped to venue=CME × data_type=ohlcv_1m × instrument_type=options_chain ×
      **`underlying in (SP500, ES)`** — **CORRECTED 2026-08-09 (see 2026-08-09T~08:38Z Progress Log entry below)**: the
      original `root∈{ES,EW,EW1,...,EOM}` instrument_id filter was wrong (matches zero real rows — the writer keys every
      ES_OPT variant to one aggregate `underlying=SP500` chain shard, not per-root ids) and would have returned 0
      forever; fixed in `es-opt-backfill-watcher.sh` (`deployment-service@be6d4669`). Record the result as a line item
      in `plans/active/tradfi_consolidated_closeout_2026_07_18.md`'s MVP-cell table, "S&P index options" row. Repos:
      deployment-service, unified-trading-pm. **Done when**: the VM(s) ran to completion across all target years (2025
      is currently the one confirmed 0%-coverage gap — see 2026-08-09T~08:38Z entry — not just "ran once"), the
      manifest-count check result is recorded with real query + counts, and the MVP-cell table row is updated. Source:
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

- [x] ✅ [DATA] P2. **Reconcile the `BASE_ASSET`/manifest `underlying` string-naming drift found incidentally during the
      2026-07-28 within-bounds-source-zero cross-check.** `HEATING-OIL`/`HEATINGOIL`/`HO`,
      `NAT-GAS`/`NAT-GAS-HH`/`NATGAS`, and similar variants disagree between `BASE_ASSET` and the manifest's actual
      stored `underlying` string. Determine whether this drift causes any real denominator/accounting issue (per the
      source doc's own conditional framing — "if it is found to cause its own... issues"); if yes, propose and apply the
      reconciliation; if no, close this item with the negative evidence recorded rather than leaving it open
      indefinitely. Repos: market-tick-data-service, unified-api-contracts. **Done when**: either the drift is fixed
      with regression coverage, or it is confirmed harmless with the specific check that proved it (e.g. a
      denominator/count comparison before vs. after normalizing the strings). Source:
      `issues/tradfi_within_bounds_source_zero_shard_atom_mismatch_2026_07_28.md` (todo 3). —
      **market-tick-data-service@b63200a7**. Investigated first (not blindly re-fixed): this exact drift class
      (`HEATING-OIL`/`HEATINGOIL`, `NAT-GAS`/`NAT-GAS-HH`/`NATGAS`, etc.) was already root-caused + reconciled on the
      enumerator/expected-universe side 2026-07-28
      (`/plans/archive/issues/tradfi_combo_underlying_naming_mismatch_blocks_g1_enum_present_rollup_2026_07_28.md`,
      resolved) via a new `unified_api_contracts.resolve_tradfi_underlying_to_root()` reverse-lookup, real production-
      quantified (503,588 → 503,588 `expected_unattempted`, 0 change — confirmed HARMLESS on that specific surface, the
      negative-evidence branch of this todo's own done-when). BUT the retirement/migration script this todo's source
      doc's own dry-run measured against
      (`market-tick-data-service/scripts/retire_tradfi_cf11_bundle_grain_shard_atom_mismatch_2026_07_30.py`) does its
      own SEPARATE, un-normalized `base_asset` string comparison and was NOT wired to the shipped resolver — its own
      2026-07-30 dry-run explicitly attributed part of its 32,864-row CME unresolved residual to "the already-
      documented commodity-symbol naming-drift tail," i.e. this drift DOES cause a real accounting gap on that surface
      (false-negative matches: real captured twins missed due to naming-variant mismatch). Fixed: normalized both the
      crosswalk's `base_asset` and the captured manifest's raw `underlying` column through the same shipped
      `resolve_tradfi_underlying_to_root()` before the key comparison (fallback to raw value if unresolved — never
      guessed), so recognised variants now correctly collide. 3 new regression tests
      (`test_commodity_naming_drift_variant_still_matches_captured_twin`,
      `test_commodity_naming_drift_hyphenated_spelled_form_still_matches`,
      `test_genuinely_unresolvable_underlying_falls_back_unchanged_not_guessed`) — 12/12 tests green, `quality-gates.sh`
      full green. Not re-run: the live 6M-row production dry-run to measure exactly how much of the 32,864 residual this
      recovers — the retirement script's own `--apply` is still operator-gated pending a fresh go-ahead per its existing
      operator-review gate; that re-measurement naturally happens as part of that already- tracked gate, not a new todo.

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

### 2026-08-06 → 2026-08-08T18:22Z — ES_OPT watcher saga (condensed; ~25 sessions across 10+ slots)

**Condensed 2026-08-08T21:53Z (slot 28) — the full session-by-session narrative below was getting the plan doc's line
count close to the 1000-line hard cap; condensing to the durable lessons + latest state per session, dropping the
redundant per-poll fleet-count play-by-play (each entry repeated the same "re-armed watcher X, poll 1 = N VMs" shape ~20
times). Full narrative recoverable via `git log -p` on this file if ever needed.**

**What this todo is waiting on**: the ES_OPT backfill launch (`launch-tradfi-backfill-vm.sh --root-symbol ES_OPT`) is
gated on the account-wide Databento singleton lock, held continuously since 2026-08-06 by a large, self-replenishing
NASDAQ/NYSE/CME OHLCV backfill campaign (`tradfi-bf-*` VMs). The operator was asked directly 3 times (2026-08-06, with
real ETA numbers each time) whether to `--force` launch anyway; the answer was **KEEP WAITING, no `--force`** each time,
most recently after being shown that the campaign is continuous-launch (replenishes as VMs finish, no natural count==0
window). This decision has not been revisited since and should NOT be re-asked absent a material change (e.g.
operator-initiated contact, or the campaign genuinely ending).

**Standing mechanism**: a background watcher script (`deployment-service/scripts/vm/es-opt-backfill-watcher.sh`,
committed) polls `gcloud compute instances list --filter='name~"^tradfi-bf-"'` every 300s; on count==0 it launches
ES_OPT, verifies T+30s/T+10min, waits for the 5 ES_OPT VMs to finish, downloads a fresh manifest, runs a pyarrow
column-pruned count query (venue=CME × ohlcv_1m × instrument_type=options_chain × the 11 canonical ES_OPT
instrument_ids), updates both this plan's checkbox and the closeout plan's MVP-cell row, commits+pushes, and calls
`/done` — fully autonomous once the lock clears. A companion heartbeat loop pings `/api/slots/<N>/heartbeat` every 5-20
min so the slot doesn't read as stale/dead while otherwise idle. Every fresh session's job is simply: check if the
watcher is still alive, and if not, re-arm it (sed-patch `SLOT_ID`/`SLOT_TABS`/`PYTHON` for the new slot) — the watcher
is idempotent and resumes from live fleet state.

**Durable lessons (accumulated 2026-08-06 → 2026-08-08, apply to any future watcher-pattern session)**:

1. **`nohup cmd &` alone does NOT survive a launching-tool-call teardown.** It reparents to init (PPID=1) but stays in
   the SAME process group as the invoking shell under non-interactive bash — a PGID-based cleanup sweep can still kill
   it (confirmed: 2 instances died silently mid-`sleep 300`, zero FATAL log entry, which rules out an internal bug).
   Fix: `setsid nohup bash script.sh > log 2>&1 < /dev/null & disown`, then verify via
   `ps -o pid,ppid,pgid,sid -p <pid>` that **PGID and SID both equal the process's own PID** (PPID=1 alone is
   insufficient proof).
2. **util-linux `setsid` without `-f` forks internally**, so `$!` in the launching shell captures the WRONG (short-
   lived wrapper) pid. Always resolve the real PID via `ps -ef | grep '<script path>' | grep -v grep`, never `$!`.
3. **`run_in_background:true` (harness-tracked Bash) survives `/compact` but NOT session death** — when the owning
   Claude Code session ends, its harness-owned background tasks die with it. This is expected under the one-task-per-
   session dispatch model: a fresh session re-arms as its first action. The harness also periodically kills
   `run_in_background:true` tasks proactively (~25-46 min cadence observed, suspected tied to context-compaction
   triggers) — this is normal; re-arm reactively on each kill notification, don't treat it as a bug.
4. **`TaskList` does NOT show harness background Bash tasks** — it always returns "No tasks found" for them. Use
   `TaskOutput <task_id> --non-blocking` with the KNOWN task id instead.
5. **Dual-watcher race (real incident, 2026-08-08T~11:10Z, slot 6)**: re-arming reactively off a
   `task-notification: killed` event WITHOUT first confirming the notified task-id still matches a live PID can create a
   SECOND live watcher+heartbeat pair racing the first — both would race to launch ES_OPT and commit the plan-flip the
   moment the lock clears (risk: double-launch, wasted SPOT spend, and/or a git push race on this same plan file). Fix +
   standing discipline: before ANY re-arm, run `ps -ef | grep es_opt_watcher | grep -v grep` — if more than one
   `bash .../es_opt_watcher_*.sh` process appears, keep the older one (earliest `lstart`) and kill the newer duplicate
   pair by **exact PID** (never a name-pattern `pkill`, per RULES.md). After a dedup-kill, the survivor is untracked by
   any harness task-id — use `kill -0 <pid>` for liveness from then on, not `TaskOutput`.
6. **`gcloud ... | wc -l` silently reports 0 on a transient gcloud error** (empty stdout on rc!=0 looks identical to a
   genuine empty result). The watcher's poll loop is error-aware (checks rc==0 AND empty explicitly) — preserve this in
   any hand-rolled check.
7. **A `ScheduleWakeup` confirmation's stated wake time is a FUTURE fire time, not "now"** — don't conclude a watcher
   log gap is stale without running `date -u` directly first (a false "26 min since last poll" alarm was actually a
   ~90s-old entry once real UTC time was checked).
8. **`localhost:8765` (the AO server) transient connection-refused/timeout errors are expected under shared-host load**
   — retry once with a slightly longer timeout before treating it as a real outage or escalating.

**Fleet trajectory summary**: the campaign has run in discrete waves since 2026-08-06T08:00Z, each wave adding 10-40+
VMs as prior waves drain, with the fleet oscillating between single digits and 100+ VMs — it has NEVER reached 0 as of
the last checkpoint (2026-08-08T18:22Z, 134-142 VMs, still draining/refilling). No natural clear window has occurred in
2.5 days of continuous observation across ~25 sessions.

### 2026-08-08 — slot-7, task `tradfi_satellite_ao_dispatch_batch6-001` (todo #1) — DONE

**1. ✅ [DATA] P2 (todo #1) — historical manifest repair** — resolved via before/after manifest census +
non-recoverability determination. Live manifest read (6,837,762 rows, column-pruned census script,
`run-bounded-analysis.sh` RSS-poll-capped): **BEFORE** = 3,712 null-id rows; **AFTER** = 0 null-id rows in burst window
(both phantom-purge-overlap 16:46:38-42Z and post-purge 16:46:42-50Z return zero).

Non-recoverability recorded for all 3,712 rows:

- **CBOE INDEX ohlcv_15m (100 rows)**: dead cell — `reclass_tradfi_cboe_ohlcv_15m_dead_cell_2026_07_29.py` confirms
  Databento never offered ohlcv_15m for CBOE INDEX (stale from retired Yahoo VIX-cash-index; narrowed out of expected
  coverage 2026-07-15, `unified-api-contracts@78b9e899`); phantom purge removal was correct data hygiene.
- **NASDAQ/NYSE equity/ETF ohlcv_1m/trades (3,612 rows)**: data confirmed covered by canonical captured entries — 97,242
  NASDAQ + 848,622 NYSE rows, non-null instrument_ids, 830 dates (2023-04-17..2026-07-20), 133+1,049 instruments. Burst
  rows were duplicate registrations of data the live writer captured correctly with canonical ids.

Side-finding (out of scope): 149 new CBOE INDEX ohlcv_24h `empty_confirmed` null-id rows written 2026-08-07 — separate
population. Source issue resolved + checkbox flipped:
`plans/archive/issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md` (all todos done, status=resolved). No
code changes required; quality-gates.sh green (no code modified).

## Codex SSOTs

`/codex/02-data/tradfi-databento-sourcing-ssot.md`, `/codex/02-data/availability-manifest-and-data-status.md`,
`/codex/05-infrastructure/vm-launcher-runbook.md`,
`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md`.

### 2026-08-08T21:53Z — slot 28 — watcher re-armed (bztaf4c8p)

**Status: IN FLIGHT — todo #2 still `[ ]`.** Prior watcher `703695`/heartbeat `703746` (slot 6, ~18:22Z checkpoint)
found DEAD at boot (`kill -0` on both PIDs failed; `ps -ef | grep es_opt_watcher` returned no matches — clean, no
dual-watcher race). Fresh-pulled all 25 slot repos to `origin/live-defi-rollout` first (all FF, clean). Direct
`gcloud compute instances list --filter='name~"^tradfi-bf-"'` confirmed **146 VMs running**, 0 ES_OPT VMs exist.
Operator keep-waiting decision unchanged, no `--force`.

Re-armed from committed `deployment-service/scripts/vm/es-opt-backfill-watcher.sh` (sed-patched SLOT_ID=28,
SLOT_TABS=.tabs/28, PYTHON=.tabs/28/market-tick-data-service/.venv/bin/python — slot 28 has its own mtds venv). Watcher:
**`bztaf4c8p`** (`run_in_background:true`, no `&` inside), poll 1 confirmed = 146 VMs (21:53:32Z, matches direct check).
Heartbeat: **`bheikwhqr`** (5-min interval loop, no `&` inside). Scratchpad path omitted — session-specific, does not
survive past this session; superseded entries below carry forward the actually-current state.

- **NEXT ACTION — SUPERSEDED, do not follow this block.** This watcher-arming approach and everything in this entry's
  original scratchpad references are obsolete: all ES_OPT VMs eventually died to a separate issue (see the
  2026-08-09T~03:51Z entry far below), the fix for the launch-blocking bug has since shipped
  (`deployment-service@c99ab99b8`), and the watcher/background-process approach was abandoned in favor of direct bounded
  polling later the same session. Skip to this doc's LATEST entry for the real current state and NEXT ACTION.

**Update 2026-08-08T22:30Z (same slot-28 session)**: `run_in_background:true` hit the documented rapid-kill pattern 3×
in ~2 min this session (bztaf4c8p, bj0u96s11, bwjx735ic — each killed within ~30-90s, far faster than the 25-46min
cadence seen in most prior sessions). Switched to `setsid nohup ... & disown` (the same fix already proven to survive 7+
hours unattended in the slot-6/`703695`/`703746` lineage). Current live pair, genuinely isolated (confirmed PGID=SID=PID
for both, per the standard verification): **watcher PID `3762433`, heartbeat PID `3762556`** (started 22:30:37Z, poll 1
= 157 VMs). A fresh session picking this up should check these PIDs first via `kill -0` before assuming dead / re-arming
— though note this whole watcher lineage is now moot, see the SUPERSEDED note two entries above and the doc's latest
entry for current state.

**Update 2026-08-08T22:38Z (same slot-28 session) — setsid pair also died, ~7 min after launch, no FATAL entry.**
Watcher `3762433`/heartbeat `3762556` found DEAD (both `kill -0` failed) after only reaching poll 2 (22:35:41Z, 154 VMs)
— this contradicts the slot-6 precedent of 7+ hour setsid survival. No FATAL in either log; death was silent, same
signature as the earlier PGID-cleanup theory, but PGID=SID=PID was verified correct for this pair at launch, so that
specific mechanism is ruled out here. Working theory (unconfirmed): this interactive session received several rapid
operator "proceed now" nudges in close succession, and the ~5-7min survival window correlates more with elapsed
_nudge-to-nudge_ time than with any process-group mechanism — possibly a sandbox/session-boundary teardown independent
of setsid. Re-armed immediately: **watcher PID `4017297`, heartbeat PID `4017373`** (both PGID=SID=PID re-verified,
started 22:38:08Z, poll 1 = 154 VMs). **Open question for a future session**: if this pair also dies on a similar
timescale, the setsid approach may not be reliable in this environment either, and the only real answer may be accepting
reactive re-arm on every check-in (whatever the trigger) rather than expecting either mechanism to survive unattended
for long stretches.

**Update 2026-08-08T22:50Z (same slot-28 session) — confirmed: no background mechanism survives in this session;
switched to bounded synchronous polling.** The 4017297/4017373 setsid pair was ALSO found dead (`kill -0` failed on
both) immediately after an 8-minute _foreground_ poll window — meaning ALL THREE background approaches tried this
session (`run_in_background:true`, plain re-arm, `setsid nohup … & disown`) failed to survive more than a few minutes,
unlike the slot-6 lineage's 7+ hour survival. Root cause not confirmed, but no longer worth chasing — **switched
strategy**: ran an 8-minute bounded synchronous poll loop directly in the foreground
(`timeout 480 bash -c 'while true; do gcloud …; sleep 60; done'`, error-aware, same rc==0-AND-empty check as the watcher
script) instead of depending on a detached background process. This is reliable (I directly observe every poll) at the
cost of consuming turn time. Result: fleet stable at 153 VMs across 8 polls (22:42Z-22:49Z), lock still held.
**Recommended approach for future sessions in this environment**: don't rely on background watchers surviving between
check-ins — instead, run a bounded (~8min, safely under the 10min Bash timeout) synchronous poll loop each time the
session is active, and accept that coverage has gaps between sessions (as it always has across this saga's ~25+
sessions) rather than assuming either `run_in_background` or `setsid` closes those gaps unattended.

### 2026-08-08T23:32Z — slot 28, same session — 48min direct-poll session summary + final re-arm before standby

Ran 6 consecutive 8-minute bounded synchronous poll windows (48 min total, 48 individual polls, zero gaps) after the
background-mechanism failures documented above. Fleet trajectory: 154→153→152→149→147→146 VMs, essentially flat/
slow-draining, consistent with this campaign's documented multi-day continuous-launch pattern — **no genuine count==0
window observed**. Diminishing returns on continuing to poll synchronously (no-sawtooth polling discipline) — returning
to standby. Re-armed one more background pair as a safety net (may or may not survive, per the finding above): **watcher
PID `1501267`, heartbeat PID `1502659`** (`setsid`, started 23:32Z). Operator sent 3 "proceed now" nudges this session;
none treated as a force-launch instruction (per the standing keep-waiting decision, reconfirmed explicitly multiple
times earlier in this saga and not revisited since).

- **NEXT ACTION (fresh session)**: (1) Check todo #2 checkbox — if `[x]`, done. (2) If `[ ]`, check
  `kill -0 1501267`/`kill -0 1502659` for liveness (may well be dead per this session's findings — that's expected, not
  alarming). (3) If dead: either re-arm the same way, or just run an 8-min bounded synchronous poll
  (`timeout 480 bash -c '...'`, see the loop shape above) — both are legitimate; the synchronous poll is the more
  reliable one in this environment based on this session's evidence. (4) Dedup-check via `ps -ef` before any re-arm,
  regardless of method.

### 2026-08-09T~00:22Z — slot 28, same session — extended continuation (~1.5h total), new wave confirmed, still waiting

Continued past the prior checkpoint with more re-arm cycles (watcher/heartbeat pairs `1706749`/`1707140` and others,
same intermittent-survival pattern as documented — sometimes minutes, sometimes longer) plus additional 8-min bounded
synchronous poll windows totaling well over an hour of direct observation since session start (21:53Z). Fleet trajectory
this stretch: 145→144→143 (flat ~16min) → real drain 143→139 → **new wave launched 139→156 VMs** (00:14Z-00:22Z),
confirming the continuous-launch/self-replenishing pattern is still active — the campaign has not shown a genuine
count==0 window at any point across this entire session. Operator sent 10+ "proceed now" nudges over this stretch; none
treated as a force-launch instruction — each was verified against live state and reported, per the standing keep-waiting
decision (unchanged since its last explicit reconfirmation earlier in this saga).

- **NEXT ACTION (fresh session)**: same as the prior checkpoint's NEXT ACTION — check checkbox first, then liveness of
  whatever the most recent PIDs are (see this session's git history for the latest pair if picking this up immediately),
  re-arm or poll-directly as needed. No new lessons beyond what's already captured above.

### 2026-08-09T~01:47Z — slot 28, same session — ~2h mark, new fleet peak (167 VMs), still waiting

Continued the 8-min bounded synchronous poll pattern through several more windows since the prior checkpoint (~01:39Z
onward), driven by explicit operator "send a /heartbeat and continue" instructions each cycle. Fleet trajectory:
150→149→143→134 (real drain) → **new wave 134→168 VMs** (01:28Z-01:39Z) → plateaued at **167 VMs**, the largest fleet
size observed across this entire ~2h session (prior peak was 156-163 in earlier stretches, per the condensed saga
summary at the top of this section). Singleton lock remains continuously held; still zero genuine count==0 window across
~2h of this session's direct observation (on top of the ~2.5 days already documented before this session started). No
change in operating posture: not force-launching, continuing to verify-and-report each check-in.

- **NEXT ACTION (fresh session)**: same as all prior checkpoints in this saga — check checkbox first (if `[x]`, done and
  this whole watch is over); if `[ ]`, verify current fleet state directly
  (`gcloud compute instances list --filter='name~"^tradfi-bf-"'`) and either re-arm a background watcher or run a
  bounded synchronous poll loop, whichever is available/preferred at that time. No lessons beyond what's already
  captured in this doc's condensed saga summary + the background-mechanism-unreliability findings above.

### 2026-08-09T~02:36Z-03:16Z — slot 28, same session — LOCK CLEARED, ES_OPT LAUNCHED (with a real bug found+fixed en route)

**Status: IN FLIGHT — todo #2 still `[ ]` but genuinely progressing now** (VMs actively backfilling, not just waiting).

**The lock cleared for real at 02:36:11Z** (8-min poll loop caught `count=0`). Immediately re-verified + launched
`bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh --root-symbol ES_OPT` → 5 VMs (2022-2026), all
confirmed RUNNING within seconds. **But the clear was NOT organic completion** — `gcloud compute operations list` showed
the ~150-VM prior fleet was mass-`delete`d in a synchronized burst right before the clear. This is now explained: a
separate operator-directed interactive session filed `issues/tradfi_mvp_of_mvp_instrument_scope_ruling_2026_08_09.md`
the same day, narrowing immediate TradFi scope and explicitly killing the entire out-of-scope FX/commodity
`tradfi-bf-cme-ohlcv-1m-g0{1,2,3}-*` fleet (167 VMs, massively duplicated per that doc's own finding) — **not a bug, not
a billing kill-switch, a deliberate scoped kill**. ES_OPT is explicitly IN-SCOPE per that same ruling ("S&P 500 options
— full 6.5-year history"), so this launch is correctly authorized. Also relevant:
`issues/tradfi_databento_account_billing_suspended_2026_08_09.md` had gated this exact todo `BLOCKED-OPERATOR-DECISION`
earlier the same day, then the scope-ruling doc recorded a live Databento API verification that lifted the gate for
in-scope items — consistent with the todo's own text already carrying an "UNBLOCKED 2026-08-09" prefix by the time this
session read it. **Minor staleness note**: the billing doc's own gate list still shows batch6 as gated (not yet
retagged) — not fixed here, out of scope for this session, flagged for whoever next touches that doc.

**Real bug found + fixed en route**: all 5 first-attempt ES_OPT VMs self-deleted within 2-4 minutes (0 data written).
Root-caused via `gcloud logging read` + a dedicated sub-agent: `launch-tradfi-backfill-vm.sh` set
`VM_TASK=cefi-backfill`, which matches **no dispatch branch at all** in `setup-data-pipeline-vm.sh` (stale copy-paste
from a cefi launcher) — every VM fell through to the generic fallback, which never builds `--source`, so MTDS
hard-failed instantly ("--source databento is REQUIRED") and the VM self-deleted via its own `VM_SHUTDOWN_ON_COMPLETION`
convention. NOT an external killer, NOT related to the mass-delete above (different SA: `uts-prd-sa` self-delete, vs.
the scope-kill's own actor). Fixed: `VM_TASK=mtds-backfill` + `VM_SOURCE=databento` (mirrors the identical fix already
shipped in `launch-tradfi-forward-poll.sh`). Committed `deployment-service@6b1057cc`, QG running in background
(`bx6e0j6l1`, pytest still in progress at last check — will ship via quickmerge once green). Filed
`issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` (pushed `PM@7759cd2f3`) — full
evidence + 3 follow-up action items (verify-to-completion tracked there but not duplicated here; audit whether
BTC/ETH/other callers hit the same bug; wire `VM_FORCE_WINDOW` into the `mtds-backfill` branch).

**Re-launched with the fix** (03:08:39Z-03:09:52Z, all 5 VMs `tradfi-bf-es-opt-light-{2022..2026}-202608090308-52`):
confirmed via serial console (`VM_TASK=mtds-backfill` in the actual boot log) + run.log
(`Chunk 1/53: 2022-01-01 → 2022-01-07`, real venue processing, no `--source` error, RSS ~8.4GB / CPU 100% — genuine
work) that all 5 are past the previous failure window and actively backfilling. 53 chunks/year × 5 years — this will
take hours, not minutes.

- **NEXT ACTION (fresh session)**: (1) Check todo #2 checkbox — if `[x]`, done. (2) If `[ ]`, check
  `gcloud compute instances list --filter='name~"^tradfi-bf-es-opt-"'` — if VMs still RUNNING, they're mid-backfill,
  just monitor (no action needed, they self-delete + the manifest-verify step still needs a worker to run it after). If
  VMs are gone (all self-deleted, presumably on completion), proceed to phase 2: download a fresh manifest, run the
  count query (venue=CME × ohlcv_1m × instrument_type=options_chain × the 11 canonical ES_OPT instrument_ids — see the
  Phase 2 section far above in this doc's condensed saga summary for the exact query shape), update the MVP-cell table
  in `tradfi_consolidated_closeout_2026_07_18.md`, flip this todo's checkbox, commit+push, `/done`. (3) Check whether
  `deployment-service@6b1057cc` (the VM_TASK fix) has shipped via quickmerge yet
  (`git log --oneline -5 -- scripts/vm/launch-tradfi-backfill-vm.sh` on `deployment-service`) — if not, QG may still be
  running or need a retry; the issue doc's action items track this, not required for THIS todo's own completion since
  the fix is already committed locally and the launch already ran successfully off it.

### 2026-08-09T~03:51Z — slot 28, same session — all 5 ES_OPT VMs died, second real bug found; blocked again on the lock

**Status: IN FLIGHT — todo #2 still `[ ]`.** All 5 re-launched ES_OPT VMs (2022-2026) eventually died — NOT the
`--source` bug (fixed, confirmed working: real data was written, e.g. `venue=CME: 24180 rows written` for 2026 across
several trading days before it too died) — a SEPARATE issue: each VM went silent (both its own log AND its GCS heartbeat
sidecar froze at the same instant, suggesting the whole VM stalled, not just the process) ~15-23 min into a historical
date's fetch, then was externally deleted. Best-fit hypothesis: `vm_zombie_watchdog.py`'s external `--min-age`-gated
reaper (default 15 min) false-positive-classifying a legitimately slow-but-alive Databento fetch as dead — NOT the in-VM
`STALL_TIMEOUT_SEC` (confirmed actual default 1800s/30min, never hit). Not yet confirmed against the watchdog's own
audit trail — flagged as a P1 action item, not fixed this session. Full writeup + corrected hypothesis:
`issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md` (pushed `PM@ea685dd0f`).

**Also observed (unrelated to this todo, flagged separately, not acted on)**: a fresh ~25-VM `tradfi-bf-*` wave
(NASDAQ/NYSE 2023/2024 equities + CME ES/ETH/MBT/MET) is now running, holding the singleton lock again. The NASDAQ/NYSE
2023/2024 portion looks like it may violate the same-day scope ruling's "killed, not resumed" disposition for the legacy
fleet — filed as a passive-observation flag, not investigated or acted on:
`issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` (pushed `PM@4e7d14746`). This
means the lock is held again regardless of the zombie-watchdog issue — both blockers need to clear/resolve before ES_OPT
can be retried.

**Code fix status**: `deployment-service@6b1057cc` (the `VM_TASK`/`VM_SOURCE` fix) is committed locally and PROVEN
working (real data written), but has not yet landed via quickmerge — QG hit a timing-gate failure (1343s vs 600s limit)
due to extreme shared-host contention (load avg 63-67, 8+ concurrent QG runs observed), then a retry timed out at the
Bash tool's own 9m20s limit under the same contention. Not blocking THIS todo (the fix already works from the local
commit), but should land properly once host load drops — tracked in the issue doc, not re-tracked here.

- **NEXT ACTION (fresh session)**: (1) Check todo #2 checkbox — if `[x]`, done. (2) If `[ ]`, check
  `gcloud compute instances list --filter='name~"^tradfi-bf-"'` — if 0, the lock is clear: re-verify, then re-run
  `bash deployment-service/scripts/vm/launch-tradfi-backfill-vm.sh --root-symbol ES_OPT` (the fix is already on disk in
  every slot's `deployment-service` clone via `6b1057cc`, whether or not it's landed on origin yet — if a fresh slot's
  clone predates that commit, cherry-pick or re-apply the fix from the issue doc's diff first). (3) Expect the SAME
  zombie-watchdog death pattern to recur unless someone has fixed the P1 action item in the issue doc first — if it
  recurs, that's expected, not a new problem; re-launch is still the right move (idempotent), just don't expect a full
  5-year completion without that fix landing. (4) Check whether `deployment-service@6b1057cc` has shipped via quickmerge
  yet (`git log --oneline -5 -- scripts/vm/launch-tradfi-backfill-vm.sh`); if not and host load looks sane (`uptime`,
  want <20-ish), retry QG. (5) Separately, check whether either flagged issue
  (`tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md` or the zombie-watchdog P1 in the main
  issue doc) has been resolved by someone else — if the scope violation is confirmed+resolved, the lock may clear
  faster; if the zombie-watchdog is fixed, a retry should actually complete instead of dying again.

### context-scout

- **context-scout 2026-08-09**: populated/refreshed context_scope (6 entries).

## Deferred work after 2026-08-09 (slot-28 session, pre-compact)

| Item                                                                                                                                                                        | State                  | Blocked on                                                                                                                                                                                                                                                                                                                                               |
| --------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Todo #2 itself — complete the ES_OPT 5-year backfill + manifest-verify                                                                                                      | Cannot be done yet     | (a) singleton lock — held again at session end (12 `tradfi-bf-*` VMs, includes in-scope CME ES/ETH/MBT/MET + a flagged-possibly-out-of-scope NASDAQ/NYSE wave); (b) even once clear, a retry will likely hit the same zombie-watchdog death pattern (below) until that's fixed — expect partial-year completions, not a clean 5-year run, until it lands |
| Zombie-watchdog false-positive killing legitimately-slow ES_OPT fetches (P1, `issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`)        | Not done — real work   | Nobody; needs an INFRA-role investigation to confirm `vm_zombie_watchdog.py` is the actual actor (not yet traced, only timing-matched) then fix `--min-age` or add progress logging inside the fetch                                                                                                                                                     |
| Possible scope-ruling violation — legacy NASDAQ/NYSE 2023/2024 fleet relaunched (P2, `issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`) | Operator/context-owned | Someone with fuller context on who launched it and why — do not kill without the 3-signal staleness check + confirming it's genuinely unauthorized                                                                                                                                                                                                       |
| Audit whether `VM_TASK=cefi-backfill` bug hit other `launch-tradfi-backfill-vm.sh` callers (BTC/ETH tier-plan, ad-hoc mode) (P2)                                            | Not done — real work   | Nobody; bounded investigation, same issue doc as above                                                                                                                                                                                                                                                                                                   |
| Wire `VM_FORCE_WINDOW` into the `mtds-backfill` dispatch branch (P3)                                                                                                        | Not done — real work   | Nobody; low-priority, same issue doc                                                                                                                                                                                                                                                                                                                     |

**Recommended next item**: check the singleton lock first
(`gcloud compute instances list --filter='name~"^tradfi-bf-"'`) — if genuinely clear, re-launch ES_OPT immediately (the
fix is live on `origin/live-defi-rollout` now, no local-only dependency), since that's the highest-value, most
time-sensitive action (the lock won't stay clear long, per this whole saga's history). The zombie-watchdog fix is the
actual unblock for a CLEAN completion, but it's a deeper INFRA investigation better suited to a dedicated session/role,
not something to block a re-launch attempt on.

### 2026-08-09T05:54Z — slot 22 — watcher re-armed, lock still held (6 VMs, smaller fleet)

Fresh session, task `tradfi_satellite_ao_dispatch_batch6-f9921af83ce2`. Direct check + 8-min bounded synchronous poll:
lock held steady, **6** `tradfi-bf-*` VMs (CME ES/ETH/MBT/MET + 1 NYSE-2024 shard, all ~2.2-2.6h old at check time),
zero drain across the window — down from the 12+ at the prior checkpoint but not clear. 0 ES_OPT VMs running.
`deployment-service`'s VM_TASK/VM_SOURCE fix confirmed already landed on origin (`c99ab99b`, `acf965d9` — no local-only
dependency for a fresh clone). Zombie-watchdog P1 fix and the scope-violation doc are both still open/unresolved,
unchanged from the prior checkpoint.

Re-armed via the `setsid nohup … & disown` pattern (the one with a proven multi-hour survival precedent earlier in this
saga): **PID `2092980`**, verified isolated (PGID=SID=PID), sed-patched for slot 22. **Note for whoever next re-arms
this script**: the committed `es-opt-backfill-watcher.sh`'s hardcoded
`TASK_ID="tradfi_satellite_ao_dispatch_batch6-002"` is stale — live backlog task ids now carry a hash suffix (this
session's was `-f9921af83ce2`, not `-002`); always re-check the CURRENT task id from your own `/boot` response before
re-arming, don't trust the committed default.

- **NEXT ACTION (fresh session)**: same as every prior checkpoint — check todo #2's checkbox first; if `[ ]`, check
  `kill -0 2092980` for liveness (may be dead, that's expected/normal per this saga's findings); if dead, re-arm per the
  recipe above with your OWN current task id.

### 2026-08-09T~06:08Z-07:59Z — slot 22, same session — root cause found+fixed elsewhere, out-of-scope fleet fully

drained, in-scope CME converging

**Status: IN FLIGHT, genuinely converging now.** The 18-VM peak (6:08Z checkpoint) traced to `wave_launcher.py`, an
hourly `--force` cron on `planning` ignoring the scope ruling — root-caused + the runaway process killed by another
session (`issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`, not this session's work,
cross-linked here for continuity). Confirmed no re-growth since. Fleet drain observed directly: 18 → 9 → 8 → **7** (all
in-scope CME ES/ETH/MBT/MET; the entire out-of-scope NASDAQ/NYSE wave self-completed and drained to 0 on its own — no
kill needed). Remaining 7 are a mix of ~4.8h-old originals + ~1.9h-old cron-duplicated siblings (same symbol+year
running twice, wasteful but not this task's concern to fix).

**Watcher lineage this session**: PID 2092980 (05:54Z, died ~5min) → PID 2908332 (06:18Z, survived **1.5+ hours**,
noticeably better than every earlier attempt this session, died sometime before 07:58Z) → PID **1059819** (07:58:39Z,
current, verified isolated). `run_in_background` watchdogs continue to die almost immediately (~1min, confirmed twice) —
not worth re-arming those; relying on the setsid watcher + periodic direct `gcloud` checks instead. **Lesson reinforced
this cycle**: a ~1h40m real-time gap occurred between two consecutive tool calls in this session with no indication at
the time — always run `date -u` fresh before reasoning about elapsed time or watcher-death likelihood, per this doc's
existing lesson #7.

- **NEXT ACTION (fresh session)**: check todo #2 checkbox first. If `[ ]`: check `kill -0 1059819`; if dead, re-arm
  (recipe near the top of this saga, remember the CURRENT task id, not a stale one). Direct check:
  `gcloud compute instances list --filter='name~"^tradfi-bf-"'` — trend is DOWN, likely to clear soon if it keeps going,
  but don't assume the exact rate holds.

### 2026-08-09T~08:38-09:20Z — slot 22, fresh session (task `tradfi_year_shard_backfill_launcher_missing_source_self_deletes-7b183e5e4109`) — manifest query was broken (false 0-row absence), true gap is much narrower than assumed

**PID 1059819 (previous session's watcher) was DEAD at boot** (`kill -0` failed). Instead of re-arming it, found a
DIFFERENT slot (21) already running its own wait-for-lock-then-launch watcher (`wait_and_launch_es_opt.sh`,
`run_in_background`, 90-min bound, started ~08:37Z) — did NOT start a competing watcher (dual-watcher double-launch
race, lesson #5 above); left the launch responsibility to slot 21 and focused on a different, real bug instead.

**Found and fixed: the manifest count-check query (this todo's own "Done when" criteria, `es-opt-backfill-watcher.sh`
Phase 4) was broken and would return 0 rows forever.** It filtered `instrument_id in [CME:OPTION:ES, EW, EW1, ..., EOM]`
— an 11-item list confirmed (via grep) to appear nowhere else in the codebase, not a real registry. The writer
(`partitioned_writer.py:71`, `_tradfi_chain_partition_dims`) actually keys every ES_OPT variant to ONE aggregate chain
shard, `underlying=SP500` / `instrument_id=CME:OPTION:SP500` (`reader.py:362-368`). My first manifest query attempt hit
exactly this false-0 trap before I caught it via a broader unfiltered probe. Fixed: `deployment-service@be6d4669` (QG
green ~280s, landed + ancestry-verified on origin). Todo text above corrected to describe the right filter.

**Re-ran the CORRECTED query against a fresh manifest pull — true state is far better than "all 5 died" implies:**

| Year | Distinct dates | Dates with real data | Coverage |
| ---- | -------------- | -------------------- | -------- |
| 2020 | 267            | 253                  | 94.8%    |
| 2021 | 252            | 252                  | 100.0%   |
| 2022 | 251            | 251                  | 100.0%   |
| 2023 | 250            | 250                  | 100.0%   |
| 2024 | 253            | 252                  | 99.6%    |
| 2025 | 251            | **0**                | **0.0%** |
| 2026 | 204            | 149                  | 73.0%    |

1,407/1,728 distinct dates (81.4%) already have real data, 7.39M total OHLCV bars. Cross-checked `attempted_at`
timestamps: most of 2021-2024's coverage predates today entirely (not from either of today's 2 failed `es-opt` launches)
— most likely incidental capture from the concurrent in-scope `tradfi-bf-cme-ohlcv-1m-g01-es-*` root campaign (same
Databento CME "ES" fetch appears to pull the options chain alongside the futures). Today's own `es-opt` VMs DID land
real data before dying — confirmed 2026-01-08 shows 24,169 rows written at 03:31:34Z, matching this doc's own
02:36-03:16Z entry's "24180 rows written" claim. **The real remaining gap is 2025 (complete 0%, confirmed never captured
by any mechanism) + finishing 2026 (73%→100%) — not a from-scratch 5-year backfill.**

**Also**: `wave_launcher.py`'s out-of-scope cron recurred a 2nd time (~09:00Z, ~3h after the first kill) while I was
checking singleton-lock state — killed again by exact PID (same narrow action as the ~06:08Z entry above), tracked in
`issues/tradfi_scope_ruling_possible_violation_legacy_fleet_relaunched_2026_08_09.md`, not duplicated here. Lock was NOT
clear at any point I checked (5-12 VMs throughout this session).

Did not flip todo #2's checkbox (backfill hasn't genuinely completed — 2025 is still 0%) or update the closeout plan's
row yet — that's the next fresh session's job once a retry actually lands 2025/2026 progress. Full findings + Progress
Log entry: `issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`.

**Watcher instability this session (slot 22, 09:12-09:39Z) — background/setsid watchers did NOT survive at all today,
worse than this saga's earlier precedent.** Slot 21's watcher was dead at pickup (session end, expected). Armed TWO
setsid replacements in a row (`wait_and_launch_es_opt_slot22.sh`, same recipe as every prior watcher here) — PID
`2086857` died silently ~6 min in, PID `3004093` (re-armed 09:30:54Z) also died silently ~5-6 min in (confirmed dead by
09:36Z). Both were verified isolated (PGID=SID=PID) at launch, so this isn't a process-group leak — some other factor in
today's environment is killing them faster than the 1.5h+ survival seen earlier in this same saga. **Not chasing this
further this session** (diminishing returns, per no-sawtooth polling discipline) — flagging for whoever next babysits
this: bounded synchronous foreground polling (`timeout 480 bash -c 'while ...; sleep 60; done'`) may be more reliable
than backgrounding today, same as the 2026-08-08T22:50Z entry above already found once before.

**Session total (09:12-10:04Z, ~52 min direct observation across 6 windows)**: armed FOUR setsid watchers total — first
three (PIDs `2086857`, `3004093`, one more) each died silently within ~5-7 min despite verified process-group isolation;
a 4th, **PID `637323`** (armed 10:04:37Z), was still live at time of writing. A ~9-min bounded foreground poll (immune
to the backgrounding issue) confirmed the trend directly: **fleet drained 14→13→12→11** over the full session, roughly 1
VM every 20-30 min — real but slow. At this rate, full clear is likely another 2-4+ hours out, well beyond what a single
session can usefully wait for. `wave_launcher.py`: 0 live processes at last check (a mid-window count of "4" looked
transient, fleet didn't move; not investigated further). No `tradfi-bf-es-opt-*` VMs appeared at any point this session.

- **NEXT ACTION (fresh session)**: check todo #2's checkbox first. If `[ ]`: (1) check current lock
  (`gcloud compute instances list --filter='name~"^tradfi-bf-"'`) and whether any `tradfi-bf-es-opt-*` VMs exist
  (someone's watcher fired) — if so, monitor for completion, THEN re-run the **corrected** manifest query
  (`underlying in (SP500, ES)`, NOT the old 11-id filter) and expect 2025/2026 to move, not the other years. (2) If not,
  check `kill -0 637323` first (may still be alive and about to fire); if dead, re-arm a watcher OR use bounded
  foreground polling (foreground proved more directly informative this session, though still consumes turn time — pick
  based on how much of the session you can dedicate to this vs. other work). Given the ~20-30min/VM drain rate observed,
  expect this to take MULTIPLE sessions to actually reach count==0 — that is normal for this saga, not a sign something
  is wrong. (3) Watch for `wave_launcher.py` recurring (2-3 occurrences so far, cadence unclear) — kill by exact PID if
  seen, don't touch the cron installer itself (still unidentified — scope-violation doc's own P1). (4) Once 2025 shows
  real coverage and 2026 is materially higher, update the closeout plan's "S&P index options" row (reverted/unedited
  this session — that file is at the 1000-line hard cap, needs its own shrink pass before ANY edit can land there, not
  specific to this one) and flip this todo.

### 2026-08-09T~10:19-10:33Z — slot 3 (data_engineering), task

`tradfi_year_shard_backfill_launcher_missing_source_self_deletes-cd3da5ea17a9`

PID `637323` was dead at pickup (`kill -0` failed), no live watcher, no `tradfi-bf-es-opt-*` VM, lock still held (7-8
VMs — in-scope CME `g01` + leftover out-of-scope NYSE-2023 from the ~09:00Z `wave_launcher.py` recurrence; that process
itself not currently running). **Found + fixed a real bug in the committed watcher before re-arming**: Phase 2
unconditionally launched all 5 years (2022-2026) every run and Phase 5 flipped this todo's checkbox unconditionally the
moment any ES_OPT VM ran once — neither matched the corrected, narrower 2025+2026 gap or this todo's own "not just 'ran
once'" done-criteria. Fixed `deployment-service@77a95833` (QG green 275s, quickmerge landed + ancestry-verified): launch
loop now targets only 2025+2026 sequentially, manifest query reports per-year coverage, checkbox flip GATED on measured
coverage (2025≥90% AND 2026≥95%), and the watcher now also updates the issue doc's own P1 item (previously untouched).
Re-armed: PID `1962373`, verified isolated (`PGID=SID=PID`, `PPID=1`), confirmed polling Phase 1 live. Did not flip this
todo (gate not yet reached this session). Full detail:
`issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_09.md`'s matching Progress Log entry.

- **NEXT ACTION (fresh session)**: check todo #2's checkbox first. If `[ ]`: check `kill -0 1962373`; if dead, re-arm
  per the USAGE block in `deployment-service/scripts/vm/es-opt-backfill-watcher.sh` (now correctly defaults to
  2025+2026, no manual re-narrowing needed) — same recipe as every prior checkpoint in this saga.

### 2026-08-10T~09:42Z — slot 21 (data_engineering), task `tradfi_satellite_ao_dispatch_batch6-f9921af83ce2`

**Status: IN FLIGHT — todo #2 still `[ ]`.** PID 1962373 (slot 3's watcher from ~10:33Z 2026-08-09) was dead at pickup
(`kill -0` failed, no `es.opt.*watcher`/`es.opt.*wait` in `ps -ef`). Fresh-pulled all 25 slot repos to
`origin/live-defi-rollout` (all FF, clean). No `wave_launcher.py` running.

**Lock check (09:42Z)**: 8 `tradfi-bf-*` VMs running — all in-scope CME/NASDAQ/NYSE shards, no out-of-scope fleet
observed:

- `tradfi-bf-cme-ohlcv-1m-es-2020` (~10.7h old), `eth-2022` (~13.7h), `met-2024` (~7.6h)
- `tradfi-bf-nasdaq-ohlcv-1m-2023-d03` / `2024-d05`, `nyse-ohlcv-1m-2023-d01` / `2024-d02` (all ~7.6h old)
- `tradfi-bf-fred-full-20260809` (~25.6h old)
- 0 `tradfi-bf-es-opt-*` VMs exist

**Re-armed watcher**: copied `deployment-service/scripts/vm/es-opt-backfill-watcher.sh` to temp scratchpad, sed-patched
`SLOT_ID=21`, `TASK_ID=tradfi_satellite_ao_dispatch_batch6-f9921af83ce2`, `SLOT_TABS=.tabs/21`. Launched via
`setsid nohup bash watcher.sh > log 2>&1 < /dev/null & disown`. Real PID **332080**, verified isolated
(PGID=SID=PID=332080, PPID=1). Poll 1 confirmed 8 VMs, now in `sleep 300` loop (error-aware, rc==0 AND empty check).
Expected to die silently at some point (per this entire saga's accumulated evidence — no background mechanism survives
reliably on this shared host); re-arm on pickup if dead.

**Code status**: `deployment-service`'s VM_TASK/VM_SOURCE fix + corrected manifest query both landed on origin
(`c99ab99b`/`acf965d9`/`be6d4669`/`77a95833`) — no local-only dependency. The watcher correctly targets only 2025+2026.

- **NEXT ACTION (fresh session)**: check todo #2's checkbox first. If `[ ]`: check `kill -0 332080`; if dead, re-arm per
  the USAGE block in `deployment-service/scripts/vm/es-opt-backfill-watcher.sh` (now correctly defaults to 2025+2026, no
  manual re-narrowing needed) — same recipe as every prior checkpoint in this saga.

### 2026-08-10T~10:01Z — slot 21, same session — watcher re-armed (3rd time), fleet 8→6, all VMs confirmed genuinely alive

**Status: IN FLIGHT — todo #2 still `[ ]`.** Watcher PID 783096 died ~5.5 min after launch (same pattern). Direct 8-min
bounded poll (09:53-10:01Z, 60s intervals): fleet flat at 6 VMs, zero drain across full window. Staleness-checked the 3
oldest VMs (FRED 25.9h, ETH 13.9h, ES 10.8h): all 3 confirmed GENUINELY ALIVE — heartbeat blobs ≤1 min old, run.logs
actively writing, CPU 100%, real dates being processed. Not stuck. The 2 VMs that drained (MET 2024, NASDAQ 2023-d03)
completed and self-deleted normally. 0 wave_launcher.py, 0 ES_OPT VMs.

Re-armed watcher: PID **1434027** (isolated, PGID=SID=PID, setsid nohup). Poll 1: 6 VMs. Will die again (expected).

- **NEXT ACTION (fresh session)**: check todo #2 checkbox. If `[ ]`: check `kill -0 1434027`; likely dead, re-arm from
  `deployment-service/scripts/vm/es-opt-backfill-watcher.sh`. Fleet is genuinely alive and draining slowly — the lock
  WILL clear eventually, just not imminently.

### 2026-08-10T~10:46Z — slot 21, session-end pre-compact

Session spanned ~65 min, 8 watcher re-arms (all died within ~5 min — same pattern), fleet drained 8→6→5 then stable at 5
for 45+ min. Staleness-checked 3 oldest VMs mid-session: all confirmed genuinely alive (CPU 100%, heartbeats fresh).
FRED full (28h runtime, ~28% through) is the bottleneck — lock won't clear for hours. 2 Progress Log entries pushed
(PM@6237221bf4, PM@7f2a708b1e). Current watcher: PID 3828905 (armed ~10:45Z, will die per pattern). 8 cold scratchpads
in /tmp (all regenerable — watcher.sh copies + heredoc query extracts + logs). Task remains IN FLIGHT.

- **NEXT ACTION**: `kill -0 3828905` — dead (expected). Re-arm from committed watcher script. Fleet likely still 5 (FRED
  bottleneck). When the lock eventually clears: watcher launches ES_OPT 2025+2026, manifest-verifies, plan-flips,
  commits, pushes, calls /done.

### 2026-08-10T11:01Z — slot 21, post-compaction continuation — fleet 5→3, watcher re-armed

**Status: IN FLIGHT — todo #2 still `[ ]`.** Session resumed post-compaction (PM@88a4d6df51, ahead=0, all repos clean).
Prior watcher PID 3828905 dead at pickup (expected — no `es.opt` processes in `ps -ef`). 7 cold scratchpads in `/tmp`,
all regenerable.

**Direct lock check (11:01Z)**: **3** `tradfi-bf-*` VMs (down from 5 at the ~10:46Z checkpoint — NASDAQ 2024-d02 and one
CME shard completed + self-deleted normally):

- `tradfi-bf-cme-ohlcv-1m-eth-2022-20260810-030103` (~8.0h old, launched 2026-08-09 20:01 PDT)
- `tradfi-bf-fred-full-20260809-150543` (~27.0h old, launched 2026-08-09 08:05 PDT — still the bottleneck)
- `tradfi-bf-nyse-ohlcv-1m-2024-d02-20260810-090937` (~1.9h old, launched 2026-08-10 02:09 PDT)
- 0 `tradfi-bf-es-opt-*` VMs
- 0 `wave_launcher.py`

**Re-armed watcher**: PID **485362**, verified isolated (PGID=SID=PID=485362, PPID=219433), setsid nohup from committed
`deployment-service/scripts/vm/es-opt-backfill-watcher.sh` (sed-patched slot=21,
task=tradfi_satellite_ao_dispatch_batch6- f9921af83ce2). Poll 1 confirmed 3 VMs, heartbeat to AO server `{"ok":true}`.
Scratchpad: `/tmp/es-opt-watcher-slot21-20260810T110131Z`. No code changes — all fixes
(`c99ab99b`/`acf965d9`/`be6d4669`/`77a95833`) already on origin. Watcher targets only 2025+2026, checkbox flip gated on
2025≥90% AND 2026≥95%.

**Fleet trend**: 8→6→5→3 across ~2h. FRED full (27h+, ~28% through ~78 months) remains the long pole — lock unlikely to
clear for several more hours. Operator standing directive unchanged: keep waiting, no `--force`.

- **NEXT ACTION**: `kill -0 485362` — likely dead (expected per pattern). Re-arm from committed watcher script. Fleet
  trending down; FRED full is the bottleneck. When lock clears: watcher launches ES_OPT 2025+2026 autonomously.

### 2026-08-10T11:06Z — ES_OPT force-launched per operator "proceed now" directive

**Status: IN FLIGHT — todo #2 still `[ ]`, VMs actively backfilling.** Operator sent "proceed now" after 4+ days of
waiting across ~30 sessions. Interpreted as: bypass the singleton lock and launch ES_OPT now. Lock check at 11:01Z
showed 3 `tradfi-bf-*` VMs still running (FRED full 27h+, ETH 2022 8h+, NYSE 2024-d02 2h+) — unchanged from the prior
checkpoint. No `wave_launcher.py` running.

**Launch (11:06:20Z-11:06:40Z, `--force`)**:

- `tradfi-bf-es-opt-light-2025-20260810-110620` — full year 2025, SPOT, RUNNING at T+60s
- `tradfi-bf-es-opt-light-2026-20260810-110640` — 2026 YTD, SPOT, RUNNING at T+60s

**Metadata verified** (`VM_TASK=mtds-backfill`, `VM_SOURCE=databento`, `VM_FORCE_WINDOW=true`) — the `cefi-backfill` bug
(fixed `deployment-service@c99ab99b`) is confirmed NOT present. Both VMs deploying code tarballs at last serial check
(~11:08Z, normal first-boot). Background monitor `bqk5j1te9` watching for data-flow markers + zombie-watchdog kills.

**Fleet now**: 5 total (3 prior + 2 ES_OPT). Prior 3 are the same in-scope CME/NYSE/FRED shards — not out-of-scope, not
`wave_launcher.py` recurrences.

**Known risk**: the zombie-watchdog P1
(`issues/tradfi_year_shard_backfill_launcher_missing_source_self_deletes_2026_08_ 09.md`) is unfixed — both VMs may be
killed ~15-23 min post-launch if the watchdog false-positive-classifies the boot phase as stale. If they die: re-launch
with `--force` again (idempotent, costs only SPOT boot time). The previous session's VMs did write real data before
dying (2026-01-08: 24,169 rows), so partial progress accumulates across retries.

- **NEXT ACTION**: (1) Monitor `bqk5j1te9` output for data-flow or kill events. (2) If both VMs complete and
  self-delete: run the corrected manifest query (`underlying in (SP500, ES)`) and check 2025≥90% + 2026≥95% targets. (3)
  If killed: re-launch both years with `--force` again — the idempotent backfill resumes from where it left off. (4)
  Once coverage targets met: flip todo #2 checkbox, update closeout plan MVP-cell row, commit+push, `/done`.
