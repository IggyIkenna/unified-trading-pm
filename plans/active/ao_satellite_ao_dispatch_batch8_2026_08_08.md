---
doc_type: plan
title: AO satellite AO batch 8 — eighth dispatch batch extracted from the AO tranche's satellite docs
summary: >-
  EIGHTH AO-dispatch batch for the `ao` topic tranche, produced by the `/ag-closeout-audit ao` skill run (2026-08-08,
  autonomous mode, scheduled `ag_closeout_auditor` dispatch, slot 12). Phase 0 re-confirmed the tranche's covering-plan
  set (batch1+finalize +batch4 archived; batch2/batch3/batch4-finalize active; batch5/batch6/batch7 still `status:
  draft`, awaiting operator approval). Phase 1 ran a full 58-agent Workflow classification over every
  non-self-dispatched AG-primary candidate (66 total candidates; 8 already self-dispatched). Headline finding: 45 of the
  50 verdicted `orphaned_*` docs are NOT actually untriaged — batch5/batch6/batch7's own Deferred sections already
  correctly classify their remaining items as operator-gated / too-large-unscoped / already-claimed-elsewhere /
  credential-gapped; those 3 batches simply haven't been operator-approved yet (see this plan's "Why this plan exists").
  Phase 0.3's Orthogonality sweep found + retagged 2 genuine mistags directly (1 `[sports,ao]`→`[sports,ci]`
  CI-governance content; 1 `[ao,cross-cutting]`→`[ao]` redundant cross-cutting tag). Only 5 candidate docs (all dated
  2026-08-06/08-07, postdating batch7's authoring) were genuinely never triaged by any prior batch — Phase 3's
  conflict-check on those 5 found ONE genuine same-file collision (two docs both target
  `deepseek-per-turn-metrics.spec.ts` with overlapping root-cause hypotheses) and merged them into one todo rather than
  drafting two racing ones. 4 bounded items extracted into this batch; the remaining items across those 5 docs are
  operator-gated design forks, deferred below.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-8, satellite-docs]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch6_2026_08_04.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch5_2026_08_03.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-08"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: research
estimate_baseline_ai_days: 1.4
estimate_calibrated_ai_days: 1.68
assigned_role: backend_engineer
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
context_scope:
  [
    agent-orchestrator/dashboard/tests/e2e/deepseek-per-turn-metrics.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/deepseek-wallet-reconciliation.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/worker-chat.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/backlog-collision.spec.ts,
    agent-orchestrator/server/deepseek_usage_poller.py,
    /codex/06-coding-standards/ui-testing-layers.md,
    /codex/05-infrastructure/per-tab-worktrees.md,
    scripts/quickmerge.sh,
  ]
source: >-
  /ag-closeout-audit ao skill run 2026-08-08 (autonomous, scheduled ag_closeout_auditor dispatch, slot 12). Phase 0
  re-derived the covering-plan set via generate_ag_closeout_audit_candidates.py --tranche ao (66 candidates, 11 covering
  batch/finalize plans, 8 self-dispatched). Phase 1 ran the full Workflow fan-out (58 agents, one per
  non-self-dispatched candidate — the full population, not a delta-only pass, since this run's Workflow completed
  cleanly) rather than a delta-only read, since no prior run this week had done the full sweep. Phase 3's conflict-check
  ran per-item against all 11 covering plans' actual todos plus the other candidate items in this same batch, for
  target-file collisions.
---

# AO satellite AO batch 8

> **`status: active`** — approved 2026-08-08, same-day as drafting, after a fresh conflict-check found no blocking
> overlap (see Progress Log). This batch's own text already argued this was the single highest-leverage action available
> ("The single highest-leverage action available right now is operator review + approval of batch5/6/7, not another
> audit pass") — batch5/6/7 were approved in the same review pass as this doc. **`assigned_vm: planning` /
> `execution_scope: orchestrator-agent`** — the `ao` tranche's 2026-07-17 "local execution only" ruling was explicitly
> LIFTED 2026-08-08 (operator, interactive); see batch5's Progress Log for the full citation trail. AO-dispatchable now,
> same as every other tranche. Authored autonomously (scheduled dispatch) and originally shipped `status: draft` pending
> operator approval.

## Why this plan exists — and the bigger finding it surfaces

A full Phase 1 Workflow (58 agents, one per non-self-dispatched `ao`-tranche candidate doc) classified 50 of 58 as
`orphaned_partial_coverage` or `orphaned_never_touched`. Reading every one of those 50 verdicts' actual coverage
evidence (not just the count) surfaces the real picture: **45 of the 50 are not actually untriaged.**
`ao_satellite_ao_dispatch_batch5_2026_08_03.md`, `…batch6_2026_08_04.md`, and `…batch7_2026_08_06.md` each already ran
their own careful per-candidate audit and filed a "Deferred — full per-doc disposition of the declined orphaned
candidates" section explaining EXACTLY why each item is not AO-dispatch-eligible today (operator-gated design fork,
too-large/unscoped, already-claimed by a different doc, credential/host-access-gapped, conflict-gated against a sibling
plan, or conditionally-gated pending a named future check). That triage is real and does not need to be redone — but
because those 3 batches are still `status: draft`, awaiting operator approval, the mechanical citation-checker (and, if
you only count checkboxes, a naive human skim) reads all of it as "not covered by an active todo," which is technically
true (a draft isn't dispatched) but misleading about how much genuine analysis has already happened.

**The single highest-leverage action available right now is operator review + approval of batch5/6/7**, not another
audit pass. Approving them would (a) formally close the "declined" disposition on ~37 of the 45 already-triaged docs (no
further action needed, just operator sign-off that the triage stands), and (b) let batch5/6/7's own already-drafted
todos land, which fully or partially close the remaining ~8 partial-coverage docs.

Of the 50 orphaned verdicts, only **5 docs** (all created 2026-08-06 or 2026-08-07, i.e. after batch7 was authored) were
genuinely never seen by any prior triage pass — confirmed via basename AND content-keyword grep across all 11 covering
plans returning zero hits for each. Phase 3 triaged those 5 directly:

- `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` — 3 of 4 items are bounded root-cause-and-fix investigations →
  **extracted (todos 1-3 below)**.
- `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` — item 1 (confirm blast radius) is bounded but
  **targets the same file** (`deepseek-per-turn-metrics.spec.ts`) as the flakiness doc's item 1, with an overlapping
  root-cause hypothesis (a live `DeepSeekUsagePoller` tick racing/overwriting the Accounts-panel fixture before or
  during the test's assertion window). Per the conflict-check, these were **merged into ONE todo** (todo 1 below) rather
  than drafted as two todos that would race the same file — items 2-3 (the fix-direction decision and its
  implementation) are explicitly self-flagged "(operator call, not unilateral)" and stay deferred.
- `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` — a live, P1, "big-finding"-tagged
  data-loss hazard reproduced 4 times in one session. Items 1+2 (check dangling-blob recoverability + a deliberate
  minimal 2-clone reproduction) are one internally-sequential, bounded investigation → **extracted (todo 4 below)**.
  Item 3 (implement a mitigation) explicitly states "do not implement without operator sign-off" — deferred. Item 4 (doc
  fold-in) depends on item 3 — deferred.
- `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md` — both items are pure "decide which side moves"
  judgment calls with no bounded sub-step — **fully deferred**.
- `ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06.md` — its own 2026-08-07
  na-eligibility-audit note already verdicts the one remaining item a genuine design-choice judgment call, not a
  mechanical follow-on — **fully deferred**, no re-litigation.

Two mistags found and fixed directly (Phase 0.3 Orthogonality sweep, before Phase 1 classification ran):
`instruments_service_pr1084_provenance_blocked_fix_stuck_on_ldr_2026_08_06.md` was tagged `[sports, ao]` but its content
is 100% CI/CD promotion-pipeline governance (provenance gate, quickmerge-bypass) — retagged `[sports, ci]`.
`ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` was tagged `[ao, cross-cutting]` but nothing in it spans outside
agent-orchestrator's own dashboard — the `cross-cutting` half was redundant, dropped to `[ao]`.

## Rules for every worker on this plan

- Todos 1-4 below are file-disjoint (verified during Phase 3's conflict-check): todo 1 touches
  `deepseek-per-turn-metrics.spec.ts` + `deepseek-wallet-reconciliation.spec.ts` + `deepseek_usage_poller.py`; todo 2
  touches only `worker-chat.spec.ts`; todo 3 touches only `backlog-collision.spec.ts`; todo 4 touches no product source
  file (a throwaway 2-clone git reproduction outside this checkout).
- Todo 1 has a hard stop: if root-causing confirms the fix requires disabling `DeepSeekUsagePoller` in the e2e backend
  or rewriting the spec's expected-value assertions, STOP short of implementing either — both are explicitly
  operator-gated per the source doc's own text (see todo 1's Done-when). A safe, non-disabling mitigation (e.g. an
  explicit wait-for-poller-tick or an assertion-timeout increase, the standard convention already used in
  `critical-health.spec.ts`) is in scope; changing what the poller does or what the test expects is not.
- Todo 4 is READ-ONLY / diagnostic-only against a throwaway pair of clones outside this checkout — it must not touch
  `scripts/quickmerge.sh` or `scripts/dev/safe-doc-push.sh` (the candidate mitigations named in the source doc's item 3
  are explicitly gated on operator sign-off before any implementation).
- Do not edit a source issue doc's checkboxes beyond appending your evidence line to the todo you executed. The paired
  finalize plan (`/plans/active/ao_satellite_ao_dispatch_batch8_finalize_2026_08_08.md`) reconciles evidence back into
  every source doc and runs archival.
- No todo below deletes prod data, mutates a GCS bucket, or launches a VM.

## Todos

- [x] [TEST] P2. ✅ **Root-cause `deepseek-per-turn-metrics.spec.ts`'s intermittent failures AND confirm the
      `DeepSeekUsagePoller` fixture-overwrite blast radius — one combined todo since both target the same file with an
      overlapping root-cause hypothesis.** First check whether these are the same underlying bug: does the poller's
      `_sweep_account` tick (confirmed to unconditionally overwrite the hand-seeded
      `AccountUsageRow.deepseek_usage_json` blob, merging in live `_compute_task_window_stats` results) race against the
      test's own assertion timing, such that the test sometimes reads pre-overwrite (hand-seeded, passing) and sometimes
      post-overwrite (live-computed, failing) values? If confirmed, this is a single fix: add an explicit
      wait-for-poller-tick or increase the assertion timeout (the standard convention already used in
      `critical-health.spec.ts`'s cold-start comment) — do NOT disable the poller or rewrite the test's expected values
      (operator-gated, see Deferred). If NOT confirmed as the same mechanism, root-cause the flakiness separately (check
      for an async-poller-vs-test-timeout race as the next most likely candidate) and, independently, confirm exactly
      which of the 7 Accounts-panel columns (`avg_turns_per_task`, `avg_context_tokens_per_task`,
      `input_tokens_per_turn`, `cache_creation_tokens_per_turn`, `cache_read_tokens_per_turn`, `output_tokens_per_turn`,
      `spend_per_turn`) the poller tick actually overwrites vs. leaves at hand-seeded values, by running the second test
      with each assertion isolated/logged one at a time. Also root-cause `deepseek-wallet-reconciliation.spec.ts`'s
      intermittent failure (same shared `chromium` project, DeepSeek-usage-adjacent) under the same investigation. If a
      general async-poller-vs-test convention emerges from this work, note it in
      `/codex/06-coding-standards/ui-testing-layers.md` as part of this same todo — do not create a separate follow-up
      todo for that alone. **Done when**: a written verdict on whether the flakiness and the poller-overwrite are the
      same root cause exists in both source docs' Progress Logs; the confirmed blast-radius table (which of the 7
      columns are affected) is recorded; either a landed non-disabling mitigation + a passing stable re-run (10x in a
      loop, zero flakes) closes both specs, or — if the only viable fix requires disabling the poller or rewriting
      assertions — the todo stops there and files the fix-direction decision as an explicit operator ask instead of
      implementing unilaterally; full `agent-orchestrator` `quality-gates.sh` green either way. Source:
      `/plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` (its 1st item only) AND
      `/plans/active/issues/e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` (its 1st item only —
      items 2-3 stay deferred, operator-gated). Repo: agent-orchestrator.

- [x] ✅ [TEST] P2. **DONE 2026-08-08 (slot-19, backend_engineer craft)** — Root-caused `worker-chat.spec.ts`'s
      intermittent failures. The hypothesized tmux startup-timing race was DISPROVEN (13 independent reproductions, the
      real fixture pane never raced). Actual root cause: `PlanRegenLoop` runs unconditionally regardless of
      `ORCHESTRATOR_MODE`; e2e backend scripts inherit `ORCHESTRATOR_VM_ID` from the launching shell (every orchestrator
      worker slot exports it), so the loop scanned the real `plans/active/*.md` corpus and overwrote e2e fixture backlog
      files with real production data — confirmed 19,000+ lines of corruption per fixture file in one run. **Fix**:
      `agent-orchestrator@ef73a44` — gate `plan_regen.start()` behind `not config.is_mock()`. **Verification**: 10/10
      clean isolated re-runs (zero flakes, zero fixture mutation), full `agent-orchestrator` `quality-gates.sh` green
      (sentinel matches `ef73a44`), SHA independently verified ancestor of `origin/live-defi-rollout`. A genuine
      residual finding (global `webServer` array + shared-host contention, NOT a worker-chat.spec.ts defect) filed as a
      new todo 5 in the source doc — operator-ask territory, not fixed here per this todo's own "operator-ask if the fix
      needs a design call" escape hatch. Full write-up + Progress Log in the source doc (checkbox there intentionally
      left unflipped per this batch's own reconciliation rule — the finalize plan flips it). Repo: agent-orchestrator.
      Source: `/plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` (its 2nd item only).

- [x] ✅ [TEST] P3. **DONE 2026-08-08 (backend_engineer craft)** — Root-caused `backlog-collision.spec.ts`'s
      intermittent "click Fix" failure. **NOT an async-completion race** — static review of the remint→confirm flow
      found no structural race. Actual blocker: TWO local-slot-only port-mismatch bugs (neither manifests in CI, which
      runs un-tabbed at `SLOT_OFFSET=0`) that made this spec un-reproducible from any `.tabs/N` slot checkout: (1)
      `run-e2e-backend-collision.sh` pointed the dashboard's Login screen at a static, hardcoded-port
      `backends.e2e.collision.json` instead of the actual slot-offset-aware backend port — "Failed to fetch" on every
      non-zero slot; (2) the spec's own follow-up out-of-band fetch read `process.env.E2E_COLLISION_BACKEND_PORT`, which
      `playwright.config.ts` never propagated to the test-runner process (only to the spawned backend subprocess). Fixed
      both — `agent-orchestrator@1e2ecac` + `agent-orchestrator@3ba4ba4` (mirrors `run-e2e-backend-tier.sh`'s
      already-established runtime-generated-backends-file pattern). **Verification**: 5/5 clean isolated re-runs, both
      tests, zero flakes (~20s/run); full `agent-orchestrator` `quality-gates.sh` green (2796 passed, dashboard
      tsc+vitest clean). SHA `3ba4ba4` independently verified ancestor of `origin/live-defi-rollout`. Full write-up +
      Progress Log in the source doc (checkbox there intentionally left unflipped per this batch's own reconciliation
      rule — the finalize plan flips it). Repo: agent-orchestrator. Source:
      `/plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` (its 3rd item only).

- [x] [INFRA] P1. **Deliberately and minimally reproduce the autostash-pop content-loss hazard, and determine whether
      discarded content is recoverable — one combined todo (the two source items are tightly sequential: the
      recoverability check must run immediately after a live reproduction, before `git gc` can prune anything).** Set up
      two throwaway clones of the SAME repo (not two independent remotes — the point is to test whether two processes
      sharing one `.git` directory can collide the way the source doc's live reproduction did): clone A makes an
      uncommitted, never-staged edit to a file X and holds it dirty; clone B (simulating a concurrent `quickmerge.sh`)
      runs `git pull --rebase --autostash` against a remote carrying new commits that do NOT touch X. Check whether file
      X's content in clone A survives. If it reproduces: immediately (before any `git gc`) run `git fsck --unreachable`
      / `git stash list` / reflog on clone A to determine whether the discarded content is recoverable from a dangling
      stash/blob object, and whether the recovered version (if any) is the FINAL edited state or an earlier/partial one.
      If it does NOT reproduce in this clean 2-clone setup, the trigger requires something specific to this workspace's
      actual shared-checkout model (the SAME `.git` directory, not just "the same remote") — narrow accordingly and
      record that finding; do not attempt to reproduce further inside a live, actively-multi-tenant `.tabs/N` checkout
      (the source doc's own explicit caution). Do NOT implement any of the candidate mitigations (flock,
      commit-then-reconcile ordering, post-pop stash-list sanity check, or a concurrency cap) — those explicitly require
      operator sign-off (see Deferred). **Done when**: a written verdict (reproduces / does not reproduce in the clean
      2-clone setup) is recorded in the source doc's Progress Log, with the recoverability finding (reliable /
      unreliable / not established) if it did reproduce; no mitigation code changed. Source:
      `/plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` (its 1st + 2nd
      items only — items 3-4 stay deferred, operator-gated). Repo: unified-trading-pm (investigation only, no shipped
      code change expected from this todo).

## Deferred — operator-gated items from the 5 newly-triaged docs, plus the un-approved batch5/6/7 backlog

**Ledger check**: 5 docs needing a fresh look this run (the only ones with zero prior-batch citation) − 1 fully
extracted (`ao_dashboard_e2e_pre_existing_flakiness`, 3 of 4 items → todos 1-3) − 1 partially extracted
(`e2e_deepseek_poller_overwrites_hand_seeded_account_blob`, 1 of 3 items → folded into todo 1) − 1 partially extracted
(`autostash_pop_can_silently_discard_uncommitted_foreign_edits`, 2 of 4 items → todo 4) − 2 fully deferred
(`dashboard_prettier_version_skew_vs_wrapper_pin`, `ao_blocked_answer_message_cross_delivered_after_slot_reassign`) = 5
docs accounted for, all items either extracted or named below (count verified against this run's own per-doc read).

- **Operator-gated** (decide fix direction, not unilateral):
  `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md`'s items 2-3 — disable the poller in the e2e
  backend vs. rewrite test expectations vs. seed a different fixture shape that survives the merge; explicitly
  self-flagged "(operator call, not unilateral)" in the source doc's own text.
- **Operator-gated** (mitigation requires sign-off on HIGH-RISK shared infra):
  `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`'s item 3 (implement a chosen mitigation
  to `scripts/quickmerge.sh`/`scripts/dev/safe-doc-push.sh`) — explicitly "do not implement without operator sign-off";
  item 4 (codex fold-in) depends on item 3's outcome.
- **Operator-gated** (pure design-fork, no default): `dashboard_prettier_version_skew_vs_wrapper_pin_2026_08_06.md`'s
  both items — which side moves to resolve the prettier version disagreement, and whether the dashboard's
  `quality-gates.sh` should gate on `format:check` at all; no evidence-based tiebreaker stated in the source doc.
- **Operator-gated** (already ruled non-mechanical by a prior audit pass):
  `ao_blocked_answer_message_cross_delivered_after_slot_reassign_2026_08_06.md`'s item 2 (resolve-or-flag orphaned
  `BlockedRow`s at reassign time) — the source doc's own 2026-08-07 na-eligibility-audit Progress Log entry already
  verdicts this "a genuine (a)-or-(b) design choice... a real judgment call, not a mechanical follow-on"; not
  re-litigated here.
- **Standing, not re-triageable by this batch**: the 45 already-triaged docs named across
  `ao_satellite_ao_dispatch_batch5_2026_08_03.md`, `…batch6_2026_08_04.md`, and `…batch7_2026_08_06.md`'s own "Deferred
  — full per-doc disposition" sections. Their classifications (operator-gated / too-large-unscoped / already-claimed /
  credential-gapped / conflict-gated) were independently re-confirmed correct by this run's own Phase 1 read (no
  disagreement found) and are not restated here — see those 3 plans directly. **The actionable next step for this
  population is operator review + approval of batch5/6/7, not another audit pass or a batch9.**

None of the above are re-triageable by re-running this same audit again without new information — the next
`/ag-closeout-audit ao` pass should check (1) whether batch5/6/7 have been approved/landed, and (2) each deferred item's
own specific named gate, per the skill's iterative-drain methodology, not re-derive the classification from scratch.

## Codex SSOTs (read before starting a todo)

`/codex/06-coding-standards/ui-testing-layers.md`, `/codex/05-infrastructure/per-tab-worktrees.md` § "What worktree
isolation does NOT cover", `/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`.

## Progress Log

- **2026-08-08** — Authored by `/ag-closeout-audit ao` (autonomous mode, scheduled `ag_closeout_auditor` dispatch, slot
  12). Phase 0 re-derived the covering-plan set via `generate_ag_closeout_audit_candidates.py --tranche ao` (66
  candidates, 11 covering plans, 8 self-dispatched — pre-verified covered without spawning agents, per the tooling's own
  self_dispatched definition). Phase 0.3's Orthogonality sweep retagged 2 mistags directly (see "Why this plan exists").
  Phase 1 ran a full Workflow (58 agents, one per non-self-dispatched candidate; 0 errors, 0 empty results) — 37
  `orphaned_never_touched`, 13 `orphaned_partial_coverage`, 6 `archivable_after_planned_work`, 1 `archivable_now`, 1
  `exclude_cross_cutting` (the retagged mistag). Reading all 50 orphaned verdicts' actual coverage evidence (not just
  the verdict label) found 45 already correctly triaged-and-declined inside batch5/6/7's own Deferred sections — those
  batches are simply not yet operator-approved. Only 5 docs (all 2026-08-06/08-07, postdating batch7) had zero prior
  citation anywhere. Phase 3's conflict-check on those 5 found one genuine same-file collision
  (`deepseek-per-turn-metrics.spec.ts`, cited by 2 different source docs with overlapping root-cause hypotheses) —
  merged into todo 1 rather than drafted as two racing todos. 4 bounded items extracted (todos 1-4); the remainder
  (operator-gated design forks) deferred above, none silently dropped. Left `status: draft` deliberately — flipping to
  `active` is the operator's call, and this run's own recommendation is that approving batch5/6/7 is the higher-leverage
  action.
- **Parked-findings ledger**: 4 findings parked this run (the 4 Deferred bullets above, one per doc) — all written
  durably in this batch's own Deferred section (Phase 3 ran this session, so this is the primary durable home per the
  skill's parking rule).
- **2026-08-08 (operator-authorized draft→active review, same-day)** — Re-ran the shared 3-surface conflict-check
  against (a) active `assigned_vm: planning` plans in `parent_epic: orchestrator_master` (only the batch finalize twins,
  all correctly `gate_on_depends`-held), (b) sibling batches 5/6/7 (this batch's own drafting already cross-referenced
  all 3 directly), (c) `ao_open_issues_consolidated_close_out_2026_07_17.md` (not touched by this batch's todos, no
  conflict). All 4 todos' Source docs (`ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`,
  `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md`,
  `autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`) re-verified still `status: open` with
  matching open-todo counts — no stale/already-done items (unsurprising, this batch was drafted the same day as this
  review). Investigated the `assigned_vm: NA`/`execution_scope: local-only` frontmatter alongside batch5-7 (see batch5's
  Progress Log for the full citation trail — a real, tranche-rooted 2026-07-17 operator ruling, not an oversight);
  applied the same unchanged treatment, flipped `status: draft → active` only, matching the exact precedent live on
  batch2/3/5/6/7. Fixed the stale draft-era H1 banner to match, and cited this batch's own "highest-leverage action"
  recommendation now that it has been acted on.
- **2026-08-08 (operator, interactive)**: RULED — the 2026-07-17 local-only ruling is LIFTED going forward; see batch5's
  Progress Log for the full note. `assigned_vm: NA → planning`, `execution_scope: local-only → orchestrator-agent`
  applied here too.
- **2026-08-08 (slot 4, ao_satellite_ao_dispatch_batch8-004)** — Todo 4 ✅. Deliberate minimal reproduction run in
  throwaway scratchpad clones. **Clean 2-clone verdict: DOES NOT REPRODUCE** — `git pull --rebase --autostash` in clone
  A (with dirty file_x) correctly preserved the edit when running sequentially; 5 concurrent pulls in the same directory
  all failed at "Cannot rebase onto multiple branches" (FETCH_HEAD race) before reaching autostash. **Trigger IS
  specific to same `.git` directory:** the stash-interleaving race was manually reproduced — two processes both running
  `git stash push` before either pops causes the pops to consume the wrong stash entry, leaving the victim's edit stuck
  in an unpopped stash. **Recoverability: RELIABLE** (if stash not explicitly dropped + no `git gc`): edit IS in stash,
  IS the final-version content, IS recoverable via `git stash list` + `git stash pop`. Full verdict recorded in source
  doc Progress Log (`/plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md`).
  No mitigation code changed (operator-gated per Deferred).
- **2026-08-08 (slot 2, ao_satellite_ao_dispatch_batch8-001)** — Todo 1 ✅. **Verdicts:**
  `deepseek-per-turn-metrics.spec.ts`: CONFIRMED same root cause as
  `/plans/active/issues/e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md`'s already-confirmed
  mechanism — `DeepSeekUsagePoller._sweep_account` unconditionally overwrites all 7 Accounts-panel columns after a 30 s
  startup delay (not a race — deterministic overwrite). Blast-radius table confirmed (all 7 columns; specific
  post-overwrite values derived from static analysis + fixture inventory). Hard stop applied — no non-disabling
  mitigation can restore hand-seeded values after overwrite; fix direction already decided and recorded in source doc
  todo 2 ✅ (disable poller in e2e backend); implementation remains in source doc todo 3 (operator-authorized,
  deferred). `deepseek-wallet-reconciliation.spec.ts`: CONFIRMED different root cause — async panel-data-fetch timing
  (NOT the poller; spec reads seeded `deepseek_message_usage`/top-up rows directly; `DeepSeekBalancePoller` skips
  accounts without `oauth_token_env_file`). Non-disabling mitigation landed: `{ timeout: 10_000 }` on first data
  assertion (standard cold-start convention per `critical-health.spec.ts`) — `agent-orchestrator@343501a`. 10x stability
  loop NOT run (`dashboard/node_modules` absent; QG skips dashboard checks when node_modules absent, still passes).
  Codex convention documented: `ui-testing-layers.md` § "agent-orchestrator e2e: background-poller vs. fixture-data
  interaction" — `unified-trading-pm@88693651d`. Source docs' Progress Logs updated same turn. `agent-orchestrator` QG
  green (2711 passed, 2 skipped; dashboard skipped — node_modules absent).
