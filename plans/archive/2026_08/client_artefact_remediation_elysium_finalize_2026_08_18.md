---
doc_type: plan
title: Client artefact remediation (Elysium) — finalize
summary: >-
  Gated finalize companion for client_artefact_remediation_elysium_2026_08_18.md. Verifies each claimed edit against
  the live HTML, reconciles finding status back into the audit reports, and archives the parent once done.
status: complete
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [admin, engineer]
tags: [client-disclosure, elysium, artifact-remediation, finalize]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/client_artefact_remediation_elysium_2026_08_18.md,
    /plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md,
  ]
created: 2026-08-18
last_updated: "2026-08-20"
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
- [x] [REVIEW] P1. ✅ **Reconcile finding status** back into the audit reports' summary tables, open → resolved.
      **Done 2026-08-19**: satisfied by the parent-level finalize pass
      ([`client_artefact_remediation_finalize_2026_08_18.md`](/plans/active/client_artefact_remediation_finalize_2026_08_18.md)),
      landed concurrently with this session's own attempt at the same edit. That pass added a `Status` column to
      `nick_ai_and_elysium_artefact_audit_2026_08_18.md`'s severity-ranked summary table covering ALL 13 rows (both
      Elysium and Nick AI, not just Elysium), each citing the closing SHA, plus flipped the doc's own
      `status: partial → pass`. This session's narrower Elysium-only edit (attempted independently, same day) was a
      strict subset and was dropped on rebase in favor of the broader landed version — see that audit doc's own
      Progress Log for the full accounting.
- [x] ✅ [DOC] P2. **Archived the parent plan** ([`client_artefact_remediation_elysium_2026_08_18.md`](/plans/archive/2026_08/client_artefact_remediation_elysium_2026_08_18.md)) — standard 6-step ritual: all 25 todos `[x]`, unlocked, `status: active→complete`, `git mv` to `plans/archive/2026_08/` (this finalize archives in the same commit, mode-1 combined flip+archival). Referrer sweep: removed the elysium-child entry from 4 active docs' `related:` (rule-13 codex, subagent foreign-checkout issue, six-surface + venue-transfer audits); grand-parent prose + INDEX left to their own archival/auto-regen. No codex contract change — remediation facts already recorded in [`nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md) (`status: pass`).

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

**2026-08-19 (slot 1, task assigned_role=review)** — Worked item 3. Independently drafted an Elysium-only `Status`
column reconciliation, then hit a rebase conflict against `origin/live-defi-rollout`: a concurrent parent-level
finalize pass had already landed a broader, superior version of the same edit (all 13 rows, both artefacts, plus a
`status: partial→pass` flip) to the same audit doc. Resolved the conflict in favor of the landed upstream version
(never overwrite already-landed peer content — RULES.md), discarded this session's redundant narrower edit, and
flipped item 3 above citing the actual landing plan/commit. Item 4 (archive) remains gated — this finalize plan's own
todos are now all `[x]` except the archival step itself, which is a distinct unit of work left for a follow-up.

**2026-08-19 (slot 1, task assigned_role=review)** — Worked item 3. Read the audit report's severity-ranked summary
table in full, cross-referenced every Elysium-tagged row against `client_artefact_remediation_elysium_2026_08_18.md`'s
own Progress Log (all todos `[x]`) to confirm each finding actually shipped rather than trusting the row text alone,
then added a `Status` column reconciling all 13 rows: 9 Elysium rows → resolved (with shipped-SHA citations), 1
`Both`-tagged row → partial (Elysium half only), 4 Nick-AI-only rows left `open` (separate, unverified-here plan).
Item 4 (archive the parent) still gated on this item — now unblocked, left for a follow-up dispatch since archival's
referrer-sweep step is a distinct unit of work.

**2026-08-20 (slot 14, infra) — item 4 done, archived.** Ran the standard 6-step archival ritual on the parent
(`client_artefact_remediation_elysium_2026_08_18.md`): all 25 todos `[x]`, unlocked, no active dependents after this
finalize archives with it. `status: active→complete`, `git mv` to `plans/archive/2026_08/`. Referrer sweep — removed the
elysium-child entry from 4 active docs' `related:` (rule-13 codex `_ssot-rules/13-artefact-claim-marks.md`, the subagent
foreign-checkout issue, and the six-surface + venue-transfer audit reports); the grand-parent's CANCELLED/SUPERSEDED
prose lines are historical and archive with the grand-parent's own finalize; `INDEX.md` is auto-regenerated. No codex
contract change — the remediation's durable facts are already in
[`nick_ai_and_elysium_artefact_audit_2026_08_18.md`](/plans/audit/results/nick_ai_and_elysium_artefact_audit_2026_08_18.md)
(`status: pass`). This finalize archives together with the parent in one commit (single-repo/mode-1 combined
flip+archival, per `plan-completion-and-archival-discipline.md`).
