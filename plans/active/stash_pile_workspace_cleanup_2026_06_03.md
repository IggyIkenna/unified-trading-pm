---
doc_type: plan
title: Workspace-wide git stash pile audit + cleanup — per-host runbook
summary:
  Runbook for auditing and clearing git stash piles across all workspace repos on any host, with archive-first
  conservative tooling.
status: active
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [agent-orchestrator, alerting-service, client-reporting-api, deployment-api, execution-service, features-service]
scope: [engineer, admin]
tags: [git, stash, workspace, cleanup, runbook, audit]
related: []
created: 2026-06-03
parent_epic: infrastructure_master
assigned_vm: NA
execution_scope: orchestrator-agent
priority: P3
estimate_class: infra
estimate_baseline_ai_days: 1.5
estimate_calibrated_ai_days: 1.2
last_updated: 2026-06-27
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on:
source:
  [
    plans/active/issues/shared_stash_pile_archive_cleanup_2026_06_01.md,
    "git stash list across all repos on the planning host (59 stashes / 16 repos, 2026-06-03)",
  ]
assigned_role: infra
effort: medium
drift_direction: advance-code
context_scope:
  [
    /codex/05-infrastructure/per-tab-worktrees.md,
    scripts/dev/audit-stash-pile.sh,
    /plans/archive/2026_07/infra_satellite_ao_dispatch_batch1_2026_07_26.md,
    /plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md,
    /codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md,
  ]
---

# Workspace-wide git stash pile — audit + cleanup (per-host runbook)

## Why this plan

The 2026-06-01 cleanup (`shared_stash_pile_archive_cleanup_2026_06_01.md`) archived + cleared a **91-deep** stash pile
in `unified-trading-pm` on one host. Two days later that same repo's pile is **back to 31**, and a host-wide scan shows
**59 stashes across 16 repos on the planning host alone** — so this is (a) workspace-wide, not PM-only, and (b)
continuous, not one-shot. We need a **reusable, archive-first, conservative tool** that any host owner runs locally,
plus a fan-out so every host (VMs + operator laptops) gets swept once.

### Mental model — the visibility boundary is the HOST, not the person

`git stash` writes to `refs/stash` and is **never pushed**. Git worktrees on one host share a single common `.git`, so
all of a host's slot worktrees see the same `refs/stash` per repo. **You cannot reach a teammate's stashes from your
machine.** Therefore the unit of work is **(host × repo)**, and the plan fans out **one todo per host**; each host owner
runs the identical script locally.

### Snapshot — planning host, 2026-06-03 (grounds the plan; not authoritative for other hosts)

| Repo                                                                                                                     | Stashes |     | Repo                           | Stashes |
| ------------------------------------------------------------------------------------------------------------------------ | ------- | --- | ------------------------------ | ------- |
| unified-trading-pm                                                                                                       | 31      |     | features-service               | 2       |
| execution-service                                                                                                        | 5       |     | client-reporting-api           | 2       |
| instruments-service                                                                                                      | 3       |     | deployment-api                 | 2       |
| alerting-service                                                                                                         | 2       |     | market-data-processing-service | 2       |
| trading-agent-service                                                                                                    | 2       |     | unified-trading-system-ui      | 2       |
| agent-orchestrator / ibkr-gateway-infra / ml-service / strategy-service / system-integration-tests / unified-trading-api | 1 each  |     |                                |         |

**TOTAL: 59 / 16 repos.** Other hosts (10 epic VMs + orchestrator VM + Ikenna laptop + Harsh laptop) are unknown until
each runs the audit.

## Safety spine (non-negotiable — inherited from the 2026-06-01 doc)

1. **Archive before touching anything** — the proven 3-way archive: gc-proof refs `refs/stash-archive/*`, a portable
   `.bundle`, and a `manifest.txt` (index → sha → label). Per repo, per host.
2. **Dry-run by default** — the script prints classifications and drops nothing unless `--apply` is passed. Smoke-test
   the classifier on one repo before sweeping the host (per smoke-test-before-scale).
3. **Conservative auto-drop only** — auto-drop is limited to the three provably-safe classes below. **All genuine WIP is
   surfaced to its owner**, never auto-dropped or auto-applied (per no-blind-edits / no-unconditional-stash-pop).
4. **Confirmation window before purge** — archives stay ~1 week after the sweep; purge only if nobody asked to restore.

## Triage taxonomy (the classifier)

Per stash, compute: index, sha, **branch-of-origin** (parsed from `WIP on <branch>` / `On <branch>`), **age** (stash
commit date), file count, `.py` count, and a class:

| Class                                | Mechanical test                                                                                                                                                | Action                                                                                                                         |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| **empty**                            | `git stash show --stat <ref>` lists 0 files                                                                                                                    | **auto-drop**                                                                                                                  |
| **redundant**                        | stash's tree diffed against the repo base (`origin/live-defi-rollout`, or `origin/main` for agent-orchestrator) has **no net change** — content already merged | **auto-drop**                                                                                                                  |
| **foreign-park / autostash residue** | label matches `foreign-*` / autostash pattern **AND** tree is already an ancestor of base (no unique content)                                                  | **auto-drop**                                                                                                                  |
| **genuine-WIP**                      | net diff vs base exists and is not attributable to an empty/redundant/park class                                                                               | **surface in report → owner confirms** (drop, or inherit-and-commit onto its own `tab/<op>/<N>` branch — see STALE note below) |

> **Conservative scope chosen 2026-06-03:** even genuine WIP from an apparently-dead local session is **surfaced, not
> auto-inherited**. The owner (or operator) decides drop-vs-inherit. The script never auto-commits another slot's WIP.

> **[doc-reconciliation 2026-07-12, finding 72, §A2 B-queue ruling] STALE BRANCH MODEL** (was: "inherit-and-commit onto
> its own `tab/<op>/<N>` branch" as a live target above and at Phase 4 below): `cursor-configs/CLAUDE.md` states the
> `tab/<op>/N` model is **RETIRED** — "any such instruction is STALE" (Multi-agent safety § per-slot worktrees). Current
> model (Path-B, per `/codex/05-infrastructure/per-tab-worktrees.md`): each slot is a `git clone --reference` with its
> own `.git`, checked out directly on `live-defi-rollout` — there is no per-tab branch to inherit onto. Genuine-WIP
> inheritance today means committing directly onto the slot's own LDR checkout (liveness-gated per the HARD RULE: dead
> claim → inherit + commit; live claim / mtime <120s → PROTECT), not creating a `tab/<op>/<N>` ref. This plan's Phase 4
> owner-review step was never reconciled to the post-2026-06-27 topology — annotation only, no phase rewrite performed
> in this pass.

## Phases

### Phase 1 — build + smoke-test the script (this host)

- [x] [INFRA] P3. ✅ Write `unified-trading-pm/scripts/dev/audit-stash-pile.sh` (home: alongside the other per-host
      slot-hygiene scripts — `slot-cron-ff-pull.sh`, `verify-slot-host-symmetry.sh`). Behaviour: iterate every repo
      under `$WORKSPACE_ROOT` with a non-empty `refs/stash`; per repo → archive 3-way under
      `.stash-archive-<host>-<date>/` + `refs/stash-archive/*`; classify each stash per the taxonomy; in `--apply` mode
      auto-drop only empty/redundant/foreign-park; always write a per-host markdown report
      `.stash-audit-<host>-<date>.md` listing every genuine-WIP survivor with owner branch + diffstat + age. **Default =
      dry-run** (classify + report, drop nothing). Flags: `--apply`, `--repo <name>` (single-repo smoke), `--base <ref>`
      override. Base ref resolves per-repo: `origin/main` for agent-orchestrator, `origin/live-defi-rollout` otherwise.
      — owner: planning-host — unified-trading-pm@e4ef61532 (scripts/dev/audit-stash-pile.sh, implements dry-run
      default + --apply/--repo/--base + classification taxonomy)
- [x] ✅ [INFRA] P3. **CLOSED 2026-08-08 (na-eligibility-audit, round7 RECLASSIFY sweep) — DONE via the cross-referenced
      doc.** `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own copy of this exact item is `[x]` DONE 2026-08-04
      at `unified-trading-pm@1fa747856`: ran the classifier dry-run against the host's shared stash pile (76 stashes),
      hand-verified the 1 `redundant` call as a true positive plus 5 additional `genuine-WIP` boundary-case spot-checks
      (broadened beyond the done-when's "≥3" since the redundant class itself only had 1 member to verify), verdict
      "classifier trustworthy: YES." Independently re-verified this pass:
      `git merge-base --is-ancestor 1fa747856 origin/live-defi-rollout` confirms ancestor. Original text preserved below
      for record. Was: Smoke-test: run `--dry-run --repo unified-trading-pm` on this host; eyeball the 31-stash
      classification; hand-verify 2-3 "redundant" calls actually have no net diff vs LDR before trusting the auto-drop
      class. — owner: planning-host **CROSS-REFERENCED 2026-07-30 (na-eligibility-audit, infra tranche, dispatch
      agt-30721a)**: this + the Phase 2 sweep-this-host item below are already extracted (verbatim scope) as
      `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Measure fleet-wide..." todo (Done when: a written
      classification report with ≥3 hand-verified `redundant` calls + an explicit classifier-trustworthy verdict,
      Source: this doc). Not checked off here — the extracting doc's todo is not yet done; tracked there going forward.

### Phase 2 — sweep this host

- [ ] [INFRA] P3. Run `audit-stash-pile.sh --apply` across all repos on the planning host; commit the generated
      `.stash-audit-<host>-2026_06_03.md` report (path under PM repo, or attach to this plan). Auto-drop count +
      survivor count recorded in the report. Do NOT purge archives yet. — owner: planning-host

### Phase 3 — fan out to every other host (the todo IS the dispatch)

Each host owner runs the identical script locally and commits its report. Cold-start context for the worker: read
`SUB_AGENT_MANDATORY_RULES.md`; the script is dry-run by default; never `--apply` without eyeballing the dry-run first;
surface — do not auto-drop — genuine WIP.

> **[doc-reconciliation 2026-07-12, finding 73, §A2 B-queue ruling] STALE DISPATCH TARGETS** (was: the 10 named
> per-epic-VM owners below, unannotated): `cursor-configs/CLAUDE.md` system map states the per-epic-VM topology was
> retired — "N slot workers, role-based dispatch (no per-epic VMs; single-VM architecture 2026-06-27)" — the same date
> this plan's `last_updated` shows, meaning this fan-out was never reconciled to the new topology. `vm-defi` / `vm-cefi`
> / `vm-tradfi` / `vm-sports` / `vm-prediction` / `vm-ml` / `vm-trading-core` / `vm-operator-ops` / `vm-cross-cutting` /
> `vm-orchestrator` are not real dispatch targets under the current central-orchestrator + role-based-dispatch model
> (`/codex/12-agent-workflow/agent-orchestrator-single-vm-architecture.md`). A dispatcher should instead run the sweep
> per SLOT on the current fleet (per-slot worktrees, `codex/05-infrastructure/per-tab- worktrees.md`), not per named
> epic VM.
>
> **RESOLVED 2026-08-08 — ruling applied.** The re-scoping judgment call this annotation flagged was already decided
> (2026-07-28, option B) in `/plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md` § 4: "Retire
> Phase 3 entirely: mark the 10 `vm-*` rows VOID ('the hosts they name no longer exist'), keep only the still-real
> laptop/VM sweeps... since that model is equally retired." That ruling was recorded but never executed (out of the
> ruling session's own assigned-file scope) — executed here: the 10 `vm-*` rows below are marked VOID, and Phase 4's
> `tab/<op>/<N>`-branch step is rewritten to the current per-slot model.

- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-defi` is not a real dispatch target under the
      single-VM/role-based-dispatch architecture; the per-epic-VM topology this row targeted no longer exists. Per
      `infra_plan_reconcile_parked_decisions_2026_07_26.md` § 4 ruling (option B, 2026-07-28). — owner: n/a (host
      retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-cefi`, same VOID reasoning as `vm-defi` above. — owner: n/a (host
      retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-tradfi`, same VOID reasoning as `vm-defi` above. — owner: n/a (host
      retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-sports`, same VOID reasoning as `vm-defi` above. — owner: n/a (host
      retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-prediction`, same VOID reasoning as `vm-defi` above. — owner: n/a (host
      retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-ml`, same VOID reasoning as `vm-defi` above. — owner: n/a (host retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-trading-core`, same VOID reasoning as `vm-defi` above. — owner: n/a (host
      retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-operator-ops`, same VOID reasoning as `vm-defi` above. — owner: n/a (host
      retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-cross-cutting`, same VOID reasoning as `vm-defi` above. — owner: n/a
      (host retired)
- [x] ✅ [INFRA] P3. **VOID 2026-08-08** — `vm-orchestrator`, same VOID reasoning as `vm-defi` above. — owner: n/a (host
      retired)
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **Ikenna laptop**; commit report. — owner: ikenna-laptop
- [ ] [INFRA] P3. Run stash audit + conservative sweep on **Harsh laptop**; commit report. — owner: harsh-laptop

### Phase 4 — owner review of genuine-WIP survivors + final purge

- [ ] [INFRA] P3. **Rewritten 2026-08-08 per the `infra_plan_reconcile_parked_decisions_2026_07_26.md` § 4 ruling
      (option B) — the `tab/<op>/<N>` branch model is retired, same as Phase 3's targets.** Aggregate all per-host
      reports; for each genuine-WIP survivor, ping its branch owner to decide drop vs. inherit-and-commit. Under the
      current Path-B model (`/codex/05-infrastructure/per-tab-worktrees.md`), each slot is a `git clone --reference`
      checked out directly on `live-defi-rollout` — there is no per-tab branch to inherit onto. "Inherit" now means
      committing directly onto the slot's own LDR checkout, **liveness-gated per the HARD RULE**: a dead claim (no live
      session, mtime on the WIP ≥120s stale) → inherit + commit onto that checkout; a live claim (mtime <120s) →
      PROTECT, do not touch. Owners resolve within the confirmation window. — owner: planning-host
- [ ] [INFRA] P3. After the ~1-week confirmation window (target **2026-06-10**), per host: if no restore was requested,
      purge that host's archive —
      `git for-each-ref refs/stash-archive/ --format='%(refname)' | xargs -n1 git update-ref -d` then
      `rm -rf .stash-archive-<host>-<date>/`. — owner: each host

### Phase 5 — prevent regrowth (codify)

- [x] ✅ [INFRA] P3. **CLOSED 2026-08-08 (na-eligibility-audit, round7 RECLASSIFY sweep) — DONE via the cross-referenced
      doc.** `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s own copy of this exact item is `[x]` DONE 2026-07-30
      at `unified-trading-pm@59756e802`: folded a WARNING-only `--max-stash-age`-style signal into
      `scripts/dev/slot-git-status-report.sh` via a new `scripts/dev/stash-pile-detect.sh` detector (count>15/oldest>14d
      thresholds, measured off a real cross-slot distribution; never touches stash content; validated against a real
      45-entry pile, a clean repo, a never-stashed repo, and a synthetic age-only trigger). Documented in
      `/codex/05-infrastructure/per-tab-worktrees.md` § "Stash-pile regrowth signal." Independently re-verified this
      pass: `git merge-base --is-ancestor 59756e802 origin/live-defi-rollout` confirms ancestor. Original text preserved
      below for record. Was: **NICE-TO-HAVE.** The pile regrew 0→31 in PM in 2 days, so the autostash/foreign-park churn
      is structural. Investigate folding a `--max-stash-age` warning into `slot-git-status-report.sh` (or a weekly cron)
      so a host pings its inbox when `refs/stash` exceeds N or a stash ages past M days, instead of relying on manual
      sweeps. Capture decision in `/codex/05-infrastructure/per-tab-worktrees.md`. — owner: planning-host
      **CROSS-REFERENCED 2026-07-30 (na-eligibility-audit, infra tranche, dispatch agt-30721a)**: already extracted
      (verbatim scope) as `infra_satellite_ao_dispatch_batch1_2026_07_26.md`'s "Add a stash-pile regrowth signal..."
      todo (Source: this doc). Not checked off here — the extracting doc's todo is not yet done; tracked there going
      forward.

## Progress Log

- **na-eligibility-audit 2026-08-09** (infra tranche) [body-hash:99ca86720460311c]: KEEP-NA, valid — unchanged since
  2026-08-08. 5 open items remain: Phase 2 `--apply` sweep (still not a clean RECLASSIFY without an explicit
  reversibility precedent for local stash refs); 2 laptop sweeps (not workable from this environment); Phase 4
  owner-review + archive-purge (both downstream-gated on Phase 2).
- **na-eligibility-audit 2026-08-08 (round7 RECLASSIFY sweep)**: KEEP-NA, stale items — closed 2 of 7 open todos with
  hard evidence, both cross-referenced duplicates already DONE in `infra_satellite_ao_dispatch_batch1_2026_07_26.md` but
  never reflected back here: the Phase-1 smoke-test (`unified-trading-pm@1fa747856`, 2026-08-04) and the Phase-5
  regrowth-signal build (`unified-trading-pm@59756e802`, 2026-07-30), both ancestor-verified this pass. Left the
  remaining 5 open: the Phase-2 `--apply` sweep (line ~136) — now that the smoke-test's own verdict is "classifier
  trustworthy: YES," this is closer to bounded, but it is still a fleet-wide auto-drop (even if scoped to the 3
  provably-safe classes) on a SHARED multi-slot host, a real-risk local-git-mutation class this sweep is not treating as
  a clean RECLASSIFY without an explicit reversibility precedent covering local stash refs (the cheat sheet's item 6
  precedent is GCS-object-specific); the 2 laptop-sweep todos (Ikenna/Harsh) are literal personal-machine-only tasks,
  not workable from this environment; Phase 4's owner-review and Phase 5's archive-purge are both downstream-gated on
  Phase 2's output. `assigned_vm: NA` correct.
- **infra-tranche NA-question resolution 2026-08-08**: executed the standing ruling from
  `/plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md` § 4 (option B, ratified 2026-07-28 but
  never applied — "out of this file's assigned scope to execute" at the time). Voided the 10 `vm-*` Phase-3 rows
  (per-epic-VM topology retired, hosts don't exist under the single-VM/role-based-dispatch model) and rewrote Phase 4's
  owner-review todo to the current per-slot `live-defi-rollout` checkout model (liveness-gated), replacing the retired
  `tab/<op>/<N>`-branch inherit-and-commit step. Phase 3 now has 2 real open todos (the two laptop sweeps) instead of
  12; Phase 4/5 unaffected in scope, only in mechanism. Did not touch Phase 1/2 (unrelated, already tracked
  cross-references to `infra_satellite_ao_dispatch_batch1_2026_07_26.md` stand).
- **na-eligibility-audit 2026-08-07 (infra tranche)**: KEEP-NA-STALE, unchanged — re-read end-to-end;
  `grep -cE '^- \[ \]'` = 17, matching the 2026-08-02 verdict's count. The 3 items already cross-referenced into
  `infra_satellite_ao_dispatch_batch1_2026_07_26.md` remain correctly cited and still not done there (re-checked, no
  citation change needed). Doc stays NA: the 12-item Phase-3 fan-out still targets the retired per-epic-VM topology,
  gated by the same unresolved `BLOCKED-OPERATOR-DECISION` in
  `/plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md`; Phase 4 stays downstream-gated on that.
- **na-eligibility-audit 2026-07-30** (infra tranche, dispatch agt-30721a): KEEP-NA-STALE — cross-referenced the 3 items
  already duplicated verbatim in `infra_satellite_ao_dispatch_batch1_2026_07_26.md` (smoke-test + sweep-this-host → its
  "Measure fleet-wide..." todo; Phase 5 regrowth signal → its own separate todo). Doc stays NA overall — the Phase 3
  fan-out's disposition (retired per-epic-VM topology) is separately tracked as a genuine BLOCKED-OPERATOR-DECISION in
  `issues/infra_plan_reconcile_parked_decisions_2026_07_26.md` (cited by the same batch1 doc), and Phase 4's
  owner-review + purge is downstream-gated on that unresolved Phase 3 re-targeting — not independently actionable.

`shared_stash_pile_archive_cleanup_2026_06_01.md` covered ONLY `unified-trading-pm` on ONE host and has its own
2026-06-08 purge window — it proceeds independently. This plan generalises its proven archive-first pattern to all repos
× all hosts and supersedes it as the canonical recurring runbook once the script lands. Do not duplicate the PM-specific
purge here.

- **context-scout 2026-08-01**: populated/refreshed context_scope (2 entries).
- **context-scout 2026-08-03**: refreshed context_scope (5 entries) -- added the BLOCKED-OPERATOR-DECISION doc
  (`infra_plan_reconcile_parked_decisions_2026_07_26.md`) that actually gates Phase 3/4's re-targeting, replacing the
  generic epic-index pointer.
- **na-eligibility-audit 2026-08-02** (infra tranche, incremental run): **KEEP-NA-STALE — unchanged from the 2026-07-30
  verdict.** In scope only because a context-scout backfill touched the file; no content change since the last marker.
  Read end-to-end; `grep -cE '^- \[ \]'` = **17**, matching this verdict's item count. The 3 items already
  cross-referenced into `infra_satellite_ao_dispatch_batch1_2026_07_26.md` are re-confirmed still correctly cited and
  still not done there, so no citation change is warranted. Doc stays NA: the 12-item Phase-3 fan-out still targets the
  RETIRED per-epic-VM topology (`vm-defi`/`vm-cefi`/… are not dispatch targets under the single-VM architecture), which
  is a re-scoping judgment call tracked as a BLOCKED-OPERATOR-DECISION in
  `/plans/archive/issues/infra_plan_reconcile_parked_decisions_2026_07_26.md`, and Phase 4's owner-review + purge is
  downstream-gated on that unresolved re-targeting.
- **context-scout 2026-08-09**: populated/refreshed context_scope (5 entries).
