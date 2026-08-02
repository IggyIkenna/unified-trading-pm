---
doc_type: plan
title: CI satellite AO batch 3 — third AO-dispatch extraction for the ci tranche (single conflict-clear item)
summary: >-
  Third AO-dispatch batch for the `ci` topic tranche, produced by `/ag-closeout-audit ci` (autonomous mode, 2026-07-30).
  Phase 0 re-checked batch1's still-open conflict-gated Deferred items (D2-D6) and batch2's (E1-E5): none have newly
  cleared since 2026-07-29 (all remain genuinely gated — most on batch2's own `scripts/quickmerge.sh` todo not yet
  landing, since batch2 is still `status: draft`). Phase 0.3 (Orthogonality HARD CHECK) found NINE docs mistagged
  `asset_group: [cross-cutting]`/`[meta]` whose content is genuinely `ci`-tranche (forked from ci-tranche batch1's own
  F5 todo, or filed by cicd-role escalation workers responding to the live 2026-07-29/30 GitHub Actions billing-wall +
  self-hosted-runner-capacity incidents) — all nine retagged to `[ci]` this run (see each doc's frontmatter comment,
  `unified-trading-pm` commit this batch ships alongside). Of the nine, this batch extracts exactly ONE conflict-clear,
  bounded, non-live-incident item; the other eight are explicitly NOT drafted here (see rationale below) because they
  are either (a) live, actively-evolving incident docs already being handled via the AO's own CI-escalation dispatch
  system (not a static-batch-appropriate target while still hot), (b) already self-dispatched via their own
  `assigned_vm: planning`, (c) role-mismatched (needs a `[UI]`-capable slot, not `cicd` — same precedent as batch1's
  D20/D28 and batch2's E12/E13), or (d) already explicitly operator-ruled `assigned_vm: NA` (human-driven) for stated
  trading-safety-blast-radius reasons. This is a genuinely single-todo plan — per `task_template.md`'s explicit
  single-todo carve-out, no separate finalize plan is authored; the archival step is folded into this one todo's own
  "Done when".
status: complete
nature: process
asset_group: [ci]
stage: [meta]
repos:
  [
    unified-trading-pm,
    strategy-service,
    ml-service,
    market-data-processing-service,
    instruments-service,
    trading-agent-service,
    greeks-service,
    market-tick-data-service,
  ]
scope: [engineer, admin]
tags: [ci, cicd, ao-dispatch, close-out, batch-3, satellite-docs, cloud-build, dockerfile, uv]
related:
  [
    /plans/active/ci_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/active/ci_satellite_ao_dispatch_batch1_finalize_2026_07_26.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_2026_07_29.md,
    /plans/archive/2026_07/ci_satellite_ao_dispatch_batch2_finalize_2026_07_29.md,
    /plans/archive/2026_07/ci_consolidated_closeout_2026_07_25.md,
    /plans/archive/issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md,
    /plans/active/issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/08-workflows/ci-cd-flow.md,
  ]
created: "2026-07-30"
last_updated: "2026-07-31"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.8
estimate_calibrated_ai_days: 0.5
assigned_role: cicd
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit ci` run 2026-07-30 (ag_closeout_auditor scheduled worker, slot 4). Phase 0.3 Orthogonality HARD
  CHECK found this batch's sole item mistagged cross-cutting; retagged and conflict-checked against batch1/batch2's own
  todos + Deferred sections (no overlap: touches per-repo Dockerfiles, not `quickmerge.sh`/`base-service.sh`/
  `base-library.sh`, the tranche's currently-contended files).
---

# CI satellite AO batch 3

> **🟢 ARCHIVED 2026-07-31 — COMPLETE.** The single todo's underlying work (retry-with-backoff hardening + the
> fleet-wide sweep) was independently completed and verified under direct dispatch against the source issue doc
> (`strategy-service@7cac6edc`, `ml-service@99edbe8`, `market-data-processing-service@c3c3aee`,
> `instruments-service@41f1a25b`, `trading-agent-service@81c08a2`, `greeks-service@2d24469`, plus the fleet-wide grep
> verification — all cited in `issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`'s own
> `## Todos`) before this satellite plan's copy of the same todo was ever picked up — re-verified live against the
> current Dockerfiles (2026-07-31) before flipping. Successor: none (this batch's work is complete, not superseded).

> **Why this batch is so small.** `ci_satellite_ao_dispatch_batch1_2026_07_26.md` (active, ~16/30 todos done at audit
> time — others are being drained concurrently by other slots) and `ci_satellite_ao_dispatch_batch2_2026_07_29.md`
> (draft, awaiting operator approval) already comprehensively cover the tranche's stable, non-live-incident backlog —
> re-checking their Deferred sections found nothing newly conflict-cleared today. The ONLY new material this run
> surfaced came from a tag-hygiene pass (Phase 0.3's Orthogonality HARD CHECK), not from new orphaned-and-untracked work
> in the stable sense batch1/batch2 already drained.

## Why 8 of the 9 retagged docs are NOT extracted here

Full list of docs retagged `[cross-cutting]`/`[meta]` → `[ci]` this run, and disposition:

| doc                                                                                         | why retagged                                                                    | why NOT a batch3 todo                                                                                                                                                                                                                                                                                                                                                      |
| ------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `issues/repo_ci_stuck_in_sit_tristate_2026_07_29.md`                                        | forked from batch1's own F5 todo; SIT-dashboard tri-state content               | **Role-mismatch**: fix spans `deployment-api` (backend type) + `deployment-ui` (`repoCi.ts` TS consumer) as one indivisible change — needs a `[UI]`-capable slot, same as batch1 D20/D28 and batch2 E12/E13. Already carries its own `- [ ]` todo in its own doc; tag fix alone makes it visible to the ci tranche going forward.                                          |
| `issues/github_actions_billing_wall_recurrence_2026_07_29.md`                               | GH Actions fleet-wide billing-wall incident content                             | **Live incident** (~10h+ active at time of this audit) already being handled via the AO's own `ldr_qg_failure`/`cicd`-role escalation dispatch (evidenced by 10+ distinct escalation IDs/slots in its Progress Log) — folding into a static batch risks colliding with its own in-flight state; its `[OPERATOR] P0` todo is the correct, already-in-place escalation path. |
| `issues/fleet_wide_qg_self_hosted_runner_capacity_crisis_2026_07_27.md`                     | self-hosted-runner capacity incident content                                    | **Live incident**, same reasoning; sole remaining open todo is itself gated on a cross-doc dependency (the day2 sequel's own P0 item landing first).                                                                                                                                                                                                                       |
| `issues/fleet_wide_qg_capacity_crisis_continues_day2_2026_07_29.md`                         | continuation of the above incident                                              | **Live incident**, same reasoning; most-open items are operator-already-ruled or gated on the same VM-capacity resolution.                                                                                                                                                                                                                                                 |
| `issues/ldr_to_main_promote_workflows_sustained_startup_failure_2026_07_30.md`              | GH Actions ldr-to-main-promote startup_failure incident (filed literally today) | **Live incident**, root cause still being diagnosed (working theory unconfirmed); already carries its own `[OPERATOR] P0` todos.                                                                                                                                                                                                                                           |
| `issues/ldr_main_backmerge_silently_resurrects_reverted_commit_2026_07_29.md`               | LDR↔main promote/backmerge race content                                         | **Already self-dispatched** (`assigned_vm: planning`, `status: open` — it IS its own dispatch vehicle).                                                                                                                                                                                                                                                                    |
| `issues/ldr_to_main_promote_fleet_silently_skips_repo_after_promote_pr_close_2026_07_28.md` | ldr-to-main-promote-fleet.yml automation-gap content                            | **Already self-dispatched** (`assigned_vm: planning`, `status: open`).                                                                                                                                                                                                                                                                                                     |
| `pm_own_workflows_wave2_self_hosted_runner_migration_2026_07_28.md`                         | PM's own self-hosted-runner migration scoping content                           | **Already operator-ruled `assigned_vm: NA`** (main-agent interim guidance on `BLK-7593bf4c`, citing Tier B's trading-safety blast radius) — deliberately human-driven, not AO-dispatchable; re-litigating that ruling is out of this audit's scope.                                                                                                                        |

Cross-reference: `issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md` (filed by the sibling
`cross-cutting` tranche auditor, same day) independently named 5 of these 9 as `ci`-by-content and deliberately left
them un-retagged pending a scoped follow-up pass — this batch's retags implement that follow-up for the `ci`-bound
subset (its `ao`-bound examples are the `ao` tranche auditor's own concern).

## Todos

- [x] ✅ [SCRIPT] P2. **VERIFIED ALREADY DONE 2026-07-31 (slot 16, cicd craft dispatch) — no new code shipped, this
      todo's work was already completed under separate direct dispatch against the source issue doc before this
      satellite copy was picked up.** Re-verified live against the actual Dockerfiles in each of the 7 named repos:
      `strategy-service`, `ml-service`, `market-data-processing-service`, `instruments-service`,
      `trading-agent-service`, `greeks-service` all carry the retry-with-backoff wrapper (3 attempts, exponential
      15s/30s backoff) around `uv pip install --system ... --no-sources`, scoped inside the `UV_EXTRA_INDEX_URL`
      BuildKit-secret layer — shipped `strategy-service@7cac6edc`, `ml-service@99edbe8`,
      `market-data-processing-service@c3c3aee`, `instruments-service@41f1a25b`, `trading-agent-service@81c08a2`,
      `greeks-service@2d24469` (each verified via a real Cloud Build trigger reaching SUCCESS per the issue doc's own P2
      todo, a stronger check than the local-docker-build verification originally specced here).
      `market-tick-data-service` correctly has NO such wrapper — confirmed not exposed (installs UTL/UAC from vendored
      `.deps/` local paths with `--no-deps`, never resolves either package from the live GAR index at build time). The
      fleet-wide sweep (part b) was separately completed and verified 2026-07-30 (slot 8, cicd craft dispatch): 23
      Dockerfiles across 21 repos grepped for the `COPY pip.conf` + `uv pip install ... --no-sources` pattern without
      `UV_EXTRA_INDEX_URL`/`UV_INDEX`; zero additional repos exposed beyond the 8 already fixed (the 6 above plus
      `alerting-service`, `fund-administration-service`). Full evidence + per-commit citations:
      `issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`'s own `## Todos` (both source P2
      items already `[x]`). **Harden the `uv pip install --system ... --no-sources` step against the publish-ordering
      race across the 7 affected repos, then proactively sweep the fleet for the same latent gap.** Two
      internally-sequential pieces from the same source doc, combined into one todo (the sweep's own output determines
      the final repo list for the hardening pattern, so fanning them out would race): (a) add a short retry-with-backoff
      (~3 attempts, exponential, ~30-60s total budget) around the `uv pip install --system -e . --no-sources` step in
      each of strategy-service, ml-service, market-data-processing-service, instruments-service, trading-agent-service,
      greeks-service, market-tick-data-service's Dockerfiles (confirmed NOT currently templated the way
      `quality-gates-v2.yml` is — this is 7 individual per-repo edits, each needing its own local Docker build
      verification before shipping); (b) fleet-wide grep for the SAME latent gap pattern already fixed in
      `instruments-service@2941646c` (2026-07-29): any repo's Dockerfile with `COPY pip.conf` + a subsequent
      `uv pip install ... --no-sources` WITHOUT a `UV_EXTRA_INDEX_URL`/`UV_INDEX` env var is silently relying on its
      pinned base image already satisfying every dependency floor, and will build-fail identically the next time ANY
      private-registry dependency gets floor-bumped past what the base image bundles — apply the retry-with-backoff from
      (a) to every additional repo this sweep finds, beyond the 7 already named. **Explicitly excludes** the doc's own
      nested P3 sub-item (whether to promote the retry pattern to a shared Dockerfile snippet/base-image convention once
      proven) — that is a follow-on convention decision, not required for this todo's own done-when. **Done when**: all
      7 named repos' Dockerfiles carry the retry-with-backoff, each verified via a local Docker build, the fleet-wide
      sweep's repo list (including any beyond the 7) is recorded in the source doc, and every touched repo's
      `quality-gates.sh` is green. **Also fold in the archival step** (this is a genuinely single-todo plan per
      `task_template.md`'s carve-out, so no separate finalize plan exists): once done, (i) flip this todo's source doc's
      own two open checkboxes (`issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`) to `[x]`
      citing this commit, (ii) if that leaves the source doc with zero open todos, run the standard 6-step archival
      ritual on it, and (iii) archive THIS plan itself via the same ritual (its own single todo done + no lock). Source:
      `issues/cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md` ([SCRIPT] P2 ×2).

## Deferred

Carried forward from batch1/batch2's re-check this round (iterative-drain step 1) — nothing newly cleared:

| id  | Item                                                                                                                 | Still gated because                                                                                                                                                                    |
| --- | -------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| F1  | batch1 D4 / batch2 E4 — delete redundant `pre-push-strict-quickmerge.sh` + repoint referrers                         | `scripts/quickmerge.sh` still held by batch2's own todo1 (sentinel-binding fix), which has not landed yet (batch2 itself is still `status: draft`) — re-check again once batch2 ships. |
| F2  | batch1 D8 / batch2 E3 — STAGE 1.6 dormancy-aware dep gate in `quickmerge.sh`                                         | Same file contention as F1.                                                                                                                                                            |
| F3  | batch1 D2/D6, batch2 E9/E10 — `digest-drift-sweep` non-convergence + 4 vacuous crons                                 | Still needs a per-item operator ruling; unchanged since 2026-07-29.                                                                                                                    |
| F4  | batch2 E6/E7/E8 (quickmerge.sh Option-B removal / MTDS `DEPLOYMENT_ENV` leak / breaking-change-differ fan-out scope) | Still operator-gated; unchanged since 2026-07-29.                                                                                                                                      |

No new conflict-gated items this round (this batch's own todo touches only per-repo Dockerfiles, not a file any other
active/draft ci-tranche plan claims).

## Escalated to the operator (parked, not guessed)

None new this round — the 3 questions batch2 already escalated (E6/E8/E14) remain open and unanswered as of this audit;
not re-escalating duplicates.

## Codex SSOTs (read before executing the todo)

- `/codex/08-workflows/ci-cd-flow.md` — pipeline / quickmerge / gate set
- `/codex/06-coding-standards/quality-gates.md` — how gates run; never `pytest` directly
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — the 6-step archival ritual this todo's
  done-when folds in
- `plans/active/task_template.md` §4 — the single-todo finalize-plan carve-out this doc relies on

## Progress Log

- **2026-07-30** — Drafted by `/ag-closeout-audit ci` (autonomous mode, `ag_closeout_auditor` scheduled worker, slot 4).
  Phase 0: re-derived the covering-plan set (batch1 active + batch1_finalize draft-gated + batch2 draft +
  batch2_finalize draft-gated — `ci_consolidated_closeout_2026_07_25.md` remains archived, its own scope closed
  2026-07-28); confirmed `generate_ag_closeout_audit_candidates.py`'s ao/ci/infra membership bug (reported 2026-07-29)
  is FIXED as of today (`unified-trading-pm@e88c41727`) and used it directly rather than a hand-rolled frontmatter
  sweep. Re-checked batch1's D2-D6 and batch2's E1-E5 conflict-gated Deferred items: none newly cleared (all still gated
  on batch2's own `quickmerge.sh` todo not yet landing, or still-open operator rulings). Phase 0.3 Orthogonality HARD
  CHECK (extended to the bare-`[cross-cutting]`/`[meta]`-but-single-tranche-content sub-bug, per SKILL.md's documented
  "second/third pattern") found 9 docs carrying real `ci`-tranche content mistagged elsewhere — traced independently via
  (a) batch1's own citation graph (`repo_ci_stuck_in_sit_tristate`, forked from its F5 todo) and (b) cross-referencing
  the sibling `cross-cutting` tranche auditor's own same-day finding
  (`issues/ag_closeout_linkage_gate_blind_to_four_tranches_2026_07_30.md`, which named 5 of these 9 as `ci`-bound
  examples but deliberately left them un-retagged pending a scoped follow-up — see that doc's Progress Log for the
  cross-reference note added this session). All 9 retagged `[ci]`; `check_frontmatter_schema.py` clean on all 9;
  `check_ag_closeout_linkage.py` still reports 0 orphans post-retag, though per the same sibling-filed issue this gate
  is now KNOWN to be structurally blind to the `ci` tranche (hardcoded `REAL_AGS` excludes it) — that "0" is not being
  relied on as evidence here, only the direct `generate_ag_closeout_audit_candidates.py` membership sweep
  (frontmatter-based, unaffected by the linkage gate's separate bug) is. Of the 9, 8 are NOT extracted into this batch
  (see table above: 4 live-incident/actively-escalation-handled, 2 already self-dispatched, 1 role-mismatched, 1 already
  operator-ruled-NA) — only `cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md`'s 2 remaining
  bounded todos (root cause already found + mostly fixed, genuinely stable/non-live) were conflict-clear and
  AO-eligible, combined into this batch's single todo. Nothing shipped, nothing flipped to `active`.

- **2026-07-30 (rulings-closeout pass, separate session)** — reviewed this plan as part of a workspace-wide sweep to
  close out recorded operator rulings implying unshipped work. **Finding: this plan's single todo is NOT backed by an
  explicit operator ruling** (no "RULED"/"operator ruling" citation anywhere in this doc or its source issue for the
  retry-with-backoff/fleet-sweep item) — it is this skill's own audit-derived triage of two still-open `[SCRIPT] P2`
  items in `cloud_build_unified_api_contracts_publish_ordering_race_2026_07_29.md` (re-confirmed both genuinely still
  `[ ]` in that source doc: the retry-with-backoff hardening and the fleet-wide auth-gap sweep). Per this sweep's own
  scope (execute already-made rulings, do not invent new authorization for audit-triaged-but-undecided work), left
  unexecuted — this plan stays `status: draft`, flipping it is still the operator's call. **Separately confirmed this
  session could not have safely executed it anyway**: the todo's own "done when" requires each of the 7 repos'
  Dockerfile edits to be "verified via a local Docker build" — `docker ps` in this session's environment returns
  `permission denied while trying to connect to the docker API` (no working daemon access), so there is no way to meet
  that verification bar here even if the todo were authorized. Nothing shipped, nothing flipped to `active`.
