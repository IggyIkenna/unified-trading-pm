---
doc_type: plan
title: AO satellite AO batch 16 — finalize
summary: >-
  Gated closeout for `ao_satellite_ao_dispatch_batch16_2026_08_09.md` — machine-held via `depends_on` +
  `gate_on_depends` until its sole todo is done. Reconciles verified evidence back into
  `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`'s own checkbox; that source doc is NOT archived here
  since it retains 1 genuinely-gated item (the P3 ghost-host-rows prune/tombstone design call).
status: active
nature: process
asset_group: [ao]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer]
tags: [ao, ao-dispatch, close-out, batch-16, finalize, satellite-extraction]
related:
  [
    /plans/active/ao_satellite_ao_dispatch_batch16_2026_08_09.md,
    /plans/active/issues/git_status_reporter_stale_public_url_token_expiry_2026_07_24.md,
    /plans/active/ao_open_issues_consolidated_close_out_2026_07_17.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
  ]
created: "2026-08-09"
last_updated: "2026-08-09"
parent_epic: infrastructure_master
assigned_vm: planning
execution_scope: orchestrator-agent
priority: P2
estimate_class: infra
estimate_baseline_ai_days: 0.2
estimate_calibrated_ai_days: 0.16
assigned_role: review
effort: medium
drift_direction: advance-code
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: [ao_satellite_ao_dispatch_batch16_2026_08_09]
gate_on_depends: true
sequential: true
context_scope:
  [
    /plans/active/ao_satellite_ao_dispatch_batch16_2026_08_09.md,
    /codex/12-agent-workflow/plan-completion-and-archival-discipline.md,
    /codex/12-agent-workflow/commit-push-flip-rule.md,
  ]
source: >-
  Operator ruling 2026-07-24 (task_template.md §4) — every AO-dispatched plan needs a gated finalize plan. Authored in
  the same turn as its batch, 2026-08-09, per the satellite-batch-extraction pattern's mandatory finalize-twin rule.
---

# AO satellite AO batch 16 — finalize

> **Machine-gated on `/plans/active/ao_satellite_ao_dispatch_batch16_2026_08_09.md`** (`depends_on` +
> `gate_on_depends: true`) — will not dispatch until its sole todo is `done`. The batch itself stays `status: draft`
> until the operator approves it; this finalize plan needs no separate flip either way.

## Todos

- [x] ✅ [REVIEW] P1. **Re-verify batch16's done-claim against reality** — confirm the near-expiry warning actually
      fires exactly once per state-transition against a real (or realistically mocked) near-expiry JWT, does not refire
      on a subsequent unchanged-state tick, and clears/resolves after a re-mint. **Done when**: independently
      reproduced, not just re-reading the shipped test. **Evidence**: confirmed `unified-trading-pm@b427499b33` is a
      real, on-branch commit (`git merge-base --is-ancestor` true against HEAD) matching its claimed diff (88 lines in
      `scripts/dev/slot-git-status-report.sh` + the 192-line `tests/test_slot_git_status_token_expiry.bats`). `bats` was
      not installed on this host (consistent with `pm_bats_tests_never_invoked_by_quality_gates_2026_07_26.md` — the QG
      pipeline never runs `.bats` files); installed bats-core 1.10.0 to a scratch prefix (no sudo, no host-wide change)
      and ran the shipped suite for real: **7/7 pass**. Independently wrote a SEPARATE, freshly-authored repro harness
      (own throwaway HTTP server, own JWTs with different offsets than the shipped test's) that sources the real
      `decode_jwt_exp`/`check_token_expiry_for_slot` functions straight from the shipped script — **13/13 checks pass**:
      fires exactly once on a 2.5-day-out JWT, does not refire across 3 unchanged ticks, clears the marker on re-mint
      with no spurious fire, correctly re-fires on a fresh near-expiry episode after that, plus 2 scenarios the shipped
      suite doesn't cover — exactly-at-the-3-day boundary still fires (confirms the `<=` comparison, not `<`), and an
      ALREADY-EXPIRED token still fires rather than being silently skipped. Also traced `resolve_token_for_slot`
      (line 423) / `post_starve_ping` (line 552) call sites to confirm the test harness's `TOKEN_FILE` env var actually
      is what the shipped code reads (line 65/426) — no name mismatch between test and implementation. Repro harness
      left at `token-expiry-repro/repro.sh` in this reviewer's scratchpad (not committed — throwaway verification
      tooling, not project code).
- [ ] [REVIEW] P0. **Reconcile verified evidence into the source doc's own checkbox** —
      `git_status_reporter_stale_public_url_token_expiry_2026_07_24.md`'s `[INFRA] P2` "Stop the 30-day treadmill" item,
      replacing the redirect-pointer with real completion evidence (commit sha, test name, live-fire confirmation if
      practical). **Done when**: the source checkbox carries real evidence, not a bare pointer.
- [ ] [REVIEW] P1. **Do NOT archive the source doc.** Confirm it still has 1 open item after this extraction (the P3
      ghost-host-rows prune/tombstone design call) and leave it `status: open`.
- [ ] [INFRA] P0. **Run the 6-step archival ritual on the batch plan itself, then regenerate the inventory** — banner
      `/plans/active/ao_satellite_ao_dispatch_batch16_2026_08_09.md`, move to `plans/archive/2026_08/`, fix every
      corpus-wide referrer including this finalize plan's own `related:`/`depends_on:`, then re-run the active-plan
      inventory generator. **Done when**: the batch plan is archived with a banner, the inventory regenerates cleanly,
      and `check_finalize_plan_coverage.py` no longer names this pair.

## Codex SSOTs

`/codex/12-agent-workflow/plan-completion-and-archival-discipline.md`,
`/codex/11-project-management/cross-reference-path-convention.md`, `/codex/12-agent-workflow/commit-push-flip-rule.md`.

## Progress Log

- **2026-08-09** — Authored in the same turn as batch16, per the mandatory finalize-twin rule (task_template.md §4).
  `sequential: true` since the 4 todos are a genuine chain. Ships `status: active` (not `draft`) — `gate_on_depends`
  already machine-holds every task until batch16's own todo is done, matching the batch7-15 finalize precedent.
- **2026-08-10 (review, slot-25)** — Todo 1 done: independently re-verified `b427499b33`'s done-claim rather than
  trusting the shipped test read-only. Installed bats-core locally (not present on host) and ran the real shipped suite
  (7/7 pass), then wrote and ran a second, separately-authored harness against the real shipped functions (13/13 pass,
  incl. 2 boundary cases outside the shipped suite). No discrepancy found — the claim holds. See the checkbox evidence
  above for the full detail. Todo 2 (reconcile evidence into the source doc's own checkbox) is next in this
  `sequential: true` chain.
