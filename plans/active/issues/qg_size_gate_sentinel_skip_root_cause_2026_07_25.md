---
doc_type: issue
title:
  Root-cause WHY quality-gates.sh's function/class/method SIZE CHECK didn't block the 2026-07-16 sports-orchestrator
  function-size regression at commit time (migrated deferred item)
summary:
  "Migrated forward from `sports_reference_function_size_qg_regression_2026_07_16.md` (archived 2026-07-25 with 0
  remaining blocking items) — that doc's acceptance item 2 ('root-cause WHY the size gate didn't block whichever commit
  introduced this — sentinel-skip vs scoped-gate run — and note the fix/process change so future same-day sports commits
  can't silently regress this ratchet again') was explicitly confirmed STILL open 'in spirit' by its own 2026-07-23
  RE-TRIAGE, even though the underlying 3 functions were independently decomposed back under the size limit by
  `instruments-service@ac22305c` (2026-07-21) — so the symptom is fixed but the PROCESS gap (how a same-day sports
  commit regrew 3 functions past MAX_FUNCTION_LINES/MAX_METHOD_LINES without the size-check phase catching it at commit
  time) was never investigated. Low severity (P3) — this is a process/tooling-hygiene question, not a live
  data-correctness or shipping blocker; the archived source doc's own RE-TRIAGE explicitly deferred it rather than
  resolving it. Thematically adjacent to `qg_sentinel_environment_blind_2026_07_23.md` (a DIFFERENT sentinel-skip
  mechanism — ENVIRONMENT-dimension binding — surfaced 2026-07-23) but not the same root cause; that doc's fix (bind
  configuration into the sentinel hash) may or may not also explain this one, which is exactly the open question here."
status: open
nature: issue
asset_group: [sports]
stage: [meta]
repos: [instruments-service, unified-trading-pm]
scope: [engineer]
tags: [code-quality, function-size, qg-ratchet, sentinel-skip, quality-gates, sports, migrated-deferred]
related:
  - /plans/archive/issues/sports_reference_function_size_qg_regression_2026_07_16.md
  - /plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md
  - /plans/active/issues/instruments_service_codex_compliance_ceiling_drift_2026_07_20.md
created: 2026-07-25
last_updated: 2026-07-25
parent_epic: instruments_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: research
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.36
assigned_role: infra
drift_direction: advance-code
resolved_by:
locked_by:
locked_since:
depends_on: []
source:
  "archival-ritual follow-up sweep 2026-07-25, migrating the one genuinely-unresolved deferred item out of
  sports_reference_function_size_qg_regression_2026_07_16.md before archiving it (per the archival ritual's 'migrate
  DEFERRED items before archiving' step) — never let real deferred work vanish silently into the archive"
---

# Root-cause the 2026-07-16 sports function-size sentinel-skip (migrated deferred item)

## Why this doc exists

`sports_reference_function_size_qg_regression_2026_07_16.md` (now archived) found 3 functions in `instruments-service`'s
`sports_reference_core.py`/`sports_reference_fixtures.py` had regrown past the `MAX_FUNCTION_LINES`/`MAX_METHOD_LINES`
size gate despite both files having been explicitly decomposed out of `FUNCTION_SIZE_EXTRA_EXCLUDES` on 2026-06-11
specifically because they were supposed to "now pass the 900-line/200-line gates directly." The symptom was fixed by
`instruments-service@ac22305c` (2026-07-21, confirmed live in a 2026-07-23 RE-TRIAGE). The MECHANISM by which a same-day
sports commit shipped this regression without the size-check phase blocking it at commit time was never investigated —
the source doc's own acceptance item 2 explicitly says so and its RE-TRIAGE confirms it "remains open in spirit."

## Original hypothesis (unconfirmed, from the source doc)

`quality-gates.sh` has a green-content-sentinel that skips the expensive TESTS+TYPE CHECK+SIZE CHECK phases when the
tree is byte-identical to the last known-green run. If the regressing sports commits (same-day candidates: `a66fc295`,
`493393c8`, `86cc71ff`, all 2026-07-16) landed via a workflow that reused a stale sentinel — or ran a `QG_SLICE`-scoped
gate that excludes phase 5 — the regression could ship silently.

## Acceptance

- [ ] [SCRIPT] P3. Root-cause WHY the size gate didn't block the commit that regrew the 3 functions past their limits on
      2026-07-16 (sentinel-skip vs scoped-gate run vs a different mechanism) and note the fix/process change so a future
      same-day sports commit can't silently regress this ratchet again.
- [ ] [SCRIPT] P3. Check whether `qg_sentinel_environment_blind_2026_07_23.md`'s planned sentinel-hardening fix (binding
      `ENVIRONMENT` into the sentinel hash) also closes this gap, or whether this is an independent sentinel-skip class
      needing its own fix.
