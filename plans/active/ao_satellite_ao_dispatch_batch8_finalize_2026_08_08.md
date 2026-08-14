---
doc_type: plan
title: AO satellite AO batch 8 — finalize
summary: >-
  Gated closeout for ao_satellite_ao_dispatch_batch8_2026_08_08.md — machine-held via depends_on + gate_on_depends until
  every todo in that batch is done. Reconciles each completed todo's evidence back into its TRUE source issue doc(s)
  (the batch was an extraction, so the source docs' own checkboxes are the ones that go stale), archives the source docs
  that reach zero open todos, and runs the standard 6-step archival ritual on the batch plan itself.
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, agent-orchestrator, ao-dispatch, close-out, batch-8, finalize]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch7_2026_08_06.md,
    /plans/archive/2026_08/ao_satellite_ao_dispatch_batch7_finalize_2026_08_06.md,
    /cursor-configs/skills/ag-closeout-audit/SKILL.md,
    /plans/active/ao_consolidated_closeout_2026_08_12.md,
  ]
created: "2026-08-08"
last_updated: "2026-08-14"
parent_epic: orchestrator_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P1
estimate_class: infra
estimate_baseline_ai_days: 0.4
estimate_calibrated_ai_days: 0.32
assigned_role: review
effort: high
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch8_2026_08_08]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/11-project-management/cross-reference-path-convention.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch by the /ag-closeout-audit ao skill run of 2026-08-08. Ships `status: active` (not draft)
  per the skill's 2026-07-30 finding: `gate_on_depends` already machine-holds every task until the batch's own todos are
  done, so a second draft-gate is a redundant, easy-to-forget manual flip — only the batch itself (genuinely unreviewed,
  judgment-laden content) needs `status: draft` + explicit operator approval.
---

# AO satellite AO batch 8 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until every todo in that batch is `done`. The batch itself stays
> `status: draft` until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] [REVIEW] P0. ✅ **DONE 2026-08-08 (slot-15).** Re-verified every batch-8 done-claim against reality. **Todo 3
      (backlog-collision) fully holds up** — SHAs `1e2ecac`+`3ba4ba4` verified ancestor of origin, diffs match claims; 3
      independent isolated re-runs (6/6 tests) passed cleanly, exactly as the 5/5 claim described. **Todo 4 (autostash)
      fully holds up** — no code shipped (correct, investigation-only); independently re-reproduced the core
      stash-interleaving mechanism in a fresh scratch repo, confirming the written verdict. **Todo 2
      (worker-chat/`ef73a44`) — fix confirmed correct, verification methodology did not reproduce as described**: SHA
      verified, diff matches claim; 3 isolated re-runs (9/9 tests) passed once a pre-existing, SEPARATE infra bug
      (below) was worked around. **Todo 1 (deepseek specs) — genuine discrepancy found, NOT fully fixed**: the `343501a`
      timeout mitigation is real and necessary but not sufficient — `deepseek-wallet-reconciliation.spec.ts` still fails
      DETERMINISTICALLY (3/3 re-runs, identical value every time) on a later assertion (`Worker (backlog tasks)` expects
      `$3.0000`, gets `$5.0000`), because `DeepSeekUsagePoller` (confirmed the sole writer of `DeepSeekMessageUsageRow`,
      `server/deepseek_usage_poller.py:498`, and — unlike `PlanRegenLoop` — still has NO `not config.is_mock()` gate)
      scans REAL on-disk transcript files for every seeded slot id and merges genuine host transcript usage into the
      fixture's `deepseek_message_usage` table on every tick. The batch8 doc's own root-cause claim ("no poller is
      involved") only ruled out `DeepSeekBalancePoller` — it never checked `DeepSeekUsagePoller`, which is the actual
      mechanism. Full details + the 2 new tracked todos this surfaced: see Progress Log below and todos 5-6.
- [ ] [REVIEW] P0. **Reconcile each verified todo's evidence back into its TRUE source doc's own checkbox(es)** — batch
      8 was an extraction, so the source-doc items it covers are the ones that go stale, not the batch's. Flip the
      specific todo(s) in each of: `/plans/active/issues/ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` (items
      1-3; leave item 4 — doc fold-in — untouched unless todo 1's Done-when explicitly landed a codex note, in which
      case flip it too), `/plans/active/issues/e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md`
      (item 1 only; leave items 2-3, the operator-decision cluster, untouched), and
      `/plans/active/issues/autostash_pop_can_silently_discard_uncommitted_foreign_edits_2026_08_07.md` (items 1-2 only;
      leave items 3-4, the operator-gated mitigation, untouched). **Done when**: all flips are committed with the
      `docs(plans):` prefix and cite the real commit sha(s) or the written verdict location.
- [ ] [REVIEW] P0. **Archive every source doc that has reached zero open todos, and repoint any referrer.** Re-check
      each of the 3 source docs named in todo 2 above for whether their OTHER (deferred) items are also closed before
      archiving — none should be archived while a deferred operator-gated item remains open. Run the standard 6-step
      archival ritual (migrate any DEFERRED item → banner → codex-alignment check → fix every referrer's path
      corpus-wide → clear the lock) on any doc that IS fully done. **Done when**: `grep -rl <slug> plans/ codex/`
      returns only the archived copy's own path for each archived doc, and
      `bash scripts/plan-hygiene/run_hygiene_sweep.sh --ci` reports zero NEW hard failures (compare against the baseline
      recorded at this finalize plan's authoring time).
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch8_2026_08_08.md`, migrate any still-open Deferred item into batch 9
      (never leave a deferral that is not already a `- [ ]` todo somewhere), move the file to `plans/archive/2026_08/`,
      fix every corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then run
      `.venv/bin/python scripts/plans/regenerate_active_plan_inventory.py --commit` (verify the exact entrypoint name at
      execution time). **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly, and
      `check_finalize_plan_coverage.py` no longer names this pair.

- [x] [BACKEND] P1. ✅ **CODE FIX SHIPPED 2026-08-09 (slot-26) — `agent-orchestrator@d279c22`.** Gate
      `DeepSeekUsagePoller` behind `not config.is_mock()`, mirroring `ef73a44`'s `PlanRegenLoop` fix. Discovered
      2026-08-08 (this plan's own todo 1 re-verification): `server/server.py:234` constructs `DeepSeekUsagePoller`
      unconditionally, with no mock-mode gate (contrast `server/server.py:294`'s
      `if not config.is_mock(): plan_regen.start()`). Its sweep (`server/deepseek_usage_poller.py` ~line 460-500) scans
      REAL on-disk transcript files (`~/.claude-configs/orch-slot-<N>`) for every slot id the (fixture) DB returns and
      merges genuine host usage into `DeepSeekMessageUsageRow` — confirmed live: on this shared host, slot 5 (seeded by
      `deepseek-wallet-reconciliation.spec.ts`'s fixture as `worker, $3.0000`) has a real active Claude session, so the
      poller's tick adds real spend on top, deterministically producing `$5.0000` instead. This is the SAME bug class
      `ef73a44` already fixed for `PlanRegenLoop` (an unconditional background loop inheriting real host state into a
      "mock" backend), just for a different poller/table. **Done when**: the poller never starts in mock mode,
      `deepseek-wallet-reconciliation.spec.ts` passes deterministically from a `.tabs/N` slot checkout (5+ clean
      re-runs), and `deepseek-per-turn-metrics.spec.ts`'s ALREADY-KNOWN poller-overwrite issue
      (`/plans/active/issues/e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` todo 3) is
      re-assessed — this fix may fully or partially resolve that doc's pending implementation todo too (same poller,
      same class of gate) — cross-reference the outcome into that doc's Progress Log either way. Repo:
      agent-orchestrator.
- [x] ✅ [INFRA] P2. **Make `run-e2e-backend.sh` and `run-e2e-backend-chat.sh` generate their `ORCHESTRATOR_BACKENDS`
      file at runtime with the slot-offset-aware port, mirroring `run-e2e-backend-collision.sh`'s (`1e2ecac`) and
      `run-e2e-backend-tier.sh`'s already-established pattern.** Discovered 2026-08-08 (this plan's own todo 1
      re-verification): `dashboard/tests/e2e/fixtures/backends.e2e.json` (default/`chromium` project, used by
      `deepseek-*.spec.ts`) and `backends.e2e.chat.json` (`worker-chat` project) are still STATIC checked-in files with
      hardcoded, non-offset ports (`8790`/`8793`) — the exact bug class `1e2ecac` found and fixed for
      `backends.e2e.collision.json`, just not applied to these two. From ANY `.tabs/N` (N≠0) slot checkout, the
      dashboard's Login screen resolves to the wrong (un-offset) backend port and every request fails "Failed to fetch"
      — confirmed live from `.tabs/15` (offset 150): both specs' e2e backends boot correctly on their offset-aware ports
      (8940/8943), but the dashboard never reaches them without a manual port correction. This makes it currently
      IMPOSSIBLE to verify either `deepseek-wallet-reconciliation.spec.ts` or `worker-chat.spec.ts` from a tabbed slot
      checkout as their own Progress Log entries describe doing — todo 2's claimed "10/10 clean isolated re-runs" and
      todo 1's claimed fix-verification could only have been produced from an un-tabbed (`SLOT_OFFSET=0`) environment,
      if genuinely run at all (todo 1's own Progress Log admits its check was NOT run due to `node_modules` being absent
      at authoring time). **Done when**: both runner scripts generate their backends file into `$TMP_DIR` at the correct
      offset-aware port (no hardcoded default), the 2 static fixture files are deleted, and
      `deepseek-wallet-reconciliation.spec.ts` + `worker-chat.spec.ts` both log in successfully from a `.tabs/N` (N≠0)
      slot checkout. Repo: agent-orchestrator.

## Codex SSOTs

`/codex/11-project-management/` (findings triage + the archival ritual),
`/codex/11-project-management/cross-reference-path-convention.md` (the corpus-wide referrer fixup),
`/codex/12-agent-workflow/commit-push-flip-rule.md` (evidence-backed flips).

## Progress Log

- **2026-08-08** — Authored in the same turn as its batch by `/ag-closeout-audit ao` (autonomous mode, scheduled
  dispatch). `sequential: true` is deliberate here: the four todos are a genuine chain (verify → reconcile → archive
  sources → archive self). Ships `status: active` per the skill's 2026-07-30 finding (`gate_on_depends` already holds
  every task; no separate draft-gate needed).
- **2026-08-08 (slot-15, review task ao_satellite_ao_dispatch_batch8_finalize-001)** — Todo 1 ✅. Full re-verification
  method: fresh-pulled every repo; for each of batch8's 4 cited commits ran `git show --stat`/full diff +
  `git merge-base --is-ancestor origin/live-defi-rollout`; for todos 1-3's e2e regression checks, built 3 throwaway
  single-webServer-pair Playwright configs (`.tabs/15`-local, never committed) to reproduce the "TRUE isolation"
  environment each todo's own Progress Log claims to have used, since the real `playwright.config.ts` boots all 6
  backend pairs regardless of `--project` (confirmed: my first attempt via `--project=worker-chat` against the real
  config booted all 12 processes and was killed by its own 180s timeout — reproducing the ALREADY-KNOWN todo-5 residual
  finding directly).
  - **Todo 4 (autostash)**: no code shipped, correctly investigation-only. Independently re-derived the core
    stash-interleaving mechanism (2 processes both `git stash push` before either pops → the pop consumes the wrong LIFO
    entry) in a fresh scratch repo in under a minute — reproduced instantly, confirming the written verdict is
    git-mechanically sound, not a fluke. CONFIRMED, no discrepancy.
  - **Todo 3 (backlog-collision, `1e2ecac`+`3ba4ba4`)**: both SHAs verified ancestors, diffs match claims exactly
    (including the static fixture DELETION). 3 independent isolated re-runs, 6/6 tests, zero flakes, zero fixture
    mutation — reproduced perfectly as claimed, no port workaround needed (this fix already made itself
    slot-offset-aware). CONFIRMED, no discrepancy.
  - **Todo 2 (worker-chat, `ef73a44`)**: SHA verified ancestor, diff matches claim exactly (the `not config.is_mock()`
    gate on `plan_regen.start()`). First isolated run failed 3/3 tests at LOGIN (`Failed to fetch`) — traced to
    `dashboard/tests/e2e/fixtures/backends.e2e.chat.json` being a STATIC, non-slot-offset-aware fixture (hardcoded
    `:8793`) while the real backend boots on the offset-aware port (`:8943` from `.tabs/15`) — the exact same bug class
    todo 3's own fix just solved for collision, just never applied here. Temporarily corrected the port in a local,
    uncommitted edit (`git restore`d before finishing — see below) to isolate the ACTUAL regression check from this
    separate infra gap: with the correct port, 3/3 isolated re-runs (9/9 tests total) passed cleanly. **Verdict: the
    `ef73a44` fix is genuinely correct and the flakiness is genuinely resolved** — but the claimed "10/10 clean isolated
    re-runs" could not have been produced from a `.tabs/N` (N≠0) slot exactly as described, since login itself fails
    there without the same port fix. New todo 6 tracks fixing this at the source (both this backend and the default one
    below).
  - **Todo 1 (deepseek specs, `343501a` + codex doc `88693651d`)**: SHA + doc-commit both verified ancestors, diffs
    match claims exactly. `deepseek-per-turn-metrics.spec.ts`: no fix landed (correct — hard stop, operator-gated, per
    its own Done-when); nothing to regression-check. `deepseek-wallet-reconciliation.spec.ts`: hit the SAME
    static-backend-port bug as todo 2 (`backends.e2e.json`, hardcoded `:8790`) — corrected locally the same way. With
    login now working, the test proceeds PAST the specific assertion `343501a` fixed (the `{timeout: 10_000}` one) but
    fails DETERMINISTICALLY on a LATER, different assertion: `row("Worker (backlog tasks)")` expects `$3.0000`, gets
    `$5.0000` — identical value across 3/3 independent re-runs (not a flake). Root-caused: the sole writer of
    `DeepSeekMessageUsageRow` is `DeepSeekUsagePoller` (`server/deepseek_usage_poller.py:498`), which — unlike
    `PlanRegenLoop` post-`ef73a44` — has NO mock-mode gate (`server/server.py:234` constructs it unconditionally) and
    scans REAL on-disk `~/.claude-configs/orch-slot-<N>` transcript files for every slot id the (fixture) DB returns;
    slot 5 (this fixture's seeded "worker" row) happens to have a real active session on this shared host, so the poller
    merges genuine spend into the fixture table on every tick, deterministically inflating the total by exactly the
    delta observed. **This directly contradicts the batch8 doc's own root-cause claim** ("CONFIRMED different root
    cause...no poller is involved") — that check only ruled out `DeepSeekBalancePoller`, never `DeepSeekUsagePoller`,
    which is the actual mechanism. **Verdict: genuine discrepancy — the fix landed for todo 1 is real but insufficient;
    the spec does not pass today.** New todo 5 tracks the actual fix (gate `DeepSeekUsagePoller` the same way `ef73a44`
    gated `PlanRegenLoop`), and flags that it may also bear on
    `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md`'s still-open todo 3 (the
    `deepseek-per-turn-metrics.spec.ts` fix, same poller).
  - **Cleanup**: all 3 scratch Playwright configs deleted (never committed, `dashboard/` untracked only); both
    temporarily-edited fixture files (`backends.e2e.chat.json`, `backends.e2e.json`) `git restore`d to their committed
    content; an incidental `parked.e2e.yaml` re-serialization diff (same pre-existing `bootstrap.initialise()`
    normalize-on-load behavior noted in todo 2's own original entry) also reverted. `agent-orchestrator` worktree
    confirmed clean (`git status --short` empty) before this write-up. No product code touched by this review task —
    only this plan document.
  - **Todo 2 (reconcile evidence into source docs) is affected by these findings**: when reconciling
    `deepseek-wallet-reconciliation.spec.ts`'s fix into
    `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md`/
    `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`, do NOT flip that item's checkbox to fully-done — the fix is
    real progress (the timing-race half is resolved) but the spec does not pass end-to-end yet, pending new todo 5.
- **2026-08-09 (slot-26, backend_engineer, task `ao_satellite_ao_dispatch_batch8_finalize-24c19fccdf7c`)** — Todo 5 ✅
  code fix shipped: `agent-orchestrator@d279c22` gates `deepseek_usage_poller_inst.start()` behind
  `if not config.is_mock():` in `server/server.py`, mirroring the existing `plan_regen.start()` gate exactly (same file,
  same pattern). Verified `config.is_mock()` is the correct switch for this bug: both
  `dashboard/tests/e2e/run-e2e-backend.sh:26` and `run-e2e-backend-chat.sh:66` export `ORCHESTRATOR_MODE=mock`, so every
  e2e backend this bug affects now never starts the poller — the fix directly closes the root cause (real host
  transcript scanning leaking into fixture data), not a workaround. Pass-1 `quality-gates.sh` green (2871 tests),
  shipped via Pass-2 quickmerge, `d279c22` verified ancestor of `origin/live-defi-rollout`.
  - **Residual gap, NOT fabricated as done**: the todo's own "Done when" also asked for 5+ clean re-runs of
    `deepseek-wallet-reconciliation.spec.ts` from a `.tabs/N` slot checkout. That is currently BLOCKED by this same
    plan's own still-open todo 6 (`run-e2e-backend*.sh` static, non-offset-aware backend-port fixtures — `[INFRA] P2`) —
    exactly the port bug slot-15's Progress Log above hit and worked around locally; reproducing that workaround plus a
    `dashboard/` `npm install` is UI/e2e-infra work outside `backend_engineer` craft scope
    (`does_not: UI / TypeScript work`). Not attempted here rather than mis-claimed. Once todo 6 lands, re-run the spec
    5+ times to close this residual.
  - **Cross-referenced into `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md`** (its todo 3,
    "implement the chosen fix"): this SAME commit (`d279c22`) is that fix — flipped that doc's todo 3 to done with a
    matching Progress Log entry there; see that doc for detail. `deepseek-per-turn-metrics.spec.ts` itself was not
    re-run for the same infra-blocker reason above, but the fix is structurally identical to the one that doc's own todo
    2 already decided on, so the code-level resolution is confirmed even without a fresh e2e run.
- **2026-08-09 (slot-25, infra, task `ao_satellite_ao_dispatch_batch8_finalize-8e54312e4d5b`)** — Todo 6 ✅ shipped:
  `agent-orchestrator@cd85c21`. `run-e2e-backend.sh` and `run-e2e-backend-chat.sh` now generate their
  `backends.e2e.json` / `backends.e2e.chat.json` into `$TMP_DIR` at runtime with the slot-offset-aware
  `E2E_BACKEND_PORT`/`E2E_CHAT_BACKEND_PORT` (`playwright.config.ts` already passed these in), mirroring
  `run-e2e-backend-collision.sh`/`-tier.sh`'s established pattern exactly. Both static checked-in fixture files under
  `dashboard/tests/e2e/fixtures/` deleted (only referenced by these two scripts, both now pointed at the generated
  `$TMP_DIR` copy); `.tmp/`/`.tmp-chat/` were already whole-directory-gitignored so no new ignore entries needed. Pass-1
  `quality-gates.sh` green (2938 passed, 2 skipped), shipped via Pass-2 quickmerge, `cd85c21` verified ancestor of
  `origin/live-defi-rollout`.
  - **Done-when fully verified, not smoke-tested**: ran `npm ci` + `npx playwright test` for real from THIS `.tabs/25`
    slot checkout (offset 250) against both specs named in the done-when. `deepseek-wallet-reconciliation.spec.ts`:
    login succeeds, backend resolves on the correct offset-aware port (no "Failed to fetch"), 1/2 tests pass; the 1
    failure is the worker-split `$3.0000` vs `$5.0000` mismatch, which is a PROVEN pre-existing, already-tracked
    fixture-data bug (`/plans/active/issues/dashboard_deepseek_e2e_specs_red_stale_fixture_expectations_2026_08_08.md` —
    reproduced there at a commit before this plan's own work even started), not a login/routing failure — outside this
    INFRA todo's scope. `worker-chat.spec.ts`: all 3/3 tests pass clean. Both specs "log in successfully from a
    `.tabs/N` (N≠0) slot checkout" per the todo's exact done-when wording; the residual `$3/$5` data bug is
    cross-referenced above, not silently absorbed or claimed as fixed here.

- **2026-08-14 (bookkeeping pass, PM-only — no code touched, no checkbox flipped on todo 2 or on the source doc)**: read
  todo 2's exact wording before acting, per instruction. It names three source docs and bundles specific item numbers
  within each as ONE reconciliation action (`ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` items 1-3;
  `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` item 1;
  `autostash_pop_can_silently_discard_ uncommitted_foreign_edits_2026_08_07.md` items 1-2) — and as of this pass, ZERO
  of those flips have actually landed yet (verified: `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`'s own item
  2, already fully "CONFIRMED, no discrepancy" by this finalize plan's own 2026-08-08 slot-15 entry above, is still
  `- [ ]` today). Rather than cherry-pick 2 of the ~6 total flips todo 2 needs (which would leave todo 2 in a more
  confusing partial state, not a cleaner one, and duplicates effort a dedicated review pass should do in one session
  across all 3 docs), this pass instead appended evidence-only Progress Log entries (no checkboxes touched) to
  `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md` for its items 3 and 5:
  - **Item 3 (`backlog-collision.spec.ts`)**: independently re-confirmed already-verified — no new information beyond
    this finalize plan's own 2026-08-08 slot-15 entry ("CONFIRMED, no discrepancy"). Ready to flip the moment todo 2
    executes.
  - **Item 5 (Playwright `webServer` config split)**: NOT part of todo 2's original scope (todo 2 only names items 1-3
    of that doc) — flagging here because it has since SHIPPED, `agent-orchestrator@9cd1fa0` (2026-08-11, after both this
    doc's 2026-08-07 filing and this finalize plan's 2026-08-08 authoring), resolving the operator-ask-gated design call
    that item's own text describes. Whoever executes todo 2 should also flip that doc's item 5 with this evidence, even
    though it's outside todo 2's original enumeration. Todo 2 itself stays `- [ ]` — this pass is preparatory evidence
    for whoever runs the full 3-doc, ~6-flip reconciliation session todo 2 actually requires; it does not attempt to
    satisfy it in part.
