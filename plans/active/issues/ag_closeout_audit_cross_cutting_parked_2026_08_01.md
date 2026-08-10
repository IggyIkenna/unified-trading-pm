---
doc_type: issue
title:
  "Parked findings from the 2026-08-01 /ag-closeout-audit cross-cutting run (6 asset_group mistags — genuine content is
  ao/ci/ui-or-infra/infrastructure/ao/tradfi — found via the Phase 1 Workflow's step-5 scope sanity-check, not retagged
  per the concurrent-sharded-worker owning-tranche rule)"
summary: >-
  6 NEW mechanically-verified `asset_group` mistags surfaced by the 2026-08-01 `/ag-closeout-audit cross-cutting` run
  (scheduled daily run, dispatch `agt-a5c7d6`, slot 13). All 6 candidate docs carry `asset_group: [cross-cutting]` but a
  per-doc Phase 1 Workflow (12 agents) found their real content is genuinely single-tranche — 2 are ao, 1 is ao-or-ci
  (spans both), 1 is ui-or-infra (deployment-api specific), 1 is infrastructure, 1 is tradfi-only. 4 of the 6 are
  independently corroborated by OTHER tranches' own recent audits reaching the same conclusion (the `ao` tranche's
  consolidated closeout already lists 3 of them in its own "genuine AO content but asset_group MISTAGGED" bucket; a
  sibling linkage-gate issue doc independently measured a 4th as one of "29 never-cited docs" under the cross-cutting
  tag). Per the skill's 2026-07-30 concurrent-sharded-worker rule ("a retag... belongs to the OWNING tranche alone, so N
  workers never race the same file"), this run does NOT perform any of the 6 retags itself — it reports them here,
  evidence-backed, for each owning tranche's own next audit pass to action directly (no further judgment call needed,
  the evidence is conclusive in every case). Recorded here per the "Parked findings ALWAYS get a durable issue doc" hard
  rule (this run reached only Phase 0-2 + a Phase 3 draft for the disjoint orphaned population — see
  `cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md` — these 6 mistags are excluded from that batch by
  definition, per Phase 2's "count by verdict, excluding exclude_cross_cutting").
status: open
nature: issue
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [cross-cutting, ag-closeout-audit, asset-group-mistag, parked-findings, orthogonality]
related:
  [
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-01"
author: unknown
last_updated: "2026-08-01"
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: local-only
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: data_engineering
drift_direction: none
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
depends_on: []
source: >-
  `/ag-closeout-audit cross-cutting` run 2026-08-01 (ag_closeout_auditor scheduled worker, dispatch agt-a5c7d6, slot
  13). Phase 0 via `generate_ag_closeout_audit_candidates.py --tranche cross-cutting` (90 members, 11 never-cited) + a
  manual asset_group:meta-sweep gap check (1 more member found). Phase 1 Workflow (12 agents) classified all 12; these 6
  verdicted exclude_cross_cutting with step-5 scope evidence.
context_scope:
  [
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
    /plans/archive/2026_08/cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md,
    /plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
  ]
---

# Parked findings — 2026-08-01 `/ag-closeout-audit cross-cutting` run

## New findings this run

### 1. `plans/archive/2026_07/ao_slot_capacity_policy_ci_scheduled_split_2026_07_29.md` — likely real owner `ao` + `ci` (spans both)

**Doc state**: `status: active`, `asset_group: [cross-cutting]`, `nature: process`, `stage: [meta]`. All 8 todos `[x]`
✅ with dated evidence; the 2026-07-31 Progress Log entry states the plan is complete but was deliberately left
`status: active`/not archived pending the operator's own archival-ritual pass.

**Why not cross-cutting**: content is 100% agent-orchestrator worker-slot-reserve policy (`server/config.py`,
`autospawn.py`, `plan_health.py`) plus a fleet-wide Cloud Build GAR-auth CI fix rolled out across 6 repos and a GitHub
Actions billing-wall incident — squarely `ao` and `ci` tranche content, never touching cefi/defi/tradfi/
prediction/sports business logic. Tags (`agent-orchestrator`, `capacity`, `ci-cd`, `scheduled-dispatch`, `slot-reserve`,
`cloud-build`) corroborate.

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[ao, ci]` (content genuinely spans both);
independently, this doc also qualifies `archivable_now` once retagged and correctly homed — flag to whichever tranche's
audit picks it up that it's ready for the standard archival ritual, not just a retag.

### 2. `plans/active/issues/checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md` — likely real owner `ao`

**Doc state**: `status: open`, `asset_group: [cross-cutting]`, `assigned_vm: NA`. 1 open todo (`[BACKEND] P3`,
operator-gated 3-way design decision on hardening the `/done` plan-flip verification guard).

**Why not cross-cutting**: content is entirely agent-orchestrator internal-tooling — a detection gap in the
`cross_repo_pm_file_touched_no_checkbox_flip` guard (`server/verify.py`) where git's rename-similarity heuristic lets a
bundled flip+archive commit evade detection. Zero cefi/defi/tradfi/prediction/sports content.

**Independent corroboration**: `plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md`'s "Satellite
AO-dispatch layer" section (a 2026-07-31 audit entry) already lists this doc BY NAME in its own 23-doc "genuine AO
content but asset_group MISTAGGED (meta/cross-cutting/infrastructure)" bucket. Its closest sibling bug over the same
guard mechanism, `plans/archive/issues/ao_done_gate_checkbox_flip_blind_to_self_archived_plan_ref_2026_07_26.md`
(resolved), carries `asset_group: [ao]`.

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[ao]`; the `ao` tranche's own 2026-07-31 audit
has already identified this exact doc for retag — this finding corroborates that one, it does not duplicate new work.

### 3. `plans/active/issues/deployment_api_sigabrt_crash_loop_unresolvable_sha_citation_2026_07_31.md` — likely real owner `ui` (or `ci`/`infra`)

**Doc state**: `status: open`, `asset_group: [cross-cutting]`, `parent_epic: infrastructure_master`. 1 open todo
(`[REVIEW] P3`: find the real commit a stale check-in meant to cite as SIGABRT-fix evidence, since the cited SHA
`agent-orchestrator@7ba17e2` does not exist on any ref).

**Why not cross-cutting**: this is a quality-gate/evidence-integrity finding whose actual remaining action is
deployment-api-specific. Its sibling doc of the identical issue-class,
`mtds_plan_flip_fabricated_commit_sha_evidence_2026_07_30.md`, is tagged `[meta]`, not cross-cutting. The parent doc
this issue is ABOUT, `deployment_api_sigabrt_crash_loop_2026_07_24.md`, had its own `asset_group` corrected 2026-07-30
from `[meta]` to `[ui]` with the explicit note "a deployment-api container stability bug" — this whole doc family's true
home is the `ui`/deployment-api tranche. A same-day independent `ao`-tranche audit reached the same tranche-mismatch
conclusion from the other direction, describing it as "deployment-api bug; an agent-orchestrator SHA is just cited as
evidence."

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[ui]` (matching the corrected parent doc) or
`[ci]` (matching the evidence-integrity sibling's `[meta]`→real-tranche mapping) — either is defensible, `ui` has the
stronger direct precedent. Independently orphaned regardless of tranche (zero coverage found anywhere in the corpus
beyond 2 incidental precedent-naming mentions).

### 4. `plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md` — likely real owner `infrastructure`

**Doc state**: `status: open`, `asset_group: [cross-cutting]`, `parent_epic: infrastructure_master`. 4 open todos (1
`[OPERATOR]` direction call, 3 `[INFRA]` bounded/partially-bounded audits).

**Why not cross-cutting**: a read-only GCP IAM audit finding the declared per-service least-privilege SA/bucket model
(`deployment-service/configs/gcp_service_accounts.yaml`) was never actually provisioned live. This is project-wide
org/account-admin hygiene — `infra_consolidated_closeout_2026_07_25.md`'s own summary lists "org/account admin" as
in-scope `infra` content verbatim, and this doc's `parent_epic: infrastructure_master` is identical to the infra
tranche's own top-level coordinator doc (cross-cutting-tranche docs instead cluster under
`instruments_master`/`mtds_mdps_master`/`manifest_master`/`features_and_ml_master`). The doc was created 2026-07-31,
well after the 2026-07-27 `asset_group` ao/ci/infra schema expansion — looks like a simple default-to-generic-label
oversight, the same pattern the infra tranche's own coordinator doc had to self-correct on 2026-07-29 ("was
[cross-cutting]").

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[infrastructure]`. Bonus for whichever worker
picks this up: independently confirmed `orphaned_never_touched` regardless of tranche (zero citation anywhere in either
the cross-cutting OR the infra closeout family), with 2 of its 4 remaining items already AO-eligible (enumerate live
Cloud Run runtime SAs; document default-compute-SA security exposure) — a real, ready `infra` batch-candidate once
retagged, not just a retag-only finding.

### 5. `plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md` — likely real owner `ao`

**Doc state**: `status: open`, `asset_group: [cross-cutting]`, `parent_epic: infrastructure_master`. 2 open
`[SCRIPT] P3`/`[DATA] P3` todos (item 1 already `[x]` done).

**Why not cross-cutting**: content is 100% CI/CD workflow-template-parity mechanics scoped to the agent-orchestrator
repo's own `.github/workflows/` copies during its self-hosted-runner migration — never touches cefi/defi/tradfi/
prediction/sports business logic.

**Independent corroboration (two separate signals)**: (a) `ao_open_issues_consolidated_close_out_2026_07_17.md`'s
2026-07-31 audit entry lists this doc BY NAME in the same 23-doc "genuine AO content but asset_group MISTAGGED" bucket
as finding 2 above; (b) `issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` independently measured
this doc among its own "29 never-cited docs" under the cross-cutting tag on 2026-07-30 — corroborating this run's direct
citation-grep finding the same zero-coverage result a day earlier.

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[ao]`; two independent, more-recent
corpus-internal audits already point the same direction — this is the 3rd doc in this parked list the `ao` tranche's own
audit has already flagged for retag (see findings 1, 2 above), suggesting the `ao` tranche's next pass should sweep for
and action all cross-cutting-tagged-but-AO-content docs as one batch rather than one at a time.

### 6. `plans/active/tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md` — likely real owner `tradfi`

**Doc state**: `status: draft`, `asset_group: [cross-cutting]`, `assigned_vm: NA`. 6 of 7 todos open (design doc for a
ForexFactory economic-calendar scraper).

**Why not cross-cutting**: filename-prefixed `tradfi_`, tags are
`[tradfi, macro, economic-calendar, consensus, forexfactory, scraper, features-service]` with zero
cefi/defi/sports/prediction tags, and a full-doc grep for `cefi|defi|sports|prediction` returns zero hits. The doc's own
lineage (`related:` → the genuinely cross-cutting 5-AG audit `macro_micro_econ_data_capture_audit_2026_06_05.md`) states
in ITS OWN summary that "Macroeconomic data is essentially TradFi-only and thin" — i.e. the corpus's own prior
cross-cutting audit already classifies this data domain as tradfi-specific, not multi-AG. This doc appears to have
simply inherited the `[cross-cutting]` tag from that parent audit's context rather than being re-scoped for its own
narrower tradfi-only deliverable — the same fork-inherits-parent's-tag pattern the skill's own SKILL.md documents as a
confirmed recurring class (6 prior examples fixed 2026-07-25).

**Recommendation [WORKER REC]**: retag `asset_group: [cross-cutting]` → `[tradfi]`. Independently orphaned regardless of
tranche (zero coverage found anywhere) — ready for the tradfi tranche's own next audit pass to pick up as a fresh
member, not just a retag.

## Todos

> **2026-08-10 — findings from this doc are now DISPATCHED, not orphaned.** The bounded, worker-determinable items below
> (mechanical `asset_group` retags, stale-claim fixes, checkbox reconciliation) were extracted into
> `/plans/active/meta_plan_corpus_hygiene_ao_dispatch_batch1_2026_08_10.md` (`assigned_vm: planning`, `status: active`)
> and are being executed there. They stayed unactioned here only because this doc is `assigned_vm: NA` /
> `execution_scope: local-only`, so nothing could ever pick them up. **A future `/ag-closeout-audit` run must NOT
> re-park them** — per `cursor-configs/skills/ag-closeout-audit/SKILL.md` § "Three things that must NOT reach a parked
> doc" rule 3, a finding lives in exactly one place at a time. Their checkboxes here are reconciled in one pass by that
> plan's own todo 17 once the work lands — do not flip them early.

- [x] ✅ [DOCS] P3. ~~Retag `plans/archive/2026_07/ao_slot_capacity_policy_ci_scheduled_split_2026_07_29.md`'s
      `asset_group` `[cross-cutting]` → `[ao, ci]` (finding 1)~~ — owning-tranche fix, leave to the `ao`/`ci` tranches'
      own audit, not this run. Done when: the tag is corrected, the doc is folded into the receiving tranche(s)'
      closeout membership, and (since all 8 todos are already done) it is routed through the standard archival ritual.
      **DONE (na-eligibility-audit 2026-08-03)** — the doc's `asset_group` is now `[ci]` (corrected 2026-08-02, comment:
      "operator-ruled... squarely ci-tranche, not generic cross-AG content" — a refinement of this todo's proposed
      `[ao, ci]` to `[ci]` only, not a discrepancy), and it carries a full `✅ ARCHIVED 2026-08-02` banner citing
      `plan_reconcile_parked_operator_decisions_2026_08_02.md` na-eligibility-audit item 22 as the archival
      authorization (all 8/8 todos done, `locked_by` cleared).
- [ ] [DOCS] P3. Retag
      `plans/active/issues/checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md`'s `asset_group`
      `[cross-cutting]` → `[ao]` (finding 2). Done when: the tag is corrected and the doc is folded into
      `ao_consolidated_closeout_2026_07_25.md`'s membership (already named there per the 2026-07-31 audit — confirm the
      retag catches up to that citation). **na-eligibility-audit 2026-08-03**: `ao_consolidated_closeout_2026_07_25.md`
      is now archived `status: complete` (2026-07-30), but that doesn't close this todo — checked the target doc's
      current frontmatter and the retag has NOT happened yet:
      `checkbox_flip_bundled_with_archival_git_mv_evades_flip_guard_2026_07_31.md` still carries
      `asset_group: [cross-cutting]`. Still genuinely open; not flipping.
- [x] ✅ [DOCS] P3. ~~Retag
      `plans/active/issues/deployment_api_sigabrt_crash_loop_unresolvable_sha_citation_2026_07_31.md`'s `asset_group`
      `[cross-cutting]` → `[ui]` (finding 3).~~ **MOOT — 2026-08-01 (slot 9, review)**: the doc's one remaining todo
      (the SHA-citation fix this retag was predicated on) resolved to a stale-clone false positive — the citation was
      already correct on trunk — and the doc has been archived to
      `/plans/archive/issues/deployment_api_sigabrt_crash_loop_unresolvable_sha_citation_2026_07_31.md` per the
      archival-discipline HARD RULE (zero open todos, `locked_by:` empty). No retag needed on an archived doc.
- [ ] [DOCS] P3. Retag
      `plans/active/issues/gcp_service_accounts_registry_diverged_from_live_provisioning_2026_07_31.md`'s `asset_group`
      `[cross-cutting]` → `[infrastructure]` (finding 4). Done when: the tag is corrected, the doc is folded into
      `infra_consolidated_closeout_2026_07_25.md`'s membership, and its 2 AO-eligible items (live SA enumeration;
      default-compute-SA risk documentation) are considered for the infra tranche's next batch.
- [x] ✅ [DOCS] P3. ~~Retag `plans/active/issues/workflow_template_drift_repeated_during_phase7_rollout_2026_07_27.md`'s
      `asset_group` `[cross-cutting]` → `[ao]` (finding 5)~~. Done when: the tag is corrected and the doc is folded into
      `ao_consolidated_closeout_2026_07_25.md`'s membership (already named there per 2 independent prior audits).
      **DONE, WITH A CORRECTION (na-eligibility-audit 2026-08-03)** — the doc's `asset_group` is now corrected
      (2026-08-02, operator-ruled per the Q&A recorded in
      `/plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`, commit
      `unified-trading-pm@5432f2c06`), but to `[ci]`, not `[ao]` as this todo proposed: comment reads "content is
      workflow-template-parity QG drift during the Phase-7 self-hosted-runner rollout, squarely ci-tranche... not
      generic cross-AG content." That also means the "fold into `ao_consolidated_closeout_2026_07_25.md`" clause is moot
      — the doc's real home is the `ci` tranche (`ci_consolidated_closeout_2026_07_25.md`, itself also archived
      `status: complete`), not `ao`. The underlying goal (fix the wrong cross-cutting tag) is achieved; this todo's
      specific proposed target tranche was superseded by the operator ruling (see
      `/plans/archive/2026_08/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` cited above).
- [x] ✅ [DOCS] P3. ~~Retag `plans/active/tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md`'s
      `asset_group` `[cross-cutting]` → `[tradfi]` (finding 6)~~ — **DONE (na-eligibility-audit 2026-08-07)**. Verified
      directly: the target doc's `asset_group` is now `[tradfi]` (inline comment: "corrected 2026-08-02
      ag-closeout-audit tradfi tranche -- was [cross-cutting], a genuine mistag... tags already say tradfi"). Fold-in
      confirmed too — the doc is cited in `plans/active/tradfi_satellite_ao_dispatch_batch7_2026_08_06.md` (+ its
      finalize), the tradfi tranche's live dispatch family. Both Done-when clauses satisfied.

## Progress Log

- **na-eligibility-audit 2026-08-02**: KEEP-NA, valid -- a cross-tranche PARKED-FINDINGS register: all 5 open todos are
  `[DOCS] P3` `asset_group` retags of docs owned by OTHER tranches (ao x2, infrastructure, tradfi, and one
  ao/ci-spanning), each explicitly scoped "leave to the owning tranche's own audit, not this run" per the 2026-07-30
  concurrent-sharded-worker rule. Cross-cutting cannot execute its own todos here by construction; flipping
  `assigned_vm` would dispatch writes into other tranches' files.

- **2026-08-01** — `/ag-closeout-audit cross-cutting` run (autonomous, scheduled daily run, dispatch `agt-a5c7d6`, slot
  13). Phase 0: `generate_ag_closeout_audit_candidates.py --tranche cross-cutting` (90 members, 6 covering docs, 11
  never-cited) + 1 more found via a manual `asset_group: meta`-sweep gap check. Orthogonality HARD CHECK re-run: clean
  (0 genuine dual-tag mistags — the 4 hits found were all legitimate multi-AG coordination docs). Phase 1 (`Workflow`,
  12 agents, one per candidate): 6 verdicted `exclude_cross_cutting` (this doc), 6 verdicted `orphaned_never_touched`
  (batched in `cross_cutting_satellite_ao_dispatch_batch3_2026_08_01.md`, `status: draft`). **Ledger**: 6 new parked
  findings this run, 6 entries written above (1-6) — balanced.
- **context-scout 2026-08-01**: populated/refreshed context_scope (4 entries).
- **context-scout 2026-08-03**: re-confirmed context_scope (4 entries, unchanged) -- process/audit-of-docs register, no
  code target; SKILL.md + conflict-check codex + the still-draft batch3 + linkage-gate issue remain the right reads.
- **na-eligibility-audit 2026-08-04**: KEEP-NA, valid — the 3 remaining open todos (items 2, 4, 6) are `[DOCS]` P3
  asset_group retags of docs owned by OTHER tranches (ao/infrastructure/tradfi), each explicitly scoped "leave to the
  owning tranche's own audit" per the 2026-07-30 concurrent-sharded-worker rule cited in this doc's own `related`/
  `source` — a redirect-banner case, not bounded AO-dispatchable work for this tranche.
- **context-scout 2026-08-05**: re-scouted; context_scope unchanged (4 entries), still accurate.
- **na-eligibility-audit 2026-08-07**: KEEP-NA, stale items closed — 1 item closed as done (finding 6 / todo 6, verified
  directly: target doc's `asset_group` is now `[tradfi]`, folded into
  `tradfi_satellite_ao_dispatch_batch7_2026_08_06.md`). The remaining 2 open todos (findings 2, 4) verified still
  genuinely open — both target docs' `asset_group` still reads `[cross-cutting]` today (fresh grep), unretagged. Doc
  stays `assigned_vm: NA` — both remaining todos are cross-tranche retags per the 2026-07-30 concurrent-sharded-worker
  rule, not this tranche's write.
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, valid -- reaffirms 2026-08-07 (unchanged): a
  cross-tranche parked-findings register; the 2 remaining open todos are `[DOCS] P3` `asset_group` retags of docs owned
  by OTHER tranches, explicitly scoped "leave to the owning tranche's own audit" per the 2026-07-30
  concurrent-sharded-worker rule -- structurally not this tranche's write, not a defaulted-to-NA judgment call.
