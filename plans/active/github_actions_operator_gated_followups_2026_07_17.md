---
doc_type: plan
title: GitHub Actions CI cost reduction — operator-gated followups (D2/D3/D4 decisions, verification-pending items)
summary: >-
  Open follow-up work forked from github_actions_ci_cost_reduction_2026_07_15.md per the 2026-07-23 plan line-cap
  remediation triage. Carries every todo from the parent that was still open (9 total): the quickmerge --agent
  sentinel-race P0, STEP 2d assert-not-decorative + the 3-dead-workflow decisions (digest-drift-sweep /
  reconcile-release-tags / cassette-drift-check), the persist-cicd-event ledger read-modify-write race (D2), the
  bare-host bootstrap proof, the billed-notify-cost + QG-fan-out re-measurements, and the two calendar-gated billing
  re-pulls (Phase 5). Also carries the parent's full "Deferred work after 2026-07-17" operator-decision ledger, hard-won
  operational lessons, the semver-agent/release-tagging cost ruling, and "Deferred work after 2026-07-23" — everything
  an operator needs to keep deciding on, minus the fully-completed migration history (now archived at
  github_actions_self_hosted_runner_migration_2026_07_15.md) and the same-day staging-machinery-shutdown audit (forked
  to github_actions_staging_machinery_shutdown_2026_07_24.md).
status: active
nature: process
asset_group: [cross-cutting]
stage: [meta]
repos: [unified-trading-pm]
scope: [engineer, admin]
tags: [ci-cd, github-actions, cost, self-hosted-runner, workflows, spend-reduction, operator-decision]
related:
  [
    /plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md,
    /plans/active/github_actions_staging_machinery_shutdown_2026_07_24.md,
    /plans/archive/issues/plan_line_cap_remediation_2026_07_23.md,
    /plans/archive/issues/quickmerge_agent_sentinel_race_vs_own_rebase_2026_07_16.md,
    /plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md,
    /plans/active/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md,
    /plans/active/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md,
    /plans/active/issues/digest_drift_sweep_silent_noop_github_token_scope_2026_07_16.md,
    /plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md,
  ]
created: "2026-07-24"
last_updated: 2026-07-24
parent_epic: deployment_and_user_management_master
assigned_vm: NA
execution_scope: local-only
priority: P0
estimate_class: infra
estimate_baseline_ai_days: 5
estimate_calibrated_ai_days: 4
assigned_role: infra
locked_by:
locked_since:
supersedes:
superseded_by:
depends_on: []
source:
  - "Split from plans/active/github_actions_ci_cost_reduction_2026_07_15.md per the line-cap remediation triage
    (plans/active/issues/plan_line_cap_remediation_2026_07_23.md, row 13, proposed action 2 of 3): the
    operator-gated-followups extraction (9 open todos + the full deferred-work ledger)."
drift_direction: advance-code
---

# GitHub Actions CI cost reduction — operator-gated followups

> **🟡 ACTIVE — forked 2026-07-24 from `github_actions_ci_cost_reduction_2026_07_15.md`** (line-cap remediation,
> 2026-07-23 triage, row 13 of 30). The parent's self-hosted-runner migration is DONE (37/37 movers, zero-billed) and
> archived verbatim at
> [/plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md](/plans/archive/2026_07/github_actions_self_hosted_runner_migration_2026_07_15.md)
> _(path corrected 2026-07-26: it said `plans/active/…`, which is self-contradictory with "archived" and does not exist
> — the file is in `plans/archive/2026_07/`; verified 0 open / 30 done todos there)_. This doc carries everything from
> the parent that is **still open** — 9 todos, plus the full "Deferred work" operator-decision ledger, hard-won
> operational lessons, and the two calendar-gated billing re-pulls. Content below is moved **verbatim** from the parent
> — nothing summarized or rewritten. The same-day staging-machinery-shutdown audit (Phase 6 + its two related Progress
> Log findings) is a distinct topic and lives in `plans/active/github_actions_staging_machinery_shutdown_2026_07_24.md`.

## Open todos forked from the parent plan (verbatim)

> The 9 items below are every open (unchecked) checkbox from the parent plan, moved verbatim in their original order.
> Each item's own text already carries its full context (evidence, SSOT issue-doc pointers, operator asks) — nothing was
> reworded.

- [ ] [INFRA] P0. **`quickmerge.sh --agent` sentinel races its OWN rebase — WRITTEN UP, operator will fix later.** Full
      analysis (mechanism, line refs, repro, 3 candidate fixes + the negative test that must keep passing) lives in
      **`plans/archive/issues/quickmerge_agent_sentinel_race_vs_own_rebase_2026_07_16.md`** — that doc is the SSOT; do
      not re-analyse it here. One-line essence: STAGE 0.4 rebases your local commits (new SHAs), then STAGE 3 demands
      the `.qg_last_passed_sha` sentinel be `==` HEAD or an ANCESTOR of it — which a rebase of your own commits makes
      impossible, so on a busy LDR `--agent` can never validate a sentinel it just wrote. **Working practice until
      fixed:** chain `quality-gates.sh --no-fix && quickmerge.sh …` in ONE shell (narrows the window; does not close
      it). Operator 2026-07-16: "we will also fix the issues with quickmerge --agent" — UNACKED, no plan owns it yet.

- [ ] [INFRA] P0. **STEP 2d — assert-not-decorative on the mover set (NEW, from this plan's own audit 2026-07-17).** **3
      of the 37 movers were long-dead silent no-ops** — `digest-drift-sweep` (never worked), `reconcile-release-tags`
      (dead since D13), `cassette-drift-check` (dead ~4 months, 52 false issues). **~8% of the audited surface was
      decorative, and NONE of it was caused by the flip** — the flip is simply what made someone read the logs. All
      three are BACKSTOPS whose healthy output and dead output are the SAME STRING (`Dispatched: 0` / `created 0 tag(s)`
      / a green job that never ran its check). **The cheapest workflow is one that does not run**:
      `reconcile-release-tags` alone burns ~48 no-op runs/day, so deleting dead glue beats moving it. Deliverable: a
      cheap recurring check that a mover's "did work" counter is not 0 on EVERY run for N days (and that "I did nothing"
      and "I could not look" are DIFFERENT exit states — the one-line assertion that would have caught all three on day
      one). Generalises `/codex/02-data/honest-absence-downstream-handling.md` from data to automation.
- [ ] ⛔ [INFRA] P0. **SUPERSEDED 2026-07-26 — DO NOT EXECUTE THIS DELETION.** ~~DELETE `reconcile-release-tags`~~ The
      script was **repurposed, not deleted**: `unified-trading-pm@6c4ee4d0c` (2026-07-23, verified ancestor of
      `origin/live-defi-rollout`) split it into two populations — tag-derived repos are **hard-refused for minting** and
      instead checked for the real invariant ("`main` must not accumulate commits past the newest `v*` tag" ⇒ STALL). It
      is now the fleet's **release-stall alarm**, and deleting it would remove the only detector for the 4-week
      fleet-wide tagging outage that motivated this todo. Codex has ruled: `/codex/08-workflows/ci-cd-flow.md:1004` §
      _"Release tag reconciler — a STALL DETECTOR, not the minter (corrected 2026-07-25)"_; CLAUDE.md carries the
      matching one-liner. The live minter is `semver-agent` on `push:[main]` (`unified-trading-pm@0b128a725`,
      ancestor-verified; fleet-rolled to 22 repos per
      [/plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md](/plans/active/cicd_mvp_ldr_to_main_pipeline_2026_06_30.md)
      § Phase 4). Left **unticked deliberately** — the deletion must not happen, and retiring vs rewriting this todo is
      a planning call parked for the operator. SSOT:
      [/plans/active/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md](/plans/active/issues/reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17.md)
      (banner at top).
- [ ] [REVIEW] P0. **OPERATOR DECISIONS on cassette-drift-check (fixed + flipped 2026-07-17, but two calls are yours).**
      (a) **Close the 52 open false `[Cassette Drift]` issues** in `unified-api-contracts` (each self-refuting: "Total
      cassettes checked: 0 / Drifted: 0 / No report file found" under a "Drift Detected" title). (b) **The 02:00 cron
      now opens a REAL 28-item issue** — but per FINDING #4 the detector's cassette→model matching is a lottery
      (filename stem only, venue discarded, substring match over 2172 models; 15 of the 28 are generic stems), so the
      report is part real drift, part artifact. Fixing it is a UAC change + a design call (should `bitget/ticker.yaml`
      validate against a venue-specific model or the canonical one?). **Ikenna owns the cassette-count verification
      (operator 2026-07-17) — do not duplicate it.** SSOT:
      `plans/active/issues/cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17.md`.

- [ ] [REVIEW] P0. **OPERATOR CALL (D2) — the CI/CD event ledger loses rows; decide fix-vs-accept (NEW 2026-07-17).**
      `persist-cicd-event` appends by downloading the whole `events.jsonl`, appending a line, and re-uploading — an
      unlocked read-modify-write on ONE object per repo per day. Overlapping writers silently discard each other's rows,
      and **every writer still logs `Persisted event to gs://…` and exits 0**, so the loss is invisible (the same
      healthy-output-equals-dead-output shape as the other three findings). ~20 PM callers share a single object;
      `ci-status-update` is 14,320 runs/30d. **The loss RATE is NOT measured** — code-read + argument only; the issue
      doc says how to measure it. **The blocking question is WHO READS THIS LEDGER** (the schema claims
      `GitHubWorkflowEvent` from `unified_api_contracts.internal`, implying a real consumer) — that decides whether
      one-object-per-event is free or expensive. **Raised with the operator twice in-session, unanswered — do not
      re-derive it, the analysis is complete.** STEP 2c reproduces the behaviour faithfully and deliberately (fixing it
      inside a cost refactor would bundle a silent behaviour change into a diff 22 workflows depend on). SSOT:
      `plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md`.

- [ ] [VERIFY] P0. **PROVE the bootstrap on a bare host** — ⏳ **PARTIAL** (unified-trading-pm@80f00684a). ✅
      **Container leg DONE**: bare `ubuntu:24.04` → EXIT=0, all 10 tools resolve; found + fixed the `sudo` assumption.
      Reproduce:
      `docker run --rm -v "$PWD/bootstrap-ci-host.sh:/b.sh:ro" ubuntu:24.04 bash -c 'useradd -m -s /bin/bash ubuntu; bash /b.sh'`.
      ❌ **STILL UNPROVEN — a container structurally cannot exercise these:** IMDS / EC2 instance role · GCP ADC
      (interactive; STEP 2b's trim depends on runner-user ADC) · **systemd — so `setup-glue-runners.sh install` (units,
      slice, refresh timer) is UNTESTED end-to-end** · actual runner registration against GitHub. **Do NOT tick this off
      the container pass**; it closes only when a real bare VM runs it. The upcoming planning-VM deploy proves the
      systemd/registration legs; the bare-VM leg stays open until we genuinely rebuild a host.

- [ ] [VERIFY] P0. **Use `scripts/cicd/measure-billed-notify-cost.sh`** (promoted out of a scratchpad 2026-07-16 — it is
      what produced this plan's notify-slack numbers, and the measurement took THREE attempts to get right: skipped jobs
      are not billed, and a throttled API call silently counts as 0). After 3–5 days, re-measure PM's billed minutes
      (ledger); confirm the moved workflows bill ~$0 and the VM absorbed the load without contention (slice
      `MemoryCurrent` < 8G, orchestrator load unaffected).

- [ ] [VERIFY] P0. Re-measure a representative QG run's billed job-minutes + the docs-PR / identical-tree skip rates
      before/after (ledger + run counts).

### Phase 5 — Prove the savings

- [ ] [VERIFY] P0. Two weeks after rollout, re-pull the billing ledger and compare to the Phase-0 baseline; record
      actual $/mo saved per repo. Target landing: **fleet ~$1,000/mo → ~$300–400/mo**, and structurally flat when
      activity grows (glue cost stays on our VM; only real test minutes scale). **1-week interim pull done 2026-07-23**
      (Progress Log below): PM itself is down 35–56% depending on baseline (real, on-target direction) but the fleet
      total is NOT down yet — masked by a +47% rise in non-PM repos this migration never touched. Re-check both threads
      at the 2-week mark, not just the fleet aggregate.

---

## Deferred work after 2026-07-17

STEP 2 is **DONE (37/37 movers on the pool, zero-billed, verified)**. Everything below is what remains, why it is not
done, and what the next session should NOT re-derive.

**STEP 2c is COMPLETE (`a6057ea36` converted → observed green on main → `0c845f930` deleted, 2026-07-17).** The persist
minute-minimum is gone from all 22 callers (~$117/mo); `ci-status-update` measured `billable: {}` end-to-end on main
(runs 29579499315, 29579977224). Finding ②'s rule still governs any FUTURE edit of `action.yml`: _edit the manifest →
prove on ONE caller → only then fan out._

### ⛔ OPERATOR DECISIONS — 4 open, nothing below them moves without these

| ID     | Decision                                                                            | Recommendation + why                                                                                                                                                                                                             |
| ------ | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **D1** | ✅ **DECIDED 2026-07-17** — operator delegated; checkout kept, `@main` pin rejected | Finding ② made pre-main testability non-negotiable; ~1s sparse checkout on our own runner = $0. Rollout executed same day (`a6057ea36`); STEP 2b's no-checkout clause amended to sparse-checkout.                                |
| **D2** | **Event ledger loses rows** — fix vs accept                                         | **Find the consumer first**, then one-object-per-event. Raised twice in-session, unanswered. Full analysis filed; do NOT re-derive. SSOT: `plans/archive/issues/persist_cicd_event_ledger_read_modify_write_race_2026_07_17.md`. |
| **D3** | **The 3 dead workflows** — operator wants to review first (2026-07-17)              | **HELD, nothing done**: delete `reconcile-release-tags`, fix `digest-drift-sweep`, and **STEP 2d is held too** (its design depends on what you decide about those three).                                                        |
| **D4** | **Cassette follow-ups** — close 52 false issues? fix the UAC matching?              | **Ikenna owns the 179/28 count verification** (operator 2026-07-17) — do not duplicate. The workflow itself is already fixed + flipped.                                                                                          |

### Not done — blocked on nobody, real work

| #   | Item                                                                                | State                                                                                                                                                                                                                                                                                                                                                                                                                              |
| --- | ----------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | ~~A2 — content-gate dedup~~                                                         | ✅ **SHIPPED + PROVEN 2026-07-17** — see the A2 todo's evidence block (c535ec087; alerting-service runs 29584946980 MISS+save / 29585163847 22s HIT+skip). [A2 todo now archived in `github_actions_self_hosted_runner_migration_2026_07_15.md`.]                                                                                                                                                                                  |
| 2   | ~~A1 — docs-only fast-path~~                                                        | ✅ **SHIPPED 2026-07-17** — see the A1 todo's evidence block (e5b22fddc, PR #1124; fleet template rollout deferred to batch with A5). [A1 todo now archived in `github_actions_self_hosted_runner_migration_2026_07_15.md`.]                                                                                                                                                                                                       |
| 3   | ~~A5 — collapse the QG fan-out~~                                                    | ✅ **DONE 2026-07-17** — measured 23 repos then collapsed to `[tests, checks]` (1bb13bfb2, PR #1126; live proof in its own run).                                                                                                                                                                                                                                                                                                   |
| 4   | ~~Security-posture codex doc~~                                                      | ✅ **DONE 2026-07-17** — `/codex/07-security/self-hosted-runner-security-posture.md`.                                                                                                                                                                                                                                                                                                                                              |
| 5   | ~~Cron cadence · debounce~~                                                         | ✅ **DONE 2026-07-17** — 5 health/backstop crons hourly (3 are HOSTED watchers = real $); debounce CLOSED not-worth-it (warm slot ~2-5s @ $0; CAS risk).                                                                                                                                                                                                                                                                           |
| 13  | Clean up the 91 pre-existing broken doc references in `doc_reference_baseline.yaml` | **NEW 2026-07-22, P3, nobody's blocking it, just not prioritized.** Real dead links (mostly `related:`/`referenced_by:` pointing at docs that were renamed or never existed at the stated path), NOT the routine archived-plan noise (that's already discounted). Fix a batch, re-run `python3 scripts/plan-hygiene/check_frontmatter_schema.py --update-doc-ref-baseline`, commit the shrunk baseline — never hand-edit the YAML. |

### Cannot be done yet — waiting, NOT neglected

| #   | Item                                                           | Blocked on                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| --- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 6   | Re-measure billed minutes (`measure-billed-notify-cost.sh`)    | the calendar — the flip landed **2026-07-17**; needs 3-5 days ⇒ earliest **~2026-07-20/22**. Nothing to measure yet.                                                                                                                                                                                                                                                                                                                                                                              |
| 7   | Two-week billing-ledger comparison vs the Phase-0 baseline     | the calendar — earliest **~2026-07-31**.                                                                                                                                                                                                                                                                                                                                                                                                                                                          |
| 8   | **Bootstrap on a bare host** (`PARTIAL`)                       | a genuine VM rebuild — systemd / IMDS / GCP ADC / runner registration **structurally cannot** run in a container.                                                                                                                                                                                                                                                                                                                                                                                 |
| 14  | **Verify `ldr-docs-gate`'s hourly `schedule:` actually fires** | the LDR→main auto-promote cycle (`*/15`, v2-gated) picking up `unified-trading-pm@51ce7c394` onto `main` — `schedule:` resolves against the DEFAULT branch's workflow file, which didn't have this fix as of 2026-07-22 session end. Check `gh run list -R IggyIkenna/unified-trading-pm --workflow=ldr-docs-gate.yml` for a `schedule`-triggered run once promotion lands; if none appears within a few hours of promotion, something else is wrong (don't assume "still waiting" indefinitely). |

### Operator-owned — do not start

| #   | Item                                       | Note                                                                                                                                                                                          |
| --- | ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 9   | `quickmerge.sh --agent` sentinel race      | P1, written up; operator will fix later. Workaround: chain `quality-gates.sh --no-fix && quickmerge.sh` in ONE shell.                                                                         |
| 10  | MTDS promote PR #601 blocked on QG failure | From the 2026-07-17 #ci-failures triage (operator: "we will take care of the … repos later"). Real, current, NOT this plan's: market-tick-data-service's own QG fails on its promote path.    |
| 11  | `deployment-api` Cloud Builds failing      | Same triage: 3+ failures/24h (e.g. build `8b581721` at `deployment-api@8c7811f`). Recurring, outside this plan.                                                                               |
| 12  | `branch-health` PROMOTION-LAG alert noise  | ~24 of 79 #ci-failures messages/24h are this one warning re-firing; a genuinely stuck `system-integration-tests` LDR→main (~4 days) hides inside it. Overlaps the Phase-3 cadence/alert todo. |

### Findings parked for later — do NOT re-investigate, they are fully written up

| Issue doc                                                              | One-line verdict                                                                                                                                                                                                                                                     |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `digest_drift_sweep_silent_noop_github_token_scope_2026_07_16`         | Never worked (PM-scoped token). Fixing it dispatches to **15 of 16 repos** — measured, re-runnable via `scripts/propagation/simulate-digest-drift-sweep.sh`. **The 15 is a SYMPTOM: the primary cascade has also been dormant since 2026-06-28.** Answer that first. |
| `reconcile_release_tags_dead_since_d13_git_tag_migration_2026_07_17`   | **DELETE, do not fix.** The earlier "re-source from the manifest" idea was wrong and would have made it confidently wrong instead of harmlessly dead.                                                                                                                |
| `d13_orphaned_version_readers_and_manifest_drift_2026_07_17`           | D13 migrated SOME version-readers. `sync-manifest-versions.py` still reads the deleted field; `versions{}` lags the tags for 9/24 repos; `assert_version_coherence.py` exits 1 with 24 violations while QG passes EXIT=0.                                            |
| `cassette_drift_check_calls_deleted_script_and_swallows_it_2026_07_17` | **FIXED + FLIPPED.** Residual: the UAC detector's model-matching is a lottery (finding #4) + 52 false issues to close (finding #5).                                                                                                                                  |
| `persist_cicd_event_ledger_read_modify_write_race_2026_07_17`          | **NEW (D2).** The event ledger is written with an unlocked read-modify-write ⇒ concurrent writers silently drop each other's rows, and every writer reports success. **Loss rate NOT measured** (the doc says how). Find the CONSUMER before choosing a fix.         |

### Hard-won context the next session should inherit rather than rediscover

- **Evidence shape**: a run-level `runner_name` is MEANINGLESS for a cross-boundary workflow — a glue job + a hosted
  KEEP-D/MOVE-C job in one run is BY DESIGN. **Always read per-JOB.** (I truncated that column once and was ~1 minute
  from reporting "5 workflows silently failed to move".)
- **Billing**: `/timing.billable.total_ms` **UNDER-REPORTS — it returns 0 for jobs that plainly ran.** GitHub bills a
  **1-minute minimum PER JOB**, so COUNT JOBS, never ms. `billable: {}` (no UBUNTU key at all) is the real zero.
- **Never `2>/dev/null` a measurement.** `gh api` has no `--arg` flag; swallowing that error rendered a broken query as
  a clean "0 runs overnight" — the literal `curl -sf || echo ""` bug this plan documented, committed by me a day later.
  Also: `gh api --paginate --jq '[...]'` emits **one array PER PAGE**, so `jq length` counts only the first.
- **Cron delivery measured ~80-90%**, NOT the ~37% in CLAUDE.md's throttle note (hourly crons landed 9/10; `*/30` landed
  16/20). Re-check that figure before tuning any cooldown to it.
- **The security invariant is the TRIGGER AUDIT, not the private flag** — visibility is a settings toggle; "no
  self-hosted workflow carries a `pull_request` trigger" is a property of the workflows and survives it. Re-run it
  before adding such a trigger to any self-hosted workflow. **It is one command — a rule with no command is a rule that
  gets skipped, so here it is** (expect ZERO output; any line is a workflow that would run PR-authored code on our VM):
  ```bash
  grep -lE '^\s*runs-on: \[self-hosted' .github/workflows/*.yml \
    | xargs grep -lE '^\s*(pull_request|pull_request_target):'
  ```
- **A composite action gets NOTHING ambient from the repo — only what the caller explicitly hands it.** GitHub withholds
  **both `secrets` and `vars`** so an untrusted third-party action cannot read org/repo values without an explicit
  opt-in. The docs state the `secrets` half and are SILENT on `vars`; the silence is not permission.
  `actions/runner#2551`.
- **Composite-action manifest errors are NOT containable.** Validation happens at LOAD, before any step runs, so
  `continue-on-error` on every step buys you nothing — a bad `action.yml` fails the CALLER's real job. With 22 callers
  that is 22 simultaneous failures. **Edit the manifest → prove on ONE caller → only then fan out.**
- **MEASUREMENT TRAPS hit this session (same family as the `--arg`/`2>/dev/null` ones above):**
  - **A compound background command reports the LAST command's exit code, not your tool's.**
    `qg.sh > log; echo "EXIT=$?"; tail log` → the harness reported **exit 0** for `tail` while QG's real status was in
    the log. Always print and read an explicit `EXIT=` marker.
  - **The Bash tool's own ceiling is 10 min (600000ms max).** Wrapping a longer job in `timeout 900` does NOT help — the
    harness SIGKILLs it first and you get a bare **137** that looks like OOM. PM's full QG exceeds 10 min ⇒ it MUST run
    `run_in_background`. (Checked: 69 GB free, no competing QG — it was never resource pressure.)
  - **`grep -rl 'self-hosted, glue'` counts your own COMMENTS.** The flip comment contains both `glue-writer` and
    `runs-on: ubuntu-latest` as literal strings, so file counts came out 37/22 and did not reconcile against 56. Anchor
    to `^\s*runs-on:` or you are measuring your own prose.
  - **A hand-wavy doc summary is an INFERENCE.** When you ask for a verbatim quote and get prose ("X appears in multiple
    keys that…"), you did not get an answer. **Search the error string first** — it is faster and it is ground truth.
- **Reading Slack directly**: `scripts/dev/slack-read-channel.py [channel] [hours]` (operator-directed 2026-07-17; auth
  = Secret Manager `SLACK_ALERTS_READER_BOT_TOKEN`, resolved in-process, never on disk). Trap it encodes: carrier posts
  keep the real content in Block Kit `blocks` — the `text` field is only the ":x: CRITICAL — <workflow>" headline, so
  grepping `text` tells you nothing about WHAT failed.
- **Session working-state (2026-07-17, slot 1)**: STEP 2c/2b work was done in a git WORKTREE of the slot-1 clone at the
  session scratchpad (`git worktree list` in `.tabs/1/unified-trading-pm` shows it; local branch `tmp/step2c-rollout`,
  fully pushed). If the scratchpad is gone, clean the stale registration with `git worktree prune` +
  `git branch -D tmp/step2c-rollout` — everything it held is on `origin/live-defi-rollout`. The worktree pattern itself
  is the documented way to work while the slot clone carries someone's live WIP.
- **5-day post-migration system check (2026-07-22)** — operator asked "is everything working, did anything break due to
  our migration?". Findings, evidence-first via `gh run list`/`gh api .../jobs`/`.../logs` (not Slack — this session's
  gcloud ADC needed an interactive reauth this tool couldn't do, so live Slack alert-volume re-verification was skipped;
  GH Actions run data is authoritative and sufficient on its own):
  - **`ldr-docs-gate` (shipped 2026-07-17 as the frontmatter backstop) had NEVER completed a single run** — 39/40
    sampled runs over 5 days show `cancelled`, 0 ever reached a verdict. Root cause:
    `concurrency: cancel-in-progress: true` on a static group name, racing against LDR's real push cadence (a new
    doc/plan push lands every few minutes fleet-wide, faster than this sub-minute check finishes) — every run got
    pre-empted by the next push before it could report anything. The backstop has been silently inert this whole time.
    **FIXED live this session**: `cancel-in-progress: false` (queue instead of cancel — self-hosted + sub-minute jobs
    make queuing free) → `unified-trading-pm@efdeb6f41`.
  - **CORRECTION #2 (real root cause, found only after the operator pushed back on my "resource limitation" theory
    2026-07-22 — that theory was WRONG, and the pushback was right)**: after the concurrency fix, runs were STILL 100%
    cancelled/stuck-queued (total population re-checked via `gh api .../runs?per_page=1` → `total_count: 1200`, not the
    40 I'd sampled earlier via a capped `--limit`; 1198 cancelled, 0 succeeded, 0 failed, ever — cross-checked against
    1402 real commits touching `plans/`/`codex/` in the same window, so the trigger itself was firing correctly). I
    first blamed shared self-hosted runner-pool CPU contention. Measured locally: the check itself runs in **2.04s** for
    the full 1670-doc corpus — nowhere near slow enough to explain a 90+-minute queue wait, and other `glue`-pool
    workflows (`cloud-build-router`, `change-freeze-check`, etc.) were completing in seconds in the EXACT same window a
    `ldr-docs-gate` job sat queued with `runner_name:""` — ruling out pool saturation outright (a saturated pool would
    starve everything, not one specific workflow). The actual cause: `runs-on: [self-hosted, Linux, X64, glue]` requires
    4 labels, but `scripts/self-hosted-runners/glue-runner-run.sh:190` registers every JIT-ephemeral runner in this pool
    with only `["self-hosted","glue"]` — no `Linux`/`X64` ever advertised. Label matching is a strict subset test, so a
    job needing all 4 can **never** match any runner in the pool — not eventually, structurally never.
    `ldr-docs-gate.yml` was the ONLY one of 36 workflows using this pool that specified the 4-label form; the other 35
    all correctly use the 2-label form matching the actual registration. **FIXED**: `runs-on: [self-hosted, glue]` →
    `unified-trading-pm@078c85dc3`. This is the REAL fix; the earlier concurrency change was necessary (a run that DID
    match a runner would otherwise still get killed by the next push) but was not sufficient on its own, and my "fixed"
    claim in the entry above was premature.
  - **LIVE PROOF (2026-07-22, same session)**: the very next `plans/**` push (this commit) triggered run `29910893758` —
    but it stayed `pending` with no job created, because the DEAD run from 08:36 (`29904643698`, created under the
    pre-fix 4-label config, which could never match a runner) was still sitting unresolved in the concurrency group and
    — since it was never cancelled by any of the ~15 pushes since — was silently jamming the whole queue behind it.
    Manually cancelled it (`gh api -X POST .../runs/29904643698/cancel`); the queue immediately unblocked and
    `29910893758` ran and completed in **12 seconds** (10:11:57→10:12:09) on `glue-ip-172-31-5-118-5`, conclusion
    `success`, `notify-broken-docs` correctly `skipped` (green verdict). First real completion in this workflow's 5-day
    existence. Three bugs total, now all fixed: (1) `cancel-in-progress:true` killing in-flight runs (`efdeb6f41`), (2)
    the labels mismatch preventing any match at all (`078c85dc3`), (3) an unresolvable zombie run parked in the
    concurrency queue with nothing to clear it (manually cancelled, no code fix needed — a genuinely dead run just needs
    cancelling once; it can't recur since (2) means no future run can get stuck the same way).
  - **Operator's 4 follow-on improvements (2026-07-22, now unblocked — the gate is confirmed working)**: (1) switch
    trigger from per-push (~240/day measured) to an hourly cron — per-push was never the right model for a check whose
    failure mode (a broken doc sitting undetected a bit longer) is low-consequence; (2) scope
    `check_frontmatter_schema.py` to just the changed files (`git diff --name-only`) instead of the bare/full-corpus
    call — the script already supports `[file ...]` args, `ldr-docs-gate.yml` just never used them; (3) add an
    existence-only check for frontmatter-referenced doc paths (`related`/`supersedes`/`parent_epic`) — confirmed via
    reading `docspec.py` that NO such check exists today (`related`-type fields are untyped `"free_list"`, never
    resolved against the filesystem); (4) Slack alert + optional AO-escalator dispatch on red, same as today just on the
    new cadence. None of these implemented yet — correctly gated on proving the actual fix works first.
  - **CORRECTION (caught when the operator asked "what is this test and should we bump it to 2s?")**: I initially
    reported UTL's `test_manifest_completeness.py::TestF1PerfGuard` (a perf-guard on `compute_completeness_fraction()`,
    added alongside the 16.7x `80d2497e` filter-then-build/memoize optimization, asserting a 1.2M-row completeness
    lookup stays fast so a revert to the old O(n) full-scan gets caught) as a **still-open** regression needing an
    operator decision on its budget. That was wrong — I hadn't checked failure timestamps against the fix's landing
    time. **It was already fixed by another agent BEFORE this system check started**: `unified-trading-library@9081e51c`
    (authored 2026-07-21T02:09:30Z, already on `live-defi-rollout`) bumped the budget 0.5s → **3.0s** for exactly this
    reason (docstring cites the same shared-host contention: "consistently measured 0.57–0.70s… ~4× headroom over the
    worst observed CI time… a revert… exceeds it by 3.5×"). Re-checked all 9 "F1 build" failures in the original sample
    — **every one is dated 2026-07-20T19:26Z–2026-07-21T01:35Z, i.e. before the 02:09Z fix**; every UTL failure _after_
    the fix (6 of them, through 2026-07-21T23:20Z) was the unrelated pip-audit/CVE issue, not F1PerfGuard; and the last
    15 UTL runs (through 2026-07-22T07:49Z) are all green. **Zero recurrences since the fix landed — already resolved,
    no operator decision needed, do not re-open or lower the budget.**
  - **Coincidental, NOT migration-caused, already fixed by others**: instruments-service's
    `TestWriteVenueCanonicalPartition` tests hit `pytest_socket.SocketConnectBlockedError` on `169.254.169.254` for a
    few hours today. Traced (via a dedicated sub-agent, `instruments-service` git history) to a same-day refactor
    (`a9be6ce9`, 03:20 UTC) that changed `_write_venue` to build its own real `get_data_sink()` instead of using the
    test's mocked sink, without updating the test's mocks — would have failed identically on a GitHub-hosted runner
    (pytest-socket's `--allow-hosts` is the same either way). Two slots raced a fix within ~50 min
    (`4ca56889`/`14a1548f`, reconciled `a74e0c46`); HEAD is clean.
  - **Real, currently-live, fleet-wide, but NOT migration-caused**: a freshly-disclosed CVE pair in `pyasn1==0.6.3`
    (CVE-2026-59885, CVE-2026-59886) is failing the pip-audit gate (part of the merged `checks` leg / Codex compliance)
    on every repo that depends on it — confirmed red on unified-trading-library, features-service, and alerting-service
    (instruments-service likely too). This predates and is unrelated to the CI-cost work; it needs a version bump/pin or
    a documented waiver. Not actioned here (out of this plan's scope) — flagged to the operator.
  - **Everything else sampled** (instruments-service hardcoded-test-project-ID / function-size / DeFi-citation-baseline
    / UAC-adapter-registration-drift failures; the single `Escalate to Orchestrator` failure on a
    `gh pr edit --add-label` call hitting GitHub's deprecated `projectCards` GraphQL field) is pre-existing/organic
    fleet churn, unrelated to A1/A2/A5/STEP2b/notify-slack/prek/cron-cadence — each caught correctly by gates that were
    unchanged by this plan's work.
  - **Verdict for the operator**: the CI-cost-reduction changes themselves (A1/A2/A5/STEP2b/alert-dedup/cron-cadence)
    are running clean — PM's own `quality-gates-v2` is 157 success / 12 failure / 31 cancelled (cancelled =
    concurrency-superseded, benign) over 5 days, and none of the fleet failures trace back to those specific changes.
    The one thing that WAS broken because of this plan's work (`ldr-docs-gate`) took two fix attempts — see the two
    CORRECTION entries above — and is now fixed pending live confirmation on the next real doc push. The F1PerfGuard
    finding above was itself later corrected too: it turned out to already be fixed by another agent before this check
    started, not an open regression.
- **`ldr-docs-gate` 4 operator-suggested improvements — SHIPPED 2026-07-22** (`unified-trading-pm@0349d1d15` +
  `51ce7c394`, same session as the LIVE PROOF above):
  1. Trigger switched `push` → `schedule: "0 * * * *"` + `workflow_dispatch` — cuts this workflow's own contribution to
     shared glue-runner load from ~240/day to 24/day.
  2. Full-corpus scan (not diff-since-last-push) KEPT deliberately — measured 2.04s for the whole 1670-doc corpus, so
     scoping buys negligible performance and doesn't map cleanly onto a periodic model anyway. What per-push attribution
     gave is recovered via a per-violating-file `git log -1` lookup instead — MORE precise than `head_commit` once
     hourly batching means several commits land between checks.
  3. New `docspec.validate_doc_references()`: existence-only check for frontmatter fields that reference other docs by
     relative path (`related`, `codex_ssots`, `supersedes`, `depends_on`, etc.), skipping bare slugs/prose by design
     (only entries containing `/` and ending `.md`/`.mdc`, no whitespace). Measured against the live corpus: 336 raw
     hits → 244 were references to a plan later completed+archived (a normal lifecycle event, now discounted via a
     `plans/archive/**` basename fallback) → 91 genuine dead links remain, seeded into
     `scripts/plan-hygiene/doc_reference_baseline.yaml` (same shrinking-ratchet convention as
     `defi_address_citation_baseline.yaml`) so the check gates NEW breakage only, not day-one pre-existing debt.
     Verified live: injecting a synthetic broken reference correctly failed with a
     `(NEW — not in doc_reference_baseline.yaml)` marker; reverted clean; `--update-doc-ref-baseline` confirmed
     idempotent (zero-diff re-run).
  4. On red, in addition to the existing Slack page, now ALSO dispatches `wall_type: plan_health` to
     `escalate-to-orchestrator.yml` (the SAME already-built resolver `plan-health-agent.yml`'s PR-gate uses —
     `server/plan_health.py` + `agents/plan-health.md`) via `pr_number: 0` (non-PR-scoped, sanctioned by that workflow's
     own contract), so a worker actually attempts the fix instead of only paging a human.
  - **NOT YET VERIFIED**: the `schedule:` trigger resolves against the repo's DEFAULT branch (`main`), which still had
    the pre-fix workflow file at commit time. Tried a direct push of just this one file to `main` — correctly REJECTED
    by branch protection (PR + required `quality-gates-v2` check, no exception; my assumption that the
    `.github/**`-direct-push carve-out meant a literal git-push bypass was WRONG for this repo's actual GitHub ruleset).
    It will reach `main` via the existing LDR→main auto-promote cycle (`ldr-to-main-promote(-fleet).yml`, `*/15`,
    v2-gated auto-merge) — new todo below to confirm the cron actually fires once that lands.
- **LESSON (2026-07-22): never pipe a secret value into visible tool output while inspecting the VM.** Twice this
  session — once reading the Slack bot token from Secret Manager to test auth, once running `ps aux`/`systemctl status`
  on the glue-runner cgroup (which embeds each JIT-ephemeral runner's registration token as a `--jitconfig` base64 CLI
  arg) — a live token landed in plaintext in tool output/the conversation transcript. Neither was written to a file
  (checked: no token-shaped string anywhere in this session's scratchpad), but both were avoidable: check a secret's
  exit code / length instead of `head -c`'ing its value, and never dump a bare `ps aux`/`systemctl status` on this
  specific cgroup — pipe through `ps -o pid,etimes,cmd | cut -c1-80` or grep for the process NAME only.

- **2026-07-23 — 1-week interim billing check (operator ask: "did the migration pay off?").** NOT the scheduled two-week
  Phase-5 re-pull below — an informal 1-week checkpoint, live-pulled from the same Enhanced-Billing ledger
  (`github-billing-token` → `GET /users/IggyIkenna/settings/billing/usage?year=2026&month=7`, 1,283 line items, 100%
  `product=actions`, token shredded from scratchpad immediately after the pull). Method: pre = Jul 1–15 (the plan's own
  Phase-0 baseline window); post = Jul 17–22 (6 full days — the first clean days after BOTH STEP 2, 37/37 movers, and
  STEP 2c, the composite-action conversion, landed 2026-07-17); Jul 16 excluded as the deploy/transition day (only 10/38
  flipped, canary testing in progress, spend that day was actually the month's 2nd-highest); Jul 23 excluded as a
  partial day (pulled mid-session).
  - **PM (the only repo STEP 2 touched) — real, measured win**: **$16.89/day → $10.94/day, -35.3%**
    (-$5.96/day;
    run-rate ~$513/mo → ~$333/mo, ~**$181/mo saved** if sustained;
    ~$36 actually saved over the 6 clean post-migration
    days). Against the tighter immediately-prior week (Jul 8–15 = $24.74/day,
    since spend was ramping into mid-July — see the Jul 13/14 spike that triggered this whole plan) the drop reads
    steeper: -55.8%, ~$420/mo run-rate. Report both; the true number is baseline-sensitive and the 2-week re-pull will
    tighten it.
  - **Fleet-wide total did NOT drop** — $35.51/day → $38.37/day (**+8.1%**), nowhere near the plan's own
    "~$1,000/mo →
    ~$300–400/mo" target. Root cause, isolated by repo: **every non-PM repo rose**,
    $18.61/day → $27.44/day (**+47%**, ~$566/mo → ~$834/mo run-rate) — and STEP 2 touched **zero** non-PM workflows, so
    this is not the migration backfiring. Per-day trace shows several repos (features-service, agent-orchestrator,
    deployment-api, market-tick-data-service) were already elevated on Jul 14–16, _before_ migration — a fleet-wide
    activity ramp this plan didn't touch, now masking PM's real saving in the naive fleet total. Not investigated
    further (out of this plan's scope) — worth a look if it doesn't revert on its own by the 2-week re-pull.
  - **Data-quality note**: this pull's Jul 1–15 fleet total
    ($532.58) is ~10% above the plan's originally-recorded
    baseline ($485, frontmatter `source:`) — Enhanced-Billing
    appears to backfill/revise a few days after the fact (the original was pulled ~Jul 15/16, before the period closed).
    Use this session's $532.58/$16.89-per-day-PM as the more complete Phase-0 reference going forward.
  - **Verdict**: PM's piece of the plan is working as designed, in the right direction, at roughly 36–100% of the item-1
    estimate ($400–500/mo) depending which baseline you trust — genuine progress, not yet provable as the full plan
    target, and invisible in a naive fleet-total check because of unrelated fleet growth. Don't re-derive this by hand
    next time — the pull command + math above is reusable verbatim for the scheduled 2-week comparison.

- **2026-07-23 (session end) — LESSONS worth more than the state.** Recorded because each cost real time today and none
  of it is inferable from the diffs:
  1. **I stated two things before verifying them, and both were materially wrong.** (a) Published
     "~$180–195/mo of
     staging waste, all GitHub-hosted" — PM's four drivers were ALREADY self-hosted since STEP 2 (in this plan's own
     MOVE list, which I failed to re-read); real figure ~$166/mo,
     ~97% of it in the two templates that CANNOT be self-hosted. (b) Repeated a sub-agent's "transient xdist flake"
     diagnosis — it was deterministic and concealed a P1 gate-bypass. **Rule: a sub-agent's DIAGNOSIS is a hypothesis,
     not a finding. Re-run the check yourself before it reaches a doc or the operator.**
  2. **`billable={}` (absence of the `UBUNTU` key) is the honest self-hosted check on this account.** `/timing`'s
     `total_ms` reads 0 for HOSTED jobs too — it proves nothing on its own. This is what made the wrong cost figure look
     plausible.
  3. **PM's LDR is too busy for the documented sentinel-race workaround alone.** The known P0 workaround (chain
     `quality-gates.sh --no-fix && quickmerge.sh` in one shell) was NOT sufficient — PM takes a push roughly every ~2
     min while its gate takes ~4, so the commit always arrived stale (failed 3×, drift of 3 → 1 → 1 commits). What
     worked: a bounded `for i in 1..5; pull --rebase --autostash; quickmerge; break-if-clean` loop — landed on
     attempt 2. Use the loop on PM; a single retry is not enough. NEVER `SKIP_BRANCH_DRIFT` (human-only).
  4. **Derive fleet-rollout order topologically from `workspace-manifest.json`, don't discover it by failure.**
     Yesterday's rollout blocked repo-by-repo on quickmerge's dep-audit. Today, computing dependency layers up front
     (Layer 1 `deployment-ui`/`unified-api-contracts`/`unified-trading-system-ui` → L2 `unified-trading-library` → L3 17
     repos → L4 `deployment-api`/`e2e-testing` → L5 `system-integration-tests`) let batches of 5-6 run cleanly in
     parallel. The one-liner that produces it is in the session transcript's audit step; re-derive with a topological
     sort over `repositories.<repo>.dependencies`.
  5. **gitleaks false-positives on ordinary prose — and the trap is RECURSIVE.** The `generic-api-key` rule blocked a
     `docs(plans):` commit twice today. Trigger shape (described, deliberately NOT reproduced here, see why below): a
     frontmatter line where the word "key" is followed by a comma and then a slash-joined token pair — gitleaks reads
     that token as a secret assigned to the "key". The recursion: my FIRST fix reworded the frontmatter, but then
     writing THIS lesson quoted the original string verbatim, which re-triggered the identical block on the very commit
     carrying the lesson. **So: describe such a trigger, never quote it.** Also: do NOT add a gitleaks suppression for a
     doc, and do not assume a gitleaks failure means you leaked something — read the `Finding:` line first, it prints
     the matched context.
  6. **Rejected approach, so it isn't re-walked:** self-hosting the two staging fleet templates to make them free. Not
     possible — all 8 runners are registered to `unified-trading-pm` ONLY (fleet repos measure 0;
     `orgs/IggyIkenna/ actions/runners` → 404, personal account, no org pool). Flipping their `runs-on` would hang all
     24 rendered copies. This is the plan's existing **KEEP-T** class, re-confirmed by measurement.

---

## Cost ruling 2026-07-23 — semver-agent stays DEAD; minting moves to the PM reconciler (option B)

Investigating the dead fleet release tagging (`plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md`
F2) surfaced a decision that belongs to THIS plan, because it is a spend decision, not a repair.

**Root cause of the tagging outage was not a bug — it was an orphaning.** `semver-agent.yml` triggers on
`push: [staging]`; the 2026-06-27 cutover made staging dormant, so the only thing that mints `v*` tags simply stopped
firing (last runs UTL 2026-06-28 / UAC 2026-06-27, matching each repo's newest tag exactly). Measured impact: **22
repos, 26–29 days, ~2,490 unreleased commits.**

**Reviving it was built, proven, and then REVERTED — on cost and noise:**

| axis         | measured                                                                                                                         |
| ------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| GHA cost     | `ubuntu-latest` (unmovable — self-hosted runners are PM-only, no org pool), ~~178 runs/day, 1-min billing minimum ⇒ **~~$32/mo** |
| commit noise | **733 PM `chore(manifest)` commits in 30 days — ~24/day, peak 84/day**, into the merge-driver file every slot rebases on         |

~$32/mo is a **~19% add-back** against this plan's ~$166/mo baseline, which is why it was rejected here rather than
treated as a straightforward fix. **Option B** puts minting in `reconcile_release_tags.py`, already scheduled `*/30` in
PM on **self-hosted runners (\$0)**, with ONE batched manifest commit per run instead of one per bump — same versions
and rollback capability, no new billable runs, no commit storm.

**Reverted, verified clean:** `unified-api-contracts@d9ff488b`, `unified-trading-library@df89ac54`,
`unified-trading-api@6987074`. The proven template is recoverable from the pre-revert shas cited in the issue doc.

**KEPT deliberately** (zero cost, zero noise, independent of the minter design):

- the release-stall **detector** in `reconcile_release_tags.py` — converts a silent 4-week outage into a `::warning::`
  naming the repos and their staleness (this is what measured the numbers above);
- `publish-package.yml` **fail-closed on `0.0.0.dev0`** + `fetch-depth: 0` (a shallow checkout has no tags, so hatch-vcs
  emitted a sentinel version — that wheel is in AR from 2026-07-03);
- `unified-trading-library@08b4d89a` — the `:VERSION` Docker tag is no longer re-pointed at new content.

**Lesson for this plan's cost model:** "revive the dead thing" is not automatically the right fix. The measurement that
mattered here was not whether it works, but what it costs per month and how many commits/day it generates — and both
were knowable before writing any code. Measure the running cost of a mechanism BEFORE restoring it.

## Deferred work after 2026-07-23

| #   | Item                                                                   | State / why deferred                                                                                                                                                                                                            | Blocked on               |
| --- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| 1   | **Trading kill-switch is a no-op** (`halt-order-flow` has no listener) | **OPERATOR-OWNED.** Verified first-hand: execution-service has only a `dependency-update` listener; 204 reads as success; the code's own comment predicts a 404 that never comes. Touches live trading behaviour — not started. | Operator ruling          |
| 2   | **Fleet release tagging dead since 2026-06-27**                        | **NOT DONE — real work, highest technical priority.** `reconcile_release_tags.py:51` expects a static `version =`; fleet moved to `dynamic` + hatch-vcs. 0 tags in ~4 weeks; `publish-package` run 0×/7d.                       | Nobody                   |
| 3   | **QG sentinel is environment-blind**                                   | **NOT DONE.** Gate-bypass: a standalone (prod-default) gate pass writes a sentinel that quickmerge (dev-mode) then honours, skipping the failing suite.                                                                         | Operator picks fix split |
| 4   | `staging_versions` dep-gate fix                                        | **BLOCKED — do not action independently.** Its premise was inverted by finding F2; `staging_versions` tracks the real git tag, `versions` does not.                                                                             | Item 2                   |
| 5   | Codex staging re-entry procedure + stale branch-model sections         | **NOT DONE.** `ci-cd-flow.md` L75-109/L763/L777-786/L1183 still describe staging as canonical; nothing in codex says the disabled triggers must be uncommented on re-entry.                                                     | Nobody                   |
| 6   | 4 orphan dispatches · 4 dead listeners · ~873 vacuous cron runs/wk     | **NOT DONE, P2.** All catalogued with file:line in the sweep issue. `digest-drift-sweep` is the only one costing real money (never converges, fans out to `ubuntu-latest`).                                                     | Nobody                   |
| 7   | Two-week billing re-pull vs the Phase-0 baseline                       | **CANNOT BE DONE YET** — needs elapsed time. Earliest ~2026-07-31. Method + exact commands are in the 2026-07-23 billing entry above; re-run verbatim.                                                                          | The calendar             |

**Recommended NEXT item: #2 (release tagging).** It is unblocked, it silently froze every package version in the fleet
~4 weeks ago, it gates #4, and unlike #1 it needs no operator ruling. #1 is more severe but is explicitly the operator's
call. SSOT for 1/2/5/6: `plans/active/issues/post_cutover_silent_assumption_sweep_2026_07_23.md`.
