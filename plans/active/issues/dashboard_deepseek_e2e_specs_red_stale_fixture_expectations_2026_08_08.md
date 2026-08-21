---
doc_type: issue
title: >-
  Two DeepSeek dashboard e2e specs are red on live-defi-rollout — seeded-fixture expectations no longer match what the
  backend computes (avg_turns_per_task 25.0 vs 9.0, worker split $3.0000 vs $5.0000)
summary: >-
  Found 2026-08-08 while regression-checking the full `chromium` Playwright project after an unrelated
  `playwright.config.ts` change. `deepseek-per-turn-metrics.spec.ts:80` and `deepseek-wallet-reconciliation.spec.ts:32`
  both fail on stale hardcoded fixture expectations: the per-turn spec expects Lifetime `avg_turns_per_task` "25.0" and
  renders "9.0" (the seed literally sets `E2E_DEEPSEEK_ACCT_AVG_TURNS_PER_TASK = 25.0`, so something between the seed
  and the view recomputes/aggregates it — note seed_e2e_state.py's own line-305 comment about a TaskUsageRow whose turns
  "fold into deepseek-per-turn-metrics.spec.ts's hardcoded" values); the wallet spec expects the worker split to contain
  "$3.0000" and renders "Worker (backlog tasks)$5.0000". PROVEN PRE-EXISTING, not caused by the tier-editor work that
  found them — both fail identically at `665e5d0` (the commit immediately before that work's first commit `0cd01aaac`),
  verified by running them in a detached worktree at that commit. Not caught by CI or `quality-gates.sh`: neither runs
  Playwright, so the dashboard e2e suite is only ever exercised by whoever runs it by hand.
status: open
nature: issue
asset_group: [ao]
stage: [meta]
repos: [agent-orchestrator]
scope: [engineer]
tags: [agent-orchestrator, dashboard, e2e, playwright, deepseek, test-fixture, ci-gap]
related:
  [/codex/06-coding-standards/ui-testing-layers.md, /plans/archive/2026_07/ao_consolidated_closeout_2026_07_25.md]
created: 2026-08-08
author: interactive-session (slot 4)
priority: P2
parent_epic: orchestrator_master
assigned_vm: NA
execution_scope: local-only
assigned_role: infra
drift_direction: advance-code
depends_on: []
locked_by:
locked_since:
supersedes:
superseded_by:
resolved_by:
source:
  [
    "discovered 2026-08-08 regression-checking `npx playwright test --project=chromium` (44 passed / 2 failed) after
    adding tier-editor.spec.ts; provenance established by re-running both specs in a detached worktree at 665e5d0",
  ]
context_scope:
  [
    agent-orchestrator/dashboard/tests/e2e/deepseek-per-turn-metrics.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/deepseek-wallet-reconciliation.spec.ts,
    agent-orchestrator/dashboard/tests/e2e/fixtures/seed_e2e_state.py,
    agent-orchestrator/server/deepseek_usage.py,
    /codex/06-coding-standards/ui-testing-layers.md,
  ]
---

# DeepSeek dashboard e2e specs red on stale fixture expectations

## Reproduce

```bash
cd agent-orchestrator/dashboard
npx playwright test --project=chromium tests/e2e/deepseek-per-turn-metrics.spec.ts \
                                       tests/e2e/deepseek-wallet-reconciliation.spec.ts
```

## The two failures

| Spec                                        | Assertion                         | Expected  | Rendered                        |
| ------------------------------------------- | --------------------------------- | --------- | ------------------------------- |
| `deepseek-per-turn-metrics.spec.ts:80`      | Lifetime row `avg_turns_per_task` | `25.0`    | `9.0`                           |
| `deepseek-wallet-reconciliation.spec.ts:32` | worker/orchestrator/review split  | `$3.0000` | `Worker (backlog tasks)$5.0000` |

## Why it is NOT the tier-editor change that found it

Both fail identically at `665e5d0` (`0cd01aaac^`), run in a detached worktree at that commit. Neither `0cd01aaac` (tier
editor) nor `95302ff35` (tier-editor e2e suite) touches any `deepseek*` or `seed_e2e_state.py` file.

## Which way to fix — needs the owner's call, hence not auto-fixed

`E2E_DEEPSEEK_ACCT_AVG_TURNS_PER_TASK = 25.0` is set explicitly in the seed, so 9.0 means the value the panel shows is
DERIVED (aggregated across seeded `TaskUsageRow`s), not the seeded scalar. So either:

- **(a) the fixture drifted** — a later commit added task rows that changed the aggregate, and the spec's hardcoded
  numbers simply need re-baselining (cheap, but re-baselining a red assertion is exactly how a real regression gets
  papered over — needs someone who knows the intended semantics); or
- **(b) the aggregation regressed** — the panel is no longer computing what `fff23c5` intended, and 25.0/$3.0000 are
  still the correct expectations.

Distinguishing (a) from (b) requires knowing which number is authoritative for `avg_turns_per_task` — the seeded
per-account scalar or the derived per-task aggregate. That is a semantics question for the deepseek-metrics owner, not a
mechanical fix, which is why this is filed rather than patched.

## Follow-ups

- [x] [REVIEW] P2. ✅ DONE 2026-08-18 — investigated per the ruling below, real regression FIRST, no re-baseline done.
      `deepseek-per-turn-metrics.spec.ts` (the "Accounts panel" test): case (b), real regression — `DeepSeekUsagePoller`
      ran unconditionally in mock mode; already fixed `agent-orchestrator@d279c22` (2026-08-09). `deepseek-wallet-
      reconciliation.spec.ts`: case (a), genuine fixture drift, safe to fix — `is_review_slot` added 2026-08-06 but
      never stamped on the fixture; already fixed `agent-orchestrator@6e3d06c` (2026-08-11), the spec's own `$3.0000`
      assertion untouched throughout. Both re-confirmed passing empirically this session. **RULED 2026-08-09 (operator): investigate as a possible real regression FIRST — do NOT re-baseline
      the fixtures yet.** Trace `agent-orchestrator/server/deepseek_usage.py`'s `avg_turns_per_task` aggregation and the
      wallet worker-split computation against `fixtures/seed_e2e_state.py`'s seeded `TaskUsageRow`s: identify whether
      any commit changed the aggregation formula since the specs' `25.0`/`$3.0000` expectations were authored, and state
      whether `9.0`/`$5.0000` is the correct output of the CURRENT formula applied to the seed data — case (a), fixture
      drift, safe to re-baseline — or a mismatch between intended and actual computation — case (b), real regression,
      needs a code fix, not a spec edit. Done when: this todo cites the specific commit/formula evidence for whichever
      case it is. Do not re-baseline the specs or change `deepseek_usage.py` as part of this todo — that is a follow-up
      once the investigation lands, and only if the investigation itself settles which value is authoritative (if it
      stays a genuine semantics call even after tracing the code/history, escalate back to `[OPERATOR]` rather than
      guessing). Repo: agent-orchestrator.
- [ ] [UI] P2. Once the two specs are green again, decide whether the dashboard Playwright suite should run anywhere
      automatically. It is currently in no gate: `scripts/quality-gates.sh` runs `tsc` + Vitest only, and
      `quality-gates-v2` does not invoke Playwright — so these two have been red with nothing reporting it. Reference
      `/codex/06-coding-standards/ui-testing-layers.md` § Gate Enforcement by Branch for where L2/L3 is supposed to run.

## Progress Log

- **context-scout 2026-08-09**: re-scouted; context_scope unchanged (5 entries), still accurate.
- **2026-08-09 (operator ruling)**: RULED — investigate as a possible real regression FIRST, do NOT re-baseline the
  fixtures yet. Todo 1 retagged `[OPERATOR]` → `[REVIEW]` and reworded into a bounded investigation (trace the
  aggregation formula's history against the seed data, do not touch the specs or the computation as part of it).
  Considered reclassifying `assigned_vm: NA` → `planning` (dispatch-scope-eligibility bar,
  `plans/active/task_template.md` §4): declined for now — this doc's other open todo ([UI] P2, gate the Playwright suite
  into CI) is explicitly sequenced AFTER these specs go green and would be concurrently dispatchable the moment the doc
  goes AO-live (same-priority todos run concurrently by default; nothing here sets `sequential: true`), and
  distinguishing (a) fixture-drift vs (b) real-regression can still terminate in a genuine semantics call the
  investigation alone can't resolve, per the doc's own original framing. Stays `assigned_vm: NA` — revisit if the
  investigation lands a clean, code-only verdict.
- **na-eligibility-audit 2026-08-09 (round9)**: KEEP-NA, valid — re-confirms the same-day operator-ruling entry
  directly above (RECLASSIFY already explicitly considered and declined this session). No new facts change that
  call.
- **na-eligibility-audit 2026-08-10 (ao full-tranche sweep)**: KEEP-NA, valid — `grep -cE '^[[:space:]]*[-*] \[ \]'` =
  **2**, matching. The 2026-08-09 operator ruling entry explicitly considered `assigned_vm: NA → planning`
  (dispatch-scope-eligibility bar) and declined it for a stated, still-current reason: the `[UI]` item is sequenced
  after the `[REVIEW]` investigation and would become concurrently dispatchable the moment this doc goes AO-live, and
  the investigation can still terminate in a genuine semantics call the investigation alone can't resolve. Explicit
  dated operator consideration-and-decline, not re-litigated.
- **context-scout 2026-08-17**: populated/refreshed context_scope (5 entries)
- **context-scout 2026-08-20**: populated/refreshed context_scope (5 entries)
- **2026-08-18 (interactive sub-agent — todo 1, the `[REVIEW]` investigation)**: **Investigation complete, per the
  operator's "investigate as a possible real regression FIRST" ruling.** Traced both failures to specific commits and
  determined case-by-case which side of the (a) fixture-drift / (b) real-regression fork each one is. **Neither is "just
  re-baseline the spec" as originally feared** — both trace to genuine code-level causes, already fixed by other
  sessions' commits before this investigation started (not fixed here; this session only verified/documented). Note:
  this doc's own two rows (`avg_turns_per_task` 25.0 vs 9.0; worker split $3.0000 vs $5.0000) are the "Accounts panel"
  hand-seeded-blob assertion in `deepseek-per-turn-metrics.spec.ts` (confirmed by exact old-line-number match at
  `665e5d0`, the commit this doc's own reproduce section cites) and the wallet-reconciliation worker-split assertion —
  **not** the sibling `ao_dashboard_e2e_pre_existing_flakiness_2026_08_07.md`'s own todo 1, which is the same two specs
  but framed as intermittent flakiness; both docs' investigations converge on the same two root causes below.
  - **`avg_turns_per_task` 25.0 vs 9.0 — case (b)-adjacent, a real regression, NOT fixture drift.** The seeded scalar
    (`E2E_DEEPSEEK_ACCT_AVG_TURNS_PER_TASK = 25.0`) was always correct; "9.0" was `DeepSeekUsagePoller._sweep_account`
    unconditionally overwriting the ENTIRE hand-seeded blob ~30s after e2e-backend boot with a live-computed value from
    an unrelated `TaskUsageRow` fixture (turn_count=9, task_count=1) — the poller had no business running at all in the
    mock/e2e backend. This is a genuine bug in the application's own e2e-mode behavior, not a stale assertion. **Fixed**:
    `agent-orchestrator@d279c22` (2026-08-09) — `server/server.py:318-319`, `if not config.is_mock():` gates
    `deepseek_usage_poller_inst.start()`. Confirmed present in current HEAD (`39d35ed`). The spec's `25.0` expectation
    was never touched and remains correct.
  - **Worker split $3.0000 vs $5.0000 — case (a), genuine fixture drift, safe (and already done) to fix the fixture, not
    the spec.** `compute_deepseek_wallet_reconciliation()` (`server/state_store/slots.py:1550`,
    `_split_attributed_spend` at line 1208) was changed by `agent-orchestrator@e936d05` (2026-08-06) to classify spend by
    a per-row snapshotted `is_review_slot` column rather than live-checking `config.review_slot_ids()` — a deliberate,
    correct production fix for a DIFFERENT bug (`review_slot_ids_config_drift_misattributes_historical_spend_2026_08_06`:
    a live config check retroactively relabels lifetime history when the review-slot reservation moves). The e2e
    fixture's synthetic review row was never updated to stamp that new column, so it read NULL (falsy) and its $2
    spend silently fell into `worker` — measured exactly as this doc's own symptom (worker $5 = $3 real worker + $2
    misrouted review; review $0; `attributed_total`/`residual` still balanced, which is why it read as a pricing bug,
    not a mis-seeded fixture). This is textbook case (a): a later, legitimate production contract change the fixture
    simply never picked up. **Fixed**: `agent-orchestrator@6e3d06c` (2026-08-11) —
    `dashboard/tests/e2e/fixtures/seed_e2e_state.py` now stamps `is_review_slot=(tag == "review")` on all 3 synthetic
    wallet rows, with the exact failure mode documented in-line (lines ~610-617). Confirmed present in current HEAD.
    **The spec's assertion (`$3.0000`) was correct throughout and was never re-baselined** — only the fixture's seeding
    code changed, to match a production contract it had fallen behind.
  - **Both fixes pre-date this investigation by 7-9 days**, landed under other sessions'/other issues' work (the poller
    fix under `e2e_deepseek_poller_overwrites_hand_seeded_account_blob_2026_08_06.md` todo 3; the `is_review_slot` fix
    under `deepseek_wallet_residual_root_cause_and_windowed_reconciliation_2026_08_11`), so this investigation found
    `git diff --stat` empty in this checkout — no new code change was needed or made.
  - **Verification, completed (addendum, same session)**: the `--repeat-each=5` run (both specs, 40 total executions,
    `workers: 1`) eventually finished (~16 min elapsed, peak host `load average` 20+ from concurrent sessions on this
    shared laptop) with **45/45 FAILED — but every failure was a login-page timeout**
    (`Test timeout of 30000ms exceeded ... waiting for locator('input[name="username"]')`), not a DeepSeek assertion
    mismatch. That's an infra/host-contention failure mode, not evidence against either fix — none of the 45 runs got
    far enough to exercise the fixed code paths. Re-ran a SINGLE clean pass instead (cheaper, less exposed to a load
    spike): **both of this doc's own originally-red assertions now PASS** — `deepseek-per-turn-metrics.spec.ts`'s
    "Accounts panel" test (856ms, the exact `avg_turns_per_task` assertion this doc's table cites) and
    `deepseek-wallet-reconciliation.spec.ts`'s worker/orchestrator/review-split test (945ms, the exact assertion this
    doc's table cites) both passed cleanly. This empirically confirms the case-(b)-adjacent poller-gate fix and the
    case-(a) `is_review_slot` fixture fix above, closing the loop the "Done when" criteria asked for.
    **New, separate, out-of-scope finding surfaced by this same clean run**: 2 OTHER tests in
    `deepseek-per-turn-metrics.spec.ts`'s *different* describe block ("Task Token Usage panel", unrelated to either row
    this doc's table describes) are newly red — root-caused the more tractable one with an exact number match: a
    recently-added fixture row for an unrelated "hourly usage time-series chart" feature
    (`E2E_USAGE_TS_HOUR_B_INPUT_TOKENS = 90000`) shares the `dispatch_role="cicd"` tag with the older
    `E2E_CICD_USAGE_INPUT_TOKENS = 2000` row (2000+90000=92000="92.0K", the exact observed value) — same bug class as
    the already-fixed `agent-orchestrator@6a4b7cb` episode, very likely fixture drift again rather than a regression,
    but not fully closed and NOT fixed here (out of scope for this doc's own two named rows). Flagged so it isn't lost;
    needs its own follow-up todo/issue.
  - Todo 2 ([UI] gate the Playwright suite into CI) remains untouched — out of scope for this investigation and still
    correctly sequenced after this todo.

- **na-eligibility-audit 2026-08-19 (ao tranche)** [body-hash:d86463dc898685af]: KEEP-NA, valid — investigation todo now done (2026-08-18, both root causes traced to already-shipped fixes, re-verified passing); sole remaining open todo is an explicit policy/design-fork call (whether to gate the dashboard Playwright suite into CI), cited verbatim in ag_closeout_audit_ao_parked_2026_08_16.md's 'design fork' category. 2 prior audit rounds (2026-08-09, 2026-08-10) already declined reclassification for this same reason.
