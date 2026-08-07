---
doc_type: issue
title: plan_reconciler findings — 2026-08-07 (ci tranche)
summary: >-
  Daily sharded plan_reconciler run for the ci tranche (asset_group: ci) — fan-out DETECT + adversarial VERIFY +
  conservative APPLY. Run journal: flips verified / contradictions / doc-drift / hygiene fixes / filed / archive
  candidates / refuted / coverage. Any open operator questions are tracked here as `- [ ]` todos per the plan_reconciler
  HARD LIMITS (STEP 6).
created: 2026-08-07
author: plan_reconciler
source: agt-6eb8c5
status: open
nature: record
asset_group: [ci]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [plan_reconciler, reconciliation, plan-hygiene, ci, run-findings]
parent_epic: agent_operating_framework_master
priority: P2
assigned_vm: NA
resolved_by:
locked_by:
related: []
---

# plan_reconciler run — 2026-08-07 (ci tranche)

> Sharded run (`tranche: ci`). Review branch `plan_reconciler/agt-6eb8c5`, PR-gated. 18 grace docs (newest commit <12h)
> were read-only. Nothing in this run rewrites codex.

## Flips verified

<!-- append per confirmed missed-flip, format: `<plan>:<todo line> — evidence <sha/artifact> — verified by plan_reconciler agt-6eb8c5 2026-08-07` -->

### Hunter F (missed-flip) — verification verdicts

- `plans/active/ui_build_warm_cache_2026_06_17.md:98` — **FLIPPED (half-done)**: pnpm global-store migration sub-parts
  (1)+(2) HARD-verified (shas reachable on origin/live-defi-rollout: `unified-trading-system-ui@474bba76`,
  `deployment-ui@de5b7af`, `unified-trading-pm@32ea69f5b`); sub-part (3) hardlinked-store verification **DEFERRED** —
  per plan_reconciler half-done rule. — verified by plan_reconciler agt-6eb8c5 2026-08-07
- `plans/active/ci_pipeline_speed_and_cost_redesign_2026_08_05.md:260` — **kept OPEN (verified partial)**: mechanism
  shipped + canaried (`unified-trading-pm@b656cb87b`/`23f1ad262`/`91ebc6584` all reachable) but the todo's own text
  states the intended I/O reduction is NOT yet delivered and rollout is gated ("Do NOT roll out to additional pools
  until this is understood"). Flipping would misstate done-ness; the author may re-scope into mechanism-shipped /
  confirmation-open.
- `plans/active/issues/qg_sentinel_environment_blind_2026_07_23.md:166` — **kept OPEN**: 1 of 4 repos shipped; box
  explicitly stays open.
- `plans/active/capability_wizard_client_lite_and_ci_regen_followup_2026_07_24.md:82` — **kept OPEN**: 1 of 3 outputs
  shipped (`unified-api-contracts@1bc2f07` reachable), 2 still blocked on-host.
- `plans/active/tradfi_forexfactory_econ_calendar_consensus_capture_2026_07_30.md:190` — **kept OPEN**: fixture sub-part
  verified live on disk (`features-service/tests/fixtures/forexfactory/` — 7 files incl.
  `json_feed_thisweek_sample_2026_07_30.json`); tests themselves not claimed done.
- `plans/active/ci_vm_exposure_remediation_2026_08_06.md:107` — **NOT a candidate**: own text says "Not shipped".

## Contradictions

<!-- confirmed plan-vs-plan / plan-vs-epic / status contradictions -->

## Doc-drift

<!-- confirmed plan↔codex drift (FLAG only — never rewrite codex) -->

### In-session codex-alignment audit — verified findings

- **D1 (P1, plan↔codex)** `plans/active/shared_ci_workflow_repo_extraction_2026_08_06.md:306-313` (todo 7f) treats the
  human-planning VM as merely stopped: "Human-planning VM (`i-0dd9812a96cdda5dc`) — could NOT be provisioned, not
  currently running. … Whoever next starts that VM should run the identical runbook" — vs
  `/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md:109`: "The separate interactive-only
  `human-planning` VM (id `i-0dd9812a96cdda5dc`) was **terminated 2026-08-03** … do not reference it as a live host; any
  future operator-interactive box would be a fresh instance, not this one" (+
  `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md:58-60` "it was terminated 2026-08-03 … do not
  carry forward any 'either VM' / 'both VMs' framing"). The plan is dated 2026-08-06 — 3 days AFTER the codex
  termination record — yet its open `[OPERATOR]` todo instructs a future operator to start the terminated instance.
  Annotate/close 7f (the runbook is moot; the observation in its own text — "Not present in `aws ec2 describe-instances`
  … at all" — is the termination, misread as stopped).
- **D2 (P2, SSOT staleness, documented-live-not-fixed)**
  `plans/active/ci_runner_fleet_split_and_vm_rightsizing_2026_08_03.md:143-144`: "the codex doc's documented
  `unified-trading-sa` mechanism didn't match the LIVE AO box's actual identity, `github-actions-deploy` — codex drift,
  not touched here" — vs `/codex/05-infrastructure/orchestrator-cloud-identity-self-service.md:50-53`: "GCP:
  `unified-trading-sa@central-element-323112.iam.gserviceaccount.com` — the orchestrator's real GCP identity … any
  tmux-spawned worker shell already authenticates as this SA". The doc names `github-actions-deploy` only as an example
  of a DIFFERENT identity (L66). Reconciler never rewrites codex → operator action: reconcile the SSOT's identity claim
  with the live box (the plan explicitly left it unfixed).
- **D3 (P2, SSOT "closes" claim vs issue still open)** `/codex/08-workflows/ci-cd-flow.md:591`: "(closes
  `breaking_change_differ_blind_to_registry_data_dicts_2026_07_09.md`, fixed 2026-07-31)" — vs the issue file's
  `status: open` (deliberate: sole open `[DESIGN] P2` parked as batch2 Deferred E8; the doc's own audit says "Still
  genuinely open — not closing", `breaking_change…2026_07_09.md:194-200`). The registry-data-dict fix itself is shipped
  - verified (`5607023a2`/`e34afc1d`/`67db4da`); only the "closes <file>" wording overreaches the file's live status.
    Align the codex wording or flip the issue's remaining item to a tracked deferral.
- **Verified non-drift (recorded, no action)**: ci-cd-flow.md's five high-traffic claims are internally consistent
  (LDR→main gate set exactly three, L61-102; quickmerge two-pass + `Quickmerge:` trailer + strict-quickmerge pre-push
  hook, L206-224/363-510/799-817; `[skip ci]` ban on v2-gated promotion-PR heads, L1206-1223; ci_status Firestore-SSOT
  with RETIRED reconciler, L655-665; template two-half rollout, L746-759/1160-1164). Governor plan ↔ quality-gates.md
  heavy-tier correction (`qg_host_adaptive_resource_governor` ↔ `quality-gates.md:3289-3292`) consistent. Host-move
  claim ("PM is now just another caller", ci-cd-flow.md L1148-1158) matches shipped state (extraction todo 16 done,
  `unified-trading-ci@f20c59f`); the extraction plan's remaining open todos (3/7c/15/20) are orthogonal
  stretch/manual/cleanup items no codex claim covers. `quality_gates_v2_concurrency` issue ↔ ci-cd-flow 🟡 CORRECTED
  2026-08-02 banner consistent (PM promote PR = frozen per-SHA head since `40386f0274`, 2026-07-18).

## Hygiene fixes

<!-- mechanical fixes applied -->

## Filed

<!-- durable - [ ] todos for routed items + _agent_pings pointers -->

## Archive candidates (operator review)

<!-- verified-done unlocked non-grace candidates; archived: true|false -->

## Refuted (dropped by verify)

<!-- candidates that failed the adversarial pass -->

## Coverage (hunters / batches / docs)

<!-- hunter tally -->

## Plans not reached

<!-- docs the run could not reach -->

### Hunter B (ci satellite dispatches) — verification verdicts

- **M1** `issues/deployment_flow_doc_stale_pre_ldr_direct_mvp_2026_07_30.md:94` — flip candidate; issue's own text
  directs flip-on-ship; batch4 copy shipped `unified-trading-pm@445f02081` (2026-08-06). Verify sha → FLIP.
- **C1** batch1 D1 row pointer "finalize plan's todo 2" wrong (finalize todo 1 is the registration commit) — verify →
  fix.
- **C2** batch1 banner still "⚠️ STATUS: `draft`" vs frontmatter `status: active` (+ 42/43 todos done); sibling finalize
  corrected its own banner 08-02 — verify → align banner.
- **C3** batch4 D4-4 / batch4-finalize todo 2 premise ("batch1's still-open todo") false since
  `unified-trading-pm@409c35437` (2026-08-03); batch4 main is GRACE (read-only) — annotate finalize side if writable.
- **C4** batch1 D27 blocker text stale (AWS credits) vs batch4 D4-6 (S3 backend stood up 2026-07-30) — verify vs issue
  doc → fix.
- **C5** batch5 todo 4 premise false (batch1 confirmed the workflow step does NOT fire; `ci_reconcile.py` literal match
  is the source, `agent-orchestrator@1f2fcc648`) — batch5 GRACE; report-only (todo self-guards via verify-first step).
- **C6** deployment_flow_doc_stale Progress Log "batch4 still draft" markers — batch4 active since 2026-08-06 — fix in
  same doc as M1.
- **C7** deployment_flow_doc_stale calls `cicd_mvp_ldr_to_main_pipeline_2026_06_30.md` "status: active" — archived —
  fix.
- **C8** batch1 D8 trailing "queued for batch 2" vs D3(2) DONE (`unified-trading-pm@b3abf1bd5`) — fix.
- **C9** batch1 `last_updated: "2026-07-26"` vs body entries to 08-03 — fix.
- **M2** batch1-finalize todo 2 — correctly self-guarded ("do not mark parent `[x]` until 29 reconciled") — no flip.

### Hunter E (misc epics: monitoring_control_plane_master / forexfactory / capability_wizard) — verification verdicts

- **F1 (P1, plan↔plan)** ORCHESTRATOR_API_TOKEN: master `:206-211` + deferred row `:636` say absent/blocked; archived
  sub-plan `ci_dashboard_deployment_ui_2026_06_10.md:208-210` records token stored in GCP+AWS SM + live-verified
  `available=true` (2026-06-11), JWT exp 2026-07-01. Master never reconciled → annotate master with sub-plan record +
  expiry + re-probe; route the re-probe as a durable todo.
- **F2 (P2)** master charter summary `:142-143` "remaining: G1 + N2 + the 2 creds" — all resolved in-doc → align.
- **F3 (P2)** master deferred row `:637` claims open `- [ ]` P1 in ci_dashboard sub-plan; sub-plan `status: complete`,
  parity shipped (`deployment-api@15fc1e4` PR #46) → align row.
- **F4 (P2)** `fleet_git_health_orchestrator` sub-plan `status: superseded` w/o `superseded_by`/banner; its lone open
  VERIFY todo has no live owner; master `:221-224` says "tracked in-sub-plan" → annotate master + ROUTE (archived doc
  not editable by reconciler).
- **F5 (P2)** forexfactory "Why this exists" `:72-75` ("features-calendar-service … does not exist") vs corrected todo 3
  (`features_service/calendar/` IS it) → annotate prose.
- **F6 (P2)** `last_updated` stale: monitoring (07-24 vs body 08-06), capability_wizard (07-24 vs 08-06) → bump.
- **F7 (P2)** stale refs: monitoring `related:` lists 4 archived docs under `plans/active/` paths +
  `plan_line_cap_remediation` cited as active but archived (monitoring :21/:522/:525, capability :23/:42/:138) → fix
  paths.
- **F8 (P3)** monitoring `assigned_vm: NA` + `execution_scope: orchestrator-agent` mix — cosmetic (regen maps NA → no
  VM, verified by hunter) — REPORT only.

### Hunter H (mechanical adjudication) — verdicts

- 7 ci AG-closeout orphans: **6 PARSER-ARTIFACTS** (checker `closeout_family_for()` globs only `ci_consolidated_*`; the
  `ci_satellite_ao_dispatch_batch*` docs are the real family, invisible to the checker) → no doc edits; FILE the checker
  gap as a durable todo. **1 REAL-ORPHAN**: `quality_gates_v2_concurrency_and_bookkeeping_job_cost` — genuinely
  unconnected → add `related:` family link.
- Reference-path FORMAT/DANGLING: zero ci-tagged docs flagged — tranche clean.

### Hunter D (gates/checks issues) — verification verdicts

- **C1 (P2)** quality_gates_v2 summary `:16` "not verified further here" vs body DONE 08-02 → align summary.
- **C2 (P2)** `DEFERRED-until-2026-08-05:` prefix still on the P3 re-measure todo, 2 days past the doc's own
  reactivation date; the doc's own mechanism (`_brief_is_deferred`) permanently excludes it from dispatch → drop the
  prefix per the doc's own reactivation instruction.
- **C3 (P2)** quality_gates_v2 context_scope/evidence point at `.github/workflows/python-quality-gates-v2.yml`, deleted
  by `b62a209dc` (08-06; live source = unified-trading-ci) → annotate.
- **C4 (P2)** pm_bats cites deleted files; open todo 1 targets non-existent `setup-python-tools/action.yml` → annotate
  with live locations (`scripts/self-hosted-runners/hosted-baseline/python-quality-gates-v2.yml`).
- **C5 (P2)** pm_bats audit verdicts claim batch4 "still draft" (batch4 active 08-06) → correct.
- **C6 (P2)** uac_value_only `locked_since: 2026-05-21` predates `created: 2026-07-20` → fix bogus lock date.
- **C7 (P3)** `last_updated` stale in digest_drift/breaking_change_differ/deployment_api_mtds_meta/pm_bats → bump.
- **C8 (P3)** pm_bats "6 .bats files" vs 13 on disk → annotate.
- **C9 (P2)** quality_gates_v2 flipped INFRA todo cites placeholder `@<shipped in this commit>` → recover real sha or
  annotate.
- **M1** uac_value_only:224 partial (struck clause done w/ shas; design clause open by design) → keep open,
  self-documented.

### Hunter A (CI/CD pipeline shape) — verdicts

- **A1 (P1)** exposure `:59-61` "all 25 pools" stale (8 pools since 08-05; `self-hosted-qg-repos.txt` = 8 entries,
  verified) → annotated.
- **A2 (P1)** runner-fleet final-state disagreement (revert doc 8-pool list vs speed doc post-cut PM6/AO2) — same-day
  claims, order-unverifiable from docs → ROUTED for live `systemctl` verification on `i-042a6332509482556`.
- **A3 (P1)** speed doc fast-tier "DO NOT BUILD" framing predates the 08-03 operator approval + shipped Phase 2
  (`unified-trading-pm@1452d5da1` reachable) → annotated.
- **A4 (P1)** governor `:382-383` "SAME host as glue-runner pools" premise dead since 08-05 migration → annotated.
- **A5 (P2)** speed doc UTL re-add superseded same-day by the revert (UTL absent from surviving-8 list + SSOT file) →
  annotated.
- **A6 (P2)** PM-headroom rationale vs open todo 24 (PM→ubuntu-latest revert) — opposing directions, both
  self-consistent at their moment → REPORT only.
- **A7 (P2)** infrastructure_master epic index drift (4 missing CI plans, archived-as-active, deprecated
  `vm-cross- cutting`) → REPORT only (epic regeneration owned elsewhere; hand-editing would be overwritten).
- **A8 (P2)** governor `:279` checked todo carried literal `@<PENDING-SHA>` → replaced with the real
  `unified-trading-pm@a6b5e24a5` (verified reachable).

### Hunter C (quickmerge/QG/env issues) — verdicts

- **F1 (P0)** MTDS env-leak cluster: mechanism RESOLVED under `mtds_flaky_is_test_run_pollution_2026_07_25.md`
  (resolved_by `market-tick-data-service@1dbdbb90` reachable; conftest scrub verified live at HEAD) while 3 open docs
  asserted "genuinely open" → flipped the root-cause todos in `mtds_deployment_env_monkeypatch_leak:335` +
  `mtds_deployment_env_race:146` with evidence annotations; closed qg_sentinel item 3 (all 4 components resolved);
  annotated the E7 hold.
- **F2 (P2)** qg_sentinel summary over-claims (deterministic/three repos) vs body corrections → summary updated.
- **F3 (P2)** silent_failures P0 "re-do the || true fix" premise false — redo shipped same-day `41e2b47bb` (verified
  in-tree, loud-FATAL block + later hardening e170e6ccf/a4eb9a288) → flipped half-done + DEFERRED the `--selfcheck`
  canary.
- **F4 (P2)** orchestrator_gcloud title "third occurrence" + last_updated stale (5 occurrences, 2nd SA in body) → title
  annotated + last_updated bumped.
- **F5 (P3)** review_role_boot title "live slot needs attention" vs slot-1 clean in body → title annotated.
- **F6 (P3)** silent_failures [x] P1 closed while enforcement unwired — self-acknowledged + tracked in batch1_finalize →
  REPORT only.
- **M1 (P2)** uv_bootstrap:83 fix shipped `unified-trading-pm@eff7413da` (reachable) → FLIPPED.
- **M2 (P2)** provenance_gate:162 hook deletion shipped `unified-trading-pm@b02ba28c7` (reachable) → FLIPPED.
- **M3** qg_sentinel item 3 watch-item — closed via F1 verification (see F1).

## Applied fixes summary (checkpointed on plan_reconciler/agt-6eb8c5)

- flips (5): ui_build_warm_cache:98 (half-done+DEFERRED), mtds_monkeypatch_leak:335, mtds_race:146, qg_sentinel item 3,
  silent_failures:108 (half-done+DEFERRED), uv_bootstrap:83, provenance_gate:162, deployment_flow:94 — 8 total.
- annotations/banner/pointer/status fixes: batch1 banner (C2) + D1 (C1) + D8 (C8) + D27 (C4) + last_updated (C9);
  batch4_finalize D4-4 (C3); deployment_flow cicd_mvp archived (C7) + holding-condition marker (C6); quality_gates_v2
  summary (C1) + reactivation prefix (C2) + context_scope note (C3) + real sha (C9) + related-family link (REAL-orphan);
  pm_bats (C4/C5/C7/C8); uac_value_only locked_since (C6); monitoring master (F1 token block + F2 summary + F3 parity
  row + F4 fleet-git note + F6 last_updated + F7 related paths); capability_wizard (F6+F7); forexfactory F5; qg_sentinel
  summary (F2); digest_drift/breaking_change_differ/deployment_api_mtds_meta last_updated (C7); orchestrator_gcloud
  (F4); review_role_boot (F5); exposure A1; speed A3+A5; governor A4+A8.

## Filed (durable - [ ] todos — routed items)

- [ ] [OPERATOR] P2. Re-probe SM (GCP + AWS) for `ORCHESTRATOR_API_TOKEN` — the 2026-06-11 JWT expired 2026-07-01;
      re-mint + add a new secret version both clouds if absent/expired (source:
      `monitoring_control_plane_master_2026_06_10.md` F1, reconciled 2026-08-07 by plan_reconciler agt-6eb8c5; the
      fleet-git proxy's live-verify gate depends on it).
- [ ] [INFRA] P2. Re-home the orphaned open VERIFY todo of `fleet_git_health_orchestrator_2026_06_10.md` (archived,
      `status: superseded`, NO `superseded_by`/banner) — its live cross-host fleet-cycle VERIFY has no live owner;
      decide successor home or close-with-citation (source: monitoring master F4, plan_reconciler agt-6eb8c5).
- [ ] [INFRA] P2. Live `systemctl list-units 'github-glue-runner*'` count on `i-042a6332509482556` to settle A2:
      `self_hosted_runner_public_repo_revert_2026_08_05.md:293` (8 pools, ao ×4/PM ×8) vs
      `ci_pipeline_speed_and_cost_redesign_2026_08_05.md:196` (post-cut PM 5→3 glue / AO 2→1 glue) — same-day
      final-state claims; align the stale doc once measured (SSM `SendCommand` denied for `ikenna-worker` on
      2026-08-07).
- [ ] [SCRIPT] P2. Extend `check_ag_closeout_linkage.py`'s `closeout_family_for()` glob to include
      `ci_satellite_ao_dispatch_batch*` docs (the ci tranche's real dispatch family) — 6 of 7 flagged ci orphans are
      parser artifacts of this gap; the ratchet (77 vs baseline 69) is inflated corpus-wide (source: plan_reconciler
      agt-6eb8c5 mechanical adjudication).
- [ ] [REVIEW] P3. `infrastructure_master` epic index drift (A7): `related_plans` missing 4 CI batch plans
      (`ci_pipeline_speed_and_cost_redesign`, `self_hosted_runner_public_repo_revert`,
      `ci_runner_fleet_split_and_vm_rightsizing`, `ci_vm_exposure_remediation`), lists `mtds_retry_safe_default_audit`
      as active (archived, complete), `assigned_vm: vm-cross-cutting` (deprecated model) — regenerate/refresh epic.
- [ ] [REVIEW] P3. A6 coordination drift: `ci_pipeline_speed_and_cost_redesign_2026_08_05.md:196` PM-headroom rationale
      (5→3 glue for self-hosted load) vs `self_hosted_runner_public_repo_revert` todo 24 (revert PM workflows to
      ubuntu-latest post-public-flip) — re-evaluate the 3-glue cut once todo 24 executes.
- [ ] [CI] P3. `ci_pipeline_speed_and_cost_redesign_2026_08_05.md:260` (git-object cache warm): mechanism shipped +
      canaried (`fast-checkout.sh`, PM@b656cb87b/23f1ad262/91ebc6584) but I/O reduction NOT yet confirmed — re-scope
      suggestion: split into mechanism-shipped / speedup-confirmation-open (kept open by plan_reconciler agt-6eb8c5).
- [ ] [CI] P3. `ci_satellite_ao_dispatch_batch5_2026_08_02.md` todo 4 premise (Record-CI-status dispatches FAILING on
      0-job kills) falsified by batch1's 2026-08-03 finding (`ci_reconcile.py` literal-match is the source;
      `agent-orchestrator@1f2fcc648`) — batch5 was grace at run time (2026-08-07); correct the premise when next edited.

## Coverage (hunters / batches / docs)

- 8 hunters (A: CI/CD shape 7 docs, B: satellite dispatches 7 docs, C: quickmerge/QG/env 9 docs, D: gates/checks 6 docs,
  E: misc epics 3 docs, F: missed-flip 32 docs, G: codex-alignment (in-session audit — D1/D2/D3 + non-drift list in
  `## Doc-drift` above), H: mechanical 7 orphan docs + ref-path).
- Working set: 31 non-grace ci docs read in full by a hunter; 18 grace docs read-only context; 0 unreached.
- Verified: 8 flips applied, ~40 annotations/banner/status fixes, 4 parser-artifact adjudications (no doc edits), 1
  REAL-orphan linkage fix, 7 routed-filed todos, 0 refuted (all hunter candidates either applied or routed).
