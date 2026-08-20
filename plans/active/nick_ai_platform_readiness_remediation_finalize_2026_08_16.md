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
parent_epic: security_and_cross_cutting_master
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
last_updated: "2026-08-20"
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
context_scope:
  [
    /plans/active/nick_ai_platform_readiness_remediation_2026_08_16.md,
    /plans/epics/system_readiness_master.md,
    /plans/active/venue_readiness_and_registry_hardening_2026_08_16.md,
    /codex/02-data/honest-coverage-model.md,
    unified-api-contracts/scripts/generate_venue_universe_denominator.py,
    /plans/active/data_pipeline_completion_2026_08_21.md,
  ]
---

# Nick AI platform readiness remediation — finalize

> **Gated on `nick_ai_platform_readiness_remediation_2026_08_16.md` finishing first** (`depends_on` +
> `gate_on_depends: true` + `sequential: true`). Flip this plan's `status` to `active` only once every todo in the
> main plan is `[x]` — this doc stays `draft` (not ingested) until then, matching the draft-gated-phase-chain
> convention in `task_template.md` §4.

## Todos (execute in order — `sequential: true`)

- [x] [DOC] P0. ✅ Done 2026-08-18 — `unified-trading-pm@<see commit below>`. **Refreshed
      `/codex/02-data/honest-coverage-model.md`'s certified Layer-1 table** using the `/honest-coverage-dump` skill
      (never re-implemented — read `gs://central-element-323112-honest-coverage/2026-08-17/coverage.json`'s own
      `layer_1.by_asset_group` block verbatim, generated_at `2026-08-17T00:49:33Z`). New certified numbers: cefi
      94.52% (69/73), defi 83.08% (108/130), tradfi 67.74% (21/31), sports 79.03% (49/62), prediction 100.00% (4/4,
      denominator now COMPLETE — no longer gated). **Self-caught and corrected an error before shipping**: this
      todo's own text (above) assumed the refresh needed the instrument_type-axis landing as a prerequisite. Checked
      that assumption directly rather than trusting it — it was WRONG. `expected_universe.py` (the actual builder of
      Layer-1's EXPECTED tuples) has always sourced `VALID_DATA_TYPES_BY_AG_AND_INSTRUMENT_TYPE` directly, never
      `VenueCapabilityRecord`, so Layer-1 was never blocked on the axis; the coverage.json read also predates the
      axis commit by ~19h. The axis landing is real but feeds a DIFFERENT script
      (`generate_venue_universe_denominator.py`, cited in `venue_readiness_and_registry_hardening_2026_08_16.md`),
      not this codex table. Recorded the correction IN the codex doc itself (visible, not silently rewritten) so a
      future reader doesn't inherit the same wrong assumption. Also re-ran `/readiness-state-dump` (the plan's other
      Tuesday-dump skill) — byte-identical to its own original verification run, confirming it likewise doesn't
      consume the axis registry. Both dumps' full diff evidence + a new stray-tuple-growth follow-up are tracked in
      `/plans/active/data_pipeline_completion_2026_08_21.md` § "Tuesday dumps" (that plan's own "re-run both dumps"
      todo and this one are the same piece of work, done once).
- [x] [REVIEW] P1. ✅ Done 2026-08-17. **Reconciled evidence into the sibling plan** —
      `unified-trading-pm@<pending, see commit below>`. Added a "Shipped evidence" cross-reference section to
      `venue_readiness_and_registry_hardening_2026_08_16.md` immediately after its readiness-contract table, mapped
      by the table's real step NAMES (not the guessed numbers this todo's own text used, which didn't fully match —
      "step 4" does not fit the Prediction item; cited against the PAPER-READY clause instead). All 6 shas verified
      to resolve. Found in the process: this finalize plan's own earlier W3 checkbox read as "done, axis extended"
      but the extension (`venue_granularity.py`) is a fidelity-tier query with per-instrument_type *exceptions*, not
      an *enumeration* of which instrument_types exist per (venue, data_type) — a different fact, and NOT what the
      artifact's coverage denominator needs. Confirmed directly:
      `unified-api-contracts/scripts/generate_venue_universe_denominator.py` still computes the 2-tuple denominator
      from `VENUE_DATA_TYPE_CAPABILITIES` alone. This correction is now recorded in the cross-reference section
      itself so it isn't re-misread the same way again.
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

**2026-08-17 — reconciliation todo done; W6 now formally BLOCKED-ON, not just cautioned.** Confirmed 2 other live
`claude` processes share this exact slot's checkout (PIDs verified via `lsof` cwd, matching the SessionStart
collision warning) — one of them is almost certainly the author of both the W3 banner and a brand-new epic,
`/plans/epics/system_readiness_master.md` (created 2026-08-17, P0, target 2026-08-25), which already lists both
nick_ai plans in its own `related_plans` and carries "Land the instrument_type axis on `VenueCapabilityRecord`" as
its own W3 P0 todo, citing the same operator ruling. Did NOT attempt to build that axis myself — real collision
risk (same slot, same registry files) and it is now clearly owned elsewhere. Instead: (1) corrected an
over-optimistic reading of my own earlier W3 completion note — `venue_granularity.py` answers a fidelity-tier
query, not an instrument_type-set enumeration, confirmed by reading `generate_venue_universe_denominator.py`
directly (still 2-tuple-only); (2) shipped the "reconcile evidence into sibling plans" todo, adding a cross-reference
section to `venue_readiness_and_registry_hardening_2026_08_16.md` mapped by the table's real step names (the
finalize todo's own guessed step numbers didn't fully match — step 4 doesn't fit the Prediction item, cited against
the PAPER-READY clause instead); (3) added an explicit `BLOCKED-ON:system_readiness_master` marker to the W6 todo
above. Remaining open in this plan: W6 itself (blocked as stated) and the "check W2 scaffold review" todo (asked
the operator directly in-session rather than trying to infer it from files). Archival stays gated on both.

**2026-08-18 — W6's blocker cleared.** `system_readiness_master.md` W3's "Land the instrument_type axis" item
shipped `unified-api-contracts@d19866d339` (2026-08-17): denominator re-measured 353 `(venue, data_type)` pairs →
660 `(venue, instrument_type, data_type)` triples (12 cells, 3.4%, disclosed unresolved). The stale "353" figure at
this Progress Log's line 113 above is a historical record of what was true when written — left as-is rather than
edited, since it accurately describes that day's state. Proceeding to execute W6 now using the two dump skills
(`/honest-coverage-dump`, `/readiness-state-dump`) that `data_pipeline_completion_2026_08_21.md` shipped for exactly
this re-measurement — see that plan's "Tuesday dumps" section for the shared "re-run after the axis lands" todo,
which this session's W6 work also satisfies (one re-run, two plans' evidence).
- **na-eligibility-audit 2026-08-17** [body-hash:e69f016a4e685458]: KEEP-NA, valid -- Gated finalize companion (depends_on + gate_on_depends: true on the main nick_ai remediation plan) -- criterion (b) applies directly. Of its 3 open todos: todo 1 (W6 codex refresh) carries an explicit 2026-08-17 BLOCKED-ON marker redirecting the actual instrument_type-axis prerequisite work to a DIFFERENT doc, /plans/epics/system_readiness_master.md W3, 'owned by a different live session -- do not duplicate it here' (criterion c, redirect); todo 2 depends on the OPERATOR's own external review status of a Claude.ai artifact (explicitly described as 'operator-paced'); todo 3 (archive both plans) is gated on todos 1-2 completing first, per its own text ('once every todo above is done and unlocked').
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries) -- added `/plans/epics/system_readiness_master.md`
  (the epic W6 is now formally `BLOCKED-ON`, per this doc's own 2026-08-17 Progress Log), the sibling
  `venue_readiness_and_registry_hardening_2026_08_16.md` plan (evidence was reconciled into it this same doc's run), and
  `generate_venue_universe_denominator.py` (the script this doc's own findings cite twice as still 2-tuple-only).
- **na-eligibility-audit 2026-08-17** [body-hash:85f392c2ef02541e]: KEEP-NA, valid -- genuine content change since the 2026-08-17 marker: todos 1 (W6 codex refresh) and 2 (reconcile evidence into sibling plan) both flipped [x] done 2026-08-18/2026-08-17 respectively (self-caught + corrected a wrong prerequisite assumption in the process, per the doc's own 2026-08-18 entry). Remaining 2 open items stay correctly gated: todo 3 ([REVIEW] P1, explicitly operator-paced review of the W2 Claude.ai artifact, not a completion gate per the doc's own text) and todo 4 (archive both plans, gated on todos 1-3 completing first). Gated finalize companion (depends_on + gate_on_depends: true on the main remediation plan) -- criterion (b) applies. Cross-cutting tranche audit.
- **context-scout 2026-08-20**: populated/refreshed context_scope (6 entries)
