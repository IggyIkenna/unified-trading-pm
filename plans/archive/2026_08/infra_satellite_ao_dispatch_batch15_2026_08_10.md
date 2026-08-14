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
status: complete
nature: process
asset_group: [infrastructure]
stage: [meta]
repos: [unified-trading-pm, market-data-processing-service]
scope: [engineer, admin]
tags: [infra, ao-dispatch, ag-closeout-audit, satellite-docs, batch-15, tmpfs, docs-standards]
related:
  [
    /plans/archive/2026_08/infra_satellite_ao_dispatch_batch15_finalize_2026_08_10.md,
    /plans/active/issues/host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md,
    /plans/active/issues/s5_7_required_docs_gaps_2026_07_29.md,
    /plans/active/codex_vs_repo_docs_ssot_audit_2026_06_01.md,
    /plans/active/infra_consolidated_closeout_2026_07_25.md,
    /plans/archive/2026_08/issues/ag_closeout_audit_infra_parked_2026_08_10.md,
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

> **🟢 ARCHIVED 2026-08-10 — COMPLETE.** Both todos done. Finalize plan
> (`infra_satellite_ao_dispatch_batch15_finalize_2026_08_10.md`) reconciled both distinct source docs the 2 todos cite
> (`host_tmp_tmpfs_full_breaks_pytest_write_2026_08_09.md`'s 2 todos — P1 sizing/routing fix, P2 ownership audit; and
> `s5_7_required_docs_gaps_2026_07_29.md`'s corrected todo — MOOT per operator ruling BLK-2b076fa9, DELETE wins), then
> archived this plan via the standard 6-step ritual. Finalize archived alongside at
> `/plans/archive/2026_08/infra_satellite_ao_dispatch_batch15_finalize_2026_08_10.md`.

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

- [x] ✅ [INFRA] P1. **Fix the shared-host `/tmp` tmpfs capacity issue at the root.** Determine whether the fixed 8GB
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
      (host/VM tmpfs provisioning) or wherever the mount is actually configured. — **DONE 2026-08-10 (slot-20,
      infra_satellite_ao_dispatch_batch15-fc54cb24200b).** Root cause: accumulation of large one-off parquet scratch on
      the fixed 8GB RAM-backed /tmp tmpfs (resized 2G→8G ~4x and still saturates → sizing is NOT the fix; only ~3.3G RAM
      genuinely free). Fix = route + reap + document: (1) instruments-service@bc36e4a5 routes the recurring writers
      (`enumerate_expected_universe.py` enum-univ-_/enum-shard-_,
      `reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py` cefi-corrector-*) to
      `$HOME/.cache/instruments-scratch` (root disk) via a `_scratch_dir()` helper (+ `--scratch-dir` /
      `$INSTRUMENTS_SCRATCH_DIR` override) — confirmed routed off the tmpfs; (2) unified-trading-pm reaper
      `cleanup-stale-tmp-parquet-scratch.sh` + cron installer (liveness-gated, 6h TTL) reclaims SIGKILL orphans +
      residual one-off /tmp parquet scratch (PM@9db60dd7d4, committed; push blocked by pre-existing repo red RB-5b82f02e
      — plan-commit-sha-evidence ratchet red from slot-28's unresolvable citation, filed as
      `issues/plan_commit_sha_evidence_unresolvable_0f9b8a65ca_2026_08_10.md`); (3) codex SSOT
      `/codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md` (PM@9db60dd7d4) documents root cause + routing
      convention + sizing decision. `df -h /tmp` 8.0G 3.1G used — no plausible path to 100% under normal fleet load with
      the recurring offenders routed off the tmpfs.
- [x] ✅ [DOCS] P2. **Reconcile market-data-processing-service's `DEPLOYMENT_GUIDE.md`/`TESTING.md` via redirect stubs,
      not new content.** — **MOOT per operator ruling BLK-2b076fa9 (2026-08-10, applied 08:45).** This todo was drafted
      (06:11) BEFORE that ruling, which is newer + specifically on-point for exactly these 2 files: option A **DELETE
      wins, NO redirect stubs needed** — `DEPLOYMENT_GUIDE_FEMI.md`/`TESTING_GUIDE.md` already cover the real content,
      and the SSOT audit's 2026-07-27 ground-truthed registry classifies `DEPLOYMENT_GUIDE.md`/`TESTING.md` as DELETE.
      The plan's bulk activation (12:10) did not amend this todo; the pre-task conflict check surfaced the contradiction
      (BLK-e2c5b647) and the operator confirmed A. `s5_7_required_docs_gaps_2026_07_29.md`'s corrected todo is already
      `[x]` CLOSED under the same ruling. Done when (satisfied): no redirect stubs created; SSOT audit registry already
      reflects DELETE for both files. Source: `issues/s5_7_required_docs_gaps_2026_07_29.md` (corrected todo,
      2026-08-10) / `codex_vs_repo_docs_ssot_audit_2026_06_01.md` (DELETE classification + redirect targets). Repo:
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

- **2026-08-10 (slot-20, infra_satellite_ao_dispatch_batch15-fc54cb24200b)** — Executed todo 1 (P1 `/tmp` tmpfs root
  fix). Investigation (plan context_scope + live host): `/tmp` is a fixed 8GB RAM-backed tmpfs in `/etc/fstab`, already
  resized ~4x (2G→8G per 2026-07-27→08-09 history) and STILL saturated to 100% on 08-09 → **accumulation problem, not
  sizing**. Live `free -h`: ~3.3G genuinely free → a resize is a poor trade (and prior operator rulings 07-08/07-26 kept
  the mount resize out of scope). Recurring offenders confirmed: instruments-service writers
  (`enumerate_expected_universe.py` enum-univ-_/enum-shard-_,
  `reconcile_correct_legacy_blank_misflips_cefi_2026_05_13.py` cefi-corrector-*) via `tempfile.NamedTemporaryFile` →
  `/tmp`, with cleanup only in `finally` (SIGKILLed runs orphan 150MB–2.8GB files). Shipped:
  **instruments-service@bc36e4a5** (routing to `$HOME/.cache/instruments-scratch`, root disk, off the tmpfs;
  `--scratch-dir`/`$INSTRUMENTS_SCRATCH_DIR` override; 5+2 NamedTemporaryFile sites routed) +
  **instruments-service@451737d1** (fixture `_PER_AG_TARGET_COUNTS` CEFI 25→24 for UAC@56db28e6 BINANCE-DELIVERY removal
  — pre-existing drift surfaced by QG, fixed ≤30min per findings triage; both verified on origin). PM: **PM@9db60dd7d4**
  reaper (`scripts/dev/cleanup-stale-tmp-parquet-scratch.sh` + `install-...cron.sh`, liveness-gated 6h TTL) + codex SSOT
  (`/codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md`). PM push blocked by a PRE-EXISTING repo red (not mine):
  slot-28's flip `b9d9725354` cites `unified-trading-pm@0f9b8a65ca` (404 on GitHub, unresolvable) → plan-commit-sha-
  evidence ratchet 0→1 blocks the `.n_sha` sentinel. Filed
  `issues/plan_commit_sha_evidence_unresolvable_0f9b8a65ca_2026_08_10.md` (+ fix todo) and registered as waiter on
  repo-blocker RB-5b82f02e. PM reaper/codex ship + this flip will land once the pre-existing PM red clears.

- **2026-08-10** — Drafted by `/ag-closeout-audit infra` (autonomous mode, scheduled daily run, slot 20, dispatch
  agt-7788a0), the tranche's second same-day dispatch (after slot 26's `all`-mode linkage-only sweep at 01:10 UTC found
  0 orphans via the lighter linkage-check pre-filter). This run's fuller 17-agent Phase-1 Workflow found 2 genuinely
  AO-eligible, conflict-clear candidates among the 9 orphaned_never_touched verdicts. Paired with
  `infra_satellite_ao_dispatch_batch15_finalize_2026_08_10.md` in the same run per the finalize-plan-coverage rule.

- **2026-08-10 (slot-3, infra)**: Flipped todo 2 `[x]` as **MOOT per operator ruling BLK-2b076fa9**. Pre-task
  conflict-check surfaced a direct contradiction between this todo (add S5.11 redirect stubs at MDPS
  `docs/DEPLOYMENT_GUIDE.md`/`docs/TESTING.md`) and the newer, on-point ruling BLK-2b076fa9 (applied 08:45, after this
  plan's 06:11 draft): option A **DELETE wins, NO redirect stubs needed**; `DEPLOYMENT_GUIDE_FEMI.md`/`TESTING_GUIDE.md`
  already cover the real content, and the SSOT audit registry (`codex_vs_repo_docs_ssot_audit_2026_06_01.md` line 874)
  classifies both files DELETE. Escalated as BLK-e2c5b647; operator confirmed A. No redirect stubs created; `s5_7`
  corrected todo already `[x]`-CLOSED under the same ruling.
- **2026-08-10 (slot-17, infra) — archived**. `git mv` to `plans/archive/2026_08/` via the standard 6-step ritual —
  banner + `status: complete`, all corpus referrers repointed (incl.
  `/codex/05-infrastructure/shared-host-tmp-tmpfs-capacity.md`), INDEX.md regenerated. Finalize plan archived alongside
  (all 3 of its todos done). `check_ag_closeout_linkage.py` 0 orphans (baseline 0) +
  `regenerate_active_plan_inventory.py` clean.
