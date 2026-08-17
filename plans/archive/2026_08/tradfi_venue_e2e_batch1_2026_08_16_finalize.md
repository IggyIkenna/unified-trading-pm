---
doc_type: plan
title: tradfi venue e2e wiring batch 1 — finalize
summary: >-
  Gated closeout for tradfi_venue_e2e_batch1_2026_08_16.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Re-verifies evidence, runs the standard 6-step archival ritual on the batch
  plan, and checks whether all 5 AG batches are now closed so venue_e2e_wiring_2026_08_16.md's own Definition of
  done can be flipped.
status: complete
nature: process
asset_group: [tradfi]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [venue-readiness, e2e-wiring, tradfi, ao-dispatch, satellite-batch, close-out, finalize]
related:
  [
    /plans/active/tradfi_consolidated_closeout_2026_07_18.md,
    /plans/archive/2026_08/tradfi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
  ]
created: "2026-08-16"
last_updated: "2026-08-17"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
drift_direction: advance-code
depends_on: [tradfi_venue_e2e_batch1_2026_08_16]
gate_on_depends: true
sequential: true
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: review
effort: low
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/tradfi_venue_e2e_batch1_2026_08_16.md,
    /plans/active/venue_e2e_wiring_2026_08_16.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored
  in the same turn as its batch, 2026-08-16 interactive session.
---

# tradfi venue e2e wiring batch 1 — finalize

> **Machine-gated on** [`/plans/active/tradfi_venue_e2e_batch1_2026_08_16.md`](/plans/active/tradfi_venue_e2e_batch1_2026_08_16.md)
> (`depends_on` + `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`.

## Todos

- [x] ✅ [REVIEW] P1. **Independently re-verified — 2026-08-17.** All 7 of that batch's todos re-confirmed
      (brief's "5" was stale — batch has 7 checked todos). 3 distinct cited SHAs, all confirmed ancestors of
      `origin/live-defi-rollout` AND diff-content-checked against their claims: `unified-trading-pm@48f83481ce`
      (steps 1-5 + step 9 investigation write-up, docs-only), `features-service@be2af7b191`
      (`CrossVenueCalculator._resolve_baseline_venue()` dominant-venue fallback +
      `test_cross_venue_calculator_missing_baseline_multi_venue_uses_dominant` present), `strategy-service@ff6c00870a`
      (`get_position_adapter()` `"ibkr" | "cme" | "cboe" | "nasdaq" | "nyse" | "ice" | "fx"` match arm +
      `test_factory_tradfi_venues_route_to_ibkr` present). Cross-referenced citations all resolve: `data_completion_
      tradfi_2026_07_15.md` (Yahoo-interim), `service_config_ownership_and_instruction_contract_2026_08_12.md:487`
      (`IBKR_FUND_MOVE` unfinished-capability), `plans/archive/2026_08/issues/tradfi_finding_e1_unsourced_operator_
      ruling_citation_2026_08_03.md`, `plans/archive/2026_07/tradfi_consolidated_native_ao_extract_2026_07_25.md` —
      no dangling citations found.
- [x] ✅ [REVIEW] P1. **DONE 2026-08-17 (slot-13).** Ran the 6-step archival ritual on
      `tradfi_venue_e2e_batch1_2026_08_16.md` (all 7 todos `[x]`, unlocked, `archive_exempt: true` dropped as
      routine hygiene per the archival commit): `status: complete`, `git mv` to
      `plans/archive/2026_08/tradfi_venue_e2e_batch1_2026_08_16.md`. Referrer sweep: 3 corpus hits found
      (`venue_e2e_wiring_2026_08_16.md:152` link — repointed to the archive path with an "archived — done" note;
      `sports_venue_e2e_batch1_2026_08_16.md` — 3 bare prose mentions, not path-shaped links, left as-is per the
      ritual's own "cites a path" scope; `INDEX.md` — auto-generated, regenerated via
      `regenerate_active_plan_inventory.py` below rather than hand-edited). No codex contract change — this batch
      shipped 2 code fixes (`features-service@be2af7b191`, `strategy-service@ff6c00870a`) already covered by their
      own tests; nothing new to establish as an SSOT rule. This finalize doc archives together with the batch plan
      in the same commit (single-repo/mode-1 combined flip+archival, sanctioned per
      `plan-completion-and-archival-discipline.md` § "No-double-gate" 2026-08-10 narrowing) once todo 3 below also
      confirms no further action is needed.
- [x] ✅ [REVIEW] P1. **DONE 2026-08-17 (slot-13).** Checked all 5 AG batches: `cefi_venue_e2e_batch1_2026_08_16.md`
      2 open, `defi_venue_e2e_batch1_2026_08_16.md` 4 open, `sports_venue_e2e_batch1_2026_08_16.md` 2 open,
      `prediction_venue_e2e_batch1_2026_08_16.md` 7 open — only `tradfi` (this finalize's own upstream) is done.
      **Not all 5 archived — no action** on `venue_e2e_wiring_2026_08_16.md`'s Definition of done section; a
      sibling finalize will find the all-5-done condition true once the last batch closes.

## Progress Log

**2026-08-17 — todo 1 (evidence re-verification) done.** Re-verified all 7 checked todos in
`tradfi_venue_e2e_batch1_2026_08_16.md` (brief cited "5", stale — actual count is 7). All 3 distinct cited SHAs
(`unified-trading-pm@48f83481ce`, `features-service@be2af7b191`, `strategy-service@ff6c00870a`) confirmed
ancestors of `origin/live-defi-rollout` via `git merge-base --is-ancestor`, and each commit's diff content
independently checked against its claim (not just the commit message). All cross-referenced doc citations
resolve. No discrepancies found. Batch plan itself now shows 0 open todos — next finalize todo (archival
ritual) is dispatchable.
