---
doc_type: plan
title: TradFi satellite AO batch 4 — post-batch3 re-audit extraction (prose-only orphans + today's fresh residuals)
summary: >-
  Fourth AO-dispatch batch for tradfi, produced by a second `/ag-closeout-audit tradfi` pass on 2026-07-26 (autonomous
  mode), run AFTER batch3 was activated and 5 of its 9 todos had already executed. Re-audited all 27 tradfi-primary
  non-covering docs against the 11-doc covering set (consolidated closeout + 4 forked children + batch1/2/3 + their
  finalizes); 22 came back orphaned. The new material this pass found that batch3's own triage could not have: (a) three
  docs whose remaining work is PROSE-ONLY with zero open checkboxes, which the closeout's aggregated-source digest
  wrongly lists as "0 open todos" — the exact trap the skill warns about; (b) residuals created THIS SAME DAY by
  batch3's own execution (the fx-provenance Deferred table, the tombstone script's Path-B bug); (c) two gates that
  measurably CLEARED (the tradfi-bf fleet fully drained 2026-07-21, unblocking a post-drain canonical re-measure; the
  features/MDPS dependency gap resolved 2026-06-29, making the sp500 plan's three BLOCKED- premises stale). Phase 3's
  conflict check cleared 8 todos (zero intra-batch file collisions); 2 conflicts are parked in the Deferred section.
status: draft
nature: process
asset_group: [tradfi]
stage: [data]
repos: [unified-trading-pm, unified-api-contracts, instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [tradfi, ao-dispatch, close-out, batch-4, satellite-docs, re-audit, prose-only-orphans]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/active/tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md,
    /plans/active/issues/tradfi_autonomous_session_operator_decisions_2026_07_25.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-26"
last_updated: "2026-07-26"
parent_epic: tradfi_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit tradfi run 2026-07-26 (autonomous / AO-dispatched mode, operator away). Phase 0 discovered the
  11-doc covering set via BOTH documented paths (filename-pattern + dependency-graph); Phase 1 classified all 27
  tradfi-primary non-covering docs by a per-doc read (no Workflow tool is exposed to this harness, so every read ran
  in-session rather than one agent per doc); Phase 3 ran the conflict-check against the consolidated closeout, its 4
  forked children, and batch1/2/3 before drafting any todo below.
assigned_role: data_engineering
sequential: false
drift_direction: advance-code
---

# TradFi satellite AO batch 4 — post-batch3 re-audit extraction

> **Status: draft — NOT approved, NOT dispatched.** Per CLAUDE.md's "Plan destination — ASK BEFORE CREATING" HARD RULE
> and the ag-closeout-audit skill's autonomous-mode guidance, a skill-drafted AO batch is never auto-shipped to
> `active`. This pass ran with the operator away and unreachable, so nothing here was flipped. Flip this frontmatter's
> `status` to `active` only after operator review.
>
> All 8 todos below are same-priority-independent and touch **distinct files** — verified explicitly (see the
> file-collision matrix near the bottom). Two todos carry a CROSS-BATCH ordering note because they write to a doc
> another still-draft batch also writes to; those notes matter only if both batches are activated together.

## Why a batch4 exists one day after batch3

`batch3` was drafted and activated earlier on 2026-07-26 off a Workflow-based triage of 22 docs. This pass re-audited
the same tranche and found genuinely new ground, not a re-run of the same list:

1. **Prose-only orphans the digest hides.** `tradfi_consolidated_closeout_2026_07_18.md`'s "Aggregated source docs"
   section reports `issues/tradfi_t1_no_working_mtds_job_2026_07_17.md` and
   `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md` as "0 open todos (closed/archived/record-only)" —
   that digest was generated 2026-07-24 by grepping each file for unchecked checkboxes. Both files carry REAL remaining
   work in prose with zero checkboxes. This is the confirmed trap the skill's Phase-1 step 1 names.
2. **Residuals batch3's own execution created today.**
   `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` gained a "Deferred work after 2026-07-26" table
   with two items whose "Blocked on" column literally reads "nobody";
   `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s tombstone entry records a real script bug found and
   deliberately left unfixed ("out of this todo's scope").
3. **Two gates that measurably cleared.** The `/plan-reconcile` pass immediately preceding this audit proved via
   `gcloud compute operations list` that ZERO `tradfi-bf-*` instances exist in `central-element-323112` in any state —
   the backfill fleet fully drained by 2026-07-21T09:48Z. That is the precondition
   `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md` explicitly waits on ("Re-measure the canonical %
   after both the writer fix AND the backfill fleet has drained, not before"). Separately,
   `/plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md` was verified this pass to be
   `status: resolved` with
   `resolved_by: market-data-processing-service@cc63d1b + features-service@34a5d4ff + market-data-processing-service@7d630a3 (2026-06-29)`
   — which makes three BLOCKED- premises in `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md` stale by a month.

## Todos

- [ ] [DATA] P0. **Correct the delete DATE in
      `issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md` and re-derive the soft-delete
      recovery window from it.** That doc's central timeline says the legacy bucket "was permanently deleted 2026-07-06"
      and its TIME-CRITICAL `[OPERATOR]` P0 computes "deleted 2026-07-06 = 20 days ago as of this writing" against the
      7-day GCS default soft-delete retention. **MEASURED 2026-07-26 (this audit), that date is wrong by 8 days**: a
      Cloud Audit Log read over a 120-day window, filtering
      `protoPayload.resourceName:"buckets/market-data-tick-tradfi-central-element-323112"` for `storage.buckets.delete`
      OR `storage.buckets.create` on project `central-element-323112`, returns EXACTLY ONE delete event —
      `2026-07-14T11:03:03.648128088Z`, `storage.buckets.delete`, principal `ikenna@odum-research.com` — and zero create
      events. So the real elapsed time is **12 days, not 20**, and the delete landed 3 minutes BEFORE the
      2026-07-14T11:06:16Z ICE-purge consolidator pause recorded in `tradfi_multisource_backfill_2026_06_22.md` — i.e.
      it was part of that day's operator session, not the 2026-07-06 v9 apply the doc reconstructs it from. Also record,
      as a measured negative, that this audit's own probe CONFIRMS the doc's credential claim and shows the `[OPERATOR]`
      gate is real rather than a false block:
      `gcloud alpha storage buckets list --soft-deleted     --project=central-element-323112` returns
      `HTTPError 403: unified-trading-sa@... does not have     storage.buckets.list access`, while
      `gcloud alpha storage buckets describe     gs://market-data-tick-tradfi-central-element-323112 --soft-deleted`
      returns `HTTPError 400: Bucket generation is     required` — i.e. the ONLY missing input is the bucket generation,
      which only the 403-denied list call yields. Repo: unified-trading-pm (doc-only; the recovery action itself stays
      `[OPERATOR]`, untouched here). **Done when**: the doc's summary, its "What I found" items (3) and (5), and the
      TIME-CRITICAL `[OPERATOR]` P0's elapsed-days arithmetic all state 2026-07-14 with the audit-log citation above;
      the 403/400 probe result is recorded so the next reader does not re-attempt it; no checkbox in that doc is flipped
      and no `[OPERATOR]` item is closed by this todo. Source:
      `issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md`.

- [ ] [REVIEW] P1. **Reconcile `issues/tradfi_t1_no_working_mtds_job_2026_07_17.md` against the shipment that already
      closed it.** The doc is `status: open` with ZERO checkboxes; its remaining work lives entirely in prose (a "Fix
      (not done here — needs its own workstream)" section plus a 2026-07-25 status note saying "This doc's own
      `status`/`resolved_by` frontmatter has not been reconciled against that shipment — left open here rather than
      unilaterally flipped, since the SIGKILL follow-up suggests the job isn't yet fully stable"). Both stated blockers
      are now closed on the OTHER side: `tradfi_backfill_throughput_followups_2026_07_24.md`'s "TradFi has NO working
      T+1 forward-fill job" todo is `[x]` with `deployment-service@11bed3c` plus a live re-verification 2026-07-25, and
      its SIGKILL follow-up todo is `[x]` ("no SIGKILL", 46m28.5s run). Re-verify LIVE rather than trusting either doc,
      via
      `gcloud run jobs executions list --job=uts-prod-market-tick-data-service-tradfi-databento-t1-recon     --region=asia-northeast1 --project=central-element-323112`
      — confirm the most recent SCHEDULED (un-forced) executions succeed and write rows. Then either flip the doc to
      `status: resolved` and populate `resolved_by`, or, if a scheduled execution is still failing, replace the prose
      "Fix" section with a real unchecked todo naming the specific remaining failure so it stops being invisible to the
      unchecked-checkbox digest. Repos: unified-trading-pm (doc), deployment-service (read-only verification). **Done
      when**: the doc either reads `status: resolved` with a `resolved_by` citing the shipped commits and the live
      execution evidence, or carries at least one canonical `- [ ] [TAG] P<N>.` todo for the residual — and in either
      case the "0 open todos" claim for this doc in `tradfi_consolidated_closeout_2026_07_18.md`'s aggregated-source
      digest is corrected in the same commit. Source: `issues/tradfi_t1_no_working_mtds_job_2026_07_17.md`.

- [ ] [DATA] P1. **Re-measure tradfi manifest `instrument_id` canonicality now that the backfill fleet has actually
      drained.** `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md` carries ZERO checkboxes but its
      "Recommended sequencing (do not skip ahead)" step 3 states the remaining work explicitly: "Re-measure the
      canonical % after both the writer fix AND the backfill fleet has drained, not before — an in-flight measurement
      will keep moving." Step 1 (the writer fix) shipped `mtds@56d39325` on 2026-07-21 for equity/etf/index. The drain
      condition is now MEASURED SATISFIED: zero `tradfi-bf-*` instances exist in `central-element-323112` in any state
      as of 2026-07-26T02:20Z, and the last equity shard self-deleted 2026-07-21T17:34:04Z. Read the live
      `market-data-tick-tradfi-prd` `_index/availability_index.parquet` (single-object download plus pandas — NOT a
      bucket walk, the same method the legacy-bucket census used) and report the canonical-vs-bare-ticker
      `instrument_id` share for `instrument_type` in {equity, etf, index}, split by `written_at` before/after the
      2026-07-21T16:20Z fix landing, so the post-fix cohort's canonicality is isolated from the historical backlog. Also
      settle the doc's two explicitly-unverified scopes by measurement: FX cash types, and CME derivatives (its
      2026-07-21T16:40Z log entry claims CME `futures_chain`/`options_chain` null-id is by-design — confirm or refute
      against the live index). **Scope guard**: this todo MEASURES and records in that issue doc's own Progress Log
      ONLY. It must NOT run, schedule, or modify the historical content-migration pass — that is
      `tradfi_manifest_content_recovery_completion_2026_07_24.md`'s Surfaces C+D todo, deliberately excluded from every
      tradfi batch as too-large-or-risky. Repo: market-tick-data-service (read-only manifest census). **Done when**: a
      dated measurement section in that issue doc reports the post-drain canonical share for equity/etf/index (split
      pre/post-fix), a verdict for FX cash types and CME derivatives, and a stated recommendation on whether the
      residual is small enough to close the doc or large enough to hand to the content-recovery plan — plus at least one
      canonical unchecked todo if any residual remains, so the doc stops reading as "0 open" to the digest. Source:
      `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`.

- [ ] [SCRIPT] P1. **Fix `reconcile_manifest_after_entity_change.py`'s `_default_csv_path()` under the Path-B per-slot
      topology.** Found and explicitly deferred by batch3's own tombstone run (2026-07-26):
      "`reconcile_manifest_after_entity_change.py`'s `_default_csv_path()` resolves `Path(__file__).parents[4]` assuming
      a non-slotted checkout — under the Path-B per-slot topology this lands on the READ-ONLY root PM clone
      (`unified-trading-system-repos/unified-trading-pm/`), not the slot's own PM clone. Worked around via
      `--output-csv` for this run; the path bug itself is a residual follow-up (not fixed here — out of this todo's
      scope)." That is a silent wrong-destination write for any future invocation that does not pass `--output-csv`, in
      a script whose whole purpose is producing an auditable tombstone CSV. Resolve the output path from the repo's own
      identity (git toplevel, or an explicit required argument) rather than a fixed `parents[N]` hop, and make the
      failure loud if no writable destination resolves. Repo: instruments-service. **Scope guard**: do NOT flip any
      checkbox in `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` — that file is written by
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s combined 7-item todo, and this residual is prose there, not
      a checkbox; record the fix in this batch plan's own evidence instead. **Done when**: `_default_csv_path()` no
      longer depends on a hard-coded parent-count hop, a unit test proves the resolved path is inside the invoking repo
      (and that an unresolvable destination raises rather than silently writing outside it), and
      `quality-gates.sh --no-fix` is green in instruments-service. Source:
      `instruments_tradfi_g1_g5_gate_execution_2026_07_24.md` (the 2026-07-26 tombstone entry's closing paragraph).

- [ ] [BACKEND] P1. **Close the two "Blocked on: nobody" items in
      `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`, combined into ONE todo because both write to
      that same doc** (mirrors batch2's same-source-doc combine discipline). (1) **Full-history census for the
      historical re-stamp** — the doc's own Deferred table says the re-stamp "needs a fresh full-history census first
      (the 4/12/802 counts are from the 2026-07-24 sample window, not a corpus-wide walk)". Read the live tradfi
      `_index/availability_index.parquet` as a single object (no GCS walk) and produce the exact corpus-wide count of
      rows where `data_type == ohlcv_24h` AND `venue` is one of ICE / KRX / FX AND the stamped source or `pipeline_mode`
      is databento-derived, broken down by venue and year, recording the snapshot path. **The re-stamp APPLY itself is
      deliberately NOT in this todo** — it is an in-place mutation of live production manifest state, the same class
      `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s `[OPERATOR]` CAS todo is gated on per
      `/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`; this todo produces the counted worklist that gate
      needs, nothing more. (2) **Finding 2 — the FX `SPOT_PAIR` manifest `instrument_id` WRITE-PATH fix** (not the
      historical backfill): find why the FX `SPOT_PAIR` manifest-writer call never receives a populated `instrument_id`
      while the GCS parquet content IS correctly id'd, starting at `market_tick_data_service/adapters/_umi_yahoo.py` per
      the doc's own recommended entry point, and fix it so NEW captures land with a populated canonical id. The
      4,310-row historical backfill stays OUT of scope for the same production-mutation reason as (1). **Conflict-check
      note**: batch2's Deferred section held both of this doc's candidates as conflict-gated against "the closeout's own
      still-open Phase A2 'NEW 2026-07-24' todo". That conflict has since **cleared by supersession, not by guesswork**:
      the 2026-07-25 second-tier trim forked Phase A2 out of `tradfi_consolidated_closeout_2026_07_18.md` into
      `tradfi_registry_coverage_and_ao_readiness_2026_07_25.md`, where the item was deliberately reformatted as a
      NON-CHECKBOX digest pointer (per that fork's own finding-H fix, and confirmed live — the child restates the two
      defects as prose citing this issue doc, with no unchecked checkbox). A pointer is not a competing claim, the same
      resolution batch1 applied to its Deribit item. Independently, batch3 already shipped the Finding-1 write-path fix
      (`unified-trading-library@f237b75a`) against that same ground with no collision. Repos: market-tick-data-service,
      unified-trading-pm (doc). **Done when**: (a) a dated census section in the issue doc reports corpus-wide per-venue
      and per-year counts for the mis-stamped `ohlcv_24h` population plus the snapshot path, and the Deferred table's
      first row is updated from "needs a census first" to "census done, apply is `[OPERATOR]`-gated"; (b) the FX
      `SPOT_PAIR` write path populates `instrument_id` on new captures, with a regression test asserting it,
      `quality-gates.sh` green in market-tick-data-service, and the Deferred table's second row updated to name the
      remaining 4,310-row historical backfill as the only residual. Source:
      `plans/active/issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md`.

- [ ] [REVIEW] P1. **Re-scope `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`'s three stale BLOCKED-
      premises.** Three of its open P0 items are gated on a blocker that resolved a MONTH ago: they cite
      `plans/active/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md` and say "GATED ON: operator
      decision on Option A vs B". **Verified live this pass**: that doc now lives at
      `/plans/archive/issues/features_delta_one_tradfi_mdps_dependency_gap_2026_06_24.md` with `status: resolved` and
      `resolved_by: market-data-processing-service@cc63d1b + features-service@34a5d4ff +     market-data-processing-service@7d630a3 (2026-06-29)`
      — Option A (a direct raw-MTDS read path in features-service) was adopted and shipped. So
      "BLOCKED-OPERATOR-DECISION" is factually stale on the MDPS `build-continuous` item, the
      `features-delta-one-service` ES item, and (as BLOCKED-UPSTREAM) the `features-volatility-service` item. Re-read
      each of the three against the shipped Option-A code path, restate what is ACTUALLY still required to run each one
      (a VM launch, a missing wiring step, or nothing), fix the dangling `plans/active/issues/...` reference to point at
      the archived path, and correct the `related:` entries that still use bare relative form to the leading-slash
      repo-root-relative convention per `/codex/11-project-management/cross-reference-path-convention.md`. **Explicitly
      NOT in scope**: launching any features or ML VM, or running any backtest — this todo re-scopes the plan's premises
      to the truth, it does not execute the work. The plan carries `locked_by: live-defi-rollout`, so do NOT archive it
      or clear the lock. Repo: unified-trading-pm (doc-only). **Done when**: none of the three P0 items still asserts a
      BLOCKED- state that the 2026-06-29 resolution disproves; each states its real current precondition; the
      archived-doc reference resolves; and every relative `related:` entry is corrected. Source:
      `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`.

- [ ] [DOC] P1. **Apply the 3 residual findings in `issues/tradfi_docs_reconciliation_findings_2026_07_21.md`.** That
      doc's banner reads "32/34 checkboxes applied 2026-07-21" but three unchecked findings remain, none claimed by any
      covering plan: **[P1 L97]** the consolidated closeout's Ground-truth-verdict header still asserts "the
      id-canonicalisation is barely started on the derivative id columns" and needs a supersede banner (that doc's own
      Progress Log now records catalogue Surface A and manifest Surface B as migrated and re-verified live 2026-07-25);
      **[P1 L460]** "Phase B migration items still shown unchecked" — **re-derive this one, do not trust the line
      number**: the Phase A1/B content it points at was forked out to
      `tradfi_manifest_content_recovery_completion_2026_07_24.md` on 2026-07-24, AFTER the finding was written, so the
      checkbox set to reconcile now lives in that child, not at L460 of the parent; **[P1 L237]** section 4 of
      `/codex/02-data/canonical-cutover-register.md` still says the tradfi corpus is "canonical on filenames only — the
      manifest measured 0 canonical rows". **CROSS-BATCH ORDERING NOTE**: two of the three findings edit
      `tradfi_consolidated_closeout_2026_07_18.md`, which `tradfi_consolidated_native_ao_extract_2026_07_25.md`'s todo
      also writes to. Both plans are currently `status: draft`; if BOTH are activated, do not dispatch this todo
      concurrently with that one. Repos: unified-trading-pm (plan + codex doc). **Done when**: all three findings are
      either applied with the corrected current state cited, or explicitly struck through in the findings doc with the
      evidence showing they no longer apply; the findings doc's own three checkboxes are flipped; and the banner's
      "32/34" count is updated. Source: `issues/tradfi_docs_reconciliation_findings_2026_07_21.md`.

- [ ] [DATA] P1. **Two uncovered residuals in `data_completion_tradfi_2026_07_15.md`, combined into ONE todo because
      both edit that same doc.** (1) **Manifest-verify the NASDAQ/NYSE 2023-2026 equity/ETF window** — the doc's
      COVERAGE-GAP todo was narrowed by `/plan-reconcile` on 2026-07-26 from "track against this running backfill" to a
      pure manifest verification, because the fleet it tracked is gone (the last NASDAQ/NYSE ohlcv-1m shard was deleted
      2026-07-21T17:34:04Z; zero `tradfi-bf-*` instances exist as of 2026-07-26T02:20Z). Read the live tradfi `_index`
      (single-object read, no walk) and report captured / `attempted_failed` / `expected_unattempted` counts for venue
      NASDAQ and NYSE, `data_type` `ohlcv_1m` and `ohlcv_1s`, dates 2023-04-15 through 2026, by year, and state plainly
      whether the window is filled, partially filled, or still substantially empty. **Scope note**: this is a
      MANIFEST-COUNT verification only and does NOT discharge `tradfi_consolidated_closeout_2026_07_18.md`'s own open P2
      todo, which asks for a fresh `data-pipeline-check-is` / `data-pipeline-check-mtds` RUN per MVP cell — a different,
      heavier method; say so explicitly in the write-up so the two are never conflated. (2) **Close the stale
      `base-library.sh` sentinel item** — the doc's own "Deferred work" section already records that
      `scripts/quality-gates-base/base-library.sh` "already writes `.qg_last_passed_sha` on a full green run … the exact
      fix this item describes has landed separately. **Already resolved** — the checklist item text is stale". Re-verify
      that against the live file and flip the stale `[SCRIPT] P2` PM-template-gap checkbox with the citation.
      **CROSS-BATCH ORDERING NOTE**: `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s todo 1 also writes checkboxes
      in this same doc (its lines 54 / 177 / 629). Both plans are `status: draft`; if BOTH are activated, do not
      dispatch this todo concurrently with that one. Repos: market-tick-data-service (read-only manifest),
      unified-trading-pm (doc). **Done when**: a dated per-year NASDAQ/NYSE coverage table is recorded in the doc with
      the explicit "manifest-count only, not a pipeline-check run" caveat, the COVERAGE-GAP todo is either flipped or
      restated with the measured remainder, and the `base-library.sh` checkbox is flipped citing the live file. Source:
      `data_completion_tradfi_2026_07_15.md`.

## Deferred — conflict-gated (do NOT draft a competing todo; parked for the operator)

- **BLOCKED-OPERATOR-DECISION — `tradfi_backfill_throughput_followups_2026_07_24.md`'s "[INFRA] P1. Bundle roots into
  fewer larger VMs" (line 289) vs `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s todo 3 sub-item (1).** Both
  change the fan-out design of the SAME file, `deployment-service/scripts/vm/_tradfi-ohlcv-launcher-lib.sh`, in
  different directions: the batch2 todo replaces `ohlcv_split_ticker_groups`'s ticker-group fan-out with N contiguous
  DATE slices (measured: equity critical path 7.1h to 1.2h, compute 231 to 46 VM-h); the throughput doc's own open todo
  instead accumulates multiple CME roots' symbol-sets into ONE VM per year-shard (a `SINGLE_VM_QUEUE` analog) and folds
  in a pd-balanced 250GB `TRADFI_OHLCV_BOOT_TYPE` disk default. They may well be compatible (one targets the equity
  launchers, the other the CME root loop) but neither doc states the interaction or the ordering, and both land in the
  same shared launcher library. Not resolvable from evidence alone, so parked per the operator's standing instruction
  never to silently resolve a conflict.

- **BLOCKED-OPERATOR-DECISION — `issues/databento_default_executor_dns_starvation_risk_2026_07_17.md`'s `[CODE] P1`
  checkbox has TWO claimants and a prior batch deliberately declined to pick.** The fix shipped (`mtds@ac857`, confirmed
  by `tradfi_backfill_throughput_followups_2026_07_24.md`'s own checked-off todo, which says "Tracking issue … is now
  STALE (fix landed) → doc-hygiene flip pending"), but `tradfi_satellite_ao_dispatch_batch2_2026_07_25.md`'s todo 5
  states verbatim: "**Deliberately scoped to NOT touch the doc's [CODE] P1 checkbox or `status`/`resolved_by`
  frontmatter** — that closure is already claimed by `tradfi_backfill_throughput_followups_2026_07_24.md`'s own
  checked-off todo … leaving that flip to whichever side the operator wants to execute avoids racing it." Drafting the
  flip here would override an explicit prior deferral to the operator. Parked unchanged.

## Deferred — too-large-or-risky (needs its own dedicated plan, not a batch todo)

- **`tradfi_manifest_content_recovery_completion_2026_07_24.md`** — unchanged from batch1/batch2/batch3. 7 open todos,
  including an `--apply` at scale over ~278K objects requiring a dedicated VM, an in-flight quarantine-population
  survey, and a BLOCKED-OPERATOR-DECISION on ICE qualifier variants. Still a live, fast-moving, multi-phase migration
  doc; still needs its own triage/design pass, not a `batchN` slot. Re-confirmed this pass, not re-triaged.

## Deferred — operator-gated (a ruling, not a re-triage, unblocks these)

Unchanged and NOT re-surfaced here, per the skill's "do not re-ask an already-asked operator question":
`issues/tradfi_mvp_mode_unreachable_dead_gate_2026_07_08.md` (the `mvp_mode` wire-vs-delete DECISION — note that
`tradfi_satellite_ao_dispatch_batch3_2026_07_26_finalize.md` is `status: active` and DOES carry a live re-check todo for
it, which corrects batch3's own claim that this deferral "has no live owner");
`issues/tradfi_chain_bundle_sampler_root_mismatch_2026_07_23.md` (which `EXCHANGE_CODE_TO_NAME` is authoritative);
`tradfi_legacy_twin_bucket_deletes_signoff_2026_07_24.md` (bucket deletes, hard-stop);
`instruments_tradfi_g1_g5_gate_execution_2026_07_24.md`'s G1 retirement section-8 purge, its ES and ES_OPT MVP-cell
items (still conflict-gated against the closeout's fresh-pipeline-check todo), and its BLOCKED-CREDENTIALS ICE plus
CME-futures-options source ask; `issues/tradfi_eu_not_draining_source_axis_drift_2026_06_24.md`'s 4,655 stale barchart
rows (keep-vs-purge); `issues/tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md`'s
`[DESIGN] P2` on whether aggregated 15m/24h TradFi bars are wanted;
`issues/tradfi_ohlcv_attempted_failed_cluster_2026_07_23.md`'s CBOE `ohlcv_15m` purge-vs-reclassify (verify-vs-fix
ambiguity, unchanged since batch2); `tradfi_multisource_backfill_2026_06_22.md`'s FX-yahoo drain (sequencing against the
FX write-path fix, unchanged since batch3); and the `altdata` asset-group home plus EIA credential asks in
`data_completion_tradfi_2026_07_15.md`.

## File-collision matrix (verified before finalizing — same-priority todos run concurrently by default)

| Todo | Primary file(s) written                                                                                            |
| ---- | ------------------------------------------------------------------------------------------------------------------ |
| 1    | `issues/tradfi_legacy_bucket_deleted_without_also_legacy_migration_2026_07_26.md`                                  |
| 2    | `issues/tradfi_t1_no_working_mtds_job_2026_07_17.md` plus one digest line in the consolidated closeout             |
| 3    | `issues/tradfi_manifest_writer_legacy_id_regression_2026_07_21.md`                                                 |
| 4    | instruments-service code + tests (no plan-doc write at all)                                                        |
| 5    | `issues/tradfi_fx_provenance_and_manifest_id_defects_2026_07_24.md` plus market-tick-data-service code             |
| 6    | `tradfi_sp500_ml_and_arb_backtest_readiness_2026_06_20.md`                                                         |
| 7    | `issues/tradfi_docs_reconciliation_findings_2026_07_21.md`, the closeout, and the canonical-cutover-register codex |
| 8    | `data_completion_tradfi_2026_07_15.md`                                                                             |

No file appears twice, with ONE deliberate exception: todos 2 and 7 both touch
`tradfi_consolidated_closeout_2026_07_18.md` — todo 2 edits exactly one line of the aggregated-source digest, todo 7
edits the Ground-truth-verdict section. Different sections of a 754-line file; if the operator prefers zero risk, run
todo 7 first, then todo 2.

## Reconciliation

Once a todo here ships, flip the corresponding checkbox/section in its named source doc, citing this plan's commit as
evidence. This plan's own reconciliation-then-archive step is machine-gated via a companion
`tradfi_satellite_ao_dispatch_batch4_2026_07_26_finalize.md` (`depends_on` on this plan plus `gate_on_depends: true`),
mirroring the batch1/batch2/batch3 finalize pattern.

## Codex SSOTs

No new durable contract is created by this plan — every todo executes an already-decided spec from its source doc, or
records a measurement. Todo 7's third finding edits `/codex/02-data/canonical-cutover-register.md`, which is itself the
codex change; the production-mutation reasoning that gates todos 1 and 5 comes from
`/codex/02-data/gcs-and-manifest-delete-safety-protocol.md`; todo 6's reference-form fix follows
`/codex/11-project-management/cross-reference-path-convention.md`.
