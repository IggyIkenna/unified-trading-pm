---
doc_type: plan
title: Infra satellite AO batch 15 — /tmp tmpfs root-cause fix + S5.7 redirect-stub reconciliation
summary: >-
  Fifteenth AO-dispatch batch for the `infra` topic tranche, produced by `/ag-closeout-audit infra` (autonomous mode,
  2026-08-10). Two independent, conflict-clear sources: (1) `host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md` —
  the shared-host `/tmp` tmpfs (fixed 8GB, RAM-backed) has hit 100% full at least once, breaking pytest fleet-wide with
  spurious "No space left on device" failures; live-reverified 2026-08-10 (currently 29% used, but with a DIFFERENT set
  of large one-off scratch parquets than the original report — confirms the underlying pattern is ongoing, not a
  one-time fluke that already self-resolved). (2) `s5_7_required_docs_gaps_2026_07_29.md`'s corrected todo (re-scoped
  this same run — see that doc's own 2026-08-10 Progress Log entry) — reconcile market-data-processing-service's
  `DEPLOYMENT_GUIDE.md`/`TESTING.md` against the S5.1 filename set via thin redirect stubs, mirroring the
  already-executed instruments-service precedent, per `codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s dated DELETE
  classification for both files.
status: draft
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, market-data-processing-service]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-15, tmpfs, docs-standards]
related:
  [
    /plans/active/infra_satellite_ao_dispatch_batch15_finalize_2026_08_10.md,
    /plans/active/issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md,
    /plans/active/issues/s5_7_required_docs_gaps_2026_07_29.md,
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/active/issues/ag_closeout_audit_infra_parked_2026_08_10.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md,
  ]
created: "2026-08-10"
last_updated: "2026-08-10"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.5
estimate_calibrated_ai_days: 0.4
assigned_role: infra
effort: medium
sequential: false
drift_direction: advance-code
locked_by:
locked_since:
context_scope:
  [
    /plans/active/issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md,
    /plans/active/issues/s5_7_required_docs_gaps_2026_07_29.md,
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
  ]
supersedes:
superseded_by:
depends_on: []
source: >-
  `/ag-closeout-audit infra` run 2026-08-10 (ag_closeout_auditor scheduled worker, slot 20, dispatch agt-7788a0). Phase
  0 re-derived the covering set via `generate_ag_closeout_audit_candidates.py --tranche infra` (58 members, 15 covering
  docs, 17 never-cited). Phase 1 ran a 17-agent Workflow classifying every never-cited candidate; 2 were AO-eligible and
  conflict-clear. See `issues/ag_closeout_audit_infra_parked_2026_08_10.md`'s "Second dispatch delta" section for the
  full run report.
---

# Infra satellite docs — AO dispatch batch 15

## Why this plan exists

**`/tmp` tmpfs capacity (P1).** The shared host's `/tmp` mount is a fixed 8GB RAM-backed tmpfs, independent of the
(healthy, 175G-free) root disk. It hit 100% full on 2026-08-09, breaking 4 unrelated `deployment-service` tests with
`write error: No space left on device` — confirmed not a test/code defect via a clean-tree stash-and-retest. Live
re-check today (2026-08-10) shows 29% used, but the specific large files have completely turned over (the original
`enum-univ-defi-*.parquet` 2.8G pair is gone; today's largest consumers are `repro-venv` 808M + several ~198-201M
one-off parquets, including a new `enum-univ-prediction-*` file) — this is the SAME unmanaged-accumulation pattern
recurring with different actors, not a one-time fluke. `free -h` shows only ~1.6GB genuinely free RAM (13GB used, 16GB
buff/cache) — raising the tmpfs ceiling is a real trade-off against live memory headroom, not a free knob; the worker
doing this todo needs to weigh that live, not assume more tmpfs is free.

**S5.7 redirect-stub reconciliation (P2).** `s5_7_required_docs_gaps_2026_07_29.md`'s last open todo asked to "fill"
market-data-processing-service's `DEPLOYMENT_GUIDE.md`/`TESTING.md` as if genuinely absent content — but
`codex_vs_repo_docs_ssot_audit_2026_06_01.md`'s dated, specific 2026-07-27 refreshed registry classifies both as
**DELETE** (stubs whose real content already lives at `DEPLOYMENT_GUIDE_FEMI.md`/`TESTING_GUIDE.md`), with both REDIRECT
targets already verified to exist. This is the identical "naming/structure drift vs the fixed S5.1 filename set" pattern
the operator already resolved for instruments-service (2026-08-08, item 77: 6 thin redirect stubs added). A 2026-08-08
na-eligibility-audit round7 pass found this exact contradiction and correctly held the todo `assigned_vm: NA` pending
reconciliation rather than guessing. This run's Phase 1 re-confirmed the same read; the source doc's own todo text has
been corrected in-place (see its 2026-08-10 Progress Log entry) from "fill" to "verify + redirect-stub," and the
corrected, now conflict-clear todo is extracted here.

## Conflict check (before drafting)

- **`/tmp` tmpfs**: grepped all 15 infra covering docs + `plans/archive/2026_0*/infra_*.md` for `tmpfs` — the only hit
  (`infra_satellite_ao_dispatch_batch10_2026_08_09.md` line 179) is a `TMPDIR`-avoidance idiom for a DIFFERENT,
  already-resolved issue (`shared_host_tmp_tmpfs_exhaustion_2026_07_08`, fixed via `cleanup-stale-qg-tmp.sh`'s own
  precedent) — not a competing claim on today's issue. Corpus-wide grep for this doc's own filename/basename: zero hits
  outside its own file and today's parked-findings doc. No conflict.
- **S5.7 redirect stubs**: the only competing claim is `codex_vs_repo_docs_ssot_audit_2026_06_01.md` itself — and it's
  not competing, it's the SOURCE of the correct approach (resolved by logic above, not a live disagreement). Grepped all
  15 infra covering docs + corpus-wide for `DEPLOYMENT_GUIDE_FEMI\|market-data-processing-service.*TESTING_GUIDE` — no
  other active plan proposes touching these 2 specific files. No conflict.
- **File-collision check across this batch's own 2 todos**: todo 1 touches host/VM tmpfs provisioning config (repo:
  unified-trading-pm scripts or wherever the mount is provisioned) + possibly a scratch-routing script; todo 2 touches 2
  doc files in `market-data-processing-service/docs/`. Zero overlap — `sequential` left unset (default concurrent).

## Todos

- [ ] [INFRA] P1. **Fix the shared-host `/tmp` tmpfs capacity issue at the root.** Determine whether the fixed 8GB
      ceiling is genuinely too small for current fleet-wide scratch-write load, or whether the real problem is large
      one-off parquet scratch files (`enum-univ-*`, per-slot corrector/regen scratch) never being cleaned up post-run —
      check `free -h` for real RAM headroom before proposing any ceiling raise (only ~1.6GB free at last check, so a
      raise may not be safe without also addressing the accumulation). Fix at the root: either raise the tmpfs size (if
      headroom genuinely allows), or route large one-off scratch parquet writes to a non-tmpfs scratch dir (mirrors the
      workspace's own scratchpad-directory convention for agent sessions), or both. Before any deletion of currently-
      large `/tmp` files as part of verifying the fix: confirm genuine ownership (is the writing process still alive?)
      per the multi-agent-safety HARD RULE against touching another slot's untracked/in-flight state — do not
      blind-delete. Done when: `df -h /tmp` no longer has a plausible path to spurious 100%-full pytest failures under
      normal fleet load (either headroom is measurably larger, or the largest recurring scratch-write offenders are
      confirmed routed elsewhere), and the fix is documented (a codex SSOT or the VM provisioning script, worker's call
      on which). Source: `issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md` (both todos, combined — the
      ownership-audit caution folds into how this fix is verified, not a separate deliverable). Repo: unified-trading-pm
      (host/VM tmpfs provisioning) or wherever the mount is actually configured.
- [ ] [DOCS] P2. **Reconcile market-data-processing-service's `DEPLOYMENT_GUIDE.md`/`TESTING.md` via redirect stubs, not
      new content.** Verify `DEPLOYMENT_GUIDE_FEMI.md` and `TESTING_GUIDE.md` genuinely cover what the canonical S5.1
      filenames would need to say (read both against `/codex/06-coding-standards/documentation-standards.md`'s
      S5.1/S5.1a required-content scope) — if confirmed, add S5.11-template thin redirect stubs at `DEPLOYMENT_GUIDE.md`
      and `TESTING.md` pointing at the real content, mirroring instruments-service's already-shipped 6-stub pattern
      exactly (stub → one-line "Canonical SSOT:" pointer + brief context, not a content fork). If the FEMI/GUIDE docs
      turn out NOT to fully cover the S5.1-required scope, fall back to filling the specific gap directly instead of
      forcing a redirect that would be misleading — worker's call, evidenced either way. Done when: both files are
      either confirmed-adequate redirect stubs or genuinely-filled content,
      `codex_vs_repo_docs_ssot_audit_2026_06_01.md` is updated to reflect the resolution (its own Appendix/registry
      entry for these 2 files), and `s5_7_required_docs_gaps_2026_07_29.md`'s corrected todo is flipped `[x]`. Source:
      `issues/s5_7_required_docs_gaps_2026_07_29.md` (corrected todo, 2026-08-10) /
      `codex_vs_repo_docs_ssot_audit_2026_06_01.md` (DELETE classification + redirect targets). Repo:
      market-data-processing-service.

## Operator approval gate

**This plan is `status: draft` — awaiting operator review.** Flip to `status: active` only after explicit approval (its
finalize twin is drafted alongside it, gated on this plan per the finalize-plan-coverage rule).

## Codex SSOTs (read before touching a todo)

- `/cursor-configs/skills/ag-closeout-audit/SKILL.md` — the procedure this batch was produced by
- `/codex/11-project-management/ao-dispatch-batch-naming-and-conflict-check.md` — the conflict-check protocol applied
  above
- `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md` — archival ritual the finalize plan runs
- `/plans/active/task_template.md` §4 — finalize-plan-coverage rule, dispatch-scope eligibility test
- `/codex/06-coding-standards/documentation-standards.md` — S5.1/S5.1a/S5.11 required-docs + redirect-stub convention

## Progress Log

- **2026-08-10** — Drafted by `/ag-closeout-audit infra` (autonomous mode, scheduled daily run, slot 20, dispatch
  agt-7788a0), the tranche's second same-day dispatch (after slot 26's `all`-mode linkage-only sweep at 01:10 UTC found
  0 orphans via the lighter linkage-check pre-filter). This run's fuller 17-agent Phase-1 Workflow found 2 genuinely
  AO-eligible, conflict-clear candidates among the 9 orphaned_never_touched verdicts. Paired with
  `infra_satellite_ao_dispatch_batch15_finalize_2026_08_10.md` in the same run per the finalize-plan-coverage rule.
