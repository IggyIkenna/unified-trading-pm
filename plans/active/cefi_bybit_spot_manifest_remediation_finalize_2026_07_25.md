---
doc_type: plan
title: BYBIT-SPOT manifest remediation — finalize (reconcile source docs + archive)
summary: >-
  Gated closeout for cefi_bybit_spot_manifest_remediation_2026_07_25.md — machine-held until every one of that plan's 5
  todos is done (depends_on + gate_on_depends: true, not just prose). Independently re-verifies todo 5's own
  reconciliation claim (does bybit_spot_manifest_stray_captures_2026_07_07.md's `status: resolved` actually hold now, or
  does it need an honesty-correction banner for the 2026-07-10 to 2026-07-25 gap between "marked resolved" and "actually
  executed"?), confirms cefi_misc_audits_and_hygiene_2026_07_25.md's corrective note landed with real evidence, then
  runs the standard 6-step archival ritual on the now-fully-closed parent plan.
status: active
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, bybit-spot, ao-dispatch, close-out, manifest-surgery, honest-coverage]
related:
  [
    /plans/active/cefi_bybit_spot_manifest_remediation_2026_07_25.md,
    /plans/archive/issues/bybit_spot_manifest_stray_captures_2026_07_07.md,
    /plans/active/issues/instruments_remaining_work_audit_2026_07_10.md,
    /plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md,
  ]
created: "2026-07-25"
last_updated: "2026-07-25"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [cefi_bybit_spot_manifest_remediation_2026_07_25]
gate_on_depends: true
source: >-
  task_template.md §4 "Every AO-dispatched plan needs a gated finalize plan" (operator ruling 2026-07-24) —
  cefi_bybit_spot_manifest_remediation_2026_07_25.md shipped without its required companion
  (check_finalize_plan_coverage.py regression, caught while shipping unrelated work on the same shared checkout).
assigned_role: data_engineering
sequential: true
drift_direction: advance-code
---

# BYBIT-SPOT manifest remediation — finalize

> **Machine-gated on `cefi_bybit_spot_manifest_remediation_2026_07_25.md`** (`depends_on` + `gate_on_depends: true`) —
> the dispatcher will not queue either todo below until every task in that plan is `done`. `sequential: true` because
> todo 2 (archival) must not run before todo 1 (reconciliation) — the archive ritual's codex-alignment check needs the
> final, reconciled state.

## Todos

- [ ] [REVIEW] P1. **Independently re-verify the parent's own reconciliation claim (todo 5, "Close the loop"), do not
      trust it as-is.** Confirm: (1) `plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md`'s corrective note cites a
      real, existing commit (re-verify via `git log`, not copied from the parent's own citation); (2) whether
      `plans/archive/issues/bybit_spot_manifest_stray_captures_2026_07_07.md`'s `status: resolved` is now genuinely TRUE
      (both corrective scripts actually ran with `--apply` against production, per the parent's todos 2-3 evidence) — if
      the gap between "marked resolved 2026-07-14" and "actually executed" is real, add an honesty banner to that doc
      noting the date gap rather than leaving it silently misleading; (3)
      `plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`'s BYBIT-SPOT finding is flipped/annotated to
      reflect the now-current (post-remediation) row counts, not left describing the stale 2026-07-10 state. **Done
      when**: all three re-verified with independent evidence citations in this todo's own Progress Log entry.
- [ ] [DOC] P2. **Archive `cefi_bybit_spot_manifest_remediation_2026_07_25.md`** via the standard 6-step ritual
      (DEFERRED check → archive banner + `status` flip → codex-alignment check → CLAUDE.md/codex update if a new durable
      contract resulted → corpus-wide referrer-path fixup → clear `locked_by`). **Done when**: plan moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path.
