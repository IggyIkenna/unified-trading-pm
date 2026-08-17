---
doc_type: plan
title: Nick AI platform readiness remediation — finalize
summary: >-
  Gated finalize for nick_ai_platform_readiness_remediation_2026_08_16.md — refresh the stale codex honest-coverage
  numbers using the FINAL post-remediation state (not the pre-remediation snapshot), reconcile shipped evidence back
  into the sibling nick_ai + venue-readiness plans, re-check whether the W2 scaffold has been reviewed, then archive.
status: active
nature: process
asset_group: [cross-cutting]
stage: [data, strategy, execution]
repos: [unified-trading-pm, unified-api-contracts]
scope: [admin, engineer]
tags: [nick-ai, readiness-remediation, finalize, codex-refresh]
related:
  [
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /plans/active/nick_ai_platform_disclosure_artifact_2026_08_16.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /codex/02-data/honest-coverage-model.md,
  ]
created: 2026-08-16
source: >-
  task_template.md's "every AO-dispatched plan needs a gated finalize plan" pattern, applied to this LOCAL plan per
  the operator's own explicit instruction to author a "gated finalize companion" alongside the main remediation plan.
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P1
drift_direction: advance-code
depends_on: [nick_ai_platform_readiness_remediation_2026_08_16]
gate_on_depends: true
sequential: true
estimate_class: infra
estimate_baseline_ai_days: 1.0
estimate_calibrated_ai_days: 0.8
assigned_role: data_engineering
effort: medium
last_updated: "2026-08-16"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /codex/02-data/honest-coverage-model.md,
  ]
---

# Nick AI platform readiness remediation — finalize

> **Gated on `nick_ai_platform_readiness_remediation_2026_08_16.md` finishing first** (`depends_on` +
> `gate_on_depends: true` + `sequential: true`). Flip this plan's `status` to `active` only once every todo in the
> main plan is `[x]` — this doc stays `draft` (not ingested) until then, matching the draft-gated-phase-chain
> convention in `task_template.md` §4.

## Todos (execute in order — `sequential: true`)

- [ ] [DOC] P0. **Refresh `/codex/02-data/honest-coverage-model.md`'s certified Layer-1 table** for defi/tradfi/
      sports/prediction, using the FINAL state after the main plan's W1/W3/W4 work has landed — not the 2026-08-16
      pre-audit snapshot, which will itself have moved (e.g. W3 changes what step-13 reports; W4-Sports may change
      the sports Layer-1 completeness if the registry-contradiction fix touches captured-data reachability). Re-run
      the same live `coverage.json` read the pre-audit used (never re-implement); cite the fresh date + generated_at
      timestamp. Done-when: every row in the codex table carries a 2026-08-16-or-later date, `safe-doc-push.sh`
      lands it.
- [ ] [REVIEW] P1. **Reconcile evidence into the sibling plans.** For every `[x]` item in the main remediation plan:
      confirm its `<repo>@<sha>` citation resolves, then add one cross-reference line into
      `venue_readiness_and_registry_hardening_2026_08_16.md`'s relevant contract-step row (step 13 for W3, steps 9/10
      for W4-CeFi, step 11/8 for W4-Sports, step 4 for W4-Prediction) — that plan's own readiness-contract table is
      the durable home for "is this step real now," not a second copy here. Do not re-verify by re-reading the shipped
      code in full; a resolving commit reference is sufficient evidence at this stage.
- [ ] [REVIEW] P1. **Check whether the W2 scaffold has been reviewed.** Re-read the main plan's W2 item — if the
      operator has marked up the [Archetype Feature
      Scaffold](https://claude.ai/code/artifact/c6c345e7-10fb-4679-b9d2-6eada7fc3f6c) and a follow-up declaration
      todo is warranted, open it as a new tracked `- [ ]` item in a fresh small plan (never inline the declarations
      here — this finalize plan's own scope is reconciliation, not archetype-registry engineering). If not yet
      reviewed, leave a one-line pointer and do not block archival on it — W2 review is explicitly operator-paced,
      not a completion gate for this finalize plan.
- [ ] [DOC] P0. **Archive both plans** (this one + the main remediation plan) once every todo above is done and
      unlocked — the standard 6-step ritual (dated archive folder, exact-successor banner, corpus-wide referrer
      fixup). If W2's scaffold review is still outstanding, that's fine — it was explicitly not a gate on this item.

## Progress Log

**2026-08-16 — authored alongside the main remediation plan**, per the operator's explicit "+ gated finalize
companion" instruction. Not yet active — gated on the main plan's completion.

**2026-08-17 — flipped to `active`.** Every dispatched item in the main plan is shipped and verified: W1 (all 3
services), W3, W4 (CeFi/both Sports halves/Prediction), W5. The only 2 items still open there are BOTH deliberately
deferred, not blocked-and-broken: W2's "20 rows not declared" (P2, explicitly operator-paced, no urgency) and the
`market-tick-data-service` todo's own text (now shipped — was blocked on a fleet-wide QG regression from an unrelated
concurrent session, cleared on its own, verified via `check_adapter_contract_regression.py` returning OK before
shipping, no rework needed). Neither blocks this finalize plan's own scope.

**Flag for whoever executes W6 (codex refresh)**: a DIFFERENT concurrent session (not this one) landed a real,
operator-ruled finding directly in the main plan's W3 section on 2026-08-17 — the venue-universe denominator is
`(venue, data_type)` 2-tuples (353 pairs, no instrument_type axis) while coverage numerators often compute at
3-tuple granularity, a genuine unit mismatch the operator ruled to fix by landing the instrument_type axis first
(read the main plan's W3 section in full before starting W6 — this may change what "final" coverage numbers actually
are, separately from anything tracked in this finalize plan). This session did not investigate that thread further
— it's another session's active work, not re-derived or duplicated here.
