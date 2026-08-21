---
doc_type: issue
title: ag-closeout-audit ui 2026-08-21 — orphan projection + parked findings
summary: >-
  2026-08-21 /ag-closeout-audit ui tranche Phase 1 audit (1 batch, 17 candidate docs). Compact orphan table.
status: open
nature: issue
asset_group: [ui]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ag-closeout-audit, ui, orphan-projection]
related: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md, /plans/active/ui_consolidated_closeout_2026_07_30.md]
created: 2026-08-21
author: claude-session-2026-08-21
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: human
priority: P2
estimate_class: research
estimate_baseline_ai_days: 0
estimate_calibrated_ai_days: 0
assigned_role: NA
drift_direction: NA
resolved_by:
locked_by:
source: ["2026-08-21 — /ag-closeout-audit ui, 1 Phase-1 batch, 17 candidates"]
depends_on: []
context_scope: [/plans/active/issues/ag_closeout_audit_cross_tranche_big_findings_2026_08_21.md]
---

# ag-closeout-audit ui 2026-08-21

17 candidates, 1 batch (`ui` is the newest tranche, added 2026-07-30 — corpus-wide retag pass still owed). Counts:
archivable_now 2 · archivable_after_planned_work 3 · orphaned_partial_coverage 1 · orphaned_never_touched 11 ·
exclude_cross_cutting 0.

**Phase 2/3 re-verification 2026-08-21 (same-day follow-up sweep)**: of the 12 orphaned rows, 1
(`architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`) has since resolved + archived and should drop
from the next count; the other 11 all re-verified genuinely still orphaned for the same reason (operator-gated /
time-gated / too-large-design-needed / process-tracking-doc-with-no-dispatchable-content) — zero cleared the
genuinely-bounded/AO-eligible bar, so no new `ui_satellite_ao_dispatch_batch` was drafted this pass. See "Orphaned —
compact table" and "Mechanical hygiene flags" above for the per-row/per-flag re-verification, and the Progress Log
below for the full sweep summary.

## Orphaned — compact table

> **Re-verified 2026-08-21 (Phase 2/3 sweep)** — every row below was re-read from its live source doc, not trusted from
> this table's Phase-1 one-liner. Verdict column added; zero rows cleared the genuinely-bounded/AO-eligible bar this
> pass — see the sweep's own Progress Log entry below for the full per-doc reasoning. No `ui_satellite_ao_dispatch_batch`
> draft was created this pass (nothing qualified).

| Doc | Taxonomy | Re-verify 2026-08-21 |
|---|---|---|
| `artifact_pipeline_observability_2026_07_17.md` | misattributed-VM-origin fix covered by batch3; 2 other items non-dispatchable/sequencing-blocked | **Still accurate.** na-eligibility-audit's own 2026-08-21 RECLASSIFY pass already extracted the one bounded item (snapshot worker) to `ui_satellite_ao_dispatch_batch5_2026_08_21.md`. Of the 3 remaining open items: "What's running tab" is sequencing-blocked on a net-new, unscoped VM-launch-as-deploy provider (design call, not a todo); the SHA-pinning item is self-marked `_(stretch, optional)_` with a stated hazard (2026-06-01 pruning incident) needing reconciliation first — too-large/design-needed; the misattributed-VM-origin correction is already duplicated in `ui_satellite_ao_dispatch_batch3_2026_08_09.md` item 3 (still active, unlocked). Still-orphaned-same-reason. |
| `consolidator_throughput_backlog_monitor_2026_07_09.md` | 2 REVIEW deploy-gate closers, deferred to unnamed milestone | **Still accurate.** Both open todos (WS-1 + WS-3 shipping gates) are explicitly deferred by a dated 2026-07-10 operator decision ("local-dev-only until all cockpit plans complete") — time/operator-gated, not a worker judgment call. Still-orphaned-same-reason. |
| `data_status_tab_and_downloads_remediation_2026_06_16.md` | DeFi phantom-row audit + APPLY-GATE sign-off, gated on a still-open 2026-08-07 operator HOLD | **Still accurate.** Re-confirmed via the doc's own 2026-08-21 na-eligibility-audit entry (same day): both open items stay gated on the 2026-08-07 operator HOLD (Ikenna's defi/sports manifest-canonicalisation work not yet landed) — no newer operator ruling found. Still-orphaned-same-reason. |
| `deployment_registry_firestore_p3_cutover_2026_07_14.md` | **carried finding, 7 re-confirmations since 2026-07-30** — see cross-tranche big findings item 15 | **Still accurate.** HALTED on a live-fleet Firestore doc-count-parity precondition (27% coverage as of 2026-08-08) — a data-measurement + soak-convergence wait, not a bounded worker todo. Still-orphaned-same-reason. |
| `deployment_registry_firestore_p5_verify_2026_07_14.md` (draft) | correctly gated behind P3 | **Still accurate** — `depends_on` + `gate_on_depends: true` on P3, which is still HALTED (see row above). |
| `issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md` | dead e2e fixture ID + generator/UI structural-skew investigation | **RESOLVED — no longer orphaned.** This doc was archived 2026-08-21 (`status: resolved`, now at `plans/archive/issues/architecture_v2_drift_leg_specs_and_manifest_residue_2026_07_16.md`) — its sole open todo landed and the closeout hub's Track 4 already cites the archived path. Drop from future orphan counts; the Phase-1 candidate set that produced this table predates the archival. |
| `issues/cost_observability_deferred_followups_2026_07_10.md` | business-context enrichment, 176 launcher scripts, only ~9 through choke point — recommend piggyback on infra tranche | **Still accurate.** Confirmed via the doc's own 2026-08-17 na-eligibility-audit entry: still only 45/149 raw-create VM launchers directly migratable per the infra tranche's own batch17 doc — too-large/design-needed for a single ui-tranche todo. Still-orphaned-same-reason. |
| `issues/deployment_api_inventory_alert_gate_ondemand_only_2026_07_27.md` | **carried finding, 6 consecutive passes; also a declared-but-unwired instance** — see cross-tranche big findings item 14 | **Still accurate.** The single `[HUMAN] P2` todo is a genuine unresolved architecture trade-off (reuse the 45s-TTL inventory endpoint vs. build a narrower alert-check-only path), re-confirmed by 6 prior audit/reconcile passes. Too-large/design-needed. Still-orphaned-same-reason. |
| `issues/plan_reconciler_findings_ui_2026_08_10.md` | scope 3 orphaned Firestore-migration successors + undefined soak-window duration | **Still accurate.** Both remaining items are explicitly `[OPERATOR]`-tagged genuine human judgment calls (per this doc's own 2026-08-17 self-audit note) — operator-gated. Still-orphaned-same-reason. |
| `issues/plan_reconciler_findings_ui_2026_08_18.md` | context-scout script bug + P0-finalize dispatch-inactivity check | **Still accurate, re-attempted.** Context-scout bug root cause is outside `plans/**` (not fixable here). The AO-backlog-status check was re-attempted this pass via `check-ao-backlog-status.sh` — SSM command timed out (see this sweep's Progress Log entry + the cross-tranche big-findings doc) — still inconclusive, third failed/inconclusive attempt across sessions. This doc is a process/tracking report (0 `- [ ] [TAG] P<n>.` checkboxes), not itself AO-eligible content — no batch candidate here. |
| `issues/plan_reconciler_findings_ui_2026_08_19.md` | run killed 18min in by the AO singleton-dedup bug — re-run needed | **Still accurate.** Same class as the row above — a process/tracking doc (0 open checkboxes, 2 carried-forward Filed notes), not itself dispatchable work. The underlying AO singleton-dedup bug is already filed separately (`ao_singleton_agent_kind_dedup_kills_concurrent_tranche_workers_2026_08_20.md`). No batch candidate here. |
| `issues/ui_admin_v1_routes_need_firebase_admin_creds_and_e2e_dev_server_instability_2026_08_09.md` | provision Firebase Admin credential/emulator + re-run gated e2e | **Still accurate.** Todo 1 is explicitly self-framed as an operator/infra decision touching CI secrets (Firebase Admin credential vs. emulator, no ruling on record); todo 3 is dependency-blocked on it. Operator-gated. Still-orphaned-same-reason. |

## Mechanical hygiene flags

> **Re-verified 2026-08-21 (Phase 2 sweep)** — none of the 4 flags below yielded a direct doc-edit this pass; see the
> Progress Log entry for why each stays as-is.

- Covering-set completeness gap: `deployment_api_true_catalogue_expected_universe_projection_ao_dispatch_2026_08_16.md`
  (+finalize) is real active coverage for `data_status_catalogue_true_source_phase2_2026_07_24.md` but is absent
  from the ui tranche's `covering_paths` — likely a symptom of the still-owed corpus-wide retag pass.
  **Re-verified 2026-08-21**: confirmed — that doc's own frontmatter is `asset_group: [cross-cutting]`, not `[ui]`,
  and its filename doesn't match the `ui_*` satellite-batch naming convention `_covering_paths()` scans for, so its
  absence from the ui tranche's covering set is mechanically CORRECT given its current tag, not a script bug.
  Whether it *should* be retagged `ui` (it covers ui-tranche-relevant ground) is exactly the judgment call the
  corpus-wide retag pass (`ui_consolidated_closeout_2026_07_30.md`'s own open P2 todo) is already tracked to resolve
  — not a mechanical fix, left un-retagged here per that doc's own precedent of deferring exactly this class of call.
- Context-scout script bug (missing `- ` bullet marker on 2026-08-17-dated Progress Log entries) confirmed across
  ≥4 docs in this corpus — filed but unfixed, root cause outside `plans/**`. **Re-verified 2026-08-21**: still
  outside this repo's write-scope (the bug is in the context-scout skill/script itself); no plans/** edit possible.
- `deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md`: zero dispatch activity for 9+ days despite its
  `depends_on` gate being satisfied since 2026-08-10/11 — flagged repeatedly, never resolved. **Re-verified
  2026-08-21 — BIG FINDING, genuine stuck-dispatch condition, escalated (not fixable via doc edit).** Read the
  source P0 doc (`deployment_api_unauthenticated_prod_p0_2026_08_10.md`) in full: its own `## Todos` section (the
  literal gate the finalize doc's banner names, "do not start until all 5 of its original `## Todos` are `[x]`") has
  all 5 items checked `[x]` with live evidence — the gate genuinely IS satisfied, not just claimed. The finalize
  plan is `status: active`, `assigned_vm: planning`, unlocked, `depends_on: [deployment_api_unauthenticated_prod_p0_2026_08_10]`
  + `gate_on_depends: true`. Attempted a fresh `/check-agent-orchestrator` this pass
  (`check-ao-backlog-status.sh deployment_api_unauthenticated_prod_p0_2026_08_10_finalize`) — the SSM command
  timed out server-side (Python `urllib` `TimeoutError` reading the response from `localhost:8765` on the
  orchestrator VM itself), so the check is inconclusive for a THIRD time across sessions (2026-08-19's
  `check-ao-backlog-status.sh` grep returned zero rows; this pass's attempt timed out entirely) — this itself is now
  a second, independent signal something may be off (either with this specific plan's dispatch or with the status
  script/API under current load), not just "still no evidence either way." This now stands at **11+ days** with a
  genuinely-satisfied dispatch gate and no confirmable AO activity — worth direct operator/AO-infra attention
  (dashboard access or a VM-side `sqlite3` query against `state.db`, the method that successfully diagnosed a
  similar-looking stuck-lock case on 2026-08-20) rather than another doc-side re-check.
- Confirmed load-bearing context (not this tranche's own finding): `plan_reconciler` is treated as a system-wide
  singleton by AO's `reap_orphan_agents()` dedup, which killed 2 of 3 concurrently-running tranche-sharded
  `plan_reconciler` workers mid-task on 2026-08-19 — the exact bug this session fixed earlier today
  (`agent-orchestrator@e8d83540`, see `ao_singleton_agent_kind_dedup_kills_concurrent_tranche_workers_2026_08_20.md`).
  **Re-verified 2026-08-21**: already fixed per the cited commit, nothing further needed.

## Progress Log

- **2026-08-21**: Doc created directly from the 2026-08-21 /ag-closeout-audit ui Phase-1 sweep (1 batch). No
  mechanical fixes applied yet.
- **ag-closeout-audit 2026-08-21 (ui tranche, Phase 2/3 sweep)**: Phase 2 — re-verified all 4 "Mechanical hygiene
  flags" and all 12 "Orphaned" rows against fresh source-doc reads (not just this doc's own Phase-1 one-liners).
  Applied zero direct doc-edits from the hygiene-flags list itself (covering-set gap is a correct-per-current-tag
  non-bug, deferred to the already-tracked corpus-wide retag todo; context-scout bug is outside `plans/**`; the
  singleton-dedup bug is already fixed). Found 1 orphan-table row (`architecture_v2_drift_leg_specs_and_manifest_
  residue_2026_07_16.md`) has since resolved + archived — updated its row + the summary counts accordingly.
  Phase 3 — re-classified all 12 orphaned rows against the bounded/AO-eligible taxonomy: 0 qualified as genuinely
  bounded (all are operator-gated, time-gated, too-large/design-needed, or a 0-checkbox process/tracking doc with
  no dispatchable content) — **no new `ui_satellite_ao_dispatch_batchN_2026_08_21.md` was drafted**, since nothing
  in this tranche's orphan set cleared the bar this pass (batch1/3/4/5 already extracted everything bounded from
  prior sweeps). **Big finding, escalated (not fixable via doc edit)**: re-verified the
  `deployment_api_unauthenticated_prod_p0_2026_08_10_finalize.md` stuck-dispatch flag — its gate premise IS
  genuinely satisfied (the source P0 doc's own 5 `## Todos` are all `[x]` with live evidence), yet the plan has now
  sat 11+ days with zero confirmable AO dispatch activity. A fresh `check-ao-backlog-status.sh` attempt this pass
  timed out server-side (SSM `TimeoutError` reading `localhost:8765` on the orchestrator VM) — the third
  inconclusive/failed attempt to confirm dispatch state across sessions. Worth direct operator/AO-infra attention
  (dashboard access, or the VM-side `sqlite3 state.db` query that successfully diagnosed a similar stuck-lock case
  on 2026-08-20) rather than another doc-side re-check. Full detail in the "Mechanical hygiene flags" section above.
  No files committed/pushed this pass (edits only, per this session's own instructions).
