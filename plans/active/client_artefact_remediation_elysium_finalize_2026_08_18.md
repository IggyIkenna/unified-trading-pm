---
doc_type: plan
title: Client artefact remediation (Elysium) — finalize
summary: >-
  Gated finalize companion for client_artefact_remediation_elysium_2026_08_18.md. Verifies each claimed edit against
  the live HTML, reconciles finding status back into the audit reports, and archives the parent once done.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, elysium, artifact-remediation, finalize]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/client_artefact_remediation_elysium_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
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
depends_on: [client_artefact_remediation_elysium_2026_08_18]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
resolved_by:
supersedes:
superseded_by:
source: >-
  Mandatory finalize companion per task_template.md §4 (operator ruling 2026-07-24) — a finalize plan closes only
  its own plan.
context_scope:
  [
    /plans/active/client_artefact_remediation_elysium_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
  ]
---

# Client artefact remediation (Elysium) — finalize

Gated on [`client_artefact_remediation_elysium_2026_08_18.md`](/plans/active/client_artefact_remediation_elysium_2026_08_18.md).

- [x] [REVIEW] P1. ✅ **Verify every claimed edit against the live HTML** — open the file, do not trust checkbox text.
      Confirm specifically that the `SigningSurface` list was NOT edited (only annotated), since the original audit
      finding there was a false positive and "fixing" it would make the document wrong. **Verified 2026-08-19**:
      opened `codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html` directly (2474 lines) and
      spot-checked the claims against live content, not checkbox text: (1) `SigningSurface` enum block (line 1840)
      reads verbatim `LOCAL_KEY / CLOUD_KMS_ENCRYPTED / COPPER_MPC / FIREBLOCKS_MPC / MOCK` — unedited, no invented
      Ceffu member — with an explanatory callout added alongside it (lines 1858-1875, cites
      `custody_surfaces.py`'s `CEFFU_ROUTES_VIA_COPPER_NOTE` + `SigningSurfaceStatus.OUT_OF_SCOPE`), exactly the
      "annotate, don't edit" shape the todo requires. (2) Instruction-type count reads `11` (stat block, line 958)
      and "The eleven action types" (line 1238). (3) §02 states "Nine families, not five" and explicitly calls out
      the invented "Liquidity provision" member (lines 1068-1105). (4) §11 heading reads "Automated movement —
      specified as a target state, mostly not yet wired" (line 1928) with the measured
      `TransferCoordinator._ensure_default_handlers()`/never-instantiated evidence inline (lines 1967-1971). (5) CeFi
      instrument-ID example uses `SPOT_PAIR` (line 1145), not `SPOT`. (6) Owner marks (`class="own"`) present
      throughout, citing `system_readiness_master.md` workstreams (W1/W4/W5/W6/W7/W8/W10/W11/W13/W17/W18/W20).
- [x] [REVIEW] P1. ✅ **Confirm zero `live` badges remain** in this file, and that each downgraded section reads
      coherently rather than just having its pill swapped. **Verified 2026-08-19**: grepped the live file for every
      `st-live`/`>live<` occurrence — 4 hits total, all non-claims: a `.st-live` CSS class definition (line 709,
      needed so the legend can still render what a `live` badge would look like), the legend's own definitional text
      (lines 823, 840 — "live: reachable on a production path AND validated with real capital"), and one changelog
      note describing the re-grade itself ("read live now reads partial", line 986). Zero section-status badges in
      the document body carry `st-live`. Read §11's "Automated movement" section in full (not just its pill) to
      confirm it reads coherently post-downgrade, not just re-pilled: the prose explicitly states the measured
      reality (one handler registered, `TransferCoordinator` never instantiated in production) rather than a bare
      status change with stale surrounding text.
- [ ] [REVIEW] P1. **Reconcile finding status** back into the audit reports' summary tables, open → resolved.
- [ ] [DOC] P2. **Archive the parent plan** once every todo above is done — standard 6-step ritual.

## Progress Log

**2026-08-18 — authored** alongside the Elysium remediation child.

**context-scout 2026-08-19**: populated context_scope (2 entries) — added the audit report this finalize
reconciles findings back into; source-path hunt skipped (finalize gate).

**2026-08-19 (slot 33, review-role, task assigned_role=review)** — Worked items 1-2 (the two `[REVIEW]` verification
todos this task was dispatched for). Opened the live
`codex/14-customer-journeys/commercial-model/strategy-service-walkthrough.html` directly rather than trusting the
parent plan's checkbox text, and spot-checked every claimed edit type: SigningSurface list unedited (only annotated),
instruction-type count (11) and family count (9, invented "Liquidity provision" explicitly called out), §11 softened
with measured evidence inline, CeFi instrument-ID example (`SPOT_PAIR`), owner marks present across 12+ sections, and
zero `live`-status badges remaining in the document body (the 4 remaining `st-live`/`>live<` string hits are legend
definitional text + a changelog note, not live section claims). Both checkboxes flipped with inline evidence. Items 3
(reconcile audit-report summary tables) and 4 (archive parent, gated on item 3) left unchecked — out of scope for this
dispatch, which named only the two `[REVIEW]` items in its brief; a future dispatch should pick those up.
