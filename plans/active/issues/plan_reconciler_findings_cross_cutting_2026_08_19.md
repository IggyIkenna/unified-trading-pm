---
doc_type: issue
title: plan_reconciler findings — cross-cutting tranche — 2026-08-19
summary: >-
  Daily deep plan-reconciliation run-findings doc for the cross-cutting topic tranche, dispatch agt-b2fcb2 (slot 11).
  Records hunter-detected candidates, adversarial-verification outcomes, applied fixes, routed operator questions, and
  coverage for this run. Also the progress journal for the run itself.
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [role, plan_reconciler, reconciliation, plan-hygiene, cross-cutting, sharded-run]
related:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_18.md,
    /plans/active/issues/plan_reconciler_findings_security_and_cross_cutting_master_2026_08_19.md,
  ]
created: "2026-08-19"
author: plan_reconciler
source: agt-b2fcb2
parent_epic: security_and_cross_cutting_master
assigned_vm: NA
execution_scope: local-only
priority: P2
estimate_class: infra
estimate_baseline: 0.1
calibrated_ai_days: 0.1
assigned_role: backend_engineer
drift_direction: fix
resolved_by:
locked_by: plan_reconciler (agt-b2fcb2) since 2026-08-19T18:33:40Z
locked_since: "2026-08-19T18:33:40Z"
depends_on: []
context_scope:
  [
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/plan_reconciler_findings_cross_cutting_2026_08_18.md,
    /plans/active/issues/plan_reconciler_findings_security_and_cross_cutting_master_2026_08_19.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# plan_reconciler findings — cross-cutting tranche — 2026-08-19

Dispatch `agt-b2fcb2`, slot 11, tranche `cross-cutting`. PM head at run start: `4865661cd289`.

## Scope

177 docs carry `asset_group: cross-cutting` in `plans/active/` (incl. `issues/`), up from 174 at the 2026-08-18 run.
`generate_tranche_doc_inventory.py --tranche cross-cutting` is the SSOT source (never a same-line grep, per
SKILL.md's own caveat).

**Overlap with today's epic-scoped run** — an epic-scoped `/plan-reconcile security_and_cross_cutting_master` run
(laptop session, `plan_reconciler_findings_security_and_cross_cutting_master_2026_08_19.md`) achieved 100% coverage
(233/233 docs) of that epic just hours before this dispatch. 65 of my 177 cross-cutting docs declare
`parent_epic: security_and_cross_cutting_master` directly (+1 more via the now-superseded `infrastructure_master`
name, fixed this run — see Hygiene fixes). Re-hunting those 66 from scratch this run would duplicate work completed
hours ago; instead this run (a) verified that epic-scoped session's claimed fixes actually landed (see Phase -1),
and (b) scoped its OWN fresh hunter sweep to the **112 cross-cutting docs NOT under that epic** (a different set of
epics: `observability_master` 24, `agent_operating_framework_master` 13, `batch_live_symmetry_master` 12,
`system_readiness_master` 11, `instruments_master` 10, `ci_master` 8, `plan_hygiene_master` 7, `manifest_master` 7,
`mtds_mdps_master` 6, `strategy_master` 5, `features_and_ml_master` 3, `uac_master` 2, `orchestrator_master` 1,
`execution_master` 1). Of those 112: **41 are inside the 12-hour grace window** (read-only context this run), leaving
**70 workable**, partitioned by LPT bin-packing into 5 size-balanced batches (~504KB / 14 docs each) for one wave of
5 parallel hunters (the corrected 5-parallel cap per `SUB_AGENT_MANDATORY_RULES.md`, not the stale `≤10` figure in
`agents/plan_reconciler.md`/`SKILL.md`).

## Phase -1 (prior findings reconciliation)

- **`plan_reconciler_findings_cross_cutting_2026_08_18.md`** (same tranche, most recent prior tranche-scoped run) —
  **grace-protected this run** (last commit 2026-08-19T14:26:16Z, ~4h old at run start — inside the 12h window,
  itself the tail of a na-eligibility-audit pass that extracted 7 of its 12 "Plans not reached" items into
  `cross_cutting_satellite_ao_dispatch_batch18_2026_08_19.md`). Cannot edit/archive it this run. Read in full for
  priority input — 4 genuinely-open items remain in its "Plans not reached" list
  (`features_service_clean_check_dangling_fleet_ci_dedup_revert_2026_08_07.md` [routed to na-eligibility-audit's
  disjoint remit], `cross_cutting_data_type_completeness_capture_mis_scoped_ao_dispatch_2026_08_15.md` [DIAG P3],
  `per_client_config_surface_keying_and_missing_axes_2026_08_12.md` [REVIEW P3, re-confirmed only],
  `ao_scheduled_skills_benchmark_and_ruled_decisions_session_2026_07_30.md` [REVIEW P3, needs external artifact
  access]) plus 1 open Contradiction (`deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md`
  — genuinely unresolved, needs an engineer to re-bisect, not a doc-hygiene gap). None are P0/P1; carried forward as
  priority-input for a future pass rather than re-derived from scratch — see "Next steps" below.
- **`plan_reconciler_findings_security_and_cross_cutting_master_2026_08_19.md`** (epic-scoped, overlapping
  population) — **NOT grace-protected** (last commit 2026-08-19T03:57:30Z, ~14.6h old at run start). Its own text
  flagged a **"DO-NOT-SHIP"** constraint (laptop session, shared-checkout contention) — every one of its ~20 fixes +
  2 archivals claimed as applied only to that session's uncommitted working tree, "the lead session ships." **Verified
  this run, live against the freshly-pulled tree, that a lead session DID ship it**: commit `b9670b9e66` ("Karak
  safety correction, 3 archivals, done-but-unchecked flips, line-1 fixes, HTML report"). Spot-checked 5 representative
  claims, all confirmed landed — `infra_satellite_ao_dispatch_batch12_finalize_2026_08_09.md` archived to
  `plans/archive/2026_08/`; `deployment_api_ar_repo_override_audit_and_iam_probe_2026_08_07.md` archived to
  `plans/archive/issues/`; `plans/epics/security_and_cross_cutting_master.md` frontmatter (`assigned_vm: NA`,
  `locked_by` cleared, `last_updated` bumped) all correct; `pm_qg_self_audits_from_a_worktree_phantom_drift_2026_08_10.md`
  `assigned_vm: planning` flip landed; the Karak/pendle/symbiotic correction is present in
  `venue_readiness_and_registry_hardening_2026_08_16.md` (todo 597-601, `unified-trading-pm@abf0117caa`). **Not
  archived** — it still carries ~35 genuinely-open "Filed" todos (confirmed-but-not-applied findings across
  contradictions / AO-readiness defects / hedge-pointers / structural issues / an archive-candidate cluster); stays
  active. Not re-litigated line-by-line this run (would consume the whole run's budget re-verifying a sweep that
  finished hours ago) — treated as already-durably-tracked (every item is a `- [ ]` todo in that doc, none
  silently dropped). Its 1 stale-epic-tag mechanical finding (see Filed #1 below) fell directly in my own
  tranche+non-grace population — found and verified ready-to-apply, but blocked by a pre-existing line-cap overage,
  so filed rather than landed.

## Contradictions

**Fixed the drift, routed the remediation (P0):**

1. **P0** `venue_e2e_wiring_2026_08_16.md` — scoped and partly-executed (5 dependent AG batch plans, 4 already
   archived done) against a **353 `(venue, data_type)`-pair** denominator, but that model was superseded 2026-08-17
   by a shipped, operator-ruled `unified-api-contracts@d19866d339`: the real unit is now **660 `(venue,
   instrument_type, data_type)` triples** (12 cells unresolved, 3.4%) — HARD evidence:
   `nick_ai_platform_readiness_remediation_finalize_2026_08_16.md`'s 2026-08-18 Progress Log entry ("W6's blocker
   cleared... denominator re-measured 353 → 660"). Independently corroborates a P1 finding already surfaced (not yet
   applied) by today's epic-scoped `security_and_cross_cutting_master` sweep. **Fixed**: added a prominent, dated
   staleness banner directly under the doc's "Universe denominator" heading (citing the exact shipped commit + the
   nick_ai doc), so no future reader/worker cites "353"/"192 declared venues" as current without seeing the flag —
   `unified-trading-pm@c0ca00144f`. **NOT fixed, routed**: whether/how the 5 AG batches' already-in-flight/archived
   scope needs re-deriving under the 660-triple unit is a genuine engineering re-scoping question, not a text
   substitution — no source of truth settles the REMEDIATION (only the fact that 660 supersedes 353). Alerted via
   `/blocked` (`BLK-f87a4927`, 3 options + `[WORKER REC]` A — re-derive the AG-batch row-lists under the new axis
   now; `can_continue: true`) and filed durably here — see "Resolved via /blocked" below once answered.

**Verified already-current (no action needed):**

2. `deployment_service_basedpyright_ratchet_broken_by_dep_backmerge_2026_08_15.md` — BOTH prior cross-cutting
   findings docs (08-16, 08-18) carried this forward as "genuinely unresolved, needs an engineer to re-bisect." Read
   fresh this run: **already resolved doc-wise by a concurrent sibling run** — its own summary now reads "Root cause
   is genuinely UNKNOWN as of this correction (2026-08-19, plan-reconcile `observability_master`... previously
   stated the falsified theory as settled fact, already flagged twice by prior `/plan-reconcile` passes and left
   unfixed)" — i.e. a sibling `observability_master`-epic-scoped `plan_reconciler` run fixed exactly the drift both
   my predecessor tranche runs flagged, earlier today. **Also reclassified out of my tranche**: `asset_group`
   corrected `[cross-cutting] → [ci]` in the same pass (own comment: "a deployment-service CI/quality-gate ratchet
   break, own tags already say 'ci', not data-pipeline scope") — no longer cross-cutting-tranche population, a
   sibling `ci`-tranche worker's doc now. The underlying `[OPERATOR]` BLOCKED-OPERATOR-DECISION (relax
   `BASEDPYRIGHT_MAX_ERRORS` 1259→1261, or hold shipping) remains genuinely open — already correctly parked with
   options + a recommendation, not re-parked here (would be a duplicate escalation for an already-surfaced
   question, now outside my scope besides).
3. `issues/dp_watcher_stale_003_identity_after_registry_id_bump_to_004_2026_07_31.md` (still `parent_epic:
   security_and_cross_cutting_master`, covered by today's epic sweep) — its Filed AO-readiness finding (worst
   line-1-completeness instance + stale line-number citations) verified real but P3/cosmetic (doc's own words:
   "Cosmetic only... no data loss, no functional regression"). Its actual fix is already WRITTEN (per the doc's own
   2026-08-15 Progress Log, sitting uncommitted in a slot-15 working tree as of that date) but blocked on the SAME
   basedpyright ratchet operator-decision as #2 above — already correctly parked there, nothing new to add. Not
   re-fixing the stale line-number citations myself this run (P3, would need a fresh live grep against
   currently-drifted line numbers to do safely, and the doc is not in this run's fresh-hunt population).

## Hygiene fixes

(none landed this run — see Filed #1 below for the one candidate found, blocked by a pre-existing line-cap)

## Filed

1. **[Line-cap-blocked-done]** `cross_cutting_satellite_ao_dispatch_batch13_2026_08_13.md` — `parent_epic:
   infrastructure_master` is stale (the epic was renamed/superseded 2026-08-18 per
   `plans/epics/infrastructure_master.md`'s own banner: "This epic was renamed to
   `security_and_cross_cutting_master.md`... CI-topic references carved out to `ci_master.md`, UAC-topic references
   carved out to `uac_master.md`"). This doc's own sibling `_finalize` plan already carries the corrected
   `parent_epic: security_and_cross_cutting_master` — single unambiguous substitution, HARD evidence (the epic's own
   banner + the sibling doc's already-correct value), no judgment call, ready to apply as-is. **Blocked**: the doc is
   1092L, over the 1000L hard line-cap (pre-existing, already inside the corpus-wide ratchet baseline — the
   corpus-wide sweep doesn't flag it — but prek's staged-file `check_line_caps.sh` hard-blocks ANY commit touching an
   over-cap file, so even this 1-line frontmatter fix cannot land until the doc is split). Reverted the edit rather
   than leave it dangling uncommitted. Per Phase 4/5 ("Line-cap-blocked-done is a distinct sub-case"), this is an
   operator-gated split finding, not a doc-hygiene gap — routing it rather than forcing the split myself. **Exact fix
   for whoever runs the split**: line 40, `parent_epic: infrastructure_master` →
   `parent_epic: security_and_cross_cutting_master`.
2. **[Out of tranche scope, noted only]** 2 other docs still cite the stale `infrastructure_master` epic name
   (`deployment_network_egress_ingress_observability_2026_08_18.md`,
   `manifest_hygiene_daily_malformed_frontmatter_blocks_quickmerge_2026_08_19.md`) but both are `asset_group:
   [infrastructure]` — a sibling `infra`-tranche worker's population, not this run's to fix.
3. **[Delete-risk tagging, verified largely self-mitigated]** `cross_cutting_satellite_ao_dispatch_batch1b_2026_07_26.md:113`
   — flagged by today's epic sweep as its highest-priority Filed item ("sole open todo['s]... no `[OPERATOR]`/
   `BLOCKED-<TOKEN>` tag" on delete-risk-adjacent work). Read the full todo (only open checkbox in the doc, 749L):
   its own body (lines 173-181) already explicitly narrates the risk AND defers the actual classify/delete/relocate
   work entirely to a sibling, already-gated doc (`repo_scripts_governance_audit_2026_06_18.md`, `assigned_vm: NA`,
   its own Finding 1), stating in-line "do not re-flip this checkbox until the governance-audit plan's Phase-1...
   actually lands." The remaining scope THIS item still tracks is narrower than the original finding assumed — not
   a live unsupervised-delete exposure today, since the delete portion is prose-deferred elsewhere. A defense-in-depth
   `[OPERATOR]`-adjacent tag would still be an improvement (machine-visible, not just prose-buried), but exactly what
   tag/rewrite is the right one given the item's now-narrower remaining scope is a judgment call, not a mechanical
   substitution — filed rather than guessed at.

## Resolved via /blocked (closed same run)

1. **`BLK-f87a4927`** — `venue_e2e_wiring_2026_08_16.md` P0 denominator-drift re-scoping question (see
   Contradictions #1 above). **ANSWERED 2026-08-19T18:46:58Z: B** (leave the 5 AG batches as-is; open a separate
   follow-up plan) — NOT my `[WORKER REC]` A, applied as ruled. **Applied same run**: filed
   `plans/active/issues/venue_e2e_wiring_660_triple_rescoping_2026_08_19.md` (4 tracked `- [ ]` todos: re-derive the
   660-triple delta list, verdict each delta row, fork fresh AG batches for genuinely-new rows, close out the
   banner) — `assigned_vm: NA` (default, not explicitly ruled either way this round); updated
   `venue_e2e_wiring_2026_08_16.md`'s banner to record the ruling + point at the new doc instead of "unresolved".
   No AG batch file touched, per the ruling. `unified-trading-pm@<this commit>`.

## Progress Log

- **2026-08-19T18:33Z (run start)**: dispatch `agt-b2fcb2`, slot 11. RULES.md + plan_reconciler.md +
  `SUB_AGENT_MANDATORY_RULES.md` read. STEP 1: PM pulled current (already up to date, HEAD `4865661cd289`); 27
  sibling repos FF'd (WARN: `unified-trading-ci` and `unified-trading-library.stale-pre-history-rewrite-*` not
  FF-clean — flagged for any STEP-4 verification depending on them). Hygiene sweep (`--ci`): 1 pre-existing hard
  failure (`assigned_vm:NA` corpus size ratchet — standing, `/na-eligibility-audit`'s remit), 1 soft warning
  (delete/VM-launch todo tagging candidate signal). Discarded 3 files of `--ci` regen side-effect dirt
  (`master_to_live_defi`, `INDEX.md`, the archived dashboard) before any commit. Phase -1 complete (see above): both
  prior cross-cutting-adjacent findings docs reconciled — the 08-18 tranche doc is grace-protected (read for
  priority input, 4 items + 1 contradiction genuinely still open, none P0/P1); the epic-scoped 08-19 doc's
  DO-NOT-SHIP fixes verified actually landed (`b9670b9e66`), its 1 stale-epic-tag finding found+filed (blocked by a
  pre-existing line-cap, see Filed #1). Tranche inventory:
  177 docs; 66 already covered by today's epic sweep; of the remaining 112, 41 grace-protected + 70 workable,
  bin-packed into 5 hunter batches. About to launch the wave of 5 hunters over the 70-doc workable supplementary
  set.
