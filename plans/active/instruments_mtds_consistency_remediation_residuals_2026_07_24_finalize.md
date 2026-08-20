---
doc_type: plan
title: Instruments <-> MTDS F1-N9 consistency remediation residuals — finalize
summary:
  Gated finalize companion for instruments_mtds_consistency_remediation_residuals_2026_07_24.md (operator ruling
  2026-07-24 requirement) — reconciles N5r/N6r + N1b evidence back into the source doc once both land, then runs the
  6-step archival ritual once the source doc has zero open todos.
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [finalize, archival, instruments, mtds, manifest]
related:
  [
    instruments_mtds_consistency_remediation_residuals_2026_07_24,
    /plans/active/cross_cutting_consolidated_closeout_2026_07_25.md,
  ]
created: "2026-08-09"
parent_epic: instruments_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: refactor
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.1
assigned_role: data_engineering
effort: medium
drift_direction: none
depends_on: [instruments_mtds_consistency_remediation_residuals_2026_07_24]
gate_on_depends: true
sequential: true
locked_by:
locked_since:
supersedes:
superseded_by:
source: >-
  Authored 2026-08-09 to satisfy task_template.md's "every AO-dispatched plan needs a gated finalize plan" rule
  (operator ruling 2026-07-24) — the source doc was reclassified assigned_vm: NA -> planning this same session once the
  operator ruled on its two remaining operator-gated items (N5r/N6r, N1b), and the finalize-plan-coverage QG gate
  correctly caught the missing companion before commit.
context_scope: [/plans/active/instruments_mtds_consistency_remediation_residuals_2026_07_24.md, /codex/12-agent-workflow/plan-completion-and-archival-discipline.md, /plans/active/task_template.md, /plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md]
last_updated: "2026-08-20"
---

# Instruments <-> MTDS F1-N9 consistency remediation residuals — finalize

## Todos

- [ ] [REVIEW] P2. **Scope narrowed 2026-08-19 (plan_reconciler, cross-cutting) — N1b is done, per this same todo's
      own 2026-08-11 verification note below; only N5r/N6r remain.** Once the source doc's remaining N5r/N6r (DeFi
      manifest rebuild-for-real-replace) todo is done, reconcile its evidence back into
      `instruments_mtds_consistency_remediation_residuals_2026_07_24.md`'s own checkboxes — re-verify the cited
      commit/manifest-state exists, don't trust a copied evidence line. Also re-check N1b's Step-4 enumerator dependency
      (flagged as unverified at ruling time) actually cleared before treating it as done.

      **2026-08-11 verification pass (slot 20) — NOT YET READY, checkbox stays open.** The source doc's own checkboxes
          read "zero open todos", but that is a delegation artifact, not genuine completion for one of the two items:
          **N1b — genuinely DONE.** Re-verified the source doc's own evidence chain (Step-4 catalogue built + confirmed live
          `instruments-service@097e230b`; UTL memoization fix `unified-trading-library@a35819ee`; 2 corrector dedup-tiebreak
          bugs found + fixed `instruments-service@8cf44c665` + `@159c0ebe`; final apply **verified merged (slot 14): 7/7
          empty_confirmed**). No further work outstanding. **N5r/N6r — NOT actually done**, despite reading `[x]` in both
          the source doc (line ~718, "EXTRACTED 2026-08-09") and the satellite plan it was extracted to
          (`cross_cutting_satellite_ao_dispatch_batch2_2026_08_09.md`, "code shipped (sub-steps a+b); VM execution (c-e)
          tracked in `/plans/active/issues/defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md`"). That issue
          doc's own todo **(e) "apply + post-verify" is still `- [ ]` open** — the live prod swap against the 133M-row defi
          `_index` has not been executed. Confirmed fresh (2026-08-11): no `defi-manifest-projection-*` VM is running and
          no `canonical-migration-defi-rebuild-*` VM is running either (`gcloud compute instances list` — 0 matches for
          either prefix), consistent with the issue doc's last progress entry (slot 8, 2026-08-10T21:3xZ) that released the
          task GATED with nothing to apply yet. **Conclusion: do not flip this REVIEW todo done and do not proceed to the
          archival todo below** until `defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e) is checked
          off with a real post-apply re-audit (0 stale rows, full twin coverage) AND that evidence is reconciled back into
          the source doc's N5r/N6r checkbox. Re-dispatch this REVIEW todo once that lands.

- [ ] [DOC] P2. Once the source doc shows zero open todos, run the standard 6-step archival ritual on it
      (`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`) — migrate any deferred item, banner,
      codex-alignment check, corpus-wide referrer fixup, then `git mv` to `plans/archive/<YYYY_MM>/`. Distinct
      `[TAG]`/priority from the REVIEW todo above (per task_template.md's same-tag-collision gotcha).

      **BLOCKED (2026-08-11, slot 20): do not archive.** See the REVIEW todo's 2026-08-11 verification note above — the
          source doc's "zero open todos" state is a delegation artifact; the delegated N5r/N6r work
          (`defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e)) is still genuinely open. Archiving now
          would strand that live tracked work's `related:` back-reference to an archived doc mid-execution. Wait for the
          REVIEW todo to actually flip first.

## Progress Log

- **2026-08-11 (slot 20)**: Dispatched the archival todo directly; per craft convention worked the finalize plan
  start-to-finish instead of archiving blind. Found the archival precondition is not genuinely met — see the inline
  2026-08-11 notes on both todos above. No archival performed. Both todos left open; skipping this task back to the
  queue (`GATED`) rather than false-`/done`ing an archival that would strand live in-progress work
  (`defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md`).
- **2026-08-11T21:59Z (slot 8)**: Re-dispatched the same archival todo; re-verified fresh rather than trusting slot 20's
  hours-old check. Same conclusion, precondition still unmet: (1) `gcloud compute instances list` — 0 matches for
  `defi-manifest-projection-` or `canonical-migration-defi-rebuild-`, no execution VM running; (2)
  `get_storage_client().list_blobs('deployment-scripts-central-element-323112', prefix='n5r-n6r-projection/')` — 0
  objects, the projection has never been run. `defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e) is
  still `- [ ]` open with no forward progress since its own last entry (slot 8, 2026-08-10T21:3xZ). No archival
  performed; both todos left open; skipping GATED again — the blocker is VM-execution work outside this archival todo's
  own scope, not something to force through here.
- **2026-08-12 (slot 6)**: Re-dispatched the same archival todo; re-verified fresh rather than trusting prior sessions'
  checks. Same conclusion, precondition still unmet: (1)
  `gcloud compute instances list --filter="name~'defi-manifest- projection-' OR name~'canonical-migration-defi-rebuild-'"`
  — 0 matches, no execution VM running; (2)
  `get_storage_client().list_blobs('deployment-scripts-central-element-323112', prefix='n5r-n6r-projection/')` — 0
  objects, the projection has never been run; (3) source doc's own checkboxes confirmed zero `- [ ]` remaining (the
  delegation artifact is genuine — N5r/N6r reads `[x]` there but is EXTRACTED to the satellite/issue-doc chain).
  `defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e) is still `- [ ]` open — the launcher (c) and
  drain-gate capability (d) are both shipped and ready, but no one has actually launched
  `launch-defi-manifest-projection-vm.sh` yet. No archival performed; both todos left open; skipping GATED — VM launch
  - execution is out of this archival todo's own scope (this finalize plan carries no `repos:`, doc-only) and belongs to
    the issue doc's own SCRIPT todo.
- **context-scout 2026-08-17**: populated/refreshed context_scope (3 entries)
- **2026-08-19 (slot 33)**: Re-dispatched the REVIEW todo; re-verified fresh rather than trusting prior sessions'
  checks. Same conclusion, precondition still unmet — N5r/N6r (e) has genuinely never been executed: (1)
  `gcloud compute instances list` — 0 matches for `defi-manifest-projection-` or `canonical-migration-defi-rebuild-`,
  no execution VM running or ever launched; (2)
  `get_storage_client().list_blobs('deployment-scripts-central-element-323112', prefix='n5r-n6r-projection/')` — 0
  objects, the projection has never been run; (3) 0 projection-related `vm-logs/` blobs — the launcher was never
  invoked; (4) `defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e) still `- [ ]`. **NEW vs prior
  sessions**: the live AO backlog shows the (e) execution task (`defi_manifest_venue_itype_canon_swap_execution-4a5cafd06bcb`)
  is QUEUED and dispatchable, and launcher (c) + drain gate (d) are both SHIPPED
  (`deployment-service@99b46b9f2d`, `market-tick-data-service@697d983c/@0a9ea724`) — the chain is not stalled: a
  data_engineering executor picking up (e) can launch `deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh`
  to produce the projection, run the drain-gate + snapshot, then `--apply-prod --confirm-prod-write` + post-verify.
  This REVIEW todo stays `- [ ]`; no archival performed; skipping GATED — the blocker is VM-execution work owned by the
  issue doc's own SCRIPT todo (e), out of this doc-only review todo's scope.
- **context-scout 2026-08-20**: populated/refreshed context_scope (4 entries)
- **2026-08-20 (slot 4)**: Re-dispatched the REVIEW todo; re-verified fresh rather than trusting prior sessions'
  checks. Same conclusion, precondition still unmet — N5r/N6r (e) has genuinely never been executed: (1)
  `gcloud compute instances list` — 0 matches for `defi-manifest-projection-` or `canonical-migration-defi-rebuild-`,
  no execution VM running or ever launched; (2)
  `get_storage_client().list_blobs('deployment-scripts-central-element-323112', prefix='n5r-n6r-projection/')` — 0
  objects, the projection has never been run; (3) 0 projection-related `vm-logs/` blobs — the launcher was never
  invoked; (4) `defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e) still `- [ ]` open. Live AO
  backlog (2026-08-20) confirms the (e) execution task
  (`defi_manifest_venue_itype_canon_swap_execution-4a5cafd06bcb`) is QUEUED and dispatchable — the chain is not
  stalled: a data_engineering executor picking it up can launch
  `deployment-service/scripts/vm/launch-defi-manifest-projection-vm.sh`, run the drain-gate + snapshot, then
  `--apply-prod --confirm-prod-write` + post-verify. This REVIEW todo stays `- [ ]`; no archival performed; skipping
  GATED — the blocker is VM-execution work owned by the issue doc's own SCRIPT todo (e), out of this doc-only review
  todo's scope.
- **2026-08-20 (slot 1)**: Re-dispatched the REVIEW todo; re-verified fresh rather than trusting slot 4's same-day
  check. Same conclusion, precondition still unmet — N5r/N6r (e) has genuinely never been executed: (1)
  `gcloud compute instances list` — 0 matches for `defi-manifest-projection-` or `canonical-migration-defi-rebuild-`
  in the live fleet (36 running VMs total, none matching either prefix); (2) UTL
  `get_storage_client().list_blobs('deployment-scripts-central-element-323112', prefix='n5r-n6r-projection/')` — 0
  objects; (3) 0 projection-related `vm-logs/` blobs; (4)
  `defi_manifest_venue_itype_canon_swap_execution_2026_08_10.md` todo (e) still `- [ ]` open. **Correction to slot
  4's same-day note**: the live AO backlog does NOT show task
  `defi_manifest_venue_itype_canon_swap_execution-4a5cafd06bcb` as freely dispatchable — `GET /api/backlog` shows it
  `status: queued` but `priority: 999` with `blocked_reason: "prerequisite
  auto_unpark__defi_manifest_venue_itype_canon_swap_execution-4783407decd9 not set"` (parked since `queued_at:
  2026-08-12T19:46:06Z`, i.e. 8 days with no forward movement). This matches RULES.md § 4's "park a task" shape
  (priority 999 + a gating condition that must be manually flipped `true`), not a transient GATED-skip cooldown
  (those cap at `tuning.dispatch_cooldown_max_eta_minutes`, default 180min, which would long since have expired). No
  `/api/prerequisites` listing endpoint was reachable to confirm who set it or why; flagging rather than guessing —
  worth an operator/main look at whether this park is intentional or a stale leftover that should be unparked so the
  dispatcher can route it again. This REVIEW todo stays `- [ ]`; no archival performed; skipping GATED — the blocker
  is VM-execution work owned by the issue doc's own SCRIPT todo (e), out of this doc-only review todo's scope.
