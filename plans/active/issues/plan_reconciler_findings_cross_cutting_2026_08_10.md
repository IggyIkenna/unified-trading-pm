---
doc_type: issue
title: plan_reconciler findings — cross-cutting tranche — 2026-08-10
summary: >-
  Daily deep plan-reconciliation run-findings doc for the cross-cutting topic tranche, dispatch agt-33a6ec (slot 28).
  Records hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and
  coverage for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, cross-cutting, sharded-run]
related: [/plans/active/cross_cutting_consolidated_closeout_2026_07_25.md]
created: "2026-08-10"
author: plan_reconciler
source: agt-33a6ec
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler (agt-33a6ec) since 2026-08-10T00:20:00Z
depends_on: []
---

# plan_reconciler findings — cross-cutting tranche — 2026-08-10

Dispatch `agt-33a6ec`, slot 28, tranche `cross-cutting`. PM head at run start: `f8f07e7459`.

## Scope

147 docs carry `asset_group: cross-cutting` in `plans/active/` (incl. `issues/`). **58 of 147 are inside the 12-hour
grace window** (heavy concurrent fleet activity on this tranche — several sibling batch/finalize plan pairs and issue
docs created within the last few hours) — read-only context this run, not written. **89 are workable.**

Note: yesterday's cross-cutting run (`plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_09.md`,
`agt-627fc7`) shows all sections still `(none yet)`/`(in progress)` — it appears to have died mid-flight before its
first STEP-5 checkpoint. That doc is itself inside today's grace window (locked since 2026-08-09T16:00:00Z, <12h old at
this run's start) so it is read-only context only; not touched, not diagnosed further here (a dead one-shot dispatch
with zero committed content is not, by itself, an actionable finding for this run).

## Flips verified

1. `bucket_iam_write_protection_per_tier_2026_06_09.md` P1.3 — closed MOOT (superseded by P2.3's already-passing
   real-tier-pair test; P1.3 as worded tests the permanently-retired dev/stg pair). Doc now 100% done, locked
   (`live-defi-rollout`) — archive-ready-once-unlocked, see Archive candidates below. `unified-trading-pm@388f07d0d0`.
2. `data_completion_to_100_all_ag_2026_06_21.md` — 2 todos flipped: (a) VM-launch canonicalisation-gate check, verified
   via the archived `cross_cutting_satellite_ao_dispatch_batch1_2026_07_26.md`'s cited `deployment-service@c97fefc9`;
   (b) Step-4 credential-gated venues, verified via the same archive's re-verification (Tardis/Helius/Databento-core/
   Odds-API already live, Glassnode+Kaiko/Sportradar/Databento-ICE-OPRA correctly filed as their own issue docs).
   `unified-trading-pm@29d8e89f42`.
3. `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` — both main checkboxes (deployment-api quote_asset/
   margin_type API, deployment-ui heatmap filter) confirmed genuinely shipped (`deployment-api@c250348`,
   `deployment-ui@e2d109a`, both verified live-on-origin 2026-08-05) despite the doc's own pre-existing stale prose
   saying otherwise. Doc reached 0 open todos — archived, see Archive candidates. `unified-trading-pm@83a81279dc`.
4. `carry_staked_basis_funding_scan_experiment_2026_06_16.md` — 2 todos flipped (`--live` 11-venue snapshot mode; dYdX
   v4 + Vertex wiring), both verified shipped via `e2e-testing@6e2ffb8` (live-code-grepped in the current file, not
   sha-ancestry — this repo's history predates a documented 2026-08-05 rewrite that broke ancestor-checking for older
   commits). A 3rd (Drift creds/RPC) NOT flipped — genuinely ambiguous whether it duplicates a sibling MTDS todo, routed
   instead of guessed. `unified-trading-pm@<pending final push>`.

## Contradictions

1. `manifest_v6_batch3_residual_orphaned_work_2026_07_21.md` — checkbox-vs-prose contradiction (both checkboxes
   correctly `[x]`, the doc's OWN 08-03 prose was stale by the time a later 08-06 audit read it) — bridging notes added,
   2 malformed/duplicate Follow-up todos closed as moot rather than deleted. Resolved + archived (see Flips).
2. 3 docs citing `cross_cutting_consolidated_closeout_2026_07_25.md` as "over the 1000-line hard cap" — live-verified
   720 lines (already split via a prior commit). **Not yet fixed in the 3 citing docs** — routed, see Filed below (low
   priority, the citations are individually stale but harmless; a future pass can batch-fix).
3. `is_catalogue_g1_root_audit_log_2026_07_24.md` self-contradicts on G1.run-full-history ownership (one line says
   EXTRACTED elsewhere, another says still-owned-here) — **not yet resolved**, see Plans not reached.
4. `master_data_canonicalisation_migration_catalogue_2026_06_07.md`'s "Deferred work — migrated to:" section is
   orphaned/stale (dead line-number refs, one successor citation points at an archived doc) — **not yet resolved**, see
   Plans not reached.
5. `live_pipeline_persistence_hot_path_decoupling_2026_06_24.md` (`status: blocked`) — the blocking condition (a dead
   compactor job) is very likely resolved per a cross-repo grep, but needs a live `gcloud run jobs executions list`
   re-verify before flipping — **not yet resolved**, see Plans not reached.

## Codex corrections applied (mechanical, evidence-cited — STEP 5.f2 carve-out)

1. `/codex/05-infrastructure/manifest-consolidator-ssot.md` — ml-store consolidator fold ratio corrected "5 → 1" to "2 →
   1", matching `bucket_fold_ml_2026_07_17.md`'s own twice-stated ground truth (only 1 of 5 ml kinds ever had a
   consolidator). Single-row substitution, no governance area touched, no new measurement.
   `unified-trading-pm@<pending>`.
2. `/codex/02-data/carry-venue-live-integration-reference.md` §8 items 1 and 6 — added a "DONE for the e2e read" marker
   matching item 7's existing pattern, both verified shipped in the same `e2e-testing@6e2ffb8` change (live-code
   confirmed, see Flips #4). `unified-trading-pm@<pending>`.

**Self-correction (important — logged for the record):** an EARLIER fix this run (part of `29d8e89f42`) corrected 3
epics' stale-looking `assigned_vm: vm-cross-cutting`/`vm-operator-ops`/`vm-ml` to `NA`, reasoning from the precedent of
3 sibling epics already fixed from `assigned_vm: planning`. That precedent does NOT actually apply — `planning` on an
epic is a live, misleading claim (D2 explicitly dropped epic-level dispatch); a legacy `vm-<id>` is EXPLICITLY
sanctioned as historical archaeology per an on-the-record 2026-07-12 ruling (finding 123/262, §A2 B-queue, cited
verbatim in `instruments_master.md`/`sports_master.md`: "RETAINED WORKSPACE-WIDE... migration OUT OF SCOPE"). Self-
caught while reviewing my own diff; reverted in `unified-trading-pm@27781e212d` before it could compound into a fresh
contradiction for a future audit to untangle. Logged here per the "report what did NOT land cleanly" honesty rule — this
was a genuine near-miss, not something to bury.

## Hygiene fixes

1. `instruments_mtds_consistency_remediation_residuals_2026_07_24.md` — repaired 9 instances of mojibake corruption
   (double-encoded 🔴/🟢 emoji + `×` multiplication sign, likely from the 2026-07-24 verbatim split from an archived
   parent). Content-only, isolated to this file (corpus-checked). `unified-trading-pm@42b68c8ba8`.
2. **Epic-roster regeneration** (`scripts/plans/populate_epic_bodies_2026_05_21.py --apply`) — ALL 22 epics were stale
   (derived "Assigned active plans" roster + `related_plans:` frontmatter drifted from live corpus state); ran
   corpus-wide since the tool is a pure DERIVED-projection regenerator (Phase-4's "regenerate via tooling, never
   hand-sync" pattern) with no narrative-content risk (spot-checked diffs on `mtds_mdps_master`/`defi_master`/
   `infrastructure_master` — only the roster section + `related_plans:` changed). `mtds_mdps_master` alone was 4 real
   docs behind (4→8); `instruments_master` undercounted 16→23. `unified-trading-pm@29d8e89f42`.
3. `strategy_master.md` epic hub — dropped a hardcoded "53 archetypes" from its own Codex-SSOTs pointer line, which
   contradicted the SAME doc's body 2 paragraphs above (which already explains the count is a live code figure, not a
   constant, and specifically warns against this exact restatement pattern).
4. `capability_wizard_analysis_findings_2026_06_11.md` — F5's "Status: OPEN" corrected to RESOLVED (verified fixed
   2026-07-27 via `unified-trading-pm@ce6eb1775` in the sibling gap-discovery doc, never reflected back); F12/F14's
   hedge-pointer ("decision deferred to the UI-phase owner") resolved to a confirmed real successor doc.
5. `carry_staked_basis_funding_scan_experiment_2026_06_16.md` — annotated a duplicate Aave-Ethereum backfill todo as
   superseded-in-place by its own doc's more refined follow-up todo (same gap, tracked twice).

## Filed

1. **`plans/active/issues/deployment_api_prod_disable_auth_true_2026_08_06.md`** — live unauthenticated prod Cloud Run
   endpoint (`uts-shared-deployment-api`), open 4+ days with 2 prior re-flags (na-eligibility-audit 2026-08-07,
   ag-closeout-audit 2026-08-08 ×2), still unresolved. Escalated immediately rather than batching at end-of-pass given
   severity: `BLK-46b42d75` (options A/B/C, recommendation A, evidence-backed via a fresh consumer-count grep). Progress
   Log entry appended to the target doc itself (already carries the tracked `- [ ]` todos — no new todo needed, this is
   a re-verify + escalate, not a new finding). Not counted as a hunter candidate (found via direct read while
   cross-referencing grace-window `ag_closeout_audit_cross_cutting_parked_*` docs for the Phase-0 pileup check).

## Archive candidates (operator review)

1. `bucket_iam_write_protection_per_tier_2026_06_09.md` — 100% done (last todo closed this run),
   `locked_by: live-defi-rollout` — needs `[unlock-plan]` before the standard archival ritual can run. Its gated
   finalize plan (`bucket_iam_write_protection_per_tier_2026_06_09_finalize_2026_07_27.md`) can dispatch once the parent
   flips `active`.

## Refuted (dropped by verify)

(none yet)

## Coverage (hunters / batches / docs)

(in progress)

## Plans not reached

(none yet)
