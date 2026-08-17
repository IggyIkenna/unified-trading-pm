---
doc_type: issue
title: market-tick-data-service — adapter-contract-call baseline regressed on live-defi-rollout HEAD (blocks every quickmerge)
summary: >-
  quickmerge's STEP 5.70 (IS-MTDS CONTRACT INTEGRITY / check_adapter_contract_regression)
  fails on market_tick_data_service/engine/orchestrator/__init__.py: 5 contract-call
  pattern occurrences found, baseline requires 6. Landed directly on live-defi-rollout
  HEAD by commit bd07cfc3 (CeFi date-concurrency Phase 1, F1-F8 refactor, slot-4) — not
  caused by, or fixable from, an unrelated PR. Blocks every subsequent
  market-tick-data-service quickmerge until either the missing contract-call site is
  restored or the baseline is regenerated with an explicit intentional-change rationale.
status: open
nature: issue
resolved_by:
locked_by:
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer]
tags: [quickmerge, adapter-contract-baseline, shard-level-failure-isolation, blocking]
created: 2026-08-16
source: >-
  Discovered mid-ship of nick_ai_platform_readiness_remediation_2026_08_16.md W1 (MTDS
  external market-data router) — quickmerge's pre-flight passed once the sibling
  unified-api-contracts dependency (another concurrent agent's WIP) went clean, but the
  re-triggered STAGE 3 quality-gates.sh re-gate (forced by "HEAD moved — a peer likely
  pushed", i.e. bd07cfc3 landing mid-run) then failed STEP 5.70 on a file this session
  never touched.
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
related:
  [
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
  ]
drift_direction: advance-code
depends_on: []
---

# market-tick-data-service — adapter-contract-call baseline regression on live-defi-rollout HEAD

## Measured

- Gate: `check_adapter_contract_regression` (quickmerge STAGE — "[5.70/6] IS-MTDS CONTRACT
  INTEGRITY"), baseline file
  `unified-trading-pm/scripts/quality_gates/adapter_contract_baseline.yaml`.
- Failing entry: `market-tick-data-service/market_tick_data_service/engine/orchestrator/__init__.py`
  — baseline `count: 6`; live count (grep for
  `classify_venue_error|ADAPTER_FETCH_FAILED|record_captured|record_empty|record_zero_rows|
  record_failed|record_catalog_unavailable|record_shard_failure`) is **5** (4×
  `classify_venue_error`, 1× `ADAPTER_FETCH_FAILED`) as of HEAD `bd07cfc3`.
- `git status --porcelain` on this file in the affected checkout is clean — the count drop is
  baked into the committed HEAD, not a working-tree artifact.
- `git log -1 -- market_tick_data_service/engine/orchestrator/__init__.py` → `bd07cfc3
  fix(orchestrator): make per-date state process-scoped + get blocking preflight off the event
  loop` (author `ikennaigboaka [slot-4·laptop]`, 2026-08-16 22:43:15 +0100), a large, deliberate
  "CeFi date-concurrency Phase 1 (F1-F8)" refactor — commit message is detailed and reasoned, not
  an accidental lint-sweep wipe (contrast with the 2026-05-20 incident the gate's own error text
  cites). A 27-line removal at the old `_emit_non_trading_day_expected_empties` region (diff hunk
  `-519,27 +534,0`) is the most likely site of the count drop, but this was not confirmed line-by-
  line against the diff before filing (bounded investigation — see "Not done" below).

## Impact

Blocks **every** `market-tick-data-service` quickmerge from this point forward (not scoped to any
one PR) until resolved — the regression is on `live-defi-rollout` HEAD itself, which every
quickmerge run pulls via the Not-Behind Gate before re-gating.

## Not done (bounded investigation, handed off)

- Did not confirm whether the dropped contract-call site is a genuine architectural regression
  (a shard-failure path that lost its `classify_venue_error`/`record_*` classification — the
  shard-level-failure-isolation HARD RULE) or an intentional consolidation the F1-F8 refactor
  should have paired with a baseline regeneration (`--regenerate-baseline`, cited in the gate's
  own remediation text as the correct path when the count change is legitimate).
- Did not attempt a fix — this is `slot-4`'s own commit and refactor; guessing at the correct
  restoration without their F1-F8 context risks either masking a real regression or fighting an
  intentional design change.

## Needed

Either: (a) `slot-4`/whoever owns the CeFi date-concurrency plan confirms the count-6→5 change is
intentional and regenerates `adapter_contract_baseline.yaml` with that rationale recorded, or (b)
if unintentional, restore the missing `classify_venue_error`/`record_*` call site in
`engine/orchestrator/__init__.py`. Either resolves the blocker for all pending
market-tick-data-service quickmerges.

## Progress Log

**2026-08-16 — filed.** Discovered as a blocking side-effect while shipping
`nick_ai_platform_readiness_remediation_2026_08_16.md` W1 (MTDS external market-data router, a
fully unrelated file set — `api/main.py` + `api/routers/`). Confirmed not caused by that change
(clean `git status` on the affected file; regression pre-dates and is independent of the W1 diff).
Filed rather than fixed per the findings-triage rule (outside every plan this session is working,
ambiguous intentionality) — see `/codex/12-agent-workflow/measurement-claims-discipline.md` on not
guessing past a bounded investigation.

**2026-08-17 — na-eligibility-audit.** [body-hash:81969e197c23c7ba] KEEP-NA, valid — First audit pass (fresh doc,
created 2026-08-16, no prior marker; 0 checkbox todos, pure narrative blocking issue). The doc's own "Needed"
section poses a binary (regenerate the baseline as intentional vs. restore a missing shard-failure-isolation call
site) the filer explicitly declined to resolve alone, citing risk of masking a real regression or fighting an
intentional design change without the F1-F8 refactor author's context — a genuine unresolved judgment call, not a
bounded worker-alone task. Doc stays assigned_vm: NA.
