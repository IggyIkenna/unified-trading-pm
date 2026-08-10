---
doc_type: plan
title: >-
  e2e_login_persona_handoff_helper_stale_2026_07_22 — finalize (reconcile + archive gate)
summary: >-
  Gated closeout for issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md — machine-held via depends_on +
  gate_on_depends: true until its sole remaining item (re-run `admin-strategy-assignments.spec.ts`, record `pw:L2 ✓`
  evidence or the specific known-blocker failure mode) is done. Reconciles evidence back into the source doc and the
  archived `dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md` item it targets, then archives the
  source doc only if the spec genuinely passed clean (not if it hit the documented Firebase-Admin-creds/dev-server
  blocker, which is a separate doc's scope to fix). Authored 2026-08-10 as part of the `ao` full-tranche RECLASSIFY +
  satellite-extraction sweep, group 3.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm, unified-trading-system-ui]
scope: [engineer]
tags: [ao-dispatch, close-out, reclassification, ui, playwright, finalize]
related:
  [
    /plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md,
    /plans/active/issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: agent_operating_framework_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [e2e_login_persona_handoff_helper_stale_2026_07_22]
gate_on_depends: true
assigned_role: review
effort: low
drift_direction: none
context_scope:
  [
    /plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
source: >-
  `/na-eligibility-audit ao` full-tranche sweep, group 3, 2026-08-10 — authored alongside the source doc's `assigned_vm:
  NA -> planning` reclassification per the mandatory finalize-twin rule.
---

# e2e_login_persona_handoff_helper_stale_2026_07_22 — finalize

> **Machine-gated on `/plans/active/issues/e2e_login_persona_handoff_helper_stale_2026_07_22.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until its sole todo is `done`.

## Todos

- [x] ✅ [REVIEW] P1. **Re-verify the outcome against reality.** If the source doc's todo claims `pw:L2 ✓`,
      independently re-run `npx playwright test --project=chromium tests/e2e/admin-strategy-assignments.spec.ts` and
      confirm exit 0. If the source doc instead recorded the known Firebase-Admin-creds/dev-server-instability blocker,
      confirm the failure signature actually matches that documented class (not a different, new failure being
      mis-attributed). — **Independently re-verified 2026-08-10 (slot-31, adopted review craft).** The source doc
      recorded the blocker outcome (NOT a `pw:L2 ✓`) — no clean-pass claim exists to re-confirm exit 0 against. Re-ran
      the spec myself against a fresh slot-31 `dev:mock` server (port 3131, self-spawned by playwright webServer): **2
      failed / 1 passed — NOT a clean pass, no `pw:L2 ✓`.** Failure signatures match the documented
      Firebase-Admin-creds/dev-server-instability class, not a new/different failure: (a) Tier-1 login
      `waitForURL("**/dashboard**")` 10s timeout on cold first navigation — page snapshot shows persona auto-filled
      (`admin@odum.internal`/`demo123`), "Signing in..." disabled, Next dev-tools "Compiling" — the first-request
      dev-server compile-latency signature (slot-6 signature (a), not a login regression; test 2's sibling passed login
      later); (b) Tier 2-5 lifecycle failed in `beforeEach` `page.goto` `/admin/strategy-assignments` (30s timeout, page
      never reached networkidle — snapshot shows shell-only render, dev-server cold-start/instability); ORG_CONFLICT
      passed (1/3). Content-verified blocker root causes live at HEAD: `lib/api/mock-handler.ts` `realRoutePrefixes`
      still passes `/api/v1/` to the real server (line 7377); `lib/firebase-admin.ts` still needs
      `FIREBASE_ADMIN_CREDENTIAL`/emulator; the `?persona=` fast-path fix (`15e4b4bc`) is landed. Matches the documented
      class confirmed across slots 20/6/4. No `pw:L2 ✓` recorded;
      `ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` remains the fix owner.
- [ ] [DOC] P1. **Reconcile evidence into both targets** — the source doc's own todo (if not already fully evidenced),
      and `/plans/archive/issues/dart_ui_capability_manifest_and_catalogue_formatting_gaps_2026_07_21.md`'s item this
      todo was always meant to retroactively close (per the source doc's own todo text).
- [ ] [REVIEW] P1. **Archive only if the spec genuinely passed clean.** If it hit the documented
      Firebase-Admin-creds/dev-server blocker instead, leave the source doc `status: open` with the finding recorded —
      do NOT archive on a blocked outcome, and do NOT attempt the Firebase-creds fix here (that is
      `ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md`'s scope). If genuinely
      clean, run the standard 6-step archival ritual (banner, move to `plans/archive/2026_08/issues/`, fix every corpus
      referrer including this finalize plan's own `related:`, re-run the active-plan inventory generator).

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/06-coding-standards/ui-testing-layers.md`.

## Progress Log

- **2026-08-10** — Authored in the same turn as the source doc's RECLASSIFY, per the mandatory finalize-twin rule.
  `sequential: true` since the 3 todos are a genuine reconcile→archive chain touching the same source doc.
- **2026-08-10 (slot-31, review craft) — Todo 1 DONE, independently re-verified.** Re-ran
  `tests/e2e/admin-strategy-assignments.spec.ts` myself against a fresh slot-31 `dev:mock` server: **2 failed / 1 passed
  — NOT a clean pass, no `pw:L2 ✓`.** Failure signatures match the documented
  Firebase-Admin-creds/dev-server-instability class (dev-server compile-latency on cold first navigation + lifecycle
  `beforeEach` navigation timeout; ORG_CONFLICT passed). Confirmed blocker root causes still live at HEAD
  (`realRoutePrefixes` `/api/v1/` passthrough, `firebase-admin.ts` cred requirement). Full detail in the todo's flip
  evidence. **Archival decision (todo 3): NOT eligible — do NOT archive the source doc.** The spec did not pass clean;
  the documented blocker is confirmed. Source doc stays `status: open`; the Firebase-creds fix remains
  `ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md`'s scope, not this plan's.
