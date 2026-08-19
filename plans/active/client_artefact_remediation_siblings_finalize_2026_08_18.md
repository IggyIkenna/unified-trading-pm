---
doc_type: plan
title: Client artefact remediation (siblings) — finalize
summary: >-
  Gated finalize companion for client_artefact_remediation_siblings_2026_08_18.md. Re-verifies each claimed fix
  against the live file, re-runs the banned-term sweep across all six artefacts, and archives the parent once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, artifact-remediation, finalize]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_siblings_2026_08_18.md,
    /plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md,
  ]
created: 2026-08-18
last_updated: "2026-08-18"
parent_epic: system_readiness_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.3
estimate_calibrated_ai_days: 0.24
assigned_role: infra
effort: high
drift_direction: none
depends_on: [client_artefact_remediation_siblings_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Mandatory finalize companion per task_template.md §4 (operator ruling 2026-07-24) — every assigned_vm:planning
  plan with more than one todo needs a gated finalize plan that closes only its own plan.
context_scope:
  [
    /plans/active/client_artefact_remediation_siblings_2026_08_18.md,
    /plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md,
  ]
---

# Client artefact remediation (siblings) — finalize

Gated on [`client_artefact_remediation_siblings_2026_08_18.md`](/plans/active/client_artefact_remediation_siblings_2026_08_18.md).
Do not start before then.

- [x] ✅ [REVIEW] P0. **Re-run the banned-term sweep across ALL SIX artefacts and confirm zero hits** — including
      inside SVG `<text>` elements, which is where one of the original 6 hits hid. Open the files; do not trust the
      parent plan's checkboxes. — verified 2026-08-19 (slot 31, review), fresh-pulled to LDR HEAD `eb190e4427`
      first. Direct `rg`/`grep` sweep of all six live files in `codex/14-customer-journeys/commercial-model/`
      (`strategy-service-deep-dive.html`, `platform-architecture.html`, `carveout-engineering.html`,
      `ODUM_Elysium_Phase2_Update_2026-07-24.html`, `platform-external-api-walkthrough.html`,
      `strategy-service-walkthrough.html`) — not a re-read of the parent plan's checkboxes. **0 hits for
      `clearloop`** (case-insensitive, whole-file grep so this also covers SVG `<text>`/`alt`/label content, plus a
      separate spacing/hyphen-variant pass and a split-tag heuristic scan — all clean). Also swept `$`
      (0 hits), `budget`/`ARR`/`valuation`/`revenue` (hits found are all legitimate technical usage — e.g.
      "capital budget" as a position-sizing term in `strategy-service-deep-dive.html`/`platform-architecture.html`,
      "Valuation and post-trade" as a component-category label in `carveout-engineering.html` — none are commercial
      figures/company valuation, so none violate the disclosure rule), the performance-figure phrase (0 hits — item
      2's fix holds), and the invented-strategy-family phrase (0 new hits outside the already-tracked
      `strategy-service-walkthrough.html` instance the Elysium child plan owns).
- [ ] [REVIEW] P1. **Verify each claimed fix against the live file**, then update the corresponding finding's
      status in [the sibling-docs audit](/plans/audit/results/client_artefact_sibling_docs_audit_2026_08_18.md)
      from open to resolved.
- [ ] [DOC] P2. **Archive the parent plan** once every todo above is done — standard 6-step ritual (status →
      `archived`, `git mv` into the dated archive folder, corpus-wide referrer-path fixup, verify no broken links,
      confirm line caps still hold).

## Progress Log

**2026-08-18 — authored** alongside the sibling remediation child, per the mandatory finalize-companion rule.

**context-scout 2026-08-19**: populated context_scope (2 entries) — added the sibling-docs audit report this
finalize reconciles findings back into; source-path hunt skipped (finalize gate).

**2026-08-19 (slot 31, review)** — Dispatched item 1 (banned-term sweep). Fresh-pulled first (LDR HEAD
`eb190e4427`). Independently swept all six live artefact files (not the parent plan's checkboxes) for `clearloop`,
`$`, `budget`/`ARR`/`valuation`/`revenue`, the performance-figure phrase, and the invented-strategy-family phrase —
see the flipped checkbox above for the full breakdown. Zero disqualifying hits. Items 2 and 3 remain open.
