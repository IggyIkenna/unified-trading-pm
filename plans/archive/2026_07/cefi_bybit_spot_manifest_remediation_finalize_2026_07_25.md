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
status: complete # (was: active) 2026-07-26 -- both todos done, parent plan archived
nature: process
asset_group: [cefi]
stage: [data]
repos: [market-tick-data-service, unified-trading-pm]
scope: [engineer, admin]
tags: [cefi, bybit-spot, ao-dispatch, close-out, manifest-surgery, honest-coverage]
related:
  [
    /plans/archive/2026_07/cefi_bybit_spot_manifest_remediation_2026_07_25.md,
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

- [x] ✅ [REVIEW] P1. **Independently re-verify the parent's own reconciliation claim (todo 5, "Close the loop"), do not
      trust it as-is.** Confirm: (1) `plans/active/cefi_misc_audits_and_hygiene_2026_07_25.md`'s corrective note cites a
      real, existing commit (re-verify via `git log`, not copied from the parent's own citation); (2) whether
      `plans/archive/issues/bybit_spot_manifest_stray_captures_2026_07_07.md`'s `status: resolved` is now genuinely TRUE
      (both corrective scripts actually ran with `--apply` against production, per the parent's todos 2-3 evidence) — if
      the gap between "marked resolved 2026-07-14" and "actually executed" is real, add an honesty banner to that doc
      noting the date gap rather than leaving it silently misleading; (3)
      `plans/active/issues/instruments_remaining_work_audit_2026_07_10.md`'s BYBIT-SPOT finding is flipped/annotated to
      reflect the now-current (post-remediation) row counts, not left describing the stale 2026-07-10 state. **Done
      when**: all three re-verified with independent evidence citations in this todo's own Progress Log entry. -- **DONE
      2026-07-26**. (1) Independently confirmed via `git log` (not copied) that `mtds@87004c5b`, `mtds@d5c07559`, and
      `unified-trading-pm@b94956932` all exist and match their described content -- added the explicit shas to the
      misc-audits corrective note. (2) `bybit_spot_manifest_stray_captures_2026_07_07.md`'s `status: resolved` is now
      genuinely TRUE -- added a 2026-07-26 addendum to that doc confirming the real `--apply` landed + was
      double-verified (by_data_type + measure_honest_coverage.py), rather than an honesty-CORRECTION banner (the prior
      2026-07-14 correction note already flagged the gap accurately; this addendum closes it, doesn't re-flag it). (3)
      `instruments_remaining_work_audit_2026_07_10.md`'s finding 7 now carries a `RESOLVED 2026-07-26` closure note
      citing the same evidence, no longer describing the stale 2026-07-10 state as current.
- [x] ✅ [DOC] P2. **Archive `cefi_bybit_spot_manifest_remediation_2026_07_25.md`** via the standard 6-step ritual
      (DEFERRED check → archive banner + `status` flip → codex-alignment check → CLAUDE.md/codex update if a new durable
      contract resulted → corpus-wide referrer-path fixup → clear `locked_by`). **Done when**: plan moved to
      `plans/archive/2026_07/`, every corpus referrer resolves to the new path. -- **DONE 2026-07-26**. (1) Zero
      DEFERRED prose (all 5 todos genuinely done). (2) Archive banner added + `status: complete`. (3) Codex-alignment:
      the force-consolidate incident this plan surfaced (4 real bugs) was a genuine gap in
      `/codex/05-infrastructure/manifest-consolidator-ssot.md`'s "Surgical ROW REMOVAL" recipe -- corrected its
      "non-blocking failure" framing (was actually silently no-op-ing the entire re-stamp) and documented the sanctioned
      fix + the new reusable `restamp_manifest_consolidator_2026_07_26.py` tool. (4) That codex update IS the
      new-durable-contract step. (5) 4 corpus referrers found + fixed
      (`plans/archive/issues/     bybit_spot_manifest_stray_captures_2026_07_07.md`, this plan's own `related:`,
      `cefi_misc_audits_and_hygiene`, `instruments_remaining_work_audit_2026_07_10`); 2 more were correctly left alone
      (a frozen historical note in `ag_closeout_audit_rollout_2026_07_25.md`, and the auto-generated inventory
      dashboard, regenerated via its real generator script rather than hand-edited:
      `regenerate_active_plan_inventory.py` → 231 plans, 0 orphans). (6) `locked_by` confirmed empty on both this plan
      and the parent. `git mv` to `plans/archive/2026_07/` -- `unified-trading-pm@(this commit)`.
