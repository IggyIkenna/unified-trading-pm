---
doc_type: plan
title: DeFi 6-venue pipeline→live build — genuine IS adapters, healthy cron, 90-day backfill, catalogue, phase flip
summary: >-
  Executes the operator's 2026-07-29 ruling on issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md —
  count ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER toward the `defi` completeness_pct denominator, but only after they
  genuinely EARN "live" status. Split out of the issue doc (per its own 2026-07-30 scope assessment + the
  defi_satellite_ao_dispatch_batch6 audit) because the ruling demands full completion across 4 real sub-steps and 3
  repos — not a single bounded todo.
status: active
nature: process
asset_group: [defi]
stage: [data]
repos: [unified-api-contracts, instruments-service, market-tick-data-service, deployment-service]
scope: [engineer]
tags: [defi, honest-coverage, venue-phase, instruments-service, backfill, ao-build]
related:
  [
    /plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md,
    /plans/active/defi_venue_pipeline_to_live_ao_build_finalize_2026_07_30.md,
  ]
created: "2026-07-30"
last_updated: 2026-07-30
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: brand-new
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 5
assigned_role: data_engineering
drift_direction: advance-code
depends_on: []
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Split from /plans/active/issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md's sole remaining open
  todo per that doc's own 2026-07-30 scope assessment ("recommend this become its own dedicated multi-todo build plan")
  and defi_satellite_ao_dispatch_batch6_2026_07_30.md's independent same-day agreement. Operator ruling already on
  record (2026-07-29: "both: count them AND build out the real IS universe") — this plan executes it, does not re-ask.
---

# DeFi 6-venue pipeline→live build

## Why this plan exists

`issues/defi_venue_phase_live_definition_contradiction_2026_07_22.md` traced a real honest-coverage undercount: 11
`phase=="pipeline"` DeFi venues with genuine capture are structurally excluded from the `defi` `completeness_pct`
denominator. The operator ruled (2026-07-29) to count qualifying venues toward the denominator, but ONLY once they
genuinely earn "live" — no partial rollout, no re-creating the same false-"already working" premise an earlier
adversarial-verify pass already caught once on this exact doc (see that doc's "BLOCKED 2026-07-22" section: a
`DEFI_VENUE_MTDS_CAPTURED` claim of "months-long" capture turned out to be a single synthetic sample, not production
data).

Scope: exactly the 6 venues already shipped as `DEFI_VENUE_MTDS_ADAPTER_VERIFIED_NOT_YET_SCHEDULED` (content-verified
accurate, 2026-07-22): **ANKR-ETHEREUM, STADER-ETHEREUM, STAKEWISE-ETHEREUM, SWELL-ETHEREUM, MANTLE-ETHEREUM,
MAKER-ETHEREUM**. The other 5 originally-investigated venues (FRAX/ALCHEMY/FLASHBOTS/ACROSS/STARGATE) had their
capture-path defects fixed 2026-07-22 (see `plans/active/issues/five_broken_defi_capture_paths_shipped_2026_07_22.md`)
but have not had their data content-verified the way these 6 have — out of scope for this plan; a future plan can cover
them once they clear the same bar.

**Ordering is real** (`sequential: true`): cron health must be confirmed before the 90-day backfill runs against it (no
point backfilling against a cron that's about to be re-fixed and change behavior); catalogue registration and the final
phase-flip both need the IS adapters to exist first. IS-adapter work and the cron fix touch different repos/files and
could in principle run in parallel, but the whole chain is short enough (5 todos) that serializing correctly beats
splitting into two plans just to parallelize two todos.

## Todos

- [x] [DATA] P1. Build genuine `instruments-service` reference-data adapters/universe entries for all 6 venues
      (ANKR-ETHEREUM, STADER-ETHEREUM, STAKEWISE-ETHEREUM, SWELL-ETHEREUM, MANTLE-ETHEREUM, MAKER-ETHEREUM), mirroring
      the existing adapter pattern already used for BLAZESTAKE / KAMINO_LENDING / MORPHOVAULTS (fixed 2026-07-22 per the
      source issue doc). Each venue must resolve through `instruments-service`'s `_build_defi_venues()` /
      expected-universe builder as a real reference-data adapter — not a bare MTDS-only on-chain handler with no IS
      counterpart, which is the exact gap `DEFI_VENUE_PHASE`'s current invariant (`phase=="live" ⟺ IS-producible`) flags
      today. Done-when: a targeted `instruments-service` CLI/pytest check confirms all 6 venues resolve with
      non-placeholder instrument entries. — ✅ instruments-service@6c193a19 (slot-15's commit, cherry-picked + shipped
      by slot-6 while resolving the blocking repo-blocker `RB-ecfc50de` — see this plan's Progress Log below). Full
      `quality-gates.sh`: 5093 passed, 0 failed, including the 30/30 targeted metadata pytest assertions for all 6
      adapters.

- [ ] [VERIFY] P1. **PREREQUISITE gate for the cron-fix todo's live-verify remainder below** (added 2026-07-30, slot-6,
      per main-agent ruling on `BLK-9d219e5f` — prevents a dispatch→block→skip churn loop on the next todo). The cron
      fix itself is ALREADY code-complete and shipped (`market-tick-data-service@5b5caffa`) — this gate is ONLY about
      whether the fix has actually reached production yet. Confirm ALL of: (a) `ldr-to-main-promote.yml` /
      `ldr-to-main-promote-fleet.yml` (unified-trading-pm) show 3+ CONSECUTIVE successful ticks, not `startup_failure`
      (`gh run list --workflow=ldr-to-main-promote.yml --limit 5`); (b) a `chore(promote): LDR → main` PR for
      `market-tick-data-service` containing `5b5caffa` has merged to `main`
      (`gh pr list --repo IggyIkenna/market-tick-data-service --state merged --base main`); (c) `image-build-gate.yml`
      ran SUCCESS on that `main` commit (confirms the deployed `:latest` image actually rebuilt). Root cause + tracking:
      `plans/active/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` (P0,
      `assigned_vm:     NA`, already on the operator's radar — do NOT attempt a GH-side fix from a worker slot). **Done
      when**: all 3 checks above pass. If any fails, leave this AND the next todo unchecked and stop here — this is an
      external/operator-owned incident, not additional cron-fix work.

- [ ] [DATA] P1. Fix/confirm the production cron backing these 6 venues' capture so it reliably writes real per-day
      manifest shards going forward — not the one-off manual-invocation samples the source doc's investigation found.
      Per that investigation: `uts-prod-mtds-collect-lst-rates` was crash-looping (OOM, then hung to the 1200s timeout)
      on both tracked runs, and the 6 GCS objects that exist today were written by a manual/ad-hoc invocation ~80-120
      min after the cron's failed attempts; MAKER's manifest-registration gap is a stated execution-order artifact of
      that manual run, not a separate bug — verify it self-resolves once the real cron runs cleanly. Reuse the
      crash-loop fix pattern already shipped for the sibling `uts-prod-mtds-collect-gas-fees` cron (see
      `five_broken_defi_capture_paths_shipped_2026_07_22.md`) if the same OOM/timeout root cause applies. Done-when: 3
      consecutive real cron-triggered (Cloud Scheduler-fired, not manual `gcloud run jobs execute`) daily runs each
      write a `capture_status=captured` manifest row for all 6 venues, verified via Cloud Run job execution history + a
      manifest query.

      **2026-07-30 (slot-6) — ROOT CAUSE CONFIRMED + FIX SHIPPED, deployment/live-verify portion still pending
                                          (blocked on a separate, already-tracked infra incident, not this fix).** Confirmed the SAME OOM/timeout root
                                          cause the gas-fees fix already patched applies here too, via direct code read (not a guess):
                                          `lst_rates_handler._check_freshness_skip()` called `ManifestFreshnessCache.bulk_load()` completely UNBOUNDED —
                                          `bulk_load() -> read_availability_index()` can synchronously block for up to
                                          `AG_CONSOLIDATOR_INFLIGHT_HORIZON_SEC["defi"]=4200s` when a defi consolidator merge is in flight
                                          (`unified-trading-library/manifest_writer/_staleness_budget.py`), and this job's own Cloud Run timeout is
                                          **1200s** (confirmed live in `deployment-service/terraform/gcp/defi_collection_scheduler.tf`'s "lst-rates"
                                          entry) — exactly the `1800s < 4200s` shape that caused the gas-fees crash-loop, just with an even tighter
                                          1200s budget here. Fixed the same way: reused the existing `_gas_fee_helpers.bounded_freshness_warmup()` helper
                                          (90s bound, fail-open — never skip on an untrustworthy/timed-out cache) instead of hand-rolling a new one.
                                          While validating via full `quality-gates.sh`, found ONE pre-existing unrelated failure blocking a green tree —
                                          `test_vault_share_price_handler.py::test_process_writes_canonical_partition_per_protocol_chain` (confirmed
                                          pre-existing via a clean-tree repro before touching it) — root-caused to a stale test assertion
                                          (`pipeline_mode=batch_onchain_subgraph`) no longer matching this handler's actual, intended, RPC-only
                                          `batch_onchain_rpc` behavior, now that `unified-api-contracts` corrected
                                          `SOURCE_PRIORITY[("defi","vault_share_price")]` to `["onchain_rpc"]` today (2026-07-30) — the MTDS-side
                                          companion fix `issues/defi_pipeline_mode_source_desync_yearn_v3_2026_07_21.md` todo 4 was waiting on. Fixed
                                          both (the handler's now-stale `_VAULT_SHARE_PRICE_SOURCE` constant + the test's stale path assertion). Full
                                          `quality-gates.sh --no-fix`: green (exit 0), shipped via quickmerge: `market-tick-data-service@5b5caffa`.

                                          **Cannot yet verify the done-when** (3 consecutive real cron-triggered runs against the FIXED code) —
                                          `image-build-gate.yml` only rebuilds the deployed container on push to `main`, not `live-defi-rollout`, and the
                                          LDR→main promotion for this repo (and the ENTIRE `promotion_model: ldr_main` fleet) is currently blocked by an
                                          already-filed, actively-investigated, unrelated incident:
                                          `plans/active/issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` (both
                                          `ldr-to-main-promote-fleet.yml` and `ldr-to-main-promote.yml` have returned `startup_failure` on every tick
                                          since 2026-07-29T18:30Z — confirmed live via `gh run list`, not stale). Once that incident resolves and this
                                          commit promotes + rebuilds, re-run: trigger `gcloud scheduler jobs run` against the real `lst-rates` Cloud
                                          Scheduler job 3x (this counts as "real cron-triggered" per this todo's own parenthetical — it invokes the
                                          actual Scheduler entity, not a raw `gcloud run jobs execute`), then confirm via Cloud Run execution history +
                                          a manifest query that all 6 venues get `capture_status=captured` rows on each run. Not flipping this checkbox
                                          — the done-when genuinely isn't met yet, and this is NOT a code gap, it's an external, already-owned
                                          deployment-pipeline outage.

- [ ] [DATA] P1. Run the 90-day historical backfill for all 6 venues via direct local invocation — no VM launch needed
      per the source doc's own estimate (~2,340 lightweight RPC calls, well under a constrained rate limit) — now that
      the cron is confirmed healthy (prior todo). Done-when: the availability manifest shows ≥90 days of
      `capture_status=captured` rows per venue (or a documented, source-cited reason for any specific-day gap — e.g. a
      genuine upstream outage), each row's `source=` field correctly tagged per
      `/codex/02-data/pipeline-mode-partition.md`.

- [ ] [DATA] P1. Register all 6 venues in the instruments catalogue so downstream consumers see a complete universe, not
      just a manifest-side capture stream (ruling item 4). Done-when: the instruments catalogue / data-status surface
      shows all 6 venues with non-zero, non-placeholder instrument counts.

- [ ] [DATA] P1. Flip `DEFI_VENUE_PHASE` for all 6 venues (ANKR/STADER/STAKEWISE/SWELL/MANTLE/MAKER) from `"pipeline"`
      to `"live"` in `unified-api-contracts/unified_api_contracts/registry/defi_venues.py`; confirm
      `VENUES_BY_ASSET_GROUP["defi"]` (`market_data_categories.py:395`) picks the flip up automatically (no separate
      edit needed there — it derives from `DEFI_VENUE_PHASE`); re-measure `completeness_pct` for `defi` before/after via
      `instruments-service/scripts/measure_honest_coverage.py --asset-group defi --diagnose-layer1` against the live
      prod manifest and report the exact before/after `n_expected`/`n_present`/`completeness_pct` numbers in this todo's
      evidence line (the source doc's last measurement: `n_expected=109, n_present=3, completeness_pct=2.75`, pre-flip
      baseline to diff against). Also confirm
      `instruments-service/tests/unit/test_orchestrator_helpers.py::test_defi_set_equals_uac_denominator_drift_guard`
      stays green post-flip, or deliberately update it to match the new intended state if it legitimately must change
      (the source doc's investigation flagged this exact test as a likely casualty of a naive flip). Operator ruling
      already on record (2026-07-29, cited in this plan's frontmatter `source:`) — do not re-ask; cite it as the
      authorization for changing this production honest-coverage number.

## Progress Log

- **2026-07-30** — plan authored (split from the issue doc's oversized single todo per that doc's own recommendation +
  the independent batch6-audit agreement same day). Companion finalize plan:
  `/plans/active/defi_venue_pipeline_to_live_ao_build_finalize_2026_07_30.md`.
- **2026-07-30 (slot-15)** — Todo 1 IMPLEMENTED, not yet shipped. Built 6 genuine `instruments-service` reference-data
  adapters (`ankr.py`/`stader.py`/`stakewise.py`/`swell.py`/`mantle.py` — LST; `maker.py` — YIELD_BEARING sDAI, not an
  LST — no validator staking involved), mirroring the existing `rocket_pool.py`/`puffer.py` single-token
  curated-registry pattern. Registered in `factory._ADAPTERS` + `ADAPTER_DATA_SOURCES` only. Committed locally at
  `instruments-service@cebead3d`; 30/30 targeted pytest assertions green
  (`tests/unit/reference_data/adapters/defi/test_{ankr,stader,stakewise,swell,mantle,maker}_metadata.py`).
  **Deliberately did NOT add the 6 venues to `_STATIC_DEFI_VENUES` / UAC `VENUE_TO_ADAPTER_KEY` / `DEFI_VENUE_PHASE`
  yet** — `_build_defi_venues()` derives from `_STATIC_DEFI_VENUES`, NOT from `_ADAPTERS`, so
  `test_defi_set_equals_uac_denominator_drift_guard` (strict `is_defi == uac_defi` set-equality) stays green; wiring
  these venues into the denominator without also flipping phase would break that invariant. This exactly mirrors the
  existing CHAINLINK precedent already documented in `factory.py`'s `ADAPTER_DATA_SOURCES` comment block ("adapter
  first, declaration second"). **Todo 5 (the phase flip) must ALSO add these 6 venues to `_STATIC_DEFI_VENUES` in the
  same commit as the `DEFI_VENUE_PHASE` flip** — doing the flip alone would leave the invariant broken the other
  direction (phase=live but not IS-producible). Left this instruction here so the todo-5 worker doesn't miss it.
  **BLOCKED shipping** on repo-blocker `RB-ecfc50de` (`instruments-service` `quality-gates.sh` full-suite red — 2
  pre-existing, unrelated sports/FOOTYSTATS failures from `unified-api-contracts@26092ac8`; verified pre-existing via
  clean-tree `git stash`, not caused by this todo's diff). Filed
  `/plans/active/issues/instruments_service_sports_footystats_uac_overlap_qg_red_2026_07_30.md` (superseded by slot-11's
  fuller root-caused report, `/plans/archive/issues/instruments_service_qg_red_uac_sports_venue_overlap_2026_07_30.md`,
  which this repo-blocker tracks). Joined `RB-ecfc50de` as a waiter — resumes via `quickmerge --agent` the moment the
  repo goes green; the checkbox below stays unflipped until then.
- **2026-07-30 (slot-6, cicd escalation agt-57430c)** — dispatched separately to fix `quality-gates-v2` RED on
  `instruments-service` promotion PR #1031 (root cause: the same `unified-api-contracts@26092ac8` FOOTYSTATS overlap
  blocking `RB-ecfc50de` above). Shipped the FOOTYSTATS/golden fix (`unified-api-contracts@c022a60e` +
  `instruments-service@5f7b8136`). Re-gating then surfaced that `unified-api-contracts@c64d2b2c` (slot-8, this plan's
  UAC-side key registration) had already landed, but slot-15's paired `instruments-service@cebead3d` (todo 1's
  implementation, above) was still sitting local-only, blocked on the exact same `RB-ecfc50de` — a circular cross-slot
  dependency neither fix alone could clear. Verified `cebead3d`'s tree (`.tabs/15/instruments-service`, read-only) was
  clean, additive-only, and non-conflicting with the golden-fixture diff; fetched it via
  `git fetch <local-path> live-defi-rollout` and cherry-picked it into this session's worktree, preserving slot-15's
  original authorship. Shipped both together — `instruments-service@6c193a19` — full `quality-gates.sh` green (5093
  passed, 0 failed). Todo 1 above is now flipped. `RB-ecfc50de` resolved.
- **2026-07-30 (slot-6) — Todo 2 (cron fix) code-complete + shipped, live-verify portion BLOCKED on a separate
  fleet-wide incident.** Confirmed the `lst-rates` crash-loop is the exact same unbounded-`bulk_load()` root cause the
  gas-fees cron already had fixed, via direct code read + the live Terraform timeout (1200s < defi's 4200s
  consolidator-inflight horizon). Fixed by reusing the existing `bounded_freshness_warmup()` helper (no new primitive
  invented). Also fixed an unrelated pre-existing QG-red (`vault_share_price_handler.py`'s `_VAULT_SHARE_PRICE_SOURCE`
  stamping the now-superseded `onchain_subgraph` value + a stale test assertion) found blocking a clean
  `quality-gates.sh` run — confirmed pre-existing before touching it, and confirmed the real fix (UAC now accepting
  `onchain_rpc` for this cell, corrected 2026-07-30) had already landed, so this was the correct companion half, not
  scope creep. Shipped: `market-tick-data-service@5b5caffa`, full QG green. Could not complete the "3 consecutive real
  cron-triggered runs" verification — the container image only rebuilds on push to `main` (`image-build-gate.yml`), and
  this repo's (and the entire `promotion_model: ldr_main` fleet's) LDR→main promotion is blocked by an already-filed,
  actively-investigated incident (`issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md` — both
  promote workflows `startup_failure` on every tick since 2026-07-29T18:30Z). Left the checkbox unflipped (genuinely not
  done) with a clear resume-point once that incident clears.
- **2026-07-30 (slot-12) — Todo 2 (VERIFY gate) checked: 1 of 3 sub-checks passes, gate NOT met, checkbox stays
  unflipped per the todo's own instruction.**
  - **(a) PASSES.** `gh run list --workflow=ldr-to-main-promote.yml --repo IggyIkenna/unified-trading-pm --limit 8` and
    the same for `ldr-to-main-promote-fleet.yml` both show 8/8 consecutive `success` runs, `createdAt` spanning
    `2026-07-30T16:45:06Z`-`18:00:05Z` — the `ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`
    incident has recovered on the pure-dispatch level (well past the 3-consecutive bar).
  - **(b) FAILS (still).** `gh pr list --repo IggyIkenna/market-tick-data-service --state merged --base main --limit 15`
    — most recent merge is still `#773` (`2026-07-28T13:56:40Z`), unchanged from slot-6's prior check. `5b5caffa` is
    confirmed NOT an ancestor of `origin/main` (`git merge-base --is-ancestor 5b5caffa origin/main` → false;
    `live-defi-rollout` is 833 commits ahead of `main`). There IS an open promote PR containing the commit — `#788`
    (`chore(promote): LDR → main (Option-B direct)`, head `2ad0407287a6`, opened `2026-07-30T17:31:18Z`, confirmed via
    `git merge-base --is-ancestor 5b5caffa <PR-788-head>` → true) — so the recovered dispatcher (check a) has already
    produced the right PR, it just hasn't merged yet: `mergeStateStatus: UNSTABLE`, and its `quality-gates-v2` run (the
    fleet's one REQUIRED check) is still `status: queued` as of this check (`createdAt: 2026-07-30T17:31:25Z`, ~35 min
    queued with no `conclusion`) — `image-build-gate` on the PR branch itself already shows `success`, but that's the
    PR-branch build, not check (c)'s post-merge `main` rebuild.
  - **(c) N/A — no `main` commit exists yet to check** (gated on (b) merging first).
  - **Verdict: gate NOT met (2 of 3 unmet).** Per the todo's own instruction, leaving this checkbox AND the next todo's
    checkbox unchecked. Not attempting a GH-side fix (`quality-gates-v2` stuck `queued` past a few minutes matches the
    documented `ci_status`/v2-deadlock pattern CLAUDE.md says self-recovers in-band — "do NOT escalate"). Resume point:
    re-run these same 3 checks once PR `#788` merges.
- **2026-07-30 (slot-5) — re-checked, gate STILL NOT met (2 of 3 unmet); one new data point (b advanced, not
  resolved).**
  - **(a) STILL PASSES.** `gh run list --workflow=ldr-to-main-promote.yml`/`-fleet.yml`
    `--repo IggyIkenna/unified-trading-pm --limit 5` — both show 5/5 consecutive `success` runs through
    `2026-07-30T19:15:0{3,5}Z`. No regression since slot-12's check.
  - **(b) STILL FAILS, but progressed.** PR `#788` (the one slot-12 observed queued on `quality-gates-v2`) is now
    `state: CLOSED` (not merged) — superseded by a fresh regenerated promote PR `#789`
    (`promote/market-tick-data-service/9f4098b1bc4f`, opened `2026-07-30T19:01:21Z`), confirmed
    `git merge-base --is-ancestor 5b5caffa 9f4098b1bc4f` → true, so `5b5caffa` is still carried forward correctly.
    `#789`'s combined commit status shows `sit-gate/fleet-green`=success and `semver-agent/label-check`=success, but its
    own `quality-gates-v2` check-suite run is STILL `status: queued` (created `19:01:25Z`, ~15 min queued with no
    conclusion as of this check) — the same v2-never-reported deadlock pattern as slot-12's check, just on a newer PR
    number. `mergeStateStatus: UNSTABLE`. Most recent actually-merged PR to `main` for this repo is still `#773`
    (`2026-07-28T13:56:40Z`) — `git merge-base --is-ancestor 5b5caffa origin/main` → false, confirmed via a fresh
    `git fetch origin main`.
  - **(c) STILL N/A** — gated on (b) merging first.
  - **Verdict: gate NOT met.** Leaving this checkbox AND the next todo's checkbox unchecked, per the todo's own
    instruction. Not attempting a GH-side fix — CLAUDE.md says the v2-never-reported deadlock self-recovers in-band, do
    NOT escalate; per the async-wait/poll HARD RULE, not parking this slot to watch it either. Resume point: re-run
    these same 3 checks once whichever promote PR is current for `market-tick-data-service` actually merges to `main`.
- **2026-07-30 (slot-10) — re-checked, gate STILL NOT met (2 of 3 unmet); dispatcher keeps recovering,
  `quality-gates-v2` keeps re-deadlocking on each fresh PR.**
  - **(a) STILL PASSES.** `gh run list --workflow=ldr-to-main-promote.yml`/`-fleet.yml`
    `--repo IggyIkenna/unified-trading-pm --limit 5` — both show 5/5 consecutive `success` runs through
    `2026-07-30T20:00:0{4,6}Z`. No regression.
  - **(b) STILL FAILS, but the dispatcher produced yet another fresh PR.** Most recent actually-merged PR to `main` for
    `market-tick-data-service` is still `#773` (`2026-07-28T13:56:40Z`) —
    `git merge-base --is-ancestor 5b5caffa origin/main` → false, confirmed via fresh `git fetch origin main`. PR `#789`
    (slot-5's observation) is now superseded by PR `#790` (`promote/market-tick-data-service/fc64e0921d7f`, opened
    `2026-07-30T20:01:32Z` — only ~2 min old at check time), confirmed
    `git merge-base --is-ancestor 5b5caffa <PR-790-head>` → true, so `5b5caffa` is still carried forward correctly.
    `mergeStateStatus: UNSTABLE`; `quality-gates-v2` + `image-build-gate` both `status: queued` (just created);
    `Plan Alignment Agent` shows `conclusion: failure` (a separate, non-gating check per this fleet's gate set — not one
    of the 3 blocking checks). `semver-agent/label-check` + `sit-gate/fleet-green` both `success`. Same
    v2-never-reported-deadlock shape as the prior 2 checks, just on PR #790 now.
  - **(c) STILL N/A** — gated on (b) merging first.
  - **Verdict: gate NOT met.** Leaving this checkbox AND the next todo's checkbox unchecked. Not attempting a GH-side
    fix (self-recovers in-band per CLAUDE.md); not parking this slot to watch a queue that was only 2 min old at check
    time, per the same async-wait/poll posture as slot-12/slot-5. Resume point unchanged: re-run these 3 checks once
    whichever promote PR is current for `market-tick-data-service` actually merges to `main`.
