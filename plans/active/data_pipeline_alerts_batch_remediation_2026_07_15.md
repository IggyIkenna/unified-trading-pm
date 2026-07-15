---
doc_type: plan
title: Data-pipeline alerts batch remediation — drive #data-pipeline-alerts to a clean/accurate state
summary:
  "Operator pasted a dense batch of data-pipeline-alerts Slack alerts (2026-07-14 23:50 to 2026-07-15 00:19 UTC) —
  DP_RUN_MOSTLY_EMPTY across sports/cefi/defi/tradfi and DP_VM_EXIT_NONZERO for features-sports VMs — and asked (a) why
  identical alert payloads re-fire ~15min apart with no dedup/RESOLVED-green signal, (b) to actually fix the underlying
  consolidator/data issues since they affect data counts, and (c) to run this autonomously/locally with sub-agents,
  looping, until the channel is clean. Local human-driven track (not AO-dispatched) per operator's explicit 'locally'
  instruction."
status: active
nature: process
asset_group: [meta]
stage: [data]
repos:
  [
    unified-trading-pm,
    alerting-service,
    unified-trading-library,
    features-service,
    deployment-service,
    market-tick-data-service,
    instruments-service,
  ]
scope: [engineer, admin]
tags: [data-pipeline, alerting, manifest-consolidator, dedup, autonomous, incident]
related:
  [
    codex/05-infrastructure/data-pipeline-alerts.md,
    codex/05-infrastructure/manifest-consolidator-ssot.md,
    plans/active/issues/manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md,
    plans/active/issues/defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md,
    plans/active/data_pipeline_hardening_self_monitoring_2026_06_22.md,
    plans/active/issues/tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md,
  ]
created: 2026-07-15
last_updated: 2026-07-15
parent_epic: observability_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 2
estimate_calibrated_ai_days: 1.6
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: [operator Slack alert paste, 2026-07-15 conversation]
assigned_role: infra
drift_direction: advance-code
---

# Data-pipeline alerts batch remediation — 2026-07-15

## Why this plan exists

Operator pasted ~60 Slack alerts from `#data-pipeline-alerts` (window 2026-07-14 23:50Z → 2026-07-15 00:19Z) and asked
three things in the same turn: (1) diagnose+fix why alerts repeat byte-identical payloads every ~15min with no
dedup/RESOLVED signal, (2) actually fix the consolidator/data issues since they affect real data counts (not just
document them), (3) drive this to a clean channel state autonomously, locally, on a loop, with sub-agents, without
stopping to ask. `/autonomous` was explicitly invoked. This is a LOCAL plan (`assigned_vm: NA`) — operator said
"locally"; not routed through AO ingestion.

**Codex SSOTs**: `codex/05-infrastructure/data-pipeline-alerts.md` (failure-mode registry + emit/route/escalate model),
`codex/05-infrastructure/manifest-consolidator-ssot.md` (consolidator runtime + verification recipe).

## Ground truth established before this plan was written (do not re-derive)

- The alert batch maps to a DENSE pre-existing corpus of tracked issue docs — this is NOT a fresh discovery, it's an
  active, ongoing, heavily-documented incident class. Confirmed via cross-reference agent + direct reads:
  - `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md` (P1, open) — explains the
    `DP_VM_EXIT_NONZERO` features-sports alerts exactly: `uts-prod-manifest-consolidator-instruments-sports` Cloud Run
    job occasionally takes 8-9min instead of ~40s, blowing the 120s freshness budget. 0/9 VM launches succeeded as of
    last entry. Doc's own "most promising near-term fix": bounded retry-with-backoff in the features-service compute
    VM's startup gate (repo: features-service).
  - `defi_consolidator_scheduler_sigkill_unresolved_2026_07_10.md` (P1, open) — defi consolidator scheduler-triggered
    executions SIGKILL every ~5-6min (down from ~2min after a partial TTL fix); canonical manifest stuck stale for days
    at a time; MTDS defi VMs self-delete via OOM-preflight guard before ever running. Multiple mitigation rounds (memory
    bump, lock TTL) tried; root cause still NOT found. Next documented step: fix the Cloud-Run-jobs app-log-shipping gap
    (stdout logging bootstrap) so the actual in-container kill point becomes visible — explicitly deferred pending a
    concurrent UTL edit that may have since landed.
  - Many other tracked issues cover individual asset_group/data_type gaps (cefi resolved 07-13; various sports/tradfi
    issues). Full list surfaced by the cross-reference agent — see Progress Log entry below.
- Live `gcloud` check (2026-07-14 ~23:34Z) confirmed: `market-data-sports` consolidator's THEN-latest execution had
  failed with `Image '...market-tick-data-service:latest' not found`, but the NEXT execution 4 min later resolved the
  image fine and proceeded normally — a transient image-tag-resolution race at Cloud-Run-job execution-creation time
  (consistent with the precedent noted in `mutable_git_sha_tag_restamping_cloudbuild_2026_07_13.md`), NOT a sustained
  breakage. Not pursued further as its own item unless it recurs.
- AO backlog check (`check-ao-backlog-status.sh consolidator`) returned 0 matching dispatched/queued tasks — nobody is
  currently working these via the AO fleet. Safe to work locally without AO collision, but per-slot git-safety rules
  still apply (fetch before push, scope commits by name).
- Alert-repeat root cause: under active investigation by a background agent as this plan was authored — see Progress Log
  for the finding once it lands.

## Todos

- [x] [INFRA] P0. Diagnose and fix the alert-repeat/no-dedup/no-RESOLVED-green bug — BOTH layers shipped:
      `alerting-service@fe76ded34a4` (cadence-aware cooldown, `DP_RUN_MOSTLY_EMPTY: 1800.0`) +
      `deployment-service@0aaab1a22` (source-side `RenagTracker`, defense-in-depth). 166 unit tests pass,
      `quality-gates.sh` green both repos. Issue doc fully resolved (all 3 todos done):
      `plans/active/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`.
- [x] [CODE] P1. Bounded retry-with-backoff shipped — `features-service@5e1ffd2e`
      (`_assert_consolidator_healthy_with_retry`, 3 attempts/75s/150s total, fail-fast intent preserved).
- [x] [INFRA] P1 — REOPENED 2026-07-15 by adversarial verification (see below). `deployment-service@69136c2c` (Terraform
      lock-TTL override) IS live and DID close the stale-lock-reclaim trigger path, but an independent verifier found
      fresh post-fix Cloud Logging evidence of 3 executions still running full concurrent merges simultaneously via a
      DIFFERENT mechanism (a genuine CAS race in `_acquire_lock`'s `if_generation_match=0`, not TTL-expiry). The
      "resolved" claim was overstated and has been corrected — issue doc reopened to `open`, `resolved_by` cleared:
      `unified-trading-pm@140579a41`. Follow-up investigation of the real concurrent-acquisition bug dispatched
      separately (fleet-wide scope — shared UTL code, not sports-only).
- [x] [INFRA] P1 — SUPERSEDED, not needed. The stdout-logging-bootstrap plan for defi turned out unnecessary: the actual
      root cause (lock-TTL livelock, not an unobservable in-container crash) was found and fixed via Terraform alone
      (see Ground Truth — defi fix already verified live-working before this todo was ever picked up). Leaving unstruck
      rather than deleted, per plan-hygiene (documents why the originally-planned approach wasn't taken).
- [x] [DATA] P1. Swept every (asset_group, data_type) pair from the alert batch. cefi/tradfi partial-ratio cells:
      already tracked under existing per-venue docs. New:
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` (3 root causes; mbp_10
      mechanical fix dispatched separately). Big finding: cefi blank-data_type 9,757-row "RESOLVED" claim was incomplete
      — live re-query confirms real-but-static orphan rows (not actively growing), annotated
      `phantom_captures_cefi_2026_06_28.md`. Commits: `unified-trading-pm@{0378027e6,fe674d7a3}`.
- [x] [INFRA] P0 — EXHAUSTED, genuinely open (Rule-1 impossibility, not a stopping-short). Investigated the real
      `_acquire_lock` concurrent-acquisition race with real production-grade testing: 25 concurrent threads + 15
      separate OS processes racing genuine writes against the live bucket (GCS CAS itself proven sound, 1 winner every
      time), pulled and byte-diffed the ACTUAL deployed container image against HEAD (identical — ruled out stale
      image), grepped every `_LOCK_PATH` delete call-site (only the two known-legitimate ones exist). Could not identify
      the actual double-acquisition mechanism from static/local analysis or reproducible synthetic races — it only
      manifests against live production timing. Found and fixed a real, separate defect while investigating: the
      existing lock test suite's stub silently ignored `if_generation_match` and always succeeded, meaning a real
      regression in `_acquire_lock` would previously have passed CI undetected — hardened the stub to model real
      per-object generation CAS + added a genuine concurrent-race regression test (8 threads, exactly 1 must win).
      Shipped `unified-trading-library@324f1056` (test-only, zero runtime behavior change, 83 existing + 1 new test
      pass, QG green). Flagged 2 plausible-but-unproven contributing factors in deployment-service (liveness-monitor
      staleness threshold not updated for the new longer merge duration; a recovery-actuator cooldown sentinel that may
      not persist across invocations) as next-agent starting points. Issue doc left `open` (not falsely resolved) with
      full methodology: `unified-trading-pm@0e79a18b5`.
- [x] [INFRA] P2. Live fleet-freshness snapshot (2026-07-15, post all fixes): `market-data-tick-{sports,tradfi,cefi}`
      and `instruments-store-sports` canonicals all updated within the last few minutes of the check;
      `market-data-tick-defi` last updated 2026-07-14T22:47:57Z, consistent with its known 86400s (daily-batch)
      freshness budget, not stale. Did not re-run the full ~26-job verification recipe line-by-line (would need another
      dedicated pass); this is a spot-check, not exhaustive — noting as a real limit rather than claiming full-fleet
      coverage.
- [ ] [REVIEW] P2 — PARTIALLY DONE, time-bound limit. A full observation cycle (up to 24h for cefi's cadence) cannot
      complete inside this session — genuinely requires real wall-clock time to pass, not more agent effort. What COULD
      be verified now: the alerting-service + deployment-service dedup fixes are unit-tested to the exact claimed
      behavior (900s-apart collapses, 1801s-apart re-delivers) and both were independently re-derived by the adversarial
      verifier, not just self-reported — high confidence the literal duplicate-spam pattern the operator showed us is
      fixed, even without waiting out a live 24h cefi cycle to watch it directly. Genuinely unverified until real time
      passes: whether a RESOLVED/green bookend actually posts when the sports/tradfi/cefi conditions clear (that
      requires the underlying condition to actually clear first, which is a data-fix problem, not an alerting one, for
      most of the remaining open items below).
- [x] [REVIEW] P3. Final report — see Progress Log closing entry below.

## Progress Log

- 2026-07-15: Plan created. Investigation to this point (issue-doc cross-reference, live gcloud consolidator health
  checks, AO backlog check) summarized in "Ground truth" above. Two background agents in flight: (1) cross-reference of
  the alert batch against tracked issue docs — DONE, findings folded into Ground Truth; (2) alert-repeat/dedup
  root-cause investigation — in flight, will fold in on completion.
- 2026-07-15 (later same session): Alert-dedup root cause DIAGNOSED (agent completed) — full code-level cause with
  file:line refs, filed as `plans/active/issues/dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md`
  (unified-trading-pm@1db306a86). Corrected the codex incident-gateway wiring claim in
  `codex/05-infrastructure/data-pipeline-alerts.md` (same commit) — DP_\* CRITICAL events were never actually wired
  through the incident gateway, contrary to the diagram; they rely on `AlertDeduplicator` + a per-event cooldown map.
  Live-verified the defi consolidator lock-TTL/livelock fix (shipped by another slot, `unified-trading-library@9358fb0b`
  - `deployment-service@fe67a53`, deployed with `CONSOLIDATOR_LOCK_TTL_SECONDS=4200`) is WORKING: a 24m28s execution
    completed successfully post-fix (no SIGKILL), canonical manifest fresh. Did NOT duplicate that work. Dispatched 4
    parallel sub-agents (SUB_AGENT_MANDATORY_RULES.md + AUTONOMOUS_AGENT_RULES.md injected):
  1. `alerting-service` — implement cadence-aware cooldown fix #1 for `DP_RUN_MOSTLY_EMPTY` (dedup issue doc todo 1).
  2. `deployment-service` — source-side re-nag interval fix #2, defense-in-depth (dedup issue doc todo 2).
  3. `unified-trading-library` + `features-service` — investigate whether the sports 8-9min intermittent slow-run issue
     shares the defi livelock root cause (and fix via Terraform lock-TTL override if so), plus ship bounded
     retry-with-backoff in the features-service startup gate regardless (Option 2 from
     `manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md`).
  4. Research/triage sweep of remaining cefi/tradfi (asset_group, data_type) pairs from the alert batch not yet
     explained — classify tracked-vs-new, file/annotate issue docs. All 4 in flight as this entry is written; will fold
     results in on completion (harness auto-notifies on each).
- 2026-07-15 (agent 1 DONE): alerting-service dedup fix shipped —
  `alerting-service@fe76ded34a46f0cfa880c563fe462c155d50809f`. `_RECURRING_WARN_EVENTS: frozenset[str]` →
  `_RECURRING_ALERT_COOLDOWNS: dict[str, float]`, `DP_RUN_MOSTLY_EMPTY: 1800.0` added. Regression tests added (router +
  data_pipeline_rules), `quality-gates.sh --no-fix` green. Issue doc todo 1 flipped (`unified-trading-pm@0b7654658`).
  Todos 2 (deployment-service) and 3 (docs) left untouched as instructed — todo 3 was already done by the parallel docs
  commit; agent correctly preserved it rather than overwriting.
- 2026-07-15 (agent 4 DONE — cefi/tradfi sweep): classified every remaining alert-batch (asset_group, data_type) pair.
  Most cefi/tradfi partial-ratio cells were already tracked under existing per-venue capture-gap docs. Two genuinely
  new/uncovered findings surfaced and require operator visibility (both flagged, see below) + one new issue doc filed:
  `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` (3 distinct root causes for tradfi
  mbp_10/ohlcv_15m/ohlcv_24h/corporate_action_confirmed/earnings_result stuck ~100% failed — one mechanical
  allowlist-gap fix dispatched separately below, two are architecture/policy decisions left for operator review).
  Commit: `unified-trading-pm@0378027e6`.
- 2026-07-15 (agent 6 DONE — cefi phantom re-query, dispatched after the sweep flagged it as a possible "big finding"):
  **CONFIRMED real, but NOT actively growing.** The 9,757 blank-`data_type` `attempted_failed` cefi rows the alert
  reports are BYTE-IDENTICAL to a 2026-06-28 issue this doc's sibling (`phantom_captures_cefi_2026_06_28.md`) claimed
  fully RESOLVED — live re-query proves that claim was incomplete, not false: all 9,757 rows share one `attempted_at`
  timestamp (2026-06-28T03:12:34Z, an undocumented `reconcile_phantom_manifest_rows_all.py --apply` run), no NEW
  blank-data_type rows have appeared since (rules out an active writer regression), and 99.0% of them have a separate,
  correctly-typed `captured` row for the same (date, venue) — i.e. these are stale orphan manifest rows from a past
  cleanup pass, not missing/at-risk data, and the phantom-audit tool has a real blind spot (any blank-`data_type` row is
  unconditionally flagged phantom). No code fix shipped — remediation needs design (delete orphans vs. harden the audit
  tool) so it was captured as 3 follow-up todos rather than rushed. Issue doc annotated (not overwritten):
  `unified-trading-pm@fe674d7a3`.
- 2026-07-15: dispatched 2 more follow-up agents in parallel: (5) mechanical fix for the tradfi mbp_10 allowlist gap
  (market-tick-data-service, same pattern as the already-fixed KRX/ICE precedents) — in flight; (agent 3 continued)
  resumed the sports/features-service+UTL agent twice after it stalled in a background-wait pattern that doesn't
  actually wake a sub-agent (corrected with explicit foreground-execution instructions) — in flight.
- 2026-07-15 (agent 3 DONE — sports consolidator, after 2 stalls + correction): confirmed the sports 8-9min slow-run
  issue shares the EXACT SAME lock-contention livelock class already fixed for defi. Fixed `deployment-service@69136c2c`
  (Terraform lock-TTL override, live-applied) + defense-in-depth `features-service@5e1ffd2e` (bounded retry). Post-fix
  live-verified: zero stale-lock reclaims across 2+ six-minute cycles (previously guaranteed under the old 300s TTL).
  Issue doc flipped to resolved. Note: this agent's commit (`05942b2f0`) landed interleaved with my own in-flight edit
  to THIS plan file (shared working directory across concurrent agents) — content was NOT lost, both sets of changes are
  present, just under one commit instead of two; noting for the record, not re-litigating (rewriting shared history is
  banned).
- 2026-07-15 (agent 2 DONE — deployment-service re-nag): shipped `deployment-service@0aaab1a22`, a new `RenagTracker`
  module (GCS-persisted `last_alerted_at` per cell, mirrors the existing `MissTracker` pattern) wired into
  `check_high_attempted_failed` + `reconcile_resolved`. 5 new tests, 166 total unit tests pass,
  `quality-gates.sh --no-fix` green (file-size ratchet: `meta_watchers.py` was already at 897/900 lines pre-change,
  lands at 925/900 post-change — consumes the repo's existing `CODEX_MAX_VIOLATIONS=1` tolerance rather than adding a
  NEW one; QG reports it non-blocking. Worth a follow-up extraction pass but not blocking this fix). Both dedup-issue
  layers (alerting-service + deployment-service) now shipped — issue doc fully resolved.
- 2026-07-15: **Big finding — operator notified in chat** (per the HARD RULE, not blind-fixed): (1) cefi blank-data_type
  9,757-row stale "RESOLVED" claim (confirmed real-but-static via live re-query, see above), (2) tradfi cross-service
  data_type misclassification (corporate_action_confirmed/earnings_result expected in the MTDS tick manifest but only
  ever captured by features-service's calendar module — a bucket that structurally can never be satisfied). Both are
  architecture/policy items needing a real decision, not blind-fixed.
- 2026-07-15 (agent 5 DONE — tradfi mbp_10): shipped `market-tick-data-service@e2018167` — added `"mbp_10"` to
  `_DATABENTO_SUPPORTED_DATA_TYPES` (was silently excluding it despite a live schema mapping + an explicit
  `configs/venue_data_types.yaml` declaration, same registry-declares/allowlist-excludes shape as the already-fixed
  KRX/ICE precedents). Verified end-to-end fetch-path (not just the allowlist line) — genuinely complete on the MTDS
  side. Regression test added (registry-declared ⊆ adapter-supported invariant). 115 tests pass, QG green. **Important
  caveat surfaced, not glossed over**: a SEPARATE UAC registry (`VENUE_DATA_TYPE_CAPABILITIES["CME"]`) only declares
  `{ohlcv_1s, ohlcv_1m}` for CME per a 2026-05-15 operator MVP-scope decision, and intersects every fetch request
  against it BEFORE this allowlist is ever reached — so **this fix alone does not yet cause live mbp_10 capture to
  start**; that needs a separate, already-tracked, operator-gated UAC registry restoration (referenced:
  `plans/archive/2026_05/tradfi_l1_l2_l3_tick_data_post_cutover_2026_06_01.md`, whose registry-restoration phases were
  apparently never actually re-applied despite being marked complete — worth a follow-up look). Issue doc updated:
  `unified-trading-pm@ee328b8c0`.
- 2026-07-15: **All 5 dispatched fix agents complete.** Shipped commits: `alerting-service@fe76ded34a4`,
  `deployment-service@{0aaab1a22,69136c2c}`, `features-service@5e1ffd2e`, `market-tick-data-service@e2018167`. Launched
  an independent adversarial-verification Workflow (5 skeptics, one per fix, no context from the implementing agents)
  before declaring any of this genuinely done — result to follow.
- 2026-07-15: **Adversarial verification pass complete — 4/5 CONFIRMED, 1/5 DISPUTED.** Verdicts:
  `alerting-service-dedup` CONFIRMED (mechanism, cooldown boundary math, and test-would-actually-catch-a-regression all
  independently re-derived, not just read). `deployment-service-renag` CONFIRMED (wiring order, key-identity match with
  the existing MissTracker, and the file-size-ratchet-is-pre-existing-not-new claim all independently re-verified by
  re-running the gate). `features-service-retry` CONFIRMED (traced that `MANIFEST_ALLOW_STALE_FALLBACK` is untouched —
  the claimed "no weakening" is real, not asserted). `mtds-mbp10-allowlist` CONFIRMED-WITH-CAVEAT (the caveat is the one
  already disclosed — UAC registry gate — not a new hidden gap). **`deployment-service-sports-ttl` DISPUTED** — see the
  corrective entry + reopened issue doc above. This is adversarial verification doing exactly its job: catching an
  overstated "resolved" claim before it became a stale false-green in the tracker. New P0 todo added for the real fix
  (the `_acquire_lock` CAS race).
- 2026-07-15 (lock-race investigation DONE — genuinely exhausted, not falsely resolved): see the P0 todo above. Real
  production-grade testing ruled out every hypothesis reachable from static/local analysis; a genuine test-fidelity gap
  was found and fixed along the way (`unified-trading-library@324f1056`); the actual mechanism remains open with a
  documented methodology for the next investigator, plus two flagged leads in deployment-service.
- 2026-07-15: **Final live fleet-freshness spot-check** — all 5 buckets touched this session are currently healthy (see
  P2 todo above for exact timestamps).

## Final report (per AUTONOMOUS_AGENT_RULES.md rule 9)

**What shipped (real, tested, verified — not self-reported):**

1. `alerting-service@fe76ded34a4` — cadence-aware alert-dedup cooldown. CONFIRMED by independent adversarial review.
2. `deployment-service@0aaab1a22` — source-side re-nag tracker (defense-in-depth for #1). CONFIRMED.
3. `deployment-service@69136c2c` — Terraform lock-TTL override for the sports consolidator. CONFIRMED live-deployed;
   closed one real trigger path (stale-lock reclaim) but did NOT fully resolve the underlying issue (see below).
4. `features-service@5e1ffd2e` — bounded retry-with-backoff on the sports startup gate. CONFIRMED.
5. `market-tick-data-service@e2018167` — tradfi `mbp_10` Databento allowlist fix. CONFIRMED-WITH-CAVEAT (fix is real and
   complete on the MTDS side; a separate UAC registry gate still blocks live capture — not this fix's scope).
6. `unified-trading-library@324f1056` — hardened the manifest-consolidator lock test suite's CAS-mocking fidelity +
   added a real concurrent-race regression test, found while investigating item 3's residual bug.
7. Corrected a pre-existing, independently-verified-as-real defi consolidator SIGKILL fix (shipped by another engineer
   minutes before this session started) — verified live, not duplicated.

**Issue docs filed/updated**: `dp_run_mostly_empty_no_recurring_dedup_2026_07_15.md` (filed, fully resolved),
`manifest_consolidator_instruments_sports_intermittent_slow_run_2026_07_14.md` (reopened after a corrected overclaim,
now honestly `open` with full methodology),
`tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` (filed, 1 of 3 findings fixed),
`phantom_captures_cefi_2026_06_28.md` (annotated — a "RESOLVED" claim corrected to reflect reality), plus
`codex/05-infrastructure/data-pipeline-alerts.md` (corrected an inaccurate architecture claim).

**Genuine impossibilities / items requiring an operator decision, not blind-fixed (Rule 1 exception)**:

1. The real `_acquire_lock` concurrent-acquisition mechanism — exhausted every static/synthetic investigation avenue;
   only reproduces under live production timing. Needs either live production tracing tooling beyond what's available in
   this session, or the two flagged deployment-service leads chased down by a fresh investigation.
2. Cefi blank-`data_type` 9,757 orphan rows — real, static (not growing), needs an operator call: delete the orphans vs.
   harden the phantom-audit tool's blank-`data_type` blind spot.
3. Tradfi `ohlcv_15m`/`ohlcv_24h` — structurally the wrong layer is being asked to serve these (by-design aggregated
   data expected at the raw-tick download layer); needs an operator call on which layer should satisfy the manifest
   cell.
4. Tradfi `corporate_action_confirmed`/`earnings_result` — cross-service misclassification (MTDS manifest expects cells
   only features-service's calendar module can ever satisfy); needs an operator call on ownership.
5. Tradfi `mbp_10` live capture — MTDS-side code fix is complete, but a separate UAC registry
   (`VENUE_DATA_TYPE_CAPABILITIES["CME"]`) still gates it shut per a 2026-05-15 operator MVP-scope decision; needs an
   operator call on whether to restore it now.

**Verified end-state of the alert channel**: the literal duplicate-spam pattern the operator showed us (byte-identical
`DP_RUN_MOSTLY_EMPTY` every ~15min) is fixed and independently verified — high confidence. Not fully "100% clean": 5
items above remain genuinely open, each requiring either further live-production investigation time or an explicit
operator decision this session correctly did not make unilaterally. This is an honest non-100% outcome, documented with
evidence per the plan's own stated exception for exactly this case.

## Operator decisions (2026-07-15, interactive reconciliation)

Presented all 5 open items to the operator with recommendations; decisions below. New todos follow.

1. **Cefi orphan rows**: **BOTH** — harden the phantom-audit tool's blank-`data_type` blind spot AND delete the 9,757
   stale orphan rows. (Operator picked the most-thorough option over my "delete only" recommendation.)
2. **Tradfi ohlcv_15m/24h**: operator confirmed the per-venue-routing read is correct (Databento-uncovered venues — e.g.
   FX spot, Korean equities — need whatever granularity their real source provides, which may only be daily;
   Databento-covered venues should get finer bars within billing limits, not be capped) BUT corrected my framing: **this
   is very likely NOT greenfield design work** — the operator believes UAC/instruments-service/MTDS already has
   infrastructure for per-venue source-capability constraints and this "might need completion" rather than a new design.
   **Action: AUDIT existing UAC/IS/MTDS per-venue capability routing FIRST** to find what's already there vs. genuinely
   missing, before writing any new code.
3. **Tradfi corporate_action_confirmed/earnings_result**: **CONFIRMED** — stop instruments-service seeding these as
   expected cells in the MTDS tick manifest (matches my recommendation).
4. **Tradfi mbp_10 UAC registry**: **Leave the MVP-scope restriction in place** (operator did NOT take my recommendation
   to restore it now) — this is a deliberate, still-intentional scope decision, not a bug. Action: correct the issue doc
   so `mbp_10`'s live-capture gap reads as "expected per scope decision," not "open gap needing a fix," and ensure the
   alert reflects that (mute/expected classification) rather than staying flagged as an active problem.
5. **Sports lock-race**: **Parked** — no further investigation this session; leave the issue doc exactly as the
   exhausted-investigation entry documents it, revisit later (possibly with better production-tracing tooling).

### New todos (this reconciliation)

- [ ] [DATA] P1. Cefi: hardening `reconcile_phantom_manifest_rows_all.py`'s (or wherever the blank-`data_type`
      phantom-matching logic actually lives — grep first) blind spot so a blank-`data_type` row is no longer
      unconditionally flagged phantom regardless of whether real data exists; then delete the confirmed 9,757 stale
      orphan rows (per `phantom_captures_cefi_2026_06_28.md`'s 2026-07-15 investigation section for the exact
      predicate/evidence). Repo: likely e2e-testing or unified-trading-library — locate via grep.
- [x] ✅ [DATA] P1. Tradfi ohlcv_15m/ohlcv_24h: AUDITED — operator's prior CONFIRMED (per-venue source-capability
      infrastructure already exists in `unified_api_contracts/registry/expected_coverage.py` +
      `market_data_categories.py::VENUE_DATA_TYPE_CAPABILITIES` + `data_source_continuity.py::_SOURCE_RESOLVERS`, and is
      mostly already correct — CME/NASDAQ/NYSE correctly excluded from ohlcv_15m/24h, ICE/KRX/FX correctly capped at
      ohlcv_24h). Shipped one completion fix (CBOE's stale ohlcv_15m entry, `unified-api-contracts@78b9e899`, same
      narrowing pattern as KRX/ICE, QG green) and found + documented 2 further genuine gaps rather than rushing them (no
      downstream aggregation writer exists anywhere despite 3 places claiming one does; `"YAHOO_FINANCE"` is a phantom
      no-adapter venue inflating the failure counts, same class as the corporate_action_confirmed/ earnings_result fix
      below). Full writeup + 2 new scoped todos:
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` § "Resolution —
      ohlcv_15m/ohlcv_24h audit (2026-07-15)".
- [x] ✅ [CODE] P1. Tradfi corporate_action_confirmed/earnings_result: stop
      `instruments-service/scripts/enumerate_expected_universe.py` from seeding these as expected cells in the MTDS tick
      manifest bucket. Confirmed as the sole seeding site (grep-verified across instruments-service +
      market-tick-data-service + UAC — no other non-test consumer of either data_type; features-service's calendar
      module, which owns the real capture code, has zero dependency on `DATA_TYPES_BY_ASSET_GROUP` and is unaffected).
      `instruments-service@03f71c81` adds a tradfi-only `_tradfi_mtds_tick_manifest_data_types()` exclusion helper wired
      into both `enumerate_v2()` and `main()`'s `data_types`-resolution sites; UAC's
      `DATA_TYPES_BY_ASSET_GROUP["tradfi"]` registry itself is deliberately left untouched (other UAC consumers —
      validity matrices, UI reference-data generation, `mvp_scope` — still need both types declared legitimate). 4 new
      regression tests (`TestTradfiMtdsTickManifestDataTypeExclusion`), full suite + `quality-gates.sh` green.
      **Historical row cleanup: deferred, not done in this pass** — the 807 `corporate_action_confirmed` + 799
      `earnings_result` already-seeded `attempted_failed` rows in the live TICK manifest are untouched (forward-only
      fix: stops future seeding, does not retroactively clean existing rows) — flagged as a follow-up in the issue doc
      rather than silently dropped; it's a production-data-mutation decision (delete vs. reclassify) that deserves its
      own scoped pass, same reasoning as the parallel cefi-orphan-rows and mbp_10 items in this remediation wave. Full
      resolution write-up + operator decision record: `unified-trading-pm@24ee65c3a`
      (`tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` § "Resolution —
      corporate_action_confirmed / earnings_result"). Independently re-verified (seeding-site confirmation, blast
      radius, scope precision vs. UAC, test coverage, historical-row decision) against the already-shipped commit before
      this checkbox flip — no discrepancies found.
- [ ] [DOCS] P2. Tradfi mbp_10: correct
      `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` to reflect that the UAC
      registry restriction is a confirmed-still-intentional operator scope decision, not an open gap — and check whether
      the `DP_RUN_MOSTLY_EMPTY` detector/alert for this specific cell should be suppressed/reclassified as expected
      rather than continuing to page as if it's an active problem.

### 2026-07-15 (later same day) — re-pasted alert batch, picked up by a different session; 5 new findings

Operator re-pasted the SAME `DP_RUN_MOSTLY_EMPTY` alert batch into a different session. Cross-checked against this
plan's own state first (git log showed the reconciliation above landed ~12 min earlier) rather than duplicating —
dispatched 4 parallel sub-agents (per this plan's own "sub-agents, looping" charter) against the 4 approved todos above,
in isolated worktrees. While investigating item 4 (mbp_10) directly, found the "1186/1186" figure the doc analyzed does
NOT match the CURRENT real failing population: **CME currently has ZERO `attempted_failed` mbp_10 rows** — the real 1186
rows are `KRX=742, NYSE=292, NASDAQ=152`, venues the operator's CME-specific decision never covered. Investigating those
revealed a bigger, cross-cutting bug (see new todo below) — NOT applying the CME reclassification logic to these 3
different venues, since that would be guessing past what was actually decided.

Also found 3 more `DP_RUN_MOSTLY_EMPTY` cells from the SAME alert batch that this plan's earlier "swept every
(asset_group, data_type) pair" pass (todo above, `unified-trading-pm@{0378027e6,fe674d7a3}`) did not cover — that sweep
says "cefi/tradfi partial-ratio cells: already tracked", but did not explicitly re-verify SPORTS or all of DEFI's cells
against existing docs. Logging what's confirmed genuinely new/untracked here rather than assuming covered:

- [ ] [DATA] P0 **NEW FINDING**: real cross-cutting classification bug — rows with an `EXPECTED_*`-prefixed
      `error_reason` (e.g. `EXPECTED_SOURCE_NOT_AVAILABLE`) are being stored with `capture_status="attempted_failed"`
      instead of `expected_unattempted`/`empty_confirmed` (an `EXPECTED_*` reason should NEVER pair with
      `attempted_failed` per this workspace's honest-absence convention). Confirmed real, live counts (may drift by the
      time this is picked up): tradfi/ohlcv_15m (~2347 rows), tradfi/trades (~2343), tradfi/ohlcv_1m (~1832),
      tradfi/mbp_10 (~1186, spanning KRX/NYSE/NASDAQ — NOT CME) — ~7,700+ rows total, clustered around a single ~90s
      batch window (`attempted_at≈2026-07-07T07:28-07:29Z`). Root-cause research (before dispatching the fix agent)
      found: the 2 known committed call sites that use this exact reason string
      (`reclass_krx_eu_source_not_available.py`, `reclass_oos_equity_eu_not_in_dataset.py`) both correctly pair it with
      `empty_confirmed` and don't match this bug's footprint (wrong data_type scope, wrong row count) — the actual
      writer that produced the mismatched rows is NOT visible in current committed source (likely an uncommitted/ad-hoc
      pass). Also confirmed a systemic gap: `ManifestWriter.record_failed()` has NO validation preventing an
      `EXPECTED_*`-prefixed reason from being passed to it (unlike `record_empty()`'s closed-set enum check), so this
      can recur silently. Dispatched to a sub-agent (data-fix: reclassify the ~7,700 rows + regression tests; code-fix:
      guard `record_failed()` against `EXPECTED_*`-prefixed reasons; new issue doc) — see that issue doc for the
      resolution once shipped. Repos: `market-tick-data-service` (data fix), `unified-trading-library` (writer guard).
- [x] ✅ [DATA] P1 **NOT YET COVERED by this plan's earlier sweep**: `defi/dex_pool_state` (2109/1583050
      attempted_failed, 0.1%) and `defi/lst_rates` (851/15830, 5.4%) — both 100%
      `error_reason=UPSTREAM_INSTRUMENTS_CATALOG_STALE` — INVESTIGATED 2026-07-15: live-requeried counts confirmed
      (dex_pool_state 2107/2109, lst_rates 851/851, `attempted_at` 2026-06-21..06-25 / ..06-30 respectively). Root cause
      is a **temporal race, not a broken/regressed gate**: every affected row is a historical backfill shard (shard
      `date` years before `attempted_at`, 0% same-day) whose `assert_defi_catalog_fresh` coverage-check genuinely found
      no IS DeFi catalogue snapshot for that historical date AT THE TIME — proven via `gcs_describe_object()` timestamps
      showing the catalogue snapshots that now cover those dates were written 2026-06-29, AFTER every affected attempt.
      R5-fix-7 (2026-06-08) referenced an earlier, smaller re-promote (R4, defi 6,853 rows) — the full historical
      per-date catalogue backfill these rows needed didn't finish until 2026-06-29, three weeks later. Also found +
      fixed a real, adjacent code gap while tracing this: `lst_rates_handler.py` was 1 of 9 DeFi handlers never
      threading `mode=` into `assert_defi_catalog_fresh` (only `dex_pools_handler.py` + `risk_params_handler.py` did) —
      didn't cause these specific rows but is a genuine near-term-batch-run latent bug, fixed with 3 new regression
      tests. Data remediation (re-collecting the 2,958 affected shards) deliberately NOT executed — a live, multi-year,
      production-API-quota-consuming re-collect is out of scope for a rushed mid-investigation action; scoped as a
      follow-up with exact commands. Full writeup, evidence, and follow-up todos:
      `plans/active/issues/defi_upstream_instruments_catalog_stale_2026_07_15.md`. Repo: market-tick-data-service.
- [ ] [DATA] P1 **NOT YET COVERED**: `sports/trades` (112277/522276 attempted_failed, 21.5%) —
      `error_reason=VENUE_FETCH_FAILED` dominates (94127 of the 112277), `attempted_at` up to 2026-07-13T23:56Z
      (freshest of all the alert-batch cells — worth checking if this is still actively recurring). `VENUE_FETCH_FAILED`
      is heavily tracked for CeFi/Tardis (`cefi_hl_aster_batch_data_gaps_2026_06_22.md`) but NOT found tracked for
      sports specifically. A smaller slice (several hundred rows) shows a DIFFERENT, more interesting pattern: a
      `record_empty(reason=SOURCE_RETURNED_ZERO) rejected: instruments-service catalog says 'trades' was ALIVE on     <VENUE>/<DATE>. Use record_failed(EmptyFromLiveInstrumentError(...)) instead`
      guard message (BETFAIR, MATCHBOOK, PINNACLE, and others, many 2022-era dates) — this exact pattern + fix design IS
      tracked (`data_completion_to_100_all_ag_2026_06_21.md:461-489`, marked `[x]` done for bookmaker venues via a
      `BOOKMAKER_NO_COVERAGE` reclassify), but these alert-batch instances run through 2026-07-13 — AFTER that fix
      landed — worth verifying whether the fix's venue/date coverage is actually complete or these are a residual gap.
- [x] ✅ [DATA] P2. `sports/odds_horizon_bucket_15m` (66/66 attempted_failed, 100%,
      `error_reason=MalformedTickFieldError`, `attempted_at` 2026-07-13T23:56Z) — INVESTIGATED + FIXED. Live re-query
      found the count has already drifted to 0 in both plausible sports manifests (a one-off manual-run artifact, not
      ongoing scheduled traffic). Root cause was a real, standing classification bug (not upstream-only):
      `SportsBucketAssignmentAdapter.process_to_candles()` raised `MalformedTickFieldError` whenever every tick row
      failed the `bm_time <= fetch_utc` causality check, even though `bm_minutes_to_kickoff` + h2h columns were
      genuinely present — mislabeling honest absence (vendor clock-skew/stale snapshot) as a malformed field, the same
      false-failure class the adapter's own existing "no h2h rows" Path A½ fix already corrected for a sibling
      condition. Fixed `market-data-processing-service@7ff43d7197a50cfe52d9ad8fe514cd6a2ca09558` (now records
      `empty_confirmed` for the 100%-causality-drop case; genuine schema drift still raises as before), 3 new regression
      tests (coverage.xml-verified both branches hit), `quality-gates.sh --no-fix` green. Checked for correlation with
      the sibling `sports/trades` `VENUE_FETCH_FAILED` investigation (same `attempted_at` batch window) — no issue doc
      filed for it yet as of this writing; based on this investigation's own evidence the two are NOT the same root
      cause (different services/manifests/code paths), noted for the next investigator rather than asserted without
      evidence. Full writeup: `plans/active/issues/sports_odds_horizon_bucket_malformed_tick_field_2026_07_15.md`.

### Post-reconciliation progress

- 2026-07-15 (background research agent): completed the ohlcv_15m/ohlcv_24h audit todo above. Full findings + the
  shipped CBOE fix + 2 new scoped follow-up todos are in
  `tradfi_unreachable_databento_data_types_mbp10_ohlcv_coarse_calendar_2026_07_15.md` § "Resolution —
  ohlcv_15m/ohlcv_24h audit (2026-07-15)" (not duplicated here per the plan-references-codex/issue-docs discipline).
- 2026-07-15 (dispatched sub-agent — tradfi mbp_10 investigation escalated into a much bigger cross-cutting finding):
  while investigating the narrow tradfi mbp_10 `DP_RUN_MOSTLY_EMPTY` cell, found the live tradfi manifest
  (`market-data-tick-tradfi-prd-central-element-323112`) had 34,260 rows (not the ~7,700 in the initial narrow grep)
  where `error_reason` carried an `EXPECTED_*`-prefixed honest-absence value but `capture_status="attempted_failed"`
  instead of `empty_confirmed` — a real, cross-cutting data-correctness bug per the workspace's findings-triage HARD
  RULE (big finding, data-correctness). Fixed both halves: **data fix**
  `market-tick-data-service@92d4fb18b826c7b43aa3597d5b1eeb135e26d829` (one-off reclassification script,
  dry-run+`--apply`+snapshot+before/after-verified: `attempted_failed` -34260, `empty_confirmed` +34260, total rows
  unchanged) and **code fix** `unified-trading-library@c08a8d61b96d6d1570389f9396068bed51001816`
  (`ManifestWriter.record_failed()` now hard-rejects an `EXPECTED_*`-prefixed `error` string — mirror-image guard to
  `record_empty()`'s existing `EmptyFromLiveInstrumentError` check — preventing recurrence). Root-cause writer
  provenance NOT established (flagged honestly, not guessed — the 2026-07-07 06:39-07:29 UTC writer is not visible in
  currently-committed source). Full writeup, counts, taxonomy-gap flag, and follow-ups:
  `plans/active/issues/tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`.
- 2026-07-15 (independent second dispatch of the SAME ohlcv_15m/ohlcv_24h audit todo — a duplicate-in-flight, not a new
  todo): re-derived the same audit conclusion independently (operator's per-venue-routing prior confirmed; 4 existing
  routing layers cited) before discovering the above agent's work had already landed. Added value rather than
  duplicating: a live re-query of the tradfi tick manifest that corrects the existing write-up's "YAHOO_FINANCE is the
  dominant contributor" claim for `ohlcv_15m` (it's actually zero — NYSE/CBOE dominate) and traces the concrete reason
  the alert keeps firing despite the routing gap being closed: `deployment-service`'s DP-FETCH-009 detector
  (`_read_attempted_failed_cells`) counts `attempted_failed` over the WHOLE manifest with no date-recency window, so the
  ~6,400 combined stale (8+ day old, non-regenerating) `ohlcv_15m`/`ohlcv_24h` rows alone permanently exceed its 500-row
  absolute threshold. Filed as a "Verification addendum" section in the issue doc (§ "Verification addendum — live
  manifest re-query + alert-persistence root cause") rather than a rewrite. No code shipped (nothing left to build for
  this finding) and the plan checkbox above was correctly already `[x]` — left as-is. Recommends this alert-persistence
  mechanism (whole-history count, no recency window) be looked at as ONE unified follow-up alongside the mbp_10 and
  corporate_action_confirmed/earnings_result stale-row questions already flagged elsewhere in this doc, rather than
  three separate piecemeal decisions.

## Reconciliation round — closing report (2026-07-15)

All 3 dispatched follow-up fixes from the operator-decision round are complete:

1. **Cefi orphan rows (BOTH, as decided)** — 🔴 **CODE fix landed, DATA fix did NOT durably stick — see correction
   below.** Tool hardening shipped `instruments-service@dd6b4e826` (generalized the blank-`data_type` blind-spot fix
   beyond the schema_version==4 special case it was previously limited to) — this part holds. The 9,757-row deletion was
   executed with real production-data rigor: re-verified the exact predicate and the 99.0% cross-reference live before
   touching anything, discovered mid-task that the originally-planned deletion mechanism was unsafe (a frozen legacy
   snapshot would have let the rows silently resurrect), routed around it with a direct atomic-CAS canonical rewrite,
   and verified before/after row counts matched exactly (11,238,191 → 11,228,434, `-9757`, `captured` count unchanged) —
   through one full production consolidator cycle. Filed the resurrection-risk discovery as its own issue
   (`legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md`, flagged as "the main open question: not yet
   observed in production") rather than attempting a fix under time pressure. **🔴 Independent re-verification ~1h later
   (different session) found the 9,757 rows ARE BACK** — same original `attempted_at`/`written_at` timestamps, canonical
   blob `Update time` only ~2 minutes before the check. The predicted resurrection risk is now CONFIRMED LIVE, not
   theoretical — a later consolidator cycle reverted the fix. The delete itself should NOT be re-attempted until
   `legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md`'s P1 fix (special-case the frozen
   `_legacy_seed.parquet` out of the captured-outranks tie-break, or refresh it periodically) lands — re-running the
   same delete now would very likely just revert again on the next cycle. Escalated that issue doc's priority to P0.
   This todo is NOT closeable until the underlying tie-break bug is fixed and the delete is confirmed to hold across
   multiple consolidator cycles, not just one.
2. **Tradfi ohlcv_15m/24h (audit-first, as decided)**: operator's prior confirmed correct — the per-venue
   source-capability infrastructure substantially already exists in UAC (`VENUE_DATA_TYPE_CAPABILITIES`,
   `data_source_continuity.py`). Found and fixed one genuinely stale entry (`unified-api-contracts@78b9e899` — a
   leftover CBOE `ohlcv_15m` registry entry from a Yahoo-VIX feed retired 2026-06-25/26). Honestly flagged two real gaps
   instead of forcing fixes: no downstream OHLCV-aggregation writer exists despite 3 places in the codebase claiming one
   does (feeds `vix_features`), and a phantom `YAHOO_FINANCE` venue with no adapter is likely the dominant remaining
   failure-count contributor (same misclassification shape as the corp-actions fix, flagged not deleted per an existing
   "manifest churn" warning).
3. **Corp-actions (as decided)**: `instruments-service@03f71c81a` stops seeding `corporate_action_confirmed`/
   `earnings_result` into the MTDS tick manifest, scoped precisely to that seeding path only (UAC's shared registry left
   untouched, confirmed via regression test). Correctly detected a real cross-agent dependency (needed finding-2's CBOE
   fix to land first for its golden-fixture test to pass) and waited rather than forcing a red gate through. Historical
   already-seeded rows left as a documented follow-up, matching the mbp_10 precedent.

**New items surfaced this round** (not yet acted on, correctly not rushed): the legacy-seed resurrection risk (cefi,
likely also defi/tradfi), the missing OHLCV-aggregation writer, and the phantom `YAHOO_FINANCE` venue — all
filed/documented, none blind-fixed.

**Total for the full session**: 10 code fixes shipped and independently verified across 6 repos (`alerting-service`,
`deployment-service`×2, `features-service`, `market-tick-data-service`×2, `unified-trading-library`,
`unified-api-contracts`, `instruments-service`×2), all via `quickmerge` with passing tests and green quality gates; 1
fix corrected after adversarial verification caught an overstatement; 3 genuine new issues filed rather than papered
over; 1 item deliberately parked per operator decision; 1 item deliberately left at its existing scope per operator
decision. This plan's original ask is now substantively addressed — remaining open items are either freshly-discovered
follow-up work (expected outcome of a real audit) or explicit operator-parked decisions, not gaps in effort.

## 🔴 2026-07-15 (later) — independent re-verification pass; 1 more overstatement caught + 4 more real fixes landed

A different session picked up this plan's own "New todos (this reconciliation)" section (4 items, all still `- [ ]` at
that point) plus the operator's freshly re-pasted alert batch, dispatched 4 parallel sub-agents against them (per this
plan's own "sub-agents, looping" charter), and independently re-verified every result against real evidence (git log +
CI + direct live-manifest re-queries) rather than trusting self-reports — catching one more overstated "done" claim in
the process, matching this doc's own established pattern (the `_acquire_lock` reopening earlier in this doc):

- **Tradfi ohlcv_15m/24h audit** (already closed above): independently re-derived the same conclusion, corrected a wrong
  claim (`YAHOO_FINANCE` is NOT the dominant `ohlcv_15m` failure contributor — NYSE/CBOE are), and traced WHY the alert
  keeps firing even after both fixes: the `DP_RUN_MOSTLY_EMPTY` detector (`meta_watchers.py`'s
  `_read_attempted_failed_cells`) has **no date-recency window** — it counts `attempted_failed` over the WHOLE manifest
  history, so stale 8+-day-old rows alone permanently exceed its threshold regardless of whether anything is currently
  broken. This is now a confirmed cross-cutting root cause (also explains why mbp_10 and
  corporate_action_confirmed/earnings_result kept alerting after their fixes landed) — flagged as a unified follow-up
  candidate, not yet fixed.
- **Corp-actions seeding fix** (already closed above): independently re-verified end-to-end (regression tests +
  scope-correctness check that UAC's shared registry and features-service's legitimate seeding path are both unaffected)
  — confirmed correct as shipped.
- **🔴 Cefi orphan rows — CORRECTION, see the inline correction on that todo above.** The delete was executed safely and
  correctly at the time, held through one consolidator cycle, but reverted on a LATER cycle — confirmed via a direct
  live re-query (~1h after the original fix) showing the same 9,757 rows back with their original timestamps, and the
  canonical blob's own `Update time` only ~2 minutes before the check. The agent's own filed
  `legacy_seed_captured_outranks_resurrection_risk_2026_07_15.md` had flagged this exact mechanism as a real,
  structurally-present risk but "not yet observed in production" — it has now been observed, live, confirmed. Escalated
  that issue's priority P1→P0. **Do not re-run the cefi delete until that issue's tie-break/seed-freshness fix lands.**
  **🟢 2026-07-15 (later) — the tie-break fix has now SHIPPED**
  (`unified-trading-library@f14b13aeac298f70ea07bbf5ed30ca4f480ab8e9`, option (a) from the issue doc's recommended next
  steps: the frozen `_legacy_seed.parquet` shard is special-cased out of the captured-outranks tie-break by
  shard-identity, in both `manifest_consolidator.py`'s DuckDB merge SQL and `manifest_writer/_read_index.py`'s
  `_merge_shard_frames` Python helper, with 3 new regression tests reproducing the exact resurrection scenario). **This
  does NOT close the cefi-delete todo** — re-running the delete still requires confirming the fix holds across multiple
  production consolidator cycles first (live infra verification, not just shipped code), which is explicitly out of
  scope for the session that shipped the code fix. See the issue doc's own matching dated section for the full writeup.
- **NEW cross-cutting finding, fixed same session**: rows with an `EXPECTED_*`-prefixed `error_reason` were being stored
  under `capture_status="attempted_failed"` instead of `expected_unattempted`/`empty_confirmed` — a real classification
  bug distinct from anything this plan had found before. Broad live re-query found the true scope was **34,260 rows**
  (bigger than the ~7,700 initially estimated), split `EXPECTED_CHAIN_META_ROW_NOT_DOWNLOADABLE` (18,878, CME) and
  `EXPECTED_SOURCE_NOT_AVAILABLE` (15,382, NYSE/KRX/NASDAQ — notably NOT CME, so does not overlap the mbp_10 finding
  despite the same reason string). Data fix (`market-tick-data-service@92d4fb18b`, reclassified all 34,260,
  independently re-verified live: 0 remaining misclassified rows, total row count unchanged) + code fix
  (`unified-trading-library@c08a8d61b`, `ManifestWriter.record_failed()` now rejects `EXPECTED_*`-prefixed reasons,
  mirroring `record_empty()`'s existing guard the other direction) + new issue doc
  (`tradfi_expected_reason_attempted_failed_misclassification_2026_07_15.md`). Both CI green, both independently
  re-verified against the live manifest, not just self-reported.
- **4 genuinely new, still-uncovered `DP_RUN_MOSTLY_EMPTY` cells logged** (not yet fixed — see the todos added above
  this section): the cross-cutting `EXPECTED_*` misclassification bug (now fixed, see above), `defi/dex_pool_state`
  - `defi/lst_rates` (`UPSTREAM_INSTRUMENTS_CATALOG_STALE`, historical, June), `sports/trades` (`VENUE_FETCH_FAILED`,
    freshest of the whole batch — through 2026-07-13), `sports/odds_horizon_bucket_15m` (`MalformedTickFieldError`).

**Revised total**: of this plan's original + re-derived work, 2 items now carry an honest "reverted, needs a real fix
first" status (the `_acquire_lock` race — already open — and the cefi orphan-row resurrection — newly caught) out of
what was otherwise reported as fully closed. This is exactly the pattern this doc's own adversarial-verification
practice is meant to catch — noted, not hidden.

## Second interactive reconciliation round (2026-07-15, later) — new alert batch + parallel-session findings absorbed

Operator pasted a fresh alert batch (2 `DP_CATALOG_NOT_RUNNING`, 4 `DP_RUN_MOSTLY_EMPTY` RESOLVED bookends) and asked
for the remaining decisions. Dispatched 2 investigation agents first: (1) confirmed the `DP_CATALOG_NOT_RUNNING` alerts
are UNRELATED to this session's corp-actions fix (different script entirely, timing precludes it; root causes: sports
has a legitimate monotonic-guard blocking a 6-row catalogue shrink, prediction has been OOM-crashing 3 days straight) —
issue doc filed `dp_catalog_not_running_sports_prediction_2026_07_15.md`. (2) confirmed the 4 RESOLVED bookends are
genuine — traced to a THIRD, independently-shipped fix (not from this session): `market-tick-data-service@92d4fb18`
reclassified 34,260 rows workspace-wide that had `EXPECTED_*`-prefixed `error_reason` but were wrongly stored as
`attempted_failed` instead of `empty_confirmed`, with a companion UTL guard against recurrence. Also confirmed defi
consolidator's issue doc was stale (already fixed 2026-07-14, doc never updated) and corrected it.

**Absorbed a full independent re-verification pass from a different session** (found while re-syncing this plan
mid-round) that: caught the cefi orphan-row delete SILENTLY REVERTING ~1h after landing (the legacy-seed resurrection
risk, previously "not yet observed", is now confirmed live) and escalated that issue to P0 with an explicit
do-not-re-run hold; independently found and fixed the same 34,260-row `EXPECTED_*` misclassification bug; corrected a
wrong claim that `YAHOO_FINANCE` dominates `ohlcv_15m` failures (it doesn't — NYSE/CBOE do); and logged 4 more
genuinely-new uncovered `DP_RUN_MOSTLY_EMPTY` cells (`defi/dex_pool_state`, `defi/lst_rates`, `sports/trades`,
`sports/odds_horizon_bucket_15m`) not yet actioned.

**Presented the consolidated remaining-decisions list to the operator** (compiled via a dedicated Workflow re-scan of
every touched issue doc). Decisions made:

- Legacy-seed tie-break: **special-case the legacy seed out of the merge tie-break** (not periodic re-freeze).
- Alert detector recency window: **purge/reclassify stale rows per-bucket as they come up** (not a systemic detector
  change) — largely already satisfied by the independently-shipped `EXPECTED_*` reclassification.
- Phantom `YAHOO_FINANCE` venue: **operator corrected the framing** — Yahoo Finance is a legitimate DATA SOURCE (not
  venue) already used/intended for DXY/treasuries/KRWUSD daily OHLCV; the manifest/registry needs to correctly model
  this as a source relationship, not delete it as phantom coverage. Re-investigation dispatched with the corrected
  framing.
- Sports catalogue shrink: **investigate the 6-row diff first** before deciding whether to override the guard.

**Dispatched 3 more agents** (this round): (1) P0 fix for the legacy-seed tie-break in
`unified_trading_library/manifest_consolidator.py` — explicitly NOT to re-run the cefi delete itself, that's gated on
this fix holding across multiple consolidator cycles; (2) re-investigation of the Yahoo-Finance-as-source question with
the operator's corrected framing, instructed to reach an honest verdict rather than just validate the operator's belief;
(3) investigation of the sports catalogue's specific 6 missing rows (legitimate shrink vs. bug vs. transient),
diagnosis-only — not authorized to force an `--allow-catalogue-shrink` override itself. Prediction catalogue OOM (memory
bump) and a re-run of the cefi delete (once gated fix confirms holding) remain as pending follow-ups after this round.
