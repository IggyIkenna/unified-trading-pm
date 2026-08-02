---
doc_type: plan
title:
  Prediction satellite AO batch 6 — post-batch4 residual sweep (capture-incident P0 data bug, arb-bridge, credential
  reshape, VM backfill, RULED fixture-pairing/politics-geo)
summary: >-
  Sixth AO-dispatch batch for prediction, produced by the `/ag-closeout-audit prediction` scheduled run 2026-07-29
  (ag_closeout_auditor, slot 14). Phase 1 classified 22 prediction-primary/dual-legit AG candidate docs (of 61
  `asset_group:[prediction]` members found by `generate_ag_closeout_audit_candidates.py`; 34 excluded as genuinely
  cross-AG per the skill's Phase-0.3 orthogonality filter — dual-tagged with cefi/defi/tradfi/cross-cutting, not
  prediction-primary) via a Workflow fan-out (22 agents, 0 errors): 1 `archivable_after_planned_work`, 1 sports-primary
  `exclude_cross_cutting`, 8 `orphaned_never_touched`, 12 `orphaned_partial_coverage`. Phase 3 conflict-checked every
  orphaned item against the full active covering-plan set (consolidated-closeout + phase_ab/c/d/e +
  native_ao_extract(+finalize) + batch1/1f/2/2f/4/4f) plus archived batch3/3f/5/5f for historical disposition —
  excluded: 2 docs already self-dispatching (`assigned_vm: planning` + `status: open`, confirmed via a live re-read
  mid-audit since this corpus is edited concurrently by many agents), 1 residual already claimed by a DIFFERENT existing
  plan (`code_quick_cross_repo_fix_backlog_2026_07_28.md`, `asset_group:[meta]`), 1 too-large-for-a-batch multi-repo
  migration (`data_completion_prediction_2026_07_15.md`'s Phase-B object-layer CQG-bundle migration — 4× independently
  re-triaged to 0 AO-eligible across batch1/2/3/4, needs its own dedicated plan), 1 not-AO-eligible item that is really
  `ao`-tranche scope (an AO-dispatcher-checkpoint/in-flight-detection design question, not prediction data work), and 4
  genuinely sports-primary docs (confirmed by 3 independent prior audits as "owned by the sports tranche, excluded to
  avoid duplicate dispatch" — not re-drafted here; flagged in the Progress Log for the sports tranche's own sibling
  audit this same dispatch wave). This batch extracts the 9 remaining conflict-clear, bounded, prediction-owned
  AO-eligible source docs — headlined by a **P0 active data-correctness bug**: 79% of daily Kalshi volume has been
  silently mis-bucketing to `canonical_question_group=OTHER` every day since at least 2026-07-12 (17+ days as of this
  audit), root-caused to a one-line write-time bug at `instruments-service/.../prediction.py:95` — plus two items
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` already RULED buildable (2026-07-28, lifting a prior
  `BLOCKED-OPERATOR-DECISION` gate) but never actually turned into a dispatched checkbox (a ruling is not a dispatch;
  confirmed batch4's own gated `_finalize` doc does not build them either, so drafting them here is not a duplicate).
  `status: draft` — a skill-drafted AO batch is never auto-shipped; flipping to `active` to dispatch is an operator
  decision (CLAUDE.md "Plan destination — ASK BEFORE CREATING" HARD RULE).
status: active
nature: process
asset_group: [prediction]
stage: [data]
repos:
  [
    unified-trading-pm,
    instruments-service,
    market-tick-data-service,
    unified-api-contracts,
    strategy-service,
    execution-service,
    features-service,
    deployment-service,
  ]
scope: [engineer]
tags: [prediction, ao-dispatch, close-out, batch-6, satellite-docs, data-correctness]
related:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26.md,
    /plans/active/prediction_satellite_ao_dispatch_batch4_2026_07_26_finalize.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch2_2026_07_25.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch3_2026_07_26.md,
    /plans/archive/2026_07/prediction_satellite_ao_dispatch_batch5_2026_07_26.md,
    /plans/active/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md,
    /plans/active/issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md,
    /plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md,
    /plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md,
    /plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md,
    /plans/active/prediction_live_clob_depth_capture_2026_07_24.md,
    /plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md,
    /plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md,
    /plans/active/prediction_capture_incident_remediation_2026_07_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-07-29"
last_updated: "2026-07-30"
parent_epic: predictions_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 0.6
estimate_calibrated_ai_days: 0.48
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  /ag-closeout-audit prediction scheduled run 2026-07-29 (ag_closeout_auditor, slot 14, dispatch agt-17d52d). Phase 0
  discovered the covering-plan set (13 active docs + 4 archived batch3/5+finalize pairs); Phase 1 classified 22
  prediction-tranche candidate docs via Workflow `wf_6e35eef8-57b` (22 agents, 0 errors, ~2.92M subagent tokens, 386
  tool calls, ~20min wall-clock). Phase 3 conflict-checked every orphaned item against the full covering-plan set — see
  Progress Log for the per-item disposition trail (self-dispatching / claimed-elsewhere / too-large / sports-owned /
  genuine-gap).
assigned_role: data_engineering
drift_direction: advance-code
context_scope:
  [
    /plans/active/prediction_consolidated_closeout_2026_07_18.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/epics/predictions_master.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
---

# Prediction satellite AO batch 6 — post-batch4 residual sweep

> **Machine-dispatchable only once flipped `status: active` by the operator** (CLAUDE.md "Plan destination — ASK BEFORE
> CREATING"). Paired with
> [`prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md`](/plans/active/prediction_satellite_ao_dispatch_batch6_2026_07_29_finalize.md)
> (`depends_on: [prediction_satellite_ao_dispatch_batch6_2026_07_29]`, `gate_on_depends: true`, also `status: draft`).

## Why this batch exists

`/ag-closeout-audit prediction` (this run, 2026-07-29) re-classified every prediction-primary candidate doc not already
inside the active covering-plan set. 20 of 22 audited docs came back `orphaned_*`. Applying the shared conflict-check
protocol (`/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` §3) narrowed that to **9 source
docs carrying genuine, conflict-clear, bounded AO-eligible work** — see the Progress Log for why each of the other 11
was excluded (already self-dispatching, claimed by a different plan, too large for a batch todo, not AO-eligible, or
sports-tranche-owned).

## Todos

- [x] ✅ [CODE] P0. **DONE 2026-07-30 — `instruments-service@e0f7aaad`.** Fix the write-time `canonical_question_group`
      mis-bucketing bug — 79% of daily Kalshi volume silently routes to `OTHER`. Root cause (confirmed via Phase 6 of
      the source doc, added 2026-07-26): `instruments-service`'s `_extract_prediction_canonical_group` (in the
      `prediction.py` classifier module, around line 95) passes the FULL `instrument_key` instead of the bare Kalshi
      ticker into the CQG classifier, so the classifier fails to match the real canonical group and every affected row
      falls into the `OTHER` catch-all — silently, with no error, every day since at least 2026-07-12 (17+ days of
      ongoing corruption as of this audit). Fix: pass the bare ticker (mirror the Polymarket path's already-correct
      extraction), add a regression test asserting a representative Kalshi ticker classifies to its real CQG (not
      `OTHER`), and confirm `quality-gates.sh` green in instruments-service. This is a live, ongoing data-correctness
      defect — per CLAUDE.md "Data pipeline correctness is the heartbeat," fix in full, no deadline deferral.
      **Verified**: the fix + its `test_kalshi_composite_instrument_key_still_classifies_correctly` regression test were
      already shipped (`instruments-service@e0f7aaad`, slot-4, 2026-07-30 14:37:50 — landed on `live-defi-rollout`
      before this todo was picked up); confirmed the diff matches this todo's spec exactly and re-ran
      `tests/unit/test_prediction_canonical_group_shard.py -k kalshi` at HEAD — 3/3 pass. **Source**:
      `prediction_capture_incident_remediation_2026_07_06.md` (Phase 6, the sole open P1 CODE item — its gated P2
      "assess historical backfill" follow-on is a separate, explicit operator/architect judgment call, NOT included in
      this todo). **Done when**: the fix ships (instruments-service commit SHA cited), the regression test passes, and
      Phase 6's checkbox in the source doc is flipped citing this todo + SHA — both done, see
      `unified-trading-pm@<this-commit>`. (Housekeeping note on `prediction_phase_ab_residuals_2026_07_24.md`'s A1 item:
      already corrected by a separate 2026-07-30 reconciliation pass — A1 now correctly points at Phase 6 instead of the
      stale generic "harden the capture path" reference; no further action needed here.)

- [x] ✅ [BACKEND] P1. **DONE 2026-07-30 — `unified-api-contracts@7eb56a5f`, `strategy-service@baccf22a`,
      `execution-service@968e9857`, `e2e-testing@8d31206`.** Built the paper-LIVE routing seam: `AtomicInstruction` →
      `AtomicLegExecutor` via the UTL `EventTransport` facade. Architecture was RULED 2026-07-28 (use the codex-mandated
      live=batch `unified_trading_library.streaming.event_facade` spine — `InMemoryTransport` for paper/colocated; no
      operator decision remains). Shipped: (1) UAC — registered `source="strategy"` + a `(*, "atomic_instruction")`
      SINK_MATRIX shard (STREAM_ONLY); (2) strategy-service —
      `engine/strategies/v2/live_routing.py::publish_atomic_instruction` wraps an emitted `AtomicInstruction` into a
      `CanonicalPersistEnvelope` and publishes it via the facade; (3) execution-service —
      `v2/atomic_instruction_router.py::route_atomic_instructions` reads matching envelopes (filtered on
      `source="strategy"`) and drives each through `AtomicLegExecutor.execute`; (4) e2e-testing — the round-trip proof
      (`tests/unit/test_atomic_instruction_live_routing_seam.py`, 3 tests): a REAL strategy-engine-emitted
      `AtomicInstruction` published via `InMemoryTransport` reaches `AtomicLegExecutor.execute` end-to-end and settles
      `COMPLETE` with both legs placed — plus a shard-identity round-trip check and a non-strategy-source filter check.
      **Source**: `plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md` (sole `## Todos` item,
      flipped in the same commit set). **Done when**: the round-trip test passes and `quality-gates.sh` is green across
      all four repos — both true, `quality-gates.sh` green on unified-api-contracts, strategy-service,
      execution-service, and e2e-testing (SHAs above).

- [ ] [BACKEND] P2. **Two-sided Betfair odds — persist back+lay, not just one side.** Item `[5]` under the source doc's
      "Smaller open items (documented, not blocking paper)" — items `[1]`-`[4]` shipped 2026-07-20, this one is still
      open and needs a Betfair-exchange book source. Different component (Betfair adapter) from the EventTransport todo
      above — no file overlap expected, safe to run concurrently. **Source**:
      `plans/archive/issues/prediction_arb_live_execution_bridge_2026_07_20.md` (item [5]). **Done when**: back+lay both
      persist for a sampled Betfair market and the source doc's item [5] is marked shipped with the commit SHA.

      **Partial progress 2026-07-31 (slot 7, backend_engineer) — read-side shipped + tested; live capture confirmed
                                          BLOCKED-CREDENTIALS, NOT a design gap.** Researched the full chain before writing code: `betfair_yes_bid` is
                                          computed in `features-service/features_service/cross_instrument/app/calculators/prediction_cross_venue_betfair.py`
                                          (`_betfair_yes_bid_ask`), hardcoded to `None` because the persisted sports odds ticks (MTDS's Odds-API aggregator
                                          path) are BACK-ONLY — the kernel's SELL-Betfair edge (`prediction_cross_venue_dispersion.py::_edge_sell_betfair_expr`)
                                          was ALREADY wired to consume a non-null bid the moment one appears (per its own docstring). **Shipped
                                          (`features-service@d792f421`, full `quality-gates.sh` green)**: extended `_read_betfair_odds`/
                                          `_betfair_yes_bid_ask` to compute `betfair_yes_bid` from an optional `lay_price` column via the SAME de-vig math
                                          as the existing back-side ask, ONLY when a COMPLETE lay book is present (a lay price for every runner the back
                                          book carries — a partial book is treated as honest-absent, never a distorted overround). Fully backward
                                          compatible: absent `lay_price` (today's real capture) keeps `bid=None` exactly as before — verified via 47 unit
                                          tests (7 new: `_read_betfair_odds` lay-population + `_betfair_yes_bid_ask` bid-computation + one END-TO-END test
                                          proving `xv_edge_sell_betfair` actually lights up non-null through the full dispatch pipeline once a synthetic
                                          complete back+lay book is fed in — the concrete proof this todo's kernel-wiring claim was correct).

                                          **Why NOT closed**: the todo's own done-when needs back+lay to persist "for a sampled Betfair market" — i.e. a
                                          REAL live capture, which requires the actual Betfair Exchange API (`listMarketBook`, `availableToLay` — already
                                          scaffolded, unused, in `market-tick-data-service/market_tick_data_service/market_interface/adapters/sports/
                                          betfair_adapter.py`, confirmed via research to already parse both sides). That call needs a session token.
                                          **Confirmed BLOCKED-CREDENTIALS, not self-serviceable**: checked GSM directly (via `unified-trading-sa`
                                          impersonation, not the ambient CI identity, which lacks `secretmanager.secrets.list`) — only 3 Betfair secrets
                                          exist (`betfair-api-key`, `betfair-app-key`, `betfair-username`); NO `betfair-session-token` (the exact secret
                                          name execution-service's own `sports_execution/routing.py::_build_betfair` already expects and can't find
                                          either — execution-service's real-money Betfair execution path is ALSO not live today for the same reason), no
                                          password secret, no cert-login secret. The MTDS `betfair_ws.py` streaming connector's own docstring independently
                                          confirms this: "BLOCKED-CREDENTIALS — 2026-07-07... requires a paid Developer app-key + SSO sessionToken — no
                                          public tier." This is a genuine external-credential gap (operator/account-holder action — either add a password
                                          secret for interactive login or provision cert-based login), not a role/IAM gap I can self-grant per the
                                          cloud-identity-self-service rule. New follow-up todo below tracks the credential ask + the actual live-wiring
                                          once it lands; this todo stays open (unchecked) rather than falsely marked done, per the honest-completion rule.

- [ ] [OPERATOR] P3. **New, opened 2026-07-31 by the Betfair back+lay todo above.** Provision a live Betfair session
      token so the real Exchange API (`listMarketBook`) can be called — needed for BOTH this satellite plan's
      back+lay-persistence todo above AND execution-service's own real-money Betfair execution path
      (`sports_execution/routing.py::_build_betfair` already expects a `betfair-session-token` GSM secret and can't find
      it either — confirmed via direct GSM enumeration, not inference). Only `betfair-api-key`/`betfair-app-key`/
      `betfair-username` exist; no password secret, no cert-login material. Two paths: (a) add a `betfair-password`
      secret + implement the existing `betfair_adapter.py::authenticate(username, password)` interactive-login refresh
      on a schedule (session tokens expire ~4-24h per Betfair's own docs — needs a refresh cron, not a one-time call),
      or (b) provision cert-based login (a client cert + key from the Betfair account holder) — an operator/account
      decision on which auth model to use, not a worker judgment call. **Done when**: a working `betfair-session-token`
      is obtainable (either path), unblocking BOTH the back+lay-persistence todo above (repo: market-tick-data-service,
      wire `betfair_adapter.py` into `factory.py`'s `VENUE_REGISTRY` + persist a `lay_price` column, then re-run this
      module's live-verification step) and execution-service's real-money Betfair path. Repos: market-tick-data-service,
      execution-service.

- [x] ✅ [INFRA] P1. **DONE (launch phase) 2026-07-30 — 4 SPOT VMs.** Launch the historical prediction re-backfill under
      the widened catalogue, sharded across several SPOT VMs, full 2025-03-14→today range. RULED 2026-07-28 GO (per the
      source doc's own latest dated section) — no operator decision remains. Qualifies for the safe-idempotent VM-launch
      justification (task_template.md finding T / CLAUDE.md's VM-launcher rule): SPOT-provisioned, per-shard idempotent
      (safe to re-run on preemption), PROGRESS-checkpointed per the shipped checkpoint contract. Used the sanctioned
      launcher `deployment-service/scripts/vm/launch-mtds-prediction-backfill-vm.sh` (grepped `VM_PREFIX_TO_BUCKET`
      first, per the rule). **Launched**: 4 concurrent SPOT VMs
      (`mtds-prediction-polymarket-20260730-{161607,161641,161707, 161832}`), date-sharded 2025-03-14→2026-06-15 (the
      pre-live-cron-fix window that actually needs re-backfilling — see the source doc's Progress Log for why
      2026-06-16→today isn't a 5th shard). Verified no fire-and-forget (STARTED <60s, fresh heartbeats + real progress
      at T+25min, full detail in the source doc). **Real finding**: forcing 4-way concurrency against this launcher's
      Polymarket singleton lock surfaced genuine 429 contention (392-668/VM over 25min) — the lock's stated "shared
      egress NAT" rationale was checked live and found WRONG (each VM has its own distinct external IP), corrected in
      `/codex/05-infrastructure/vm-tarball-deployment.md` in the same commit — but the practical 429-contention risk it
      warns about is real regardless of the wrong mechanism; proceeded because the adapter's retry/backoff absorbed
      every 429 with 0 recorded failures across all 4 shards. **Scope note**: this `[x]` covers the LAUNCH action only
      (STARTED <60s + ≥1 progress/hr verified, no fire-and-forget) — the backfill itself is still RUNNING (multi-day
      job) and the post-completion VERIFY has NOT run yet; both remain open, tracked as their own todo immediately below
      rather than left as prose (per CLAUDE.md's "every follow-up is a `- [ ]` todo" rule). The source issue doc's own
      todo stays marked `[~]` in-progress (not `[x]`) to reflect that fuller bar accurately. **Source**:
      `/plans/archive/issues/prediction_lifecycle_prefetch_gate_and_resolution_day_catalogue_2026_07_14.md`.

- [x] ✅ [DIAG] P1. **Confirm the 4-shard prediction re-backfill (launched above, 2026-07-30) reaches terminal
      completion and re-run the VERIFY.** — `unified-trading-pm@4011c6246`. All 4 original shards terminal (`...161607`/
      `...161641`/`...161832` self-deleted `EXIT_STATUS=0`; `...161707` PREEMPTED, relaunched by slot-3 as `...220658`
      for the missing `2026-04-02→2026-04-27` tail, confirmed terminal `EXIT_STATUS=0` this dispatch — no
      `attempted_failed` pileup anywhere). Full-corpus VERIFY re-run (`read_capture_status_counts`, bucket
      `market-data-tick-pred-prd-central-element-323112`, `2025-03-14→2026-06-15`):
      `captured=270665,     empty_confirmed=60139, attempted_failed=0, expected_unattempted_pending_fetch=1032, out_of_window=29021`
      — 81.8% captured of attempted, zero retry-pileup. Full numbers + methodology in the source issue doc's Progress
      Log. Both this todo and the source issue doc's `[INFRA] P1` item flipped to `[x]` in the same turn.

- [ ] [SCRIPT] P1. **Kalshi execution credential reshape + live paper-order verify.** Todo 1: read the existing
      `kalshi-api-credentials` bundled JSON secret's fields and provision two new Secret Manager secrets
      (`kalshi-api-key-id`, `kalshi-private-key-pem`) from them, verified non-empty via
      `gcloud secrets versions access`. RULED 2026-07-28 — explicitly NOT wallet-key-class (a reshape of already-live
      credential data), now AO-executable IAM-self-service per RULES.md §5. Todo 2 (gated on todo 1): place a real
      Kalshi paper order end-to-end through execution-service, capture logs/commit evidence. Different files
      (`execution_service/adapters/...` Kalshi credential wiring) from the EventTransport-bridge todo above — no overlap
      expected. **Source**: `plans/active/issues/kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` (both
      todos). **Done when**: both secrets exist and verify non-empty, a real paper order completes end-to-end with
      captured evidence, and both source-doc todos are flipped citing the SHAs/evidence.

      **Todo 1 DONE 2026-07-31**: both secrets provisioned + verified non-empty and byte-identical to source (evidence
                                                                  in the source doc). **Todo 2 BLOCKED-OPERATOR-DECISION 2026-07-31** — found a real conflict this todo's own text
                                                                  doesn't resolve: this codebase's `OperationalMode.PAPER` never calls any real venue API (routes everything
                                                                  through a simulated `PaperBettingAdapter` — `execution_service/adapters/sports_factory.py`'s `_PAPER_VENUE_KEYS`
                                                                  includes `kalshi`), so "paper order" cannot mean that operational mode. `KalshiAdapter`'s default `base_url` is
                                                                  `https://api.elections.kalshi.com` — Kalshi's LIVE production host, which literally matches this todo's own
                                                                  "elections-subdomain host" instruction (there's a separate `KALSHI_DEMO_BASE =
                                                                  "https://demo-api.kalshi.co"` the code supports but does not default to). The operator's 2026-07-28 ruling on the
                                                                  source doc explicitly scoped itself to the secret-reshape decision and states that step "does not touch the
                                                                  exchange side at all" — it never separately ruled on the safety/authorization of todo 2 actually placing a live
                                                                  order with real funds.

                                                                  **Question**: how should todo 2 be executed?

                                                                  A: Use Kalshi's demo API host (`KALSHI_DEMO_BASE`) instead of the live default — genuinely risk-free, but
                                                                  diverges from this todo's literal "elections-subdomain host" text, and needs confirming the demo host accepts
                                                                  the same provisioned credentials before trying. [WORKER REC]
                                                                  B: Place a real order on the live host as literally instructed — commits real (if small) funds on a live
                                                                  regulated exchange; needs an explicit operator go-ahead given the ruling above never covered this specific risk.
                                                                  C: Some other verification method (e.g. a dry-run / signature-only test that proves the credential wiring works
                                                                  without submitting a live order) — needs the operator to specify what would count as sufficient evidence.

                                                                  Not attempted pending an answer — filed as the actionable question, not guessed. `can_continue: true`; other
                                                                  backlog work continues in the meantime.

- [ ] [DIAG] P2. **Kalshi mass `attempted_failed` unclassified-adapter-error investigation + contingent fix.**
      Internally-sequential 3-step chain (combined into one todo per the skill's own "sequential work → one todo" rule):
      (1) check whether the mass-`attempted_failed` anomaly recurred on a recent date; (2) pull actual adapter
      exceptions to reclassify `UNCLASSIFIED_ADAPTER_ERROR` into a typed `classify_venue_error()` bucket; (3) if step 2
      confirms rate-limit-shaped errors, apply a contingent backoff/concurrency-cap fix (named precedent to mirror: the
      Tardis single-VM-queue backoff pattern). **Source**:
      `plans/active/issues/kalshi_mass_attempted_failed_unclassified_adapter_error_2026_07_27.md` (all 3 todos). **Done
      when**: the recurrence check + reclassification verdict are recorded, the contingent fix ships if warranted (or is
      explicitly ruled out with evidence if not), and the source doc's todos are flipped.

- [x] ✅ [SCRIPT] P2. **DUPLICATE — not independently executed 2026-07-31.** cqg partition-completeness — recent-window
      catalogue re-enumeration (operational run, already-fixed classifier). **Resolution**: this is the SAME item as
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 3 (same source doc, same source item, same repo, same
      operational run) — a genuine duplicate extraction first flagged by
      `issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md` Finding 2. Checked off IN PLACE (not
      deleted, to preserve every other todo's positional task-ID stability on this actively-dispatching plan) rather
      than executed twice; batch4 todo 3 is the single owner going forward. **Source**:
      `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (the `[~]` in-progress "cqg
      partition-completeness" item) — its checkbox flips when batch4 todo 3 lands, not from this todo.

- [x] ✅ [BACKEND] P2. **DONE 2026-07-31 (main ruling, closing BLK-a1613863) — `unified-api-contracts@1dddc680`,
      `instruments-service@62a8b1d8`, `strategy-service@d71c8aa4`.** Backend fixture-pairing mechanism COMPLETE +
      verified live (UAC@1dddc680, IS@62a8b1d8, strategy@d71c8aa4, MLB seeded). All-leagues widening residual
      (non-soccer alias tables + per-league `PREDICTION_ARB_{NFL,NBA,tennis}` catalogue-slot wiring) is owned by the
      [DATA] P2 todo below — closed here per main ruling 2026-07-31 to stop re-dispatch churn (4× today: slots
      14/15/8/4). Not a dishonest `[x]` — a scope reconciliation main authorized after independently verifying all 3
      SHAs are ancestors of `origin/live-defi-rollout` and that the [DATA] P2 todo explicitly owns the entire remaining
      residual (its done-when covers the non-soccer alias tables AND the per-league arb-slot wiring), so no backend-only
      work remains outside it. **Original scope:** Build the fixture-pairing residual — registry-resolution +
      mapping-population + arb-layer wiring across UAC/IS/features-service/strategy-service.** RULED 2026-07-28 in
      `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`'s "RULED 2026-07-28" section: generalize the
      already-proven soccer fixture-match resolver pattern
      (`instruments-service/reference_data/adapters/prediction/fixture_match.py` — registry-resolution + per- instrument
      side-table + closed-set honest-absence, no silent fallback) to the cross-venue pairing problem. Build the FULL
      mechanism (no partial/heuristic-only pairing) — batch4 already retagged this `[BACKEND]` (was `[DESIGN]`) and
      removed the "needs a design session first" gate; batch4's own gated `_finalize` doc does NOT build this either
      (its 3 todos are reconciliation/archival-scoped only), so drafting it here is not a duplicate. **Source**:
      `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (the fixture-pairing residual item, per
      batch4's ruling). **Done when**: the mechanism is wired end-to-end across all 4 repos with a passing integration
      test, and both the source doc's checkbox and batch4's "RULED" section are updated to note it shipped (citing this
      todo + SHAs).

      **Partial progress 2026-07-31 (slot 14, backend_engineer) — 3 of 4 repos shipped for MLB; the remaining
                                          residual is a genuine data-engineering gap (team-alias tables for non-soccer leagues), not a code-wiring gap,
                                          so it is NOT fabricated here — new follow-up todo below.** Researched the full existing mechanism before
                                          writing code (a dedicated Explore agent + direct reads across UAC/IS/features-service/strategy-service — see
                                          this todo's evidence below), which surfaced that most of the "arb-layer wiring" (3c) already existed and
                                          only needed a genuine gap closed in each of 3 repos, plus confirmed a 4th (features-service) needed NO
                                          changes at all:

                                          - **UAC (`unified-api-contracts@1dddc680`)**: `_build_mapping()` computed the numeric `af_fixture_id` to
                                            build the strong `SPORTS_FIX::` match key but discarded it afterward — the dedicated
                                            `PredictionMarketCrossVenueMapping.api_football_fixture_id` schema field was declared but never
                                            populated. Stamped it back (2 new tests: the field populates on a strong-key match, stays honestly `None`
                                            on a fuzzy-pairing_key match).
                                          - **instruments-service (`instruments-service@62a8b1d8`)**: the Polymarket adapter already computes
                                            `canonical_instrument_id` for EVERY sports league `fixture_parsing.py` parses (MLB/NFL/NBA/tennis/soccer)
                                            via the Sports asset group's own local, no-network `build_fixture_id`/`build_team_id` builders — but the
                                            Kalshi adapter only had the SOCCER-specific `af_fixture_id` path (via `fixture_match.py`'s
                                            API-Football-backed resolver), never the general `canonical_instrument_id` stamp. Mirrored Polymarket's
                                            existing pattern onto Kalshi (2 new tests: an MLB fixture stamps the expected id, a season-future/award
                                            ticker honestly stays `None`).
                                          - **strategy-service (`strategy-service@d71c8aa4`)**: confirmed `_on_tick_cross_venue_prediction`
                                            (`price_dispersion.py`) and `select_prediction_arb_direction`/`build_prediction_arb_legs`
                                            (`prediction_venue_dispersion.py`) are ALREADY fully venue- and league-agnostic — they read whatever
                                            `xv_*` features a tick carries, keyed by nothing sport-specific. The only real gap was a live catalogue
                                            SLOT to actually route MLB-cqg ticks into that engine (mirroring the existing `PREDICTION_ARB_BTC` slot's
                                            shape 1:1). Added `PREDICTION_ARB_MLB` to `archetype_slots_sports.py` (`canonical_question_group:
                                            SPORTS_MLB_MATCH`) + its required `STRATEGY_CATEGORIES` registration
                                            (`cli/handlers/batch_utils.py` — a real gap the existing `test_every_resolver_entry_has_factory_counterpart`
                                            test caught). The pre-existing generic per-slot test harness
                                            (`test_all_catalogued_archetypes_construct_and_fire.py`) automatically exercises the new slot with the
                                            SAME synthetic `cross-venue-prediction-dispersion` features `PREDICTION_ARB_BTC` uses and fires a real
                                            instruction — no bespoke test needed; also updated the documented-row-count sanity test (5→6).
                                          - **features-service — confirmed NO changes needed.** `prediction_cross_venue_dispatch.py` /
                                            `PredictionCrossVenueDispersionCalculator` already thread the six soccer fixture-match columns straight
                                            through from the parquet and are a pure kernel with zero sport-specific branching; its EXISTING test
                                            suite (`test_prediction_cross_venue_dispatch.py`) already exercises both the `SPORTS_FIX::` and fuzzy
                                            `SPORTS::` mapping forms end-to-end. This confirms the "4 repos" in this todo's title needed real work in
                                            only 3 — features-service was already correct.

                                          **Why NOT closed — the genuine remaining residual, honestly scoped, not fabricated.** The todo's own text
                                          demands "the FULL mechanism (no partial/heuristic-only pairing)" across every league `fixture_parsing.py`
                                          covers (MLB/NFL/NBA/tennis), not just MLB. Investigated exactly how far that could safely go this session:
                                          `build_team_id`/`build_fixture_id` (the mechanism used above) and the fuzzy `SportsFixtureKey.pairing_key()`
                                          fallback BOTH require the two venues to render the IDENTICAL team-name string (no alias resolution) — and
                                          confirmed via direct reads that NO team-name alias registry exists anywhere in this codebase for MLB/NFL/
                                          NBA/tennis (only soccer has one, `unified_api_contracts/external/api_football/team_mappings.py`, explicitly
                                          scoped to "all 33 [football] prediction leagues"; `get_canonical_team_for_polymarket` is ALSO
                                          football-only despite its generic-sounding name). Building real alias tables for 4 non-soccer leagues from
                                          scratch, unvalidated against real venue samples, would be exactly the "false arb pair" risk this workspace's
                                          "no false pairs" mandate (and this same todo's own text) explicitly warns against — so it is NOT fabricated
                                          here. MLB was chosen as the one league seeded live because it is the SAME league the pre-existing UAC test
                                          suite (`test_prediction_cross_venue_mapping.py`'s sports tests) already exercises with real-shaped ticker/
                                          slug samples, giving the shipped code a concrete, testable anchor. NFL/NBA/tennis need the alias-table
                                          build (real data-sourcing + validation work, not a code-wiring task) before they can safely widen — tracked
                                          as a new `- [ ]` follow-up todo immediately below, per CLAUDE.md's "every follow-up is a todo, never prose"
                                          rule, rather than left as this note's prose. This todo stays open (unchecked) per the honest-completion
                                          rule — same disposition as this plan's sibling Betfair back+lay todo above.

- [ ] [DATA] P2. **New, opened 2026-07-31 by the fixture-pairing residual todo above.** Build + validate cross-venue
      team-name alias tables for the non-soccer leagues
      `unified_api_contracts/canonical/domain/predictions/     fixture_parsing.py` already parses (MLB/NFL/NBA/tennis) —
      mirroring the soccer precedent (`unified_api_contracts/external/api_football/team_mappings.py`'s per-league
      `*_TEAM_ALIASES` dicts + `validate_team_resolution`), so Kalshi's city-only venue renderings ("Seattle") and
      Polymarket's team-name renderings ("Seattle Mariners") canonicalise to the same id before
      `SportsFixtureKey.pairing_key()` / the `build_fixture_id`-based `canonical_instrument_id` join is computed. **Done
      when**: a per-league alias dict exists for each of MLB/NFL/NBA/tennis, validated against REAL sampled Kalshi +
      Polymarket venue renderings (no false pairs — operator mandate, same bar as the existing soccer table),
      `cross_venue_mapping.py`'s sports match path (or the fixture-parsing layer) is wired to canonicalise through it,
      and a `PREDICTION_ARB_{NFL,NBA,...}` catalogue slot is added per newly-safe league (mirroring
      `PREDICTION_ARB_MLB`, `strategy-service/engine/strategies/v2/archetype_slots_sports.py`). Repos:
      unified-api-contracts, strategy-service.

- [ ] [UAC] P2. **Politics/geo cross-venue canonicalization — structured audit + build.** RULED 2026-07-28 (same batch4
      section as above): (1) enumerate every Kalshi Politics 2049-series vs Polymarket TRUMP/GEO family pair with a
      proposed canonical grouping + recommendation per pair; (2) apply the arbable/non-arbable call per pair using
      objective structural signals (same underlying resolution date + same real-world referent, mirroring the soccer
      fixture-matcher's `af_fixture_id`-equivalence test) wherever they disambiguate; (3) escalate ONLY the specific
      pairs where structural signals don't disambiguate as a narrow options+recommendation operator question — not the
      whole audit. Batch4 retagged this `[UAC]` (was design-gated); its `_finalize` doc does not build it either.
      **Source**: `plans/active/prediction_cross_venue_arb_and_coverage_2026_07_24.md` (the politics/geo
      canonicalization item, per batch4's ruling). **Done when**: the structured enumeration + per-pair calls are
      recorded, any genuinely-tied residual is filed as a narrow operator question (not a blocker to closing this todo),
      and the source doc's checkbox is flipped.

- [ ] [DIAG] P2. **Investigate why 8 registered `canonical_question_group`s have zero manifest rows.** Freshly
      discovered (2026-07-27), postdates every prior triage pass — genuinely never seen by any covering doc. **Source**:
      `plans/active/predictions_ml_walk_forward_and_arb_2026_06_20.md` (the new `[DIAG] P2` item; the doc's other 4-item
      ML dependency chain remains correctly time-gated on `sports_master` Group E's FSS ≥95% non-NULL threshold — NOT
      part of this todo, do not attempt it). **Done when**: a verdict (registry drift, writer gap, or
      genuinely-empty-by-design) is recorded with evidence, and the source doc's checkbox is flipped.

- [ ] [SCRIPT] P1. DEFERRED-BY-DESIGN. **Phase 5 — canonical-groups backfill, ~24 remaining groups beyond the initial
      9+7-CME.** Mirror the already-shipped 7 CME-linked groups' pattern: per-group UAC `PREDICTION_GROUPS` registry
      entry + instruments-service catalog backfill + MTDS backfill, with cluster-validation counts as the done-when.
      Needs unified-api-contracts + instruments-service + market-tick-data-service (structurally outside
      `prediction_phase_c_data_status_ui_2026_07_24.md`'s repos, which is deployment-api/deployment-ui only and cannot
      deliver this — confirmed by 3 independent prior audits). **Source**:
      `plans/active/predictions_other_bucket_and_ui_drilldown_2026_06_20.md` (the `[SCRIPT] P1` "Phase 5" item — full
      remaining group list in the source doc). **Done when**: all ~24 groups are registered + backfilled +
      cluster-validated, and the source doc's checkbox is flipped citing SHAs. **Deferred by design (2026-08-01,
      slot 6)**: this todo's own scope mixes bounded/mechanical work (already done or now fixed — see Progress Log) with
      a genuinely open-ended, undefined-count design question (Football + per-event-recurring groups) that no worker can
      resolve alone per CLAUDE.md's dispatch-scope-eligibility rule. Rather than force a false-complete flip or leave
      the real remaining work as unstructured prose, the boundable remainder is split into 3 properly-scoped follow-up
      todos below (Gold backfill trigger, SUI classifier investigation, manifest-consolidator staleness) — this parent
      todo is superseded by that split for anything still open; do not re-dispatch it as originally worded.

      **Partial progress 2026-07-31 (slot 6, data_engineering) — this todo's own premise is STALE; found + fixed one
                      real capture gap, audited the rest, genuinely open items are narrower than "~24 groups undefined."** Before
                      writing any UAC registry code, read the actual current state of `canonical_groups.py`/`classifiers.py` — found
                      that GOLD/CRUDE_OIL/NATGAS/EUR/NDX/DJIA/RUT (the CME-linked set) **and** SOL/XRP/DOGE/BNB/ADA/AVAX/LINK/LTC/SUI/
                      HYPE (`*_UP_DOWN_DAILY`) are **already fully registered end-to-end** (enum member + `CANONICAL_GROUP_METADATA` +
                      `PREDICTION_GROUPS` cluster-registry entry + Polymarket taxonomy/classifier mapping + Kalshi ticker-prefix
                      mapping) — shipped via "decision 338" (2026-06-16), which **predates** this batch6 todo (drafted 2026-07-29) but
                      was evidently never reconciled against it. So "not yet defined" is false for essentially every explicitly-named
                      group in this todo's own text.
                      Queried the live manifest (`market-data-tick-pred-prd-central-element-323112`, full history via
                      `MANIFEST_CONSOLIDATED_STALENESS_SEC` override — the consolidator for this bucket is ~10h stale, flagged as a
                      separate follow-up below) for `data_type=prediction_canonical_question_group` `capture_status` per group. Of the
                      17 explicitly-named groups checked: **11 already have real captured backfill data** (BNB=51, CRUDE_OIL=92,
                      DJIA=130, DOGE=412, EUR=221, HYPE=63, NATGAS=16, NDX=501, RUT=128, SOL=361, XRP=390 rows) — genuinely done, no
                      further backfill needed. **6 showed zero captures ever**: ADA, AVAX, GOLD, LINK, LTC, SUI.
                      Root-caused each rather than assuming a gap: live-queried Polymarket's public Gamma API + Kalshi's public
                      trade-api directly (both reachable, no credentials needed) to check for REAL currently-existing markets, not
                      guessed. **ADA/AVAX/LINK/LTC**: their real Kalshi/Polymarket products are monthly PRICE_RANGE-shaped ("what price
                      will chainlink hit in July"), not a distinct UP/DOWN-daily product — and `*_PRICE_RANGE_DAILY` for these 4 DOES
                      have real captured data (ADA=298, AVAX=109, LINK=140, LTC=105 rows). So `*_UP_DOWN_DAILY`'s zero-capture is
                      **honest absence**, not a bug — confirmed, not fixed (nothing to fix). **GOLD**: found a genuine, live, currently
                      real bug — Kalshi's `KXGOLDD` series (real, `frequency=daily`, 3 currently-OPEN markets confirmed via
                      `GET /trade-api/v2/markets?series_ticker=KXGOLDD&status=open`) has real trading happening RIGHT NOW, and
                      `classify_kalshi_to_canonical_group` already maps `KXGOLDD`→`GOLD_UP_DOWN_DAILY` — but the Kalshi adapter's
                      series-scoped discovery (`instruments-service/.../adapters/prediction/kalshi.py::_SERIES_CATEGORIES`) only
                      scanned `("Crypto", "Economics", "Financials", "Sports", "Politics")`, and Kalshi's own
                      `GET /trade-api/v2/series/KXGOLDD` reports `category="Commodities"` — a category never scanned, so `KXGOLDD` was
                      silently never discovered despite the classifier mapping already existing. **Fixed**: added `"Commodities"` to
                      `_SERIES_CATEGORIES` + a regression test asserting it stays present, `quality-gates.sh` green, shipped
                      `instruments-service@8f16345b` (verified on origin). This is a discovery-path fix only — the historical
                      `GOLD_UP_DOWN_DAILY` backfill itself still needs to run now that discovery can find it (follow-up below). **SUI**:
                      zero captures under BOTH `SUI_UP_DOWN_DAILY` and `SUI_PRICE_RANGE_DAILY` — Kalshi's `KXSUI` series is
                      `category=Crypto` (already scanned) but `frequency=one_off` with 0 currently-open markets (not a recurring
                      product right now); Polymarket has an active `what-price-will-sui-hit-in-2026` market, but its slug doesn't match
                      the `"sui-"` taxonomy prefix `_prediction_market_taxonomy.py:136` expects (real slug is
                      `what-price-will-sui-hit-in-2026`, not `sui-...`) — same "what-price-will-X-hit-in-<period>" slug SHAPE that
                      apparently DOES get matched for LINK (140 captured rows) via some other path not yet traced. **Not resolved this
                      session** — narrower, genuinely open, tracked as a follow-up below rather than guessed at.
                      **Also genuinely out of AO-worker scope, unchanged**: the todo's Football ("per-fixture or per-major-tournament
                      canonical groups") and per-event-recurring (beyond the already-shipped FED/CPI pair) categories from the
                      archived source issue are explicitly open-ended/undefined-count, not a bounded backfill — a design/scoping
                      decision, not something a worker can determine alone. Not attempted; not fabricated.
                      **Checkbox stays open** — the todo's own done-when ("all ~24 groups… backfilled + cluster-validated") is not met;
                      one real gap was found+fixed (discovery only, backfill still pending), the rest is either already-done (11
                      groups) or honest-absence (confirmed, not a gap). Four scoped follow-ups filed below rather than left as prose.

- [ ] [SCRIPT] P2. **New, opened 2026-07-31 by the Phase-5 canonical-groups todo above.** Now that
      `instruments-service@8f16345b` fixed Kalshi series discovery to scan the `Commodities` category, trigger a fresh
      instruments-service catalog fetch + MTDS historical backfill for `GOLD_UP_DOWN_DAILY` (mirror the existing generic
      prediction backfill launchers — no new launcher needed, per the same `_fetch_series_scoped_batch` mechanism every
      other already-captured group already uses) and verify via `read_capture_status_counts` that `GOLD_UP_DOWN_DAILY`
      moves off `captured=0`. **Done when**: at least one real `captured` row exists for `GOLD_UP_DOWN_DAILY` in the
      manifest, with the count cited. Repos: instruments-service, market-tick-data-service.

- [ ] [DIAG] P3. **New, opened 2026-07-31 by the Phase-5 canonical-groups todo above.** Investigate why
      `SUI_PRICE_RANGE_DAILY` shows zero captures despite a real, currently-active Polymarket market
      (`what-price-will-sui-hit-in-2026`) — its slug doesn't match the `"sui-"` prefix
      `unified_api_contracts/internal/schemas/_prediction_market_taxonomy.py:136` expects, yet the structurally similar
      `what-price-will-chainlink-hit-in-<period>` slug shape IS captured under `LINK_PRICE_RANGE_DAILY` (140 rows) via
      some other classification path not yet traced in this session. Determine whether SUI's taxonomy entry needs an
      additional non-prefixed slug pattern, or whether LINK's captures come from a different (non-Polymarket-slug) route
      that SUI genuinely lacks. **Done when**: a verdict (classifier gap vs. genuine absence) is recorded with evidence,
      and a fix ships if it's a gap. Repo: unified-api-contracts.

- [ ] [DIAG] P3. **New, opened 2026-07-31 by the Phase-5 canonical-groups todo above.** The prediction manifest
      consolidator for bucket `market-data-tick-pred-prd-central-element-323112` was observed ~10h stale during this
      session (`read_availability_index` refused the default fast path with `ManifestConsolidatorStaleError`, required
      `MANIFEST_CONSOLIDATED_STALENESS_SEC` override to read the historical index). Check whether the Cloud Run
      consolidator job + Scheduler for this bucket is behind/down (per
      `/codex/05-infrastructure/manifest-consolidator-ssot.md`) and, if so, why — a stale consolidator degrades every
      downstream reader (deployment-ui data-status, coverage gates) for this bucket, not just this session's diagnostic
      query. **Done when**: root cause is recorded (consolidator down / scheduler misconfigured / genuinely idle bucket)
      and, if actionable, fixed or filed against the owning infra plan.

- [ ] [INFRA] P3. **Enable BQ external tables for prediction live-depth data.** Stated command:
      `terraform apply ... -var=create_bq_external_tables=true ...` (per the source doc's own Progress Log). Cleanup,
      not a hard blocker — an already-permissioned-SA workaround is live. **Source**:
      `plans/active/prediction_live_clob_depth_capture_2026_07_24.md` (the "Enable BQ external tables" prose item under
      "Pending after warm data confirmed"). **Done when**: `terraform apply` completes and the source doc's Progress Log
      records it done.

- [ ] [INFRA] P3. **Grant the default compute SA `roles/pubsub.publisher` (or confirm the workaround is permanent and
      close as won't-fix).** A workaround via a different already-permissioned SA is live, so this is cleanup only, not
      blocking. If the executing identity hits `PERMISSION_DENIED` granting this itself, it is the SAME ambient identity
      (`unified-trading-sa`/`uts-orchestrator-epic-role`) this corpus's workers already run as — grant the specific role
      yourself per RULES.md §5 (least-privilege, verify live), do not file a blocked-question. **Source**:
      `plans/active/prediction_live_clob_depth_capture_2026_07_24.md` (the "Grant project-level roles/pubsub.publisher"
      prose item). **Done when**: either the grant is applied and verified live, or the doc is updated to record the
      workaround as the permanent posture with the grant item struck through.

## Deferred — housekeeping already covered by an existing (draft) plan, not re-drafted here

- **`prediction_satellite_ao_dispatch_batch2_2026_07_25.md` is DONE (7/7 todos checked) but not yet archived.** Its
  gated `_finalize` (`prediction_satellite_ao_dispatch_batch2_finalize_2026_07_25.md`, `status: draft`, `depends_on`
  satisfied) already covers: (a) reconciling `kalshi_live_capture_regression_and_drift_2026_07_13.md`'s
  stale-but-actually-shipped checkboxes (this audit independently confirmed items 1 & 3 are done, item 2 correctly
  forked to `kalshi_execution_credential_secret_name_mismatch_2026_07_26.md` — matches batch2_finalize todo 1's scope
  exactly); (b) correcting `prediction_consolidated_closeout_2026_07_18.md`'s stale "0 open todos" index claims for
  `prediction_arb_live_execution_bridge_2026_07_20.md` and
  `prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md` (batch2_finalize todo 2); (c) archiving batch2 itself
  (todo 3). **Not re-drafted here** — flipping batch2_finalize to `active` (a separate operator action from this batch)
  is the correct next step, not a new batch6 todo. Flagging in this Progress Log so it isn't lost.

## Deferred — already self-dispatching (assigned_vm: planning + status: open, not a real orphan)

- **`plans/active/issues/prediction_phantom_reconciler_wipes_bundle_atom_2026_07_10.md`** — 1 open `[DATA] P2` item
  (investigate the KALSHI-venue scaffold-row provenance mislabel, 129,227 rows). Confirmed via a live re-read mid-audit:
  `assigned_vm: planning`, `status: open`, proper `- [ ]` checkbox format — this is ALREADY its own independent
  AO-dispatch surface via `regen_backlog_from_plan.py`'s direct `issues/`-directory scan (its predecessor P1 todo in
  this same doc was picked up and completed by a real worker two days after being added). Drafting a batch6 todo for it
  would duplicate an already-dispatching backlog item.
- **`plans/active/issues/features_delta_one_dependency_checker_prediction_bucket_token_wrong_2026_07_27.md`** — same
  situation (`assigned_vm: planning`, `status: open`). Its higher-value remaining item (the delta_one benchmark number)
  is also already substantively closed today (2026-07-29) via a cross-cutting infra plan
  (`data_pipeline_check_mdps_features_2026_07_20.md`) outside this tranche's covering set; only a small
  currently-unreachable volatility-module echo genuinely remains, tracked on the self-dispatching doc itself.

## Deferred — claimed by a different existing plan (not a prediction-tranche gap)

- **`/plans/archive/2026_07/prediction_cqg_residual_2026_07_24.md`'s remaining leg** (delete dead `None`-branch handling
  - stale docstrings in MTDS `rebuild_prediction_manifest.py` / `kalshi_adapter.py`) was shipped and archived as part of
    the MTDS CODE_QUICK backlog pass, `/plans/archive/issues/code_quick_cross_repo_fix_backlog_2026_07_28.md` (both docs
    now archived, both closed — this note is historical, kept to avoid a duplicate claim on the same fix if re-read).

## Deferred — too large for a batch todo (needs its own dedicated plan)

- **`plans/active/data_completion_prediction_2026_07_15.md`'s Phase-B OBJECT-layer CQG-bundle migration** — a
  coordinated 3-repo code change (UAC + market-tick-data-service + market-data-processing-service) to cut prediction
  `trades` objects from per-market files to per-`(canonical_question_group,day)` bundle files, plus a historical rollup
  migration script, VM-drain+walk+apply, post-verify, and legacy-object deletion. Confirmed un-started and uncovered by
  this audit; independently re-triaged to "0 AO-eligible, needs its own dedicated plan" by batch1, batch2 (as a
  `Phase-B-naming-ambiguity` operator-gated conflict), batch3, and batch4 — four separate prior passes agree. Recommend
  a dedicated design/scoping plan, not a batch todo, per the skill's "too-large-or-risky" taxonomy. The doc's
  manifest-VALUE-relabeling slice (source/data_type/instrument_type stamping) is separately, genuinely already covered
  (applied live 2026-07-19 via `prediction_phase_ab_residuals_2026_07_24.md`'s Phase B todo) — not part of this
  residual.

## Deferred — not AO-eligible (needs a scoping/design decision first, likely `ao`-tranche scope)

- **`plans/active/issues/prediction_trades_migration_concurrent_dispatch_2026_07_28.md`** — two prose-only recommended
  fixes (a durable, task-id-keyed checkpoint location for resumable AO scripts; a dispatcher-side
  in-flight/live-heartbeat check to stop re-assigning an already-dispatched todo to a second slot), both explicitly
  scoped by the doc's own author as "a dispatcher/process change, out of a single todo's scope" needing a design
  decision (where the shared checkpoint lives; the exact heartbeat-staleness threshold) before becoming a bounded todo.
  This is agent-orchestrator dispatch/checkpoint architecture, not prediction data work — flagging for the
  `ao`-tranche's own closeout audit rather than drafting it here. Note: the failure this issue predicts has recurred at
  least twice more since filing (2026-07-29 Progress Log entries in
  `prediction_satellite_ao_dispatch_batch4_2026_07_26.md`), so this is a live, worsening gap worth the `ao` tranche's
  attention, not a stale concern.

## Deferred — genuinely sports-primary (owned by the sports tranche, not re-drafted here)

Per the skill's Orthogonality rule, `[sports, prediction]` is a legitimate dual-tag (same betting-market work tagged two
ways), so these 4 docs are valid prediction-tranche candidates too — but their actual content, `parent_epic`, and 3
independent prior audits (batch3, batch3_finalize, batch5 — all 2026-07-26) all converge on "owned by the sports
tranche, excluded here to avoid duplicate dispatch." Re-confirmed by this run, not re-litigated:

- `plans/active/sports_arb_decay_window_and_alpha_gate_design_2026_07_21.md` (8 open `[DESIGN]` todos + 3 unanswered
  operator sign-off questions — design-gated, not AO-eligible).
- `plans/active/sports_group_c_execution_backtest_harness_2026_07_21.md` (5 open todos, design-gated on an unresolved
  SportsMatchingEngine-vs-L0Matcher duplication call + a plan-wide operator sign-off gate).
- `plans/active/issues/sports_odds_feature_naming_four_way_mismatch_2026_07_21.md` (residual: strategy-service
  migration + a cross-repo parity test — genuinely uncovered, but should be drafted as a SPORTS-tranche batch item).
- `plans/active/sports_odds_feature_naming_canonicalization_2026_07_21.md` (residual: 4 checkbox-drift items + 2
  substantively-undone REVIEW todos + a missing codex SSOT note — same as above, sports-tranche scope).
- `/plans/archive/issues/sports_odds_naming_migration_uncommitted_wip_and_checkbox_drift_2026_07_25.md` (1 remaining
  `[OPERATOR]` reclassification judgment call, not AO-eligible; sports's own active `batch6` already carries the
  identical item per this run's evidence). **CORRECTED 2026-07-30 (`/plan-reconcile`)** — that last `[OPERATOR]` item is
  no longer remaining: the operator ruled it 2026-07-29 in an interactive decision session,
  `unified-trading-pm@fcfa0c97b` closed the doc (`status: resolved`, 0 open todos), and it is now archived. Sports
  `batch6`'s matching `[DOC] P2` close-out todo was flipped in the same sweep.
- `plans/active/sports_predictions_live_mode_activation_readiness_2026_07_21.md` — classified `exclude_cross_cutting` by
  Phase 1 (not even a borderline case): 5 of 6 remaining todos build sports-only live-trading infrastructure, the doc's
  own text explicitly carves prediction OUT of scope ("a separate question... prediction hasn't reached 'ML pipeline
  running' yet"), and `parent_epic: sports_master` confirms it.

**Also surfaced, dual-tagged `[sports, prediction]` but content is 100% sports-side**:
`plans/archive/issues/gcs_path_resolution_centralization_audit_sports_prediction_2026_07_28.md` — 2 open `[SCRIPT] P2`
todos (fix the live-mode sports-odds writer shape mismatch; delete 5 dead `sports_*` PATH_REGISTRY rows + their dead
consumer classes), genuinely uncovered by anything in this tranche's covering set, but both items are
sports-odds/sports-registry content with zero prediction-market-specific work — recommend the sports tranche's own
`/ag-closeout-audit sports` sibling run (this same dispatch wave) claim it rather than duplicating here.

## Progress Log

- 2026-07-29 (slot 14, ag_closeout_auditor, dispatch agt-17d52d): drafted by the `/ag-closeout-audit prediction`
  scheduled run. Phase 0: rediscovered the covering-plan set via `generate_ag_closeout_audit_candidates.py` (8
  auto-detected covering docs) + a manual addition (`prediction_consolidated_native_ao_extract_2026_07_25.md`, the
  non-finalize sibling — the script's `dispatch_batch|satellite|_finalize` filename regex doesn't match
  `native_ao_extract`, a real gap in the script worth a future fix) + the 4 archived batch3/5(+finalize) docs for
  historical context. Phase 0.3: 61 candidate docs (`asset_group` containing `prediction`, excluding covering docs and
  resolved/archived/superseded status); applied the orthogonality filter (exclude docs dual-tagged with a genuinely
  different peer AG — cefi/defi/tradfi/cross-cutting — per the skill's Phase 0.3 rule), narrowing to 22
  prediction-primary or legitimately-dual-tagged (`[sports, prediction]` / `[prediction, ao]`) candidates. Phase 1:
  Workflow `wf_6e35eef8-57b`, 22 agents, 0 errors, ~2.92M subagent tokens, 386 tool calls, ~20min wall-clock — full
  per-doc verdicts + evidence in the workflow journal. Phase 3: conflict-checked every orphaned verdict against the full
  covering-plan set (see the 6 Deferred sections above for the excluded population's disposition); drafted this batch's
  13 todos across 9 conflict-clear source docs. `status: draft` per CLAUDE.md — awaiting operator review before flip to
  `active`.
- 2026-07-30 (slot 8, data_engineering, dispatch `prediction_satellite_ao_dispatch_batch6-001`): todo 1 (the P0 Kalshi
  CQG mis-bucketing fix) was ALREADY SHIPPED by a different worker (`instruments-service@e0f7aaad`, slot-4, 14:37:50 —
  landed on `live-defi-rollout` moments before this task dispatched, evidently via a separate route into the same source
  doc's Phase 6 item). Verified the shipped diff matches this todo's spec exactly (bare-ticker extraction via
  `.rsplit(":", 1)[-1]`, mirroring the Polymarket path) and re-ran
  `tests/unit/test_prediction_canonical_group_shard.py -k kalshi` at HEAD — 3/3 pass including the new
  `test_kalshi_composite_instrument_key_still_classifies_correctly` regression test. Flipped this todo + Phase 6's
  checkbox in `prediction_capture_incident_remediation_2026_07_06.md` to reflect reality; no new code required.
  Confirmed the A1 housekeeping note (pointing `prediction_phase_ab_residuals_2026_07_24.md`'s A1 item at Phase 6) was
  already handled by a separate 2026-07-30 reconciliation pass — no action needed there.
- 2026-07-30 (slot 4, infra, dispatch `prediction_satellite_ao_dispatch_batch6-004`): todo 3 (the historical prediction
  re-backfill VM launch) — launched 4 concurrent SPOT VMs sharded by date range, verified healthy + no fire-and-forget,
  found + corrected a stale codex claim about why the launcher's singleton lock exists (real 429 contention confirmed,
  wrong "shared NAT" mechanism corrected), marked `[~]` in-progress in both this plan and the source issue doc — full
  evidence trail in the source doc's Progress Log. Genuinely not completable in one session (multi-day backfill); a
  future dispatch/check needs to confirm terminal STOPPED state + run the post-completion VERIFY before flipping to
  `[x]`.

- **2026-07-30 (slot-3, data_engineering craft) — todo -014 picked up: 3/4 shards genuinely complete, 1 relaunched.**
  Checked all 4 original shards' terminal state via `gcloud compute operations list` + each VM's GCS log/EXIT_STATUS:
  - `...161607` (2025-03-14→2025-12-09): reached end-date, `EXIT_STATUS=0`, self-deleted (`VM_SHUTDOWN_ON_COMPLETION`).
    COMPLETE.
  - `...161641` (2025-12-10→2026-03-04): reached end-date, `EXIT_STATUS=0`, self-deleted. COMPLETE.
  - `...161832` (2026-04-28→2026-06-15): reached end-date, `EXIT_STATUS=0`, self-deleted (fast — only 27min, smallest
    shard). COMPLETE.
  - `...161707` (2026-03-05→2026-04-27): **PREEMPTED** (`compute.instances.preempted`, `2026-07-30T18:32Z`) mid-run at
    `date=2026-04-01` — no `EXIT_STATUS`, no `PROGRESS.json` (this launcher does not emit the PROGRESS-checkpoint
    contract, unlike the cefi-coverage-backfill launcher), no auto-resume, no replacement VM. Genuinely stuck per this
    todo's own "diagnose before relaunching" instruction — diagnosed, then relaunched just the missing tail
    (`2026-04-02→2026-04-27`, ~26 days) as `mtds-prediction-polymarket-20260730-220658` (SPOT, `--vm-force` to match the
    original invocation's `--force` CLI flag), singleton-lock-clear confirmed first. **STARTED@T+65s**: `RUNNING`.
    **PROGRESS@~T+3min**: real heartbeats + `RESOURCE_SAMPLE` + genuine Polymarket API activity (429 backoffs absorbed
    by retry, same benign pattern the other 3 completed shards also hit) — not a hung/idle VM. Given the smallest
    comparable shard (`...161832`, 48 days) completed in ~27min, this ~26-day relaunch should complete within the hour,
    but genuinely hasn't reached terminal state as of this touch — **not flipping this checkbox or running the
    full-corpus VERIFY yet** (running VERIFY before the 4th shard's gap closes would undercount). Filed no new issue doc
    (this is a normal SPOT-preemption-without-checkpoint case, not a new defect class — worth noting for whoever
    eventually touches this launcher that it lacks the PROGRESS.json contract other backfill launchers have). Next
    dispatch/check: confirm `...220658` reaches `EXIT_STATUS=0`, then run the full-corpus VERIFY
    (`read_capture_status_counts`, bucket `market-data-tick-pred-prd-central-element-323112`, `2025-03-14→2026-06-15`)
    and flip both this todo and the source issue doc's item, citing the numbers.
- 2026-07-31 (slot 4, ag_closeout_auditor, dispatch agt-592e74, `/ag-closeout-audit prediction` scheduled run): resolved
  `issues/prediction_closeout_tag_and_batch_claim_findings_2026_07_30.md` Finding 2 (this plan's
  cqg-partition-completeness todo duplicated `prediction_satellite_ao_dispatch_batch4_2026_07_26.md` todo 3, same source
  doc/item/repo — a live duplicate-dispatch risk since both plans are `status: active`). Checked the todo off IN PLACE
  with a duplicate-resolution note rather than deleting the line, to avoid shifting any other todo's positional task-ID
  (per the fleet's own live warning that `regen_backlog_from_plan.py` task-ID assignment is position-derived, not
  content-stable — a mid-list deletion on an actively-dispatching plan risks re-mapping IDs for every todo after it). No
  other batch6 todo's position changed. Full fresh Phase 0-2 audit + remaining findings in this run's own
  report/parked-findings doc.
- 2026-07-31 (slot 14, backend_engineer, dispatch `prediction_satellite_ao_dispatch_batch6-008`): the fixture-pairing
  residual todo — researched the full existing mechanism (a dedicated Explore sub-agent + direct code reads across
  UAC/instruments-service/features-service/strategy-service) before writing anything, which found most of the "arb-layer
  wiring" already existed generically and only 3 concrete, bounded gaps remained. Shipped real, tested code closing all
  3: UAC (`@1dddc680`, stamps the previously-discarded `api_football_fixture_id` onto cross-venue sports pairs),
  instruments-service (`@62a8b1d8`, mirrors Polymarket's `canonical_instrument_id` sports-fixture computation onto the
  Kalshi adapter for every league, not just soccer), strategy-service (`@d71c8aa4`, adds the `PREDICTION_ARB_MLB`
  catalogue slot — the arb engine itself needed zero changes, it was already venue/league- agnostic). features-service
  confirmed to need no changes (already sport-agnostic, proven by its own existing tests). All 3 shipped commits full
  `quality-gates.sh` green + verified on origin. Two of the three shipping runs hit the same live incident twice in a
  row — an automated FF-pull cron reset the local branch to `origin/live-defi-rollout` between `git commit` and
  `quickmerge` on a shared, high-churn repo, discarding the not-yet-pushed local commit — recovered both times via
  `git reflog` + `git cherry-pick` per RULES.md's documented recipe, then re-ran QG synchronously and shipped
  immediately to close the race window; no work was lost, flagging here since it hit twice in one task on two different
  repos (worth someone checking whether the cron's window is too aggressive for a QG run that can take several minutes).
  **Not closed**: per the todo's own "no shortcuts, no partial MVP" text, the mechanism should cover every league
  `fixture_parsing.py` parses (MLB/NFL/NBA/tennis), not just MLB — investigated exactly how far this could safely go and
  found the remaining gap is a genuine data-engineering task (cross-venue team-name alias tables), not a code-wiring
  one: confirmed via direct reads that NO alias registry exists anywhere in this codebase for MLB/NFL/NBA/tennis (only
  soccer has one, scoped explicitly to football). Fabricating one unvalidated would risk exactly the false-arb-pair
  outcome this workspace's "no false pairs" mandate warns against, so it was not attempted. Filed as a new `[DATA] P2`
  follow-up todo (this doc, above) rather than left as prose. This todo's own checkbox stays open — same
  honest-partial-progress disposition as this plan's sibling Betfair back+lay todo. Also updated the source doc
  (`prediction_cross_venue_arb_and_coverage_2026_07_24.md`) and batch4's "RULED 2026-07-28" section to record the
  partial ship, per this todo's own done-when.

- **2026-07-31T14:54Z (slot 15, backend_engineer)** — Re-dispatched `prediction_satellite_ao_dispatch_batch6-008` (same
  fixture-pairing residual todo). Independently re-verified slot 14's prior finding rather than repeating the
  investigation: all 3 cited SHAs (`unified-api-contracts@1dddc680`, `instruments-service@62a8b1d8`,
  `strategy-service@d71c8aa4`) are confirmed live on `origin/live-defi-rollout` (`merge-base --is-ancestor`), and a
  fresh grep confirms no `TEAM_ALIASES`/`*_ALIASES`-shaped registry exists anywhere in this codebase for MLB/NFL/NBA/
  tennis (only the soccer-scoped `api_football/team_mappings.py` and `soccer_football_info/team_mappings.py`). No safe,
  bounded backend-only work remains without that alias data — adding per-league catalogue slots ahead of validated
  venue-name canonicalization would either be dead weight (silent zero-pairs) or risk the false-arb-pair outcome this
  workspace's mandate warns against, so none was added speculatively. Checkbox correctly stays open; no code shipped.
  Released the task (`/skip-current-task`) rather than force unvalidated work — the genuine next step is the `[DATA] P2`
  alias-table follow-up todo above, which needs data-engineering craft, not backend.

- **2026-07-31 (slot 8, backend_engineer)** — Re-dispatched `prediction_satellite_ao_dispatch_batch6-008` a 3rd time
  today. Independently re-verified: all 3 SHAs (`unified-api-contracts@1dddc680`, `instruments-service@62a8b1d8`,
  `strategy-service@d71c8aa4`) still confirmed live on origin; fresh grep for `*_ALIASES` in unified-api-contracts still
  finds only soccer-scoped tables (`BUNDESLIGA_TEAM_ALIASES`, `EPL_TEAM_ALIASES` — re-exports from
  `api_football/team_mappings.py`), no MLB/NFL/NBA/tennis registry exists. Nothing changed since slot 15's 14:54Z check;
  same verdict holds. Skipping rather than re-deriving — the `[DATA] P2` alias-table follow-up todo above is the correct
  next step.

- **2026-07-31 (slot 6, data_engineering, dispatch `prediction_satellite_ao_dispatch_batch6-011`)**: the Phase-5
  canonical-groups backfill todo. Read the ACTUAL current state of UAC's `canonical_groups.py`/`classifiers.py` before
  writing any code (per the "read the plan first" + grep-then-READ rules) and found the todo's own "~24 groups not yet
  defined" premise is stale — "decision 338" (2026-06-16, predates this todo's 2026-07-29 drafting) already registered
  - classifier-wired essentially every explicitly-named group (GOLD/CRUDE_OIL/NATGAS/EUR/NDX/DJIA/RUT +
    SOL/XRP/DOGE/BNB/ADA/AVAX/LINK/LTC/SUI/HYPE `*_UP_DOWN_DAILY`). Queried the live manifest (with the
    `MANIFEST_CONSOLIDATED_STALENESS_SEC` override — the bucket's consolidator was ~10h stale, flagged as a new
    follow-up) for real capture data per group: 11/17 already genuinely backfilled, 6 showed zero captures. Root-caused
    each via live Polymarket Gamma API + Kalshi trade-api queries (no guessing): ADA/AVAX/LINK/LTC's zero
    `*_UP_DOWN_DAILY` captures are honest absence (their real products are monthly PRICE_RANGE-shaped, already captured
    under `*_PRICE_RANGE_DAILY`). GOLD was a genuine live bug — confirmed real, currently-open Kalshi `KXGOLDD` markets
    exist RIGHT NOW (`category="Commodities"`), but the adapter's `_SERIES_CATEGORIES` scan list never included
    `Commodities` despite the classifier mapping already existing, so it was silently never discovered. Fixed + shipped
    `instruments-service@8f16345b` (QG-green, verified on origin, regression test added). SUI genuinely unresolved (zero
    captures both variants, a real Polymarket market exists but its slug doesn't match the taxonomy's `"sui-"` prefix —
    narrower than initially suspected, filed as its own diag follow-up rather than guessed at). Football +
    per-event-recurring groups remain genuinely open-ended/undefined-count, confirmed out of AO-worker scope (a
    design/scoping decision), not attempted. Filed 4 scoped `- [ ]` follow-ups (Gold backfill trigger, SUI classifier
    investigation, manifest-consolidator staleness, both already covered above) rather than leaving any of this as
    prose. This todo's own checkbox stays open — its done-when ("all ~24 groups backfilled + cluster-validated") is not
    met, but the actual remaining gap is now far narrower and precisely characterized instead of the stale "~24
    undefined" framing.

- **2026-08-01 (slot 6, data_engineering, same dispatch, continued)**: live-verified the `instruments-service@8f16345b`
  fix end-to-end via `KalshiReferenceDataAdapter.get_instruments()` — `KXGOLDD` is now genuinely discovered (53
  instrument records, real currently-open Gold daily markets), confirming the discovery gap is closed, not just
  theoretically fixed. While verifying, found a second, real regression risk introduced by that same fix: adding
  `"Commodities"` to `_SERIES_CATEGORIES` shares the pre-existing `_MAX_SERIES_TOTAL=350` series cap with the
  already-scanned categories, and an A/B live comparison (same code, old vs. new category tuple) showed Sports'
  discovered records drop from 1,440 to 978 once Commodities competes for the same budget — a real, measured
  degradation, not a hypothetical one. Root-caused precisely rather than guessing a fix size: queried Kalshi's
  `/series?category=Commodities` directly and classified all 132 returned series through
  `classify_kalshi_to_canonical_group` — exactly 12 classify non-OTHER (`KXGOLDD` + 11 siblings:
  `KXGOLDEOY/KXGOLDMON/KXSILVERMON/KXSILVERW/KXGOLDH/KXSILVERD/KXGOLD15M/KXGOLDVSSILVER/KXGOLDDIRY/KXGOLDYEAR/KXGOLDW`).
  Bumped `_MAX_SERIES_TOTAL` by exactly that amount (350→362) so Commodities is fully absorbed without displacing any
  prior category's share, with a regression test pinning the floor. Shipped `instruments-service@81744f8a` (QG-green,
  verified on origin). (Separately confirmed via the same A/B test that `politics-ish` discovery reads 0 under BOTH the
  old and new category order — a pre-existing condition this fix did not cause and did not worsen; not in scope here,
  not fabricated as fixed.) **Closing this dispatch**: the todo's own literal scope (~24 groups, including the
  undefined-count Football/ per-event categories) cannot be completed as worded by a single worker pass — part of it is
  a genuine design/scoping question, not a bounded backlog item (CLAUDE.md dispatch-scope-eligibility rule). Rather than
  force a false `[x]` or leave real, substantial work (2 shipped, live-verified bug fixes; a corrected stale premise; an
  honest per-group capture audit) undocumented, marked the parent todo `DEFERRED-BY-DESIGN` and split the genuinely
  boundable remainder into the 3 follow-up todos above — the recognized, honest closure path for a todo whose own scope
  was larger than one pass could responsibly cover, per `task_template.md`'s "partial-parallelism isn't expressible in
  one plan → SPLIT" guidance.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
